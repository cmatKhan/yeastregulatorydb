import logging

from django.db import models

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
    feature_identifier_col = models.CharField(
        max_length=40,
        default="none",
        help_text="The name of the column that should be used as the default "
        "feature identifier column. Eg 'name'. Defaults to 'none'.",
    )
    effect_col = models.CharField(
        max_length=40,
        default="none",
        help_text="The name of the column that should be used as the default "
        "effect column. Eg 'score'. Defaults to 'none' if there is no effect column.",
    )
    default_effect_threshold = models.FloatField(
        default=0.0,
        help_text="The default threshold for the effect column. Defaults to 0.0.",
    )
    pval_col = models.CharField(
        max_length=40,
        default="none",
        help_text="The name of the column that should be used as the default "
        "p-value column. Eg 'pvalue'. Defaults to 'none' if there is no p-value column.",
    )
    default_pvalue_threshold = models.FloatField(
        default=1.0,
        help_text="The default threshold for the p-value column. Defaults to 1.0.",
    )

    def __str__(self):
        return f"{self.fileformat}"

    class Meta:
        db_table = "fileformat"
