from typing import Dict
import pandas as pd
from ..models import ChrMap


def count_hops(df: pd.DataFrame, chr_format: str) -> Dict[str, int]:
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
    :return: dictionary with the counts
    :rtype: dict
    
    :raises RuntimeError: if the dataframe is empty
    :raises RuntimeError: if the dataframe does not have a column `chr`
    """
    if df.empty:
        raise RuntimeError("Dataframe is empty.")

    if 'chr' not in df.columns:
        raise RuntimeError("Dataframe does not have a column `chr`.")

    chr_map = ChrMap.objects.values(chr_format, 'type')
    chr_map_df = pd.DataFrame.from_records(chr_map)

    df = df.merge(chr_map_df, 
                  how='left', 
                  left_on='chr', 
                  right_on=chr_format)

    df = df.groupby('type').size().reset_index(name='counts')

    categories = ['genomic', 'mito', 'plasmid']
    for category in categories:
        if category not in df['type'].values:
            df = pd.concat(
                [df, pd.DataFrame([{'type': category, 'counts': 0}])], 
                ignore_index=True)

    df.set_index('type', inplace=True)
    hops_dict = df['counts'].to_dict()

    return hops_dict