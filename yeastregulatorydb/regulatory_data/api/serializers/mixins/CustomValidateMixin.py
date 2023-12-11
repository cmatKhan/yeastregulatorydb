from rest_framework import serializers


class CustomValidateMixin:  # pylint: disable=too-few-public-methods
    """
    A mixin for Django Rest Framework serializers that raises a 400 error if
    the user tries to pass `modifiedBy` in the request data. `modifiedBy` is
    set automatically in the view or viewset.

    To use this mixin, include it in your serializer and call `super()` in your
    `validate()` method.

    Example:

    .. code-block:: python

        class YourSerializer(ValidateModifiedByMixin,
                             serializers.ModelSerializer):
            ...

            def validate(self, data):
                if 'modifiedBy' in data:
                    raise serializers.ValidationError(
                        {'modifiedBy': 'This field is read-only.'})

                return super().validate(data)
    """

    def validate(self, data):
        if "modifiedBy" in data:
            raise serializers.ValidationError({"modifiedBy": "This field is read-only."})

        return super().validate(data)  # type: ignore[misc]
