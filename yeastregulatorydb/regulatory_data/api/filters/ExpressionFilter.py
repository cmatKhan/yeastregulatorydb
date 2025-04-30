import logging

import django_filters
from django.db.models import Q
from django.db.models.query import QuerySet

from ...models.Expression import Expression
from .utils.ListCharFilter import ListCharFilter

logger = logging.getLogger(__name__)


class ExpressionFilter(django_filters.rest_framework.FilterSet):
    # pylint: disable=R0801
    id = django_filters.NumberFilter()
    regulator = django_filters.NumberFilter(help_text="Regulator Record ID")
    regulator_locus_tag = ListCharFilter(
        field_name="regulator__genomicfeature__locus_tag",
        lookup_expr="iexact",
        label="Regulator Locus Tag",
        help_text="Comma separated list of locus tags",
    )
    regulator_symbol = ListCharFilter(
        field_name="regulator__genomicfeature__symbol",
        lookup_expr="iexact",
        label="Regulator Symbol",
        help_text="Comma separated list of symbols",
    )
    batch = django_filters.CharFilter(field_name="batch", lookup_expr="iexact", help_text="Expression Batch string")
    # pylint: enable=R0801
    replicate = django_filters.NumberFilter(label="Replicate Number", help_text="Replicate number")
    control = django_filters.CharFilter(
        lookup_expr="iexact", label="Experiment control condition", help_text="Control condition"
    )
    mechanism = django_filters.CharFilter(
        lookup_expr="iexact", label="Regulatory Mechanism", help_text="Regulatory Mechanism (McIsaac only)"
    )
    restriction = django_filters.CharFilter(
        lookup_expr="iexact", label="Restriction enzyme", help_text="Regulatory enzyme (McIsaac only)"
    )
    time = django_filters.NumberFilter(field_name="time", label="Time Point", help_text="Time point (McIsaac only)")
    strain = ListCharFilter(
        field_name="strain", lookup_expr="iexact", label="Strain", help_text="Comma separated list of strains"
    )
    source = django_filters.NumberFilter(label="Source Record ID", help_text="Source Record ID")
    source_name = django_filters.CharFilter(
        field_name="source__name", lookup_expr="iexact", label="Source Name", help_text="Source Name"
    )
    source_time = django_filters.CharFilter(
        method="filter_source_time",
        label="Source/Time",
        help_text="Comma separated tuples of source/time pairs separated by semi-colons",
    )
    lab = django_filters.CharFilter(
        field_name="source__lab", lookup_expr="iexact", label="Lab Name", help_text="Lab Name"
    )
    assay = django_filters.CharFilter(
        field_name="source__assay", lookup_expr="iexact", label="Assay Name", help_text="Assay Name"
    )
    workflow = django_filters.CharFilter(
        field_name="source__workflow", lookup_expr="iexact", label="Workflow Name", help_text="Workflow Name"
    )
    preferred_replicate = django_filters.BooleanFilter(
        field_name="preferred_replicate",
        label="Preferred Replicate",
        help_text="Filter by whether the replicate is preferred (True or False)",
    )

    class Meta:
        model = Expression
        fields = [
            "id",
            "regulator",
            "regulator_locus_tag",
            "regulator_symbol",
            "batch",
            "replicate",
            "control",
            "mechanism",
            "restriction",
            "time",
            "strain",
            "source",
            "source_time",
            "lab",
            "assay",
            "workflow",
            "preferred_replicate",
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
