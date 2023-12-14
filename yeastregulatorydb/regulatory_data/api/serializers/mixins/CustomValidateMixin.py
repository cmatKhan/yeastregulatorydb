from django.utils import timezone
from rest_framework import serializers


class CustomValidateMixin:  # pylint: disable=too-few-public-methods
    """
    A mixin for Django Rest Framework serializers that raises a 400 error if
    the user tries to pass `modifier` in the request data. `modifier` is
    set automatically in the view or viewset.

    To use this mixin, include it in your serializer and call `super()` in your
    `validate()` method.

    Example:

    .. code-block:: python

        class YourSerializer(ValidateModifiedByMixin,
                             serializers.ModelSerializer):
            ...

            def validate(self, data):
                if 'modifier' in data:
                    raise serializers.ValidationError(
                        {'modifier': 'This field is read-only.'})

                return super().validate(data)
    """

    def validate(self, data):
        # require that the user is authenticated
        request = self.context.get("request")
        if not request.user.is_authenticated:
            raise serializers.ValidationError("User must be authenticated to validate data and create a new record.")

        # these fields are expected to be overwritten in `create` and `update`
        data["uploader"] = request.user
        data["upload_date"] = timezone.now()
        data["modifier"] = request.user
        data["modified_date"] = timezone.now()

        return super().validate(data)  # type: ignore[misc]

    def validate_uploader(self, value):
        """
        Check that the uploader is `None` -- the user should not be passing this value.
        """
        if value is not None:
            raise serializers.ValidationError("This field is read-only.")
        return value

    def validate_upload_date(self, value):
        """
        Check that the upload_date is `None` -- the user should not be passing this value.
        """
        if value is not None:
            raise serializers.ValidationError("This field is read-only.")
        return value

    def validate_modifier(self, value):
        """
        Check that the modifier is `None` -- the user should not be passing this value.
        """
        if value is not None:
            raise serializers.ValidationError("This field is read-only.")
        return value

    def validate_modified_date(self, value):
        """
        Check that the modified_date is `None` -- the user should not be passing this value.
        """
        if value is not None:
            raise serializers.ValidationError("This field is read-only.")
        return value

    def create(self, validated_data):
        # Get the request from the serializer context
        request = self.context.get("request")

        # Get the user from the request
        if not request.user.is_authenticated:
            raise serializers.ValidationError("User must be authenticated to create a new record.")

        # Set the uploader and modifier fields
        validated_data["uploader"] = request.user
        validated_data["modifier"] = request.user

        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Get the request from the serializer context
        request = self.context.get("request")

        # Get the user from the request
        if not request.user.is_authenticated:
            raise serializers.ValidationError("User must be authenticated to create a new record.")

        # Set the modifier field
        validated_data["modifier"] = request.user

        # Set the modified_date field
        validated_data["modified_date"] = timezone.now()

        return super().update(instance, validated_data)
