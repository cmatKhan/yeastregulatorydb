from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from yeastregulatorydb.regulatory_data.api.filters import BindingConcatenatedFilter
from yeastregulatorydb.regulatory_data.api.serializers import BindingConcatenatedSerializer

from ...models import BindingConcatenated
from .mixins import UpdateModifiedMixin


class BindingConcatenatedViewSet(UpdateModifiedMixin, viewsets.ModelViewSet):
    queryset = (
        BindingConcatenated.objects.all()
        .prefetch_related(
            "bindings__regulator",
            "bindings__source",
            "bindings__regulator__genomicfeature",
            "bindings__source__lab",
            "bindings__source__assay",
            "bindings__source__workflow",
            "bindings__bindingmanualqc",
        )
        .select_related(
            "bindings__regulator",
            "bindings__source",
            "bindings__regulator__genomicfeature",
            "bindings__source__lab",
            "bindings__source__assay",
            "bindings__source__workflow",
        )
    )
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = BindingConcatenatedSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = BindingConcatenatedFilter
