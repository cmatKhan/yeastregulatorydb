# from rest_framework import serializers

# from ...models import RankResponse
# from .mixins.CustomValidateMixin import CustomValidateMixin


# class RankResponseSerializer(CustomValidateMixin, serializers.ModelSerializer):
#     uploader = serializers.ReadOnlyField(source="uploader.username")
#     modifier = serializers.CharField(source="uploader.username", required=False)
#     regulator_id = serializers.IntegerField(read_only=True)
#     regulator_symbol = serializers.CharField(read_only=True)
#     regulator_locus_tag = serializers.CharField(read_only=True)
#     binding_source = serializers.SerializerMethodField()
#     expression_source = serializers.SerializerMethodField()
#     expression_time = serializers.CharField(read_only=True)
#     expression_mechanism = serializers.CharField(read_only=True)
#     expression_restrction = serializers.CharField(read_only=True)
#     dto_result = serializers.JSONField(read_only=True)

#     class Meta:
#         model = RankResponse
#         fields = "__all__"

#     def get_binding_source(self, obj):
#         # TODO: fix the naming -- promotersetsig.get_source
#         return obj.get_binding_source_name()

#     def get_expression_source(self, obj):
#         return obj.get_expression_source_name()

from rest_framework import serializers

from ...models import RankResponse
from .mixins.CustomValidateMixin import CustomValidateMixin


class RankResponseSerializer(CustomValidateMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifier = serializers.CharField(source="uploader.username", required=False)
    regulator_id = serializers.IntegerField(read_only=True)
    regulator_symbol = serializers.CharField(read_only=True)
    regulator_locus_tag = serializers.CharField(read_only=True)
    binding_source = serializers.SerializerMethodField()
    expression_source = serializers.SerializerMethodField()
    expression_time = serializers.CharField(read_only=True)
    expression_mechanism = serializers.CharField(read_only=True)
    expression_restrction = serializers.CharField(read_only=True)
    univariate_rsquared = serializers.FloatField(read_only=True)
    univariate_pvalue = serializers.FloatField(read_only=True)
    # New fields extracted from dto_result
    binding_rank_threshold = serializers.SerializerMethodField()
    perturbation_rank_threshold = serializers.SerializerMethodField()
    binding_set_size = serializers.SerializerMethodField()
    perturbation_set_size = serializers.SerializerMethodField()
    fdr = serializers.SerializerMethodField()
    empirical_pvalue = serializers.SerializerMethodField()

    class Meta:
        model = RankResponse
        fields = "__all__"

    def get_binding_source(self, obj):
        return obj.get_binding_source_name()

    def get_expression_source(self, obj):
        return obj.get_expression_source_name()

    # ---- Extracted DTO fields ----

    def get_binding_rank_threshold(self, obj):
        return self._safe_get(obj.dto_result, ["rank1"])

    def get_perturbation_rank_threshold(self, obj):
        return self._safe_get(obj.dto_result, ["rank2"])

    def get_binding_set_size(self, obj):
        return self._safe_get(obj.dto_result, ["set1_len"])

    def get_perturbation_set_size(self, obj):
        return self._safe_get(obj.dto_result, ["set2_len"])

    def get_fdr(self, obj):
        return self._safe_get(obj.dto_result, ["fdr"])

    def get_empirical_pvalue(self, obj):
        return self._safe_get(obj.dto_result, ["empirical_pvalue"])

    def _safe_get(self, result, keys):
        try:
            for k in keys:
                result = result[k]
            return result
        except Exception:
            return None
