from rest_framework import serializers

from ...models.BindingSource import BindingSource


class BindingSourceSerializer(serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifiedBy = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = BindingSource
        fields = "__all__"
