import os
import tarfile
import tempfile

import pandas as pd
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from ...serializers import BulkUploadSerializer


class BulkUploadMixin:
    def get_serializer_class(self):
        if self.action == "bulk_upload":
            # Store the original serializer class
            self.default_serializer_class = self.serializer_class
            # Set the serializer class to BulkUploadSerializer
            self.serializer_class = BulkUploadSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=["post"])
    def bulk_upload(self, request):
        bulk_serializer = self.get_serializer(data=request.data)
        if bulk_serializer.is_valid():
            # create a temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # open the tar file and extract it to the temporary directory
                with tarfile.open(fileobj=bulk_serializer.validated_data["tarred_dir"]) as tar:
                    tar.extractall(path=temp_dir)

                # create a dict where the keys are the filenames and the values are the file paths
                file_mapping = {}
                for dirpath, dirnames, filenames in os.walk(temp_dir):
                    for file in filenames:
                        if file not in file_mapping:
                            file_mapping[file] = os.path.join(dirpath, file)
                        else:
                            raise ValueError(f"Duplicate file name {file} in the tar file. Filenames must be unique!")

                df = pd.read_csv(bulk_serializer.validated_data["csv_file"])
                if "file" not in df.columns:
                    return Response("Column 'file' not found in CSV", status=status.HTTP_400_BAD_REQUEST)
                # ensure that only the basename is in the `file` column
                df["file"] = df["file"].apply(os.path.basename)
                # if there is a nonunique filename in the CSV, return a 400 response
                if len(df["file"].unique()) != len(df["file"]):
                    return Response(
                        "Duplicate filename in CSV. the `file` column must have unique file BASENAMES",
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                default_serializer_list = []
                errors = []

                for index, row in df.iterrows():
                    row_dict = row.to_dict()
                    try:
                        with open(file_mapping[row_dict["file"]], "rb") as f:
                            row_dict["file"] = SimpleUploadedFile(row_dict["file"], f.read())
                    except KeyError:
                        errors.append(f"File {row_dict['file']} in the CSV not found in the tar file")
                        # continue checking the rest of the samplesheet so that the user gets all
                        # errors rather than having to repeatedly submit
                        continue

                    default_serializer = self.default_serializer_class(data=row_dict, context={"request": request})

                    if default_serializer.is_valid():
                        default_serializer_list.append(default_serializer)
                    else:
                        errors.append(f"Error in row {index}: {default_serializer.errors}")

                if errors:
                    return Response("\n".join(errors), status=status.HTTP_400_BAD_REQUEST)

                # Save the serializers in a transaction so that if one fails,
                # none of the serializers in the list are saved
                with transaction.atomic():
                    for serializer in default_serializer_list:
                        self.perform_create(serializer)
                return Response("Bulk upload successful", status=status.HTTP_201_CREATED)

        else:
            return Response(f"Bulk upload not valid: {bulk_serializer.errors}", status=status.HTTP_400_BAD_REQUEST)
