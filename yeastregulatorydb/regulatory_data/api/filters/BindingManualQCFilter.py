import django_filters
from django.db.models import Q

from ...models.BindingManualQC import BindingManualQC


class BindingManualQCFilter(django_filters.rest_framework.FilterSet):
    id = django_filters.NumberFilter()
    single_binding = django_filters.NumberFilter(label="Single Binding ID", help_text="ID of the single binding")
    composite_binding = django_filters.NumberFilter(
        label="Composite Binding ID", help_text="ID of the composite binding"
    )
    best_datatype = django_filters.ChoiceFilter(
        choices=BindingManualQC.MANUAL_QC_CHOICES, label="Best Datatype", help_text="Best datatype for the binding"
    )
    data_usable = django_filters.ChoiceFilter(
        choices=BindingManualQC.MANUAL_QC_CHOICES, label="Data Usable", help_text="Data usable for the binding"
    )
    passing_replicate = django_filters.ChoiceFilter(
        choices=BindingManualQC.MANUAL_QC_CHOICES,
        label="Passing Replicate",
        help_text="Passing replicate for the binding",
    )
    rank_recall = django_filters.ChoiceFilter(
        choices=BindingManualQC.MANUAL_QC_CHOICES, label="Rank Recall", help_text="Rank recall for the binding"
    )
    regulator = django_filters.NumberFilter(method="filter_regulator", label="Regulator ID", help_text="Regulator ID")
    regulator_locus_tag = django_filters.CharFilter(
        method="filter_regulator_locus_tag",
        lookup_expr="iexact",
        label="Regulator locus tag",
        help_text="Regulator locus tag",
    )
    regulator_symbol = django_filters.CharFilter(
        method="filter_regulator_symbol", lookup_expr="iexact", label="Regulator symbol", help_text="Regulator symbol"
    )
    batch = django_filters.CharFilter(
        method="filter_batch", lookup_expr="iexact", label="Binding Batch", help_text="Binding batch"
    )
    source = django_filters.CharFilter(
        method="filter_source", lookup_expr="iexact", label="Data Source ID", help_text="Data Source ID"
    )
    source_name = django_filters.CharFilter(
        method="filter_source_name", lookup_expr="iexact", label="Data Source name", help_text="Data Source name"
    )

    class Meta:
        model = BindingManualQC
        fields = [
            "id",
            "single_binding",
            "composite_binding",
            "best_datatype",
            "data_usable",
            "passing_replicate",
            "rank_recall",
            "regulator",
            "regulator_locus_tag",
            "regulator_symbol",
            "batch",
            "source",
            "source_name",
        ]

    def filter_binding(self, queryset, name, value):
        return queryset.filter(
            Q(single_binding__isnull=False, **{f"single_binding__{name}": value})
            | Q(composite_binding__isnull=False, **{f"composite_binding__{name}": value})
        )

    def filter_regulator(self, queryset, name, value):
        return self.filter_binding(queryset, "regulator", value)

    def filter_regulator_locus_tag(self, queryset, name, value):
        return self.filter_binding(queryset, "regulator__genomicfeature__locus_tag", value)

    def filter_regulator_symbol(self, queryset, name, value):
        return self.filter_binding(queryset, "regulator__genomicfeature__symbol", value)

    def filter_batch(self, queryset, name, value):
        return self.filter_binding(queryset, "batch", value)

    def filter_source(self, queryset, name, value):
        return self.filter_binding(queryset, "source", value)

    def filter_source_name(self, queryset, name, value):
        return self.filter_binding(queryset, "source__name", value)
