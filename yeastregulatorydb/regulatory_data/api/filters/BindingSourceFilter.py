import django_filters

from ...models import BindingSource


class BindingSourceFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter()
    pk = django_filters.NumberFilter()
    fileformat_id = django_filters.NumberFilter()
    fileformat = django_filters.CharFilter(field_name="fileformat_id__fileformat", lookup_expr="iexact")
    lab = django_filters.CharFilter(lookup_expr="iexact")
    assay = django_filters.CharFilter(lookup_expr="iexact")
    workflow = django_filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = BindingSource
        fields = [
            "id",
            "pk",
            "fileformat_id",
            "fileformat",
            "lab",
            "assay",
            "workflow",
        ]
