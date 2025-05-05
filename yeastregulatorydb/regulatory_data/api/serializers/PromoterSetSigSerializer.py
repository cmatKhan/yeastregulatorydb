import logging

from rest_framework import serializers

from ...models import PromoterSetSig
from .mixins.CustomValidateMixin import CustomValidateMixin
from .mixins.FileValidationMixin import FileValidationMixin

logger = logging.getLogger(__name__)


class PromoterSetSigSerializer(CustomValidateMixin, FileValidationMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifier = serializers.CharField(source="uploader.username", required=False)

    source_name = serializers.CharField(read_only=True)
    regulator_symbol = serializers.CharField(read_only=True)
    regulator_locus_tag = serializers.CharField(read_only=True)
    condition = serializers.CharField(read_only=True)
    data_usable = serializers.CharField(read_only=True)
    preferred_replicate = serializers.CharField(read_only=True)
    background_name = serializers.CharField(source="background.name", read_only=True)
    promoterset = serializers.CharField(source="promoter.name", read_only=True)
    batch = serializers.CharField(read_only=True)
    lab = serializers.CharField(read_only=True)
    assay = serializers.CharField(read_only=True)
    source_orig_id = serializers.CharField(read_only=True)

    def update(self, instance, validated_data):
        # Track if the file field is actually being updated
        file_updated = "file" in validated_data

        # Call original update method
        instance = super().update(instance, validated_data)

        # Only save again if the file field was updated
        if file_updated:
            logger.warning("File field was updated. Saving instance again to ensure file changes are persisted.")
            instance.save(update_fields=["file"])

        return instance

    class Meta:
        model = PromoterSetSig
        # note when not using __all__ for some reason the additional fields are not
        # passed through to the attrs needed to extract the fileformat in the
        # validate_df() fucnction
        fields = "__all__"
