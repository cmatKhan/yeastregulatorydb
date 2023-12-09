import django_filters

from ...models.FileFormat import FileFormat


class ExpressionManualQCFilter(django_filters.FilterSet):
    class Meta:
        model = FileFormat
        fields = {"fileformat": ["exact"]}
