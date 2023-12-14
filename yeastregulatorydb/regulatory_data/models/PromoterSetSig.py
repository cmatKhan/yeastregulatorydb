import logging

from django.core.files.storage import default_storage
from django.db import models
from django.dispatch import receiver

from .BaseModel import BaseModel
from .mixins.FileUploadWithIdMixin import FileUploadMixin

logger = logging.getLogger(__name__)


class PromoterSetSig(BaseModel, FileUploadMixin):
    """
    Store PromoterSetSig data
    """

    binding = models.ForeignKey("Binding", on_delete=models.CASCADE, help_text="foreign key to the 'Binding' table")
    promoter = models.ForeignKey(
        "PromoterSet", on_delete=models.CASCADE, help_text="foreign key to the 'promoter' table"
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
        return f"pk:{self.pk};binding:{self.binding};" f"promoter_id:{self.promoter};background:{self.background}"

    class Meta:
        db_table = "promotersetsig"

    # pylint:disable=R0801
    def save(self, *args, **kwargs):
        # Store the old file path
        old_file_name = self.file.name if self.file else None
        super().save(*args, **kwargs)
        self.update_file_name("file", "promotersetsig", "tsv.gz")
        new_file_name = self.file.name
        super().save(update_fields=["file"])
        # If the file name changed, delete the old file
        if old_file_name and old_file_name != new_file_name:
            default_storage.delete(old_file_name)

    # pylint:enable=R0801


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
