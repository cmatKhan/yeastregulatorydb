from rest_framework import serializers

from ...models.PromoterSetSig import PromoterSetSig
from .mixins.CustomValidateMixin import CustomValidateMixin


class PromoterSetSigSerializer(CustomValidateMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifiedBy = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = PromoterSetSig
        fields = "__all__"

    def get_background_id(self, obj):
        return obj.background_id.id if obj.background_id else "undefined"
