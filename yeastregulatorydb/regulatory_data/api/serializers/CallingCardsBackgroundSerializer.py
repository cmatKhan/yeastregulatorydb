from rest_framework import serializers

from ...models.CallingCardsBackground import CallingCardsBackground
from .mixins.CustomValidateMixin import CustomValidateMixin
from .mixins.FileValidationMixin import FileValidationMixin


class CallingCardsBackgroundSerializer(CustomValidateMixin, FileValidationMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifier = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = CallingCardsBackground
        fields = "__all__"

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Add the custom attribute to the serialized data
        ret["promotersetsig_processing"] = getattr(instance, "promotersetsig_processing", False)
        return ret
