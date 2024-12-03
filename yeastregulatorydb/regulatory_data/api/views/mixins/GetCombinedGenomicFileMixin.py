import logging
import os
import tempfile

import pandas as pd
from django.http import FileResponse
from rest_framework.decorators import action

from yeastregulatorydb.regulatory_data.utils import add_genomicfeature_to_file

logger = logging.getLogger(__name__)


class GetCombinedGenomicFileMixin:
    """
    Mixin to add an 'export' action to a viewset, which exports the queryset as a gzipped CSV file.
    """

    @action(detail=False, methods=["get"])
    def combined(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        df_list = []
        with tempfile.TemporaryDirectory() as tmpdir:
            for record in queryset:
                df = add_genomicfeature_to_file(record, tmpdir)
                df_list.append(df)

        combined_df = pd.concat(df_list, ignore_index=True)

        tmpfile = tempfile.NamedTemporaryFile(suffix=".csv.gz", delete=False)
        combined_df.to_csv(tmpfile.name, compression="gzip", index=False)
        tmpfile.close()

        response = FileResponse(open(tmpfile.name, "rb"), content_type="application/gzip")
        response["Content-Disposition"] = "attachment; filename=combined.csv.gz"
        os.unlink(tmpfile.name)

        return response
