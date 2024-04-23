import os

from django.core.files.base import ContentFile


def attach_file_to_instance(instance, file_path):
    with open(file_path, "rb") as f:
        # Django’s ContentFile creates a file from string content, which might not be suitable for binary data
        instance.file.save(os.path.basename(file_path), ContentFile(f.read()), save=True)
