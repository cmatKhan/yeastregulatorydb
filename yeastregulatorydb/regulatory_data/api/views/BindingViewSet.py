from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.db import IntegrityError, transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import ValidationError

from ...models import Binding
from ...tasks import promotersetsig_rankedresponse_chained
from ..filters import BindingFilter
from ..serializers import BindingManualQCSerializer, BindingSerializer, PromoterSetSigSerializer
from .mixins import BulkUploadMixin, ExportTableAsGzipFileMixin, UpdateModifiedMixin


class BindingViewSet(BulkUploadMixin, UpdateModifiedMixin, ExportTableAsGzipFileMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Binding instances.
    """

    queryset = (
        Binding.objects.select_related("uploader", "regulator", "regulator__genomicfeature", "source")
        .all()
        .order_by("-id")
    )
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = BindingSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = BindingFilter

    # note that the hop info are added in the FileFormatMixin in the serializers
    @transaction.atomic
    def perform_create(self, serializer):
        try:
            try:
                instance = serializer.save()
            except IntegrityError as e:
                raise ValidationError({"binding": str(e)})
            if instance is None:
                raise ValidationError(
                    {"binding": "Could not save Binding instance. Not sure why. Check logs and contact your admin"}
                )
            # create a BindingManualQC instance and save to the DB
            bindingmanualqc_data = self.request.data.copy()
            bindingmanualqc_data["binding"] = instance.id
            bindingmanualqc_data["notes"] = bindingmanualqc_data.pop("qc_notes", "none")
            bindingmanualqc_serializer = BindingManualQCSerializer(
                data=bindingmanualqc_data, context={"request": self.request}
            )
            bindingmanualqc_serializer.is_valid(raise_exception=True)
            bindingmanualqc_serializer.save()

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
                try:
                    promotersetsiginstance = promotersetsig_serializer.save()
                except IntegrityError as e:
                    raise ValidationError({"promotersetsig": str(e)})
                # if the promotersetsiginstance was successfully saved, then try
                # to launch a rankresponse task
                lock_id = "add_data_lock"
                acquire_lock = lambda: cache.add(lock_id, True, timeout=60 * 60)  # flake8: noqa: E731
                release_lock = lambda: cache.delete(lock_id)  # flake8: noqa: E731

            # if the source.assay is recognized as one associated with a task,
            # set the promotersetsig_processing attribute
            promotersetsig_format = None
            if instance.source.assay == "chipexo":
                if instance.source.name == "chipexo_pugh_allevents":
                    promotersetsig_format = settings.CHIPEXO_PROMOTER_SIG_FORMAT
            elif instance.source.assay == "callingcards":
                promotersetsig_format = settings.CALLINGCARDS_PROMOTER_SIG_FORMAT

            if promotersetsig_format:
                lock_id = "add_data_lock"
                acquire_lock = lambda: cache.add(lock_id, True, timeout=60 * 60)  # flake8: noqa: E731
                release_lock = lambda: cache.delete(lock_id)  # flake8: noqa: E731

                if acquire_lock():
                    try:
                        if self.request.data.get("testing", False) or self.request.query_params.get("testing", False):
                            promotersetsig_rankedresponse_chained(
                                instance.id, self.request.user.id, promotersetsig_format
                            )
                        else:
                            transaction.on_commit(
                                lambda: promotersetsig_rankedresponse_chained(
                                    instance.id, self.request.user.id, promotersetsig_format
                                )
                            )
                    finally:
                        release_lock()
        except:  # noqa: E722
            # Delete the file of the instance if an exception occurs
            if instance.file and default_storage.exists(instance.file.name):
                default_storage.delete(instance.file.name)

            # Delete the file of the promotersetsiginstance if it exists and an exception occurs
            try:
                if (
                    promotersetsiginstance
                    and promotersetsiginstance.file
                    and default_storage.exists(promotersetsiginstance.file.name)
                ):
                    default_storage.delete(promotersetsiginstance.file.name)
            except UnboundLocalError:
                pass
            except Exception as exc:
                raise ValidationError({"BindingViewSet": str(exc)})

            raise
