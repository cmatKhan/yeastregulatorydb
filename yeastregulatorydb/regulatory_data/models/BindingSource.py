import logging
import re

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .BaseModel import BaseModel

logger = logging.getLogger(__name__)


class BindingSource(BaseModel):
    """
    Store binding data source information
    """

    fileformat_id = models.ForeignKey(
        "FileFormat",
        on_delete=models.CASCADE,
        help_text="Foreign key to the FileFormat table",
    )
    lab = models.CharField(
        max_length=20, blank=False, null=False, help_text="The name of the lab which generated the data"
    )
    assay = models.CharField(
        max_length=20, blank=False, null=False, help_text="name of the assay used to generate the data"
    )
    workflow = models.CharField(
        max_length=50, default="undefined", help_text="The workflow used to generate the data, including version"
    )
    description = models.CharField(
        max_length=100,
        default="none",
        help_text="A description of the data. include a URL to github "
        "repo with scripts describing how the data was parsed",
    )
    citation = models.CharField(max_length=200, default="ask_admin", help_text="citation for the data")
    notes = models.CharField(
        max_length=100, default="none", help_text="Any additional notes about the source of the binding data"
    )

    def __str__(self):
        return f"{self.lab}_{self.workflow}"

    class Meta:
        db_table = "bindingsource"
        unique_together = (
            "lab",
            "assay",
            "workflow",
        )


@receiver(pre_save, sender=BindingSource)
def sanitize_entries(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Sanitize the lab, type and workflow fields before saving to the database
    """
    # sanitize lab
    sanitized_lab = re.sub(r"[^a-zA-Z0-9_]", "_", instance.lab.strip()).lower()
    logger.debug("Original Binding Source lab: %s; Sanitized to: %s", instance.lab, sanitized_lab)
    instance.lab = sanitized_lab
    # sanitize type
    sanitized_assay = re.sub(r"[^a-zA-Z0-9_]", "_", instance.assay.strip()).lower()
    logger.debug("Original Binding Source type: %s; Sanitized to: %s", instance.assay, sanitized_assay)
    instance.assay = sanitized_assay
    # sanitize workflow
    sanitized_workflow = re.sub(r"[^a-zA-Z0-9_]", "_", instance.workflow.strip()).lower()
    logger.debug("Original Binding Source workflow: %s; Sanitized to: %s", instance.workflow, sanitized_workflow)
    instance.workflow = sanitized_workflow
