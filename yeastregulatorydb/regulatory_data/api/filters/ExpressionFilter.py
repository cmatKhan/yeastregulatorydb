import logging

import django_filters
from django.db.models import Q
from django.db.models.query import QuerySet

from ...models.Expression import Expression

logger = logging.getLogger(__name__)


class ExpressionFilter(django_filters.FilterSet):
    # pylint: disable=R0801
    id = django_filters.NumberFilter()
    pk = django_filters.NumberFilter()
    regulator = django_filters.NumberFilter()
    regulator_locus_tag = django_filters.CharFilter(
        field_name="regulator__genomicfeature__locus_tag", lookup_expr="iexact"
    )
    regulator_symbol = django_filters.CharFilter(field_name="regulator__genomicfeature__symbol", lookup_expr="iexact")
    batch = django_filters.CharFilter(field_name="batch", lookup_expr="iexact")
    # pylint: enable=R0801
    replicate = django_filters.NumberFilter()
    control = django_filters.CharFilter(lookup_expr="iexact")
    mechanism = django_filters.CharFilter(lookup_expr="iexact")
    restriction = django_filters.CharFilter(lookup_expr="iexact")
    time = django_filters.NumberFilter(field_name="time")
    source = django_filters.NumberFilter()
    source_time = django_filters.CharFilter(method="filter_source_time")
    lab = django_filters.CharFilter(field_name="source__lab", lookup_expr="iexact")
    assay = django_filters.CharFilter(field_name="source__assay", lookup_expr="iexact")
    workflow = django_filters.CharFilter(field_name="source__workflow", lookup_expr="iexact")

    class Meta:
        model = Expression
        fields = [
            "id",
            "pk",
            "regulator",
            "regulator_locus_tag",
            "regulator_symbol",
            "batch",
            "replicate",
            "control",
            "mechanism",
            "restriction",
            "time",
            "source",
            "source_time",
            "lab",
            "assay",
            "workflow",
        ]

    # pylint: enable=R0801

    def filter_source_time(self, queryset, name, value) -> QuerySet:
        """
        Filter by source/time tuples. The value should be a string
        of comma separated tuples. tuples should be separated by
        semi-colons. For example: "mcisaac_oe,15;2,0;3,0"

        :param queryset: Expression queryset
        :param name: name of the field to filter
        :param value: value to filter by
        :return: filtered queryset

        """
        # parse the source/time string into tuples
        source_time_list = value.split(";")
        # create a Q object to hold the conditions
        matched_conditions = Q()
        # iterate over source/time tuples
        filtered_source_set = set()
        for source_time in source_time_list:
            # split the string into 2 parts on the comma
            source_name, time = source_time.split(",")
            time = int(time)
            matched_conditions |= Q(source__name=source_name, time=time)
            filtered_source_set.add(source_name)
        # apply the filter such that the the records with a specified source/time
        # are filtered for that specific set of source_names and times. Otherwise,
        # the rest of the records with other source_names are untouched
        # Include records whose source names are not in the source_time pairs
        unmatched_sources = Q(source__name__in=filtered_source_set)
        final_conditions = matched_conditions | ~unmatched_sources

        return queryset.filter(final_conditions)
