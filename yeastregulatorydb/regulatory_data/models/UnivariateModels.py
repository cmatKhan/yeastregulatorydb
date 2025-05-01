import logging

from django.db import models
from django.db.models import UniqueConstraint

from .BaseModel import BaseModel

logger = logging.getLogger(__name__)


class UnivariateModels(BaseModel):
    """
    Store UnivariateModels data
    """

    promotersetsig = models.ForeignKey(
        "PromoterSetSig",
        on_delete=models.CASCADE,
        related_name="um_promotersetsig",
        help_text="Foreign key to the 'PromoterSetSig' table",
    )

    expression = models.ForeignKey(
        "Expression",
        on_delete=models.CASCADE,
        related_name="um_expression",
        help_text="Foreign key to the 'Expression' table",
    )

    rsquared = models.FloatField(help_text="The R-squared value of the univariate model", default=0.0)

    pvalue = models.FloatField(help_text="The p-value of the univariate model", default=0.0)

    coefficients = models.JSONField(help_text="The coefficients of the univariate model")

    def __str__(self):
        return f"pk:{self.pk}"

    class Meta:
        db_table = "univariatemodels"
        constraints = [
            UniqueConstraint(
                fields=["promotersetsig", "expression"], name="unique_promotersetsig_expression_univariatemodels"
            )
        ]
        indexes = [models.Index(fields=["expression", "promotersetsig"], name="idx_expr_pss_univariatemodels")]

    # pylint:enable=R0801

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
