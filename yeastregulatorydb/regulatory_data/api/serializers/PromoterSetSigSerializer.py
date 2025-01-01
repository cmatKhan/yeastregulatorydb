from rest_framework import serializers

from ...models import Binding, BindingConcatenated, CallingCardsBackground, FileFormat, PromoterSetSig
from .mixins.CustomValidateMixin import CustomValidateMixin
from .mixins.FileValidationMixin import FileValidationMixin


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

    class Meta:
        model = PromoterSetSig
        # note when not using __all__ for some reason the additional fields are not
        # passed through to the attrs needed to extract the fileformat in the
        # validate_df() fucnction
        fields = "__all__"
        # fields = [
        #     "id",
        #     "uploader",
        #     "modifier",
        #     "upload_date",
        #     "modified_date",
        #     "single_binding",
        #     "composite_binding",
        #     "fileformat",
        #     "background",
        #     "source",
        #     "regulator_symbol",
        #     "regulator_locus_tag",
        #     "condition",
        #     "background_name",
        #     "promoterset",
        #     "data_usable",
        #     "preferred_replicate",
        #     "file",
        # ]
