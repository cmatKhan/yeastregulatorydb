from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from ...models.Binding import Binding
from ..filters.BindingFilter import BindingFilter
from ..serializers.BindingSerializer import BindingSerializer
from .mixins.UpdateModifiedMixin import UpdateModifiedMixin


class BindingViewSet(UpdateModifiedMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Binding instances.
    """

    queryset = Binding.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = BindingSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = BindingFilter
