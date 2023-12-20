import os
import re

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.query import QuerySet
from django.test import RequestFactory
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, force_authenticate

from yeastregulatorydb.users.models import User

from ..api.views import ChrMapViewSet, GenomicFeatureViewSet
from ..models import Binding, ChrMap, DataSource, Expression, Regulator
from .factories import BindingFactory, ExpressionFactory, RegulatorFactory
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
        data["source"] = cc_datasource.id
        data["regulator"] = regulator.id

        response = client.post(reverse("api:binding-list"), data, format="multipart")

        assert response.status_code == 201, response.data
        assert Binding.objects.count() == 1
        assert (
            re.match(r"binding\/brent_nf_cc\/\d+\.qbed\.gz$", Binding.objects.get().file.name) is not None
        ), Binding.objects.get().file.name


@pytest.mark.django_db
def test_bulk_binding_upload(chipexo_datasource: DataSource, regulator: Regulator, chrmap: QuerySet, user: User):
    token = Token.objects.get(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    # set path to test data and check that it exists
    base_path = os.path.join(os.path.dirname(__file__), "test_data")
    assert os.path.exists(base_path), f"path: {base_path}"

    csv_path = os.path.join(base_path, "binding_bulk_chipexo_upload.csv")
    assert os.path.exists(csv_path), f"path: {csv_path}"

    chipexo_file1_path = os.path.join(base_path, "binding/chipexo/28366_chrI.csv.gz")
    assert os.path.exists(chipexo_file1_path), f"path: {chipexo_file1_path}"

    chipexo_file2_path = os.path.join(base_path, "binding/chipexo/28363_chrI.csv.gz")
    assert os.path.exists(chipexo_file2_path), f"path: {chipexo_file2_path}"

    csv_handle = open(csv_path, "rb")
    chipexo_file1_handle = open(chipexo_file1_path, "rb")
    chipexo_file2_handle = open(chipexo_file2_path, "rb")
    data = {
        "csv_file": SimpleUploadedFile("bulk_upload.csv", csv_handle.read(), content_type="text/csv"),
        "files": [
            SimpleUploadedFile("28366.csv.gz", chipexo_file1_handle.read(), content_type="application/gzip"),
            SimpleUploadedFile("28363.csv.gz", chipexo_file2_handle.read(), content_type="application/gzip"),
        ],
    }

    response = client.post(reverse("api:binding-bulk-upload"), data, format="multipart")

    assert response.status_code == 201, response.data
    assert Binding.objects.count() == 2, Binding.objects.count()
    csv_handle.close()
    chipexo_file1_handle.close()
    chipexo_file2_handle.close()


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
        data["regulator"] = regulator.id

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

    RegulatorFactory.create(id=1)
    RegulatorFactory.create(id=2)

    # set path to test data and check that it exists
    base_path = os.path.join(os.path.dirname(__file__), "test_data")
    assert os.path.exists(base_path), f"path: {base_path}"

    csv_path = os.path.join(base_path, "expression_bulk_upload.csv")
    assert os.path.exists(csv_path), f"path: {csv_path}"

    expression_filepath1 = os.path.join(
        os.path.dirname(__file__), "test_data", "expression/mcisaac/hap5_15min_mcisaac_chr1.csv.gz"
    )
    assert os.path.exists(expression_filepath1), f"path: {expression_filepath1}"

    expression_filepath2 = os.path.join(os.path.dirname(__file__), "test_data", "expression/hu/hap5_hu_chr1.csv.gz")
    assert os.path.exists(expression_filepath2), f"path: {expression_filepath2}"

    csv_handle = open(csv_path, "rb")
    expression_file_handle1 = open(expression_filepath1, "rb")
    expression_file_handle2 = open(expression_filepath2, "rb")
    data = {
        "csv_file": SimpleUploadedFile("bulk_upload.csv", csv_handle.read(), content_type="text/csv"),
        "files": [
            SimpleUploadedFile(
                "hap5_15min_mcisaac_chr1.csv.gz", expression_file_handle1.read(), content_type="application/gzip"
            ),
            SimpleUploadedFile("hap5_hu_chr1.csv.gz", expression_file_handle2.read(), content_type="application/gzip"),
        ],
    }

    response = client.post(reverse("api:expression-bulk-upload"), data, format="multipart")

    assert response.status_code == 201, response.data
    assert Expression.objects.count() == 2, Expression.objects.count()
    csv_handle.close()
    expression_file_handle1.close()
    expression_file_handle2.close()
