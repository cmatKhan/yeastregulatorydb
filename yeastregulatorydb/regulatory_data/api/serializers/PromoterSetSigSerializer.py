from rest_framework import serializers

from ...models.PromoterSetSig import PromoterSetSig


class PromoterSetSigSerializer(serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifiedBy = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = PromoterSetSig
        fields = "__all__"
