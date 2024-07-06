import django_filters

from ...models.GenomicFeature import GenomicFeature


class GenomicFeatureFilter(django_filters.rest_framework.FilterSet):
    id = django_filters.NumberFilter()
    chr = django_filters.CharFilter(
        field_name="chr__ucsc", lookup_expr="exact", label="Chromosome", help_text="Chromosome"
    )
    start = django_filters.RangeFilter(
        field_name="start",
        label="Start coordinate",
        help_text="A range describing the start position(s) of the feature",
    )
    end = django_filters.RangeFilter(
        field_name="end", label="End coordinate", help_text="A range describing the end position(s) of the feature"
    )
    strand = django_filters.CharFilter(lookup_expr="exact", label="Feature strand", help_text="Feature strand")
    type = django_filters.CharFilter(
        lookup_expr="iexact", label="Feature type", help_text="Feature type, eg `gene', `CDS', `tRNA', etc"
    )
    locus_tag = django_filters.CharFilter(
        lookup_expr="iexact", label="Locus tag", help_text="The systematic ID from SGD"
    )
    symbol = django_filters.CharFilter(
        lookup_expr="iexact", label="Feature symbol", help_text="The common name of the feature from SGD"
    )
    source = django_filters.CharFilter(
        lookup_expr="iexact", label="Feature source", help_text="Source of the annotation"
    )
    alias = django_filters.CharFilter(
        lookup_expr="iexact",
        label="Feature alias",
        help_text="If there are aliases for the common name of the feature, they are listed in this field",
    )
    note = django_filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = GenomicFeature
        fields = [
            "id",
            "chr",
            "start",
            "end",
            "strand",
            "type",
            "locus_tag",
            "symbol",
            "source",
            "alias",
            "note",
        ]
