import logging
import os
import tempfile

import pandas as pd
from django.db import models
from django.http import FileResponse
from rest_framework.decorators import action

from yeastregulatorydb.regulatory_data.models import GenomicFeature
from yeastregulatorydb.regulatory_data.utils import extract_file_from_storage

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
                # Iterate over the filtered queryset
                filepath = extract_file_from_storage(record.file, tmpdir)
                df = pd.read_csv(filepath, compression="gzip")
                try:
                    fileformat = record.get_fileformat()
                except AttributeError as exc:
                    raise AttributeError(
                        "Could not find 'get_fileformat()' method on the record. "
                        "This method should return a FileFormat instance. "
                        "Please report this as an issue to: https://github.com/cmatKhan/yeastregulatorydb/issues"
                    ) from exc

                effect_column = fileformat.effect_col
                pval_column = fileformat.pval_col
                identifier_column = fileformat.feature_identifier_col

                df = df.rename(
                    columns={effect_column: "effect", pval_column: "pvalue", identifier_column: "target_id"}
                )
                # if there is not a column named "effect", add one with NA values
                # do the same for "pvalue". for identifiers, add "none"
                if "effect" not in df.columns:
                    df["effect"] = float("NaN")
                if "pvalue" not in df.columns:
                    df["pvalue"] = float("NaN")
                if "target_id" not in df.columns:
                    df["target_id"] = "none"
                else:
                    # pull the genomicfeature table with columns `id`, `locus_tag` and `symbol`
                    # rename `locus_tag` to `target_locus_tag` and `symbol` to `target_symbol`
                    genomicfeature_records = GenomicFeature.objects.annotate(
                        target_id=models.F("id"),
                        target_locus_tag=models.F("locus_tag"),
                        target_symbol=models.F("symbol"),
                    ).values("target_id", "target_locus_tag", "target_symbol")

                    # transform the genomicfeature_records into a dataframe
                    genomicfeature_df = pd.DataFrame.from_records(genomicfeature_records)

                    # merge with the dataframe on target_id
                    df = df.merge(genomicfeature_df, on="target_id", how="left")

                df["record_id"] = record.id

                try:
                    regulator = record.get_genomicfeature()
                except AttributeError as exc:
                    raise AttributeError(
                        "Could not find 'get_genomicfeature()' method on the record. "
                        "This method should return a GenomicFeature instance. "
                        "Please report this as an issue to: https://github.com/cmatKhan/yeastregulatorydb/issues"
                    ) from exc
                df["regulator_id"] = regulator.genomicfeature.id
                df["regulator_locus_tag"] = regulator.genomicfeature.locus_tag
                df["regulator_symbol"] = regulator.genomicfeature.symbol

                # select columns
                df = df[
                    [
                        "regulator_id",
                        "regulator_locus_tag",
                        "regulator_symbol",
                        "target_id",
                        "target_locus_tag",
                        "target_symbol",
                        "record_id",
                        "effect",
                        "pvalue",
                    ]
                ]

                df_list.append(df)

        # bind the rows of the dataframes together
        combined_df = pd.concat(df_list, ignore_index=True)

        # return a response with the combined dataframe
        tmpfile = tempfile.NamedTemporaryFile(suffix=".csv.gz", delete=False)
        combined_df.to_csv(tmpfile.name, compression="gzip", index=False)
        tmpfile.close()

        response = FileResponse(open(tmpfile.name, "rb"), content_type="application/gzip")
        response["Content-Disposition"] = "attachment; filename=combined.csv.gz"

        # Delete the file after the response is created
        os.unlink(tmpfile.name)

        return response
