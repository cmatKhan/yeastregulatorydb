from celery import chain
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from ...models import Binding, PromoterSet
from ...tasks import promoter_significance_task, rank_response_tasks
from ..filters.PromoterSetFilter import PromoterSetFilter
from ..serializers.PromoterSetSerializer import PromoterSetSerializer
from .mixins.UpdateModifiedMixin import UpdateModifiedMixin


class PromoterSetViewSet(UpdateModifiedMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing PromoterSet instances.
    """

    queryset = PromoterSet.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = PromoterSetSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PromoterSetFilter


def perform_create(self, serializer):
    instance = serializer.save()

    lock_id = "add_data_lock"
    acquire_lock = lambda: cache.add(lock_id, True, timeout=60 * 60)
    release_lock = lambda: cache.delete(lock_id)

    if acquire_lock():
        try:
            for binding_obj in Binding.objects.all():
                # Call promoter_significance_task and then rank_response_tasks
                task = chain(
                    promoter_significance_task.s(binding_obj.id, self.request.user.id, instance.id),
                    rank_response_tasks.s(user_id=self.request.user.id),
                )
                task.apply_async()
        finally:
            release_lock()
