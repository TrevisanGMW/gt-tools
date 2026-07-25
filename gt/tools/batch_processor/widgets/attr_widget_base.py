"""
Batch Processor Attribute Widget Base
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_tasks as tasks
import gt.ui.file_dialog as ui_file_dialog
import gt.ui.python_output_view as ui_python_output_view
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_utils as ui_qt_utils
import gt.ui.qt_import as ui_qt
import gt.core.prefs as core_prefs
from functools import partial
import os


def get_icon_path(icon_name, fallback=None):
    """Gets a resource library icon path from an attribute name.

    Args:
        icon_name (str): Icon attribute name.
        fallback (str, optional): Fallback icon attribute name.

    Returns:
        str: Icon path.
    """
    if icon_name and hasattr(ui_res_lib.Icon, icon_name):
        return getattr(ui_res_lib.Icon, icon_name)
    if fallback and hasattr(ui_res_lib.Icon, fallback):
        return getattr(ui_res_lib.Icon, fallback)
    return ui_res_lib.Icon.rigger_module_generic


def configure_label_for_scaled_displays(label, minimum_width=None, word_wrap=False):
    """Makes labels less likely to clip on scaled or remote displays.

    Args:
        label (QLabel): Label to configure.
        minimum_width (int, optional): Minimum label width.
        word_wrap (bool, optional): Whether long labels can wrap.

    Returns:
        QLabel: Configured label.
    """
    label.setWordWrap(bool(word_wrap))
    if minimum_width is not None:
        label.setMinimumWidth(int(minimum_width))
    minimum_height = label.fontMetrics().lineSpacing() + 10
    if word_wrap:
        minimum_height = max(minimum_height, label.fontMetrics().lineSpacing() * 2 + 12)
    label.setMinimumHeight(minimum_height)
    label.setSizePolicy(ui_qt.QtLib.SizePolicy.Minimum, ui_qt.QtLib.SizePolicy.Preferred)
    label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignLeft | ui_qt.QtLib.AlignmentFlag.AlignVCenter)
    label.setContentsMargins(0, 2, 0, 2)
    return label


class AttrWidgetBase(ui_qt.QtWidgets.QWidget):
    """Base widget for batch project and task attribute panels."""

    def __init__(self, parent=None, project=None, refresh_parent_func=None, controller=None, *args, **kwargs):
        """Initializes the base attribute widget.

        Args:
            parent (QWidget, optional): Parent widget.
            project (BatchProcessorModel, optional): Project model.
            refresh_parent_func (callable, optional): Function used to refresh the parent UI.
            controller (BatchProcessorController, optional): Owning controller.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(parent, *args, **kwargs)
        self.project = project
        self.refresh_parent_func = refresh_parent_func
        self.controller = controller
        self.content_layout = ui_qt.QtWidgets.QVBoxLayout()
        self.content_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)
        self.content_layout.setSpacing(5)

        self.scroll_content_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        self.scroll_content_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)
        self.scroll_content_layout.setSpacing(5)
        self.scroll_content_layout.addLayout(self.content_layout)

    def add_widget_separator_line(self, label_text="", parent_layout=None, tooltip=None):
        """Creates a separator line matching the Auto Rigger attribute panel style.

        Args:
            label_text (str, optional): Label text to show in the separator.
            parent_layout (QLayout, optional): Layout that receives the separator.
            tooltip (str, optional): Tooltip to assign to separator widgets.
        """
        target_layout = parent_layout or self.content_layout
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 5)
        target_layout.addLayout(layout)

        left_line = ui_qt.QtWidgets.QFrame()
        left_line.setFrameShape(ui_qt.QtWidgets.QFrame.HLine)
        left_line.setFrameShadow(ui_qt.QtWidgets.QFrame.Sunken)
        layout.addWidget(left_line, 1)

        if label_text:
            label = ui_qt.QtWidgets.QLabel(label_text)
            configure_label_for_scaled_displays(label)
            label.setStyleSheet("color: grey; padding: 0 8px;")
            label.setToolTip(tooltip or label_text)
            layout.addWidget(label, 0)

        right_line = ui_qt.QtWidgets.QFrame()
        right_line.setFrameShape(ui_qt.QtWidgets.QFrame.HLine)
        right_line.setFrameShadow(ui_qt.QtWidgets.QFrame.Sunken)
        layout.addWidget(right_line, 1)

        if tooltip:
            left_line.setToolTip(tooltip)
            right_line.setToolTip(tooltip)

    def add_collapsible_section(self, label_text, collapsed=False, state_setter=None, tooltip=None):
        """Adds a collapsible section to the content layout.

        Args:
            label_text (str): Section header text.
            collapsed (bool, optional): Whether the section starts collapsed.
            state_setter (callable, optional): Function called with the collapsed state when toggled.
            tooltip (str, optional): Tooltip assigned to the section header.

        Returns:
            dict: Section widgets and content layout.
        """
        header_layout = ui_qt.QtWidgets.QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 5)
        self.content_layout.addLayout(header_layout)

        left_line = ui_qt.QtWidgets.QFrame()
        left_line.setFrameShape(ui_qt.QtWidgets.QFrame.HLine)
        left_line.setFrameShadow(ui_qt.QtWidgets.QFrame.Sunken)
        header_layout.addWidget(left_line, 1)

        toggle_button = ui_qt.QtWidgets.QPushButton(label_text)
        toggle_button.setCheckable(True)
        toggle_button.setChecked(not bool(collapsed))
        toggle_button.setMinimumHeight(28)
        toggle_button.setToolTip(tooltip or label_text)
        header_layout.addWidget(toggle_button, 0)

        right_line = ui_qt.QtWidgets.QFrame()
        right_line.setFrameShape(ui_qt.QtWidgets.QFrame.HLine)
        right_line.setFrameShadow(ui_qt.QtWidgets.QFrame.Sunken)
        header_layout.addWidget(right_line, 1)

        container = ui_qt.QtWidgets.QWidget()
        container_layout = ui_qt.QtWidgets.QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        container_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)
        self.content_layout.addWidget(container)

        def refresh_collapsed_state(store_state=False):
            """Refreshes the collapsible section visibility and persisted state.

            Args:
                store_state (bool, optional): Whether to call the state setter.
            """
            is_expanded = toggle_button.isChecked()
            container.setVisible(is_expanded)
            if is_expanded:
                toggle_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_up_arrow))
            else:
                toggle_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_down_arrow))
            if store_state and callable(state_setter):
                state_setter(not is_expanded)

        toggle_button.clicked.connect(lambda *args: refresh_collapsed_state(store_state=True))
        refresh_collapsed_state(store_state=False)
        if tooltip:
            left_line.setToolTip(tooltip)
            right_line.setToolTip(tooltip)
            container.setToolTip(tooltip)
        return {
            "button": toggle_button,
            "container": container,
            "content_layout": container_layout,
        }

    def call_parent_refresh(self):
        """Queues the parent refresh function when one was provided.

        Deferring the refresh allows the active Qt signal or event to finish before
        a parent rebuild can delete the widget that emitted it.
        """
        if callable(self.refresh_parent_func):
            ui_qt.QtCore.QTimer.singleShot(0, self.refresh_parent_func)

    def add_labeled_layout(self, label_text, label_width=110, tooltip=None, parent_layout=None):
        """Adds a horizontal row with a fixed-width label.

        Args:
            label_text (str): Label text.
            label_width (int, optional): Label width.
            tooltip (str, optional): Tooltip assigned to the label.
            parent_layout (QLayout, optional): Layout that receives the new row.

        Returns:
            QHBoxLayout: Created layout.
        """
        target_layout = parent_layout or self.content_layout
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 5)
        layout.setSpacing(8)
        label = ui_qt.QtWidgets.QLabel("{0}:".format(label_text))
        configure_label_for_scaled_displays(label, minimum_width=label_width, word_wrap=False)
        label.setMinimumHeight(35)
        label.setToolTip(tooltip or label_text)
        layout.addWidget(label)
        target_layout.addLayout(layout)
        return layout

    def create_text_field(self, text="", placeholder="", tooltip=None):
        """Creates a standard expanding text field.

        Args:
            text (str, optional): Initial text.
            placeholder (str, optional): Placeholder text.
            tooltip (str, optional): Tooltip text.

        Returns:
            ConfirmableQLineEdit: Created field.
        """
        field = ui_qt_utils.ConfirmableQLineEdit()
        field.setMinimumHeight(35)
        field.setMinimumWidth(1)
        field.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        field.setText(str(text or ""))
        field.setPlaceholderText(str(placeholder or ""))
        field.setToolTip(tooltip or placeholder or str(text or ""))
        return field

    def add_text_field(
        self,
        label_text,
        value,
        setter,
        placeholder="",
        tooltip=None,
        label_width=140,
        parent_layout=None,
    ):
        """Adds a text field row.

        Args:
            label_text (str): Label text.
            value (str): Initial value.
            setter (callable): Function that receives the new field text.
            placeholder (str, optional): Placeholder text.
            tooltip (str, optional): Tooltip text.
            label_width (int, optional): Label width.
            parent_layout (QLayout, optional): Layout that receives the row.

        Returns:
            QLineEdit: Created text field.
        """
        layout = self.add_labeled_layout(
            label_text,
            label_width=label_width,
            tooltip=tooltip,
            parent_layout=parent_layout,
        )
        field = self.create_text_field(text=value, placeholder=placeholder, tooltip=tooltip)
        layout.addWidget(field)
        field.textChanged.connect(lambda value_text: setter(value_text))
        return field

    def add_path_template_field(
        self,
        label_text,
        value,
        setter,
        placeholder="",
        tooltip=None,
        dir_only=False,
        file_filter="All Files (*);;",
        return_widgets=False,
        parent_layout=None,
        convert_to_project_relative=True,
    ):
        """Adds a path-template field with an optional browse button.

        Args:
            label_text (str): Label text.
            value (str): Initial value.
            setter (callable): Function that receives the new field text.
            placeholder (str, optional): Placeholder text.
            tooltip (str, optional): Tooltip text.
            dir_only (bool, optional): Whether the dialog should select directories.
            file_filter (str, optional): File dialog filter.
            return_widgets (bool, optional): Whether to return all created path widgets.
            parent_layout (QLayout, optional): Layout that receives the row.
            convert_to_project_relative (bool, optional): Whether absolute paths under {project-dir} should convert.

        Returns:
            QLineEdit or dict: Created text field, or all created widgets.
        """
        layout = self.add_labeled_layout(label_text, tooltip=tooltip, parent_layout=parent_layout)
        field = self.create_text_field(text=value, placeholder=placeholder, tooltip=tooltip)
        info_button = ui_qt.QtWidgets.QPushButton()
        info_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_env_var))
        info_button.setToolTip("Get more information about the current path.")
        open_button = ui_qt.QtWidgets.QPushButton()
        open_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open_external))
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
                setter=setter,
                convert_to_project_relative=convert_to_project_relative,
            )
        )
        info_button.clicked.connect(partial(self.open_env_var_feedback_dialog, field=field))
        open_button.clicked.connect(partial(self.open_resolved_path_directory, field=field))
        browse_button.clicked.connect(
            partial(
                self.open_path_dialog,
                field=field,
                dir_only=dir_only,
                file_filter=file_filter,
                convert_to_project_relative=convert_to_project_relative,
            )
        )
        if return_widgets:
            return {
                "layout": layout,
                "field": field,
                "info_button": info_button,
                "open_button": open_button,
                "browse_button": browse_button,
            }
        return field

    def set_path_field_value(self, value, field, setter, convert_to_project_relative=True):
        """Stores a path field value after applying optional project-relative conversion.

        Args:
            value (str): New field value.
            field (QLineEdit): Field being edited.
            setter (callable): Function that receives the stored value.
            convert_to_project_relative (bool, optional): Whether to convert absolute project paths.
        """
        stored_value = value
        if convert_to_project_relative:
            stored_value = self.path_to_project_relative(value)
        if stored_value != value and field:
            field.blockSignals(True)
            field.setText(stored_value)
            field.blockSignals(False)
        setter(stored_value)

    def open_env_var_feedback_dialog(self, field):
        """Opens a dialog showing the resolved path represented by a field.

        Args:
            field (QLineEdit): Path field to inspect.
        """
        path = field.text()
        parsed_path = self.get_resolved_field_path(field)
        exists = os.path.exists(parsed_path)
        is_dir = os.path.isdir(parsed_path)
        is_file = os.path.isfile(parsed_path)
        info_lines = self.build_path_information_lines(
            parsed_path=parsed_path,
            exists=exists,
            is_dir=is_dir,
            is_file=is_file,
        )
        file_paths = tasks.list_files_from_path(parsed_path, include_subdirectories=True)
        self.show_path_list(
            title="Resolved Input Files",
            file_paths=file_paths,
            header_lines=info_lines,
        )
        self.emit_status_message(
            'Resolved path information for: "{0}" ({1} file(s)).'.format(path, len(file_paths))
        )

    @staticmethod
    def build_path_information_lines(parsed_path, exists=False, is_dir=False, is_file=False):
        """Builds path information lines for dialogs and list previews.

        Args:
            parsed_path (str): Resolved path value.
            exists (bool, optional): Whether the path exists.
            is_dir (bool, optional): Whether the path is a directory.
            is_file (bool, optional): Whether the path is a file.

        Returns:
            list: Text lines describing the path.
        """
        return [
            "Parsed Path:",
            str(parsed_path or ""),
            "",
            "Exists: {0}".format(bool(exists)),
            "Directory: {0}".format(bool(is_dir)),
            "File: {0}".format(bool(is_file)),
        ]

    def show_path_list(self, title, file_paths, header_lines=None):
        """Shows a list of paths in a text output window.

        Args:
            title (str): Window title.
            file_paths (list): Paths to display.
            header_lines (list, optional): Lines to show before the path count.
        """
        output_window = ui_python_output_view.PythonOutputView(parent=self, editable=False)
        output_window.setWindowTitle(title)
        output_lines = []
        if header_lines:
            output_lines.extend([str(line) for line in header_lines])
            output_lines.append("")
        output_lines.extend(["Count: {0}".format(len(file_paths or [])), ""])
        output_lines.extend(file_paths or ["No files found."])
        output_window.set_python_output_text("\n".join(output_lines))
        output_window.show()

    def open_resolved_path_directory(self, field):
        """Attempts to open the resolved directory represented by a field.

        Args:
            field (QLineEdit): Path field to inspect.
        """
        if not str(field.text() or "").strip():
            self.emit_status_message(
                "Warning: Unable to open directory because the path field is empty.",
                status="warning",
            )
            return
        path = self.get_resolved_field_path(field)
        directory_path = path
        if os.path.isfile(directory_path):
            directory_path = os.path.dirname(directory_path)
        if not os.path.isdir(directory_path):
            message = "Target folder does not exist:\n{0}".format(directory_path or path or "<empty>")
            self.open_warning_dialog("Target Folder Missing", message)
            self.emit_status_message(
                "Warning: Unable to open directory because the path does not exist: {0}".format(directory_path),
                status="warning",
            )
            return
        try:
            os.startfile(directory_path)
            self.emit_status_message("Opened directory: {0}".format(directory_path))
        except AttributeError:
            import subprocess

            subprocess.Popen(["xdg-open", directory_path])
            self.emit_status_message("Opened directory: {0}".format(directory_path))
        except Exception as exception:
            self.emit_status_message("Unable to open directory: {0}".format(exception))

    def add_checkbox(self, label_text, value, setter, layout=None, tooltip=None):
        """Adds a checkbox row.

        Args:
            label_text (str): Label text.
            value (bool): Initial checked state.
            setter (callable): Function that receives the new checked state.
            layout (QLayout, optional): Existing layout that receives the controls.
            tooltip (str, optional): Tooltip text.

        Returns:
            QCheckBox: Created checkbox.
        """
        target_layout = layout or self.add_labeled_layout(label_text, tooltip=tooltip)
        if layout:
            label = ui_qt.QtWidgets.QLabel("{0}:".format(label_text))
            configure_label_for_scaled_displays(label)
            label.setToolTip(tooltip or label_text)
            target_layout.addWidget(label)
        checkbox = ui_qt.QtWidgets.QCheckBox()
        checkbox.setMinimumHeight(checkbox.sizeHint().height() + 2)
        checkbox.setChecked(bool(value))
        checkbox.setToolTip(tooltip or label_text)
        target_layout.addWidget(checkbox)
        checkbox.stateChanged.connect(lambda *args: setter(checkbox.isChecked()))
        return checkbox

    def add_spin_box(self, label_text, value, setter, minimum=0, maximum=9999, tooltip=None, parent_layout=None):
        """Adds an integer spin box row.

        Args:
            label_text (str): Label text.
            value (int): Initial value.
            setter (callable): Function that receives the new integer value.
            minimum (int, optional): Minimum value.
            maximum (int, optional): Maximum value.
            tooltip (str, optional): Tooltip text.
            parent_layout (QLayout, optional): Layout that receives the row.

        Returns:
            QSpinBox: Created spin box.
        """
        layout = self.add_labeled_layout(label_text, tooltip=tooltip, parent_layout=parent_layout)
        spin_box = ui_qt.QtWidgets.QSpinBox()
        spin_box.setRange(int(minimum), int(maximum))
        spin_box.setValue(int(value or 0))
        spin_box.setMinimumHeight(35)
        spin_box.setToolTip(tooltip or label_text)
        layout.addWidget(spin_box)
        spin_box.valueChanged.connect(lambda value_int: setter(value_int))
        return spin_box

    def add_combo_box(self, label_text, value, values, setter, tooltip=None, parent_layout=None):
        """Adds a combo box row.

        Args:
            label_text (str): Label text.
            value (str): Current value.
            values (list): Available text values.
            setter (callable): Function that receives the new text value.
            tooltip (str, optional): Tooltip text.
            parent_layout (QLayout, optional): Layout that receives the row.

        Returns:
            QComboBox: Created combo box.
        """
        layout = self.add_labeled_layout(label_text, tooltip=tooltip, parent_layout=parent_layout)
        combo_box = ui_qt.QtWidgets.QComboBox()
        combo_box.setMinimumHeight(35)
        combo_box.setMinimumWidth(1)
        combo_box.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        combo_box.setToolTip(tooltip or label_text)
        for item in values:
            combo_box.addItem(str(item))
        if value and combo_box.findText(str(value)) == -1:
            combo_box.addItem(str(value))
        index = combo_box.findText(str(value or ""))
        if index >= 0:
            combo_box.setCurrentIndex(index)
        layout.addWidget(combo_box)
        combo_box.currentTextChanged.connect(lambda value_text: setter(value_text))
        return combo_box

    def add_radio_button_group(self, label_text, value, values, setter, tooltip=None, parent_layout=None):
        """Adds a horizontal radio button group.

        Args:
            label_text (str): Label text.
            value (str): Current selected value.
            values (list): Available radio button values.
            setter (callable): Function that receives the selected value.
            tooltip (str, optional): Tooltip text.
            parent_layout (QLayout, optional): Layout that receives the row.

        Returns:
            dict: Radio buttons keyed by value.
        """
        layout = self.add_labeled_layout(label_text, tooltip=tooltip, parent_layout=parent_layout)
        buttons = {}

        def on_radio_toggled(is_checked, radio_value):
            """Handles radio button selection changes.

            Args:
                is_checked (bool): Whether the radio button is now checked.
                radio_value (str): Value represented by the radio button.
            """
            if is_checked:
                setter(str(radio_value))

        for item in values:
            radio_button = ui_qt.QtWidgets.QRadioButton(str(item))
            radio_button.setMinimumHeight(radio_button.sizeHint().height() + 2)
            radio_button.setToolTip(tooltip or label_text)
            layout.addWidget(radio_button)
            buttons[str(item)] = radio_button
            radio_button.toggled.connect(partial(on_radio_toggled, radio_value=item))
            if str(item) == str(value):
                radio_button.setChecked(True)
        if values and str(value) not in buttons:
            buttons[str(values[0])].setChecked(True)
            setter(str(values[0]))
        return buttons

    def open_warning_dialog(self, title, message):
        """Opens a warning dialog.

        Args:
            title (str): Dialog title.
            message (str): Warning message.
        """
        message_box = ui_qt.QtWidgets.QMessageBox(self)
        try:
            message_box.setIcon(ui_qt.QtWidgets.QMessageBox.Warning)
            message_box.setStandardButtons(ui_qt.QtWidgets.QMessageBox.Ok)
        except AttributeError:
            message_box.setIcon(ui_qt.QtWidgets.QMessageBox.Icon.Warning)
            message_box.setStandardButtons(ui_qt.QtWidgets.QMessageBox.StandardButton.Ok)
        message_box.setWindowTitle(title)
        message_box.setText(message)
        self.exec_dialog(message_box)

    def add_text_area(self, label_text, value, setter, placeholder="", tooltip=None, parent_layout=None):
        """Adds a multi-line text area row.

        Args:
            label_text (str): Label text.
            value (str): Initial text.
            setter (callable): Function that receives text when edited.
            placeholder (str, optional): Placeholder text.
            tooltip (str, optional): Tooltip text.
            parent_layout (QLayout, optional): Layout that receives the row.

        Returns:
            QTextEdit: Created text area.
        """
        target_layout = parent_layout or self.content_layout
        self.add_widget_separator_line(label_text=label_text, tooltip=tooltip, parent_layout=target_layout)
        text_area = ui_qt.QtWidgets.QTextEdit()
        text_area.setMinimumHeight(85)
        text_area.setMinimumWidth(1)
        text_area.setPlainText(str(value or ""))
        text_area.setPlaceholderText(str(placeholder or ""))
        text_area.setToolTip(tooltip or placeholder or label_text)
        text_area.textChanged.connect(lambda: setter(text_area.toPlainText()))
        target_layout.addWidget(text_area)
        return text_area

    def open_path_dialog(
        self,
        field,
        dir_only=False,
        file_filter="All Files (*);;",
        multiple_files=False,
        convert_to_project_relative=True,
    ):
        """Opens a path dialog and writes the selected path to a field.

        Args:
            field (QLineEdit): Field to update.
            dir_only (bool, optional): Whether the dialog should select directories.
            file_filter (str, optional): File dialog filter.
            multiple_files (bool, optional): Whether multiple files can be selected.
            convert_to_project_relative (bool, optional): Whether selected paths should convert to project-relative.
        """
        current_path = self.get_resolved_field_path(field)
        starting_directory = self.get_dialog_starting_directory(current_path)
        file_path = ui_file_dialog.file_dialog(
            parent=self,
            write_mode=False,
            starting_directory=starting_directory,
            file_filter=file_filter,
            dir_only=dir_only,
            ok_caption="Select",
            cancel_caption="Cancel",
            multiple_files=multiple_files,
        )
        if not file_path:
            return
        if isinstance(file_path, list):
            if convert_to_project_relative:
                file_path = "\n".join([self.path_to_project_relative(path) for path in file_path])
            else:
                file_path = "\n".join([tasks.normalize_path(path) for path in file_path])
        elif convert_to_project_relative:
            file_path = self.path_to_project_relative(file_path)
        else:
            file_path = tasks.normalize_path(file_path)
        field.setText(file_path)

    def get_dialog_starting_directory(self, current_path=None):
        """Gets a useful starting directory for path dialogs.

        Args:
            current_path (str, optional): Current resolved path value.

        Returns:
            str or None: Existing directory to use as dialog start.
        """
        if current_path:
            current_path = os.path.abspath(os.path.expanduser(str(current_path)))
            if os.path.isdir(current_path):
                return current_path
            parent_path = os.path.dirname(current_path)
            if parent_path and os.path.isdir(parent_path):
                return parent_path
        if self.project and hasattr(self.project, "get_project_dir"):
            project_dir = self.project.get_project_dir()
            if project_dir and os.path.isdir(project_dir):
                return project_dir
        return None

    def get_resolved_field_path(self, field):
        """Gets a resolved path from a text field.

        Args:
            field (QLineEdit): Field to resolve.

        Returns:
            str: Resolved path.
        """
        if not self.project:
            return field.text()
        task = self.get_context_task()
        task_index = None
        if task and hasattr(self.project, "get_task_environment_index"):
            task_index = self.project.get_task_environment_index(task)
        return self.project.resolve_template_path(field.text(), task=task, task_index=task_index)

    def get_context_task(self):
        """Gets the task associated with this widget, when available.

        Returns:
            BatchTask or None: Context task.
        """
        return getattr(self, "task", None)

    def emit_status_message(self, message, status="info"):
        """Sends a status/log message through the owning controller when possible.

        Args:
            message (str): Message to emit.
            status (str, optional): Status level used for the bottom status field.
        """
        try:
            controller = self.get_batch_controller()
            if controller and hasattr(controller, "log_status"):
                controller.log_status(message, status=status)
        except Exception:
            pass

    def get_batch_controller(self):
        """Gets the owning batch processor controller.

        Returns:
            BatchProcessorController or None: Controller when it can be found.
        """
        controller = getattr(self, "controller", None)
        if controller:
            return controller
        try:
            window = self.window()
            controller = getattr(window, "controller", None)
            if controller:
                self.controller = controller
                return controller
        except Exception:
            pass
        parent = self.parent()
        while parent:
            controller = getattr(parent, "controller", None)
            if controller:
                self.controller = controller
                return controller
            try:
                parent = parent.parent()
            except Exception:
                parent = None
        return None

    @staticmethod
    def exec_dialog(dialog):
        """Executes a Qt dialog using the binding-compatible method name.

        Args:
            dialog (QDialog): Dialog to execute.

        Returns:
            object: Dialog execution result.
        """
        exec_method = getattr(dialog, "exec_", None)
        if not exec_method:
            exec_method = getattr(dialog, "exec")
        return exec_method()

    def path_to_project_relative(self, path):
        """Converts a path to a project-relative path when possible.

        Args:
            path (str): Path to convert.

        Returns:
            str: Relative or original path.
        """
        if not self.project or not path:
            return path
        if not self.should_convert_absolute_paths_to_project_relative():
            return path
        try:
            project_dir = self.project.get_project_dir()
            if not project_dir:
                return path
            absolute_path = tasks.normalize_path(path)
            project_dir = tasks.normalize_path(project_dir)
            if not os.path.isabs(absolute_path):
                return path
            common_path = os.path.commonpath([project_dir, absolute_path])
            if os.path.normcase(common_path) != os.path.normcase(project_dir):
                return path
            relative_path = os.path.relpath(absolute_path, project_dir)
            if relative_path == ".":
                return "{project-dir}"
            is_inside_project = not relative_path.startswith(os.pardir + os.sep)
            is_inside_project = is_inside_project and relative_path != os.pardir
            if is_inside_project and not os.path.isabs(relative_path):
                return "{{project-dir}}/{0}".format(relative_path.replace("\\", "/"))
        except Exception:
            pass
        return path

    def should_convert_absolute_paths_to_project_relative(self):
        """Checks the global preference for automatic project-relative path conversion.

        Returns:
            bool: True when browsed absolute paths should become {project-dir} templates.
        """
        try:
            controller = self.get_batch_controller()
            if controller and hasattr(controller, "get_convert_abs_paths_to_relative"):
                return controller.get_convert_abs_paths_to_relative()
        except Exception:
            pass
        try:
            preferences = core_prefs.Prefs(constants.Project.PREFS_FILENAME)
            default_value = preferences.get_bool(key="on_set_path_abs_to_relative", default=True)
            return preferences.get_bool(
                key=constants.Project.PREFS_KEY_CONVERT_ABS_PATHS_TO_RELATIVE,
                default=default_value,
            )
        except Exception:
            return True

    @staticmethod
    def split_list_text(text):
        """Converts comma or newline separated text into a list.

        Args:
            text (str): Text to parse.

        Returns:
            list: Parsed values.
        """
        if not text:
            return []
        normalized = str(text).replace(",", "\n")
        return [line.strip() for line in normalized.splitlines() if line.strip()]
