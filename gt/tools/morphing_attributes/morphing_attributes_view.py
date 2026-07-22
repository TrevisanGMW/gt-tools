"""
Morphing Attributes View

Qt recreation of the legacy "Add Morphing Attributes" window. The layout keeps
the original sections, ordering, and color language, but is fully driven by Qt
layouts so every element resizes gracefully with the window.
"""

from gt.tools.morphing_attributes import morphing_attributes_model as model
from gt.ui.qt_utils import MayaWindowMeta
import gt.ui.qt_utils as qt_utils
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt


class MorphingAttributesView(metaclass=MayaWindowMeta):
    """Compact, resizable Qt view for the Morphing Attributes tool."""

    WINDOW_TITLE = "Add Morphing Attributes"
    MIN_WIDTH = 300
    CONTROL_HEIGHT = 24
    BUTTON_HEIGHT = 28
    TITLE_BAR_HEIGHT = 22

    def __init__(self, parent=None, controller=None, version=None):
        """Initializes the Morphing Attributes view.

        Args:
            parent (QWidget, optional): Parent widget.
            controller (MorphingAttributesController, optional): Controller reference kept
                to avoid premature garbage collection.
            version (str, optional): Tool version shown in the window title.
        """
        super().__init__(parent=parent)
        self.controller = controller

        title = self.WINDOW_TITLE
        if version:
            title += "  (v{0})".format(str(version))
        self.setWindowTitle(title)
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_morphing_attributes))
        self.setMinimumWidth(self.MIN_WIDTH)
        self.setStyleSheet(self._build_stylesheet())

        self.help_btn = None
        self.load_morphing_btn = None
        self.source_status_btn = None
        self.blend_nodes_list = None
        self.load_holder_btn = None
        self.holder_status_btn = None
        self.desired_filter_field = None
        self.desired_filter_combo = None
        self.undesired_filter_field = None
        self.undesired_filter_combo = None
        self.ignore_case_chk = None
        self.add_separator_chk = None
        self.ignore_connected_chk = None
        self.sort_chk = None
        self.modify_range_chk = None
        self.delete_instead_chk = None
        self.old_min_spin = None
        self.old_max_spin = None
        self.new_min_spin = None
        self.new_max_spin = None
        self.range_widget = None
        self.create_btn = None

        self.build_widgets()

        # Start as small as possible when floating, while remaining resizable.
        self.adjustSize()
        compact_height = self.minimumSizeHint().height()
        if compact_height > 0:
            self.resize(self.width(), compact_height)
        qt_utils.center_window(self)

    # --------------------------------------------------------------- Building
    def build_widgets(self):
        """Builds and arranges every widget in the view."""
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(6)

        main_layout.addWidget(self._build_title_bar())

        # 1. Deformed Mesh (Source)
        main_layout.addWidget(self._build_section_label("1. Deformed Mesh (Source):"))
        source_row = ui_qt.QtWidgets.QHBoxLayout()
        source_row.setSpacing(6)
        self.load_morphing_btn = self._create_action_button("Load Morphing Object")
        self.load_morphing_btn.setToolTip("Select a mesh with a blend shape node and load it as the source.")
        self.source_status_btn = self._create_status_button()
        self.source_status_btn.setToolTip("Select the loaded morphing object.")
        source_row.addWidget(self.load_morphing_btn)
        source_row.addWidget(self.source_status_btn)
        main_layout.addLayout(source_row)

        blend_label = ui_qt.QtWidgets.QLabel("Blend Shape Nodes:")
        blend_label.setObjectName("hintLabel")
        main_layout.addWidget(blend_label)
        self.blend_nodes_list = ui_qt.QtWidgets.QListWidget()
        self.blend_nodes_list.setMinimumHeight(70)
        self.blend_nodes_list.setToolTip("Blend shape nodes found on the loaded morphing object.")
        self.blend_nodes_list.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Expanding)
        main_layout.addWidget(self.blend_nodes_list, 1)

        # 2. Attribute Holder (Target)
        main_layout.addWidget(self._build_section_label("2. Attribute Holder (Target):"))
        holder_row = ui_qt.QtWidgets.QHBoxLayout()
        holder_row.setSpacing(6)
        self.load_holder_btn = self._create_action_button("Load Attribute Holder")
        self.load_holder_btn.setToolTip("Select the object that will receive the morphing attributes.")
        self.holder_status_btn = self._create_status_button()
        self.holder_status_btn.setToolTip("Select the loaded attribute holder.")
        holder_row.addWidget(self.load_holder_btn)
        holder_row.addWidget(self.holder_status_btn)
        main_layout.addLayout(holder_row)

        # 3. Settings and Filters
        main_layout.addWidget(self._build_separator("3. Settings and Filters"))
        main_layout.addLayout(self._build_filters_layout())
        main_layout.addLayout(self._build_options_layout())
        main_layout.addWidget(self._build_range_widget())

        main_layout.addWidget(self._build_line())
        self.create_btn = ui_qt.QtWidgets.QPushButton("Create Morphing Attributes")
        self.create_btn.setObjectName("primaryButton")
        self.create_btn.setFixedHeight(self.BUTTON_HEIGHT)
        self.create_btn.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        self.create_btn.setToolTip("Create (or delete) the morphing attributes using the settings above.")
        main_layout.addWidget(self.create_btn)

    def _build_title_bar(self):
        """Builds the dark title strip with the tool name and help button.

        Returns:
            QFrame: Title bar widget.
        """
        title_widget = ui_qt.QtWidgets.QFrame()
        title_widget.setObjectName("titleBar")
        title_widget.setFixedHeight(self.TITLE_BAR_HEIGHT)
        title_layout = ui_qt.QtWidgets.QHBoxLayout(title_widget)
        title_layout.setContentsMargins(8, 0, 2, 0)
        title_layout.setSpacing(4)
        title_label = ui_qt.QtWidgets.QLabel(self.WINDOW_TITLE)
        title_label.setObjectName("titleLabel")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        self.help_btn = ui_qt.QtWidgets.QPushButton("Help")
        self.help_btn.setObjectName("titleButton")
        self.help_btn.setFixedHeight(self.TITLE_BAR_HEIGHT - 4)
        self.help_btn.setToolTip("Open help information for this tool.")
        title_layout.addWidget(self.help_btn)
        return title_widget

    def _build_filters_layout(self):
        """Builds the desired/undesired filter rows.

        Returns:
            QVBoxLayout: Filter controls layout.
        """
        layout = ui_qt.QtWidgets.QVBoxLayout()
        layout.setSpacing(6)

        desired_row = ui_qt.QtWidgets.QHBoxLayout()
        desired_row.setSpacing(6)
        self.desired_filter_field = self._create_line_edit("Desired Filter (Optional)")
        self.desired_filter_field.setToolTip("Comma separated tokens. Only matching targets are added.")
        self.desired_filter_combo = self._create_filter_combo()
        desired_row.addWidget(self.desired_filter_field, 1)
        desired_row.addWidget(self.desired_filter_combo)
        layout.addLayout(desired_row)

        undesired_row = ui_qt.QtWidgets.QHBoxLayout()
        undesired_row.setSpacing(6)
        self.undesired_filter_field = self._create_line_edit("Undesired Filter (Optional)")
        self.undesired_filter_field.setToolTip("Comma separated tokens. Matching targets are ignored.")
        self.undesired_filter_combo = self._create_filter_combo()
        undesired_row.addWidget(self.undesired_filter_field, 1)
        undesired_row.addWidget(self.undesired_filter_combo)
        layout.addLayout(undesired_row)
        return layout

    def _build_options_layout(self):
        """Builds the two-column checkbox grid.

        Returns:
            QGridLayout: Checkbox grid layout.
        """
        grid = ui_qt.QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(4)
        grid.setContentsMargins(6, 2, 6, 2)

        self.ignore_case_chk = ui_qt.QtWidgets.QCheckBox("Ignore Uppercase")
        self.add_separator_chk = ui_qt.QtWidgets.QCheckBox("Add Separator")
        self.ignore_connected_chk = ui_qt.QtWidgets.QCheckBox("Ignore Connected")
        self.sort_chk = ui_qt.QtWidgets.QCheckBox("Sort Attributes")
        self.modify_range_chk = ui_qt.QtWidgets.QCheckBox("Modify Range")
        self.delete_instead_chk = ui_qt.QtWidgets.QCheckBox("Delete Instead")

        self.ignore_case_chk.setToolTip("Ignore letter casing when comparing filter tokens.")
        self.add_separator_chk.setToolTip("Add a locked enum attribute used as a visual separator.")
        self.ignore_connected_chk.setToolTip("Skip targets that already have an incoming connection.")
        self.sort_chk.setToolTip("Sort the created attributes alphabetically.")
        self.modify_range_chk.setToolTip("Remap the attribute range through a remapValue node.")
        self.delete_instead_chk.setToolTip("Delete the matching attributes instead of creating them.")

        grid.addWidget(self.ignore_case_chk, 0, 0)
        grid.addWidget(self.add_separator_chk, 0, 1)
        grid.addWidget(self.ignore_connected_chk, 1, 0)
        grid.addWidget(self.sort_chk, 1, 1)
        grid.addWidget(self.modify_range_chk, 2, 0)
        grid.addWidget(self.delete_instead_chk, 2, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        return grid

    def _build_range_widget(self):
        """Builds the old/new range spin box grid.

        Returns:
            QWidget: Range controls widget.
        """
        self.range_widget = ui_qt.QtWidgets.QWidget()
        grid = ui_qt.QtWidgets.QGridLayout(self.range_widget)
        grid.setContentsMargins(6, 2, 6, 2)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(4)

        self.old_min_spin = self._create_spin_box()
        self.old_max_spin = self._create_spin_box()
        self.new_min_spin = self._create_spin_box()
        self.new_max_spin = self._create_spin_box()

        grid.addWidget(self._create_row_label("Old Min:"), 0, 0)
        grid.addWidget(self.old_min_spin, 0, 1)
        grid.addWidget(self._create_row_label("Old Max:"), 0, 2)
        grid.addWidget(self.old_max_spin, 0, 3)
        grid.addWidget(self._create_row_label("New Min:"), 1, 0)
        grid.addWidget(self.new_min_spin, 1, 1)
        grid.addWidget(self._create_row_label("New Max:"), 1, 2)
        grid.addWidget(self.new_max_spin, 1, 3)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        return self.range_widget

    # ------------------------------------------------------------ Widget makers
    def _create_action_button(self, label):
        """Creates a neutral load/action button.

        Args:
            label (str): Button text.

        Returns:
            QPushButton: Created button.
        """
        button = ui_qt.QtWidgets.QPushButton(label)
        button.setObjectName("actionButton")
        button.setFixedHeight(self.BUTTON_HEIGHT)
        button.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        return button

    def _create_status_button(self):
        """Creates a status button used to display and re-select a loaded object.

        Returns:
            QPushButton: Created status button.
        """
        button = ui_qt.QtWidgets.QPushButton("Not loaded yet")
        button.setObjectName("statusButton")
        button.setFixedHeight(self.BUTTON_HEIGHT)
        button.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        return button

    def _create_line_edit(self, placeholder):
        """Creates a consistently sized line edit.

        Args:
            placeholder (str): Placeholder text.

        Returns:
            QLineEdit: Created field.
        """
        field = ui_qt.QtWidgets.QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setFixedHeight(self.CONTROL_HEIGHT)
        return field

    def _create_filter_combo(self):
        """Creates a filter-method combo box.

        Returns:
            QComboBox: Created combo box.
        """
        combo = ui_qt.QtWidgets.QComboBox()
        combo.addItems(model.FILTER_METHOD_LABELS)
        combo.setFixedHeight(self.CONTROL_HEIGHT)
        combo.setSizePolicy(ui_qt.QtLib.SizePolicy.Minimum, ui_qt.QtLib.SizePolicy.Fixed)
        return combo

    def _create_spin_box(self):
        """Creates an integer spin box for range values.

        Returns:
            QSpinBox: Created spin box.
        """
        spin = ui_qt.QtWidgets.QSpinBox()
        spin.setRange(-1000000, 1000000)
        spin.setFixedHeight(self.CONTROL_HEIGHT)
        spin.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        return spin

    @staticmethod
    def _create_row_label(text):
        """Creates a right-aligned range row label.

        Args:
            text (str): Label text.

        Returns:
            QLabel: Created label.
        """
        label = ui_qt.QtWidgets.QLabel(text)
        label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignRight | ui_qt.QtLib.AlignmentFlag.AlignVCenter)
        return label

    @staticmethod
    def _build_section_label(text):
        """Creates a bold section header label.

        Args:
            text (str): Header text.

        Returns:
            QLabel: Created label.
        """
        label = ui_qt.QtWidgets.QLabel(text)
        label.setObjectName("sectionHeader")
        label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        return label

    @staticmethod
    def _build_line():
        """Creates a plain horizontal divider line.

        Returns:
            QFrame: Divider line.
        """
        line = ui_qt.QtWidgets.QFrame()
        line.setFrameShape(ui_qt.QtLib.FrameStyle.HLine)
        line.setFrameShadow(ui_qt.QtLib.FrameStyle.Sunken)
        return line

    def _build_separator(self, text):
        """Creates a centered titled separator (line + label + line).

        Args:
            text (str): Separator title text.

        Returns:
            QWidget: Separator widget.
        """
        widget = ui_qt.QtWidgets.QWidget()
        layout = ui_qt.QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 4, 0, 2)
        layout.setSpacing(7)
        left_line = self._build_line()
        right_line = self._build_line()
        label = ui_qt.QtWidgets.QLabel(text)
        label.setObjectName("sectionLabel")
        label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        layout.addWidget(left_line, 1)
        layout.addWidget(label)
        layout.addWidget(right_line, 1)
        return widget

    # --------------------------------------------------------------- Utilities
    def set_status(self, target, text, state):
        """Updates a status button's text and color.

        Args:
            target (str): Which status button ("source" or "holder").
            text (str): Text to display.
            state (str): One of "idle", "loaded" or "failed".
        """
        button = self.source_status_btn if target == "source" else self.holder_status_btn
        button.setText(text)
        button.setProperty("state", state)
        button.style().unpolish(button)
        button.style().polish(button)

    def get_blend_nodes(self):
        """Gets the blend shape node names currently listed.

        Returns:
            list: Blend shape node names.
        """
        return [self.blend_nodes_list.item(row).text() for row in range(self.blend_nodes_list.count())]

    def set_blend_nodes(self, nodes):
        """Populates the blend shape node list.

        Args:
            nodes (list): Blend shape node names.
        """
        self.blend_nodes_list.clear()
        for node in nodes:
            self.blend_nodes_list.addItem(node)

    def get_selected_blend_node(self):
        """Gets the currently selected blend shape node.

        Returns:
            str: Selected blend shape node name, or an empty string.
        """
        item = self.blend_nodes_list.currentItem()
        return item.text() if item else ""

    @staticmethod
    def _build_stylesheet():
        """Builds the combined Maya base and tool-specific stylesheet.

        Returns:
            str: Stylesheet string.
        """
        return ui_res_lib.Stylesheet.maya_dialog_base + """
            QFrame#titleBar { background-color: #666666; border: 1px solid #6f6f6f; }
            QLabel#titleLabel { color: #f0f0f0; font-weight: bold; }
            QLabel#sectionHeader { color: #e0e0e0; font-weight: bold; }
            QLabel#sectionLabel { color: #aaaaaa; }
            QLabel#hintLabel { color: #aaaaaa; font-size: 10px; }
            QCheckBox { color: #dddddd; }
            QPushButton#titleButton { background: transparent; border: none; color: #e5e5e5; padding: 2px 10px; }
            QPushButton#titleButton:hover { background-color: #7a7a7a; }
            QPushButton#actionButton {
                background-color: #5c5c5c; border: 1px solid #444444; color: #dddddd; padding: 2px 6px;
            }
            QPushButton#actionButton:hover { background-color: #696969; }
            QPushButton#actionButton:pressed { background-color: #4b4b4b; }
            QPushButton#statusButton {
                background-color: #333333; border: 1px solid #444444; color: #dddddd; padding: 2px 6px;
            }
            QPushButton#statusButton[state="loaded"] { background-color: #99cc99; color: #1c1c1c; }
            QPushButton#statusButton[state="failed"] { background-color: #ff6666; color: #1c1c1c; }
            QPushButton#primaryButton {
                background-color: #999999; border: 1px solid #444444; color: #202020; padding: 2px 6px;
            }
            QPushButton#primaryButton:hover { background-color: #aaaaaa; }
            QPushButton#primaryButton:pressed { background-color: #4b4b4b; color: #dddddd; }
            QLineEdit, QSpinBox, QComboBox { background-color: #292929; border: 1px solid #444444; padding: 1px 4px; }
            QLineEdit:disabled, QSpinBox:disabled { background-color: #353535; color: #707070; }
            QListWidget { background-color: #292929; border: 1px solid #444444; }
        """


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = MorphingAttributesView()
        window.show()
