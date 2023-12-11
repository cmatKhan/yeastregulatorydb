from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from ...models.CallingCardsBackground import CallingCardsBackground
from ..filters.CallingCardsBackgroundFilter import CallingCardsBackgroundFilter
from ..serializers.CallingCardsBackgroundSerializer import CallingCardsBackgroundSerializer
from .mixins.UpdateModifiedMixin import UpdateModifiedMixin


class CallingCardsBackgroundViewSet(UpdateModifiedMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing CallingCardsBackground instances.
    """

    queryset = CallingCardsBackground.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CallingCardsBackgroundSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CallingCardsBackgroundFilter
