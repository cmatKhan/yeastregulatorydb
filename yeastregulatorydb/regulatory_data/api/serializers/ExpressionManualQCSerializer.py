from rest_framework import serializers

from ...models.ExpressionManualQC import ExpressionManualQC
from .mixins.CustomValidateMixin import CustomValidateMixin


class ExpressionManualQCSerializer(CustomValidateMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifiedBy = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = ExpressionManualQC
        fields = "__all__"
