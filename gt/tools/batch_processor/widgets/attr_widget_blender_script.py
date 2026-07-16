"""
Batch Processor Blender Task Attribute Widget
"""

from gt.tools.batch_processor.widgets.attr_widget_motionbuilder_script import AttrWidgetMotionBuilderScriptTask
from gt.tools.batch_processor.widgets import attr_widget_base
from gt.tools.batch_processor.tasks import task_blender_script
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt
from functools import partial


class AttrWidgetBlenderScriptTask(AttrWidgetMotionBuilderScriptTask):
    """Attribute widget for Blender script tasks."""

    def add_motionbuilder_controls(self):
        """Adds Blender executable controls."""
        self.add_widget_separator_line(
            label_text="Blender",
            tooltip="Blender executable used to run this task outside Maya.",
        )
        tooltip = "Path to blender.exe. Example: C:/Program Files/Blender Foundation/Blender 4.1/blender.exe"
        layout = self.add_labeled_layout("Executable", label_width=100, tooltip=tooltip)
        field = self.create_text_field(
            text=self.task.settings.get("blender_executable"),
            placeholder="Optional until run: C:/Program Files/Blender Foundation/Blender 4.1/blender.exe",
            tooltip=tooltip,
        )
        info_button = ui_qt.QtWidgets.QPushButton()
        info_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_env_var))
        info_button.setToolTip("Get more information about the resolved executable path.")
        open_button = ui_qt.QtWidgets.QPushButton()
        open_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        open_button.setToolTip("Open the resolved Blender executable directory.")
        browse_button = ui_qt.QtWidgets.QPushButton()
        browse_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        browse_button.setToolTip("Browse for blender.exe.")
        find_button = ui_qt.QtWidgets.QPushButton("Find")
        find_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_reset))
        find_button.setToolTip("Try to locate Blender in common install folders.")
        layout.addWidget(field)
        layout.addWidget(info_button)
        layout.addWidget(open_button)
        layout.addWidget(browse_button)
        layout.addWidget(find_button)
        field.textChanged.connect(
            partial(
                self.set_path_field_value,
                field=field,
                setter=partial(self.set_task_setting, key="blender_executable"),
            )
        )
        info_button.clicked.connect(partial(self.open_env_var_feedback_dialog, field=field))
        open_button.clicked.connect(partial(self.open_resolved_path_directory, field=field))
        browse_button.clicked.connect(
            partial(
                self.open_path_dialog,
                field=field,
                dir_only=False,
                file_filter="Blender Executable (blender.exe);;Executables (*.exe);;All Files (*);;",
            )
        )
        find_button.clicked.connect(partial(self.find_blender_executable, field=field))
        self.motionbuilder_path_widgets = {
            "field": field,
            "info_button": info_button,
            "open_button": open_button,
            "browse_button": browse_button,
            "find_button": find_button,
        }

    def add_motionbuilder_execution_controls(self):
        """Adds Blender process behavior controls."""
        self.add_text_area(
            "Arguments",
            self.task.settings.get("blender_arguments"),
            partial(self.set_task_setting, key="blender_arguments"),
            placeholder=task_blender_script.DEFAULT_BLENDER_ARGUMENTS,
            tooltip="Blender process arguments. One argument per line, or quoted shell-style text.",
        )
        self.add_text_field(
            "Script Flag",
            self.task.settings.get("script_flag"),
            partial(self.set_task_setting, key="script_flag"),
            placeholder=task_blender_script.DEFAULT_BLENDER_SCRIPT_FLAG,
            tooltip="Command-line flag used before the script path.",
            label_width=100,
        )
        options_layout = self.add_labeled_layout(
            "Process",
            label_width=100,
            tooltip="Controls how the batch task waits for Blender.",
        )
        self.add_checkbox(
            "Wait",
            self.task.settings.get("wait_for_completion", True),
            partial(self.set_task_setting, key="wait_for_completion"),
            layout=options_layout,
            tooltip="Wait for Blender to finish before continuing the batch task.",
        )
        self.add_checkbox(
            "Require Output",
            self.task.settings.get("require_output_file", True),
            partial(self.set_task_setting, key="require_output_file"),
            layout=options_layout,
            tooltip=(
                "Fail when Blender exits without creating a file with the expected name in the output folder. "
                "The file extension is ignored."
            ),
        )
        self.add_checkbox(
            "Pass Task Args",
            self.task.settings.get("pass_standard_arguments", True),
            partial(self.set_task_setting, key="pass_standard_arguments"),
            layout=options_layout,
            tooltip="Pass --input, --output, --project-dir, --task, --task-id, and --context to the script.",
        )
        self.add_checkbox(
            "Pass Env",
            self.task.settings.get("pass_environment_arguments", True),
            partial(self.set_task_setting, key="pass_environment_arguments"),
            layout=options_layout,
            tooltip="Pass project environment variables as --env-name values and repeated --env-var name=value pairs.",
        )
        options_layout.addStretch()

        fallback_layout = self.add_labeled_layout(
            "Fallback",
            label_width=100,
            tooltip="Optional behavior when Blender does not write the expected output file.",
        )
        self.add_checkbox(
            "Copy Input",
            self.task.settings.get("copy_input_if_output_missing", False),
            partial(self.set_task_setting, key="copy_input_if_output_missing"),
            layout=fallback_layout,
            tooltip="Copy the input file to the output path if Blender does not create one.",
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

    def find_blender_executable(self, field):
        """Finds Blender and writes it to the executable field.

        Args:
            field (QLineEdit): Executable field to update.
        """
        found_path = task_blender_script.find_blender_executable()
        if not found_path:
            self.emit_status_message("Unable to find Blender in common install folders.", status="warning")
            return
        field.setText(found_path)
        self.emit_status_message("Found Blender executable: {0}".format(found_path))

    def on_button_run_code_clicked(self):
        """Prevents accidentally running Blender code in Maya."""
        self.emit_status_message(
            "Blender code is executed by running this task through the batch processor.",
            status="warning",
        )

    def on_insert_selection_clicked(self):
        """Prevents inserting Maya selection data into a Blender task."""
        self.emit_status_message(
            "Maya selection insertion is not available for Blender tasks.",
            status="warning",
        )
