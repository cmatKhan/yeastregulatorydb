import logging
from typing import Any, Dict

from django.db.models import Q
from rest_framework import serializers

from ...models import BindingManualQC, PromoterSetSig, RankResponse
from .mixins.CustomValidateMixin import CustomValidateMixin

logger = logging.getLogger(__name__)


class BindingManualQCSerializer(CustomValidateMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifier = serializers.CharField(source="uploader.username", required=False)
    rank_response_status = serializers.CharField(read_only=True)
    dto_status = serializers.CharField(read_only=True)
    manual_fail = serializers.BooleanField(required=False)

    class Meta:
        model = BindingManualQC
        fields = "__all__"

    def validate(self, data):
        # if this is a partial update, retrieve the instance
        instance = getattr(self, "instance", None)

        # get the single_binding or composite_binding from the data or the instance
        single_binding = data.get("single_binding", getattr(instance, "single_binding", None))
        composite_binding = data.get("composite_binding", getattr(instance, "composite_binding", None))

        # Validate (before getting to the DB) that either single_binding
        # or composite_binding is set, but not both
        if not single_binding and not composite_binding:
            raise serializers.ValidationError("Either single_binding or composite_binding must be set.")
        if single_binding and composite_binding:
            raise serializers.ValidationError("Only one of single_binding or composite_binding can be set.")

        return super().validate(data)

    def get_binding(self, instance: BindingManualQC) -> Any:
        single_binding = instance.single_binding
        composite_binding = instance.composite_binding
        return single_binding if single_binding else composite_binding

    def get_batch(self, instance: BindingManualQC) -> str:
        single_binding = instance.single_binding
        return single_binding.batch if single_binding else None

    def get_batch_replicate(self, instance: BindingManualQC) -> int:
        single_binding = instance.single_binding
        return single_binding.replicate if single_binding else None

    def get_source(self, instance: BindingManualQC) -> Any:
        binding_instance = self.get_binding(instance)
        return binding_instance.source.id if binding_instance else None

    def get_source_name(self, instance: BindingManualQC) -> str:
        binding_instance = self.get_binding(instance)
        return binding_instance.source.name if binding_instance else None

    def get_regulator(self, instance: BindingManualQC) -> Any:
        binding_instance = self.get_binding(instance)
        return binding_instance.regulator.id if binding_instance else None

    def get_regulator_locus_tag(self, instance: BindingManualQC) -> str:
        binding_instance = self.get_binding(instance)
        return binding_instance.regulator.genomicfeature.locus_tag if binding_instance else None

    def get_regulator_symbol(self, instance: BindingManualQC) -> str:
        binding_instance = self.get_binding(instance)
        return binding_instance.regulator.genomicfeature.symbol if binding_instance else None

    def to_representation(self, instance: Any) -> Dict[str, Any]:
        ret = super().to_representation(instance)
        ret["single_binding"] = instance.single_binding.id if instance.single_binding else None
        ret["composite_binding"] = instance.composite_binding.id if instance.composite_binding else None
        ret["batch"] = self.get_batch(instance)
        ret["batch_replicate"] = self.get_batch_replicate(instance)
        ret["source"] = self.get_source(instance)
        ret["source_name"] = self.get_source_name(instance)
        ret["regulator"] = self.get_regulator(instance)
        ret["regulator_locus_tag"] = self.get_regulator_locus_tag(instance)
        ret["regulator_symbol"] = self.get_regulator_symbol(instance)
        return ret
