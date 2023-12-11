from rest_framework import serializers

from ...models.GenomicFeature import GenomicFeature
from .mixins.CustomValidateMixin import CustomValidateMixin


class GenomicFeatureSerializer(CustomValidateMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifiedBy = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = GenomicFeature
        fields = "__all__"
