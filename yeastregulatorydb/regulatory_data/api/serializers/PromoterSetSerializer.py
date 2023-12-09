from rest_framework import serializers

from ...models.PromoterSet import PromoterSet


class PromoterSetSerializer(serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifiedBy = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = PromoterSet
        fields = "__all__"
