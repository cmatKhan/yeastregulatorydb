import logging

from django.core.files.storage import default_storage
from django.db import models
from django.dispatch import receiver

from .BaseModel import BaseModel
from .mixins.FileUploadWithIdMixin import FileUploadMixin

logger = logging.getLogger(__name__)


class CallingCardsBackground(BaseModel, FileUploadMixin):
    """
    Store calling cards background hops data
    """

    name = models.CharField(
        max_length=10, blank=False, null=False, help_text="The name of the background data", unique=True
    )
    file = models.FileField(upload_to="temp", help_text="A file which stores data on " "regulator/DNA interaction")
    genomic_inserts = models.PositiveIntegerField(
        default=0, help_text="The number of inserts which map to chromosomes with type `genomic` in ChrMap"
    )
    mito_inserts = models.PositiveIntegerField(
        default=0, help_text="The number of inserts which map to chromosomes with type `mitochondrial` in ChrMap"
    )
    plasmid_inserts = models.PositiveIntegerField(
        default=0, help_text="The number of inserts which map to contigs with type `plasmid` in ChrMap"
    )
    notes = models.CharField(
        max_length=100, default="none", help_text="free entry text field, no more than 100 char long"
    )

    def __str__(self):
        return f"background:{self.name}"

    class Meta:
        db_table = "callingcardsbackground"

    # pylint:disable=R0801
    def save(self, *args, **kwargs):
        # Store the old file path
        old_file_name = self.file.name if self.file else None
        super().save(*args, **kwargs)
        self.update_file_name("file", "callingcards/background", "tsv.gz")
        new_file_name = self.file.name
        super().save(update_fields=["file"])
        # If the file name changed, delete the old file
        if old_file_name and old_file_name != new_file_name:
            default_storage.delete(old_file_name)

    # pylint:enable=R0801


@receiver(models.signals.post_delete, sender=CallingCardsBackground)
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
