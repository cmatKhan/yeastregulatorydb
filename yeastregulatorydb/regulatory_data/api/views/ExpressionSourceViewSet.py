from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from ...models.ExpressionSource import ExpressionSource
from ..filters.ExpressionSourceFilter import ExpressionSourceFilter
from ..serializers.ExpressionSourceSerializer import ExpressionSourceSerializer
from .mixins.UpdateModifiedMixin import UpdateModifiedMixin


class ExpressionSourceViewSet(UpdateModifiedMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing ExpressionSource instances.
    """

    queryset = ExpressionSource.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ExpressionSourceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ExpressionSourceFilter
