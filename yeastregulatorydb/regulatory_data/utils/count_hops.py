import pandas as pd

from ..models import ChrMap


def count_hops(df: pd.DataFrame, chr_format: str, deduplicate_strands: bool = True) -> dict[str, int]:
    """
    Given a dataframe and a chr_format, get from the ChrMap table
    the corresponding chromosome format and the field `type` which has
    levels `genomic`, `mito` and `plasmid`. Then,
    count how many rows in the dataframe fall into each category.
    Return a dictionary with the counts.

    :param df: dataframe with the data to be counted
    :type df: pd.DataFrame
    :param chr_format: chromosome format
    :type chr_format: str
    :param deduplicate_strands: whether to deduplicate based on `chr`, `start`, `end`
        such that if an insertion occurs at the same coordinate on opposite strands, it
        is counted only once. Note that this should be set to False for the background
        and other combined data
    :type deduplicate_strands: bool

    :return: dictionary with the counts
    :rtype: dict

    :raises RuntimeError: if the dataframe is empty
    :raises RuntimeError: if the dataframe does not have a column `chr`
    """
    if df.empty:
        raise RuntimeError("Dataframe is empty.")

    if "chr" not in df.columns:
        raise RuntimeError("Dataframe does not have a column `chr`.")

    df_internal = df.copy()

    chr_map = ChrMap.objects.values(chr_format, "type")
    chr_map_df = pd.DataFrame.from_records(chr_map)

    df_internal = df_internal.merge(chr_map_df, how="left", left_on="chr", right_on=chr_format)

    if deduplicate_strands:
        # deduplicate based on `chr`, `start`, `end` such that if an insertion occurs
        # at the same coordinate but on opposite strands, only one record is retained
        df_internal.drop_duplicates(subset=["chr", "start", "end"], inplace=True)
        # set strand to '*'
        df_internal["strand"] = "*"

    df_counts = df_internal.groupby("type").size().reset_index(name="counts")

    categories = ["genomic", "mito", "plasmid"]
    for category in categories:
        if category not in df_counts["type"].values:
            df_counts = pd.concat([df_counts, pd.DataFrame([{"type": category, "counts": 0}])], ignore_index=True)

    hops_dict = {row["type"]: row["counts"] for _, row in df_counts.iterrows()}

    return hops_dict
