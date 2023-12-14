from django.forms.models import model_to_dict


def model_to_dict_select(factory_instance):
    """
    Take a factory instance and transform it to a dict. Remove the
    automatically generated fields that are not required for the
    serializer, `id`, `uploader`, and `modifier`.
    """
    dict = model_to_dict(factory_instance)
    [dict.pop(key) for key in {"id", "uploader", "modifier"}]
    return dict
