import logging

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from yeastregulatorydb.regulatory_data.tasks import promoter_significance_combined_task

from ...models import BindingManualQC
from ..filters.BindingManualQCFilter import BindingManualQCFilter
from ..serializers.BindingManualQCSerializer import BindingManualQCSerializer
from .mixins import ExportTableAsGzipFileMixin, UpdateModifiedMixin

logger = logging.getLogger(__name__)


class BindingManualQCViewSet(UpdateModifiedMixin, ExportTableAsGzipFileMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing BindingManualQC instances.
    """

    queryset = (
        BindingManualQC.objects.select_related(
            "uploader",
            "modifier",
            "single_binding",
            "single_binding__regulator",
            "single_binding__regulator__genomicfeature",
            "single_binding__source",
            "single_binding__source__fileformat",
            "composite_binding",
            "composite_binding__regulator",
            "composite_binding__regulator__genomicfeature",
            "composite_binding__source",
            "composite_binding__source__fileformat",
        )
        .all()
        .order_by("-id")
    )
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = BindingManualQCSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = BindingManualQCFilter
