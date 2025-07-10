import logging

from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from yeastregulatorydb.regulatory_data.api.filters import BindingConcatenatedFilter
from yeastregulatorydb.regulatory_data.api.serializers import (
    BindingConcatenatedSerializer,
)
from yeastregulatorydb.regulatory_data.models import Binding

from ...models import BindingConcatenated
from .mixins import (
    ExportTableAsGzipFileMixin,
    RetrieveRecordsAndFilesMixin,
    UpdateModifiedMixin,
)

logger = logging.getLogger(__name__)

class BindingConcatenatedViewSet(
    UpdateModifiedMixin, ExportTableAsGzipFileMixin, RetrieveRecordsAndFilesMixin, viewsets.ModelViewSet
):
    queryset = (
        BindingConcatenated.objects.all()
        .select_related("uploader", "regulator", "regulator__genomicfeature", "source")
        .prefetch_related(Prefetch("bindings", queryset=Binding.objects.select_related("regulator", "source")))
    )
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = BindingConcatenatedSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = BindingConcatenatedFilter

    @action(detail=False, methods=["get"])
    def record_table_and_files(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        # if 'add_genomicfeature_to_file' is passed in the request, that value, which
        # must be 'true' or 'false' will be used preferentially to the default value,
        # which is true. This will return a file with the regulator_id, symbol and
        # locus_tag columns
        return self.retrieve_records_and_files(request, queryset, add_genomicfeature_to_file="false")

    def destroy(self, request, *args, **kwargs):
        ids = request.data.get("ids", None)

        if isinstance(ids, list):
            try:
                BindingConcatenated.objects.filter(id__in=ids).delete()
            except Exception as exc:
                return Response(
                    {"error": f"Failed to delete BindingConcatenated instances: {str(exc)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            return Response({"message": "Successfully deleted"}, status=status.HTTP_200_OK)
        else:
            instance = self.get_object()
            # Custom pre-deletion logic
            logger.info(f"Deleting BindingConcatenated with ID {instance.id}")
            self.perform_destroy(instance)
            # Custom post-deletion logic
            return Response({"message": "Successfully deleted"}, status=status.HTTP_200_OK)
