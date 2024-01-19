import pandas as pd
from django.http import HttpResponse
from rest_framework.decorators import action


class ExportTableAsGzipFileMixin:
    """
    Mixin to add an 'export' action to a viewset, which exports the queryset as a gzipped CSV file.
    """

    @action(detail=False, methods=["get"])
    def export(self, request):
        # Get the queryset and apply any filters
        queryset = self.filter_queryset(self.get_queryset())

        # Convert the filtered queryset to a DataFrame
        df = pd.DataFrame.from_records(queryset.values())

        # Create a HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{self.queryset.model.__name__}.csv.gz"'

        # Write the DataFrame to a CSV string and compress it
        csv_data = df.to_csv(index=False, compression="gzip")

        # Set the compressed CSV data as the content of the response
        response.content = csv_data

        return response
