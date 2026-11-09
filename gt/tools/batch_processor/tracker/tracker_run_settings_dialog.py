"""Non-modal dialog that changes run settings of an active tracker run."""

import gt.ui.qt_import as ui_qt
import gt.ui.resource_library as ui_res_lib

from gt.tools.batch_processor import batch_processor_run_settings as run_settings


def build_spin_box_stylesheet():
    """Builds the dark tracker-themed stylesheet for spin boxes.

    Returns:
        str: Stylesheet text for QSpinBox widgets.
    """
    arrow_up = ui_res_lib.Icon.ui_arrow_up.replace("\\", "/")
    arrow_down = ui_res_lib.Icon.ui_arrow_down.replace("\\", "/")
    return (
        "QSpinBox { background-color: #202020; color: #e6e6e6; border: 1px solid #484848;"
        " border-radius: 3px; padding: 2px 4px 2px 7px; selection-background-color: #55788a;"
        " selection-color: #ffffff; }"
        "QSpinBox:hover { border-color: #65747c; }"
        "QSpinBox:focus { border-color: #66899a; }"
        "QSpinBox:disabled { background-color: #292929; color: #808080; border-color: #3a3a3a; }"
        "QSpinBox::up-button, QSpinBox::down-button { subcontrol-origin: border; width: 16px;"
        " background-color: #363636; border: none; border-left: 1px solid #484848; }"
        "QSpinBox::up-button { subcontrol-position: top right; border-top-right-radius: 3px; }"
        "QSpinBox::down-button { subcontrol-position: bottom right; border-bottom-right-radius: 3px;"
        " border-top: 1px solid #484848; }"
        "QSpinBox::up-button:hover, QSpinBox::down-button:hover { background-color: #465158; }"
        "QSpinBox::up-button:pressed, QSpinBox::down-button:pressed { background-color: #55788a; }"
        f"QSpinBox::up-arrow {{ image: url({arrow_up}); width: 8px; height: 8px; }}"
        f"QSpinBox::down-arrow {{ image: url({arrow_down}); width: 8px; height: 8px; }}"
    )


def build_dialog_stylesheet():
    """Builds the dark tracker-themed stylesheet for the run settings dialog.

    Returns:
        str: Stylesheet text for the dialog and its children.
    """
    return (
        "QDialog { background-color: #292929; }"
        "QLabel { background: transparent; color: #e6e6e6; }"
        "QLabel#runSettingsNote { color: #9a9a9a; }"
        "QToolTip { background-color: #444444; color: #e6e6e6; border: 1px solid #5a5a5a; }"
        "QPushButton { background-color: #363636; color: #e6e6e6; border: 1px solid #4a4a4a;"
        " border-radius: 3px; padding: 5px 14px; }"
        "QPushButton:hover { background-color: #465158; border-color: #65747c; }"
        "QPushButton:pressed { background-color: #55788a; border-color: #7395a5; color: #ffffff; }"
        "QPushButton:disabled { background-color: #2d2d2d; color: #808080; border-color: #3a3a3a; }"
    ) + build_spin_box_stylesheet()


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
        self.note_label.setObjectName("runSettingsNote")
        self.setStyleSheet(build_dialog_stylesheet())
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
