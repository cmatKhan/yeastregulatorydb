import pandas as pd
from django.db import models

from yeastregulatorydb.regulatory_data.models import GenomicFeature
from yeastregulatorydb.regulatory_data.utils import extract_file_from_storage


def add_genomicfeature_to_file(
    record, tmpdir, rename_metric_columns: bool = True, target_id_colname: str = "target_id", return_cols: list = None
):
    """
    Add genomic feature information to a file. Optionally (default) standardize
    the metric columns and return a standard set of columns.

    :param record: The record to extract the file from
    :type record: Any
    :param tmpdir: The temporary directory to extract the file to
    :type tmpdir: str
    :param rename_metric_columns: Whether to rename the metric columns to 'effect' and 'pvalue'.
        Defaults to True.
    :type rename_metric_columns: bool, optional
    :param target_id_colname: The column to use as the target_id. Default is 'target_id'. If
        the column is not present, leave this as 'target_id' and a value of 'none' will
        be set in the values.
    :type target_id: str, optional
    :param return_cols: The columns to return. Default is None, which sets the following:
        ['regulator_id', 'regulator_locus_tag',
        'regulator_symbol', 'target_id', 'target_locus_tag', 'target_symbol',
        'record_id', 'effect', 'pvalue']. Pass in ['all'] to return all columns.
    :type return_cols: list, optional
    :return: A DataFrame with the genomic feature information added
    :rtype: pd.DataFrame

    :raises AttributeError: If the record does not have a 'get_fileformat()' method
    :raises AttributeError: If the record does not have a 'get_genomicfeature()' method
    """
    filepath = extract_file_from_storage(record.file, tmpdir)
    df = pd.read_csv(filepath, compression="gzip")

    if rename_metric_columns:
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

    # If the target_id column is not present, add a dummy column
    if "target_id" not in df.columns:
        df["target_id"] = "none"
    df["target_id"] = df[target_id_colname]
    # Merge the genomic feature information
    genomicfeature_records = GenomicFeature.objects.annotate(
        target_id=models.F("id"),
        target_locus_tag=models.F("locus_tag"),
        target_symbol=models.F("symbol"),
    ).values("target_id", "target_locus_tag", "target_symbol")

    genomicfeature_df = pd.DataFrame.from_records(genomicfeature_records)
    df = df.merge(genomicfeature_df, on="target_id", how="left")

    # Add the record id
    df["record_id"] = record.id

    # Add the regulator information
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

    if return_cols == ["all"]:
        return_cols = df.columns.tolist()
    if return_cols is None:
        return_cols = [
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

    df = df[return_cols]

    return df
