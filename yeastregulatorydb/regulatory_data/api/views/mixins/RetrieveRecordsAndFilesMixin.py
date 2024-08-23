import logging
import os
import tempfile

import pandas as pd
from django.http import HttpResponse

from yeastregulatorydb.regulatory_data.utils import (
    create_tarball,
    extract_file_from_storage,
)

from .add_genomicfeature_to_file import add_genomicfeature_to_file

logger = logging.getLogger(__name__)


class RetrieveRecordsAndFilesMixin:
    """
    Mixin to retrieve records as a table and the files in a tar.gz directory.

    Optionally pass in 'add_genomicfeature_to_file' as `true` to add the regulator_id,
    regulator_locus_tag, and regulator_symbol to the file.

    The return is a tar.gz archive with metadata.csv, which are the records, and the
    files as CSVS where their filenames are the `id` from the metadata.csv
    """

    def retrieve_records_and_files(self, request, queryset, **kwargs):
        queryset = self.filter_queryset(queryset)
        # if 'add_genomicfeature_to_file' is in the request, then use that value.
        # if it is not present, check to see if it is in the kwargs. If it is not
        # then default to "false"
        add_genomicfeature_to_file_flag = (
            request.query_params.get(
                "add_genomicfeature_to_file", kwargs.get("add_genomicfeature_to_file", "false")
            ).lower()
            == "true"
        )

        records_df = pd.DataFrame(list(queryset.values()))

        with tempfile.TemporaryDirectory() as tmpdir:
            records_csv_path = os.path.join(tmpdir, "metadata.csv")
            records_df.to_csv(records_csv_path, index=False)

            for record in queryset:
                if record.file:
                    try:
                        dest_file_path = os.path.join(tmpdir, f"{record.id}.csv.gz")
                        if add_genomicfeature_to_file_flag:
                            df = add_genomicfeature_to_file(
                                record,
                                tmpdir,
                                kwargs.get("rename_metric_cols", True),
                                kwargs.get("return_cols", None),
                                effect_colname=request.query_params.get("effect_colname", None),
                                pvalue_colname=request.query_params.get("pvalue_colname", None),
                            )
                            df.to_csv(dest_file_path, compression="gzip", index=False)
                        else:
                            file_path = extract_file_from_storage(record.file, tmpdir)
                            with open(file_path, "rb") as src_file:
                                with open(dest_file_path, "wb") as dest_file:
                                    dest_file.write(src_file.read())
                    except FileExistsError as exc:
                        raise FileExistsError(f"Error extracting file from storage: {record.file.name}. {str(exc)}")
                    except FileNotFoundError as exc:
                        raise FileNotFoundError(f"Error extracting file from storage: {record.file.name}. {str(exc)}")

            tar_path = os.path.join(tmpdir, "results.tar.gz")
            create_tarball(tmpdir, tar_path)

            with open(tar_path, "rb") as f:
                tar_content = f.read()

        response = HttpResponse(tar_content, content_type="application/gzip")
        response["Content-Disposition"] = 'attachment; filename="records_and_files.tar.gz"'
        return response
