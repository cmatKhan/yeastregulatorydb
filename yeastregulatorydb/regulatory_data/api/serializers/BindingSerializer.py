from rest_framework import serializers

from ...models.Binding import Binding
from .mixins.CustomValidateMixin import CustomValidateMixin


class BindingSerializer(CustomValidateMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifiedBy = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = Binding
        fields = "__all__"
