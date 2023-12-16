from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from yeastregulatorydb.regulatory_data.tasks.chipexo_pugh_allevents_promoter_sig import (
    chipexo_pugh_allevents_promoter_sig,
)

from ...models.Binding import Binding
from ..filters.BindingFilter import BindingFilter
from ..serializers.BindingSerializer import BindingSerializer
from .mixins.BulkUploadMixin import BulkUploadMixin
from .mixins.UpdateModifiedMixin import UpdateModifiedMixin


class BindingViewSet(UpdateModifiedMixin, viewsets.ModelViewSet, BulkUploadMixin):
    """
    A viewset for viewing and editing Binding instances.
    """

    queryset = Binding.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = BindingSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = BindingFilter

    def perform_create(self, serializer):
        instance = serializer.save()
        if instance.source.name == "chipexo_pugh_allevents":
            chipexo_pugh_allevents_promoter_sig.delay(instance.id, self.request.user.id)
