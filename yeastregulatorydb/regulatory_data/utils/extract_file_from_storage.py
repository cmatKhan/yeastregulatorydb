import os
import uuid

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
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
    :raises FileExistsError: If the data needs to be downloaded, then a unique subdir
        is created. If that subdir already exists, this error is raised.
    :raises FileNotFoundError: If the file.url is used, and the url returns something
    other than a status_code 200
    """
    if not os.path.isdir(dirpath):
        raise FileExistsError(f"Directory does not exist: {dirpath}")

    # Check if the file exists in the local storage path. If it does,
    # just return that path
    local_path = os.path.join(settings.MEDIA_ROOT, file.name)
    if os.path.exists(local_path):
        return local_path
    else:
        # Else, create a unique directory name using a unique identifier within dirpath
        unique_dir = os.path.join(dirpath, str(uuid.uuid4()))
        # if the unique directory already exists, raise an error. This unique
        # subdir is a check on accidently overwriting data with the same filename
        # while retaining the original files' extension by using basename
        os.makedirs(unique_dir, exist_ok=False)

        # Use the basename of the file for the new local path
        output_path = os.path.join(unique_dir, os.path.basename(file.name))

        try:
            # Check if file exists in default storage (which includes S3)
            if default_storage.exists(file.name):
                # Open the file from storage (this will be streamed if it's on S3)
                with default_storage.open(file.name, "rb") as source_file:
                    with open(output_path, "wb") as destination_file:
                        for chunk in source_file.chunks():
                            destination_file.write(chunk)
            else:
                raise FileNotFoundError(f"File does not exist in storage: {file.name}")
        except NotImplementedError:
            raise ImproperlyConfigured("This backend doesn't support absolute paths.")

        return output_path
