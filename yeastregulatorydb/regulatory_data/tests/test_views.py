import os
import re
import tarfile
import tempfile

import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.query import QuerySet
from django.test import RequestFactory
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from yeastregulatorydb.users.models import User

from ..api.serializers import ExpressionSerializer, PromoterSetSerializer
from ..api.views import ChrMapViewSet, GenomicFeatureViewSet
from ..models import Binding, ChrMap, DataSource, Expression, PromoterSetSig, RankResponse, Regulator
from .factories import BindingFactory, ExpressionFactory, GenomicFeatureFactory, PromoterSetFactory
from .utils.model_to_dict_select import model_to_dict_select


@pytest.mark.django_db
def test_create_chrmap(user: User, rf: RequestFactory):
    # Create a request
    data = {
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

    # create and authenticate a request
    request = rf.post("/chrmap/", data, format="json")
    force_authenticate(request, user=user)

    # Create a viewset
    viewset = ChrMapViewSet.as_view({"post": "create"})

    # Call the viewset with the request
    response = viewset(request)

    # Check that the response has a 201 status code
    assert response.status_code == 201, response.data

    # Check that a new ChrMap instance was created
    assert ChrMap.objects.count() == 1

    # Check that the new ChrMap instance has the correct refseq
    assert ChrMap.objects.get().refseq == "NC_001133.9"


def test_list_chrmap(user: User, chrmap: QuerySet, rf: RequestFactory):
    # Create a request
    request = rf.get(f"/api/chrmap/{chrmap.first().id}/")
    force_authenticate(request, user=user)

    # Call the view with the request
    response = ChrMapViewSet.as_view({"get": "list"})(request)

    assert response.status_code == 200


def test_gene_list(user: User, genomicfeature_chr1_genes: QuerySet, rf: RequestFactory):
    # Create a request
    request = rf.get("/api/genomicfeature/50/")
    force_authenticate(request, user=user)

    # Call the view with the request
    response = GenomicFeatureViewSet.as_view({"get": "retrieve"})(request, pk="50")

    assert response.status_code == 200
    assert response.data["locus_tag"] == "YAL031W-A"


@pytest.mark.django_db
def test_single_binding_upload(cc_datasource: DataSource, regulator: Regulator, chrmap: QuerySet, user: User):
    token = Token.objects.get(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    data = model_to_dict_select(BindingFactory.build())
    # set path to test data and check that it exists
    file_path = os.path.join(
        os.path.dirname(__file__), "test_data", "binding/callingcards/hap5_expr17_chr1_ucsc.qbed.gz"
    )
    assert os.path.exists(file_path), f"path: {file_path}"

    # Open the file and read its content
    with open(file_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile("hap5_expr17_chrI.qbed.gz", file_content, content_type="application/gzip")
        data["file"] = upload_file
        # note: test passing the regulator_locus_tag and source_name
        # instead of the regulator and source ids works
        data.pop("source")
        data["source_name"] = cc_datasource.name
        data.pop("regulator")
        data["regulator_locus_tag"] = regulator.genomicfeature.locus_tag

        response = client.post(reverse("api:binding-list"), data, format="multipart")

        assert response.status_code == 201, response.data
        assert Binding.objects.count() == 1
        assert (
            re.match(r"binding\/brent_nf_cc\/\d+\.qbed\.gz$", Binding.objects.get().file.name) is not None
        ), Binding.objects.get().file.name


@pytest.mark.django_db
def test_bulk_binding_upload(
    chipexo_datasource: DataSource, regulator: Regulator, chrmap: QuerySet, user: User, test_data_dict: dict
):
    token = Token.objects.get(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    # set path to test data and check that it exists
    base_path = os.path.join(os.path.dirname(__file__), "test_data")
    assert os.path.exists(base_path), f"path: {base_path}"

    csv_path = test_data_dict["config_files"]["files"][0]
    assert os.path.basename(csv_path) == "binding_bulk_chipexo_upload.csv", f"path: {csv_path}"
    assert os.path.exists(csv_path), f"path: {csv_path}"

    chipexo_file1_path = os.path.join(base_path, "binding/chipexo/28366_chrI.csv.gz")
    assert os.path.exists(chipexo_file1_path), f"path: {chipexo_file1_path}"

    chipexo_file2_path = os.path.join(base_path, "binding/chipexo/28363_chrI.csv.gz")
    assert os.path.exists(chipexo_file2_path), f"path: {chipexo_file2_path}"

    # create a new directory in a tmpdir and tar it
    with tempfile.TemporaryDirectory() as temp_dir:
        # create a tar file
        tar_file_path = os.path.join(temp_dir, "tarred_dir.tar.gz")
        with tarfile.open(tar_file_path, "w:gz") as tar:
            tar.add(chipexo_file1_path, arcname=os.path.basename(chipexo_file1_path))
            tar.add(chipexo_file2_path, arcname=os.path.basename(chipexo_file2_path))

        csv_handle = open(csv_path, "rb")
        tar_handle = open(tar_file_path, "rb")
        data = {
            "csv_file": SimpleUploadedFile("bulk_upload.csv", csv_handle.read(), content_type="text/csv"),
            "tarred_dir": SimpleUploadedFile("tarred_dir.tar", tar_handle.read(), content_type="application/gzip"),
        }

        response = client.post(reverse("api:binding-bulk-upload"), data, format="multipart")

        assert response.status_code == 201, response.data
        assert Binding.objects.count() == 2, Binding.objects.count()
        csv_handle.close()
        tar_handle.close()


@pytest.mark.django_db
def test_expression_single_upload(mcisaac_datasource: DataSource, regulator: Regulator, chrmap: QuerySet, user: User):
    token = Token.objects.get(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    data = model_to_dict_select(ExpressionFactory.build())
    # set path to test data and check that it exists
    file_path = os.path.join(
        os.path.dirname(__file__), "test_data", "expression/mcisaac/hap5_15min_mcisaac_chr1.csv.gz"
    )
    assert os.path.exists(file_path), f"path: {file_path}"

    # Open the file and read its content
    with open(file_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile(
            "hap5_15min_mcisaac_chr1.csv.gz", file_content, content_type="application/gzip"
        )
        data["file"] = upload_file
        data["source"] = mcisaac_datasource.id
        # test that passing the regulator symbol works
        data.pop("regulator")
        data["regulator_symbol"] = regulator.genomicfeature.symbol

        response = client.post(reverse("api:expression-list"), data, format="multipart")

        assert response.status_code == 201, response.data
        assert Expression.objects.count() == 1
        assert (
            re.match(r"expression\/mcisaac_oe\/\d+\.csv\.gz$", Expression.objects.get().file.name) is not None
        ), Expression.objects.get().file.name


@pytest.mark.django_db
def test_expression_bulk_upload(
    chrmap: QuerySet, hu_datasource: DataSource, mcisaac_datasource: DataSource, user: User
):
    token = Token.objects.get(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    GenomicFeatureFactory.create(symbol="HAP5")

    # RegulatorFactory.create(id=1)
    # RegulatorFactory.create(id=2)

    # set path to test data and check that it exists
    base_path = os.path.join(os.path.dirname(__file__), "test_data")
    assert os.path.exists(base_path), f"path: {base_path}"

    csv_path = os.path.join(base_path, "config_files/expression_bulk_upload.csv")
    assert os.path.exists(csv_path), f"path: {csv_path}"

    expression_filepath1 = os.path.join(
        os.path.dirname(__file__), "test_data", "expression/mcisaac/hap5_15min_mcisaac_chr1.csv.gz"
    )
    assert os.path.exists(expression_filepath1), f"path: {expression_filepath1}"

    expression_filepath2 = os.path.join(os.path.dirname(__file__), "test_data", "expression/hu/hap5_hu_chr1.csv.gz")
    assert os.path.exists(expression_filepath2), f"path: {expression_filepath2}"

    # create a tar file in a tempdir and add the expression files to it
    with tempfile.TemporaryDirectory() as temp_dir:
        tar_file_path = os.path.join(temp_dir, "tarred_dir.tar.gz")
        with tarfile.open(tar_file_path, "w:gz") as tar:
            tar.add(expression_filepath1, arcname=os.path.basename(expression_filepath1))
            tar.add(expression_filepath2, arcname=os.path.basename(expression_filepath2))

        csv_handle = open(csv_path, "rb")
        tar_handle = open(tar_file_path, "rb")
        data = {
            "csv_file": SimpleUploadedFile("bulk_upload.csv", csv_handle.read(), content_type="text/csv"),
            "tarred_dir": SimpleUploadedFile("tarred_dir.tar", tar_handle.read(), content_type="application/gzip"),
        }

        response = client.post(reverse("api:expression-bulk-upload"), data, format="multipart")

        assert response.status_code == 201, response.data
        assert Expression.objects.count() == 2, Expression.objects.count()
        csv_handle.close()
        tar_handle.close()


@pytest.mark.django_db
def test_rank_response_summary(
    chrmap: QuerySet,
    fileformat: QuerySet,
    chipexo_datasource: DataSource,
    regulator: Regulator,
    user: User,
    test_data_dict: dict,
    mcisaac_datasource: DataSource,
):
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = user

    token = Token.objects.get(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    # set path to test data and check that it exists
    promoterset_path = test_data_dict["promoters"]["files"][1]
    assert os.path.basename(promoterset_path) == "yiming_promoters_chrI.bed.gz"
    assert os.path.exists(promoterset_path), f"path: {promoterset_path}"

    expression_path = test_data_dict["expression"]["mcisaac"]["files"][0]
    assert os.path.basename(expression_path) == "hap5_15min_mcisaac_chr1.csv.gz"
    assert os.path.exists(expression_path), f"path: {expression_path}"

    # Open the file and read its content
    with open(promoterset_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile("yiming_promoters_chrI.bed.gz", file_content, content_type="application/gzip")
        data = model_to_dict_select(PromoterSetFactory.build(name="yiming", file=upload_file))
        serializer = PromoterSetSerializer(data=data, context={"request": request})
        assert serializer.is_valid() is True, serializer.errors
        serializer.save()

    # create the chipexo Binding record
    file_path = os.path.join(os.path.dirname(__file__), "test_data", "binding/chipexo/28366_chrI.csv.gz")
    assert os.path.exists(file_path), f"path: {file_path}"

    # Open the file and read its content
    with open(expression_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile("28366_chrI.csv.gz", file_content, content_type="application/gzip")
        data = model_to_dict_select(
            ExpressionFactory.build(source=mcisaac_datasource, regulator=regulator, file=upload_file)
        )
        expression_serializer = ExpressionSerializer(data=data, context={"request": request})
        assert expression_serializer.is_valid() is True, serializer.errors
        expression_serializer.save()

    # Open the file and read its content
    with open(file_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile("28366_chrI.csv.gz", file_content, content_type="application/gzip")
        data = model_to_dict_select(
            BindingFactory.build(source=chipexo_datasource, regulator=regulator, file=upload_file)
        )

        settings.CELERY_TASK_ALWAYS_EAGER = True
        response = client.post(reverse("api:binding-list"), data, format="multipart")
        assert response.status_code == 201, response.data
        assert Binding.objects.count() == 1
        assert PromoterSetSig.objects.count() == 1
        assert RankResponse.objects.count() == 1

    response = client.get(reverse("api:rankresponse-summary"), {"rank_response_id": RankResponse.objects.first().id})
    assert response.status_code == 200, response.data
