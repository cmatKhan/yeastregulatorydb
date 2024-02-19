from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from ...models.GenomicFeature import GenomicFeature
from ..filters.GenomicFeatureFilter import GenomicFeatureFilter
from ..serializers.GenomicFeatureSerializer import GenomicFeatureSerializer
from .mixins import ExportTableAsGzipFileMixin, UpdateModifiedMixin


class GenomicFeatureViewSet(UpdateModifiedMixin, ExportTableAsGzipFileMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing GenomicFeature instances.
    """

    queryset = GenomicFeature.objects.select_related("uploader").all().order_by("id")
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = GenomicFeatureSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = GenomicFeatureFilter
