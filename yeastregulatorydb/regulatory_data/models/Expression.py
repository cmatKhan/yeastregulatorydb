import logging

from django.db import models
from django.dispatch import receiver

from .BaseModel import BaseModel
from .mixins.GzipFileUploadWithIdMixin import GzipFileUploadWithIdMixin

logger = logging.getLogger(__name__)


class Expression(BaseModel, GzipFileUploadWithIdMixin):
    """
    Store minimal metadata and filepaths to expression data
    """

    regulator = models.ForeignKey("Regulator", on_delete=models.CASCADE)
    batch = models.CharField(
        max_length=20,
        default="undefined",
        help_text="A batch identifier for a set of data, eg the run number in the case of calling cards",
        db_index=True,
    )
    strain = models.CharField(
        max_length=20,
        default="undefined",
        help_text="The strain used in the experiment. This will be derived "
        "from the original data source. Default value is `undefined`",
    )
    replicate = models.PositiveIntegerField(default=1, help_text="Replicate number", db_index=True)
    control = models.CharField(
        choices=[("undefined", "undefined"), ("wt", "wt"), ("wt_mata", "wt_mata")],
        default="undefined",
        help_text="Intended for micro-array data, this field records the "
        "control strain used to generate the relative intensity data",
        db_index=True,
    )
    mechanism = models.CharField(
        choices=[("gev", "gev"), ("zev", "zev"), ("tfko", "tfko")],
        max_length=10,
        default="undefined",
        help_text="The mechanism by which the regulator was perturbed",
        db_index=True,
    )
    restriction = models.CharField(
        choices=[("undefined", "undefined"), ("P", "P"), ("M", "M"), ("N", "N")],
        max_length=10,
        default="undefined",
        help_text="This is a feature of the McIsaac ZEV data",
        db_index=True,
    )
    time = models.PositiveIntegerField(default=0, help_text="Timepoint of the experiment in minutes", db_index=True)
    source = models.ForeignKey("DataSource", on_delete=models.CASCADE)
    file = models.FileField(
        upload_to="temp",
        help_text="A file which stores gene expression " "data that results from a given regulator " "perturbation",
    )
    notes = models.CharField(max_length=100, default="none", help_text="Free entry notes about the data")

    def __str__(self):
        return f"{self.pk}"

    class Meta:
        db_table = "expression"
        unique_together = (
            "regulator",
            "batch",
            "strain",
            "replicate",
            "control",
            "mechanism",
            "restriction",
            "time",
            "source",
        )

    def save(self, *args, **kwargs):
        # Store the old file path
        is_create = self.pk is None
        super().save(*args, **kwargs)
        if is_create:
            self.update_file_name("file", f"expression/{self.source.name}", "csv.gz")
            super().save(update_fields=["file"])

    def get_genomicfeature(self):
        """return the genomicfeature associated with this expression instance"""
        return self.regulator

    def get_fileformat(self):
        """return the fileformat associated with this expression instance"""
        return self.source.fileformat


# pylint: disable=R0801
@receiver(models.signals.post_delete, sender=Expression)
def remove_file_from_s3(sender, instance, using, **kwargs):  # pylint: disable=unused-argument
    """
    this is a post_delete signal. Hence, if the delete command is successful,
    the file will be deleted. If the delete command is successful, and for some
    reason the delete signal fails, it is possible to end up with files in S3
    which are not referenced by the database.
    upon inception, there did not exist any images which were not referenced.
    So,if unreferenced files are ever found, that should indicate that these
    files are erroneous and can be safely deleted
    """
    # note that if the directory (and all subdirectories) are empty, the
    # directory will also be removed
    instance.file.delete(save=False)
