from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from ...models import Expression, PromoterSetSig
from ...tasks import rank_response_task
from ..filters import ExpressionFilter
from ..serializers import ExpressionSerializer
from .mixins.BulkUploadMixin import BulkUploadMixin
from .mixins.UpdateModifiedMixin import UpdateModifiedMixin


class ExpressionViewSet(UpdateModifiedMixin, viewsets.ModelViewSet, BulkUploadMixin):
    """
    A viewset for viewing and editing Expression instances.
    """

    queryset = Expression.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ExpressionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ExpressionFilter

    def perform_create(self, serializer):
        instance = serializer.save()
        promotersetsig_id_list = PromoterSetSig.objects.filter(
            binding__regulator__id=instance.regulator.id
        ).values_list("id", flat=True)

        # Create a chain of tasks for each promotersetsig_id
        lock_id = "add_data_lock"
        acquire_lock = lambda: cache.add(lock_id, True, timeout=60 * 60)  # flake8: noqa: E731
        release_lock = lambda: cache.delete(lock_id)  # flake8: noqa: E731

        if acquire_lock():
            try:
                # Create a chain of tasks
                for promotersetsig_id in promotersetsig_id_list:
                    rank_response_task.apply_async(args=[promotersetsig_id, self.request.user.id])
            finally:
                release_lock()
