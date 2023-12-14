import os

import pandas as pd
import pytest
from django.db.models.query import QuerySet

from yeastregulatorydb.regulatory_data.models import (
    Binding,
    BindingManualQC,
    BindingSource,
    CallingCardsBackground,
    ChrMap,
    Expression,
    ExpressionManualQC,
    ExpressionSource,
    FileFormat,
    GenomicFeature,
    PromoterSet,
    PromoterSetSig,
    Regulator,
)
from yeastregulatorydb.regulatory_data.tests.factories import (
    BindingFactory,
    BindingManualQCFactory,
    BindingSourceFactory,
    CallingCardsBackgroundFactory,
    ChrMapFactory,
    ExpressionFactory,
    ExpressionManualQCFactory,
    ExpressionSourceFactory,
    FileFormatFactory,
    GenomicFeatureFactory,
    PromoterSetFactory,
    PromoterSetSigFactory,
    RegulatorFactory,
)
from yeastregulatorydb.users.models import User
from yeastregulatorydb.users.tests.factories import UserFactory

TEST_DATA_ROOT = os.path.join(os.path.dirname(__file__), "regulatory_data/test_data")


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    return UserFactory()


@pytest.fixture
def binding(db) -> Binding:
    return BindingFactory()


@pytest.fixture
def bindingmanualqc(db) -> BindingManualQC:
    return BindingManualQCFactory()


@pytest.fixture
def bindingsource(db) -> BindingSource:
    return BindingSourceFactory()


@pytest.fixture
def callingcardsbackground(db) -> CallingCardsBackground:
    return CallingCardsBackgroundFactory()


@pytest.fixture
def chrmap(db) -> ChrMap:
    data = {
        "id": 1,
        "refseq": "NC_001133.9",
        "igenomes": "I",
        "ensembl": "I",
        "ucsc": "chrI",
        "mitra": "NC_001133",
        "seqlength": 230218,
        "numbered": "1",
        "chr": "chr1",
        "type": "genomic",
    }
    return ChrMapFactory(**data)


@pytest.fixture
def expression(db) -> Expression:
    return ExpressionFactory()


@pytest.fixture
def expressionmanualqc(db) -> ExpressionManualQC:
    return ExpressionManualQCFactory()


@pytest.fixture
def expressionsource(db) -> ExpressionSource:
    return ExpressionSourceFactory()


@pytest.fixture
def fileformat(db) -> QuerySet:
    # harb, hu both csvs
    format_dict = {
        "array": ({"gene_id": "int", "effect": "float", "pval": "float"}, ",", "effect", "pval"),
        "qbed": ({"chr": "str", "start": "int", "end": "int", "depth": "int", "strand": "str"}, "\t", "none", "none"),
        "kemmeren": (
            {"gene_id": "str", "M": "float", "Madj": "float", "A": "float", "pval": "float"},
            ",",
            "Madj",
            "pval",
        ),
        "mcisaac": (
            {
                "gene_id": "int",
                "log2_ratio": "float",
                "log2_cleaned_ratio": "float",
                "log2_noise_model": "float",
                "log2_cleaned_ratio_zth2d": "float",
                "log2_selected_timecourses": "float",
                "log2_shrunken_timecourses": "float",
            },
            ",",
            "log2_shrunken_timecourses",
            "none",
        ),
        "bed6": (
            {"chr": "str", "start": "int", "end": "int", "name": "str", "score": "float", "strand": "str"},
            "\t",
            "none",
            "none",
        ),
    }
    for key, value in format_dict.items():
        fields, separator, effect, pval = value
        FileFormatFactory.create(fileformat=key, fields=fields, separator=separator, effect_col=effect, pval_col=pval)
    return FileFormat.objects.all()


@pytest.fixture
def genomicfeature(db) -> GenomicFeature:
    return GenomicFeatureFactory()


@pytest.fixture
def genomicfeature_chr1_genes(db, chrmap: ChrMap, user: User) -> QuerySet:
    chr1_genes_df = pd.read_csv(os.path.join(TEST_DATA_ROOT, "chr1_genes.csv.gz"), compression="gzip")
    chr1_genes_dict = chr1_genes_df.to_dict(orient="records")
    for record in chr1_genes_dict:
        record["chr"] = chrmap
        record["uploader"] = user
        record["modifier"] = user
    # bulk create the GenomicFeature instances
    GenomicFeature.objects.bulk_create([GenomicFeature(**record) for record in chr1_genes_dict])
    return GenomicFeature.objects.all()


@pytest.fixture
def promoterset(db) -> PromoterSet:
    return PromoterSetFactory()


@pytest.fixture
def promotersetsig(db) -> PromoterSetSig:
    return PromoterSetSigFactory()


@pytest.fixture
def regulator(db) -> Regulator:
    return RegulatorFactory()
