import django_filters

from ...models.FileFormat import FileFormat


class FileFormatFilter(django_filters.FilterSet):
    class Meta:
        model = FileFormat
        fields = {"fileformat": ["exact"]}
