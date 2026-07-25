"""
Batch Processor Project Attribute Widget
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor.widgets import attr_widget_base
import gt.ui.python_output_view as ui_python_output_view
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_utils as ui_qt_utils
import gt.ui.qt_import as ui_qt
from functools import partial
import json


class AttrWidgetProject(attr_widget_base.AttrWidgetBase):
    """Attribute widget for project-level batch processor settings."""

    def __init__(self, parent=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the project attribute widget.

        Args:
            parent (QWidget, optional): Parent widget.
            project (BatchProcessorModel, optional): Project model.
            refresh_parent_func (callable, optional): Function used to refresh the parent UI.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(parent=parent, project=project, refresh_parent_func=refresh_parent_func, *args, **kwargs)
        self.project_name_field = None
        self.create_log_checkbox = None
        self.create_task_time_log_checkbox = None
        self.purge_logs_checkbox = None
        self.log_path_widgets = None
        self.add_widget_project_header()
        self.add_widget_separator_line(
            label_text="Environment Variables",
            tooltip="Project variables used by task path templates.",
        )
        self.add_environment_variable_field(
            "project-dir",
            "Project Dir",
            "Root directory for this batch project. Used as {project-dir}.",
            browse=True,
            placeholder="Project root folder. Blank stays unresolved until a project file is saved or opened.",
        )
        self.add_environment_variable_field(
            "input-dir",
            "Input Dir",
            "Folder name or path fragment used as {input-dir}.",
        )
        self.add_environment_variable_field(
            "task-dir",
            "Task Dir",
            "Folder name or path fragment used as {task-dir}.",
        )
        self.add_environment_variable_field(
            "output-dir",
            "Output Dir",
            "Folder name or path fragment used as {output-dir}.",
        )

        self.add_widget_separator_line(label_text="Run Preferences")
        worker_layout = self.add_labeled_layout(
            "Workers",
            label_width=90,
            tooltip="Run using multiple headless Maya worker processes.",
        )
        self.add_checkbox(
            "Multi",
            self.project.run_settings.get("multi_instance"),
            partial(self.set_run_setting, key="multi_instance"),
            layout=worker_layout,
            tooltip="Run using multiple headless Maya instances when available.",
        )
        worker_label = ui_qt.QtWidgets.QLabel("Count:")
        attr_widget_base.configure_label_for_scaled_displays(worker_label)
        worker_label.setToolTip("Number of worker instances to use in multi-instance mode.")
        worker_layout.addWidget(worker_label)
        worker_spin_box = ui_qt.QtWidgets.QSpinBox()
        worker_spin_box.setRange(1, 64)
        worker_spin_box.setValue(int(self.project.run_settings.get("worker_count") or 1))
        worker_spin_box.setMinimumHeight(35)
        worker_spin_box.setFixedWidth(90)
        worker_spin_box.setToolTip("Number of worker instances to use in multi-instance mode.")
        worker_spin_box.valueChanged.connect(partial(self.set_run_setting, key="worker_count"))
        worker_layout.addWidget(worker_spin_box)
        # Match the visual gap the empty "Multi" checkbox leaves before "Count:"
        # so the retries group is not flush against the worker count spin box.
        worker_layout.addSpacing(8)
        retry_tooltip = (
            "Number of times a failed job is retried at the end of the run. "
            "0 disables retries. Each still-failing job is re-run up to this many times, "
            "and jobs that keep failing after all retries remain failed."
        )
        retry_label = ui_qt.QtWidgets.QLabel("Retries:")
        attr_widget_base.configure_label_for_scaled_displays(retry_label)
        retry_label.setToolTip(retry_tooltip)
        worker_layout.addWidget(retry_label)
        retry_spin_box = ui_qt.QtWidgets.QSpinBox()
        retry_spin_box.setRange(0, 64)
        retry_spin_box.setValue(int(self.project.run_settings.get("max_retries") or 0))
        retry_spin_box.setMinimumHeight(35)
        retry_spin_box.setFixedWidth(90)
        retry_spin_box.setToolTip(retry_tooltip)
        retry_spin_box.valueChanged.connect(partial(self.set_run_setting, key="max_retries"))
        worker_layout.addWidget(retry_spin_box)
        worker_layout.addSpacing(8)
        timeout_tooltip = (
            "Maximum minutes a single job may run before it is automatically canceled. "
            "0 disables the timeout, so stuck jobs can run indefinitely. When a job times out "
            "it is retried if retry attempts remain; otherwise it is marked as timed out."
        )
        timeout_label = ui_qt.QtWidgets.QLabel("Timeout (min):")
        attr_widget_base.configure_label_for_scaled_displays(timeout_label)
        timeout_label.setToolTip(timeout_tooltip)
        worker_layout.addWidget(timeout_label)
        timeout_spin_box = ui_qt.QtWidgets.QSpinBox()
        timeout_spin_box.setRange(0, 100000)
        timeout_spin_box.setValue(int(self.project.run_settings.get("timeout_minutes") or 0))
        timeout_spin_box.setMinimumHeight(35)
        timeout_spin_box.setFixedWidth(90)
        timeout_spin_box.setToolTip(timeout_tooltip)
        timeout_spin_box.valueChanged.connect(partial(self.set_run_setting, key="timeout_minutes"))
        worker_layout.addWidget(timeout_spin_box)
        worker_layout.addStretch()

        self.add_text_field(
            "Preferred Maya",
            self.project.run_settings.get("preferred_maya_version", ""),
            partial(self.set_run_setting, key="preferred_maya_version"),
            placeholder="Optional version, e.g. 2025",
            tooltip=(
                "Preferred Maya version used for multi-instance jobs. "
                "If not found in default Autodesk install locations, the launcher falls back to the current mayapy."
            ),
            label_width=90,
        )

        logging_layout = self.add_labeled_layout(
            "Logs",
            label_width=90,
            tooltip="Controls where run logs are written and whether old logs are purged before each run.",
        )
        self.create_log_checkbox = self.add_checkbox(
            "Create Log",
            self.project.run_settings.get("create_log", True),
            self.set_create_log,
            layout=logging_layout,
            tooltip="Write run logs to the batch project folder.",
        )
        self.create_task_time_log_checkbox = self.add_checkbox(
            "Task Times",
            self.project.run_settings.get("create_task_time_log", True),
            self.set_create_task_time_log,
            layout=logging_layout,
            tooltip="Write task durations to separate timing log files in the log folder.",
        )
        self.purge_logs_checkbox = self.add_checkbox(
            "Purge On Run",
            self.project.run_settings.get("purge_logs_on_run", True),
            partial(self.set_run_setting, key="purge_logs_on_run"),
            layout=logging_layout,
            tooltip="Delete existing files in the log folder before starting a new batch run.",
        )
        logging_layout.addStretch()

        self.log_path_widgets = self.add_path_template_field(
            "Log Path",
            self.project.run_settings.get("log_path") or constants.Project.DEFAULT_RUN_SETTINGS.get("log_path"),
            partial(self.set_run_setting, key="log_path"),
            placeholder=constants.Project.DEFAULT_RUN_SETTINGS.get("log_path"),
            tooltip="Project-relative or absolute folder used for batch processor logs.",
            dir_only=True,
            return_widgets=True,
        )

        self.refresh_log_preferences_enabled_state()
        self.add_text_area(
            "Notes",
            self.project.notes,
            self.set_project_notes,
            placeholder="Optional notes for this batch project.",
            tooltip="Free-form project notes saved in the .batch file.",
        )
        self.content_layout.addStretch()

    def add_widget_project_header(self):
        """Adds the project header with icon, editable name, and JSON button."""
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 5)
        layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)

        icon_label = ui_qt.QtWidgets.QLabel()
        icon_label.setPixmap(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_project).pixmap(32, 32))
        icon_label.setToolTip("Batch Project")
        layout.addWidget(icon_label)

        self.project_name_field = ui_qt_utils.ConfirmableQLineEdit()
        self.project_name_field.setMinimumHeight(35)
        self.project_name_field.setMinimumWidth(1)
        self.project_name_field.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        self.project_name_field.setText(self.project.project_name or constants.Project.DEFAULT_NAME)
        self.project_name_field.setToolTip("Project name.")
        self.project_name_field.editingFinished.connect(self.set_project_name)
        layout.addWidget(self.project_name_field)

        json_button = ui_qt.QtWidgets.QPushButton()
        json_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_dict))
        json_button.setToolTip("View Project JSON")
        json_button.clicked.connect(self.show_project_json)
        layout.addWidget(json_button)
        self.content_layout.addLayout(layout)

    def add_environment_variable_field(self, key, label, tooltip, browse=False, placeholder=None):
        """Adds an editable environment variable field.

        Args:
            key (str): Environment variable key.
            label (str): UI label.
            tooltip (str): Tooltip text.
            browse (bool, optional): Whether to include a directory browse button.
            placeholder (str, optional): Placeholder text.
        """
        value = self.project.environment_variables.get(key, "")
        setter = partial(self.set_environment_variable, key=key)
        placeholder = placeholder or constants.Project.DEFAULT_ENVIRONMENT_VARIABLES.get(key, "")
        if browse:
            self.add_path_template_field(
                label,
                value,
                setter,
                placeholder=placeholder,
                tooltip=tooltip,
                dir_only=True,
                convert_to_project_relative=False,
            )
        else:
            self.add_text_field(
                label,
                value,
                setter,
                placeholder=placeholder,
                tooltip=tooltip,
            )

    def set_project_name(self):
        """Updates the project name from the header field."""
        self.project.project_name = self.project_name_field.text() or constants.Project.DEFAULT_NAME
        ui_qt.QtCore.QTimer.singleShot(0, self.call_parent_refresh)
        self.emit_status_message('Project renamed to "{0}".'.format(self.project.project_name))

    def set_project_notes(self, value):
        """Updates project notes.

        Args:
            value (str): Notes text.
        """
        self.project.notes = value or ""

    def set_environment_variable(self, value, key):
        """Sets a project environment variable.

        Args:
            value (str): Environment variable value.
            key (str): Environment variable key.
        """
        self.project.environment_variables[key] = value

    def set_run_setting(self, value, key):
        """Sets a project run setting.

        Args:
            value (object): Setting value.
            key (str): Run setting key.
        """
        previous_value = self.project.run_settings.get(key)
        self.project.run_settings[key] = value
        if previous_value != value:
            self.emit_run_setting_message(key=key, value=value)

    def emit_run_setting_message(self, key, value):
        """Emits a status message for run settings that can affect execution.

        Args:
            key (str): Run setting key.
            value (object): New setting value.
        """
        if key == "multi_instance":
            state_name = "enabled" if value else "disabled"
            self.emit_status_message("Multi-instance mode {0}.".format(state_name), status="warning")
        elif key == "worker_count":
            self.emit_status_message("Worker count changed to {0}.".format(value), status="warning")
        elif key == "max_retries":
            if value:
                self.emit_status_message(
                    "Failed jobs will be retried up to {0} time(s) at the end of the run.".format(value),
                    status="warning",
                )
            else:
                self.emit_status_message("Failed job retries disabled.")
        elif key == "timeout_minutes":
            if value:
                self.emit_status_message(
                    "Jobs running longer than {0} minute(s) will be canceled automatically.".format(value),
                    status="warning",
                )
            else:
                self.emit_status_message("Job timeout disabled.")
        elif key == "preferred_maya_version":
            self.emit_status_message(
                'Preferred Maya version changed to "{0}". Validate before running multi-instance jobs.'.format(
                    value or "current"
                ),
                status="warning",
            )
        elif key == "create_log":
            state_name = "enabled" if value else "disabled"
            self.emit_status_message("Run log creation {0}.".format(state_name), status="warning")
        elif key == "create_task_time_log":
            state_name = "enabled" if value else "disabled"
            self.emit_status_message("Task timing log creation {0}.".format(state_name), status="warning")
        elif key == "purge_logs_on_run":
            if value:
                self.emit_status_message("Existing log files will be purged before each run.", status="warning")
            else:
                self.emit_status_message("Existing log files will be preserved before each run.")

    def set_create_log(self, value):
        """Sets the create-log run setting and refreshes dependent controls.

        Args:
            value (bool): Whether logs should be written.
        """
        self.set_run_setting(value=value, key="create_log")
        self.refresh_log_preferences_enabled_state()

    def set_create_task_time_log(self, value):
        """Sets the task-time-log run setting and refreshes dependent controls.

        Args:
            value (bool): Whether task timing logs should be written.
        """
        self.set_run_setting(value=value, key="create_task_time_log")
        self.refresh_log_preferences_enabled_state()

    def refresh_log_preferences_enabled_state(self):
        """Enables log folder controls when either project log type is active."""
        create_log = bool(self.project.run_settings.get("create_log", True))
        create_task_time_log = bool(self.project.run_settings.get("create_task_time_log", True))
        if self.purge_logs_checkbox:
            self.purge_logs_checkbox.setEnabled(create_log or create_task_time_log)
        if self.log_path_widgets:
            for key in ["field", "info_button", "open_button", "browse_button"]:
                self.log_path_widgets[key].setEnabled(create_log or create_task_time_log)

    def show_project_json(self):
        """Shows the current project data as JSON."""
        output_window = ui_python_output_view.PythonOutputView(parent=self, editable=False)
        output_window.setWindowTitle("Batch Project JSON")
        output_window.set_python_output_text(json.dumps(self.project.to_dict(), indent=4, sort_keys=True))
        output_window.show()
