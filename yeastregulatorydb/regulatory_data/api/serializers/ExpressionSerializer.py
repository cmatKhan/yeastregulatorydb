from django.db.models import F
from rest_framework import serializers

from ...models.Expression import Expression
from .mixins import CustomValidateMixin, FileValidationMixin, GetDataSourceMixin, GetOrCreateRegulatorMixin


class ExpressionSerializer(
    GetOrCreateRegulatorMixin,
    GetDataSourceMixin,
    CustomValidateMixin,
    FileValidationMixin,
    serializers.ModelSerializer,
):
    # Read-only fields derived from annotations or related models
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifier = serializers.ReadOnlyField(source="modifier.username")
    regulator_id = serializers.CharField(source="regulator.genomicfeature.id", read_only=True)
    regulator_locus_tag = serializers.CharField(source="regulator.genomicfeature.locus_tag", read_only=True)
    regulator_symbol = serializers.CharField(source="regulator.genomicfeature.symbol", read_only=True)
    source_name = serializers.CharField(source="source.name", read_only=True)
    assay = serializers.CharField(source="source.assay", read_only=True)
    fileformat = serializers.CharField(source="source.fileformat.name", read_only=True)

    # Flattened fields from ExpressionManualQC
    strain_verified = serializers.CharField(read_only=True)
    preferred_replicate = serializers.BooleanField(read_only=True)
    qc_notes = serializers.CharField(read_only=True)

    class Meta:
        model = Expression
        # note when not using __all__ for some reason the additional fields are not
        # passed through to the attrs needed to extract the fileformat in the
        # validate_df() fucnction
        fields = "__all__"
        # fields = [
        #     "id",
        #     "uploader",
        #     "modifier",
        #     "regulator_id",
        #     "regulator_locus_tag",
        #     "regulator_symbol",
        #     "source_name",
        #     "fileformat",
        #     "assay",
        #     "strain_verified",
        #     "preferred_replicate",
        #     "notes",
        #     "qc_notes",
        #     "file",
        # ]
