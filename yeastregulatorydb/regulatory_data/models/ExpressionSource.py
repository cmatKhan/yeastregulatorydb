import logging
import re

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .BaseModel import BaseModel

logger = logging.getLogger(__name__)


class ExpressionSource(BaseModel):
    """
    Store expression data source information
    """

    fileformat_id = models.ForeignKey(
        "FileFormat", on_delete=models.CASCADE, help_text="foreign key to the fileformat table"
    )
    lab = models.CharField(
        max_length=20,
        blank=False,
        null=False,
        help_text="name of the lab that generated the data. Single word preferred. No spaces -- use `_` instead",
    )
    assay = models.CharField(
        max_length=20,
        blank=False,
        null=False,
        help_text="name of the assay used to generate the data. Single word preferred. No spaces -- use `_` instead",
    )
    workflow = models.CharField(
        max_length=50,
        default="undefined",
        help_text="If known, note how the data was processed. Single word preferred. No spaces -- use `_` instead",
    )
    citation = models.CharField(max_length=200, default="ask_admin", help_text="citation for the data")
    description = models.CharField(max_length=200, default="none", help_text="brief description of the data")
    notes = models.CharField(max_length=100, default="none", help_text="any additional notes about the data")

    def __str__(self):
        return f"{self.lab}_{self.workflow}"

    class Meta:
        db_table = "expressionsource"


@receiver(pre_save, sender=ExpressionSource)
def sanitize_entries(sender, instance, **kwargs):  # pylint: disable=unused-argument
    # sanitize lab
    sanitized_lab = re.sub(r"[^a-zA-Z0-9_]", "_", instance.lab.strip()).lower()
    logger.debug("Original Expression Source lab: %s; Sanitized to: %s", instance.lab, sanitized_lab)
    instance.lab = sanitized_lab
    # sanitize type
    sanitized_lab = re.sub(r"[^a-zA-Z0-9_]", "_", instance.lab.strip()).lower()
    logger.debug("Original Expression Source type: %s; Sanitized to: %s", instance.lab, sanitized_lab)
    instance.lab = sanitized_lab
    # sanitize workflow
    sanitized_workflow = re.sub(r"[^a-zA-Z0-9_]", "_", instance.workflow.strip()).lower()
    logger.debug("Original Expression Source workflow: %s; Sanitized to: %s", instance.workflow, sanitized_workflow)
    instance.workflow = sanitized_workflow
