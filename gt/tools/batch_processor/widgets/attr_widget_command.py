"""
Batch Processor Command Task Widget
"""

from gt.tools.batch_processor.tasks import task_command_utils as command_utils
from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
import gt.ui.python_output_view as ui_python_output_view
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt
from functools import partial

ARGUMENTS_TOOLTIP = (
    "Program arguments. Separate arguments with spaces or new lines.\n"
    'Wrap arguments that contain spaces in double quotes, e.g. "C:/My Folder/file.txt".\n'
    "Backslashes are kept as typed. Lines starting with # are ignored.\n"
    "Batch tokens such as {project-dir} or {input-file} are resolved."
)
SHELL_TEXT_TOOLTIP = (
    "Shell command text. Use this mode for pipes, redirection, or several commands.\n"
    "System Shell: cmd.exe on Windows (each line runs only if the previous one succeeded), /bin/sh elsewhere.\n"
    "PowerShell: the whole text runs as one PowerShell script and stops on the first error.\n"
    "Batch tokens such as {project-dir} are resolved."
)
ENVIRONMENT_TOOLTIP = (
    "Extra environment variables for the process, one KEY=VALUE per line.\n"
    "Reference existing variables with ${NAME} or %NAME%, e.g. PATH=C:/tools;${PATH}\n"
    "Batch tokens are resolved. Values of names containing TOKEN, SECRET, PASSWORD, or KEY are masked in logs."
)
WAIT_MODE_TOOLTIP = (
    "Wait For Exit: run the command and wait until it finishes.\n"
    "Wait Until Ready: run the command, then repeat a readiness check until it passes,\n"
    "    e.g. 'docker compose up -d' followed by a health URL. If the command keeps\n"
    "    running (a server), it is left running once ready and stopped if never ready.\n"
    "Launch And Continue: start the program and move on without waiting (e.g. open an app)."
)
READY_TARGET_TOOLTIP = (
    "URL Responds: an http(s) URL that must answer with a 2xx/3xx status.\n"
    "Port Open: 'port' or 'host:port' that must accept TCP connections.\n"
    "File Exists: a file or folder path that must exist.\n"
    "Command Succeeds: a system shell command that must exit with code 0."
)
READY_TARGET_PLACEHOLDERS = {
    command_utils.ReadyCheck.URL: "http://127.0.0.1:8000/health",
    command_utils.ReadyCheck.PORT: "127.0.0.1:8000",
    command_utils.ReadyCheck.FILE: "{project-dir}/ready.flag",
    command_utils.ReadyCheck.COMMAND: "docker inspect -f {{.State.Running}} my_container",
}


class AttrWidgetCommandTask(AttrWidgetTask):
    """Attribute widget for the Command task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the Command widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskCommand, optional): Command task model.
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
        self.program_container = None
        self.shell_container = None
        self.ready_container = None
        self.timeout_container = None
        self.ready_target_field = None
        self.output_log_container = None
        self.add_common_task_settings(include_source=False, include_target=False, include_overwrite=False)
        self.add_command_controls()
        self.add_environment_controls()
        self.add_execution_controls()
        self.add_output_controls()
        self.add_widget_separator_line()
        self.add_action_buttons()
        self.add_segmentation_section(
            main_label="Run Once After All Jobs",
            main_key="run_once_after_multi_instance",
            main_tooltip=(
                "Run this command once after every regular job has finished,\n"
                "instead of once per input item (e.g. stop a Docker container).\n"
                "This task must be among the last enabled processing tasks."
            ),
        )
        self.content_layout.addStretch()
        self.refresh_visibility()

    # ------------------------------------------------------------------ Builders
    def add_container(self):
        """Adds a widget container whose visibility can be toggled.

        Returns:
            tuple: (QWidget container, QVBoxLayout for its rows).
        """
        container = ui_qt.QtWidgets.QWidget()
        layout = ui_qt.QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.content_layout.addWidget(container)
        return container, layout

    def add_command_controls(self):
        """Adds the command mode, program, and shell controls."""
        self.add_widget_separator_line(label_text="Command")
        self.add_combo_box(
            "Mode",
            self.task.settings.get("command_mode"),
            command_utils.COMMAND_MODES,
            self.set_command_mode,
            tooltip=(
                "Program: run an executable directly with an argument list (safest, no shell parsing).\n"
                "Shell: run text through cmd/sh or PowerShell (pipes, redirection, several commands)."
            ),
        )
        self.program_container, program_layout = self.add_container()
        self.add_path_template_field(
            "Executable",
            self.task.settings.get("executable"),
            partial(self.set_task_setting, key="executable"),
            placeholder="docker",
            tooltip=(
                "Program to run. A bare name such as 'docker' or 'git' is searched on PATH.\n"
                "A path may use batch tokens such as {project-dir}."
            ),
            file_filter="Programs (*.exe *.bat *.cmd *.ps1);;All Files (*);;",
            parent_layout=program_layout,
            convert_to_project_relative=False,
        )
        self.add_text_area(
            "Arguments",
            self.task.settings.get("arguments"),
            partial(self.set_task_setting, key="arguments"),
            placeholder="compose\n-f \"{project-dir}/docker/compose.yml\"\nup -d",
            tooltip=ARGUMENTS_TOOLTIP,
            parent_layout=program_layout,
        )
        self.shell_container, shell_layout = self.add_container()
        self.add_combo_box(
            "Shell",
            self.task.settings.get("shell_type"),
            command_utils.SHELL_TYPES,
            partial(self.set_task_setting, key="shell_type"),
            tooltip=SHELL_TEXT_TOOLTIP,
            parent_layout=shell_layout,
        )
        self.add_text_area(
            "Shell Command",
            self.task.settings.get("command_text"),
            partial(self.set_task_setting, key="command_text"),
            placeholder="docker compose -f \"{project-dir}/docker/compose.yml\" down",
            tooltip=SHELL_TEXT_TOOLTIP,
            parent_layout=shell_layout,
        )
        self.add_path_template_field(
            "Working Directory",
            self.task.settings.get("working_directory"),
            partial(self.set_task_setting, key="working_directory"),
            placeholder="{project-dir}",
            tooltip="Folder the command runs in. Empty uses the project directory.",
            dir_only=True,
        )

    def add_environment_controls(self):
        """Adds environment variable controls."""
        self.add_text_area(
            "Environment Variables",
            self.task.settings.get("environment_overrides"),
            partial(self.set_task_setting, key="environment_overrides"),
            placeholder="HF_HUB_OFFLINE=1\nPATH=C:/tools;${PATH}",
            tooltip=ENVIRONMENT_TOOLTIP,
        )
        options_layout = self.add_labeled_layout(
            "Environment",
            label_width=100,
            tooltip="Controls which variables the process receives.",
        )
        for label_text, key, tooltip in [
            (
                "Inherit Parent",
                "inherit_environment",
                "Start from the current process environment.\n"
                "When off, only system essentials such as PATH and SYSTEMROOT are kept.",
            ),
            (
                "Pass Task Args",
                "pass_standard_arguments",
                "Expose BATCH_INPUT, BATCH_SOURCE, BATCH_PROJECT, BATCH_PROJECT_DIR, BATCH_TASK, and BATCH_TASK_ID.",
            ),
            (
                "Pass Env",
                "pass_environment_arguments",
                "Expose project environment variables as BATCH_ENV_NAME process variables.",
            ),
        ]:
            self.add_checkbox(
                label_text,
                self.task.settings.get(key, True),
                partial(self.set_task_setting, key=key),
                layout=options_layout,
                tooltip=tooltip,
            )
        options_layout.addStretch()

    def add_execution_controls(self):
        """Adds wait, timeout, success, and readiness controls."""
        self.add_widget_separator_line(label_text="Execution")
        self.add_combo_box(
            "Wait Mode",
            self.task.settings.get("wait_mode"),
            command_utils.WAIT_MODES,
            self.set_wait_mode,
            tooltip=WAIT_MODE_TOOLTIP,
        )
        self.timeout_container, timeout_layout = self.add_container()
        self.add_spin_box(
            "Timeout (s)",
            self.task.settings.get("timeout_seconds", 0),
            partial(self.set_task_setting, key="timeout_seconds"),
            minimum=0,
            maximum=604800,
            tooltip="Stop the command (and its child processes) after this many seconds.\nZero waits forever.",
            parent_layout=timeout_layout,
        )
        self.ready_container, ready_layout = self.add_container()
        self.add_combo_box(
            "Ready Check",
            self.task.settings.get("ready_check"),
            command_utils.READY_CHECKS,
            self.set_ready_check,
            tooltip=READY_TARGET_TOOLTIP,
            parent_layout=ready_layout,
        )
        self.ready_target_field = self.add_text_field(
            "Ready Target",
            self.task.settings.get("ready_target"),
            partial(self.set_task_setting, key="ready_target"),
            placeholder=READY_TARGET_PLACEHOLDERS.get(self.task.settings.get("ready_check"), ""),
            tooltip=READY_TARGET_TOOLTIP,
            label_width=110,
            parent_layout=ready_layout,
        )
        self.add_spin_box(
            "Ready Timeout (s)",
            self.task.settings.get("ready_timeout_seconds", 600),
            partial(self.set_task_setting, key="ready_timeout_seconds"),
            minimum=0,
            maximum=604800,
            tooltip="Give up after this many seconds and stop the started process.\nZero waits forever.",
            parent_layout=ready_layout,
        )
        self.add_spin_box(
            "Check Every (s)",
            self.task.settings.get("ready_interval_seconds", 5),
            partial(self.set_task_setting, key="ready_interval_seconds"),
            minimum=1,
            maximum=3600,
            tooltip="Seconds between readiness checks.",
            parent_layout=ready_layout,
        )
        self.add_text_field(
            "Success Exit Codes",
            self.task.settings.get("accepted_exit_codes"),
            partial(self.set_task_setting, key="accepted_exit_codes"),
            placeholder="0",
            tooltip=(
                "Exit codes that count as success: single values, lists, and ranges, e.g. '0, 3-7'.\n"
                "Use * to accept any exit code. Robocopy, for example, succeeds with 0-7."
            ),
            label_width=110,
        )
        self.add_combo_box(
            "On Failure",
            self.task.settings.get("on_failure"),
            command_utils.FAILURE_ACTIONS,
            partial(self.set_task_setting, key="on_failure"),
            tooltip=(
                "Fail: stop this item (or the run, for run-once tasks).\n"
                "Warning: report a warning and continue.\n"
                "Ignore: log the failure and continue (e.g. stopping a container that is not running)."
            ),
        )

    def add_output_controls(self):
        """Adds output logging controls."""
        self.add_widget_separator_line(label_text="Output")
        options_layout = self.add_labeled_layout("Output", label_width=100, tooltip="Where command output goes.")
        self.add_checkbox(
            "Show In Log",
            self.task.settings.get("log_output", True),
            partial(self.set_task_setting, key="log_output"),
            layout=options_layout,
            tooltip="Stream every output line into the batch log.",
        )
        self.add_checkbox(
            "Write Log File",
            self.task.settings.get("write_output_log", False),
            self.set_write_output_log,
            layout=options_layout,
            tooltip="Also append the output to a text file.",
        )
        options_layout.addStretch()
        self.output_log_container, output_log_layout = self.add_container()
        self.add_path_template_field(
            "Log File",
            self.task.settings.get("output_log_path"),
            partial(self.set_task_setting, key="output_log_path"),
            placeholder="{project-dir}/logs/command_{task-idx-padded}.log",
            tooltip="Text file that receives the command output (appended).",
            file_filter="Log Files (*.log *.txt);;All Files (*);;",
            parent_layout=output_log_layout,
        )

    def add_action_buttons(self):
        """Adds the preview and run buttons."""
        layout = self.add_labeled_layout("Actions", tooltip="Preview or run this command.")
        preview_button = self.create_action_button(
            "Preview Command",
            tooltip="Show the resolved command, working directory, and environment overrides.",
            icon_path=ui_res_lib.Icon.ui_env_var,
        )
        preview_button.clicked.connect(lambda *args: self.show_command_preview())
        run_button = self.create_action_button(
            "Run Command",
            tooltip="Run only this Command task using the current settings.",
            icon_path=ui_res_lib.Icon.ui_play,
        )
        run_button.clicked.connect(self.run_this_task_now)
        layout.addWidget(preview_button)
        layout.addWidget(run_button)
        layout.addStretch()

    # ------------------------------------------------------------------ Setters
    def set_command_mode(self, value):
        """Sets the command mode and refreshes visible controls.

        Args:
            value (str): CommandMode value.
        """
        self.set_task_setting(value, key="command_mode")
        self.refresh_visibility()

    def set_wait_mode(self, value):
        """Sets the wait mode and refreshes visible controls.

        Args:
            value (str): WaitMode value.
        """
        self.set_task_setting(value, key="wait_mode")
        self.refresh_visibility()

    def set_ready_check(self, value):
        """Sets the readiness check and updates the target placeholder.

        Args:
            value (str): ReadyCheck value.
        """
        self.set_task_setting(value, key="ready_check")
        if self.ready_target_field:
            self.ready_target_field.setPlaceholderText(READY_TARGET_PLACEHOLDERS.get(value, ""))

    def set_write_output_log(self, value):
        """Sets output log writing and refreshes visible controls.

        Args:
            value (bool): Whether to write a log file.
        """
        self.set_task_setting(value, key="write_output_log")
        self.refresh_visibility()

    def refresh_visibility(self):
        """Shows only the controls that apply to the current settings."""
        is_shell = self.task.settings.get("command_mode") == command_utils.CommandMode.SHELL
        wait_mode = self.task.settings.get("wait_mode")
        visibility_pairs = [
            (self.program_container, not is_shell),
            (self.shell_container, is_shell),
            (self.timeout_container, wait_mode == command_utils.WaitMode.WAIT_FOR_EXIT),
            (self.ready_container, wait_mode == command_utils.WaitMode.WAIT_UNTIL_READY),
            (self.output_log_container, bool(self.task.settings.get("write_output_log", False))),
        ]
        for container, is_visible in visibility_pairs:
            if container is not None:
                container.setVisible(is_visible)

    def show_command_preview(self):
        """Shows the resolved command in a read-only output window."""
        lines = self.task.build_preview_lines(self.project)
        output_window = ui_python_output_view.PythonOutputView(parent=self, editable=False)
        output_window.setWindowTitle("Command Preview")
        output_window.set_python_output_text("\n".join(lines))
        output_window.show()
        self.emit_status_message(f'Previewed command for "{self.task.display_name}".')
