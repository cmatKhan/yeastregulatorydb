import pandas as pd

from ..models import ChrMap


def count_hops(df: pd.DataFrame, chr_format: str, consider_strand: bool = False) -> dict[str, int]:
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
    :param consider_strand: whether to consider the strand or not. If set to `False`,
     the default, then we sum the depths of records with the same `chr`, `start`, `end`
     coordinates on different strands and report it as a single record. If set to `True`,
     then records with the same `chr`, `start, `end` are considered distinct.
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

    if not consider_strand:
        df_internal = df.groupby(["chr", "start", "end"]).aggregate({"depth": "sum"}).reset_index()

    chr_map = ChrMap.objects.values(chr_format, "type")
    chr_map_df = pd.DataFrame.from_records(chr_map)

    df_internal = (
        df_internal.merge(chr_map_df, how="left", left_on="chr", right_on=chr_format)
        .groupby("type")
        .size()
        .reset_index(name="counts")
    )

    categories = ["genomic", "mito", "plasmid"]
    for category in categories:
        if category not in df_internal["type"].values:
            df_internal = pd.concat([df_internal, pd.DataFrame([{"type": category, "counts": 0}])], ignore_index=True)

    hops_dict = {row["type"]: row["counts"] for _, row in df_internal.iterrows()}

    return hops_dict
