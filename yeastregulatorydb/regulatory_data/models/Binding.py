import logging

from django.db import models
from django.dispatch import receiver

from .BaseModel import BaseModel
from .mixins.GzipFileUploadWithIdMixin import GzipFileUploadWithIdMixin

logger = logging.getLogger(__name__)


class Binding(BaseModel, GzipFileUploadWithIdMixin):
    """
    Store some metadata and filepaths to binding data
    """

    CONDITION_CHOICES = [
        ("unknown", "unknown"),
        ("YPD", "YPD"),
        ("SM", "SM"),
        ("RAPA", "RAPA"),
        ("H2O2Hi", "H2O2Hi"),
        ("H2O2Lo", "H2O2Lo"),
        ("Acid", "Acid"),
        ("Alpha", "Alpha"),
        ("BUT14", "BUT14"),
        ("BUT90", "BUT90"),
        ("Thi-", "Thi-"),
        ("GAL", "GAL"),
        ("HEAT", "HEAT"),
        ("Pi-", "Pi-"),
        ("RAFF", "RAFF"),
    ]

    regulator = models.ForeignKey(
        "Regulator", on_delete=models.CASCADE, help_text="Foreign key to the Regulator table"
    )
    batch = models.CharField(
        max_length=20,
        default="none",
        help_text="A batch identifier for a set of data, " "eg the run number in the case of calling cards",
    )
    replicate = models.PositiveIntegerField(default=1, help_text="Replicate number")
    source = models.ForeignKey("DataSource", on_delete=models.CASCADE)
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
        help_text="If the strain identifier is known, it is provided. Otherwise, the value is `unknown`",
    )
    condition = models.CharField(
        max_length=20,
        default="unknown",
        choices=CONDITION_CHOICES,
        help_text="If the condition is known, it is provided. Otherwise, the value is `unknown`",
    )
    file = models.FileField(
        upload_to="temp", help_text="A file which stores data on regulator/DNA interaction", blank=True, null=True
    )
    # NOTE: the _inserts fields are added during the serialization process from the file
    # in BindingSerializer and its mixin ValidateFileMixin
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
    notes = models.CharField(
        max_length=100, default="none", help_text="free entry text field, no more than 100 char long"
    )

    def __str__(self):
        return str(self.pk)

    class Meta:
        db_table = "binding"
        unique_together = ("regulator", "batch", "condition", "replicate", "source")

    def save(self, *args, **kwargs):
        # Store the old file path
        is_create = self.pk is None
        super().save(*args, **kwargs)
        if is_create:
            self.update_file_name("file", f"binding/{self.source.name}")
            super().save(update_fields=["file"])


@receiver(models.signals.post_delete, sender=Binding)
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
