from rest_framework import serializers

from ...models.Regulator import Regulator
from .mixins.CustomValidateMixin import CustomValidateMixin


class RegulatorSerializer(CustomValidateMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifier = serializers.CharField(source="uploader.username", required=False)
    regulator_locus_tag = serializers.CharField(source="genomicfeature.locus_tag", read_only=True)
    regulator_symbol = serializers.CharField(source="genomicfeature.symbol", read_only=True)

    class Meta:
        model = Regulator
        fields = "__all__"
