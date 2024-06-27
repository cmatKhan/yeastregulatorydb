from rest_framework import serializers

from ...models import PromoterSetSig, Binding, BindingConcatenated
from .BindingConcatenatedSerializer import BindingConcatenatedSerializer
from .mixins.CustomValidateMixin import CustomValidateMixin
from .mixins.FileValidationMixin import FileValidationMixin


# class PromoterSetSigSerializer(CustomValidateMixin, FileValidationMixin, serializers.ModelSerializer):
#     uploader = serializers.ReadOnlyField(source="uploader.username")
#     modifier = serializers.CharField(source="uploader.username", required=False)

#     class Meta:
#         model = PromoterSetSig
#         fields = "__all__"

#     def get_background_id(self, obj):
#         return obj.background.id if obj.background else "undefined"

#     def to_representation(self, instance):
#         ret = super().to_representation(instance)
#         # Add the custom attribute to the serialized data
#         ret["rankresponse_processing"] = getattr(instance, "rankresponse_processing", False)
#         return ret


class PromoterSetSigSerializer(CustomValidateMixin, FileValidationMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifier = serializers.CharField(source="uploader.username", required=False)
    single_binding = serializers.PrimaryKeyRelatedField(
        queryset=Binding.objects.all(), required=False, allow_null=True
    )
    composite_binding = BindingConcatenatedSerializer(required=False, allow_null=True)

    class Meta:
        model = PromoterSetSig
        fields = "__all__"

    def get_background_id(self, obj):
        return obj.background.id if obj.background else "undefined"

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Add the custom attribute to the serialized data
        ret["rankresponse_processing"] = getattr(instance, "rankresponse_processing", False)
        return ret

    def create(self, validated_data):
        composite_binding_data = validated_data.pop("composite_binding", None)
        if composite_binding_data:
            composite_binding = BindingConcatenated.objects.create(
                genomic_inserts=composite_binding_data.get("genomic_inserts", 0),
                mito_inserts=composite_binding_data.get("mito_inserts", 0),
                plasmid_inserts=composite_binding_data.get("plasmid_inserts", 0),
                notes=composite_binding_data.get("notes", "none"),
            )
            composite_binding.bindings.set(composite_binding_data["bindings"])
            validated_data["composite_binding"] = composite_binding

        return super().create(validated_data)

    def update(self, instance, validated_data):
        composite_binding_data = validated_data.pop("composite_binding", None)
        if composite_binding_data:
            if instance.composite_binding:
                instance.composite_binding.bindings.set(composite_binding_data["bindings"])
                instance.composite_binding.genomic_inserts = composite_binding_data.get(
                    "genomic_inserts", instance.composite_binding.genomic_inserts
                )
                instance.composite_binding.mito_inserts = composite_binding_data.get(
                    "mito_inserts", instance.composite_binding.mito_inserts
                )
                instance.composite_binding.plasmid_inserts = composite_binding_data.get(
                    "plasmid_inserts", instance.composite_binding.plasmid_inserts
                )
                instance.composite_binding.notes = composite_binding_data.get(
                    "notes", instance.composite_binding.notes
                )
                instance.composite_binding.save()
            else:
                composite_binding = BindingConcatenated.objects.create(
                    genomic_inserts=composite_binding_data.get("genomic_inserts", 0),
                    mito_inserts=composite_binding_data.get("mito_inserts", 0),
                    plasmid_inserts=composite_binding_data.get("plasmid_inserts", 0),
                    notes=composite_binding_data.get("notes", "none"),
                )
                composite_binding.bindings.set(composite_binding_data["bindings"])
                instance.composite_binding = composite_binding

        return super().update(instance, validated_data)
