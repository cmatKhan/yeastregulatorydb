import django_filters
from django.db.models import Q

from ...models import BindingManualQC, PromoterSetSig


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
            "lab",
            "assay",
            "workflow",
            "data_usable",
            "aggregated",
        ]

    def filter_binding(self, queryset, name, value):
        return queryset.filter(
            Q(single_binding__isnull=False, **{f"single_binding__{name}": value})
            | Q(composite_binding__isnull=False, **{f"composite_binding__{name}": value})
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
