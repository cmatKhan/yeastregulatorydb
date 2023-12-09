"""
.. module:: Binding
   :synopsis: A model for storing filepaths to files concerning regulator/DNA binding data.

This model is used to keep an index of the files which store binding data,
eg chip-seq, chip-exo, calling cards. More information on the data itself
is stored in the BindingSource model.

.. author:: Chase Mateusiak
.. date:: 2023-04-17
.. modified:: 2023-12-07
"""
import logging

from django.core.files.storage import default_storage
from django.db import models
from django.dispatch import receiver

from .BaseModel import BaseModel
from .mixins.FileUploadWithIdMixin import FileUploadMixin

logger = logging.getLogger(__name__)


class Binding(BaseModel, FileUploadMixin):
    """
    Store some metadata and filepaths to binding data
    """

    regulator = models.ForeignKey("Regulator", on_delete=models.CASCADE)
    batch = models.CharField(
        max_length=20,
        default="none",
        help_text="A batch identifier for a set of data, " "eg the run number in the case of calling cards",
    )
    replicate = models.PositiveIntegerField(default=1, help_text="Replicate number")
    source_id = models.ForeignKey("BindingSource", on_delete=models.CASCADE)
    source_orig_id = models.CharField(
        max_length=20,
        default="none",
        help_text="If the data was provided by a third party, and that data "
        "has a unique identifier, it is provided here. Otherwise, the value "
        " is `none`",
    )
    strain = models.CharField(
        max_length=20,
        default="unknown",
        help_text="If the strain identifier is known, it is provided. " "Otherwise, the value is `unknown`",
    )
    file = models.FileField(upload_to="temp", help_text="A file which stores data on regulator/DNA interaction")
    genomic_inserts = models.PositiveIntegerField(
        default=0,
        help_text="The number of inserts which map to chromosomes labelled as `genomic` in the ChrMap table",
    )
    mito_inserts = models.PositiveIntegerField(
        default=0,
        help_text="The number of inserts which map to chromosomes labelled as mitochondrial in the ChrMap table",
    )
    plasmid_inserts = models.PositiveIntegerField(
        default=0,
        help_text="The number of inserts which map to contigs labelled as plasmid in the ChrMap table",
    )
    notes = models.CharField(max_length=100, default="none")

    def __str__(self):
        return f"{self.source_id}_{self.regulator}__{self.batch}__{self.replicate}"

    class Meta:
        db_table = "binding"
        constraints = [
            models.CheckConstraint(
                check=models.Q(start__gt=0),
                name="start_cannot_be_less_than_one",
            ),
        ]
        unique_together = ("regulator", "batch", "replicate", "source_id")

    def save(self, *args, **kwargs):
        # Store the old file path
        old_file_name = self.file.name if self.file else None
        super().save(*args, **kwargs)
        self.update_file_name("file", f"binding/{self.source_id}", "tsv.gz")
        new_file_name = self.file.name
        super().save(update_fields=["file"])
        # If the file name changed, delete the old file
        if old_file_name and old_file_name != new_file_name:
            default_storage.delete(old_file_name)


@receiver(models.signals.post_delete, sender=Binding)
def remove_file_from_s3(sender, instance, using, **kwargs):
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
