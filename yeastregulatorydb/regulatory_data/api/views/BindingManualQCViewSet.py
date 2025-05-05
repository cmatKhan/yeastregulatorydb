import logging

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Case, CharField, Exists, F, OuterRef, Q, Value, When
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from yeastregulatorydb.regulatory_data.tasks import promoter_significance_combined_task

from ...models import DTO, BindingManualQC, PromoterSetSig, RankResponse
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
        .prefetch_related(
            "single_binding__promoter_set_sigs",
            "composite_binding__promoter_set_sigs",
        )
        .annotate(
            has_passing_rankresponse=Exists(
                RankResponse.objects.filter(
                    (
                        ~Q(expression__source__name="mcisaac_oe")  # All sources except mcisaac_oe
                        | (Q(expression__source__name="mcisaac_oe", expression__time=15))  # mcisaac_oe with time=15
                    ),
                    promotersetsig__in=PromoterSetSig.objects.filter(
                        Q(single_binding=OuterRef(OuterRef("single_binding")))
                        | Q(composite_binding=OuterRef(OuterRef("composite_binding")))
                    ),
                    passing=True,
                )
            ),
            has_any_rankresponse=Exists(
                RankResponse.objects.filter(
                    (
                        ~Q(expression__source__name="mcisaac_oe")  # All sources except mcisaac_oe
                        | (Q(expression__source__name="mcisaac_oe", expression__time=15))  # mcisaac_oe with time=15
                    ),
                    promotersetsig__in=PromoterSetSig.objects.filter(
                        Q(single_binding=OuterRef(OuterRef("single_binding")))
                        | Q(composite_binding=OuterRef(OuterRef("composite_binding")))
                    ),
                )
            ),
            has_passing_dto=Exists(
                DTO.objects.filter(
                    (
                        ~Q(expression__source__name="mcisaac_oe")  # All sources except mcisaac_oe
                        | (Q(expression__source__name="mcisaac_oe", expression__time=15))  # mcisaac_oe with time=15
                    ),
                    promotersetsig__in=PromoterSetSig.objects.filter(
                        Q(single_binding=OuterRef(OuterRef("single_binding")))
                        | Q(composite_binding=OuterRef(OuterRef("composite_binding")))
                    ),
                    passing_pvalue=True,
                    passing_fdr=True,
                )
            ),
            has_any_dto=Exists(
                DTO.objects.filter(
                    (
                        ~Q(expression__source__name="mcisaac_oe")  # All sources except mcisaac_oe
                        | (Q(expression__source__name="mcisaac_oe", expression__time=15))  # mcisaac_oe with time=15
                    ),
                    promotersetsig__in=PromoterSetSig.objects.filter(
                        Q(single_binding=OuterRef(OuterRef("single_binding")))
                        | Q(composite_binding=OuterRef(OuterRef("composite_binding")))
                    ),
                )
            ),
        )
        .annotate(
            rank_response_status=Case(
                When(has_passing_rankresponse=True, then=Value("pass")),
                When(has_any_rankresponse=True, then=Value("fail")),
                default=Value("unreviewed"),
                output_field=CharField(),
            ),
            dto_status=Case(
                When(has_passing_dto=True, then=Value("pass")),
                When(has_any_dto=True, then=Value("fail")),
                default=Value("unreviewed"),
                output_field=CharField(),
            ),
        )
        .order_by("-id")
    ).distinct()

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
        updated_records = []
        errors = []
        update_cc_combined_set = set()

        for item in data:
            try:
                instance = BindingManualQC.objects.get(id=item["id"])
            except BindingManualQC.DoesNotExist:
                errors.append(f"BindingManualQC with id {item['id']} does not exist")
                logger.error(f"BindingManualQC with id {item['id']} does not exist")
                continue

            # Handle single_binding and composite_binding
            binding_source = None
            assay = None

            if instance.single_binding:
                binding_source = instance.single_binding.source
                assay = binding_source.assay
            elif instance.composite_binding:
                binding_source = instance.composite_binding.source
                assay = binding_source.assay

            if binding_source and assay == "callingcards" and item.get("data_usable"):
                update_cc_combined_set.add(
                    (
                        (
                            instance.single_binding.regulator.id
                            if instance.single_binding
                            else instance.composite_binding.regulator.id
                        ),
                        binding_source.name,
                        item.get("data_usable", "pass"),
                    )
                )

            try:
                for attr, value in item.items():
                    setattr(instance, attr, value)
                instance.full_clean()  # Validate before saving
                instance.save()
                updated_records.append(instance)
            except DjangoValidationError as exc:
                errors.append(f"Failed to update BindingManualQC with id {item['id']}: {exc}")
                logger.error(f"Failed to update BindingManualQC with id {item['id']}: {exc}")

        if errors:
            raise DRFValidationError({"errors": errors})

        # Launch tasks for the aggregated callingcards data
        for regulator_id, source_name, data_usable in update_cc_combined_set:
            task_arguments = {
                "user_id": self.request.user.id,
                "regulator_id": regulator_id,
                "datasource_name": source_name,
                "output_fileformat": settings.CALLINGCARDS_PROMOTER_SIG_FORMAT,
                "data_usable": data_usable,
            }

            if self.request.data.get("testing", False):
                promoter_significance_combined_task.delay(**task_arguments)
            else:
                logger.info(
                    f"Launching promoter_significance_combined_task for regulator_id={regulator_id}, "
                    f"datasource_name={source_name}, data_usable={data_usable}"
                )
                transaction.on_commit(lambda: promoter_significance_combined_task(**task_arguments))

        return Response(status=status.HTTP_204_NO_CONTENT)
