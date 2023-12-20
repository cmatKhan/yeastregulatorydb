import django_filters

from ...models import RankResponse


class RankResponseFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter()
    pk = django_filters.NumberFilter()
    promotersetsig_id = django_filters.NumberFilter(field_name="promotersetsig__id")
    binding_source = django_filters.CharFilter(
        field_name="promotersetsig__binding__source__name", lookup_expr="iexact"
    )
    expression_id = django_filters.NumberFilter(field_name="expression__id")
    expression_source = django_filters.CharFilter(field_name="expression__source__name", lookup_expr="iexact")
    regulator_locus_tag = django_filters.CharFilter(
        field_name="expression__regulator__regulator__locus_tag", lookup_expr="iexact"
    )
    regulator_symbol = django_filters.CharFilter(
        field_name="expression__regulator__regulator__symbol", lookup_expr="iexact"
    )
    expression_effect_threshold = django_filters.NumberFilter()
    expression_pvalue_threshold = django_filters.NumberFilter()
    normalized = django_filters.BooleanFilter()
    significant_response = django_filters.BooleanFilter()

    class Meta:
        model = RankResponse
        fields = [
            "id",
            "pk",
            "promotersetsig_id",
            "binding_source",
            "expression_id",
            "expression_source",
            "regulator_locus_tag",
            "regulator_symbol",
            "expression_effect_threshold",
            "expression_pvalue_threshold",
            "normalized",
            "significant_response",
        ]
