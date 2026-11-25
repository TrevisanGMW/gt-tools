"""
Animation Evaluator Controller - Connects the view, model, and Maya service.
"""

from gt.tools.anim_evaluator import anim_evaluator_model as model_module
from gt.tools.anim_evaluator import anim_evaluator_service as service
from gt.core.motion_eval import evaluation
from gt.core.motion_eval import templates
import gt.ui.qt_import as ui_qt
import traceback
import logging
import json
import os

logger = logging.getLogger(__name__)

TEMPLATE_FILE_FILTER = "Custom Skeleton (*.json);;All Files (*)"
REPORT_FILE_FILTER = "Evaluation Report (*.json);;All Files (*)"


class AnimEvaluatorController:
    """Handles user actions for the Animation Evaluator."""

    def __init__(self, model, view):
        """Connects the model and view, then shows the window.

        Args:
            model (AnimEvaluatorModel): Tool state.
            view (AnimEvaluatorView): Tool window.
        """
        self.model = model
        self.view = view
        self.view.controller = self
        self.view.preset_editor.last_directory_getter = self.model.get_last_directory
        self.populate_view()
        self.connect_signals()
        self.view.show()

    # ------------------------------------------------ Setup ------------------------------------------------
    def populate_view(self):
        """Fills every control from the model."""
        settings = self.model.settings
        self.view.mode_combo.blockSignals(True)
        self.view.mode_combo.setCurrentIndex(max(0, self.view.mode_combo.findData(self.model.get_mode())))
        self.view.mode_combo.blockSignals(False)
        for widget, value in (
            (self.view.range_combo, settings["range_mode"]),
            (self.view.scope_combo, settings["general_scope"]),
        ):
            widget.blockSignals(True)
            widget.setCurrentText(value)
            widget.blockSignals(False)
        spin_values = ((self.view.start_spin, settings["custom_start"]), (self.view.end_spin, settings["custom_end"]))
        for spin, value in spin_values:
            spin.blockSignals(True)
            spin.setValue(int(value))
            spin.blockSignals(False)
        self.view.node_list_field.setText(settings["node_list"])
        self.view.target_mode_combo.setCurrentIndex(
            max(0, self.view.target_mode_combo.findData(settings["score_target_mode"]))
        )
        self.view.target_name_field.setText(settings["score_node_name"])
        self.view.score_attribute_field.setText(settings["score_attribute"])
        self.view.report_attribute_field.setText(settings["report_attribute"])
        self.view.write_report_checkbox.setChecked(settings["write_report_attribute"])
        self.view.preset_editor.set_preset(self.model.get_preset())
        self.refresh_template_view()
        self.view.set_report(self.model.last_report)
        self.refresh_mode_controls()

    def connect_signals(self):
        """Connects view signals to controller actions."""
        buttons = self.view.buttons
        buttons["reset"].clicked.connect(self.reset_options)
        buttons["load_template"].clicked.connect(self.load_template)
        buttons["detect_template"].clicked.connect(self.detect_template)
        buttons["evaluate"].clicked.connect(self.evaluate)
        buttons["write_score"].clicked.connect(self.write_score)
        buttons["copy_summary"].clicked.connect(self.copy_summary)
        buttons["export_report"].clicked.connect(self.export_report)
        buttons["export_graphs"].clicked.connect(self.export_graphs)
        buttons["assign_selected"].clicked.connect(self.assign_selected)
        buttons["check_scene"].clicked.connect(self.check_scene)
        buttons["save_template"].clicked.connect(self.save_template)
        self.view.template_combo.currentIndexChanged.connect(self.on_template_combo_changed)
        self.view.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        self.view.range_combo.currentTextChanged.connect(lambda value: self.set_setting("range_mode", value))
        self.view.scope_combo.currentTextChanged.connect(lambda value: self.set_setting("general_scope", value))
        self.view.start_spin.valueChanged.connect(lambda value: self.model.set_setting("custom_start", value))
        self.view.end_spin.valueChanged.connect(lambda value: self.model.set_setting("custom_end", value))
        self.view.node_list_field.editingFinished.connect(
            lambda: self.model.set_setting("node_list", self.view.node_list_field.text())
        )
        self.view.target_mode_combo.currentIndexChanged.connect(self.on_target_mode_changed)
        self.view.target_name_field.editingFinished.connect(
            lambda: self.model.set_setting("score_node_name", self.view.target_name_field.text().strip())
        )
        self.view.score_attribute_field.editingFinished.connect(
            lambda: self.model.set_setting("score_attribute", self.view.score_attribute_field.text().strip())
        )
        self.view.report_attribute_field.editingFinished.connect(
            lambda: self.model.set_setting("report_attribute", self.view.report_attribute_field.text().strip())
        )
        self.view.write_report_checkbox.toggled.connect(
            lambda value: self.set_setting("write_report_attribute", bool(value))
        )
        self.view.preset_editor.changed_callback = self.on_preset_changed
        self.view.role_table.itemChanged.connect(self.on_template_edited)
        self.view.template_name_field.editingFinished.connect(self.on_template_edited)
        self.view.up_axis_combo.currentTextChanged.connect(self.on_template_edited)
        self.view.results_tree.itemDoubleClicked.connect(self.on_result_double_clicked)

    def set_setting(self, key, value):
        """Stores a setting and refreshes mode-dependent controls.

        Args:
            key (str): Setting key.
            value (object): New value.
        """
        self.model.set_setting(key, value)
        self.refresh_mode_controls()

    def refresh_mode_controls(self):
        """Enables only the controls that affect the current settings."""
        self.view.refresh_mode_controls(
            mode=self.model.get_mode(),
            range_mode=self.model.get_setting("range_mode"),
            uses_skeleton=self.model.uses_skeleton(),
            write_report=bool(self.model.get_setting("write_report_attribute")),
        )

    def refresh_template_view(self):
        """Shows the active template."""
        source = self.model.get_setting("template_source")
        combo_key = self.model.get_setting("template_key") if source == model_module.TEMPLATE_SOURCE_BUILTIN else ""
        self.view.set_template(self.model.template, self.model.get_template_source_label(), combo_key)
        self.view.set_resolution(None)

    # ------------------------------------------------ Settings Events ------------------------------------------------
    def reset_options(self):
        """Restores every tool setting."""
        self.model.reset_to_defaults()
        self.populate_view()
        self.view.set_status("Options reset to defaults.")

    def on_mode_changed(self, index):
        """Stores the evaluation mode.

        Args:
            index (int): Combo index.
        """
        mode = self.view.mode_combo.itemData(index)
        self.model.set_mode(mode)
        self.view.preset_editor.set_mode(mode, notify=False)
        self.refresh_mode_controls()

    def on_preset_changed(self, preset):
        """Stores preset edits.

        Args:
            preset (dict): Compact preset.
        """
        self.model.set_preset(preset)

    def on_target_mode_changed(self, index):
        """Stores the score target mode and suggests a matching name.

        Args:
            index (int): Combo index.
        """
        target_mode = self.view.target_mode_combo.itemData(index)
        self.model.set_setting("score_target_mode", target_mode)
        if target_mode == service.scene_io.TARGET_ROLE and not self.view.target_name_field.text().strip():
            self.view.target_name_field.setText("hips")
            self.model.set_setting("score_node_name", "hips")

    # ------------------------------------------------ Template Actions ------------------------------------------------
    def on_template_combo_changed(self, index):
        """Activates the template chosen in the combo.

        Args:
            index (int): Combo index.
        """
        template_key = self.view.template_combo.itemData(index)
        if template_key:
            self.model.select_builtin_template(template_key)
            self.refresh_template_view()
            self.view.set_status(f'Using the built-in "{self.model.template["name"]}" skeleton.')
            return
        if self.model.get_setting("custom_template") or self.model.get_setting("template_path"):
            source = model_module.TEMPLATE_SOURCE_CUSTOM
            if self.model.get_setting("template_path") and os.path.isfile(self.model.get_setting("template_path")):
                source = model_module.TEMPLATE_SOURCE_FILE
            self.model.settings["template_source"] = source
            try:
                self.model.load_active_template()
            except (IOError, OSError, ValueError) as exception:
                self.view.set_status(f"Unable to load the Custom Skeleton: {exception}", "warning")
            self.refresh_template_view()
            return
        self.load_template()

    def load_template(self):
        """Loads a template JSON file."""
        file_path, _ = ui_qt.QtWidgets.QFileDialog.getOpenFileName(
            self.view, "Load Custom Skeleton", self.get_dialog_directory(), TEMPLATE_FILE_FILTER
        )
        if not file_path:
            self.refresh_template_view()
            return
        try:
            self.model.load_template_file(file_path)
        except (IOError, OSError, ValueError) as exception:
            self.view.set_status(f"Unable to load the Custom Skeleton: {exception}", "error")
            self.refresh_template_view()
            return
        self.refresh_template_view()
        self.view.set_status(f'Loaded Custom Skeleton "{self.model.template["name"]}".', "success")

    def save_template(self):
        """Saves the active template to a JSON file."""
        self.on_template_edited()
        default_name = f"{self.model.template.get('name', 'skeleton').replace(' ', '_').lower()}.json"
        file_path, _ = ui_qt.QtWidgets.QFileDialog.getSaveFileName(
            self.view,
            "Save Custom Skeleton",
            os.path.join(self.get_dialog_directory(), default_name),
            TEMPLATE_FILE_FILTER,
        )
        if not file_path:
            return
        try:
            self.model.save_template_file(file_path)
        except (IOError, OSError) as exception:
            self.view.set_status(f"Unable to save the Custom Skeleton: {exception}", "error")
            return
        self.refresh_template_view()
        self.view.set_status(f"Saved Custom Skeleton to {file_path}", "success")

    def on_template_edited(self, *args):
        """Stores template edits from the skeleton tab as the custom template.

        Args:
            *args: Ignored signal arguments.
        """
        edited = self.view.get_template_from_table()
        current = templates.normalize_template(self.model.template)
        compared_keys = ("name", "up_axis", "roles")
        if all(edited[key] == current[key] for key in compared_keys):
            return
        edited["description"] = current.get("description", "")
        self.model.update_template(edited)
        self.view.template_combo.blockSignals(True)
        self.view.template_combo.setCurrentIndex(self.view.template_combo.findData(""))
        self.view.template_combo.blockSignals(False)
        self.view.template_source_label.setText(f"Source: {self.model.get_template_source_label()}")

    def detect_template(self):
        """Selects the built-in template that matches the scene."""
        try:
            template_key = service.detect_builtin_template()
        except Exception as exception:
            self.report_exception("Unable to inspect the scene", exception)
            return
        if not template_key:
            self.view.set_status("No built-in skeleton matches this scene. Map the roles in the Skeleton tab.",
                                 "warning")
            return
        self.model.select_builtin_template(template_key)
        self.refresh_template_view()
        self.check_scene()

    def check_scene(self):
        """Resolves the template in the open scene and shows the result."""
        self.on_template_edited()
        try:
            resolution = service.resolve_template(self.model.template, require_biped=True)
        except Exception as exception:
            self.report_exception("Unable to resolve the skeleton", exception)
            return
        self.view.set_resolution(resolution)
        resolved_count = len(resolution["roles"])
        if resolution["missing_required"]:
            missing = ", ".join(templates.ROLE_LABELS[role] for role in resolution["missing_required"])
            self.view.set_status(f"Resolved {resolved_count} role(s). Missing for Biped mode: {missing}", "warning")
        else:
            group = f' (prefix "{resolution["group"]}")' if resolution["group"] else ""
            self.view.set_status(f"Resolved {resolved_count} role(s){group}. Ready for Biped mode.", "success")
        for warning in resolution["warnings"]:
            logger.warning(warning)

    def assign_selected(self):
        """Assigns the selected scene node name to the selected role row."""
        row = self.view.get_selected_role_row()
        if row is None:
            self.view.set_status("Select a role row in the Skeleton tab first.", "warning")
            return
        try:
            names = service.get_selected_base_names()
        except Exception as exception:
            self.report_exception("Unable to read the selection", exception)
            return
        if not names:
            self.view.set_status("Select a joint in the scene first.", "warning")
            return
        self.view.set_role_names(row, names[:1])
        self.view.set_status(f'Assigned "{names[0]}" to {templates.ROLE_LABELS[templates.ROLE_KEYS[row]]}.')

    # ------------------------------------------------ Evaluation ------------------------------------------------
    def evaluate(self):
        """Evaluates the open scene."""
        self.on_template_edited()
        settings = self.model.settings
        try:
            report = service.evaluate(
                preset=self.model.get_preset(),
                template=self.model.template if self.model.uses_skeleton() else None,
                range_mode=settings["range_mode"],
                custom_start=settings["custom_start"],
                custom_end=settings["custom_end"],
                general_scope=settings["general_scope"],
                node_names=self.model.get_node_names(),
            )
        except ValueError as exception:
            self.view.set_status(str(exception), "warning")
            return
        except Exception as exception:
            self.report_exception("Evaluation failed", exception)
            return
        self.model.last_report = report
        self.view.set_report(report)
        self.view.tabs.setCurrentIndex(0)
        for line in evaluation.summarize_report(report):
            print(f"[Animation Evaluator] {line}")
        level = {"passed": "success", "warning": "warning", "failed": "error"}.get(report["status"], "info")
        self.view.set_status(
            f"Score {report['score']}/100 ({report['status']}) over frames "
            f"{report['frame_range'][0]}-{report['frame_range'][1]}.",
            level,
        )

    def write_score(self):
        """Writes the last score to the configured attribute."""
        if not self.model.last_report:
            self.view.set_status("Evaluate the scene before writing a score.", "warning")
            return
        try:
            outcome = service.write_score(self.model.last_report, self.model.get_score_options())
        except ValueError as exception:
            self.view.set_status(str(exception), "warning")
            return
        except Exception as exception:
            self.report_exception("Unable to write the score", exception)
            return
        self.view.set_status(outcome["message"], "success" if outcome["written"] else "info")

    def copy_summary(self):
        """Copies the report summary to the clipboard."""
        if not self.model.last_report:
            self.view.set_status("Evaluate the scene first.", "warning")
            return
        ui_qt.QtWidgets.QApplication.clipboard().setText("\n".join(evaluation.summarize_report(self.model.last_report)))
        self.view.set_status("Summary copied to the clipboard.")

    def export_report(self):
        """Saves the full report as JSON."""
        if not self.model.last_report:
            self.view.set_status("Evaluate the scene first.", "warning")
            return
        file_path, _ = ui_qt.QtWidgets.QFileDialog.getSaveFileName(
            self.view, "Export Evaluation Report", self.get_dialog_directory(), REPORT_FILE_FILTER
        )
        if not file_path:
            return
        try:
            with open(file_path, "w", encoding="utf-8") as stream:
                json.dump(evaluation.strip_series(self.model.last_report), stream, indent=4)
        except (IOError, OSError) as exception:
            self.view.set_status(f"Unable to export the report: {exception}", "error")
            return
        self.model.set_setting("last_directory", os.path.dirname(file_path))
        self.view.set_status(f"Report exported to {file_path}", "success")

    def export_graphs(self):
        """Asks for a folder and saves PNG graphs of the last evaluation."""
        if not self.model.last_report:
            self.view.set_status("Evaluate the scene first.", "warning")
            return
        directory = ui_qt.QtWidgets.QFileDialog.getExistingDirectory(
            self.view, "Export Graphs To Folder", self.get_dialog_directory()
        )
        if not directory:
            return
        try:
            written = service.export_graphs(self.model.last_report, directory)
        except Exception as exception:
            self.report_exception("Unable to export graphs", exception)
            return
        self.model.set_setting("last_directory", directory)
        if not written:
            self.view.set_status("No graphs were written.", "warning")
            return
        self.view.set_status(f"Exported {len(written)} graph image(s) to {directory}", "success")

    def on_result_double_clicked(self, item, column):
        """Jumps to a frame span or selects an offender.

        Args:
            item (QTreeWidgetItem): Clicked item.
            column (int): Clicked column.
        """
        data = item.data(0, ui_qt.QtLib.ItemDataRole.UserRole)
        if not isinstance(data, dict):
            return
        try:
            if "frame" in data:
                service.go_to_frame(data["frame"])
                self.view.set_status(f"Moved to frame {data['frame']}.")
            elif "offender" in data and self.model.last_report:
                selected = service.select_nodes(service.get_offender_nodes(self.model.last_report, data["offender"]))
                message = f"Selected {', '.join(path.split('|')[-1] for path in selected)}." if selected else \
                    f'No scene node found for "{data["offender"]}".'
                self.view.set_status(message)
        except Exception as exception:
            self.report_exception("Unable to update the scene", exception)

    # ------------------------------------------------ Helpers ------------------------------------------------
    def get_dialog_directory(self):
        """Gets the starting folder for file dialogs.

        Returns:
            str: Existing folder or the home folder.
        """
        directory = self.model.get_last_directory()
        return directory if directory and os.path.isdir(directory) else os.path.expanduser("~")

    def report_exception(self, prefix, exception):
        """Logs a traceback and shows a concise status.

        Args:
            prefix (str): Message prefix.
            exception (Exception): Raised exception.
        """
        logger.warning(traceback.format_exc())
        self.view.set_status(f"{prefix}: {exception}", "error")
