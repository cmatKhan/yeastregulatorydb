import os

import pytest
from celery.result import EagerResult
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.query import QuerySet
from rest_framework.test import APIRequestFactory

from yeastregulatorydb.regulatory_data.api.serializers import (
    BindingSerializer,
    ExpressionSerializer,
    PromoterSetSerializer,
    PromoterSetSigSerializer,
)
from yeastregulatorydb.regulatory_data.models import DataSource, PromoterSet, PromoterSetSig, RankResponse, Regulator
from yeastregulatorydb.regulatory_data.tasks import promoter_significance_task, rank_response_task
from yeastregulatorydb.regulatory_data.tasks.chained_tasks import promotersetsig_rankedresponse_chained
from yeastregulatorydb.regulatory_data.tests.factories import (
    BindingFactory,
    BindingManualQCFactory,
    ExpressionFactory,
    PromoterSetFactory,
    PromoterSetSigFactory,
)
from yeastregulatorydb.regulatory_data.tests.utils.model_to_dict_select import model_to_dict_select
from yeastregulatorydb.users.models import User

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
def test_promoter_significance_task(
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


@pytest.mark.django_db
def test_rank_response_task(
    settings,
    chrmap: QuerySet,
    fileformat: QuerySet,
    promoterset: PromoterSet,
    user: User,
    regulator: Regulator,
    chipexo_datasource: DataSource,
    mcisaac_datasource: DataSource,
    test_data_dict: dict,
):
    """test promoter_significance_task task"""
    # Create a request object and set the user
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = user

    # create the promoter set record
    promotersetsig_path = test_data_dict["binding"]["chipexo"]["files"][1]
    assert os.path.basename(promotersetsig_path) == "28366_yiming_promoter_sig.csv.gz"
    assert os.path.exists(promotersetsig_path), f"path: {promotersetsig_path}"

    expression_path = test_data_dict["expression"]["mcisaac"]["files"][0]
    assert os.path.basename(expression_path) == "hap5_15min_mcisaac_chr1.csv.gz"
    assert os.path.exists(expression_path), f"path: {expression_path}"

    binding_record = BindingFactory.create(source=chipexo_datasource, regulator=regulator)

    BindingManualQCFactory.create(binding=binding_record)

    # Open the file and read its content
    with open(promotersetsig_path, "rb") as promotersetsig_file_obj:
        promotersetsig_file_content = promotersetsig_file_obj.read()
        # Create a SimpleUploadedFile instance
        promotersetsig_upload_file = SimpleUploadedFile(
            "28366_yiming_promoter_sig.csv.gz", promotersetsig_file_content, content_type="application/gzip"
        )
        promotersetsig_data = model_to_dict_select(
            PromoterSetSigFactory.build(
                file=promotersetsig_upload_file,
                binding=binding_record,
                promoter=promoterset,
                fileformat=fileformat.get(fileformat="chipexo_promoter_sig"),
            )
        )
        promotersetsig_serializer = PromoterSetSigSerializer(data=promotersetsig_data, context={"request": request})
        assert promotersetsig_serializer.is_valid() is True, promotersetsig_serializer.errors
        promotersetsig_instance = promotersetsig_serializer.save()

    # Open the file and read its content
    with open(expression_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile("28366_chrI.csv.gz", file_content, content_type="application/gzip")
        data = model_to_dict_select(
            ExpressionFactory.build(source=mcisaac_datasource, regulator=binding_record.regulator, file=upload_file)
        )
        serializer = ExpressionSerializer(data=data, context={"request": request})
        assert serializer.is_valid() is True, serializer.errors
        serializer.save()

    settings.CELERY_TASK_ALWAYS_EAGER = True
    task_result = rank_response_task.delay(promotersetsig_instance.id, request.user.id)
    assert isinstance(task_result, EagerResult)
    assert isinstance(task_result.result, list)


def test_promotersetsig_rankedresponse_chained(
    settings,
    chrmap: QuerySet,
    fileformat: QuerySet,
    chipexo_datasource: DataSource,
    regulator: Regulator,
    user: User,
    test_data_dict: dict,
    mcisaac_datasource: DataSource,
):
    """test promotersetsig_rankedresponse_chained task"""
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

    expression_path = next(
        file
        for file in test_data_dict["expression"]["mcisaac"]["files"]
        if os.path.basename(file) == "hap5_15min_mcisaac_chr1.csv.gz"
    )
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

    # Open the file and read its content
    with open(expression_path, "rb") as file_obj:
        file_content = file_obj.read()
        # Create a SimpleUploadedFile instance
        upload_file = SimpleUploadedFile("28366_chrI.csv.gz", file_content, content_type="application/gzip")
        data = model_to_dict_select(
            ExpressionFactory.build(source=mcisaac_datasource, regulator=instance.regulator, file=upload_file)
        )
        expression_serializer = ExpressionSerializer(data=data, context={"request": request})
        assert expression_serializer.is_valid() is True, serializer.errors
        expression_serializer.save()

    settings.CELERY_TASK_ALWAYS_EAGER = True
    task_result = promotersetsig_rankedresponse_chained(
        instance.id, request.user.id, settings.CHIPEXO_PROMOTER_SIG_FORMAT
    )
    task_result.get()
    assert PromoterSetSig.objects.count() == 1
    assert RankResponse.objects.count() == 1
