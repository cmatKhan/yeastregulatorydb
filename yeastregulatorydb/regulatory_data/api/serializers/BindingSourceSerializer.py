from rest_framework import serializers

from ...models.BindingSource import BindingSource
from .mixins.CustomValidateMixin import CustomValidateMixin


class BindingSourceSerializer(CustomValidateMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifier = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = BindingSource
        fields = "__all__"
