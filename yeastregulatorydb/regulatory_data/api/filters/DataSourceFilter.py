import django_filters

from ...models import DataSource


class DataSourceFilter(django_filters.rest_framework.FilterSet):
    id = django_filters.NumberFilter()
    fileformat_id = django_filters.NumberFilter()
    fileformat = django_filters.CharFilter(field_name="fileformat__fileformat", lookup_expr="iexact")
    lab = django_filters.CharFilter(lookup_expr="iexact")
    assay = django_filters.CharFilter(lookup_expr="iexact")
    workflow = django_filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = DataSource
        fields = [
            "id",
            "fileformat_id",
            "fileformat",
            "lab",
            "assay",
            "workflow",
        ]
