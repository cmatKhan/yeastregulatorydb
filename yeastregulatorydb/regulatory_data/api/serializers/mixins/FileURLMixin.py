from django.conf import settings
from rest_framework import serializers

from yeastregulatorydb.regulatory_data.utils import (
    generate_presigned_url,
    is_s3_storage,
)


# this is an attempt at getting the file download to work through the restframework
# API. Didn't help.
class FileURLMixin:
    file_url = serializers.SerializerMethodField()

    def get_file_url(self, obj):
        file_field = getattr(obj, "file", None)
        if not file_field:
            return None

        file_key = file_field.name
        if is_s3_storage():
            presigned_url = generate_presigned_url(file_key)
            if presigned_url:
                return presigned_url
            return None
        else:
            request = self.context.get("request")
            return request.build_absolute_uri(f"{settings.MEDIA_URL}{file_key}")
