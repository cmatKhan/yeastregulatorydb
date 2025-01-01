from django_filters import BaseInFilter, NumberFilter


class NumbersInFilter(BaseInFilter, NumberFilter):
    pass
