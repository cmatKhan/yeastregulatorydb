import django_filters

from ...models import ExpressionManualQC


class ExpressionManualQCFilter(django_filters.rest_framework.FilterSet):
    id = django_filters.NumberFilter()
    expression = django_filters.NumberFilter(label="Expression ID", help_text="ID of the expression")
    strain_verified = django_filters.ChoiceFilter(
        choices=[("yes", "yes"), ("no", "no"), ("unverified", "unverified")],
        label="Strain Verified",
        help_text="Strain verified status",
    )
    regulator_locus_tag = django_filters.CharFilter(
        field_name="expression__regulator__genomicfeature__locus_tag",
        lookup_expr="iexact",
        label="Regulator locus tag",
        help_text="Regulator locus tag",
    )
    regulator_symbol = django_filters.CharFilter(
        field_name="expression__regulator__genomicfeature__symbol",
        lookup_expr="iexact",
        label="Regulator symbol",
        help_text="Regulator symbol",
    )
    time = django_filters.NumberFilter(field_name="expression__time", label="Time", help_text="Time (McIsaac only)")
    source = django_filters.NumberFilter(field_name="expression__source__id", label="Source ID", help_text="Source ID")
    lab = django_filters.CharFilter(
        field_name="expression__source__lab",
        lookup_expr="iexact",
        label="Lab Name",
        help_text="Lab which generated the data",
    )
    assay = django_filters.CharFilter(
        field_name="expression__source__assay",
        lookup_expr="iexact",
        label="Assay Name",
        help_text="Assay used to generate the data, eg 'callingcards'",
    )
    workflow = django_filters.CharFilter(
        field_name="expression__source__workflow",
        lookup_expr="iexact",
        label="Workflow Name",
        help_text="Workflow used to generate data",
    )

    # pylint: disable=R0801
    class Meta:
        model = ExpressionManualQC
        fields = [
            "id",
            "expression",
            "strain_verified",
            "regulator_locus_tag",
            "regulator_symbol",
            "time",
            "source",
            "lab",
            "assay",
            "workflow",
        ]

    # pylint: enable=R0801
