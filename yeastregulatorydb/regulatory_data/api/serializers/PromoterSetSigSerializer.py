from rest_framework import serializers

from ...models import Binding, BindingConcatenated, CallingCardsBackground, FileFormat, PromoterSetSig
from .mixins.CustomValidateMixin import CustomValidateMixin
from .mixins.FileValidationMixin import FileValidationMixin


class PromoterSetSigSerializer(CustomValidateMixin, FileValidationMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifier = serializers.CharField(source="uploader.username", required=False)
    single_binding = serializers.PrimaryKeyRelatedField(
        queryset=Binding.objects.all(), required=False, allow_null=True
    )
    composite_binding = serializers.PrimaryKeyRelatedField(
        queryset=BindingConcatenated.objects.all(), required=False, allow_null=True
    )
    fileformat = serializers.PrimaryKeyRelatedField(queryset=FileFormat.objects.all(), required=True)
    background = serializers.PrimaryKeyRelatedField(
        queryset=CallingCardsBackground.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = PromoterSetSig
        fields = "__all__"

    def validate(self, data):
        # Validate (before getting to the DB) that either single_binding
        # or composite_binding is set, but not both
        single_binding = data.get("single_binding")
        composite_binding = data.get("composite_binding")

        if not single_binding and not composite_binding:
            raise serializers.ValidationError("Either single_binding or composite_binding must be set.")
        if single_binding and composite_binding:
            raise serializers.ValidationError("Only one of single_binding or composite_binding can be set.")

        return super().validate(data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["source"] = self.get_source(instance)
        ret["regulator_symbol"] = self.get_regulator_symbol(instance)
        ret["regulator_locus_tag"] = self.get_regulator_locus_tag(instance)
        ret["background_name"] = instance.background.name if instance.background else None
        ret["rank_recall"] = self.get_rank_recall(instance)
        ret["data_usable"] = self.get_data_usable(instance)
        return ret

    def get_source(self, instance):
        if instance.single_binding:
            return instance.single_binding.source.name
        elif instance.composite_binding and instance.composite_binding.bindings.exists():
            return instance.composite_binding.bindings.first().source.name
        return None

    def get_regulator_symbol(self, instance):
        if instance.single_binding:
            return instance.single_binding.regulator.genomicfeature.symbol
        elif instance.composite_binding and instance.composite_binding.bindings.exists():
            return instance.composite_binding.bindings.first().regulator.genomicfeature.symbol
        return None

    def get_regulator_locus_tag(self, instance):
        if instance.single_binding:
            return instance.single_binding.regulator.genomicfeature.locus_tag
        elif instance.composite_binding and instance.composite_binding.bindings.exists():
            return instance.composite_binding.bindings.first().regulator.genomicfeature.locus_tag
        return None

    def get_rank_recall(self, instance):
        if instance.single_binding:
            return instance.single_binding.bindingmanualqc_set.first().rank_recall
        elif instance.composite_binding and instance.composite_binding.bindingmanualqc_set.exists():
            return instance.composite_binding.bindingmanualqc_set.first().rank_recall
        return None

    def get_data_usable(self, instance):
        if instance.single_binding:
            return instance.single_binding.bindingmanualqc_set.first().data_usable
        elif instance.composite_binding and instance.composite_binding.bindingmanualqc_set.exists():
            return instance.composite_binding.bindingmanualqc_set.first().data_usable
        return None
