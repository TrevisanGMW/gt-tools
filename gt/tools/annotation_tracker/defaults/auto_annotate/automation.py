"""Fills missing schema defaults and creates a range for an empty timeline."""

import os

from gt.tools.annotation_tracker import annotation_tracker_model

ANNOTATION_TRACKER_DISPLAY = {
    "label": "Fill Schema Defaults",
    "button_color": "#424D57",
}


def fill_defaults(fields, get_value, update_value, scene_name=""):
    """Applies explicit schema defaults to fields with no annotation.

    Args:
        fields (list): Flattened fields for the current metadata section.
        get_value (callable): Reads a field value by name.
        update_value (callable): Writes a field value by name.
        scene_name (str, optional): Source name for file-level metadata.
    """
    for field in fields:
        name = field.get("name")
        if not name or get_value(name) not in (None, ""):
            continue
        value = field.get("default")
        field_type = field.get("type")
        if name == "source" and field_type == "string" and value in (None, ""):
            value = scene_name
        if value in (None, "") or field_type not in ("string", "boolean", "integer", "enum"):
            continue
        if field_type == "enum" and value not in field.get("options", []):
            continue
        if field_type == "integer":
            value = annotation_tracker_model.coerce_schema_integer(value, field)
        update_value(name, value)


def run(tracker):
    """Applies defaults for the schema currently loaded in the tracker.

    Args:
        tracker (dict): Automation context supplied by the tracker.
    """
    schema = tracker["schema"]
    cmds = tracker["cmds"]
    scene_path = cmds.file(query=True, sceneName=True, shortName=True)
    scene_name = os.path.splitext(scene_path)[0]
    file_fields = annotation_tracker_model.flatten_schema_items(schema.get("file_level", []))
    fill_defaults(file_fields, tracker["get_file_data"], tracker["update_file_data"], scene_name)

    active_range = tracker["active_range"]
    range_fields = annotation_tracker_model.flatten_schema_items(schema.get("frame_range", []))
    if any(field.get("name") for field in range_fields) and not tracker["timeline_ranges"]:
        start = cmds.playbackOptions(query=True, minTime=True)
        end = cmds.playbackOptions(query=True, maxTime=True)
        active_range = tracker["create_range"]("Full Playback", start, end)
    if active_range and not active_range.locked:
        fill_defaults(range_fields, active_range.custom_data.get, tracker["update_range_data"])
    tracker["refresh_ui"]()


run(context)
