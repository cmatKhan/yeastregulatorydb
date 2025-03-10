import gzip
import io
import logging
import os
import tempfile
import uuid
from collections import namedtuple
from types import SimpleNamespace

import pandas as pd
from callingcardstools.PeakCalling.yeast.call_peaks import call_peaks as callingcards_promoter_sig
from celery import group
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files import File
from django.db import transaction
from django.db.models import Count
from django.db.models.query import QuerySet
from django.db.utils import IntegrityError

from config import celery_app
from yeastregulatorydb.regulatory_data.api.serializers import (
    BindingConcatenatedSerializer,
    BindingManualQCSerializer,
    PromoterSetSigSerializer,
)
from yeastregulatorydb.regulatory_data.models import (
    Binding,
    BindingConcatenated,
    CallingCardsBackground,
    ChrMap,
    DataSource,
    FileFormat,
    PromoterSet,
    PromoterSetSig,
    Regulator,
)
from yeastregulatorydb.regulatory_data.utils.extract_file_from_storage import extract_file_from_storage
from yeastregulatorydb.users.models import User

logger = logging.getLogger(__name__)


def get_user_by_id(user_id: int) -> User:
    """Retrieve user by ID.

    :param user_id: The ID of the user.
    :type user_id: int

    :return: User object.
    :rtype: User

    :raises ValueError: If the user does not exist.
    """
    User = get_user_model()
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise ValueError(f"User with id {user_id} does not exist")


def get_binding_records(regulator_id: int, data_usable: str, datasource_name: str) -> QuerySet:
    """Retrieve binding records based on regulator ID, data usability, and data source name.

    :param regulator_id: The ID of the regulator.
    :type regulator_id: int
    :param data_usable: Data usability status.
    :type data_usable: str
    :param datasource_name: Name of the data source.
    :type datasource_name: str

    :return: Queryset of binding records.
    :rtype: QuerySet

    :raises ValueError: If binding records do not exist.
    """
    try:
        return Binding.objects.filter(
            bindingmanualqc__data_usable=data_usable,
            regulator_id=regulator_id,
            source__name=datasource_name,
        )
    except Binding.DoesNotExist:
        raise ValueError(
            f"Binding records with regulator_id {regulator_id}, data_usable '{data_usable}' and datasource_name '{datasource_name}' do not exist"
        )


def handle_less_2_binding_records(binding_records: list, regulator_id: int, datasource_name: str) -> None:
    """Handle cases with fewer binding records.

    :param binding_records: Queryset of binding records.
    :type binding_records: QuerySet
    :param regulator_id: The ID of the regulator.
    :type regulator_id: int
    :param datasource_name: Name of the data source.
    :type datasource_name: str

    :return: Empty list if conditions are met.
    :rtype: list
    """
    binding_concatenated_record = BindingConcatenated.objects.filter(
        regulator_id=regulator_id, source__name=datasource_name
    ).first()
    if binding_concatenated_record is not None:
        binding_concatenated_record_id = binding_concatenated_record.id
        binding_concatenated_record.delete()
        logger.info(
            f"BindingConcatenated record with regulator_id {regulator_id} and datasource_name {datasource_name} deleted because the number of Binding records is less than 2"
        )
        return [-binding_concatenated_record_id]
    return []


def check_existing_binding_concatenated(
    binding_records: list, regulator_id: int, datasource_name: str
) -> BindingConcatenated | None:
    """Check for existing BindingConcatenated records.

    :param binding_records: Queryset of binding records.
    :type binding_records: QuerySet
    :param regulator_id: The ID of the regulator.
    :type regulator_id: int
    :param datasource_name: Name of the data source.
    :type datasource_name: str

    :return: A BindingConcatenated record if it exists, updated for the new set of
        bindings if necessary. Else None.
    :rtype: BindingConcatenated | None
    """
    # Attempt to find a matching BindingConcatenated record based on regulator and source
    potential_match = (
        BindingConcatenated.objects.filter(regulator_id=regulator_id, source__name=datasource_name)
        .annotate(num_bindings=Count("bindings"))
        .first()
    )

    # If potential_match has an item it in, check to see if the binding set matches
    # exactly. If it does, return the potential_match record
    if potential_match is not None:
        existing_binding_ids = set(potential_match.bindings.values_list("id", flat=True))
        current_binding_ids = set(binding_records.values_list("id", flat=True))

        # if there is an exact match, return `potential_match`
        if existing_binding_ids == current_binding_ids:
            # The existing record matches the current set of bindings, log and return the record
            logger.info(
                f"BindingConcatenated record with bindings {binding_records}, regulator_id {regulator_id}, and datasource_name {datasource_name} already exists."
            )
            return potential_match
    # otherwise, return none. Later, the BindingConcatenatedSerializer will handle
    # either creating a new record, or updating an existing one
    else:
        logger.debug(
            f"No existing BindingConcatenated record found for the current set of bindings with regulator_id: "
            f"{regulator_id} and datasource_name: {datasource_name}"
        )
        return None


def get_fileformat(output_fileformat: str) -> FileFormat:
    """Retrieve file format record by format name.

    :param output_fileformat: The name of the output file format.
    :type output_fileformat: str

    :return: FileFormat object.
    :rtype: FileFormat

    :raises ValueError: If the file format does not exist.
    """
    try:
        return FileFormat.objects.get(fileformat=output_fileformat)
    except FileFormat.DoesNotExist:
        raise ValueError(f"FileFormat '{output_fileformat}' does not exist")


def extract_files(binding_records, tmpdir: str) -> list:
    """Extract files from storage for given binding records.

    :param binding_records: Queryset of binding records.
    :type binding_records: QuerySet
    :param tmpdir: Path to temporary directory.
    :type tmpdir: str

    :return: List of file paths.
    :rtype: list
    """
    return [extract_file_from_storage(binding_record.file, tmpdir) for binding_record in binding_records]


def generate_promoter_significance_result(
    binding_filepath_list: list,
    promoter_record: PromoterSet,
    background_record: CallingCardsBackground,
    tmpdir: str,
    chrmap_filepath: str,
) -> namedtuple:
    """Generate promoter significance result.

    :param binding_filepath_list: List of binding file paths.
    :type binding_filepath_list: list
    :param promoter_record: Promoter record object.
    :type promoter_record: PromoterSet
    :param background_record: Background record object.
    :type background_record: CallingCardsBackground
    :param tmpdir: Path to temporary directory.
    :type tmpdir: str
    :param chrmap_filepath: Path to chromosome map file.
    :type chrmap_filepath: str

    :return: A ResultObject namedtuple which has the slots `df` and `background_id`
        containing dataframe and background ID.
    :rtype: namedtuple
    """
    promoter_filepath = extract_file_from_storage(promoter_record.file, tmpdir)
    background_filepath = extract_file_from_storage(background_record.file, tmpdir)
    logger.debug(
        f"Calling callingcards_promoter_sig with promoter_filepath {promoter_filepath}, "
        f"background_filepath {background_filepath}, binding_filepath_list {binding_filepath_list}"
    )
    result = callingcards_promoter_sig(
        experiment_data_paths=binding_filepath_list,
        experiment_orig_chr_convention=settings.CHR_FORMAT,
        promoter_data_path=promoter_filepath,
        promoter_orig_chr_convention=settings.CHR_FORMAT,
        background_data_path=background_filepath,
        background_orig_chr_convention=settings.CHR_FORMAT,
        chrmap_data_path=chrmap_filepath,
        unified_chr_convention=settings.CHR_FORMAT,
        deduplicate_experiment=False,
        genomic_only=True,
    )
    logger.debug(
        f"SUCCESS: callingcards_promoter_sig with promoter_filepath {promoter_filepath} "
        f"background_filepath {background_filepath}, binding_filepath_list {binding_filepath_list}"
    )
    ResultObject = namedtuple("ResultObject", ["df", "promoter_id", "background_id"])
    return ResultObject(result, promoter_record.id, background_record.id)


@transaction.atomic
def save_promoter_significance_results(
    result_list: list,
    user: User,
    binding_records: Binding,
    regulator_id: int,
    datasource_name: str,
    fileformat_record: FileFormat,
) -> list:
    """Save promoter significance results to the database

    :param result_list: List of result objects.
    :type result_list: list
    :param user: User object.
    :type user: User
    :param binding_records: Queryset of binding records.
    :type binding_records: QuerySet
    :param regulator_id: The ID of the regulator.
    :type regulator_id: int
    :param datasource_name: Name of the data source.
    :type datasource_name: str
    :param fileformat_record: FileFormat object.
    :type fileformat_record: FileFormat

    :return: List of PromoterSetSig IDs.
    :rtype: list
    """
    output_list = []
    for result_df, promoter_id, background_id in result_list:
        buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode="wb") as gzipped_file:
            result_df.to_csv(gzipped_file, index=False)
        buffer.seek(0)
        django_file = File(buffer, name=f"{uuid.uuid4()}.csv.gz")
        mock_request = SimpleNamespace(user=user)

        composite_binding_data = {
            "bindings": [binding.id for binding in binding_records],
            "regulator": regulator_id,
            "source": DataSource.objects.get(name=datasource_name).id,
        }
        logger.debug(f"Creating compositeBinding record with data: {composite_binding_data}")
        composite_binding_serializer = BindingConcatenatedSerializer(
            data=composite_binding_data, context={"request": mock_request}
        )

        if not composite_binding_serializer.is_valid(raise_exception=True):
            logger.error(f"compositeBinding Serializer is invalid: {composite_binding_serializer.errors}")
            raise ValueError("compositeBinding Serializer is invalid: ", composite_binding_serializer.errors)

        composite_binding_record = composite_binding_serializer.save()

        if composite_binding_record.bindingmanualqc_set.exists():
            composite_binding_manualqc_record = composite_binding_record.bindingmanualqc_set.first()
            composite_binding_manualqc_record.data_usable = "unreviewed"
            composite_binding_manualqc_record.preferred_replicate = True
            composite_binding_manualqc_record.save()
        else:
            composite_binding_manualqc_data = {
                "composite_binding": composite_binding_record.id,
                "preferred_replicate": True,
                "note": f"aggregated callingcards replicates for source {datasource_name}",
            }
            composite_binding_manualqc_serializer = BindingManualQCSerializer(
                data=composite_binding_manualqc_data, context={"request": mock_request}
            )

            if not composite_binding_manualqc_serializer.is_valid(raise_exception=True):
                logger.error(
                    f"compositeBindingManualQC Serializer is invalid: {composite_binding_manualqc_serializer.errors}"
                )
                raise ValueError(
                    "compositeBindingManualQC Serializer is invalid: ", composite_binding_manualqc_serializer.errors
                )
            composite_binding_manualqc_serializer.save()

        # If the database transaction which saves the PromoterSetSig record succeeds,
        # then we're going to use this to delete this old record
        current_promotersetsig_record = PromoterSetSig.objects.filter(
            composite_binding=composite_binding_record.id, promoter=promoter_id, background=background_id
        ).first()

        promotersetsig_data = {
            "composite_binding": composite_binding_record.id,
            "promoter": promoter_id,
            "background": background_id,
            "fileformat": fileformat_record.id,
            "file": django_file,
        }
        serializer = PromoterSetSigSerializer(
            data=promotersetsig_data,
            context={"request": mock_request},
        )
        if not serializer.is_valid(raise_exception=True):
            logger.error(f"promoterSetSig Serializer is invalid: {serializer.errors}")
            raise ValueError("promoterSetSig Serializer is invalid: ", serializer.errors)
        try:
            promoter_set_sig = serializer.save()
            output_list.append(promoter_set_sig.id)
            # if there was a PromoterSetSig record with the same BindingConcatenated
            # record, promoter and background, then delete it if the save was successful
            if current_promotersetsig_record is not None:
                current_promotersetsig_record.delete()
        except (IntegrityError, ValidationError) as exc:
            logger.error(f"Error saving promoterSetSig record: {exc}")
            raise
    return output_list


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def promoter_significance_combined_task(
    self,
    user_id: int,
    regulator_id: int,
    datasource_name: str,
    output_fileformat: str,
    data_usable: str = "pass",
    **kwargs,
) -> list:
    """For each promoter set in PromoterSet, create the  promoter significance file.
    Return a list of PromoterSetSig objects that may be passed on to the rank response
    endpoint. NOTE that this task expects the following global variables to
    be set in the django settings:
    - CHR_FORMAT: The chromosome format to use for the input and output files
    - CALLINGCARDS_PROMOTER_SIG_FORMAT: The name of the callingcards promoter significance

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
    user = get_user_by_id(user_id)
    binding_records = get_binding_records(regulator_id, data_usable, datasource_name)

    logger.debug(f"Found {binding_records.count()} binding records for regulator_id {regulator_id}")

    # if the number of binding records is less than 2, check to see if there is a
    # BindingConcatenated record. If there is, delete it. This will also delete the
    # corresponding BindingManualQC and PromoterSetSig record.
    # Return is a list where there is a minus sign in front of the deleted
    # BindingConcatenated record ID
    if len(binding_records) < 2:
        logger.debug(f"Less than 2 binding records found for regulator_id {regulator_id}")
        return handle_less_2_binding_records(binding_records, regulator_id, datasource_name)

    # Check to see if a BindingConcatenated record that matches _exactly_ the regulator,
    # datsource, and binding records already exists.
    possible_bindingconcatenated_record = check_existing_binding_concatenated(
        binding_records, regulator_id, datasource_name
    )
    # if so, return the id of the PromoterSetSig. However, if a record existed, but had
    # a different set of bindings, then it is deleted (along with related objects) and
    # None is returned. If no record with the regulator/source exists, then None is
    # also returned
    if possible_bindingconcatenated_record is not None:
        logger.info(
            f"Returning existing concatenated PromoterSetSig record for regulator_id "
            f"{regulator_id} and datasource_name {datasource_name}"
        )
        return [PromoterSetSig.objects.filter(composite_binding=possible_bindingconcatenated_record.id).first().id]

    fileformat_record = get_fileformat(output_fileformat)

    with tempfile.TemporaryDirectory() as tmpdir:
        # write the chrmap file to a temporary directory
        chrmap_filepath = os.path.join(tmpdir, "chrmap.csv")
        pd.DataFrame(list(ChrMap.objects.all().values())).to_csv(chrmap_filepath, index=False)

        # do the same with the binding data -- extract from storage, write to tmpdir
        binding_filepath_list = extract_files(binding_records, tmpdir)
        promoterset_objects_iterator = (
            PromoterSet.objects.filter(id=kwargs.get("promoterset_id")).iterator()
            if "promoterset_id" in kwargs
            else PromoterSet.objects.iterator()
        )

        result_list = []
        for promoter_record in promoterset_objects_iterator:
            background_objects_iterator = (
                CallingCardsBackground.objects.filter(id=kwargs.get("background_id")).iterator()
                if "background_id" in kwargs
                else CallingCardsBackground.objects.iterator()
            )
            for background_record in background_objects_iterator:
                result_list.append(
                    generate_promoter_significance_result(
                        binding_filepath_list, promoter_record, background_record, tmpdir, chrmap_filepath
                    )
                )
        # this function occurs in an atomic block -- all records are saved/updated
        # successfully, or any transactions already performed in the block are
        # rolled back before exit
        # NOTE: if there does not exist a BindingConcatenated record with the same
        # bindings, regulator, and source, then one will be created before the
        # related PromoterSetSig record is created
        return save_promoter_significance_results(
            result_list, user, binding_records, regulator_id, datasource_name, fileformat_record
        )


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def _admin_promoter_significance_combined_task(self, user_id: int, **kwargs) -> None:
    """
    Iterate over a list of PromoterSetSig object ids and call the
    promoter_significance_task. The kwargs are passed to the promoter_significance_task

    :param promotersetsig_ids: A list of promotersetsig object ids
    :type promotersetsig_ids: list
    :param user_id: the id of the user that initiated the task
    :type user_id: int
    :param kwargs: keyword arguments to be passed to the promoter_significance_task
    """

    # from the Binding table, get a list of the regulator_ids that are associated
    # with records with the source.assay "callingcards"
    regulator_ids = kwargs.get(
        "regulator_ids",
        Binding.objects.filter(source__assay="callingcards").values_list("regulator_id", flat=True).distinct(),
    )

    datasource_names = kwargs.get(
        "datasource_names",
        Binding.objects.filter(source__assay="callingcards").values_list("source__name", flat=True).distinct(),
    )

    if isinstance(regulator_ids, int):
        # verify that the regulator_id is a valid one
        try:
            assert Binding.objects.filter(regulator_id=regulator_ids).count() > 0
            regulator_ids = [regulator_ids]
        except AssertionError as exc:
            logger.error(f"Regulator id {regulator_ids} is not valid: {exc}")
            raise ValueError(f"Regulator id {regulator_ids} is not valid: {exc}")

    if isinstance("datasource_names", str):
        # verify that it is a valid datasource name
        try:
            assert DataSource.objects.filter(name=datasource_names).count() == 1
            datasource_names = [datasource_names]
        except AssertionError as exc:
            logger.error(f"Datasource name {datasource_names} is not valid: {exc}")
            raise ValueError(f"Datasource name {datasource_names} is not valid: {exc}")

    if not regulator_ids or not datasource_names:
        logger.warning("No regulator_ids or datasource_names found. Task will not proceed.")
        raise ValueError("No regulator_ids or datasource_names found. Task will not proceed.")

    task_list = []

    for source_name in datasource_names:
        logger.info(f"Preparing promoter_significance_combined_task for datasource {source_name}")
        for regulator_id in regulator_ids:
            try:
                regulator = Regulator.objects.get(id=regulator_id)
                logger.debug(
                    f"Preparing promoter_significance_combined_task for regulator {regulator.genomicfeature.locus_tag}"
                )
                existing_binding_concatenated = BindingConcatenated.objects.filter(
                    regulator=regulator, source__name=source_name
                ).first()
                if existing_binding_concatenated is not None:
                    logger.info(
                        f"Deleting BindingConcatenated record with regulator_id {regulator_id} and datasource_name {source_name}"
                    )
                    existing_binding_concatenated.delete()
                task = promoter_significance_combined_task.s(
                    user_id=user_id,
                    regulator_id=regulator_id,
                    datasource_name=source_name,
                    output_fileformat=kwargs.get("output_fileformat", settings.CALLINGCARDS_PROMOTER_SIG_FORMAT),
                    data_usable=kwargs.get("data_usable", "pass"),
                )
                task_list.append(task)
            except Regulator.DoesNotExist:
                logger.error(f"Regulator with id {regulator_id} does not exist.")
            except Exception as e:
                logger.error(f"Error preparing task for regulator {regulator_id} and datasource {source_name}: {e}")

    # Execute the group of tasks simultaneously without waiting for them to finish
    if task_list:
        group(task_list).apply_async()
