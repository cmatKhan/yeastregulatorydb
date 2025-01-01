# pyright: reportMissingImports=false, reportMissingModuleSource=false

import io
import json
import tarfile

import pandas as pd
from celery import group
from celery.result import GroupResult
from django.db import IntegrityError
from django.db.models import Case, CharField, F, Value, When
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from yeastregulatorydb.regulatory_data.models import Expression, PromoterSetSig
from yeastregulatorydb.regulatory_data.tasks import rank_response_task

from ..filters.PromoterSetSigFilter import PromoterSetSigFilter
from ..serializers.PromoterSetSigSerializer import PromoterSetSigSerializer
from .mixins import (
    ExportTableAsGzipFileMixin,
    GetCombinedGenomicFileMixin,
    RetrieveRecordsAndFilesMixin,
    UpdateModifiedMixin,
)


class PromoterSetSigViewSet(
    UpdateModifiedMixin,
    ExportTableAsGzipFileMixin,
    GetCombinedGenomicFileMixin,
    RetrieveRecordsAndFilesMixin,
    viewsets.ModelViewSet,
):
    """
    A viewset for viewing and editing PromoterSetSig instances.
    """

    # NOTE: THERE IS A USAGE OF .DISTINCT() BELOW THAT IS ERROR PRONE
    # Because composite_binding links to mulltiple binding sources, but we only use
    # fields that are the same among those binding sources, distinct() eliminates the
    # duplicates. But this is obviously not a good way. be very careful
    queryset = (
        PromoterSetSig.objects.order_by("id")
        .select_related(
            "uploader",
            "single_binding",
            "single_binding__regulator",
            "single_binding__regulator__genomicfeature",
            "single_binding__source",
            "composite_binding",
            "composite_binding__regulator",
            "composite_binding__regulator__genomicfeature",
            "composite_binding__source",
            "promoter",
            "background",
            "fileformat",
        )
        .prefetch_related(
            "composite_binding__bindings",
            "composite_binding__bindings__source",
            "composite_binding__bindings__regulator",
            "composite_binding__bindings__regulator__genomicfeature",
        )
        .annotate(
            source_name=Case(
                When(single_binding__isnull=False, then=F("single_binding__source__name")),
                When(composite_binding__isnull=False, then=F("composite_binding__bindings__source__name")),
                default=Value(None),
                output_field=CharField(),
            ),
            assay=Case(
                When(single_binding__isnull=False, then=F("single_binding__source__assay")),
                When(composite_binding__isnull=False, then=F("composite_binding__bindings__source__assay")),
                default=Value(None),
                output_field=CharField(),
            ),
            lab=Case(
                When(single_binding__isnull=False, then=F("single_binding__source__lab")),
                When(composite_binding__isnull=False, then=F("composite_binding__bindings__source__lab")),
                default=Value(None),
                output_field=CharField(),
            ),
            batch=Case(
                When(single_binding__isnull=False, then=F("single_binding__batch")),
                default=Value(None),
                output_field=CharField(),
            ),
            regulator_symbol=Case(
                When(single_binding__isnull=False, then=F("single_binding__regulator__genomicfeature__symbol")),
                When(
                    composite_binding__isnull=False,
                    then=F("composite_binding__bindings__regulator__genomicfeature__symbol"),
                ),
                default=Value(None),
                output_field=CharField(),
            ),
            regulator_locus_tag=Case(
                When(single_binding__isnull=False, then=F("single_binding__regulator__genomicfeature__locus_tag")),
                When(
                    composite_binding__isnull=False,
                    then=F("composite_binding__bindings__regulator__genomicfeature__locus_tag"),
                ),
                default=Value(None),
                output_field=CharField(),
            ),
            # note: since the composite_binding is only used for calling cards, which dosen't havea  condition
            # there is no need to use the composite binding When
            condition=Case(
                When(single_binding__isnull=False, then=F("single_binding__condition")),
                default=Value(None),
                output_field=CharField(),
            ),
            data_usable=Case(
                When(single_binding__isnull=False, then=F("single_binding__bindingmanualqc__data_usable")),
                When(composite_binding__isnull=False, then=F("composite_binding__bindingmanualqc__data_usable")),
                default=Value(None),
                output_field=CharField(),
            ),
            manual_fail=Case(
                When(single_binding__isnull=False, then=F("single_binding__bindingmanualqc__manual_fail")),
                When(composite_binding__isnull=False, then=F("composite_binding__bindingmanualqc__manual_fail")),
                default=Value(None),
                output_field=CharField(),
            ),
            preferred_replicate=Case(
                When(single_binding__isnull=False, then=F("single_binding__bindingmanualqc__preferred_replicate")),
                When(
                    composite_binding__isnull=False, then=F("composite_binding__bindingmanualqc__preferred_replicate")
                ),
                default=Value(None),
                output_field=CharField(),
            ),
            source_orig_id=Case(
                When(single_binding__isnull=False, then=F("single_binding__source_orig_id")),
                default=Value(None),
                output_field=CharField(),
            ),
        )
    ).distinct()

    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = PromoterSetSigSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PromoterSetSigFilter

    def perform_create(self, serializer):
        try:
            instance = serializer.save()
        except IntegrityError as e:
            raise ValidationError({"promotersetsig": str(e)})
        if instance is None:
            raise ValidationError(
                {
                    "promotersetsig": "Could not save PromoterSetSig instance. "
                    "Not sure why. Check logs and contact your admin"
                }
            )

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
            add_genomicfeature_to_file="true",
            rename_metric_cols=False,
            return_cols=["all"],
        )

    @action(detail=False, methods=["post"])
    def rankresponse(self, request, *args, **kwargs):

        # Check if data is a list
        if not isinstance(request.data, list):
            raise ValidationError("Expected a list of dictionaries in the request body.")

        # Iterate over each dictionary in the request.data
        tasks = []
        for item in request.data:
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
                    raise ValidationError(
                        "The value for the 'summarize_by_rank_bin' key must be either 'true' or 'false'"
                    )
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

            # Create Celery tasks for each promoterset_id
            tasks.append(rank_response_task.s(promoterset_ids, expression_ids, **additional_arguments, **kwargs))

        # Create a group of tasks and trigger them
        celery_group_result = group(tasks).apply_async()
        celery_group_result.save()

        # Return the group task ID for tracking
        return Response({"group_task_id": celery_group_result.id}, status=202)

    @action(detail=False, methods=["get"])
    def rankresponse_task_status(self, request, *args, **kwargs):
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
    def rankresponse_get_data(self, request, *args, **kwargs):
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
