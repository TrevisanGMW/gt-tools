"""
Batch Processor Validation Task Widgets
"""

from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
from gt.tools.batch_processor.widgets.inline_python_editor import InlinePythonEditorWidget
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
        self.node_type_widget = None
        self.add_common_task_settings()
        self.add_widget_separator_line(label_text="Scene Validation Preferences")
        self.add_combo_box(
            "Scope",
            self.task.settings.get("validation_scope"),
            task_validation.VALIDATION_SCOPES,
            self.set_validation_scope,
            tooltip=(
                "Scope forwarded to validators that support it.\n"
                "Scene: check everything in the scene.\n"
                "Selection: check the current selection, usually built by the pre-script.\n"
                "Type: check nodes matching the node types configured below."
            ),
        )
        self.add_node_type_controls()
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
        self.add_pre_validation_script_section()
        self.add_run_current_scene_button()
        self.add_segmentation_section(
            main_label="Run Once After All Jobs",
            main_key="run_once_after_multi_instance",
            main_tooltip=(
                "In multi-instance mode, wait for every regular job to succeed,\n"
                "then run this validation once over the files found at its Source Path.\n"
                "This task must be the last enabled processing task.\n"
                'Enable "Add Separator" to mark this run-once step in the task list.'
            ),
        )
        self.content_layout.addStretch()

    def add_node_type_controls(self):
        """Adds the node type field shown only while the Type scope is active."""
        node_type_tooltip = (
            "Single node type forwarded to the validators as node_type\n"
            "when the Type scope is used.\n"
            "Examples: mesh, joint, or nurbsCurve."
        )
        self.node_type_widget = ui_qt.QtWidgets.QWidget()
        node_type_layout = ui_qt.QtWidgets.QVBoxLayout(self.node_type_widget)
        node_type_layout.setContentsMargins(0, 0, 0, 0)
        node_type_layout.setSpacing(0)
        self.add_text_field(
            "Node Type",
            self.task.settings.get("validation_node_type"),
            partial(self.set_task_setting, key="validation_node_type"),
            placeholder="mesh",
            tooltip=node_type_tooltip,
            parent_layout=node_type_layout,
        )
        self.content_layout.addWidget(self.node_type_widget)
        self.refresh_node_type_visibility()

    def set_validation_scope(self, value):
        """Sets the validation scope and refreshes the node type field.

        Args:
            value (str): Selected scope name.
        """
        self.set_task_setting(value, key="validation_scope")
        self.refresh_node_type_visibility()

    def refresh_node_type_visibility(self):
        """Shows the node type field only while the Type scope is selected."""
        if not self.node_type_widget:
            return
        self.node_type_widget.setVisible(self.task.uses_node_type_scope())

    def add_pre_validation_script_section(self):
        """Adds the collapsed optional pre-validation script section."""
        collapsed = bool(self.task.settings.get("pre_validation_script_collapsed", True))
        section = self.add_collapsible_section(
            label_text="Pre-Validation Script",
            collapsed=collapsed,
            state_setter=partial(self.set_task_setting, key="pre_validation_script_collapsed"),
            tooltip="Optional Python script that runs in the loaded scene before the validators.",
        )
        layout = section.get("content_layout")
        options_layout = ui_qt.QtWidgets.QHBoxLayout()
        options_layout.setContentsMargins(0, 0, 0, 5)
        self.add_checkbox(
            "Run",
            self.task.settings.get("run_pre_validation_script"),
            partial(self.set_task_setting, key="run_pre_validation_script"),
            layout=options_layout,
            tooltip="Run the configured script after the scene is loaded and before validation starts.",
        )
        self.add_checkbox(
            "Pass Task Args",
            self.task.settings.get("pre_validation_script_pass_standard_arguments", True),
            partial(self.set_task_setting, key="pre_validation_script_pass_standard_arguments"),
            layout=options_layout,
            tooltip="Expose input, output, project, task, and related values as arguments and args.",
        )
        self.add_checkbox(
            "Pass Env",
            self.task.settings.get("pre_validation_script_pass_environment_arguments", True),
            partial(self.set_task_setting, key="pre_validation_script_pass_environment_arguments"),
            layout=options_layout,
            tooltip="Expose project environment variables as environment_variables and env.",
        )
        options_layout.addStretch()
        layout.addLayout(options_layout)
        editor = InlinePythonEditorWidget(
            parent=self,
            owner=self,
            text=self.task.settings.get("pre_validation_script_text") or "",
            placeholder="Write an optional pre-validation Python script here, or choose an example.",
            tooltip=(
                "Inline Python pass executed in the loaded scene before the validators run.\n"
                "Use it to build a selection for the Selection scope or to prepare the scene.\n"
                "Use context, arguments/args, environment_variables/env, project, task,\n"
                "work_item, output_path, validation_scope, node_type, and validator_names."
            ),
            text_changed_callback=partial(self.set_task_setting, key="pre_validation_script_text"),
            font_size=self.task.settings.get("pre_validation_script_font_size") or 14,
            font_size_changed_callback=partial(self.set_task_setting, key="pre_validation_script_font_size"),
            sample_scripts_directory=self.task.pre_validation_script_samples_directory,
        )
        layout.addWidget(editor)

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
        tooltip = (
            "Run the configured validators against the scene currently open in Maya.\n"
            "The pre-validation script runs first when it is enabled."
        )
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
            self.task.run_pre_validation_script_if_needed(
                project=self.project,
                work_item=None,
                step_output_dir="",
            )
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
        self.add_segmentation_section(
            main_label="Run Once After All Jobs",
            main_key="run_once_after_multi_instance",
            main_tooltip=(
                "In multi-instance mode, wait for every regular job to succeed,\n"
                "then run this integrity check once over the files found at its Source Path.\n"
                "This task must be the last enabled processing task.\n"
                'Enable "Add Separator" to mark this run-once step in the task list.'
            ),
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
        self.add_segmentation_section(
            main_label="Run Once After All Jobs",
            main_key="run_once_after_multi_instance",
            main_tooltip=(
                "In multi-instance mode, wait for every regular job to succeed,\n"
                "then compare the configured folders once.\n"
                "This task must be the last enabled processing task.\n"
                'Enable "Add Separator" to mark this run-once step in the task list.'
            ),
        )
        self.content_layout.addStretch()


