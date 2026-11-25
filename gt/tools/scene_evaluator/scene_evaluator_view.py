"""Qt windows for Scene Evaluator, validator selection and preferences."""

from pathlib import Path

from gt.tools.scene_evaluator.scene_evaluator_model import (
    ACTION_ALWAYS_ALLOW,
    ACTION_CONFIRM_BYPASS,
    ACTION_REQUIRE_PASS,
    DEFAULT_SETTINGS,
)
from gt.ui import qt_import as ui_qt
from gt.ui import qt_utils
from gt.ui import resource_library
from gt.ui.line_text_widget import LineTextWidget
from gt.ui.syntax_highlighter import PythonSyntaxHighlighter
from gt.ui.validator_widget import ValidatorWidget


CHECKBOX_STYLESHEET = f"""
QCheckBox::indicator, QGroupBox::indicator, QListView::indicator {{
    width: 13px;
    height: 13px;
    border: 1px solid #686868;
    border-radius: 3px;
    background-color: #373737;
}}
QCheckBox::indicator:checked, QGroupBox::indicator:checked, QListView::indicator:checked {{
    image: url("{Path(resource_library.Icon.ui_checkmark_muted).as_posix()}");
    background-color: #484848;
    border-color: #858585;
}}
"""


class ToolbarStatusLabel(ui_qt.QtWidgets.QLabel):
    """Draws a centered status message within the space available in the toolbar."""

    def minimumSizeHint(self):
        """Reserves space for a short message at the current font size.

        Returns:
            QSize: Minimum toolbar status size in logical pixels.
        """
        metrics = self.fontMetrics()
        return ui_qt.QtCore.QSize(metrics.horizontalAdvance("0") * 18, metrics.height())

    def paintEvent(self, event):
        """Paints a single line and elides long status text.

        Args:
            event (QPaintEvent): Qt paint event.
        """
        if not self.text():
            return
        text_area = self.contentsRect()
        message = self.fontMetrics().elidedText(self.text(), ui_qt.QtCore.Qt.ElideRight, text_area.width())
        painter = ui_qt.QtGui.QPainter(self)
        painter.setPen(ui_qt.QtGui.QColor("#9D9D9D"))
        painter.drawText(text_area, ui_qt.QtCore.Qt.AlignCenter, message)


class SceneEvaluatorView(metaclass=qt_utils.MayaWindowMeta):
    """Displays the shared validation UI and tool controls."""

    STATUS_DURATION_MS = 4000

    def __init__(self, parent=None, version=None):
        """Builds the main window.

        Args:
            parent (QWidget, optional): Maya's main window.
            version (str, optional): Tool version to include in the title.
        """
        super().__init__(parent=parent)
        self.setWindowTitle(f"Scene Evaluator (v{version})" if version else "Scene Evaluator")
        self.setWindowIcon(ui_qt.QtGui.QIcon(resource_library.Icon.tool_scene_evaluator))
        self.setStyleSheet(resource_library.Stylesheet.maya_dialog_base)
        self.resize(680, 470)

        self.edit_validators_button = ui_qt.QtWidgets.QPushButton("Edit Validators")
        self.preferences_button = ui_qt.QtWidgets.QPushButton("Preferences")
        self.validator_widget = ValidatorWidget(validators=[], parent=self)
        self.validator_widget.layout().setContentsMargins(0, 0, 0, 0)
        self.validator_widget.splitter_validator_results.setSizes([280, 380])
        toolbar = ui_qt.QtWidgets.QHBoxLayout()
        self.validator_widget.add_scope_selection_ui(layout=toolbar)
        self.validator_widget.scope_group.setStyleSheet(
            resource_library.Stylesheet.btn_radio_base
            + """
QRadioButton { padding: 0px 4px 0px 0px; }
QRadioButton::indicator:checked { background-color: #929292; border-color: #707070; }
"""
        )

        self.status_label = ToolbarStatusLabel()
        self.status_label.setTextFormat(ui_qt.QtCore.Qt.PlainText)
        self.status_label.setSizePolicy(ui_qt.QtWidgets.QSizePolicy.Expanding, ui_qt.QtWidgets.QSizePolicy.Preferred)
        self.status_timer = ui_qt.QtCore.QTimer(self)
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(self.clear_status)
        toolbar.addWidget(self.status_label, 1)
        toolbar.addWidget(self.edit_validators_button)
        toolbar.addWidget(self.preferences_button)

        self.action_button = ui_qt.QtWidgets.QPushButton()
        self.action_button.hide()
        self.validator_widget.get_main_buttons_layout().addWidget(self.action_button)

        layout = ui_qt.QtWidgets.QVBoxLayout(self)
        layout.addLayout(toolbar)
        layout.addWidget(self.validator_widget, 1)

    def set_status(self, message):
        """Temporarily displays a message in the center of the toolbar.

        Args:
            message (str): Status text. An empty string hides the status row.
        """
        self.status_timer.stop()
        self.status_label.setText(message)
        self.status_label.setToolTip(message)
        if message:
            self.status_timer.start(self.STATUS_DURATION_MS)

    def clear_status(self):
        """Clears the current toolbar message."""
        self.set_status("")

    def confirm_validation_bypass(self, issue, action_label):
        """Asks whether to proceed with an action despite an unmet validation requirement.

        Args:
            issue (str): Reason validation could not pass.
            action_label (str): Label of the action the user requested.

        Returns:
            bool: Whether the user explicitly chose to run the action.
        """
        dialog = ui_qt.QtWidgets.QMessageBox(self)
        dialog.setWindowTitle("Bypass Validation")
        dialog.setIcon(ui_qt.QtWidgets.QMessageBox.Warning)
        dialog.setTextFormat(ui_qt.QtCore.Qt.PlainText)
        dialog.setText(issue)
        dialog.setInformativeText(f'Run "{action_label}" anyway?')
        run_button = dialog.addButton("Run Anyway", ui_qt.QtWidgets.QMessageBox.AcceptRole)
        cancel_button = dialog.addButton(ui_qt.QtLib.StandardButton.Cancel)
        dialog.setDefaultButton(cancel_button)
        dialog.setEscapeButton(cancel_button)
        try:
            dialog.exec_()
            return dialog.clickedButton() == run_button
        finally:
            dialog.deleteLater()


class ValidatorSelectionDialog(ui_qt.QtWidgets.QDialog):
    """Lets a user choose which checks appear in the main window."""

    def __init__(self, validators, selected_ids, parent=None):
        """Creates a checkable list of validators.

        Args:
            validators (list[tuple]): Validator IDs, display names and descriptions.
            selected_ids (list[str]): IDs that should initially be checked.
            parent (QWidget, optional): Scene Evaluator window.
        """
        super().__init__(parent)
        self.setWindowTitle("Edit Validators")
        self.setStyleSheet(CHECKBOX_STYLESHEET)
        self.resize(390, 460)
        self.search_field = ui_qt.QtWidgets.QLineEdit()
        self.search_field.setPlaceholderText("Search validators by name")
        self.search_field.setClearButtonEnabled(True)
        self.validator_list = ui_qt.QtWidgets.QListWidget()
        self.validator_list.setAlternatingRowColors(True)
        for validator_id, name, description in validators:
            item = ui_qt.QtWidgets.QListWidgetItem(name, self.validator_list)
            item.setData(ui_qt.QtLib.ItemDataRole.UserRole, validator_id)
            item.setToolTip(description)
            item.setFlags(item.flags() | ui_qt.QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(ui_qt.QtCore.Qt.Checked if validator_id in selected_ids else ui_qt.QtCore.Qt.Unchecked)
        self.search_field.textChanged.connect(self.filter_validators)

        buttons = ui_qt.QtWidgets.QDialogButtonBox(
            ui_qt.QtWidgets.QDialogButtonBox.Ok | ui_qt.QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = ui_qt.QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.search_field)
        layout.addWidget(self.validator_list, 1)
        layout.addWidget(buttons)
        self.search_field.setFocus()

    def filter_validators(self, search_text):
        """Shows matching validator names while preserving all check states.

        Args:
            search_text (str): Case-insensitive substring to match.
        """
        search_text = search_text.strip().casefold()
        for index in range(self.validator_list.count()):
            item = self.validator_list.item(index)
            item.setHidden(search_text not in item.text().casefold())

    def selected_validator_ids(self):
        """Collects the checked validator IDs.

        Returns:
            list[str]: IDs of the selected validators.
        """
        items = (self.validator_list.item(index) for index in range(self.validator_list.count()))
        return [
            item.data(ui_qt.QtLib.ItemDataRole.UserRole)
            for item in items
            if item.checkState() == ui_qt.QtCore.Qt.Checked
        ]


class SceneEvaluatorPreferencesDialog(ui_qt.QtWidgets.QDialog):
    """Edits the action button and stages portable presets."""

    def __init__(self, settings, parent=None):
        """Builds the preference controls and loads the current settings.

        Args:
            settings (dict): Current validator choices and action settings.
            parent (QWidget, optional): Scene Evaluator window.
        """
        super().__init__(parent)
        self.setWindowTitle("Scene Evaluator Preferences")
        self.setStyleSheet(CHECKBOX_STYLESHEET)
        self.resize(610, 445)
        self.action_group = ui_qt.QtWidgets.QGroupBox("Show Action Button")
        self.action_group.setCheckable(True)
        self.action_label = ui_qt.QtWidgets.QLineEdit()
        self.action_label.setPlaceholderText("Export Scene")
        self.action_mode = ui_qt.QtWidgets.QComboBox()
        self.action_mode.addItem("Only when all checks pass", ACTION_REQUIRE_PASS)
        self.action_mode.addItem("Allow with bypass confirmation", ACTION_CONFIRM_BYPASS)
        self.action_mode.addItem("Always allow", ACTION_ALWAYS_ALLOW)
        self.action_mode.setSizeAdjustPolicy(ui_qt.QtWidgets.QComboBox.AdjustToContents)
        self.action_mode.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        self.action_mode.setToolTip("The first two modes recheck the current scope before running the action.")

        editor = LineTextWidget(parent=self)
        self.script_editor = editor.get_text_edit()
        self.script_editor.setPlaceholderText("Python to run when the action button is clicked")
        self.script_editor.setToolTip("Use cmds for Maya commands and validation_scope for 'scene' or 'selection'.")
        self.highlighter = PythonSyntaxHighlighter(self.script_editor.document())
        action_layout = ui_qt.QtWidgets.QFormLayout(self.action_group)
        action_layout.setFieldGrowthPolicy(ui_qt.QtWidgets.QFormLayout.ExpandingFieldsGrow)
        action_layout.addRow("Button Label", self.action_label)
        action_layout.addRow("Action Behavior", self.action_mode)
        action_layout.addRow("Python Script", editor)

        self.import_button = ui_qt.QtWidgets.QPushButton("Import Preset")
        self.export_button = ui_qt.QtWidgets.QPushButton("Export Preset")
        self.include_validators = ui_qt.QtWidgets.QCheckBox("Include validator selection")
        self.include_validators.setChecked(True)
        self.include_validators.setToolTip("Include the selected validators when importing or exporting a preset.")
        self.reset_button = ui_qt.QtWidgets.QPushButton("Reset Preset")
        self.reset_button.setToolTip("Restore the default action settings and clear the validator selection.")
        self.reset_button.clicked.connect(self.reset_settings)

        preset_layout = ui_qt.QtWidgets.QHBoxLayout()
        preset_layout.addWidget(self.import_button)
        preset_layout.addWidget(self.export_button)
        preset_layout.addWidget(self.include_validators)
        preset_layout.addStretch()
        preset_layout.addWidget(self.reset_button)

        self.buttons = ui_qt.QtWidgets.QDialogButtonBox(
            ui_qt.QtWidgets.QDialogButtonBox.Save | ui_qt.QtWidgets.QDialogButtonBox.Cancel
        )
        self.buttons.rejected.connect(self.reject)

        self.status_label = ui_qt.QtWidgets.QLabel()
        self.status_label.setTextFormat(ui_qt.QtCore.Qt.PlainText)
        self.status_label.setWordWrap(True)
        self.status_label.hide()
        footer_layout = ui_qt.QtWidgets.QHBoxLayout()
        footer_layout.addWidget(self.status_label, 1)
        footer_layout.addWidget(self.buttons, 0, ui_qt.QtCore.Qt.AlignRight | ui_qt.QtCore.Qt.AlignVCenter)

        layout = ui_qt.QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.action_group, 1)
        layout.addLayout(preset_layout)
        layout.addLayout(footer_layout)
        self.load_settings(settings)

    def reset_settings(self):
        """Stages the default action settings and empty validator selection."""
        self.load_settings(DEFAULT_SETTINGS)
        self.include_validators.setChecked(True)
        self.set_status("Defaults loaded. Click Save to reset the action settings and validator selection.")

    def load_settings(self, settings):
        """Replaces the draft with current preferences or an imported preset.

        Args:
            settings (dict): Validated validator choices and action settings.
        """
        self.draft_settings = settings
        self.action_group.setChecked(settings["action"]["enabled"])
        self.action_label.setText(settings["action"]["label"])
        self.action_mode.setCurrentIndex(self.action_mode.findData(settings["action"]["mode"]))
        self.script_editor.setPlainText(settings["action"]["script"])

    def get_settings(self):
        """Collects current controls and staged validator choices.

        Returns:
            dict: Draft settings to save or export.
        """
        return {
            **self.draft_settings,
            "action": {
                "enabled": self.action_group.isChecked(),
                "label": self.action_label.text(),
                "script": self.script_editor.toPlainText(),
                "mode": self.action_mode.currentData(),
            },
        }

    def set_status(self, message):
        """Displays the result of a preset or preference operation.

        Args:
            message (str): Status text displayed in the dialog.
        """
        self.status_label.setText(message)
        self.status_label.setVisible(bool(message))
