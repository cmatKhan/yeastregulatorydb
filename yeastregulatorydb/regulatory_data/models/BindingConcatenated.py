from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import m2m_changed


class BindingConcatenated(models.Model):
    bindings = models.ManyToManyField("Binding")
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


def validate_bindings(sender, instance, action, **kwargs):
    if action == "post_add" or action == "post_remove" or action == "post_clear":
        if instance.bindings.exists():
            first_binding = instance.bindings.first()
            regulator_id = first_binding.regulator_id
            source_id = first_binding.source_id

            for binding in instance.bindings.all():
                if binding.regulator_id != regulator_id:
                    raise ValidationError("All bindings must have the same regulator.")
                if binding.source_id != source_id:
                    raise ValidationError("All bindings must have the same source.")


m2m_changed.connect(validate_bindings, sender=BindingConcatenated.bindings.through)
