import django_filters
from django.db.models import Q

from ...models.RankResponse import RankResponse
from .utils.CharInFilter import CharInFilter


class RankResponseFilter(django_filters.rest_framework.FilterSet):
    id = CharInFilter(field_name="id", lookup_expr="in")
    promotersetsig = django_filters.NumberFilter(
        label="Promoter Set Signature ID",
        help_text="ID of the promoter set signature",
    )
    expression = django_filters.NumberFilter(label="Expression ID", help_text="ID of the expression")
    regulator_id = django_filters.NumberFilter(
        field_name="expression__regulator",
        label="Regulator ID",
        help_text="ID of the regulator",
    )
    regulator_locus_tag = django_filters.CharFilter(
        field_name="expression__regulator__genomicfeature__locus_tag",
        method="filter_regulator_locus_tag",
        label="Regulator Locus Tag",
        help_text="Regulator Locus Tag",
    )
    regulator_symbol = django_filters.CharFilter(
        field_name="expression__regulator__genomicfeature__symbol",
        method="filter_regulator_symbol",
        label="Regulator Symbol",
        help_text="Regulator Symbol",
    )
    expression_conditions = django_filters.CharFilter(
        method="filter_expression_conditions",
        label="Expression Conditions",
        help_text=(
            "This provides a method of filtering expression data based on additional "
            "expression fields. Currently `expression_source` and any field in Expression "
            "can be used. Those additional expression fields need to be separated by a comma. "
            "and identified by their field name (no expression_ prefix). This includes `preferred_replicate` "
            "Format: `expression_source=some_source;expression_source=another_source,time=15`. "
            "(e.g., `expression_source=kemmeren_tfko;expression_source=mcisaac_oe,time=15`)."
        ),
    )

    class Meta:
        model = RankResponse
        fields = ["id", "promotersetsig", "expression", "regulator_id", "regulator_locus_tag", "regulator_symbol"]

    def filter_regulator_symbol(self, queryset, name, value):
        # Split the value by commas
        tags = value.split(",")
        # Apply an `in` filter to match any of the tags
        return queryset.filter(**{f"expression__regulator__genomicfeature__symbol__in": tags})

    def filter_regulator_locus_tag(self, queryset, name, value):
        # Split the value by commas
        tags = value.split(",")
        # Apply an `in` filter to match any of the tags
        return queryset.filter(**{f"expression__regulator__genomicfeature__locus_tag__in": tags})

    def filter_expression_conditions(self, queryset, name, value):
        """
        Custom filter to handle complex expression conditions.
        Format: `expression_source=value[,time=value];expression_source=value`.
        Example: `expression_source=datasource1;expression_source=datasource2,time=15`.

        NOTE: expression_source and expressionmanualqc__preferred_replicate are special cases.
        """
        conditions = value.split(";")
        q_objects = Q()

        for condition in conditions:
            sub_conditions = condition.split(",")
            sub_q = Q()

            for sub_condition in sub_conditions:
                key, val = sub_condition.split("=")
                key = key.strip()
                val = val.strip()

                # Map `expression_source` to `expression__source__name`
                if key == "expression_source":
                    field_name = "expression__source__name"
                elif key == "preferred_replicate":
                    field_name = "expression__expressionmanualqc__preferred_replicate"
                    if not val.lower() in ["true", "false", "1", "0"]:
                        raise ValueError(
                            "preferred_replicate must be either `true`, `false`, `1` or `0`. Case doesn't matter."
                        )
                    else:
                        val = val.lower() in ["true", "1"]
                else:
                    field_name = f"expression__{key}"

                sub_q &= Q(**{field_name: val})

            # Combine each sub-condition group with OR
            q_objects |= sub_q

        return queryset.filter(q_objects)
