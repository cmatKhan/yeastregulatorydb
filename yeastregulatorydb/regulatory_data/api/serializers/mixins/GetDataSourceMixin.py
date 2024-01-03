import logging
from typing import Any

from rest_framework import serializers

from ....models import DataSource

logger = logging.getLogger(__name__)


class GetDataSourceMixin:
    """
    This mixin is intended for serializers for models that have a `source`
    field which foreign keys to the DataSource model. It extends the
    DRF function to_interval_value() to populate the `source` field if
    `source_name` is provided in the request data.
    """

    def get_source_instance(self, data: dict) -> DataSource:
        """
        Check if the source_name is in the request data. If it is, then
        return the source instance.

        :param data: request data
        :type data: dict
        :return: DataSource instance
        :rtype: DataSource

        :raises serializers.ValidationError: if source_name is not in the request data
        :raises serializers.ValidationError: if the source_name does not correspond to a DataSource instance
        """
        if "source_name" not in data:
            raise serializers.ValidationError(
                "You must provide either field `source` with a valid source "
                "instance `id` or `source_name` with a valid DataSource "
                "instance name"
            )
        else:
            try:
                return DataSource.objects.get(name=data.get("source_name"))
            except DataSource.DoesNotExist:
                raise serializers.ValidationError("Source with name %s does not exist" % data.get("source_name"))

    def to_internal_value(self, data: Any) -> Any:
        """
        Override the DRF to_internal_value() method to populate the `source`
        basd on the `source_name` if `source` is not in the request data, but
        `source_name` is.
        """
        if "source" not in data:
            data["source"] = self.get_source_instance(data).pk
            data.pop("source_name", None)
        return super().to_internal_value(data)
