"""Maya actions and asynchronous HTTP orchestration for Kimodo Generator."""

import copy
import datetime
import functools
import html
import json
import math
import os
import re
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
from gt.tools.kimodo_generator.kimodo_generator_help import ACTION_TOOLTIPS, TABLE_ACTION_TOOLTIPS
from gt.tools.kimodo_generator.kimodo_generator_model import (
    KimodoGeneratorModel, default_download_directory, query_wsl_distributions, resolve_environment_python,
)

QtWidgets = ui_qt.QtWidgets
QtCore = ui_qt.QtCore
logger = logging.getLogger(__name__)


class _CenteredCheckBoxCell(QtWidgets.QWidget):
    """Centers a checkbox within a resizable table cell."""

    def __init__(self, parent=None):
        """Creates a cell widget with one checkbox.

        Args:
            parent (QWidget, optional): Parent table.
        """
        super().__init__(parent)
        self.checkbox = QtWidgets.QCheckBox(self)
        self._position_checkbox()

    def _position_checkbox(self):
        """Centers the checkbox using its style-aware size hint."""
        size = self.checkbox.sizeHint()
        x_position = max(0, int((self.width() - size.width()) / 2))
        y_position = max(0, int((self.height() - size.height()) / 2))
        self.checkbox.setGeometry(x_position, y_position, size.width(), size.height())

    def resizeEvent(self, event):
        """Re-centers the checkbox when the table cell is resized.

        Args:
            event (QResizeEvent): Cell resize event.
        """
        self._position_checkbox()
        super().resizeEvent(event)


class _CenteredIconTextDelegate(QtWidgets.QStyledItemDelegate):
    """Paints a constraint icon and label together, centered in their table cell."""

    def paint(self, painter, option, index):
        """Draws selection/background through Qt, then centers the icon-label pair.

        Args:
            painter (QPainter): Active item painter.
            option (QStyleOptionViewItem): Style and geometry for the cell.
            index (QModelIndex): Model index supplying display text and icon.
        """
        style = option.widget.style() if option.widget else QtWidgets.QApplication.style()
        background_option = QtWidgets.QStyleOptionViewItem(option)
        background_option.text = ""
        background_option.icon = ui_qt.QtGui.QIcon()
        style.drawControl(QtWidgets.QStyle.ControlElement.CE_ItemViewItem,
                          background_option, painter, option.widget)

        text = str(index.data(QtCore.Qt.ItemDataRole.DisplayRole) or "")
        icon = index.data(QtCore.Qt.ItemDataRole.DecorationRole)
        icon_size = option.decorationSize
        icon_width = max(1, icon_size.width())
        icon_height = max(1, icon_size.height())
        spacing = 5 if text and icon else 0
        text_width = option.fontMetrics.horizontalAdvance(text)
        group_width = min(option.rect.width(), icon_width + spacing + text_width)
        text_width = max(0, group_width - icon_width - spacing)
        left = option.rect.x() + max(0, (option.rect.width() - group_width) // 2)

        painter.save()
        if icon:
            icon_rect = QtCore.QRect(left, option.rect.y() + (option.rect.height() - icon_height) // 2,
                                     icon_width, icon_height)
            icon.paint(painter, icon_rect, QtCore.Qt.AlignmentFlag.AlignCenter)
        text_rect = QtCore.QRect(left + icon_width + spacing, option.rect.y(), text_width, option.rect.height())
        selected = bool(option.state & QtWidgets.QStyle.StateFlag.State_Selected)
        role = (ui_qt.QtGui.QPalette.ColorRole.HighlightedText if selected
                else ui_qt.QtGui.QPalette.ColorRole.Text)
        painter.setPen(option.palette.color(role))
        display_text = option.fontMetrics.elidedText(text, QtCore.Qt.TextElideMode.ElideRight, text_width)
        painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignLeft,
                         display_text)
        painter.restore()


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
        self.prompt_display_fps = 30.0
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
        view.constraints.setItemDelegateForColumn(2, _CenteredIconTextDelegate(view.constraints))
        view.constraints.horizontalHeader().sectionResized.connect(self.schedule_center_constraint_checkboxes)
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
        view.limit_body_joint_translations.toggled.connect(self._action_callback("save_auto_humanik"))
        view.template_pose_previews.toggled.connect(self._action_callback("save_pose_preview_template"))
        view.pose_frame.customContextMenuRequested.connect(self.show_pose_frame_context_menu)
        view.path_frames.textChanged.connect(self.update_path_sample_controls)
        view.path_curve_samples.valueChanged.connect(self._action_callback("save_path_curve_samples"))
        view.prompt_frames.toggled.connect(self._action_callback("set_prompt_duration_mode"))
        view.model.currentIndexChanged.connect(self._action_callback("generation_model_changed"))
        view.auto_download.toggled.connect(self._action_callback("save_auto_download"))
        view.auto_maya_file.toggled.connect(self._action_callback("save_auto_maya_file"))
        view.auto_import_maya.toggled.connect(self._action_callback("save_auto_import_maya"))
        view.auto_import_all_samples.toggled.connect(self._action_callback("save_auto_import_all_samples"))
        view.auto_clear_scene.toggled.connect(self._action_callback("save_auto_clear_scene"))
        view.auto_frame_rate.toggled.connect(self._action_callback("save_auto_frame_rate"))
        view.auto_frame_range.toggled.connect(self._action_callback("save_auto_frame_range"))
        view.show_console.toggled.connect(self._action_callback("save_show_console"))
        view.auto_connect.toggled.connect(self._action_callback("save_auto_connect"))
        self.timer = QtCore.QTimer(view)
        self.timer.setInterval(1500)
        self.timer.timeout.connect(self.poll_jobs)
        self.load_widgets()
        self.timer.start()
        self.view.show()
        if self.view.auto_connect.isChecked():
            QtCore.QTimer.singleShot(0, self.auto_connect_on_launch)

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

    def save_auto_connect(self):
        """Persists whether the bridge connection action runs when the tool opens."""
        if not self.loading:
            self.model.connection["auto_connect"] = self.view.auto_connect.isChecked()
            self.model.save_preferences()

    def auto_connect_on_launch(self):
        """Runs the normal Connect / Start action when the saved option is enabled."""
        if self.closed or not self._view_is_valid() or not self.view.auto_connect.isChecked():
            return
        try:
            self.connect_bridge()
        except (ValueError, FileNotFoundError) as warning:
            logger.warning("%s", warning)
            self.message(str(warning), warning=True)

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
        if table.horizontalHeader().sectionResizeMode(unused_column) == QtWidgets.QHeaderView.ResizeMode.Stretch:
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
        self.fit_jobs_table_width()
        self.fit_constraints_table_width()

    def fit_jobs_table_width(self):
        """Fits the Results table's final column to the available viewport width."""
        self._fit_table_to_viewport(self.view.jobs, "jobs", "Stage / Model")

    def fit_constraints_table_width(self):
        """Fits the Constraints table's name column to the available viewport width."""
        self._fit_table_to_viewport(self.view.constraints, "constraints", "Name")
        self.center_constraint_checkboxes()
        self.schedule_center_constraint_checkboxes()

    def schedule_center_constraint_checkboxes(self, *unused):
        """Defers checkbox centering until Qt finishes updating index-widget geometry.

        Args:
            *unused: Optional header-resize signal arguments.
        """
        if not self.closed:
            QtCore.QTimer.singleShot(0, self.center_constraint_checkboxes)

    def center_constraint_checkboxes(self, *unused):
        """Keeps Use checkboxes centered after table and column layout changes.

        Args:
            *unused: Optional header-resize signal arguments.
        """
        if self.closed or not qt_utils.is_qt_object_valid(self.view.constraints):
            return
        for row in range(self.view.constraints.rowCount()):
            cell = self.view.constraints.cellWidget(row, 0)
            if isinstance(cell, _CenteredCheckBoxCell):
                cell._position_checkbox()

    def _fit_table_to_viewport(self, table, preference_key, last_column_label):
        """Keeps a table within its viewport while preserving saved fixed widths.

        The final column fills the available remainder. Earlier columns retain saved
        widths where possible, but shrink proportionally on narrower displays.

        Args:
            table (QTableWidget): Table to constrain.
            preference_key (str): Persistent width entry for the table.
            last_column_label (str): Header text used to size the final column.
        """
        if not qt_utils.is_qt_object_valid(table) or table.columnCount() < 2:
            return

        last_column = table.columnCount() - 1
        viewport_width = table.viewport().width()
        if viewport_width <= 0:
            return

        header = table.horizontalHeader()
        metrics = table.fontMetrics()
        minimum_last_width = metrics.horizontalAdvance(last_column_label) + max(24, metrics.height())
        available_fixed_width = max(1, viewport_width - minimum_last_width)
        saved_widths = self.model.table_widths.get(preference_key, [])
        preferred_widths = []
        for column in range(last_column):
            try:
                saved_width = int(saved_widths[column]) if len(saved_widths) == table.columnCount() else 0
            except (TypeError, ValueError):
                saved_width = 0
            preferred_widths.append(saved_width if saved_width > 0 else max(1, table.columnWidth(column)))

        preferred_total = sum(preferred_widths)
        if preferred_total > available_fixed_width:
            ratio = available_fixed_width / float(preferred_total)
            fixed_widths = [max(1, int(width * ratio)) for width in preferred_widths]
            overflow = sum(fixed_widths) - available_fixed_width
            for index in reversed(range(len(fixed_widths))):
                if overflow <= 0:
                    break
                reduction = min(overflow, max(0, fixed_widths[index] - 1))
                fixed_widths[index] -= reduction
                overflow -= reduction
        else:
            fixed_widths = preferred_widths

        table.setProperty("gt_adjusting_columns", True)
        try:
            for column, width in enumerate(fixed_widths):
                header.setSectionResizeMode(column, QtWidgets.QHeaderView.ResizeMode.Interactive)
                table.setColumnWidth(column, width)
            header.setSectionResizeMode(last_column, QtWidgets.QHeaderView.ResizeMode.Stretch)
        finally:
            table.setProperty("gt_adjusting_columns", False)

    @staticmethod
    def _add_menu_action(menu, label, callback, enabled=True, icon_path=None, tooltip=None):
        """Adds one consistently configured table-menu action.

        Args:
            menu (QMenu): Parent context menu.
            label (str): User-facing action text.
            callback (callable): Slot invoked when the action is selected.
            enabled (bool): Whether the action can currently run.
            icon_path (str, optional): Icon resource path.
            tooltip (str, optional): Detailed action help.

        Returns:
            QAction: Created menu action.
        """
        action = menu.addAction(label)
        if icon_path:
            action.setIcon(ui_qt.QtGui.QIcon(icon_path))
        if tooltip:
            action.setToolTip(tooltip)
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
            current_type = None
            if selected and row < len(self.model.constraints):
                current_type = self.model.constraints[row]["parameters"].get("type")
            pose_types = ("fullbody", "left-hand", "right-hand", "left-foot", "right-foot")
            self._add_menu_action(menu, "Preview Pose", invoke("preview_pose"),
                                  selected and current_type in pose_types,
                                  resources.Icon.ui_open, ACTION_TOOLTIPS["preview_pose"])
            self._add_menu_action(
                menu, "Preview Root Path", invoke("preview_root_path"),
                selected and current_type == "root2d", resources.Icon.kimodo_action_preview_path,
                TABLE_ACTION_TOOLTIPS["preview_root_path"])
            self._add_menu_action(menu, "Enable / Disable", invoke("toggle_constraint"), selected,
                                  resources.Icon.ui_toggle_disabled)
            pose_types = (("Full Body", "fullbody"), ("Left Hand", "left-hand"),
                          ("Right Hand", "right-hand"), ("Left Foot", "left-foot"),
                          ("Right Foot", "right-foot"))
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
            self._add_menu_action(menu, "Load Constraints JSON", invoke("import_constraints"),
                                  icon_path=resources.Icon.rigger_action_import_grayscale,
                                  tooltip=ACTION_TOOLTIPS["import_constraints"])
            self._add_menu_action(menu, "Save Constraints JSON", invoke("export_constraints"),
                                  icon_path=resources.Icon.rigger_action_export_grayscale,
                                  tooltip=ACTION_TOOLTIPS["export_constraints"])
            menu.addSeparator()
            self._add_menu_action(menu, "Duplicate Constraint", invoke("duplicate_constraint"), selected,
                                  resources.Icon.rigger_action_duplicate_grayscale,
                                  ACTION_TOOLTIPS["duplicate_constraint"])
            self._add_menu_action(menu, "Copy Constraint", invoke("copy_constraint"), selected,
                                  resources.Icon.rigger_action_copy_grayscale)
            self._add_menu_action(menu, "Paste Constraint", invoke("paste_constraint"),
                                  icon_path=resources.Icon.rigger_action_paste_grayscale)
            menu.addSeparator()
            self._add_menu_action(menu, "Remove All Constraints", invoke("remove_all_constraints"),
                                  bool(self.model.constraints), resources.Icon.ui_trash,
                                  ACTION_TOOLTIPS["remove_all_constraints"])
            menu.addSeparator()
            self._add_menu_action(menu, "Remove Constraint", invoke("remove_constraint"), selected,
                                  resources.Icon.ui_trash, ACTION_TOOLTIPS["remove_constraint"])
        elif name == "jobs":
            job = self.model.jobs[row] if selected and row < len(self.model.jobs) else None
            terminal = bool(job and job.get("status") in kimodo.TERMINAL_STATUSES)
            generation = bool(job and job.get("operation") != "download_model")
            succeeded = bool(job and job.get("status") == "succeeded")
            self._add_menu_action(menu, "Refresh Job", invoke("refresh_job"), selected,
                                  resources.Icon.tool_package_updater)
            self._add_menu_action(menu, "Cancel Job", invoke("cancel_job"), selected and not terminal,
                                  resources.Icon.setup_close)
            menu.addSeparator()
            self._add_menu_action(menu, "Download / Repair Results", invoke("download_results"),
                                  succeeded and generation, resources.Icon.rigger_action_import_grayscale)
            self._add_menu_action(menu, "Create / Repair Maya Files", invoke("create_maya_files"),
                                  succeeded and generation, resources.Icon.ui_new)
            self._add_menu_action(menu, "Import Generated Maya File", invoke("import_maya_file"),
                                  bool(job and job.get("maya_files")), resources.Icon.rigger_action_import_grayscale)
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
        view.auto_connect.setChecked(settings.get("auto_connect", False))
        view.token.setText(self.model.token)
        view.prompt_frames.setChecked(self.model.prompt_durations_in_frames)
        self.populate_models()
        self.prompt_display_fps = self._model_fps(model_id=self.model.definition.get("model"))
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
        view.path_curve_samples.setValue(self.model.path_curve_samples)
        self.update_path_sample_controls()
        hik = self.model.humanik
        view.hik_name.setText(hik["character_name"])
        view.hik_xml.setText(hik["definition_path"])
        view.hik_pose.setText(hik["tpose_path"])
        view.hik_frame.setText("" if hik["reference_frame"] is None else str(hik["reference_frame"]))
        view.hik_lock.setChecked(hik["lock_definition"])
        view.auto_humanik.setChecked(self.model.definition["maya"]["auto_humanik"])
        view.limit_body_joint_translations.setChecked(
            self.model.definition["maya"]["limit_body_joint_translations"])
        view.template_pose_previews.setChecked(self.model.pose_previews_template)
        view.auto_download.setChecked(self.model.auto_download)
        view.auto_maya_file.setChecked(self.model.auto_maya_file)
        view.auto_import_maya.setChecked(self.model.auto_import_maya)
        view.auto_import_all_samples.setChecked(self.model.auto_import_all_samples)
        view.auto_clear_scene.setChecked(self.model.auto_clear_scene)
        view.auto_frame_rate.setChecked(self.model.auto_frame_rate)
        view.auto_frame_range.setChecked(self.model.auto_frame_range)
        for widget in (view.auto_import_all_samples, view.auto_clear_scene,
                       view.auto_frame_rate, view.auto_frame_range):
            widget.setEnabled(self.model.auto_import_maya)
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
        self.model.path_curve_samples = view.path_curve_samples.value()
        self.gather_humanik()

    def gather_prompts(self):
        """Copies only editable prompt rows into the model."""
        view = self.view
        prompts = []
        for row in range(view.prompts.rowCount()):
            duration = view.prompts.item(row, 0).text()
            prompts.append({"duration_seconds": self._read_prompt_duration(duration),
                            "text": view.prompts.item(row, 1).text()})
        self.model.definition["prompts"] = prompts

    def _read_prompt_duration(self, value):
        """Converts the visible duration cell into the seconds stored by Kimodo.

        Args:
            value (str): Editable seconds or frame count.

        Returns:
            float: Duration in seconds.

        Raises:
            ValueError: When the duration is not numeric or frame mode has a non-integer value.
        """
        try:
            duration = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError("Prompt durations must be numeric.") from error
        if not self.model.prompt_durations_in_frames:
            return duration
        if not math.isfinite(duration) or duration < 1 or not duration.is_integer():
            raise ValueError("Frame durations must be positive whole numbers.")
        frame_count = int(duration)
        seconds = frame_count / self.prompt_display_fps
        # Kimodo truncates seconds * fps. Avoid binary rounding losing the last frame.
        if int(seconds * self.prompt_display_fps) < frame_count:
            seconds = math.nextafter(seconds, math.inf)
        return seconds

    def set_prompt_duration_mode(self):
        """Changes the prompt editor unit without changing the seconds-based request."""
        if self.loading:
            return
        requested_mode = self.view.prompt_frames.isChecked()
        try:
            self.gather_prompts()
        except ValueError:
            blocker = QtCore.QSignalBlocker(self.view.prompt_frames)
            self.view.prompt_frames.setChecked(self.model.prompt_durations_in_frames)
            del blocker
            raise
        self.model.prompt_durations_in_frames = requested_mode
        self.prompt_display_fps = self._model_fps(model_id=self.view.model.currentData())
        self.populate_prompts()
        self.model.save_preferences()
        self.update_project_summary()

    def generation_model_changed(self):
        """Keeps prompt seconds stable while the displayed model-frame rate changes."""
        model_id = self.view.model.currentData() or kimodo.DEFAULT_MODEL
        if self.loading:
            self.prompt_display_fps = self._model_fps(model_id=model_id)
            return
        previous_model = self.model.definition.get("model")
        try:
            self.gather_prompts()
        except ValueError:
            blocker = QtCore.QSignalBlocker(self.view.model)
            self.view.model.setCurrentIndex(max(0, self.view.model.findData(previous_model)))
            del blocker
            raise
        self.model.definition["model"] = model_id
        self.prompt_display_fps = self._model_fps(model_id=model_id)
        self.populate_prompts()
        self.model.save_preferences()
        self.update_project_summary()

    def gather_connection(self):
        """Copies only server fields so connection management ignores unfinished generation edits."""
        view = self.view
        self.model.connection.update(url=view.url.text().strip(), mode=view.mode.currentData(),
                                     python_path=view.python_path.text().strip(),
                                     distribution=view.distribution.currentText().strip(),
                                     device=view.device.currentText(),
                                     text_encoder_url=view.encoder_url.text().strip(),
                                     start_encoder=view.start_encoder.isChecked(),
                                     show_console=view.show_console.isChecked(),
                                     auto_connect=view.auto_connect.isChecked())
        self.model.token = view.token.text()
        self.tokens_by_url[view.url.text().strip().rstrip("/")] = self.model.token
        self.model.save_preferences()

    def gather_constraints(self):
        """Applies edited names, enabled states, and one-based UI timing."""
        for row, entry in enumerate(self.model.constraints):
            table = self.view.constraints
            entry["enabled"] = self.constraint_is_enabled(row)
            entry["name"] = table.item(row, 3).text()
            frames = self.parse_frames(table.item(row, 1).text())
            if len(frames) != len(entry["parameters"]["frame_indices"]):
                raise ValueError("Keep the same number of keys when retiming a constraint row.")
            entry["parameters"]["frame_indices"] = frames

    def constraint_is_enabled(self, row):
        """Reads the single checkbox widget that represents a constraint's Use state.

        Args:
            row (int): Constraint table row.

        Returns:
            bool: Whether the row's Use checkbox is checked.
        """
        cell = self.view.constraints.cellWidget(row, 0)
        return bool(cell and cell.checkbox.isChecked())

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

    def _generation_frame_count(self, definition):
        """Estimates generated clip length using selected-model metadata when available.

        Args:
            definition (dict): Current generation request.

        Returns:
            int: Expected number of model frames.
        """
        model_id = definition.get("model")
        model_fps = self._model_fps(model_id=model_id)
        return sum(int(segment["duration_seconds"] * model_fps) for segment in definition["prompts"])

    def _model_fps(self, model_id=None):
        """Resolves the selected model's frame rate with Kimodo's 30 FPS fallback.

        Args:
            model_id (str, optional): Model identifier. The current selection is used by default.

        Returns:
            float: Positive finite model frame rate.
        """
        model_id = model_id or self.view.model.currentData() or self.model.definition.get("model")
        model_info = next((item for item in self.model.capabilities.get("models", [])
                           if item.get("id") == model_id), {})
        try:
            model_fps = float(model_info.get("fps", 30.0))
        except (TypeError, ValueError):
            model_fps = 30.0
        if not math.isfinite(model_fps) or model_fps <= 0:
            model_fps = 30.0
        return model_fps

    def populate_prompts(self):
        """Displays the ordered prompt segments."""
        table = self.view.prompts
        duration_header = "Frames" if self.model.prompt_durations_in_frames else "Seconds"
        table.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem(duration_header))
        table.horizontalHeaderItem(0).setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        table.horizontalHeaderItem(0).setToolTip(table.toolTip())
        fps = self._model_fps(model_id=self.view.model.currentData())
        table.setRowCount(len(self.model.definition["prompts"]))
        for row, segment in enumerate(self.model.definition["prompts"]):
            duration = int(segment["duration_seconds"] * fps) if self.model.prompt_durations_in_frames \
                else segment["duration_seconds"]
            duration_item = QtWidgets.QTableWidgetItem(str(duration))
            duration_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 0, duration_item)
            table.setItem(row, 1, QtWidgets.QTableWidgetItem(segment["text"]))
        self.view.fit_table_columns(table)

    def populate_models(self):
        """Displays discovered models while preserving an explicitly saved model."""
        combo = self.view.model
        current = self.model.definition["model"]
        blocker = QtCore.QSignalBlocker(combo)
        try:
            combo.clear()
            for info in self.model.capabilities.get("models", []):
                suffix = "cached config" if info.get("cached") else "download on first use"
                combo.addItem(f"{info['name']} ({suffix})", info["id"])
            if combo.findData(current) < 0:
                combo.addItem(current, current)
            combo.setCurrentIndex(combo.findData(current))
        finally:
            del blocker
        if not self.loading:
            new_fps = self._model_fps(model_id=combo.currentData())
            if new_fps != self.prompt_display_fps:
                self.gather_prompts()
                self.prompt_display_fps = new_fps
                if self.model.prompt_durations_in_frames:
                    self.populate_prompts()

    def populate_constraints(self):
        """Displays stable authoring entries with editable timing and labels."""
        table = self.view.constraints
        selected = table.currentRow()
        table.setRowCount(len(self.model.constraints))
        table.horizontalHeaderItem(1).setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        table.horizontalHeaderItem(2).setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        for row, entry in enumerate(self.model.constraints):
            check = QtWidgets.QTableWidgetItem()
            check.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable)
            check.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 0, check)
            checkbox_cell = _CenteredCheckBoxCell(table)
            checkbox = checkbox_cell.checkbox
            checkbox.setChecked(entry["enabled"])
            checkbox.clicked.connect(lambda unused=False, active_row=row: table.selectRow(active_row))
            checkbox.toggled.connect(self.update_project_summary)
            table.setCellWidget(row, 0, checkbox_cell)
            checkbox_cell._position_checkbox()
            frame_item = QtWidgets.QTableWidgetItem(
                ", ".join(str(frame + 1) for frame in entry["parameters"]["frame_indices"]))
            frame_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 1, frame_item)
            constraint_type = entry["parameters"]["type"]
            icon_paths = {
                "fullbody": resources.Icon.kimodo_constraint_body,
                "left-hand": resources.Icon.kimodo_constraint_hand,
                "right-hand": resources.Icon.kimodo_constraint_hand,
                "left-foot": resources.Icon.kimodo_constraint_foot,
                "right-foot": resources.Icon.kimodo_constraint_foot,
                "root2d": resources.Icon.kimodo_constraint_path,
            }
            type_labels = {
                "fullbody": "Full Body",
                "left-hand": "Left Hand",
                "right-hand": "Right Hand",
                "left-foot": "Left Foot",
                "right-foot": "Right Foot",
                "root2d": "Root Path",
            }
            kind = QtWidgets.QTableWidgetItem(type_labels.get(constraint_type, constraint_type))
            kind.setFlags(kind.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            kind.setIcon(ui_qt.QtGui.QIcon(icon_paths.get(constraint_type, resources.Icon.kimodo_constraint_body)))
            kind.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            kind.setToolTip(f"{type_labels.get(constraint_type, constraint_type)} constraint")
            table.setItem(row, 2, kind)
            name = QtWidgets.QTableWidgetItem(entry["name"])
            name.setToolTip(entry["name"])
            table.setItem(row, 3, name)
        if table.rowCount():
            table.selectRow(min(max(selected, 0), table.rowCount() - 1))
        self.view.fit_table_columns(table)
        self.fit_constraints_table_width()

    def populate_jobs(self):
        """Updates job history without changing the selected job."""
        if self.closed or not self._results_view_is_valid():
            self._view_destroyed()
            return
        table = self.view.jobs
        selected = table.currentRow()
        for column in (0, 1):
            table.horizontalHeaderItem(column).setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        table.blockSignals(True)
        table.setRowCount(len(self.model.jobs))
        for row, job in enumerate(self.model.jobs):
            submitted = self._format_submitted_time(job.get("submitted_at"))
            status = job_results.display_status(job).replace("_", " ").title()
            values = (job["job_id"][:12], submitted, status, job_results.display_stage_and_request(job))
            for column, text in enumerate(values):
                item = QtWidgets.QTableWidgetItem(text)
                if column in (0, 1, 2):
                    item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                elif column == 3:
                    item.setToolTip(text)
                table.setItem(row, column, item)
        if table.rowCount():
            table.selectRow(min(selected if selected >= 0 else table.rowCount() - 1, table.rowCount() - 1))
        table.blockSignals(False)
        self.view.fit_table_columns(table)
        self.fit_jobs_table_width()
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
            if self.constraint_is_enabled(row):
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
            f"Maya + HIK {'on' if view.auto_maya_file.isChecked() else 'off'}, "
            f"import {'all samples' if view.auto_import_all_samples.isChecked() else 'selected sample'} "
            f"({'on' if view.auto_import_maya.isChecked() else 'off'}), "
            f"force-clear {'on' if view.auto_clear_scene.isChecked() else 'off'}, "
            f"frame-rate match {'on' if view.auto_frame_rate.isChecked() else 'off'}, "
            f"frame-range match {'on' if view.auto_frame_range.isChecked() else 'off'}<br>"
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
        for key in ("cleanup_error", "download_error", "refresh_error", "maya_export_error", "maya_import_error"):
            if job.get(key):
                text += f"\n{job[key]}"
        imported_files = job.get("maya_imported_files") or {}
        if len(imported_files) > 1:
            text += "\nImported Maya files:\n" + "\n".join(imported_files.values())
        elif job.get("maya_imported"):
            text += f"\nImported Maya file: {job['maya_imported']}"
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
        definition_data = definition.as_dict()
        frame_count = self._generation_frame_count(definition_data)
        kimodo.validate_constraints(definition_data["constraints"], frame_count)
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

    def randomize_seed(self):
        """Writes a new unsigned 32-bit seed into the generation settings.

        Returns:
            int: Seed written to the Seed field.
        """
        import secrets

        seed = secrets.randbits(32)
        self.view.seed.setText(str(seed))
        self.message(f"Random seed selected: {seed}.")
        return seed

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

    def import_maya_file(self):
        """Imports the selected job's generated Maya file without clearing the current scene."""
        self.import_generated_maya_file(self.selected_job())

    def import_generated_maya_file(self, job, automatic=False):
        """Imports a generated Maya scene, optionally force-clearing first.

        Args:
            job (dict): Completed generation job containing exported Maya files.
            automatic (bool): Whether the persistent automatic scene-clear option applies.

        Returns:
            str: Absolute path imported first into the current Maya scene.
        """
        maya_files = job.get("maya_files") or {}
        if not maya_files:
            raise ValueError("Create Maya Files first; this job has no generated Maya scene.")

        import_all_samples = automatic and self.model.auto_import_all_samples
        if import_all_samples:
            sample_names = sorted(maya_files, key=lambda name: (name != "motion.json", name))
        else:
            sample_name = None
            try:
                if self.selected_job() is job:
                    sample_name = self.view.sample.currentText()
            except ValueError:
                pass
            if sample_name not in maya_files:
                sample_name = "motion.json" if "motion.json" in maya_files else sorted(maya_files)[0]
            sample_names = [sample_name]

        paths = {}
        for sample_name in sample_names:
            path = os.path.abspath(maya_files[sample_name])
            if not os.path.isfile(path) or os.path.splitext(path)[1].lower() != ".ma":
                raise ValueError(f"Generated Maya file is missing or invalid: {path}")
            paths[sample_name] = path

        import maya.cmds as cmds

        motion_metadata = None
        metadata_error = None
        if automatic and (self.model.auto_frame_rate or self.model.auto_frame_range):
            motion_path = job.get("paths", {}).get(sample_names[0])
            try:
                from gt.core.io import read_json_dict

                if not motion_path or not os.path.isfile(motion_path):
                    raise ValueError("The matching downloaded motion JSON is unavailable.")
                motion = read_json_dict(motion_path)
                kimodo.validate_motion(motion)
                motion_metadata = {"fps": motion["fps"], "frame_count": motion["frame_count"]}
            except Exception as error:
                metadata_error = str(error)

        clear_scene = automatic and self.model.auto_clear_scene
        if clear_scene:
            cmds.file(new=True, force=True)
        use_sample_namespaces = import_all_samples and len(sample_names) > 1
        for sample_name in sample_names:
            import_options = {"i": True, "type": "mayaAscii", "ignoreVersion": True,
                              "mergeNamespacesOnClash": False}
            if use_sample_namespaces:
                requested_namespace = self.view.namespace.text().strip() or "kimodo"
                base = re.sub(r"[^A-Za-z0-9_]+", "_", requested_namespace)
                sample = re.sub(r"[^A-Za-z0-9_]+", "_", os.path.splitext(sample_name)[0])
                namespace = f"{base}_{sample}".strip("_") or "kimodo_sample"
                if namespace[0].isdigit():
                    namespace = f"kimodo_{namespace}"
                import_options["namespace"] = self._namespace(namespace)
            cmds.file(paths[sample_name], **import_options)
        adjustments = []
        if automatic and motion_metadata:
            if self.model.auto_frame_rate:
                cmds.currentUnit(time=f"{motion_metadata['fps']:g}fps", updateAnimation=False)
                adjustments.append(f"{motion_metadata['fps']:g} FPS")
            if self.model.auto_frame_range:
                end_frame = motion_metadata["frame_count"]
                cmds.playbackOptions(minTime=1, maxTime=end_frame,
                                     animationStartTime=1, animationEndTime=end_frame)
                adjustments.append(f"frames 1–{end_frame}")
        if clear_scene:
            cmds.viewFit(all=True)
        job["maya_imported"] = paths[sample_names[0]]
        job["maya_imported_files"] = {sample_name: paths[sample_name] for sample_name in sample_names}
        job.pop("maya_import_error", None)
        self.model.save_preferences()
        self.populate_jobs()
        action = "Cleared the current scene and imported" if clear_scene else "Imported"
        imported_text = (f"{len(sample_names)} generated Maya files into the same scene"
                         if len(sample_names) > 1 else f"generated Maya file: {paths[sample_names[0]]}")
        if metadata_error:
            self.message(f"{action} {imported_text}, but automatic timing adjustments were skipped: "
                         f"{metadata_error}", warning=True)
        else:
            adjustment_text = f" Set {', '.join(adjustments)}." if adjustments else ""
            self.message(f"{action} {imported_text}.{adjustment_text}")
        return paths[sample_names[0]]

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
        """Persists HumanIK and joint-translation authoring options."""
        if not self.loading:
            self.model.definition["maya"] = {
                "auto_humanik": self.view.auto_humanik.isChecked(),
                "limit_body_joint_translations": self.view.limit_body_joint_translations.isChecked(),
            }
            self.model.save_preferences()

    def save_pose_preview_template(self):
        """Persists whether newly created pose previews are unselectable templates."""
        if not self.loading:
            self.model.pose_previews_template = self.view.template_pose_previews.isChecked()
            self.model.save_preferences()

    def update_path_sample_controls(self, *unused):
        """Enables automatic curve sampling only when explicit root-path frames are blank."""
        self.view.path_curve_samples.setEnabled(not self.view.path_frames.text().strip())

    def save_path_curve_samples(self, *unused):
        """Persists the requested automatic NURBS curve sample count."""
        if not self.loading:
            self.model.path_curve_samples = self.view.path_curve_samples.value()
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
        """Captures selected locators or a curve using explicit or automatic timing."""
        import maya.cmds as cmds

        self.gather_constraints()
        selected_nodes = cmds.ls(selection=True, long=True) or []
        path_nodes = []
        for node in selected_nodes:
            node_type = cmds.nodeType(node)
            if node_type in ("transform", "joint"):
                path_nodes.append(node)
            elif node_type == "nurbsCurve":
                parent = cmds.listRelatives(node, parent=True, fullPath=True) or []
                path_nodes.extend(parent[:1])
        path_nodes = list(dict.fromkeys(path_nodes))
        frame_text = self.view.path_frames.text().strip()
        self.gather_prompts()
        frame_count = self._generation_frame_count(self.model.definition)
        automatic_curve = False
        if frame_text:
            frames = self.parse_frames(frame_text)
        else:
            curve_shapes = []
            if len(path_nodes) == 1:
                curve_shapes = [shape for shape in cmds.listRelatives(
                    path_nodes[0], shapes=True, fullPath=True) or [] if cmds.nodeType(shape) == "nurbsCurve"]
            if len(path_nodes) >= 2:
                key_count = len(path_nodes)
            elif curve_shapes:
                key_count = min(self.view.path_curve_samples.value(), frame_count)
                automatic_curve = True
            else:
                raise ValueError("Leave Root path frames blank to evenly spread two or more selected transforms, "
                                 "or to sample one selected NURBS curve across the generated clip.")
            frames = kimodo.distribute_constraint_frames(key_count, frame_count)
        constraint = kimodo.capture_root_path(path_nodes, frames, self.model.pose_group or None)
        kimodo.validate_constraints([constraint], frame_count)
        self.model.add_constraint(constraint, "Root path")
        self.populate_constraints()
        self.model.save_preferences()
        if automatic_curve:
            requested_samples = self.view.path_curve_samples.value()
            timing = f"with {len(frames)} curve samples"
            if len(frames) < requested_samples:
                timing += f" (requested {requested_samples}; limited by clip length)"
            timing += " evenly spread across the generated clip"
        elif frame_text:
            timing = "at the entered clip frames"
        else:
            timing = "evenly across the generated clip"
        self.message(f"Root path captured {timing} in the pose skeleton's placement space.")

    def preview_pose(self):
        """Creates a separate pose preview without changing the authoring skeleton."""
        self.gather_constraints()
        row = self.view.constraints.currentRow()
        if row < 0 or row >= len(self.model.constraints):
            raise ValueError("Connect and select a pose constraint first.")
        entry = self.model.constraints[row]
        if entry["parameters"].get("type") == "root2d":
            raise ValueError("Select a pose constraint; use Preview Root Path for a path constraint.")
        self._preview_pose_entry(entry)
        style = "template (unselectable)" if self.view.template_pose_previews.isChecked() else "selectable"
        self.message(f"Pose preview created as a {style} skeleton: {self._preview_display_name(entry)}.")

    @staticmethod
    def _preview_display_name(entry):
        """Builds a Maya-safe label identifying a constraint preview by name and first frame.

        Args:
            entry (dict): Named Kimodo constraint row.

        Returns:
            str: Maya-safe display name.
        """
        parameters = entry["parameters"]
        label = re.sub(r"[^A-Za-z0-9_]+", "_", entry.get("name") or parameters.get("type", "constraint"))
        label = label.strip("_") or "constraint"
        if label[0].isdigit():
            label = f"constraint_{label}"
        frame = parameters.get("frame_indices", [0])[0] + 1
        return f"kimodo_{label[:48]}_frame_{frame:03d}"

    def _preview_pose_entry(self, entry):
        """Creates and names one pose preview from a constraint row."""
        if not self.model.rest_motion:
            raise ValueError("Connect first to load the reference skeleton for pose previews.")
        display_name = self._preview_display_name(entry)
        kimodo.preview_pose(
            entry["parameters"], self.model.rest_motion, namespace=self._namespace("kimodo_preview"),
            template=self.view.template_pose_previews.isChecked(), display_name=display_name)

    def preview_all_constraints(self):
        """Creates previews for all pose and root-path constraint rows, including disabled rows."""
        self.gather_constraints()
        entries = list(self.model.constraints)
        if not entries:
            raise ValueError("Add at least one pose or root path constraint to preview.")
        has_poses = any(entry["parameters"].get("type") != "root2d" for entry in entries)
        if has_poses and not self.model.rest_motion:
            raise ValueError("Connect first to load the reference skeleton for pose previews.")

        created = 0
        failures = []
        for entry in entries:
            display_name = self._preview_display_name(entry)
            try:
                if entry["parameters"].get("type") == "root2d":
                    self._create_root_path_preview(entry["parameters"], display_name, select=False)
                else:
                    self._preview_pose_entry(entry)
                created += 1
            except Exception as error:
                failures.append(f"{entry.get('name') or display_name}: {error}")
                logger.warning("Could not preview Kimodo constraint %s: %s", display_name, error)
        if not created:
            raise ValueError("No constraint previews were created. " + "; ".join(failures))
        if failures:
            self.message(f"Created {created} previews; {len(failures)} failed. See the Script Editor for details.",
                         warning=True)
        else:
            self.message(f"Created previews for all {created} constraints.")

    def remove_all_constraints(self):
        """Confirms and removes all constraint rows from this setup, without deleting scene objects."""
        count = len(self.model.constraints)
        if not count:
            self.message("There are no constraints to remove.", warning=True)
            return
        answer = QtWidgets.QMessageBox.question(
            self.view, "Remove All Constraints", f"Remove all {count} constraints from this setup?\n\n"
            "This does not delete Maya preview objects.",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No)
        if answer != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        self.model.constraints = []
        self.populate_constraints()
        self.model.save_preferences()
        self.message(f"Removed {count} constraints from this setup.")

    def remove_pose_previews(self):
        """Deletes tracked Kimodo pose and root-path previews without touching other scene objects."""
        count = kimodo.remove_pose_previews()
        if not count:
            self.message("No Kimodo constraint previews were found in the current Maya scene.", warning=True)
            return
        self.message(f"Removed {count} Kimodo constraint preview{'s' if count != 1 else ''}.")

    def show_pose_frame_context_menu(self, position):
        """Opens the frame spinbox menu with a Maya-current-time shortcut.

        Args:
            position (QPoint): Position relative to the pose frame spinbox.
        """
        menu = QtWidgets.QMenu(self.view.pose_frame)
        self._add_menu_action(
            menu,
            "Set Clip Frame to Current Maya Frame",
            self._action_callback("set_pose_frame_to_current_time"),
            icon_path=resources.Icon.ui_goto_location,
            tooltip="Query Maya's current timeline time when clicked and copy its nearest whole frame into Clip "
                    "frame. This sets the pose's destination in the generated clip; it does not change Maya time "
                    "or sample a different pose.")
        execute = getattr(menu, "exec_", None) or getattr(menu, "exec")
        execute(self.view.pose_frame.mapToGlobal(position))

    def set_pose_frame_to_current_time(self):
        """Copies Maya's current timeline frame into the pose destination field."""
        import maya.cmds as cmds

        maya_frame = int(round(cmds.currentTime(query=True)))
        self.view.pose_frame.setValue(maya_frame)
        clip_frame = self.view.pose_frame.value()
        if clip_frame != maya_frame:
            self.message(f"Maya frame {maya_frame} is outside the Clip frame range; using {clip_frame} instead.",
                         warning=True)
            return
        self.message(f"Clip frame set to Maya frame {clip_frame}.")

    def preview_root_path(self):
        """Creates a Maya curve showing one selected root-path constraint."""
        self.gather_constraints()
        row = self.view.constraints.currentRow()
        if row < 0 or row >= len(self.model.constraints):
            raise ValueError("Select a root path constraint to preview.")
        entry = self.model.constraints[row]
        parameters = entry["parameters"]
        if parameters.get("type") != "root2d":
            raise ValueError("The selected row is not a root path constraint.")
        curve = self._create_root_path_preview(parameters, self._preview_display_name(entry))
        self.message(f"Root path preview created: {curve}")
        return curve

    def _create_root_path_preview(self, parameters, display_name, select=True):
        """Builds a tracked Maya curve from one native root-path constraint.

        Args:
            parameters (dict): Native root-path conditioning data.
            display_name (str): Maya-safe display label.
            select (bool): Select the curve after creation for an individual preview.

        Returns:
            str: Created curve transform.
        """
        import maya.cmds as cmds
        import maya.api.OpenMaya as om

        kimodo.validate_constraints([parameters])
        coordinates = parameters.get("smooth_root_2d", [])
        if len(coordinates) < 2:
            raise ValueError("A root path preview requires at least two path samples.")

        units_per_meter = 1.0 / om.MDistance(1, om.MDistance.uiUnit()).asMeters()
        group = self.model.pose_group
        if group:
            if not cmds.objExists(group):
                raise ValueError("The pose placement group no longer exists; choose the pose source again.")
            points = [(x * units_per_meter, 0.0, z * units_per_meter) for x, z in coordinates]
        elif cmds.upAxis(query=True, axis=True) == "y":
            points = [(x * units_per_meter, 0.0, z * units_per_meter) for x, z in coordinates]
        else:
            points = [(x * units_per_meter, -y * units_per_meter, 0.0) for x, y in coordinates]

        curve = cmds.curve(name=display_name, degree=1, point=points)
        if group:
            curve = (cmds.parent(curve, group, relative=True) or [curve])[0]
        kimodo.tag_path_preview(curve)
        if select:
            cmds.select(curve, replace=True)
        return curve

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
        """Validates the complete request and estimates generated clip timing."""
        self.gather()
        data = self.model.build_definition().as_dict()
        frame_count = self._generation_frame_count(data)
        kimodo.validate_constraints(data["constraints"], frame_count)
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

    def load_default_setup(self):
        """Resets generation and project settings while preserving connection and history."""
        answer = QtWidgets.QMessageBox.question(
            self.view, "Reset to Default Setup",
            "Reset prompts, constraints, HumanIK overrides, and generation/import settings to their defaults?\n\n"
            "The current bridge connection, WSL/Python settings, token, job history, and Maya scene are preserved.",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No)
        if answer != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        defaults = KimodoGeneratorModel(preferences=False)
        preserved_widths = copy.deepcopy(self.model.table_widths)
        self.model.definition = copy.deepcopy(defaults.definition)
        self.model.constraints = copy.deepcopy(defaults.constraints)
        self.model.prompt_durations_in_frames = defaults.prompt_durations_in_frames
        self.model.path_curve_samples = defaults.path_curve_samples
        self.model.pose_previews_template = defaults.pose_previews_template
        self.model.output_directory = defaults.output_directory
        self.model.namespace = defaults.namespace
        self.model.start_frame = defaults.start_frame
        self.model.humanik = copy.deepcopy(defaults.humanik)
        self.model.auto_download = defaults.auto_download
        self.model.auto_maya_file = defaults.auto_maya_file
        self.model.auto_import_maya = defaults.auto_import_maya
        self.model.auto_import_all_samples = defaults.auto_import_all_samples
        self.model.auto_clear_scene = defaults.auto_clear_scene
        self.model.auto_frame_rate = defaults.auto_frame_rate
        self.model.auto_frame_range = defaults.auto_frame_range
        self.model.table_widths = preserved_widths
        self.model.pose_group = ""
        self.load_widgets()
        self.view.pose_source.setText("Pose source: select a Kimodo skeleton")
        self.model.save_preferences()
        self.message("Default generation setup loaded. The bridge connection and job history were preserved.")

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
        """Opens a job's download folder, or the configured target when no job is selected."""
        row = self.view.jobs.currentRow()
        if not 0 <= row < len(self.model.jobs):
            folder = self.model.output_directory
            if not folder:
                raise ValueError("Choose a Download Folder first.")
            folder = os.path.abspath(folder)
            try:
                os.makedirs(folder, exist_ok=True)
            except OSError as error:
                self.message(f"No job was selected, and the Download Folder could not be prepared: {error}",
                             warning=True)
                return
            opened = ui_qt.QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(folder))
            if not opened:
                self.message(f"No job was selected. Could not open the Download Folder: {folder}", warning=True)
                return
            self.message(f"No job selected; opened the configured Download Folder: {folder}", warning=True)
            return

        path = self.selected_job().get("paths", {}).get("result.json")
        if not path or not os.path.isfile(path):
            raise ValueError("Download the job first.")
        folder = os.path.dirname(path)
        if not ui_qt.QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(folder)):
            raise ValueError(f"Could not open the results folder: {folder}")

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
