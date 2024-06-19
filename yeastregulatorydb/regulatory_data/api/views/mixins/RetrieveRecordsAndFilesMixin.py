import os
import tempfile

import pandas as pd
from django.http import HttpResponse

from yeastregulatorydb.regulatory_data.utils.create_tarball import create_tarball


class RetrieveRecordsAndFilesMixin:
    """
    Mixin to retrieve records as a table and the files in a tar.gz directory.
    """

    def retrieve_records_and_files(self, request, queryset):
        # Filter the queryset based on the request filters
        queryset = self.filter_queryset(queryset)

        # Convert queryset to DataFrame
        records_df = pd.DataFrame(list(queryset.values()))

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write records to CSV file
            records_csv_path = os.path.join(tmpdir, "metadata.csv")
            records_df.to_csv(records_csv_path, index=False)

            # Write each file to the directory
            for record in queryset:
                if record.file:
                    file_path = record.file.path
                    if os.path.exists(file_path):
                        dest_file_path = os.path.join(tmpdir, f"{record.id}.csv.gz")
                        with open(file_path, "rb") as src_file:
                            with open(dest_file_path, "wb") as dest_file:
                                dest_file.write(src_file.read())

            # Create a tarball of the directory
            tar_path = os.path.join(tmpdir, "results.tar.gz")
            create_tarball(tmpdir, tar_path)

            # Read the tarball into memory
            with open(tar_path, "rb") as f:
                tar_content = f.read()

        # Return the tarball as a download
        response = HttpResponse(tar_content, content_type="application/gzip")
        response["Content-Disposition"] = 'attachment; filename="records_and_files.tar.gz"'
        return response
