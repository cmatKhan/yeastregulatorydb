import django_filters

from ...models import Binding, BindingManualQC
from .utils.NumbersInFilter import NumbersInFilter


class BindingFilter(django_filters.rest_framework.FilterSet):
    # pylint: disable=R0801
    id = NumbersInFilter(field_name="id", lookup_expr="in")
    regulator = django_filters.NumberFilter(label="Regulator ID", help_text="Regulator ID")
    regulator_locus_tag = django_filters.CharFilter(
        field_name="regulator__genomicfeature__locus_tag",
        lookup_expr="iexact",
        label="Regulator Locus Tag",
        help_text="Regulator Locus Tag",
    )
    regulator_symbol = django_filters.CharFilter(
        field_name="regulator__genomicfeature__symbol",
        lookup_expr="iexact",
        label="Regulator Symbol",
        help_text="Regulator Symbol",
    )
    batch = django_filters.CharFilter(
        lookup_expr="iexact", label="Batch", help_text="Batch identifier, eg run_1234 for brentlab calling cards"
    )
    # pylint: enable=R0801
    replicate = django_filters.NumberFilter(label="Replicate", help_text="Within batch replicate number")
    source = django_filters.NumberFilter(label="Data Source ID", help_text="Data Source ID")
    source_name = django_filters.CharFilter(
        field_name="source__name", lookup_expr="iexact", label="Data Source name", help_text="Data Source name"
    )
    source_orig_id = django_filters.CharFilter(
        lookup_expr="iexact",
        label="Data Source Original ID",
        help_text="If the original data source of the data had a unique ID, it is stored in this field",
    )
    strain = django_filters.CharFilter(lookup_expr="iexact", label="Strain", help_text="Strain")
    condition = django_filters.ChoiceFilter(
        choices=Binding.CONDITION_CHOICES, label="Condition", help_text="Experimental conditions of the sample"
    )
    lab = django_filters.CharFilter(
        field_name="source__lab", lookup_expr="iexact", label="Lab", help_text="Lab which generated the data"
    )
    assay = django_filters.CharFilter(
        field_name="source__assay", lookup_expr="iexact", label="Assay", help_text="Assay which generated the data"
    )
    workflow = django_filters.CharFilter(
        field_name="source__workflow",
        lookup_expr="iexact",
        label="Workflow",
        help_text="Workflow which generated the data",
    )
    data_usable = django_filters.ChoiceFilter(
        field_name="bindingmanualqc__data_usable",
        choices=BindingManualQC.MANUAL_QC_CHOICES,
        label="Data Usable",
        help_text="QC label determining whether the data is recommended for use for analysis",
    )

    # pylint: disable=R0801
    class Meta:
        model = Binding
        fields = [
            "id",
            "regulator",
            "regulator_locus_tag",
            "regulator_symbol",
            "batch",
            "replicate",
            "source",
            "source_name",
            "condition",
            "source_orig_id",
            "strain",
            "lab",
            "assay",
            "workflow",
            "data_usable",
        ]

    # pylint: enable=R0801
