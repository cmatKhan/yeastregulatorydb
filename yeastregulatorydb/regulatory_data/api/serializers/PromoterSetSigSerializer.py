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

        if instance.single_binding:
            single_binding = instance.single_binding
            ret["source"] = single_binding.source.name
            ret["regulator_symbol"] = single_binding.regulator.genomicfeature.symbol
            ret["regulator_locus_tag"] = single_binding.regulator.genomicfeature.locus_tag
            ret["condition"] = single_binding.condition
            qc_set = list(single_binding.bindingmanualqc_set.all())
            ret["rank_recall"] = qc_set[0].rank_recall if qc_set else None
            ret["data_usable"] = qc_set[0].data_usable if qc_set else None
        elif instance.composite_binding:
            composite_binding = instance.composite_binding
            bindings = list(composite_binding.bindings.all())
            if bindings:
                first_binding = bindings[0]
                ret["source"] = first_binding.source.name
                ret["regulator_symbol"] = first_binding.regulator.genomicfeature.symbol
                ret["regulator_locus_tag"] = first_binding.regulator.genomicfeature.locus_tag
                qc_set = list(first_binding.bindingmanualqc_set.all())
                ret["rank_recall"] = qc_set[0].rank_recall if qc_set else None
                ret["data_usable"] = qc_set[0].data_usable if qc_set else None
            else:
                ret["source"] = None
                ret["regulator_symbol"] = None
                ret["regulator_locus_tag"] = None
                ret["rank_recall"] = None
                ret["data_usable"] = None
        else:
            ret["source"] = None
            ret["regulator_symbol"] = None
            ret["regulator_locus_tag"] = None
            ret["condition"] = None
            ret["rank_recall"] = None
            ret["data_usable"] = None

        ret["background_name"] = instance.background.name if instance.background else None

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
