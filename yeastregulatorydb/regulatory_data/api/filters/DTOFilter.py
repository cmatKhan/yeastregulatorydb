import django_filters

from ...models.DTO import DTO
from .utils.CharInFilter import CharInFilter


class DTOFilter(django_filters.rest_framework.FilterSet):
    id = django_filters.BaseInFilter(field_name="id", lookup_expr="in")
    promotersetsig = django_filters.NumberFilter(
        label="Promoter Set Signature ID", help_text="ID of the promoter set signature"
    )
    expression = django_filters.NumberFilter(label="Expression ID", help_text="ID of the expression")
    regulator_id = django_filters.NumberFilter(
        field_name="expression__regulator", label="Regulator ID", help_text="ID of the regulator", lookup_expr="in"
    )
    regulator_locus_tag = CharInFilter(
        field_name="expression__regulator__genomicfeature__locus_tag",
        lookup_expr="in",
        label="Regulator Locus Tag",
        help_text="Regulator Locus Tag",
    )
    regulator_symbol = django_filters.CharFilter(
        method="filter_regulator_symbol", label="Regulator Symbol", help_text="Regulator Symbol", lookup_expr="in"
    )

    class Meta:
        model = DTO
        fields = ["id", "promotersetsig", "expression", "regulator_id", "regulator_locus_tag", "regulator_symbol"]

    def filter_regulator_symbol(self, queryset, name, value):
        # Split the value by commas
        tags = value.split(",")
        # Apply an `in` filter to match any of the tags
        return queryset.filter(**{f"expression__regulator__genomicfeature__symbol__in": tags})
