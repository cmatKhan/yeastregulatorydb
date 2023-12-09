from rest_framework import serializers

from ...models.ExpressionSource import ExpressionSource


class ExpressionSourceSerializer(serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifiedBy = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = ExpressionSource
        fields = "__all__"
