import django_filters
from django.db.models import Q

from ...models import BindingManualQC, PromoterSetSig
from .utils import ensure_iterable


class PromoterSetSigFilter(django_filters.rest_framework.FilterSet):
    id = django_filters.NumberFilter(label="Promoter Set Signature ID", help_text="ID of the promoter set signature")
    single_binding = django_filters.NumberFilter(
        label="Single Binding ID",
        help_text="All binding replicates for single binding data sets have a single binding ID",
    )
    composite_binding = django_filters.NumberFilter(
        label="Composite Binding ID", help_text="Aggregated callingcards replicate sets have a composite binding ID"
    )
    promoter = django_filters.NumberFilter(label="PromoterSet ID", help_text="ID of the promoter set")
    promoter_name = django_filters.CharFilter(
        field_name="promoter__name", lookup_expr="iexact", label="Promoter Name", help_text="Name of the promoter set"
    )
    background = django_filters.NumberFilter(label="Background ID", help_text="ID of the background")
    background_name = django_filters.CharFilter(
        field_name="background__name",
        lookup_expr="iexact",
        label="Background Name",
        help_text="Name of the background",
    )
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
    source = django_filters.NumberFilter(method="filter_source", label="Data Source ID", help_text="Data Source ID")
    source_name = django_filters.CharFilter(
        method="filter_source_name", label="Data Source Name", help_text="Data Source Name"
    )
    lab = django_filters.CharFilter(
        method="filter_lab",
        lookup_expr="iexact",
        label="Binding Data Lab Name",
        help_text="Lab name which generated the binding data",
    )
    assay = django_filters.CharFilter(
        method="filter_assay", lookup_expr="iexact", label="Binding Data Assay Name", help_text="Binding assay name"
    )
    workflow = django_filters.CharFilter(
        method="filter_workflow",
        lookup_expr="iexact",
        label="Binding Data Workflow",
        help_text="Binding workflow name",
    )
    data_usable = django_filters.ChoiceFilter(
        method="filter_data_usable",
        choices=BindingManualQC.MANUAL_QC_CHOICES,
        label="Binding Data Usable",
        help_text="Binding data usable status",
    )
    aggregated = django_filters.BooleanFilter(
        method="filter_aggregated",
        label="Aggregated",
        help_text="Filter by aggregated (composite_binding is not null)",
    )
    condition = django_filters.CharFilter(
        method="filter_condition",
        label="Condition",
        help_text="Filter by the `condition` field in the single_binding record. Useful for harbison_chip data",
    )
    deduplicate = django_filters.BooleanFilter(
        method="filter_deduplicate",
        label="Deduplicate",
        help_text="When true, removes single_binding rec "
        "composite_binding exists for the same regulator_id and source_name",
    )

    class Meta:
        model = PromoterSetSig
        fields = [
            "id",
            "single_binding",
            "composite_binding",
            "promoter",
            "promoter_name",
            "background",
            "background_name",
            "regulator_locus_tag",
            "regulator_symbol",
            "source",
            "source_name",
            "lab",
            "assay",
            "workflow",
            "data_usable",
            "aggregated",
            "condition",
        ]

    def filter_binding(self, queryset, name, value):
        value = ensure_iterable(value)
        return queryset.filter(
            Q(single_binding__isnull=False, **{f"single_binding__{name}__in": value})
            | Q(composite_binding__isnull=False, **{f"composite_binding__{name}__in": value})
        )

    def filter_single_binding(self, queryset, name, value):
        return queryset.filter(**{f"single_binding__{name}": value})

    def filter_regulator_locus_tag(self, queryset, name, value):
        return self.filter_binding(queryset, "regulator__genomicfeature__locus_tag", value)

    def filter_regulator_symbol(self, queryset, name, value):
        return self.filter_binding(queryset, "regulator__genomicfeature__symbol", value)

    def filter_batch(self, queryset, name, value):
        return self.filter_single_binding(queryset, "batch", value)

    def filter_source(self, queryset, name, value):
        return self.filter_binding(queryset, "source", value)

    def filter_source_name(self, queryset, name, value):
        return self.filter_binding(queryset, "source__name", value)

    def filter_lab(self, queryset, name, value):
        return self.filter_binding(queryset, "source__lab", value)

    def filter_assay(self, queryset, name, value):
        return self.filter_binding(queryset, "source__assay", value)

    def filter_workflow(self, queryset, name, value):
        return self.filter_binding(queryset, "source__workflow", value)

    def filter_data_usable(self, queryset, name, value):
        return self.filter_binding(queryset, "bindingmanualqc__data_usable", value)

    def filter_aggregated(self, queryset, name, value):
        if value:
            return queryset.filter(composite_binding__isnull=False)
        else:
            return queryset.filter(composite_binding__isnull=True)

    def filter_condition(self, queryset, name, value):
        return self.filter_single_binding(queryset, "condition", value)

    def filter_deduplicate(self, queryset, name, value):
        """
        Filter out single_binding records when composite_binding
        exists for the same regulator_id and source_name.
        """
        if value:  # Apply deduplication only if the user has requested it
            # Get the distinct combinations of regulator_id and source_name that have composite_binding
            composite_subquery = queryset.filter(composite_binding__isnull=False).values(
                "composite_binding__regulator", "composite_binding__source"
            )

            # Exclude single_binding records where a composite_binding exists for the same regulator_id/source_name
            queryset = queryset.exclude(
                Q(single_binding__isnull=False)
                & Q(single_binding__regulator__in=composite_subquery.values("composite_binding__regulator"))
                & Q(single_binding__source__in=composite_subquery.values("composite_binding__source"))
            )
        return queryset
