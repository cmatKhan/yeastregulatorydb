from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from yeastregulatorydb.regulatory_data.api.filters import BindingConcatenatedFilter
from yeastregulatorydb.regulatory_data.api.serializers import BindingConcatenatedSerializer
from yeastregulatorydb.regulatory_data.models import Binding

from ...models import BindingConcatenated
from .mixins import UpdateModifiedMixin


class BindingConcatenatedViewSet(UpdateModifiedMixin, viewsets.ModelViewSet):
    queryset = (
        BindingConcatenated.objects.all()
        .select_related("uploader", "regulator", "regulator__genomicfeature", "source")
        .prefetch_related(Prefetch("bindings", queryset=Binding.objects.select_related("regulator", "source")))
    )
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = BindingConcatenatedSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = BindingConcatenatedFilter
