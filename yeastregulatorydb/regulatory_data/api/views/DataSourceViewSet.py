from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from ...models.DataSource import DataSource
from ..filters.DataSourceFilter import DataSourceFilter
from ..serializers.DataSourceSerializer import DataSourceSerializer
from .mixins.UpdateModifiedMixin import UpdateModifiedMixin


class DataSourceViewSet(UpdateModifiedMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing DataSource instances.
    """

    queryset = DataSource.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = DataSourceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DataSourceFilter
