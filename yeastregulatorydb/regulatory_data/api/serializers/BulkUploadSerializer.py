from rest_framework import serializers


class BulkUploadSerializer(serializers.Serializer):
    csv_file = serializers.FileField()
    tarred_dir = serializers.FileField()
