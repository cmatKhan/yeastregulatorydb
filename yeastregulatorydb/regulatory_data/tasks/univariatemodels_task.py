import json
import logging
import os
import tempfile
from types import SimpleNamespace
from typing import Union

import numpy as np
import pandas as pd
import statsmodels.api as sm
from django.contrib.auth import get_user_model

from config import celery_app
from yeastregulatorydb.regulatory_data.api.serializers import UnivariateModelsSerializer
from yeastregulatorydb.regulatory_data.models import Expression, PromoterSetSig, UnivariateModels
from yeastregulatorydb.regulatory_data.tasks.dto_task import conditional_filter, get_ranks
from yeastregulatorydb.regulatory_data.utils import add_genomicfeature_to_file

logger = logging.getLogger(__name__)


def shifted_negative_log_ranks(ranks: np.ndarray) -> np.ndarray:
    """
    Transforms ranks to negative log10 values and shifts such that the lowest value is
    0.

    :param ranks: A vector of ranks
    :return np.ndarray: A vector of negative log10 transformed ranks shifted such that
        the lowest value is 0
    :raises ValueError: If the ranks are not numeric.

    """
    if not np.issubdtype(ranks.dtype, np.number):
        raise ValueError("`ranks` must be a numeric")
    max_rank = np.max(ranks)
    log_max_rank = np.log10(max_rank)
    return -1 * np.log10(ranks) + log_max_rank


# set the soft time limit to 2 hrs
@celery_app.task(serializer="json", soft_time_limit=7200, time_limit=8000)
def univariatemodels_task(
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
            if UnivariateModels.objects.filter(
                promotersetsig=promotersetsig_record.id, expression_id=expression_record.id
            ).exists():
                return {
                    "success": UnivariateModels.objects.get(
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

        pss_transformed_rank_colname = "pss_transformed_rank"
        expr_transformed_rank_colname = "expr_transformed_rank"

        pss_df[pss_transformed_rank_colname] = shifted_negative_log_ranks(pss_df["rank"].values)
        expr_df[expr_transformed_rank_colname] = shifted_negative_log_ranks(expr_df["rank"].values)

        # inner join the two dataframes on the feature columns
        merged_df = pd.merge(
            pss_df.loc[:, [pss_feature_colname, pss_transformed_rank_colname]],
            expr_df.loc[:, [expr_feature_colname, expr_transformed_rank_colname]],
            how="inner",
            on=[pss_feature_colname, expr_feature_colname],
        )

        # Log transform and then shift the ranks, and
        # define the independent variable (X) and dependent variable (y)
        X = merged_df[pss_transformed_rank_colname].values
        y = merged_df[expr_transformed_rank_colname].values

        # Add a constant to the independent variable (intercept term) for modeling
        X = sm.add_constant(X)

        # Fit the linear model
        model = sm.OLS(y, X).fit()

        # Extract the r_squared, pvalue, and coefficients
        r_squared = model.rsquared
        pvalue = model.f_pvalue
        coefficients = model.params

        output_dict = {}
        try:

            # if the record won't be saved, just return the modeling results
            univariatemodels_data = {
                "rsquared": r_squared,
                "pvalue": pvalue,
                "coefficients": json.dumps({k: v for k, v in zip(["intercept", "slope"], coefficients)}),
            }

            if save_record:

                # update the record with the promotersetsig and expression ids
                univariatemodels_data.update(
                    {"promotersetsig": promotersetsig_record.id, "expression": expression_record.id}
                )

                mock_request = SimpleNamespace(user=user)  # Mock the request object

                serializer = UnivariateModelsSerializer(data=univariatemodels_data, context={"request": mock_request})
                if serializer.is_valid():
                    univariatemodels_record = serializer.save()
                    output_dict["success"] = univariatemodels_record.pk
                else:
                    # Handle validation errors
                    raise ValueError(f"Invalid data: {serializer.errors}")
            else:
                output_dict["success"] = univariatemodels_data
        except Exception as exc:
            logger.error(f"Error saving UnivariateModels: {exc}", exc_info=True)
            output_dict["error"] = f"ERROR: {str(exc)}"

        return output_dict
