"""
Batch Processor MotionBuilder Task Attribute Widget
"""

from gt.tools.batch_processor.widgets.attr_widget_python_script import AttrWidgetPythonScriptTask
from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
from gt.tools.batch_processor.widgets import attr_widget_base
from gt.tools.batch_processor.tasks import task_motionbuilder_script
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt
from functools import partial
import os


class AttrWidgetMotionBuilderScriptTask(AttrWidgetPythonScriptTask):
    """Attribute widget for MotionBuilder script tasks."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the MotionBuilder script task widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskMotionBuilderScript, optional): MotionBuilder task.
            project (BatchProcessorModel, optional): Project model.
            refresh_parent_func (callable, optional): Function used to refresh parent UI.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        AttrWidgetTask.__init__(
            self,
            parent=parent,
            task=task,
            project=project,
            refresh_parent_func=refresh_parent_func,
            *args,
            **kwargs
        )
        self.mode_buttons = None
        self.python_edit = None
        self.python_edit_font = None
        self.font_size_slider = None
        self.font_size_value_label = None
        self.highlighter = None
        self.base_stylesheet = ""
        self.single_mode_widget = None
        self.external_mode_widget = None
        self.batch_mode_widget = None
        self.script_path_widgets = None
        self.scripts_path_widgets = None
        self.script_list_layout = None
        self.script_count_label = None
        self.batch_filters_button = None
        self.batch_filters_widget = None
        self.batch_include_field = None
        self.batch_exclude_field = None
        self.motionbuilder_path_widgets = None

        self.add_common_task_settings()
        self.add_motionbuilder_controls()
        self.add_motionbuilder_execution_controls()
        self.add_python_mode_controls()
        self.add_single_script_controls()
        self.remove_inline_maya_buttons()
        self.add_external_file_controls()
        self.add_batch_script_controls()
        self.refresh_mode_visibility()
        self.content_layout.addStretch()

    def add_motionbuilder_controls(self):
        """Adds MotionBuilder executable controls."""
        self.add_widget_separator_line(
            label_text="MotionBuilder",
            tooltip="MotionBuilder executable used to run this task outside Maya.",
        )
        tooltip = "Path to motionbuilder.exe. Example: C:/Program Files/Autodesk/MotionBuilder 2025/bin/x64/motionbuilder.exe"
        layout = self.add_labeled_layout("Executable", label_width=100, tooltip=tooltip)
        field = self.create_text_field(
            text=self.task.settings.get("motionbuilder_executable"),
            placeholder="Optional until run: C:/Program Files/Autodesk/MotionBuilder 2025/bin/x64/motionbuilder.exe",
            tooltip=tooltip,
        )
        info_button = ui_qt.QtWidgets.QPushButton()
        info_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_env_var))
        info_button.setToolTip("Get more information about the resolved executable path.")
        open_button = ui_qt.QtWidgets.QPushButton()
        open_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        open_button.setToolTip("Open the resolved MotionBuilder executable directory.")
        browse_button = ui_qt.QtWidgets.QPushButton()
        browse_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        browse_button.setToolTip("Browse for motionbuilder.exe.")
        find_button = ui_qt.QtWidgets.QPushButton("Find")
        find_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_reset))
        find_button.setToolTip("Try to locate MotionBuilder in common Autodesk install folders.")
        layout.addWidget(field)
        layout.addWidget(info_button)
        layout.addWidget(open_button)
        layout.addWidget(browse_button)
        layout.addWidget(find_button)
        field.textChanged.connect(
            partial(
                self.set_path_field_value,
                field=field,
                setter=partial(self.set_task_setting, key="motionbuilder_executable"),
            )
        )
        info_button.clicked.connect(partial(self.open_env_var_feedback_dialog, field=field))
        open_button.clicked.connect(partial(self.open_resolved_path_directory, field=field))
        browse_button.clicked.connect(
            partial(
                self.open_path_dialog,
                field=field,
                dir_only=False,
                file_filter="MotionBuilder Executable (motionbuilder.exe);;Executables (*.exe);;All Files (*);;",
            )
        )
        find_button.clicked.connect(partial(self.find_motionbuilder_executable, field=field))
        self.motionbuilder_path_widgets = {
            "field": field,
            "info_button": info_button,
            "open_button": open_button,
            "browse_button": browse_button,
            "find_button": find_button,
        }

    def add_motionbuilder_execution_controls(self):
        """Adds MotionBuilder process behavior controls."""
        self.add_text_area(
            "Arguments",
            self.task.settings.get("motionbuilder_arguments"),
            partial(self.set_task_setting, key="motionbuilder_arguments"),
            placeholder=task_motionbuilder_script.DEFAULT_MOBU_ARGUMENTS,
            tooltip="MotionBuilder process arguments. One argument per line, or quoted shell-style text.",
        )
        self.add_text_field(
            "Script Flag",
            self.task.settings.get("script_flag"),
            partial(self.set_task_setting, key="script_flag"),
            placeholder="Optional. Usually empty for MotionBuilder.",
            tooltip=(
                "Optional command-line flag used before the script path. "
                "Leave empty for the standard MotionBuilder batch command."
            ),
            label_width=100,
        )
        options_layout = self.add_labeled_layout(
            "Process",
            label_width=100,
            tooltip="Controls how the batch task waits for MotionBuilder.",
        )
        self.add_checkbox(
            "Wait",
            self.task.settings.get("wait_for_completion", True),
            partial(self.set_task_setting, key="wait_for_completion"),
            layout=options_layout,
            tooltip="Wait for MotionBuilder to finish before continuing the batch task.",
        )
        self.add_checkbox(
            "Require Output",
            self.task.settings.get("require_output_file", True),
            partial(self.set_task_setting, key="require_output_file"),
            layout=options_layout,
            tooltip="Fail when MotionBuilder exits without creating the expected output file.",
        )
        self.add_checkbox(
            "Pass Task Args",
            self.task.settings.get("pass_standard_arguments", True),
            partial(self.set_task_setting, key="pass_standard_arguments"),
            layout=options_layout,
            tooltip=(
                "Expose task values to MotionBuilder through BATCH_INPUT, BATCH_OUTPUT, BATCH_PROJECT_DIR, "
                "BATCH_TASK, BATCH_TASK_ID, and BATCH_CONTEXT."
            ),
        )
        self.add_checkbox(
            "Pass Env",
            self.task.settings.get("pass_environment_arguments", True),
            partial(self.set_task_setting, key="pass_environment_arguments"),
            layout=options_layout,
            tooltip="Expose project environment variables as BATCH_ENV_NAME process variables.",
        )
        options_layout.addStretch()

        fallback_layout = self.add_labeled_layout(
            "Fallback",
            label_width=100,
            tooltip="Optional behavior when MotionBuilder does not write the expected output file.",
        )
        self.add_checkbox(
            "Copy Input",
            self.task.settings.get("copy_input_if_output_missing", False),
            partial(self.set_task_setting, key="copy_input_if_output_missing"),
            layout=fallback_layout,
            tooltip="Copy the input file to the output path if MotionBuilder does not create one.",
        )
        timeout_label = ui_qt.QtWidgets.QLabel("Timeout:")
        attr_widget_base.configure_label_for_scaled_displays(timeout_label)
        timeout_label.setToolTip("Maximum seconds to wait. Zero means no timeout.")
        fallback_layout.addWidget(timeout_label)
        timeout_spinbox = ui_qt.QtWidgets.QSpinBox()
        timeout_spinbox.setRange(0, 999999)
        timeout_spinbox.setValue(int(self.task.settings.get("timeout_seconds") or 0))
        timeout_spinbox.setMinimumHeight(35)
        timeout_spinbox.setToolTip("Maximum seconds to wait. Zero means no timeout.")
        timeout_spinbox.valueChanged.connect(partial(self.set_task_setting, key="timeout_seconds"))
        fallback_layout.addWidget(timeout_spinbox)
        fallback_layout.addStretch()

    def remove_inline_maya_buttons(self):
        """Removes Maya-only inline editor buttons from this external application task."""
        if not self.single_mode_widget:
            return
        for button in self.single_mode_widget.findChildren(ui_qt.QtWidgets.QPushButton):
            if button.text() == "Run Code":
                button.setParent(None)
                button.deleteLater()

    def find_motionbuilder_executable(self, field):
        """Finds MotionBuilder and writes it to the executable field.

        Args:
            field (QLineEdit): Executable field to update.
        """
        found_path = task_motionbuilder_script.find_motionbuilder_executable()
        if not found_path:
            self.emit_status_message("Unable to find MotionBuilder in common install folders.", status="warning")
            return
        field.setText(found_path)
        self.emit_status_message("Found MotionBuilder executable: {0}".format(found_path))

    def on_button_run_code_clicked(self):
        """Prevents accidentally running MotionBuilder code in Maya."""
        self.emit_status_message(
            "MotionBuilder code is executed by running this task through the batch processor.",
            status="warning",
        )

    def on_insert_selection_clicked(self):
        """Prevents inserting Maya selection data into a MotionBuilder task."""
        self.emit_status_message(
            "Maya selection insertion is not available for MotionBuilder tasks.",
            status="warning",
        )

    def refresh_script_list(self, update_status=True):
        """Refreshes detected MotionBuilder Python scripts.

        Args:
            update_status (bool, optional): Whether to emit a bottom status message.
        """
        super().refresh_script_list(update_status=update_status)
        if self.script_count_label:
            self.script_count_label.setToolTip("Detected MotionBuilder Python scripts.")

    def open_python_script(self, script_path):
        """Opens a script path in the operating system.

        Args:
            script_path (str): Script path to open.
        """
        if not script_path or not os.path.isfile(script_path):
            self.emit_status_message("Unable to open MotionBuilder script: path does not exist.", status="warning")
            return
        super().open_python_script(script_path=script_path)
