"""
.. module:: chrmap
   :synopsis: Module for the `ChrMap` model that stores chromosome mapping
              information for different genome assemblies.

This module defines the `ChrMap` model used to store the chromosome mapping
information for different genome sources, eg between igenomes, ucsc and
refseq. This table classifies chromosomes as genomic or mitochondrial,
and adds and identifies as such some plasmid sequences which are added to
callingcards strains. It additionally has the seqlength of each contig.

.. moduleauthor:: Chase Mateusiak
.. date:: 2023-04-21
.. modified::2023-12-07
"""
from django.db import models

from .BaseModel import BaseModel


class ChrMap(BaseModel):
    """
    A model for storing chromosome mapping information for different genome
    assemblies.

    Fields:
        - `refseq`: CharField with a max length of 12, representing the RefSeq
          identifier for a given chromosome.
        - `igenomes`: CharField with a max length of 12, representing the
          iGenomes identifier for a given chromosome.
        - `ensembl`: CharField with a max length of 12, representing the
          Ensembl identifier for a given chromosome.
        - `ucsc`: CharField with a max length of 12, representing the UCSC
          identifier for a given chromosome.
        - `mitra`: CharField with a max length of 15, representing the Mitra
          identifier for a given chromosome.
        - `seqlength`: PositiveIntegerField representing the sequence length of
          a given chromosome.
        - `numbered`: CharField with a max length of 12, representing the
          numbered identifier for a given chromosome.
        - `chr`: CharField with a max length of 12, representing the chromosome
          number or identifier.

    Example usage:

    .. code-block:: python

        from callingcards.models import ChrMap

        # get all ChrMap records
        all_maps = ChrMap.objects.all()

    """

    TYPE = [("genomic", "genomic"), ("mito", "mito"), ("plasmid", "plasmid")]

    refseq = models.CharField(max_length=12, unique=True, help_text="RefSeq chr identifiers")
    igenomes = models.CharField(max_length=12, unique=True, help_text="iGenomes chr identifiers")
    ensembl = models.CharField(max_length=12, unique=True, help_text="Ensembl chr identifiers")
    ucsc = models.CharField(max_length=12, unique=True, help_text="UCSC chr identifiers")
    mitra = models.CharField(max_length=15, unique=True, help_text="Mitra chr identifiers")
    numbered = models.CharField(max_length=12, unique=True, help_text="Numbered chr identifiers")
    chr = models.CharField(max_length=12, unique=True, help_text="Chromosome number or identifier")
    seqlength = models.PositiveIntegerField(help_text="Sequence length of a given chromosome/contig")
    type = models.CharField(
        max_length=8, choices=TYPE, default="genomic", help_text="Chromosome type, one of genomic, mito or plasmid"
    )

    def __str__(self):
        return f"{self.ucsc}(chrID:{self.pk})"  # pylint: disable=no-member

    class Meta:
        managed = True
        db_table = "chrmap"
