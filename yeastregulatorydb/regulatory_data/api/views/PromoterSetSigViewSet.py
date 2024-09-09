# pyright: reportMissingImports=false, reportMissingModuleSource=false

import json
import os
import tempfile

import pandas as pd
from celery import group
from celery.result import AsyncResult
from django.db import IntegrityError
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from yeastregulatorydb.regulatory_data.models import DataSource, Expression, PromoterSetSig
from yeastregulatorydb.regulatory_data.tasks import rank_response_task
from yeastregulatorydb.regulatory_data.utils.create_tarball import create_tarball

from ..filters.PromoterSetSigFilter import PromoterSetSigFilter
from ..serializers.PromoterSetSigSerializer import PromoterSetSigSerializer
from .mixins import (
    ExportTableAsGzipFileMixin,
    GetCombinedGenomicFileMixin,
    RetrieveRecordsAndFilesMixin,
    UpdateModifiedMixin,
)


def get_expression_data_source(request: Request) -> DataSource:
    """
    Extract the expression data source id using either the query parakmeter `expression_data_source`,
    which should be a string in the data source 'name' field, or expression_data_source_id,
    which is the `id` of a data source entry. If the 'data_source' or data_source_id'
    doesn't find a single record, return an error

    :param request: request object
    :type request: Request
    :return: DataSource instance
    :rtype: DataSource

    :raises ValidationError: If the data source is not found by either the name or id
    """
    data_source_id = request.query_params.get("expression_data_source_id", None)
    data_source = request.query_params.get("expression_data_source", None)
    if data_source_id:
        data_source = DataSource.objects.filter(id=data_source_id)
    elif data_source:
        data_source = DataSource.objects.filter(name=data_source)
    else:
        raise ValidationError(
            "Either expression_data_source_id or expression_data_source must be specified in the query parameters"
        )
    if data_source.count() == 0:
        raise ValidationError("The data source name or id returned no matches to a data source in the database.")
    if data_source.count() > 1:
        raise ValidationError("The data source query returned multiple matches to your query. There should only be 1.")
    return data_source.first()


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

    @action(detail=False, methods=["get"])
    def rankresponse(self, request, *args, **kwargs):
        # Use the existing filter class and queryset from the viewset
        filtered_queryset = self.filter_queryset(self.get_queryset())

        # Check if the filtered queryset is empty
        if not filtered_queryset.exists():
            raise ValidationError("No matching PromoterSetSig records found for the given parameters.")

        # Extract promoterset IDs from the filtered queryset
        promotersetsig_id_list = list(filtered_queryset.values_list("id", flat=True))

        # Handle additional parameters like expression_id
        expression_id = request.query_params.get("expression_id", None)
        if expression_id:
            # Validate expression_id
            if not Expression.objects.filter(id=expression_id).exists():
                raise ValidationError(f"Expression with id {expression_id} does not exist.")
            kwargs["expression_id"] = expression_id

        if request.query_params.get("expression_effect_threshold", None):
            kwargs["expression_effect_threshold"] = request.query_params.get("expression_effect_threshold")

        if request.query_params.get("expression_pvalue_threshold", None):
            kwargs["expression_pvalue_threshold"] = request.query_params.get("expression_pvalue_threshold")

        if request.query_params.get("rank_bin_size", None):
            kwargs["rank_bin_size"] = request.query_params.get("rank_bin_size")

        if request.query_params.get("rank_by_binding_effect", None):
            kwargs["rank_by_binding_effect"] = request.query_params.get("rank_by_binding_effect")

        # celery_result = rank_response_task.delay(promotersetsig_id, **kwargs)
        # results_dict = celery_result.get()

        # Create a group of tasks, one per promotersetsig_id
        tasks = group(
            rank_response_task.s(promotersetsig_id, **kwargs) for promotersetsig_id in promotersetsig_id_list
        )

        # Trigger the group of tasks and get the result
        celery_group_result = tasks.apply_async()

        # Return the group task ID for tracking
        return Response({"group_task_id": celery_group_result.id}, status=202)

    @action(detail=False, methods=["get"])
    def rankresponse_task_status(self, request, *args, **kwargs):
        task_id = request.query_params.get("task_id", None)

        if task_id:
            result = AsyncResult(task_id)

            if result.state == "PENDING":
                return Response({"status": "PENDING"}, status=status.HTTP_200_OK)
            elif result.state == "STARTED":
                return Response({"status": "STARTED"}, status=status.HTTP_200_OK)
            elif result.state == "FAILURE":
                return Response(
                    {"status": "FAILURE", "error": str(result.result)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            elif result.state == "SUCCESS":
                # When the task is done, process the results and create the tarball
                results_dict = result.result
                if not isinstance(results_dict, dict):
                    return Response(
                        {"error": "Unexpected result format."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

                with tempfile.TemporaryDirectory() as tmpdir:
                    metadata = {}
                    for expression_id, rr_dict in results_dict.items():
                        promotersetsig_id = rr_dict.get("promotersetsig_id")
                        csv_path = f"{tmpdir}/{promotersetsig_id}_{expression_id}.csv.gz"
                        try:
                            data_path = rr_dict.pop("data")
                        except KeyError:
                            raise ValidationError(f"Key `data` is missing for expression_id: {expression_id}")
                        rr_dict["filename"] = os.path.basename(csv_path)
                        metadata[expression_id] = rr_dict

                        # Write the DataFrame to CSV
                        try:
                            pd.DataFrame(data_path).to_csv(csv_path, compression="gzip", index=False)
                        except ValidationError as exc:
                            return Response(
                                {"error": f"Error writing CSV file for expression_id: {expression_id}. {str(exc)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            )

                    # Write the metadata to file
                    metadata_path = f"{tmpdir}/metadata.json"
                    with open(metadata_path, "w") as f:
                        json.dump(metadata, f)

                    # Create a tarball of the directory
                    tar_path = f"{tmpdir}/results.tar.gz"
                    create_tarball(tmpdir, tar_path)

                    # Return the tarball as a file download
                    with open(tar_path, "rb") as f:
                        tar_content = f.read()

                    response = HttpResponse(tar_content, content_type="application/gzip")
                    response["Content-Disposition"] = f'attachment; filename="rankresponse_{task_id}.tar.gz"'
                    return response

        return Response({"error": "You must provide a valid task_id."}, status=status.HTTP_400_BAD_REQUEST)

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
