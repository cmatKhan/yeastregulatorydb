from rest_framework import serializers

from ...models import UnivariateModels
from .mixins.CustomValidateMixin import CustomValidateMixin


class UnivariateModelsSerializer(CustomValidateMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifier = serializers.CharField(source="uploader.username", required=False)
    regulator_symbol = serializers.CharField(read_only=True)
    regulator_locus_tag = serializers.CharField(read_only=True)
    binding_source = serializers.CharField(read_only=True)
    expression_source = serializers.CharField(read_only=True)

    class Meta:
        model = UnivariateModels
        fields = "__all__"
