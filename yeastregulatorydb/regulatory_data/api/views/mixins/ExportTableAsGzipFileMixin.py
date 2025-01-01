import gzip
import logging
from io import BytesIO

import pandas as pd
from django.core.cache import cache
from django.db.models import Max
from django.http import HttpResponse
from rest_framework.decorators import action

logger = logging.getLogger(__name__)


class ExportTableAsGzipFileMixin:
    """
    Mixin to add an 'export' action to a viewset, which exports the queryset as a gzipped CSV file.
    """

    @action(detail=False, methods=["get"])
    def export(self, request):
        # Generate a cache key based on the model name
        model_name = self.queryset.model.__name__
        cache_key = f"{model_name}_export_cache"
        last_modified_cache_key = f"{model_name}_last_modified"

        # Check if query params exist (indicating filtered data)
        if not request.query_params:
            # Get the latest modification timestamp of the queryset
            last_modified = self.queryset.aggregate(last_modified=Max("modified_date"))["last_modified"]

            # Check if the cached file is still valid
            cached_last_modified = cache.get(last_modified_cache_key)
            cached_gzip_data = cache.get(cache_key)

            if cached_gzip_data and cached_last_modified == last_modified:
                logger.info("Serving cached export data.")
                response = HttpResponse(cached_gzip_data, content_type="application/gzip")
                response["Content-Disposition"] = f'attachment; filename="{model_name}.csv.gz"'
                return response

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

        # Cache the gzip file and last modified timestamp (only if no filters applied)
        if not request.query_params:
            gzip_data = gzip_buffer.getvalue()
            cache.set(cache_key, gzip_data, timeout=7200)  # Cache for 2 hour
            cache.set(last_modified_cache_key, last_modified, timeout=7200)

        # Create a HttpResponse object with the appropriate CSV header
        logger.info("Serving freshly generated export data.")
        response = HttpResponse(gzip_buffer.getvalue(), content_type="application/gzip")
        response["Content-Disposition"] = f'attachment; filename="{model_name}.csv.gz"'

        return response


# import gzip
# import logging
# from io import BytesIO

# import pandas as pd
# from django.core.cache import cache
# from django.db.models import Max
# from django.http import HttpResponse
# from rest_framework.decorators import action

# logger = logging.getLogger(__name__)


# class ExportTableAsGzipFileMixin:
#     """
#     Mixin to add an 'export' action to a viewset, which exports the queryset as a gzipped CSV file.
#     """

#     @action(detail=False, methods=["get"])
#     def export(self, request):
#         # Generate a cache key based on the model name and filter parameters
#         model_name = self.queryset.model.__name__
#         cache_key = f"{model_name}_export_cache"
#         last_modified_cache_key = f"{model_name}_last_modified"

#         # Get the latest modification timestamp of the queryset
#         last_modified = self.queryset.aggregate(last_modified=Max("modified_date"))["last_modified"]

#         # Check if the cached file is still valid
#         cached_last_modified = cache.get(last_modified_cache_key)
#         cached_gzip_data = cache.get(cache_key)

#         if cached_gzip_data and cached_last_modified == last_modified:
#             logger.info("Serving cached export data.")
#             response = HttpResponse(cached_gzip_data, content_type="application/gzip")
#             response["Content-Disposition"] = f'attachment; filename="{model_name}.csv.gz"'
#             return response

#         # Get the queryset and apply any filters
#         queryset = self.filter_queryset(self.get_queryset())

#         # Serialize the queryset
#         serializer = self.get_serializer(queryset, many=True)
#         serialized_data = serializer.data

#         # Convert the serialized data to a DataFrame
#         df = pd.DataFrame.from_records(serialized_data)

#         # Create a CSV string
#         csv_data = df.to_csv(index=False)

#         # Compress the CSV data using gzip
#         gzip_buffer = BytesIO()
#         with gzip.GzipFile(fileobj=gzip_buffer, mode="w") as f:
#             f.write(csv_data.encode("utf-8"))

#         # Cache the gzip file and last modified timestamp
#         gzip_data = gzip_buffer.getvalue()
#         cache.set(cache_key, gzip_data, timeout=3600)  # Cache for 1 hour
#         cache.set(last_modified_cache_key, last_modified, timeout=3600)

#         # Create a HttpResponse object with the appropriate CSV header
#         logger.info("Serving freshly generated export data.")
#         response = HttpResponse(gzip_data, content_type="application/gzip")
#         response["Content-Disposition"] = f'attachment; filename="{model_name}.csv.gz"'

#         return response
