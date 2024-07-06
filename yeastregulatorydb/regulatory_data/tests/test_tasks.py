import os
import tempfile
from urllib.parse import urlencode

import pandas as pd
import pytest
from celery.result import EagerResult
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Subquery
from django.db.models.query import QuerySet
from django.http import QueryDict
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APIRequestFactory

from yeastregulatorydb.regulatory_data.api.serializers import (
    BindingSerializer,
    ExpressionSerializer,
    PromoterSetSerializer,
)
from yeastregulatorydb.regulatory_data.models import (
    Binding,
    BindingConcatenated,
    BindingManualQC,
    CallingCardsBackground,
    DataSource,
    PromoterSet,
    PromoterSetSig,
    Regulator,
)
from yeastregulatorydb.regulatory_data.tasks import promoter_significance_combined_task, promoter_significance_task
from yeastregulatorydb.regulatory_data.tests.utils.model_to_dict_select import model_to_dict_select
from yeastregulatorydb.regulatory_data.utils import extract_file_from_storage
from yeastregulatorydb.users.models import User

from .factories import BindingFactory, ExpressionFactory, GenomicFeatureFactory, PromoterSetFactory, RegulatorFactory

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
def test_promoter_significance_task(
    clean_test_database,
    settings,
    chrmap: QuerySet,
    fileformat: QuerySet,
    chipexo_datasource: DataSource,
    regulator: Regulator,
    user: User,
    test_data_dict: dict,
):
    """test promoter_significance_task task"""
    # Create a request object and set the user
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = user

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

    # create the chipexo Binding record
    file_path = next(
        file for file in test_data_dict["binding"]["chipexo"]["files"] if os.path.basename(file) == "28366_chrI.csv.gz"
    )
    assert os.path.exists(file_path), f"path: {file_path}"

    # Open the file and read its content
    with open(file_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile("28366_chrI.csv.gz", file_content, content_type="application/gzip")
        data = model_to_dict_select(
            BindingFactory.build(source=chipexo_datasource, regulator=regulator, file=upload_file)
        )
        serializer = BindingSerializer(data=data, context={"request": request})
        assert serializer.is_valid() is True, serializer.errors
        instance = serializer.save()
        settings.CELERY_TASK_ALWAYS_EAGER = True
        task_result = promoter_significance_task.delay(
            instance.id, request.user.id, settings.CHIPEXO_PROMOTER_SIG_FORMAT
        )
        assert isinstance(task_result, EagerResult)
        assert isinstance(task_result.result, list)


# @pytest.mark.django_db
# def test_rank_response_task(
#     settings,
#     chrmap: QuerySet,
#     fileformat: QuerySet,
#     promoterset: PromoterSet,
#     user: User,
#     regulator: Regulator,
#     chipexo_datasource: DataSource,
#     mcisaac_datasource: DataSource,
#     test_data_dict: dict,
# ):
#     """test promoter_significance_task task"""
#     # Create a request object and set the user
#     factory = APIRequestFactory()
#     request = factory.get("/")
#     request.user = user

#     # create the promoter set record
#     promotersetsig_path = next(
#         file
#         for file in test_data_dict["binding"]["chipexo"]["files"]
#         if os.path.basename(file) == "28366_yiming_promoter_sig.csv.gz"
#     )
#     assert os.path.exists(promotersetsig_path), f"path: {promotersetsig_path}"

#     expression_path = next(
#         file
#         for file in test_data_dict["expression"]["mcisaac"]["files"]
#         if os.path.basename(file) == "hap5_15_mcisc_chr1.csv.gz"
#     )
#     assert os.path.exists(expression_path), f"path: {expression_path}"

#     binding_record = BindingFactory.create(source=chipexo_datasource, regulator=regulator)

#     BindingManualQCFactory.create(binding=binding_record)

#     # Open the file and read its content
#     with open(promotersetsig_path, "rb") as promotersetsig_file_obj:
#         promotersetsig_file_content = promotersetsig_file_obj.read()
#         # Create a SimpleUploadedFile instance
#         promotersetsig_upload_file = SimpleUploadedFile(
#             "28366_yiming_promoter_sig.csv.gz", promotersetsig_file_content, content_type="application/gzip"
#         )
#         promotersetsig_data = model_to_dict_select(
#             PromoterSetSigFactory.build(
#                 file=promotersetsig_upload_file,
#                 binding=binding_record,
#                 promoter=promoterset,
#                 fileformat=fileformat.get(fileformat="chipexo_promoter_sig"),
#             )
#         )
#         promotersetsig_serializer = PromoterSetSigSerializer(data=promotersetsig_data, context={"request": request})
#         assert promotersetsig_serializer.is_valid() is True, promotersetsig_serializer.errors
#         promotersetsig_instance = promotersetsig_serializer.save()

#     # Open the file and read its content
#     with open(expression_path, "rb") as file_obj:
#         file_content = file_obj.read()
#         # Create a SimpleUploadedFile instance
#         upload_file = SimpleUploadedFile("28366_chrI.csv.gz", file_content, content_type="application/gzip")
#         data = model_to_dict_select(
#             ExpressionFactory.build(source=mcisaac_datasource, regulator=binding_record.regulator, file=upload_file)
#         )
#         serializer = ExpressionSerializer(data=data, context={"request": request})
#         assert serializer.is_valid() is True, serializer.errors
#         serializer.save()

#     settings.CELERY_TASK_ALWAYS_EAGER = True
#     task_result = rank_response_task.delay(promotersetsig_instance.id, request.user.id)
#     assert isinstance(task_result, EagerResult)
#     assert isinstance(task_result.result, list)


@pytest.mark.django_db()
def test_promoter_significance_combined_task(
    clean_test_database,
    auth_token: Token,
    cc_datasource: DataSource,
    yiming_promoterset: PromoterSet,
    adh1_background: CallingCardsBackground,
    chrmap: QuerySet,
    fileformat: QueryDict,
    test_data_dict: dict,
):
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = auth_token.user

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token " + auth_token.key)

    genomicfeature_instance = GenomicFeatureFactory.create(symbol="HAP5")
    hap5_regulator = RegulatorFactory.create(genomicfeature=genomicfeature_instance)

    for ccfile in ["ccexperiment_292_hap5_chrI.csv.gz", "ccexperiment_302_hap5_chrI.csv.gz"]:
        binding_path = next(
            file for file in test_data_dict["binding"]["callingcards"]["files"] if os.path.basename(file) == ccfile
        )
        assert os.path.exists(binding_path), f"path: {binding_path}"

        # Open the file and read its content
        with open(binding_path, "rb") as file_obj:
            file_content = file_obj.read()
            # Create a SimpleUploadedFile instance
            upload_file = SimpleUploadedFile(ccfile, file_content, content_type="application/gzip")
            data = model_to_dict_select(BindingFactory.build())
            # set path to test data and check that it exists
            data["file"] = upload_file
            # note: test passing the regulator_locus_tag and source_name
            # instead of the regulator and source ids works
            data.pop("source")
            data["source_name"] = cc_datasource.name
            data.pop("regulator")
            data["regulator_locus_tag"] = hap5_regulator.genomicfeature.locus_tag

            # Define your query parameters
            query_params = {"testing": "True"}

            # Create the URL for the request
            url = reverse("api:binding-list")

            # Add the query parameters to the URL
            url += "?" + urlencode(query_params)

            settings.CELERY_TASK_ALWAYS_EAGER = True
            response = client.post(url, data, format="multipart")

            assert response.status_code == 201, response.data

    # get the Binding records
    binding_records = Binding.objects.all()

    # get the bindingmanualqc records associated with the binding_records and update
    # the data_usable field to "pass"
    BindingManualQC.objects.filter(single_binding__in=Subquery(binding_records.values("id"))).update(
        data_usable="pass"
    )

    settings.CELERY_TASK_ALWAYS_EAGER = True
    task_result = promoter_significance_combined_task.delay(
        request.user.id, hap5_regulator.id, cc_datasource.name, settings.CALLINGCARDS_PROMOTER_SIG_FORMAT
    )

    assert isinstance(task_result, EagerResult)
    assert isinstance(task_result.result, list)
    assert BindingConcatenated.objects.count() == 1
    # assert that exactly 1 of the PromoterSetSig records has a not null composite_binding field
    concat_id = PromoterSetSig.objects.get(composite_binding__isnull=False).id
    assert isinstance(concat_id, int)

    # Extract the files from each of the PromoterSetSig records, read them in as pandas DataFrames
    file_dict = {}
    for promotersetsig in PromoterSetSig.objects.all():
        with promotersetsig.file.open() as file_obj:
            # create a temporary directory context manager
            with tempfile.TemporaryDirectory() as temp_dir:
                file_path = extract_file_from_storage(promotersetsig.file)
                file_dict[promotersetsig.id] = pd.read_csv(file_path)

    # Ensure 'experiment_hops' column exists in all DataFrames
    for df in file_dict.values():
        assert "experiment_hops" in df.columns, "The 'experiment_hops' column should be present in all DataFrames"
        assert (
            "experiment_total_hops" in df.columns
        ), "The 'experiment_total_hops' column should be present in all DataFrames"
        assert "background_hops" in df.columns, "The 'background_hops' column should be present in all DataFrames"
        assert (
            "background_total_hops" in df.columns
        ), "The 'background_total_hops' column should be present in all DataFrames"

    # Identify the DataFrames for comparison
    other_ids = [key for key in file_dict.keys() if key != concat_id]
    assert len(other_ids) == 2, "There should be exactly two other PromoterSetSig records"

    df_concat = file_dict[concat_id]
    df_other1 = file_dict[other_ids[0]]
    df_other2 = file_dict[other_ids[1]]

    # Ensure that the shapes are the same before comparing values
    assert df_concat.shape == df_other1.shape == df_other2.shape, "Shapes of DataFrames should match for comparison"

    # Check that the experiment_hops values are equal
    assert df_concat["experiment_hops"].equals(
        df_other1["experiment_hops"] + df_other2["experiment_hops"]
    ), "The 'experiment_hops' values should be the sum of corresponding entries in df_other1 and df_other2"

    # check that experiment_total_hops equals the sum of the other binding data
    assert df_concat["experiment_total_hops"].equals(
        df_other1["experiment_total_hops"] + df_other2["experiment_total_hops"]
    ), "The 'experiment_total_hops' values should be the sum of corresponding entries in df_other1 and df_other2"

    # assert that the background_hops are the same for all DataFrames
    assert df_concat["background_hops"].equals(df_other1["background_hops"]) and df_other1["background_hops"].equals(
        df_other2["background_hops"]
    ), "The 'background_hops' should be the same in all three dataframes"

    # assert that the background_total_hops are the same for all DataFrames
    assert df_concat["background_total_hops"].equals(df_other1["background_total_hops"]) and df_other1[
        "background_total_hops"
    ].equals(
        df_other2["background_total_hops"]
    ), "The 'background_total_hops' values should be the same in all three dataframes"
