"""Records an event entry for the active Annotation Tracker range."""

import json

import gt.ui.qt_import as ui_qt


QtWidgets = ui_qt.QtWidgets
current_frame = int(context["cmds"].currentTime(query=True))

dialog = QtWidgets.QDialog()
dialog.setWindowTitle("Record Event")
dialog_layout = QtWidgets.QFormLayout(dialog)

event_name_field = QtWidgets.QLineEdit()
start_frame_field = QtWidgets.QSpinBox()
end_frame_field = QtWidgets.QSpinBox()
for frame_field in (start_frame_field, end_frame_field):
    frame_field.setRange(-100000, 100000)
start_frame_field.setValue(current_frame)
end_frame_field.setValue(current_frame + 10)

dialog_layout.addRow("Event Name:", event_name_field)
dialog_layout.addRow("Start Frame:", start_frame_field)
dialog_layout.addRow("End Frame:", end_frame_field)

buttons = QtWidgets.QDialogButtonBox(
    QtWidgets.QDialogButtonBox.StandardButton.Ok
    | QtWidgets.QDialogButtonBox.StandardButton.Cancel
)
buttons.accepted.connect(dialog.accept)
buttons.rejected.connect(dialog.reject)
dialog_layout.addRow(buttons)

if dialog.exec() == QtWidgets.QDialog.Accepted:
    event_name = event_name_field.text().strip()
    if event_name:
        event_data = {
            event_name: {
                "start_frame": start_frame_field.value(),
                "end_frame": end_frame_field.value(),
            }
        }
        context["update_range_data"]("event", json.dumps(event_data))
    else:
        context["cmds"].warning("An event name is required.")
