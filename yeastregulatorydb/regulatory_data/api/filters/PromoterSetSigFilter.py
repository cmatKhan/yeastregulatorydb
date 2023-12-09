import django_filters

from ...models.PromoterSetSig import PromoterSetSig


class PromoterSetSigFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter()
    pk = django_filters.NumberFilter()
    binding_id = django_filters.NumberFilter()
    promoter_id = django_filters.NumberFilter()
    promoter_name = django_filters.CharFilter(field_name="promoter_id__name", lookup_expr="iexact")
    background_id = django_filters.NumberFilter(field_name="background_id")
    background_name = django_filters.CharFilter(field_name="background_id__name", lookup_expr="iexact")
    regulator_locus_tag = django_filters.CharFilter(
        field_name="binding_id__regulator__locus_tag", lookup_expr="iexact"
    )
    regulator_symbol = django_filters.CharFilter(field_name="binding_id__regulator__symbol", lookup_expr="iexact")
    batch = django_filters.CharFilter(field_name="binding_id__batch", lookup_expr="iexact")
    replicate = django_filters.NumberFilter(field_name="binding_id__replicate")
    source_id = django_filters.NumberFilter(field_name="binding_id__source_id")
    lab = django_filters.CharFilter(field_name="binding_id__source_id__lab", lookup_expr="iexact")
    assay = django_filters.CharFilter(field_name="binding_id__source_id__assay", lookup_expr="iexact")
    workflow = django_filters.CharFilter(field_name="binding_id__source_id__workflow", lookup_expr="iexact")

    class Meta:
        model = PromoterSetSig
        fields = [
            "id",
            "pk",
            "binding_id",
            "promoter_id",
            "background_id",
            "regulator_locus_tag",
            "regulator_symbol",
            "batch",
            "replicate",
            "source_id",
            "lab",
            "assay",
            "workflow",
        ]
