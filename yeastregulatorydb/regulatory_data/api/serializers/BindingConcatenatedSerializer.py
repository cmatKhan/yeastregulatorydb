from rest_framework import serializers
from ...models import BindingConcatenated, Binding


class BindingConcatenatedSerializer(serializers.ModelSerializer):
    bindings = serializers.PrimaryKeyRelatedField(queryset=Binding.objects.all(), many=True)

    class Meta:
        model = BindingConcatenated
        fields = ["id", "bindings", "genomic_inserts", "mito_inserts", "plasmid_inserts", "notes"]
