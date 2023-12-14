import os
import shutil

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from yeastregulatorydb.regulatory_data.models import ChrMap, FileFormat
from yeastregulatorydb.users.models import User

from ..api.serializers import FileFormatSerializer, GenomicFeatureSerializer, PromoterSetSerializer
from .factories import ChrMapFactory, FileFormatFactory, GenomicFeatureFactory, PromoterSetFactory
from .utils.model_to_dict_select import model_to_dict_select

# @pytest.mark.django_db
# def test_binding_serializer(tmpdir, user: User):
#     """
#     Test the GenomicFileValidationMixin of the BindingSerializer by creating
#     example binding files, using pandas, in a tmpdir and then validaitng them
#     """
#     # Create foreign key instances
#     chrmap1 = ChrMapFactory(ucsc="chr1", seqlength=100)
#     # init binding data


@pytest.mark.django_db
def test_fileformat_serializer(user: User):
    # Create a request instance
    factory = APIRequestFactory()
    request = factory.get("/")
    # Authenticate the request
    request.user = user
    # init fileformat data
    data = {
        "fileformat": "mcisaac",
        "fields": {
            "gene_id": "int",
            "log2_ratio": "float",
            "log2_cleaned_ratio": "float",
            "log2_noise_model": "float",
            "log2_cleaned_ratio_zth2d": "float",
            "log2_selected_timecourses": "float",
            "log2_shrunken_timecourses": "float",
        },
        "separator": ",",
        "effect_col": "log2_shrunken_timecourses",
        "pval_col": None,
    }
    fileformat1 = model_to_dict_select(FileFormatFactory.build(**data))
    # Serialize the FileFormat instance with the request in the context
    serializer1 = FileFormatSerializer(data=fileformat1, context={"request": request})
    # Check that the serializer is valid
    assert serializer1.is_valid() == True, serializer1.errors


@pytest.mark.django_db
def test_genomic_feature_serializer(user: User):
    # Create a request instance
    factory = APIRequestFactory()
    request = factory.get("/")
    # Authenticate the request
    request.user = user
    # Create foreign key instances
    chrmap1 = ChrMapFactory(ucsc="chr1", seqlength=100)
    # init genomic feature data
    data = {"chr": chrmap1, "start": 3, "end": 4}
    genomic_feature1 = model_to_dict_select(GenomicFeatureFactory.build(**data))
    # Serialize the GenomicFeature instance with the request in the context
    serializer1 = GenomicFeatureSerializer(data=genomic_feature1, context={"request": request})
    # Check that the serializer is valid
    assert serializer1.is_valid() == True, serializer1.errors

    # test that the serializer is invalid if start > end
    data.update({"start": 4, "end": 3})
    genomic_feature2 = model_to_dict_select(GenomicFeatureFactory.build(**data))
    serializer2 = GenomicFeatureSerializer(data=genomic_feature2, context={"request": request})
    with pytest.raises(ValidationError) as excinfo1:
        serializer2.is_valid(raise_exception=True), serializer2.errors
    assert excinfo1.match("`start` value cannot be greater than end value")

    # test that start <= seqlength
    data.update({"start": 101, "end": 102})
    genomic_feature3 = model_to_dict_select(GenomicFeatureFactory.build(**data))
    serializer3 = GenomicFeatureSerializer(data=genomic_feature3, context={"request": request})
    with pytest.raises(ValidationError) as excinfo2:
        serializer3.is_valid(raise_exception=True), serializer3.errors
    assert excinfo2.match("`start` of feature cannot exceed length of chromosome")

    # test that the serializer is invalid if start or end > chromosome length
    # or start < 1
    data.update({"start": 0, "end": 400})
    genomic_feature4 = model_to_dict_select(GenomicFeatureFactory.build(**data))
    serializer4 = GenomicFeatureSerializer(data=genomic_feature4, context={"request": request})
    with pytest.raises(ValidationError) as excinfo3:
        serializer4.is_valid(raise_exception=True), serializer3.errors
    assert excinfo3.match("`start` value cannot be less than 1")
    assert excinfo3.match("`end` of feature cannot exceed length of chromosome")


@pytest.mark.django_db
def test_promoterset_serializer(tmpdir, user: User, chrmap: ChrMap):
    # Create a request instance
    factory = APIRequestFactory()
    request = factory.get("/")
    # Authenticate the request
    request.user = user

    # set path to test data and check that it exists
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_data", "yiming_promoters_chrI.bed.gz")
    assert os.path.exists(file_path), f"path: {file_path}"

    shutil.copy(file_path, tmpdir)
    tmpdir_path = os.path.join(tmpdir, "yiming_promoters_chrI.bed.gz")
    assert os.path.exists(tmpdir_path)

    # Open the file and read its content
    with open(tmpdir_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        uploaded_file = SimpleUploadedFile(
            "yiming_promoters_chrI.bed.gz", file_content, content_type="application/gzip"
        )

        fields_dict = {"name": "yiming", "file": uploaded_file}
        data = model_to_dict_select(PromoterSetFactory.build(**fields_dict))

        serializer1 = PromoterSetSerializer(data=data, context={"request": request})

        assert serializer1.is_valid() == True, serializer1.errors
