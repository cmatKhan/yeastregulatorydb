import logging

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .BaseModel import BaseModel

logger = logging.getLogger(__name__)


class FileFormat(BaseModel):
    """
    Store the filetype name and a comma separated string of field names
    """

    fileformat = models.CharField(
        max_length=20,
        blank=False,
        null=False,
        unique=True,
        help_text="A filetype name. This should be short, eg 'bed' or 'qbed' or 'tsv'",
    )
    fields = models.CharField(
        max_length=200,
        blank=False,
        null=False,
        help_text='A comma separated list of field names. Eg "chromosome, start, end, strand, name, score"',
    )

    def __str__(self):
        return f"{self.fileformat}"

    class Meta:
        db_table = "fileformat"


@receiver(pre_save, sender=FileFormat)
def sanitize_entries(sender, instance, **kwargs):  # pylint: disable=unused-argument
    instance.fields = instance.fields.replace(" ", "").strip()  # remove spaces
