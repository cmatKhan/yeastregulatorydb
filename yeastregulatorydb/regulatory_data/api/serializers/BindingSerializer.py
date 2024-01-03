import logging

from rest_framework import serializers

from ...models import Binding
from .mixins import CustomValidateMixin, FileValidationMixin, GetDataSourceMixin, GetOrCreateRegulatorMixin

logger = logging.getLogger(__name__)


class BindingSerializer(
    GetDataSourceMixin,
    GetOrCreateRegulatorMixin,
    CustomValidateMixin,
    FileValidationMixin,
    serializers.ModelSerializer,
):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifier = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = Binding
        fields = "__all__"

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Add the custom attribute to the serialized data
        ret["promotersetsig_processing"] = getattr(instance, "promotersetsig_processing", False)
        return ret
