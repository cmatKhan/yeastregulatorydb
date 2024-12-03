from django_filters import BaseInFilter, CharFilter


# Create a filter class for handling lists of values
class CharInFilter(BaseInFilter, CharFilter):
    pass
