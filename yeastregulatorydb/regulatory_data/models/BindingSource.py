"""
.. module:: BindingSource
   :synopsis: A model for storing the various origins of binding data

This model is used to store information about the source of binding data,
including how it is processed and how it was parsed into the stored format.

.. author:: Chase Mateusiak
.. date:: 2023-04-17
.. modified:: 2023-12-07
"""
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
        help_text="A description of the data. include a URL to github repo with scripts describing how the data was parsed",
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
def sanitize_entries(sender, instance, **kwargs):
    """
    Sanitize the lab, type and workflow fields before saving to the database
    """
    # sanitize lab
    sanitized_lab = re.sub(r"[^a-zA-Z0-9_]", "_", instance.name.strip()).lower()
    logger.debug(f"Original Binding Source lab: %s; Sanitized to: %s", instance.lab, sanitized_lab)
    instance.lab = sanitized_lab
    # sanitize type
    sanitized_type = re.sub(r"[^a-zA-Z0-9_]", "_", instance.type.strip()).lower()
    logger.debug(f"Original Binding Source type: %s; Sanitized to: %s", instance.type, sanitized_type)
    instance.type = sanitized_type
    # sanitize workflow
    sanitized_workflow = re.sub(r"[^a-zA-Z0-9_]", "_", instance.workflow.strip()).lower()
    logger.debug(f"Original Binding Source workflow: %s; Sanitized to: %s", instance.workflow, sanitized_workflow)
    instance.workflow = sanitized_workflow
