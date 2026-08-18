"""Qt view for the GT Tools Startup Scripts tool."""

from gt.tools.batch_processor.widgets.inline_python_editor import InlinePythonEditorWidget
from gt.ui.qt_utils import MayaWindowMeta
import gt.ui.qt_import as ui_qt
import gt.ui.qt_utils as qt_utils
import gt.ui.resource_library as ui_res_lib
import os


class StartupScriptsView(metaclass=MayaWindowMeta):
    """Presents editable Python sources and their Maya startup triggers."""

    def __init__(self, parent=None, controller=None, version=None):
        """Initializes the Startup Scripts window.

        Args:
            parent (QWidget, optional): Parent Maya widget.
            controller (StartupScriptsController, optional): Owning controller.
            version (str, optional): Version text appended to the title.
        """
        super().__init__(parent=parent)
        self.setObjectName("StartupScripts")
        self.controller = controller
        self.is_loading = False
        self.sample_load_callback = None
        self.sample_menu = ui_qt.QtWidgets.QMenu(self)

        title = "Startup Scripts"
        if version:
            title += f" - (v{version})"
        self.setWindowTitle(title)
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_startup_scripts))
        self.setMinimumSize(900, 620)
        self.resize(1080, 760)

        self.script_list = None
        self.add_script_button = None
        self.duplicate_script_button = None
        self.move_up_button = None
        self.move_down_button = None
        self.remove_script_button = None
        self.details_widget = None
        self.name_field = None
        self.enabled_checkbox = None
        self.run_mode_combo = None
        self.print_message_checkbox = None
        self.inline_editor = None
        self.external_files_list = None
        self.script_directories_list = None
        self.add_external_file_button = None
        self.remove_external_file_button = None
        self.add_directory_button = None
        self.remove_directory_button = None
        self.examples_button = None
        self.run_selected_button = None
        self.status_label = None
        self._build_widgets()

    def _build_widgets(self):
        """Builds the Startup Scripts window controls."""
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        description_label = ui_qt.QtWidgets.QLabel(
            "Configure Python to run after GT Tools loads. Sources run inline code first, then "
            "external files, then every Python file in configured directories."
        )
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: #BDBDBD;")
        main_layout.addWidget(description_label)

        splitter = ui_qt.QtWidgets.QSplitter(ui_qt.QtLib.Orientation.Horizontal, self)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_script_list_widget())
        splitter.addWidget(self._build_details_widget())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([250, 800])
        main_layout.addWidget(splitter, 1)

        footer_layout = ui_qt.QtWidgets.QHBoxLayout()
        footer_layout.setContentsMargins(0, 0, 0, 0)
        self.status_label = ui_qt.QtWidgets.QLabel("Create or select a startup script to configure it.")
        self.status_label.setWordWrap(True)
        footer_layout.addWidget(self.status_label, 1)
        self.run_selected_button = ui_qt.QtWidgets.QPushButton("Run Selected")
        self.run_selected_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.dev_code))
        self.run_selected_button.setToolTip(
            "Runs all available sources in the selected configuration now. "
            "This ignores its configured startup trigger."
        )
        footer_layout.addWidget(self.run_selected_button)
        main_layout.addLayout(footer_layout)
        qt_utils.center_window(self)

    def _build_script_list_widget(self):
        """Builds the configuration-list panel.

        Returns:
            QWidget: Left-side configuration-list widget.
        """
        container = ui_qt.QtWidgets.QWidget(self)
        layout = ui_qt.QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(6)
        title_label = ui_qt.QtWidgets.QLabel("Startup Configurations")
        title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(title_label)

        self.script_list = ui_qt.QtWidgets.QListWidget()
        self.script_list.setToolTip("Configurations run from top to bottom for the selected trigger.")
        layout.addWidget(self.script_list, 1)

        first_row = ui_qt.QtWidgets.QHBoxLayout()
        self.add_script_button = self._create_button("Add", ui_res_lib.Icon.ui_add, "Add a startup script.")
        self.duplicate_script_button = self._create_button(
            "Duplicate", ui_res_lib.Icon.ui_copy_text, "Duplicate the selected startup script."
        )
        first_row.addWidget(self.add_script_button)
        first_row.addWidget(self.duplicate_script_button)
        layout.addLayout(first_row)

        second_row = ui_qt.QtWidgets.QHBoxLayout()
        self.move_up_button = self._create_button(
            "Up", ui_res_lib.Icon.rigger_action_up_arrow, "Move selected script up."
        )
        self.move_down_button = self._create_button(
            "Down", ui_res_lib.Icon.rigger_action_down_arrow, "Move selected script down."
        )
        self.remove_script_button = self._create_button(
            "Remove", ui_res_lib.Icon.ui_delete, "Remove the selected startup script."
        )
        second_row.addWidget(self.move_up_button)
        second_row.addWidget(self.move_down_button)
        second_row.addWidget(self.remove_script_button)
        layout.addLayout(second_row)
        return container

    def _build_details_widget(self):
        """Builds the selected-configuration editor.

        Returns:
            QWidget: Right-side editor widget.
        """
        self.details_widget = ui_qt.QtWidgets.QWidget(self)
        layout = ui_qt.QtWidgets.QVBoxLayout(self.details_widget)
        layout.setContentsMargins(6, 0, 0, 0)
        layout.setSpacing(8)

        settings_group = ui_qt.QtWidgets.QGroupBox("Configuration")
        settings_layout = ui_qt.QtWidgets.QGridLayout(settings_group)
        settings_layout.setColumnStretch(1, 1)
        self.name_field = ui_qt.QtWidgets.QLineEdit()
        self.name_field.setPlaceholderText("Startup Script")
        self.name_field.setToolTip("Name shown in the configuration list and startup output.")
        self.enabled_checkbox = ui_qt.QtWidgets.QCheckBox("Enabled")
        self.enabled_checkbox.setToolTip("Disabled configurations never execute.")
        self.run_mode_combo = ui_qt.QtWidgets.QComboBox()
        self.run_mode_combo.setToolTip("Choose when this configuration runs.")
        self.print_message_checkbox = ui_qt.QtWidgets.QCheckBox("Print execution messages")
        self.print_message_checkbox.setToolTip(
            "Print clear output-window messages before and after this configuration runs."
        )
        settings_layout.addWidget(ui_qt.QtWidgets.QLabel("Name:"), 0, 0)
        settings_layout.addWidget(self.name_field, 0, 1)
        settings_layout.addWidget(self.enabled_checkbox, 0, 2)
        settings_layout.addWidget(ui_qt.QtWidgets.QLabel("Run when:"), 1, 0)
        settings_layout.addWidget(self.run_mode_combo, 1, 1)
        settings_layout.addWidget(self.print_message_checkbox, 1, 2)
        layout.addWidget(settings_group)

        inline_group = ui_qt.QtWidgets.QGroupBox("Inline Python")
        inline_layout = ui_qt.QtWidgets.QVBoxLayout(inline_group)
        inline_layout.setContentsMargins(8, 8, 8, 8)
        inline_header = ui_qt.QtWidgets.QHBoxLayout()
        inline_description = ui_qt.QtWidgets.QLabel(
            "Inline code is optional and is empty by default. It runs before external sources."
        )
        inline_description.setStyleSheet("color: #BDBDBD;")
        inline_description.setWordWrap(True)
        self.examples_button = self._create_button(
            "Examples ▼", ui_res_lib.Icon.ui_templates, "Load a packaged example into the inline editor."
        )
        inline_header.addWidget(inline_description, 1)
        inline_header.addWidget(self.examples_button)
        inline_layout.addLayout(inline_header)
        self.inline_editor = InlinePythonEditorWidget(
            parent=inline_group,
            owner=self,
            placeholder="Write Python code here, or load an example.",
            tooltip="Python run after GT Tools is fully loaded in Maya.",
        )
        inline_layout.addWidget(self.inline_editor, 1)
        layout.addWidget(inline_group, 1)

        source_layout = ui_qt.QtWidgets.QHBoxLayout()
        source_layout.addWidget(
            self._build_source_group(
                "External Python Files",
                "Files run after inline code in the order shown.",
                is_directory=False,
            ),
            1,
        )
        source_layout.addWidget(
            self._build_source_group(
                "Script Directories",
                "Every .py file in each folder and subfolder runs alphabetically after external files.",
                is_directory=True,
            ),
            1,
        )
        layout.addLayout(source_layout)
        return self.details_widget

    def _build_source_group(self, title, description, is_directory):
        """Builds one external source-list group.

        Args:
            title (str): Source group title.
            description (str): Short usage explanation.
            is_directory (bool): Whether this group selects directories.

        Returns:
            QGroupBox: Configured source group widget.
        """
        group = ui_qt.QtWidgets.QGroupBox(title)
        layout = ui_qt.QtWidgets.QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        description_label = ui_qt.QtWidgets.QLabel(description)
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: #BDBDBD;")
        layout.addWidget(description_label)
        source_list = ui_qt.QtWidgets.QListWidget()
        source_list.setMinimumHeight(90)
        source_list.setToolTip("Uncheck a source to retain it without running it.")
        layout.addWidget(source_list)
        button_layout = ui_qt.QtWidgets.QHBoxLayout()
        add_button = self._create_button(
            "Add Folder" if is_directory else "Add File",
            ui_res_lib.Icon.ui_open,
            "Choose a Python script directory." if is_directory else "Choose Python script files.",
        )
        remove_button = self._create_button(
            "Remove", ui_res_lib.Icon.ui_delete, "Remove the selected source."
        )
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        if is_directory:
            self.script_directories_list = source_list
            self.add_directory_button = add_button
            self.remove_directory_button = remove_button
        else:
            self.external_files_list = source_list
            self.add_external_file_button = add_button
            self.remove_external_file_button = remove_button
        return group

    @staticmethod
    def _create_button(label, icon_path, tooltip):
        """Creates a consistently configured tool button.

        Args:
            label (str): Button text.
            icon_path (str): Resource-library icon path.
            tooltip (str): Help text shown for the button.

        Returns:
            QPushButton: Configured button.
        """
        button = ui_qt.QtWidgets.QPushButton(label)
        button.setIcon(ui_qt.QtGui.QIcon(icon_path))
        button.setToolTip(tooltip)
        return button

    def set_run_modes(self, run_modes):
        """Populates the available configuration triggers.

        Args:
            run_modes (list): Ordered trigger display values.
        """
        self.run_mode_combo.blockSignals(True)
        self.run_mode_combo.clear()
        self.run_mode_combo.addItems(run_modes or [])
        self.run_mode_combo.blockSignals(False)

    def set_scripts(self, scripts, selected_script_id=""):
        """Rebuilds the configuration list while retaining the selected script.

        Args:
            scripts (list): Ordered script configurations.
            selected_script_id (str, optional): Identifier to select after rebuilding.
        """
        self.script_list.blockSignals(True)
        self.script_list.clear()
        selected_row = -1
        for index, script in enumerate(scripts if isinstance(scripts, list) else []):
            name = script.get("name") or f"Startup Script {index + 1}"
            if not script.get("enabled", True):
                name += " (Disabled)"
            item = ui_qt.QtWidgets.QListWidgetItem(name)
            item.setData(ui_qt.QtLib.ItemDataRole.UserRole, script.get("id"))
            item.setToolTip(script.get("run_mode") or "")
            self.script_list.addItem(item)
            if script.get("id") == selected_script_id:
                selected_row = index
        if selected_row < 0 and self.script_list.count():
            selected_row = 0
        self.script_list.setCurrentRow(selected_row)
        self.script_list.blockSignals(False)

    def get_current_script_id(self):
        """Gets the selected startup-script identifier.

        Returns:
            str: Selected stable identifier, or an empty string.
        """
        item = self.script_list.currentItem()
        if not item:
            return ""
        return item.data(ui_qt.QtLib.ItemDataRole.UserRole) or ""

    def set_script_details(self, script):
        """Loads one configuration into the editable controls.

        Args:
            script (dict or None): Script configuration to display.
        """
        self.is_loading = True
        has_script = isinstance(script, dict)
        self.details_widget.setEnabled(has_script)
        if not has_script:
            self.is_loading = False
            return
        self.name_field.blockSignals(True)
        self.enabled_checkbox.blockSignals(True)
        self.run_mode_combo.blockSignals(True)
        self.print_message_checkbox.blockSignals(True)
        self.inline_editor.python_edit.blockSignals(True)
        self.inline_editor.font_size_slider.blockSignals(True)
        self.external_files_list.blockSignals(True)
        self.script_directories_list.blockSignals(True)

        self.name_field.setText(script.get("name") or "")
        self.enabled_checkbox.setChecked(script.get("enabled", True))
        self.run_mode_combo.setCurrentText(script.get("run_mode") or "")
        self.print_message_checkbox.setChecked(script.get("print_execution_message", True))
        self.inline_editor.set_text(script.get("script_text") or "")
        self.inline_editor.font_size_slider.setValue(int(script.get("font_size", 14) or 14))
        self.inline_editor.set_editor_font_size(int(script.get("font_size", 14) or 14))
        self._set_source_entries(self.external_files_list, script.get("external_files", []))
        self._set_source_entries(self.script_directories_list, script.get("script_directories", []))

        self.name_field.blockSignals(False)
        self.enabled_checkbox.blockSignals(False)
        self.run_mode_combo.blockSignals(False)
        self.print_message_checkbox.blockSignals(False)
        self.inline_editor.python_edit.blockSignals(False)
        self.inline_editor.font_size_slider.blockSignals(False)
        self.external_files_list.blockSignals(False)
        self.script_directories_list.blockSignals(False)
        self.is_loading = False

    @staticmethod
    def _set_source_entries(source_list, entries):
        """Populates a checkable source list from source-entry dictionaries.

        Args:
            source_list (QListWidget): Destination list widget.
            entries (list): Source dictionaries containing paths and enabled states.
        """
        source_list.clear()
        for entry in entries if isinstance(entries, list) else []:
            if not isinstance(entry, dict):
                continue
            path = entry.get("path") or ""
            item = ui_qt.QtWidgets.QListWidgetItem(path)
            item.setToolTip(path)
            item.setData(ui_qt.QtLib.ItemDataRole.UserRole, dict(entry))
            item.setFlags(item.flags() | ui_qt.QtLib.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                ui_qt.QtLib.CheckState.Checked
                if entry.get("enabled", True)
                else ui_qt.QtLib.CheckState.Unchecked
            )
            source_list.addItem(item)

    @staticmethod
    def get_source_entries(source_list):
        """Gets source entries from a checkable source list.

        Args:
            source_list (QListWidget): Source list to read.

        Returns:
            list: JSON-compatible source-entry dictionaries.
        """
        entries = []
        for index in range(source_list.count()):
            item = source_list.item(index)
            entry = item.data(ui_qt.QtLib.ItemDataRole.UserRole) or {"path": item.text()}
            entries.append(
                {
                    "path": str(entry.get("path") or item.text()),
                    "enabled": item.checkState() == ui_qt.QtLib.CheckState.Checked,
                }
            )
        return entries

    def choose_external_files(self):
        """Shows a dialog to select one or more external Python files.

        Returns:
            list: Selected file paths.
        """
        file_paths, _ = ui_qt.QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Add External Python Files",
            self.get_dialog_starting_directory(),
            "Python Files (*.py)",
        )
        return file_paths or []

    def choose_script_directory(self):
        """Shows a dialog to select a directory containing Python scripts.

        Returns:
            str: Selected directory path, or an empty string.
        """
        return ui_qt.QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Add Script Directory",
            self.get_dialog_starting_directory(),
        )

    def set_sample_scripts(self, samples):
        """Rebuilds the packaged examples menu.

        Args:
            samples (list): Sample dictionaries containing paths and relative paths.
        """
        self.sample_menu.clear()
        if not samples:
            action = self.sample_menu.addAction("No examples found")
            action.setEnabled(False)
            return
        for sample in samples:
            relative_path = str(sample.get("relative_path") or "")
            label = os.path.splitext(relative_path)[0].replace("_", " ").replace("\\", " / ")
            action = self.sample_menu.addAction(label.title())
            action.setToolTip(relative_path.replace("\\", "/"))
            action.triggered.connect(
                lambda checked=False, path=sample.get("path", ""): self.request_sample_load(path)
            )

    def show_samples_menu(self, checked=False):
        """Displays the packaged examples menu below the Examples button.

        Args:
            checked (bool, optional): Button state emitted by Qt.
        """
        menu_position = self.examples_button.mapToGlobal(self.examples_button.rect().bottomLeft())
        if hasattr(self.sample_menu, "exec"):
            self.sample_menu.exec(menu_position)
        else:
            self.sample_menu.exec_(menu_position)

    def request_sample_load(self, sample_path):
        """Requests that the controller load a selected sample into the editor.

        Args:
            sample_path (str): Absolute packaged sample path.
        """
        if self.inline_editor.get_text().strip() and not self.confirm_inline_replacement():
            return
        if callable(self.sample_load_callback):
            self.sample_load_callback(sample_path)

    def confirm_inline_replacement(self):
        """Confirms that an example may replace non-empty inline code.

        Returns:
            bool: True when existing inline code may be replaced.
        """
        result = ui_qt.QtWidgets.QMessageBox.question(
            self,
            "Replace Inline Script?",
            "The inline script already contains code.\n\nReplace it with the selected example?",
            ui_qt.QtLib.StandardButton.Yes | ui_qt.QtLib.StandardButton.No,
            ui_qt.QtLib.StandardButton.No,
        )
        return result == ui_qt.QtLib.StandardButton.Yes

    def confirm_remove_script(self, script_name):
        """Confirms removal of a persistent startup-script configuration.

        Args:
            script_name (str): Name of the configuration to remove.

        Returns:
            bool: True when the configuration may be removed.
        """
        result = ui_qt.QtWidgets.QMessageBox.question(
            self,
            "Remove Startup Script?",
            f"Remove the persistent startup script '{script_name}'?",
            ui_qt.QtLib.StandardButton.Yes | ui_qt.QtLib.StandardButton.No,
            ui_qt.QtLib.StandardButton.No,
        )
        return result == ui_qt.QtLib.StandardButton.Yes

    def get_dialog_starting_directory(self):
        """Gets a stable starting directory for file selection dialogs.

        Returns:
            str: Existing current working directory.
        """
        return os.getcwd()

    def emit_status_message(self, message, status="info"):
        """Shows routine feedback in the window's status area.

        Args:
            message (str): User-facing feedback.
            status (str, optional): One of info, warning, or error.
        """
        colors = {"warning": "#D89B34", "error": "#D9534F", "info": "#BDBDBD"}
        self.status_label.setText(str(message))
        self.status_label.setStyleSheet(f"color: {colors.get(status, colors['info'])};")
