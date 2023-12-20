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
from yeastregulatorydb.regulatory_data.models import DataSource, PromoterSet, Regulator
from yeastregulatorydb.regulatory_data.tasks import promoter_significance_task, rank_response_task
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


@pytest.mark.djanbo_db
def test_promoter_significance_task(
    settings, chrmap: QuerySet, fileformat: QuerySet, chipexo_datasource: DataSource, regulator: Regulator, user: User
):
    """test promoter_significance_task task"""
    # Create a request object and set the user
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = user

    # create the promoter set record
    promoterset_path = os.path.join(os.path.dirname(__file__), "test_data", "yiming_promoters_chrI.bed.gz")
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
    file_path = os.path.join(os.path.dirname(__file__), "test_data", "binding/chipexo/28366_chrI.csv.gz")
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


@pytest.mark.djanbo_db
def test_rank_response_task(
    settings,
    chrmap: QuerySet,
    fileformat: QuerySet,
    promoterset: PromoterSet,
    user: User,
    regulator: Regulator,
    chipexo_datasource: DataSource,
    mcisaac_datasource: DataSource,
):
    """test promoter_significance_task task"""
    # Create a request object and set the user
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = user

    # create the promoter set record
    promotersetsig_path = os.path.join(
        os.path.dirname(__file__), "test_data", "binding/chipexo/28366_yiming_promoter_sig.csv.gz"
    )
    assert os.path.exists(promotersetsig_path), f"path: {promotersetsig_path}"

    expression_path = os.path.join(
        os.path.dirname(__file__), "test_data", "expression/mcisaac/hap5_15min_mcisaac_chr1.csv.gz"
    )
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
