import django_filters
from django.db.models import Q

from ...models import Binding, BindingConcatenated, BindingManualQC


class BindingConcatenatedFilter(django_filters.rest_framework.FilterSet):
    id = django_filters.NumberFilter()
    genomic_inserts = django_filters.NumberFilter()
    mito_inserts = django_filters.NumberFilter()
    plasmid_inserts = django_filters.NumberFilter()
    notes = django_filters.CharFilter(lookup_expr="iexact")

    # Filter fields for related bindings
    regulator = django_filters.NumberFilter(field_name="bindings__regulator")
    regulator_locus_tag = django_filters.CharFilter(
        field_name="bindings__regulator__genomicfeature__locus_tag", lookup_expr="iexact"
    )
    regulator_symbol = django_filters.CharFilter(
        field_name="bindings__regulator__genomicfeature__symbol", lookup_expr="iexact"
    )
    batch = django_filters.CharFilter(field_name="bindings__batch", lookup_expr="iexact")
    replicate = django_filters.NumberFilter(field_name="bindings__replicate")
    source = django_filters.NumberFilter(field_name="bindings__source")
    source_orig_id = django_filters.CharFilter(field_name="bindings__source_orig_id", lookup_expr="iexact")
    strain = django_filters.CharFilter(field_name="bindings__strain", lookup_expr="iexact")
    condition = django_filters.ChoiceFilter(field_name="bindings__condition", choices=Binding.CONDITION_CHOICES)
    lab = django_filters.CharFilter(field_name="bindings__source__lab", lookup_expr="iexact")
    assay = django_filters.CharFilter(field_name="bindings__source__assay", lookup_expr="iexact")
    workflow = django_filters.CharFilter(field_name="bindings__source__workflow", lookup_expr="iexact")
    data_usable = django_filters.ChoiceFilter(
        field_name="bindings__bindingmanualqc__data_usable", choices=BindingManualQC.MANUAL_QC_CHOICES
    )

    class Meta:
        model = BindingConcatenated
        fields = [
            "id",
            "genomic_inserts",
            "mito_inserts",
            "plasmid_inserts",
            "notes",
            "regulator",
            "regulator_locus_tag",
            "regulator_symbol",
            "batch",
            "replicate",
            "source",
            "condition",
            "source_orig_id",
            "strain",
            "lab",
            "assay",
            "workflow",
            "data_usable",
        ]
