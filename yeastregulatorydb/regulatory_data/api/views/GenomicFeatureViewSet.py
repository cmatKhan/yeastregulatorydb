from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ...models.GenomicFeature import GenomicFeature
from ..filters.GenomicFeatureFilter import GenomicFeatureFilter
from ..serializers.GenomicFeatureSerializer import GenomicFeatureSerializer
from .mixins import BulkUploadMixin, ExportTableAsGzipFileMixin, UpdateModifiedMixin


class GenomicFeatureViewSet(UpdateModifiedMixin, BulkUploadMixin, ExportTableAsGzipFileMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing GenomicFeature instances.
    """

    queryset = GenomicFeature.objects.select_related("uploader").all().order_by("id")
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = GenomicFeatureSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = GenomicFeatureFilter

    # the bulk upload mixing provides two additional enpoints. But genomicfeature
    # cannot take the bulk-file-upload endpoint. If a user sends a request to
    # bulk-file-upload, the server will return a 405 response.
    @action(detail=False, methods=["post"], url_path="bulk-file-upload")
    def bulk_file_upload(self, request, *args, **kwargs):
        return Response(
            {"detail": "bulk-file-upload not valid for genomicfeature."}, status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
