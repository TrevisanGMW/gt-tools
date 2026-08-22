"""Dockable Qt view for the Script Library tool."""

from gt.tools.script_library.script_library_constants import ScriptLibraryConstants
from gt.ui.line_text_widget import LineTextWidget
from gt.ui.squared_widget import SquaredWidget
from gt.ui.syntax_highlighter import PythonSyntaxHighlighter
from gt.ui.qt_utils import MayaWindowMeta
import gt.ui.qt_import as ui_qt
import gt.ui.qt_utils as qt_utils
import gt.ui.resource_library as ui_res_lib
import html
import os


class ScriptLibraryView(metaclass=MayaWindowMeta):
    """Builds the dockable Script Library interface."""

    def __init__(self, parent=None, controller=None, version=None):
        """Initializes the Script Library window.

        Args:
            parent (QWidget, optional): Parent Qt widget.
            controller (ScriptLibraryController, optional): Controller retained by the view.
            version (str, optional): Tool version displayed in the title.
        """
        super().__init__(parent=parent)
        self.controller = controller
        self.splitter = None
        self.search_bar = None
        self.edit_mode_button = None
        self.item_list = None
        self.management_widget = None
        self.add_button = None
        self.delete_button = None
        self.duplicate_button = None
        self.open_scripts_folder_button = None
        self.import_script_button = None
        self.export_selected_button = None
        self.import_all_button = None
        self.export_all_button = None
        self.details_stack = None
        self.use_widget = None
        self.script_title = None
        self.preview_image = None
        self.description_label = None
        self.run_button = None
        self.list_run_button = None
        self.edit_widget = None
        self.name_field = None
        self.edit_script_name_button = None
        self.icon_mode_combo = None
        self.package_icon_field = None
        self.open_resource_library_button = None
        self.icon_asset_label = None
        self.upload_icon_button = None
        self.snapshot_button = None
        self.script_editor_widget = None
        self.script_editor = None
        self.description_field = None
        self.visible_check_box = None
        self.show_details_in_use_check_box = None
        self.auto_save_check_box = None
        self.save_button = None
        self.add_to_shelf_button = None
        self.status_label = None
        self.status_timer = None
        self.highlighter = None
        self._editor_icon_value = ""

        window_title = "Script Library"
        if version:
            window_title += f" - (v{version})"
        self.setWindowTitle(window_title)
        self.setGeometry(100, 100, 760, 520)
        self.create_widgets()
        self.create_layout()
        self.setWindowFlags(
            self.windowFlags()
            | ui_qt.QtLib.WindowFlag.WindowMaximizeButtonHint
            | ui_qt.QtLib.WindowFlag.WindowMinimizeButtonHint
        )
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_script_library))
        stylesheet = ui_res_lib.Stylesheet.scroll_bar_base
        stylesheet += ui_res_lib.Stylesheet.maya_dialog_base
        stylesheet += ui_res_lib.Stylesheet.list_widget_base
        stylesheet += ui_res_lib.Stylesheet.combobox_base
        self.setStyleSheet(stylesheet)
        qt_utils.resize_to_screen(self, percentage=42)
        qt_utils.center_window(self)
        self.resize_splitter_to_screen()
        self.update_preview_image()
        self.clear_details()

    def create_widgets(self):
        """Creates all widgets used by the Script Library view."""
        base_font = ui_qt.QtGui.QFont()
        base_font.setPointSize(10)

        self.search_bar = ui_qt.QtWidgets.QLineEdit(self)
        self.search_bar.setFont(base_font)
        self.search_bar.setPlaceholderText("Search scripts...")
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.setToolTip("Filter scripts by name, file name, or description.")

        self.edit_mode_button = ui_qt.QtWidgets.QPushButton("Edit Mode")
        self.edit_mode_button.setCheckable(True)
        self.edit_mode_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_edit))
        self.edit_mode_button.setToolTip(
            "Toggle editing and data-management controls. Hidden scripts are only listed in edit mode."
        )

        self.item_list = ui_qt.QtWidgets.QListWidget()
        self.item_list.setFont(base_font)
        self.item_list.setAlternatingRowColors(True)
        if ui_qt.IS_PYSIDE6:
            context_menu_policy = ui_qt.QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        else:
            context_menu_policy = ui_qt.QtCore.Qt.CustomContextMenu
        self.item_list.setContextMenuPolicy(context_menu_policy)
        self.item_list.setToolTip(
            "Select a script. Right-click a script for run, open, and shelf actions."
        )

        self.add_button = self._create_button(
            "Add Script", ui_res_lib.Icon.library_add, "Create a new editable script."
        )
        self.delete_button = self._create_button(
            "Delete", ui_res_lib.Icon.library_remove, "Delete the selected script and its managed assets."
        )
        self.duplicate_button = self._create_button(
            "Duplicate",
            ui_res_lib.Icon.library_duplicate,
            "Duplicate the selected script with a fresh stable ID.",
        )
        self.open_scripts_folder_button = self._create_button(
            "Open Folder", ui_res_lib.Icon.util_open_dir, "Open the Prefs-managed scripts folder."
        )
        self.import_script_button = self._create_button(
            "Import Script", ui_res_lib.Icon.library_import, "Import a .py or .gtscript file."
        )
        self.export_selected_button = self._create_button(
            "Export Selected",
            ui_res_lib.Icon.library_export,
            "Export the selected script and its managed icon as a compressed archive.",
        )
        self.import_all_button = self._create_button(
            "Import Backup", ui_res_lib.Icon.library_import, "Import a complete .gtscriptlib backup."
        )
        self.export_all_button = self._create_button(
            "Export Backup",
            ui_res_lib.Icon.library_export,
            "Create a compressed backup of every script and managed icon.",
        )

        self.script_title = ui_qt.QtWidgets.QLabel("Script: No Selection")
        self.script_title.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        self.script_title.setFont(base_font)
        self.script_title.setToolTip("Name of the currently selected script.")
        self.preview_image = SquaredWidget(self, center_y=False)
        self.preview_image.setToolTip("Script icon, uploaded image, or viewport snapshot.")
        self.description_label = ui_qt.QtWidgets.QLabel("")
        self.description_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        self.description_label.setWordWrap(True)
        self.description_label.setFont(base_font)
        self.description_label.setToolTip("Description of the currently selected script.")
        self.run_button = self._create_button(
            "Run", ui_res_lib.Icon.library_build, "Execute the selected script."
        )
        self.run_button.setStyleSheet(ui_res_lib.Stylesheet.btn_push_bright)
        self.list_run_button = self._create_button(
            "Run", ui_res_lib.Icon.library_build, "Execute the selected script."
        )
        self.list_run_button.setStyleSheet(ui_res_lib.Stylesheet.btn_push_bright)

        self.name_field = ui_qt.QtWidgets.QLineEdit()
        self.name_field.setPlaceholderText("Nice name shown in the library")
        self.name_field.setToolTip("The display name shown in the Script Library list.")
        self.edit_script_name_button = self._create_button(
            "Edit File Name",
            ui_res_lib.Icon.library_edit,
            "Rename the .py script file and any managed custom icon or snapshot. This does not change Nice Name.",
        )
        self.icon_mode_combo = ui_qt.QtWidgets.QComboBox()
        for icon_mode in ScriptLibraryConstants.ICON_MODES:
            self.icon_mode_combo.addItem(
                ScriptLibraryConstants.ICON_MODE_LABELS[icon_mode], icon_mode
            )
        self.icon_mode_combo.setToolTip("Choose how this script is represented in the library.")
        self.package_icon_field = ui_qt.QtWidgets.QLineEdit()
        self.package_icon_field.setPlaceholderText("e.g. dev_code or resource_library.Icon.dev_code")
        self.package_icon_field.setToolTip("Package icon attribute or file name to use for this script.")
        self.open_resource_library_button = self._create_button(
            "Browse Package Icons",
            ui_res_lib.Icon.tool_resource_library,
            "Open Resource Library. Copy or type an Icon attribute name in the field above.",
        )
        self.icon_asset_label = ui_qt.QtWidgets.QLabel("Managed Icon File: None")
        self.icon_asset_label.setWordWrap(True)
        self.icon_asset_label.setToolTip(
            "Name of the uploaded icon or viewport snapshot stored beside this script."
        )
        if ui_qt.IS_PYSIDE6:
            selectable_flag = ui_qt.QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        else:
            selectable_flag = ui_qt.QtCore.Qt.TextSelectableByMouse
        self.icon_asset_label.setTextInteractionFlags(selectable_flag)
        self.upload_icon_button = self._create_button(
            "Upload Icon", ui_res_lib.Icon.ui_open, "Copy an image or SVG beside the script."
        )
        self.snapshot_button = self._create_button(
            "Viewport Snapshot",
            ui_res_lib.Icon.library_snapshot,
            "Capture the current viewport and store it beside the script.",
        )

        self.script_editor_widget = LineTextWidget(self)
        self.script_editor = self.script_editor_widget.get_text_edit()
        self.script_editor.setPlaceholderText("Write the Python code to execute...")
        self.script_editor_widget.setMinimumHeight(210)
        self.script_editor.setToolTip("Python source code executed by the Run button or shelf shortcut.")
        self.highlighter = PythonSyntaxHighlighter(self.script_editor.document())

        self.description_field = ui_qt.QtWidgets.QTextEdit()
        self.description_field.setAcceptRichText(False)
        self.description_field.setPlaceholderText("Optional description shown below the script icon")
        self.description_field.setMaximumHeight(85)
        self.description_field.setToolTip("Optional text displayed below the script preview in use mode.")
        self.visible_check_box = ui_qt.QtWidgets.QCheckBox("Visible")
        self.visible_check_box.setChecked(True)
        self.visible_check_box.setToolTip("Show this script in use mode.")
        self.save_button = self._create_button(
            "Save Changes", ui_res_lib.Icon.ui_save, "Save metadata and Python content through Prefs."
        )
        self.save_button.setStyleSheet(ui_res_lib.Stylesheet.btn_push_bright)
        self.add_to_shelf_button = self._create_button(
            "Add to Shelf",
            ui_res_lib.Icon.library_shelf,
            "Add a shelf button that runs the latest saved version of this script.",
        )
        for action_button in (self.save_button, self.add_to_shelf_button):
            action_button.setMinimumSize(140, 36)
            action_button.setSizePolicy(
                ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed
            )

        self.show_details_in_use_check_box = ui_qt.QtWidgets.QCheckBox(
            "Show Details in Use Mode"
        )
        self.show_details_in_use_check_box.setToolTip(
            "Show the thumbnail, description, and Run button in use mode. Disable for a list-only library."
        )
        self.auto_save_check_box = ui_qt.QtWidgets.QCheckBox("Auto Save Changes")
        self.auto_save_check_box.setToolTip(
            "Save script fields automatically as they change. The Save Changes button is hidden while enabled."
        )

        self.status_label = ui_qt.QtWidgets.QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(20)
        self.status_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        self.status_label.setToolTip("Temporary status and error messages.")
        self.status_label.setVisible(False)
        self.status_timer = ui_qt.QtCore.QTimer(self)
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(self.clear_status)

    def create_layout(self):
        """Creates the responsive split layout for use and edit modes."""
        search_layout = ui_qt.QtWidgets.QHBoxLayout()
        search_layout.addWidget(self.search_bar, 1)
        search_layout.addWidget(self.edit_mode_button)

        management_layout = ui_qt.QtWidgets.QGridLayout()
        management_layout.setContentsMargins(0, 0, 0, 0)
        management_layout.setHorizontalSpacing(5)
        management_layout.setVerticalSpacing(5)
        management_layout.addWidget(self.add_button, 0, 0)
        management_layout.addWidget(self.delete_button, 0, 1)
        management_layout.addWidget(self.duplicate_button, 1, 0)
        management_layout.addWidget(self.open_scripts_folder_button, 1, 1)
        management_layout.addWidget(self.import_script_button, 2, 0)
        management_layout.addWidget(self.export_selected_button, 2, 1)
        management_layout.addWidget(self.import_all_button, 3, 0)
        management_layout.addWidget(self.export_all_button, 3, 1)
        self.management_widget = ui_qt.QtWidgets.QWidget()
        self.management_widget.setLayout(management_layout)

        list_layout = ui_qt.QtWidgets.QVBoxLayout()
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.addLayout(search_layout)
        list_layout.addWidget(self.item_list, 1)
        list_layout.addWidget(self.management_widget)
        list_layout.addWidget(self.list_run_button)
        list_container = ui_qt.QtWidgets.QWidget()
        list_container.setLayout(list_layout)
        list_container.setMinimumWidth(250)

        use_layout = ui_qt.QtWidgets.QVBoxLayout()
        use_layout.setContentsMargins(4, 4, 4, 4)
        use_layout.addWidget(self.script_title)
        use_layout.addWidget(self.preview_image, 1)
        use_layout.addWidget(self.description_label)
        use_layout.addWidget(self.run_button)
        self.use_widget = ui_qt.QtWidgets.QWidget()
        self.use_widget.setLayout(use_layout)

        edit_layout = ui_qt.QtWidgets.QVBoxLayout()
        edit_layout.setContentsMargins(4, 4, 4, 4)
        edit_layout.setSpacing(6)
        name_layout = ui_qt.QtWidgets.QHBoxLayout()
        name_label = ui_qt.QtWidgets.QLabel("Nice Name:")
        name_label.setToolTip("Display name shown in the Script Library list.")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_field, 1)
        name_layout.addWidget(self.edit_script_name_button)
        name_layout.addWidget(self.visible_check_box)
        edit_layout.addLayout(name_layout)

        icon_mode_layout = ui_qt.QtWidgets.QHBoxLayout()
        icon_source_label = ui_qt.QtWidgets.QLabel("Icon Source:")
        icon_source_label.setToolTip("Select a package icon, uploaded icon, viewport snapshot, or default icon.")
        icon_mode_layout.addWidget(icon_source_label)
        icon_mode_layout.addWidget(self.icon_mode_combo, 1)
        edit_layout.addLayout(icon_mode_layout)
        edit_layout.addWidget(self.package_icon_field)
        edit_layout.addWidget(self.open_resource_library_button)
        edit_layout.addWidget(self.icon_asset_label)
        icon_action_layout = ui_qt.QtWidgets.QHBoxLayout()
        icon_action_layout.addWidget(self.upload_icon_button)
        icon_action_layout.addWidget(self.snapshot_button)
        edit_layout.addLayout(icon_action_layout)

        content_label = ui_qt.QtWidgets.QLabel("Script Content:")
        content_label.setToolTip("Python source code saved for the selected script.")
        edit_layout.addWidget(content_label)
        edit_layout.addWidget(self.script_editor_widget, 1)
        description_field_label = ui_qt.QtWidgets.QLabel("Description:")
        description_field_label.setToolTip("Optional description shown under the preview in use mode.")
        edit_layout.addWidget(description_field_label)
        edit_layout.addWidget(self.description_field)
        preferences_group = ui_qt.QtWidgets.QGroupBox("Library Preferences")
        preferences_group.setToolTip("Preferences stored through Prefs for this Script Library.")
        preferences_layout = ui_qt.QtWidgets.QVBoxLayout(preferences_group)
        preferences_layout.addWidget(self.show_details_in_use_check_box)
        preferences_layout.addWidget(self.auto_save_check_box)
        edit_layout.addWidget(preferences_group)
        edit_action_layout = ui_qt.QtWidgets.QHBoxLayout()
        edit_action_layout.addWidget(self.save_button, 1)
        edit_action_layout.addWidget(self.add_to_shelf_button, 1)
        edit_layout.addLayout(edit_action_layout)
        self.edit_widget = ui_qt.QtWidgets.QWidget()
        self.edit_widget.setLayout(edit_layout)

        self.details_stack = ui_qt.QtWidgets.QStackedWidget()
        self.details_stack.addWidget(self.use_widget)
        self.details_stack.addWidget(self.edit_widget)
        self.details_stack.setMinimumWidth(330)

        self.splitter = ui_qt.QtWidgets.QSplitter(self)
        self.splitter.setHandleWidth(5)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(list_container)
        self.splitter.addWidget(self.details_stack)

        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 9)
        main_layout.addWidget(self.splitter, 1)
        main_layout.addWidget(self.status_label)

    @staticmethod
    def _create_button(text, icon_path, tooltip):
        """Creates a consistently configured push button.

        Args:
            text (str): Button text.
            icon_path (str): Icon file path.
            tooltip (str): Button tooltip.

        Returns:
            QPushButton: Configured button.
        """
        button = ui_qt.QtWidgets.QPushButton(text)
        if icon_path:
            button.setIcon(ui_qt.QtGui.QIcon(icon_path))
        button.setToolTip(tooltip)
        return button

    def set_edit_mode(self, is_edit_mode, show_details_in_use_mode=True):
        """Updates widgets for edit or use mode.

        Args:
            is_edit_mode (bool): Whether edit mode is active.
            show_details_in_use_mode (bool, optional): Whether the use-mode details
                panel should be visible.
        """
        is_edit_mode = bool(is_edit_mode)
        signals_blocked = self.edit_mode_button.blockSignals(True)
        self.edit_mode_button.setChecked(is_edit_mode)
        self.edit_mode_button.setText("Edit Mode: On" if is_edit_mode else "")
        self.edit_mode_button.blockSignals(signals_blocked)
        self.management_widget.setVisible(is_edit_mode)
        self.details_stack.setCurrentIndex(1 if is_edit_mode else 0)
        self.details_stack.setVisible(is_edit_mode or bool(show_details_in_use_mode))
        self.list_run_button.setVisible(
            not is_edit_mode and not bool(show_details_in_use_mode)
        )

    def set_library_preferences(self, show_details_in_use_mode, auto_save):
        """Updates the edit-only preference widgets and save-button visibility.

        Args:
            show_details_in_use_mode (bool): Whether use mode shows script details.
            auto_save (bool): Whether editor field changes save automatically.
        """
        show_blocked = self.show_details_in_use_check_box.blockSignals(True)
        auto_blocked = self.auto_save_check_box.blockSignals(True)
        self.show_details_in_use_check_box.setChecked(bool(show_details_in_use_mode))
        self.auto_save_check_box.setChecked(bool(auto_save))
        self.show_details_in_use_check_box.blockSignals(show_blocked)
        self.auto_save_check_box.blockSignals(auto_blocked)
        self.save_button.setVisible(not bool(auto_save))

    def set_editor_enabled(self, is_enabled):
        """Enables or disables selection-dependent controls.

        Args:
            is_enabled (bool): New enabled state.
        """
        for widget in (
            self.name_field,
            self.edit_script_name_button,
            self.icon_mode_combo,
            self.package_icon_field,
            self.open_resource_library_button,
            self.upload_icon_button,
            self.snapshot_button,
            self.script_editor,
            self.description_field,
            self.visible_check_box,
            self.save_button,
            self.add_to_shelf_button,
            self.delete_button,
            self.duplicate_button,
            self.export_selected_button,
        ):
            widget.setEnabled(bool(is_enabled))
        self.run_button.setEnabled(bool(is_enabled))
        self.list_run_button.setEnabled(bool(is_enabled))

    def set_editor_data(self, item, script_content):
        """Loads one script into the edit fields.

        Args:
            item (ScriptLibraryItem): Selected script item.
            script_content (str): Stored Python source code.
        """
        self.name_field.setText(item.nice_name)
        icon_index = self.icon_mode_combo.findData(item.icon_mode)
        self.icon_mode_combo.setCurrentIndex(max(0, icon_index))
        self._editor_icon_value = item.icon_value
        if item.icon_mode == ScriptLibraryConstants.ICON_MODE_PACKAGE:
            self.package_icon_field.setText(item.icon_value)
        else:
            self.package_icon_field.clear()
        self._set_icon_asset_label(item.icon_value)
        self.script_editor.setPlainText(script_content)
        self.description_field.setPlainText(item.description)
        self.visible_check_box.setChecked(item.visible)
        self.update_icon_controls(item.icon_mode)

    def get_editor_data(self):
        """Gets the current edit-field values.

        Returns:
            dict: Editable script metadata and content.
        """
        icon_mode = self.icon_mode_combo.currentData()
        icon_value = self._editor_icon_value
        if icon_mode == ScriptLibraryConstants.ICON_MODE_PACKAGE:
            icon_value = self.package_icon_field.text().strip()
        elif icon_mode == ScriptLibraryConstants.ICON_MODE_DEFAULT:
            icon_value = ""
        return {
            "nice_name": self.name_field.text().strip(),
            "script_content": self.script_editor.toPlainText(),
            "description": self.description_field.toPlainText().strip(),
            "visible": self.visible_check_box.isChecked(),
            "icon_mode": icon_mode,
            "icon_value": icon_value,
        }

    def set_editor_icon(self, icon_mode, icon_value):
        """Updates the icon fields after upload or snapshot actions.

        Args:
            icon_mode (str): New icon mode.
            icon_value (str): New managed icon file name.
        """
        self._editor_icon_value = str(icon_value or "")
        icon_index = self.icon_mode_combo.findData(icon_mode)
        if icon_index >= 0:
            self.icon_mode_combo.setCurrentIndex(icon_index)
        self._set_icon_asset_label(icon_value)
        self.update_icon_controls(icon_mode)

    def _set_icon_asset_label(self, icon_value):
        """Shows the managed uploaded-icon or snapshot file name.

        Args:
            icon_value (str): Managed file name or an empty value.
        """
        display_value = html.escape(str(icon_value or "None"))
        self.icon_asset_label.setText(
            "Managed Icon File: "
            f'<span style="color: #808080;">{display_value}</span>'
        )

    def update_icon_controls(self, icon_mode):
        """Updates icon widgets for the selected icon mode.

        Args:
            icon_mode (str): Active icon mode.
        """
        is_package = icon_mode == ScriptLibraryConstants.ICON_MODE_PACKAGE
        is_custom = icon_mode == ScriptLibraryConstants.ICON_MODE_CUSTOM
        is_snapshot = icon_mode == ScriptLibraryConstants.ICON_MODE_SNAPSHOT
        self.package_icon_field.setVisible(is_package)
        self.open_resource_library_button.setVisible(is_package)
        self.icon_asset_label.setVisible(is_custom or is_snapshot)
        self.upload_icon_button.setEnabled(is_custom)
        self.snapshot_button.setEnabled(is_snapshot)

    def update_use_display(self, nice_name, description, image_path):
        """Updates the non-edit script display.

        Args:
            nice_name (str): User-facing script name.
            description (str): Optional script description.
            image_path (str): Resolved preview image path.
        """
        qt_utils.update_formatted_label(
            target_label=self.script_title,
            text="Script: ",
            text_size=3,
            text_color="grey",
            output_text=nice_name,
            output_size=3,
            output_color="white",
            overall_alignment="center",
        )
        self.description_label.setText(description or "")
        self.description_label.setVisible(bool(description))
        self.update_preview_image(image_path)

    def update_preview_image(self, image_path=None):
        """Updates the preview with a safe placeholder fallback.

        Args:
            image_path (str, optional): Candidate preview image path.
        """
        resolved_path = image_path
        if not resolved_path or not os.path.isfile(resolved_path):
            resolved_path = ui_res_lib.Icon.script_library_missing_icon
        pixmap = ui_qt.QtGui.QPixmap(resolved_path)
        if pixmap.isNull():
            pixmap = ui_qt.QtGui.QPixmap(ui_res_lib.Icon.script_library_missing_icon)
        self.preview_image.set_pixmap(pixmap)

    def clear_details(self):
        """Clears selection-dependent details and disables their controls."""
        self.script_title.setText("Script: No Selection")
        self.description_label.clear()
        self.description_label.setVisible(False)
        self.update_preview_image()
        self.name_field.clear()
        self.package_icon_field.clear()
        self._set_icon_asset_label("")
        self.script_editor.clear()
        self.description_field.clear()
        self.visible_check_box.setChecked(True)
        self._editor_icon_value = ""
        self.set_editor_enabled(False)

    def clear_script_list(self):
        """Removes every script list item."""
        self.item_list.clear()

    def add_script_item(self, item_name, icon, metadata, is_hidden=False):
        """Adds one script to the list.

        Args:
            item_name (str): User-facing script name.
            icon (QIcon): Resolved script icon.
            metadata (dict): Item metadata containing its stable ID.
            is_hidden (bool, optional): Whether the item is hidden in use mode.

        Returns:
            QListWidgetItem: Added list item.
        """
        list_item = ui_qt.QtWidgets.QListWidgetItem(item_name)
        if icon:
            list_item.setIcon(icon)
        list_item.setData(ui_qt.QtLib.ItemDataRole.UserRole, metadata)
        if is_hidden:
            list_item.setForeground(ui_qt.QtGui.QColor(ui_res_lib.Color.Hex.gray_lighter))
            list_item.setToolTip("Hidden in Use Mode")
        else:
            list_item.setToolTip(
                "Select this script. Right-click for Run Script, Open Script, and Add to Shelf."
            )
        self.item_list.addItem(list_item)
        return list_item

    def get_selected_script_id(self):
        """Gets the stable ID stored on the selected list item.

        Returns:
            str: Stable script ID or empty string.
        """
        item = self.item_list.currentItem()
        if not item:
            return ""
        metadata = item.data(ui_qt.QtLib.ItemDataRole.UserRole) or {}
        return str(metadata.get("script_id") or "")

    def select_script_id(self, script_id):
        """Selects a visible list row by stable ID.

        Args:
            script_id (str): Stable script identifier.

        Returns:
            bool: True when the script was selected.
        """
        for index in range(self.item_list.count()):
            item = self.item_list.item(index)
            metadata = item.data(ui_qt.QtLib.ItemDataRole.UserRole) or {}
            if metadata.get("script_id") == script_id:
                self.item_list.setCurrentItem(item)
                self.item_list.scrollToItem(
                    item, ui_qt.QtLib.ScrollHint.PositionAtCenter
                )
                return True
        return False

    def show_status(self, message, warning=False):
        """Displays a concise status message at the bottom of the tool.

        Args:
            message (str): Status text.
            warning (bool, optional): Whether warning coloring is used.
        """
        self.status_label.setText(str(message or ""))
        if warning:
            self.status_label.setStyleSheet("color: #E6B85C;")
        else:
            self.status_label.setStyleSheet("color: #BDBDBD;")
        self.status_label.setVisible(bool(message))
        if message:
            self.status_timer.start(2000)

    def clear_status(self):
        """Hides the temporary status message after its display interval."""
        self.status_label.clear()
        self.status_label.setVisible(False)

    def resize_splitter_to_screen(self, percentage=30):
        """Sets useful initial splitter proportions across Qt versions.

        Args:
            percentage (int, optional): Screen width percentage used for sizing.

        Raises:
            ValueError: If percentage is outside the range zero to one hundred.
        """
        if not 0 <= percentage <= 100:
            raise ValueError("Percentage should be between 0 and 100")
        if hasattr(ui_qt.QtWidgets, "QDesktopWidget"):
            screen_geometry = ui_qt.QtWidgets.QDesktopWidget().availableGeometry(self)
        else:
            screen = self.screen() if hasattr(self, "screen") else None
            screen = screen or ui_qt.QtGui.QGuiApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
        width = screen_geometry.width() * (percentage / 100.0)
        self.splitter.setSizes([int(width * 0.42), int(width * 0.58)])

    def closeEvent(self, event):
        """Lets the controller persist pending edits before the window closes.

        Args:
            event (QCloseEvent): Qt close event.
        """
        if self.controller and hasattr(self.controller, "on_view_close"):
            self.controller.on_view_close()
        super().closeEvent(event)


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = ScriptLibraryView()
        window.show()
