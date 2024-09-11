# pyright: reportMissingImports=false, reportMissingModuleSource=false

import json
import os
import tarfile
import tempfile

import pandas as pd
from celery import group
from celery.result import GroupResult
from django.db import IntegrityError
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from yeastregulatorydb.regulatory_data.models import (
    Expression,
    PromoterSetSig,
)
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

    queryset = (
        PromoterSetSig.objects.select_related(
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
            "single_binding__bindingmanualqc_set",
            "composite_binding__bindings",
            "composite_binding__bindings__bindingmanualqc_set",
            "composite_binding__bindings__source",
            "composite_binding__bindings__regulator",
            "composite_binding__bindings__regulator__genomicfeature",
        )
        .all()
        .order_by("id")
    )

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
            for promoterset_id in promoterset_ids:
                tasks.append(rank_response_task.s(promoterset_ids, expression_ids, **additional_arguments, **kwargs))

        # Create a group of tasks and trigger them
        celery_group_result = group(tasks).apply_async()
        celery_group_result.save()

        # Return the group task ID for tracking
        return Response({"group_task_id": celery_group_result.id}, status=202)

    @action(detail=False, methods=["get"])
    def rankresponse_task_status(self, request, *args, **kwargs):
        group_task_id = request.query_params.get("task_id", None)

        if group_task_id:
            # Retrieve the group result using the group_task_id
            group_result = GroupResult.restore(group_task_id)

            if not group_result:
                return Response({"error": "Invalid group_task_id"}, status=status.HTTP_400_BAD_REQUEST)

            # Check the status of the group of tasks
            if group_result.ready():
                if group_result.failed():
                    # If any task in the group failed, return failure status
                    failed_tasks = [res for res in group_result.results if res.failed()]
                    return Response(
                        {"status": "FAILURE", "error": "One or more tasks failed", "failed_tasks": failed_tasks},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                # When all tasks are successful, combine the results from each task
                with tempfile.TemporaryDirectory() as tmpdir:
                    metadata = {}
                    for result in group_result.results:
                        results_dict = result.result
                        if not isinstance(results_dict, dict):
                            return Response(
                                {"error": "Unexpected result format."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                            )

                        # Combine the results of each task
                        promotersetsig_ids = results_dict.get("promotersetsig_ids")
                        expression_ids = results_dict.get("expression_ids")
                        n_responsive = results_dict.get("n_responsive")
                        total_expression_genes = results_dict.get("total_expression_genes")
                        data = results_dict.get("data")

                        # Add metadata for each result
                        metadata[f"{promotersetsig_ids}_{expression_ids}"] = {
                            "promotersetsig_ids": promotersetsig_ids,
                            "expression_ids": expression_ids,
                            "n_responsive": n_responsive,
                            "total_expression_genes": total_expression_genes,
                        }

                        # Save CSV for each task result
                        csv_filename = f"{promotersetsig_ids}_{expression_ids}.csv.gz"
                        csv_path = os.path.join(tmpdir, csv_filename)

                        # Write the data (DataFrame) to CSV
                        try:
                            pd.DataFrame(data).to_csv(csv_path, compression="gzip", index=False)
                        except Exception as exc:
                            return Response(
                                {"error": f"Error writing CSV file: {str(exc)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            )

                    # Write the metadata to file
                    metadata_path = os.path.join(tmpdir, "metadata.json")
                    with open(metadata_path, "w") as f:
                        json.dump(metadata, f)

                    # Create a tarball of the directory
                    tar_path = os.path.join(tmpdir, "results.tar.gz")
                    with tarfile.open(tar_path, "w:gz") as tar:
                        for result in group_result.results:
                            promotersetsig_ids = result.result.get("promotersetsig_ids")
                            expression_ids = result.result.get("expression_ids")
                            csv_filename = f"{promotersetsig_ids}_{expression_ids}.csv.gz"
                            csv_path = os.path.join(tmpdir, csv_filename)
                            tar.add(csv_path, arcname=os.path.basename(csv_path))
                        tar.add(metadata_path, arcname=os.path.basename(metadata_path))

                    # Return the tarball as a file download
                    with open(tar_path, "rb") as f:
                        tar_content = f.read()

                    response = HttpResponse(tar_content, content_type="application/gzip")
                    response["Content-Disposition"] = f'attachment; filename="rankresponse_{group_task_id}.tar.gz"'
                    return response
            else:
                # If the tasks are not complete, return the current status
                return Response({"status": group_result.state}, status=status.HTTP_200_OK)

        return Response({"error": "You must provide a valid group_task_id."}, status=status.HTTP_400_BAD_REQUEST)

    # results_dict = celery_result.get()

    # with tempfile.TemporaryDirectory() as tmpdir:
    #     metadata = {}
    #     # Write each DataFrame to a compressed CSV file
    #     for expression_id, rr_dict in results_dict.items():
    #         csv_path = f"{tmpdir}/{promotersetsig_id}_{expression_id}.csv.gz"
    #         # the `result` is a dictionary. Convert to DataFrame and write to CSV
    #         try:
    #             data_path = rr_dict.pop("data")
    #         except KeyError:
    #             raise ValidationError(
    #                 "The rank response task did not return "
    #                 "the expected data structure. "
    #                 "Key `data` is missing for expression_id: ",
    #                 expression_id,
    #             )
    #         rr_dict["filename"] = os.path.basename(csv_path)
    #         metadata[expression_id] = rr_dict

    #         # write the csv to file
    #         pd.DataFrame(data_path).to_csv(csv_path, compression="gzip", index=False)

    #     # write the json metadata to file
    #     metadata_path = f"{tmpdir}/metadata.json"
    #     with open(metadata_path, "w") as f:
    #         json.dump(metadata, f)

    #     # Create a tarball of the directory
    #     tar_path = f"{tmpdir}/results.tar.gz"
    #     create_tarball(tmpdir, tar_path)

    #     # Read the tarball into memory (consider streaming for large files)
    #     with open(tar_path, "rb") as f:
    #         tar_content = f.read()

    # # Return the tarball as a download
    # response = HttpResponse(tar_content, content_type="application/gzip")
    # response["Content-Disposition"] = f'attachment; filename="rankresponse_{promotersetsig_id}.tar.gz"'
    # return response
