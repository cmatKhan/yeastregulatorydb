import os

import pandas as pd
import pytest
from django.db.models.query import QuerySet
from rest_framework.authtoken.models import Token

from yeastregulatorydb.regulatory_data.models import (
    Binding,
    BindingManualQC,
    CallingCardsBackground,
    ChrMap,
    DataSource,
    Expression,
    ExpressionManualQC,
    FileFormat,
    GenomicFeature,
    PromoterSet,
    PromoterSetSig,
    Regulator,
)
from yeastregulatorydb.regulatory_data.tests.factories import (
    BindingFactory,
    BindingManualQCFactory,
    CallingCardsBackgroundFactory,
    ChrMapFactory,
    DataSourceFactory,
    ExpressionFactory,
    ExpressionManualQCFactory,
    FileFormatFactory,
    GenomicFeatureFactory,
    PromoterSetFactory,
    PromoterSetSigFactory,
    RegulatorFactory,
)
from yeastregulatorydb.users.models import User
from yeastregulatorydb.users.tests.factories import UserFactory

TEST_DATA_ROOT = os.path.join(os.path.dirname(__file__), "regulatory_data/tests/test_data")


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    user_instance = UserFactory()
    Token.objects.create(user=user_instance)
    return user_instance


@pytest.fixture
def binding(db) -> Binding:
    return BindingFactory()


@pytest.fixture
def bindingmanualqc(db) -> BindingManualQC:
    return BindingManualQCFactory()


@pytest.fixture
def callingcardsbackground(db) -> CallingCardsBackground:
    return CallingCardsBackgroundFactory()


@pytest.fixture
def chrmap(db, user: User) -> QuerySet:
    data = [
        {
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
        },
        {
            "id": 17,
            "refseq": "NC_001224.1",
            "igenomes": "MT",
            "ensembl": "Mito",
            "ucsc": "chrM",
            "mitra": "NC_0011224",
            "seqlength": 85779,
            "numbered": "M",
            "chr": "chrM",
            "type": "mito",
        },
        {
            "id": 18,
            "refseq": "RDM_2",
            "igenomes": "RDM_2",
            "ensembl": "RDM_2",
            "ucsc": "RDM_2",
            "mitra": "RDM_2",
            "seqlength": 6018,
            "numbered": "RDM_2",
            "chr": "RDM_2",
            "type": "plasmid",
        },
        {
            "id": 19,
            "refseq": "RDM_3",
            "igenomes": "RDM_3",
            "ensembl": "RDM_3",
            "ucsc": "RDM_3",
            "mitra": "RDM_3",
            "seqlength": 9013,
            "numbered": "RDM_3",
            "chr": "RDM_3",
            "type": "plasmid",
        },
        {
            "id": 20,
            "refseq": "RDM_5",
            "igenomes": "RDM_5",
            "ensembl": "RDM_5",
            "ucsc": "RDM_5",
            "mitra": "RDM_5",
            "seqlength": 11450,
            "numbered": "RDM_5",
            "chr": "RDM_5",
            "type": "plasmid",
        },
    ]
    for record in data:
        record["uploader"] = user
        record["modifier"] = user
    ChrMap.objects.bulk_create([ChrMap(**record) for record in data])
    return ChrMap.objects.all()


@pytest.fixture
def expression(db) -> Expression:
    return ExpressionFactory()


@pytest.fixture
def expressionmanualqc(db) -> ExpressionManualQC:
    return ExpressionManualQCFactory()


@pytest.fixture
def datasource(db) -> DataSource:
    return DataSourceFactory()


@pytest.fixture
def fileformat(db) -> QuerySet:
    # harb, hu both csvs
    format_dict = {
        "array": ({"gene_id": "int", "effect": "float", "pval": "float"}, ",", "effect", "pval"),
        "qbed": ({"chr": "str", "start": "int", "end": "int", "depth": "int", "strand": "str"}, "\t", "none", "none"),
        "chipexo_allevents": (
            {
                "chr": "str",
                "start": "int",
                "end": "int",
                "YPD_Sig": "float",
                "YPD_Ctrl": "float",
                "YPD_log2Fold": "float",
                "YPD_log2P": "float",
            },
            ",",
            "YPD_log2Fold",
            "YPD_log2P",
        ),
        "chipexo_promoter_sig": (
            {
                "chr": "str",
                "start": "int",
                "end": "int",
                "name": "str",
                "strand": "str",
                "n_sig_peaks": "int",
                "max_fc": "float",
                "min_pval": "float",
            },
            ",",
            "max_fc",
            "min_pval",
        ),
        "cc_promoter_sig": (
            {
                "chr": "str",
                "start": "int",
                "end": "int",
                "name": "str",
                "strand": "str",
                "experiment_hops": "int",
                "background_hops": "int",
                "background_total_hops": "int",
                "experiment_total_hops": "int",
                "callingcards_enrichment": "int",
                "poisson_pval": "int",
                "hypergeometric_pval": "int",
            },
            ",",
            "callingcards_enrichment",
            "poisson_pval",
        ),
        "kemmeren": (
            {"gene_id": "int", "M": "float", "Madj": "float", "A": "float", "pval": "float"},
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
def cc_datasource(db, fileformat: QuerySet) -> DataSource:
    qbed_fileformat = fileformat.filter(fileformat="qbed").first()
    content = {
        "name": "brent_nf_cc",
        "fileformat": qbed_fileformat,
        "lab": "brent",
        "assay": "callingcards",
        "workflow": "nf-core/callingcards:dev",
    }
    return DataSourceFactory(**content)


@pytest.fixture
def chipexo_datasource(db, fileformat: QuerySet) -> DataSource:
    chipexo = fileformat.filter(fileformat="chipexo_allevents").first()
    content = {
        "id": 100,
        "name": "chipexo_pugh_allevents",
        "fileformat": chipexo,
        "lab": "pugh",
        "assay": "chipexo",
        "workflow": "none",
    }
    return DataSourceFactory(**content)


@pytest.fixture
def harbison_datasource(db, fileformat: QuerySet) -> DataSource:
    array = fileformat.filter(fileformat="array").first()
    content = {
        "name": "harbison_chip",
        "fileformat": array,
        "lab": "harbison",
        "assay": "chip",
        "workflow": "none",
    }
    return DataSourceFactory(**content)


@pytest.fixture
def hu_datasource(db, fileformat: QuerySet) -> DataSource:
    array = fileformat.filter(fileformat="array").first()
    content = {
        "name": "hu_reimann_tfko",
        "fileformat": array,
        "lab": "hu",
        "assay": "tfko",
        "workflow": "none",
    }
    return DataSourceFactory(**content)


@pytest.fixture
def kemmeren_datasource(db, fileformat: QuerySet) -> DataSource:
    kemmeren = fileformat.filter(fileformat="kemmeren").first()
    content = {
        "name": "kemmeren_tfko",
        "fileformat": kemmeren,
        "lab": "kemmeren",
        "assay": "tfko",
        "workflow": "none",
    }
    return DataSourceFactory(**content)


@pytest.fixture
def mcisaac_datasource(db, fileformat: QuerySet) -> DataSource:
    mcisaac = fileformat.filter(fileformat="mcisaac").first()
    content = {
        "name": "mcisaac_oe",
        "fileformat": mcisaac,
        "lab": "mcisaac",
        "assay": "overexpression",
        "workflow": "none",
    }


@pytest.fixture
def genomicfeature(db) -> GenomicFeature:
    return GenomicFeatureFactory()


@pytest.fixture
def genomicfeature_chr1_genes(db, chrmap: QuerySet, user: User) -> QuerySet:
    chr1_genes_df = pd.read_csv(os.path.join(TEST_DATA_ROOT, "chr1_genes.csv.gz"), compression="gzip")
    chr1_genes_dict = chr1_genes_df.to_dict(orient="records")
    for record in chr1_genes_dict:
        record["chr"] = chrmap.first()
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
    hap5_genomic_feature = GenomicFeatureFactory(locus_tag="YOR358W", symbol="HAP5")
    return RegulatorFactory(id=1, regulator=hap5_genomic_feature)
