import logging

from django.db import models

from .BaseModel import BaseModel

logger = logging.getLogger(__name__)


class BindingManualQC(BaseModel):
    """
    Store labels from QC reviews of binding data
    """

    binding = models.OneToOneField("Binding", on_delete=models.CASCADE, help_text="Foreign key to the Binding table")
    best_datatype = models.BooleanField(
        default=True,
        help_text="True if the only binding data that performs better is from "
        "the same binding source. Otherwise, False",
    )
    data_usable = models.BooleanField(
        default=True,
        help_text="`True` if there is no reason to believe the data has "
        "technical faults. Otherwise, `False`, which recommends against "
        "using the data in analysis",
    )
    passing_replicate = models.BooleanField(
        default=True,
        help_text="Primarily, and probably only, relevant to Calling Cards data. "
        "`True` if the replicate's hops should be counted towards the "
        "target hop count. `False` otherwise",
    )
    notes = models.CharField(
        max_length=100, default="unreviewed", help_text="Free entry field for notes from the manual QC review"
    )

    def __str__(self):
        return f"binding: {self.binding}"

    class Meta:
        db_table = "bindingmanualqc"
