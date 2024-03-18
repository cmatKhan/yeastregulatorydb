import io
import os
import re
import tarfile
import tempfile
from urllib.parse import urlencode

import pandas as pd
import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.query import QuerySet
from django.http import QueryDict
from django.test import RequestFactory
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from yeastregulatorydb.users.models import User

from ..api.serializers import (
    BindingSerializer,
    CallingCardsBackgroundSerializer,
    ExpressionSerializer,
    PromoterSetSerializer,
    PromoterSetSigSerializer,
)
from ..api.views import ChrMapViewSet, GenomicFeatureViewSet
from ..models import Binding, BindingManualQC, ChrMap, DataSource, Expression, PromoterSetSig, Regulator
from .factories import (
    BindingFactory,
    CallingCardsBackgroundFactory,
    ExpressionFactory,
    GenomicFeatureFactory,
    PromoterSetFactory,
    PromoterSetSigFactory,
    RegulatorFactory,
)
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


def test_bulk_genomicfeature_upload(user: User, chrmap: QuerySet, test_data_dict: dict):
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = user

    token = Token.objects.get(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    genomicfeature_path = next(
        file for file in test_data_dict["genome"]["files"] if os.path.basename(file) == "chr1_genes.csv.gz"
    )
    assert os.path.exists(genomicfeature_path), f"path: {genomicfeature_path}"

    # Open the file and read its content
    with open(genomicfeature_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile("genomicfeature.csv.gz", file_content, content_type="application/gzip")
        data = {"csv_file": upload_file}

        response = client.post(reverse("api:genomicfeature-bulk-record-upload"), data, format="multipart")

        assert response.status_code == 201, response.data


@pytest.mark.django_db
def test_single_binding_upload(
    cc_datasource: DataSource,
    regulator: Regulator,
    chrmap: QuerySet,
    test_data_dict: dict,
    user: User,
    fileformat: QuerySet,
    mcisaac_datasource: DataSource,
):
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = user

    token = Token.objects.get(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    expression_path = next(
        file
        for file in test_data_dict["expression"]["mcisaac"]["files"]
        if os.path.basename(file) == "hap5_15min_mcisaac_chr1.csv.gz"
    )
    assert os.path.exists(expression_path), f"path: {expression_path}"

    # Open the file and read its content
    with open(expression_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile("28366_chrI.csv.gz", file_content, content_type="application/gzip")
        data = model_to_dict_select(
            ExpressionFactory.build(source=mcisaac_datasource, regulator=regulator, file=upload_file)
        )
        expression_serializer = ExpressionSerializer(data=data, context={"request": request})
        assert expression_serializer.is_valid() is True, expression_serializer.errors
        expression_serializer.save()

    # set path to test data and check that it exists
    promoterset_path = next(
        file
        for file in test_data_dict["promoters"]["files"]
        if os.path.basename(file) == "yiming_promoters_chrI.bed.gz"
    )
    assert os.path.exists(promoterset_path), f"path: {promoterset_path}"

    # Open the file and read its content
    with open(promoterset_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile("yiming_promoters_chrI.bed.gz", file_content, content_type="application/gzip")
        data = model_to_dict_select(PromoterSetFactory.build(name="yiming", file=upload_file))
        serializer = PromoterSetSerializer(data=data, context={"request": request})
        assert serializer.is_valid() is True, serializer.errors
        serializer.save()

    background_path = next(
        file
        for file in test_data_dict["background"]["files"]
        if os.path.basename(file) == "adh1_background_chrI.qbed.gz"
    )
    assert os.path.exists(background_path), f"path: {background_path}"

    # Open the file and read its content
    with open(background_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile("adh1_background_chrI.qbed.gz", file_content, content_type="application/gzip")
        data = model_to_dict_select(
            CallingCardsBackgroundFactory.build(
                name="adh1", fileformat=fileformat.get(fileformat="qbed"), file=upload_file
            )
        )
        ccbackground_serializer = CallingCardsBackgroundSerializer(data=data, context={"request": request})
        assert ccbackground_serializer.is_valid() is True, ccbackground_serializer.errors
        ccbackground_serializer.save()

    binding_path = next(
        file
        for file in test_data_dict["binding"]["callingcards"]["files"]
        if os.path.basename(file) == "hap5_expr17_chr1_ucsc.qbed.gz"
    )
    assert os.path.exists(binding_path), f"path: {binding_path}"

    # Open the file and read its content
    with open(binding_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile("hap5_expr17_chrI.qbed.gz", file_content, content_type="application/gzip")
        data = model_to_dict_select(BindingFactory.build())
        # set path to test data and check that it exists
        data["file"] = upload_file
        # note: test passing the regulator_locus_tag and source_name
        # instead of the regulator and source ids works
        data.pop("source")
        data["source_name"] = cc_datasource.name
        data.pop("regulator")
        data["regulator_locus_tag"] = regulator.genomicfeature.locus_tag

        # Define your query parameters
        query_params = {"testing": "True"}

        # Create the URL for the request
        url = reverse("api:binding-list")

        # Add the query parameters to the URL
        url += "?" + urlencode(query_params)

        settings.CELERY_TASK_ALWAYS_EAGER = True
        response = client.post(url, data, format="multipart")

        assert response.status_code == 201, response.data
        assert Binding.objects.count() == 1
        assert (
            re.match(r"binding\/brent_nf_cc\/\d+\.qbed\.gz$", Binding.objects.get().file.name) is not None
        ), Binding.objects.get().file.name
        # assert that there exists a promotersetsig with this binding instance id
        assert PromoterSetSig.objects.count() == 1, PromoterSetSig.objects.count()
        assert PromoterSetSig.objects.filter(binding=Binding.objects.get()).exists(), PromoterSetSig.objects.all()
        # assert that there is a rankresponse with the promotersetsig instance id
        # assert RankResponse.objects.count() == 1, RankResponse.objects.count()
        # assert RankResponse.objects.filter(
        #     promotersetsig=PromoterSetSig.objects.get()
        # ).exists(), RankResponse.objects.all()


@pytest.mark.django_db
def test_single_binding_harbison_upload(
    harbison_datasource: DataSource,
    regulator: Regulator,
    chrmap: QuerySet,
    test_data_dict: dict,
    user: User,
    fileformat: QuerySet,
    mcisaac_datasource: DataSource,
):
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = user

    token = Token.objects.get(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    genomicfeature_instance = GenomicFeatureFactory.create(symbol="RTG3")
    rtg3_regulator = RegulatorFactory.create(genomicfeature=genomicfeature_instance)

    expression_path = next(
        file
        for file in test_data_dict["expression"]["mcisaac"]["files"]
        if os.path.basename(file) == "140_SMY2111_20160421_P_ZEV_15.csv.gz"
    )
    assert os.path.exists(expression_path), f"path: {expression_path}"

    # Open the file and read its content
    with open(expression_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile(
            "140_SMY2111_20160421_P_ZEV_15.csv.gz", file_content, content_type="application/gzip"
        )
        data = model_to_dict_select(
            ExpressionFactory.build(source=mcisaac_datasource, regulator=rtg3_regulator, file=upload_file)
        )
        expression_serializer = ExpressionSerializer(data=data, context={"request": request})
        assert expression_serializer.is_valid() is True, expression_serializer.errors
        expression_serializer.save()

    # set path to test data and check that it exists
    promoterset_path = next(
        file
        for file in test_data_dict["promoters"]["files"]
        if os.path.basename(file) == "yiming_promoters_chrI.bed.gz"
    )
    assert os.path.exists(promoterset_path), f"path: {promoterset_path}"

    # Open the file and read its content
    with open(promoterset_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile("yiming_promoters_chrI.bed.gz", file_content, content_type="application/gzip")
        data = model_to_dict_select(PromoterSetFactory.build(name="yiming", file=upload_file))
        serializer = PromoterSetSerializer(data=data, context={"request": request})
        assert serializer.is_valid() is True, serializer.errors
        serializer.save()

    background_path = next(
        file
        for file in test_data_dict["background"]["files"]
        if os.path.basename(file) == "adh1_background_chrI.qbed.gz"
    )
    assert os.path.exists(background_path), f"path: {background_path}"

    # Open the file and read its content
    with open(background_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile("adh1_background_chrI.qbed.gz", file_content, content_type="application/gzip")
        data = model_to_dict_select(
            CallingCardsBackgroundFactory.build(
                name="adh1", fileformat=fileformat.get(fileformat="qbed"), file=upload_file
            )
        )
        ccbackground_serializer = CallingCardsBackgroundSerializer(data=data, context={"request": request})
        assert ccbackground_serializer.is_valid() is True, ccbackground_serializer.errors
        ccbackground_serializer.save()

    binding_path = next(
        file
        for file in test_data_dict["binding"]["harbison"]["files"]
        if os.path.basename(file) == "140_H2O2Lo.csv.gz"
    )
    assert os.path.exists(binding_path), f"path: {binding_path}"

    # Open the file and read its content
    with open(binding_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile("140_H2O2Lo.csv.gz", file_content, content_type="application/gzip")
        data = model_to_dict_select(BindingFactory.build())
        # set path to test data and check that it exists
        data["file"] = upload_file
        # note: test passing the regulator_locus_tag and source_name
        # instead of the regulator and source ids works
        data.pop("source")
        data["source_name"] = harbison_datasource.name
        data.pop("regulator")
        data["regulator_symbol"] = "RTG3"  # regulator.genomicfeature.locus_tag
        data["condition"] = "H2O2Lo"

        # Define your query parameters
        query_params = {"testing": "True"}

        # Create the URL for the request
        url = reverse("api:binding-list")

        # Add the query parameters to the URL
        url += "?" + urlencode(query_params)

        settings.CELERY_TASK_ALWAYS_EAGER = True
        response = client.post(url, data, format="multipart")

        assert response.status_code == 201, response.data
        assert Binding.objects.count() == 1
        assert Binding.objects.get().file.name == "", Binding.objects.get().file.name
        # assert that there exists a promotersetsig with this binding instance id
        assert PromoterSetSig.objects.count() == 1, PromoterSetSig.objects.count()
        assert PromoterSetSig.objects.filter(binding=Binding.objects.get()).exists(), PromoterSetSig.objects.all()
        # assert that there is a rankresponse with the promotersetsig instance id
        # assert RankResponse.objects.count() == 1, RankResponse.objects.count()
        # assert RankResponse.objects.filter(
        #     promotersetsig=PromoterSetSig.objects.get()
        # ).exists(), RankResponse.objects.all()


@pytest.mark.django_db
def test_single_binding_upload_with_promotersetsig_and_combinedfile(
    harbison_datasource: DataSource,
    mcisaac_datasource: DataSource,
    regulator: Regulator,
    user: User,
    test_data_dict: dict,
):
    """some uploads to the binding table remove the `file` from the binding instance. `file`
    in this case is allowed to be NULL. Once the binding instance is created, that instance
    `id` and the originally uploaded `file` are used to create a promtersetsig instance.
    the `rankresponse` task is also automatically submitted
    """
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = user

    token = Token.objects.get(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    expression_path = next(
        file
        for file in test_data_dict["expression"]["mcisaac"]["files"]
        if os.path.basename(file) == "hap5_15min_mcisaac_chr1.csv.gz"
    )
    assert os.path.exists(expression_path), f"path: {expression_path}"

    # Open the file and read its content
    with open(expression_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile("28366_chrI.csv.gz", file_content, content_type="application/gzip")
        data = model_to_dict_select(
            ExpressionFactory.build(source=mcisaac_datasource, regulator=regulator, file=upload_file)
        )
        expression_serializer = ExpressionSerializer(data=data, context={"request": request})
        assert expression_serializer.is_valid() is True, expression_serializer.errors
        expression_serializer.save()

    data = model_to_dict_select(BindingFactory.build())
    # set path to test data and check that it exists
    file_path = next(
        file
        for file in test_data_dict["binding"]["harbison"]["files"]
        if os.path.basename(file) == "hap5_harbison_chr1.csv.gz"
    )
    assert os.path.exists(file_path), f"path: {file_path}"

    # Open the file and read its content
    with open(file_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile("hap5_harbison_chrI.csv.gz", file_content, content_type="application/gzip")
        data["file"] = upload_file
        # note: test passing the regulator_locus_tag and source_name
        # instead of the regulator and source ids works
        data.pop("source")
        data["source_name"] = harbison_datasource.name
        data.pop("regulator")
        data["regulator_locus_tag"] = regulator.genomicfeature.locus_tag

        # Define your query parameters
        query_params = {"testing": "True"}

        # Create the URL for the request
        url = reverse("api:binding-list")

        # Add the query parameters to the URL
        url += "?" + urlencode(query_params)

        settings.CELERY_TASK_ALWAYS_EAGER = True
        response = client.post(url, data, format="multipart")

        assert response.status_code == 201, response.data
        assert Binding.objects.count() == 1
        # assert the `file` field is null
        assert Binding.objects.get().file.name == ""
        # assert PromoterSetSig with the Binding instance `id` exists
        assert PromoterSetSig.objects.count() == 1, PromoterSetSig.objects.count()
        assert PromoterSetSig.objects.filter(binding=Binding.objects.get()).exists(), PromoterSetSig.objects.all()
        # assert the `file` field of the PromoterSetSig instance is not null
        assert PromoterSetSig.objects.get().file.name != ""
        assert (
            re.match(r"promotersetsig\/\d+\.csv\.gz$", PromoterSetSig.objects.get().file.name) is not None
        ), PromoterSetSig.objects.get().file.name
        # assert RankResponse.objects.count() == 1, RankResponse.objects.count()

        # get the response from the expression-combined endpoint
        response = client.get(reverse("api:promotersetsig-combined"), {"regulator_symbol": "HAP5"})

        assert response.status_code == 200, response.data

        # Save the response content to a BytesIO object
        content = io.BytesIO(b"".join(response.streaming_content))
        # Reset the cursor to the beginning of the file
        content.seek(0)
        # Read the BytesIO object into a DataFrame
        df = pd.read_csv(content, compression="gzip")
        assert "regulator_id" in df.columns, df.columns
        assert "regulator_locus_tag" in df.columns, df.columns
        assert "regulator_symbol" in df.columns, df.columns
        assert "target_id" in df.columns, df.columns
        assert "target_locus_tag" in df.columns, df.columns
        assert "target_symbol" in df.columns, df.columns
        assert "record_id" in df.columns, df.columns
        assert "effect" in df.columns, df.columns
        assert "pvalue" in df.columns, df.columns


@pytest.mark.django_db
def test_bulk_binding_upload(
    chipexo_datasource: DataSource,
    cc_datasource: DataSource,
    kemmeren_datasource: DataSource,
    regulator: Regulator,
    chrmap: QuerySet,
    fileformat: QueryDict,
    user: User,
    test_data_dict: dict,
):
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = user

    token = Token.objects.get(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    expression_path = next(
        file
        for file in test_data_dict["expression"]["kemmeren"]["files"]
        if os.path.basename(file) == "hap5_kemmeren_chr1.csv.gz"
    )
    assert os.path.exists(expression_path), f"path: {expression_path}"

    # Open the file and read its content
    with open(expression_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile("hap5_kemmeren_chrI.csv.gz", file_content, content_type="application/gzip")
        data = model_to_dict_select(
            ExpressionFactory.build(source=kemmeren_datasource, regulator=regulator, file=upload_file)
        )
        expression_serializer = ExpressionSerializer(data=data, context={"request": request})
        assert expression_serializer.is_valid() is True, expression_serializer.errors
        expression_serializer.save()

    # set path to test data and check that it exists
    promoterset_path = next(
        file
        for file in test_data_dict["promoters"]["files"]
        if os.path.basename(file) == "yiming_promoters_chrI.bed.gz"
    )
    assert os.path.exists(promoterset_path), f"path: {promoterset_path}"

    # Open the file and read its content
    with open(promoterset_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile("yiming_promoters_chrI.bed.gz", file_content, content_type="application/gzip")
        data = model_to_dict_select(PromoterSetFactory.build(name="yiming", file=upload_file))
        serializer = PromoterSetSerializer(data=data, context={"request": request})
        assert serializer.is_valid() is True, serializer.errors
        serializer.save()

    background_path = next(
        file
        for file in test_data_dict["background"]["files"]
        if os.path.basename(file) == "adh1_background_chrI.qbed.gz"
    )
    assert os.path.exists(background_path), f"path: {background_path}"

    # Open the file and read its content
    with open(background_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile("adh1_background_chrI.qbed.gz", file_content, content_type="application/gzip")
        data = model_to_dict_select(
            CallingCardsBackgroundFactory.build(
                name="adh1", fileformat=fileformat.get(fileformat="qbed"), file=upload_file
            )
        )
        ccbackground_serializer = CallingCardsBackgroundSerializer(data=data, context={"request": request})
        assert ccbackground_serializer.is_valid() is True, ccbackground_serializer.errors
        ccbackground_serializer.save()

    # upload cc background data

    chipexo_csv_path = next(
        file
        for file in test_data_dict["config"]["files"]
        if os.path.basename(file) == "binding_bulk_chipexo_upload.csv"
    )
    assert os.path.exists(chipexo_csv_path), f"path: {chipexo_csv_path}"

    cc_csv_path = next(
        file for file in test_data_dict["config"]["files"] if os.path.basename(file) == "binding_bulk_cc_upload.csv"
    )
    assert os.path.exists(cc_csv_path), f"path: {cc_csv_path}"

    chipexo_file1_path = next(
        file for file in test_data_dict["binding"]["chipexo"]["files"] if os.path.basename(file) == "28366_chrI.csv.gz"
    )
    assert os.path.exists(chipexo_file1_path), f"path: {chipexo_file1_path}"

    chipexo_file2_path = next(
        file for file in test_data_dict["binding"]["chipexo"]["files"] if os.path.basename(file) == "28363_chrI.csv.gz"
    )
    assert os.path.exists(chipexo_file2_path), f"path: {chipexo_file2_path}"

    cc_filepath1 = next(
        file
        for file in test_data_dict["binding"]["callingcards"]["files"]
        if os.path.basename(file) == "ccexperiment_292_hap5_chrI.csv.gz"
    )
    assert os.path.exists(cc_filepath1), f"path: {cc_filepath1}"

    cc_filepath2 = next(
        file
        for file in test_data_dict["binding"]["callingcards"]["files"]
        if os.path.basename(file) == "ccexperiment_297_hap5_chrI.csv.gz"
    )
    assert os.path.exists(cc_filepath2), f"path: {cc_filepath2}"

    # create a new directory in a tmpdir and tar it
    with tempfile.TemporaryDirectory() as temp_dir:
        # create a tar file
        tar_file_path = os.path.join(temp_dir, "tarred_dir.tar.gz")
        with tarfile.open(tar_file_path, "w:gz") as tar:
            tar.add(chipexo_file1_path, arcname=os.path.basename(chipexo_file1_path))
            tar.add(chipexo_file2_path, arcname=os.path.basename(chipexo_file2_path))

        csv_handle = open(chipexo_csv_path, "rb")
        tar_handle = open(tar_file_path, "rb")
        data = {
            "csv_file": SimpleUploadedFile("bulk_upload.csv", csv_handle.read(), content_type="text/csv"),
            "tarred_dir": SimpleUploadedFile("tarred_dir.tar", tar_handle.read(), content_type="application/gzip"),
            "testing": True,
        }

        settings.CELERY_TASK_ALWAYS_EAGER = True
        response = client.post(reverse("api:binding-bulk-file-upload"), data, format="multipart")

        assert response.status_code == 201, response.data
        assert Binding.objects.count() == 2, Binding.objects.count()
        assert PromoterSetSig.objects.count() == 2, PromoterSetSig.objects.count()
        csv_handle.close()
        tar_handle.close()

    # add two more callingcards files
    with tempfile.TemporaryDirectory() as temp_dir:
        # create a tar file
        tar_file_path = os.path.join(temp_dir, "tarred_dir.tar.gz")
        with tarfile.open(tar_file_path, "w:gz") as tar:
            tar.add(cc_filepath1, arcname=os.path.basename(cc_filepath1))
            tar.add(cc_filepath2, arcname=os.path.basename(cc_filepath2))

        csv_handle = open(cc_csv_path, "rb")
        tar_handle = open(tar_file_path, "rb")
        data = {
            "csv_file": SimpleUploadedFile("bulk_upload.csv", csv_handle.read(), content_type="text/csv"),
            "tarred_dir": SimpleUploadedFile("tarred_dir.tar", tar_handle.read(), content_type="application/gzip"),
            "testing": True,
        }

        settings.CELERY_TASK_ALWAYS_EAGER = True
        response = client.post(reverse("api:binding-bulk-file-upload"), data, format="multipart")

        assert response.status_code == 201, response.data
        assert Binding.objects.count() == 4, Binding.objects.count()
        assert BindingManualQC.objects.count() == 4, BindingManualQC.objects.count()
        assert PromoterSetSig.objects.count() == 4, PromoterSetSig.objects.count()
        csv_handle.close()
        tar_handle.close()

        qbed_qc_records = BindingManualQC.objects.filter(binding__source__fileformat__fileformat="qbed")

        # test the BindingManualQC bulk-file-upload endpoint by updating the data_usable
        # field to 'passing' for the BindingManualQC instances foreign keyed to the
        # Binding instances with the qbed fileformat
        data = [{"id": record.id, "data_usable": "pass"} for record in qbed_qc_records]
        response = client.post(
            reverse("api:bindingmanualqc-bulk-update"), {"data": data, "testing": True}, format="json"
        )

        assert response.status_code == 204, response.data
        Binding.objects.count() == 5, Binding.objects.count()
        PromoterSetSig.objects.count() == 5, PromoterSetSig.objects.count()


@pytest.mark.django_db()
def test_expression_task_upload(
    hu_datasource: DataSource, chrmap: QuerySet, fileformat: QueryDict, test_data_dict: dict, user: User
):
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = user

    token = Token.objects.get(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    genomicfeature_instance = GenomicFeatureFactory.create(symbol="RTG3")
    rtg3_regulator = RegulatorFactory.create(genomicfeature=genomicfeature_instance)

    binding_path = next(
        file
        for file in test_data_dict["binding"]["harbison"]["files"]
        if os.path.basename(file) == "140_H2O2Lo.csv.gz"
    )
    assert os.path.exists(binding_path), f"path: {binding_path}"

    # Open the file and read its content
    with open(binding_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile("140_H2O2Lo.csv.gz", file_content, content_type="application/gzip")
        data = model_to_dict_select(BindingFactory.build())
        # set path to test data and check that it exists
        data["file"] = upload_file
        # note: test passing the regulator_locus_tag and source_name
        # instead of the regulator and source ids works
        data.pop("source")
        data["source_name"] = hu_datasource.name
        data.pop("regulator")
        data["regulator_symbol"] = "RTG3"
        data["condition"] = "H2O2Lo"
        binding_serializer = BindingSerializer(data=data, context={"request": request})
        assert binding_serializer.is_valid() is True, binding_serializer.errors
        binding_instance = binding_serializer.save()

    promotersetsig_path = next(
        file for file in test_data_dict["promotersetsig"]["files"] if os.path.basename(file) == "RTG3_harbison.csv.gz"
    )
    assert os.path.exists(promotersetsig_path), f"path: {promotersetsig_path}"

    # Open the file and read its content
    with open(promotersetsig_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile("RTG3_harbison.csv.gz", file_content, content_type="application/gzip")
        data = model_to_dict_select(PromoterSetSigFactory.build())
        data["file"] = upload_file
        data["binding"] = binding_instance.id
        data["fileformat"] = fileformat.get(fileformat="array").id
        promotersetsig_serializer = PromoterSetSigSerializer(data=data, context={"request": request})
        assert promotersetsig_serializer.is_valid() is True, promotersetsig_serializer.errors
        promotersetsig_serializer.save()

    expression_file_path = next(
        file for file in test_data_dict["expression"]["hu"]["files"] if os.path.basename(file) in "RTG3.csv.gz"
    )
    assert os.path.exists(expression_file_path), f"path: {expression_file_path}"

    expression_data = model_to_dict_select(ExpressionFactory.build())
    # set path to test data and check that it exists

    # Open the file and read its content
    with open(expression_file_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile("RTG3.csv.gz", file_content, content_type="application/gzip")
        expression_data["file"] = upload_file
        expression_data["source"] = hu_datasource.id
        # test that passing the regulator symbol works
        expression_data["regulator"] = rtg3_regulator.id

        # Define your query parameters
        query_params = {"testing": "True"}

        # Create the URL for the request
        url = reverse("api:expression-list")

        # Add the query parameters to the URL
        url += "?" + urlencode(query_params)

        settings.CELERY_TASK_ALWAYS_EAGER = True
        response = client.post(url, expression_data, format="multipart")

        assert response.status_code == 201, response.data
        assert Expression.objects.count() == 1
        assert (
            re.match(r"expression\/hu_reimann_tfko\/\d+\.csv\.gz$", Expression.objects.get().file.name) is not None
        ), Expression.objects.get().file.name
        # assert RankResponse.objects.count() == 1, RankResponse.objects.count()


@pytest.mark.django_db
def test_expression_bulk_upload_and_combinedfile(
    chrmap: QuerySet, hu_datasource: DataSource, mcisaac_datasource: DataSource, user: User, test_data_dict: dict
):
    token = Token.objects.get(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    GenomicFeatureFactory.create(symbol="HAP5")

    # set path to test data and check that it exists
    csv_path = next(
        file for file in test_data_dict["config"]["files"] if os.path.basename(file) == "expression_bulk_upload.csv"
    )
    assert os.path.exists(csv_path), f"path: {csv_path}"

    expression_filepath1 = next(
        file
        for file in test_data_dict["expression"]["mcisaac"]["files"]
        if os.path.basename(file) == "hap5_15min_mcisaac_chr1.csv.gz"
    )
    assert os.path.exists(expression_filepath1), f"path: {expression_filepath1}"

    expression_filepath2 = next(
        file for file in test_data_dict["expression"]["hu"]["files"] if os.path.basename(file) == "hap5_hu_chr1.csv.gz"
    )
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

        response = client.post(reverse("api:expression-bulk-file-upload"), data, format="multipart")

        assert response.status_code == 201, response.data
        assert Expression.objects.count() == 2, Expression.objects.count()
        csv_handle.close()
        tar_handle.close()

        # get the response from the expression-combined endpoint
        response = client.get(reverse("api:expression-combined"), {"regulator_symbol": "HAP5"})

        assert response.status_code == 200, response.data

        # Save the response content to a BytesIO object
        content = io.BytesIO(b"".join(response.streaming_content))
        # Reset the cursor to the beginning of the file
        content.seek(0)
        # Read the BytesIO object into a DataFrame
        df = pd.read_csv(content, compression="gzip")
        assert "regulator_id" in df.columns, df.columns
        assert "regulator_locus_tag" in df.columns, df.columns
        assert "regulator_symbol" in df.columns, df.columns
        assert "target_id" in df.columns, df.columns
        assert "target_locus_tag" in df.columns, df.columns
        assert "target_symbol" in df.columns, df.columns
        assert "record_id" in df.columns, df.columns
        assert "effect" in df.columns, df.columns
        assert "pvalue" in df.columns, df.columns


# @pytest.mark.django_db
# def test_rank_response_summary(
#     chrmap: QuerySet,
#     fileformat: QuerySet,
#     chipexo_datasource: DataSource,
#     regulator: Regulator,
#     user: User,
#     test_data_dict: dict,
#     mcisaac_datasource: DataSource,
# ):
#     factory = APIRequestFactory()
#     request = factory.get("/")
#     request.user = user

#     token = Token.objects.get(user=user)
#     client = APIClient()
#     client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

#     # set path to test data and check that it exists
#     promoterset_path = next(
#         file
#         for file in test_data_dict["promoters"]["files"]
#         if os.path.basename(file) == "yiming_promoters_chrI.bed.gz"
#     )
#     assert os.path.exists(promoterset_path), f"path: {promoterset_path}"

#     expression_path = next(
#         file
#         for file in test_data_dict["expression"]["mcisaac"]["files"]
#         if os.path.basename(file) == "hap5_15min_mcisaac_chr1.csv.gz"
#     )
#     assert os.path.exists(expression_path), f"path: {expression_path}"

#     # Open the file and read its content
#     with open(promoterset_path, "rb") as file_obj:
#         file_content = file_obj.read()
#         # Create a SimpleUploadedFile instance
#         upload_file = SimpleUploadedFile("yiming_promoters_chrI.bed.gz",
#                                          file_content, content_type="application/gzip")
#         data = model_to_dict_select(PromoterSetFactory.build(name="yiming", file=upload_file))
#         serializer = PromoterSetSerializer(data=data, context={"request": request})
#         assert serializer.is_valid() is True, serializer.errors
#         serializer.save()

#     # create the chipexo Binding record
#     file_path = next(
#         file for file in test_data_dict["binding"]["chipexo"]["files"] \
#                   if os.path.basename(file) == "28366_chrI.csv.gz"
#     )
#     assert os.path.exists(file_path), f"path: {file_path}"

#     # Open the file and read its content
#     with open(expression_path, "rb") as file_obj:
#         file_content = file_obj.read()
#         # Create a SimpleUploadedFile instance
#         upload_file = SimpleUploadedFile("28366_chrI.csv.gz", file_content, content_type="application/gzip")
#         data = model_to_dict_select(
#             ExpressionFactory.build(source=mcisaac_datasource, regulator=regulator, file=upload_file)
#         )
#         expression_serializer = ExpressionSerializer(data=data, context={"request": request})
#         assert expression_serializer.is_valid() is True, serializer.errors
#         expression_serializer.save()

#     # Open the file and read its content
#     with open(file_path, "rb") as file_obj:
#         file_content = file_obj.read()
#         # Create a SimpleUploadedFile instance
#         upload_file = SimpleUploadedFile("28366_chrI.csv.gz", file_content, content_type="application/gzip")
#         data = model_to_dict_select(
#             BindingFactory.build(source=chipexo_datasource, regulator=regulator, file=upload_file)
#         )
#         # Define your query parameters
#         query_params = {"testing": "True"}

#         # Create the URL for the request
#         url = reverse("api:binding-list")

#         # Add the query parameters to the URL
#         url += "?" + urlencode(query_params)

#         settings.CELERY_TASK_ALWAYS_EAGER = True
#         response = client.post(url, data, format="multipart")

#         assert response.status_code == 201, response.data
#         assert Binding.objects.count() == 1
#         assert PromoterSetSig.objects.count() == 1
#         assert RankResponse.objects.count() == 1

#     response = client.get(reverse("api:rankresponse-summary"), {"rank_response_id": RankResponse.objects.first().id})
#     assert response.status_code == 200, response.data
