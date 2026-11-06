"""Non-modal dialog that changes run settings of an active tracker run."""

import gt.ui.qt_import as ui_qt

from gt.tools.batch_processor import batch_processor_run_settings as run_settings


DIALOG_ROWS = (
    (
        run_settings.WORKER_COUNT,
        "Max Workers",
        1,
        run_settings.MAX_WORKER_COUNT,
        "Maximum concurrent workers. Lowering it never stops running jobs;\n"
        "new jobs wait until enough workers finish.",
    ),
    (
        run_settings.MAX_RETRIES,
        "Retries",
        0,
        run_settings.MAX_RETRY_COUNT,
        "Times a failed job is retried. 0 disables retries.",
    ),
    (
        run_settings.TIMEOUT_MINUTES,
        "Timeout (min)",
        0,
        run_settings.MAX_TIMEOUT_MINUTES,
        "Minutes a job may run before it is canceled. 0 disables the timeout.\n"
        "Applies to jobs launched after the change; running jobs keep their timeout.",
    ),
)


class TrackerRunSettingsDialog(ui_qt.QtWidgets.QDialog):
    """Edits the live worker limit, retries, and timeout of a run."""

    def __init__(self, apply_callback, parent=None):
        """Creates the dialog.

        Args:
            apply_callback (callable): Receives a dict of changed run settings.
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)
        self.apply_callback = apply_callback
        self.spin_boxes = {}
        self.setWindowTitle("Adjust Run Settings")
        self.setModal(False)
        layout = ui_qt.QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        form_layout = ui_qt.QtWidgets.QFormLayout()
        form_layout.setLabelAlignment(ui_qt.QtLib.AlignmentFlag.AlignRight | ui_qt.QtLib.AlignmentFlag.AlignVCenter)
        for setting_key, label_text, minimum, maximum, tooltip in DIALOG_ROWS:
            spin_box = ui_qt.QtWidgets.QSpinBox()
            spin_box.setRange(minimum, maximum)
            spin_box.setMinimumHeight(28)
            spin_box.setMinimumWidth(110)
            spin_box.setToolTip(tooltip)
            label = ui_qt.QtWidgets.QLabel(f"{label_text}:")
            label.setToolTip(tooltip)
            form_layout.addRow(label, spin_box)
            self.spin_boxes[setting_key] = spin_box
        layout.addLayout(form_layout)
        self.note_label = ui_qt.QtWidgets.QLabel(
            "Changes apply right away. Later \"Settings Override\" tasks may overwrite them unless "
            "Preferences > Keep Manual Run Setting Changes is on."
        )
        self.note_label.setWordWrap(True)
        self.note_label.setStyleSheet("color: grey;")
        layout.addWidget(self.note_label)
        button_layout = ui_qt.QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        self.apply_button = ui_qt.QtWidgets.QPushButton("Apply")
        self.apply_button.setToolTip("Apply the values above to the running batch.")
        self.apply_button.clicked.connect(lambda *args: self.apply_changes())
        self.close_button = ui_qt.QtWidgets.QPushButton("Close")
        self.close_button.clicked.connect(lambda *args: self.close())
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)
        self.resize(340, self.sizeHint().height())

    def set_values(self, values):
        """Loads current run settings into the spin boxes.

        Args:
            values (dict): Run settings keyed by run setting key.
        """
        for setting_key, spin_box in self.spin_boxes.items():
            spin_box.blockSignals(True)
            spin_box.setValue(int(values.get(setting_key) or 0))
            spin_box.blockSignals(False)

    def get_values(self):
        """Reads the spin box values.

        Returns:
            dict: Run settings keyed by run setting key.
        """
        return {setting_key: spin_box.value() for setting_key, spin_box in self.spin_boxes.items()}

    def apply_changes(self):
        """Sends the current values to the apply callback."""
        if callable(self.apply_callback):
            self.apply_callback(self.get_values())

    def set_editable(self, editable):
        """Enables or disables editing, for example after the run finishes.

        Args:
            editable (bool): Whether values can still be applied.
        """
        for spin_box in self.spin_boxes.values():
            spin_box.setEnabled(bool(editable))
        self.apply_button.setEnabled(bool(editable))
