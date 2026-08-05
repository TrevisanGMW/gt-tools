"""Compatibility functions for the MVC Add Offset Transform tool."""

from gt.tools.add_offset_transform.add_offset_transform_model import AddOffsetTransformModel

script_name = "Add Offset Transform"
script_version = "?.?.?"
settings = {"outliner_color": [0.5, 1.0, 0.4]}


def build_gui_add_offset_transform():
    """Launches the Add Offset Transform MVC interface."""
    from gt.tools.add_offset_transform import launch_tool

    return launch_tool()


def create_inbetween(layer_tag, parent_type, layer_type):
    """Creates offsets through the former public function.

    Args:
        layer_tag (str): Offset suffix.
        parent_type (str): Legacy pivot source, Parent or Selection.
        layer_type (str): Group, Joint, or Locator.

    Returns:
        list: Created offset nodes.
    """
    model = AddOffsetTransformModel()
    model.settings.update({
        "transform_suffix": str(layer_tag or "").strip().strip("_"),
        "pivot_source": parent_type,
        "transform_type": layer_type,
        "outliner_color": list(settings.get("outliner_color")),
    })
    return model.create_offsets()


def parse_text_field(text_field_data):
    """Parses the former comma-separated text field format.

    Args:
        text_field_data (str): Field text.

    Returns:
        list: Clean values.
    """
    return [item.strip() for item in str(text_field_data or "").split(",") if item.strip()]


if __name__ == "__main__":
    build_gui_add_offset_transform()
