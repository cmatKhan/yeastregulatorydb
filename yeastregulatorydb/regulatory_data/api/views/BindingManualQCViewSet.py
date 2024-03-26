import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from yeastregulatorydb.regulatory_data.tasks import (
    combine_cc_passing_replicates_promotersig_chained,
    combine_cc_passing_replicates_task,
)

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
            "binding",
            "binding__regulator",
            "binding__regulator__genomicfeature",
            "binding__source",
            "binding__source__fileformat",
        )
        .all()
        .order_by("-id")
    )

    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = BindingManualQCSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = BindingManualQCFilter

    def perform_update(self, serializer):
        """
        Modify the default `perform_update` method such that
        """
        updated_fields = serializer.validated_data.keys()
        instance = serializer.save()
        if (
            "data_usable" in updated_fields
            and instance.binding.source.assay == "callingcards"
            and instance.data_usable
        ):
            combine_cc_passing_replicates_task.delay(instance.binding.regulator.id, self.request.user.id)

    @action(detail=False, methods=["post"], url_path="bulk-update")
    def bulk_update(self, request, *args, **kwargs):
        data = request.data.get("data")
        updated_records = []
        errors = []
        update_cc_combined_set = set()

        for item in data:
            instance = BindingManualQC.objects.get(id=item["id"])
            if instance.binding.source.assay == "callingcards" and item.get("data_usable"):
                update_cc_combined_set.add(instance.binding.regulator.id)
            try:
                for attr, value in item.items():
                    setattr(instance, attr, value)
                instance.full_clean()  # This line validates the model instance before saving
                instance.save()
                updated_records.append(instance)
            except BindingManualQC.DoesNotExist:
                errors.append(f"BindingManualQC with id {item['id']} does not exist")
                logger.error(f"BindingManualQC with id {item['id']} does not exist")
            except DjangoValidationError as exc:
                errors.append(f"Failed to update BindingManualQC with id {item['id']}: {exc}")
                logger.error(f"Failed to update BindingManualQC with id {item['id']}: {exc}")

        if errors:
            # return a 400 response with the collected errors
            raise DRFValidationError({"errors": errors})

        # After all records are updated, perform your operation on the set
        for regulator_id in update_cc_combined_set:
            if self.request.data.get("testing", False):
                combine_cc_passing_replicates_promotersig_chained(self.request.user.id, regulator_id=regulator_id)
            else:
                transaction.on_commit(
                    lambda: combine_cc_passing_replicates_promotersig_chained(
                        self.request.user.id, regulator_id=regulator_id
                    )
                )

        return Response(status=status.HTTP_204_NO_CONTENT)
