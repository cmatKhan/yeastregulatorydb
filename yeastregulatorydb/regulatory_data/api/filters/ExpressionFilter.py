import django_filters

from ...models.Expression import Expression


class ExpressionFilter(django_filters.FilterSet):
    # pylint: disable=R0801
    id = django_filters.NumberFilter()
    pk = django_filters.NumberFilter()
    regulator = django_filters.NumberFilter()
    regulator_locus_tag = django_filters.CharFilter(
        field_name="regulator__genomicfeature__locus_tag", lookup_expr="iexact"
    )
    regulator_symbol = django_filters.CharFilter(field_name="regulator__genomicfeature__symbol", lookup_expr="iexact")
    batch = django_filters.CharFilter(field_name="batch", lookup_expr="iexact")
    # pylint: enable=R0801
    replicate = django_filters.NumberFilter()
    control = django_filters.CharFilter(lookup_expr="iexact")
    mechanism = django_filters.CharFilter(lookup_expr="iexact")
    restriction = django_filters.CharFilter(lookup_expr="iexact")
    time = django_filters.NumberFilter(field_name="time")
    source = django_filters.NumberFilter()
    lab = django_filters.CharFilter(field_name="source__lab", lookup_expr="iexact")
    assay = django_filters.CharFilter(field_name="source__assay", lookup_expr="iexact")
    workflow = django_filters.CharFilter(field_name="source__workflow", lookup_expr="iexact")

    class Meta:
        model = Expression
        fields = [
            "id",
            "pk",
            "regulator",
            "regulator_locus_tag",
            "regulator_symbol",
            "batch",
            "replicate",
            "control",
            "mechanism",
            "restriction",
            "time",
            "source",
            "lab",
            "assay",
            "workflow",
        ]

    # pylint: enable=R0801
