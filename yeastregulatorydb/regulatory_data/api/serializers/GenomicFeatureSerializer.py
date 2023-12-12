from rest_framework import serializers

from ...models import ChrMap, GenomicFeature
from .mixins.CustomValidateMixin import CustomValidateMixin


class GenomicFeatureSerializer(CustomValidateMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifiedBy = serializers.CharField(source="uploader.username", required=False)

    class Meta:
        model = GenomicFeature
        fields = "__all__"

    def validate(self, data):
        """
        Check that the chr field is present.
        """
        if "chr" not in data:
            raise serializers.ValidationError("`chr` field is missing")
        return data

    def validate_start(self, value):
        """
        Check that the start value is less than the end value and that it is
        greater than 0.
        """
        if isinstance(value, str) and value.isdigit():
            value = int(value)
        elif not isinstance(value, int):
            raise serializers.ValidationError("`start` value must be an integer")

        if value < 1:
            raise serializers.ValidationError("Start value cannot be less than 1")

        chr = ChrMap.objects.get(pk=self.initial_data["chr"])
        if value > chr.seqlength:
            raise serializers.ValidationError("`start` of feature cannot exceed length of chromosome")

        if "end" in self.initial_data and value > self.initial_data["end"]:
            raise serializers.ValidationError("Start value cannot be greater than end value")

        return value

    def validate_end(self, value):
        """
        Check that the end is less than or equal to the length of the chromosome + 1,
        that end is at least 1, and that end is either an int or a str representation
        of an int. No need to check that end > start because that is done in the
        `validate_start` method.
        """
        if isinstance(value, str) and value.isdigit():
            value = int(value)
        elif not isinstance(value, int):
            raise serializers.ValidationError("`end` value must be an integer")

        if value < 1:
            raise serializers.ValidationError("End value cannot be less than 1")

        chr = ChrMap.objects.get(pk=self.initial_data["chr"])
        if value >= chr.seqlength + 1:
            raise serializers.ValidationError("End of feature cannot exceed length of chromosome")

        return value
