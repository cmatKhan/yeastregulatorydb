import django_filters

from ...models import ExpressionManualQC


class ExpressionManualQCFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter()
    pk = django_filters.NumberFilter()
    expression = django_filters.NumberFilter()
    strain_verified = django_filters.ChoiceFilter(choices=[("yes", "yes"), ("no", "no"), ("unverified", "unverified")])
    regulator_locus_tag = django_filters.CharFilter(
        field_name="expression__regulator__regulator__locus_tag", lookup_expr="iexact"
    )
    regulator_symbol = django_filters.CharFilter(
        field_name="expression__regulator__regulator__symbol", lookup_expr="iexact"
    )
    batch = django_filters.CharFilter(field_name="expression__batch", lookup_expr="iexact")
    replicate = django_filters.NumberFilter(field_name="expression__replicate")
    control = django_filters.CharFilter(field_name="expression__control", lookup_expr="iexact")
    mechanism = django_filters.CharFilter(field_name="expression__mechanism", lookup_expr="iexact")
    restriction = django_filters.CharFilter(field_name="expression__restriction", lookup_expr="iexact")
    time = django_filters.NumberFilter(field_name="expression__time")
    source = django_filters.NumberFilter(field_name="expression__source__id")
    lab = django_filters.CharFilter(field_name="expression__source__lab", lookup_expr="iexact")
    assay = django_filters.CharFilter(field_name="expression__source__assay", lookup_expr="iexact")
    workflow = django_filters.CharFilter(field_name="expression__source__workflow", lookup_expr="iexact")

    # pylint: disable=R0801
    class Meta:
        model = ExpressionManualQC
        fields = [
            "id",
            "pk",
            "expression",
            "strain_verified",
            "regulator_locus_tag",
            "regulator_symbol",
            "batch",
            "replicate",
            "control",
            "mechanism",
            "restriction",
            "time",
            "source",
            "lab",
            "assay",
            "workflow",
        ]

    # pylint: enable=R0801
