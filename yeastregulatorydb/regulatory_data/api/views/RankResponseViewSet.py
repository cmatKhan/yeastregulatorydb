import tempfile

import pandas as pd
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ...models import RankResponse
from ...utils.extract_file_from_storage import extract_file_from_storage
from ..filters.RankResponseFilter import RankResponseFilter
from ..serializers.RankResponseSerializer import RankResponseSerializer
from .mixins.UpdateModifiedMixin import UpdateModifiedMixin


class RankResponseViewSet(UpdateModifiedMixin, viewsets.ModelViewSet):
    """
    A viewset for viewing and editing RankResponse instances.
    """

    queryset = (
        RankResponse.objects.select_related(
            "uploader",
        )
        .all()
        .order_by("id")
    )
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = RankResponseSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RankResponseFilter

    @action(detail=False, methods=["get"])
    def summary(self, request, *args, **kwargs):
        if "rank_response_id" not in request.query_params:
            return Response({"error": "rank_response_id must be specified"}, status=status.HTTP_400_BAD_REQUEST)

        filtered_queryset = self.filter_queryset(self.get_queryset())
        if len(filtered_queryset) != 1:
            return Response(
                {
                    "error": "rank_response_summary returned multiple matches to your query. There should only be 1. "
                    "Contact our admin -- this message shouldn't appear -- but in the meantime, "
                    "re-submit with only the `rank_response_id` as a paramater"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        with tempfile.TemporaryDirectory() as tmpdir:
            for rank_response_record in filtered_queryset:
                # Iterate over the filtered queryset
                filepath = extract_file_from_storage(rank_response_record.file, tmpdir)
                df = pd.read_csv(filepath, compression="gzip")

            with tempfile.NamedTemporaryFile(suffix=".gz") as tmpfile:
                df.to_csv(tmpfile.name, compression="gzip", index=False)
                tmpfile.seek(0)
                response = HttpResponse(tmpfile, content_type="application/gzip")
                response["Content-Disposition"] = "attachment; filename=rank_response_summary.csv.gz"
                return response
