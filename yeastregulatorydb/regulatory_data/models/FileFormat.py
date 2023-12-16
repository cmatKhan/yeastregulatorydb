import logging

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .BaseModel import BaseModel

logger = logging.getLogger(__name__)


class FileFormat(BaseModel):
    """
    Store the file format name and a comma separated string of field names
    """

    fileformat = models.CharField(
        max_length=20,
        blank=False,
        null=False,
        unique=True,
        db_index=True,
        help_text="A file format name. This should be short, eg 'bed' or 'qbed' or 'tsv'",
    )
    fields = models.JSONField(
        blank=False,
        null=False,
        help_text="A JSON key:value set of columns and expected "
        "datatypes. Eg "
        '{"chr": "str",'
        '"start": "int",'
        '"end": "int",'
        '"name": "str",'
        '"score": "float",'
        '"strand": ["+", "-", "*"]}',
    )
    separator = models.CharField(
        max_length=2,
        choices=[
            ("\t", "tab"),
            (",", "comma"),
        ],
        default="\t",
        help_text="The separator used in the file. Defaults to tab.",
    )
    effect_col = models.CharField(
        max_length=40,
        default="none",
        help_text="The name of the column that should be used as the default "
        "effect column. Eg 'score'. Defaults to 'none' if there is no effect column.",
    )
    pval_col = models.CharField(
        max_length=40,
        default="none",
        help_text="The name of the column that should be used as the default "
        "p-value column. Eg 'pvalue'. Defaults to 'none' if there is no p-value column.",
    )

    def __str__(self):
        return f"{self.fileformat}"

    class Meta:
        db_table = "fileformat"
