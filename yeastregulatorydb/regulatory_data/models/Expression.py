import logging

from django.core.files.storage import default_storage
from django.db import models
from django.dispatch import receiver

from .BaseModel import BaseModel
from .mixins.FileUploadWithIdMixin import FileUploadMixin

logger = logging.getLogger(__name__)


class Expression(BaseModel, FileUploadMixin):
    """
    Store minimal metadata and filepaths to expression data
    """

    regulator_id = models.ForeignKey("Regulator", on_delete=models.CASCADE)
    batch = models.CharField(
        max_length=20,
        default="undefined",
        help_text="A batch identifier for a set of data, " "eg the run number in the case of calling cards",
    )
    replicate = models.PositiveIntegerField(default=1, help_text="Replicate number")
    control = models.CharField(
        choices=[("undefined", "undefined"), ("wt", "wt"), ("wt_mata", "wt_mata")],
        default="undefined",
        help_text="Intended for micro-array data, this field records the "
        "control strain used to generate the relative intensity data",
    )
    mechanism = models.CharField(
        choices=[("gev", "gev"), ("zev", "zev"), ("tfko", "tfko")],
        max_length=10,
        default="undefined",
        help_text="The mechanism by which the regulator was perturbed",
    )
    restriction = models.CharField(
        choices=[("undefined", "undefined"), ("P", "P"), ("M", "M"), ("N", "N")],
        max_length=10,
        default="undefined",
        help_text="This is a feature of the McIsaac ZEV data",
    )
    time = models.PositiveIntegerField(default=0, help_text="Timepoint of the experiment in minutes")
    source_id = models.ForeignKey("ExpressionSource", on_delete=models.CASCADE)
    file = models.FileField(
        upload_to="temp",
        help_text="A file which stores gene expression " "data that results from a given regulator " "perturbation",
    )
    notes = models.CharField(max_length=100, default="none", help_text="Free entry notes about the data")

    def __str__(self):
        return f"{self.source_id}_{self.regulator_id}__{self.batch}__{self.replicate}"

    class Meta:
        db_table = "expression"

    # pylint: disable=R0801
    def save(self, *args, **kwargs):
        # Store the old file path
        old_file_name = self.file.name if self.file else None
        super().save(*args, **kwargs)
        self.update_file_name("file", f"expression/{self.source_id}", "tsv.gz")
        new_file_name = self.file.name
        super().save(update_fields=["file"])
        # If the file name changed, delete the old file
        if old_file_name and old_file_name != new_file_name:
            default_storage.delete(old_file_name)

    # pylint: enable=R0801


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
