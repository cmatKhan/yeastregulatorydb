import logging
import os
import random
import uuid

import faker
import pytest
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils.http import urlencode
from factory import Faker, LazyFunction, SubFactory, post_generation
from factory.django import DjangoModelFactory, FileField
from rest_framework.authtoken.models import Token

from yeastregulatorydb.regulatory_data.api.serializers import ExpressionSerializer, PromoterSetSerializer
from yeastregulatorydb.users.tests.factories import UserFactory

from ..models import (
    Binding,
    BindingConcatenated,
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
from .utils.model_to_dict_select import model_to_dict_select

fake = faker.Faker()

logger = logging.getLogger(__name__)


def sentence_with_max_chars(max_chars=100):
    sentence = fake.sentence(nb_words=10)
    if len(sentence) > max_chars:
        sentence = sentence[:max_chars].rsplit(" ", 1)[0] + "."
    return sentence


class ChrMapFactory(DjangoModelFactory):
    uploader = SubFactory(UserFactory)
    modifier = SubFactory(UserFactory)
    refseq = LazyFunction(lambda: f"NC_{uuid.uuid4().hex[:8]}")
    igenomes = LazyFunction(lambda: f"IG_{uuid.uuid4().hex[:8]}")
    ensembl = LazyFunction(lambda: f"EN_{uuid.uuid4().hex[:8]}")
    ucsc = LazyFunction(lambda: f"chr{uuid.uuid4().hex[:8]}")
    mitra = LazyFunction(lambda: f"NC_{uuid.uuid4().hex[:8]}")
    numbered = LazyFunction(lambda: str(uuid.uuid4().int)[:12])
    chr = LazyFunction(lambda: f"chr{uuid.uuid4().hex[:8]}")
    seqlength = Faker("random_int", min=2001, max=10000)
    type = LazyFunction(lambda: random.choice(["genomic", "mito", "plasmid"]))

    class Meta:
        model = ChrMap
        django_get_or_create = ["chr"]

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        instance = super()._create(model_class, *args, **kwargs)
        logger.debug(f"Created ChrMap instance: {instance}")
        return instance


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
    notes = LazyFunction(sentence_with_max_chars)

    class Meta:
        model = Expression
        django_get_or_create = [
            "regulator",
            "batch",
            "replicate",
            "control",
            "mechanism",
            "restriction",
            "time",
            "source",
        ]

    @post_generation
    def attach_real_file(self, create, extracted, **kwargs):
        if extracted:
            # Assuming `extracted` is a path to the file
            with open(extracted, "rb") as f:
                self.file.save(name=self.file.generate(), content=File(f), save=True)


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


class BindingConcatenatedFactory(DjangoModelFactory):
    genomic_inserts = 0
    mito_inserts = 0
    plasmid_inserts = 0
    notes = "none"

    class Meta:
        model = BindingConcatenated

    @post_generation
    def bindings(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of bindings were passed in, use them
            for binding in extracted:
                self.bindings.add(binding)


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
    single_binding = SubFactory(BindingFactory)
    promoter = SubFactory(PromoterSetFactory)
    background = SubFactory(CallingCardsBackgroundFactory)
    fileformat = SubFactory(FileFormatFactory)
    file = FileField(filename="testfile.csv.gz")

    class Meta:
        model = PromoterSetSig
        django_get_or_create = ["single_binding", "promoter", "background"]


class PromoterSetSigWithCompositeBindingFactory(DjangoModelFactory):
    uploader = SubFactory(UserFactory)
    modifier = SubFactory(UserFactory)
    composite_binding = SubFactory(BindingConcatenatedFactory)
    promoter = SubFactory(PromoterSetFactory)
    background = SubFactory(CallingCardsBackgroundFactory)
    fileformat = SubFactory(FileFormatFactory)
    file = FileField(filename="testfile.csv.gz")

    class Meta:
        model = PromoterSetSig
        django_get_or_create = ["composite_binding", "promoter", "background"]


@pytest.fixture
def single_binding_expression_setup(db, user, test_data_dict, mcisaac_datasource, regulator, fileformat):
    """
    Fixture to setup database state for tests that involve multiple file uploads
    and complex interactions.
    """
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    # Helper function to upload a file and create an object in the database
    def upload_file_and_create_object(file_path, factory_class, serializer_class, additional_data={}):
        with open(file_path, "rb") as file_obj:
            file_content = file_obj.read()
            upload_file = SimpleUploadedFile(
                name=file_path.split("/")[-1], content=file_content, content_type="application/gzip"
            )
            data = factory_class.build(file=upload_file, **additional_data)
            data_dict = {
                **model_to_dict_select(data),
                **additional_data,
            }  # Assume model_to_dict_select serializes the factory-built instance to dict
            serializer = serializer_class(data=data_dict)
            assert serializer.is_valid(), serializer.errors
            serializer.save()

    # Upload all required files and create their respective database entries
    expression_path = next(
        file
        for file in test_data_dict["expression"]["mcisaac"]["files"]
        if os.path.basename(file) == "hap5_15_mcisc_chr1.csv.gz"
    )
    assert os.path.exists(expression_path), f"path: {expression_path}"
    upload_file_and_create_object(
        expression_path,
        ExpressionFactory,
        ExpressionSerializer,
        {"source": mcisaac_datasource, "regulator": regulator},
    )

    promoterset_path = next(
        file
        for file in test_data_dict["promoters"]["files"]
        if os.path.basename(file) == "yiming_promoters_chrI.bed.gz"
    )
    assert os.path.exists(promoterset_path), f"path: {promoterset_path}"
    upload_file_and_create_object(promoterset_path, PromoterSetFactory, PromoterSetSerializer, {"name": "yiming"})

    background_path = next(
        file
        for file in test_data_dict["background"]["files"]
        if os.path.basename(file) == "adh1_background_chrI.qbed.gz"
    )
    assert os.path.exists(background_path), f"path: {background_path}"
    upload_file_and_create_object(
        background_path,
        CallingCardsBackgroundFactory,
        None,
        {"name": "adh1", "fileformat": fileformat.get(fileformat="qbed")},
    )

    binding_path = next(
        file
        for file in test_data_dict["binding"]["callingcards"]["files"]
        if os.path.basename(file) == "hap5_expr17_chr1_ucsc.qbed.gz"
    )
    assert os.path.exists(binding_path), f"path: {binding_path}"
    upload_file_and_create_object(
        binding_path, BindingFactory, None, {"source": mcisaac_datasource, "regulator": regulator}
    )

    # add another background to test automatic promoterset sig processing
    dsir4_background_path = next(
        file
        for file in test_data_dict["background"]["files"]
        if os.path.basename(file) == "dsir4_background_chrI.qbed.gz"
    )
    assert os.path.exists(dsir4_background_path), f"path: {dsir4_background_path}"
    upload_file_and_create_object(
        dsir4_background_path, CallingCardsBackgroundFactory, None, {"name": "dsir4", "fileformat": fileformat}
    )
    # Return the client for use in tests if needed
    return client
