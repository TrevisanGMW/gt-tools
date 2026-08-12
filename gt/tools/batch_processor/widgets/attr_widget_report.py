"""
Batch Processor Report Task Widgets
"""

from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
from gt.tools.batch_processor.tasks import task_report
import gt.ui.python_output_view as ui_python_output_view
import gt.ui.qt_import as ui_qt
from functools import partial


REPORT_ITEMS_PER_ROW = 4


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
        self.add_common_task_settings()
        self.add_widget_separator_line(label_text="Report Preferences")
        self.add_combo_box(
            "Detail",
            self.task.get_detail_mode(),
            task_report.REPORT_DETAIL_MODES,
            partial(self.set_task_setting, key="report_detail_mode"),
            tooltip=(
                "Total Only: write only the combined totals.\n"
                "List + Total: write the totals and a list with the values found in every file."
            ),
        )
        self.add_text_field(
            "Report Name",
            self.task.settings.get("report_file_name"),
            partial(self.set_task_setting, key="report_file_name"),
            placeholder=task_report.DEFAULT_REPORT_FILE_NAME,
            tooltip=(
                "Report file name. Project tokens such as {project-name} are resolved when the report is written.\n"
                'Defaults to "'
                + task_report.DEFAULT_REPORT_FILE_NAME
                + '" when this field is empty.'
            ),
        )
        self.add_combo_box(
            "Load Mode",
            self.task.settings.get("source_load_mode"),
            ["Open", "Import"],
            partial(self.set_task_setting, key="source_load_mode"),
            tooltip=(
                "How scenes are loaded before scene values are read.\n"
                "Scenes are only loaded when a selected report item needs scene data."
            ),
        )
        self.add_report_item_checkboxes()
        self.add_report_item_activation_buttons()
        self.add_report_action_buttons()
        self.add_segmentation_section(
            main_label="Run Once After All Jobs",
            main_key="run_once_after_multi_instance",
            main_tooltip=(
                "In multi-instance mode, wait for every regular job to succeed,\n"
                "then build this report once over the files found at its Source Path.\n"
                "This task must be the last enabled processing task while this option is on.\n"
                "Turn it off to report on each file as its job runs. Parallel workers merge\n"
                "their results into the same report either way.\n"
                'Enable "Add Separator" to mark this run-once step in the task list.'
            ),
        )
        self.content_layout.addStretch()

    def add_report_item_checkboxes(self):
        """Adds one checkbox per registered report item."""
        self.add_widget_separator_line(label_text="Report Items")
        selected_keys = self.task.get_metric_keys()
        row_layout = None
        for index, metric in enumerate(task_report.REPORT_METRICS):
            if index % REPORT_ITEMS_PER_ROW == 0:
                row_layout = ui_qt.QtWidgets.QHBoxLayout()
                row_layout.setContentsMargins(0, 0, 0, 5)
                self.content_layout.addLayout(row_layout)
            metric_key = metric.get("key")
            checkbox = self.add_checkbox(
                metric.get("label"),
                metric_key in selected_keys,
                partial(self.set_metric_enabled, metric_key=metric_key),
                layout=row_layout,
                tooltip=metric.get("tooltip"),
            )
            self.metric_checkboxes[metric_key] = checkbox
            if index % REPORT_ITEMS_PER_ROW == REPORT_ITEMS_PER_ROW - 1:
                row_layout.addStretch()
        if row_layout and len(task_report.REPORT_METRICS) % REPORT_ITEMS_PER_ROW:
            row_layout.addStretch()

    def add_report_item_activation_buttons(self):
        """Adds buttons that activate or clear every report item."""
        tooltip = "Activate or clear every report item at once."
        layout = self.add_labeled_layout("Activation", tooltip=tooltip)
        for label_text, value, button_tooltip in [
            ("Activate All", True, "Enable every report item."),
            ("Activate None", False, "Disable every report item."),
        ]:
            button = ui_qt.QtWidgets.QPushButton(label_text)
            button.setMinimumHeight(35)
            button.setToolTip(button_tooltip)
            button.clicked.connect(partial(self.set_all_metrics_enabled, value))
            layout.addWidget(button)

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
        """Adds or removes one report item from the task settings.

        Args:
            value (bool): Whether the report item should be included.
            metric_key (str): Report item key.
        """
        selected_keys = set(self.task.get_metric_keys())
        if value:
            selected_keys.add(metric_key)
        else:
            selected_keys.discard(metric_key)
        self.set_task_setting(task_report.normalize_metric_keys(selected_keys), key="report_metrics")

    def set_all_metrics_enabled(self, value):
        """Enables or disables every report item.

        Args:
            value (bool): Whether every report item should be included.
        """
        metric_keys = [metric.get("key") for metric in task_report.REPORT_METRICS] if value else []
        self.set_task_setting(metric_keys, key="report_metrics")
        for metric_key, checkbox in self.metric_checkboxes.items():
            if checkbox:
                checkbox.blockSignals(True)
                checkbox.setChecked(metric_key in metric_keys)
                checkbox.blockSignals(False)

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
        report_data = self.task.build_report_data([entry])
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
