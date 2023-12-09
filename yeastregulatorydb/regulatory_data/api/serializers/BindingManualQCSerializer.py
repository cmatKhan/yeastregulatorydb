from rest_framework import serializers

from ...models.BindingManualQC import BindingManualQC


class BindingManualQCSerializer(serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifiedBy = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = BindingManualQC
        fields = "__all__"
