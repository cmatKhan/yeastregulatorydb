import django_filters

from ...models.ExpressionSource import ExpressionSource


class ExpressionSourceFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter()
    pk = django_filters.NumberFilter()
    fileformat_id = django_filters.NumberFilter()
    fileformat = django_filters.CharFilter(field_name="fileformat__fileformat", lookup_expr="iexact")
    lab = django_filters.CharFilter(lookup_expr="iexact")
    assay = django_filters.CharFilter(lookup_expr="iexact")
    workflow = django_filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = ExpressionSource
        fields = ["id", "pk", "fileformat_id", "fileformat", "lab", "assay", "workflow"]
