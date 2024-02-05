from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from ...models.ExpressionManualQC import ExpressionManualQC
from ..filters.ExpressionManualQCFilter import ExpressionManualQCFilter
from ..serializers.ExpressionManualQCSerializer import ExpressionManualQCSerializer
from .mixins.UpdateModifiedMixin import UpdateModifiedMixin


class ExpressionManualQCViewSet(UpdateModifiedMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing ExpressionManualQC instances.
    """

    queryset = ExpressionManualQC.objects.select_related(
        "uploader",
        "expression",
        "expression__regulator",
        "expression__regulator__genomicfeature",
        "expression__source",
        "expression__source__fileformat",
    ).all().order_by("-id")
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ExpressionManualQCSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ExpressionManualQCFilter
