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
        run_code_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.dev_code))
        run_code_btn.setToolTip("Execute the Python code in the text editor.")
        run_code_btn.clicked.connect(self.on_button_run_code_clicked)
        top_layout.addWidget(run_code_btn)

        insert_selection_btn = ui_qt.QtWidgets.QPushButton("Insert Selection")
        insert_selection_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.dev_filter))
        insert_selection_btn.setToolTip("Insert the current Maya selection as a Python list at the cursor.")
        insert_selection_btn.clicked.connect(self.on_insert_selection_clicked)
        top_layout.addWidget(insert_selection_btn)

        save_btn = ui_qt.QtWidgets.QPushButton("Save")
        save_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_save))
        save_btn.setToolTip("Save the current script to a file.")
        save_btn.clicked.connect(self.on_save_clicked)
        top_layout.addWidget(save_btn)

        load_btn = ui_qt.QtWidgets.QPushButton("Load")
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
        top_layout.addStretch()
        single_layout.addLayout(top_layout)

        self.python_edit = PythonCodeTextEdit()
        self.python_edit.setMinimumHeight(240)
        self.python_edit.setMinimumWidth(1)
        self.python_edit.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Expanding)
        self.python_edit.setPlainText(self.task.get_inline_script_text(self.project))
        self.python_edit.setPlaceholderText("Enter Python code to run for each incoming file.")
        self.base_stylesheet = ""
        self.python_edit.setStyleSheet(self.base_stylesheet)
        self.python_edit_font = ui_qt_utils.get_font(ui_res_lib.Font.roboto)
        self.python_edit.setFont(self.python_edit_font)
        self.python_edit.setFontPointSize(initial_font_size)
        self.python_edit.setToolTip("Python code executed for every incoming file. Use context for batch data.")
        single_layout.addWidget(self.python_edit)

        try:
            import gt.ui.syntax_highlighter as ui_syntax_highlighter

            self.highlighter = ui_syntax_highlighter.PythonSyntaxHighlighter(self.python_edit.document())
        except Exception:
            self.highlighter = None

        self.set_editor_font_size(initial_font_size)
        self.python_edit.textChanged.connect(self.on_text_changed)

    def add_external_file_controls(self):
        """Adds controls for running one external Python file."""
        self.external_mode_widget = ui_qt.QtWidgets.QWidget()
        self.external_mode_widget.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Preferred)
        external_layout = ui_qt.QtWidgets.QVBoxLayout(self.external_mode_widget)
        external_layout.setContentsMargins(0, 0, 0, 0)
        external_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)
        self.content_layout.addWidget(self.external_mode_widget)

        self.add_widget_separator_line(
            label_text="External File",
            parent_layout=external_layout,
            tooltip="Single external Python file executed for every incoming file.",
        )
        self.script_path_widgets = self.add_script_file_path_controls(external_layout)

    def add_batch_script_controls(self):
        """Adds the folder-based batch script controls."""
        self.batch_mode_widget = ui_qt.QtWidgets.QWidget()
        self.batch_mode_widget.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Preferred)
        batch_layout = ui_qt.QtWidgets.QVBoxLayout(self.batch_mode_widget)
        batch_layout.setContentsMargins(0, 0, 0, 0)
        batch_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)
        self.content_layout.addWidget(self.batch_mode_widget)

        self.add_widget_separator_line(
            label_text="Batch Directory",
            parent_layout=batch_layout,
            tooltip="Folder containing Python scripts to run in sorted order.",
        )
        self.scripts_path_widgets = self.add_scripts_path_controls(batch_layout)

        buttons_layout = ui_qt.QtWidgets.QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 5)
        buttons_layout.addStretch()
        self.batch_filters_button = ui_qt.QtWidgets.QPushButton()
        self.batch_filters_button.setCheckable(True)
        self.batch_filters_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.dev_filter))
        self.batch_filters_button.setToolTip("Show or hide include and exclude filters for batch-directory scripts.")
        self.batch_filters_button.clicked.connect(self.toggle_batch_filters)
        buttons_layout.addWidget(self.batch_filters_button)
        refresh_button = ui_qt.QtWidgets.QPushButton("Refresh Scripts")
        refresh_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_reset))
        refresh_button.setToolTip("Refresh detected Python scripts.")
        refresh_button.clicked.connect(lambda *args: self.refresh_script_list(update_status=True))
        buttons_layout.addWidget(refresh_button)
        batch_layout.addLayout(buttons_layout)
        self.add_batch_filter_controls(batch_layout)

        self.script_count_label = ui_qt.QtWidgets.QLabel()
        self.script_count_label.setToolTip("Detected Python scripts.")
        batch_layout.addWidget(self.script_count_label)
        self.script_list_layout = ui_qt.QtWidgets.QVBoxLayout()
        self.script_list_layout.setContentsMargins(0, 0, 0, 5)
        batch_layout.addLayout(self.script_list_layout)
        self.refresh_batch_filters_visibility(store_state=False)
        self.refresh_script_list(update_status=False)

    def add_batch_filter_controls(self, parent_layout):
        """Adds optional include and exclude controls for batch-directory scripts.

        Args:
            parent_layout (QLayout): Layout that receives the filter controls.
        """
        self.batch_filters_widget = ui_qt.QtWidgets.QWidget()
        self.batch_filters_widget.setSizePolicy(
            ui_qt.QtLib.SizePolicy.Expanding,
            ui_qt.QtLib.SizePolicy.Preferred,
        )
        filters_layout = ui_qt.QtWidgets.QVBoxLayout(self.batch_filters_widget)
        filters_layout.setContentsMargins(0, 0, 0, 5)
        filters_layout.setSpacing(5)
        include_tooltip = (
            "Optional comma, semicolon, or newline-separated glob patterns. "
            "When empty, every non-excluded .py script is included."
        )
        exclude_tooltip = (
            "Comma, semicolon, or newline-separated glob patterns to skip. "
            "Matches file names, relative script paths, or absolute paths."
        )
        self.batch_include_field = self.add_text_field(
            "Include",
            self.task.settings.get("batch_include_patterns"),
            partial(self.set_batch_filter_text, key="batch_include_patterns"),
            placeholder="Optional: publish_*.py, rig/*.py",
            tooltip=include_tooltip,
            parent_layout=filters_layout,
        )
        self.batch_exclude_field = self.add_text_field(
            "Exclude",
            self.task.settings.get("batch_exclude_patterns"),
            partial(self.set_batch_filter_text, key="batch_exclude_patterns"),
            placeholder="Skip: wip_*.py, _shared.py, deprecated/*",
            tooltip=exclude_tooltip,
            parent_layout=filters_layout,
        )
        parent_layout.addWidget(self.batch_filters_widget)

    def toggle_batch_filters(self, *args):
        """Toggles visibility for batch include and exclude filters."""
        self.refresh_batch_filters_visibility(store_state=True)

    def refresh_batch_filters_visibility(self, store_state=False):
        """Refreshes batch filter widget visibility and button text.

        Args:
            store_state (bool, optional): Whether to persist the current button state.
        """
        if not self.batch_filters_widget or not self.batch_filters_button:
            return
        is_visible = bool(self.task.settings.get("batch_filters_visible", False))
        if store_state:
            is_visible = bool(self.batch_filters_button.isChecked())
            self.task.settings["batch_filters_visible"] = is_visible
        self.batch_filters_button.setChecked(is_visible)
        self.batch_filters_button.setText("Hide Filters" if is_visible else "Show Filters")
        self.batch_filters_widget.setVisible(is_visible)

    def set_batch_filter_text(self, text, key):
        """Stores batch filter text and refreshes the detected scripts.

        Args:
            text (str): Filter text.
            key (str): Task settings key.
        """
        self.set_task_setting(text, key=key)
        self.refresh_script_list(update_status=False)

    def add_script_file_path_controls(self, parent_layout):
        """Adds the external Python script path controls.

        Args:
            parent_layout (QLayout): Layout that receives the controls.

        Returns:
            dict: Created widgets.
        """
        tooltip = "Python file to run for every incoming file."
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 5)
        layout.setSpacing(8)
        label = ui_qt.QtWidgets.QLabel("Script File:")
        attr_widget_base.configure_label_for_scaled_displays(label, minimum_width=140, word_wrap=True)
        label.setToolTip(tooltip)
        layout.addWidget(label)
        field = self.create_text_field(
            text=self.task.settings.get("script_path"),
            placeholder="{project-dir}/scripts/post_process.py",
            tooltip=tooltip,
        )
        info_button = ui_qt.QtWidgets.QPushButton()
        info_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_env_var))
        info_button.setToolTip("Get more information about the current path.")
        open_button = ui_qt.QtWidgets.QPushButton()
        open_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        open_button.setToolTip("Open the resolved script directory.")
        browse_button = ui_qt.QtWidgets.QPushButton()
        browse_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        browse_button.setToolTip("Browse for a Python script.")
        edit_button = ui_qt.QtWidgets.QPushButton()
        edit_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_templates_python))
        edit_button.setToolTip("Open this Python script for editing.")
        layout.addWidget(field)
        layout.addWidget(info_button)
        layout.addWidget(open_button)
        layout.addWidget(browse_button)
        layout.addWidget(edit_button)
        field.textChanged.connect(
            partial(
                self.set_path_field_value,
                field=field,
                setter=partial(self.set_task_setting, key="script_path"),
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
            lambda checked=False: self.open_python_script(self.task.resolve_script_path(self.project))
        )
        parent_layout.addLayout(layout)
        return {
            "layout": layout,
            "field": field,
            "info_button": info_button,
            "open_button": open_button,
            "browse_button": browse_button,
            "edit_button": edit_button,
        }

    def add_scripts_path_controls(self, parent_layout):
        """Adds the scripts folder path controls inside the batch container.

        Args:
            parent_layout (QLayout): Layout that receives the controls.

        Returns:
            dict: Created widgets.
        """
        tooltip = "Folder containing Python scripts to run in sorted order."
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 5)
        layout.setSpacing(8)
        label = ui_qt.QtWidgets.QLabel("Scripts Directory:")
        attr_widget_base.configure_label_for_scaled_displays(label, minimum_width=140, word_wrap=True)
        label.setToolTip(tooltip)
        layout.addWidget(label)
        field = self.create_text_field(
            text=self.task.settings.get("scripts_path"),
            placeholder="{project-dir}/scripts",
            tooltip=tooltip,
        )
        info_button = ui_qt.QtWidgets.QPushButton()
        info_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_env_var))
        info_button.setToolTip("Get more information about the current path.")
        open_button = ui_qt.QtWidgets.QPushButton()
        open_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        open_button.setToolTip("Open the resolved directory.")
        browse_button = ui_qt.QtWidgets.QPushButton()
        browse_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        browse_button.setToolTip("Browse for a concrete path.")
        layout.addWidget(field)
        layout.addWidget(info_button)
        layout.addWidget(open_button)
        layout.addWidget(browse_button)
        field.textChanged.connect(
            partial(
                self.set_path_field_value,
                field=field,
                setter=partial(self.set_task_setting, key="scripts_path"),
            )
        )
        field.textChanged.connect(lambda *args: self.refresh_scripts_if_directory_exists())
        info_button.clicked.connect(partial(self.open_env_var_feedback_dialog, field=field))
        open_button.clicked.connect(partial(self.open_resolved_path_directory, field=field))
        browse_button.clicked.connect(partial(self.open_path_dialog, field=field, dir_only=True))
        parent_layout.addLayout(layout)
        return {
            "layout": layout,
            "field": field,
            "info_button": info_button,
            "open_button": open_button,
            "browse_button": browse_button,
        }

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
        """Refreshes the batch script list when the configured directory exists."""
        if not self.scripts_path_widgets or not self.script_list_layout:
            return
        directory_path = self.get_resolved_field_path(self.scripts_path_widgets.get("field"))
        if os.path.isdir(directory_path):
            self.refresh_script_list(update_status=True)

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
        self.set_editor_font_size(self.font_size_slider.value())
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
        """Opens the configured legacy Python script for editing."""
        script_path = self.task.resolve_script_path(self.project)
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
