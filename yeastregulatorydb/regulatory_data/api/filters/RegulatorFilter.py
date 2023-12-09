import django_filters

from ...models.Regulator import Regulator


class RegulatorFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter(field_name="id")
    pk = django_filters.NumberFilter(field_name="pk")
    regulator_locus_tag = django_filters.CharFilter(field_name="regulator__locus_tag", lookup_expr="iexact")
    regulator_symbol = django_filters.CharFilter(field_name="regulator__symbol", lookup_expr="iexact")
    under_development = django_filters.BooleanFilter(field_name="under_development")

    class Meta:
        model = Regulator
        fields = ["id", "pk", "regulator_locus_tag", "regulator_symbol", "under_development"]
