from rest_framework import serializers

from ...models.Binding import Binding
from .mixins.CustomValidateMixin import CustomValidateMixin
from .mixins.GenomicFileValidationMixin import GenomicFileValidationMixin


class BindingSerializer(CustomValidateMixin, GenomicFileValidationMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifier = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = Binding
        fields = "__all__"
