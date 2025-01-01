import logging

from django.db import models
from django.db.models import UniqueConstraint
from django.dispatch import receiver

from .BaseModel import BaseModel
from .mixins.GzipFileUploadWithIdMixin import GzipFileUploadWithIdMixin

logger = logging.getLogger(__name__)


class RankResponse(BaseModel, GzipFileUploadWithIdMixin):
    """
    Store RankResponse data
    """

    promotersetsig = models.ForeignKey(
        "PromoterSetSig",
        on_delete=models.CASCADE,
        related_name="promotersetsig",
        help_text="Foreign key to the 'PromoterSetSig' table",
    )

    expression = models.ForeignKey(
        "Expression",
        on_delete=models.CASCADE,
        related_name="expression",
        help_text="Foreign key to the 'Expression' table",
    )

    # a json field to store parameters used to generate the rankresponse
    parameters = models.JSONField(
        help_text=(
            "A json field to store parameters used to generate the rankresponse. "
            "The keys are 'bin_size' and 'bin_overlap'. The values are integers."
        )
    )

    passing = models.BooleanField(
        help_text="A boolean field which is `True` if at least one bin is significant in the first 100.",
        default=True,
    )

    total_expression_genes = models.IntegerField(
        help_text="The total number of genes in the expression data", default=0
    )

    random_expectation = models.FloatField(help_text="The random expectation", default=0.0)

    rank_25 = models.FloatField(help_text="The rank response at bin 25", default=0.0)

    rank_50 = models.FloatField(help_text="The rank response at bin 50", default=0.0)

    file = models.FileField(
        upload_to="temp",
        help_text=(
            "A csv which summarizes the responsiveness of a given TF, "
            "ranked by binding. The data is unsummarized but the column "
            "'bin' allows for summarization"
        ),
    )

    def __str__(self):
        return f"pk:{self.pk}"

    class Meta:
        db_table = "rankresponse"
        constraints = [
            UniqueConstraint(
                fields=["promotersetsig", "expression"], name="unique_promotersetsig_expression_rankresponse"
            )
        ]

    # pylint:disable=R0801
    def save(self, *args, **kwargs):
        # Store the old file path
        is_create = self.pk is None
        super().save(*args, **kwargs)
        if is_create:
            self.update_file_name("file", "rankresponse", "csv.gz")
            super().save(update_fields=["file"])

    # pylint:enable=R0801

    def get_regulator(self):
        """return the regulator associated with this promotersetsig instance"""
        return self.promotersetsig.get_regulator()

    def get_genomicfeature(self):
        """return the genomicfeature associated with this promotersetsig instance"""
        return self.get_regulator().genomicfeature

    def get_binding_source_name(self):
        """return the source associated with this promotersetsig instance"""
        # TODO: fix the naming -- promotersetsig.get_source_name() returns the source,
        # not the name
        return self.promotersetsig.get_source_name().name

    def get_expression_source_name(self):
        """return the source associated with this promotersetsig instance"""
        return self.expression.get_source_name()


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
