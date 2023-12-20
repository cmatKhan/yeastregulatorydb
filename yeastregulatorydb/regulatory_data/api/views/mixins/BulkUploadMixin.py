import pandas as pd
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from ....forms import BulkUploadForm


class BulkUploadMixin:
    @action(detail=False, methods=["post"])
    def bulk_upload(self, request):
        form = BulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES["csv_file"]
            files = request.FILES.getlist("files")
            file_mapping = {file.name: file for file in files}

            df = pd.read_csv(csv_file)
            if "file" not in df.columns:
                return Response("Column 'file' not found in CSV", status=status.HTTP_400_BAD_REQUEST)

            serializer_list = []
            errors = []

            for index, row in df.iterrows():
                row_dict = row.to_dict()
                try:
                    row_dict["file"] = file_mapping[row_dict["file"]]
                except KeyError:
                    errors.append(f"File {row_dict['file']} in the csv not found in the uploaded set of files")
                    continue

                serializer = self.get_serializer(data=row_dict)

                if serializer.is_valid():
                    serializer_list.append(serializer)
                else:
                    errors.append(f"Error in row {index}: {serializer.errors}")

            if errors:
                return Response("\n".join(errors), status=status.HTTP_400_BAD_REQUEST)

            # Save the serializers in a transaction so that if one fails,
            # none of the serializers in the list are saved
            with transaction.atomic():
                for serializer in serializer_list:
                    serializer.save()

            return Response("Bulk upload successful", status=status.HTTP_201_CREATED)

        else:
            return Response(f"Form is not valid: {form.errors}", status=status.HTTP_400_BAD_REQUEST)
