"""
Batch Processor Report Task Widgets
"""

from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
from gt.tools.batch_processor.tasks import task_report
import gt.ui.python_output_view as ui_python_output_view
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt
from functools import partial


class AttrWidgetSceneReportTask(AttrWidgetTask):
    """Attribute widget for the read-only report task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the report widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskSceneReport, optional): Task model.
            project (BatchProcessorModel, optional): Project model.
            refresh_parent_func (callable, optional): Refresh callback.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(
            parent=parent,
            task=task,
            project=project,
            refresh_parent_func=refresh_parent_func,
            *args,
            **kwargs
        )
        self.metric_checkboxes = {}
        self.report_item_rows = {}
        self.report_items_layout = None
        self.report_items_empty_label = None
        self.add_report_item_button = None
        self.add_report_item_menu = ui_qt.QtWidgets.QMenu(self)
        self.detail_combo_box = None
        self.timestamp_combo_box = None
        self.load_mode_combo_box = None
        self.skip_condition_combo_box = None
        self.report_name_field = None
        self.add_common_task_settings()
        self.add_widget_separator_line(label_text="Report Preferences")
        first_preference_row = ui_qt.QtWidgets.QHBoxLayout()
        first_preference_row.setContentsMargins(0, 0, 0, 0)
        first_preference_row.setSpacing(8)
        self.detail_combo_box = self.add_combo_box(
            "Detail",
            self.task.get_detail_mode(),
            task_report.REPORT_DETAIL_MODES,
            partial(self.set_task_setting, key="report_detail_mode"),
            tooltip=(
                "Total Only: write only the combined totals.\n"
                "List + Total: write the totals and a list with the values found in every file."
            ),
            parent_layout=first_preference_row,
        )
        self.timestamp_combo_box = self.add_combo_box(
            "Timestamp Format",
            self.task.get_timestamp_format(),
            task_report.REPORT_TIMESTAMP_FORMATS,
            partial(self.set_task_setting, key="report_timestamp_format"),
            tooltip=(
                "Choose how the report creation time is displayed.\n"
                "Each option starts with a letter and shows an example of the output."
            ),
            parent_layout=first_preference_row,
        )
        first_preference_row.setStretch(0, 1)
        first_preference_row.setStretch(1, 2)
        self.content_layout.addLayout(first_preference_row)

        second_preference_row = ui_qt.QtWidgets.QHBoxLayout()
        second_preference_row.setContentsMargins(0, 0, 0, 0)
        second_preference_row.setSpacing(8)
        self.load_mode_combo_box = self.add_combo_box(
            "Load Mode",
            self.task.settings.get("source_load_mode"),
            ["Open", "Import"],
            partial(self.set_task_setting, key="source_load_mode"),
            tooltip=(
                "How scenes are loaded before scene values are read.\n"
                "Scenes are only loaded when a selected report item needs scene data."
            ),
            parent_layout=second_preference_row,
        )
        self.skip_condition_combo_box = self.add_combo_box(
            "Skip Condition",
            self.task.get_skip_condition(),
            task_report.REPORT_SKIP_CONDITIONS,
            partial(self.set_task_setting, key="report_skip_condition"),
            tooltip=(
                "Skip this report when the previous enabled task skipped one or more items.\n"
                "The same state is available to scripts as {batch-previous-task-skipped}."
            ),
            parent_layout=second_preference_row,
        )
        second_preference_row.setStretch(0, 1)
        second_preference_row.setStretch(1, 2)
        self.content_layout.addLayout(second_preference_row)
        self.report_name_field = self.add_text_field(
            "Report Name",
            self.task.settings.get("report_file_name"),
            partial(self.set_task_setting, key="report_file_name"),
            placeholder=task_report.DEFAULT_REPORT_FILE_NAME,
            tooltip=(
                "Report file name.\nProject tokens such as {project-name} are resolved when the report is written.\n"
                'Defaults to "'
                + task_report.DEFAULT_REPORT_FILE_NAME
                + '" when this field is empty.'
            ),
            label_width=110,
        )
        self.add_report_item_list()
        self.add_report_action_buttons()
        self.add_report_notes_section()
        self.add_segmentation_section(
            main_label="Run Once After All Jobs",
            main_key="run_once_after_multi_instance",
            main_tooltip=(
                "In multi-instance mode, wait for every regular job to finish,\n"
                "then build this report once over the files found at its Source Path.\n"
                'The report is skipped if any job failed, unless "Run After Failed Jobs" is on.\n'
                "This task must be the last enabled processing task while this option is on.\n"
                "Turn it off to report on each file as its job runs.\nParallel workers merge\n"
                "their results into the same report either way.\n"
                'Enable "Add Separator" to mark this run-once step in the task list.'
            ),
            secondary_label="Run After Failed Jobs",
            secondary_key="run_after_failed_jobs",
            secondary_tooltip=(
                "In multi-instance mode, still build the run-once report when one or more jobs failed,\n"
                "timed out, or were canceled. Only files found at the Source Path are reported.\n"
                "Off by default: the report is skipped when any job did not succeed."
            ),
        )
        self.content_layout.addStretch()

    def add_report_notes_section(self):
        """Adds the optional, collapsible notes section above segmentation settings."""
        self.task.settings.setdefault("report_notes_collapsed", True)
        notes_tooltip = (
            "Optional notes appended to the report.\nBy default, {project-notes} resolves to the "
            "project notes saved in the .batch file."
        )
        section = self.add_collapsible_section(
            "Report Notes",
            collapsed=self.task.settings.get("report_notes_collapsed", True),
            state_setter=partial(self.set_task_setting, key="report_notes_collapsed"),
            tooltip=notes_tooltip,
        )
        self.add_text_area(
            "Notes",
            self.task.settings.get("report_notes", task_report.DEFAULT_REPORT_NOTES),
            partial(self.set_task_setting, key="report_notes"),
            placeholder=task_report.DEFAULT_REPORT_NOTES,
            tooltip=notes_tooltip,
            parent_layout=section.get("content_layout"),
        )

    def add_report_item_list(self):
        """Adds the configurable list of report items."""
        self.add_widget_separator_line(label_text="Report Items")
        header_layout = ui_qt.QtWidgets.QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 5)
        description = ui_qt.QtWidgets.QLabel("Select values to include in the report.")
        header_layout.addWidget(description)
        header_layout.addStretch()
        self.add_report_item_button = ui_qt.QtWidgets.QPushButton()
        self.add_report_item_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_add))
        self.add_report_item_button.setIconSize(ui_qt.QtCore.QSize(18, 18))
        self.add_report_item_button.setMinimumHeight(32)
        self.add_report_item_button.setMinimumWidth(32)
        self.add_report_item_button.setAccessibleName("Add Report Item")
        self.add_report_item_button.setToolTip("Add another report value and its available preferences.")
        self.add_report_item_button.clicked.connect(self.show_add_report_item_menu)
        header_layout.addWidget(self.add_report_item_button)
        self.content_layout.addLayout(header_layout)

        report_items_container = ui_qt.QtWidgets.QWidget()
        self.report_items_layout = ui_qt.QtWidgets.QVBoxLayout(report_items_container)
        self.report_items_layout.setContentsMargins(0, 0, 0, 0)
        self.report_items_layout.setSpacing(4)
        self.content_layout.addWidget(report_items_container)
        self.report_items_empty_label = ui_qt.QtWidgets.QLabel("No report items added.")
        self.report_items_empty_label.setStyleSheet("color: #888888;")
        self.report_items_layout.addWidget(self.report_items_empty_label)

        for metric_key in self.task.get_report_item_keys():
            self.create_report_item_row(metric_key)
        self.update_report_item_list_state()

    def create_report_item_row(self, metric_key):
        """Creates one report item row with its activation and item-specific settings.

        Args:
            metric_key (str): Report item key.
        """
        metric = task_report.get_metric_definition(metric_key)
        if not metric or metric_key in self.report_item_rows:
            return
        row = ui_qt.QtWidgets.QFrame()
        row.setFrameShape(ui_qt.QtLib.FrameStyle.StyledPanel)
        row_layout = ui_qt.QtWidgets.QHBoxLayout(row)
        row_layout.setContentsMargins(5, 2, 5, 2)
        row_layout.setSpacing(8)
        checkbox = ui_qt.QtWidgets.QCheckBox(metric.get("label") or metric_key)
        checkbox.setMinimumHeight(30)
        checkbox.setChecked(metric_key in self.task.get_metric_keys())
        checkbox.setToolTip(metric.get("tooltip") or "Include this value in the report.")
        checkbox.clicked.connect(
            lambda value=False, item_key=metric_key: self.set_metric_enabled(value, item_key)
        )
        row_layout.addWidget(checkbox)
        row_layout.addStretch()

        row_data = {"widget": row, "checkbox": checkbox}
        if metric_key == "time":
            duration_combo = ui_qt.QtWidgets.QComboBox()
            duration_combo.setMinimumHeight(30)
            duration_combo.setMinimumWidth(220)
            duration_combo.setToolTip("Choose how scene durations are displayed in totals and file details.")
            duration_combo.addItems(task_report.REPORT_DURATION_FORMATS)
            duration_combo.setCurrentText(self.task.get_duration_format())
            duration_combo.currentTextChanged.connect(self.set_time_duration_format)
            row_layout.addWidget(duration_combo)
            row_data["duration_combo"] = duration_combo

        remove_button = ui_qt.QtWidgets.QPushButton()
        remove_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_trash))
        remove_button.setIconSize(ui_qt.QtCore.QSize(16, 16))
        remove_button.setFixedSize(30, 30)
        remove_button.setAccessibleName("Remove {0}".format(metric.get("label") or metric_key))
        remove_button.setToolTip("Remove this item from the report list.")
        remove_button.clicked.connect(partial(self.remove_report_item, metric_key=metric_key))
        row_layout.addWidget(remove_button)
        row_data["remove_button"] = remove_button
        self.report_items_layout.addWidget(row)
        self.report_item_rows[metric_key] = row_data
        self.metric_checkboxes[metric_key] = checkbox

    def show_add_report_item_menu(self, checked=False):
        """Shows metrics that have not been added to the report list.

        Args:
            checked (bool, optional): Qt button state, unused.
        """
        self.add_report_item_menu.clear()
        added_keys = set(self.task.get_report_item_keys())
        available_metrics = [metric for metric in task_report.REPORT_METRICS if metric.get("key") not in added_keys]
        for metric in available_metrics:
            metric_key = metric.get("key")
            action = self.add_report_item_menu.addAction(metric.get("label") or metric_key)
            action.setToolTip(metric.get("tooltip") or "Add this value to the report.")
            action.triggered.connect(partial(self.add_report_item, metric_key=metric_key))
        if available_metrics:
            self.add_report_item_menu.popup(
                self.add_report_item_button.mapToGlobal(self.add_report_item_button.rect().bottomLeft())
            )
        else:
            self.emit_status_message("All report items are already in the list.", status="info")

    def add_report_item(self, checked=False, metric_key=None):
        """Adds and activates a report item.

        Args:
            checked (bool, optional): Qt action state.
            metric_key (str): Report item key.
        """
        if not metric_key or metric_key in self.task.get_report_item_keys():
            return
        item_keys = task_report.normalize_metric_keys(self.task.get_report_item_keys() + [metric_key])
        metric_keys = task_report.normalize_metric_keys(self.task.get_metric_keys() + [metric_key])
        self.set_task_setting(item_keys, key="report_items")
        self.set_task_setting(metric_keys, key="report_metrics")
        self.create_report_item_row(metric_key)
        self.update_report_item_list_state()

    def remove_report_item(self, checked=False, metric_key=None):
        """Removes one report item and its activation state.

        Args:
            checked (bool, optional): Qt button state.
            metric_key (str): Report item key.
        """
        if not metric_key:
            return
        item_keys = [key for key in self.task.get_report_item_keys() if key != metric_key]
        metric_keys = [key for key in self.task.get_metric_keys() if key != metric_key]
        self.set_task_setting(item_keys, key="report_items")
        self.set_task_setting(metric_keys, key="report_metrics")
        row_data = self.report_item_rows.pop(metric_key, None)
        self.metric_checkboxes.pop(metric_key, None)
        if row_data:
            row = row_data.get("widget")
            self.report_items_layout.removeWidget(row)
            row.hide()
            row.deleteLater()
        self.update_report_item_list_state()

    def update_report_item_list_state(self):
        """Updates the empty message and Add button availability."""
        has_items = bool(self.report_item_rows)
        self.report_items_empty_label.setVisible(not has_items)
        has_available_items = len(self.report_item_rows) < len(task_report.REPORT_METRICS)
        self.add_report_item_button.setEnabled(has_available_items)
        if not has_available_items:
            self.add_report_item_button.setToolTip("All report items have been added.")
        else:
            self.add_report_item_button.setToolTip("Add another report value and its available preferences.")

    def add_report_action_buttons(self):
        """Adds the preview and run actions."""
        tooltip = "Preview the report values of the current scene, or run this report task on its source files."
        layout = self.add_labeled_layout("Actions", tooltip=tooltip)
        preview_tooltip = "Collect the selected report items from the scene currently open in Maya."
        preview_button = ui_qt.QtWidgets.QPushButton("Preview Current Scene")
        preview_button.setMinimumHeight(35)
        preview_button.setToolTip(preview_tooltip)
        preview_button.clicked.connect(self.preview_current_scene)
        layout.addWidget(preview_button)
        run_tooltip = "Run only this Report task against its configured source files."
        run_button = ui_qt.QtWidgets.QPushButton("Run Report")
        run_button.setMinimumHeight(35)
        run_button.setToolTip(run_tooltip)
        run_button.clicked.connect(self.run_this_task_now)
        layout.addWidget(run_button)

    def set_metric_enabled(self, value, metric_key):
        """Changes whether one added report item is active.

        Args:
            value (bool): Whether the report item should be included.
            metric_key (str): Report item key.
        """
        item_keys = self.task.get_report_item_keys()
        if "report_items" not in self.task.settings:
            self.set_task_setting(item_keys, key="report_items")

        selected_keys = set(self.task.get_metric_keys())
        if value:
            selected_keys.add(metric_key)
        else:
            selected_keys.discard(metric_key)
        self.set_task_setting(task_report.normalize_metric_keys(selected_keys), key="report_metrics")

    def set_time_duration_format(self, duration_format):
        """Stores the selected duration format on the Time report item.

        Args:
            duration_format (str): Selected duration display format.
        """
        item_settings = dict(self.task.settings.get("report_item_settings") or {})
        time_settings = dict(item_settings.get("time") or {})
        time_settings["duration_format"] = duration_format
        item_settings["time"] = time_settings
        self.set_task_setting(item_settings, key="report_item_settings")

    def preview_current_scene(self):
        """Shows the report values collected from the scene currently open in Maya."""
        if not self.task.get_metric_keys():
            self.emit_status_message("Report has no report items selected.", status="warning")
            return
        try:
            entry = self.task.collect_entry(self.get_current_scene_path(), load_scene=False)
        except Exception as exception:
            self.emit_status_message("Unable to preview report values: {0}".format(exception), status="warning")
            return
        report_data = self.task.build_report_data([entry], project=self.project)
        report_data["detail_mode"] = task_report.REPORT_DETAIL_LIST_AND_TOTAL
        output_window = ui_python_output_view.PythonOutputView(parent=self, editable=False)
        output_window.setWindowTitle("Report Preview")
        output_window.set_python_output_text("\n".join(task_report.build_report_lines(report_data)))
        output_window.show()
        status = "warning" if entry.get("errors") else "info"
        self.emit_status_message("Report preview finished.", status=status)

    @staticmethod
    def get_current_scene_path():
        """Gets the path of the scene currently open in Maya.

        Returns:
            str: Scene path, or an empty string when the scene was never saved.
        """
        try:
            import maya.cmds as cmds

            return cmds.file(query=True, sceneName=True) or ""
        except Exception:
            return ""
