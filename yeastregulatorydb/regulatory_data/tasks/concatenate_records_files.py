import gzip
import os

import pandas as pd
from celery import shared_task

from yeastregulatorydb.regulatory_data.utils.extract_file_from_storage import (
    extract_file_from_storage,  # Your provided function
)


@shared_task
def concatenate_rankresponse_files(queryset_data, output_dir):
    """
    Task to concatenate RankResponse files with appended ID columns.

    :param queryset_data: List of dictionaries containing `id` and `file_path` for RankResponse objects.
    :param output_dir: Directory to save the concatenated output file.
    :return: Path to the concatenated gzip file.
    """
    dataframes = []
    for item in queryset_data:
        rankresponse_id = item["id"]
        file_path = item["file_path"]

        # Read the file into a DataFrame and append the ID column
        df = pd.read_csv(file_path, compression="gzip", sep="\t")
        df["rankresponse_id"] = rankresponse_id
        dataframes.append(df)

    # Concatenate all DataFrames
    concatenated_df = pd.concat(dataframes, ignore_index=True)

    # Save to a temporary file
    output_file_path = os.path.join(output_dir, "concatenated_data.gz")
    with gzip.open(output_file_path, "wt") as gz_file:
        concatenated_df.to_csv(gz_file, sep="\t", index=False)

    return output_file_path
