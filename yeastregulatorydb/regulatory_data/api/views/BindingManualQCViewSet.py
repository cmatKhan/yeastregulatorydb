from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from ...models.BindingManualQC import BindingManualQC
from ..filters.BindingManualQCFilter import BindingManualQCFilter
from ..serializers.BindingManualQCSerializer import BindingManualQCSerializer
from .mixins.UpdateModifiedMixin import UpdateModifiedMixin


class BindingManualQCViewSet(UpdateModifiedMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing BindingManualQC instances.
    """

    queryset = (
        BindingManualQC.objects.select_related(
            "uploader",
            "modifier",
            "binding",
            "binding__regulator",
            "binding__regulator__genomicfeature",
            "binding__source",
            "binding__source__fileformat",
        )
        .all()
        .order_by("-id")
    )

    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = BindingManualQCSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = BindingManualQCFilter
