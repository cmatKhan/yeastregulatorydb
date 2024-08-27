import logging

from rest_framework import serializers

from ...models import Binding, DataSource, Regulator
from .mixins import (
    CustomValidateMixin,
    FileValidationMixin,
    GetDataSourceMixin,
    GetOrCreateRegulatorMixin,
)

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
    regulator = serializers.PrimaryKeyRelatedField(queryset=Regulator.objects.all(), required=True)
    source = serializers.PrimaryKeyRelatedField(queryset=DataSource.objects.all(), required=True)
    data_usable = serializers.CharField(read_only=True)

    class Meta:
        model = Binding
        fields = "__all__"

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["source"] = instance.source.id
        ret["source_name"] = instance.source.name
        ret["assay"] = instance.source.assay
        ret["regulator_symbol"] = instance.regulator.genomicfeature.symbol
        ret["regulator_locus_tag"] = instance.regulator.genomicfeature.locus_tag

        return ret
