import logging

import pandas as pd
from django.db import models

from yeastregulatorydb.regulatory_data.models import GenomicFeature
from yeastregulatorydb.regulatory_data.utils import extract_file_from_storage

logger = logging.getLogger(__name__)


def add_genomicfeature_to_file(record, tmpdir, rename_metric_columns: bool = True, return_cols: list = None, **kwargs):
    """
    Add genomic feature information to a file. Optionally (default) standardize
    the metric columns and return a standard set of columns.

    Additional keyword arguments:
        - effect_colname: name of the effect column. Default is to use the
            effect column specified in the associated fileformat record
        - pvalue_colname: name of the pvalue column. Default is the pvalue column
            specified in fileformat

    :param record: The record to extract the file from
    :type record: Any
    :param tmpdir: The temporary directory to extract the file to
    :type tmpdir: str
    :param rename_metric_columns: Whether to rename the metric columns to 'effect' and 'pvalue'.
        Defaults to True.
    :type rename_metric_columns: bool, optional
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

    try:
        fileformat = record.get_fileformat()
    except AttributeError as exc:
        raise AttributeError(
            "Could not find 'get_fileformat()' method on the record. "
            "This method should return a FileFormat instance. "
            "Please report this as an issue to: https://github.com/cmatKhan/yeastregulatorydb/issues"
        ) from exc

    if rename_metric_columns:

        # Rename the effect and pvalue columns. If 'effect_colname' or 'pvalue_colname'
        # are not in kwargs, or are None, use the fileformat specified column
        effect_column = kwargs.get("effect_colname") or fileformat.effect_col
        pval_column = kwargs.get("pvalue_colname") or fileformat.pval_col

        df = df.rename(columns={effect_column: "effect", pval_column: "pvalue"})
        if "effect" not in df.columns:
            df["effect"] = float("NaN")
        if "pvalue" not in df.columns:
            df["pvalue"] = float("NaN")

    # If the target_id column is not present, add a dummy column
    identifier_column = fileformat.feature_identifier_col
    df = df.rename(columns={identifier_column: "target_id"})
    if "target_id" not in df.columns:
        df["target_id"] = "none"
    # Merge the genomic feature information
    genomicfeature_records = GenomicFeature.objects.annotate(
        target_id=models.F("id"),
        target_locus_tag=models.F("locus_tag"),
        target_symbol=models.F("symbol"),
    ).values("target_id", "target_locus_tag", "target_symbol")

    genomicfeature_df = pd.DataFrame.from_records(genomicfeature_records)
    try:
        df = df.merge(genomicfeature_df, on="target_id", how="left")
    except ValueError:
        logger.error(
            f"Could not merge the genomic feature information for record {record.id}. "
            f"Filepath: {filepath}. "
            f"This may be due to the target_id column not being present in the file. "
            f"Please ensure that the file has a column with the target_id values. "
            f"the data: {df.head()} and the genomicfeature_df: {genomicfeature_df.head()}"
        )
        raise

    # Add the record id
    df["record_id"] = record.id

    # Add the regulator information
    try:
        regulator = record.get_regulator()
    except AttributeError as exc:
        raise AttributeError(
            "Could not find 'get_regulator()' method on the record. "
            "This method should return a Regulator instance. "
            "Please report this as an issue to: https://github.com/cmatKhan/yeastregulatorydb/issues"
        ) from exc
    df["regulator_id"] = regulator.id
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
