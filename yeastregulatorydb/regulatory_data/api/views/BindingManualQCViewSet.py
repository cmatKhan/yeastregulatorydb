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

    def perform_update(self, serializer):
        """
        Modify the default `perform_update` method such that

        Note that the user can choose how to aggregate the data from the request
        with "aggregation_criteria". Right now defaults to `pass` -- only aggregate
        the passing replicates.
        """

        instance = serializer.save()
        updated_fields = serializer.validated_data.keys()
        data_usable_updated = "data_usable" in updated_fields and instance.data_usable

        if instance.single_binding and instance.single_binding.source.assay == "callingcards" and data_usable_updated:
            promoter_significance_combined_task.delay(
                user_id=self.request.user.id,
                regulator_id=instance.single_binding.regulator.id,
                datasource_name=instance.single_binding.source.name,
                output_fileformat=settings.CALLINGCARDS_PROMOTER_SIG_FORMAT,
                data_usable=self.request.data.get("aggregation_criteria", "pass"),
            )

        return instance

    @action(detail=False, methods=["post"], url_path="bulk-update")
    @transaction.atomic
    def bulk_update(self, request, *args, **kwargs):
        data = request.data.get("data")
        # collect errors and updated records to report as a Response after all
        # items have been processed
        updated_records = []
        errors = []
        # Create a set to store the regulator_id, source_name, and data_usable for callingcards data
        # data_usable is set to "pass" by default to only aggregate the passing replicates.
        # This is parameterized through the request.data, though, so the option is
        # exposed to the user
        update_cc_combined_set = set()

        for item in data:
            instance = BindingManualQC.objects.get(id=item["id"])
            if instance.single_binding.source.assay == "callingcards" and item.get("data_usable"):
                # TODO defaulting to data_usable pass is really questionable. Presumably
                # if item.get("data_usable") is not None, then the default doesn't
                # matter. But, possibly consider checking that it is valid and raising
                # an error if not.
                update_cc_combined_set.add(
                    (
                        instance.single_binding.regulator.id,
                        instance.single_binding.source.name,
                        item.get("data_usable", "pass"),
                    )
                )
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
        for regulator_id, source_name, data_usable in update_cc_combined_set:
            if self.request.data.get("testing", False):
                promoter_significance_combined_task.delay(
                    user_id=self.request.user.id,
                    regulator_id=regulator_id,
                    datasource_name=source_name,
                    output_fileformat=settings.CALLINGCARDS_PROMOTER_SIG_FORMAT,
                    data_usable=data_usable,
                )
            else:
                logger.info(
                    f"Launching promoter_significance_combined_task for regulator_id={regulator_id}, "
                    f"datasource_name={source_name}, data_usable={data_usable}"
                )
                transaction.on_commit(
                    lambda: promoter_significance_combined_task(
                        user_id=self.request.user.id,
                        regulator_id=regulator_id,
                        datasource_name=source_name,
                        output_fileformat=settings.CALLINGCARDS_PROMOTER_SIG_FORMAT,
                        data_usable=data_usable,
                    )
                )

        return Response(status=status.HTTP_204_NO_CONTENT)
