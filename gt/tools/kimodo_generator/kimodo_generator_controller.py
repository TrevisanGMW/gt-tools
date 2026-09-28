"""Maya actions and asynchronous HTTP orchestration for Kimodo Generator."""

import copy
import datetime
import functools
import html
import json
import math
import os
import threading
import time
import uuid
import logging
from gt.ui import qt_import as ui_qt
from gt.ui import qt_utils
from gt.ui import resource_library as resources
from gt.utils import kimodo
from gt.tools.kimodo_generator import kimodo_generator_hik as humanik
from gt.tools.kimodo_generator import kimodo_generator_hik_tools as hik_tools
from gt.tools.kimodo_generator import kimodo_generator_results as job_results
from gt.tools.kimodo_generator.kimodo_generator_job_actions import KimodoJobActions
from gt.tools.kimodo_generator.kimodo_generator_model import (
    default_download_directory, query_wsl_distributions, resolve_environment_python,
)

QtWidgets = ui_qt.QtWidgets
QtCore = ui_qt.QtCore
logger = logging.getLogger(__name__)


class KimodoGeneratorController(QtCore.QObject, KimodoJobActions):
    """Keeps network waits off the UI thread and all Maya operations on it."""

    completed = QtCore.Signal(str, object, object)

    def __init__(self, model, view):
        """Binds the view, loads state, and starts lightweight job polling.

        Args:
            model (KimodoGeneratorModel): Persistent authoring state.
            view (KimodoGeneratorView): Constructed Qt window.
        """
        super().__init__()
        self.model = model
        self.view = view
        self.view.controller = self
        self.closed = False
        self.loading = False
        self.pending = {}
        self.last_connection = None
        self.tokens_by_url = {}
        self.submitting_job = None
        self.imported_group = None
        self.completed.connect(self._finished)
        # Maya can delete a retained workspace-control child without delivering
        # the view's closeEvent. Keep the controller from outliving its widgets.
        view.destroyed.connect(self._view_destroyed)
        for key, button in view.buttons.items():
            button.clicked.connect(self._action_callback(key))
        for name, table in view.table_registry.items():
            table.horizontalHeader().sectionResized.connect(
                functools.partial(self.save_table_widths, name, table))
            table.customContextMenuRequested.connect(
                functools.partial(self.show_table_context_menu, name, table))
        view.jobs.itemSelectionChanged.connect(self.refresh_job_details)
        view.tabs.currentChanged.connect(self.update_project_summary)
        view.mode.currentIndexChanged.connect(self.update_launch_fields)
        view.distribution.currentIndexChanged.connect(self.save_wsl_distribution)
        view.distribution.lineEdit().editingFinished.connect(self.save_wsl_distribution)
        view.output.editingFinished.connect(self._action_callback("save_output_folder"))
        for field in (view.hik_name, view.hik_xml, view.hik_pose, view.hik_frame):
            field.editingFinished.connect(self._action_callback("save_humanik_settings"))
        view.hik_lock.toggled.connect(self._action_callback("save_humanik_settings"))
        view.auto_humanik.toggled.connect(self._action_callback("save_auto_humanik"))
        view.auto_download.toggled.connect(self._action_callback("save_auto_download"))
        view.auto_maya_file.toggled.connect(self._action_callback("save_auto_maya_file"))
        view.show_console.toggled.connect(self._action_callback("save_show_console"))
        self.timer = QtCore.QTimer(view)
        self.timer.setInterval(1500)
        self.timer.timeout.connect(self.poll_jobs)
        self.load_widgets()
        self.timer.start()
        self.view.show()

    def _view_is_valid(self):
        """Checks that the controller's C++ view still exists.

        Returns:
            bool: True when the view and its child widgets are safe to access.
        """
        return qt_utils.is_qt_object_valid(self.view)

    def _results_view_is_valid(self):
        """Checks every Results widget touched by periodic polling.

        Returns:
            bool: True when the Results UI is safe to update.
        """
        if not self._view_is_valid():
            return False
        names = ("jobs", "result_info", "sample", "progress")
        return all(qt_utils.is_qt_object_valid(getattr(self.view, name, None)) for name in names)

    def _stop_polling(self):
        """Stops the polling timer when its Qt owner has not already deleted it."""
        timer = getattr(self, "timer", None)
        if qt_utils.is_qt_object_valid(timer):
            timer.stop()

    def _view_destroyed(self, *unused):
        """Invalidates asynchronous UI work when Maya destroys the window directly.

        Args:
            *unused: QObject.destroyed signal arguments.
        """
        self._stop_polling()
        self.closed = True
        self.pending.clear()

    def _action_callback(self, key, *action_args):
        """Binds one named action without late-bound loop closures.

        Args:
            key (str): Registered button name.
            *action_args: Optional fixed arguments forwarded to the action.

        Returns:
            callable: Qt button callback.
        """
        def invoke(checked=False):
            """Runs a user action and reports errors non-modally.

            Args:
                checked (bool): Unused Qt checked state.
            """
            try:
                getattr(self, "connect_bridge" if key == "connect" else key)(*action_args)
            except (ValueError, FileNotFoundError) as warning:
                logger.warning("%s", warning)
                self.message(str(warning), warning=True)
            except Exception as error:
                logger.exception("Kimodo action %s failed", key)
                self.message(str(error), error=True)
        return invoke

    def message(self, text, error=False, warning=False):
        """Displays routine feedback in the bottom status field.

        Args:
            text (str): User-facing message.
            error (bool): Whether to use warning text color.
            warning (bool): Whether this is expected user guidance instead of a failure.
        """
        if not self.closed:
            self.view.status.setText(f"Warning: {text}" if warning else text)
            self.view.status.setProperty("feedback_level", "warning" if warning else "error" if error else "info")
            color = "#e6b677" if warning else "#ee9292" if error else "#c7d9d6"
            self.view.status.setStyleSheet(f"color: {color};")

    def run_network(self, key, function, callback):
        """Runs an HTTP/process task; its callback is delivered on Qt's thread.

        Args:
            key (str): Prevents duplicate concurrent operations of the same kind.
            function (callable): Network-only or subprocess operation.
            callback (callable): Main-thread result handler.
        """
        if key in self.pending:
            self.message("That operation is already running.")
            return
        self.pending[key] = callback
        if key in self.view.buttons:
            self.view.buttons[key].setEnabled(False)

        def run():
            """Computes a result without touching Qt widgets or the Maya scene."""
            try:
                result, error = function(), None
            except (ValueError, FileNotFoundError) as exception:
                logger.warning("%s", exception)
                result, error = None, exception
            except Exception as exception:
                logger.exception("Kimodo background operation %s failed", key)
                result, error = None, exception
            if not self.closed:
                self.completed.emit(key, result, error)

        threading.Thread(target=run, name=f"Kimodo_{key}", daemon=True).start()

    @QtCore.Slot(str, object, object)
    def _finished(self, key, result, error):
        """Dispatches completed network work on the main thread.

        Args:
            key (str): Operation key.
            result (object): Successful return value.
            error (Exception or None): Failure or expected validation warning.
        """
        callback = self.pending.pop(key, None)
        if self.closed:
            return
        if key in self.view.buttons:
            self.view.buttons[key].setEnabled(True)
        if error:
            if key == "generate" and self.submitting_job:
                self.submitting_job.update(
                    status="submission_unknown", stage="Refresh to check acceptance", error=str(error))
                self.submitting_job = None
                self.model.save_preferences()
                self.populate_jobs()
            expected = isinstance(error, (ValueError, FileNotFoundError))
            self.message(str(error), error=not expected, warning=expected)
            return
        try:
            if callback:
                callback(result)
        except (ValueError, FileNotFoundError) as warning:
            logger.warning("%s", warning)
            self.message(str(warning), warning=True)
        except Exception as exception:
            logger.exception("Kimodo result action failed")
            self.message(str(exception), error=True)

    def update_launch_fields(self):
        """Enables settings that apply to the selected connection mode."""
        mode = self.view.mode.currentData()
        self.view.python_path.setEnabled(mode != "existing")
        self.view.distribution.setEnabled(mode == "wsl")
        self.view.buttons["browse_python"].setEnabled(mode != "existing")
        self.view.buttons["query_wsl"].setEnabled(mode == "wsl")
        self.view.buttons["restart_bridge"].setEnabled(mode != "existing")
        for widget in (self.view.encoder_url, self.view.device, self.view.start_encoder, self.view.show_console):
            widget.setEnabled(mode != "existing")

    def save_show_console(self):
        """Persists the bridge console preference without validating other fields."""
        if not self.loading:
            self.model.connection["show_console"] = self.view.show_console.isChecked()
            self.model.save_preferences()

    def save_wsl_distribution(self):
        """Persists the latest selected or manually entered WSL distribution."""
        if self.loading:
            return
        distribution = self.view.distribution.currentText().strip()
        if distribution == self.model.connection.get("distribution", ""):
            return
        self.model.connection["distribution"] = distribution
        self.model.save_preferences()

    def save_table_widths(self, name, table, unused_column, unused_previous, unused_current):
        """Persists a user's manual column widths for one named table.

        Args:
            name (str): Stable table preference key.
            table (QTableWidget): Resized table.
            unused_column (int): Qt resized section index.
            unused_previous (int): Previous section width.
            unused_current (int): New section width.
        """
        if self.loading or table.property("gt_adjusting_columns"):
            return
        self.model.table_widths[name] = [table.columnWidth(index) for index in range(table.columnCount())]
        table.setProperty("gt_user_widths", True)
        self.model.save_preferences()

    def restore_table_widths(self):
        """Restores valid user column widths and leaves unsaved tables auto-fitted."""
        for name, table in self.view.table_registry.items():
            widths = self.model.table_widths.get(name)
            table.setProperty("gt_adjusting_columns", True)
            try:
                if widths and len(widths) == table.columnCount():
                    for column, width in enumerate(widths):
                        table.horizontalHeader().setSectionResizeMode(
                            column, QtWidgets.QHeaderView.ResizeMode.Interactive)
                        table.setColumnWidth(column, width)
                    table.setProperty("gt_user_widths", True)
                    table.setProperty("gt_columns_fitted", True)
                else:
                    table.setProperty("gt_user_widths", False)
                    table.setProperty("gt_columns_fitted", False)
                    self.view.fit_table_columns(table, force=True)
            finally:
                table.setProperty("gt_adjusting_columns", False)

    @staticmethod
    def _add_menu_action(menu, label, callback, enabled=True, icon_path=None):
        """Adds one consistently configured table-menu action.

        Args:
            menu (QMenu): Parent context menu.
            label (str): User-facing action text.
            callback (callable): Slot invoked when the action is selected.
            enabled (bool): Whether the action can currently run.
            icon_path (str, optional): Icon resource path.

        Returns:
            QAction: Created menu action.
        """
        action = menu.addAction(label)
        if icon_path:
            action.setIcon(ui_qt.QtGui.QIcon(icon_path))
        action.setEnabled(enabled)
        action.triggered.connect(callback)
        return action

    def show_table_context_menu(self, name, table, position):
        """Builds actions appropriate to the right-clicked Kimodo table.

        Args:
            name (str): Stable table name: prompts, constraints, or jobs.
            table (QTableWidget): Source table.
            position (QPoint): Position relative to the table viewport.
        """
        row = table.rowAt(position.y())
        if row >= 0:
            table.selectRow(row)
        selected = row >= 0
        menu = QtWidgets.QMenu(table)
        invoke = self._action_callback
        if name == "prompts":
            self._add_menu_action(menu, "Add Segment", invoke("add_prompt"),
                                  icon_path=resources.Icon.ui_add)
            menu.addSeparator()
            self._add_menu_action(menu, "Duplicate Segment", invoke("duplicate_prompt"), selected,
                                  resources.Icon.rigger_action_duplicate_grayscale)
            self._add_menu_action(menu, "Copy Segment", invoke("copy_prompt"), selected,
                                  resources.Icon.rigger_action_copy_grayscale)
            self._add_menu_action(menu, "Paste Segment", invoke("paste_prompt"),
                                  icon_path=resources.Icon.rigger_action_paste_grayscale)
            menu.addSeparator()
            self._add_menu_action(menu, "Move Up", invoke("prompt_up"), selected and row > 0,
                                  resources.Icon.rigger_action_up_arrow)
            self._add_menu_action(menu, "Move Down", invoke("prompt_down"),
                                  selected and row < table.rowCount() - 1,
                                  resources.Icon.rigger_action_down_arrow)
            self._add_menu_action(menu, "Remove Segment", invoke("remove_prompt"),
                                  selected and table.rowCount() > 1, resources.Icon.ui_trash)
        elif name == "constraints":
            self._add_menu_action(menu, "Preview Pose", invoke("preview_pose"), selected,
                                  resources.Icon.ui_open)
            self._add_menu_action(menu, "Enable / Disable", invoke("toggle_constraint"), selected,
                                  resources.Icon.ui_toggle_disabled)
            pose_types = (("Full Body", "fullbody"), ("Left Hand", "left-hand"),
                          ("Right Hand", "right-hand"), ("Left Foot", "left-foot"),
                          ("Right Foot", "right-foot"))
            current_type = None
            if selected and row < len(self.model.constraints):
                current_type = self.model.constraints[row]["parameters"].get("type")
            type_menu = menu.addMenu("Change Pose Type")
            type_menu.menuAction().setIcon(ui_qt.QtGui.QIcon(resources.Icon.ui_edit))
            type_menu.setEnabled(current_type in dict(pose_types).values())
            for label, constraint_type in pose_types:
                action = self._add_menu_action(
                    type_menu, label, invoke("change_constraint_type", constraint_type),
                    enabled=current_type != constraint_type, icon_path=resources.Icon.ui_edit)
                action.setCheckable(True)
                action.setChecked(current_type == constraint_type)
            menu.addSeparator()
            self._add_menu_action(menu, "Duplicate Constraint", invoke("duplicate_constraint"), selected,
                                  resources.Icon.rigger_action_duplicate_grayscale)
            self._add_menu_action(menu, "Copy Constraint", invoke("copy_constraint"), selected,
                                  resources.Icon.rigger_action_copy_grayscale)
            self._add_menu_action(menu, "Paste Constraint", invoke("paste_constraint"),
                                  icon_path=resources.Icon.rigger_action_paste_grayscale)
            self._add_menu_action(menu, "Remove Constraint", invoke("remove_constraint"), selected,
                                  resources.Icon.ui_trash)
            menu.addSeparator()
            self._add_menu_action(menu, "Load Constraints JSON", invoke("import_constraints"),
                                  icon_path=resources.Icon.rigger_action_import_grayscale)
            self._add_menu_action(menu, "Save Constraints JSON", invoke("export_constraints"),
                                  icon_path=resources.Icon.rigger_action_export_grayscale)
        elif name == "jobs":
            job = self.model.jobs[row] if selected and row < len(self.model.jobs) else None
            terminal = bool(job and job.get("status") in kimodo.TERMINAL_STATUSES)
            generation = bool(job and job.get("operation") != "download_model")
            succeeded = bool(job and job.get("status") == "succeeded")
            self._add_menu_action(menu, "Refresh Job", invoke("refresh_job"), selected,
                                  resources.Icon.tool_check_for_updates)
            self._add_menu_action(menu, "Cancel Job", invoke("cancel_job"), selected and not terminal,
                                  resources.Icon.setup_close)
            menu.addSeparator()
            self._add_menu_action(menu, "Download / Repair Results", invoke("download_results"),
                                  succeeded and generation, resources.Icon.rigger_action_import_grayscale)
            self._add_menu_action(menu, "Create / Repair Maya Files", invoke("create_maya_files"),
                                  succeeded and generation, resources.Icon.ui_new)
            self._add_menu_action(menu, "Open Results Folder", invoke("open_folder"), selected,
                                  resources.Icon.util_open_dir)
            self._add_menu_action(menu, "Import Sample", invoke("import_sample"),
                                  succeeded and generation, resources.Icon.rigger_action_import_grayscale)
            menu.addSeparator()
            self._add_menu_action(menu, "Copy Job ID", invoke("copy_job_id"), selected,
                                  resources.Icon.rigger_action_copy_grayscale)
            self._add_menu_action(menu, "Copy Server Location", invoke("copy_server_location"), selected,
                                  resources.Icon.rigger_action_copy_grayscale)
            menu.addSeparator()
            self._add_menu_action(menu, "Clean Selected Job...", invoke("clear_selected_job"), selected,
                                  resources.Icon.ui_trash)
            menu.addSeparator()
            has_finished = any(item.get("status") in kimodo.TERMINAL_STATUSES for item in self.model.jobs)
            self._add_menu_action(menu, "Clear Finished", invoke("clear_finished"), has_finished,
                                  resources.Icon.ui_trash)
            self._add_menu_action(menu, "Clear All History", invoke("clear_history"), bool(self.model.jobs),
                                  resources.Icon.ui_trash)
        if menu.isEmpty():
            return
        execute = getattr(menu, "exec_", None) or getattr(menu, "exec")
        execute(table.viewport().mapToGlobal(position))

    @staticmethod
    def _set_clipboard_payload(kind, data):
        """Copies one versioned Kimodo table entry to the system clipboard.

        Args:
            kind (str): Clipboard entry kind.
            data (dict): JSON-compatible entry data.
        """
        payload = {"schema": "gt-kimodo-table-v1", "kind": kind, "data": data}
        QtWidgets.QApplication.clipboard().setText(json.dumps(payload, indent=2, sort_keys=True))

    @staticmethod
    def _get_clipboard_payload(kind):
        """Reads and validates a Kimodo table entry from the system clipboard.

        Args:
            kind (str): Required clipboard entry kind.

        Returns:
            dict: Copied entry data.
        """
        try:
            payload = json.loads(QtWidgets.QApplication.clipboard().text())
        except (TypeError, ValueError) as error:
            raise ValueError(f"Clipboard does not contain a copied Kimodo {kind}.") from error
        if (not isinstance(payload, dict) or payload.get("schema") != "gt-kimodo-table-v1"
                or payload.get("kind") != kind or not isinstance(payload.get("data"), dict)):
            raise ValueError(f"Clipboard does not contain a copied Kimodo {kind}.")
        return payload["data"]

    def load_widgets(self):
        """Populates widgets from model state without modifying it."""
        self.loading = True
        view = self.view
        settings = self.model.connection
        view.mode.setCurrentIndex(max(0, view.mode.findData(settings["mode"])))
        for widget, key in ((view.url, "url"), (view.python_path, "python_path"),
                            (view.encoder_url, "text_encoder_url")):
            widget.setText(settings.get(key) or "")
        view.distribution.setCurrentText(settings.get("distribution") or "")
        view.device.setCurrentText(settings["device"])
        view.start_encoder.setChecked(settings["start_encoder"])
        view.show_console.setChecked(settings.get("show_console", True))
        view.token.setText(self.model.token)
        self.populate_prompts()
        parameters = self.model.definition["parameters"]
        view.seed.setText("" if parameters["seed"] is None else str(parameters["seed"]))
        view.samples.setValue(parameters["num_samples"])
        view.steps.setValue(parameters["diffusion_steps"])
        view.postprocess.setChecked(parameters["postprocess"])
        view.text_guidance.setValue(parameters["guidance"][0])
        view.constraint_guidance.setValue(parameters["guidance"][1])
        view.transition.setValue(parameters["transition_frames"])
        view.heading.setValue(math.degrees(parameters["heading"]))
        view.output.setText(self.model.output_directory)
        view.namespace.setText(self.model.namespace)
        view.start_frame.setValue(self.model.start_frame)
        hik = self.model.humanik
        view.hik_name.setText(hik["character_name"])
        view.hik_xml.setText(hik["definition_path"])
        view.hik_pose.setText(hik["tpose_path"])
        view.hik_frame.setText("" if hik["reference_frame"] is None else str(hik["reference_frame"]))
        view.hik_lock.setChecked(hik["lock_definition"])
        view.auto_humanik.setChecked(self.model.definition["maya"]["auto_humanik"])
        view.auto_download.setChecked(self.model.auto_download)
        view.auto_maya_file.setChecked(self.model.auto_maya_file)
        self.populate_models()
        self.populate_constraints()
        self.populate_jobs()
        self.restore_table_widths()
        self.loading = False
        self.update_launch_fields()
        self.update_project_summary()

    def gather(self):
        """Copies editable widget values into model state and validates them."""
        view = self.view
        self.gather_connection()
        self.gather_prompts()
        self.model.definition.update(model=view.model.currentData() or kimodo.DEFAULT_MODEL)
        self.model.definition["parameters"] = {
            "seed": int(view.seed.text()) if view.seed.text().strip() else None,
            "num_samples": view.samples.value(), "diffusion_steps": view.steps.value(),
            "postprocess": view.postprocess.isChecked(),
            "guidance": [view.text_guidance.value(), view.constraint_guidance.value()],
            "transition_frames": view.transition.value(), "heading": math.radians(view.heading.value())}
        self.gather_constraints()
        self.model.output_directory = view.output.text().strip()
        self.model.namespace = view.namespace.text().strip()
        self.model.start_frame = view.start_frame.value()
        self.gather_humanik()

    def gather_prompts(self):
        """Copies only editable prompt rows into the model."""
        view = self.view
        prompts = []
        for row in range(view.prompts.rowCount()):
            prompts.append({"duration_seconds": float(view.prompts.item(row, 0).text()),
                            "text": view.prompts.item(row, 1).text()})
        self.model.definition["prompts"] = prompts

    def gather_connection(self):
        """Copies only server fields so connection management ignores unfinished generation edits."""
        view = self.view
        self.model.connection.update(url=view.url.text().strip(), mode=view.mode.currentData(),
                                     python_path=view.python_path.text().strip(),
                                     distribution=view.distribution.currentText().strip(),
                                     device=view.device.currentText(),
                                     text_encoder_url=view.encoder_url.text().strip(),
                                     start_encoder=view.start_encoder.isChecked(),
                                     show_console=view.show_console.isChecked())
        self.model.token = view.token.text()
        self.tokens_by_url[view.url.text().strip().rstrip("/")] = self.model.token
        self.model.save_preferences()

    def gather_constraints(self):
        """Applies edited names, enabled states, and one-based UI timing."""
        for row, entry in enumerate(self.model.constraints):
            table = self.view.constraints
            entry["enabled"] = table.item(row, 0).checkState() == QtCore.Qt.CheckState.Checked
            entry["name"] = table.item(row, 3).text()
            frames = self.parse_frames(table.item(row, 1).text())
            if len(frames) != len(entry["parameters"]["frame_indices"]):
                raise ValueError("Keep the same number of keys when retiming a constraint row.")
            entry["parameters"]["frame_indices"] = frames

    @staticmethod
    def parse_frames(text):
        """Converts comma-separated one-based UI frames into native indices.

        Args:
            text (str): User-entered frame list.

        Returns:
            list: Zero-based frame indices.
        """
        frames = [int(value.strip()) - 1 for value in text.split(",") if value.strip()]
        if not frames or any(value < 0 for value in frames):
            raise ValueError("Clip frames must be positive integers, separated by commas.")
        return frames

    def populate_prompts(self):
        """Displays the ordered prompt segments."""
        table = self.view.prompts
        table.setRowCount(len(self.model.definition["prompts"]))
        for row, segment in enumerate(self.model.definition["prompts"]):
            table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(segment["duration_seconds"])))
            table.setItem(row, 1, QtWidgets.QTableWidgetItem(segment["text"]))
        self.view.fit_table_columns(table)

    def populate_models(self):
        """Displays discovered models while preserving an explicitly saved model."""
        combo = self.view.model
        current = self.model.definition["model"]
        combo.clear()
        for info in self.model.capabilities.get("models", []):
            suffix = "cached config" if info.get("cached") else "download on first use"
            combo.addItem(f"{info['name']} ({suffix})", info["id"])
        if combo.findData(current) < 0:
            combo.addItem(current, current)
        combo.setCurrentIndex(combo.findData(current))

    def populate_constraints(self):
        """Displays stable authoring entries with editable timing and labels."""
        table = self.view.constraints
        selected = table.currentRow()
        table.setRowCount(len(self.model.constraints))
        for row, entry in enumerate(self.model.constraints):
            check = QtWidgets.QTableWidgetItem()
            check.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsUserCheckable |
                           QtCore.Qt.ItemFlag.ItemIsSelectable)
            check.setCheckState(QtCore.Qt.CheckState.Checked if entry["enabled"] else QtCore.Qt.CheckState.Unchecked)
            check.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 0, check)
            table.setItem(row, 1, QtWidgets.QTableWidgetItem(
                ", ".join(str(frame + 1) for frame in entry["parameters"]["frame_indices"])))
            kind = QtWidgets.QTableWidgetItem(entry["parameters"]["type"])
            kind.setFlags(kind.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, 2, kind)
            table.setItem(row, 3, QtWidgets.QTableWidgetItem(entry["name"]))
        if table.rowCount():
            table.selectRow(min(max(selected, 0), table.rowCount() - 1))
        self.view.fit_table_columns(table)

    def populate_jobs(self):
        """Updates job history without changing the selected job."""
        if self.closed or not self._results_view_is_valid():
            self._view_destroyed()
            return
        table = self.view.jobs
        selected = table.currentRow()
        table.blockSignals(True)
        table.setRowCount(len(self.model.jobs))
        for row, job in enumerate(self.model.jobs):
            submitted = self._format_submitted_time(job.get("submitted_at"))
            status = job_results.display_status(job).replace("_", " ").title()
            values = (job["job_id"][:12], submitted, status, job_results.display_stage_and_request(job))
            for column, text in enumerate(values):
                item = QtWidgets.QTableWidgetItem(text)
                if column == 2:
                    item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, column, item)
        if table.rowCount():
            table.selectRow(min(selected if selected >= 0 else table.rowCount() - 1, table.rowCount() - 1))
        table.blockSignals(False)
        self.view.fit_table_columns(table)
        self.refresh_job_details()
        self.update_project_summary()

    @staticmethod
    def _format_submitted_time(timestamp):
        """Formats a server submission timestamp in the user's local timezone.

        Args:
            timestamp (float or None): Unix timestamp reported by the bridge.

        Returns:
            str: Readable local date and time, or a dash while submission is pending.
        """
        try:
            return datetime.datetime.fromtimestamp(float(timestamp)).strftime("%Y-%m-%d %H:%M:%S")
        except (TypeError, ValueError, OSError, OverflowError):
            return "â€”"

    @staticmethod
    def _summary_path(value):
        """Escapes a path or URL and adds safe wrapping opportunities.

        Args:
            value (object): Display value containing path separators.

        Returns:
            str: HTML-safe text with zero-width wrapping points.
        """
        escaped = html.escape(str(value))
        return escaped.replace("/", "/&#8203;").replace("\\", "\\&#8203;")

    def update_project_summary(self, *unused):
        """Builds a current read-only project overview from widgets and job history.

        Args:
            *unused: Optional Qt tab-change signal arguments.
        """
        if self.closed or not self._view_is_valid():
            return
        view = self.view
        durations = []
        prompt_names = []
        for row in range(view.prompts.rowCount()):
            try:
                durations.append(float(view.prompts.item(row, 0).text()))
            except (AttributeError, TypeError, ValueError):
                pass
            item = view.prompts.item(row, 1)
            if item and item.text().strip():
                prompt_names.append(item.text().strip())
        enabled_constraints = 0
        constraint_types = []
        for row in range(view.constraints.rowCount()):
            item = view.constraints.item(row, 0)
            if item and item.checkState() == QtCore.Qt.CheckState.Checked:
                enabled_constraints += 1
                kind = view.constraints.item(row, 2)
                if kind:
                    constraint_types.append(kind.text())
        status_counts = {}
        for job in self.model.jobs:
            status = job.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        status_text = ", ".join(f"{key}: {value}" for key, value in sorted(status_counts.items())) or "none"
        downloaded = sum(job_results.local_status(job) == "downloaded" for job in self.model.jobs)
        maya_ready = sum(bool(job.get("maya_files")) for job in self.model.jobs)
        mode = view.mode.currentText()
        runtime = ""
        if view.mode.currentData() == "wsl":
            runtime = f"<br><b>WSL:</b> {html.escape(view.distribution.currentText().strip() or 'not selected')}"
        elif view.mode.currentData() == "native":
            runtime = f"<br><b>Python:</b> {self._summary_path(view.python_path.text().strip() or 'not selected')}"
        model_name = view.model.currentText() or view.model.currentData() or "not loaded"
        seed = view.seed.text().strip() or "random"
        constraint_summary = ", ".join(sorted(set(constraint_types))) or "none"
        hik_mode = "custom overrides" if any((view.hik_xml.text().strip(), view.hik_pose.text().strip(),
                                               view.hik_frame.text().strip())) else "automatic Kimodo defaults"
        prompts = " â†’ ".join(prompt_names) if prompt_names else "none"
        view.project_summary.setText(
            f"<h3>Connection</h3><b>Mode:</b> {html.escape(mode)}<br>"
            f"<b>Bridge:</b> {self._summary_path(view.url.text().strip() or 'not configured')}{runtime}"
            f"<h3>Generation</h3><b>Model:</b> {html.escape(str(model_name))}<br>"
            f"<b>Prompts:</b> {html.escape(prompts)}<br>"
            f"<b>Duration:</b> {sum(durations):g} seconds across {view.prompts.rowCount()} segment(s)<br>"
            f"<b>Seed / samples / steps:</b> {html.escape(seed)} / {view.samples.value()} / {view.steps.value()}<br>"
            f"<b>Constraints:</b> {enabled_constraints} enabled of {view.constraints.rowCount()} "
            f"({html.escape(constraint_summary)})"
            f"<h3>Output and HumanIK</h3><b>Folder:</b> {self._summary_path(view.output.text().strip())}<br>"
            f"<b>Automation:</b> download {'on' if view.auto_download.isChecked() else 'off'}, "
            f"Maya + HIK {'on' if view.auto_maya_file.isChecked() else 'off'}<br>"
            f"<b>HumanIK:</b> {hik_mode}"
            f"<h3>Jobs</h3><b>History:</b> {len(self.model.jobs)} ({html.escape(status_text)})<br>"
            f"<b>Local:</b> {downloaded} downloaded, {maya_ready} Maya-ready")

    def selected_job(self):
        """Gets the selected history entry.

        Returns:
            dict: Selected job.
        """
        if self.closed or not self._results_view_is_valid():
            raise ValueError("The Kimodo Generator window is closed.")
        row = self.view.jobs.currentRow()
        if not 0 <= row < len(self.model.jobs):
            raise ValueError("Select a job in Results.")
        return self.model.jobs[row]

    def refresh_job_details(self):
        """Shows the selected job's source, errors, provenance, and samples."""
        if self.closed or not self._results_view_is_valid():
            return
        try:
            job = self.selected_job()
        except ValueError:
            self.view.result_info.setText("No job selected. Generate motion to create a new request.")
            self.view.sample.clear()
            self.view.sample_selector.hide()
            self.view.progress.setValue(0)
            return
        resolved = job.get("resolved", {})
        text = f"{job['url']}\n{job['job_id']}\n{job.get('error') or job.get('stage', '')}"
        text += f"\nServer: {job['status']} | Local: {job_results.local_status(job)}"
        text += f"\nMaya files: {job_results.maya_status(job)}"
        if job.get("maya_files"):
            text += "\n" + "\n".join(job["maya_files"].values())
        for key in ("cleanup_error", "download_error", "refresh_error", "maya_export_error"):
            if job.get(key):
                text += f"\n{job[key]}"
        if job.get("server_missing"):
            text += "\nServer job is missing; existing local files are still available."
        if resolved:
            text += f"\nModel: {resolved.get('model')} | Seed: {resolved.get('seed', '—')}"
        self.view.result_info.setText(text)
        self.view.progress.setValue(int(job.get("progress", 1 if job["status"] == "succeeded" else 0) * 100))
        current = self.view.sample.currentText()
        self.view.sample.clear()
        names = resolved.get("samples")
        if not names:
            available = set(job.get("paths", {}))
            available.update(entry.get("name", "") for entry in job.get("artifacts", []))
            names = sorted(name for name in available if name == "motion.json"
                           or (name.startswith("sample_") and name.endswith(".json")))
        self.view.sample.addItems(names)
        self.view.sample_selector.setVisible(len(names) > 1)
        if current in names:
            self.view.sample.setCurrentText(current)

    def connect_bridge(self):
        """Starts or connects to a bridge using a background worker."""
        self.gather_connection()
        connection = self.model.make_connection()
        self.last_connection = connection
        self.message("Connecting to Kimodo…")

        def operation():
            """Checks readiness and obtains model and skeleton metadata.

            Returns:
                tuple: Health, capabilities and rest motion.
            """
            health = connection.start_local()
            client = kimodo.KimodoClient(connection)
            return health, client.capabilities(), client.skeleton()

        def ready(result):
            """Stores discovered capabilities and updates connection feedback.

            Args:
                result (tuple): Health, capabilities and rest motion.
            """
            health, self.model.capabilities, self.model.rest_motion = result
            self._store_resolved_python(connection)
            self.populate_models()
            self.model.save_preferences()
            self.view.connection_info.setText(self._bridge_status_text(health, connection))
            self.message("Connected. Choose a model, add prompts or poses, and generate.")

        self.run_network("connect", operation, ready)

    @staticmethod
    def _bridge_status_text(health, connection):
        """Formats readable bridge ownership, process, and activity information.

        Args:
            health (dict): Bridge health payload.
            connection (KimodoConnection): Current connection/launch settings.

        Returns:
            str: Multi-line status suitable for the Connection tab.
        """
        runtime = health.get("runtime", {})
        if connection.mode == "wsl":
            location = f"WSL distribution {connection.distribution}"
        elif connection.mode == "native":
            location = "native Windows"
        else:
            location = runtime.get("platform", "externally managed server")
        lines = [f"Bridge: READY at {connection.url}", f"Runs in: {location}"]
        if runtime:
            lines.extend((f"PID: {runtime.get('pid', 'unknown')} | Device: {runtime.get('device', 'unknown')}",
                          f"Python: {runtime.get('python_executable', 'unknown')}",
                          f"Bridge code: {runtime.get('bridge_script', 'unknown')}",
                          f"Server jobs: {runtime.get('job_directory', 'unknown')}",
                          f"Activity: {runtime.get('queued_jobs', 0)} queued; "
                          f"active {runtime.get('active_job_id') or 'none'}; "
                          f"{runtime.get('unfinished_jobs', 0)} unfinished",
                          f"Text encoder: {runtime.get('text_encoder_url') or 'not configured'}"))
        else:
            lines.append("Legacy bridge: restart once to enable process details, cleanup, and Maya management.")
        if connection.log_path:
            lines.append(f"Startup log: {connection.log_path}")
        elif connection.mode != "existing" and connection.show_console:
            lines.append("Bridge console: opened in a separate window")
        return "\n".join(lines)

    def _store_resolved_python(self, connection):
        """Stores an environment folder's resolved interpreter after local startup.

        Args:
            connection (KimodoConnection): Connection whose launch path was normalized.
        """
        if connection.mode == "existing" or not connection.python_path:
            return
        self.model.connection["python_path"] = connection.python_path
        self.view.python_path.setText(connection.python_path)

    def test_bridge(self):
        """Tests only the configured bridge and displays where its process runs."""
        self.gather_connection()
        connection = self.model.make_connection()
        client = kimodo.KimodoClient(connection)

        def ready(health):
            """Displays bridge runtime information after a successful probe.

            Args:
                health (dict): Validated health payload.
            """
            self.view.connection_info.setText(self._bridge_status_text(health, connection))
            self.message("Bridge connection succeeded.")
        self.run_network("test_bridge", client.health, ready)

    def test_encoder(self):
        """Tests the configured Gradio text encoder independently of the bridge."""
        self.gather_connection()
        url = self.model.connection["text_encoder_url"]

        def ready(result):
            """Reports a successful encoder probe without changing bridge state.

            Args:
                result (dict): Encoder readiness payload.
            """
            self.message(f"Text encoder is ready at {result['url']} (API: {result['api_name']}).")
        self.run_network("test_encoder", lambda: kimodo.probe_text_encoder(url), ready)

    def stop_bridge(self):
        """Requests graceful idle bridge shutdown, preserving encoder and persistent data."""
        self.gather_connection()
        connection = self.model.make_connection()
        answer = QtWidgets.QMessageBox.question(
            self.view, "Stop Kimodo Bridge",
            f"Stop the bridge at {connection.url}?\n\n"
            "The bridge refuses while jobs are active. Generated jobs, model weights, downloaded results, and an "
            "independently managed text encoder are preserved.",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No)
        if answer != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        def stopped(result):
            """Updates the connection display after server acknowledgement.

            Args:
                result (dict): Shutdown acknowledgement.
            """
            runtime = result.get("runtime", {})
            self.view.connection_info.setText(
                f"Bridge: STOPPED at {connection.url}\nPrevious PID: {runtime.get('pid', 'unknown')}\n"
                "Text encoder: not changed by the endpoint; test it separately")
            self.message("Bridge stopped. Persistent job/model files were preserved; test the encoder separately.")
        self.run_network("stop_bridge", kimodo.KimodoClient(connection).shutdown, stopped)

    def restart_bridge(self):
        """Gracefully stops, redeploys, starts, and reconnects a configured local bridge."""
        self.gather_connection()
        connection = self.model.make_connection()
        if connection.mode == "existing":
            raise ValueError("Choose Start in WSL or Start on Windows and provide its Kimodo Python before restart. "
                             "An existing-server URL does not tell Maya how to launch that server.")
        answer = QtWidgets.QMessageBox.question(
            self.view, "Restart Kimodo Bridge",
            f"Restart the bridge at {connection.url} using the current GT Tools code?\n\n"
            "The bridge refuses while jobs are active. The job store, model weights, and independently managed "
            "text encoder are preserved.",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No)
        if answer != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        def operation():
            """Stops the old process, waits for its port, then starts the configured runtime.

            Returns:
                tuple: New health, capabilities and rest skeleton.
            """
            connection.validate_local_launch()
            client = kimodo.KimodoClient(connection)
            client.shutdown()
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                try:
                    client.health()
                except ConnectionError:
                    break
                time.sleep(0.2)
            else:
                raise TimeoutError(f"Bridge at {connection.url} did not stop within 20 seconds.")
            health = connection.start_local()
            return health, client.capabilities(), client.skeleton()

        def restarted(result):
            """Loads discovery from the replacement process and displays its runtime.

            Args:
                result (tuple): Health, capabilities and rest skeleton.
            """
            health, self.model.capabilities, self.model.rest_motion = result
            self.last_connection = connection
            self._store_resolved_python(connection)
            self.populate_models()
            self.model.save_preferences()
            self.view.connection_info.setText(self._bridge_status_text(health, connection))
            self.message("Bridge restarted with the current GT Tools code and reconnected.")
        self.run_network("restart_bridge", operation, restarted)

    def refresh_models(self):
        """Refreshes server capabilities without starting another process."""
        self.gather_connection()
        client = kimodo.KimodoClient(self.model.make_connection())

        def ready(capabilities):
            """Applies refreshed model discovery.

            Args:
                capabilities (dict): Advertised backend support.
            """
            self.model.capabilities = capabilities
            self.populate_models()
            self.message("Model list refreshed.")
        self.run_network("refresh_models", client.capabilities, ready)

    def generate(self):
        """Validates and submits a saved request snapshot without blocking Maya."""
        if "generate" in self.pending:
            return
        self.gather()
        definition = self.model.build_definition()
        connection = self.model.make_connection()
        job_id = uuid.uuid4().hex
        entry = self.model.add_job({"job_id": job_id, "status": "submitting", "stage": "submitting",
                                    "operation": "generate"}, connection, definition.as_dict())
        self.submitting_job = entry
        self.populate_jobs()
        self.view.jobs.selectRow(len(self.model.jobs) - 1)
        self.view.tabs.setCurrentIndex(self.view.results_tab_index)

        def submitted(result):
            """Records server acceptance.

            Args:
                result (dict): Job state.
            """
            entry.update(result)
            self.submitting_job = None
            self.model.save_preferences()
            self.populate_jobs()
            self.message("Generation queued. You can continue working in Maya.")
        self.run_network("generate", lambda: kimodo.KimodoClient(connection).submit(definition, job_id), submitted)

    def summary_generate(self):
        """Submits the current project from the Summary tab."""
        self.generate()

    def download_model(self):
        """Queues a model download after an explicit size/access notice."""
        self.gather()
        model = self.model.definition["model"]
        answer = QtWidgets.QMessageBox.question(self.view, "Download Kimodo Model",
            f"Download {model} into the server's Hugging Face cache?\n"
            "Model files may be several GB. The server needs network access and any required model authorization.")
        if answer != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        connection = self.model.make_connection()

        def submitted(result):
            """Adds the model download to job history.

            Args:
                result (dict): Accepted download job.
            """
            self.model.add_job(result, connection)
            self.populate_jobs()
            self.view.tabs.setCurrentIndex(self.view.results_tab_index)
        self.run_network("download_model", lambda: kimodo.KimodoClient(connection).download_model(model), submitted)

    def _job_client(self, job):
        """Creates a client without forwarding one server's token to another.

        Args:
            job (dict): History entry carrying its original server URL.

        Returns:
            KimodoClient: Origin-scoped client.
        """
        url = job["url"].rstrip("/")
        token = self.tokens_by_url.get(url)
        return kimodo.KimodoClient(kimodo.KimodoConnection(url=url, token=token or None))


    def cancel_job(self):
        """Requests cancellation without killing a shared server process."""
        job = self.selected_job()
        client = self._job_client(job)
        self.run_network("cancel_job", lambda: client.cancel(job["job_id"]),
                         lambda result: self.message("Cancellation requested; waiting for a supported stop boundary."))


    def _sample_path(self):
        """Resolves a downloaded sample for the selected job.

        Returns:
            str: Existing motion JSON path.
        """
        path = self.selected_job().get("paths", {}).get(self.view.sample.currentText())
        if not path or not os.path.isfile(path):
            raise ValueError("Download the results and select a motion sample first.")
        return path

    def _namespace(self, base=None):
        """Chooses an unused namespace without replacing previous imports.

        Args:
            base (str, optional): Requested prefix.

        Returns:
            str: Available namespace.
        """
        import maya.cmds as cmds

        base = base or self.view.namespace.text().strip() or "kimodo"
        candidate = base
        index = 2
        while cmds.namespace(exists=f":{candidate}"):
            candidate = f"{base}_{index}"
            index += 1
        return candidate

    def import_sample(self):
        """Imports the selected sample on the Maya main thread."""
        result = kimodo.import_motion(self._sample_path(), self._namespace(), self.view.start_frame.value())
        self.imported_group = result["group"]
        self.model.pose_group = result["group"]
        self.view.pose_source.setText(f"Pose source: {result['group']}")
        self.message(
            f"Imported {len(result['joints'])} joints, frames {result['start_frame']:g}–{result['end_frame']:g}.")

    def create_skeleton(self):
        """Creates an editable SOMA rest skeleton for pose authoring."""
        if not self.model.rest_motion:
            raise ValueError("Connect to the bridge first to load the SOMA skeleton.")
        self.save_auto_humanik()
        settings = None
        if self.view.auto_humanik.isChecked():
            self.gather_humanik()
            settings = self.model.humanik
        definition = kimodo.KimodoGenerationDefinition.from_dict(self.model.definition)
        result = definition.create_pose_skeleton(
            self.model.rest_motion, namespace=self._namespace("kimodo_pose"), humanik_settings=settings)
        self.model.pose_group = result["group"]
        self.view.pose_source.setText(f"Pose source: {result['group']}")
        state = f" HumanIK: {result['humanik']}." if result["humanik"] else ""
        self.message(f"Editable pose skeleton created.{state} Pose it in Maya, then capture each desired pose.")

    def save_auto_humanik(self):
        """Persists the local authoring option without requiring completed generation inputs."""
        if not self.loading:
            self.model.definition["maya"] = {"auto_humanik": self.view.auto_humanik.isChecked()}
            self.model.save_preferences()

    def use_selection(self):
        """Sets the pose source from the current Maya selection."""
        self.model.pose_group = kimodo.find_pose_group()
        self.view.pose_source.setText(f"Pose source: {self.model.pose_group}")

    def capture_pose(self):
        """Adds the current pose at the chosen clip frame."""
        self.gather_constraints()
        frame = self.view.pose_frame.value() - 1
        constraint = kimodo.capture_pose(self.model.pose_group or None, frame, self.view.pose_kind.currentData())
        self.model.add_constraint(constraint, f"Pose at {frame + 1}")
        self.populate_constraints()
        self.model.save_preferences()
        self.message(f"Captured pose at clip frame {frame + 1}.")

    def capture_path(self):
        """Captures selected locators or a curve using explicit destination timing."""
        import maya.cmds as cmds

        self.gather_constraints()
        constraint = kimodo.capture_root_path(cmds.ls(selection=True, long=True),
            self.parse_frames(self.view.path_frames.text()), self.model.pose_group or None)
        self.model.add_constraint(constraint, "Root path")
        self.populate_constraints()
        self.model.save_preferences()
        self.message("Root path captured in the pose skeleton's placement space.")

    def preview_pose(self):
        """Creates a separate pose preview without changing the authoring skeleton."""
        self.gather_constraints()
        row = self.view.constraints.currentRow()
        if row < 0 or not self.model.rest_motion:
            raise ValueError("Connect and select a pose constraint first.")
        kimodo.preview_pose(self.model.constraints[row]["parameters"], self.model.rest_motion,
                            namespace=self._namespace("kimodo_preview"))
        self.message("Pose preview created in a new namespace.")

    def duplicate_constraint(self):
        """Duplicates a constraint with a fresh ID and the chosen destination frame."""
        self.gather_constraints()
        row = self.view.constraints.currentRow()
        if row < 0:
            raise ValueError("Select a constraint to duplicate.")
        entry = self.model.constraints[row]
        parameters = copy.deepcopy(entry["parameters"])
        offset = self.view.pose_frame.value() - 1 - parameters["frame_indices"][0]
        parameters["frame_indices"] = [frame + offset for frame in parameters["frame_indices"]]
        self.model.add_constraint(parameters, f"{entry['name']} copy")
        self.populate_constraints()
        self.view.constraints.selectRow(len(self.model.constraints) - 1)
        self.model.save_preferences()

    def copy_constraint(self):
        """Copies the selected constraint as a portable JSON clipboard entry."""
        self.gather_constraints()
        row = self.view.constraints.currentRow()
        if row < 0:
            raise ValueError("Select a constraint to copy.")
        entry = copy.deepcopy(self.model.constraints[row])
        entry.pop("id", None)
        self._set_clipboard_payload("constraint", entry)
        self.message(f"Copied constraint: {entry['name']}")

    def paste_constraint(self):
        """Appends a copied constraint with a fresh stable identifier."""
        self.gather_constraints()
        data = self._get_clipboard_payload("constraint")
        parameters = data.get("parameters")
        if not isinstance(parameters, dict):
            raise ValueError("Copied constraint data is incomplete.")
        name = data.get("name") if isinstance(data.get("name"), str) else None
        entry = self.model.add_constraint(parameters, f"{name or parameters.get('type', 'Constraint')} copy")
        entry["enabled"] = bool(data.get("enabled", True))
        self.populate_constraints()
        self.view.constraints.selectRow(len(self.model.constraints) - 1)
        self.model.save_preferences()
        self.message(f"Pasted constraint: {entry['name']}")

    def toggle_constraint(self):
        """Toggles whether the selected constraint participates in generation."""
        self.gather_constraints()
        row = self.view.constraints.currentRow()
        if row < 0:
            raise ValueError("Select a constraint to enable or disable.")
        entry = self.model.constraints[row]
        entry["enabled"] = not entry["enabled"]
        self.populate_constraints()
        self.view.constraints.selectRow(row)
        self.model.save_preferences()
        state = "enabled" if entry["enabled"] else "disabled"
        self.message(f"Constraint {state}: {entry['name']}")

    def change_constraint_type(self, constraint_type):
        """Changes the selected pose constraint's body-part conditioning type.

        Args:
            constraint_type (str): Supported full-body, hand, or foot pose type.
        """
        pose_types = {"fullbody", "left-hand", "right-hand", "left-foot", "right-foot"}
        if constraint_type not in pose_types:
            raise ValueError(f"Unsupported pose constraint type: {constraint_type}")
        self.gather_constraints()
        row = self.view.constraints.currentRow()
        if row < 0:
            raise ValueError("Select a pose constraint to change its type.")
        entry = self.model.constraints[row]
        current_type = entry["parameters"].get("type")
        if current_type not in pose_types:
            raise ValueError("Only captured pose constraints can change pose type.")
        entry["parameters"]["type"] = constraint_type
        kimodo.validate_constraints([entry["parameters"]])
        self.populate_constraints()
        self.view.constraints.selectRow(row)
        self.model.save_preferences()
        label = constraint_type.replace("-", " ").title()
        self.message(f"Changed pose constraint type to {label}: {entry['name']}")

    def remove_constraint(self):
        """Removes only the selected in-memory authoring entry."""
        self.gather_constraints()
        row = self.view.constraints.currentRow()
        if row >= 0:
            self.model.constraints.pop(row)
            self.populate_constraints()
            self.model.save_preferences()

    def add_prompt(self):
        """Appends an editable text segment."""
        self.gather_prompts()
        self.model.definition["prompts"].append({"text": "Describe the next motion.", "duration_seconds": 2.0})
        self.populate_prompts()

    def duplicate_prompt(self):
        """Duplicates the selected prompt immediately after its source row."""
        self.gather_prompts()
        row = self.view.prompts.currentRow()
        if row < 0:
            raise ValueError("Select a prompt segment to duplicate.")
        segment = copy.deepcopy(self.model.definition["prompts"][row])
        self.model.definition["prompts"].insert(row + 1, segment)
        self.populate_prompts()
        self.view.prompts.selectRow(row + 1)
        self.model.save_preferences()

    def copy_prompt(self):
        """Copies the selected prompt segment as a portable JSON clipboard entry."""
        self.gather_prompts()
        row = self.view.prompts.currentRow()
        if row < 0:
            raise ValueError("Select a prompt segment to copy.")
        segment = copy.deepcopy(self.model.definition["prompts"][row])
        self._set_clipboard_payload("prompt", segment)
        self.message("Copied prompt segment.")

    def paste_prompt(self):
        """Inserts a copied prompt after the current row, or at the end."""
        self.gather_prompts()
        segment = self._get_clipboard_payload("prompt")
        text = segment.get("text")
        try:
            duration = float(segment.get("duration_seconds"))
        except (TypeError, ValueError) as error:
            raise ValueError("Copied prompt duration must be a positive number.") from error
        if not isinstance(text, str) or not text.strip() or not math.isfinite(duration) or duration <= 0:
            raise ValueError("Copied prompt requires motion text and a positive duration.")
        row = self.view.prompts.currentRow()
        target = row + 1 if row >= 0 else len(self.model.definition["prompts"])
        self.model.definition["prompts"].insert(
            target, {"text": text.strip(), "duration_seconds": duration})
        self.populate_prompts()
        self.view.prompts.selectRow(target)
        self.model.save_preferences()
        self.message("Pasted prompt segment.")

    def remove_prompt(self):
        """Removes a segment while retaining at least one prompt."""
        self.gather_prompts()
        row = self.view.prompts.currentRow()
        if row >= 0 and len(self.model.definition["prompts"]) > 1:
            self.model.definition["prompts"].pop(row)
            self.populate_prompts()

    def move_prompt(self, offset):
        """Moves a selected prompt without losing edited values.

        Args:
            offset (int): Relative destination row.
        """
        self.gather_prompts()
        row = self.view.prompts.currentRow()
        target = row + offset
        prompts = self.model.definition["prompts"]
        if row >= 0 and 0 <= target < len(prompts):
            prompts[row], prompts[target] = prompts[target], prompts[row]
            self.populate_prompts()
            self.view.prompts.selectRow(target)

    def prompt_up(self):
        """Moves the selected prompt one row earlier."""
        self.move_prompt(-1)

    def prompt_down(self):
        """Moves the selected prompt one row later."""
        self.move_prompt(1)

    def validate(self):
        """Validates the complete request and estimates SOMA timing."""
        self.gather()
        data = self.model.build_definition().as_dict()
        if "soma" in data["model"]:
            frames = sum(int(segment["duration_seconds"] * 30) for segment in data["prompts"])
            kimodo.validate_constraints(data["constraints"], frames)
        self.message(f"Valid request: {len(data['prompts'])} segments, {len(data['constraints'])} constraints.")

    def import_constraints(self):
        """Loads native Kimodo JSON into editable constraint rows."""
        path, unused = QtWidgets.QFileDialog.getOpenFileName(self.view, "Load Constraints", "", "JSON (*.json)")
        if path:
            self.gather_constraints()
            self.model.import_constraints(path)
            self.populate_constraints()
            self.message("Constraints loaded. Edit clip frames and enable the keys you want to use.")

    def export_constraints(self):
        """Saves enabled native constraints through a standard save dialog."""
        self.gather()
        path, unused = QtWidgets.QFileDialog.getSaveFileName(
            self.view, "Save Constraints", "constraints.json", "JSON (*.json)")
        if path:
            self.model.export_constraints(path)
            self.message("Constraints saved.")

    def load_setup(self):
        """Loads a portable authoring setup."""
        path, unused = QtWidgets.QFileDialog.getOpenFileName(self.view, "Load Kimodo Setup", "", "JSON (*.json)")
        if path:
            self.model.load_setup(path)
            self.load_widgets()
            self.message("Setup loaded.")

    def save_setup(self):
        """Saves prompt and pose authoring data."""
        self.gather()
        path, unused = QtWidgets.QFileDialog.getSaveFileName(
            self.view, "Save Kimodo Setup", "kimodo_setup.json", "JSON (*.json)")
        if path:
            self.model.save_setup(path)
            self.message("Setup saved.")

    def browse_output(self):
        """Selects a local artifact download directory."""
        path = QtWidgets.QFileDialog.getExistingDirectory(self.view, "Results Folder", self.view.output.text())
        if path:
            self.view.output.setText(path)
            self.save_output_folder()

    def save_output_folder(self):
        """Persists folder edits immediately, independently of incomplete prompt edits."""
        if self.loading:
            return
        try:
            path = self.model.set_output_directory(self.view.output.text())
        except ValueError:
            self.view.output.setText(self.model.output_directory)
            raise
        self.view.output.setText(path)
        self.message(f"Download folder saved: {path}")

    def use_cache(self):
        """Restores the PackageCache download target without deleting any files."""
        self.view.output.setText(default_download_directory())
        self.save_output_folder()

    def browse_python(self):
        """Selects an environment folder and resolves the correct executable path."""
        mode = self.view.mode.currentData()
        distribution = self.view.distribution.currentText().strip()
        current = self.view.python_path.text().strip()
        if mode == "wsl":
            if not distribution:
                raise ValueError("Query WSL and select a distribution before browsing its Python environment.")
            root = f"\\\\wsl.localhost\\{distribution}"
            initial = root + (os.path.dirname(current).replace("/", "\\") if current.startswith("/") else "\\home")
        elif mode == "native":
            initial = os.path.dirname(current) if current else os.path.expanduser("~")
        else:
            raise ValueError("Choose a local launch mode before browsing for its Python environment.")
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self.view, "Select Kimodo Python Environment Folder", initial,
            QtWidgets.QFileDialog.Option.ShowDirsOnly | QtWidgets.QFileDialog.Option.DontResolveSymlinks)
        if directory:
            def resolved(executable):
                """Stores the validated interpreter without blocking the folder dialog.

                Args:
                    executable (str): Absolute runtime Python path.
                """
                self.view.python_path.setText(executable)
                self.model.connection.update(mode=mode, python_path=executable, distribution=distribution)
                self.model.save_preferences()
                self.message(f"Kimodo Python saved: {executable}")

            self.message("Checking the selected Python environment…")
            self.run_network("browse_python", lambda: resolve_environment_python(
                directory, mode, distribution), resolved)

    def query_wsl(self):
        """Discovers WSL names asynchronously and preserves an existing selection."""
        def queried(distributions):
            """Populates the editable dropdown after Windows responds.

            Args:
                distributions (list): Installed distribution names.
            """
            combo = self.view.distribution
            current = combo.currentText().strip()
            blocker = QtCore.QSignalBlocker(combo)
            try:
                combo.clear()
                combo.addItems(distributions)
                if current:
                    combo.setCurrentText(current)
            finally:
                del blocker
            if not distributions:
                self.message("No WSL distributions found. Install one, or choose another connection mode.",
                             warning=True)
                return
            self.save_wsl_distribution()
            self.message(f"Found {len(distributions)} WSL distribution(s). Choose the one containing Kimodo.")
        self.message("Querying installed WSL distributions…")
        self.run_network("query_wsl", query_wsl_distributions, queried)

    def open_folder(self):
        """Opens the selected job's existing download folder."""
        path = self.selected_job().get("paths", {}).get("result.json")
        if not path or not os.path.isfile(path):
            raise ValueError("Download the job first.")
        ui_qt.QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(os.path.dirname(path)))

    def gather_humanik(self):
        """Validates the optional HumanIK fields independently of generation inputs."""
        frame = self.view.hik_frame.text().strip()
        self.model.humanik = humanik.validate_settings({
            "character_name": self.view.hik_name.text(), "definition_path": self.view.hik_xml.text(),
            "tpose_path": self.view.hik_pose.text(), "reference_frame": float(frame) if frame else None,
            "lock_definition": self.view.hik_lock.isChecked()})

    def save_humanik_settings(self):
        """Persists valid overrides without requiring complete generation fields."""
        if not self.loading:
            self.gather_humanik()
            self.model.save_preferences()

    def browse_hik_xml(self):
        """Chooses an optional native HumanIK Match List XML definition."""
        path, unused = QtWidgets.QFileDialog.getOpenFileName(
            self.view, "HumanIK Definition", self.view.hik_xml.text(), "HumanIK XML (*.xml)")
        if path:
            self.view.hik_xml.setText(path)
            self.save_humanik_settings()

    def browse_hik_pose(self):
        """Chooses an optional batch-processor/core.pose T-pose JSON file."""
        path, unused = QtWidgets.QFileDialog.getOpenFileName(
            self.view, "HumanIK T-pose", self.view.hik_pose.text(), "Pose JSON (*.pose *.json)")
        if path:
            self.view.hik_pose.setText(path)
            self.save_humanik_settings()

    def create_humanik(self):
        """Characterizes the selected import, or the latest import when nothing is selected."""
        self.gather_humanik()
        self.model.save_preferences()
        result = humanik.create_definition(self.humanik_source(), self.model.humanik)
        state = "locked" if result["locked"] else "unlocked"
        self.message(f"HumanIK {result['character']}: {result['mapped_joints']} joints mapped, {state}. "
                     "Animation preserved. Open Maya HumanIK to use the character.")

    def humanik_source(self):
        """Gets the selected import or latest imported sample.

        Returns:
            str: Source group or joint to resolve within the Kimodo hierarchy.
        """
        import maya.cmds as cmds

        selection = cmds.ls(selection=True, long=True) or []
        if len(selection) > 1:
            raise ValueError("Select one imported Kimodo group or joint for HumanIK.")
        target = selection[0] if selection else (self.model.pose_group or self.imported_group)
        if not target:
            raise ValueError("Import a sample first, or select an existing Kimodo group or joint.")
        return target


    def humanik_export_path(self, title, extension):
        """Requests an output filename and confirms any existing final target.

        Args:
            title (str): Dialog caption.
            extension (str): Required default extension including dot.

        Returns:
            str: Confirmed path, or empty when canceled.
        """
        path, unused = QtWidgets.QFileDialog.getSaveFileName(
            self.view, title, "", f"HumanIK (*{extension})")
        if not path:
            return ""
        if not path.lower().endswith(extension):
            path += extension
        if os.path.exists(path) and not self.confirm_humanik(f"Replace the existing file?\n{path}"):
            return ""
        return path

    def confirm_humanik(self, text):
        """Confirms a scene or file change with Cancel as the default.

        Args:
            text (str): Scope and consequences of the action.

        Returns:
            bool: Whether the user confirmed.
        """
        buttons = QtWidgets.QMessageBox.StandardButton
        return QtWidgets.QMessageBox.question(
            self.view, "HumanIK", text, buttons.Ok | buttons.Cancel, buttons.Cancel) == buttons.Ok

    def hik_export_pose(self):
        """Exports the current source pose and stores it as the T-pose override."""
        source = self.humanik_source()
        hik_tools.source_joints(source)
        path = self.humanik_export_path("Export Pose", ".pose")
        if path:
            hik_tools.export_pose(source, path)
            self.view.hik_frame.clear()
            self.view.hik_pose.setText(path)
            self.save_humanik_settings()
            self.message(f"Exported current pose and set T-pose override: {path}")

    def hik_export_source(self):
        """Exports the source's attached definition and stores the XML override."""
        character = hik_tools.source_character(self.humanik_source())
        path = self.humanik_export_path("Export Source HIK", ".xml")
        if path:
            hik_tools.export_definition(character, path)
            self.view.hik_xml.setText(path)
            self.save_humanik_settings()
            self.message(f"Exported source HumanIK: {path}")


    def hik_apply_pose(self):
        """Tests the default/custom source pose with explicit approval to change this frame."""
        self.gather_humanik()
        source = self.humanik_source()
        hik_tools.source_joints(source)
        if self.confirm_humanik("Apply the HumanIK reference pose to this source? Animated channels receive "
                                "new/replaced keys at the current Maya frame. Other existing keys are kept, "
                                "but interpolation between keys can change. "
                                "Use Maya Undo to revert."):
            count = hik_tools.apply_pose(source, self.model.humanik)
            self.message(f"Applied reference pose to {count} joints at the current frame. Maya Undo can revert it.")

    def hik_import_source(self):
        """Tests source characterization with automatic defaults or supplied overrides."""
        self.create_humanik()


    def reset(self):
        """Resets editable preferences while preserving job history."""
        jobs = self.model.jobs
        self.model.reset()
        self.model.jobs = jobs
        self.load_widgets()
        self.model.save_preferences()
        self.message("Settings reset. Generated files and job history were retained.")

    def help(self):
        """Opens the local detailed guide or packaged documentation fallback."""
        repository = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        guide = os.path.join(os.path.dirname(repository), "assets", "kimodo", "kimodo.md")
        if not os.path.isfile(guide):
            guide = os.path.join(repository, "docs", "README.md")
        ui_qt.QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(guide))

    def close(self):
        """Stops polling and saves edits; generation continues in the bridge."""
        if self.closed:
            return
        self._stop_polling()
        if not self._view_is_valid():
            self._view_destroyed()
            return
        try:
            self.gather()
            self.model.save_preferences()
        except (ValueError, TypeError, AttributeError) as error:
            logger.warning("Could not save incomplete Kimodo edits: %s", error)
        self.closed = True
