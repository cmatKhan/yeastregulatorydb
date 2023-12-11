from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from ...models.BindingSource import BindingSource
from ..filters.BindingSourceFilter import BindingSourceFilter
from ..serializers.BindingSourceSerializer import BindingSourceSerializer
from .mixins.UpdateModifiedMixin import UpdateModifiedMixin


class BindingSourceViewSet(UpdateModifiedMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing BindingSource instances.
    """

    queryset = BindingSource.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = BindingSourceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = BindingSourceFilter
