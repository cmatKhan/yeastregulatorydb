from celery import group
from celery.result import GroupResult
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Case, CharField, F, Value, When
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from yeastregulatorydb.regulatory_data.tasks import dto_task

from ...models import DTO, PromoterSetSig
from ..filters.DTOFilter import DTOFilter
from ..serializers.DTOSerializer import DTOSerializer
from .mixins import ExportTableAsGzipFileMixin, RetrieveRecordsAndFilesMixin, UpdateModifiedMixin


def generate_dto_tasks(user_id: int, request_data: list, **kwargs) -> list:
    """
    Submit DTO tasks for each item in the request data
    """
    # Iterate over each dictionary in the request.data
    tasks = []
    for item in request_data:
        promoterset_id = item.pop("promotersetsig_id")
        if not promoterset_id:
            raise ValidationError("Each dictionary must contain a 'promotersetsig_id' key")

        expression_id = item.pop("expression_id")
        if not expression_id:
            raise ValidationError("Each dictionary must contain an 'expression_id' key")

        # Create Celery tasks for each promoterset_id and expression_id pair. Pass
        # any remaining arguments from `item` through to dto_task. See dto_task()
        # docstring for more information about the expected arguments.
        tasks.append(dto_task.s(user_id, promoterset_id, expression_id, **item))
    return tasks


class DTOViewSet(UpdateModifiedMixin, ExportTableAsGzipFileMixin, RetrieveRecordsAndFilesMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Regulator instances.
    """

    queryset = (
        DTO.objects.order_by("id")
        .select_related(
            "uploader",
            "promotersetsig",
            "expression",
        )
        .annotate(
            binding_source=Case(
                When(
                    promotersetsig__single_binding__isnull=False,
                    then=F("promotersetsig__single_binding__source__name"),
                ),
                When(
                    promotersetsig__composite_binding__isnull=False,
                    then=F("promotersetsig__composite_binding__bindings__source__name"),
                ),
                default=Value(None),
                output_field=CharField(),
            ),
            expression_source=F("expression__source__name"),
            regulator=F("expression__regulator"),
            regulator_symbol=F("expression__regulator__genomicfeature__symbol"),
            regulator_locus_tag=F("expression__regulator__genomicfeature__locus_tag"),
        )
    ).distinct()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = DTOSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DTOFilter

    @action(detail=False, methods=["get"])
    def record_table_and_files(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        # if 'add_genomicfeature_to_file' is passed in the request, that value, which
        # must be 'true' or 'false' will be used preferentially to the default value,
        # which is true. This will return a file with the regulator_id, symbol and
        # locus_tag columns
        return self.retrieve_records_and_files(
            request,
            queryset,
            add_genomicfeature_to_file="false",
            rename_metric_cols=False,
            return_cols=["all"],
        )

    @action(detail=False, methods=["post"], url_path="bulk-update")
    @transaction.atomic
    def bulk_update(self, request, *args, **kwargs):
        """
        Bulk update the records in the DTO table.
        """
        data = request.data.get("data", [])

        if not data:
            return Response({"error": "No data provided for bulk update."}, status=status.HTTP_400_BAD_REQUEST)

        # Perform the bulk update
        for item in data:
            try:
                instance = DTO.objects.get(id=item["id"])
                for attr, value in item.items():
                    if attr != "id":  # Avoid attempting to update the primary key
                        setattr(instance, attr, value)
                instance.full_clean()  # Validate the model instance
                instance.save()
            except DTO.DoesNotExist:
                return Response(
                    {"error": f"DTO with id {item['id']} does not exist."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except DjangoValidationError as exc:
                return Response(
                    {"error": f"Validation error for DTO with id {item['id']}: {str(exc)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response({"message": "Records updated successfully."}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"])
    def submit(self, request, *args, **kwargs):

        # Check if data is a list
        if not isinstance(request.data, list):
            raise ValidationError("Expected a list of dictionaries in the request body.")

        tasks = generate_dto_tasks(self.request.user.id, request.data, **kwargs)

        # Create a group of tasks and trigger them
        celery_group_result = group(tasks).apply_async()
        celery_group_result.save()

        # Return the group task ID for tracking
        return Response({"group_task_id": celery_group_result.id}, status=202)

    @action(detail=False, methods=["get"])
    def status(self, request, *args, **kwargs):
        group_task_id = request.query_params.get("group_task_id", None)

        if not group_task_id:
            return Response({"error": "You must provide a valid group_task_id."}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the group result using the group_task_id
        group_result = GroupResult.restore(group_task_id)

        if not group_result:
            return Response({"error": "Invalid group_task_id"}, status=status.HTTP_400_BAD_REQUEST)

        # Summarize task states by counting the occurrences of each state
        state_counts = {}
        for task in group_result.results:
            state = task.state
            state_counts[state] = state_counts.get(state, 0) + 1

        # Handle not ready tasks
        if not group_result.ready():
            return Response(
                {"status": "IN_PROGRESS", "task_state_summary": state_counts},
                status=status.HTTP_200_OK,
            )

        # Handle failure cases
        if group_result.failed():
            failed_tasks = [res for res in group_result.results if res.failed()]
            return Response(
                {"status": "FAILURE", "error": "One or more tasks failed", "failed_tasks": failed_tasks},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Handle success cases
        if group_result.ready() and not group_result.failed():
            # Extract primary keys from successful tasks
            finished_task_pks = []
            error_tasks = []
            for task in group_result.results:
                if task.successful():
                    task_result = task.result
                    if isinstance(task_result, dict):
                        if "success" in task_result:
                            finished_task_pks.append(task_result["success"])
                        elif "error" in task_result:
                            error_tasks.append({task.id: task_result["error"]})

            return Response(
                {
                    "status": "SUCCESS",
                    "group_task_id": group_task_id,
                    "task_state_summary": state_counts,
                    "success_pks": finished_task_pks,
                    "error_tasks": error_tasks,
                },
                status=status.HTTP_200_OK,
            )

        # Fallback for unknown states
        return Response(
            {"status": "UNKNOWN", "group_task_id": group_task_id},
            status=status.HTTP_202_ACCEPTED,
        )
