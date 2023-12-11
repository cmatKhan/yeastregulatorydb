from rest_framework import serializers

from ...models.BindingManualQC import BindingManualQC
from .mixins.CustomValidateMixin import CustomValidateMixin


class BindingManualQCSerializer(CustomValidateMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifiedBy = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = BindingManualQC
        fields = "__all__"
