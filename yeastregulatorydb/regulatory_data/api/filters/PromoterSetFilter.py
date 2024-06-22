import django_filters

from ...models.PromoterSet import PromoterSet


class PromoterSetFilter(django_filters.rest_framework.FilterSet):
    class Meta:
        model = PromoterSet
        fields = {"id": ["exact"], "name": ["exact"]}
