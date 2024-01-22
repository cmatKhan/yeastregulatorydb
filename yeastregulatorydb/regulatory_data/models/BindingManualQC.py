import logging

from django.db import models

from .BaseModel import BaseModel

logger = logging.getLogger(__name__)


class BindingManualQC(BaseModel):
    """
    Store labels from QC reviews of binding data
    """

    MANUAL_QC_CHOICES = [("unreviewed", "unreviewed"), ("pass", "pass"), ("fail", "fail"), ("note", "note")]

    binding = models.OneToOneField("Binding", on_delete=models.CASCADE, help_text="Foreign key to the Binding table")
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
