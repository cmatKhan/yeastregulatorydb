import gzip
import io
import logging

import pandas as pd
from django.conf import settings
from rest_framework import serializers

from yeastregulatorydb.regulatory_data.models import FileFormat
from yeastregulatorydb.regulatory_data.utils.validate_genomic_df import validate_genomic_df

logger = logging.getLogger(__name__)


class GenomicFileValidationMixin:
    """
    Mixin for validating genomic files. The assumption is that all files will
    have at least the columns `chr`, `start`, and `end`, and that the levels
    of the `chr` column are in the CHR_FORMAT field of ChrMap. This expects
    that a `fileformat` format is passed in the initial_data. If the calling
    model does not have a `fileformat` field that foreign keys to the FileFormat,
    then you may pass 'default` through the Serializer class, which calls the
    default validation methods and assumes bed6 format
    """

    def validate_file(self, value):
        # check that there is data in the file
        if value.size == 0:
            raise serializers.ValidationError("File is empty")
        # check extension
        if not value.name.endswith(".gz"):
            raise serializers.ValidationError(
                "all uploaded files are expected to be gzipped tsv files. "
                "The file extension before .gz does not matter, but if it is gzipped, "
                "there should be a .gz extention. Gzip it and try again."
            )
        # read in the file with pandas. raise a validationerror if it fails
        if self.instance:  # type: ignore[attr-defined]
            separator = self.instance.fileformat.separator  # type: ignore[attr-defined]
            fields = self.instance.fileformat.fields  # type: ignore[attr-defined]
        else:
            if self.initial_data:  # type: ignore[attr-defined]
                fileformat = self.initial_data.get("fileformat")  # type: ignore[attr-defined]
                if fileformat is None:
                    logger.warning("fileformat not provided. Assuming default (bed6)")
                    fileformat = "default"
                else:
                    try:
                        # if the fileformat is set to default, then assume it is
                        # a bedfile, which is the default format for
                        # `validate_genomic_df()`
                        if not fileformat == "default":
                            file_format = FileFormat.objects.get(id=fileformat)
                            separator = file_format.separator
                            fields = file_format.fields
                    except FileFormat.DoesNotExist:
                        raise serializers.ValidationError("fileformat does not correspond to a valid FileFormat id")
            else:
                raise serializers.ValidationError("initial_data must be provided")
        # Reset the file pointer to the beginning of the file
        value.file.seek(0)

        # Try to decompress the gzipped data
        try:
            decompressed_file = gzip.decompress(value.file.read())
        except OSError:
            raise serializers.ValidationError("The file is not a valid gzipped file.")

        # Convert the bytes object to a StringIO object
        try:
            file_like_object = io.StringIO(decompressed_file.decode())
        except UnicodeDecodeError:
            raise serializers.ValidationError("The file content could not be decoded.")

        # Try to read the data into a pandas DataFrame
        try:
            if fileformat == "default":
                df = pd.read_csv(file_like_object, sep="\t")
            else:
                df = pd.read_csv(file_like_object, sep=separator)
        except pd.errors.ParserError:
            raise serializers.ValidationError("The file could not be parsed as a CSV file.")
        try:
            # the default fields for validate_genomic_df are bed6 fields
            if fileformat == "default":
                df = validate_genomic_df(df, settings.CHR_FORMAT)
            else:
                df = validate_genomic_df(df, settings.CHR_FORMAT, fields)
        except ValueError as e:
            raise serializers.ValidationError(f"Invalid file. Error: {e}")
        return value
