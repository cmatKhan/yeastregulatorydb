import logging

from django.core.files.storage import default_storage
from django.db import models
from django.dispatch import receiver

from .BaseModel import BaseModel
from .mixins.GzipFileUploadWithIdMixin import GzipFileUploadWithIdMixin

logger = logging.getLogger(__name__)


class RankResponse(BaseModel, GzipFileUploadWithIdMixin):
    """
    Store Rank Response data for a given binding and expression set for a given regulator
    at specific expression effect and pvalue thresholds. The data may or may not be normalized
    across expression data sets.
    """

    promotersetsig = models.ForeignKey(
        "PromoterSetSig", on_delete=models.CASCADE, help_text="foreign key to the 'PromoterSetSig' table"
    )
    expression = models.ForeignKey(
        "Expression", on_delete=models.CASCADE, help_text="foreign key to the 'Expression' table"
    )
    expression_effect_threshold = models.FloatField(
        help_text="The threshold (absolute value) at which to label a gene as "
        "'responsive' in the expression data. Works in conjunction with `expression_pvalue_threshold'. "
        "Default is 0",
        default=0,
    )
    expression_pvalue_threshold = models.FloatField(
        help_text="The threshold at which to label a gene as 'responsive' in "
        "the expression data. Works in conjunction with `expression_effect_threshold`. "
        "Default is 1",
        default=1,
    )
    fileformat = models.ForeignKey(
        "FileFormat", on_delete=models.CASCADE, help_text="foreign key to the 'FileFormat' table"
    )
    normalized = models.BooleanField(
        help_text="This indicates whether the data has been normalized to have the same number of responsive genes "
        "across expression data sets. Default is False. WARNING: not yet implemented -- all are `False`",
        default=False,
    )
    file = models.FileField(
        upload_to="temp",
        help_text="A file which stores the rank response data for a given "
        "binding and expression set for a given regulator at specific "
        "expression effect and pvalue thresholds",
    )
    significant_response = models.BooleanField(
        help_text="This field is used to indicate whether there are any bins "
        "in the top 250 genes with a confidence interval that does not include 0",
        default=False,
    )

    def __str__(self):
        return f"pk:{self.pk}"

    class Meta:
        db_table = "rankresponse"

    # pylint:disable=R0801
    def save(self, *args, **kwargs):
        # Store the old file path
        is_create = self.pk is None
        super().save(*args, **kwargs)
        if is_create:
            old_file_name = self.file.name if self.file else None
            self.update_file_name("file", "rankresponse", "csv.gz")
            new_file_name = self.file.name
            super().save(update_fields=["file"])
            # If the file name changed, delete the old file
            # if old_file_name and old_file_name != new_file_name:
            #     default_storage.delete(old_file_name)

    # pylint:enable=R0801


@receiver(models.signals.post_delete, sender=RankResponse)
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
