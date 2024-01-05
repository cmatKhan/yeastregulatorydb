import random

import faker
from factory import Faker, LazyFunction, SubFactory
from factory.django import DjangoModelFactory, FileField

from yeastregulatorydb.users.tests.factories import UserFactory

from ..models import (
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
    RankResponse,
    Regulator,
)

fake = faker.Faker()


def sentence_with_max_chars(max_chars=100):
    sentence = fake.sentence(nb_words=10)
    if len(sentence) > max_chars:
        sentence = sentence[:max_chars].rsplit(" ", 1)[0] + "."
    return sentence


class ChrMapFactory(DjangoModelFactory):
    uploader = SubFactory(UserFactory)
    modifier = SubFactory(UserFactory)
    refseq = Faker("pystr", max_chars=12)
    igenomes = Faker("pystr", max_chars=12)
    ensembl = Faker("pystr", max_chars=12)
    ucsc = Faker("pystr", max_chars=12)
    mitra = Faker("pystr", max_chars=15)
    numbered = Faker("pystr", max_chars=12)
    chr = Faker("pystr", max_chars=12)
    seqlength = Faker("random_int", min=2001, max=10000)
    type = fake.random_element(elements=["genomic", "mito", "plasmid"])

    class Meta:
        model = ChrMap
        django_get_or_create = ["chr"]


class GenomicFeatureFactory(DjangoModelFactory):
    uploader = SubFactory(UserFactory)
    modifier = SubFactory(UserFactory)
    chr = SubFactory(ChrMapFactory)
    start = Faker("random_int", min=1, max=1000)
    end = Faker("random_int", min=1001, max=2000)
    strand = fake.random_element(elements=["+", "-", "*"])
    type = Faker("pystr", max_chars=30)
    locus_tag = Faker("pystr", max_chars=20)
    symbol = Faker("pystr", max_chars=20)
    source = Faker("pystr", max_chars=50)
    alias = Faker("pystr", max_chars=150)
    note = Faker("pystr", max_chars=1000)

    class Meta:
        model = GenomicFeature
        django_get_or_create = ["locus_tag", "symbol"]


class RegulatorFactory(DjangoModelFactory):
    uploader = SubFactory(UserFactory)
    modifier = SubFactory(UserFactory)
    genomicfeature = SubFactory(GenomicFeatureFactory)
    under_development = Faker("pybool")
    notes = Faker("pystr", max_chars=50)

    class Meta:
        model = Regulator
        django_get_or_create = ["genomicfeature"]


class FileFormatFactory(DjangoModelFactory):
    uploader = SubFactory(UserFactory)
    modifier = SubFactory(UserFactory)
    fileformat = Faker("word")
    fields = {
        "chr": fake.random_element(elements=("str", "int", "float")),
        "start": fake.random_element(elements=("str", "int", "float")),
        "end": fake.random_element(elements=("str", "int", "float")),
        "name": fake.random_element(elements=("str", "int", "float")),
        "score": fake.random_element(elements=("str", "int", "float")),
        "strand": ["+", "-", "*"],
    }
    separator = fake.random_element(elements=("\t", ","))
    effect_col = Faker("word")
    pval_col = Faker("word")

    class Meta:
        model = FileFormat
        django_get_or_create = ["fileformat"]


class DataSourceFactory(DjangoModelFactory):
    uploader = SubFactory(UserFactory)
    modifier = SubFactory(UserFactory)
    fileformat = SubFactory(FileFormatFactory)
    name = Faker("pystr", max_chars=50)
    lab = Faker("word")
    assay = Faker("word")
    workflow = Faker("word")
    citation = Faker("sentence")
    description = Faker("sentence")
    notes = Faker("sentence")

    class Meta:
        model = DataSource
        django_get_or_create = ["lab", "assay", "workflow"]


class ExpressionFactory(DjangoModelFactory):
    uploader = SubFactory(UserFactory)
    modifier = SubFactory(UserFactory)
    regulator = SubFactory(RegulatorFactory)
    batch = Faker("word")
    replicate = fake.random_digit()
    control = fake.random_element(elements=["undefined", "wt", "wt_mata"])
    mechanism = fake.random_element(elements=["gev", "zev", "tfko"])
    restriction = fake.random_element(elements=["undefined", "P", "M", "N"])
    time = fake.random_digit()
    source = SubFactory(DataSourceFactory)
    file = Faker("file_name")
    notes = Faker("sentence")

    class Meta:
        model = Expression
        django_get_or_create = ["regulator", "source"]


class ExpressionManualQCFactory(DjangoModelFactory):
    uploader = SubFactory(UserFactory)
    modifier = SubFactory(UserFactory)
    expression = SubFactory(ExpressionFactory)
    strain_verified = fake.random_element(elements=["yes", "no", "unverified"])

    class Meta:
        model = ExpressionManualQC
        django_get_or_create = ["expression"]


class CallingCardsBackgroundFactory(DjangoModelFactory):
    uploader = SubFactory(UserFactory)
    modifier = SubFactory(UserFactory)
    name = Faker("pystr", max_chars=10)
    file = FileField(filename="testfile.qbed.gz")
    fileformat = SubFactory(FileFormatFactory)
    genomic_inserts = Faker("random_digit_not_null")
    mito_inserts = Faker("random_digit_not_null")
    plasmid_inserts = Faker("random_digit_not_null")
    notes = LazyFunction(sentence_with_max_chars)

    class Meta:
        model = CallingCardsBackground
        django_get_or_create = ["name"]


class BindingFactory(DjangoModelFactory):
    uploader = SubFactory(UserFactory)
    modifier = SubFactory(UserFactory)
    regulator = SubFactory(RegulatorFactory)
    batch = Faker("pystr", max_chars=20)
    replicate = Faker("pyint")
    source = SubFactory(DataSourceFactory)
    condition = LazyFunction(lambda: random.choice(Binding.CONDITION_CHOICES)[0])
    source_orig_id = Faker("pystr", max_chars=20)
    strain = Faker("pystr", max_chars=20)
    file = Faker("file_name")
    genomic_inserts = Faker("pyint")
    mito_inserts = Faker("pyint")
    plasmid_inserts = Faker("pyint")
    notes = Faker("pystr", max_chars=100)

    class Meta:
        model = Binding
        django_get_or_create = ["regulator", "batch", "replicate", "source"]


class BindingManualQCFactory(DjangoModelFactory):
    uploader = SubFactory(UserFactory)
    modifier = SubFactory(UserFactory)
    binding = SubFactory(BindingFactory)
    best_datatype = Faker("pybool")
    data_usable = Faker("pybool")
    passing_replicate = Faker("pybool")
    notes = Faker("pystr", max_chars=100)

    class Meta:
        model = BindingManualQC
        django_get_or_create = ["binding"]


class PromoterSetFactory(DjangoModelFactory):
    uploader = SubFactory(UserFactory)
    modifier = SubFactory(UserFactory)
    name = Faker("pystr", max_chars=10)
    file = FileField(filename="testfile.bed.gz")
    notes = LazyFunction(sentence_with_max_chars)

    class Meta:
        model = PromoterSet
        django_get_or_create = ["name"]


class PromoterSetSigFactory(DjangoModelFactory):
    uploader = SubFactory(UserFactory)
    modifier = SubFactory(UserFactory)
    binding = SubFactory(BindingFactory)
    promoter = SubFactory(PromoterSetFactory)
    background = SubFactory(CallingCardsBackgroundFactory)
    fileformat = SubFactory(FileFormatFactory)
    file = FileField(filename="testfile.csv.gz")

    class Meta:
        model = PromoterSetSig
        django_get_or_create = ["binding", "promoter", "background"]


class RankResponseFactory(DjangoModelFactory):
    uploader = SubFactory(UserFactory)
    modifier = SubFactory(UserFactory)
    promotersetsig = SubFactory(PromoterSetSigFactory)
    expression = SubFactory(ExpressionFactory)
    expression_effect_threshold = 0.0
    expression_pvalue_threshold = 1.0
    fileformat = SubFactory(FileFormatFactory)
    normalized = False
    file = FileField(filename="rankresponse.csv.gz")
    significant_response = Faker("pybool")

    class Meta:
        model = RankResponse
        django_get_or_create = ["promotersetsig", "expression"]
