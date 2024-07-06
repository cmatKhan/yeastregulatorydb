import django_filters

from ...models import DataSource


class DataSourceFilter(django_filters.rest_framework.FilterSet):
    id = django_filters.NumberFilter()
    fileformat_id = django_filters.NumberFilter(label="File Format ID", help_text="ID of the file format")
    fileformat = django_filters.CharFilter(
        field_name="fileformat__fileformat", lookup_expr="iexact", label="File Format", help_text="File format"
    )
    lab = django_filters.CharFilter(lookup_expr="iexact", label="Lab", help_text="Lab which generated the data")
    assay = django_filters.CharFilter(
        lookup_expr="iexact",
        label="Assay",
        help_text="Assay used to generate the data, eg 'callingcards' or 'chipexo'",
    )
    workflow = django_filters.CharFilter(
        lookup_expr="iexact", label="Workflow", help_text="Workflow used to generate data"
    )

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
