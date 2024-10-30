from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from ...models.RankResponse import RankResponse
from ..filters.RankResponseFilter import RankResponseFilter
from ..serializers.RankResponseSerializer import RankResponseSerializer
from .mixins import ExportTableAsGzipFileMixin, UpdateModifiedMixin


class RankResponseViewSet(UpdateModifiedMixin, ExportTableAsGzipFileMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Regulator instances.
    """

    queryset = RankResponse.objects.all().order_by("id")
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = RankResponseSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RankResponseFilter
