from django.db.models import Q
from django_filters import CharFilter


class ListCharFilter(CharFilter):
    def filter(self, qs, value):
        if not value:
            return qs
        values = value.split(",")
        # Ensure the lookup_expr is correctly applied to each value in the list
        lookup = f"{self.field_name}__{self.lookup_expr}"
        q_objects = Q()
        for val in values:
            q_objects |= Q(**{lookup: val})
        return qs.filter(q_objects).distinct()
