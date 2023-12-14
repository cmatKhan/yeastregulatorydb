from rest_framework import serializers

from ...models.CallingCardsBackground import CallingCardsBackground
from .mixins.CustomValidateMixin import CustomValidateMixin
from .mixins.GenomicFileValidationMixin import GenomicFileValidationMixin


class CallingCardsBackgroundSerializer(CustomValidateMixin, GenomicFileValidationMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifier = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = CallingCardsBackground
        fields = "__all__"
