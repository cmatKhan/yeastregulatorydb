import gzip
import io
import json
import logging
import os
import tarfile
import tempfile

import pandas as pd
from celery import group
from celery.result import GroupResult
from django.db.models import Case, CharField, F, FloatField, JSONField, OuterRef, Subquery, Value, When
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from yeastregulatorydb.regulatory_data.tasks import rank_response_task
from yeastregulatorydb.regulatory_data.utils.extract_file_from_storage import extract_file_from_storage

from ...models import DTO, Expression, PromoterSetSig, RankResponse, UnivariateModels
from ..filters.RankResponseFilter import RankResponseFilter
from ..serializers.RankResponseSerializer import RankResponseSerializer
from .mixins import ExportTableAsGzipFileMixin, RetrieveRecordsAndFilesMixin, UpdateModifiedMixin

logger = logging.getLogger(__name__)


def generate_rank_response_tasks(user_id: int, request_data: list, **kwargs) -> list:
    """
    Submit rank response tasks for each item in the request data.

    :param request_data: A list of dictionaries containing the following
        keys:
            - promotersetsig_ids: List of PromoterSetSig object ids
            - expression_ids: List of Expression object ids
            - expression_effect_colname: Optional. The column name in the
                expression data that contains the effect size
            - expression_effect_threshold: Optional. The threshold for the
                effect size
            - expression_pvalue_threshold: Optional. The threshold for the
                p-value
            - rank_bin_size: Optional. The size of the rank bins
            - rank_by_binding_effect: Optional. Whether to rank by binding
                effect
            - summarize_by_rank_bin: Optional. Whether to summarize by rank
                bin

    :return: A list of tasks that have been submitted to the rank response celery tasks
    """
    # Iterate over each dictionary in the request.data
    tasks = []
    for item in request_data:
        additional_arguments = {}
        if item.get("expression_effect_colname", None):
            additional_arguments["expression_effect_colname"] = item.get("expression_effect_colname")

        if item.get("expression_effect_threshold", None):
            additional_arguments["expression_effect_threshold"] = item.get("expression_effect_threshold")

        if item.get("expression_pvalue_threshold", None):
            additional_arguments["expression_pvalue_threshold"] = item.get("expression_pvalue_threshold")

        if item.get("rank_bin_size", None):
            additional_arguments["rank_bin_size"] = item.get("rank_bin_size")

        if item.get("rank_by_binding_effect", None):
            rank_by_binding_effect = item.get("rank_by_binding_effect").lower()
            if rank_by_binding_effect not in ["true", "false"]:
                raise ValidationError(
                    "The value for the 'rank_by_binding_effect' key must be either 'true' or 'false'"
                )
            additional_arguments["rank_by_binding_effect"] = rank_by_binding_effect == "true"

        if item.get("summarize_by_rank_bin", None):
            summarize_by_rank_bin = item.get("summarize_by_rank_bin").lower()
            if summarize_by_rank_bin not in ["true", "false"]:
                raise ValidationError("The value for the 'summarize_by_rank_bin' key must be either 'true' or 'false'")
            additional_arguments["summarize_by_rank_bin"] = summarize_by_rank_bin == "true"

        promoterset_ids = item.get("promotersetsig_ids")
        if not promoterset_ids:
            raise ValidationError("Each dictionary must contain a 'promotersetsig_ids' key")
        if not isinstance(promoterset_ids, list):
            promoterset_ids = promoterset_ids.split(",")

        for pss_id in promoterset_ids:
            # Validate the promoterset_id from the data item
            if not PromoterSetSig.objects.filter(id=pss_id).exists():
                raise ValidationError(f"PromoterSetSig with id {pss_id} does not exist.")

        expression_ids = item.get("expression_ids")
        if not expression_ids:
            raise ValidationError("Each dictionary must contain an 'expression_ids' key")
        if not isinstance(expression_ids, list):
            expression_ids = expression_ids.split(",")

        for expr_id in expression_ids:
            # Validate the expression_id from the data item
            if not Expression.objects.filter(id=expr_id).exists():
                raise ValidationError(f"Expression with id {expr_id} does not exist.")

        additional_arguments["save_record"] = item.get("save_record", False)

        if not isinstance(additional_arguments["save_record"], bool):
            if additional_arguments["save_record"].lower() in ["true", "1"]:
                additional_arguments["save_record"] = True
            elif additional_arguments["save_record"].lower() in ["false", "0"]:
                additional_arguments["save_record"] = False
            else:
                raise ValidationError("The value for the 'save_record' key must be either 'true' or 'false'")

        # Create Celery tasks for each promoterset_id
        tasks.append(rank_response_task.s(user_id, promoterset_ids, expression_ids, **additional_arguments, **kwargs))

    return tasks


class RankResponseViewSet(
    UpdateModifiedMixin, ExportTableAsGzipFileMixin, RetrieveRecordsAndFilesMixin, viewsets.ModelViewSet
):
    """
    A viewset for viewing and editing Regulator instances.
    """

    dto_result_subquery = Subquery(
        DTO.objects.filter(
            promotersetsig_id=OuterRef("promotersetsig_id"), expression_id=OuterRef("expression_id")
        ).values("result")[:1],
        output_field=JSONField(),
    )

    rsquared_subquery = Subquery(
        UnivariateModels.objects.filter(
            promotersetsig_id=OuterRef("promotersetsig_id"), expression_id=OuterRef("expression_id")
        ).values("rsquared")[:1],
        output_field=FloatField(),
    )

    pvalue_subquery = Subquery(
        UnivariateModels.objects.filter(
            promotersetsig_id=OuterRef("promotersetsig_id"), expression_id=OuterRef("expression_id")
        ).values("pvalue")[:1],
        output_field=FloatField(),
    )

    queryset = (
        RankResponse.objects.order_by("id")
        .select_related(
            "uploader",
            "promotersetsig__single_binding__source",
            "promotersetsig__composite_binding__source",
            "expression__source",
            "expression__expressionmanualqc",
        )
        .annotate(
            preferred_replicate=Case(
                When(
                    promotersetsig__single_binding__isnull=False,
                    then=F("promotersetsig__single_binding__bindingmanualqc__preferred_replicate"),
                ),
                When(promotersetsig__composite_binding__isnull=False, then=Value(True)),
                default=Value(None),
                output_field=CharField(),
            ),
            regulator_id=F("expression__regulator"),
            regulator_symbol=F("expression__regulator__genomicfeature__symbol"),
            regulator_locus_tag=F("expression__regulator__genomicfeature__locus_tag"),
            expression_time=F("expression__time"),
            expression_mechanism=F("expression__mechanism"),
            experession_restriction=F("expression__restriction"),
            expression_control=F("expression__control"),
            expression_replicate=F("expression__replicate"),
            univariate_rsquared=rsquared_subquery,
            univariate_pvalue=pvalue_subquery,
            dto_result=dto_result_subquery,
        )
    )
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = RankResponseSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RankResponseFilter

    # def retrieve(self, request, *args, **kwargs):
    #     """
    #     This adds a feature to the default retrieve() function. If "retrieve_all_data"
    #     is passed as a query parameter `retrieve_all_data`, false by default, which
    #     allows a user to a concatenated file of the rankresponse files for each record
    #     in the queryset. The result is cached by its request parameters.
    #     """
    #     # Check if "retrieve_all_data" parameter is passed
    #     retrieve_all_data = request.query_params.get("retrieve_all_data", False).tolower() == "true"
    #     if not isinstance(retrieve_all_data, bool):
    #         raise ValidationError(
    #             "The value for the 'retrieve_all_data' key " "must be either 'true' or 'false', or omitted."
    #         )
    #     if retrieve_all_data:
    #         # Get the queryset
    #         queryset = self.filter_queryset(self.get_queryset())

    #         # Retrieve the files
    #         file_paths = []
    #         with tempfile.TemporaryDirectory() as temp_dir:
    #             for rank_response in queryset:
    #                 file = rank_response.file
    #                 if file:
    #                     # Use your provided function to fetch the file
    #                     file_path = extract_file_from_storage(file, dirpath=temp_dir)
    #                     file_paths.append(file_path)

    #             # Concatenate files into a single gzip file
    #             with tempfile.NamedTemporaryFile(delete=False, suffix=".gz") as temp_file:
    #                 with gzip.open(temp_file, "wb") as outfile:
    #                     for file_path in file_paths:
    #                         with open(file_path, "rb") as infile:
    #                             outfile.write(infile.read())

    #                 temp_file_path = temp_file.name

    #         # Serve the concatenated file
    #         with open(temp_file_path, "rb") as f:
    #             response = HttpResponse(f.read(), content_type="application/gzip")
    #             response["Content-Disposition"] = "attachment; filename=concatenated_data.gz"

    #         # Cleanup temporary concatenated file
    #         os.unlink(temp_file_path)

    #         return response
    #     else:
    #         # Default behavior
    #         return super().retrieve(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def record_table_and_files(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        # if 'add_genomicfeature_to_file' is passed in the request, that value, which
        # must be 'true' or 'false' will be used preferentially to the default value,
        # which is true. This will return a file with the regulator_id, symbol and
        # locus_tag columns
        return self.retrieve_records_and_files(
            request,
            queryset,
            add_genomicfeature_to_file="false",
            rename_metric_cols=False,
            return_cols=["all"],
        )

    @action(detail=False, methods=["post"])
    def submit(self, request, *args, **kwargs):

        # Check if data is a list
        if not isinstance(request.data, list):
            logger.error("Expected a list of dictionaries in the request body.")
            return Response(
                {"error": "Expected a list of dictionaries in the request body."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tasks = generate_rank_response_tasks(self.request.user.id, request.data, **kwargs)

        # Create a group of tasks and trigger them
        celery_group_result = group(tasks).apply_async()
        celery_group_result.save()

        # Return the group task ID for tracking
        return Response({"group_task_id": celery_group_result.id}, status=202)

    @action(detail=False, methods=["get"])
    def status(self, request, *args, **kwargs):
        group_task_id = request.query_params.get("group_task_id", None)

        if not group_task_id:
            return Response({"error": "You must provide a valid group_task_id."}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the group result using the group_task_id
        group_result = GroupResult.restore(group_task_id)

        if not group_result:
            return Response({"error": "Invalid group_task_id"}, status=status.HTTP_400_BAD_REQUEST)

        # Summarize task states by counting the occurrences of each state
        state_counts = {}
        for task in group_result.results:
            state = task.state
            state_counts[state] = state_counts.get(state, 0) + 1

        # Handle not ready tasks
        if not group_result.ready():
            return Response(
                {"status": "IN_PROGRESS", "task_state_summary": state_counts},  # Summarizing task states
                status=status.HTTP_200_OK,
            )

        # Handle failure cases
        if group_result.failed():
            failed_tasks = [res for res in group_result.results if res.failed()]
            return Response(
                {"status": "FAILURE", "error": "One or more tasks failed", "failed_tasks": failed_tasks},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Handle success cases
        if group_result.ready() and not group_result.failed():
            return Response(
                {"status": "SUCCESS", "group_task_id": group_task_id, "task_state_summary": state_counts},
                status=status.HTTP_200_OK,
            )

        # Fallback for unknown states
        return Response(
            {"status": "UNKNOWN", group_task_id: group_task_id},
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=False, methods=["get"])
    def retrieve_task(self, request, *args, **kwargs):
        group_task_id = request.query_params.get("group_task_id", None)

        if not group_task_id:
            return Response({"error": "You must provide a valid group_task_id."}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the group result using the group_task_id
        group_result = GroupResult.restore(group_task_id)

        if not group_result:
            return Response({"error": "Invalid group_task_id"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the task is ready
        if group_result.ready() and not group_result.failed():
            # Create in-memory tarball
            tar_buffer = io.BytesIO()

            # Collect metadata
            metadata = {}

            # Open tarfile in memory
            with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
                for result in group_result.results:
                    results_dict = result.result
                    if not isinstance(results_dict, dict):
                        return Response(
                            {"error": "Unexpected result format."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )

                    # Add metadata for each result
                    metadata[result.id] = {
                        "regulator_symbol": results_dict.get("regulator_symbol"),
                        "promotersetsig_ids": results_dict.get("promotersetsig_ids"),
                        "expression_ids": results_dict.get("expression_ids"),
                        "n_responsive": results_dict.get("n_responsive"),
                        "total_expression_genes": results_dict.get("total_expression_genes"),
                        "passing": results_dict.get("passing"),
                        "rank_25": results_dict.get("rank_25"),
                        "rank_50": results_dict.get("rank_50"),
                    }

                    # Create CSV in memory
                    csv_buffer = io.BytesIO()
                    try:
                        pd.DataFrame(results_dict.get("data")).to_csv(csv_buffer, compression="gzip", index=False)
                        csv_buffer.seek(0)  # Reset buffer to the beginning for reading
                    except Exception as exc:
                        return Response(
                            {"error": f"Error writing CSV file: {str(exc)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )

                    # Add CSV to tarball
                    tar_info = tarfile.TarInfo(name=f"{result.id}.csv.gz")
                    tar_info.size = len(csv_buffer.getvalue())
                    tar.addfile(tar_info, csv_buffer)

                # Write metadata to memory
                metadata_buffer = io.BytesIO(json.dumps(metadata).encode())
                tar_info = tarfile.TarInfo(name="metadata.json")
                tar_info.size = len(metadata_buffer.getvalue())
                tar.addfile(tar_info, metadata_buffer)

            # Return the tarball as a file download
            tar_buffer.seek(0)  # Reset buffer to the beginning for reading
            response = HttpResponse(tar_buffer.getvalue(), content_type="application/gzip")
            response["Content-Disposition"] = f'attachment; filename="rankresponse_{group_task_id}.tar.gz"'
            return response
        else:
            return Response(
                {"error": "The task is not yet complete or has failed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def destroy(self, request, *args, **kwargs):
        ids = request.data.get("ids", None)

        if isinstance(ids, list):
            try:
                RankResponse.objects.filter(id__in=ids).delete()
            except Exception as exc:
                return Response(
                    {"error": f"Failed to delete RankResponse instances: {str(exc)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            return Response({"message": "Successfully deleted"}, status=status.HTTP_200_OK)
        else:
            instance = self.get_object()
            # Custom pre-deletion logic
            logger.info(f"Deleting RankResponse with ID {instance.id}")
            self.perform_destroy(instance)
            # Custom post-deletion logic
            return Response({"message": "Successfully deleted"}, status=status.HTTP_200_OK)
