from rest_framework import serializers


class BulkFileUploadSerializer(serializers.Serializer):
    csv_file = serializers.FileField()
    tarred_dir = serializers.FileField()
