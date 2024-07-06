import logging

from django.db import models

from .BaseModel import BaseModel

logger = logging.getLogger(__name__)


class BindingManualQC(BaseModel):
    """
    Store labels from QC reviews of binding data
    """

    MANUAL_QC_CHOICES = [("unreviewed", "unreviewed"), ("pass", "pass"), ("fail", "fail"), ("note", "note")]

    single_binding = models.ForeignKey(
        "Binding",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Foreign key to the 'Binding' table",
    )
    composite_binding = models.ForeignKey(
        "BindingConcatenated",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Foreign key to the 'BindingConcatenated' table",
    )
    best_datatype = models.CharField(
        default="unreviewed",
        choices=MANUAL_QC_CHOICES,
        help_text="`pass` if the only binding data that performs better is from "
        "the same binding source. Otherwise, `unreviewed` or `fail`",
    )
    data_usable = models.CharField(
        default="unreviewed",
        choices=MANUAL_QC_CHOICES,
        help_text="`pass` if there is no reason to believe the data has "
        "technical faults. Otherwise, `unreviewed` or `false`",
    )
    passing_replicate = models.CharField(
        default="unreviewed",
        choices=MANUAL_QC_CHOICES,
        help_text="Primarily, and probably only, relevant to Calling Cards data. "
        "`pass` if the replicate's hops should be counted towards the "
        "target hop count. `unreviewed` or `false` otherwise",
    )
    rank_recall = models.CharField(
        default="unreviewed",
        choices=MANUAL_QC_CHOICES,
        help_text="`pass` if at least 1 rank response bin in the first 100 "
        "genes ranked by pvalue is significant. Else `unreviewed` or `fail`",
    )
    notes = models.CharField(
        max_length=100, default="none", help_text="Free entry field for notes from the manual QC review"
    )

    def __str__(self):
        return str(self.pk)

    class Meta:
        db_table = "bindingmanualqc"
        constraints = [
            models.CheckConstraint(
                check=(models.Q(single_binding__isnull=False) | models.Q(composite_binding__isnull=False)),
                name="single_or_composite_binding_not_null_bindingmanualqc",
            ),
            # null values are not considered equal in postgres, SQLite, or MySQL.
            # From the postgres 16 docs:
            # "By default, two null values are not considered equal in this comparison"
            # https://www.postgresql.org/docs/16/ddl-constraints.html#DDL-CONSTRAINTS-UNIQUE-CONSTRAINTS
            models.UniqueConstraint(fields=["single_binding"], name="unique_single_binding_bindingmanualqc"),
            models.UniqueConstraint(fields=["composite_binding"], name="unique_composite_binding_bindingmanualqc"),
        ]
