from rest_framework import serializers

from ...models import DataSource, FileFormat
from .mixins.CustomValidateMixin import CustomValidateMixin


class DataSourceSerializer(CustomValidateMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifier = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = DataSource
        fields = "__all__"

    def validate_fileformat(self, value):
        if isinstance(value, int):
            return value
        elif isinstance(value, str):
            try:
                return FileFormat.objects.get(fileformat=value).id
            except FileFormat.DoesNotExist:
                raise serializers.ValidationError(
                    "FileFormat not found. Provide either the FileFormat `id` or the `fileformat` string."
                )
        return value

    def validate_source(self, value):
        if isinstance(value, int):
            return value
        elif isinstance(value, str):
            try:
                return DataSource.objects.get(name=value).id
            except DataSource.DoesNotExist:
                raise serializers.ValidationError("Lab not found")
        return value.upper()
