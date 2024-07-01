import os

import boto3
from botocore.exceptions import ClientError


def generate_presigned_url(file_key, expiration=3600):
    """Generate a presigned URL to share an S3 object

    :param file_key: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("DJANGO_AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("DJANGO_AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("DJANGO_AWS_S3_REGION_NAME", default=None),
    )
    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": os.getenv("DJANGO_AWS_STORAGE_BUCKET_NAME"), "Key": file_key},
            ExpiresIn=expiration,
        )
    except ClientError as e:
        print(e)
        return None

    return response
