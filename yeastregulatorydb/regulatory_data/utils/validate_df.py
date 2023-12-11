import logging

import pandas as pd

logger = logging.getLogger(__name__)


def validate_df(
    df: pd.DataFrame,
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
    Confirm whether a dataframe representing a specific filetype is valid.

    :param df: dataframe with the data to be validated
    :type df: pd.DataFrame
    :param expected_col_dict: dictionary with the expected column names and datatypes.
    If a column has expected factor levels, provide a list of those levels.
    Defaults to the BED6 format: {"chr": str, "start": int, "end": int,
        "name": str, "score": float, "strand": ["+", "-", "*"]}
    :type expected_col_dict: dict, optional

    :return: The validated dataframe
    :rtype: pd.DataFrame

    :raises ValueError:
        - if the dataframe does not have all the columns specified in `expected_col_dict`
        - if the columns violate the expected datatypes, given the `expected_col_dict`
    """
    for colname, data in expected_col_dict.items():
        if isinstance(data, list):
            if not set(df[colname]).issubset(set(data)):
                raise ValueError(f"Column {colname} must be one of {data}")
        else:
            if not pd.api.types.is_dtype_equal(df[colname], data):
                raise ValueError(f"Column {colname} must be of type {data}")

    return df
