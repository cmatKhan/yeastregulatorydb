import django_filters

from ...models.Binding import Binding


class BindingFilter(django_filters.FilterSet):
    # pylint: disable=R0801
    id = django_filters.NumberFilter()
    pk = django_filters.NumberFilter()
    regulator = django_filters.NumberFilter()
    regulator_locus_tag = django_filters.CharFilter(
        field_name="regulator__genomicfeature__locus_tag", lookup_expr="iexact"
    )
    regulator_symbol = django_filters.CharFilter(field_name="regulator__genomicfeature__symbol", lookup_expr="iexact")
    batch = django_filters.CharFilter(lookup_expr="iexact")
    # pylint: enable=R0801
    replicate = django_filters.NumberFilter()
    source = django_filters.NumberFilter()
    source_orig_id = django_filters.CharFilter(lookup_expr="iexact")
    strain = django_filters.CharFilter(lookup_expr="iexact")
    condition = django_filters.ChoiceFilter(choices=Binding.CONDITION_CHOICES)
    lab = django_filters.CharFilter(field_name="source__lab", lookup_expr="iexact")
    assay = django_filters.CharFilter(field_name="source__assay", lookup_expr="iexact")
    workflow = django_filters.CharFilter(field_name="source__workflow", lookup_expr="iexact")

    # pylint: disable=R0801
    class Meta:
        model = Binding
        fields = [
            "id",
            "pk",
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
        ]

    # pylint: enable=R0801
