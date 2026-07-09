"""
Renamer View
"""

from gt.tools.renamer import renamer_model as model
from gt.ui.qt_utils import MayaWindowMeta
import gt.ui.qt_utils as qt_utils
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt


class RenamerView(metaclass=MayaWindowMeta):
    """Qt view for GT Renamer."""

    def __init__(self, parent=None, version=None):
        """Initializes the renamer view.

        Args:
            parent (QWidget, optional): Parent widget.
            version (str, optional): Tool version.
        """
        super().__init__(parent=parent)
        self.setWindowTitle("GT Renamer" + (" - (v{0})".format(version) if version else ""))
        self.setMinimumWidth(360)
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_renamer))
        self.build_widgets()
        qt_utils.center_window(self)

    def build_widgets(self):
        """Builds all view widgets."""
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        title_layout = ui_qt.QtWidgets.QHBoxLayout()
        title_label = ui_qt.QtWidgets.QLabel("GT Renamer")
        title_label.setStyleSheet("font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        self.reset_btn = ui_qt.QtWidgets.QPushButton("Reset")
        self.reset_btn.setToolTip("Reset persistent Renamer settings to defaults.")
        title_layout.addWidget(self.reset_btn)
        main_layout.addLayout(title_layout)

        main_layout.addWidget(self.create_separator("Selection"))
        scope_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.selection_group = ui_qt.QtWidgets.QButtonGroup(self)
        self.selected_radio = ui_qt.QtWidgets.QRadioButton(model.SELECTION_SELECTED)
        self.hierarchy_radio = ui_qt.QtWidgets.QRadioButton(model.SELECTION_HIERARCHY)
        self.all_radio = ui_qt.QtWidgets.QRadioButton(model.SELECTION_ALL)
        self.selected_radio.setToolTip("Rename only the current Maya selection.")
        self.hierarchy_radio.setToolTip("Rename the current Maya selection and its hierarchy.")
        self.all_radio.setToolTip("Rename all supported scene objects, excluding default Maya nodes.")
        for radio_btn in [self.selected_radio, self.hierarchy_radio, self.all_radio]:
            self.selection_group.addButton(radio_btn)
            radio_btn.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
            scope_layout.addWidget(radio_btn, 1)
        main_layout.addLayout(scope_layout)

        main_layout.addWidget(self.create_separator("Other Utilities"))
        utility_layout_one = ui_qt.QtWidgets.QHBoxLayout()
        utility_layout_two = ui_qt.QtWidgets.QHBoxLayout()
        self.remove_first_btn = self.create_action_button("Remove First", "neutral")
        self.remove_last_btn = self.create_action_button("Remove Last", "neutral")
        self.uppercase_btn = self.create_action_button("U-Case", "neutral")
        self.capitalize_btn = self.create_action_button("Capitalize", "neutral")
        self.lowercase_btn = self.create_action_button("L-Case", "neutral")
        self.remove_first_btn.setToolTip("Remove the first character from each target object name.")
        self.remove_last_btn.setToolTip("Remove the last character from each target object name.")
        self.uppercase_btn.setToolTip("Convert target object names to uppercase.")
        self.capitalize_btn.setToolTip("Capitalize target object names.")
        self.lowercase_btn.setToolTip("Convert target object names to lowercase.")
        utility_layout_one.addWidget(self.remove_first_btn)
        utility_layout_one.addWidget(self.remove_last_btn)
        utility_layout_two.addWidget(self.uppercase_btn)
        utility_layout_two.addWidget(self.capitalize_btn)
        utility_layout_two.addWidget(self.lowercase_btn)
        main_layout.addLayout(utility_layout_one)
        main_layout.addLayout(utility_layout_two)

        main_layout.addWidget(self.create_separator("Rename and Number / Letter"))
        rename_layout = ui_qt.QtWidgets.QHBoxLayout()
        rename_label = ui_qt.QtWidgets.QLabel("Rename:")
        rename_label.setMinimumWidth(58)
        self.rename_field = ui_qt.QtWidgets.QLineEdit()
        self.rename_field.setPlaceholderText("new_name")
        self.rename_field.setToolTip("Base name used by Rename and Number or Rename and Letter.")
        self.use_source_checkbox = ui_qt.QtWidgets.QCheckBox("Use Source")
        self.use_source_checkbox.setToolTip("Use each object's current name as the base name.")
        rename_layout.addWidget(rename_label)
        rename_layout.addWidget(self.rename_field)
        rename_layout.addWidget(self.use_source_checkbox)
        main_layout.addLayout(rename_layout)

        number_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.start_number_field = ui_qt.QtWidgets.QSpinBox()
        self.start_number_field.setRange(0, 999999)
        self.start_number_field.setToolTip("Number used by the first renamed object.")
        self.padding_number_field = ui_qt.QtWidgets.QSpinBox()
        self.padding_number_field.setRange(1, 12)
        self.padding_number_field.setToolTip("Minimum number of digits used by Rename and Number.")
        self.uppercase_checkbox = ui_qt.QtWidgets.QCheckBox("Uppercase")
        self.uppercase_checkbox.setToolTip("Use uppercase letters for Rename and Letter.")
        number_layout.addWidget(ui_qt.QtWidgets.QLabel("Start #:"))
        number_layout.addWidget(self.start_number_field)
        number_layout.addWidget(ui_qt.QtWidgets.QLabel("Padding:"))
        number_layout.addWidget(self.padding_number_field)
        number_layout.addWidget(self.uppercase_checkbox)
        main_layout.addLayout(number_layout)

        rename_button_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.rename_number_btn = self.create_action_button("Rename and Number", "blue")
        self.rename_letter_btn = self.create_action_button("Rename and Letter", "blue")
        self.rename_number_btn.setToolTip("Rename targets using the base name and an incrementing padded number.")
        self.rename_letter_btn.setToolTip("Rename targets using the base name and an incrementing letter suffix.")
        rename_button_layout.addWidget(self.rename_number_btn)
        rename_button_layout.addWidget(self.rename_letter_btn)
        main_layout.addLayout(rename_button_layout)

        main_layout.addWidget(self.create_separator("Prefix and Suffix"))
        self.prefix_group = ui_qt.QtWidgets.QButtonGroup(self)
        self.suffix_group = ui_qt.QtWidgets.QButtonGroup(self)
        prefix_mode_layout = self.create_mode_input_row("Prefix:", "prefix_")
        self.prefix_auto_radio = prefix_mode_layout["auto"]
        self.prefix_input_radio = prefix_mode_layout["input"]
        self.prefix_field = prefix_mode_layout["field"]
        self.prefix_group.addButton(self.prefix_auto_radio)
        self.prefix_group.addButton(self.prefix_input_radio)
        main_layout.addLayout(prefix_mode_layout["layout"])

        suffix_mode_layout = self.create_mode_input_row("Suffix:", "_suffix")
        self.suffix_auto_radio = suffix_mode_layout["auto"]
        self.suffix_input_radio = suffix_mode_layout["input"]
        self.suffix_field = suffix_mode_layout["field"]
        self.suffix_group.addButton(self.suffix_auto_radio)
        self.suffix_group.addButton(self.suffix_input_radio)
        main_layout.addLayout(suffix_mode_layout["layout"])

        suffix_grid = ui_qt.QtWidgets.QGridLayout()
        suffix_grid.setHorizontalSpacing(4)
        suffix_grid.setVerticalSpacing(3)
        self.transform_suffix_field = self.create_small_field()
        self.mesh_suffix_field = self.create_small_field()
        self.nurbs_crv_suffix_field = self.create_small_field()
        self.joint_suffix_field = self.create_small_field()
        self.locator_suffix_field = self.create_small_field()
        self.surface_suffix_field = self.create_small_field()
        self.add_grid_field(suffix_grid, 0, 0, "Group", self.transform_suffix_field)
        self.add_grid_field(suffix_grid, 0, 1, "Mesh", self.mesh_suffix_field)
        self.add_grid_field(suffix_grid, 0, 2, "Nurbs", self.nurbs_crv_suffix_field)
        self.add_grid_field(suffix_grid, 1, 0, "Joint", self.joint_suffix_field)
        self.add_grid_field(suffix_grid, 1, 1, "Locator", self.locator_suffix_field)
        self.add_grid_field(suffix_grid, 1, 2, "Surface", self.surface_suffix_field)
        main_layout.addLayout(suffix_grid)

        prefix_grid = ui_qt.QtWidgets.QGridLayout()
        prefix_grid.setHorizontalSpacing(4)
        prefix_grid.setVerticalSpacing(3)
        self.left_prefix_field = self.create_small_field()
        self.center_prefix_field = self.create_small_field()
        self.right_prefix_field = self.create_small_field()
        self.add_grid_field(prefix_grid, 0, 0, "Left", self.left_prefix_field)
        self.add_grid_field(prefix_grid, 0, 1, "Center", self.center_prefix_field)
        self.add_grid_field(prefix_grid, 0, 2, "Right", self.right_prefix_field)
        main_layout.addLayout(prefix_grid)

        prefix_button_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.add_prefix_btn = self.create_action_button("Add Prefix", "green")
        self.add_suffix_btn = self.create_action_button("Add Suffix", "green")
        self.add_prefix_btn.setToolTip("Add either an automatic position prefix or the manual prefix input.")
        self.add_suffix_btn.setToolTip("Add either an automatic type suffix or the manual suffix input.")
        prefix_button_layout.addWidget(self.add_prefix_btn)
        prefix_button_layout.addWidget(self.add_suffix_btn)
        main_layout.addLayout(prefix_button_layout)

        main_layout.addWidget(self.create_separator("Search and Replace"))
        search_layout = ui_qt.QtWidgets.QGridLayout()
        search_layout.setHorizontalSpacing(6)
        self.search_field = ui_qt.QtWidgets.QLineEdit()
        self.replace_field = ui_qt.QtWidgets.QLineEdit()
        self.search_field.setPlaceholderText("search_text")
        self.replace_field.setPlaceholderText("replace_text")
        self.search_field.setToolTip("Text to find in each target object name.")
        self.replace_field.setToolTip("Replacement text.")
        search_layout.addWidget(ui_qt.QtWidgets.QLabel("Search:"), 0, 0)
        search_layout.addWidget(self.search_field, 0, 1)
        search_layout.addWidget(ui_qt.QtWidgets.QLabel("Replace:"), 1, 0)
        search_layout.addWidget(self.replace_field, 1, 1)
        main_layout.addLayout(search_layout)
        self.search_replace_btn = self.create_action_button("Search and Replace", "orange")
        self.search_replace_btn.setToolTip("Replace matching text in target object names.")
        main_layout.addWidget(self.search_replace_btn)

        self.selected_radio.setChecked(True)
        self.prefix_auto_radio.setChecked(True)
        self.suffix_auto_radio.setChecked(True)
        self.refresh_enabled_states()

    @staticmethod
    def create_separator(text):
        """Creates a section separator.

        Args:
            text (str): Section text.

        Returns:
            QWidget: Separator widget.
        """
        widget = ui_qt.QtWidgets.QWidget()
        layout = ui_qt.QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 6, 0, 2)
        layout.setSpacing(8)
        label = ui_qt.QtWidgets.QLabel(text)
        label.setStyleSheet("color: grey; font-weight: bold;")
        line = ui_qt.QtWidgets.QFrame()
        line.setFrameShape(ui_qt.QtWidgets.QFrame.HLine)
        line.setFrameShadow(ui_qt.QtWidgets.QFrame.Sunken)
        layout.addWidget(label)
        layout.addWidget(line, 1)
        return widget

    @staticmethod
    def create_small_field():
        """Creates a compact line edit.

        Returns:
            QLineEdit: Compact field.
        """
        field = ui_qt.QtWidgets.QLineEdit()
        field.setMinimumWidth(1)
        return field

    @staticmethod
    def add_grid_field(layout, row, column, label_text, field):
        """Adds a labeled field to a grid.

        Args:
            layout (QGridLayout): Parent grid layout.
            row (int): Row index.
            column (int): Column index.
            label_text (str): Label text.
            field (QLineEdit): Field widget.
        """
        field_layout = ui_qt.QtWidgets.QVBoxLayout()
        field_layout.setSpacing(2)
        label = ui_qt.QtWidgets.QLabel(label_text)
        label.setStyleSheet("color: grey;")
        label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        field_layout.addWidget(label)
        field_layout.addWidget(field)
        layout.addLayout(field_layout, row, column)

    @staticmethod
    def create_mode_input_row(label_text, placeholder):
        """Creates an auto/input mode row.

        Args:
            label_text (str): Row label.
            placeholder (str): Field placeholder.

        Returns:
            dict: Row widgets.
        """
        layout = ui_qt.QtWidgets.QHBoxLayout()
        label = ui_qt.QtWidgets.QLabel(label_text)
        label.setMinimumWidth(58)
        auto_radio = ui_qt.QtWidgets.QRadioButton("Auto")
        input_radio = ui_qt.QtWidgets.QRadioButton("Input")
        field = ui_qt.QtWidgets.QLineEdit()
        field.setPlaceholderText(placeholder)
        layout.addWidget(label)
        layout.addWidget(auto_radio)
        layout.addWidget(input_radio)
        layout.addWidget(field)
        return {"layout": layout, "auto": auto_radio, "input": input_radio, "field": field}

    @staticmethod
    def create_action_button(label, color_name):
        """Creates a colored action button.

        Args:
            label (str): Button label.
            color_name (str): Color key.

        Returns:
            QPushButton: Created button.
        """
        button = ui_qt.QtWidgets.QPushButton(label)
        button.setMinimumHeight(36)
        colors = {
            "neutral": ("#d1d1d1", "#dedede"),
            "blue": ("#d8d8d8", "#e4e4e4"),
            "green": ("#d5d5d5", "#e1e1e1"),
            "orange": ("#dddddd", "#e8e8e8"),
        }
        base_color, hover_color = colors.get(color_name, colors.get("neutral"))
        button.setStyleSheet(
            "QPushButton { background-color: %s; color: #202020; font-weight: bold; border: 1px solid #8f8f8f; }"
            "QPushButton:hover { background-color: %s; border: 1px solid #777777; }"
            "QPushButton:pressed { background-color: #c8c8c8; }" % (base_color, hover_color)
        )
        return button

    def refresh_enabled_states(self):
        """Refreshes widget enabled states."""
        self.rename_field.setEnabled(not self.use_source_checkbox.isChecked())
        prefix_auto = self.prefix_auto_radio.isChecked()
        suffix_auto = self.suffix_auto_radio.isChecked()
        self.prefix_field.setEnabled(not prefix_auto)
        self.suffix_field.setEnabled(not suffix_auto)
        for field in [self.left_prefix_field, self.center_prefix_field, self.right_prefix_field]:
            field.setEnabled(prefix_auto)
        for field in [
            self.transform_suffix_field,
            self.mesh_suffix_field,
            self.nurbs_crv_suffix_field,
            self.joint_suffix_field,
            self.locator_suffix_field,
            self.surface_suffix_field,
        ]:
            field.setEnabled(suffix_auto)

    def set_selection_type(self, selection_type):
        """Sets the active selection radio button.

        Args:
            selection_type (str): Selection type.
        """
        selection_type = model.normalize_selection_type(selection_type)
        if selection_type == model.SELECTION_HIERARCHY:
            self.hierarchy_radio.setChecked(True)
        elif selection_type == model.SELECTION_ALL:
            self.all_radio.setChecked(True)
        else:
            self.selected_radio.setChecked(True)

    def get_selection_type(self):
        """Gets the active selection radio button text.

        Returns:
            str: Selection type.
        """
        checked_button = self.selection_group.checkedButton()
        if checked_button:
            return checked_button.text()
        return model.SELECTION_SELECTED


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = RenamerView()
        window.show()
