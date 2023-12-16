import os
import shutil

import requests
from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage


def extract_file_from_storage(file: File, dirpath: str = ".") -> str:
    """
    Return the path to a file. If the file is stored locally, the path
    to the local storage is returned. Else, if the file is stored on S3,
    the file is downloaded to the directory specified by `dirpath` and
    the path to the downloaded file is returned.

    :param file: The file to download
    :type file: File
    :param dirpath: The path to the directory where the file should be downloaded.
    Note that while this is a required argument, if the file is stored locally
    and not on S3, the file is not copied and this argument is ignored.
    :type dirpath: str

    :return: The path to the file
    :rtype: str

    :raises FileExistsError: If the directory specified by `dirpath` does not exist
    :raises FileNotFoundError: If the file.url is used, and the url returns something
    other than a status_code 200
    """
    if not os.path.isdir(dirpath):
        raise FileExistsError(f"Directory does not exist: {dirpath}")

    local_path = os.path.join(settings.MEDIA_ROOT, file.name)

    if os.path.exists(local_path):
        return local_path
    else:
        if default_storage.exists(file.name):
            with default_storage.open(file.name, "rb") as source_file:
                with open(local_path, "wb") as destination_file:
                    for chunk in source_file.chunks():
                        destination_file.write(chunk)
        else:
            raise FileNotFoundError(f"File does not exist in storage: {file.name}")

    return local_path
