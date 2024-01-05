from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from yeastregulatorydb.regulatory_data.tasks import rank_response_task

from ...models.PromoterSetSig import PromoterSetSig
from ..filters.PromoterSetSigFilter import PromoterSetSigFilter
from ..serializers.PromoterSetSigSerializer import PromoterSetSigSerializer
from .mixins.UpdateModifiedMixin import UpdateModifiedMixin


class PromoterSetSigViewSet(UpdateModifiedMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing PromoterSetSig instances.
    """

    queryset = PromoterSetSig.objects.all().order_by("id")
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = PromoterSetSigSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PromoterSetSigFilter

    def perform_create(self, serializer):
        instance = serializer.save()

        # Create a chain of tasks for each promotersetsig_id
        lock_id = "add_data_lock"
        acquire_lock = lambda: cache.add(lock_id, True, timeout=60 * 60)
        release_lock = lambda: cache.delete(lock_id)

        if acquire_lock():
            # set this attribute to be returend by the to_ret() method of the
            # serializer
            instance.rankresponse_processing = True
            try:
                rank_response_task.delay(instance.id, self.request.user.id)
            finally:
                release_lock()
