import logging

import pandas as pd

from .validate_chr_col import validate_chr_col
from .validate_df import validate_df

logger = logging.getLogger(__name__)


def validate_genomic_df(
    df: pd.DataFrame,
    chr_format: str,
    expected_col_dict: dict = {
        "chr": str,
        "start": int,
        "end": int,
        "name": str,
        "score": float,
        "strand": ["+", "-", "*"],
    },
) -> pd.DataFrame:
    """
    Confirm whether a dataframe storing genomic data is valid. The dataframe
    must have at least the columns `chr`, `start` and `end`. The `chr` column
    must be a subset of the `chr_format` column in the ChrMap table. The
    `start` column must be less than or equal to the `end` column. The
    `expected_col_dict` parameter can be used to specify the expected column
    names and their types.

    :param df: dataframe with the data to be validated
    :type df: pd.DataFrame
    :param chr_format: chromosome format. Must be a field in ChrMap
    :type chr_format: str
    :param expected_col_dict: dictionary with the expected column names and datatypes.
    If a column has expected factor levels, provide a list of those levels.
    Defaults to the BED6 format: {"chr": str, "start": int, "end": int,
        "name": str, "score": float, "strand": ["+", "-", "*"]}
    :type expected_col_dict: dict, optional

    :return: The validated dataframe
    :rtype: pd.DataFrame

    :raises ValueError:
        - if the dataframe does not have the columns `chr`, `start` and `end`
        - if the dataframe does not have all the columns specified in `expected_col_dict`
        - if the `chr` column is not a subset of the `chr_format` column in the ChrMap table
        - if the `start` column is not less than or equal to the `end` column
        - if the `start` or `end` coordinate exceed the chromosome bounds
        - if the columns violate the expected datatypes, given the `expected_col_dict`
    """
    # immediately check if the dataframe has `chr`, `start` and `end` columns
    # all genomic data must have at least this
    if ("chr", "start", "end") not in df.columns:
        raise ValueError("A genomic dataframe must at least have the columns `chr` `start` and `end`")

    # cast the `chr` column to str
    df["chr"] = df["chr"].astype(str)
    # validate the `chr` column against the ChrMap table
    if not validate_chr_col(df, chr_format):
        raise ValueError(
            "the levels of the `chr` column are not a subset of " "the levels of %s in the ChrMap table" % chr_format
        )

    # validate the dataframe given the expected_col_dict
    df = validate_df(df, expected_col_dict)

    return df
