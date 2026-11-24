"""
Multi-File Importer View

Widgets only. Every tool setting is bound to one widget through setting_widgets, so the
controller reads and writes all settings with get_settings and set_settings.
"""

from gt.tools.multi_file_importer import multi_file_importer_constants as constants
from gt.ui.collapsible_section import CollapsibleSection
from gt.ui.syntax_highlighter import PythonSyntaxHighlighter
from gt.ui.line_text_widget import LineTextWidget
from gt.ui.file_drop_list import FileDropList
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_utils as ui_qt_utils
import gt.ui.qt_import as ui_qt
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

COLUMN_FILE = 0
COLUMN_FORMAT = 1
COLUMN_STATUS = 2
COLUMN_FOLDER = 3
COLUMN_LABELS = ["File", "Format", "Status", "Folder"]
LABEL_WIDTH = 104
STATUS_COLORS = {
    constants.STATUS_PENDING: (150, 150, 150),
    constants.STATUS_IMPORTED: (124, 174, 122),
    constants.STATUS_WARNING: (214, 182, 86),
    constants.STATUS_FAILED: (214, 106, 106),
    constants.STATUS_SKIPPED: (150, 150, 150),
    constants.STATUS_CANCELLED: (150, 150, 150),
}
ENTRY_ID_ROLE = ui_qt.QtCore.Qt.ItemDataRole.UserRole
WINDOW_MINIMUM_WIDTH = 470
DISABLED_STYLESHEET = (
    "QLineEdit:disabled, QComboBox:disabled, QAbstractSpinBox:disabled, QTextEdit:disabled, "
    "QPlainTextEdit:disabled { color: rgb(105, 105, 105); background-color: rgb(52, 52, 52); "
    "border: 1px solid rgb(62, 62, 62); }"
    "QCheckBox:disabled, QLabel:disabled, QRadioButton:disabled { color: rgb(105, 105, 105); }"
    "QPushButton:disabled { color: rgb(105, 105, 105); }"
)
CONTEXT_ACTIONS = [
    ("check_all", "Check All"),
    ("uncheck_all", "Uncheck All"),
    ("check_selected", "Check Selected"),
    ("uncheck_selected", "Uncheck Selected"),
    ("solo_selected", "Solo Selected (Check Only These)"),
    ("invert_checks", "Invert Checks"),
    None,
    ("select_all", "Select All Rows"),
    ("select_checked", "Select Checked Rows"),
    None,
    ("copy_paths", "Copy Paths"),
    ("paste_paths", "Paste Paths"),
    ("open_folder", "Open Containing Folder"),
    None,
    ("remove_selected", "Remove Selected"),
    ("remove_unchecked", "Remove Unchecked"),
    ("remove_missing", "Remove Missing Files"),
    ("reset_status", "Reset Status"),
]
CONTEXT_SHORTCUTS = {"copy_paths": "Ctrl+C", "paste_paths": "Ctrl+V", "remove_selected": "Del",
                     "select_all": "Ctrl+A"}


class MultiFileImporterView(metaclass=ui_qt_utils.MayaWindowMeta):
    """Main window of the Multi-File Importer."""

    def __init__(self, parent=None, controller=None, version=None):
        """Initializes the view.

        Args:
            parent (QWidget, optional): Parent widget.
            controller (MultiFileImporterController, optional): Kept here so it is not garbage collected.
            version (str, optional): Tool version shown in the title.
        """
        super().__init__(parent=parent)
        self.controller = controller
        self.close_func = None
        self.setting_widgets = {}
        self.sections = {}
        self.format_option_widgets = {}
        self.row_labels = {}
        self.context_actions = {}
        self.setWindowTitle(constants.TOOL_NAME + (f" - (v{version})" if version else ""))
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_multi_file_importer))
        self.setWindowFlags(
            self.windowFlags()
            | ui_qt.QtLib.WindowFlag.WindowMaximizeButtonHint
            | ui_qt.QtLib.WindowFlag.WindowMinimizeButtonHint
        )
        self.setMinimumWidth(WINDOW_MINIMUM_WIDTH)
        self.build_widgets()
        stylesheet = ui_res_lib.Stylesheet.scroll_bar_base
        stylesheet += ui_res_lib.Stylesheet.maya_dialog_base
        stylesheet += DISABLED_STYLESHEET
        self.setStyleSheet(stylesheet)
        self.import_btn.setStyleSheet(ui_res_lib.Stylesheet.btn_push_bright + DISABLED_STYLESHEET)
        self.update_import_button_size()
        self.fit_to_contents()
        ui_qt_utils.center_window(self)

    # ------------------------------------------------------------------ build
    def build_widgets(self):
        """Builds every widget and layout."""
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(6)
        splitter = ui_qt.QtWidgets.QSplitter(ui_qt.QtCore.Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.build_files_area())
        splitter.addWidget(self.build_settings_area())
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        self.splitter = splitter
        main_layout.addWidget(splitter, 1)
        main_layout.addLayout(self.build_progress_row())
        self.import_btn = ui_qt.QtWidgets.QPushButton("Import Files")
        self.import_btn.setToolTip("Import every checked file in list order.")
        self.import_btn.setMinimumHeight(32)
        main_layout.addWidget(self.import_btn)
        self.status_line = ui_qt.QtWidgets.QLineEdit()
        self.status_line.setReadOnly(True)
        self.status_line.setPlaceholderText("Status")
        main_layout.addWidget(self.status_line)
        self.refresh_enabled_states()

    def build_files_area(self):
        """Builds the file list, its buttons and list options.

        Returns:
            QWidget: Files area.
        """
        files_widget = ui_qt.QtWidgets.QWidget()
        files_layout = ui_qt.QtWidgets.QVBoxLayout(files_widget)
        files_layout.setContentsMargins(0, 0, 0, 0)
        files_layout.setSpacing(4)
        self.file_list = FileDropList(placeholder_text="Drop files or folders here")
        self.file_list.setColumnCount(len(COLUMN_LABELS))
        self.file_list.setHeaderLabels(COLUMN_LABELS)
        self.file_list.setRootIsDecorated(False)
        self.file_list.setUniformRowHeights(True)
        self.file_list.setSelectionMode(ui_qt.QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.file_list.setMinimumHeight(150)
        self.file_list.setToolTip("Drop files or folders here. Right-click for more options.")
        header = self.file_list.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(COLUMN_FILE, ui_qt.QtWidgets.QHeaderView.ResizeMode.Interactive)
        self.file_list.setColumnWidth(COLUMN_FILE, 170)
        self.file_list.setColumnWidth(COLUMN_FORMAT, 80)
        self.file_list.setColumnWidth(COLUMN_STATUS, 70)
        self.context_menu = None
        files_layout.addWidget(self.file_list, 1)

        options_layout = ui_qt.QtWidgets.QHBoxLayout()
        recursive_checkbox = self.create_checkbox(
            "recursive", "Recursive", "Include files in sub-folders when adding or dropping folders."
        )
        self.filter_combo = self.create_combo(
            "extension_filter", [], "Only add files of this format when adding folders or dropping files."
        )
        self.file_count_label = ui_qt.QtWidgets.QLabel("No files")
        self.file_count_label.setStyleSheet("color: grey;")
        self.file_count_label.setAlignment(ui_qt.QtCore.Qt.AlignmentFlag.AlignCenter)
        self.file_count_label.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Policy.Ignored, ui_qt.QtWidgets.QSizePolicy.Policy.Preferred
        )
        options_layout.addWidget(recursive_checkbox)
        options_layout.addWidget(self.file_count_label, 1)
        options_layout.addWidget(ui_qt.QtWidgets.QLabel("Filter:"))
        self.filter_combo.setSizeAdjustPolicy(
            ui_qt.QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.filter_combo.setMinimumContentsLength(14)
        self.filter_combo.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Policy.Fixed, ui_qt.QtWidgets.QSizePolicy.Policy.Fixed
        )
        options_layout.addWidget(self.filter_combo)
        files_layout.addLayout(options_layout)

        buttons_layout = ui_qt.QtWidgets.QHBoxLayout()
        buttons_layout.setSpacing(4)
        self.add_files_btn = ui_qt.QtWidgets.QPushButton("Add Files")
        self.add_files_btn.setToolTip("Pick files to add to the list.")
        self.add_folder_btn = ui_qt.QtWidgets.QPushButton("Add Folder")
        self.add_folder_btn.setToolTip("Add every supported file in a folder (sub-folders when Recursive is on).")
        self.remove_btn = ui_qt.QtWidgets.QPushButton("Remove")
        self.remove_btn.setToolTip("Remove the selected files from the list (Delete key).")
        self.clear_btn = ui_qt.QtWidgets.QPushButton("Clear")
        self.clear_btn.setToolTip("Remove every file from the list.")
        self.sort_btn = ui_qt.QtWidgets.QPushButton("Sort")
        self.sort_btn.setToolTip("Sort the list. Files are imported (and placed) in list order.")
        self.sort_menu = ui_qt.QtWidgets.QMenu(self.sort_btn)
        self.sort_actions = {}
        for sort_mode in constants.SORT_MODES:
            self.sort_actions[sort_mode] = self.sort_menu.addAction(sort_mode)
        self.sort_btn.setMenu(self.sort_menu)
        for button in [self.add_files_btn, self.add_folder_btn, self.remove_btn, self.clear_btn, self.sort_btn]:
            buttons_layout.addWidget(button)
        files_layout.addLayout(buttons_layout)
        return files_widget

    def build_context_menu(self, handlers=None, enabled_states=None):
        """Builds a new right-click menu for the file list.

        A new menu is built for every click (and kept on the view while it is open), so the menu never
        points at Qt actions that Maya deleted while re-hosting or restoring the window.

        Args:
            handlers (dict, optional): Action key to callable run when the action is triggered.
            enabled_states (dict, optional): Action key to enabled state.

        Returns:
            QMenu: The new menu.
        """
        self.context_menu = ui_qt.QtWidgets.QMenu(self)
        self.context_actions = {}
        for action_data in CONTEXT_ACTIONS:
            if action_data is None:
                self.context_menu.addSeparator()
                continue
            action_key, label = action_data
            shortcut = CONTEXT_SHORTCUTS.get(action_key)
            action = self.context_menu.addAction(f"{label}\t{shortcut}" if shortcut else label)
            action.setEnabled((enabled_states or {}).get(action_key, True))
            handler = (handlers or {}).get(action_key)
            if callable(handler):
                action.triggered.connect(lambda *args, function=handler: function())
            self.context_actions[action_key] = action
        return self.context_menu

    def show_context_menu(self, position, handlers, enabled_states=None):
        """Builds and shows the right-click menu.

        Args:
            position (QPoint): Click position in file list viewport coordinates.
            handlers (dict): Action key to callable.
            enabled_states (dict, optional): Action key to enabled state.
        """
        menu = self.build_context_menu(handlers, enabled_states)
        execute_menu = getattr(menu, "exec", None) or getattr(menu, "exec_")
        execute_menu(self.file_list.viewport().mapToGlobal(position))

    def build_settings_area(self):
        """Builds the scrollable collapsible sections.

        Returns:
            QScrollArea: Settings area.
        """
        settings_widget = ui_qt.QtWidgets.QWidget()
        settings_layout = ui_qt.QtWidgets.QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, 0, 6, 0)
        settings_layout.setSpacing(2)
        settings_layout.addWidget(self.build_import_section())
        settings_layout.addWidget(self.build_formats_section())
        settings_layout.addWidget(self.build_placement_section())
        settings_layout.addWidget(self.build_scene_section())
        settings_layout.addWidget(self.build_review_section())
        settings_layout.addWidget(self.build_scripts_section())
        settings_layout.addWidget(self.build_preferences_section())
        settings_layout.addStretch()
        self.settings_container = settings_widget
        scroll_area = ui_qt.QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(ui_qt.QtWidgets.QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(ui_qt.QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setWidget(settings_widget)
        self.settings_scroll = scroll_area
        return scroll_area

    def create_section(self, section_key, title):
        """Creates a collapsible section and registers it.

        Args:
            section_key (str): Section key (constants.SECTION_*).
            title (str): Header text.

        Returns:
            CollapsibleSection: Created section.
        """
        section = CollapsibleSection(title, expanded=constants.DEFAULT_SECTION_STATES.get(section_key, True))
        section.toggled.connect(lambda *args: ui_qt.QtCore.QTimer.singleShot(0, self.make_room_for_sections))
        self.sections[section_key] = section
        return section

    def make_room_for_sections(self):
        """Gives the settings area the height its sections need, within the current window size.

        The window never grows: extra height comes from the file list (down to its minimum height) and the
        settings area shows a scroll bar when the expanded sections still do not fit.
        """
        if not ui_qt_utils.is_qt_object_valid(self):
            return
        needed_height = self.settings_container.sizeHint().height()
        table_size, settings_size = self.splitter.sizes()
        total_size = table_size + settings_size
        minimum_table_size = self.file_list.minimumHeight() + 70
        settings_size = max(min(needed_height, total_size - minimum_table_size), self.settings_scroll.minimumHeight())
        self.splitter.setSizes([total_size - settings_size, settings_size])

    def build_import_section(self):
        """Builds the Import section.

        Returns:
            CollapsibleSection: Section widget.
        """
        section = self.create_section(constants.SECTION_IMPORT, "Import")
        layout = section.content_layout
        layout.addLayout(
            self.create_row(
                "Mode",
                self.create_combo(
                    "load_mode",
                    constants.LOAD_MODES,
                    "Import: copy the file contents into the scene.\n"
                    "Reference: link the files (Maya scenes, FBX, Alembic). Other formats are imported.",
                ),
            )
        )
        self.namespace_template_field = self.create_line_edit(
            "namespace_template", "{name}", "Custom namespace. Tokens: {name} = file name, {index} = file position."
        )
        layout.addLayout(
            self.create_row(
                "Namespace",
                self.create_combo(
                    "namespace_mode",
                    constants.NAMESPACE_MODES,
                    "Namespace for each file's nodes. Avoids name clashes when the same rig is imported many times.\n"
                    "References always use a namespace (the file name when None is selected).",
                ),
                self.namespace_template_field,
            )
        )
        layout.addLayout(
            self.create_row(
                "On Failure",
                self.create_combo(
                    "on_failure",
                    constants.FAILURE_POLICIES,
                    "Skip File: keep importing the remaining files.\nStop Import: stop at the first failure.",
                ),
            )
        )
        return section

    def build_formats_section(self):
        """Builds the Format Options section, whose form is rebuilt for the selected format.

        Returns:
            CollapsibleSection: Section widget.
        """
        section = self.create_section(constants.SECTION_FORMATS, "Format Options")
        self.format_combo = ui_qt.QtWidgets.QComboBox()
        self.format_combo.setToolTip("Format whose import options are shown below. Options are saved per format.")
        section.content_layout.addLayout(self.create_row("Format", self.format_combo))
        self.format_description_label = ui_qt.QtWidgets.QLabel("")
        self.format_description_label.setWordWrap(True)
        self.format_description_label.setStyleSheet("color: grey;")
        section.content_layout.addWidget(self.format_description_label)
        self.format_form_widget = ui_qt.QtWidgets.QWidget()
        self.format_form_layout = ui_qt.QtWidgets.QVBoxLayout(self.format_form_widget)
        self.format_form_layout.setContentsMargins(0, 0, 0, 0)
        self.format_form_layout.setSpacing(5)
        section.content_layout.addWidget(self.format_form_widget)
        return section

    def build_placement_section(self):
        """Builds the Placement section.

        Returns:
            CollapsibleSection: Section widget.
        """
        section = self.create_section(constants.SECTION_PLACEMENT, "Placement")
        layout = section.content_layout
        self.group_template_field = self.create_line_edit(
            "group_template", "{name}_grp", "Group name. Tokens: {name} = file name, {index} = file position."
        )
        layout.addLayout(
            self.create_row(
                None,
                self.create_checkbox(
                    "group_per_file", "Group each file", "Put each file's top-level nodes under its own group."
                ),
                self.group_template_field,
            )
        )
        self.parent_all_name_field = self.create_line_edit("parent_all_name", "imported_files_grp", "Top group name.")
        layout.addLayout(
            self.create_row(
                None,
                self.create_checkbox(
                    "parent_all", "Parent all under", "Put every imported file under one top-level group."
                ),
                self.parent_all_name_field,
            )
        )
        layout.addLayout(
            self.create_row(
                "Offset",
                self.create_combo(
                    "offset_mode",
                    constants.OFFSET_MODES,
                    "None: keep files where they are.\nLine: move each file by a step from the previous one.\n"
                    "Grid: arrange files in rows and columns.\n"
                    "Groups are moved when they exist; otherwise top-level nodes are moved through their "
                    "offsetParentMatrix, which keeps animation intact.",
                ),
            )
        )
        self.line_step_row = self.create_row_widget(
            "Step (X, Y, Z)",
            self.create_double("line_step_x", -1e7, 1e7, 2, "Distance between files along X."),
            self.create_double("line_step_y", -1e7, 1e7, 2, "Distance between files along Y."),
            self.create_double("line_step_z", -1e7, 1e7, 2, "Distance between files along Z."),
        )
        layout.addWidget(self.line_step_row)
        self.grid_rows_widget = ui_qt.QtWidgets.QWidget()
        grid_layout = ui_qt.QtWidgets.QVBoxLayout(self.grid_rows_widget)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(5)
        columns_spin = self.create_int("grid_columns", 0, 1000, "Columns per row. 0 picks a square grid automatically.")
        columns_spin.setSpecialValueText("Auto")
        grid_layout.addLayout(
            self.create_row(
                "Columns",
                columns_spin,
                self.create_combo("grid_plane", constants.GRID_PLANES, "Floor: rows along Z. Wall: rows along Y."),
            )
        )
        self.grid_spacing_a_spin = self.create_double("grid_spacing_a", 0, 1e7, 2, "Distance between columns (X).")
        self.grid_spacing_b_spin = self.create_double(
            "grid_spacing_b", 0, 1e7, 2, "Distance between rows (Z on the floor, Y on the wall)."
        )
        grid_layout.addLayout(self.create_row("Spacing", self.grid_spacing_a_spin, self.grid_spacing_b_spin))
        layout.addWidget(self.grid_rows_widget)
        self.auto_spacing_padding_label = ui_qt.QtWidgets.QLabel("Padding")
        self.auto_spacing_padding_spin = self.create_double(
            "auto_spacing_padding", 0, 1e7, 2, "Extra distance added around the largest file."
        )
        layout.addLayout(
            self.create_row(
                None,
                self.create_checkbox(
                    "auto_spacing",
                    "Auto spacing",
                    "Measure every file after importing and space them by the largest bounding box plus padding.\n"
                    "Placement then happens after all files are imported (after per-file scripts).",
                ),
                self.auto_spacing_padding_label,
                self.auto_spacing_padding_spin,
            )
        )
        layout.addWidget(
            self.create_checkbox("center_layout", "Center on origin", "Center the whole line or grid on the origin.")
        )
        layout.addWidget(
            self.create_checkbox(
                "protect_skinned_meshes",
                "Keep skinned meshes in place",
                "Skinned meshes already move with their joints. When a file is offset, its skinned meshes stop\n"
                "inheriting parent transforms (their world position is kept) so they are not moved twice.",
            )
        )
        self.layout_controls_name_field = self.create_line_edit(
            "layout_controls_name", "imported_files_layout",
            "Name of the locator holding the layout attributes. With \"Parent all under\", the top group is used.",
        )
        layout.addLayout(
            self.create_row(
                None,
                self.create_checkbox(
                    "create_layout_controls",
                    "Layout controls",
                    "Create attributes that keep driving the layout after importing: column/row spacing (or line\n"
                    "step), and for every file a labeled separator, an offset and a visibility toggle.\n"
                    "Placement then happens after all files are imported (after per-file scripts).",
                ),
                self.layout_controls_name_field,
            )
        )
        return section

    def build_scene_section(self):
        """Builds the Scene Settings section.

        Returns:
            CollapsibleSection: Section widget.
        """
        section = self.create_section(constants.SECTION_SCENE, "Scene Settings")
        layout = section.content_layout
        source_tooltip = (
            "Keep Current: do not change it.\nFirst File / Last File: read it from that file before importing.\n"
            "Custom: use the value on the right. Applied before importing so keys land on the right frames."
        )
        self.frame_rate_custom_combo = self.create_combo(
            "frame_rate_custom", constants.FRAME_RATES, "Custom frame rate (frames per second)."
        )
        self.frame_rate_custom_combo.setEditable(True)
        self.frame_rate_custom_combo.setValidator(ui_qt.QtGui.QDoubleValidator(0.001, 100000.0, 3))
        layout.addLayout(
            self.create_row(
                "Frame Rate",
                self.create_combo("frame_rate_source", constants.SCENE_SOURCES, source_tooltip),
                self.frame_rate_custom_combo,
            )
        )
        self.linear_unit_custom_combo = self.create_combo(
            "linear_unit_custom", constants.LINEAR_UNITS, "Custom linear unit."
        )
        layout.addLayout(
            self.create_row(
                "Linear Unit",
                self.create_combo("linear_unit_source", constants.SCENE_SOURCES, source_tooltip),
                self.linear_unit_custom_combo,
            )
        )
        self.up_axis_custom_combo = self.create_combo("up_axis_custom", constants.UP_AXES, "Custom up axis.")
        layout.addLayout(
            self.create_row(
                "Up Axis",
                self.create_combo("up_axis_source", constants.SCENE_SOURCES, source_tooltip),
                self.up_axis_custom_combo,
            )
        )
        layout.addLayout(
            self.create_row(
                "Timeline",
                self.create_combo(
                    "timeline_mode",
                    constants.TIMELINE_MODES,
                    "Keyframes (All Files): cover the keys of every imported file.\n"
                    "First File / Last File: use that file's stored range (Maya scenes, USD) or its keys.\n"
                    "Manual: use the range on the next row.\nKeep Current: do not change the timeline.",
                ),
            )
        )
        self.timeline_start_spin = self.create_double("timeline_start", -1e7, 1e7, 2, "Manual start frame.")
        self.timeline_end_spin = self.create_double("timeline_end", -1e7, 1e7, 2, "Manual end frame.")
        layout.addLayout(self.create_row("Start / End", self.timeline_start_spin, self.timeline_end_spin))
        layout.addWidget(
            self.create_checkbox(
                "timeline_round",
                "Round range to whole frames",
                "Floor the start and ceil the end so fractional key times stay inside the range.",
            )
        )
        layout.addWidget(
            self.create_checkbox(
                "reapply_scene_settings",
                "Reapply after importing",
                "Set the frame rate, unit and up axis again after every file is imported, in case an importer\n"
                '(e.g. FBX with "Let FBX Set Frame Rate") changed them. "Keep Current" restores the value the\n'
                "scene had before importing. Keys keep their real-world timing when the frame rate changes.",
            )
        )
        return section

    def build_preferences_section(self):
        """Builds the Preferences section (settings files and tool behavior).

        Returns:
            CollapsibleSection: Section widget.
        """
        section = self.create_section(constants.SECTION_PREFERENCES, "Preferences")
        layout = section.content_layout
        layout.addWidget(
            self.create_checkbox(
                "new_scene_on_import",
                "Start a new scene when importing",
                "Clicking Import first starts a new scene. You are asked to save unsaved changes;\n"
                "cancelling that question cancels the import.",
            )
        )
        layout.addWidget(
            self.create_checkbox(
                "keep_file_list",
                "Keep file list between sessions",
                "Remember the file list (and checked states) when the tool is closed and opened again.",
            )
        )
        layout.addWidget(
            self.create_checkbox(
                "remember_section_states",
                "Remember expanded sections",
                "Open the tool with the same sections expanded as last time. Off: every section starts collapsed.",
            )
        )
        layout.addWidget(
            self.create_checkbox(
                "include_files_in_export",
                "Include file list in exported settings",
                "Export Settings also saves the file list; Import Settings adds those files to the list.",
            )
        )
        buttons_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.export_settings_btn = ui_qt.QtWidgets.QPushButton("Export Settings...")
        self.export_settings_btn.setToolTip("Save every setting and format option to a JSON file.")
        self.import_settings_btn = ui_qt.QtWidgets.QPushButton("Import Settings...")
        self.import_settings_btn.setToolTip("Load settings and format options from a JSON file.")
        self.reset_btn = ui_qt.QtWidgets.QPushButton("Reset Settings")
        self.reset_btn.setToolTip("Restore every setting to its default. The file list is kept.")
        for button in [self.export_settings_btn, self.import_settings_btn, self.reset_btn]:
            buttons_layout.addWidget(button)
        layout.addLayout(buttons_layout)
        return section

    def build_review_section(self):
        """Builds the Review Overrides section. Each override has a checkbox enabling it.

        Returns:
            CollapsibleSection: Section widget.
        """
        section = self.create_section(constants.SECTION_REVIEW, "Review Overrides")
        layout = section.content_layout
        hint_label = ui_qt.QtWidgets.QLabel("Applied once after importing. Unchecked items are left as they are.")
        hint_label.setStyleSheet("color: grey;")
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)
        self.review_value_widgets = {}
        review_rows = [
            ("review_anti_aliasing", "Anti-aliasing", "review_anti_aliasing_samples",
             constants.ANTI_ALIASING_SAMPLES, "Enable multisample anti-aliasing with this sample count."),
            ("review_textures", "Textures", "review_textures_value", constants.VISIBILITY_VALUES,
             "Show or hide textures in every viewport."),
            ("review_joints", "Joints", "review_joints_value", constants.VISIBILITY_VALUES,
             "Show or hide joints in every viewport (display filter only, joints are not changed)."),
            ("review_shading", "Shading", "review_shading_value", constants.SHADING_VALUES,
             "Viewport shading mode."),
            ("review_lighting", "Lighting", "review_lighting_value", constants.LIGHTING_VALUES,
             "Viewport lighting mode."),
            ("review_grid", "Grid", "review_grid_value", constants.VISIBILITY_VALUES,
             "Show or hide the viewport grid."),
        ]
        for checkbox_key, label, value_key, values, tooltip in review_rows:
            checkbox = self.create_checkbox(checkbox_key, label, tooltip)
            checkbox.setMinimumWidth(LABEL_WIDTH)
            value_combo = self.create_combo(value_key, values, tooltip)
            self.review_value_widgets[checkbox_key] = [value_combo]
            layout.addLayout(self.create_row(None, checkbox, value_combo))
        clip_checkbox = self.create_checkbox(
            "review_clip_planes", "Clip Planes", "Near and far clip planes of every perspective camera."
        )
        clip_checkbox.setMinimumWidth(LABEL_WIDTH)
        clip_near_spin = self.create_double("review_clip_near", 0.0001, 1e8, 4, "Near clip plane.")
        clip_far_spin = self.create_double("review_clip_far", 0.001, 1e9, 1, "Far clip plane.")
        self.review_value_widgets["review_clip_planes"] = [clip_near_spin, clip_far_spin]
        layout.addLayout(self.create_row(None, clip_checkbox, clip_near_spin, clip_far_spin))
        actions_layout = ui_qt.QtWidgets.QGridLayout()
        actions_layout.setContentsMargins(0, 2, 0, 0)
        actions_layout.addWidget(
            self.create_checkbox("review_frame_content", "Frame imported content", "Frame the imported files in "
                                 "every visible viewport."), 0, 0
        )
        actions_layout.addWidget(
            self.create_checkbox("review_go_to_start", "Go to start frame", "Move the current time to the "
                                 "timeline start."), 0, 1
        )
        actions_layout.addWidget(
            self.create_checkbox("review_clear_selection", "Clear selection", "Deselect everything when done."), 1, 0
        )
        layout.addLayout(actions_layout)
        return section

    def build_scripts_section(self):
        """Builds the Scripts section.

        Returns:
            CollapsibleSection: Section widget.
        """
        section = self.create_section(constants.SECTION_SCRIPTS, "Scripts")
        layout = section.content_layout
        self.per_file_editor, self.per_file_load_btn = self.create_script_block(
            layout,
            "per_file_script_enabled",
            "per_file_script",
            "Run after each file",
            f"Runs after each file is imported and organized.\nVariables: {constants.PER_FILE_SCRIPT_VARIABLES}",
        )
        self.post_editor, self.post_load_btn = self.create_script_block(
            layout,
            "post_script_enabled",
            "post_script",
            "Run after all files",
            "Runs once at the end (also after a cancel), after the timeline and review overrides.\n"
            f"Variables: {constants.POST_SCRIPT_VARIABLES}",
        )
        return section

    def create_script_block(self, layout, enabled_key, code_key, label, tooltip):
        """Creates an enable checkbox, a load button and a Python editor.

        Args:
            layout (QLayout): Layout receiving the widgets.
            enabled_key (str): Setting key of the checkbox.
            code_key (str): Setting key of the script text.
            label (str): Checkbox label.
            tooltip (str): Help text.

        Returns:
            tuple: (LineTextWidget editor, QPushButton load button).
        """
        checkbox = self.create_checkbox(enabled_key, label, tooltip)
        load_btn = ui_qt.QtWidgets.QPushButton("Load...")
        load_btn.setToolTip("Load the script text from a .py file.")
        header_layout = ui_qt.QtWidgets.QHBoxLayout()
        header_layout.addWidget(checkbox)
        header_layout.addStretch()
        header_layout.addWidget(load_btn)
        layout.addLayout(header_layout)
        editor = LineTextWidget(self)
        editor.setMinimumHeight(110)
        editor.setToolTip(tooltip)
        PythonSyntaxHighlighter(editor.get_text_edit().document())
        editor.get_text_edit().setPlaceholderText(f"# {tooltip.splitlines()[-1]}")
        self.setting_widgets[code_key] = editor
        layout.addWidget(editor)
        return editor, load_btn

    def build_progress_row(self):
        """Builds the progress bar row, hidden while idle.

        Returns:
            QHBoxLayout: Progress row.
        """
        progress_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.progress_bar = ui_qt.QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v / %m")
        self.progress_label = ui_qt.QtWidgets.QLabel("")
        self.progress_label.setMinimumWidth(80)
        self.cancel_btn = ui_qt.QtWidgets.QPushButton("Cancel")
        self.cancel_btn.setToolTip("Stop after the file being imported finishes.")
        progress_layout.addWidget(self.progress_bar, 2)
        progress_layout.addWidget(self.progress_label, 1)
        progress_layout.addWidget(self.cancel_btn)
        self.progress_widgets = [self.progress_bar, self.progress_label, self.cancel_btn]
        for widget in self.progress_widgets:
            widget.setVisible(False)
        return progress_layout

    # ------------------------------------------------------------------ widget factories
    def create_checkbox(self, key, label, tooltip=""):
        """Creates a checkbox bound to a setting.

        Args:
            key (str): Setting key.
            label (str): Checkbox text.
            tooltip (str, optional): Help text.

        Returns:
            QCheckBox: Created checkbox.
        """
        checkbox = ui_qt.QtWidgets.QCheckBox(label)
        checkbox.setToolTip(tooltip)
        self.setting_widgets[key] = checkbox
        return checkbox

    def create_combo(self, key, items, tooltip=""):
        """Creates a combo box bound to a setting.

        Args:
            key (str): Setting key.
            items (list): Combo items.
            tooltip (str, optional): Help text.

        Returns:
            QComboBox: Created combo box.
        """
        combo = ui_qt.QtWidgets.QComboBox()
        combo.addItems([str(item) for item in items])
        combo.setToolTip(tooltip)
        self.setting_widgets[key] = combo
        return combo

    def create_line_edit(self, key, placeholder="", tooltip=""):
        """Creates a line edit bound to a setting.

        Args:
            key (str): Setting key.
            placeholder (str, optional): Placeholder text.
            tooltip (str, optional): Help text.

        Returns:
            QLineEdit: Created line edit.
        """
        line_edit = ui_qt.QtWidgets.QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        line_edit.setToolTip(tooltip)
        self.setting_widgets[key] = line_edit
        return line_edit

    def create_double(self, key, minimum, maximum, decimals=2, tooltip=""):
        """Creates a double spin box bound to a setting.

        Args:
            key (str): Setting key.
            minimum (float): Minimum value.
            maximum (float): Maximum value.
            decimals (int, optional): Decimals shown.
            tooltip (str, optional): Help text.

        Returns:
            QDoubleSpinBox: Created spin box.
        """
        spin_box = ui_qt.QtWidgets.QDoubleSpinBox()
        spin_box.setRange(minimum, maximum)
        spin_box.setDecimals(decimals)
        spin_box.setToolTip(tooltip)
        spin_box.setKeyboardTracking(False)
        if key:
            self.setting_widgets[key] = spin_box
        return spin_box

    def create_int(self, key, minimum, maximum, tooltip=""):
        """Creates an integer spin box bound to a setting.

        Args:
            key (str): Setting key.
            minimum (int): Minimum value.
            maximum (int): Maximum value.
            tooltip (str, optional): Help text.

        Returns:
            QSpinBox: Created spin box.
        """
        spin_box = ui_qt.QtWidgets.QSpinBox()
        spin_box.setRange(minimum, maximum)
        spin_box.setToolTip(tooltip)
        spin_box.setKeyboardTracking(False)
        if key:
            self.setting_widgets[key] = spin_box
        return spin_box

    def create_row(self, label_text, *widgets):
        """Creates a row with an optional fixed-width label and widgets that share the space.

        Args:
            label_text (str): Label text, or None for no label.
            *widgets (QWidget): Widgets to place after the label.

        Returns:
            QHBoxLayout: Row layout.
        """
        row_layout = ui_qt.QtWidgets.QHBoxLayout()
        row_layout.setSpacing(6)
        label = None
        if label_text is not None:
            label = ui_qt.QtWidgets.QLabel(label_text)
            label.setFixedWidth(LABEL_WIDTH)
            row_layout.addWidget(label)
        for widget in widgets:
            row_layout.addWidget(widget, 1)
        if label is not None:
            for widget in widgets:
                self.row_labels[id(widget)] = (label, list(widgets))
        return row_layout

    def set_widget_enabled(self, widget, enabled):
        """Enables or disables a widget. Its row label greys out once every widget of the row is disabled.

        Args:
            widget (QWidget): Widget to update.
            enabled (bool): New state.
        """
        widget.setEnabled(bool(enabled))
        label, row_widgets = self.row_labels.get(id(widget), (None, []))
        if label is not None:
            label.setEnabled(any(row_widget.isEnabled() for row_widget in row_widgets))

    def create_row_widget(self, label_text, *widgets):
        """Creates a row wrapped in a widget, so it can be shown or hidden.

        Args:
            label_text (str): Label text, or None.
            *widgets (QWidget): Widgets in the row.

        Returns:
            QWidget: Row widget.
        """
        row_widget = ui_qt.QtWidgets.QWidget()
        row_layout = self.create_row(label_text, *widgets)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_widget.setLayout(row_layout)
        return row_widget

    # ------------------------------------------------------------------ settings binding
    @staticmethod
    def read_widget_value(widget):
        """Reads the value of a bound widget.

        Args:
            widget (QWidget): Bound widget.

        Returns:
            object: Widget value.
        """
        if isinstance(widget, ui_qt.QtWidgets.QCheckBox):
            return widget.isChecked()
        if isinstance(widget, ui_qt.QtWidgets.QComboBox):
            data = widget.currentData()
            return data if data is not None else widget.currentText()
        if isinstance(widget, (ui_qt.QtWidgets.QSpinBox, ui_qt.QtWidgets.QDoubleSpinBox)):
            return widget.value()
        if isinstance(widget, ui_qt.QtWidgets.QLineEdit):
            return widget.text()
        if isinstance(widget, LineTextWidget):
            return widget.get_text_edit().toPlainText()
        return None

    @staticmethod
    def write_widget_value(widget, value):
        """Writes a value to a bound widget without emitting change signals.

        Args:
            widget (QWidget): Bound widget.
            value (object): Value to show.
        """
        target_widget = widget.get_text_edit() if isinstance(widget, LineTextWidget) else widget
        blocked = target_widget.blockSignals(True)
        try:
            if isinstance(widget, ui_qt.QtWidgets.QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, ui_qt.QtWidgets.QComboBox):
                data_index = widget.findData(value)
                text_index = data_index if data_index >= 0 else widget.findText(str(value))
                if text_index >= 0:
                    widget.setCurrentIndex(text_index)
                elif widget.isEditable():
                    widget.setEditText(str(value))
            elif isinstance(widget, ui_qt.QtWidgets.QSpinBox):
                widget.setValue(int(value))
            elif isinstance(widget, ui_qt.QtWidgets.QDoubleSpinBox):
                widget.setValue(float(value))
            elif isinstance(widget, ui_qt.QtWidgets.QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, LineTextWidget):
                if widget.get_text_edit().toPlainText() != str(value):
                    widget.get_text_edit().setPlainText(str(value))
        finally:
            target_widget.blockSignals(blocked)

    def get_settings(self):
        """Reads every bound setting.

        Returns:
            dict: Setting key to value.
        """
        return {key: self.read_widget_value(widget) for key, widget in self.setting_widgets.items()}

    def set_settings(self, settings):
        """Shows settings in their widgets.

        Args:
            settings (dict): Setting key to value.
        """
        for key, value in (settings or {}).items():
            widget = self.setting_widgets.get(key)
            if widget is not None:
                self.write_widget_value(widget, value)
        self.refresh_enabled_states()

    def connect_setting_changes(self, callback):
        """Calls a function whenever any bound setting changes.

        Args:
            callback (callable): Function called without arguments.
        """
        for widget in self.setting_widgets.values():
            self.connect_widget_change(widget, callback)

    @staticmethod
    def connect_widget_change(widget, callback):
        """Connects the change signal of one widget.

        Args:
            widget (QWidget): Widget.
            callback (callable): Function called without arguments.
        """
        if isinstance(widget, ui_qt.QtWidgets.QCheckBox):
            widget.toggled.connect(lambda *args: callback())
        elif isinstance(widget, ui_qt.QtWidgets.QComboBox):
            widget.currentIndexChanged.connect(lambda *args: callback())
            if widget.isEditable():
                widget.editTextChanged.connect(lambda *args: callback())
        elif isinstance(widget, (ui_qt.QtWidgets.QSpinBox, ui_qt.QtWidgets.QDoubleSpinBox)):
            widget.valueChanged.connect(lambda *args: callback())
        elif isinstance(widget, ui_qt.QtWidgets.QLineEdit):
            widget.textChanged.connect(lambda *args: callback())
        elif isinstance(widget, LineTextWidget):
            widget.get_text_edit().textChanged.connect(lambda *args: callback())

    def set_filter_items(self, items):
        """Sets the format filter items.

        Args:
            items (list): (label, key) tuples.
        """
        blocked = self.filter_combo.blockSignals(True)
        self.filter_combo.clear()
        for label, key in items:
            self.filter_combo.addItem(label, key)
        self.filter_combo.blockSignals(blocked)

    def set_script_text(self, code_key, text):
        """Replaces the text of a script editor and notifies listeners.

        Args:
            code_key (str): "per_file_script" or "post_script".
            text (str): Script text.
        """
        editor = self.setting_widgets.get(code_key)
        if editor is not None:
            editor.get_text_edit().setPlainText(text)

    def refresh_enabled_states(self):
        """Enables or shows dependent widgets based on the current settings."""
        settings = self.get_settings()
        set_enabled = self.set_widget_enabled
        set_enabled(self.namespace_template_field, settings["namespace_mode"] == constants.NAMESPACE_CUSTOM)
        set_enabled(self.group_template_field, settings["group_per_file"])
        set_enabled(self.parent_all_name_field, settings["parent_all"])
        offset_mode = settings["offset_mode"]
        self.line_step_row.setVisible(offset_mode == constants.OFFSET_LINE)
        self.grid_rows_widget.setVisible(offset_mode == constants.OFFSET_GRID)
        has_offset = offset_mode != constants.OFFSET_NONE
        set_enabled(self.setting_widgets["auto_spacing"], has_offset)
        set_enabled(self.setting_widgets["center_layout"], has_offset)
        set_enabled(self.layout_controls_name_field, settings["create_layout_controls"] and not settings["parent_all"])
        set_enabled(self.auto_spacing_padding_spin, has_offset and settings["auto_spacing"])
        self.auto_spacing_padding_label.setEnabled(has_offset and settings["auto_spacing"])
        uses_fixed_spacing = not settings["auto_spacing"]
        set_enabled(self.grid_spacing_a_spin, uses_fixed_spacing)
        set_enabled(self.grid_spacing_b_spin, uses_fixed_spacing)
        set_enabled(self.frame_rate_custom_combo, settings["frame_rate_source"] == constants.SOURCE_CUSTOM)
        set_enabled(self.linear_unit_custom_combo, settings["linear_unit_source"] == constants.SOURCE_CUSTOM)
        set_enabled(self.up_axis_custom_combo, settings["up_axis_source"] == constants.SOURCE_CUSTOM)
        is_manual = settings["timeline_mode"] == constants.TIMELINE_MANUAL
        set_enabled(self.timeline_start_spin, is_manual)
        set_enabled(self.timeline_end_spin, is_manual)
        set_enabled(self.setting_widgets["timeline_round"], settings["timeline_mode"] != constants.TIMELINE_KEEP
                    and not is_manual)
        for checkbox_key, value_widgets in self.review_value_widgets.items():
            for value_widget in value_widgets:
                set_enabled(value_widget, bool(settings[checkbox_key]))
        set_enabled(self.per_file_editor, settings["per_file_script_enabled"])
        set_enabled(self.per_file_load_btn, settings["per_file_script_enabled"])
        set_enabled(self.post_editor, settings["post_script_enabled"])
        set_enabled(self.post_load_btn, settings["post_script_enabled"])

    # ------------------------------------------------------------------ format options
    def set_format_items(self, items):
        """Sets the formats listed in the Format Options section.

        Args:
            items (list): (label, key) tuples.
        """
        blocked = self.format_combo.blockSignals(True)
        self.format_combo.clear()
        for label, key in items:
            self.format_combo.addItem(label, key)
        self.format_combo.blockSignals(blocked)

    def get_selected_format_key(self):
        """Gets the importer key selected in the Format Options section.

        Returns:
            str: Importer key, or an empty string.
        """
        return self.format_combo.currentData() or ""

    def set_format_options(self, description, options, values, on_change):
        """Rebuilds the option form for one format.

        Args:
            description (str): Format description.
            options (list): ImportOption objects.
            values (dict): Current option values.
            on_change (callable): Called without arguments when any option changes.
        """
        while self.format_form_layout.count():
            item = self.format_form_layout.takeAt(0)
            item_widget = item.widget()
            if item_widget is not None:
                item_widget.deleteLater()
        self.format_option_widgets = {}
        self.format_description_label.setText(description)
        if not options:
            empty_label = ui_qt.QtWidgets.QLabel("This format has no options.")
            empty_label.setStyleSheet("color: grey;")
            self.format_form_layout.addWidget(empty_label)
            return
        for option in options:
            option_widget = self.create_option_widget(option)
            self.write_widget_value(option_widget, values.get(option.key, option.default))
            self.connect_widget_change(option_widget, on_change)
            self.format_option_widgets[option.key] = option_widget
            if isinstance(option_widget, ui_qt.QtWidgets.QCheckBox):
                row_widget = self.create_row_widget(None, option_widget)
            else:
                row_widget = self.create_row_widget(option.label, option_widget)
            self.format_form_layout.addWidget(row_widget)

    def create_option_widget(self, option):
        """Creates the widget for one importer option.

        Args:
            option (ImportOption): Option description.

        Returns:
            QWidget: Option widget (not bound to tool settings).
        """
        if option.option_type == "bool":
            option_widget = ui_qt.QtWidgets.QCheckBox(option.label)
        elif option.option_type == "choice":
            option_widget = ui_qt.QtWidgets.QComboBox()
            option_widget.addItems([str(choice) for choice in option.choices])
        elif option.option_type == "int":
            option_widget = ui_qt.QtWidgets.QSpinBox()
            option_widget.setRange(
                int(option.minimum) if option.minimum is not None else -10000000,
                int(option.maximum) if option.maximum is not None else 10000000,
            )
            option_widget.setKeyboardTracking(False)
        elif option.option_type == "float":
            option_widget = ui_qt.QtWidgets.QDoubleSpinBox()
            option_widget.setDecimals(option.decimals)
            option_widget.setRange(
                float(option.minimum) if option.minimum is not None else -1e9,
                float(option.maximum) if option.maximum is not None else 1e9,
            )
            option_widget.setKeyboardTracking(False)
        else:
            option_widget = ui_qt.QtWidgets.QLineEdit()
        option_widget.setToolTip(option.tooltip)
        return option_widget

    def get_format_values(self):
        """Reads the values of the current format form.

        Returns:
            dict: Option key to value.
        """
        return {key: self.read_widget_value(widget) for key, widget in self.format_option_widgets.items()}

    # ------------------------------------------------------------------ file list
    def set_entries(self, entries):
        """Rebuilds the file list.

        Args:
            entries (list): FileEntry objects, in order.
        """
        blocked = self.file_list.blockSignals(True)
        self.file_list.clear()
        for entry in entries:
            item = ui_qt.QtWidgets.QTreeWidgetItem()
            item.setData(COLUMN_FILE, ENTRY_ID_ROLE, entry.entry_id)
            item.setFlags(item.flags() | ui_qt.QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            self.file_list.addTopLevelItem(item)
            self.update_entry_item(item, entry)
        self.file_list.blockSignals(blocked)
        self.update_counts(entries)

    def update_counts(self, entries):
        """Updates the checked-file count and the import button text.

        Args:
            entries (list): FileEntry objects.
        """
        enabled_count = len([entry for entry in entries if entry.enabled])
        self.file_count_label.setText(f"{enabled_count} of {len(entries)} files checked" if entries else "No files")
        self.import_btn.setText(f"Import {enabled_count} File{'s' if enabled_count != 1 else ''}")
        self.update_import_button_size()

    def update_import_button_size(self):
        """Keeps the import button tall and wide enough for its text (it uses a padded stylesheet)."""
        text_size = self.import_btn.fontMetrics().size(0, "Import 0000 Files")
        self.import_btn.setMinimumHeight(max(34, self.import_btn.sizeHint().height(), text_size.height() + 18))
        self.import_btn.setMinimumWidth(text_size.width() + 40)

    def update_entry(self, entry):
        """Updates the row of one entry.

        Args:
            entry (FileEntry): Entry to show.
        """
        for item_index in range(self.file_list.topLevelItemCount()):
            item = self.file_list.topLevelItem(item_index)
            if item.data(COLUMN_FILE, ENTRY_ID_ROLE) == entry.entry_id:
                blocked = self.file_list.blockSignals(True)
                self.update_entry_item(item, entry)
                self.file_list.blockSignals(blocked)
                self.file_list.scrollToItem(item)
                return

    @staticmethod
    def update_entry_item(item, entry):
        """Writes an entry into a tree item.

        Args:
            item (QTreeWidgetItem): Item to update.
            entry (FileEntry): Entry to show.
        """
        item.setText(COLUMN_FILE, entry.name)
        item.setText(COLUMN_FORMAT, entry.get_format_label())
        item.setText(COLUMN_STATUS, entry.status)
        item.setText(COLUMN_FOLDER, entry.folder)
        check_state = ui_qt.QtCore.Qt.CheckState.Checked if entry.enabled else ui_qt.QtCore.Qt.CheckState.Unchecked
        item.setCheckState(COLUMN_FILE, check_state)
        tooltip = entry.path + (f"\n{entry.status}: {entry.message}" if entry.message else "")
        for column in range(len(COLUMN_LABELS)):
            item.setToolTip(column, tooltip)
        item.setForeground(COLUMN_STATUS, ui_qt.QtGui.QColor(*STATUS_COLORS.get(entry.status, (150, 150, 150))))

    def get_item_entry_id(self, item):
        """Gets the entry ID stored on a tree item.

        Args:
            item (QTreeWidgetItem): Tree item.

        Returns:
            str: Entry ID.
        """
        return item.data(COLUMN_FILE, ENTRY_ID_ROLE)

    @staticmethod
    def is_item_checked(item):
        """Checks whether a tree item is checked.

        Args:
            item (QTreeWidgetItem): Tree item.

        Returns:
            bool: Checked state.
        """
        return item.checkState(COLUMN_FILE) == ui_qt.QtCore.Qt.CheckState.Checked

    def select_entries(self, entry_ids):
        """Selects the rows of the given entries.

        Args:
            entry_ids (list): Entry IDs to select.
        """
        entry_ids = set(entry_ids or [])
        self.file_list.clearSelection()
        for item_index in range(self.file_list.topLevelItemCount()):
            item = self.file_list.topLevelItem(item_index)
            if self.get_item_entry_id(item) in entry_ids:
                item.setSelected(True)

    def get_selected_entry_ids(self):
        """Gets the IDs of the selected rows.

        Returns:
            list: Entry IDs.
        """
        return [self.get_item_entry_id(item) for item in self.file_list.selectedItems()]

    # ------------------------------------------------------------------ progress and status
    def set_running(self, is_running):
        """Switches between idle and running states.

        Args:
            is_running (bool): Whether an import is running.
        """
        for widget in self.progress_widgets:
            widget.setVisible(is_running)
        self.cancel_btn.setEnabled(is_running)
        for widget in [self.import_btn, self.add_files_btn, self.add_folder_btn, self.remove_btn,
                       self.clear_btn, self.sort_btn, self.file_list]:
            widget.setEnabled(not is_running)
        for section in self.sections.values():
            section.content_widget.setEnabled(not is_running)
        self.file_list.setAcceptDrops(not is_running)

    def set_progress(self, completed_count, total_count, text=""):
        """Updates the progress bar.

        Args:
            completed_count (int): Files finished.
            total_count (int): Total files.
            text (str, optional): Text next to the bar, usually the current file.
        """
        self.progress_bar.setMaximum(max(1, int(total_count)))
        self.progress_bar.setValue(int(completed_count))
        self.progress_label.setText(text)
        self.progress_label.setToolTip(text)

    def set_cancel_requested(self):
        """Shows that a cancel is pending."""
        self.cancel_btn.setEnabled(False)
        self.progress_label.setText("Cancelling after the current file...")

    def set_status(self, text, status=ui_qt_utils.StatusLine.INFO):
        """Shows a message in the status line.

        Args:
            text (str): Message.
            status (str, optional): One of ui_qt_utils.StatusLine values.
        """
        ui_qt_utils.set_status_line_text(self.status_line, text, status=status, pulse=None)
        self.status_line.setToolTip(text)

    # ------------------------------------------------------------------ sizing
    def fit_to_contents(self):
        """Resizes the window to the smallest size that shows the table and sections without scroll bars.

        Only the initial size is set; the user can resize freely afterwards. Docked windows are sized by Maya.
        """
        settings_height = self.settings_container.sizeHint().height()
        screen_height = 900
        screen = ui_qt.QtWidgets.QApplication.primaryScreen()
        if screen is not None:
            screen_height = screen.availableGeometry().height()
        self.settings_scroll.setMinimumHeight(min(settings_height, int(screen_height * 0.45)))
        header_width = sum(self.file_list.columnWidth(column) for column in range(len(COLUMN_LABELS) - 1))
        table_width = header_width + 120 + self.file_list.frameWidth() * 2
        self.adjustSize()
        width = max(WINDOW_MINIMUM_WIDTH, table_width + 20, self.minimumSizeHint().width())
        height = self.minimumSizeHint().height()
        self.resize(width, height)
        self.splitter.setSizes([self.file_list.minimumHeight() + 70, settings_height])

    def is_floating_window(self):
        """Checks whether the window is floating (not docked in Maya).

        Returns:
            bool: True when floating or when docking is unavailable.
        """
        is_floating = getattr(self, "isFloating", None)
        if callable(is_floating):
            try:
                return bool(is_floating())
            except Exception as exception:
                logger.debug(f"Unable to read the docking state: {exception}")
        return True

    def fit_floating_window(self):
        """Fits the window (or its floating Maya workspace control) to the contents after it is shown."""
        if not self.is_floating_window():
            return
        self.fit_to_contents()
        top_window = self.window()
        if top_window is not self:
            top_window.resize(self.size())

    # ------------------------------------------------------------------ close
    def set_close_callback(self, callback):
        """Sets a function called when the window closes.

        Stored as "close_func", the name MayaWindowMeta clears on windows it replaces, so a window that is
        being replaced by a newer instance does not run (and save) its old state.

        Args:
            callback (callable): Function called without arguments.
        """
        self.close_func = callback

    def _run_close_callback(self):
        """Runs the close callback, ignoring errors from deleted Qt objects."""
        close_callback = getattr(self, "close_func", None)
        if not callable(close_callback):
            return
        try:
            close_callback()
        except RuntimeError as exception:
            logger.debug(f"Ignored close callback error: {exception}")

    def closeEvent(self, event):
        """Runs the close callback before closing.

        Args:
            event (QCloseEvent): Close event.
        """
        self._run_close_callback()
        super().closeEvent(event)

    def dockCloseEventTriggered(self):
        """Runs the close callback when the docked window closes."""
        self._run_close_callback()
