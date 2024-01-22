from django.db import models

from .BaseModel import BaseModel


class RegulatorManager(models.Manager):
    """Custom manager for the Regulator model

    Example usage:

    .. code-block:: python

        # in RegulatorManager
        def custom_method(self):
            # do some operations eg filter, exclude, annotation...
            # and return

        # get all Regulator records that are still under development
        my_regulator_set = Regulator.objects.custom_method()
    """

    def under_development(self):
        return self.filter(under_development=True)

    def annotated(self):
        return self.select_related(
            "uploader",
            "genomicfeature",
        ).annotate(
            regulator_locus_tag=models.F("genomicfeature__locus_tag"),
            regulator_symbol=models.F("genomicfeature__symbol"),
        )


class Regulator(BaseModel):
    """This table is used to store the set of proteins on which an experiment
    has been performed. Eg, if a given locus tag is one of the overexpressed
    proteins in McIsaac or a TF in the callingcards set.

    Fields:
        - regulator: ForeignKey to the Gene model, representing the gene that
        the regulator.
        - under_development: BooleanField, representing whether the calling
        card experiment for this transcription factor is still under
        development.
        - notes: CharField with a max length of 50, representing any notes
        about the transcription factor or calling card experiment.

    Example usage:

    .. code-block:: python


        from callingcards.models import Regulator

        # get all Regulator records
        all_regulators = Regulator.objects.all()
    """

    objects = RegulatorManager()

    genomicfeature = models.ForeignKey(
        "GenomicFeature", models.PROTECT, db_index=True, help_text="foreign key to the `id` field of GenomicFeature"
    )
    under_development = models.BooleanField(
        default=False, help_text="whether the regulator is being currently interrogated in any experiments"
    )
    notes = models.CharField(
        max_length=50, default="none", help_text="free entry text field, no more than 50 char long"
    )

    def __str__(self):
        return str(self.pk)

    class Meta:
        managed = True
        db_table = "regulator"
