from django.core.cache import cache
from django.core.files.storage import default_storage
from django.db import IntegrityError, transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import ValidationError

from ...models import Expression, PromoterSetSig
from ...tasks import rank_response_tasks
from ..filters import ExpressionFilter
from ..serializers import ExpressionManualQCSerializer, ExpressionSerializer
from .mixins import BulkUploadMixin, ExportTableAsGzipFileMixin, GetCombinedGenomicFileMixin, UpdateModifiedMixin


class ExpressionViewSet(
    BulkUploadMixin,
    UpdateModifiedMixin,
    ExportTableAsGzipFileMixin,
    GetCombinedGenomicFileMixin,
    viewsets.ModelViewSet,
):
    """
    A viewset for viewing and editing Expression instances.
    """

    queryset = Expression.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ExpressionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ExpressionFilter

    @transaction.atomic
    def perform_create(self, serializer):
        try:
            try:
                instance = serializer.save()
            except IntegrityError as e:
                raise ValidationError({"expression": str(e)})
            if instance is None:
                raise ValidationError(
                    {
                        "expression": "Could not save Expression instance. "
                        "Not sure why. Check logs and contact your admin"
                    }
                )
            # create a manual QC instance and save to the DB
            expressionmanualqc_serializer = ExpressionManualQCSerializer(
                data={"expression": instance.id}, context={"request": self.request}
            )
            expressionmanualqc_serializer.is_valid(raise_exception=True)
            try:
                expressionmanualqc_instance = expressionmanualqc_serializer.save()
            except IntegrityError as e:
                ValidationError({"expression": str(e)})

            # Create a chain of tasks for each promotersetsig_id
        #     lock_id = "add_data_lock"
        #     acquire_lock = lambda: cache.add(lock_id, True, timeout=60 * 60)  # flake8: noqa: E731
        #     release_lock = lambda: cache.delete(lock_id)  # flake8: noqa: E731

        #     if acquire_lock():
        #         promotersetsig_id_list = list(
        #             PromoterSetSig.objects.filter(binding__regulator__id=instance.regulator.id).values_list(
        #                 "id", flat=True
        #             )
        #         )

        #         if promotersetsig_id_list:
        #             try:
        #                 if self.request.query_params.get("testing"):
        #                     rank_response_tasks.delay(
        #                         promotersetsig_id_list, self.request.user.id, expression_id=instance.id
        #                     )
        #                 else:
        #                     transaction.on_commit(
        #                         lambda: rank_response_tasks.delay(
        #                             promotersetsig_id_list, self.request.user.id, expression_id=instance.id
        #                         )
        #                     )
        #             finally:
        #                 release_lock()
        #         else:
        #             release_lock()
        except:
            # Delete the file of the instance if an exception occurs
            if instance.file and default_storage.exists(instance.file.name):
                default_storage.delete(instance.file.name)

            raise
