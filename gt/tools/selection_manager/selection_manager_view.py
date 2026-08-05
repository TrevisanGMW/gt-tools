"""
Selection Manager View
"""

from gt.tools.selection_manager import selection_manager_model as model
from gt.ui.qt_utils import MayaWindowMeta
import gt.ui.qt_utils as qt_utils
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt


class SelectionManagerView(metaclass=MayaWindowMeta):
    """Qt view for Selection Manager."""

    def __init__(self, parent=None, controller=None, version=None):
        """Initializes the Selection Manager view.

        Args:
            parent (QWidget, optional): Parent widget.
            controller (SelectionManagerController, optional): Controller reference.
            version (str, optional): Tool version string.
        """
        super().__init__(parent=parent)
        self.controller = controller
        self.setWindowTitle("Selection Manager" + (" - (v{0})".format(version) if version else ""))
        self.setMinimumWidth(350)
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_selection_manager))
        self.mode_btn = None
        self.build_widgets()
        qt_utils.center_window(self)

    def build_widgets(self):
        """Builds all view widgets."""
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        title_layout = ui_qt.QtWidgets.QHBoxLayout()
        title_label = ui_qt.QtWidgets.QLabel("Selection Manager")
        title_label.setStyleSheet("font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        self.mode_btn = ui_qt.QtWidgets.QPushButton(model.UI_MODE_DEFAULT)
        self.mode_btn.setToolTip("Toggle Selection Manager UI mode.")
        self.mode_btn.setMaximumWidth(82)
        title_layout.addWidget(self.mode_btn)
        self.reset_btn = ui_qt.QtWidgets.QPushButton("Reset")
        self.reset_btn.setToolTip("Reset Selection Manager filters, colors, stored selections, and saved preferences.")
        title_layout.addWidget(self.reset_btn)
        main_layout.addLayout(title_layout)

        main_layout.addWidget(self.create_separator("Element Name"))
        self.name_contains_checkbox = ui_qt.QtWidgets.QCheckBox("Does Contain")
        self.name_contains_checkbox.setToolTip("Include objects whose names contain any text from the left field.")
        self.name_not_contains_checkbox = ui_qt.QtWidgets.QCheckBox("Doesn't Contain")
        self.name_not_contains_checkbox.setToolTip(
            "Exclude objects whose names contain any text from the right field."
        )
        self.name_contains_field = ui_qt.QtWidgets.QLineEdit("_jnt")
        self.name_contains_field.setToolTip("Comma-separated name fragments to include. Example: _jnt, _ctrl")
        self.name_not_contains_field = ui_qt.QtWidgets.QLineEdit("endJnt, eye")
        self.name_not_contains_field.setToolTip("Comma-separated name fragments to exclude. Example: endJnt, eye")
        main_layout.addLayout(
            self.create_dual_filter_row(
                self.name_contains_checkbox,
                self.name_contains_field,
                self.name_not_contains_checkbox,
                self.name_not_contains_field,
            )
        )

        main_layout.addWidget(self.create_separator("Element Type"))
        self.type_contains_checkbox = ui_qt.QtWidgets.QCheckBox("Does Contain")
        self.type_contains_checkbox.setToolTip("Include objects matching any Maya node type from the left field.")
        self.type_not_contains_checkbox = ui_qt.QtWidgets.QCheckBox("Doesn't Contain")
        self.type_not_contains_checkbox.setToolTip("Exclude objects matching any Maya node type from the right field.")
        self.type_contains_field = ui_qt.QtWidgets.QLineEdit("joint")
        self.type_contains_field.setToolTip("Comma-separated Maya node types to include. Example: joint, mesh")
        self.type_not_contains_field = ui_qt.QtWidgets.QLineEdit("mesh")
        self.type_not_contains_field.setToolTip("Comma-separated Maya node types to exclude. Example: mesh, camera")
        main_layout.addLayout(
            self.create_dual_filter_row(
                self.type_contains_checkbox,
                self.type_contains_field,
                self.type_not_contains_checkbox,
                self.type_not_contains_field,
            )
        )
        self.shape_behavior_combo = ui_qt.QtWidgets.QComboBox()
        self.shape_behavior_combo.addItems(model.SHAPE_BEHAVIOR_OPTIONS)
        self.shape_behavior_combo.setCurrentText(model.SHAPE_BEHAVIOR_SHAPES)
        self.shape_behavior_combo.setToolTip(
            "Determines how shape-node matches are handled: shape nodes only, transforms only, "
            "transforms from matched shapes, or both transforms and shapes."
        )
        main_layout.addLayout(self.create_labeled_row("Behavior", self.shape_behavior_combo))
        type_buttons_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.print_selection_types_btn = ui_qt.QtWidgets.QPushButton("Print Selection Types")
        self.print_selection_types_btn.setToolTip("Print unique Maya node types found in the current selection.")
        self.print_scene_types_btn = ui_qt.QtWidgets.QPushButton("Print All Scene Types")
        self.print_scene_types_btn.setToolTip("Print unique Maya node types found in the entire scene.")
        type_buttons_layout.addWidget(self.print_selection_types_btn)
        type_buttons_layout.addWidget(self.print_scene_types_btn)
        main_layout.addLayout(type_buttons_layout)

        main_layout.addWidget(self.create_separator("Visibility"))
        visibility_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.visibility_checkbox = ui_qt.QtWidgets.QCheckBox("Visibility State")
        self.visibility_checkbox.setToolTip("Filter objects by their visibility attribute.")
        self.visibility_on_radio = ui_qt.QtWidgets.QRadioButton("On")
        self.visibility_on_radio.setToolTip("Include visible objects when visibility filtering is enabled.")
        self.visibility_off_radio = ui_qt.QtWidgets.QRadioButton("Off")
        self.visibility_off_radio.setToolTip("Include hidden objects when visibility filtering is enabled.")
        self.visibility_off_radio.setChecked(True)
        visibility_layout.addWidget(self.visibility_checkbox)
        visibility_layout.addStretch()
        visibility_layout.addWidget(self.visibility_on_radio)
        visibility_layout.addWidget(self.visibility_off_radio)
        main_layout.addLayout(visibility_layout)

        main_layout.addWidget(self.create_separator("Outliner Color"))
        self.outliner_color_checkbox = ui_qt.QtWidgets.QCheckBox("Using Outliner Color")
        self.outliner_color_checkbox.setToolTip("Include objects using the selected outliner color.")
        self.outliner_color_button = self.create_color_button([1, 1, 1])
        self.outliner_color_get_btn = ui_qt.QtWidgets.QPushButton("Get")
        self.outliner_color_get_btn.setToolTip("Read the outliner color from the first selected object.")
        self.no_outliner_color_checkbox = ui_qt.QtWidgets.QCheckBox("But Not Using Color")
        self.no_outliner_color_checkbox.setToolTip("Exclude objects using the selected outliner color.")
        self.no_outliner_color_button = self.create_color_button([1, 1, 1])
        self.no_outliner_color_get_btn = ui_qt.QtWidgets.QPushButton("Get")
        self.no_outliner_color_get_btn.setToolTip("Read the outliner color from the first selected object.")
        main_layout.addLayout(
            self.create_color_row(
                self.outliner_color_checkbox,
                self.outliner_color_button,
                self.outliner_color_get_btn,
            )
        )
        main_layout.addLayout(
            self.create_color_row(
                self.no_outliner_color_checkbox,
                self.no_outliner_color_button,
                self.no_outliner_color_get_btn,
            )
        )

        stored_header_layout = ui_qt.QtWidgets.QHBoxLayout()
        stored_header_layout.addWidget(self.create_separator("Stored Selections"))
        stored_header_layout.addStretch()
        self.add_stored_slot_btn = ui_qt.QtWidgets.QPushButton("+")
        self.add_stored_slot_btn.setMaximumWidth(32)
        self.add_stored_slot_btn.setToolTip("Add another stored selection row.")
        stored_header_layout.addWidget(self.add_stored_slot_btn)
        main_layout.addLayout(stored_header_layout)
        self.store_buttons = {}
        self.stored_section_layout = ui_qt.QtWidgets.QVBoxLayout()
        self.stored_section_layout.setSpacing(4)
        main_layout.addLayout(self.stored_section_layout)

        main_layout.addWidget(self.create_separator("Actions"))
        self.select_hierarchy_btn = ui_qt.QtWidgets.QPushButton("Select Hierarchy")
        self.select_hierarchy_btn.setToolTip("Select descendants of the current Maya selection.")
        self.create_selection_btn = ui_qt.QtWidgets.QPushButton("Create New Selection")
        self.create_selection_btn.setToolTip("Run active filters against all scene objects and replace the selection.")
        self.update_selection_btn = ui_qt.QtWidgets.QPushButton("Update Current Selection")
        self.update_selection_btn.setToolTip("Run active filters against the current Maya selection.")
        main_layout.addWidget(self.select_hierarchy_btn)
        main_layout.addWidget(self.create_selection_btn)
        main_layout.addWidget(self.update_selection_btn)

        self.refresh_enabled_states()

    @staticmethod
    def create_separator(text):
        """Creates a section label.

        Args:
            text (str): Section text.

        Returns:
            QWidget: Separator widget.
        """
        widget = ui_qt.QtWidgets.QWidget()
        layout = ui_qt.QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 6, 0, 2)
        layout.setSpacing(8)
        line_left = ui_qt.QtWidgets.QFrame()
        line_left.setFrameShape(ui_qt.QtWidgets.QFrame.HLine)
        line_left.setFrameShadow(ui_qt.QtWidgets.QFrame.Sunken)
        label = ui_qt.QtWidgets.QLabel(text)
        label.setStyleSheet("color: grey; font-weight: bold;")
        line_right = ui_qt.QtWidgets.QFrame()
        line_right.setFrameShape(ui_qt.QtWidgets.QFrame.HLine)
        line_right.setFrameShadow(ui_qt.QtWidgets.QFrame.Sunken)
        layout.addWidget(line_left)
        layout.addWidget(label)
        layout.addWidget(line_right, 1)
        return widget

    @staticmethod
    def create_labeled_row(label_text, widget):
        """Creates a row with a label and widget.

        Args:
            label_text (str): Label text.
            widget (QWidget): Widget to add.

        Returns:
            QHBoxLayout: Created layout.
        """
        layout = ui_qt.QtWidgets.QHBoxLayout()
        label = ui_qt.QtWidgets.QLabel("{0}:".format(label_text))
        label.setMinimumWidth(80)
        layout.addWidget(label)
        layout.addWidget(widget)
        return layout

    @staticmethod
    def create_dual_filter_row(left_checkbox, left_field, right_checkbox, right_field):
        """Creates a dual filter row.

        Args:
            left_checkbox (QCheckBox): Left checkbox.
            left_field (QLineEdit): Left text field.
            right_checkbox (QCheckBox): Right checkbox.
            right_field (QLineEdit): Right text field.

        Returns:
            QGridLayout: Created layout.
        """
        layout = ui_qt.QtWidgets.QGridLayout()
        layout.addWidget(left_checkbox, 0, 0)
        layout.addWidget(right_checkbox, 0, 1)
        layout.addWidget(left_field, 1, 0)
        layout.addWidget(right_field, 1, 1)
        return layout

    @staticmethod
    def create_color_button(color):
        """Creates a color swatch button.

        Args:
            color (list): RGB values.

        Returns:
            QPushButton: Color button.
        """
        button = ui_qt.QtWidgets.QPushButton()
        button.setMinimumHeight(24)
        button.setFixedWidth(80)
        button.setProperty("rgb_color", list(color))
        button.setToolTip("Click to pick this outliner color.")
        SelectionManagerView.set_color_button(button, color)
        return button

    @staticmethod
    def set_color_button(button, color):
        """Sets a color button swatch.

        Args:
            button (QPushButton): Button to update.
            color (list): RGB values.
        """
        rgb = [max(0, min(255, int(float(value) * 255))) for value in color]
        button.setProperty("rgb_color", list(color))
        button.setStyleSheet("background-color: rgb({0}, {1}, {2});".format(rgb[0], rgb[1], rgb[2]))

    @staticmethod
    def create_color_row(checkbox, color_button, get_button):
        """Creates a color option row.

        Args:
            checkbox (QCheckBox): Option checkbox.
            color_button (QPushButton): Color swatch.
            get_button (QPushButton): Get-from-selection button.

        Returns:
            QHBoxLayout: Created layout.
        """
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setSpacing(6)
        layout.addWidget(checkbox)
        layout.addStretch()
        layout.addWidget(color_button)
        layout.addWidget(get_button)
        return layout

    def add_stored_selection_row(self, slot):
        """Adds a stored selection row to the stored section.

        Args:
            slot (int): Selection slot.
        """
        self.stored_section_layout.addLayout(self.create_stored_selection_row(slot))

    def create_stored_selection_row(self, slot):
        """Creates a stored selection row.

        Args:
            slot (int): Selection slot.

        Returns:
            QHBoxLayout: Created layout.
        """
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setSpacing(4)
        remove_btn = ui_qt.QtWidgets.QPushButton("-")
        store_btn = ui_qt.QtWidgets.QPushButton("Get")
        add_btn = ui_qt.QtWidgets.QPushButton("+")
        clear_btn = ui_qt.QtWidgets.QPushButton("Clear")
        set_btn = ui_qt.QtWidgets.QPushButton()
        text_btn = ui_qt.QtWidgets.QPushButton()
        delete_btn = ui_qt.QtWidgets.QPushButton()
        remove_btn.setMaximumWidth(32)
        add_btn.setMaximumWidth(32)
        set_btn.setMaximumWidth(32)
        text_btn.setMaximumWidth(32)
        delete_btn.setMaximumWidth(32)
        set_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_save))
        text_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_templates_python))
        delete_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete))
        remove_btn.setToolTip("Remove the current Maya selection from this stored selection.")
        store_btn.setToolTip("Store the current Maya selection, or select the stored objects when populated.")
        add_btn.setToolTip("Add the current Maya selection to this stored selection.")
        clear_btn.setToolTip("Clear this stored selection row.")
        set_btn.setToolTip("Save this stored selection as a Maya object set.")
        text_btn.setToolTip("Export this stored selection to a text file.")
        delete_btn.setToolTip("Delete this stored selection row.")
        self.set_utility_button_style(remove_btn, "negative")
        self.set_utility_button_style(add_btn, "positive")
        self.set_utility_button_style(clear_btn, "neutral")
        self.set_utility_button_style(delete_btn, "negative")
        self.set_store_button_style(store_btn, has_selection=False)
        self.store_buttons[slot] = {
            "remove": remove_btn,
            "store": store_btn,
            "add": add_btn,
            "clear": clear_btn,
            "set": set_btn,
            "text": text_btn,
            "delete": delete_btn,
        }
        for widget in [remove_btn, store_btn, add_btn, clear_btn, set_btn, text_btn, delete_btn]:
            layout.addWidget(widget)
        return layout

    @staticmethod
    def set_utility_button_style(button, style_name):
        """Applies a soft utility color to a stored-selection button.

        Args:
            button (QPushButton): Button to style.
            style_name (str): Style key. Accepted values are positive, negative, or neutral.
        """
        if style_name == "positive":
            button.setStyleSheet(
                "QPushButton { background-color: #557f63; color: white; font-weight: bold; }"
                "QPushButton:hover { background-color: #659574; }"
            )
            return
        if style_name == "negative":
            button.setStyleSheet(
                "QPushButton { background-color: #8a5a5a; color: white; font-weight: bold; }"
                "QPushButton:hover { background-color: #9b6767; }"
            )
            return
        button.setStyleSheet(
            "QPushButton { background-color: #5a6068; color: white; font-weight: bold; }"
            "QPushButton:hover { background-color: #6a717a; }"
        )

    def clear_stored_selection_rows(self):
        """Removes all stored selection row layouts."""
        while self.stored_section_layout.count():
            item = self.stored_section_layout.takeAt(0)
            layout = item.layout()
            if layout:
                while layout.count():
                    child_item = layout.takeAt(0)
                    widget = child_item.widget()
                    if widget:
                        widget.deleteLater()
                layout.deleteLater()
        self.store_buttons = {}

    def refresh_enabled_states(self):
        """Refreshes dependent widget enabled states."""
        self.name_contains_field.setEnabled(self.name_contains_checkbox.isChecked())
        self.name_not_contains_field.setEnabled(self.name_not_contains_checkbox.isChecked())
        self.type_contains_field.setEnabled(self.type_contains_checkbox.isChecked())
        self.type_not_contains_field.setEnabled(self.type_not_contains_checkbox.isChecked())
        self.shape_behavior_combo.setEnabled(
            self.type_contains_checkbox.isChecked() or self.type_not_contains_checkbox.isChecked()
        )
        self.visibility_on_radio.setEnabled(self.visibility_checkbox.isChecked())
        self.visibility_off_radio.setEnabled(self.visibility_checkbox.isChecked())
        self.outliner_color_button.setEnabled(self.outliner_color_checkbox.isChecked())
        self.outliner_color_get_btn.setEnabled(self.outliner_color_checkbox.isChecked())
        self.no_outliner_color_button.setEnabled(self.no_outliner_color_checkbox.isChecked())
        self.no_outliner_color_get_btn.setEnabled(self.no_outliner_color_checkbox.isChecked())

    def apply_ui_mode(self, ui_mode):
        """Applies the selected UI mode to optional controls.

        Args:
            ui_mode (str): UI mode.
        """
        if ui_mode not in model.UI_MODES:
            ui_mode = model.UI_MODE_DEFAULT
        self.mode_btn.setText(ui_mode)
        show_default = ui_mode in [model.UI_MODE_DEFAULT, model.UI_MODE_COMPLETE]
        show_complete = ui_mode == model.UI_MODE_COMPLETE
        for widget in [
            self.print_selection_types_btn,
            self.print_scene_types_btn,
        ]:
            widget.setVisible(show_complete)
        self.add_stored_slot_btn.setVisible(show_default)
        for slot in self.store_buttons:
            buttons = self.store_buttons.get(slot) or {}
            for key in ["set", "text", "delete"]:
                if key in buttons:
                    buttons[key].setVisible(show_complete)

    def update_store_button_label(self, slot, selection):
        """Updates a store button label.

        Args:
            slot (int): Slot number.
            selection (list): Stored selection.
        """
        store_btn = self.store_buttons[int(slot)]["store"]
        if not selection:
            store_btn.setText("Get")
            store_btn.setToolTip("Store the current Maya selection.")
            self.set_store_button_style(store_btn, has_selection=False)
            return
        if len(selection) == 1:
            store_btn.setText("{0} Obj".format(len(selection)))
        else:
            store_btn.setText("{0} Objs".format(len(selection)))
        tooltip_selection = "\n".join(selection[:15])
        if len(selection) > 15:
            tooltip_selection += "\n..."
        store_btn.setToolTip("Select stored objects:\n{0}".format(tooltip_selection))
        self.set_store_button_style(store_btn, has_selection=True)

    @staticmethod
    def set_store_button_style(button, has_selection):
        """Updates the stored-selection main button style.

        Args:
            button (QPushButton): Store/load button.
            has_selection (bool): Whether the row has stored objects.
        """
        if has_selection:
            button.setStyleSheet(
                "QPushButton { background-color: #3f7f5f; color: white; font-weight: bold; }"
                "QPushButton:hover { background-color: #4d956f; }"
            )
            return
        button.setStyleSheet(
            "QPushButton { background-color: #5a6068; color: white; font-weight: bold; }"
            "QPushButton:hover { background-color: #6a717a; }"
        )


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = SelectionManagerView()
        window.show()
