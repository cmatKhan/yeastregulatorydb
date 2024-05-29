# pyright: reportMissingImports=false, reportMissingModuleSource=false
import tempfile

import pandas as pd
from django.db import IntegrityError
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.serializers import ValidationError

from yeastregulatorydb.regulatory_data.models import DataSource, Expression, PromoterSetSig
from yeastregulatorydb.regulatory_data.tasks import rank_response_task
from yeastregulatorydb.regulatory_data.utils.create_tarball import create_tarball

from ..filters.PromoterSetSigFilter import PromoterSetSigFilter
from ..serializers.PromoterSetSigSerializer import PromoterSetSigSerializer
from .mixins import ExportTableAsGzipFileMixin, GetCombinedGenomicFileMixin, UpdateModifiedMixin


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
    viewsets.ModelViewSet,
):
    """
    A viewset for viewing and editing PromoterSetSig instances.
    """

    queryset = (
        PromoterSetSig.objects.select_related(
            "uploader",
            "binding",
            "promoter",
            "background",
            "fileformat",
        )
        .prefetch_related("binding__bindingmanualqc")
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
    def rankresponse(self, request, *args, **kwargs):
        promotersetsig_id = request.query_params.get("promotersetsig_id", None)
        if promotersetsig_id is None:
            raise ValidationError("promotersetsig_id must be provided in the query parameters")
        # validate that the promotersetsig_id exists in the database
        if not PromoterSetSig.objects.filter(id=promotersetsig_id).exists():
            raise ValidationError(f"PromoterSetSig with id {promotersetsig_id} does not exist")

        if request.query_params.get("expression_id", None):
            expression_id = request.query_params.get("expression_id")
            # verify that the expression_id exists in the expression table
            if not Expression.objects.filter(id=expression_id).exists():
                raise ValidationError(f"Expression with id {expression_id} does not exist")
            kwargs["expression_id"] = expression_id

        celery_result = rank_response_task.delay(promotersetsig_id, **kwargs)
        results_dict = celery_result.get()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write each DataFrame to a compressed CSV file
            for expression_id, result in results_dict.items():
                csv_path = f"{tmpdir}/promoter_{promotersetsig_id}_expression_{expression_id}.csv.gz"
                # the `result` is a dictionary. Convert to DataFrame and write to CSV
                pd.DataFrame(result).to_csv(csv_path, compression="gzip", index=False)

            # Create a tarball of the directory
            tar_path = f"{tmpdir}/results.tar.gz"
            create_tarball(tmpdir, tar_path)

            # Read the tarball into memory (consider streaming for large files)
            with open(tar_path, "rb") as f:
                tar_content = f.read()

        # Return the tarball as a download
        response = HttpResponse(tar_content, content_type="application/gzip")
        response["Content-Disposition"] = f'attachment; filename="rankresponse_{promotersetsig_id}.tar.gz"'
        return response
