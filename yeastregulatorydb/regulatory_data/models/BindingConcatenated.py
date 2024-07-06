from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import m2m_changed

from .BaseModel import BaseModel


class BindingConcatenated(BaseModel):
    bindings = models.ManyToManyField("Binding", help_text="Many to many relationship with the Binding table")
    regulator = models.ForeignKey(
        "Regulator", on_delete=models.CASCADE, help_text="Foreign key to the Regulator table"
    )
    source = models.ForeignKey("DataSource", on_delete=models.CASCADE, help_text="Foreign key to the DataSource table")
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
        max_length=100, default="none", help_text="Free entry text field, no more than 100 char long"
    )

    def __str__(self):
        return str(self.pk)

    class Meta:
        db_table = "bindingconcatenated"
        # the regulator and source must be unique together -- currently, this table
        # stores the aggregation fo passing calligncards replicates
        constraints = [
            models.UniqueConstraint(fields=["regulator", "source"], name="unique_regulator_source_bindingconcatenated")
        ]


def validate_bindings(sender, instance, action, **kwargs):
    if action in ["post_add", "post_remove", "post_clear"]:
        if instance.bindings.exists():
            regulator_id = instance.regulator.id
            source_id = instance.source.id

            for binding in instance.bindings.all():
                if binding.regulator_id != regulator_id:
                    raise ValidationError("All bindings must have the same regulator.")
                if binding.source_id != source_id:
                    raise ValidationError("All bindings must have the same source.")


m2m_changed.connect(validate_bindings, sender=BindingConcatenated.bindings.through)
