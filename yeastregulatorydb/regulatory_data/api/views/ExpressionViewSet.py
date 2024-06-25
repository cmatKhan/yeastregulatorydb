from django.core.files.storage import default_storage
from django.db import IntegrityError, transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import ValidationError

from ...models import Expression
from ..filters import ExpressionFilter
from ..serializers import ExpressionManualQCSerializer, ExpressionSerializer
from .mixins import (
    BulkUploadMixin,
    ExportTableAsGzipFileMixin,
    GetCombinedGenomicFileMixin,
    RetrieveRecordsAndFilesMixin,
    UpdateModifiedMixin,
)


class ExpressionViewSet(
    BulkUploadMixin,
    UpdateModifiedMixin,
    ExportTableAsGzipFileMixin,
    GetCombinedGenomicFileMixin,
    RetrieveRecordsAndFilesMixin,
    viewsets.ModelViewSet,
):
    """
    A viewset for viewing and editing Expression instances.
    """

    queryset = (
        Expression.objects.select_related(
            "uploader", "regulator", "regulator__genomicfeature", "source", "source__fileformat"
        )
        .all()
        .order_by("-id")
    )
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ExpressionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ExpressionFilter

    @action(detail=False, methods=["get"])
    def record_table_and_files(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        # if 'add_genomicfeature_to_file' is passed in the request, that value, which
        # must be 'true' or 'false' will be used preferentially to the default value,
        # which is true. This will return a file with the regulator_id, symbol and
        # locus_tag columns
        return self.retrieve_records_and_files(request, queryset, add_genomicfeature_to_file="true")

    @transaction.atomic
    def perform_create(self, serializer):
        try:
            try:
                instance = serializer.save()
            except IntegrityError as e:
                raise ValidationError({"expression": str(e)})
            if instance is None:
                raise ValidationError(
                    {
                        "expression": "Could not save Expression instance. "
                        "Not sure why. Check logs and contact your admin"
                    }
                )
            # create a manual QC instance and save to the DB
            expressionmanualqc_serializer = ExpressionManualQCSerializer(
                data={"expression": instance.id}, context={"request": self.request}
            )
            expressionmanualqc_serializer.is_valid(raise_exception=True)
            try:
                expressionmanualqc_serializer.save()
            except IntegrityError as e:
                ValidationError({"expression": str(e)})

        except:  # noqa: E722
            # Delete the file of the instance if an exception occurs
            if instance.file and default_storage.exists(instance.file.name):
                default_storage.delete(instance.file.name)

            raise
