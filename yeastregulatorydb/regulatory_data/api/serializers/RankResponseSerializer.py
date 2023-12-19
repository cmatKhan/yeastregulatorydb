from rest_framework import serializers

from ...models import RankResponse
from .mixins.CustomValidateMixin import CustomValidateMixin
from .mixins.FileValidationMixin import FileValidationMixin


class RankResponseSerializer(CustomValidateMixin, FileValidationMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifier = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = RankResponse
        fields = "__all__"
