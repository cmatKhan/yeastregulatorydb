import django_filters

from ...models.BindingManualQC import BindingManualQC


class BindingManualQCFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter()
    pk = django_filters.NumberFilter()
    binding_id = django_filters.NumberFilter()
    rank_response_pass = django_filters.BooleanFilter()
    best_response_pass = django_filters.BooleanFilter()
    data_usable = django_filters.BooleanFilter()
    passing_replicate = django_filters.BooleanFilter()
    regulator_id = django_filters.NumberFilter(field_name="binding_id__regulator")
    regulator_locus_tag = django_filters.CharFilter(
        field_name="binding_id__regulator__locus_tag", lookup_expr="iexact"
    )
    regulator_symbol = django_filters.CharFilter(field_name="binding_id__regulator__symbol", lookup_expr="iexact")
    batch = django_filters.CharFilter(field_name="binding_id__batch", lookup_expr="iexact")
    source_id = django_filters.CharFilter(field_name="binding_id__source_id", lookup_expr="iexact")

    class Meta:
        model = BindingManualQC
        fields = [
            "id",
            "pk",
            "binding_id",
            "rank_response_pass",
            "best_response_pass",
            "data_usable",
            "passing_replicate",
            "regulator_id",
            "regulator_locus_tag",
            "regulator_symbol",
            "batch",
            "source",
        ]
