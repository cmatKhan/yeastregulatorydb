import django_filters

from ...models.Expression import Expression


class ExpressionFilter(django_filters.FilterSet):
    # pylint: disable=R0801
    id = django_filters.NumberFilter()
    pk = django_filters.NumberFilter()
    regulator_id = django_filters.NumberFilter()
    regulator_locus_tag = django_filters.CharFilter(field_name="regulator_id__locus_tag", lookup_expr="iexact")
    regulator_symbol = django_filters.CharFilter(field_name="regulator_id__symbol", lookup_expr="iexact")
    batch = django_filters.CharFilter(field_name="batch", lookup_expr="iexact")
    # pylint: enable=R0801
    replicate = django_filters.NumberFilter()
    control = django_filters.CharFilter(lookup_expr="iexact")
    mechanism = django_filters.CharFilter(lookup_expr="iexact")
    restriction = django_filters.CharFilter(lookup_expr="iexact")
    time = django_filters.NumberFilter(field_name="time")
    source_id = django_filters.CharFilter(lookup_expr="iexact")
    lab = django_filters.CharFilter(field_name="source_id__lab", lookup_expr="iexact")
    assay = django_filters.CharFilter(field_name="source_id__assay", lookup_expr="iexact")
    workflow = django_filters.CharFilter(field_name="source_id__workflow", lookup_expr="iexact")

    class Meta:
        model = Expression
        fields = [
            "id",
            "pk",
            "regulator_id",
            "regulator_locus_tag",
            "regulator_symbol",
            "batch",
            "replicate",
            "control",
            "mechanism",
            "restriction",
            "time",
            "source_id",
            "lab",
            "assay",
            "workflow",
        ]

    # pylint: enable=R0801
