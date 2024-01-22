import logging

from django.db import models

from .BaseModel import BaseModel

logger = logging.getLogger(__name__)


class ExpressionManualQC(BaseModel):
    """
    Record labels from QC reviews of expression data
    """

    expression = models.OneToOneField(
        "Expression",
        on_delete=models.CASCADE,
        help_text="foreign key to the expression table",
    )
    strain_verified = models.CharField(
        max_length=10,
        choices=(("yes", "yes"), ("no", "no"), ("unverified", "unverified")),
        default="unverified",
        help_text="whether the strain is verified",
    )

    def __str__(self):
        return str(self.pk)

    class Meta:
        db_table = "expressionmanualqc"
