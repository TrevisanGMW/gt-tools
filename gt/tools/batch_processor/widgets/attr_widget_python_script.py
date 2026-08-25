"""
Batch Processor Python Task Attribute Widgets
"""

from gt.tools.batch_processor import batch_processor_task_base as task_base
from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
from gt.tools.batch_processor.widgets import attr_widget_base
from gt.tools.batch_processor.tasks.task_python_script import SCRIPT_MODE_BATCH_DIRECTORY
from gt.tools.batch_processor.tasks.task_python_script import SCRIPT_MODE_EXTERNAL_FILE
from gt.tools.batch_processor.tasks.task_python_script import SCRIPT_MODE_INLINE
from gt.tools.batch_processor.tasks.task_python_script import SCRIPT_MODE_VALUES
from gt.tools.batch_processor.widgets.inline_python_editor import PythonCodeTextEdit
from gt.tools.batch_processor.widgets.inline_python_editor import SampleScriptMenuButton
from gt.tools.batch_processor.widgets.inline_python_editor import configure_inline_script_button
from gt.ui.line_text_widget import LineTextWidget
from gt.ui.line_text_widget import apply_text_font_size
import gt.ui.file_dialog as ui_file_dialog
import gt.ui.qt_utils as ui_qt_utils
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt
from functools import partial
import os
import subprocess
import sys
import tempfile
import traceback


class AttrWidgetPythonScriptTask(AttrWidgetTask):
    """Attribute widget for the unified Python task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the Python task widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (PythonScriptTask, optional): Python task.
            project (BatchProcessorModel, optional): Project model.
            refresh_parent_func (callable, optional): Function used to refresh parent UI.
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
        self.mode_buttons = None
        self.python_edit = None
        self.python_edit_font = None
        self.python_editor_widget = None
        self.font_size_slider = None
        self.font_size_value_label = None
        self.highlighter = None
        self.sample_scripts_button = None
        self.base_stylesheet = ""
        self.single_mode_widget = None
        self.external_mode_widget = None
        self.batch_mode_widget = None
        self.script_path_widgets = []
        self.scripts_path_widgets = []
        self.external_scripts_layout = None
        self.batch_directories_layout = None
        self.external_script_widgets = []
        self.batch_directory_widgets = []
        self.script_list_layout = None
        self.script_count_label = None

        self.add_common_task_settings(
            scene_io_settings={
                "load_mode_key": "source_load_mode",
                "output_extension_key": "output_extension",
                "output_extension_values": [".ma", ".mb"],
            }
        )
        self.add_python_mode_controls()
        self.add_python_context_controls()
        self.add_single_script_controls()
        self.add_external_file_controls()
        self.add_batch_script_controls()
        self.refresh_mode_visibility()
        self.content_layout.addStretch()

    def add_python_mode_controls(self):
        """Adds the Python execution mode radio buttons."""
        self.add_widget_separator_line(label_text="Python Mode")
        tooltip = "Choose whether this task runs inline code, one external file, or every script in a folder."
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 3)
        layout.setSpacing(8)
        label = ui_qt.QtWidgets.QLabel("Mode:")
        label.setMinimumWidth(80)
        attr_widget_base.configure_label_for_scaled_displays(label, minimum_width=80)
        label.setMinimumHeight(35)
        label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignLeft | ui_qt.QtLib.AlignmentFlag.AlignVCenter)
        label.setToolTip(tooltip)
        layout.addWidget(label)
        self.mode_buttons = {}

        def on_radio_toggled(is_checked, radio_value):
            """Handles compact mode radio button changes.

            Args:
                is_checked (bool): Whether the button is checked.
                radio_value (str): Mode value.
            """
            if is_checked:
                self.set_script_mode(str(radio_value))

        for mode in SCRIPT_MODE_VALUES:
            radio_button = ui_qt.QtWidgets.QRadioButton(str(mode))
            radio_button.setMinimumHeight(28)
            radio_button.setToolTip(tooltip)
            radio_button.toggled.connect(partial(on_radio_toggled, radio_value=mode))
            layout.addWidget(radio_button)
            self.mode_buttons[str(mode)] = radio_button
            if str(mode) == str(self.task.get_script_mode()):
                radio_button.setChecked(True)
        layout.addStretch()
        self.content_layout.addLayout(layout)

    def add_python_context_controls(self):
        """Adds controls for script argument and environment exposure."""
        tooltip = (
            "Expose batch task values to Python scripts through arguments/args, "
            "and project environment variables through environment_variables/env."
        )
        layout = self.add_labeled_layout("Context", label_width=80, tooltip=tooltip)
        self.add_checkbox(
            "Pass Task Args",
            self.task.settings.get("pass_standard_arguments", True),
            partial(self.set_task_setting, key="pass_standard_arguments"),
            layout=layout,
            tooltip="Expose input, output, project, task, and related values as arguments and args.",
        )
        self.add_checkbox(
            "Pass Env",
            self.task.settings.get("pass_environment_arguments", True),
            partial(self.set_task_setting, key="pass_environment_arguments"),
            layout=layout,
            tooltip="Expose project environment variables as environment_variables and env.",
        )
        layout.addStretch()

    def add_single_script_controls(self):
        """Adds the inline script editor."""
        self.single_mode_widget = ui_qt.QtWidgets.QWidget()
        self.single_mode_widget.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Expanding)
        single_layout = ui_qt.QtWidgets.QVBoxLayout(self.single_mode_widget)
        single_layout.setContentsMargins(0, 0, 0, 0)
        single_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)
        self.content_layout.addWidget(self.single_mode_widget, 1)

        self.add_widget_separator_line(
            label_text="Inline Script",
            parent_layout=single_layout,
            tooltip="Inline Python code executed for every incoming file.",
        )

        top_layout = ui_qt.QtWidgets.QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 5)
        run_code_btn = ui_qt.QtWidgets.QPushButton("Run Code")
        configure_inline_script_button(run_code_btn)
        run_code_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.dev_code))
        run_code_btn.setToolTip("Execute the Python code in the text editor.")
        run_code_btn.clicked.connect(self.on_button_run_code_clicked)
        top_layout.addWidget(run_code_btn)

        insert_selection_btn = ui_qt.QtWidgets.QPushButton("Insert Selection")
        configure_inline_script_button(insert_selection_btn)
        insert_selection_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.dev_filter))
        insert_selection_btn.setToolTip("Insert the current Maya selection as a Python list at the cursor.")
        insert_selection_btn.clicked.connect(self.on_insert_selection_clicked)
        top_layout.addWidget(insert_selection_btn)

        save_btn = ui_qt.QtWidgets.QPushButton("Save")
        configure_inline_script_button(save_btn)
        save_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_save))
        save_btn.setToolTip("Save the current script to a file.")
        save_btn.clicked.connect(self.on_save_clicked)
        top_layout.addWidget(save_btn)

        load_btn = ui_qt.QtWidgets.QPushButton("Load")
        configure_inline_script_button(load_btn)
        load_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        load_btn.setToolTip("Load a script from a file.")
        load_btn.clicked.connect(self.on_load_clicked)
        top_layout.addWidget(load_btn)
        top_layout.addStretch()

        font_label = ui_qt.QtWidgets.QLabel("Font Size:")
        attr_widget_base.configure_label_for_scaled_displays(font_label)
        font_label.setToolTip("Python editor font size.")
        top_layout.addWidget(font_label)
        self.font_size_slider = ui_qt.QtWidgets.QSlider(ui_qt.QtLib.Orientation.Horizontal)
        self.font_size_slider.setRange(8, 24)
        self.font_size_slider.setMinimumWidth(125)
        initial_font_size = int(self.task.settings.get("font_size") or 14)
        self.font_size_slider.setValue(initial_font_size)
        self.font_size_slider.valueChanged.connect(self.set_editor_font_size)
        top_layout.addWidget(self.font_size_slider)
        self.font_size_value_label = ui_qt.QtWidgets.QLabel(str(initial_font_size))
        attr_widget_base.configure_label_for_scaled_displays(self.font_size_value_label)
        self.font_size_value_label.setMinimumWidth(24)
        top_layout.addWidget(self.font_size_value_label)
        sample_scripts_directory = getattr(self.task, "sample_scripts_directory", "")
        if sample_scripts_directory:
            self.sample_scripts_button = SampleScriptMenuButton(
                sample_scripts_directory=sample_scripts_directory,
                get_text_callback=self.get_inline_editor_text,
                set_text_callback=self.set_inline_editor_text,
                status_callback=self.emit_status_message,
                parent=self,
            )
            top_layout.addWidget(self.sample_scripts_button)
        else:
            top_layout.addStretch()
        single_layout.addLayout(top_layout)

        self.python_editor_widget = LineTextWidget(
            parent=self.single_mode_widget,
            text_edit=PythonCodeTextEdit(),
        )
        self.python_editor_widget.setMinimumHeight(240)
        self.python_editor_widget.setMinimumWidth(1)
        self.python_editor_widget.setSizePolicy(
            ui_qt.QtLib.SizePolicy.Expanding,
            ui_qt.QtLib.SizePolicy.Expanding,
        )
        self.python_edit = self.python_editor_widget.get_text_edit()
        self.python_edit.setPlainText(self.task.get_inline_script_text(self.project))
        self.python_edit.setPlaceholderText("Enter Python code to run for each incoming file.")
        self.base_stylesheet = ""
        self.python_edit.setStyleSheet(self.base_stylesheet)
        self.python_edit_font = ui_qt_utils.get_font(ui_res_lib.Font.roboto)
        self.python_edit.setFont(self.python_edit_font)
        self.python_edit.setFontPointSize(initial_font_size)
        self.python_edit.setToolTip("Python code executed for every incoming file. Use context for batch data.")
        single_layout.addWidget(self.python_editor_widget)

        try:
            import gt.ui.syntax_highlighter as ui_syntax_highlighter

            self.highlighter = ui_syntax_highlighter.PythonSyntaxHighlighter(self.python_edit.document())
        except Exception:
            self.highlighter = None

        self.set_editor_font_size(initial_font_size)
        self.python_edit.textChanged.connect(self.on_text_changed)

    def get_inline_editor_text(self):
        """Gets the current inline script editor text.

        Returns:
            str: Current Python code.
        """
        if not self.python_edit:
            return ""
        return self.python_edit.toPlainText()

    def set_inline_editor_text(self, script_text):
        """Replaces the inline script editor text.

        Args:
            script_text (str): Python code to display and persist.
        """
        if self.python_edit:
            self.python_edit.setPlainText(str(script_text or ""))

    def add_external_file_controls(self):
        """Adds controls for running an ordered list of external Python files."""
        self.external_mode_widget = ui_qt.QtWidgets.QWidget()
        self.external_mode_widget.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Preferred)
        external_layout = ui_qt.QtWidgets.QVBoxLayout(self.external_mode_widget)
        external_layout.setContentsMargins(0, 0, 0, 0)
        external_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)
        self.content_layout.addWidget(self.external_mode_widget)

        self.add_widget_separator_line(
            label_text="External File",
            parent_layout=external_layout,
            tooltip="External Python files executed in the order shown for every incoming file.",
        )
        buttons_layout = ui_qt.QtWidgets.QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 5)
        buttons_layout.addStretch()
        add_button = ui_qt.QtWidgets.QPushButton("+")
        self.configure_add_button(add_button)
        add_button.setToolTip("Add an external Python script entry with its default path.")
        add_button.clicked.connect(self.add_external_scripts)
        buttons_layout.addWidget(add_button)
        external_layout.addLayout(buttons_layout)
        self.external_scripts_layout = ui_qt.QtWidgets.QVBoxLayout()
        self.external_scripts_layout.setContentsMargins(0, 0, 0, 5)
        self.external_scripts_layout.setSpacing(3)
        external_layout.addLayout(self.external_scripts_layout)
        self.refresh_external_script_rows()

    def add_batch_script_controls(self):
        """Adds controls for running scripts from ordered directories."""
        self.batch_mode_widget = ui_qt.QtWidgets.QWidget()
        self.batch_mode_widget.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Preferred)
        batch_layout = ui_qt.QtWidgets.QVBoxLayout(self.batch_mode_widget)
        batch_layout.setContentsMargins(0, 0, 0, 0)
        batch_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)
        self.content_layout.addWidget(self.batch_mode_widget)

        self.add_widget_separator_line(
            label_text="Batch Directory",
            parent_layout=batch_layout,
            tooltip="Directories are processed in order; scripts in each directory are sorted and run first.",
        )
        buttons_layout = ui_qt.QtWidgets.QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 5)
        buttons_layout.addStretch()
        add_button = ui_qt.QtWidgets.QPushButton("+")
        self.configure_add_button(add_button)
        add_button.setToolTip("Add a batch script directory.")
        add_button.clicked.connect(self.add_batch_directory)
        buttons_layout.addWidget(add_button)
        refresh_button = ui_qt.QtWidgets.QPushButton("Refresh Scripts")
        refresh_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_reset))
        refresh_button.setToolTip("Refresh detected Python scripts.")
        refresh_button.clicked.connect(lambda *args: self.refresh_script_list(update_status=True))
        buttons_layout.addWidget(refresh_button)
        batch_layout.addLayout(buttons_layout)

        self.batch_directories_layout = ui_qt.QtWidgets.QVBoxLayout()
        self.batch_directories_layout.setContentsMargins(0, 0, 0, 5)
        self.batch_directories_layout.setSpacing(3)
        batch_layout.addLayout(self.batch_directories_layout)

        self.script_count_label = ui_qt.QtWidgets.QLabel()
        self.script_count_label.setToolTip("Detected Python scripts.")
        batch_layout.addWidget(self.script_count_label)
        self.script_list_layout = ui_qt.QtWidgets.QVBoxLayout()
        self.script_list_layout.setContentsMargins(0, 0, 0, 5)
        batch_layout.addLayout(self.script_list_layout)
        self.refresh_batch_directory_rows()
        self.refresh_script_list(update_status=False)

    @staticmethod
    def configure_add_button(button):
        """Makes an add button's plus icon easier to see without resizing it.

        Args:
            button (QPushButton): Add button to configure.
        """
        button.setText("")
        button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_add))
        button.setIconSize(ui_qt.QtCore.QSize(18, 18))
        button.setMinimumWidth(32)

    def _clear_dynamic_rows(self, layout):
        """Clears row widgets from a dynamic layout.

        Args:
            layout (QLayout): Layout containing row widgets.
        """
        while layout and layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def add_external_scripts(self):
        """Adds a new external Python script entry with its default path."""
        entries = self.task.get_external_script_entries()
        default_path = self.task.get_default_settings().get("script_path", "")
        entries.append({"path": default_path, "enabled": True})
        self.task.set_external_script_entries(entries)
        self.refresh_external_script_rows()
        self.emit_status_message("Added an external Python script entry.")

    def refresh_external_script_rows(self):
        """Rebuilds external script rows from task settings."""
        if not self.external_scripts_layout:
            return
        self._clear_dynamic_rows(self.external_scripts_layout)
        self.script_path_widgets = []
        self.external_script_widgets = []
        entries = self.task.get_external_script_entries()
        if not entries:
            empty_label = ui_qt.QtWidgets.QLabel("No external Python scripts configured. Use + to add one.")
            empty_label.setStyleSheet("color: grey;")
            self.external_scripts_layout.addWidget(empty_label)
            return
        entry_count = len(entries)
        for script_index, entry in enumerate(entries):
            self.add_external_script_row(script_index, entry, entry_count)

    def add_external_script_row(self, script_index, entry, entry_count=None):
        """Adds one editable external script row.

        Args:
            script_index (int): Zero-based entry index.
            entry (dict): External script settings.
            entry_count (int, optional): Number of configured external script entries.

        Returns:
            dict: Created row widgets.
        """
        tooltip = "External Python file to run for every incoming file."
        entry_count = entry_count if entry_count is not None else len(self.task.get_external_script_entries())
        row_widget = ui_qt.QtWidgets.QWidget()
        layout = ui_qt.QtWidgets.QHBoxLayout(row_widget)
        layout.setContentsMargins(0, 0, 0, 3)
        layout.setSpacing(6)
        index_label = ui_qt.QtWidgets.QLabel(f"{script_index + 1:02d}")
        index_label.setMinimumWidth(28)
        index_label.setStyleSheet("color: grey;")
        index_label.setToolTip("External script order.")
        layout.addWidget(index_label)
        enabled_checkbox = ui_qt.QtWidgets.QCheckBox()
        enabled_checkbox.setChecked(bool(entry.get("enabled", True)))
        enabled_checkbox.setToolTip("Disabled scripts remain saved but are not run.")
        enabled_checkbox.stateChanged.connect(
            lambda *args, index=script_index, checkbox=enabled_checkbox: self.set_external_script_enabled(
                index, checkbox.isChecked()
            )
        )
        layout.addWidget(enabled_checkbox)
        field = self.create_text_field(
            text=entry.get("path"),
            placeholder="{project-dir}/scripts/post_process.py",
            tooltip=tooltip,
        )
        info_button = ui_qt.QtWidgets.QPushButton()
        info_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_env_var))
        info_button.setToolTip("Get more information about the current path.")
        open_button = ui_qt.QtWidgets.QPushButton()
        open_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open_external))
        open_button.setToolTip("Open the resolved script directory.")
        browse_button = ui_qt.QtWidgets.QPushButton()
        browse_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        browse_button.setToolTip("Browse for a Python script.")
        edit_button = ui_qt.QtWidgets.QPushButton()
        edit_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_templates_python))
        edit_button.setToolTip("Open this Python script for editing.")
        delete_button = ui_qt.QtWidgets.QPushButton()
        delete_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete))
        delete_button.setToolTip("Remove this external script.")
        layout.addWidget(field)
        layout.addWidget(info_button)
        layout.addWidget(open_button)
        layout.addWidget(browse_button)
        layout.addWidget(edit_button)
        move_up_button = None
        move_down_button = None
        if entry_count > 1:
            move_up_button = self.create_move_button(
                icon_path=ui_res_lib.Icon.ui_arrow_up,
                tooltip="Move this external script up in the execution order.",
                enabled=script_index > 0,
            )
            move_down_button = self.create_move_button(
                icon_path=ui_res_lib.Icon.ui_arrow_down,
                tooltip="Move this external script down in the execution order.",
                enabled=script_index < entry_count - 1,
            )
            layout.addWidget(move_up_button)
            layout.addWidget(move_down_button)
        layout.addWidget(delete_button)
        field.textChanged.connect(
            partial(
                self.set_path_field_value,
                field=field,
                setter=partial(self.set_external_script_path, script_index=script_index),
            )
        )
        info_button.clicked.connect(partial(self.open_env_var_feedback_dialog, field=field))
        open_button.clicked.connect(partial(self.open_resolved_path_directory, field=field))
        browse_button.clicked.connect(
            partial(
                self.open_path_dialog,
                field=field,
                dir_only=False,
                file_filter="Python Files (*.py);;All Files (*);;",
            )
        )
        edit_button.clicked.connect(
            lambda checked=False, path_field=field: self.open_python_script(
                self.get_resolved_field_path(path_field)
            )
        )
        if move_up_button:
            move_up_button.clicked.connect(
                lambda checked=False, index=script_index: self.move_external_script(index, -1)
            )
        if move_down_button:
            move_down_button.clicked.connect(
                lambda checked=False, index=script_index: self.move_external_script(index, 1)
            )
        delete_button.clicked.connect(lambda checked=False, index=script_index: self.remove_external_script(index))
        self.external_scripts_layout.addWidget(row_widget)
        row_widgets = {
            "row": row_widget,
            "field": field,
            "enabled_checkbox": enabled_checkbox,
            "info_button": info_button,
            "open_button": open_button,
            "browse_button": browse_button,
            "edit_button": edit_button,
            "move_up_button": move_up_button,
            "move_down_button": move_down_button,
            "delete_button": delete_button,
        }
        self.script_path_widgets.append(row_widgets)
        self.external_script_widgets.append(row_widgets)
        return row_widgets

    def set_external_script_path(self, path, script_index):
        """Stores an external script path from a row editor.

        Args:
            path (str): New script path.
            script_index (int): Zero-based entry index.
        """
        entries = self.task.get_external_script_entries()
        if script_index >= len(entries):
            return
        entries[script_index]["path"] = path
        self.task.set_external_script_entries(entries)

    def set_external_script_enabled(self, script_index, enabled):
        """Stores the enabled state from an external script row.

        Args:
            script_index (int): Zero-based entry index.
            enabled (bool): Whether the script should run.
        """
        entries = self.task.get_external_script_entries()
        if script_index >= len(entries):
            return
        entries[script_index]["enabled"] = bool(enabled)
        self.task.set_external_script_entries(entries)

    def remove_external_script(self, script_index):
        """Removes one external script entry.

        Args:
            script_index (int): Zero-based entry index.
        """
        entries = self.task.get_external_script_entries()
        if script_index >= len(entries):
            return
        entries.pop(script_index)
        self.task.set_external_script_entries(entries)
        self.refresh_external_script_rows()

    def move_external_script(self, script_index, index_offset):
        """Moves an external script row and refreshes its displayed order.

        Args:
            script_index (int): Zero-based index of the external script to move.
            index_offset (int): Positive or negative number of positions to move.
        """
        if not self.task.move_external_script_entry(script_index, index_offset):
            return
        self.refresh_external_script_rows()
        self.emit_status_message("Updated external Python script order.")

    def add_batch_directory(self):
        """Adds a batch script directory entry with its default path."""
        entries = self.task.get_batch_directory_entries()
        default_path = self.task.get_default_settings().get("scripts_path", "")
        entries.append({"path": default_path, "include_patterns": "", "exclude_patterns": ""})
        self.task.set_batch_directory_entries(entries)
        self.refresh_batch_directory_rows()
        self.refresh_script_list(update_status=True)

    def refresh_batch_directory_rows(self):
        """Rebuilds batch-directory rows from task settings."""
        if not self.batch_directories_layout:
            return
        self._clear_dynamic_rows(self.batch_directories_layout)
        self.scripts_path_widgets = []
        self.batch_directory_widgets = []
        entries = self.task.get_batch_directory_entries()
        if not entries:
            empty_label = ui_qt.QtWidgets.QLabel("No batch script directories configured. Use + to add one.")
            empty_label.setStyleSheet("color: grey;")
            self.batch_directories_layout.addWidget(empty_label)
            return
        entry_count = len(entries)
        for directory_index, entry in enumerate(entries):
            self.add_batch_directory_row(directory_index, entry, entry_count)

    def add_batch_directory_row(self, directory_index, entry, entry_count=None):
        """Adds an expandable two-row batch-directory entry.

        Args:
            directory_index (int): Zero-based directory index.
            entry (dict): Batch-directory settings.
            entry_count (int, optional): Number of configured batch-directory entries.

        Returns:
            dict: Created row widgets.
        """
        tooltip = "Folder containing Python scripts. Its scripts run before later directories."
        entry_count = entry_count if entry_count is not None else len(self.task.get_batch_directory_entries())
        container = ui_qt.QtWidgets.QWidget()
        container_layout = ui_qt.QtWidgets.QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(2)
        path_row = ui_qt.QtWidgets.QHBoxLayout()
        path_row.setContentsMargins(0, 0, 0, 0)
        path_row.setSpacing(6)
        index_label = ui_qt.QtWidgets.QLabel(f"{directory_index + 1:02d}")
        index_label.setMinimumWidth(28)
        index_label.setStyleSheet("color: grey;")
        index_label.setToolTip("Batch directory order.")
        path_row.addWidget(index_label)
        field = self.create_text_field(
            text=entry.get("path"),
            placeholder="{project-dir}/scripts",
            tooltip=tooltip,
        )
        info_button = ui_qt.QtWidgets.QPushButton()
        info_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_env_var))
        info_button.setToolTip("Get more information about the current path.")
        open_button = ui_qt.QtWidgets.QPushButton()
        open_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open_external))
        open_button.setToolTip("Open this directory.")
        browse_button = ui_qt.QtWidgets.QPushButton()
        browse_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        browse_button.setToolTip("Browse for a directory.")
        expand_button = ui_qt.QtWidgets.QPushButton("v")
        expand_button.setCheckable(True)
        expand_button.setMinimumWidth(32)
        expand_button.setToolTip("Show or hide include, exclude, and delete controls.")
        path_row.addWidget(field)
        path_row.addWidget(info_button)
        path_row.addWidget(open_button)
        path_row.addWidget(browse_button)
        move_up_button = None
        move_down_button = None
        if entry_count > 1:
            move_up_button = self.create_move_button(
                icon_path=ui_res_lib.Icon.ui_arrow_up,
                tooltip="Move this batch directory up in the execution order.",
                enabled=directory_index > 0,
            )
            move_down_button = self.create_move_button(
                icon_path=ui_res_lib.Icon.ui_arrow_down,
                tooltip="Move this batch directory down in the execution order.",
                enabled=directory_index < entry_count - 1,
            )
            path_row.addWidget(move_up_button)
            path_row.addWidget(move_down_button)
        path_row.addWidget(expand_button)
        container_layout.addLayout(path_row)

        filters_row = ui_qt.QtWidgets.QWidget()
        filters_layout = ui_qt.QtWidgets.QHBoxLayout(filters_row)
        filters_layout.setContentsMargins(34, 0, 0, 3)
        filters_layout.setSpacing(6)
        include_label = ui_qt.QtWidgets.QLabel("Include:")
        include_label.setMinimumWidth(52)
        include_field = self.create_text_field(
            text=entry.get("include_patterns"),
            placeholder="publish_*.py, rig/*.py",
            tooltip="Optional glob patterns to include for this directory.",
        )
        exclude_label = ui_qt.QtWidgets.QLabel("Exclude:")
        exclude_label.setMinimumWidth(52)
        exclude_field = self.create_text_field(
            text=entry.get("exclude_patterns"),
            placeholder="wip_*.py, deprecated/*",
            tooltip="Glob patterns to skip for this directory.",
        )
        delete_button = ui_qt.QtWidgets.QPushButton()
        delete_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete))
        delete_button.setToolTip("Remove this batch script directory.")
        filters_layout.addWidget(include_label)
        filters_layout.addWidget(include_field, 1)
        filters_layout.addWidget(exclude_label)
        filters_layout.addWidget(exclude_field, 1)
        filters_layout.addWidget(delete_button)
        container_layout.addWidget(filters_row)
        filters_row.setVisible(False)

        field.textChanged.connect(
            partial(
                self.set_path_field_value,
                field=field,
                setter=partial(self.set_batch_directory_path, directory_index=directory_index),
            )
        )
        field.textChanged.connect(lambda *args: self.refresh_scripts_if_directory_exists())
        include_field.textChanged.connect(
            lambda value, index=directory_index: self.set_batch_directory_filter(index, "include_patterns", value)
        )
        exclude_field.textChanged.connect(
            lambda value, index=directory_index: self.set_batch_directory_filter(index, "exclude_patterns", value)
        )
        info_button.clicked.connect(partial(self.open_env_var_feedback_dialog, field=field))
        open_button.clicked.connect(partial(self.open_resolved_path_directory, field=field))
        browse_button.clicked.connect(partial(self.open_path_dialog, field=field, dir_only=True))
        expand_button.toggled.connect(
            lambda is_checked, button=expand_button, widget=filters_row: self.toggle_batch_directory(
                button, widget, is_checked
            )
        )
        if move_up_button:
            move_up_button.clicked.connect(
                lambda checked=False, index=directory_index: self.move_batch_directory(index, -1)
            )
        if move_down_button:
            move_down_button.clicked.connect(
                lambda checked=False, index=directory_index: self.move_batch_directory(index, 1)
            )
        delete_button.clicked.connect(
            lambda checked=False, index=directory_index: self.remove_batch_directory(index)
        )
        self.batch_directories_layout.addWidget(container)
        row_widgets = {
            "container": container,
            "field": field,
            "info_button": info_button,
            "open_button": open_button,
            "browse_button": browse_button,
            "move_up_button": move_up_button,
            "move_down_button": move_down_button,
            "expand_button": expand_button,
            "filters_row": filters_row,
            "include_field": include_field,
            "exclude_field": exclude_field,
            "delete_button": delete_button,
        }
        self.scripts_path_widgets.append(row_widgets)
        self.batch_directory_widgets.append(row_widgets)
        return row_widgets

    @staticmethod
    def toggle_batch_directory(button, filters_widget, is_expanded):
        """Toggles the advanced row for a batch directory.

        Args:
            button (QPushButton): Expand/collapse button.
            filters_widget (QWidget): Advanced settings row.
            is_expanded (bool): Whether the row should be visible.
        """
        filters_widget.setVisible(bool(is_expanded))
        button.setText("^" if is_expanded else "v")

    def set_batch_directory_path(self, path, directory_index):
        """Stores a batch-directory path from a row editor.

        Args:
            path (str): New directory path.
            directory_index (int): Zero-based directory index.
        """
        entries = self.task.get_batch_directory_entries()
        if directory_index >= len(entries):
            return
        entries[directory_index]["path"] = path
        self.task.set_batch_directory_entries(entries)

    def set_batch_directory_filter(self, directory_index, key, value):
        """Stores an include or exclude filter for a batch directory.

        Args:
            directory_index (int): Zero-based directory index.
            key (str): Entry key to update.
            value (str): Filter text.
        """
        entries = self.task.get_batch_directory_entries()
        if directory_index >= len(entries):
            return
        entries[directory_index][key] = value
        self.task.set_batch_directory_entries(entries)
        self.refresh_script_list(update_status=False)

    def remove_batch_directory(self, directory_index):
        """Removes one batch-directory entry.

        Args:
            directory_index (int): Zero-based directory index.
        """
        entries = self.task.get_batch_directory_entries()
        if directory_index >= len(entries):
            return
        entries.pop(directory_index)
        self.task.set_batch_directory_entries(entries)
        self.refresh_batch_directory_rows()
        self.refresh_script_list(update_status=True)

    def move_batch_directory(self, directory_index, index_offset):
        """Moves a batch-directory row and refreshes the detected scripts.

        Args:
            directory_index (int): Zero-based index of the directory to move.
            index_offset (int): Positive or negative number of positions to move.
        """
        if not self.task.move_batch_directory_entry(directory_index, index_offset):
            return
        self.refresh_batch_directory_rows()
        self.refresh_script_list(update_status=True)

    @staticmethod
    def create_move_button(icon_path, tooltip, enabled):
        """Creates a compact script-order button.

        Args:
            icon_path (str): Resource path for the arrow icon.
            tooltip (str): User-facing button tooltip.
            enabled (bool): Whether the movement is valid at the current list edge.

        Returns:
            QPushButton: Configured move button.
        """
        button = ui_qt.QtWidgets.QPushButton()
        button.setIcon(ui_qt.QtGui.QIcon(icon_path))
        button.setIconSize(ui_qt.QtCore.QSize(16, 16))
        button.setMinimumWidth(28)
        button.setEnabled(bool(enabled))
        button.setToolTip(tooltip)
        return button

    def set_script_mode(self, value):
        """Sets the current script mode and refreshes visible controls.

        Args:
            value (str): Selected script mode.
        """
        self.task.set_script_mode(value)
        self.refresh_mode_visibility()

    def refresh_mode_visibility(self):
        """Shows the controls for the active script mode."""
        script_mode = self.task.get_script_mode()
        is_inline_mode = script_mode == SCRIPT_MODE_INLINE
        is_external_file_mode = script_mode == SCRIPT_MODE_EXTERNAL_FILE
        is_batch_directory_mode = script_mode == SCRIPT_MODE_BATCH_DIRECTORY
        if self.single_mode_widget:
            self.single_mode_widget.setVisible(is_inline_mode)
        if self.external_mode_widget:
            self.external_mode_widget.setVisible(is_external_file_mode)
        if self.batch_mode_widget:
            self.batch_mode_widget.setVisible(is_batch_directory_mode)
        if is_batch_directory_mode:
            self.refresh_script_list(update_status=False)

    def refresh_scripts_if_directory_exists(self):
        """Refreshes the batch script list when a configured directory exists."""
        if not self.batch_directory_widgets or not self.script_list_layout:
            return
        for row_widgets in self.batch_directory_widgets:
            directory_path = self.get_resolved_field_path(row_widgets.get("field"))
            if os.path.isdir(directory_path):
                self.refresh_script_list(update_status=True)
                return

    def on_button_run_code_clicked(self):
        """Executes the Python code from the text editor."""
        script_text = self.python_edit.toPlainText() if self.python_edit else ""
        if not script_text.strip():
            message = "Python editor code is empty."
            self.emit_status_message(message, status="warning")
            sys.stdout.write("{0}\n".format(message))
            return
        try:
            runtime_context = self.build_editor_preview_context()
            sys.stdout.write("Running Python editor code...\n")
            self.task.run_inline_python_script(script_text=script_text, context=runtime_context)
        except Exception as exception:
            traceback.print_exc()
            message = "Python editor code failed: {0}".format(exception)
            self.emit_status_message(message, status="warning")
            sys.stderr.write("{0}\n".format(message))
            return
        self.emit_status_message("Executed Python editor code.")
        sys.stdout.write("Executed Python editor code.\n")

    def build_editor_preview_context(self):
        """Builds the context used when running inline code from the editor.

        Returns:
            dict: Runtime context matching the task execution context.
        """
        work_item = self.build_editor_preview_work_item()
        task_index = None
        step_output_dir = tempfile.gettempdir()
        if self.project:
            try:
                if hasattr(self.project, "get_task_environment_index"):
                    task_index = self.project.get_task_environment_index(self.task)
                step_output_dir = self.task.resolve_task_path(self.project, task_index=task_index)
            except Exception:
                step_output_dir = self.project.get_project_dir() or tempfile.gettempdir()
        try:
            output_path = self.task.build_output_path(work_item=work_item, step_output_dir=step_output_dir)
        except Exception:
            output_path = os.path.join(step_output_dir, "python_preview{0}".format(self.task.get_output_extension()))
        return self.task.build_script_context(
            work_item=work_item,
            output_path=output_path,
            project=self.project,
            script_paths=[],
            context={"preview": True, "run_code": True},
        )

    def build_editor_preview_work_item(self):
        """Builds a representative work item for the editor Run Code action.

        Returns:
            WorkItem: Preview work item.
        """
        source_path = ""
        if self.project:
            try:
                input_files = self.project.discover_input_files()
                if input_files:
                    source_path = input_files[0]
            except Exception:
                source_path = ""
            if not source_path:
                source_path = self.project.get_project_dir()
        if not source_path:
            source_path = os.getcwd()
        return task_base.WorkItem(source_path=source_path)

    def set_editor_font_size(self, size):
        """Updates the Python editor font size.

        Args:
            size (int): New editor font size.
        """
        size = int(size or 14)
        self.task.settings["font_size"] = size
        if self.font_size_value_label:
            self.font_size_value_label.setText(str(size))
        if self.python_edit_font:
            self.python_edit_font.setPointSize(size)
            self.python_edit.setFont(self.python_edit_font)
        apply_text_font_size(self.python_edit, size)
        self._update_editor_stylesheet(size)

    def _update_editor_stylesheet(self, font_size):
        """Applies font size and tab width to the Python editor.

        Args:
            font_size (int): Font size.
        """
        if not self.python_edit:
            return
        dynamic_stylesheet = self.base_stylesheet + "; font-size: {0}pt;".format(font_size)
        self.python_edit.setStyleSheet(dynamic_stylesheet)
        if self.python_editor_widget:
            self.python_editor_widget.number_bar.setFont(self.python_edit.font())
            self.python_editor_widget.number_bar.update()
        font_metrics = ui_qt.QtGui.QFontMetrics(self.python_edit.font())
        if hasattr(font_metrics, "horizontalAdvance"):
            space_width = font_metrics.horizontalAdvance(" ")
        else:
            space_width = font_metrics.width(" ")
        try:
            self.python_edit.setTabStopWidth(space_width * 6)
        except Exception:
            self.python_edit.setTabStopDistance(space_width * 6)

    def on_save_clicked(self):
        """Saves the current editor contents to a Python file."""
        import gt.core.io as core_io

        file_path = ui_file_dialog.file_dialog(
            parent=self,
            write_mode=True,
            caption="Save Python Script",
            starting_directory=self.get_dialog_starting_directory(),
            file_filter="Python Files (*.py)",
        )
        if not file_path:
            return
        content = self.python_edit.toPlainText()
        success = core_io.write_data(path=file_path, data=content)
        if success:
            self.emit_status_message("Saved Python script: {0}".format(file_path))
        else:
            self.emit_status_message("Warning: Failed to save script: {0}".format(file_path), status="warning")

    def on_load_clicked(self):
        """Loads a Python file into the editor."""
        import gt.core.io as core_io

        file_path = ui_file_dialog.file_dialog(
            parent=self,
            write_mode=False,
            caption="Open Python Script",
            starting_directory=self.get_dialog_starting_directory(),
            file_filter="Python Files (*.py)",
        )
        if not file_path:
            return
        content = core_io.read_data(path=file_path)
        if content is not None:
            self.python_edit.setText(content)
            self.on_text_changed()
            self.emit_status_message("Loaded Python script: {0}".format(file_path))
        else:
            self.emit_status_message("Warning: Failed to read script: {0}".format(file_path), status="warning")

    def on_insert_selection_clicked(self):
        """Inserts the current Maya selection as a Python list at the cursor."""
        try:
            import gt.core.selection as core_sel

            selection = core_sel.ensure_selection_count(selection_limit=None, require_exact_count=False)
        except Exception as exception:
            self.emit_status_message(
                "Warning: Unable to insert Maya selection: {0}".format(exception),
                status="warning",
            )
            return
        if selection:
            cursor = self.python_edit.textCursor()
            cursor.insertText(repr(selection))

    def on_text_changed(self):
        """Stores the editor content on the task settings."""
        self.task.settings["script_text"] = self.python_edit.toPlainText()
        if self.font_size_slider:
            self._update_editor_stylesheet(self.font_size_slider.value())
        if self.python_edit and self.python_edit_font:
            self.python_edit.setFont(self.python_edit_font)

    def refresh_script_list(self, update_status=True):
        """Refreshes the detected script list.

        Args:
            update_status (bool, optional): Whether to emit a bottom status message.
        """
        if not self.script_list_layout or not self.script_count_label:
            return
        self.clear_script_list()
        script_paths = self.task.get_script_paths(self.project)
        self.script_count_label.setText("Detected Scripts: {0}".format(len(script_paths)))
        if not script_paths:
            label = ui_qt.QtWidgets.QLabel("No Python scripts found.")
            label.setStyleSheet("color: grey;")
            self.script_list_layout.addWidget(label)
        for script_index, script_path in enumerate(script_paths, start=1):
            self.add_script_row(script_path=script_path, script_index=script_index)
        if update_status:
            self.emit_status_message("Detected {0} Python script(s).".format(len(script_paths)))

    def clear_script_list(self):
        """Clears script list row widgets."""
        while self.script_list_layout.count():
            item = self.script_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def add_script_row(self, script_path, script_index):
        """Adds one read-only script row.

        Args:
            script_path (str): Script path represented by the row.
            script_index (int): One-based script index.
        """
        row_widget = ui_qt.QtWidgets.QWidget()
        row_layout = ui_qt.QtWidgets.QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        index_label = ui_qt.QtWidgets.QLabel("{0:02d}".format(int(script_index)))
        index_label.setMinimumWidth(28)
        index_label.setStyleSheet("color: grey;")
        index_label.setToolTip("Script order.")
        icon_label = ui_qt.QtWidgets.QLabel()
        icon_label.setPixmap(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_templates_python).pixmap(18, 18))
        icon_label.setToolTip("Python script.")
        label = ui_qt.QtWidgets.QLabel(os.path.basename(script_path))
        label.setMinimumWidth(1)
        label.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Preferred)
        label.setToolTip(script_path)
        edit_button = ui_qt.QtWidgets.QPushButton()
        edit_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_templates_python))
        edit_button.setToolTip("Open this Python script for editing.")
        edit_button.clicked.connect(lambda checked=False, path=script_path: self.open_python_script(path))
        row_layout.addWidget(index_label)
        row_layout.addWidget(icon_label)
        row_layout.addWidget(label, 1)
        row_layout.addWidget(edit_button)
        self.script_list_layout.addWidget(row_widget)

    def open_configured_script(self):
        """Opens the first enabled external Python script for editing."""
        script_paths = self.task.get_script_paths(self.project)
        script_path = script_paths[0] if script_paths else self.task.resolve_script_path(self.project)
        self.open_python_script(script_path)

    def open_python_script(self, script_path):
        """Opens a Python script in an external editor.

        Args:
            script_path (str): Python script path.
        """
        if not script_path or not os.path.isfile(script_path):
            self.emit_status_message(
                "Warning: Unable to open Python script because the file does not exist: {0}".format(script_path),
                status="warning",
            )
            return
        try:
            if os.name == "nt":
                subprocess.Popen(["notepad.exe", script_path])
            else:
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.Popen([opener, script_path])
            self.emit_status_message("Opened Python script: {0}".format(script_path))
        except Exception as exception:
            self.emit_status_message(
                "Warning: Unable to open Python script: {0}".format(exception),
                status="warning",
            )


class AttrWidgetPythonScriptsFolderTask(AttrWidgetPythonScriptTask):
    """Backward-compatible alias for old imports."""
