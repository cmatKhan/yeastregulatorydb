import logging

from django.db import models
from django.dispatch import receiver

from .BaseModel import BaseModel
from .mixins.GzipFileUploadWithIdMixin import GzipFileUploadWithIdMixin

logger = logging.getLogger(__name__)


class PromoterSetSig(BaseModel, GzipFileUploadWithIdMixin):
    """
    Store PromoterSetSig data
    """

    binding = models.ForeignKey("Binding", on_delete=models.CASCADE, help_text="foreign key to the 'Binding' table")
    promoter = models.ForeignKey(
        "PromoterSet", on_delete=models.CASCADE, help_text="foreign key to the 'promoter' table", blank=True, null=True
    )
    # note: in the serializer, when a user makes a GET request, a null value
    # is transformed to the string 'undefined' prior to returning to client
    background = models.ForeignKey(
        "CallingCardsBackground",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        help_text="foreign key to the 'CallingCardsBackground' table",
    )
    fileformat = models.ForeignKey(
        "FileFormat", on_delete=models.CASCADE, help_text="foreign key to the 'FileFormat' table"
    )
    file = models.FileField(upload_to="temp", help_text="A file which stores data on " "regulator/DNA interaction")

    def __str__(self):
        return f"pk:{self.pk}"

    class Meta:
        db_table = "promotersetsig"

    # pylint:disable=R0801
    def save(self, *args, **kwargs):
        # Store the old file path
        is_create = self.pk is None
        super().save(*args, **kwargs)
        if is_create:
            self.update_file_name("file", "promotersetsig", "csv.gz")
            super().save(update_fields=["file"])

    # pylint:enable=R0801

    def get_genomicfeature(self):
        """return the genomicfeature associated with this promotersetsig instance"""
        return self.binding.regulator

    def get_fileformat(self):
        """return the fileformat associated with this expression instance"""
        return self.fileformat


@receiver(models.signals.post_delete, sender=PromoterSetSig)
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
