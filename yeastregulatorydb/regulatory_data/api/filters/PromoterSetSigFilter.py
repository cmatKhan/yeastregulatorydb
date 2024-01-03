import django_filters

from ...models.PromoterSetSig import PromoterSetSig


class PromoterSetSigFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter()
    pk = django_filters.NumberFilter()
    binding = django_filters.NumberFilter()
    promoter = django_filters.NumberFilter()
    promoter_name = django_filters.CharFilter(field_name="promoter__name", lookup_expr="iexact")
    background = django_filters.NumberFilter()
    background_name = django_filters.CharFilter(field_name="background_id__name", lookup_expr="iexact")
    regulator_locus_tag = django_filters.CharFilter(
        field_name="binding__regulator__genomicfeature__locus_tag", lookup_expr="iexact"
    )
    regulator_symbol = django_filters.CharFilter(
        field_name="binding__regulator__genomicfeature__symbol", lookup_expr="iexact"
    )
    batch = django_filters.CharFilter(field_name="binding__batch", lookup_expr="iexact")
    replicate = django_filters.NumberFilter(field_name="binding__replicate")
    source = django_filters.NumberFilter(field_name="binding__source")
    lab = django_filters.CharFilter(field_name="binding__source__lab", lookup_expr="iexact")
    assay = django_filters.CharFilter(field_name="binding__source__assay", lookup_expr="iexact")
    workflow = django_filters.CharFilter(field_name="binding__source__workflow", lookup_expr="iexact")

    # pylint: disable=R0801
    class Meta:
        model = PromoterSetSig
        fields = [
            "id",
            "pk",
            "binding",
            "promoter_id",
            "background_id",
            "regulator_locus_tag",
            "regulator_symbol",
            "batch",
            "replicate",
            "source",
            "lab",
            "assay",
            "workflow",
        ]

        # pylint: enable=R0801
