from rest_framework import serializers

from ...models.Expression import Expression
from .mixins import CustomValidateMixin, FileValidationMixin, GetDataSourceMixin, GetOrCreateRegulatorMixin


class ExpressionSerializer(
    GetOrCreateRegulatorMixin,
    GetDataSourceMixin,
    CustomValidateMixin,
    FileValidationMixin,
    serializers.ModelSerializer,
):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifier = serializers.CharField(source="uploader.username", required=False)
    regulator_locus_tag = serializers.CharField(source="regulator.genomicfeature.locus_tag", read_only=True)
    regulator_symbol = serializers.CharField(source="regulator.genomicfeature.symbol", read_only=True)

    class Meta:
        model = Expression
        fields = "__all__"

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Add the custom attribute to the serialized data
        ret["promotersetsig_processing"] = getattr(instance, "promotersetsig_processing", False)
        return ret
