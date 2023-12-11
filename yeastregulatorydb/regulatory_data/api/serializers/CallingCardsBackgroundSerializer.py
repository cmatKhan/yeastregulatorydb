from rest_framework import serializers

from ...models.CallingCardsBackground import CallingCardsBackground
from .mixins.CustomValidateMixin import CustomValidateMixin


class CallingCardsBackgroundSerializer(CustomValidateMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifiedBy = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = CallingCardsBackground
        fields = "__all__"
