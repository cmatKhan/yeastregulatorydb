from rest_framework import serializers

from ...models import DTO
from .mixins.CustomValidateMixin import CustomValidateMixin


class DTOSerializer(CustomValidateMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifier = serializers.CharField(source="uploader.username", required=False)
    regulator_symbol = serializers.SerializerMethodField()
    binding_source = serializers.SerializerMethodField()
    expression_source = serializers.SerializerMethodField()

    class Meta:
        model = DTO
        fields = "__all__"

    def get_regulator_symbol(self, obj):
        return obj.get_genomicfeature().symbol

    def get_binding_source(self, obj):
        # TODO: fix the naming -- promotersetsig.get_source
        return obj.get_binding_source_name()

    def get_expression_source(self, obj):
        return obj.get_expression_source_name()
