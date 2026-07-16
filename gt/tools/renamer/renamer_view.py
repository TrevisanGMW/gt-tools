"""Renamer View."""

from gt.tools.renamer import renamer_model as model
from gt.ui.qt_utils import MayaWindowMeta
import gt.ui.qt_utils as qt_utils
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt


class RenamerView(metaclass=MayaWindowMeta):
    """Compact Qt view for GT Renamer."""

    WINDOW_WIDTH = 330
    LABEL_WIDTH = 58
    CONTROL_HEIGHT = 24
    BUTTON_HEIGHT = 28

    def __init__(self, parent=None, version=None):
        """Initializes the renamer view.

        Args:
            parent (QWidget, optional): Parent widget.
            version (str, optional): Tool version.
        """
        super().__init__(parent=parent)
        self.setWindowTitle("GT Renamer" + (" - (v{0})".format(version) if version else ""))
        self.setMinimumWidth(self.WINDOW_WIDTH)
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_renamer))
        self.setStyleSheet(self._build_stylesheet())
        self.build_widgets()
        self.adjustSize()
        qt_utils.center_window(self)

    def build_widgets(self):
        """Builds all view widgets."""
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)

        main_layout.addWidget(self._build_title_bar())
        main_layout.addSpacing(2)
        main_layout.addLayout(self._build_selection_layout())

        main_layout.addWidget(self.create_separator("Other Utilities"))
        main_layout.addLayout(self._build_utility_layout())

        main_layout.addWidget(self.create_separator("Rename and Number / Letter"))
        main_layout.addLayout(self._build_rename_layout())

        main_layout.addWidget(self.create_separator("Prefix and Suffix"))
        main_layout.addLayout(self._build_prefix_suffix_layout())

        main_layout.addWidget(self.create_separator("Search and Replace"))
        main_layout.addLayout(self._build_search_replace_layout())

        self.selected_radio.setChecked(True)
        self.prefix_auto_radio.setChecked(True)
        self.suffix_auto_radio.setChecked(True)
        self.refresh_enabled_states()

    def _build_title_bar(self):
        """Builds the dark title strip.

        Returns:
            QWidget: Title bar widget.
        """
        title_widget = ui_qt.QtWidgets.QFrame()
        title_widget.setObjectName("renamerTitleBar")
        title_layout = ui_qt.QtWidgets.QHBoxLayout(title_widget)
        title_layout.setContentsMargins(8, 4, 4, 4)
        title_layout.setSpacing(4)
        title_label = ui_qt.QtWidgets.QLabel("GT Renamer")
        title_label.setObjectName("renamerTitle")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        self.reset_btn = ui_qt.QtWidgets.QPushButton("Reset")
        self.reset_btn.setObjectName("titleButton")
        self.reset_btn.setFixedHeight(self.CONTROL_HEIGHT)
        self.reset_btn.setToolTip("Reset persistent Renamer settings to defaults.")
        title_layout.addWidget(self.reset_btn)
        return title_widget

    def _build_selection_layout(self):
        """Builds the selection-scope controls.

        Returns:
            QHBoxLayout: Selection layout.
        """
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(8, 2, 8, 2)
        self.selection_group = ui_qt.QtWidgets.QButtonGroup(self)
        self.selected_radio = ui_qt.QtWidgets.QRadioButton(model.SELECTION_SELECTED)
        self.hierarchy_radio = ui_qt.QtWidgets.QRadioButton(model.SELECTION_HIERARCHY)
        self.all_radio = ui_qt.QtWidgets.QRadioButton(model.SELECTION_ALL)
        self.selected_radio.setToolTip("Rename only the current Maya selection.")
        self.hierarchy_radio.setToolTip("Rename the current Maya selection and its hierarchy.")
        self.all_radio.setToolTip("Rename all supported scene objects, excluding default Maya nodes.")
        for radio_button in [self.selected_radio, self.hierarchy_radio, self.all_radio]:
            self.selection_group.addButton(radio_button)
            layout.addWidget(radio_button, 1, ui_qt.QtLib.AlignmentFlag.AlignCenter)
        return layout

    def _build_utility_layout(self):
        """Builds the compact character and case utility controls.

        Returns:
            QVBoxLayout: Utility controls layout.
        """
        layout = ui_qt.QtWidgets.QVBoxLayout()
        layout.setSpacing(4)
        first_row = ui_qt.QtWidgets.QHBoxLayout()
        second_row = ui_qt.QtWidgets.QHBoxLayout()
        first_row.setSpacing(4)
        second_row.setSpacing(4)
        self.remove_first_btn = self.create_action_button("Remove First Letter")
        self.remove_last_btn = self.create_action_button("Remove Last Letter")
        self.uppercase_btn = self.create_action_button("U-Case")
        self.capitalize_btn = self.create_action_button("Capitalize")
        self.lowercase_btn = self.create_action_button("L-Case")
        self.remove_first_btn.setToolTip("Remove the first character from each target object name.")
        self.remove_last_btn.setToolTip("Remove the last character from each target object name.")
        self.uppercase_btn.setToolTip("Convert target object names to uppercase.")
        self.capitalize_btn.setToolTip("Capitalize target object names.")
        self.lowercase_btn.setToolTip("Convert target object names to lowercase.")
        first_row.addWidget(self.remove_first_btn)
        first_row.addWidget(self.remove_last_btn)
        second_row.addWidget(self.uppercase_btn)
        second_row.addWidget(self.capitalize_btn)
        second_row.addWidget(self.lowercase_btn)
        layout.addLayout(first_row)
        layout.addLayout(second_row)
        return layout

    def _build_rename_layout(self):
        """Builds rename-and-number and rename-and-letter controls.

        Returns:
            QVBoxLayout: Rename controls layout.
        """
        layout = ui_qt.QtWidgets.QVBoxLayout()
        layout.setSpacing(4)
        rename_row = ui_qt.QtWidgets.QHBoxLayout()
        rename_row.setSpacing(5)
        rename_label = self.create_row_label("Rename:")
        self.rename_field = self.create_line_edit("new_name")
        self.rename_field.setToolTip("Base name used by Rename and Number or Rename and Letter.")
        self.use_source_checkbox = ui_qt.QtWidgets.QCheckBox("Use Source")
        self.use_source_checkbox.setToolTip("Use each object's current name as the base name.")
        rename_row.addWidget(rename_label)
        rename_row.addWidget(self.rename_field, 1)
        rename_row.addWidget(self.use_source_checkbox)

        options_row = ui_qt.QtWidgets.QHBoxLayout()
        options_row.setSpacing(5)
        self.start_number_field = ui_qt.QtWidgets.QSpinBox()
        self.start_number_field.setRange(0, 999999)
        self.start_number_field.setFixedHeight(self.CONTROL_HEIGHT)
        self.start_number_field.setToolTip("Number used by the first renamed object.")
        self.padding_number_field = ui_qt.QtWidgets.QSpinBox()
        self.padding_number_field.setRange(1, 12)
        self.padding_number_field.setFixedHeight(self.CONTROL_HEIGHT)
        self.padding_number_field.setToolTip("Minimum number of digits used by Rename and Number.")
        self.uppercase_checkbox = ui_qt.QtWidgets.QCheckBox("Uppercase")
        self.uppercase_checkbox.setToolTip("Use uppercase letters for Rename and Letter.")
        options_row.addWidget(self.create_row_label("Start #:"))
        options_row.addWidget(self.start_number_field)
        options_row.addWidget(ui_qt.QtWidgets.QLabel("Padding:"))
        options_row.addWidget(self.padding_number_field)
        options_row.addWidget(self.uppercase_checkbox)

        button_row = ui_qt.QtWidgets.QHBoxLayout()
        button_row.setSpacing(4)
        self.rename_number_btn = self.create_action_button("Rename and Number", primary=True)
        self.rename_letter_btn = self.create_action_button("Rename and Letter", primary=True)
        self.rename_number_btn.setToolTip("Rename targets using the base name and an incrementing padded number.")
        self.rename_letter_btn.setToolTip("Rename targets using the base name and an incrementing letter suffix.")
        button_row.addWidget(self.rename_number_btn)
        button_row.addWidget(self.rename_letter_btn)
        layout.addLayout(rename_row)
        layout.addLayout(options_row)
        layout.addSpacing(2)
        layout.addLayout(button_row)
        return layout

    def _build_prefix_suffix_layout(self):
        """Builds prefix and suffix controls in the legacy compact arrangement.

        Returns:
            QVBoxLayout: Prefix and suffix controls layout.
        """
        layout = ui_qt.QtWidgets.QVBoxLayout()
        layout.setSpacing(4)
        self.prefix_group = ui_qt.QtWidgets.QButtonGroup(self)
        self.suffix_group = ui_qt.QtWidgets.QButtonGroup(self)

        prefix_row = self.create_mode_input_row("Prefix:", "prefix_")
        self.prefix_auto_radio = prefix_row["auto"]
        self.prefix_input_radio = prefix_row["input"]
        self.prefix_field = prefix_row["field"]
        self.prefix_group.addButton(self.prefix_auto_radio)
        self.prefix_group.addButton(self.prefix_input_radio)

        suffix_row = self.create_mode_input_row("Suffix:", "_suffix")
        self.suffix_auto_radio = suffix_row["auto"]
        self.suffix_input_radio = suffix_row["input"]
        self.suffix_field = suffix_row["field"]
        self.suffix_group.addButton(self.suffix_auto_radio)
        self.suffix_group.addButton(self.suffix_input_radio)
        layout.addLayout(prefix_row["layout"])
        layout.addLayout(suffix_row["layout"])

        suffix_grid = ui_qt.QtWidgets.QGridLayout()
        suffix_grid.setHorizontalSpacing(3)
        suffix_grid.setVerticalSpacing(2)
        suffix_fields = [
            ("Group", "transform_suffix_field"),
            ("Mesh", "mesh_suffix_field"),
            ("Nurbs", "nurbs_crv_suffix_field"),
            ("Joint", "joint_suffix_field"),
            ("Locator", "locator_suffix_field"),
            ("Surface", "surface_suffix_field"),
        ]
        for column, (label_text, attribute_name) in enumerate(suffix_fields):
            field = self.create_small_field()
            setattr(self, attribute_name, field)
            self.add_grid_field(suffix_grid, 0, column, label_text, field)
        layout.addLayout(suffix_grid)

        prefix_grid = ui_qt.QtWidgets.QGridLayout()
        prefix_grid.setHorizontalSpacing(3)
        prefix_grid.setVerticalSpacing(2)
        self.left_prefix_field = self.create_small_field()
        self.center_prefix_field = self.create_small_field()
        self.right_prefix_field = self.create_small_field()
        self.add_grid_field(prefix_grid, 0, 0, "Left", self.left_prefix_field)
        self.add_grid_field(prefix_grid, 0, 1, "Center", self.center_prefix_field)
        self.add_grid_field(prefix_grid, 0, 2, "Right", self.right_prefix_field)
        layout.addLayout(prefix_grid)

        button_row = ui_qt.QtWidgets.QHBoxLayout()
        button_row.setSpacing(4)
        self.add_prefix_btn = self.create_action_button("Add Prefix", primary=True)
        self.add_suffix_btn = self.create_action_button("Add Suffix", primary=True)
        self.add_prefix_btn.setToolTip("Add either an automatic position prefix or the manual prefix input.")
        self.add_suffix_btn.setToolTip("Add either an automatic type suffix or the manual suffix input.")
        button_row.addWidget(self.add_prefix_btn)
        button_row.addWidget(self.add_suffix_btn)
        layout.addSpacing(2)
        layout.addLayout(button_row)
        return layout

    def _build_search_replace_layout(self):
        """Builds search and replace controls.

        Returns:
            QVBoxLayout: Search and replace layout.
        """
        layout = ui_qt.QtWidgets.QVBoxLayout()
        layout.setSpacing(4)
        field_grid = ui_qt.QtWidgets.QGridLayout()
        field_grid.setHorizontalSpacing(5)
        field_grid.setVerticalSpacing(3)
        self.search_field = self.create_line_edit("search_text")
        self.replace_field = self.create_line_edit("replace_text")
        self.search_field.setToolTip("Text to find in each target object name.")
        self.replace_field.setToolTip("Replacement text.")
        field_grid.addWidget(self.create_row_label("Search:"), 0, 0)
        field_grid.addWidget(self.search_field, 0, 1)
        field_grid.addWidget(self.create_row_label("Replace:"), 1, 0)
        field_grid.addWidget(self.replace_field, 1, 1)
        self.search_replace_btn = self.create_action_button("Search and Replace", primary=True)
        self.search_replace_btn.setToolTip("Replace matching text in target object names.")
        layout.addLayout(field_grid)
        layout.addSpacing(2)
        layout.addWidget(self.search_replace_btn)
        return layout

    @staticmethod
    def create_separator(text):
        """Creates a centered section separator.

        Args:
            text (str): Section text.

        Returns:
            QWidget: Separator widget.
        """
        widget = ui_qt.QtWidgets.QWidget()
        layout = ui_qt.QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 7, 0, 2)
        layout.setSpacing(7)
        left_line = ui_qt.QtWidgets.QFrame()
        right_line = ui_qt.QtWidgets.QFrame()
        for line in [left_line, right_line]:
            line.setFrameShape(ui_qt.QtLib.FrameStyle.HLine)
            line.setFrameShadow(ui_qt.QtLib.FrameStyle.Sunken)
        label = ui_qt.QtWidgets.QLabel(text)
        label.setObjectName("sectionLabel")
        label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        layout.addWidget(left_line, 1)
        layout.addWidget(label)
        layout.addWidget(right_line, 1)
        return widget

    def create_line_edit(self, placeholder):
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

    def create_small_field(self):
        """Creates a compact preset field.

        Returns:
            QLineEdit: Compact field.
        """
        field = ui_qt.QtWidgets.QLineEdit()
        field.setMinimumWidth(24)
        field.setFixedHeight(self.CONTROL_HEIGHT)
        field.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        if ui_qt.IS_PYSIDE6:
            ignored_policy = ui_qt.QtWidgets.QSizePolicy.Policy.Ignored
        else:
            ignored_policy = ui_qt.QtWidgets.QSizePolicy.Ignored
        field.setSizePolicy(ignored_policy, ui_qt.QtLib.SizePolicy.Fixed)
        return field

    @staticmethod
    def add_grid_field(layout, row, column, label_text, field):
        """Adds a label and field to a compact grid column.

        Args:
            layout (QGridLayout): Parent grid layout.
            row (int): Row index.
            column (int): Column index.
            label_text (str): Label text.
            field (QLineEdit): Field widget.
        """
        label = ui_qt.QtWidgets.QLabel(label_text)
        label.setObjectName("presetLabel")
        label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        layout.addWidget(label, row, column)
        layout.addWidget(field, row + 1, column)

    def create_mode_input_row(self, label_text, placeholder):
        """Creates an auto/input mode row.

        Args:
            label_text (str): Row label.
            placeholder (str): Field placeholder.

        Returns:
            dict: Row layout and widgets.
        """
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setSpacing(5)
        auto_radio = ui_qt.QtWidgets.QRadioButton("Auto")
        input_radio = ui_qt.QtWidgets.QRadioButton("Input")
        field = self.create_line_edit(placeholder)
        layout.addWidget(self.create_row_label(label_text))
        layout.addWidget(auto_radio)
        layout.addWidget(input_radio)
        layout.addWidget(field, 1)
        return {"layout": layout, "auto": auto_radio, "input": input_radio, "field": field}

    def create_row_label(self, text):
        """Creates a fixed-width row label.

        Args:
            text (str): Label text.

        Returns:
            QLabel: Created label.
        """
        label = ui_qt.QtWidgets.QLabel(text)
        label.setFixedWidth(self.LABEL_WIDTH)
        label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignRight | ui_qt.QtLib.AlignmentFlag.AlignVCenter)
        return label

    def create_action_button(self, label, primary=False):
        """Creates a shallow neutral action button.

        Args:
            label (str): Button label.
            primary (bool, optional): Whether this is a main section action.

        Returns:
            QPushButton: Created button.
        """
        button = ui_qt.QtWidgets.QPushButton(label)
        button.setObjectName("primaryButton" if primary else "utilityButton")
        button.setFixedHeight(self.BUTTON_HEIGHT)
        button.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        return button

    @staticmethod
    def _build_stylesheet():
        """Builds the view stylesheet.

        Returns:
            str: Combined Maya and Renamer stylesheet.
        """
        return ui_res_lib.Stylesheet.maya_dialog_base + """
            QFrame#renamerTitleBar { background-color: #555555; border: 1px solid #626262; }
            QLabel#renamerTitle { color: #f0f0f0; font-weight: bold; }
            QLabel#sectionLabel { color: #aaaaaa; }
            QLabel#presetLabel { color: #aaaaaa; font-style: italic; font-size: 10px; }
            QRadioButton, QCheckBox { color: #dddddd; }
            QPushButton#titleButton { background: transparent; border: none; color: #e5e5e5; padding: 2px 8px; }
            QPushButton#titleButton:hover { background-color: #666666; }
            QPushButton#utilityButton, QPushButton#primaryButton {
                background-color: #5c5c5c; border: 1px solid #444444; color: #dddddd; padding: 2px 4px;
            }
            QPushButton#primaryButton { background-color: #9a9a9a; color: #202020; }
            QPushButton#utilityButton:hover { background-color: #696969; }
            QPushButton#primaryButton:hover { background-color: #aaaaaa; }
            QPushButton#utilityButton:pressed, QPushButton#primaryButton:pressed { background-color: #4b4b4b; }
            QLineEdit, QSpinBox { background-color: #292929; border: 1px solid #444444; padding: 1px 4px; }
            QLineEdit:disabled, QSpinBox:disabled { background-color: #353535; color: #707070; }
        """

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
