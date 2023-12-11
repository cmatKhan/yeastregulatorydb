from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from ...models.FileFormat import FileFormat
from ..filters.FileFormatFilter import FileFormatFilter
from ..serializers.FileFormatSerializer import FileFormatSerializer
from .mixins.UpdateModifiedMixin import UpdateModifiedMixin


class FileFormatViewSet(UpdateModifiedMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing FileFormat instances.
    """

    queryset = FileFormat.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = FileFormatSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = FileFormatFilter
