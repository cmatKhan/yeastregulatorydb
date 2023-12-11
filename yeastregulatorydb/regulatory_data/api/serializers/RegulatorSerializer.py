from rest_framework import serializers

from ...models.Regulator import Regulator
from .mixins.CustomValidateMixin import CustomValidateMixin


class RegulatorSerializer(CustomValidateMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifiedBy = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = Regulator
        fields = "__all__"
