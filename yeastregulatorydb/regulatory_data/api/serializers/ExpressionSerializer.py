from rest_framework import serializers

from ...models.Expression import Expression


class ExpressionSerializer(serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifiedBy = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = Expression
        fields = "__all__"
