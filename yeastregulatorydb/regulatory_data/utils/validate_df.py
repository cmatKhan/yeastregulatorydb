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
    Confirm whether a dataframe representing a specific file format is valid.

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
    for colname, expected_type_or_levels in expected_col_dict.items():
        if isinstance(expected_type_or_levels, list):
            if not set(df[colname]).issubset(set(expected_type_or_levels)):
                raise ValueError(f"Column {colname} must be one of {expected_type_or_levels}")
        else:
            # if the expected coltype is a string, try to cast all values to string
            if expected_type_or_levels == str:
                try:
                    df[colname] = df[colname].astype(str)
                except ValueError:
                    raise ValueError(
                        f"Column {colname} is expected to be a str. It is not, "
                        "and could not be cast to str. It's actually of type {df[colname].dtype}. Fix it!"
                    )
            # if the expected coltype is an int, try to cast all values to int
            # raise an error if there are decimal values in an `int` column
            if expected_type_or_levels == int:
                try:
                    if df[colname].apply(float.is_integer).all() == False:
                        raise ValueError(
                            f"Column {colname} is expected to be an int. It contains decimal values or `NaN`. Fix it!"
                        )
                    else:
                        df[colname] = df[colname].astype(int)
                except TypeError:
                    logger.debug("column is expected to be an int and is an int column")
            if not all(isinstance(x, expected_type_or_levels) for x in df[colname]):
                raise ValueError(
                    f"Column {colname} must be of type {str(expected_type_or_levels)}. "
                    f"Currently, it is type {df[colname].dtype}"
                )

    return df
