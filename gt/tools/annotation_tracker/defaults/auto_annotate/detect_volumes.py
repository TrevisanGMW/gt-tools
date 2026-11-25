"""Adds selected Maya transforms to the active range's interaction volumes."""

from gt.tools.annotation_tracker import annotation_tracker_model

ANNOTATION_TRACKER_DISPLAY = {
    "label": "Detect Interaction Volumes",
    "button_color": "#414D49",
}


def run(tracker):
    """Records selected transforms in the string field attached to this script.

    Args:
        tracker (dict): Automation context supplied by the tracker.
    """
    cmds = tracker["cmds"]
    if tracker.get("field_section") == "file_level":
        cmds.warning("Detect Volumes requires a frame-range string field.")
        return
    active_range = tracker["active_range"]
    if not active_range or active_range.locked:
        cmds.warning("Select an unlocked range to record interaction volumes.")
        return
    field_name = annotation_tracker_model.get_range_automation_field(
        tracker["schema"], "detect_volumes.py", "interaction_volumes", tracker.get("field_name")
    )
    if not field_name:
        cmds.warning("The active schema has no string field for interaction volumes.")
        return
    transforms = cmds.ls(selection=True, long=True, type="transform") or []
    if not transforms:
        cmds.warning("Select the interaction volume transforms in Maya.")
        return
    current_value = active_range.custom_data.get(field_name) or ""
    volumes = [name.strip() for name in str(current_value).split(",") if name.strip()]
    tracker["update_range_data"](field_name, ", ".join(dict.fromkeys(volumes + transforms)))


run(context)
