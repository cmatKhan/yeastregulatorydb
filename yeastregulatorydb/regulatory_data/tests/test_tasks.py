import os

import pytest
from celery.result import EagerResult
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.query import QuerySet
from rest_framework.test import APIRequestFactory

from yeastregulatorydb.regulatory_data.api.serializers import BindingSerializer, PromoterSetSerializer
from yeastregulatorydb.regulatory_data.models import DataSource, Regulator
from yeastregulatorydb.regulatory_data.tasks.chipexo_pugh_allevents_promoter_sig import (
    chipexo_pugh_allevents_promoter_sig,
)
from yeastregulatorydb.regulatory_data.tests.factories import BindingFactory, PromoterSetFactory
from yeastregulatorydb.regulatory_data.tests.utils.model_to_dict_select import model_to_dict_select
from yeastregulatorydb.users.models import User

pytestmark = pytest.mark.django_db


@pytest.mark.djanbo_db
def test_chipexo_pugh_allevents_promoter_sig(
    settings, chrmap: QuerySet, fileformat: QuerySet, chipexo_datasource: DataSource, regulator: Regulator, user: User
):
    """test chipexo_pugh_allevents_promoter_sig task"""
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
        assert serializer.is_valid() == True, serializer.errors
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
        assert serializer.is_valid() == True, serializer.errors
        instance = serializer.save()
        settings.CELERY_TASK_ALWAYS_EAGER = True
        task_result = chipexo_pugh_allevents_promoter_sig.delay(instance.id, request.user.id)
        assert isinstance(task_result, EagerResult)
        assert isinstance(task_result.result, list)
