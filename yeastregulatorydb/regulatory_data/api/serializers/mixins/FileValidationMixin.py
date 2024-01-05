import gzip
import io
import logging

import pandas as pd
from django.conf import settings
from rest_framework import serializers

from yeastregulatorydb.regulatory_data.api.serializers.FileFormatSerializer import FileFormatSerializer
from yeastregulatorydb.regulatory_data.utils.count_hops import count_hops
from yeastregulatorydb.regulatory_data.utils.validate_df import validate_df
from yeastregulatorydb.regulatory_data.utils.validate_genomic_df import validate_genomic_df

logger = logging.getLogger(__name__)


def handle_missing_fileformat() -> tuple[str, dict]:
    """
    if the fileformat or source (which should be a DataSource object) is not provided,
    then assume the file is in bed6 format and return the default separator and fields
    """
    logger.warning("no `fileformat` provided. Assuming default BED6 format file fields")
    separator = "\t"
    fields = {"chr": str, "start": int, "end": int, "name": str, "score": float, "strand": str}
    return separator, fields


class FileValidationMixin:
    """
    Mixin for validating genomic files. The assumption is that all files will
    have at least the columns `chr`, `start`, and `end`, and that the levels
    of the `chr` column are in the CHR_FORMAT field of ChrMap. This expects
    that a `fileformat` format is passed in the initial_data. If the calling
    model does not have a `fileformat` field that foreign keys to the FileFormat,
    then you may pass 'default` through the Serializer class, which calls the
    default validation methods and assumes bed6 format
    """

    def validate(self, attrs):
        # in the django settings, there is a variable NULL_BINDING_FILE_DATASOURCES
        # that has a list of datasource names that are allowed to have null
        # binding.file fields. If the datasource.name in attrs is in that list,
        # then skip the `file` validation logic below
        # note that there are serializers which use this mixin which do not
        # have `source` fields -- those serializers should skip checking
        # the datasource name
        if attrs.get("source"):
            if attrs.get("source").name in settings.NULL_BINDING_FILE_DATASOURCES:
                attrs.pop("file")
                return attrs

        # below is all logic which verifies the uploaded file. It is in the
        # `validate` method because it relies on a number of other validated
        # fields in the serializer
        if "file" not in attrs.keys():
            raise serializers.ValidationError(
                "file is a required fields in any model serializer using the GenomicFileValidaitionMixin"
            )
        # check that there is data in the file
        if attrs.get("file").size == 0:
            raise serializers.ValidationError("File is empty")
        # check extension
        if not attrs.get("file").name.endswith(".gz"):
            raise serializers.ValidationError(
                "all uploaded files are expected to be gzipped tsv files. "
                "The file extension before .gz does not matter, but if it is gzipped, "
                "there should be a .gz extention. Gzip it and try again."
            )
        # read in the file with pandas. raise a validationerror if it fails
        if self.instance:  # type: ignore[attr-defined]
            separator = self.instance.fileformat.separator  # type: ignore[attr-defined]
            fields = FileFormatSerializer(attrs.get("fileformat")).fields_as_types  # type: ignore[attr-defined]
        else:
            if "fileformat" in attrs.keys():
                try:
                    separator = attrs.get("fileformat").separator
                    # extract with the serializer in order to translate the json string
                    # to a python dict with the correct types in the values
                    fileformat_serializer = FileFormatSerializer(attrs.get("fileformat"))
                    fields = fileformat_serializer.fields_as_types
                except AttributeError:
                    separator, fields = handle_missing_fileformat()
            elif "source" in attrs.keys():
                try:
                    separator = attrs.get("source").fileformat.separator
                    # extract with the serializer in order to translate the json string
                    # to a python dict with the correct types in the values
                    fileformat_serializer = FileFormatSerializer(attrs.get("source").fileformat)
                    fields = fileformat_serializer.fields_as_types
                except AttributeError:
                    separator, fields = handle_missing_fileformat()
            else:
                separator, fields = handle_missing_fileformat()

        # Reset the file pointer to the beginning of the file
        attrs.get("file").seek(0)

        # Try to decompress the gzipped data
        try:
            decompressed_file = gzip.decompress(attrs.get("file").read())
        except OSError:
            raise serializers.ValidationError("The file is not a valid gzipped file.")

        # Convert the bytes object to a StringIO object
        try:
            file_like_object = io.StringIO(decompressed_file.decode())
        except UnicodeDecodeError:
            raise serializers.ValidationError("The file content could not be decoded.")

        # Try to read the data into a pandas DataFrame
        try:
            df = pd.read_csv(file_like_object, sep=separator)
        except pd.errors.ParserError:
            raise serializers.ValidationError("The file could not be parsed with separator: {separator}")
        try:
            if {"chr", "start", "end"}.issubset(set(df.columns)):
                logger.info("Validating genomic coordinates in uploaded file")
                df = validate_genomic_df(df, settings.CHR_FORMAT, fields)
                if "depth" in df.columns:
                    logger.info("Counting genomic insertions and adding the tallies to the initial data")
                    count_dict = count_hops(df, settings.CHR_FORMAT)
                    for key in count_dict.keys():
                        # add the inserts to the initial data
                        attrs[key + "_inserts"] = count_dict[key]
            else:
                df = validate_df(df, fields)
        except ValueError as e:
            raise serializers.ValidationError(f"Invalid file. Error: {e}")
        return attrs
