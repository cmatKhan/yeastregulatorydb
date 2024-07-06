import django_filters

from yeastregulatorydb.regulatory_data.models import BindingConcatenated


class BindingConcatenatedFilter(django_filters.rest_framework.FilterSet):
    id = django_filters.NumberFilter()

    # Filter fields for related bindings
    regulator = django_filters.NumberFilter(field_name="regulator")
    regulator_locus_tag = django_filters.CharFilter(
        field_name="regulator__genomicfeature__locus_tag", lookup_expr="iexact"
    )
    regulator_symbol = django_filters.CharFilter(field_name="regulator__genomicfeature__symbol", lookup_expr="iexact")
    source = django_filters.NumberFilter(field_name="source")
    source_name = django_filters.CharFilter(field_name="source__name", lookup_expr="iexact")

    class Meta:
        model = BindingConcatenated
        fields = ["id", "regulator", "regulator_locus_tag", "regulator_symbol", "source", "source_name"]
