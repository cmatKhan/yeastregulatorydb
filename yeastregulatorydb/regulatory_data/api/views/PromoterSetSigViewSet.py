from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from ...models.PromoterSetSig import PromoterSetSig
from ..filters.PromoterSetSigFilter import PromoterSetSigFilter
from ..serializers.PromoterSetSigSerializer import PromoterSetSigSerializer
from .mixins.UpdateModifiedMixin import UpdateModifiedMixin


class PromoterSetSigViewSet(UpdateModifiedMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing PromoterSetSig instances.
    """

    queryset = PromoterSetSig.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = PromoterSetSigSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PromoterSetSigFilter
