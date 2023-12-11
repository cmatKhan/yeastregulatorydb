from rest_framework import serializers

from ...models.FileFormat import FileFormat
from .mixins.CustomValidateMixin import CustomValidateMixin


class FileFormatSerializer(CustomValidateMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifiedBy = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = FileFormat
        fields = "__all__"
