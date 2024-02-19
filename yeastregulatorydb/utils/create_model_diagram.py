import json

from django.db.models import ForeignKey, ManyToManyField, Model, OneToOneField


def serialize_model_metadata(model: Model) -> str:
    """
    Serialize the metadata of a Django model

    :param model: The Django model
    :type model: Model

    :return: The serialized metadata
    :rtype: str
    """
    metadata = {"model_name": model.__name__, "fields": [], "relationships": []}

    for field in model._meta.get_fields():
        if field.is_relation:
            rel_type = (
                "ForeignKey"
                if isinstance(field, ForeignKey)
                else (
                    "OneToOneField"
                    if isinstance(field, OneToOneField)
                    else "ManyToManyField"
                    if isinstance(field, ManyToManyField)
                    else "UnknownRelation"
                )
            )
            metadata["relationships"].append(
                {"name": field.name, "related_model": field.related_model.__name__, "type": rel_type}
            )
        else:
            metadata["fields"].append({"name": field.name, "type": field.get_internal_type()})

    return json.dumps(metadata, indent=2)


def create_uml_svg_from_metadata(metadata_json: str) -> str:
    """
    Create a UML diagram in SVG format from the serialized model metadata

    :param metadata_json: The serialized model metadata
    :type metadata_json: str

    :return: The SVG content
    :rtype: str
    """
    metadata = json.loads(metadata_json)

    svg_start = '<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">'
    svg_end = "</svg>"
    text_template = '<text x="{x}" y="{y}" font-family="Arial" font-size="14" fill="black">{text}</text>'
    rect_template = (
        '<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{fill}" stroke="black" stroke-width="1"/>'
    )

    svg_content = ""
    x, y = 10, 20
    char_width = 8  # Approximate width of each character in pixels
    line_height = 20
    padding = 10  # Padding for text inside rectangles

    # Calculate max width based on the longest field name or relationship text
    max_text_length = len(metadata["model_name"]) * char_width
    for field in metadata["fields"]:
        field_text = f"{field['name']} ({field['type']})"
        max_text_length = max(max_text_length, len(field_text) * char_width)
    for rel in metadata["relationships"]:
        rel_text = f"{rel['name']} -> {rel['related_model']} ({rel['type']})"
        max_text_length = max(max_text_length, len(rel_text) * char_width)

    max_width = max_text_length + (2 * padding)  # Add padding to both sides

    # Model name
    svg_content += rect_template.format(x=x, y=y, width=max_width, height=line_height, fill="lightgrey")
    svg_content += text_template.format(x=x + padding, y=y + 15, text=metadata["model_name"])
    y += line_height

    # Fields
    for field in metadata["fields"]:
        y += line_height
        field_text = f"{field['name']} ({field['type']})"
        svg_content += rect_template.format(x=x, y=y, width=max_width, height=line_height, fill="white")
        svg_content += text_template.format(x=x + padding, y=y + 15, text=field_text)

    # Relationships
    y += line_height  # Extra space before relationships
    for rel in metadata["relationships"]:
        y += line_height
        rel_text = f"{rel['name']} -> {rel['related_model']} ({rel['type']})"
        svg_content += rect_template.format(x=x, y=y, width=max_width, height=line_height, fill="white")
        svg_content += text_template.format(x=x + padding, y=y + 15, text=rel_text)

    svg_height = y + 30  # Add some padding at the bottom

    svg = svg_start.format(width=max_width + 20, height=svg_height) + svg_content + svg_end

    return svg


def create_model_diagram(model: Model) -> tuple[str, str]:
    """
    Create a UML diagram in SVG format from a Django model

    :param model: The Django model
    :type model: Model

    :return: The serialized metadata and the SVG content
    :rtype: Tuple[str, str]
    """
    metadata = serialize_model_metadata(model)
    svg = create_uml_svg_from_metadata(metadata)
    return metadata, svg
