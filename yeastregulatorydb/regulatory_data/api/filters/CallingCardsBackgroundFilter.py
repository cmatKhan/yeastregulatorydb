import django_filters

from ...models.CallingCardsBackground import CallingCardsBackground


class CallingCardsBackgroundFilter(django_filters.filters.FilterSet):
    class Meta:
        model = CallingCardsBackground
        fields = {"name": ["exact"]}
