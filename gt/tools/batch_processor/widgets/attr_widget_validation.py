"""
Batch Processor Validation Task Widgets
"""

from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
from gt.tools.batch_processor.tasks import task_validation
import gt.ui.python_output_view as ui_python_output_view
import gt.ui.qt_import as ui_qt
from functools import partial
import json


class AttrWidgetMayaSceneValidationTask(AttrWidgetTask):
    """Attribute widget for Maya scene validation."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the Maya scene validation widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskValidationMayaScene, optional): Task model.
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
        self.add_common_task_settings()
        self.add_widget_separator_line(label_text="Scene Validation Preferences")
        self.add_combo_box(
            "Scope",
            self.task.settings.get("validation_scope"),
            ["Scene", "Selection", "Type"],
            partial(self.set_task_setting, key="validation_scope"),
            tooltip="Scope forwarded to validators that support it.",
        )
        self.add_combo_box(
            "Log Mode",
            self.task.settings.get("log_mode"),
            [
                task_validation.VALIDATION_LOG_ISSUES,
                task_validation.VALIDATION_LOG_ALL,
                task_validation.VALIDATION_LOG_NONE,
            ],
            partial(self.set_task_setting, key="log_mode"),
            tooltip="When validation logs should be written.",
        )
        self.add_checkbox(
            "Fail On Issues",
            self.task.settings.get("fail_on_issues"),
            partial(self.set_task_setting, key="fail_on_issues"),
            tooltip="Fail the task when any validator reports warning or worse.",
        )
        self.add_validator_controls()
        self.add_run_current_scene_button()
        self.content_layout.addStretch()

    def add_validator_controls(self):
        """Adds validator selector controls."""
        layout = self.add_labeled_layout("Validator", tooltip="Add a validator from gt.core.validator.")
        combo_box = ui_qt.QtWidgets.QComboBox()
        combo_box.setEditable(True)
        combo_box.setMinimumHeight(35)
        combo_box.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        for validator_name in task_validation.get_available_scene_validators():
            combo_box.addItem(validator_name)
        layout.addWidget(combo_box)
        add_button = ui_qt.QtWidgets.QPushButton("Add")
        add_button.setMinimumHeight(35)
        add_button.clicked.connect(partial(self.add_validator, combo_box=combo_box))
        layout.addWidget(add_button)
        self.validators_text_area = self.add_text_area(
            "Validators",
            "\n".join(self.task.settings.get("validators") or []),
            partial(self.set_task_setting_list_from_text, key="validators"),
            placeholder="One validator name per line.",
            tooltip="Validator class names to run for each scene.",
        )

    def add_validator(self, combo_box):
        """Adds a selected validator to the list.

        Args:
            combo_box (QComboBox): Validator selector.
        """
        validator_name = combo_box.currentText().strip()
        current_values = self.task.settings.get("validators") or []
        if validator_name and validator_name not in current_values:
            current_values.append(validator_name)
            self.task.settings["validators"] = current_values
            self.validators_text_area.setPlainText("\n".join(current_values))

    def add_run_current_scene_button(self):
        """Adds a button used to run validators against the current Maya scene."""
        tooltip = "Run the configured validators against the scene currently open in Maya."
        layout = self.add_labeled_layout("Actions", tooltip=tooltip)
        button = ui_qt.QtWidgets.QPushButton("Run On Current Scene")
        button.setMinimumHeight(35)
        button.setToolTip(tooltip)
        button.clicked.connect(self.run_validators_on_current_scene)
        layout.addWidget(button)
        layout.addStretch()

    def run_validators_on_current_scene(self):
        """Runs this task's validators against the current Maya scene and shows a result window."""
        if not self.task.get_validator_names():
            self.emit_status_message("Validate Scene has no validators configured.", status="warning")
            return
        try:
            results = self.task.run_validators()
        except Exception as exception:
            self.emit_status_message("Unable to run current-scene validation: {0}".format(exception), status="warning")
            return
        has_issues = any(result_data.get("status_value", 0) > 1 for result_data in results)
        title = "Validate Scene Results"
        output_window = ui_python_output_view.PythonOutputView(parent=self, editable=False)
        output_window.setWindowTitle(title)
        output_lines = [
            "Task: {0}".format(self.task.display_name),
            "Validators: {0}".format(len(results)),
            "Issues Found: {0}".format("Yes" if has_issues else "No"),
            "",
            json.dumps(results, indent=4, sort_keys=True),
        ]
        output_window.set_python_output_text("\n".join(output_lines))
        output_window.show()
        status = "warning" if has_issues else "info"
        self.emit_status_message("Validate Scene current-scene test finished.", status=status)


class AttrWidgetFileIntegrityValidationTask(AttrWidgetTask):
    """Attribute widget for file integrity validation."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the file validation widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskValidationFileIntegrity, optional): Task model.
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
        self.add_common_task_settings()
        self.add_widget_separator_line(label_text="File Integrity Preferences")
        self.add_combo_box(
            "Log Mode",
            self.task.settings.get("log_mode"),
            [
                task_validation.VALIDATION_LOG_ISSUES,
                task_validation.VALIDATION_LOG_ALL,
                task_validation.VALIDATION_LOG_NONE,
            ],
            partial(self.set_task_setting, key="log_mode"),
            tooltip="Write JSON integrity reports for every file, only files with issues, or never.",
        )
        self.add_text_field(
            "Min Size (Bytes)",
            self.task.settings.get("minimum_file_size_bytes"),
            partial(self.set_task_setting, key="minimum_file_size_bytes"),
            tooltip="Minimum valid file size in bytes. 1024 bytes = 1 KB. 1048576 bytes = 1 MB.",
        )
        self.add_text_field(
            "Max Size (Bytes)",
            self.task.settings.get("maximum_file_size_bytes"),
            partial(self.set_task_setting, key="maximum_file_size_bytes"),
            placeholder="Optional",
            tooltip="Optional maximum valid file size in bytes. Leave empty when there is no upper limit.",
        )
        self.add_combo_box(
            "Checksum",
            self.task.settings.get("checksum_algorithm"),
            ["sha1", "sha256", "md5"],
            partial(self.set_task_setting, key="checksum_algorithm"),
            tooltip="Hash algorithm used when detecting files with matching contents.",
        )
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 5)
        for label_text, key, tooltip in [
            ("Empty Files", "warn_when_empty", "Report zero-byte files as integrity warnings."),
            (
                "Group Size Diff",
                "warn_when_size_differs_from_group",
                "Report files whose byte size differs from the other files processed by this task.",
            ),
            ("Duplicate Hashes", "detect_duplicate_checksums", "Report files that share the same checksum."),
            ("Fail On Issues", "fail_on_issues", "Fail the task when any integrity issue is found."),
        ]:
            self.add_checkbox(
                label_text,
                self.task.settings.get(key),
                partial(self.set_task_setting, key=key),
                layout=layout,
                tooltip=tooltip,
            )
        layout.addStretch()
        self.content_layout.addLayout(layout)
        self.add_run_selected_task_button(
            label_text="Run Integrity Check",
            tooltip="Run only this Validate Integrity task against its configured source files.",
        )
        self.content_layout.addStretch()


class AttrWidgetFolderCompareValidationTask(AttrWidgetTask):
    """Attribute widget for folder comparison validation."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the folder compare widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskValidationFolderCompare, optional): Task model.
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
        self.add_common_task_settings(include_source=False)
        self.add_widget_separator_line(label_text="Parity Validation Preferences")
        self.add_path_template_field(
            "Folder A",
            self.task.settings.get("folder_a"),
            partial(self.set_task_setting, key="folder_a"),
            placeholder="{previous-task-path}",
            tooltip="First folder used as one side of the parity validation.",
            dir_only=True,
        )
        self.add_path_template_field(
            "Folder B",
            self.task.settings.get("folder_b"),
            partial(self.set_task_setting, key="folder_b"),
            placeholder="{next-task-path}",
            tooltip="Second folder used as the other side of the parity validation.",
            dir_only=True,
        )
        self.add_combo_box(
            "Method",
            self.task.settings.get("comparison_method"),
            task_validation.get_folder_compare_methods(),
            partial(self.set_task_setting, key="comparison_method"),
            tooltip=(
                "How folder parity is compared: relative paths, file names, file names without extensions, "
                "or SHA1 checksums for matching relative paths."
            ),
        )
        self.add_combo_box(
            "Log Mode",
            self.task.settings.get("log_mode"),
            [
                task_validation.VALIDATION_LOG_ISSUES,
                task_validation.VALIDATION_LOG_ALL,
                task_validation.VALIDATION_LOG_NONE,
            ],
            partial(self.set_task_setting, key="log_mode"),
            tooltip="Write JSON parity reports for every comparison, only comparisons with differences, or never.",
        )
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 5)
        self.add_checkbox(
            "Subdirectories",
            self.task.settings.get("include_subdirectories"),
            partial(self.set_task_setting, key="include_subdirectories"),
            layout=layout,
            tooltip="Include files inside nested folders when building the parity comparison.",
        )
        self.add_checkbox(
            "Fail On Differences",
            self.task.settings.get("fail_on_differences"),
            partial(self.set_task_setting, key="fail_on_differences"),
            layout=layout,
            tooltip="Fail this validation task when the compared folders do not match.",
        )
        layout.addStretch()
        self.content_layout.addLayout(layout)
        self.add_run_selected_task_button(
            label_text="Run Parity Check",
            tooltip="Run only this Validate Parity task against its configured folders.",
        )
        self.content_layout.addStretch()


