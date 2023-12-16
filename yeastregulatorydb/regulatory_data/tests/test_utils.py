import os

import pandas as pd
import pytest
from django.db.models.query import QuerySet

from yeastregulatorydb.regulatory_data.models import ChrMap
from yeastregulatorydb.regulatory_data.utils.count_hops import count_hops


@pytest.mark.django_db
def test_count_hops(chrmap: QuerySet):
    input_data_path = os.path.join(
        os.path.dirname(__file__), "test_data/binding/callingcards/ccexperiment_511.qbed.gz"
    )
    df = pd.read_csv(input_data_path, sep="\t", compression="gzip")
    actual = count_hops(df, "ucsc")  # replace 'chr_format' with the actual chromosome format
    assert actual == {"genomic": 222, "mito": 4, "plasmid": 47}
