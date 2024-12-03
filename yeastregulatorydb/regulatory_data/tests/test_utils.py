import os

import numpy as np
import pandas as pd
import pytest
from django.db.models.query import QuerySet

from yeastregulatorydb.regulatory_data.utils import count_hops, stable_rank


@pytest.mark.django_db
def test_count_hops(clean_test_database, chrmap: QuerySet):

    input_data_path = os.path.join(
        os.path.dirname(__file__), "test_data/binding/callingcards/ccexperiment_511.qbed.gz"
    )
    df = pd.read_csv(input_data_path, sep="\t", compression="gzip")
    actual = count_hops(df, "ucsc")  # replace 'chr_format' with the actual chromosome format
    assert actual == {"genomic": 222, "mito": 4, "plasmid": 47}


def test_rank_by_col1_only():
    col1 = np.array([0.1, 0.5, 0.5, 0.9])
    ranks = stable_rank(col1, col1_ascending=True, method="min")
    assert np.allclose(ranks, [1, 2, 2, 4]), "Failed ranking by col1 only (ascending)"

    ranks = stable_rank(col1, col1_ascending=False, method="min")
    assert np.allclose(ranks, [4, 2, 2, 1]), "Failed ranking by col1 only (descending)"


def test_rank_col1_and_break_ties_with_col2():
    col1 = np.array([0.1, 0.5, 0.5, 0.9])
    col2 = np.array([10, 5, 15, 1])

    # Col1 ascending, Col2 ascending
    ranks = stable_rank(col1, col2, col1_ascending=True, col2_ascending=True, method="min")
    assert np.allclose(ranks, [1, 2, 3, 4]), "Failed ranking with col1 ascending and col2 ascending"

    # Col1 ascending, Col2 descending
    ranks = stable_rank(col1, col2, col1_ascending=True, col2_ascending=False, method="min")
    assert np.allclose(ranks, [1, 3, 2, 4]), "Failed ranking with col1 ascending and col2 descending"

    # Col1 descending, Col2 ascending
    ranks = stable_rank(col1, col2, col1_ascending=False, col2_ascending=True, method="min")
    assert np.allclose(ranks, [4, 2, 3, 1]), "Failed ranking with col1 descending and col2 ascending"

    # Col1 descending, Col2 descending
    ranks = stable_rank(col1, col2, col1_ascending=False, col2_ascending=False, method="min")
    assert np.allclose(ranks, [4, 3, 2, 1]), "Failed ranking with col1 descending and col2 descending"


def test_handle_ties_in_col1():
    col1 = np.array([0.5, 0.5, 0.5, 0.9])
    col2 = np.array([10, 15, 5, 1])

    # Col1 ascending, Col2 descending
    ranks = stable_rank(col1, col2, col1_ascending=True, col2_ascending=False, method="min")
    assert np.allclose(ranks, [2, 1, 3, 4]), "Failed to handle ties in col1 with col2 descending"

    # Col1 descending, Col2 ascending
    ranks = stable_rank(col1, col2, col1_ascending=False, col2_ascending=True, method="min")
    assert np.allclose(ranks, [3, 4, 2, 1]), "Failed to handle ties in col1 with col2 ascending"


def test_no_col2_provided():
    col1 = np.array([0.3, 0.1, 0.9, 0.5])
    ranks = stable_rank(col1, col1_ascending=True)
    assert np.allclose(ranks, [2, 1, 4, 3]), "Failed ranking when col2 is not provided"

    ranks = stable_rank(col1, col1_ascending=False)
    assert np.allclose(ranks, [3, 4, 1, 2]), "Failed descending ranking when col2 is not provided"


def test_invalid_inputs():
    col1 = np.array(["a", "b", "c"])
    col2 = np.array([0.1, 0.5, 0.9])

    with pytest.raises(ValueError, match="`col1` must be numeric"):
        stable_rank(col1)

    with pytest.raises(ValueError, match="`col2` must be numeric"):
        stable_rank(np.array([0.1, 0.5, 0.9]), col2=np.array(["x", "y", "z"]))


def test_empty_inputs():
    col1 = np.array([])
    col2 = np.array([])

    with pytest.raises(ValueError):
        stable_rank(col1)

    with pytest.raises(ValueError):
        stable_rank(col1, col2)


def test_edge_case_single_element():
    col1 = np.array([0.1])
    ranks = stable_rank(col1)
    assert np.allclose(ranks, [1]), "Failed edge case with a single element"

    col2 = np.array([10])
    ranks = stable_rank(col1, col2)
    assert np.allclose(ranks, [1]), "Failed edge case with single element and col2"
