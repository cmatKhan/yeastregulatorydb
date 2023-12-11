import django_filters

from ...models.GenomicFeature import GenomicFeature


class GenomicFeatureFilter(django_filters.FilterSet):
    chr = django_filters.CharFilter(field_name="chr__ucsc")
    start = django_filters.NumberFilter()
    end = django_filters.NumberFilter()
    strand = django_filters.CharFilter(lookup_expr='exact')
    type = django_filters.CharFilter(lookup_expr="iexact")
    gene_biotype = django_filters.CharFilter(lookup_expr="iexact")
    locus_tag = django_filters.CharFilter(lookup_expr="iexact")
    gene = django_filters.CharFilter(lookup_expr="iexact")
    source = django_filters.CharFilter(lookup_expr="iexact")
    alias = django_filters.CharFilter(lookup_expr="iexact")
    note = django_filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = GenomicFeature
        fields = [
            "chr",
            "start",
            "end",
            "strand",
            "type",
            "gene_biotype",
            "locus_tag",
            "gene",
            "source",
            "alias",
            "note",
        ]
