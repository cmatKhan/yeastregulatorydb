from rest_framework import serializers

from ...models import RankResponse
from .mixins.CustomValidateMixin import CustomValidateMixin


class RankResponseSerializer(CustomValidateMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifier = serializers.CharField(source="uploader.username", required=False)
    regulator_symbol = serializers.CharField(read_only=True)
    regulator_locus_tag = serializers.CharField(read_only=True)
    binding_source = serializers.SerializerMethodField()
    expression_source = serializers.SerializerMethodField()
    expression_time = serializers.CharField(read_only=True)
    expression_mechanism = serializers.CharField(read_only=True)
    expression_restrction = serializers.CharField(read_only=True)

    class Meta:
        model = RankResponse
        fields = "__all__"

    def get_binding_source(self, obj):
        # TODO: fix the naming -- promotersetsig.get_source
        return obj.get_binding_source_name()

    def get_expression_source(self, obj):
        return obj.get_expression_source_name()
