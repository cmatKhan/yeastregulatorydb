from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from ...models.Regulator import Regulator
from ..filters.RegulatorFilter import RegulatorFilter
from ..serializers.RegulatorSerializer import RegulatorSerializer
from .mixins.UpdateModifiedMixin import UpdateModifiedMixin


class RegulatorViewSet(UpdateModifiedMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Regulator instances.
    """

    queryset = Regulator.objects.annotated().all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = RegulatorSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RegulatorFilter
