import django_filters

from ...models.FileFormat import FileFormat


class FileFormatFilter(django_filters.rest_framework.FilterSet):
    class Meta:
        model = FileFormat
        fields = {"fileformat": ["exact"]}
