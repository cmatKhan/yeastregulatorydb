from rest_framework import serializers

from ...models.FileFormat import FileFormat
from .mixins.CustomValidateMixin import CustomValidateMixin


class FileFormatSerializer(CustomValidateMixin, serializers.ModelSerializer):
    uploader = serializers.ReadOnlyField(source="uploader.username")
    modifier = serializers.CharField(source="uploader.username", required=False)
    # allowed to be null because if it is `None` it will be set to "none" in
    # the vlaidate methods below. If this key isn't passed at all, there is a
    # default value of "none" in the model.
    effect_col = serializers.CharField(allow_null=True)
    pval_col = serializers.CharField(allow_null=True)

    class Meta:
        model = FileFormat
        fields = "__all__"

    def validate_effect_col(self, value):
        if value is None:
            return "none"
        return value

    def validate_pval_col(self, value):
        if value is None:
            return "none"
        return value

    def validate_fields(self, value):
        valid_types = ["str", "int", "float"]
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                {
                    "fileformat": "FileFormat field `fields` must be a dictionary "
                    "(which it will be if a valid json is passed. You may need to "
                    "check your JSON if this is a PUT or UPDATE)."
                }
            )
        for key, val in value.items():
            if isinstance(val, list):
                continue
            if val not in valid_types:
                raise serializers.ValidationError(
                    {
                        "fields": f"Invalid datatype for field '{key}': '{val}'. "
                        "Field types must be one of {valid_types} or a list."
                    }
                )
        return value

    @property
    def fields_as_types(self):
        fields_dict = self.to_representation(self.instance)["fields"]
        for key, value in fields_dict.items():
            if value == "str":
                fields_dict[key] = str
            elif value == "int":
                fields_dict[key] = int
            elif value == "float":
                fields_dict[key] = float
        return fields_dict

    # def to_representation(self, instance):
    #     out = super().to_representation(instance)
    #     fields_dict = out["fields"]
    #     for key, value in fields_dict.items():
    #         if value == "str":
    #             fields_dict[key] = str
    #         elif value == "int":
    #             fields_dict[key] = int
    #         elif value == "float":
    #             fields_dict[key] = float
    #     out["fields"] = fields_dict
    #     return out
