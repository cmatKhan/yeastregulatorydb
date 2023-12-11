import faker
from factory import Faker, SubFactory
from factory.django import DjangoModelFactory, FileField

from ..models import (
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

fake = faker.Faker()


class ChrMapFactory(DjangoModelFactory):
    refseq = Faker("pystr", max_chars=12)
    igenomes = Faker("pystr", max_chars=12)
    ensembl = Faker("pystr", max_chars=12)
    ucsc = Faker("pystr", max_chars=12)
    mitra = Faker("pystr", max_chars=15)
    numbered = Faker("pystr", max_chars=12)
    chr = Faker("pystr", max_chars=12)
    seqlength = Faker("random_int", min=1, max=10000)
    type = fake.random_element(elements=["genomic", "mito", "plasmid"])

    class Meta:
        model = ChrMap
        django_get_or_create = ["refseq", "igenomes", "ensembl", "ucsc", "mitra", "numbered", "chr"]


class GenomicFeatureFactory(DjangoModelFactory):
    chr = SubFactory(ChrMapFactory)
    start = Faker("random_int", min=1, max=1000)
    end = Faker("random_int", min=1001, max=2000)
    strand = fake.random_element(elements=GenomicFeature.STRAND_CHOICES)
    type = Faker("pystr", max_chars=30)
    biotype = Faker("pystr", max_chars=20)
    locus_tag = Faker("pystr", max_chars=20)
    symbol = Faker("pystr", max_chars=20)
    source = Faker("pystr", max_chars=50)
    alias = Faker("pystr", max_chars=150)
    note = Faker("pystr", max_chars=1000)

    class Meta:
        model = GenomicFeature
        django_get_or_create = ["locus_tag", "symbol"]


class RegulatorFactory(DjangoModelFactory):
    regulator = SubFactory(GenomicFeatureFactory)
    under_development = Faker("pybool")
    notes = Faker("pystr", max_chars=50)

    class Meta:
        model = Regulator
        django_get_or_create = ["regulator"]


class FileFormatFactory(DjangoModelFactory):
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


class ExpressionSourceFactory(DjangoModelFactory):
    fileformat_id = SubFactory(FileFormatFactory)
    lab = Faker("word")
    assay = Faker("word")
    workflow = Faker("word")
    citation = Faker("sentence")
    description = Faker("sentence")
    notes = Faker("sentence")

    class Meta:
        model = ExpressionSource
        django_get_or_create = ["fileformat_id"]


class ExpressionFactory(DjangoModelFactory):
    regulator_id = SubFactory(RegulatorFactory)
    batch = Faker("word")
    replicate = fake.random_digit()
    control = fake.random_element(elements=["undefined", "wt", "wt_mata"])
    mechanism = fake.random_element(elements=["gev", "zev", "tfko"])
    restriction = fake.random_element(elements=["undefined", "P", "M", "N"])
    time = fake.random_digit()
    source_id = SubFactory(ExpressionSourceFactory)
    file = Faker("file_name")
    notes = Faker("sentence")

    class Meta:
        model = Expression
        django_get_or_create = ["regulator_id", "source_id"]


class ExpressionManualQCFactory(DjangoModelFactory):
    expression_id = SubFactory(ExpressionFactory)
    strain_verified = fake.random_element(elements=["yes", "no", "unverified"])

    class Meta:
        model = ExpressionManualQC
        django_get_or_create = ["expression_id"]


class CallingCardsBackgroundFactory(DjangoModelFactory):
    name = Faker("pystr", max_chars=10)
    file = FileField(filename="testfile.tsv.gz")
    genomic_inserts = Faker("random_digit_not_null")
    mito_inserts = Faker("random_digit_not_null")
    plasmid_inserts = Faker("random_digit_not_null")
    notes = Faker("sentence", nb_words=10)

    class Meta:
        model = CallingCardsBackground
        django_get_or_create = ["name"]


class BindingSourceFactory(DjangoModelFactory):
    fileformat_id = SubFactory(FileFormatFactory)
    lab = Faker("pystr", max_chars=20)
    assay = Faker("pystr", max_chars=20)
    workflow = Faker("pystr", max_chars=50)
    description = Faker("pystr", max_chars=100)
    citation = Faker("pystr", max_chars=200)
    notes = Faker("pystr", max_chars=100)

    class Meta:
        model = BindingSource
        django_get_or_create = ["fileformat_id", "lab", "assay", "workflow"]


class BindingFactory(DjangoModelFactory):
    regulator_id = SubFactory(RegulatorFactory)
    batch = Faker("pystr", max_chars=20)
    replicate = Faker("pyint")
    source_id = SubFactory(BindingSourceFactory)
    source_orig_id = Faker("pystr", max_chars=20)
    strain = Faker("pystr", max_chars=20)
    file = Faker("file_name")
    genomic_inserts = Faker("pyint")
    mito_inserts = Faker("pyint")
    plasmid_inserts = Faker("pyint")
    notes = Faker("pystr", max_chars=100)

    class Meta:
        model = Binding
        django_get_or_create = ["regulator", "batch", "replicate", "source_id"]


class BindingManualQCFactory(DjangoModelFactory):
    binding_id = SubFactory(BindingFactory)
    rank_response_pass = Faker("pybool")
    best_response_pass = Faker("pybool")
    data_usable = Faker("pybool")
    passing_replicate = Faker("pybool")
    notes = Faker("pystr", max_chars=100)

    class Meta:
        model = BindingManualQC
        django_get_or_create = ["binding_id"]


class PromoterSetFactory(DjangoModelFactory):
    name = Faker("pystr", max_chars=10)
    file = FileField(filename="testfile.bed.gz")
    notes = Faker("sentence", nb_words=10)

    class Meta:
        model = PromoterSet
        django_get_or_create = ["name"]


class PromoterSetSigFactory(DjangoModelFactory):
    binding_id = SubFactory(BindingFactory)
    promoter_id = SubFactory(PromoterSetFactory)
    background_id = SubFactory(CallingCardsBackgroundFactory)
    filetype = SubFactory(FileFormatFactory)
    file = FileField(filename="testfile.tsv.gz")

    class Meta:
        model = PromoterSetSig
        django_get_or_create = ["binding_id", "promoter_id", "background_id"]
