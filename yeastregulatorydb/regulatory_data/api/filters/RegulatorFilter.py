import django_filters

from ...models.Regulator import Regulator
from .utils.ListCharFilter import ListCharFilter


class RegulatorFilter(django_filters.rest_framework.FilterSet):
    id = django_filters.NumberFilter(field_name="id")
    regulator_locus_tag = django_filters.CharFilter(field_name="genomicfeature__locus_tag", lookup_expr="iexact")
    regulator_symbol = ListCharFilter(field_name="genomicfeature__symbol", lookup_expr="iexact")
    under_development = django_filters.BooleanFilter(field_name="under_development")

    class Meta:
        model = Regulator
        fields = ["id", "regulator_locus_tag", "regulator_symbol", "under_development"]
