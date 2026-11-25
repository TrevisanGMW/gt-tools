"""Adds an event to the active range using the current schema."""

import json
import math

from gt.tools.annotation_tracker import annotation_tracker_model
from gt.ui.qt_import import QtWidgets

ANNOTATION_TRACKER_DISPLAY = {
    "label": "Record Event",
    "button_color": "#4E4753",
}


def run(tracker):
    """Prompts for a new event and merges it into the schema's event field.

    Args:
        tracker (dict): Automation context supplied by the tracker.
    """
    cmds = tracker["cmds"]
    if tracker.get("field_section") == "file_level":
        cmds.warning("Event Recorder requires a frame-range string field.")
        return
    active_range = tracker["active_range"]
    if not active_range or active_range.locked:
        cmds.warning("Select an unlocked range to record an event.")
        return
    field_name = annotation_tracker_model.get_range_automation_field(
        tracker["schema"], "event_recorder.py", "event", tracker.get("field_name")
    )
    if not field_name:
        cmds.warning("The active schema has no string field for recording events.")
        return
    try:
        events = json.loads(active_range.custom_data.get(field_name) or "{}")
    except (TypeError, ValueError):
        events = None
    if not isinstance(events, dict):
        cmds.warning("The range's event field must contain a JSON object before adding events.")
        return

    first_frame = math.ceil(active_range.start)
    last_frame = math.floor(active_range.end)
    if first_frame > last_frame:
        cmds.warning("The selected range contains no whole frames.")
        return
    current_frame = min(max(int(cmds.currentTime(query=True)), first_frame), last_frame)
    dialog = QtWidgets.QDialog(tracker.get("parent"))
    dialog.setWindowTitle("Record Event")
    layout = QtWidgets.QFormLayout(dialog)
    name_field = QtWidgets.QLineEdit()
    start_field = QtWidgets.QSpinBox()
    end_field = QtWidgets.QSpinBox()
    for field in (start_field, end_field):
        field.setRange(first_frame, last_frame)
    start_field.setValue(current_frame)
    end_field.setValue(min(current_frame + 10, last_frame))
    start_field.valueChanged.connect(end_field.setMinimum)
    end_field.setMinimum(current_frame)
    layout.addRow("Event Name:", name_field)
    layout.addRow("Start Frame:", start_field)
    layout.addRow("End Frame:", end_field)
    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
    )
    accept_button = buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
    accept_button.setEnabled(False)
    name_field.textChanged.connect(
        lambda text: accept_button.setEnabled(bool(text.strip()) and text.strip() not in events)
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)
    if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        events[name_field.text().strip()] = {"start_frame": start_field.value(), "end_frame": end_field.value()}
        tracker["update_range_data"](field_name, json.dumps(events, ensure_ascii=False))


run(context)
