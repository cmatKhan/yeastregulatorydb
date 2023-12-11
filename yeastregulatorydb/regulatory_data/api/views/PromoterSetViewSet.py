from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from ...models.PromoterSet import PromoterSet
from ..filters.PromoterSetFilter import PromoterSetFilter
from ..serializers.PromoterSetSerializer import PromoterSetSerializer
from .mixins.UpdateModifiedMixin import UpdateModifiedMixin


class PromoterSetViewSet(UpdateModifiedMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing PromoterSet instances.
    """

    queryset = PromoterSet.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = PromoterSetSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PromoterSetFilter
