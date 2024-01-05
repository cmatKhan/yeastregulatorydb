from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from ...models.Binding import Binding
from ...tasks import promotersetsig_rankedresponse_chained, rank_response_task
from ..filters import BindingFilter
from ..serializers import BindingSerializer, PromoterSetSigSerializer
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

    @transaction.atomic
    def perform_create(self, serializer):
        try:
            instance = serializer.save()

            # if the source.name is in the settings NULL_BINDING_FILE_DATASOURCES,
            # then the `file` needs to be added to the promotersetsig table
            # with the FK to the binding instance
            if instance.source.name in settings.NULL_BINDING_FILE_DATASOURCES:
                promotersetsig_serializer = PromoterSetSigSerializer(
                    data={
                        "binding": instance.id,
                        "fileformat": instance.source.fileformat.id,
                        "file": self.request.data.get("file"),
                    },
                    context={"request": self.request},
                )
                promotersetsig_serializer.is_valid(raise_exception=True)
                promotersetsiginstance = promotersetsig_serializer.save()
                # if the promotersetsiginstance was successfully saved, then try
                # to launch a rankresponse task
                lock_id = "add_data_lock"
                acquire_lock = lambda: cache.add(lock_id, True, timeout=60 * 60)  # flake8: noqa: E731
                release_lock = lambda: cache.delete(lock_id)  # flake8: noqa: E731

                if acquire_lock():
                    promotersetsiginstance.rankresponse_processing = True
                    promotersetsiginstance.save()
                    try:
                        rank_response_task.delay(promotersetsiginstance.id, self.request.user.id)
                    finally:
                        release_lock()

            # if the source.assay is recognized as one associated with a task,
            # set the promotersetsig_processing attribute
            promotersetsig_format = None
            if instance.source.assay == "chipexo":
                if instance.source.name == "chipexo_pugh_allevents":
                    promotersetsig_format = settings.CHIPEXO_PROMOTER_SIG_FORMAT
            elif instance.source.assay == "callingcards":
                promotersetsig_format = settings.CALLINGCARDS_PROMOTER_SIG_FORMAT

            if promotersetsig_format:
                # this attribute is added to the returned serialized data
                instance.promotersetsig_processing = True
                lock_id = "add_data_lock"
                acquire_lock = lambda: cache.add(lock_id, True, timeout=60 * 60)  # flake8: noqa: E731
                release_lock = lambda: cache.delete(lock_id)  # flake8: noqa: E731

                if acquire_lock():
                    try:
                        promotersetsig_rankedresponse_chained(instance.id, self.request.user.id, promotersetsig_format)
                    finally:
                        release_lock()
        except:
            # Delete the file of the instance if an exception occurs
            if instance.file and default_storage.exists(instance.file.name):
                default_storage.delete(instance.file.name)

            # Delete the file of the promotersetsiginstance if it exists and an exception occurs
            if (
                promotersetsiginstance
                and promotersetsiginstance.file
                and default_storage.exists(promotersetsiginstance.file.name)
            ):
                default_storage.delete(promotersetsiginstance.file.name)

            raise
