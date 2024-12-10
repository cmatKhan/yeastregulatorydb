import json
import logging
import os
import subprocess
import tempfile
from types import SimpleNamespace
from typing import Literal, Tuple, Union

import numpy as np
import pandas as pd
from django.contrib.auth import get_user_model

from config import celery_app
from yeastregulatorydb.regulatory_data.api.serializers import DTOSerializer
from yeastregulatorydb.regulatory_data.models import DTO, Expression, PromoterSetSig
from yeastregulatorydb.regulatory_data.utils import add_genomicfeature_to_file, stable_rank

logger = logging.getLogger(__name__)


def get_ranks(prefix: Literal["pss", "expression"], df: pd.DataFrame, **kwargs) -> np.ndarray:
    """
    This is a helper function to create a column of ranks given a dataframe. The
    `prefix` is used to permit passing in different keyword arguments for the
    PromoterSetSig and Expression files in kwargs.

    :param prefix: The prefix to use for the keyword arguments. One of "pss" or "expression"
    :param df: The dataframe from which to extract columns to calculate the ranks
    :param unfiltered_background: If this is true, the features will be
    :param kwargs: Additional keyword arguments to pass to the stable_rank function. The
        keywords that are currently supported are:

    - {prefix}_col1_ascending: Whether the first column should be sorted in ascending order
        (default: True)
    - {prefix}_col2_ascending: Whether the second column should be sorted in ascending order
        (default: True)
    - {prefix}_method: The method to use for stable ranking (default: "min")
    - {prefix}_ranker_col1: The name of the column to use as the first ranker
    - {prefix}_ranker_col1_abs: Whether to take the absolute value of the first ranker
    - {prefix}_ranker_col2: The name of the column to use as the second ranker
    - {prefix}_ranker_col2_abs: Whether to take the absolute value of the second ranker

    :return: A numpy array with ranks

    :raises KeyError: If the column specified in the ranker_col1 or ranker_col2 keyword
        arguments is not found in the dataframe
    """
    logger.debug(f"Calculating ranks for {prefix} dataframe. Columns: {df.columns}. Keyword arguments: {kwargs}")

    # Prepare stable rank arguments
    stable_rank_arguments = {
        "col1_ascending": kwargs.get(f"{prefix}_col1_ascending", True),
        "method": kwargs.get(f"{prefix}_method", "min"),
    }

    # Extract and process columns for ranking
    try:
        ranker_col1 = kwargs.get(f"{prefix}_ranker_col1", "pvalue")
        stable_rank_arguments["col1"] = (
            df.loc[:, ranker_col1].abs().values
            if kwargs.get(f"{prefix}_ranker_col1_abs", False)
            else df.loc[:, ranker_col1].values
        )
    except KeyError:
        raise KeyError(f"Column '{ranker_col1}' not found in the PromoterSetSig file. The columns are: {df.columns}")

    if kwargs.get(f"{prefix}_ranker_col2"):
        ranker_col2 = kwargs.get(f"{prefix}_ranker_col2")
        try:
            stable_rank_arguments["col2"] = (
                df.loc[:, ranker_col2].abs().values
                if kwargs.get(f"{prefix}_ranker_col2_abs", False)
                else df.loc[:, ranker_col2].values
            )
            stable_rank_arguments["col2_ascending"] = kwargs.get(f"{prefix}_col2_ascending", False)
        except KeyError:
            raise KeyError(f"Column '{ranker_col2}' not found in the PromoterSetSig file")

    return stable_rank(**stable_rank_arguments)


def conditional_filter(
    df: pd.DataFrame, filter_condition: Union[str, None], feature_col
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    If the filter is a string, then use it to filter the dataframe. Return the filtered
    dataframe, and the unfiltered set of features.

    :param df: The dataframe to filter
    :param filter_condition: The filter to use. If None, then return the dataframe as is

    :return: A tuple with the filtered dataframe and the unfiltered set of features

    :raises ValueError: If the filter is not a string
    """
    feature_set = df[feature_col]
    # Apply optional filtering if `{prefix}_filter` is provided
    if filter_condition:
        logger.debug(f"Applying filter condition: {filter_condition}")
        try:
            df = df.query(filter_condition)
            logger.debug(f"Filtered dataframe shape: {df.shape}")
        except Exception as e:
            raise ValueError(f"Invalid filter condition: '{filter_condition}'. Error: {e}")

    return df, feature_set


# set the soft time limit to 2 hrs
@celery_app.task(serializer="json", soft_time_limit=7200, time_limit=8000)
def dto_task(
    user_id: int,
    promotersetsig_id: int,
    expression_id: int,
    promotersetsig_df: Union[pd.DataFrame, None] = None,
    expression_df: Union[pd.DataFrame, None] = None,
    save_record: bool = True,
    **kwargs,
) -> dict:
    """
    Task to run the DTO executable with the given parameters.

    :param promotersetsig_id: The ID of the PromoterSetSig record
    :param expression_id: The ID of the Expression record

    :param promotersetsig_df: A pandas DataFrame with the PromoterSetSig data. If this is
        provided, then the promotersetsig_id is not used. This is intended for testing
        purposes only.
    :param expression_df: A pandas DataFrame with the Expression data. If this is provided,
        then the expression_id is not used. This is intended for testing purposes only.

    :param kwargs: Additional keyword arguments to pass to the DTO executable. keyword
        arguments associated with the promotersetsig file should be prefixed with "pss_"
        and keyword arguments associated with the expression file should be prefixed with
        "expression_". The keywords that are currently supported are:

        ## general arguments
        - deduplicate: Whether to deduplicate the ranks based on the target_symbol column
            (default: True)
        - intersect_features: Whether to filter the rows of both dataframes to only include
            the features that are in the intersection of the two sets (default: True)
        - use_unfiltered_background: Whether to use the intersect of the pss_df and
            expression_df backgrounds prior to any possible filtering (default: True)

        ## promoter set sig arguments:
        - pss_feature_colname: The name of the feature column in the PromoterSetSig file.
            Defaults to target_symbol
        - pss_pvalue_colname: The name of the p-value column in the PromoterSetSig file
        - pss_effect_colname: The name of the effect column in the PromoterSetSig file
        - pss_rename_metric_columns: Whether to rename the metric columns in the
            PromoterSetSig file (default: True)
        - pss_col1_ascending: Whether the first column should be sorted in ascending order
            (default: True)
        - pss_col2_ascending: Whether the second column should be sorted in ascending order
            (default: True)
        - pss_method: The method to use for stable ranking (default: "min")
        - pss_ranker_col1: The name of the column to use as the first ranker
        - pss_ranker_col1_abs: Whether to take the absolute value of the first ranker col
        - pss_ranker_col2: The name of the column to use as the second ranker
        - pss_ranker_col2_abs: Whether to take the absolute value of the second ranker col

        ## expression arguments:
        - expression_feature_colname: The name of the feature column in the Expression file.
            Defaults to target_symbol
        - expression_pvalue_colname: The name of the p-value column in the Expression file
        - expression_effect_colname: The name of the effect column in the Expression file
        - expression_rename_metric_columns: Whether to rename the metric columns in the
            Expression file (default: True)
        - expression_col1_ascending: Whether the first column should be sorted in ascending order
            (default: True)
        - expression_col2_ascending: Whether the second column should be sorted in ascending order
            (default: True)
        - expression_method: The method to use for stable ranking (default: "min")
        - expression_ranker_col1: The name of the column to use as the first ranker
        - expression_ranker_col1_abs: Whether to take the absolute value of the first ranker col
        - expression_ranker_col2: The name of the column to use as the second ranker
        - expression_ranker_col2_abs: Whether to take the absolute value of the second ranker col

        ## DTO executable arguments:
        - n_permutations: Number of permutations to run (default: 1000)
        - n_threads: Number of threads to use (default: 1)

    :return: A dictionary with key "success" and value the primary key of the
        newly created DTO record. If there is an error when trying to save the
        record, the dictionary will have key "error" and value the error message.
    """
    # providing promotersetsig_df and/or expression_df is intended for testing only.
    # save_record should be false as a result
    if save_record and (promotersetsig_df or expression_df):
        raise ValueError("Cannot save record if promotersetsig_df or expression_df are provided")

    # get the User record -- this is used to udpate the database if save_record is True
    try:
        User = get_user_model()
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise ValueError(f"User with id {user_id} does not exist")

    with tempfile.TemporaryDirectory() as tmpdir:

        # if promotersetsig_df is None, then we need to get the promotersetsig record
        # and use it to retrieve the pss file
        if promotersetsig_df is None:
            tmpdir_promotersetsig = os.path.join(tmpdir, "promotersetsig")
            os.makedirs(tmpdir_promotersetsig, exist_ok=True)

            promotersetsig_record = PromoterSetSig.objects.get(id=promotersetsig_id)

            pss_df = add_genomicfeature_to_file(
                promotersetsig_record,
                tmpdir_promotersetsig,
                rename_metric_columns=kwargs.get("pss_rename_metric_columns", True),
                pvalue_colname=kwargs.get("pss_pvalue_colname", None),
                effect_colname=kwargs.get("pss_effect_colname", None),
                return_cols=["all"],
            )
        else:
            pss_df = promotersetsig_df

        if expression_df is None:
            # if expression_df is None, then we need to get the expression record
            # and use it to retrieve the expression file
            tmpdir_expression = os.path.join(tmpdir, "expression")
            os.makedirs(tmpdir_expression, exist_ok=True)

            expression_record = Expression.objects.get(id=expression_id)

            # If a record with the same promotersetsig.id and expression.id exists,
            # then just return that pk
            if DTO.objects.filter(
                promotersetsig=promotersetsig_record.id, expression_id=expression_record.id
            ).exists():
                return {
                    "success": DTO.objects.get(
                        promotersetsig=promotersetsig_record.id, expression_id=expression_record.id
                    ).pk
                }

            # if the expression_record.regulator is not the same as the
            # promoter_record.regulator raise an error
            if expression_record.get_regulator() != promotersetsig_record.get_regulator():
                raise ValueError(
                    f"Expression record regulator {expression_record.regulator} is not the same as the "
                    f"PromoterSetSig record regulator {promotersetsig_record.regulator}"
                )

            expr_df = add_genomicfeature_to_file(
                expression_record,
                tmpdir_expression,
                rename_metric_columns=kwargs.get("expression_rename_metric_columns", True),
                pvalue_colname=kwargs.get("expression_pvalue_colname", None),
                effect_colname=kwargs.get("expression_effect_colname", None),
                return_cols=["all"],
            )
        else:
            expr_df = expression_df

        # get the feature column names
        pss_feature_colname = kwargs.get("pss_feature_colname", "target_symbol")
        expr_feature_colname = kwargs.get("expression_feature_colname", "target_symbol")

        # add the ranks to the dataframes
        pss_df["rank"] = get_ranks("pss", pss_df, **kwargs)
        expr_df["rank"] = get_ranks("expression", expr_df, **kwargs)

        # if kwargs.get("deduplicate") is True, then for pss_df and expr_df if
        # there are multiple rows with the same target_symbol, keep only the row
        # with the lowest rank. If the ranks are tied, just keep the first row.
        if kwargs.get("deduplicate", True):
            pss_df = pss_df.sort_values("rank").drop_duplicates(pss_feature_colname, keep="first")
            expr_df = expr_df.sort_values("rank").drop_duplicates(expr_feature_colname, keep="first")

        pss_df, pss_background = conditional_filter(pss_df, kwargs.get("pss_filter", None), pss_feature_colname)
        expr_df, expr_background = conditional_filter(
            expr_df, kwargs.get("expression_filter", None), expr_feature_colname
        )

        # if use_unfiltered_background is true, then the background is the intersect
        # of the backgrounds prior to the possible filtering from `conditional_filter()`
        # Else, the background is the intersect of the features in the two dataframes.
        # NOTE: if tehre is no filter condition passed for pss and expr, then either
        # of these conditions returns the same thing, so there is no need to set
        # use_unfiltered_background to False. It is only necessary to use
        # `use_unfiltered_background` if you specifically want to use the intersect of
        # the dataframes after filtering as the background.
        background = (
            set(pss_background).intersection(set(expr_background))
            if kwargs.get("use_unfiltered_background", True)
            else set(pss_df[pss_feature_colname]).intersection(set(expr_df[expr_feature_colname]))
        )

        # if intersect_features is True, then filter the dataframes to only include
        # the features that are in the background
        if kwargs.get("intersect_features", True):
            pss_df = pss_df[pss_df[pss_feature_colname].isin(background)]
            expr_df = expr_df[expr_df[expr_feature_colname].isin(background)]
            logger.info("The number of rows remaiing after filtering: {} and {}".format(len(pss_df), len(expr_df)))

        pss_df.loc[:, [pss_feature_colname, "rank"]].to_csv(
            os.path.join(tmpdir, "pss_ranks.csv"), index=False, header=None
        )

        expr_df.loc[:, [expr_feature_colname, "rank"]].to_csv(
            os.path.join(tmpdir, "expression_ranks.csv"), index=False, header=None
        )

        pd.DataFrame(list(background), columns=["background"]).to_csv(
            os.path.join(tmpdir, "background.csv"), index=False, header=None
        )

        output_dict = {}
        try:
            # Execute the DTO executable with the given parameters
            result = subprocess.run(
                [
                    os.getenv("DTO_EXECUTABLE"),
                    "-1",
                    os.path.join(tmpdir, "pss_ranks.csv"),
                    "-2",
                    os.path.join(tmpdir, "expression_ranks.csv"),
                    "-b",
                    os.path.join(tmpdir, "background.csv"),
                    "-p",
                    str(kwargs.get("n_permutations", 1000)),  # Ensure numeric arguments are strings
                    "-t",
                    str(kwargs.get("n_threads", 1)),  # Ensure numeric arguments are strings
                ],
                cwd=tmpdir,
                stdout=subprocess.PIPE,  # Capture stdout
                stderr=subprocess.PIPE,  # Capture stderr
                check=True,  # Raise CalledProcessError if the command fails
                text=True,  # Decode stdout and stderr as text
            )

        except subprocess.CalledProcessError as exc:
            # Extend the error with custom information
            raise RuntimeError(
                f"DTO execution failed with exit code {exc.returncode}. Command: {exc.cmd}. Output: {exc.stderr}"
            ) from exc

        dto_result = json.loads(result.stdout)

        try:
            passing_fdr = dto_result["fdr"] <= 0.2
        except KeyError as exc:
            logger.error(f"Error getting FDR: {exc}", exc_info=True)
            passing_fdr = False

        try:
            passing_pvalue = dto_result["empirical_pvalue"] <= 0.1
        except KeyError as exc:
            logger.error(f"Error getting empirical p-value: {exc}", exc_info=True)
            passing_pvalue = False

        try:
            if save_record:

                dto_data = {
                    "promotersetsig": promotersetsig_record.id,  # Use primary key if related fields are ForeignKey/OneToOneField
                    "expression": expression_record.id,  # Use primary key
                    "parameters": kwargs,
                    "result": dto_result,
                    "passing_fdr": passing_fdr,
                    "passing_pvalue": passing_pvalue,
                }

                mock_request = SimpleNamespace(user=user)  # Mock the request object

                serializer = DTOSerializer(data=dto_data, context={"request": mock_request})
                if serializer.is_valid():
                    dto = serializer.save()
                    output_dict["success"] = dto.pk
                else:
                    # Handle validation errors
                    raise ValueError(f"Invalid data: {serializer.errors}")
            else:
                output_dict["success"] = dto_result
        except Exception as exc:
            logger.error(f"Error saving DTO: {exc}", exc_info=True)
            output_dict["error"] = f"ERROR: {str(exc)}"

        return output_dict
