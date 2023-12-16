import gzip
import io
import logging
import os
import tempfile
from types import SimpleNamespace

import pandas as pd
from callingcardstools.Analysis.yeast.chipexo_promoter_sig import chipexo_promoter_sig
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File

from config import celery_app
from yeastregulatorydb.regulatory_data.api.serializers import PromoterSetSigSerializer
from yeastregulatorydb.regulatory_data.models import Binding, ChrMap, FileFormat, PromoterSet
from yeastregulatorydb.regulatory_data.utils.extract_file_from_storage import extract_file_from_storage

logger = logging.getLogger(__name__)


@celery_app.task()
def chipexo_pugh_allevents_promoter_sig(chipexo_id: int, user_id: int) -> list:
    """For each promoter set in PromoterSet, create the chipexo promoter significance file.
    Return a list of PromoterSetSig objects that may be passed on to the rank response
    endpoint.

    :param chipexo_record: The Binding record for the chipexo_pugh_allevents data
    :type chipexo_record: Binding
    :param user_id: The id of the user who initiated the task
    :type user_id: int

    :return: A list of PromoterSetSig object ids
    :rtype: list

    :raises ValueError: If the Binding record with id `chipexo_id` does not
        exist or if the chipexo_promoter_sig FileFormat does not exist
    :raises ValidationError: If the serializer is invalid
    """
    try:
        User = get_user_model()
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise ValueError(f"User with id {user_id} does not exist")
    try:
        chipexo_record = Binding.objects.get(id=chipexo_id)
    except Binding.DoesNotExist:
        raise ValueError(f"Binding record with id {chipexo_id} does not exist")

    try:
        chipexo_promoter_sig_fileformat = FileFormat.objects.get(fileformat="chipexo_promoter_sig")
    except FileFormat.DoesNotExist:
        raise ValueError("FileFormat chipexo_promoter_sig does not exist")

    with tempfile.TemporaryDirectory() as tmpdir:
        chipexo_filepath = extract_file_from_storage(chipexo_record.file, tmpdir)

        chrmap_filepath = os.path.join(tmpdir, "chrmap.csv")

        pd.DataFrame(list(ChrMap.objects.all().values())).to_csv(chrmap_filepath, index=False)

        promoter_set_sig_list = []
        for promoter_record in PromoterSet.objects.iterator():
            promoter_filepath = extract_file_from_storage(promoter_record.file, tmpdir)

            result = chipexo_promoter_sig(
                chipexo_filepath,
                settings.CHR_FORMAT,
                promoter_filepath,
                settings.CHR_FORMAT,
                chrmap_filepath,
                settings.CHR_FORMAT,
            )

            buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=buffer, mode="wb") as gzipped_file:
                result.to_csv(gzipped_file, index=False)

            # Reset buffer position
            buffer.seek(0)

            # Create a Django File object with a filename
            django_file = File(buffer, name="my_file.csv.gz")

            # Create a mock request with only a user attribute
            # Assuming you have the user_id available
            mock_request = SimpleNamespace(user=user)

            serializer = PromoterSetSigSerializer(
                data={
                    "binding": chipexo_record.id,
                    "promoter": promoter_record.id,
                    "fileformat": chipexo_promoter_sig_fileformat.id,
                    "file": django_file,
                },
                context={"request": mock_request},
            )

            if serializer.is_valid():
                promoter_set_sig = serializer.save()
                promoter_set_sig_list.append(promoter_set_sig.id)
            else:
                logger.error(f"ChipExo promoterSetSig Serializer is invalid: {serializer.errors}")

    return promoter_set_sig_list
