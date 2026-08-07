"""Qt view for Animation Label Tracker."""

import json
import os
import shutil

import gt.ui.qt_import as ui_qt
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_utils as qt_utils

from gt.tools.anim_label_tracker import label_tracker as legacy_tracker
from gt.tools.anim_label_tracker import label_tracker_model
from gt.tools.anim_label_tracker.label_tracker_schema_editor import SchemaEditorDialog


QtWidgets = ui_qt.QtWidgets
QtGui = ui_qt.QtGui


class AnimationLabelTrackerView(
    metaclass=qt_utils.MayaWindowMeta,
    base_inheritance=legacy_tracker.RangeToolWindow,
):
    """Builds the dockable tracker UI while retaining established interactions."""

    def __init__(self, model=None, parent=None):
        """Initializes the tracker view.

        Args:
            model (AnimationLabelTrackerModel, optional): Persistent tracker model.
            parent (QWidget, optional): Parent widget.
        """
        self.model = model or label_tracker_model.AnimationLabelTrackerModel()
        self.controller = None
        super().__init__(parent=parent)
        self._build_validation_tab()
        self._add_schema_editor_button()
        self._apply_button_icons()
        self._apply_model_preferences()
        self._connect_preference_persistence()
        self.highlight_validation()

    def _build_validation_tab(self):
        """Adds the full validation report tab."""
        self.tab_validation = QtWidgets.QWidget()
        validation_layout = QtWidgets.QVBoxLayout(self.tab_validation)
        self.validation_text = QtWidgets.QPlainTextEdit()
        self.validation_text.setReadOnly(True)
        self.validation_text.setPlaceholderText("Validation results will appear here.")
        validation_layout.addWidget(self.validation_text)
        preferences_index = self.tabs.indexOf(self.tab_prefs)
        if preferences_index >= 0:
            self.tabs.insertTab(preferences_index, self.tab_validation, "Validation")
        else:
            self.tabs.addTab(self.tab_validation, "Validation")

    def _add_schema_editor_button(self):
        """Adds an edit button to the Preferences schema path row."""
        self.btn_edit_schema = QtWidgets.QPushButton()
        self.btn_edit_schema.setToolTip("Edit schema")
        self.btn_edit_schema.clicked.connect(self.open_schema_editor)
        parent_widget = self.schema_path_fld.parentWidget()
        parent_layout = parent_widget.layout() if parent_widget else None
        if parent_layout:
            for index in range(parent_layout.count()):
                layout_item = parent_layout.itemAt(index)
                row_layout = layout_item.layout()
                if row_layout and row_layout.indexOf(self.schema_path_fld) >= 0:
                    row_layout.addWidget(self.btn_edit_schema)
                    return

    def _set_icon_button(self, button, icon_path, tooltip):
        """Sets a resource-library icon on a compact action button.

        Args:
            button (QPushButton): Button to update.
            icon_path (str): Resource-library icon path.
            tooltip (str): Button tooltip.
        """
        if not button:
            return
        button.setIcon(QtGui.QIcon(icon_path))
        button.setText("")
        button.setToolTip(tooltip)

    def _apply_button_icons(self):
        """Applies repository icons to existing tracker actions."""
        self._set_icon_button(self.btn_add_schema, ui_res_lib.Icon.ui_add, "Create sample schema")
        self._set_icon_button(self.btn_load_schema, ui_res_lib.Icon.ui_open, "Browse schema")
        self._set_icon_button(self.btn_add_auto, ui_res_lib.Icon.ui_add, "Create sample automation")
        self._set_icon_button(self.btn_load_auto, ui_res_lib.Icon.ui_open, "Browse automations")
        self._set_icon_button(self.delete_btn, ui_res_lib.Icon.ui_delete, "Delete range")
        self._set_icon_button(
            self.btn_select_node,
            ui_res_lib.Icon.ui_cursor,
            "Select scene data node",
        )
        active_range = getattr(self.timeline, "active_range", None)
        lock_icon = (
            ui_res_lib.Icon.ui_lock_closed
            if active_range and active_range.locked
            else ui_res_lib.Icon.ui_lock_open
        )
        self._set_icon_button(self.lock_btn, lock_icon, "Lock or unlock range")
        self._set_icon_button(self.color_btn, ui_res_lib.Icon.ui_cursor, "Set range color")

        for button in self.prefs_widget.findChildren(QtWidgets.QPushButton):
            if button is getattr(self, "btn_edit_schema", None):
                continue
            if button.toolTip() or button.text() != "Delete Node":
                continue
            self._set_icon_button(button, ui_res_lib.Icon.ui_delete, "Delete scene data node")

        if hasattr(self, "btn_edit_schema"):
            self._set_icon_button(self.btn_edit_schema, ui_res_lib.Icon.ui_edit, "Edit schema")

    def _apply_model_preferences(self):
        """Applies persisted preferences to the existing UI."""
        preferences = self.model.preferences
        widgets = {
            "schema_path": self.schema_path_fld,
            "automation_path": self.auto_path_fld,
            "magnet_enabled": self.chk_magnet,
            "snap_threshold": self.spin_magnet,
            "auto_crop": self.chk_auto_crop,
            "crop_tolerance": self.spin_crop_tolerance,
            "auto_stretch": self.chk_auto_stretch,
            "stretch_tolerance": self.spin_stretch_tolerance,
            "show_frames": self.chk_frames,
            "show_names": self.chk_names,
            "random_colors": self.chk_colors,
            "sync_time": self.chk_sync,
            "limit_bounds": self.chk_bounds,
            "razor_random_colors": self.chk_razor_colors,
            "run_all_automations": self.chk_run_all_auto,
            "show_validation_status": self.chk_val_status,
            "write_scene_node": self.chk_write_node,
        }
        for key, widget in widgets.items():
            value = preferences.get(key)
            widget.blockSignals(True)
            if isinstance(widget, QtWidgets.QLineEdit):
                widget.setText(str(value or ""))
            elif isinstance(widget, QtWidgets.QSpinBox):
                widget.setValue(int(value))
            elif isinstance(widget, QtWidgets.QCheckBox):
                widget.setChecked(bool(value))
            widget.blockSignals(False)

        self.timeline.magnet_enabled = bool(preferences.get("magnet_enabled", True))
        self.timeline.snap_threshold = int(preferences.get("snap_threshold", 10))
        self.timeline.auto_crop_enabled = bool(preferences.get("auto_crop", False))
        self.timeline.crop_tolerance = int(preferences.get("crop_tolerance", 10))
        self.timeline.auto_stretch_enabled = bool(preferences.get("auto_stretch", False))
        self.timeline.stretch_tolerance = int(preferences.get("stretch_tolerance", 10))
        self.timeline.pref_show_frames = bool(preferences.get("show_frames", True))
        self.timeline.pref_show_names = bool(preferences.get("show_names", False))
        self.timeline.pref_random_colors = bool(preferences.get("random_colors", True))
        self.timeline.pref_sync_time = bool(preferences.get("sync_time", True))
        self.timeline.pref_limit_bounds = bool(preferences.get("limit_bounds", True))
        self.timeline.pref_razor_random_colors = bool(
            preferences.get("razor_random_colors", True)
        )
        self.check_schema_path(rebuild=True)
        self.build_automations_ui()
        self.timeline.update()

    def _connect_preference_persistence(self):
        """Persists path, snapping, and display changes immediately."""
        for widget in (
            self.schema_path_fld,
            self.auto_path_fld,
            self.chk_magnet,
            self.spin_magnet,
            self.chk_auto_crop,
            self.spin_crop_tolerance,
            self.chk_auto_stretch,
            self.spin_stretch_tolerance,
            self.chk_frames,
            self.chk_names,
            self.chk_colors,
            self.chk_sync,
            self.chk_bounds,
            self.chk_razor_colors,
            self.chk_run_all_auto,
            self.chk_val_status,
            self.chk_write_node,
        ):
            if isinstance(widget, QtWidgets.QLineEdit):
                widget.textChanged.connect(self.save_preferences)
            elif isinstance(widget, QtWidgets.QSpinBox):
                widget.valueChanged.connect(self.save_preferences)
            else:
                widget.stateChanged.connect(self.save_preferences)

    def save_preferences(self, *args):
        """Captures current UI values in the persistent model."""
        self.model.update_preferences(
            {
                "schema_path": self.schema_path_fld.text().strip(),
                "automation_path": self.auto_path_fld.text().strip(),
                "magnet_enabled": self.chk_magnet.isChecked(),
                "snap_threshold": self.spin_magnet.value(),
                "auto_crop": self.chk_auto_crop.isChecked(),
                "crop_tolerance": self.spin_crop_tolerance.value(),
                "auto_stretch": self.chk_auto_stretch.isChecked(),
                "stretch_tolerance": self.spin_stretch_tolerance.value(),
                "show_frames": self.chk_frames.isChecked(),
                "show_names": self.chk_names.isChecked(),
                "random_colors": self.chk_colors.isChecked(),
                "sync_time": self.chk_sync.isChecked(),
                "limit_bounds": self.chk_bounds.isChecked(),
                "razor_random_colors": self.chk_razor_colors.isChecked(),
                "run_all_automations": self.chk_run_all_auto.isChecked(),
                "show_validation_status": self.chk_val_status.isChecked(),
                "write_scene_node": self.chk_write_node.isChecked(),
            }
        )

    def highlight_validation(self):
        """Updates the existing validation bar and full validation report."""
        super().highlight_validation()
        if not hasattr(self, "validation_text"):
            return
        start_frame = getattr(self.timeline, "start_frame", 0)
        end_frame = getattr(self.timeline, "end_frame", 0)
        errors = label_tracker_model.collect_validation_errors(
            self.schema,
            self.timeline.ranges,
            self.file_data,
            start_frame,
            end_frame,
        )
        if not self.schema:
            report = "No schema loaded."
        elif errors:
            report = self._format_validation_report(errors)
        else:
            report = "Validation Passed!\n\nNo issues were found."
        self.validation_text.setPlainText(report)

    def _format_validation_report(self, errors):
        """Formats validation issues into clearly separated sections.

        Args:
            errors (list): Flat validation error messages.

        Returns:
            str: Formatted validation report.
        """
        timeline_errors = []
        file_errors = []
        range_errors = {}
        for error in errors:
            if error.startswith("File "):
                file_errors.append(error)
            elif error.startswith("Range ") and "': " in error:
                range_name, _ = error.split("': ", 1)
                range_errors.setdefault(range_name + "'", []).append(error)
            else:
                timeline_errors.append(error)

        sections = []
        if timeline_errors:
            sections.append("Timeline\n{0}".format("\n".join(
                "- {0}".format(error) for error in timeline_errors
            )))
        if file_errors:
            sections.append("File Data\n{0}".format("\n".join(
                "- {0}".format(error) for error in file_errors
            )))
        for range_name, range_issue_list in range_errors.items():
            sections.append("{0}\n{1}".format(
                range_name,
                "\n".join("- {0}".format(error) for error in range_issue_list),
            ))

        return "Validation Issues ({0})\n\n{1}".format(
            len(errors),
            "\n\n".join(sections),
        )

    def open_schema_editor(self):
        """Opens the form and JSON schema editor and writes accepted changes."""
        dialog = SchemaEditorDialog(self.schema, parent=self)
        if dialog.exec() != QtWidgets.QDialog.Accepted:
            return
        path = self.schema_path_fld.text().strip()
        if not path:
            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Write Schema",
                "schema.json",
                "JSON Files (*.json)",
            )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as schema_file:
                json.dump(dialog.get_schema(), schema_file, indent=2, ensure_ascii=False)
            self.schema_path_fld.setText(path)
            self.check_schema_path(rebuild=True)
            self.status_bar.setText("Schema written: {0}".format(path))
        except (OSError, TypeError, ValueError) as error:
            QtWidgets.QMessageBox.warning(self, "Write Schema", str(error))

    def create_example_schema(self):
        """Writes the packaged sample schema to a user-selected path."""
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Example Schema",
            "schema.json",
            "JSON Files (*.json)",
        )
        if not path:
            return
        try:
            shutil.copyfile(label_tracker_model.get_sample_schema_path(), path)
            self.schema_path_fld.setText(path)
            self.status_bar.setText("Created example schema: {0}".format(path))
        except OSError as error:
            QtWidgets.QMessageBox.warning(self, "Create Schema", str(error))

    def create_example_automation(self):
        """Writes the packaged sample automation to a user-selected path."""
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Example Automation Script",
            "automation.py",
            "Python Files (*.py)",
        )
        if not path:
            return
        try:
            shutil.copyfile(label_tracker_model.get_sample_automation_path(), path)
            self.auto_path_fld.setText(os.path.dirname(path))
            self.build_automations_ui()
            self.status_bar.setText("Created example automation: {0}".format(path))
        except OSError as error:
            QtWidgets.QMessageBox.warning(self, "Create Automation", str(error))

    def populate_edit_area(self, range_item):
        """Populates the existing range area and restores compact icons.

        Args:
            range_item (RangeItem or None): Active range.
        """
        super().populate_edit_area(range_item)
        self._apply_button_icons()

    def closeEvent(self, event):
        """Persists preferences before closing tracker.

        Args:
            event (QCloseEvent): Qt close event.
        """
        """Persists preferences before closing the tracker."""
        self.save_preferences()
        super().closeEvent(event)


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = AnimationLabelTrackerView()
        window.show()
