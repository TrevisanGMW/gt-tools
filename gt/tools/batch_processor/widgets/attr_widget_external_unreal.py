"""Batch Processor Unreal Engine task attribute widget."""

from functools import partial

from gt.tools.batch_processor.tasks import task_external_unreal
from gt.tools.batch_processor.widgets import attr_widget_base
from gt.tools.batch_processor.widgets.attr_widget_external_mobu import (
    AttrWidgetMotionBuilderScriptTask,
)
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt


class AttrWidgetUnrealScriptTask(AttrWidgetMotionBuilderScriptTask):
    """Attribute widget for Unreal Engine script tasks."""

    def add_motionbuilder_controls(self):
        """Adds Unreal Engine executable and project controls."""
        self.add_widget_separator_line(
            label_text="Unreal Engine",
            tooltip="Unreal Engine executable and project used by the task.",
        )

        executable_layout = self.add_labeled_layout(
            "Executable",
            label_width=100,
            tooltip="Path to UnrealEditor-Cmd.exe.",
        )
        executable_field = self.create_text_field(
            text=self.task.settings.get("unreal_executable"),
            placeholder=(
                "Optional until run: C:/Program Files/Epic Games/UE_5.5/"
                "Engine/Binaries/Win64/UnrealEditor-Cmd.exe"
            ),
            tooltip="Path to UnrealEditor-Cmd.exe.",
        )
        executable_field.textChanged.connect(
            partial(self.set_task_setting, key="unreal_executable")
        )
        executable_layout.addWidget(executable_field)

        browse_executable_button = ui_qt.QtWidgets.QPushButton()
        browse_executable_button.setIcon(
            ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open)
        )
        browse_executable_button.setToolTip("Browse for UnrealEditor-Cmd.exe.")
        browse_executable_button.clicked.connect(
            partial(
                self.open_path_dialog,
                field=executable_field,
                file_filter=(
                    "Unreal Editor (UnrealEditor-Cmd.exe);;"
                    "Executables (*.exe);;All Files (*)"
                ),
            )
        )
        executable_layout.addWidget(browse_executable_button)

        find_executable_button = ui_qt.QtWidgets.QPushButton("Find")
        find_executable_button.setIcon(
            ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_reset)
        )
        find_executable_button.setToolTip(
            "Try to locate UnrealEditor-Cmd.exe in common install folders."
        )
        find_executable_button.clicked.connect(
            partial(self.find_unreal_executable, executable_field)
        )
        executable_layout.addWidget(find_executable_button)

        project_layout = self.add_labeled_layout(
            "Project",
            label_width=100,
            tooltip="Unreal .uproject file required for headless execution.",
        )
        project_field = self.create_text_field(
            text=self.task.settings.get("unreal_project_path"),
            placeholder="Required: C:/Project/MyProject.uproject",
            tooltip="Unreal .uproject file required for headless execution.",
        )
        project_field.textChanged.connect(
            partial(self.set_task_setting, key="unreal_project_path")
        )
        project_layout.addWidget(project_field)

        browse_project_button = ui_qt.QtWidgets.QPushButton()
        browse_project_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        browse_project_button.setToolTip("Browse for an Unreal .uproject file.")
        browse_project_button.clicked.connect(
            partial(
                self.open_path_dialog,
                field=project_field,
                file_filter=(
                    "Unreal Project (*.uproject);;All Files (*)"
                ),
            )
        )
        project_layout.addWidget(browse_project_button)

    def add_motionbuilder_execution_controls(self):
        """Adds Unreal Engine process and argument controls."""
        self.add_text_area(
            "Arguments",
            self.task.settings.get("unreal_arguments"),
            partial(self.set_task_setting, key="unreal_arguments"),
            placeholder=task_external_unreal.DEFAULT_UNREAL_ARGUMENTS,
            tooltip="Unreal Engine command-line arguments.",
        )

        options_layout = self.add_labeled_layout(
            "Process",
            label_width=100,
            tooltip="Controls how the batch task waits for Unreal Engine.",
        )
        self.add_checkbox(
            "Wait",
            self.task.settings.get("wait_for_completion", True),
            partial(self.set_task_setting, key="wait_for_completion"),
            layout=options_layout,
            tooltip="Wait for Unreal Engine to finish before continuing.",
        )
        self.add_checkbox(
            "Require Output",
            self.task.settings.get("require_output_file", True),
            partial(self.set_task_setting, key="require_output_file"),
            layout=options_layout,
            tooltip="Fail when the task does not create its expected output.",
        )
        self.add_checkbox(
            "Pass Task Args",
            self.task.settings.get("pass_standard_arguments", True),
            partial(self.set_task_setting, key="pass_standard_arguments"),
            layout=options_layout,
            tooltip="Pass standard batch arguments after the Unreal script flag.",
        )
        self.add_checkbox(
            "Pass Env",
            self.task.settings.get("pass_environment_arguments", True),
            partial(self.set_task_setting, key="pass_environment_arguments"),
            layout=options_layout,
            tooltip="Pass project environment variables to the script.",
        )
        options_layout.addStretch()

        fallback_layout = self.add_labeled_layout(
            "Fallback",
            label_width=100,
            tooltip="Optional behavior when Unreal does not create an output.",
        )
        self.add_checkbox(
            "Copy Input",
            self.task.settings.get("copy_input_if_output_missing", False),
            partial(
                self.set_task_setting,
                key="copy_input_if_output_missing",
            ),
            layout=fallback_layout,
            tooltip="Copy the input to the output path when no output is created.",
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
        timeout_spinbox.valueChanged.connect(
            partial(self.set_task_setting, key="timeout_seconds")
        )
        fallback_layout.addWidget(timeout_spinbox)
        fallback_layout.addStretch()

    def find_unreal_executable(self, field):
        """Finds UnrealEditor-Cmd.exe and updates the executable field.

        Args:
            field (QLineEdit): Executable field to update.
        """
        found_path = task_external_unreal.find_unreal_executable()
        if not found_path:
            self.emit_status_message(
                "Unable to find UnrealEditor-Cmd.exe in common install folders.",
                status="warning",
            )
            return
        field.setText(found_path)
        self.emit_status_message(f"Found Unreal executable: {found_path}")

    def on_button_run_code_clicked(self):
        """Prevents accidentally running Unreal code in Maya."""
        self.emit_status_message(
            "Unreal Engine code is executed by running the batch task.",
            status="warning",
        )

    def on_insert_selection_clicked(self):
        """Prevents inserting Maya selection data into an Unreal task."""
        self.emit_status_message(
            "Maya selection insertion is not available for Unreal tasks.",
            status="warning",
        )
