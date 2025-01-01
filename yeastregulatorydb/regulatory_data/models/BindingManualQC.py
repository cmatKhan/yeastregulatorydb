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
    data_usable = models.CharField(
        default="unreviewed",
        choices=MANUAL_QC_CHOICES,
        help_text="`pass` if there is no reason to believe the data has "
        "technical faults. Otherwise, `unreviewed` or `false`",
    )
    manual_fail = models.BooleanField(
        default=False,
        help_text=(
            "This provides a way of overriding the automated QC "
            "If it is set to `True`, a reason should be provided in the `notes` field"
        ),
    )
    preferred_replicate = models.BooleanField(
        default=False,
        help_text=(
            "If `True`, this is the preferred replicate for a "
            "replicate binding set. This is intended to be used for "
            "data sources without aggregated replicates"
        ),
    )
    notes = models.CharField(
        max_length=300, default="none", help_text="Free entry field for notes from the manual QC review"
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
