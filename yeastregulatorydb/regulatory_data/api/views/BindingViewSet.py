from celery import chain
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from ...models.Binding import Binding
from ...tasks import promoter_significance_task, rank_response_tasks
from ..filters import BindingFilter
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
        task_type = None
        if instance.source.name == "chipexo_pugh_allevents":
            task_type = "chipexo_promoter_sig"
        elif instance.source.name == "callingcards":
            task_type = "callingcards_promoter_sig"

        if task_type:
            lock_id = "add_data_lock"
            acquire_lock = lambda: cache.add(lock_id, True, timeout=60 * 60)  # flake8: noqa: E731
            release_lock = lambda: cache.delete(lock_id)  # flake8: noqa: E731

            if acquire_lock():
                try:
                    # Create a chain of tasks
                    task = chain(
                        promoter_significance_task.s(instance.id, self.request.user.id, task_type),
                        rank_response_tasks.s(user_id=self.request.user.id),
                    )
                    task.apply_async()
                finally:
                    release_lock()
