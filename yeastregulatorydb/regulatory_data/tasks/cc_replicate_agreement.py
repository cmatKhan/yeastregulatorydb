import logging
import os
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List

import numpy as np
import pandas as pd

from config import celery_app
from yeastregulatorydb.regulatory_data.models import PromoterSetSig
from yeastregulatorydb.regulatory_data.utils.extract_file_from_storage import (
    extract_file_from_storage,
)

logger = logging.getLogger(__name__)


def calculate_spearman_corr(data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the Spearman correlation matrix between samples.
    """
    try:
        if isinstance(data, np.ndarray):
            data = pd.DataFrame(data)

        spearman_corr_matrix = data.corr(method="spearman")
        return spearman_corr_matrix

    except Exception as e:
        logger.error(f"Error calculating Spearman correlation: {e}")
        return None


def calculate_log_manhattan_outliers(data: pd.DataFrame, log_base: int = 10) -> pd.Series:
    """
    Calculate log-transformed Manhattan distances for each sample from the median rank,
    used to detect outliers by quantifying how much each sample deviates from
    the "typical" behavior.

    The function performs the following steps:

    1. **Rank the Genes**:
        - For each sample (column), the genes (rows) are ranked using average
          ranking in case of ties.
        - Ranking is done column-wise to preserve the relative order of genes
          within each sample.

    2. **Log Transformation**:
        - The ranks are log-transformed to emphasize differences among high-ranked
          genes and compress differences among lower-ranked genes.
        - The log transformation is done using the provided base
          (default is base-10 logarithm).
        - The formula for log transformation is:
          \[
          \text{log\_ranks} = \frac{\log(\text{ranks})}{\log(\text{log\_base})}
          \]
        - This transformation makes subtle differences in higher ranks more
          prominent, while de-emphasizing differences among lower-ranked genes.

    3. **Calculate Median of Log-Transformed Ranks**:
        - For each gene (row), the median rank across all samples is calculated
          from the log-transformed ranks.
        - This median serves as a **centroid** that represents the "typical" rank
          behavior for each gene across all samples.

    4. **Calculate Absolute Deviations**:
        - The absolute deviations between each sample's log-transformed ranks and
          the median log rank are computed.
        - For each gene in each sample, the absolute deviation is calculated as:
          \[
          \text{abs\_deviation} = |\text{log\_rank(sample)} - \text{median\_log\_rank}|
          \]
        - This quantifies how much each sample deviates from the typical rank for
          that gene.

    5. **Calculate Manhattan Distance**:
        - For each sample, the total Manhattan distance is calculated by summing
          the absolute deviations for all genes:
          \[
          \text{total\_manhattan\_distance} = \sum \text{abs\_deviation}
          \]
        - This gives a single value representing how far a sample deviates from
          the median rank behavior across all genes.

    :param data: Input data as a pandas DataFrame where rows are genes and columns are samples.
    :param log_base: Base for the logarithm transformation (default is 10).

    :return: Series of Manhattan distances for each sample.

    :raises ValueError: If the input data is not a pandas DataFrame.
    """
    if not isinstance(data, pd.DataFrame):
        raise ValueError("Input data must be a pandas DataFrame")
    try:
        # Rank the genes for each sample
        ranks = data.rank(axis=0, method="average")

        # Apply log transformation to the ranks to emphasize differences in high ranks
        log_ranks = np.log(ranks) / np.log(log_base)

        # Calculate the median of the log-transformed ranks (this serves as the centroid)
        median_log_ranks = log_ranks.median(axis=1)

        # Calculate the absolute deviations from the median (log-transformed ranks)
        absolute_deviation_log_ranks = log_ranks.sub(median_log_ranks, axis=0).abs()

        # Sum the absolute deviations to calculate the Manhattan distance for each sample
        total_manhattan_distances = absolute_deviation_log_ranks.sum(axis=0)

        return total_manhattan_distances

    except Exception as e:
        logger.error(f"Error calculating log-transformed Manhattan outliers: {e}")
        return None


# add RLE calculation

#


# Main function to compute all metrics in parallel
def calculate_metrics(data: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    For callingcards replicates, calculate all metrics
    (Spearman, Kendall's W, PCA, and MAD) in parallel using available CPUs.
    """

    metrics = {"spearman_corr": calculate_spearman_corr, "log_manhattan_dist": calculate_log_manhattan_outliers}

    results_dict = {}

    # Use ProcessPoolExecutor to calculate in parallel
    with ProcessPoolExecutor() as executor:
        # Submit each metric function to the executor
        future_to_metric = {executor.submit(func, data): metric_name for metric_name, func in metrics.items()}

        # Collect the results as they complete
        for future in as_completed(future_to_metric):
            metric_name = future_to_metric[future]
            try:
                result = future.result()
                results_dict[metric_name] = result
            except Exception as e:
                logger.error(f"Error calculating {metric_name}: {e}")
                results_dict[metric_name] = None

    return results_dict


@celery_app.task(serializer="json")
def cc_replicate_agreement(promotersetsig_ids: List[int]) -> dict:
    """
    :param promotersetsig_ids: List of PromoterSetSig object ids

    :return: Dictionary of metric names and their results

    :raises ValueError: If the PromoterSetSig objects do not have the same regulator,
        or the assay is not callingcards
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        filepaths = {}
        regulator_symbol = set()
        assay = set()
        feature_col = set()
        effect_col = set()
        pval_col = set()

        tmpdir_promotersetsig = os.path.join(tmpdir, "promotersetsig")
        os.makedirs(tmpdir_promotersetsig, exist_ok=True)

        for promotersetsig_id in promotersetsig_ids:
            promotersetsig_record = PromoterSetSig.objects.get(id=promotersetsig_id)

            regulator_symbol.add(promotersetsig_record.get_genomicfeature().symbol)
            if len(regulator_symbol) > 1:
                raise ValueError("All PromoterSetSig objects must have the same regulator")

            assay.add(promotersetsig_record.get_assay())
            if len(assay) > 1:
                raise ValueError("All PromoterSetSig objects must have the same assay")
            if assay - {"callingcards"}:
                raise ValueError("Assay must be callingcards")

            feature_col.add(promotersetsig_record.fileformat.feature_identifier_col)
            if len(feature_col) > 1:
                raise ValueError("All PromoterSetSig objects must have the same feature column")
            effect_col.add(promotersetsig_record.fileformat.effect_col)
            if len(effect_col) > 1:
                raise ValueError("All PromoterSetSig objects must have the same effect column")
            pval_col.add(promotersetsig_record.fileformat.pval_col)
            if len(pval_col) > 1:
                raise ValueError("All PromoterSetSig objects must have the same pvalue column")

            promotersetsig_filepath = extract_file_from_storage(promotersetsig_record.file, tmpdir_promotersetsig)
            filepaths[promotersetsig_id] = promotersetsig_filepath

        # Read the data and extract the relevant columns
        data_list = []
        for id, filepath in filepaths.items():
            data = pd.read_csv(filepath)

            # verify that there are no duplicate feature identifiers
            if data.duplicated(subset=[promotersetsig_record.fileformat.feature_identifier_col]).any():
                raise ValueError("Duplicate feature identifiers found in the data")

            data_subset = (
                data[
                    [
                        promotersetsig_record.fileformat.feature_identifier_col,
                        promotersetsig_record.fileformat.pval_col,
                    ]
                ]
                .rename(columns={promotersetsig_record.fileformat.pval_col: f"{str(id)}"})
                .set_index(promotersetsig_record.fileformat.feature_identifier_col)
            )
            data_list.append(data_subset)

        input_data = pd.concat(data_list, axis=1, join="inner")

        # Calculate metrics on the input data
        return calculate_metrics(input_data)
