import gzip
import io
import logging
import os
import tempfile
import uuid
from collections import namedtuple
from types import SimpleNamespace

import pandas as pd
from callingcardstools.Analysis.yeast.chipexo_promoter_sig import chipexo_promoter_sig
from callingcardstools.PeakCalling.yeast.call_peaks import call_peaks as callingcards_promoter_sig
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File

from config import celery_app
from yeastregulatorydb.regulatory_data.api.serializers import PromoterSetSigSerializer
from yeastregulatorydb.regulatory_data.models import Binding, CallingCardsBackground, ChrMap, FileFormat, PromoterSet
from yeastregulatorydb.regulatory_data.utils.extract_file_from_storage import extract_file_from_storage

logger = logging.getLogger(__name__)


@celery_app.task()
def promoter_significance_task(binding_id: int, user_id: int, output_fileformat: str, **kwargs) -> list:
    """For each promoter set in PromoterSet, create the chipexo promoter significance file.
    Return a list of PromoterSetSig objects that may be passed on to the rank response
    endpoint.

    :param binding_id: The Binding record for the chipexo_pugh_allevents data
    :type binding_id: Binding
    :param user_id: The id of the user who initiated the task
    :type user_id: int
    :param output_fileformat: The name of the output FileFormat
    :type output_fileformat: str
    :param kwargs: Additional keyword arguments. If `promoterset_id` is passed,
    then the significance will be calculated only that specific promoterset.
    Else, it is calculated over all promoter sets in the PromoterSet table.
    If the output_fileformat is callingcards_promoter_sig and `background_id`
    is passed in kwargs, then the promoter significance will be calculated
    that specific background set only. Else, significance will be calculated
    for all background sets

    :return: A list of PromoterSetSig object ids
    :rtype: list

    :raises ValueError: If the Binding record with id `binding_id` does not
        exist or if the chipexo_promoter_sig FileFormat does not exist
    :raises ValidationError: If the serializer is invalid
    """
    try:
        User = get_user_model()
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise ValueError(f"User with id {user_id} does not exist")

    try:
        binding_record = Binding.objects.get(id=binding_id)
    except Binding.DoesNotExist:
        raise ValueError(f"Binding record with id {binding_id} does not exist")

    try:
        fileformat_record = FileFormat.objects.get(fileformat=output_fileformat)
    except FileFormat.DoesNotExist:
        raise ValueError(f"FileFormat '{output_fileformat}' does not exist")

    with tempfile.TemporaryDirectory() as tmpdir:
        chrmap_filepath = os.path.join(tmpdir, "chrmap.csv")

        pd.DataFrame(list(ChrMap.objects.all().values())).to_csv(chrmap_filepath, index=False)

        binding_filepath = extract_file_from_storage(binding_record.file, tmpdir)

        # result_list stores ResultObject tuples where `df` is the dataframe
        # output by the promoter_significance function and `background_id` is
        # if promoterset_id is passed, then extract only that record. Else,
        # generate an iterator that will return all records in the PromoterSet
        # table
        promoterset_objects_iterator = (
            PromoterSet.objects.filter(id=kwargs.get("promoterset_id")).iterator()
            if "promoterset_id" in kwargs
            else PromoterSet.objects.iterator()
        )
        # None if there is no background, or the record `id` if there is
        ResultObject = namedtuple("ResultObject", ["df", "background_id"])
        result_list = []
        for promoter_record in promoterset_objects_iterator:
            promoter_filepath = extract_file_from_storage(promoter_record.file, tmpdir)

            if output_fileformat == settings.CHIPEXO_PROMOTER_SIG_FORMAT:
                result = chipexo_promoter_sig(
                    binding_filepath,
                    settings.CHR_FORMAT,
                    promoter_filepath,
                    settings.CHR_FORMAT,
                    chrmap_filepath,
                    settings.CHR_FORMAT,
                )
                result_list.append(ResultObject(result, None))
            elif output_fileformat == settings.CALLINGCARDS_PROMOTER_SIG_FORMAT:
                # if background_id is passed, then extract only that record.
                # else, generate an iterator that will return all records in
                # the CallingCardsBackground table
                background_objects_iterator = (
                    CallingCardsBackground.objects.filter(id=kwargs.get("background_id")).iterator()
                    if "background_id" in kwargs
                    else CallingCardsBackground.objects.iterator()
                )
                for background_record in background_objects_iterator:
                    background_filepath = extract_file_from_storage(background_record.file, tmpdir)

                    result = callingcards_promoter_sig(
                        binding_filepath,
                        settings.CHR_FORMAT,
                        promoter_filepath,
                        settings.CHR_FORMAT,
                        background_filepath,
                        settings.CHR_FORMAT,
                        chrmap_filepath,
                        False,
                        settings.CHR_FORMAT,
                    )
                    result_list.append(ResultObject(result, binding_record.id))
            else:
                raise ValueError(f"FileFormat '{output_fileformat}' not supported")

        # output_list stores promoter_set_sig `id`s for successfully uploaded
        # records
        output_list = []
        for res_obj in result_list:
            buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=buffer, mode="wb") as gzipped_file:
                res_obj.df.to_csv(gzipped_file, index=False)

            # Reset buffer position
            buffer.seek(0)

            # Create a Django File object with a uuid filename
            django_file = File(buffer, name=f"{uuid.uuid4()}.csv.gz")

            # Create a mock request with only a user attribute
            # Assuming you have the user_id available
            mock_request = SimpleNamespace(user=user)

            upload_data = {
                "binding": binding_record.id,
                "promoter": promoter_record.id,
                "fileformat": fileformat_record.id,
                "file": django_file,
            }
            if res_obj.background_id:
                upload_data["background"] = res_obj.background_id

            serializer = PromoterSetSigSerializer(
                data=upload_data,
                context={"request": mock_request},
            )

            if serializer.is_valid():
                promoter_set_sig = serializer.save()
                output_list.append(promoter_set_sig.id)
            else:
                logger.error(f"promoterSetSig Serializer is invalid: {serializer.errors}")

    return output_list
