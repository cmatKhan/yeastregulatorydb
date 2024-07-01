from django.core.files.storage import default_storage


def is_s3_storage():
    return "S3Boto3Storage" in str(type(default_storage))
