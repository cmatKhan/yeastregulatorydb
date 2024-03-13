import gzip
import io
import logging
import uuid
from types import SimpleNamespace

import pandas as pd
from django.contrib.auth import get_user_model
from django.core.files import File

from config import celery_app
from yeastregulatorydb.regulatory_data.api.filters import BindingFilter
from yeastregulatorydb.regulatory_data.api.serializers import BindingSerializer
from yeastregulatorydb.regulatory_data.models import Binding
from yeastregulatorydb.regulatory_data.utils import extract_file_from_storage

from .BaseTask import MyBaseTask

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, base=MyBaseTask)
def combine_cc_passing_replicates_task(self, regulator_id: int, user_id: int, **kwargs) -> list:
    """
    Combine the qbed files for the passing replicates of the calling cards assay.
    Note that by default, assay='callingcards' and data_usable='passing'
    are used as filters. Note that this deduplicates the qbed on `chr`, `start`, `end`
    such that if there are is an insertion at the same location on opposite strands,
    one of those insertions will be removed. The strand is set to '*' in the combined
    file.

    :param regulator_id: a regulator id
    :type regulator_id: int
    :param user_id: a user id
    :type user_id: int
    :param output_fileformat: the name of the output FileFormat
    :type output_fileformat: str
    :param kwargs: additional keyword arguments. This may be used to pass
        additional filters to the BindingFilter
    :type kwargs: dict

    :returns: a list of regulator genomic feature names which have been
    processed
    :rtype: list
    """

    try:
        User = get_user_model()
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise ValueError(f"User with id {user_id} does not exist")

    filters = {
        "regulator_id": regulator_id,
        "assay": kwargs.pop("assay", "callingcards"),
        "data_usable": kwargs.pop("data_usable", "passing"),
    }
    filters.update(kwargs)  # update filters with kwargs
    cc_binding_set = BindingFilter(filters, queryset=Binding.objects.all()).qs
    # get the qbed files from the django storage and read in data
    qbed_df_list = []
    for cc_record in cc_binding_set:
        filepath = extract_file_from_storage(cc_record.file)
        # read filepath into pandas dataframe
        df = pd.read_csv(filepath, sep="\t")
        # deduplicate the dataframe based on chr,start,end so that insertions at the
        # same position on opposite strands are not counted twice. set the strand to
        # '*'
        df = df.drop_duplicates(subset=["chr", "start", "end"])
        qbed_df_list.append(df)

    # combine the qbed files
    combined_qbed_df = pd.concat(qbed_df_list)

    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb") as gzipped_file:
        combined_qbed_df.to_csv(gzipped_file, sep="\t", index=False)

    # Reset buffer position
    buffer.seek(0)

    # Create a Django File object with a uuid filename
    django_file = File(buffer, name=f"{uuid.uuid4()}.csv.gz")

    # Create a mock request with only a user attribute
    # Assuming you have the user_id available
    mock_request = SimpleNamespace(user=user)

    source = kwargs.get("source_name") if kwargs.get("source_name") else cc_binding_set[0].source.name

    # Attempt to find an existing record
    existing_record = Binding.objects.filter(regulator_id=regulator_id, batch="cc_combined").first()

    upload_data = {
        "regulator": regulator_id,
        "batch": "cc_combined",
        "source_name": source,
        "file": django_file,
    }

    if existing_record:
        # Use serializer for updating to apply validation/transformation
        serializer = BindingSerializer(
            existing_record,
            data=upload_data,
            context={"request": mock_request},
        )
    # Proceed with creation logic if no existing record is found
    else:
        serializer = BindingSerializer(
            data=upload_data,
            context={"request": mock_request},
        )

    if serializer.is_valid():
        combined_binding_record = serializer.save()
        return combined_binding_record.id
    else:
        error_msg = f"Combined Binding Serializer is invalid: {serializer.errors}"
        logger.error(error_msg)
        raise ValueError(error_msg)
