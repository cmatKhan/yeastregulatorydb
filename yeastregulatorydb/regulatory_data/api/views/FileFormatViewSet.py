from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from ...models.FileFormat import FileFormat
from ..filters.FileFormatFilter import FileFormatFilter
from ..serializers.FileFormatSerializer import FileFormatSerializer
from .mixins import ExportTableAsGzipFileMixin, UpdateModifiedMixin


class FileFormatViewSet(UpdateModifiedMixin, ExportTableAsGzipFileMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing FileFormat instances.
    """

    queryset = FileFormat.objects.select_related("uploader").all().order_by("id")
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = FileFormatSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = FileFormatFilter
