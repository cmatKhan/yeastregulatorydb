import gzip
import io
import logging
import os
import tempfile
import uuid
from types import SimpleNamespace
from typing import List

from callingcardstools.Analysis.yeast import rank_response
from django.contrib.auth import get_user_model
from django.core.files import File

from config import celery_app
from yeastregulatorydb.regulatory_data.api.serializers import RankResponseSerializer
from yeastregulatorydb.regulatory_data.models import Expression, PromoterSetSig
from yeastregulatorydb.regulatory_data.utils.extract_file_from_storage import extract_file_from_storage

logger = logging.getLogger(__name__)


@celery_app.task(serializer="json")
def rank_response_task(
    user_id: int,
    promotersetsig_ids: List[int],
    expression_ids: List[int],
    **kwargs,
) -> dict:

    summarize_by_rank_bin = kwargs.get("summarize_by_rank_bin", True)
    if not isinstance(summarize_by_rank_bin, bool):
        raise ValueError("summarize_by_rank_bin must be a boolean")

    with tempfile.TemporaryDirectory() as tmpdir:
        regulator_symbol = set()
        # create a subdirectory 'promotersetsig' in the temporary directory
        # to store the extracted promotersetsig files
        promotersetsig_dict = {
            "filepaths": [],
            "source": set(),
            "feature_col": set(),
            "effect_col": set(),
            "pval_col": set(),
        }
        tmpdir_promotersetsig = tmpdir + "/promotersetsig"
        os.makedirs(tmpdir_promotersetsig, exist_ok=True)
        for promotersetsig_id in promotersetsig_ids:
            promotersetsig_record = PromoterSetSig.objects.get(id=promotersetsig_id)

            regulator_symbol.add(promotersetsig_record.get_genomicfeature().symbol)
            if len(regulator_symbol) > 1:
                raise ValueError("All PromoterSetSig objects must have the same regulator")

            promotersetsig_dict["source"].add(promotersetsig_record.get_source_name().name)
            if len(promotersetsig_dict["source"]) > 1:
                raise ValueError("All PromoterSetSig objects must have the same source")

            # if these values are empty, add them to the set
            if promotersetsig_dict["feature_col"] == set():
                # as long as the source is all the same, these will be all the same
                promotersetsig_dict["feature_col"].add(promotersetsig_record.fileformat.feature_identifier_col)
                promotersetsig_dict["effect_col"].add(promotersetsig_record.fileformat.effect_col)
                promotersetsig_dict["pval_col"].add(promotersetsig_record.fileformat.pval_col)

            # extract the file from the storage and store the filepath
            promotersetsig_filepath = extract_file_from_storage(promotersetsig_record.file, tmpdir_promotersetsig)
            promotersetsig_dict["filepaths"].append(promotersetsig_filepath)

        # create a subdir for the expression data
        expression_dict = {
            "filepaths": [],
            "source": set(),
            "feature_col": set(),
            "effect_col": set(),
            "effect_threshold": set(),
            "pval_col": set(),
            "pval_threshold": set(),
        }
        tmpdir_expression = tmpdir + "/expression"
        os.makedirs(tmpdir_expression, exist_ok=True)
        for expression_id in expression_ids:
            expression_record = Expression.objects.get(id=expression_id)

            regulator_symbol.add(expression_record.get_genomicfeature().symbol)
            if len(regulator_symbol) > 1:
                raise ValueError("All PromoterSetSig and Expression objects must have the same regulator")

            expression_dict["source"].add(expression_record.source.name)
            if len(expression_dict["source"]) > 1:
                raise ValueError("All Expression objects must have the same source")

            # as long as the source is all the same, these will be all the same
            # only update once
            if expression_dict["feature_col"] == set():
                expression_dict["feature_col"].add(expression_record.source.fileformat.feature_identifier_col)

                # set the effect column settings
                expression_effect_colname = kwargs.get(
                    "expression_effect_colname", expression_record.source.fileformat.effect_col
                )
                expression_dict["effect_col"].add(expression_effect_colname)

                expression_effect_threshold = float(
                    kwargs.get(
                        "expression_effect_threshold", expression_record.source.fileformat.default_effect_threshold
                    )
                )
                expression_dict["effect_threshold"].add(expression_effect_threshold)

                # set the pvalue column settings
                expression_dict["pval_col"].add(expression_record.source.fileformat.pval_col)

                # if the expression pval column is none, set the thres to none. This
                # is in the event that there is no pvalue column
                # TODO consider requiring a pvalue column?
                expression_pval_threshold = (
                    None
                    if expression_record.source.fileformat.pval_col == "none"
                    or expression_record.source.fileformat.pval_col is None
                    else float(
                        kwargs.get(
                            "expression_pvalue_threshold", expression_record.source.fileformat.default_pvalue_threshold
                        )
                    )
                )
                expression_dict["pval_threshold"].add(expression_pval_threshold)

            expression_filepath = extract_file_from_storage(expression_record.file, tmpdir_expression)
            expression_dict["filepaths"].append(expression_filepath)

        rank_bin_size = int(kwargs.get("rank_bin_size", 5))

        rank_by_binding_effect = kwargs.get("rank_by_binding_effect", False)
        if not isinstance(rank_by_binding_effect, bool):
            raise ValueError("rank_by_binding_effect must be a boolean")

        config_dict = {
            "binding_data_path": promotersetsig_dict["filepaths"],
            "binding_source": promotersetsig_dict["source"].pop(),
            "binding_identifier_col": promotersetsig_dict["feature_col"].pop(),
            "binding_effect_col": promotersetsig_dict["effect_col"].pop(),
            "binding_pvalue_col": promotersetsig_dict["pval_col"].pop(),
            "rank_by_binding_effect": rank_by_binding_effect,
            "expression_data_path": expression_dict["filepaths"],
            "expression_source": expression_dict["source"].pop(),
            "expression_identifier_col": expression_dict["feature_col"].pop(),
            "expression_effect_col": expression_dict["effect_col"].pop(),
            "expression_effect_thres": expression_dict["effect_threshold"].pop(),
            "expression_pvalue_col": expression_dict["pval_col"].pop(),
            "expression_pvalue_thres": expression_dict["pval_threshold"].pop(),
            "rank_bin_size": rank_bin_size,
            "normalization_threshold": int(kwargs.get("normalization_threshold", -1)),
        }

        logger.debug(f"Rank Response task config: {config_dict}")

        # validate the configuration key/value pairs
        args = rank_response.validate_config(config_dict)

        rank_response_df, labeled_binding_response_df, random_expectation_df = (
            rank_response.create_rank_response_table(args)
        )

        # true if any of the rank_bins less than 100 have ci_lower > 0
        try:
            passing = (
                rank_response_df[rank_response_df["rank_bin"] < 100]["ci_lower"].max()
                > random_expectation_df.random[0]
            )
        except TypeError:
            passing = False
        except KeyError:
            passing = False

        try:
            rank_25_rr = rank_response_df.loc[rank_response_df["rank_bin"] == 25, "response_ratio"].values[0]
        except (ZeroDivisionError, KeyError, IndexError) as exc:
            logger.error(f"Error calculating rank_25: {exc}")
            rank_25_rr = 0.0

        try:
            rank_50_rr = rank_response_df.loc[rank_response_df["rank_bin"] == 50, "response_ratio"].values[0]
        except (ZeroDivisionError, KeyError, IndexError) as exc:
            logger.error(f"Error calculating rank_50: {exc}")
            rank_50_rr = 0.0

        # note that the `id` needs to be like this in order for the return to be
        # consistent with the RetrieveRecordsAndFilesMixin
        # if kwargs.get("summary", True) is True, return the rank_response_df
        # summarized by rank_bin. Else, return the labeled_binding_response_df
        results_dict = {
            "regulator_symbol": regulator_symbol.pop(),
            "promotersetsig_ids": ",".join(map(str, promotersetsig_ids)),
            "expression_ids": ",".join(map(str, expression_ids)),
            "data": (rank_response_df.to_dict() if summarize_by_rank_bin else labeled_binding_response_df.to_dict()),
            "n_responsive": int(random_expectation_df.responsive[0]),
            "total_expression_genes": float(
                random_expectation_df.unresponsive[0] + random_expectation_df.responsive[0]
            ),
            "passing": int(passing),
            "rank_25": rank_25_rr,
            "rank_50": rank_50_rr,
        }

        if kwargs.get("save_record", False):
            # get the User record -- this is used to udpate the database if save_record is True
            try:
                User = get_user_model()
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise ValueError(f"User with id {user_id} does not exist")

            if len(promotersetsig_ids) > 1:
                raise ValueError(
                    "`save_record` can currently only be used when there is a single promotersetsig record"
                )
            if len(expression_ids) > 1:
                raise ValueError("`save_record` can currently only be used when there is a single expression record")

            buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=buffer, mode="wb") as gzipped_file:
                labeled_binding_response_df.to_csv(gzipped_file, index=False)
                gzipped_file.flush()

            # Reset buffer position
            buffer.seek(0)

            # Test gzip integrity
            try:
                with gzip.GzipFile(fileobj=buffer, mode="rb") as gzipped_file:
                    _ = gzipped_file.read(1024)  # Read a chunk to validate
                logger.debug("Gzip file integrity check passed.")
            except (OSError, EOFError) as e:
                logger.error(f"Gzip file integrity check failed: {e}")
                raise ValueError("Compressed file is invalid or corrupted.")

            buffer.seek(0)  # Reset buffer for Django File
            # Create a Django File object with a uuid filename
            upload_file = File(buffer, name=f"{uuid.uuid4()}.csv.gz")

            record_data = {
                "promotersetsig": promotersetsig_ids[0],
                "expression": expression_ids[0],
                "parameters": kwargs,
                "passing": passing,
                "random_expectation": random_expectation_df.random[0],
                "total_expression_genes": random_expectation_df.unresponsive[0] + random_expectation_df.responsive[0],
                "rank_25": rank_25_rr,
                "rank_50": rank_50_rr,
                "file": upload_file,
            }

            mock_request = SimpleNamespace(user=user)  # Mock the request object

            serializer = RankResponseSerializer(data=record_data, context={"request": mock_request})
            if serializer.is_valid():
                rr_record = serializer.save()
                results_dict["id"] = rr_record.id
            else:
                # Handle validation errors
                logger.error(f"Invalid data: {serializer.errors}")
    return results_dict
