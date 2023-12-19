import gzip
import io
import logging
import tempfile
import uuid

from callingcardstools.Analysis.yeast import rank_response
from django.contrib.auth import get_user_model
from django.core.files import File

from config import celery_app
from yeastregulatorydb.regulatory_data.models import Expression, FileFormat, PromoterSetSig, RankResponse
from yeastregulatorydb.regulatory_data.utils.extract_file_from_storage import extract_file_from_storage

logger = logging.getLogger(__name__)


@celery_app.task()
def rank_response_tasks(promotersetsig_ids: list, user_id: int, **kwargs) -> None:
    for promotersetsig_id in promotersetsig_ids:
        rank_response_task.delay(promotersetsig_id, user_id, **kwargs)


@celery_app.task()
def rank_response_task(
    promotersetsig_id: int,
    user_id: int,
    **kwargs,
) -> list:
    try:
        User = get_user_model()
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise ValueError(f"User with id {user_id} does not exist")

    try:
        promotersetsig_record = PromoterSetSig.objects.get(id=promotersetsig_id)
    except PromoterSetSig.DoesNotExist:
        raise ValueError(f"Binding record with id {promotersetsig_id} does not exist")

    try:
        rankresponse_summary_fileformat_record = FileFormat.objects.get(fileformat="rank_repsonse_summary")
    except FileFormat.DoesNotExist:
        raise ValueError(f"FileFormat 'rank_response_summary' does not exist")

    try:
        binding_expression_annotated_fileformat_record = FileFormat.objects.get(
            fileformat="binding_expression_annotated"
        )
    except FileFormat.DoesNotExist:
        raise ValueError(f"FileFormat 'binding_expression_annotated' does not exist")

    with tempfile.TemporaryDirectory() as tmpdir:
        promotersetsig_filepath = extract_file_from_storage(promotersetsig_record.file, tmpdir)

        expression_objects_iterator = (
            Expression.objects.filter(id=kwargs.get("expression_id")).iterator()
            if "expression_id" in kwargs
            else Expression.objects.iterator()
        )

        results_list = []
        for record in expression_objects_iterator:
            expression_filepath = extract_file_from_storage(record.file, tmpdir)

            config_dict = {
                "binding_data_path": promotersetsig_filepath,
                "binding_identifier_col": promotersetsig_record.binding.source.fileformat.feature_identifier_col,
                "binding_effect_col": promotersetsig_record.binding.source.fileformat,
                "binding_pvalue_col": promotersetsig_record.binding.source.fileformat,
                "binding_source": promotersetsig_record.binding.source.name,
                "expression_data_path": expression_filepath,
                "expression_identifier_col": record.source.fileformat.feature_identifier_col,
                "expression_effect_col": record.source.fileformat.effect_col,
                "expression_pvalue_col": record.source.fileformat.pval_col,
                "expression_source": record.source.name,
                "expression_effect_thres": kwargs.get(
                    "expression_effect_threshold", record.source.fileformat.default_effect_threshold
                ),
                "expression_effect_thres": kwargs.get(
                    "expression_pvalue_threshold", record.source.fileformat.default_pvalue_threshold
                ),
                "normalize": kwargs.get("normalize", False),
                "rank_bin_size": kwargs.get("rank_bin_size", 5),
            }

            # validate the configuration key/value pairs
            args = rank_response.validate_config(config_dict)
            # read i the binding data
            try:
                binding_data = rank_response.read_in_data(
                    args["binding_data_path"],
                    args["binding_identifier_col"],
                    args["binding_effect_col"],
                    args["binding_pvalue_col"],
                    args["binding_source"],
                    "binding",
                )
            except (KeyError, FileExistsError, AttributeError) as exc:
                logger.error("Error reading in binding data: %s", exc)
                raise

            # read in the expression data
            try:
                expression_data = rank_response.read_in_data(
                    args["expression_data_path"],
                    args["expression_identifier_col"],
                    args["expression_effect_col"],
                    args["expression_pvalue_col"],
                    args["expression_source"],
                    "expression",
                )
            except (KeyError, FileExistsError, AttributeError) as exc:
                logger.error("Error reading in expression data: %s", exc)
                raise

            df = expression_data.merge(
                binding_data[["binding_effect", "binding_pvalue", "binding_source", "feature"]],
                how="inner",
                on="feature",
            )
            # test that there no incomplete cases. raise an error if there are
            if df.isnull().values.any():
                error_message = "There are incomplete cases in the data"
                logger.error(error_message)
                raise ValueError(error_message)

            try:
                binding_expr_annotated_df, random_df, rank_response_df = rank_response.rank_response_ratio_summarize(
                    df,
                    effect_expression_thres=args["expression_effect_thres"],
                    p_expression_thres=args["expression_pvalue_thres"],
                    normalize=args["normalize"],
                    bin_size=args["rank_bin_size"],
                )
            except KeyError as exc:
                logger.error("Error summarizing data: %s", exc)
                raise

            results_list.append((record, binding_expr_annotated_df))

    output_list = []
    for result_tuple in results_list:
        # extract the dataframes from the output tuple
        expression_record, binding_expr_annotated_df = result_tuple
        # create a buffer to store the dataframe
        binding_expr_annotated_buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=binding_expr_annotated_buffer, mode="wb") as gzipped_file:
            binding_expr_annotated_df.df.to_csv(gzipped_file, index=False)
        # Reset buffer position
        binding_expr_annotated_buffer.seek(0)
        # Create a Django File object with a uuid filename
        binding_expr_annotated_file = File(binding_expr_annotated_buffer, name=f"{uuid.uuid4()}.csv.gz")

        rank_response_buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=rank_response_buffer, mode="wb") as gzipped_file:
            rank_response_df.df.to_csv(gzipped_file, index=False)
        # Reset buffer position
        rank_response_buffer.seek(0)
        # Create a Django File object with a uuid filename
        rank_response_file = File(rank_response_buffer, name=f"{uuid.uuid4()}.csv.gz")

        rankresponse_record = RankResponse.objects.create(
            user=user,
            promotersetsig=promotersetsig_record,
            expression=expression_record,
            fileformat=rank_response_file,
            file=binding_expr_annotated_file,
        )

        # serialize the PromoterSetSig object
        serializer = RankResponse(rankresponse_record)
        # validate the serializer
        serializer.is_valid(raise_exception=True)
        # save the serializer
        serializer.save()
        # add the id to the output list
        output_list.append(rankresponse_record.id)

    return output_list
