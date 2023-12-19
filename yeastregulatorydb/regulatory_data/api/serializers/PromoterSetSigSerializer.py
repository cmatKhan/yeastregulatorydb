from rest_framework import serializers

from ...models import PromoterSetSig
from .mixins.CustomValidateMixin import CustomValidateMixin
from .mixins.FileValidationMixin import FileValidationMixin


class PromoterSetSigSerializer(CustomValidateMixin, FileValidationMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifier = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = PromoterSetSig
        fields = "__all__"

    def get_background_id(self, obj):
        return obj.background.id if obj.background else "undefined"
