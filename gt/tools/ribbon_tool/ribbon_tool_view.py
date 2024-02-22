"""
Ribbon Tool View/Window/UI
"""
from PySide2.QtWidgets import QPushButton, QLabel, QVBoxLayout, QFrame, QSpinBox, QHBoxLayout, QCheckBox, QLineEdit
from PySide2.QtWidgets import QComboBox, QDoubleSpinBox
import gt.ui.resource_library as resource_library
from gt.ui.qt_utils import MayaWindowMeta
from PySide2 import QtWidgets, QtCore
import gt.ui.qt_utils as qt_utils
from PySide2.QtGui import QIcon


class RibbonToolView(metaclass=MayaWindowMeta):
    def __init__(self, parent=None, controller=None, version=None):
        """
        Initialize the RibbonToolView.
        This window represents the main GUI window of the tool.

        Args:
            parent (str): Parent for this window
            controller (RibbonToolViewController): RibbonToolViewController, not to be used, here so
                                                          it's not deleted by the garbage collector.  Defaults to None.
            version (str, optional): If provided, it will be used to determine the window title. e.g. Title - (v1.2.3)
        """
        super().__init__(parent=parent)

        self.controller = controller  # Only here so it doesn't get deleted by the garbage collectors

        # Window Title
        self.window_title = "GT Ribbon Tool"
        _window_title = self.window_title
        if version:
            _window_title += f' - (v{str(version)})'
        self.setWindowTitle(_window_title)

        # Title
        self.title_label = QtWidgets.QLabel(self.window_title)
        self.title_label.setStyleSheet('background-color: rgb(93, 93, 93); border: 0px solid rgb(93, 93, 93); \
                                                color: rgb(255, 255, 255); padding: 10px; margin-bottom: 0; text-align: left;')
        self.title_label.setFont(qt_utils.get_font(resource_library.Font.roboto))
        self.help_btn = QPushButton('Help')
        self.help_btn.setToolTip("Open Help Dialog.")
        self.help_btn.setStyleSheet('color: rgb(255, 255, 255); padding: 10px; '
                                    'padding-right: 15px; padding-left: 15px; margin: 0;')
        self.help_btn.setFont(qt_utils.get_font(resource_library.Font.roboto))

        # Prefix
        self.prefix_label = QLabel("Prefix:")
        self.prefix_label.setMinimumWidth(90)
        self.prefix_content = QLineEdit()
        self.prefix_content.setPlaceholderText("Enter prefix here...")
        self.prefix_clear_btn = QPushButton("Clear")
        self.prefix_clear_btn.setStyleSheet("padding: 7; border-radius: 5px;")
        self.prefix_clear_btn.clicked.connect(self.clear_prefix_content)

        # Num Controls
        self.num_controls_label = QLabel("Number of Controls:")
        self.num_controls_label.setMinimumWidth(170)
        self.num_controls_content = QSpinBox()
        self.num_controls_content.setMinimum(1)
        self.num_controls_content.setSingleStep(1)
        self.num_controls_content.setValue(6)

        # Num Joints
        self.num_joints_label = QLabel("Number of Joints:")
        self.num_joints_label.setMinimumWidth(170)
        self.num_joints_content = QSpinBox()
        self.num_joints_content.setMinimum(0)
        self.num_joints_content.setSingleStep(1)
        self.num_joints_content.setValue(8)

        # Num Joints
        self.num_joints_label = QLabel("Number of Joints:")
        self.num_joints_label.setMinimumWidth(170)
        self.num_joints_content = QSpinBox()
        self.num_joints_content.setMinimum(0)
        self.num_joints_content.setSingleStep(1)
        self.num_joints_content.setValue(8)

        # Drop Off Rate
        self.dropoff_label = QLabel("Dropoff Rate:")
        self.dropoff_label.setMinimumWidth(170)
        self.dropoff_content = QDoubleSpinBox()
        self.dropoff_content.setMinimum(0)
        self.dropoff_content.setMaximum(10)
        self.dropoff_content.setSingleStep(0.1)
        self.dropoff_content.setValue(2)

        # Span Multiplier
        self.span_multiplier_label = QLabel("Span Multiplier:")
        self.span_multiplier_label.setMinimumWidth(170)
        self.span_multiplier_content = QSpinBox()
        self.span_multiplier_content.setMinimum(0)
        self.span_multiplier_content.setSingleStep(1)
        self.span_multiplier_content.setValue(0)

        # Checkboxes
        self.equidistant_label = QLabel("Equidistant:")
        self.equidistant_label.setToolTip("Ensures equidistant calculation between the distance of every follicle.")
        self.equidistant_label.setMinimumWidth(100)
        self.equidistant_checkbox = QCheckBox()
        self.equidistant_checkbox.setChecked(True)
        self.add_fk_label = QLabel("Add FK:")
        self.add_fk_label.setToolTip("Creates extra forward-kinematics controls to drive ribbon controls.")
        self.add_fk_label.setMinimumWidth(100)
        self.add_fk_checkbox = QCheckBox()
        self.add_fk_checkbox.setChecked(True)
        self.constraint_source_label = QLabel("Constraint Source:")
        self.constraint_source_label.setToolTip("Constraint source transforms to follow the ribbon. "
                                                "(This skips joint creation)")
        self.constraint_source_label.setMinimumWidth(100)
        self.constraint_source_checkbox = QCheckBox()
        self.constraint_source_checkbox.setChecked(True)
        self.parent_jnt_label = QLabel("Parent Skin Joints:")
        self.parent_jnt_label.setToolTip("Creates a hierarchy with the generated driven joints.")
        self.parent_jnt_label.setMinimumWidth(100)
        self.parent_jnt_checkbox = QCheckBox()
        self.parent_jnt_checkbox.setChecked(True)

        # Surface Data / Mode
        self.mode_label = QLabel("Source Mode:")
        self.mode_label.setToolTip("No Source: Creates a simple ribbon.\n"
                                         "Surface: Uses provided surface as input.\n"
                                         "Transform List: Creates ribbon using a provided transform list.")
        self.mode_combo_box = QComboBox()
        self.mode_combo_box.addItems(["No Source", "Surface", "Transform List"])
        self.mode_combo_box.setStyleSheet("padding: 5;")

        self.surface_data_set_btn = QPushButton('Set')
        self.surface_data_set_btn.setToolTip("Uses selection to determine source data.")
        self.surface_data_clear_btn = QPushButton('Clear')
        self.surface_data_clear_btn.setToolTip("Clears source data.")
        self.surface_data_set_btn.setStyleSheet("padding: 5;")
        self.surface_data_content_btn = QPushButton("No Data")
        self.surface_data_content_btn.setToolTip('Current Surface Data (Click to Select It)')

        # Create Button
        self.create_ribbon_btn = QPushButton("Create Ribbon")
        self.create_ribbon_btn.setStyleSheet("padding: 10;")
        self.create_ribbon_btn.setSizePolicy(self.create_ribbon_btn.sizePolicy().Expanding,
                                             self.create_ribbon_btn.sizePolicy().Expanding)

        # Window Setup ------------------------------------------------------------------------------------
        self.create_layout()
        self.mode_combo_box.currentIndexChanged.connect(self.update_ui_from_mode)

        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.WindowMaximizeButtonHint |
                            QtCore.Qt.WindowMinimizeButtonHint)
        self.setWindowIcon(QIcon(resource_library.Icon.tool_ribbon))

        stylesheet = resource_library.Stylesheet.scroll_bar_base
        stylesheet += resource_library.Stylesheet.maya_dialog_base
        stylesheet += resource_library.Stylesheet.list_widget_base
        stylesheet += resource_library.Stylesheet.spin_box_base
        stylesheet += resource_library.Stylesheet.checkbox_base
        stylesheet += resource_library.Stylesheet.line_edit_base
        stylesheet += resource_library.Stylesheet.combobox_rounded
        self.setStyleSheet(stylesheet)
        self.create_ribbon_btn.setStyleSheet(resource_library.Stylesheet.btn_push_bright)
        qt_utils.center_window(self)
        self.update_ui_from_mode(0) # No Source

    def create_layout(self):
        """Create the layout for the window."""
        # Top Layout -------------------------------------------------------------------------
        title_layout = QtWidgets.QHBoxLayout()
        title_layout.setSpacing(0)
        title_layout.addWidget(self.title_label, 5)
        title_layout.addWidget(self.help_btn)

        # Body Layout -------------------------------------------------------------------------
        body_layout = QVBoxLayout()
        body_layout.setContentsMargins(15, 0, 15, 5)  # L-T-R-B

        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(self.prefix_label)
        prefix_layout.addWidget(self.prefix_content)
        prefix_layout.addWidget(self.prefix_clear_btn)
        prefix_layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        body_layout.addLayout(prefix_layout)

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(self.mode_label)
        mode_layout.addWidget(self.mode_combo_box)
        mode_layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        body_layout.addLayout(mode_layout)

        num_controls_layout = QHBoxLayout()
        num_controls_layout.addWidget(self.num_controls_label)
        num_controls_layout.addWidget(self.num_controls_content)
        body_layout.addLayout(num_controls_layout)

        num_joints_layout = QHBoxLayout()
        num_joints_layout.addWidget(self.num_joints_label)
        num_joints_layout.addWidget(self.num_joints_content)
        body_layout.addLayout(num_joints_layout)

        drop_off_layout = QHBoxLayout()
        drop_off_layout.addWidget(self.dropoff_label)
        drop_off_layout.addWidget(self.dropoff_content)
        body_layout.addLayout(drop_off_layout)

        span_multiplier_layout = QHBoxLayout()
        span_multiplier_layout.addWidget(self.span_multiplier_label)
        span_multiplier_layout.addWidget(self.span_multiplier_content)
        body_layout.addLayout(span_multiplier_layout)

        checkboxes_one_layout = QHBoxLayout()
        checkboxes_one_layout.addWidget(self.equidistant_label)
        checkboxes_one_layout.addWidget(self.equidistant_checkbox)
        checkboxes_one_layout.addWidget(self.parent_jnt_label)
        checkboxes_one_layout.addWidget(self.parent_jnt_checkbox)
        body_layout.addLayout(checkboxes_one_layout)

        checkboxes_two_layout = QHBoxLayout()
        checkboxes_two_layout.addWidget(self.add_fk_label)
        checkboxes_two_layout.addWidget(self.add_fk_checkbox)
        checkboxes_two_layout.addWidget(self.constraint_source_label)
        checkboxes_two_layout.addWidget(self.constraint_source_checkbox)
        body_layout.addLayout(checkboxes_two_layout)

        surface_data_layout = QtWidgets.QVBoxLayout()
        sur_data_label_content_layout = QtWidgets.QHBoxLayout()
        set_clear_layout = QtWidgets.QHBoxLayout()
        content_layout = QtWidgets.QHBoxLayout()
        set_clear_layout.addWidget(self.surface_data_set_btn)
        set_clear_layout.addWidget(self.surface_data_clear_btn)
        content_layout.addWidget(self.surface_data_content_btn)
        sur_data_label_content_layout.addLayout(set_clear_layout)
        sur_data_label_content_layout.addLayout(content_layout)
        set_clear_layout.setSpacing(2)
        content_layout.setSpacing(0)
        source_data_label = QLabel("Source Surface/Transform List:")
        source_data_label.setStyleSheet(f"font-weight: bold; font-size: 8; margin-top: 0; "
                                        f"color: {resource_library.Color.RGB.gray_lighter};")
        source_data_label.setAlignment(QtCore.Qt.AlignCenter)
        source_data_font = qt_utils.get_font(resource_library.Font.roboto)
        source_data_font.setPointSize(6)
        source_data_label.setFont(source_data_font)
        surface_data_layout.addWidget(source_data_label)
        surface_data_layout.addLayout(sur_data_label_content_layout)

        source_layout = QVBoxLayout()
        source_layout.setContentsMargins(15, 0, 15, 5)  # L-T-R-B
        source_layout.addLayout(surface_data_layout)

        bottom_main_button_layout = QVBoxLayout()
        bottom_main_button_layout.addWidget(self.create_ribbon_btn)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)

        separator_two = QFrame()
        separator_two.setFrameShape(QFrame.HLine)
        separator_two.setFrameShadow(QFrame.Sunken)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        top_layout = QtWidgets.QVBoxLayout()
        bottom_layout = QtWidgets.QVBoxLayout()
        top_layout.addLayout(title_layout)
        top_layout.setContentsMargins(15, 15, 15, 10)  # L-T-R-B
        main_layout.addLayout(top_layout)
        main_layout.addLayout(body_layout)
        main_layout.addWidget(separator)
        main_layout.addLayout(source_layout)
        main_layout.addWidget(separator_two)
        bottom_layout.addLayout(bottom_main_button_layout)
        bottom_layout.setContentsMargins(15, 0, 15, 15)  # L-T-R-B
        main_layout.addLayout(bottom_layout)

    def update_ui_from_mode(self, index):
        """
        Updates UI according to the selected mode.
        Args:
            index (int) The index of the combobox.
        """
        if index == 0:  # No Source
            self.surface_data_set_btn.setEnabled(False)
            self.surface_data_clear_btn.setEnabled(False)
            self.surface_data_content_btn.setEnabled(False)
            self.constraint_source_label.setEnabled(False)
            self.constraint_source_checkbox.setEnabled(False)
            self.clear_source_data_button()
        elif index == 1:  # From Surface
            self.surface_data_set_btn.setEnabled(True)
            self.surface_data_clear_btn.setEnabled(True)
            self.surface_data_content_btn.setEnabled(True)
            self.constraint_source_label.setEnabled(False)
            self.constraint_source_checkbox.setEnabled(False)
            self.clear_source_data_button()
        elif index == 2:  # From Transform List
            self.surface_data_set_btn.setEnabled(True)
            self.surface_data_clear_btn.setEnabled(True)
            self.surface_data_content_btn.setEnabled(True)
            self.constraint_source_label.setEnabled(True)
            self.constraint_source_checkbox.setEnabled(True)
            self.clear_source_data_button()

    def close_window(self):
        """ Closes this window """
        self.close()

    # Setters --------------------------------------------------------------------------------------------------
    def clear_source_data_button(self):
        """ Clears the source data content button by changing its colors and text. """
        self.set_source_data_button_values(text="No Data",
                                           color_text=resource_library.Color.RGB.gray_light,
                                           color_text_disabled=resource_library.Color.RGB.gray_mid_light,
                                           color_btn=resource_library.Color.RGB.gray_darker,
                                           color_btn_hover=resource_library.Color.RGB.gray_mid_light,
                                           color_btn_pressed=resource_library.Color.RGB.gray_mid_lighter,
                                           color_btn_disabled=resource_library.Color.RGB.gray_darker)

    def clear_prefix_content(self):
        """
        Clears the text in the QLineEdit used for prefix.
        """
        self.prefix_content.setText("")

    def set_source_data_button_values(self, text=None, color_text=None, color_text_disabled=None, color_btn=None,
                                      color_btn_hover=None, color_btn_pressed=None, color_btn_disabled=None):
        """
        Updates the source data button color, text and button color (background color)
        Args:
            text (str, optional): New button text.
            color_btn (str, optional): HEX or RGB string to be used as background color.
            color_text (str, optional): HEX or RGB string to be used as text color.
            color_text_disabled (str, optional): HEX or RGB string to be used as disabled text color.
            color_btn_hover (str, optional): HEX or RGB string to be used as button hover color.
            color_btn_pressed (str, optional): HEX or RGB string to be used as button pressed color.
            color_btn_disabled (str, optional): HEX or RGB string to be used as button disabled color.
        """
        if text is not None:
            self.surface_data_content_btn.setText(text)
        # Base
        new_stylesheet = "QPushButton {"
        if color_text:
            new_stylesheet += f"color: {color_text}; "
        if color_btn:
            new_stylesheet += f"background-color: {color_btn}; "
        new_stylesheet += "}"
        # Hover
        new_stylesheet += "\nQPushButton:hover {"
        if color_btn_hover:
            new_stylesheet += f"background-color: {color_btn_hover}; "
        new_stylesheet += "}"
        # Pressed
        new_stylesheet += "\nQPushButton:pressed {"
        if color_btn_pressed:
            new_stylesheet += f"background-color: {color_btn_pressed}; "
        new_stylesheet += "}"
        # Disabled
        new_stylesheet += "\nQPushButton:disabled {"
        if color_btn_disabled:
            new_stylesheet += f"background-color: {color_btn_disabled}; "
        if color_text_disabled:
            new_stylesheet += f"color: {color_text_disabled}; "
        new_stylesheet += "}"
        self.surface_data_content_btn.setStyleSheet(new_stylesheet)

    # Getters --------------------------------------------------------------------------------------------------
    def get_prefix(self):
        """
        Gets the current text of the prefix line edit.
        Returns:
            str: Text found in the prefix text box
        """
        return self.prefix_content.text()

    def get_mode_combobox_index(self):
        """
        Gets the current index of the mode combobox.
        0 = No Source, 1 = Surface Input, 2 = Transform List Input
        Returns:
            int: Index of the mode combobox
        """
        return self.mode_combo_box.currentIndex()

    def get_num_controls_value(self):
        """
        Gets the current value of the number of controls spin box
        Returns:
            int: Number of controls value.
        """
        return self.num_controls_content.value()

    def get_num_joints_value(self):
        """
        Gets the current value of the number of joints spin box
        Returns:
            int: Number of joints value.
        """
        return self.num_joints_content.value()

    def get_dropoff_rate_value(self):
        """
        Gets the current value of the dropoff rate spin box
        Returns:
            double: Dropoff rate value.
        """
        return self.dropoff_content.value()

    def is_equidistant_checked(self):
        """
        Gets the current value of the equidistant checkbox
        Returns:
            bool: True if checked, False otherwise.
        """
        return self.equidistant_checkbox.isChecked()

    def is_add_fk_checked(self):
        """
        Gets the current value of the add FK checkbox
        Returns:
            bool: True if checked, False otherwise.
        """
        return self.add_fk_checkbox.isChecked()

    def is_parent_skin_joints_checked(self):
        """
        Gets the current value of the parent skin joints checkbox
        Returns:
            bool: True if checked, False otherwise.
        """
        return self.parent_jnt_checkbox.isChecked()

    def is_constraint_source_checked(self):
        """
        Gets the current value of the parent skin joints checkbox
        Returns:
            bool: True if checked, False otherwise.
        """
        return self.constraint_source_checkbox.isChecked()


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = RibbonToolView(version="1.2.3")  # View
        window.set_source_data_button_values(text="Some Data", color_btn="#333333", color_text="#FFFFFF")
        window.show()
