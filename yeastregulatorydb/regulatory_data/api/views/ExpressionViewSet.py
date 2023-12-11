from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from ...models.Expression import Expression
from ..filters.ExpressionFilter import ExpressionFilter
from ..serializers.ExpressionSerializer import ExpressionSerializer
from .mixins.UpdateModifiedMixin import UpdateModifiedMixin


class ExpressionViewSet(UpdateModifiedMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Expression instances.
    """

    queryset = Expression.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ExpressionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ExpressionFilter
