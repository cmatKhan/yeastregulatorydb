import logging

from django.db import models
from django.db.models import UniqueConstraint

from .BaseModel import BaseModel

logger = logging.getLogger(__name__)


class DTO(BaseModel):
    """
    Store DTO data
    """

    promotersetsig = models.ForeignKey(
        "PromoterSetSig",
        on_delete=models.CASCADE,
        related_name="dto_pss",
        help_text="Foreign key field to the 'PromoterSetSig' table",
    )

    expression = models.ForeignKey(
        "Expression",
        on_delete=models.CASCADE,
        related_name="dto_expression",
        help_text="Foreign keys field to the 'Expression' table",
    )

    passing_fdr = models.BooleanField(
        help_text=("A boolean field which is `True` when FDR >= 0.2. See the DTO paper/software for more details"),
        default=True,
    )

    passing_pvalue = models.BooleanField(
        help_text=("A boolean field which is `True` when the empirical p-value <= 0.1"),
        default=True,
    )

    parameters = models.JSONField(help_text="A json field to store the parameters used to generate the DTO result")

    result = models.JSONField(help_text=("A json field to store the result of DTO"))

    def __str__(self):
        return f"pk:{self.pk}"

    class Meta:
        db_table = "dto"
        constraints = [
            UniqueConstraint(fields=["promotersetsig", "expression"], name="unique_promotersetsig_expression")
        ]

    def get_regulator(self):
        """return the regulator associated with this promotersetsig instance"""
        return self.promotersetsig.get_regulator()

    def get_genomicfeature(self):
        """return the genomicfeature associated with this promotersetsig instance"""
        return self.get_regulator().genomicfeature

    def get_binding_source_name(self):
        """return the source associated with this promotersetsig instance"""
        # TODO: fix the naming -- promotersetsig.get_source_name() returns the source,
        # not the name
        return self.promotersetsig.get_source_name().name

    def get_expression_source_name(self):
        """return the source associated with this promotersetsig instance"""
        return self.expression.get_source_name()
