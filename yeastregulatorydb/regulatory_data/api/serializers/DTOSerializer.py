from rest_framework import serializers

from ...models import DTO
from .mixins.CustomValidateMixin import CustomValidateMixin


class DTOSerializer(CustomValidateMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifier = serializers.CharField(source="uploader.username", required=False)
    regulator_symbol = serializers.CharField(read_only=True)
    regulator_locus_tag = serializers.CharField(read_only=True)
    binding_source = serializers.CharField(read_only=True)
    expression_source = serializers.CharField(read_only=True)
    binding_rank_threshold = serializers.SerializerMethodField()
    perturbation_rank_threshold = serializers.SerializerMethodField()
    binding_set_size = serializers.SerializerMethodField()
    perturbation_set_size = serializers.SerializerMethodField()
    fdr = serializers.SerializerMethodField()
    empirical_pvalue = serializers.SerializerMethodField()

    class Meta:
        model = DTO
        fields = "__all__"

    # a result json looks like this:
    # "result": {
    #             "fdr": 0.38730347884261584,
    #             "rank1": 146,
    #             "rank2": 407,
    #             "set1_len": 141,
    #             "set2_len": 399,
    #             "population_size": 5979,
    #             "empirical_pvalue": 0.3,
    #             "unpermuted_pvalue": 0.0024287128092493433,
    #             "unpermuted_intersection_size": 19
    #         },

    def get_binding_rank_threshold(self, obj):
        return self._safe_get(obj.result, ["rank1"])

    def get_perturbation_rank_threshold(self, obj):
        return self._safe_get(obj.result, ["rank2"])

    def get_binding_set_size(self, obj):
        return self._safe_get(obj.result, ["set1_len"])

    def get_perturbation_set_size(self, obj):
        return self._safe_get(obj.result, ["set2_len"])

    def get_fdr(self, obj):
        return self._safe_get(obj.result, ["fdr"])

    def get_empirical_pvalue(self, obj):
        return self._safe_get(obj.result, ["empirical_pvalue"])

    def _safe_get(self, result, keys):
        try:
            for k in keys:
                result = result[k]
            return result
        except Exception:
            return None
