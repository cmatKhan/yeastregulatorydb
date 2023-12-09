import django_filters

from ...models.PromoterSet import PromoterSet


class PromoterSetFilter(django_filters.FilterSet):
    class Meta:
        model = PromoterSet
        fields = {"name": ["exact"]}
