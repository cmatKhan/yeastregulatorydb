from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ...models.ExpressionManualQC import ExpressionManualQC
from ..filters.ExpressionManualQCFilter import ExpressionManualQCFilter
from ..serializers.ExpressionManualQCSerializer import ExpressionManualQCSerializer
from .mixins.ExportTableAsGzipFileMixin import ExportTableAsGzipFileMixin
from .mixins.UpdateModifiedMixin import UpdateModifiedMixin


class ExpressionManualQCViewSet(UpdateModifiedMixin, ExportTableAsGzipFileMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing ExpressionManualQC instances.
    """

    queryset = (
        ExpressionManualQC.objects.select_related(
            "uploader",
            "expression",
            "expression__regulator",
            "expression__regulator__genomicfeature",
            "expression__source",
            "expression__source__fileformat",
        )
        .all()
        .order_by("-id")
    )
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ExpressionManualQCSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ExpressionManualQCFilter

    @action(detail=False, methods=["post"], url_path="bulk-update")
    @transaction.atomic
    def bulk_update(self, request, *args, **kwargs):
        """
        Bulk update the records in the ExpressionManualQC table.
        """
        data = request.data.get("data", [])

        if not data:
            return Response({"error": "No data provided for bulk update."}, status=status.HTTP_400_BAD_REQUEST)

        # Perform the bulk update
        for item in data:
            try:
                instance = ExpressionManualQC.objects.get(id=item["id"])
                for attr, value in item.items():
                    if attr != "id":  # Avoid attempting to update the primary key
                        setattr(instance, attr, value)
                instance.full_clean()  # Validate the model instance
                instance.save()
            except ExpressionManualQC.DoesNotExist:
                return Response(
                    {"error": f"ExpressionManualQC with id {item['id']} does not exist."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except DjangoValidationError as exc:
                return Response(
                    {"error": f"Validation error for ExpressionManualQC with id {item['id']}: {str(exc)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response({"message": "Records updated successfully."}, status=status.HTTP_204_NO_CONTENT)
