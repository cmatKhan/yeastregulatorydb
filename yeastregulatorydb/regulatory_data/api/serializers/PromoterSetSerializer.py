from rest_framework import serializers

from ...models.PromoterSet import PromoterSet
from .mixins.CustomValidateMixin import CustomValidateMixin


class PromoterSetSerializer(CustomValidateMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifiedBy = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = PromoterSet
        fields = "__all__"
