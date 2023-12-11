from rest_framework import serializers

from ...models.ChrMap import ChrMap
from .mixins.CustomValidateMixin import CustomValidateMixin


class ChrMapSerializer(CustomValidateMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifiedBy = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = ChrMap
        fields = "__all__"
