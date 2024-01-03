import gzip
import io
import logging
import tempfile
import uuid
from types import SimpleNamespace

from callingcardstools.Analysis.yeast import rank_response
from django.contrib.auth import get_user_model
from django.core.files import File

from config import celery_app
from yeastregulatorydb.regulatory_data.api.serializers import RankResponseSerializer
from yeastregulatorydb.regulatory_data.models import Expression, FileFormat, PromoterSetSig
from yeastregulatorydb.regulatory_data.utils.extract_file_from_storage import extract_file_from_storage

logger = logging.getLogger(__name__)


@celery_app.task()
def rank_response_tasks(promotersetsig_ids: list, user_id: int, **kwargs) -> None:
    """
    Iterate over a list of PromoterSetSig object ids and call the
    rank_response_task. The kwargs are passed to the rank_response_task

    :param promotersetsig_ids: A list of promotersetsig object ids
    :type promotersetsig_ids: list
    :param user_id: the id of the user that initiated the task
    :type user_id: int
    :param kwargs: keyword arguments to be passed to the rank_response_task
    """
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
        rankresponse_format = FileFormat.objects.get(fileformat="rankresponse")
    except FileFormat.DoesNotExist:
        raise ValueError("FileFormat 'rank_response_summary' does not exist")

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

            expr_pval_thres = kwargs.get(
                "expression_pvalue_threshold", record.source.fileformat.default_pvalue_threshold
            )
            expr_pval_thres = None if expr_pval_thres == 1.0 else expr_pval_thres

            config_dict = {
                "binding_data_path": promotersetsig_filepath,
                "binding_identifier_col": promotersetsig_record.fileformat.feature_identifier_col,
                "binding_effect_col": promotersetsig_record.fileformat.effect_col,
                "binding_pvalue_col": promotersetsig_record.fileformat.pval_col,
                "binding_source": promotersetsig_record.binding.source.name,
                "expression_data_path": expression_filepath,
                "expression_identifier_col": record.source.fileformat.feature_identifier_col,
                "expression_effect_col": record.source.fileformat.effect_col,
                "expression_pvalue_col": record.source.fileformat.pval_col,
                "expression_source": record.source.name,
                "expression_effect_thres": kwargs.get(
                    "expression_effect_threshold", record.source.fileformat.default_effect_threshold
                ),
                "expression_pvalue_thres": expr_pval_thres,
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
                binding_expr_annotated_df, _, rank_response_summary_df = rank_response.rank_response_ratio_summarize(
                    df,
                    effect_expression_thres=args["expression_effect_thres"],
                    p_expression_thres=args["expression_pvalue_thres"],
                    normalize=args["normalize"],
                    bin_size=args["rank_bin_size"],
                )
            except KeyError as exc:
                logger.error("Error summarizing data: %s", exc)
                raise

            results_list.append((record, binding_expr_annotated_df, rank_response_summary_df))

    output_list = []
    for result_tuple in results_list:
        # extract the dataframes from the output tuple
        expression_record, binding_expr_annotated_df, rank_response_summary_df = result_tuple
        # create a buffer to store the dataframe
        binding_expr_annotated_buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=binding_expr_annotated_buffer, mode="wb") as gzipped_file:
            binding_expr_annotated_df.to_csv(gzipped_file, index=False)
        # Reset buffer position
        binding_expr_annotated_buffer.seek(0)
        # Create a Django File object with a uuid filename
        binding_expr_annotated_file = File(binding_expr_annotated_buffer, name=f"{uuid.uuid4()}.csv.gz")

        # if there is any value in ci_lower greater than 0 in the first
        # 100 rows, then the rank response test passes
        rank_response_pass = rank_response_summary_df["ci_lower"].head(50).gt(0).any()

        upload_data = {
            "promotersetsig": promotersetsig_record.pk,
            "expression": expression_record.pk,
            "fileformat": rankresponse_format.pk,
            "file": binding_expr_annotated_file,
            "significant_response": rank_response_pass,
        }

        # Create a mock request with only a user attribute
        # Assuming you have the user_id available
        mock_request = SimpleNamespace(user=user)
        # serialize the PromoterSetSig object
        serializer = RankResponseSerializer(
            data=upload_data,
            context={"request": mock_request},
        )

        # validate the serializer
        serializer.is_valid(raise_exception=True)
        # save the serializer
        instance = serializer.save()
        # add the id to the output list
        output_list.append(instance.id)

    return output_list
