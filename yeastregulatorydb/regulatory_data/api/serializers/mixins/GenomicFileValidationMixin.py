import pandas as pd
from django.conf import settings
from rest_framework import serializers

from yeastregulatorydb.regulatory_data.models import FileFormat
from yeastregulatorydb.regulatory_data.utils.validate_genomic_df import validate_genomic_df


class GenomicFileValidationMixin:
    def validate_file(self, value):
        # check extension
        if not value.name.endswith(".gz"):
            raise serializers.ValidationError(
                "all uploaded files are expected to be gzipped tsv files. "
                "The file extension before .gz does not matter, but if it is gzipped, "
                "there should be a .gz extention. Gzip it and try again."
            )
        # read in the file with pandas. raise a validationerror if it fails
        if self.instance:  # type: ignore[attr-defined]
            separator = self.instance.filetype_id.separator  # type: ignore[attr-defined]
            fields = self.instance.filetype_id.fields  # type: ignore[attr-defined]
        else:
            if self.initial_data:  # type: ignore[attr-defined]
                filetype_id = self.initial_data.get("filetype_id")  # type: ignore[attr-defined]
                if filetype_id is None:
                    raise serializers.ValidationError("filetype_id must be provided")
                else:
                    try:
                        file_format = FileFormat.objects.get(id=filetype_id)
                        separator = file_format.separator
                        fields = file_format.fields
                    except FileFormat.DoesNotExist:
                        raise serializers.ValidationError("filetype_id does not correspond to a valid FileFormat id")
            else:
                raise serializers.ValidationError("initial_data must be provided")
        try:
            df = pd.read_csv(value, sep=separator, compression="gzip")
        except Exception as e:
            raise serializers.ValidationError(f"Could not read file. Error: {e}")
        try:
            df = validate_genomic_df(df, settings.CHR_FORMAT, fields)
        except ValueError as e:
            raise serializers.ValidationError(f"Invalid file. Error: {e}")
        return value
