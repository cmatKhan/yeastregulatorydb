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
from django.core.files.storage import default_storage

from config import celery_app
from yeastregulatorydb.regulatory_data.api.serializers import PromoterSetSigSerializer
from yeastregulatorydb.regulatory_data.models import (
    Binding,
    CallingCardsBackground,
    ChrMap,
    FileFormat,
    PromoterSet,
    PromoterSetSig,
)
from yeastregulatorydb.regulatory_data.utils.extract_file_from_storage import extract_file_from_storage

logger = logging.getLogger(__name__)


# implement a task that will run the promoter significance task on all binding records
# with data source 'brent_nf_cc'
@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def promoter_significance_task_all_single_callingcards(self, user_id: int, output_fileformat: str, **kwargs) -> list:
    try:
        User = get_user_model()
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise ValueError(f"User with id {user_id} does not exist")

    try:
        fileformat_record = FileFormat.objects.get(fileformat=output_fileformat)
    except FileFormat.DoesNotExist:
        raise ValueError(f"FileFormat '{output_fileformat}' does not exist")

    # get all binding records with data source 'brent_nf_cc' that do not have NA/null
    # single_binding
    binding_records = Binding.objects.filter(source__name="brent_nf_cc")
    output_list = []
    for binding_record in binding_records:
        binding_id = binding_record.id
        result = promoter_significance_task(
            binding_id=binding_id,
            user_id=user_id,
            output_fileformat=output_fileformat,
            **kwargs,
        )
        output_list.extend(result)
    return output_list


# TODO implement retry logic
@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def promoter_significance_task(self, binding_id: int, user_id: int, output_fileformat: str, **kwargs) -> list:
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

        # Write chrmap to temporary file
        pd.DataFrame(list(ChrMap.objects.all().values())).to_csv(chrmap_filepath, index=False)

        binding_filepath = extract_file_from_storage(binding_record.file, tmpdir)

        promoterset_objects_iterator = (
            PromoterSet.objects.filter(id=kwargs.get("promoterset_id")).iterator()
            if "promoterset_id" in kwargs
            else PromoterSet.objects.iterator()
        )

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
                background_objects_iterator = (
                    CallingCardsBackground.objects.filter(id=kwargs.get("background_id")).iterator()
                    if "background_id" in kwargs
                    else CallingCardsBackground.objects.iterator()
                )

                if background_objects_iterator is None:
                    raise ValueError("No background records found")

                for background_record in background_objects_iterator:
                    background_filepath = extract_file_from_storage(background_record.file, tmpdir)

                    result = callingcards_promoter_sig(
                        experiment_data_paths=[binding_filepath],
                        experiment_orig_chr_convention=settings.CHR_FORMAT,
                        promoter_data_path=promoter_filepath,
                        promoter_orig_chr_convention=settings.CHR_FORMAT,
                        background_data_path=background_filepath,
                        background_orig_chr_convention=settings.CHR_FORMAT,
                        chrmap_data_path=chrmap_filepath,
                        unified_chr_convention=settings.CHR_FORMAT,
                        deduplicate_experiment=kwargs.get("deduplicate_experiment", True),
                    )
                    result_list.append(ResultObject(result, background_record.id))
            else:
                raise ValueError(f"FileFormat '{output_fileformat}' not supported")

        output_list = []
        for res_obj in result_list:
            buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=buffer, mode="wb") as gzipped_file:
                res_obj.df.to_csv(gzipped_file, index=False)

            buffer.seek(0)
            django_file = File(buffer, name=f"{uuid.uuid4()}.csv.gz")

            mock_request = SimpleNamespace(user=user)

            # Check if an existing record exists
            existing_record = PromoterSetSig.objects.filter(
                single_binding=binding_record,
                promoter=promoter_record,
                background_id=res_obj.background_id,
                fileformat=fileformat_record,
            ).first()

            if existing_record:
                logger.info(f"Existing record found. Attempting to update PromoterSetSig ID {existing_record.id}.")
                # Use serializer for updates to ensure full validation and file handling
                serializer = PromoterSetSigSerializer(
                    existing_record,
                    data={"file": django_file, "fileformat": fileformat_record.id},
                    partial=True,
                    context={"request": mock_request},
                )

                if serializer.is_valid():
                    old_file = existing_record.file
                    try:
                        if old_file and old_file.name:  # Ensure file exists
                            if default_storage.exists(old_file.name):  # Check if file physically exists
                                logger.info(f"Deleting old file: {old_file.name}")
                                default_storage.delete(old_file.name)  # Manually remove from storage

                        # Save updated record
                        # note that the serializer .update() method will be called
                        # since the existing_record already has a `pk`
                        promoter_set_sig = serializer.save()
                        output_list.append(promoter_set_sig.id)
                        logger.info(f"Updated PromoterSetSig ID {promoter_set_sig.id}.")

                    except Exception as e:
                        # Delete the record if the file could not be deleted
                        existing_record.delete()
                        logger.error(f"Failed to save updated PromoterSetSig. Deleting the record. Error: {e}")
            else:
                # Create new record
                upload_data = {
                    "single_binding": binding_record.id,
                    "promoter": promoter_record.id,
                    "fileformat": fileformat_record.id,
                    "file": django_file,
                }
                if res_obj.background_id:
                    upload_data["background"] = res_obj.background_id

                serializer = PromoterSetSigSerializer(data=upload_data, context={"request": mock_request})

                if serializer.is_valid():
                    promoter_set_sig = serializer.save()
                    output_list.append(promoter_set_sig.id)
                    logger.info(f"Created PromoterSetSig ID {promoter_set_sig.id}.")
                else:
                    logger.error(f"Cannot create new PromoterSetSig record: {serializer.errors}")

    return output_list
