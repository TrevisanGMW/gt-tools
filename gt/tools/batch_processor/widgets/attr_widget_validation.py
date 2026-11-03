"""
Batch Processor Validation Task Widgets
"""

from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
from gt.tools.batch_processor.widgets.inline_python_editor import InlinePythonEditorWidget
from gt.tools.batch_processor.widgets.table_height_handle import TableHeightHandle
from gt.tools.batch_processor.tasks import task_validation_python
from gt.tools.batch_processor.tasks import task_validation
import gt.ui.python_output_view as ui_python_output_view
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt
from functools import partial
import traceback
import json


LABEL_WIDTH = 100
SCRIPT_EDITOR_DEFAULT_HEIGHT = 320
SCRIPT_EDITOR_MINIMUM_HEIGHT = 200
ROW_COLUMNS = 4
LOG_MODE_VALUES = [
    task_validation.VALIDATION_LOG_ISSUES,
    task_validation.VALIDATION_LOG_ALL,
    task_validation.VALIDATION_LOG_NONE,
]
RUN_ONCE_AFTER_TOOLTIP = (
    "In multi-instance mode, wait for every regular job to succeed,\n"
    "then run this {0} once over the files found at its Source Path.\n"
    "This task must be the last enabled processing task.\n"
    'Enable "Add Separator" to mark this run-once step in the task list.'
)


class AttrWidgetValidationTaskBase(AttrWidgetTask):
    """Shared layout helpers used by every validation task widget.

    Option rows use a fixed grid of ROW_COLUMNS equal columns that lines up with
    the I/O Mode row, and every row label uses the same width as the Task
    Input/Output section so fields start at the same horizontal position.
    """

    def add_labeled_layout(self, label_text, label_width=LABEL_WIDTH, tooltip=None, parent_layout=None):
        """Adds a labeled row using the validation label width by default.

        Args:
            label_text (str): Label text.
            label_width (int, optional): Label width.
            tooltip (str, optional): Tooltip assigned to the label.
            parent_layout (QLayout, optional): Layout that receives the new row.

        Returns:
            QHBoxLayout: Created layout.
        """
        return super().add_labeled_layout(
            label_text,
            label_width=label_width,
            tooltip=tooltip,
            parent_layout=parent_layout,
        )

    @staticmethod
    def add_row_cell(layout, span=1):
        """Adds one grid cell to an option row.

        Args:
            layout (QHBoxLayout): Row layout.
            span (int, optional): Number of grid columns the cell occupies.

        Returns:
            QHBoxLayout: Layout inside the cell.
        """
        cell_widget = ui_qt.QtWidgets.QWidget()
        cell_widget.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        cell_widget.setProperty("grid_span", int(span))
        cell_layout = ui_qt.QtWidgets.QHBoxLayout(cell_widget)
        cell_layout.setContentsMargins(0, 0, 0, 0)
        cell_layout.setSpacing(5)
        layout.addWidget(cell_widget, int(span))
        return cell_layout

    @staticmethod
    def fill_row_cells(layout):
        """Adds empty cells so a row always spans ROW_COLUMNS grid columns.

        Args:
            layout (QHBoxLayout): Row layout.
        """
        used_columns = 0
        for item_index in range(layout.count()):
            widget = layout.itemAt(item_index).widget()
            if widget is not None and widget.property("grid_span"):
                used_columns += int(widget.property("grid_span"))
        for _ in range(max(0, ROW_COLUMNS - used_columns)):
            AttrWidgetValidationTaskBase.add_row_cell(layout)

    def add_row_combo_cell(self, layout, value, values, key, tooltip="", span=1):
        """Adds a combo box cell bound to a task setting.

        The row label describes the whole row, so cells never add their own labels.

        Args:
            layout (QHBoxLayout): Row layout.
            value (str): Current value.
            values (list): Available values.
            key (str): Task setting key.
            tooltip (str, optional): Tooltip text.
            span (int, optional): Number of grid columns the cell occupies.

        Returns:
            QComboBox: Created combo box.
        """
        cell_layout = self.add_row_cell(layout, span=span)
        combo_box = self.create_row_combo_box(value=value, values=values, tooltip=tooltip)
        combo_box.currentTextChanged.connect(partial(self.set_task_setting, key=key))
        cell_layout.addWidget(combo_box, 1)
        return combo_box

    def add_results_row(
        self,
        log_tooltip,
        fail_key="fail_on_issues",
        fail_label="Fail On Issues",
        fail_tooltip="",
        parent_layout=None,
    ):
        """Adds one "Log & Fail" row holding the log mode and the fail-on-issues option.

        Args:
            log_tooltip (str): Tooltip for the log mode combo.
            fail_key (str, optional): Task setting key for the fail option.
            fail_label (str, optional): Visible label for the fail option.
            fail_tooltip (str, optional): Tooltip for the fail option.
            parent_layout (QLayout, optional): Layout receiving the row.

        Returns:
            tuple: (QComboBox, QCheckBox) created controls.
        """
        layout = self.add_labeled_layout(
            "Log & Fail",
            tooltip=f"When validation logs are written, and whether issues fail the task.\n{log_tooltip}",
            parent_layout=parent_layout,
        )
        log_combo = self.add_row_combo_cell(
            layout,
            self.task.settings.get("log_mode"),
            LOG_MODE_VALUES,
            "log_mode",
            tooltip=log_tooltip,
            span=ROW_COLUMNS - 1,
        )
        fail_checkbox = self.add_option_checkbox(layout, fail_label, fail_key, fail_tooltip)
        return log_combo, fail_checkbox

    def add_checkbox_row(self, label_text, options, tooltip=None, parent_layout=None):
        """Adds a labeled row of evenly distributed checkboxes.

        Args:
            label_text (str): Row label.
            options (list): Tuples of (checkbox text, setting key, tooltip, default value).
            tooltip (str, optional): Row label tooltip.
            parent_layout (QLayout, optional): Layout receiving the row.

        Returns:
            dict: Checkboxes keyed by setting key.
        """
        layout = self.add_labeled_layout(label_text, tooltip=tooltip, parent_layout=parent_layout)
        checkboxes = {}
        for option_label, key, option_tooltip, default_value in options:
            checkboxes[key] = self.add_option_checkbox(layout, option_label, key, option_tooltip, default_value)
        self.fill_row_cells(layout)
        return checkboxes

    def add_option_checkbox(self, layout, label_text, key, tooltip="", default_value=False):
        """Adds one evenly spaced checkbox bound to a task setting.

        Args:
            layout (QHBoxLayout): Row layout receiving the checkbox.
            label_text (str): Checkbox text.
            key (str): Task setting key.
            tooltip (str, optional): Checkbox tooltip.
            default_value (bool, optional): Value used when the setting is missing.

        Returns:
            QCheckBox: Created checkbox.
        """
        checkbox = ui_qt.QtWidgets.QCheckBox(label_text)
        checkbox.setMinimumHeight(checkbox.sizeHint().height() + 2)
        checkbox.setChecked(bool(self.task.settings.get(key, default_value)))
        checkbox.setToolTip(tooltip or label_text)
        checkbox.stateChanged.connect(lambda *args: self.set_task_setting(checkbox.isChecked(), key=key))
        cell_layout = self.add_row_cell(layout)
        cell_layout.addWidget(checkbox)
        cell_layout.addStretch()
        return checkbox

    def add_actions_row(self, buttons, tooltip=None):
        """Adds an Actions row holding padded action buttons.

        Args:
            buttons (list): Tuples of (label, tooltip, callback, icon path).
            tooltip (str, optional): Row label tooltip.

        Returns:
            list: Created buttons.
        """
        layout = self.add_labeled_layout("Actions", tooltip=tooltip)
        created_buttons = []
        for label_text, button_tooltip, callback, icon_path in buttons:
            button = self.create_action_button(label_text, tooltip=button_tooltip, icon_path=icon_path)
            button.clicked.connect(callback)
            layout.addWidget(button)
            created_buttons.append(button)
        layout.addStretch()
        return created_buttons

    def show_results_window(self, title, output_lines):
        """Shows a read-only results window.

        Args:
            title (str): Window title.
            output_lines (list): Lines displayed in the window.

        Returns:
            PythonOutputView: Created window.
        """
        output_window = ui_python_output_view.PythonOutputView(parent=self, editable=False)
        output_window.setWindowTitle(title)
        output_window.set_python_output_text("\n".join(output_lines))
        output_window.show()
        return output_window


class AttrWidgetMayaSceneValidationTask(AttrWidgetValidationTaskBase):
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
        self.validators_text_area = None
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
                "Type: check nodes matching the node type configured below."
            ),
        )
        self.add_node_type_controls()
        self.add_results_row(
            log_tooltip="When validation logs should be written.",
            fail_tooltip="Fail the task when any validator reports warning or worse.",
        )
        self.add_validator_controls()
        self.add_pre_validation_script_section()
        self.add_actions_row(
            [
                (
                    "Run On Current Scene",
                    "Run the configured validators against the scene currently open in Maya.\n"
                    "The pre-validation script runs first when it is enabled.",
                    self.run_validators_on_current_scene,
                    ui_res_lib.Icon.ui_play,
                ),
            ]
        )
        self.add_segmentation_section(
            main_label="Run Once After All Jobs",
            main_key="run_once_after_multi_instance",
            main_tooltip=RUN_ONCE_AFTER_TOOLTIP.format("validation"),
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
            label_width=LABEL_WIDTH,
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
        options_layout = self.add_labeled_layout(
            "Script",
            tooltip="Pre-validation script options.",
            parent_layout=layout,
        )
        for label_text, key, tooltip, default_value in [
            (
                "Run",
                "run_pre_validation_script",
                "Run the configured script after the scene is loaded and before validation starts.",
                False,
            ),
            (
                "Pass Task Args",
                "pre_validation_script_pass_standard_arguments",
                "Expose input, output, project, task, and related values as arguments and args.",
                True,
            ),
            (
                "Pass Env",
                "pre_validation_script_pass_environment_arguments",
                "Expose project environment variables as environment_variables and env.",
                True,
            ),
        ]:
            self.add_option_checkbox(options_layout, label_text, key, tooltip, default_value)
        self.fill_row_cells(options_layout)
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
        add_button = self.create_action_button("Add", tooltip="Add the selected validator to the list.")
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
            self.emit_status_message(f"Unable to run current-scene validation: {exception}", status="warning")
            return
        has_issues = any(result_data.get("status_value", 0) > 1 for result_data in results)
        self.show_results_window(
            "Validate Scene Results",
            [
                f"Task: {self.task.display_name}",
                f"Validators: {len(results)}",
                f"Issues Found: {'Yes' if has_issues else 'No'}",
                "",
                json.dumps(results, indent=4, sort_keys=True),
            ],
        )
        status = "warning" if has_issues else "info"
        self.emit_status_message("Validate Scene current-scene test finished.", status=status)


class AttrWidgetFileIntegrityValidationTask(AttrWidgetValidationTaskBase):
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
        self.add_results_row(
            log_tooltip="Write JSON integrity reports for every file, only files with issues, or never.",
            fail_tooltip="Fail the task when any integrity issue is found.",
        )
        self.add_file_size_row()
        self.add_combo_box(
            "Checksum",
            self.task.settings.get("checksum_algorithm"),
            ["sha1", "sha256", "md5"],
            partial(self.set_task_setting, key="checksum_algorithm"),
            tooltip="Hash algorithm used when detecting files with matching contents.",
        )
        self.add_checkbox_row(
            "Checks",
            [
                ("Empty Files", "warn_when_empty", "Report zero-byte files as integrity warnings.", True),
                (
                    "Group Size Diff",
                    "warn_when_size_differs_from_group",
                    "Report files whose byte size differs from the other files processed by this task.",
                    False,
                ),
                (
                    "Duplicate Hashes",
                    "detect_duplicate_checksums",
                    "Report files that share the same checksum.",
                    False,
                ),
            ],
            tooltip="Optional integrity checks.",
        )
        self.add_actions_row(
            [
                (
                    "Run Integrity Check",
                    "Run only this Validate Integrity task against its configured source files.",
                    self.run_this_task_now,
                    ui_res_lib.Icon.ui_play,
                ),
            ]
        )
        self.add_segmentation_section(
            main_label="Run Once After All Jobs",
            main_key="run_once_after_multi_instance",
            main_tooltip=RUN_ONCE_AFTER_TOOLTIP.format("integrity check"),
        )
        self.content_layout.addStretch()

    def add_file_size_row(self):
        """Adds the minimum and maximum file size fields on one aligned row."""
        size_tooltip = "File size limits in bytes.\n1024 bytes = 1 KB.\n1048576 bytes = 1 MB."
        layout = self.add_labeled_layout("Min / Max Bytes", tooltip=f"Minimum and maximum file size.\n{size_tooltip}")
        for key, placeholder, tooltip in [
            ("minimum_file_size_bytes", "Minimum (0)", "Minimum valid file size in bytes."),
            (
                "maximum_file_size_bytes",
                "Maximum (no limit)",
                "Optional maximum valid file size in bytes.\nLeave empty when there is no upper limit.",
            ),
        ]:
            group_layout = self.add_row_cell(layout, span=ROW_COLUMNS // 2)
            field = self.create_text_field(
                text=self.task.settings.get(key),
                placeholder=placeholder,
                tooltip=f"{tooltip}\n{size_tooltip}",
            )
            field.textChanged.connect(partial(self.set_task_setting, key=key))
            group_layout.addWidget(field, 1)


class AttrWidgetFolderCompareValidationTask(AttrWidgetValidationTaskBase):
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
        self.add_comparison_row()
        self.add_results_row(
            log_tooltip="Write JSON parity reports for every comparison, only comparisons with differences, or never.",
            fail_key="fail_on_differences",
            fail_label="Fail On Differences",
            fail_tooltip="Fail this validation task when the compared folders do not match.",
        )
        self.add_actions_row(
            [
                (
                    "Run Parity Check",
                    "Run only this Validate Parity task against its configured folders.",
                    self.run_this_task_now,
                    ui_res_lib.Icon.ui_play,
                ),
            ]
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

    def add_comparison_row(self):
        """Adds the comparison method and subdirectory option on one row."""
        method_tooltip = (
            "How folder parity is compared: relative paths, file names, file names without extensions, "
            "or SHA1 checksums for matching relative paths."
        )
        layout = self.add_labeled_layout("Compare", tooltip=method_tooltip)
        self.add_row_combo_cell(
            layout,
            self.task.settings.get("comparison_method"),
            task_validation.get_folder_compare_methods(),
            "comparison_method",
            tooltip=method_tooltip,
            span=ROW_COLUMNS - 1,
        )
        self.add_option_checkbox(
            layout,
            "Subdirectories",
            "include_subdirectories",
            "Include files inside nested folders when building the parity comparison.",
            True,
        )


class AttrWidgetPythonValidationTask(AttrWidgetValidationTaskBase):
    """Attribute widget for custom Python script validation."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the Python validation widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskValidationPythonScript, optional): Task model.
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
        self.mode_buttons = {}
        self.mode_button_group = None
        self.preferences_section = None
        self.script_editor_height_handle = None
        self.inline_mode_widget = None
        self.external_mode_widget = None
        self.script_editor = None
        self.scene_option_widgets = []
        self.add_common_task_settings()
        self.preferences_section = self.add_collapsible_section(
            label_text="Python Validation Preferences",
            collapsed=bool(self.task.settings.get("preferences_collapsed", False)),
            state_setter=partial(self.set_task_setting, key="preferences_collapsed"),
            tooltip="Script mode, context, scene loading, logging, and failure options.",
        )
        preferences_layout = self.preferences_section.get("content_layout")
        self.add_mode_row(parent_layout=preferences_layout)
        self.add_context_row(parent_layout=preferences_layout)
        self.add_scene_row(parent_layout=preferences_layout)
        self.add_results_row(
            log_tooltip="Write JSON validation reports for every file, only files with issues, or never.",
            fail_tooltip="Fail the task when the script reports errors (or warnings, when they count as issues).",
            parent_layout=preferences_layout,
        )
        self.add_checkbox_row(
            "Issue Rules",
            [
                (
                    "Warnings Are Issues",
                    "warnings_are_issues",
                    "Count warnings as issues for Fail On Issues and Log Issues Only.\n"
                    "When off, only errors count as issues.",
                    True,
                ),
                (
                    "Fail On Script Error",
                    "fail_on_script_error",
                    "Fail the task when the validation script raises an exception or cannot be read,\n"
                    "even when Fail On Issues is off. The error is still written to the log.",
                    True,
                ),
            ],
            tooltip="How reported results are interpreted.",
            parent_layout=preferences_layout,
        )
        self.add_external_file_controls()
        self.add_inline_script_controls()
        self.add_actions_row(
            [
                (
                    "Run On Current Scene",
                    "Run the validation script against the scene currently open in Maya and show the results.\n"
                    "Nothing is loaded, saved, or logged.",
                    self.run_validation_on_current_scene,
                    ui_res_lib.Icon.ui_play,
                ),
                (
                    "Run Validation Task",
                    "Run only this Validate Python task against its configured source files.",
                    self.run_this_task_now,
                    ui_res_lib.Icon.batch_task_validate_python,
                ),
            ]
        )
        self.add_segmentation_section(
            main_label="Run Once After All Jobs",
            main_key="run_once_after_multi_instance",
            main_tooltip=RUN_ONCE_AFTER_TOOLTIP.format("validation"),
        )
        self.refresh_mode_visibility()
        self.refresh_scene_option_state()
        self.content_layout.addStretch()

    def add_mode_row(self, parent_layout=None):
        """Adds the Inline / External File script mode radio buttons.

        Each radio button lives in its own grid cell (a different parent widget),
        so an explicit exclusive button group keeps them mutually exclusive.

        Args:
            parent_layout (QLayout, optional): Layout receiving the row.
        """
        tooltip = "Run inline code stored in the project, or a .py file (useful for scripts shared between projects)."
        layout = self.add_labeled_layout("Script Mode", tooltip=tooltip, parent_layout=parent_layout)
        self.mode_button_group = ui_qt.QtWidgets.QButtonGroup(self)
        self.mode_button_group.setExclusive(True)
        for mode in task_validation_python.SCRIPT_MODE_VALUES:
            radio_button = ui_qt.QtWidgets.QRadioButton(mode)
            radio_button.setMinimumHeight(radio_button.sizeHint().height() + 2)
            radio_button.setToolTip(tooltip)
            self.mode_button_group.addButton(radio_button)
            radio_button.setChecked(mode == self.task.get_script_mode())
            radio_button.toggled.connect(partial(self.on_mode_toggled, mode=mode))
            cell_layout = self.add_row_cell(layout)
            cell_layout.addWidget(radio_button)
            cell_layout.addStretch()
            self.mode_buttons[mode] = radio_button
        self.fill_row_cells(layout)

    def on_mode_toggled(self, is_checked, mode):
        """Stores the selected script mode.

        Args:
            is_checked (bool): Whether the radio button is now checked.
            mode (str): Mode represented by the radio button.
        """
        if not is_checked:
            return
        self.set_task_setting(mode, key="script_mode")
        self.refresh_mode_visibility()

    def add_context_row(self, parent_layout=None):
        """Adds the script context exposure options.

        Args:
            parent_layout (QLayout, optional): Layout receiving the row.
        """
        self.add_checkbox_row(
            "Context",
            [
                (
                    "Pass Task Args",
                    "pass_standard_arguments",
                    "Expose input, output, project, task, and related values as arguments and args.",
                    True,
                ),
                (
                    "Pass Env",
                    "pass_environment_arguments",
                    "Expose project environment variables as environment_variables and env.",
                    True,
                ),
            ],
            tooltip="Values exposed to the validation script.",
            parent_layout=parent_layout,
        )

    def add_scene_row(self, parent_layout=None):
        """Adds scene loading options on one row.

        Args:
            parent_layout (QLayout, optional): Layout receiving the row.
        """
        load_tooltip = (
            "Open or import each incoming file in Maya before running the script.\n"
            "Turn off to validate files without loading them (for example JSON, FBX size, or naming checks)."
        )
        layout = self.add_labeled_layout("Scene Load", tooltip=load_tooltip, parent_layout=parent_layout)
        load_checkbox = self.add_option_checkbox(layout, "Load Scene", "load_scene", load_tooltip, True)
        load_checkbox.stateChanged.connect(lambda *args: self.refresh_scene_option_state())
        mode_tooltip = "Open source Maya scene files directly, or import the source into a new scene."
        mode_combo = self.add_row_combo_cell(
            layout,
            self.task.settings.get("source_load_mode") or "Open",
            ["Open", "Import"],
            "source_load_mode",
            tooltip=mode_tooltip,
            span=ROW_COLUMNS - 2,
        )
        plugins_checkbox = self.add_option_checkbox(
            layout,
            "Load Plugins",
            "load_relevant_plugins",
            "Load known file-format plugins before opening or importing.",
            True,
        )
        self.scene_option_widgets = [mode_combo, plugins_checkbox]

    def refresh_scene_option_state(self):
        """Enables scene load options only while Load Scene is on."""
        is_enabled = bool(self.task.settings.get("load_scene", True))
        for widget in self.scene_option_widgets:
            widget.setEnabled(is_enabled)

    def add_external_file_controls(self):
        """Adds the external script path field."""
        self.external_mode_widget = ui_qt.QtWidgets.QWidget()
        external_layout = ui_qt.QtWidgets.QVBoxLayout(self.external_mode_widget)
        external_layout.setContentsMargins(0, 0, 0, 0)
        external_layout.setSpacing(0)
        self.add_path_template_field(
            "Script Path",
            self.task.settings.get("script_path"),
            partial(self.set_task_setting, key="script_path"),
            placeholder=task_validation_python.DEFAULT_EXTERNAL_SCRIPT_PATH,
            tooltip=(
                "Python validation script (.py) executed for every incoming file.\n"
                "Path templates such as {project-dir} are supported."
            ),
            file_filter="Python Files (*.py);;All Files (*);;",
            parent_layout=external_layout,
        )
        self.content_layout.addWidget(self.external_mode_widget)

    def add_inline_script_controls(self):
        """Adds the inline validation script editor."""
        self.inline_mode_widget = ui_qt.QtWidgets.QWidget()
        self.inline_mode_widget.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        inline_layout = ui_qt.QtWidgets.QVBoxLayout(self.inline_mode_widget)
        inline_layout.setContentsMargins(0, 0, 0, 0)
        self.add_widget_separator_line(
            label_text="Validation Script",
            parent_layout=inline_layout,
            tooltip="Inline Python validation code executed for every incoming file.",
        )
        self.script_editor = InlinePythonEditorWidget(
            parent=self.inline_mode_widget,
            owner=self,
            text=self.task.settings.get("script_text") or "",
            placeholder=(
                "Report results with validation.error(...), validation.warning(...), validation.check(...),\n"
                "or return True / False / a list of messages from run(context).\n"
                "Use Examples to load a starting point."
            ),
            tooltip=(
                "Inline Python validation code.\n"
                "Globals: validation, cmds, context, arguments/args, environment_variables/env,\n"
                "project, task, work_item, output_path/log_dir, scene_loaded, and preview."
            ),
            text_changed_callback=partial(self.set_task_setting, key="script_text"),
            font_size=self.task.settings.get("script_font_size") or 14,
            font_size_changed_callback=partial(self.set_task_setting, key="script_font_size"),
            sample_scripts_directory=self.task.sample_scripts_directory,
            run_code_callback=self.run_validation_on_current_scene,
            run_code_tooltip="Run this validation script against the current Maya scene and show the results.",
        )
        self.script_editor.setMinimumHeight(SCRIPT_EDITOR_MINIMUM_HEIGHT)
        self.script_editor.setFixedHeight(SCRIPT_EDITOR_DEFAULT_HEIGHT)
        inline_layout.addWidget(self.script_editor)
        self.script_editor_height_handle = TableHeightHandle(
            table=self.script_editor,
            task=self.task,
            state_key="script_editor_height",
            parent=self.inline_mode_widget,
        )
        self.script_editor_height_handle.setToolTip(
            "Drag to adjust the script editor height. The height is saved with the task."
        )
        inline_layout.addWidget(self.script_editor_height_handle)
        inline_layout.addSpacing(6)
        self.content_layout.addWidget(self.inline_mode_widget)

    def refresh_mode_visibility(self):
        """Shows the controls for the active script mode."""
        is_external = self.task.is_external_file_mode()
        if self.external_mode_widget:
            self.external_mode_widget.setVisible(is_external)
        if self.inline_mode_widget:
            self.inline_mode_widget.setVisible(not is_external)

    def run_validation_on_current_scene(self):
        """Runs the validation script against the current Maya scene and shows the results."""
        settings_result = self.task.validate(self.project)
        if settings_result.errors:
            self.emit_status_message(settings_result.errors[0], status="warning")
            return
        try:
            reporter = self.task.run_on_current_scene(self.project)
        except Exception as exception:
            traceback.print_exc()
            self.emit_status_message(f"Unable to run Python validation: {exception}", status="warning")
            return
        self.task.print_report_summary("current scene", reporter)
        report = reporter.to_dict(warnings_are_issues=self.task.warnings_are_issues())
        self.show_results_window("Validate Python Results", build_report_lines(self.task, report))
        status = "warning" if reporter.script_error or report.get("has_issues") else "info"
        self.emit_status_message(f"Validate Python [{report.get('status')}]: {report.get('summary')}", status=status)


def build_report_lines(task, report):
    """Builds readable result lines for the Validate Python results window.

    Args:
        task (TaskValidationPythonScript): Task that produced the report.
        report (dict): Serialized ValidationReporter data.

    Returns:
        list: Output lines.
    """
    scene_path = task_validation_python.get_current_scene_path() or "<untitled scene>"
    lines = [
        f"Task: {task.display_name}",
        f"Scene: {scene_path}",
        f"Status: {str(report.get('status')).upper()}",
        f"Summary: {report.get('summary')}",
        f"Has Issues: {'Yes' if report.get('has_issues') else 'No'}",
        "",
    ]
    issues = report.get("issues") or []
    if not issues:
        lines.append("No messages reported.")
    for issue in issues:
        node = f" ({issue.get('node')})" if issue.get("node") else ""
        lines.append(f"[{issue.get('severity')}] {issue.get('message')}{node}")
        if issue.get("traceback"):
            lines.append(str(issue.get("traceback")).rstrip())
    lines.extend(["", "Log Entry Preview:", json.dumps(report, indent=4, sort_keys=True)])
    return lines
