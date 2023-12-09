"""
.. module:: ExpressionManualQC
   :synopsis: A model for storing labels and notes from manual QC reviews of
   the data

   This model is used to keep track of decisions and labels relating to the
   Expression data QC. Since we have very little access to the raw data,
   this (will eventually) focus on the comparison between the expression set
   and the binding data.

.. moduleauthor:: Chase Mateusiak
.. date:: 2023-04-21
.. modified::2023-12-07
"""
import logging

from django.db import models
from django.dispatch import receiver

from .BaseModel import BaseModel

logger = logging.getLogger(__name__)


class ExpressionManualQC(BaseModel):
    """
    Record labels from QC reviews of expression data
    """

    expression_id = models.ForeignKey(
        "Expression", on_delete=models.CASCADE, help_text="foreign key to the expression table"
    )
    strain_verified = models.CharField(
        max_length=10,
        choices=(("yes", "yes"), ("no", "no"), ("unverified", "unverified")),
        default="unverified",
    )

    def __str__(self):
        return f"expression_id:{self.expression_id}"

    class Meta:
        db_table = "expressionmanualqc"
