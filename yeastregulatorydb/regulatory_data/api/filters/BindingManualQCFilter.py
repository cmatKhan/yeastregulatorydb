import django_filters

from ...models.BindingManualQC import BindingManualQC


class BindingManualQCFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter()
    pk = django_filters.NumberFilter()
    binding = django_filters.NumberFilter()
    rank_response_pass = django_filters.BooleanFilter()
    best_response_pass = django_filters.BooleanFilter()
    data_usable = django_filters.BooleanFilter()
    passing_replicate = django_filters.BooleanFilter()
    regulator = django_filters.NumberFilter(field_name="binding__regulator")
    regulator_locus_tag = django_filters.CharFilter(field_name="binding__regulator__locus_tag", lookup_expr="iexact")
    regulator_symbol = django_filters.CharFilter(field_name="binding__regulator__symbol", lookup_expr="iexact")
    batch = django_filters.CharFilter(field_name="binding__batch", lookup_expr="iexact")
    source = django_filters.CharFilter(field_name="binding__source", lookup_expr="iexact")

    class Meta:
        model = BindingManualQC
        fields = [
            "id",
            "pk",
            "binding",
            "rank_response_pass",
            "best_response_pass",
            "data_usable",
            "passing_replicate",
            "regulator",
            "regulator_locus_tag",
            "regulator_symbol",
            "batch",
            "source",
        ]
