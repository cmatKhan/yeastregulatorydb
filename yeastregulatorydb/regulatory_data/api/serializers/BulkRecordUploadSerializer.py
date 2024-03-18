from rest_framework import serializers


class BulkRecordUploadSerializer(serializers.Serializer):
    csv_file = serializers.FileField()

    def validate_csv_file(self, value):
        # Check the header of the file to confirm it's gzip
        header = value.read(2)
        value.seek(0)  # Reset the file read pointer to the beginning
        if header == b"\x1f\x8b":  # Gzip file header signature
            return value
        else:
            raise serializers.ValidationError("Upload file must be gzipped")
