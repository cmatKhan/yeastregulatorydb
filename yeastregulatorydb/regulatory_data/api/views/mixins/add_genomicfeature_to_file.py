import pandas as pd
from django.db import models

from yeastregulatorydb.regulatory_data.models import GenomicFeature
from yeastregulatorydb.regulatory_data.utils import extract_file_from_storage


def add_genomicfeature_to_file(record, tmpdir):
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

    df = df.rename(columns={effect_column: "effect", pval_column: "pvalue", identifier_column: "target_id"})
    if "effect" not in df.columns:
        df["effect"] = float("NaN")
    if "pvalue" not in df.columns:
        df["pvalue"] = float("NaN")
    if "target_id" not in df.columns:
        df["target_id"] = "none"
    else:
        genomicfeature_records = GenomicFeature.objects.annotate(
            target_id=models.F("id"),
            target_locus_tag=models.F("locus_tag"),
            target_symbol=models.F("symbol"),
        ).values("target_id", "target_locus_tag", "target_symbol")

        genomicfeature_df = pd.DataFrame.from_records(genomicfeature_records)
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

    return df
