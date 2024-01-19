import tempfile

import pandas as pd
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import ValidationError

from yeastregulatorydb.regulatory_data.tasks import rank_response_task

from ...models.PromoterSetSig import PromoterSetSig
from ..filters.PromoterSetSigFilter import PromoterSetSigFilter
from ..serializers.PromoterSetSigSerializer import PromoterSetSigSerializer
from .mixins import ExportTableAsGzipFileMixin, GetCombinedGenomicFileMixin, UpdateModifiedMixin


class PromoterSetSigViewSet(
    UpdateModifiedMixin, ExportTableAsGzipFileMixin, GetCombinedGenomicFileMixin, viewsets.ModelViewSet
):
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
        try:
            instance = serializer.save()
        except IntegrityError as e:
            raise ValidationError({"promotersetsig": str(e)})
        if instance is None:
            raise ValidationError(
                {
                    "promotersetsig": "Could not save PromoterSetSig instance. "
                    "Not sure why. Check logs and contact your admin"
                }
            )

        # Create a chain of tasks for each promotersetsig_id
        lock_id = "add_data_lock"
        acquire_lock = lambda: cache.add(lock_id, True, timeout=60 * 60)
        release_lock = lambda: cache.delete(lock_id)

        # if acquire_lock():
        #     try:
        #         if self.request.query_params.get("testing"):
        #             rank_response_task.delay(instance.id, self.request.user.id, testing=True)
        #         else:
        #             transaction.on_commit(lambda: rank_response_task.delay(instance.id, self.request.user.id))
        #     finally:
        #         release_lock()
