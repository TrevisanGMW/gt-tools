"""
Batch Processor Common Task Attribute Widget
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_tasks as tasks
from gt.tools.batch_processor.widgets import attr_widget_base
import gt.ui.input_window_text as ui_input_window_text
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_utils as ui_qt_utils
import gt.ui.qt_import as ui_qt
from functools import partial
import ast
import json


class AttrWidgetTask(attr_widget_base.AttrWidgetBase):
    """Base widget for task-level settings."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes a task attribute widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (BatchTask, optional): Task model.
            project (BatchProcessorModel, optional): Project model.
            refresh_parent_func (callable, optional): Function used to refresh parent UI.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(parent=parent, project=project, refresh_parent_func=refresh_parent_func, *args, **kwargs)
        self.task = task
        self.task_name_field = None
        self.source_path_widgets = None
        self.target_path_widgets = None
        self.incoming_files_button = None
        self.modify_targets_button = None
        self.modify_checkbox = None
        self.passthrough_checkbox = None
        self.overwrite_checkbox = None
        self.scene_load_mode_combo = None
        self.output_extension_combo = None
        self._updating_output_mode = False
        self.task_io_section = None
        self.add_widget_task_header()

    def add_widget_task_header(self):
        """Adds the task header with active state, icon, name, raw data, and delete button."""
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 5)
        layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)

        active_checkbox = ui_qt.QtWidgets.QCheckBox()
        active_checkbox.setChecked(self.task.enabled)
        active_checkbox.setToolTip("Enable or disable this task during processing.")
        active_checkbox.stateChanged.connect(lambda *args: self.set_task_enabled(active_checkbox.isChecked()))
        layout.addWidget(active_checkbox)

        icon_path = attr_widget_base.get_icon_path(self.task.icon)
        icon_label = ui_qt.QtWidgets.QLabel()
        icon_label.setPixmap(ui_qt.QtGui.QIcon(icon_path).pixmap(32, 32))
        icon_label.setToolTip(self.task.default_display_name)
        layout.addWidget(icon_label)

        task_type_label = ui_qt.QtWidgets.QLabel(self.task.default_display_name)
        attr_widget_base.configure_label_for_scaled_displays(task_type_label, word_wrap=True)
        task_type_label.setToolTip("Task type: {0}".format(self.task.task_type))
        layout.addWidget(task_type_label)

        self.task_name_field = ui_qt_utils.ConfirmableQLineEdit()
        self.task_name_field.setMinimumHeight(35)
        self.task_name_field.setMinimumWidth(1)
        self.task_name_field.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        self.task_name_field.setText(self.task.display_name)
        self.task_name_field.setToolTip("User-facing task name.")
        self.task_name_field.editingFinished.connect(self.set_task_name)
        layout.addWidget(self.task_name_field)

        edit_button = ui_qt.QtWidgets.QPushButton()
        edit_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_dict))
        edit_button.setToolTip("Edit raw task JSON data.")
        edit_button.clicked.connect(self.open_raw_data_editor)
        layout.addWidget(edit_button)

        delete_button = ui_qt.QtWidgets.QPushButton()
        delete_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete))
        delete_button.setToolTip("Remove this task from the project.")
        delete_button.clicked.connect(self.delete_task)
        layout.addWidget(delete_button)
        self.content_layout.addLayout(layout)

    def add_task_path_field(self, tooltip=None):
        """Adds a standard task path-template field.

        Args:
            tooltip (str, optional): Tooltip for the path field.
        """
        self.add_target_path_field(tooltip=tooltip)

    def add_common_task_settings(
        self,
        include_source=True,
        include_target=True,
        include_overwrite=True,
        scene_io_settings=None,
        collapsible=True,
        passthrough_label=None,
    ):
        """Adds settings shared by most processing tasks.

        Args:
            include_source (bool, optional): Whether to include source controls.
            include_target (bool, optional): Whether to include target controls.
            include_overwrite (bool, optional): Whether to include overwrite controls.
            scene_io_settings (dict, optional): Scene loading and output options to add to the I/O section.
            collapsible (bool, optional): Whether the section should be collapsible.
            passthrough_label (str, optional): Label for a task-specific no-write output mode.
        """
        self.task.settings.setdefault("task_io_collapsed", False)
        if collapsible:
            self.task_io_section = self.add_collapsible_section(
                "Task Input/Output",
                collapsed=self.task.settings.get("task_io_collapsed", False),
                state_setter=self.set_task_io_collapsed,
                tooltip="Common task input/output controls.",
            )
            section_layout = self.task_io_section.get("content_layout")
        else:
            self.add_widget_separator_line(
                label_text="Task Input/Output",
                tooltip="Common task input/output controls.",
            )
            section_layout = self.content_layout
        options_layout = self.add_labeled_layout(
            "I/O Mode",
            label_width=100,
            tooltip="Common task input/output.",
            parent_layout=section_layout,
        )
        if include_source:
            incoming_checkbox = ui_qt.QtWidgets.QCheckBox("Incoming")
            incoming_checkbox.setMinimumHeight(incoming_checkbox.sizeHint().height() + 2)
            incoming_checkbox.setChecked(self.task.uses_incoming_files())
            incoming_checkbox.setToolTip("Use all incoming files collected by earlier input tasks.")
            incoming_button = ui_qt.QtWidgets.QPushButton()
            incoming_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_env_var))
            incoming_button.setToolTip("Show incoming files that would be used by this task.")
            incoming_button.clicked.connect(self.show_incoming_files)
            incoming_checkbox.stateChanged.connect(lambda *args: self.set_source_mode_from_checkbox(incoming_checkbox))
            self.add_option_group(options_layout, incoming_checkbox, incoming_button)
            self.incoming_files_button = incoming_button
        if include_source:
            self.add_source_path_controls(parent_layout=section_layout)
        if include_target:
            modify_checkbox = ui_qt.QtWidgets.QCheckBox("Modify")
            modify_checkbox.setMinimumHeight(modify_checkbox.sizeHint().height() + 2)
            modify_checkbox.setChecked(self.task.modifies_in_place())
            modify_checkbox.setToolTip("Modify received files in place instead of writing to the target path.")
            modify_button = ui_qt.QtWidgets.QPushButton()
            modify_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_env_var))
            modify_button.setToolTip("Show files that would be modified by this task.")
            modify_button.clicked.connect(self.show_modify_target_files)
            modify_checkbox.stateChanged.connect(lambda *args: self.set_output_mode_from_checkbox(modify_checkbox))
            self.add_option_group(options_layout, modify_checkbox, modify_button)
            self.modify_targets_button = modify_button
            self.modify_checkbox = modify_checkbox
        if include_target and passthrough_label:
            passthrough_checkbox = ui_qt.QtWidgets.QCheckBox(passthrough_label)
            passthrough_checkbox.setMinimumHeight(passthrough_checkbox.sizeHint().height() + 2)
            passthrough_checkbox.setChecked(self.task.passes_through())
            passthrough_checkbox.setToolTip(
                "Process incoming files without creating, replacing, or modifying an output file."
            )
            passthrough_checkbox.stateChanged.connect(
                lambda *args: self.set_passthrough_mode_from_checkbox(passthrough_checkbox)
            )
            self.add_option_group(options_layout, passthrough_checkbox)
            self.passthrough_checkbox = passthrough_checkbox
        if include_target:
            self.add_target_path_controls(parent_layout=section_layout)
        if include_overwrite:
            overwrite_checkbox = ui_qt.QtWidgets.QCheckBox("Overwrite")
            overwrite_checkbox.setMinimumHeight(overwrite_checkbox.sizeHint().height() + 2)
            overwrite_checkbox.setChecked(bool(self.task.settings.get("overwrite", False)))
            overwrite_checkbox.setToolTip("Allow this task to overwrite existing files at its target path.")
            overwrite_checkbox.stateChanged.connect(lambda *args: self.set_overwrite_from_checkbox(overwrite_checkbox))
            self.add_option_group(options_layout, overwrite_checkbox)
            self.overwrite_checkbox = overwrite_checkbox
        self.add_task_index_checkbox(options_layout)
        if scene_io_settings:
            self.add_scene_io_settings(parent_layout=section_layout, **scene_io_settings)
        self.refresh_source_path_enabled_state()
        self.refresh_target_path_enabled_state()

    def set_task_io_collapsed(self, is_collapsed):
        """Stores the Task Input/Output collapsed state on the task.

        Args:
            is_collapsed (bool): Whether the I/O section is collapsed.
        """
        self.task.settings["task_io_collapsed"] = bool(is_collapsed)

    @staticmethod
    def add_option_group(parent_layout, checkbox, button=None):
        """Adds a fixed option group to a parent layout.

        Args:
            parent_layout (QHBoxLayout): Parent row layout.
            checkbox (QCheckBox): Option checkbox.
            button (QPushButton, optional): Optional button shown beside the checkbox.
        """
        group_widget = ui_qt.QtWidgets.QWidget()
        group_widget.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        group_layout = ui_qt.QtWidgets.QHBoxLayout(group_widget)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(5)
        group_layout.addWidget(checkbox)
        if button:
            group_layout.addWidget(button)
        group_layout.addStretch()
        parent_layout.addWidget(group_widget)

    def add_source_path_field(self, tooltip=None):
        """Adds a standard source path-template field.

        Args:
            tooltip (str, optional): Tooltip for the path field.
        """
        tooltip = tooltip or "Source path used by this task. Defaults to the previous task path."
        self.add_path_template_field(
            "Source Path",
            self.task.settings.get("source_path") or self.task.default_source_path_template,
            partial(self.set_task_setting, key="source_path"),
            placeholder=self.task.default_source_path_template,
            tooltip=tooltip,
            dir_only=True,
        )

    def add_source_path_controls(self, tooltip=None, parent_layout=None):
        """Adds source mode controls with source path widgets.

        Args:
            tooltip (str, optional): Tooltip for the path field.
            parent_layout (QLayout, optional): Layout that receives the controls.
        """
        tooltip = tooltip or "Use incoming work items, or discover files from this source path."
        layout = self.add_labeled_layout(
            "Source Path",
            label_width=100,
            tooltip=tooltip,
            parent_layout=parent_layout,
        )
        field = self.create_text_field(
            text=self.task.settings.get("source_path") or self.task.default_source_path_template,
            placeholder=self.task.default_source_path_template,
            tooltip=tooltip,
        )
        info_button = ui_qt.QtWidgets.QPushButton()
        info_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_env_var))
        info_button.setToolTip("Get more information about the current path.")
        open_button = ui_qt.QtWidgets.QPushButton()
        open_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        open_button.setToolTip("Open the resolved source directory.")
        browse_button = ui_qt.QtWidgets.QPushButton()
        browse_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        browse_button.setToolTip("Browse for a concrete source path.")
        layout.addWidget(field)
        layout.addWidget(info_button)
        layout.addWidget(open_button)
        layout.addWidget(browse_button)
        field.textChanged.connect(
            partial(
                self.set_path_field_value,
                field=field,
                setter=partial(self.set_task_setting, key="source_path"),
            )
        )
        info_button.clicked.connect(partial(self.open_env_var_feedback_dialog, field=field))
        open_button.clicked.connect(partial(self.open_resolved_path_directory, field=field))
        browse_button.clicked.connect(partial(self.open_path_dialog, field=field, dir_only=True))
        self.source_path_widgets = {
            "field": field,
            "info_button": info_button,
            "open_button": open_button,
            "browse_button": browse_button,
        }
        self.refresh_source_path_enabled_state()

    def add_target_path_field(self, tooltip=None):
        """Adds a standard target path-template field.

        Args:
            tooltip (str, optional): Tooltip for the path field.
        """
        tooltip = tooltip or "Target path used by this task. Supports variables such as {project-dir}."
        self.add_path_template_field(
            "Target Path",
            self.task.get_target_path_template(),
            partial(self.set_task_setting, key="target_path"),
            placeholder=self.task.default_target_path_template,
            tooltip=tooltip,
            dir_only=True,
        )

    def add_target_path_controls(self, tooltip=None, parent_layout=None):
        """Adds target mode controls with target path widgets.

        Args:
            tooltip (str, optional): Tooltip for the path field.
            parent_layout (QLayout, optional): Layout that receives the controls.
        """
        tooltip = tooltip or "Write new files to this target path, or modify received files in place."
        layout = self.add_labeled_layout(
            "Target Path",
            label_width=100,
            tooltip=tooltip,
            parent_layout=parent_layout,
        )
        field = self.create_text_field(
            text=self.task.get_target_path_template(),
            placeholder=self.task.default_target_path_template,
            tooltip=tooltip,
        )
        info_button = ui_qt.QtWidgets.QPushButton()
        info_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_env_var))
        info_button.setToolTip("Get more information about the current path.")
        open_button = ui_qt.QtWidgets.QPushButton()
        open_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        open_button.setToolTip("Open the resolved target directory.")
        browse_button = ui_qt.QtWidgets.QPushButton()
        browse_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        browse_button.setToolTip("Browse for a concrete target path.")
        layout.addWidget(field)
        layout.addWidget(info_button)
        layout.addWidget(open_button)
        layout.addWidget(browse_button)
        field.textChanged.connect(
            partial(
                self.set_path_field_value,
                field=field,
                setter=partial(self.set_task_setting, key="target_path"),
            )
        )
        info_button.clicked.connect(partial(self.open_env_var_feedback_dialog, field=field))
        open_button.clicked.connect(partial(self.open_resolved_path_directory, field=field))
        browse_button.clicked.connect(partial(self.open_path_dialog, field=field, dir_only=True))
        self.target_path_widgets = {
            "field": field,
            "info_button": info_button,
            "open_button": open_button,
            "browse_button": browse_button,
        }
        self.refresh_target_path_enabled_state()

    def add_scene_io_settings(
        self,
        parent_layout,
        load_mode_key="source_load_mode",
        load_mode_label="Source Load Mode",
        load_mode_values=None,
        output_extension_key="output_extension",
        output_extension_label="Output Extension",
        output_extension_value=None,
        output_extension_values=None,
        output_extension_setter=None,
        load_plugins_key="load_relevant_plugins",
        load_plugins_label="Load Plugins",
        include_load_plugins=True,
    ):
        """Adds scene loading and output settings in one row.

        Args:
            parent_layout (QLayout): Layout that receives the row.
            load_mode_key (str, optional): Task setting key for source load mode.
            load_mode_label (str, optional): Label for the load mode combo.
            load_mode_values (list, optional): Combo values for source loading.
            output_extension_key (str, optional): Task setting key for output extension.
            output_extension_label (str, optional): Label for output extension.
            output_extension_value (str, optional): Visible output extension value.
            output_extension_values (list, optional): Combo values for output extension.
            output_extension_setter (callable, optional): Custom setter for output extension changes.
            load_plugins_key (str, optional): Task setting key for plugin loading.
            load_plugins_label (str, optional): Label for the plugin loading checkbox.
            include_load_plugins (bool, optional): Whether to include plugin loading controls.
        """
        load_mode_values = load_mode_values or ["Open", "Import"]
        output_extension_values = output_extension_values or [".ma", ".mb"]
        layout = self.add_labeled_layout(
            "Scene Output",
            label_width=100,
            tooltip="Scene loading and output settings.",
            parent_layout=parent_layout,
        )
        load_mode_layout = self.add_row_option_group(
            parent_layout=layout,
            label_text=load_mode_label,
            tooltip="Open source Maya scene files directly, or import the source into a new scene.",
        )
        load_mode_combo = self.create_row_combo_box(
            value=self.task.settings.get(load_mode_key),
            values=load_mode_values,
            tooltip="Open source Maya scene files directly, or import the source into a new scene.",
        )
        load_mode_combo.currentTextChanged.connect(partial(self.set_task_setting, key=load_mode_key))
        load_mode_layout.addWidget(load_mode_combo)
        self.scene_load_mode_combo = load_mode_combo

        output_extension_layout = self.add_row_option_group(
            parent_layout=layout,
            label_text=output_extension_label,
            tooltip="Output file extension used for the cooked result.",
        )
        output_extension_combo = self.create_row_combo_box(
            value=output_extension_value or self.task.settings.get(output_extension_key),
            values=output_extension_values,
            tooltip="Output file extension used for the cooked result.",
        )
        if output_extension_setter:
            output_extension_combo.currentTextChanged.connect(output_extension_setter)
        else:
            output_extension_combo.currentTextChanged.connect(
                partial(self.set_task_setting, key=output_extension_key)
            )
        output_extension_layout.addWidget(output_extension_combo)
        self.output_extension_combo = output_extension_combo

        if include_load_plugins:
            load_plugins_layout = self.add_row_option_group(
                parent_layout=layout,
                label_text=load_plugins_label,
                tooltip="Load known file-format plugins before opening or importing.",
            )
            load_plugins_checkbox = ui_qt.QtWidgets.QCheckBox()
            load_plugins_checkbox.setMinimumHeight(load_plugins_checkbox.sizeHint().height() + 2)
            load_plugins_checkbox.setChecked(bool(self.task.settings.get(load_plugins_key)))
            load_plugins_checkbox.setToolTip("Load known file-format plugins before opening or importing.")
            load_plugins_checkbox.stateChanged.connect(
                lambda *args: self.set_task_setting(load_plugins_checkbox.isChecked(), key=load_plugins_key)
            )
            load_plugins_layout.addWidget(load_plugins_checkbox)
            load_plugins_layout.addStretch()

    @staticmethod
    def add_row_option_group(parent_layout, label_text, tooltip=None):
        """Adds an evenly distributed compact option group to a row.

        Args:
            parent_layout (QLayout): Parent row layout.
            label_text (str): Label text.
            tooltip (str, optional): Tooltip text.

        Returns:
            QHBoxLayout: Layout inside the created option group widget.
        """
        group_widget = ui_qt.QtWidgets.QWidget()
        group_widget.setMinimumWidth(1)
        group_widget.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        group_layout = ui_qt.QtWidgets.QHBoxLayout(group_widget)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(5)
        label = ui_qt.QtWidgets.QLabel("{0}:".format(label_text))
        attr_widget_base.configure_label_for_scaled_displays(label)
        label.setToolTip(tooltip or label_text)
        group_layout.addWidget(label)
        parent_layout.addWidget(group_widget, 1)
        return group_layout

    @staticmethod
    def add_row_label(layout, label_text, tooltip=None):
        """Adds a compact label to an existing row.

        Args:
            layout (QLayout): Layout that receives the label.
            label_text (str): Label text.
            tooltip (str, optional): Tooltip text.

        Returns:
            QLabel: Created label.
        """
        label = ui_qt.QtWidgets.QLabel(label_text)
        attr_widget_base.configure_label_for_scaled_displays(label)
        label.setToolTip(tooltip or label_text)
        layout.addWidget(label)
        return label

    @staticmethod
    def create_row_combo_box(value, values, tooltip=None):
        """Creates a compact combo box for a shared row.

        Args:
            value (str): Current selected value.
            values (list): Available text values.
            tooltip (str, optional): Tooltip text.

        Returns:
            QComboBox: Created combo box.
        """
        combo_box = ui_qt.QtWidgets.QComboBox()
        combo_box.setMinimumHeight(35)
        combo_box.setMinimumWidth(90)
        combo_box.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        combo_box.setToolTip(tooltip or "")
        for item in values:
            combo_box.addItem(str(item))
        if value and combo_box.findText(str(value)) == -1:
            combo_box.addItem(str(value))
        index = combo_box.findText(str(value or ""))
        if index >= 0:
            combo_box.setCurrentIndex(index)
        return combo_box

    def set_source_mode_from_checkbox(self, checkbox):
        """Sets the source mode from a checkbox.

        Args:
            checkbox (QCheckBox): Source mode checkbox.
        """
        previous_mode = self.task.settings.get("source_mode")
        if checkbox.isChecked():
            self.task.settings["source_mode"] = tasks.SOURCE_MODE_INCOMING
        else:
            self.task.settings["source_mode"] = tasks.SOURCE_MODE_PATH
        if previous_mode != self.task.settings.get("source_mode"):
            mode_name = "incoming files" if self.task.uses_incoming_files() else "source path"
            self.emit_status_message(
                'Task "{0}" input mode changed to {1}. Validate before running.'.format(
                    self.task.display_name,
                    mode_name,
                ),
                status="warning",
            )
        self.refresh_source_path_enabled_state()

    def set_output_mode_from_checkbox(self, checkbox):
        """Sets the output mode from a checkbox.

        Args:
            checkbox (QCheckBox): Output mode checkbox.
        """
        if self._updating_output_mode:
            return
        previous_mode = self.task.settings.get("output_mode")
        if checkbox.isChecked():
            if getattr(self, "passthrough_checkbox", None):
                self._updating_output_mode = True
                try:
                    self.passthrough_checkbox.setChecked(False)
                finally:
                    self._updating_output_mode = False
            self.task.settings["output_mode"] = tasks.OUTPUT_MODE_MODIFY
        elif getattr(self, "passthrough_checkbox", None) and self.passthrough_checkbox.isChecked():
            self.task.settings["output_mode"] = tasks.OUTPUT_MODE_PASSTHROUGH
        else:
            self.task.settings["output_mode"] = tasks.OUTPUT_MODE_TARGET
        if previous_mode != self.task.settings.get("output_mode"):
            if self.task.modifies_in_place():
                message = 'Task "{0}" output mode changed to Modify. Validate paths before running.'
                status = "warning"
            else:
                message = 'Task "{0}" output mode changed to Target Path.'
                status = "info"
            self.emit_status_message(message.format(self.task.display_name), status=status)
        self.refresh_target_path_enabled_state()

    def set_passthrough_mode_from_checkbox(self, checkbox):
        """Sets the task-specific no-write output mode from a checkbox.

        Args:
            checkbox (QCheckBox): Pass-through mode checkbox.
        """
        if self._updating_output_mode:
            return
        previous_mode = self.task.settings.get("output_mode")
        if checkbox.isChecked():
            if getattr(self, "modify_checkbox", None):
                self._updating_output_mode = True
                try:
                    self.modify_checkbox.setChecked(False)
                finally:
                    self._updating_output_mode = False
            self.task.settings["output_mode"] = tasks.OUTPUT_MODE_PASSTHROUGH
        elif getattr(self, "modify_checkbox", None) and self.modify_checkbox.isChecked():
            self.task.settings["output_mode"] = tasks.OUTPUT_MODE_MODIFY
        else:
            self.task.settings["output_mode"] = tasks.OUTPUT_MODE_TARGET
        if previous_mode != self.task.settings.get("output_mode"):
            if self.task.passes_through():
                message = f'Task "{self.task.display_name}" output mode changed to {checkbox.text()}.'
            else:
                message = f'Task "{self.task.display_name}" output mode changed to Target Path.'
            self.emit_status_message(message, status="info")
        self.refresh_target_path_enabled_state()

    def set_overwrite_from_checkbox(self, checkbox):
        """Sets overwrite behavior from a checkbox and reports the change.

        Args:
            checkbox (QCheckBox): Overwrite checkbox.
        """
        self.set_task_setting(checkbox.isChecked(), key="overwrite")

    def add_task_index_checkbox(self, layout):
        """Adds the task-index participation checkbox to a row.

        Args:
            layout (QLayout): Layout that receives the checkbox group.

        Returns:
            QCheckBox: Created checkbox.
        """
        index_checkbox = ui_qt.QtWidgets.QCheckBox("Index")
        index_checkbox.setMinimumHeight(index_checkbox.sizeHint().height() + 2)
        index_checkbox.setChecked(bool(self.task.includes_task_index()))
        index_checkbox.setToolTip("Include this task when resolving task index variables such as {task-idx}.")
        index_checkbox.stateChanged.connect(lambda *args: self.set_task_include_in_index(index_checkbox.isChecked()))
        self.add_option_group(layout, index_checkbox)
        return index_checkbox

    def set_task_include_in_index(self, value):
        """Sets whether this task contributes to task index variables.

        Args:
            value (bool): Whether the task should be counted.
        """
        self.set_task_setting(bool(value), key="include_in_task_index")

    def refresh_source_path_enabled_state(self):
        """Refreshes source path widgets based on source mode."""
        if not self.source_path_widgets:
            return
        is_source_path_enabled = not self.task.uses_incoming_files()
        for key in ["field", "info_button", "open_button", "browse_button"]:
            self.source_path_widgets[key].setEnabled(is_source_path_enabled)
        if self.incoming_files_button:
            self.incoming_files_button.setEnabled(self.task.uses_incoming_files())

    def refresh_target_path_enabled_state(self):
        """Refreshes target path widgets based on output mode."""
        if not self.target_path_widgets:
            return
        is_target_path_enabled = self.task.writes_to_target_path()
        for key in ["field", "info_button", "open_button", "browse_button"]:
            self.target_path_widgets[key].setEnabled(is_target_path_enabled)
        if self.modify_targets_button:
            self.modify_targets_button.setEnabled(self.task.modifies_in_place())
        if getattr(self, "overwrite_checkbox", None):
            self.overwrite_checkbox.setEnabled(not self.task.passes_through())
        if self.scene_load_mode_combo:
            self.scene_load_mode_combo.setEnabled(not self.task.passes_through())
        if self.output_extension_combo:
            self.output_extension_combo.setEnabled(not self.task.passes_through())

    def show_incoming_files(self):
        """Shows incoming files discovered by the input tasks in this task's segment."""
        file_paths = self.project.discover_incoming_files_for_task(self.task) if self.project else []
        self.show_path_list(title="Incoming Files", file_paths=file_paths)
        self.emit_status_message("Incoming files preview found {0} file(s).".format(len(file_paths)))

    def show_modify_target_files(self):
        """Shows files that would be modified when Modify is enabled."""
        file_paths = self.get_source_preview_paths()
        self.show_path_list(title="Files To Modify", file_paths=file_paths)
        self.emit_status_message("Modify preview found {0} file(s).".format(len(file_paths)))

    def get_source_preview_paths(self):
        """Gets source paths represented by this task's current source settings.

        Returns:
            list: File paths.
        """
        if not self.project:
            return []
        if self.task.uses_incoming_files():
            return self.project.discover_incoming_files_for_task(self.task)
        task_index = self.project.get_task_environment_index(self.task)
        return self.task.discover_source_files(project=self.project, task_index=task_index)

    def show_path_list(self, title, file_paths, header_lines=None):
        """Shows a list of paths in a text output window.

        Args:
            title (str): Window title.
            file_paths (list): Paths to display.
            header_lines (list, optional): Lines to show before the path count.
        """
        super(AttrWidgetTask, self).show_path_list(
            title=title,
            file_paths=file_paths,
            header_lines=header_lines,
        )

    def add_run_selected_task_button(self, label_text="Run Selected Task", tooltip=None):
        """Adds a button that runs only this task through the batch controller.

        Args:
            label_text (str, optional): Button text.
            tooltip (str, optional): Button tooltip.
        """
        tooltip = tooltip or "Run only this task using the current batch project settings."
        layout = self.add_labeled_layout("Actions", tooltip=tooltip)
        button = ui_qt.QtWidgets.QPushButton(label_text)
        button.setMinimumHeight(35)
        button.setToolTip(tooltip)
        button.clicked.connect(self.run_this_task_now)
        layout.addWidget(button)
        layout.addStretch()

    def run_this_task_now(self):
        """Runs this task through the owning batch controller."""
        if not self.task:
            self.emit_status_message("Unable to run task: no task is active.", status="warning")
            return
        if not self.task.enabled:
            self.emit_status_message(
                'Task "{0}" is disabled. Enable it before running it.'.format(self.task.display_name),
                status="warning",
            )
            return
        try:
            controller = self.get_batch_controller()
            if not controller or not hasattr(controller, "_run_project"):
                self.emit_status_message("Unable to run task: batch controller was not found.", status="warning")
                return
            self.emit_status_message('Running task "{0}" only.'.format(self.task.display_name))
            controller._run_project(
                run_from_task_id=self.task.id,
                run_to_task_id=self.task.id,
                force_single_instance=bool(getattr(self.task, "is_aggregate_task", False)),
            )
        except Exception as exception:
            self.emit_status_message("Unable to run task: {0}".format(exception), status="warning")

    def set_task_name(self):
        """Updates the task display name from the header field."""
        display_name = self.task_name_field.text() or self.task.default_display_name
        if self.task_name_field.text() != display_name:
            self.task_name_field.setText(display_name)
        if self.task.display_name == display_name:
            return
        self.task.display_name = display_name
        if not self.refresh_task_tree_item():
            self.call_parent_refresh()

    def refresh_task_tree_item(self):
        """Refreshes this task's existing tree item without rebuilding the details widget.

        Returns:
            bool: True when the owning controller updated the tree item.
        """
        controller = self.get_batch_controller()
        if not controller or not hasattr(controller, "refresh_task_tree_item"):
            return False
        return bool(controller.refresh_task_tree_item(self.task.id))

    def set_task_enabled(self, value):
        """Updates the task enabled state.

        Args:
            value (bool): New enabled state.
        """
        enabled = bool(value)
        if self.task.enabled == enabled:
            return
        self.task.enabled = enabled
        state_name = "enabled" if self.task.enabled else "disabled"
        self.emit_status_message('Task "{0}" {1}.'.format(self.task.display_name, state_name))
        if not self.refresh_task_tree_item():
            self.call_parent_refresh()

    def set_task_setting(self, value, key):
        """Sets a task setting.

        Args:
            value (object): Setting value.
            key (str): Setting key.
        """
        previous_value = self.task.settings.get(key)
        self.task.settings[key] = value
        if previous_value != value:
            self.emit_task_setting_change_message(key=key, value=value)

    def emit_task_setting_change_message(self, key, value):
        """Emits a status message for task settings that can significantly change a run.

        Args:
            key (str): Setting key that changed.
            value (object): New setting value.
        """
        if key == "overwrite":
            if value:
                self.emit_status_message(
                    'Task "{0}" overwrite enabled. Existing target files may be replaced.'.format(
                        self.task.display_name
                    ),
                    status="warning",
                )
            else:
                self.emit_status_message(
                    'Task "{0}" overwrite disabled. Existing target files will be skipped.'.format(
                        self.task.display_name
                    )
                )
        elif key == "include_in_task_index":
            if value:
                self.emit_status_message(
                    'Task "{0}" will be included in task index variables.'.format(self.task.display_name)
                )
            else:
                self.emit_status_message(
                    'Task "{0}" will be excluded from task index variables.'.format(self.task.display_name),
                    status="warning",
                )
        elif key in ["source_load_mode", "output_extension", "usd_format", "load_relevant_plugins"]:
            self.emit_status_message(
                'Task "{0}" changed {1} to "{2}". Validate before running.'.format(
                    self.task.display_name,
                    key.replace("_", " "),
                    value,
                ),
                status="warning",
            )

    def set_task_setting_list_from_text(self, text, key):
        """Sets a list task setting from comma or newline separated text.

        Args:
            text (str): Text to parse.
            key (str): Setting key.
        """
        self.task.settings[key] = self.split_list_text(text)

    def open_raw_data_editor(self):
        """Opens an editable raw-data window for the current task."""
        param_win = ui_input_window_text.InputWindowText(
            parent=self,
            message='Editing Raw Data for Task "{0}"'.format(self.task.display_name),
            window_title='Raw data for "{0}"'.format(self.task.display_name),
            image=ui_res_lib.Icon.rigger_dict,
            window_icon=ui_res_lib.Icon.library_parameters,
            image_scale_pct=10,
            is_python_code=True,
        )
        param_win.set_confirm_button_text("Apply")
        formatted_dict = json.dumps(self.task.to_dict(), indent=4, sort_keys=True)
        param_win.set_text_field_text(formatted_dict)
        param_win.confirm_button.clicked.connect(
            partial(self.update_task_from_raw_data, param_win.get_text_field_text)
        )
        param_win.confirm_button.clicked.connect(param_win.close_window)
        param_win.show()

    def update_task_from_raw_data(self, data_getter):
        """Updates the task from raw JSON or Python dictionary text.

        Args:
            data_getter (callable): Function that returns the raw text.
        """
        data = data_getter()
        try:
            try:
                data_as_dict = json.loads(data)
            except Exception:
                data_as_dict = ast.literal_eval(data)
            updated_task = tasks.create_task_from_dict(data_as_dict)
            self.task.display_name = updated_task.display_name
            self.task.enabled = updated_task.enabled
            self.task.settings = updated_task.settings
            self.task.extra_data = updated_task.extra_data
            self.call_parent_refresh()
        except Exception as exception:
            raise Exception('Unable to set task attributes from provided raw data. Issue: "{0}".'.format(exception))

    def delete_task(self):
        """Deletes the task associated with this attribute widget after confirmation."""
        should_confirm = True
        try:
            controller = self.get_batch_controller()
            if controller and hasattr(controller, "get_confirm_delete_task"):
                should_confirm = controller.get_confirm_delete_task()
        except Exception:
            should_confirm = True
        if should_confirm:
            message_box = ui_qt.QtWidgets.QMessageBox(self)
            message_box.setWindowTitle('Delete Task "{0}"?'.format(self.task.display_name))
            message_box.setText('Are you sure you want to delete task "{0}"?'.format(self.task.display_name))
            question_icon = ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete)
            message_box.setIconPixmap(question_icon.pixmap(64, 64))
            message_box.addButton(ui_qt.QtLib.StandardButton.Yes)
            message_box.addButton(ui_qt.QtLib.StandardButton.No)
            result = self.exec_dialog(message_box)
            if result != ui_qt.QtLib.StandardButton.Yes:
                return
        self.project.remove_task(self.task.id)
        self.call_parent_refresh()


def get_task_widget_class(task):
    """Gets the widget class associated with a task.

    Args:
        task (BatchTask): Task to inspect.

    Returns:
        type: Widget class used to edit the task.
    """
    if task.task_type == constants.TaskType.INPUT:
        from gt.tools.batch_processor.widgets.attr_widget_input import AttrWidgetInputTask

        return AttrWidgetInputTask
    if task.task_type == constants.TaskType.MAYA_IMPORT:
        from gt.tools.batch_processor.widgets.attr_widget_maya_import import AttrWidgetMayaImportTask

        return AttrWidgetMayaImportTask
    if task.task_type == constants.TaskType.RENAME:
        from gt.tools.batch_processor.widgets.attr_widget_rename import AttrWidgetRenameTask

        return AttrWidgetRenameTask
    if task.task_type == constants.TaskType.PYTHON_SCRIPT:
        from gt.tools.batch_processor.widgets.attr_widget_python_script import AttrWidgetPythonScriptTask

        return AttrWidgetPythonScriptTask
    if task.task_type == constants.TaskType.MOTIONBUILDER_SCRIPT:
        from gt.tools.batch_processor.widgets.attr_widget_motionbuilder_script import AttrWidgetMotionBuilderScriptTask

        return AttrWidgetMotionBuilderScriptTask
    if task.task_type == constants.TaskType.BLENDER_SCRIPT:
        from gt.tools.batch_processor.widgets.attr_widget_blender_script import AttrWidgetBlenderScriptTask

        return AttrWidgetBlenderScriptTask
    if task.task_type == constants.TaskType.PYTHON_SCRIPTS_FOLDER:
        from gt.tools.batch_processor.widgets.attr_widget_python_script import AttrWidgetPythonScriptsFolderTask

        return AttrWidgetPythonScriptsFolderTask
    if task.task_type == constants.TaskType.MAYA_SAVE:
        from gt.tools.batch_processor.widgets.attr_widget_maya_save import AttrWidgetMayaSaveTask

        return AttrWidgetMayaSaveTask
    if task.task_type == constants.TaskType.USD_EXPORT:
        from gt.tools.batch_processor.widgets.attr_widget_usd_export import AttrWidgetUsdExportTask

        return AttrWidgetUsdExportTask
    if task.task_type == constants.TaskType.RETARGET:
        from gt.tools.batch_processor.widgets.attr_widget_retarget import AttrWidgetRetargetTask

        return AttrWidgetRetargetTask
    if task.task_type == constants.TaskType.HIK_RETARGET:
        from gt.tools.batch_processor.widgets.attr_widget_hik_retarget import AttrWidgetRetargetHumanIK

        return AttrWidgetRetargetHumanIK
    if task.task_type == constants.TaskType.FBX_EXPORT:
        from gt.tools.batch_processor.widgets.attr_widget_new_tasks import AttrWidgetFbxExportTask

        return AttrWidgetFbxExportTask
    if task.task_type == constants.TaskType.AUTO_RIG_BUILD:
        from gt.tools.batch_processor.widgets.attr_widget_new_tasks import AttrWidgetAutoRigBuildTask

        return AttrWidgetAutoRigBuildTask
    if task.task_type == constants.TaskType.CLIP_SPLIT:
        from gt.tools.batch_processor.widgets.attr_widget_new_tasks import AttrWidgetClipSplitTask

        return AttrWidgetClipSplitTask
    if task.task_type == constants.TaskType.CLIP_SNAPSHOT:
        from gt.tools.batch_processor.widgets.attr_widget_new_tasks import AttrWidgetClipSnapshotTask

        return AttrWidgetClipSnapshotTask
    if task.task_type == constants.TaskType.MAP_RENAME:
        from gt.tools.batch_processor.widgets.attr_widget_new_tasks import AttrWidgetMapRenameTask

        return AttrWidgetMapRenameTask
    if task.task_type == constants.TaskType.DELETE_PROJECT_FILES:
        from gt.tools.batch_processor.widgets.attr_widget_new_tasks import AttrWidgetDeleteProjectFilesTask

        return AttrWidgetDeleteProjectFilesTask
    if task.task_type == constants.TaskType.ZIP_COMPRESS:
        from gt.tools.batch_processor.widgets.attr_widget_new_tasks import AttrWidgetZipCompressTask

        return AttrWidgetZipCompressTask
    if task.task_type == constants.TaskType.MAYA_SCENE_VALIDATE:
        from gt.tools.batch_processor.widgets.attr_widget_new_tasks import AttrWidgetMayaSceneValidationTask

        return AttrWidgetMayaSceneValidationTask
    if task.task_type == constants.TaskType.FILE_INTEGRITY_VALIDATE:
        from gt.tools.batch_processor.widgets.attr_widget_new_tasks import AttrWidgetFileIntegrityValidationTask

        return AttrWidgetFileIntegrityValidationTask
    if task.task_type == constants.TaskType.FOLDER_COMPARE_VALIDATE:
        from gt.tools.batch_processor.widgets.attr_widget_new_tasks import AttrWidgetFolderCompareValidationTask

        return AttrWidgetFolderCompareValidationTask
    if task.task_type == constants.TaskType.THUMBNAIL_CAPTURE:
        from gt.tools.batch_processor.widgets.attr_widget_new_tasks import AttrWidgetThumbnailCaptureTask

        return AttrWidgetThumbnailCaptureTask
    if task.task_type == constants.TaskType.PLAYBLAST_CAPTURE:
        from gt.tools.batch_processor.widgets.attr_widget_new_tasks import AttrWidgetPlayblastCaptureTask

        return AttrWidgetPlayblastCaptureTask
    return AttrWidgetTask
