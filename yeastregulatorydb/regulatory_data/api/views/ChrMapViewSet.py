from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from ...models.ChrMap import ChrMap
from ..serializers.ChrMapSerializer import ChrMapSerializer
from .mixins.UpdateModifiedMixin import UpdateModifiedMixin


class ChrMapViewSet(UpdateModifiedMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing ChrMap instances.
    """

    queryset = ChrMap.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ChrMapSerializer
    filter_backends = [DjangoFilterBackend]
