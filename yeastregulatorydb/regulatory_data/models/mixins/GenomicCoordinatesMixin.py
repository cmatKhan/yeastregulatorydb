"""Mixins which may be useful for storing genomic data

.. author:: Chase Mateusiak
.. date:: 2023-04-20
.. modified:: 2023-12-07
"""
from enum import Enum

from django.db import models


class Strand(Enum):
    """
    Enum representing the strand of a genomic feature. This is used to
    provide some flexibility in how these values are stored in the database.
    """

    POSITIVE = "+"
    NEGATIVE = "-"
    UNSTRANDED = "*"


class GenonomicCoordinatesMixin(models.Model):
    """
    A mixin for models that have genomic coordinates (i.e. a chromosome, start,
    end, and strand).

    Fields:
        - chr: ForeignKey to the `ChrMap` model, representing the chromosome
          that the feature is located on.
        - start: PositiveIntegerField representing the start position of the
          feature.
        - end: PositiveIntegerField representing the end position of the
          feature.
        - strand: CharField with a max length of 1, representing the strand of
          the feature. Valid choices are defined in the `Strand` enum.

    Constraints:
        - start_cannot_be_less_than_one: start position must be greater than 0.
        - end_cannot_exceed_chromosome_length: end position must be less than
          or equal to the length of the chromosome.
    """

    STRAND_CHOICES = ((Strand.POSITIVE.value, "+"), (Strand.NEGATIVE.value, "-"), (Strand.UNSTRANDED.value, "*"))

    chr = models.ForeignKey("ChrMap", models.PROTECT, db_index=True, help_text="foreign key to the `id` field of ChrMap")  # type: ignore[misc]
    start = models.PositiveIntegerField(db_index=True, help_text="start position of the feature")
    end = models.PositiveIntegerField(db_index=True, help_text="end position of the feature")
    strand = models.CharField(
        max_length=1,
        choices=STRAND_CHOICES,
        default=Strand.UNSTRANDED.value,
        db_index=True,
        help_text="strand of the feature, one of +, -, or *",
    )

    class Meta:
        abstract = True
        constraints = [
            models.CheckConstraint(
                check=models.Q(start__gt=0),
                name="start_cannot_be_less_than_one",
            ),
            models.CheckConstraint(
                check=models.Q(end__lte=models.F("chr__seqlength")),
                name="end_cannot_exceed_chromosome_length",
            ),
        ]
