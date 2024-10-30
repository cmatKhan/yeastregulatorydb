import django_filters

from ...models.RankResponse import RankResponse


class RankResponseFilter(django_filters.rest_framework.FilterSet):
    id = django_filters.NumberFilter(field_name="id")
    promotersetsig = django_filters.NumberFilter(
        label="Promoter Set Signature ID", help_text="ID of the promoter set signature"
    )
    expression = django_filters.NumberFilter(label="Expression ID", help_text="ID of the expression")

    class Meta:
        model = RankResponse
        fields = ["id", "promotersetsig", "expression"]
