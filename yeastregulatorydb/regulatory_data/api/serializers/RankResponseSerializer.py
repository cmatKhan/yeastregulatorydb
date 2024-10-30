from rest_framework import serializers

from ...models import RankResponse
from .mixins.CustomValidateMixin import CustomValidateMixin


class RankResponseSerializer(CustomValidateMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifier = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = RankResponse
        fields = "__all__"
