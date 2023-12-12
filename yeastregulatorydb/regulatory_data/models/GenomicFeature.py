from enum import Enum

from django.db import models

from .BaseModel import BaseModel


class Strand(Enum):
    """
    Enum representing the strand of a genomic feature. This is used to
    provide some flexibility in how these values are stored in the database.
    """

    POSITIVE = "+"
    NEGATIVE = "-"
    UNSTRANDED = "*"


class GenomicFeatureManager(models.Manager):  # pylint: disable=too-few-public-methods
    """Custom manager for the GenomicFeature model

    Example usage:

    .. code-block:: python
        # in GenomicFeatureManager
        def max_id(self):
          # get the maximum id of all GenomicFeature records
          max_id = GenomicFeature.objects.max_id()

    """

    def max_id(self):
        return self.aggregate(models.Max("pk"))["pk__max"] or 0


class GenomicFeature(BaseModel):
    """
    A model for storing genomic coordinates and annotations for genomic features.

    Fields:
        - `chr`: ForeignKey to the `ChrMap` model, representing the chromosome
          that the genomic feature is located on.
        - `start`: PositiveIntegerField representing the starting genomic
          coordinate of the genomic feature.
        - `end`: IntegerField representing the ending genomic coordinate of
          the genomic feature.
        - `strand`: CharField with a max length of 1, representing the strand
          of the genomic feature.
        - `type`: CharField with a max length of 30, representing the type of
          the genomic feature.
        - `biotype`: CharField with a max length of 20, representing the
          biotype of the feature.
        - `locus_tag`: CharField with a max length of 20 and a unique
          constraint, representing the locus tag of the feature.
        - `symbol`: CharField with a max length of 20, representing the feature
          symbol (eg GAL4).
        - `source`: CharField with a max length of 50, representing the source
          of the feature information.
        - `alias`: CharField with a max length of 150, representing the alias
          of the feature.
        - `note`: CharField with a max length of 1000, representing any notes
          about the feature.

    Example usage:

    .. code-block:: python

        from callingcards.models import GenomicFeature

        # get all GenomicFeature records
        all_features = GenomicFeature.objects.all()
    """

    objects = GenomicFeatureManager()

    STRAND_CHOICES = ((Strand.POSITIVE.value, "+"), (Strand.NEGATIVE.value, "-"), (Strand.UNSTRANDED.value, "*"))

    chr = models.ForeignKey(
        "ChrMap", models.CASCADE, db_index=True, help_text="foreign key to the `id` field of ChrMap"
    )
    start = models.PositiveIntegerField(db_index=True, help_text="start position of the feature")
    end = models.PositiveIntegerField(db_index=True, help_text="end position of the feature")
    strand = models.CharField(
        max_length=1,
        choices=STRAND_CHOICES,
        default=Strand.UNSTRANDED.value,
        db_index=True,
        help_text="strand of the feature, one of +, -, or *",
    )
    type = models.CharField(
        max_length=30,
        default="unknown",
        help_text="CharField with a max length of 30, representing the type of the genomic feature",
    )
    biotype = models.CharField(
        max_length=20,
        default="unknown",
        help_text="CharField with a max length of 20, representing the biotype of the feature",
    )
    # note: in the save method below, a unique integer is appended to the
    # default value if the this field is left blank on input
    locus_tag = models.CharField(
        unique=True,
        max_length=20,
        default="unknown",
        help_text="CharField with a max length of 20 and a unique constraint, "
        "representing the locus tag of the feature, eg YAL001C",
    )
    # note: in the save method below, a unique integer is appended to the
    # default value if the this field is left blank on input
    symbol = models.CharField(
        max_length=20,
        default="unknown",
        help_text="CharField with a max length of 20, representing the feature symbol (eg GAL4)",
    )
    source = models.CharField(
        max_length=50,
        help_text="CharField with a max length of 50, representing the source of the feature information",
    )
    # note: in the save method below, a unique integer is appended to the
    # default value if the this field is left blank on input
    alias = models.CharField(
        max_length=150,
        default="unknown",
        help_text="CharField with a max length of 150, representing the alias of the feature",
    )
    note = models.CharField(
        max_length=1000,
        default="none",
        help_text="CharField with a max length of 1000, representing any notes about the feature",
    )

    def save(self, *args, **kwargs):
        """
        Overrides the default save method to automatically generate a unique
        integer to append to the `locus_tag`, `symbol`, and `alias` fields if
        they are left blank on input.
        """
        # Get the maximum value of the auto-incremented field in the table
        max_id = GenomicFeature.objects.max_id()
        # Check if the systematic field has the default value
        if self.locus_tag == "unknown":
            self.locus_tag = f"unknown_{max_id + 1}"

        if self.symbol == "unknown":
            self.symbol = f"unknown_{max_id + 1}"

        if self.alias == "unknown":
            self.alias = f"unknown_{max_id + 1}"

        super().save(*args, **kwargs)

    def __str__(self):
        """
        Returns a string representation of the `GenomicFeature` model.
        """
        return f"{self.symbol}({self.locus_tag}; pk: {self.pk}"

    class Meta:
        managed = True
        db_table = "genomicfeature"
        constraints = [
            models.CheckConstraint(
                check=models.Q(start__gt=0),
                name="start_cannot_be_less_than_one",
            ),
        ]
