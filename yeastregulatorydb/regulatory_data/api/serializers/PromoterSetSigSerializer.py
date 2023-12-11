import pandas as pd
from django.conf import settings
from rest_framework import serializers

from yeastregulatorydb.regulatory_data.utils.validate_genomic_df import validate_genomic_df

from ...models import FileFormat, PromoterSetSig
from .mixins.CustomValidateMixin import CustomValidateMixin
from .mixins.FileValidationMixin import FileValidationMixin


class PromoterSetSigSerializer(CustomValidateMixin, FileValidationMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifiedBy = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = PromoterSetSig
        fields = "__all__"

    def get_background_id(self, obj):
        return obj.background_id.id if obj.background_id else "undefined"
