from django.db import IntegrityError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import ValidationError

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

    queryset = (
        PromoterSetSig.objects.select_related(
            "uploader",
            "binding",
            "promoter",
            "background",
            "fileformat",
        )
        .prefetch_related("binding__bindingmanualqc")
        .all()
        .order_by("id")
    )
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
