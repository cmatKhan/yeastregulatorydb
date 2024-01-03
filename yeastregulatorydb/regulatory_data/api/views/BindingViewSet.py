from django.conf import settings
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from ...models.Binding import Binding
from ...tasks import promotersetsig_rankedresponse_chained
from ..filters import BindingFilter
from ..serializers.BindingSerializer import BindingSerializer
from .mixins import BulkUploadMixin, UpdateModifiedMixin


class BindingViewSet(BulkUploadMixin, UpdateModifiedMixin, viewsets.ModelViewSet):
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
        if instance.source.assay == "chipexo":
            if instance.source.name == "chipexo_pugh_allevents":
                task_type = settings.CHIPEXO_PROMOTER_SIG_FORMAT
        elif instance.source.assay == "callingcards":
            task_type = settings.CALLINGCARDS_PROMOTER_SIG_FORMAT

        if task_type:
            # this attribute is added to the returned serialized data
            instance.promotersetsig_processing = True
            lock_id = "add_data_lock"
            acquire_lock = lambda: cache.add(lock_id, True, timeout=60 * 60)  # flake8: noqa: E731
            release_lock = lambda: cache.delete(lock_id)  # flake8: noqa: E731

            if acquire_lock():
                try:
                    promotersetsig_rankedresponse_chained(instance.id, self.request.user.id, task_type)
                finally:
                    release_lock()
