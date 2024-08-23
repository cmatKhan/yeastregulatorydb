import gzip
from io import BytesIO
import logging

import pandas as pd
from django.http import HttpResponse
from rest_framework.decorators import action

logger = logging.getLogger(__name__)


class ExportTableAsGzipFileMixin:
    """
    Mixin to add an 'export' action to a viewset, which exports the queryset as a gzipped CSV file.
    """

    @action(detail=False, methods=["get"])
    def export(self, request):
        # Get the queryset and apply any filters
        queryset = self.filter_queryset(self.get_queryset())

        # Serialize the queryset
        serializer = self.get_serializer(queryset, many=True)
        serialized_data = serializer.data

        # Convert the serialized data to a DataFrame
        df = pd.DataFrame.from_records(serialized_data)

        # Create a CSV string
        csv_data = df.to_csv(index=False)

        # Compress the CSV data using gzip
        gzip_buffer = BytesIO()
        with gzip.GzipFile(fileobj=gzip_buffer, mode="w") as f:
            f.write(csv_data.encode("utf-8"))

        # Create a HttpResponse object with the appropriate CSV header.
        response = HttpResponse(gzip_buffer.getvalue(), content_type="application/gzip")
        response["Content-Disposition"] = f'attachment; filename="{self.queryset.model.__name__}.csv.gz"'

        return response
