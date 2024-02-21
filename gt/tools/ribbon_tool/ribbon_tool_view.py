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
        self.prefix_content = QLineEdit()
        self.prefix_clear_btn = QPushButton("Clear")
        self.prefix_clear_btn.setStyleSheet("padding: 7; border-radius: 5px;")

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
        self.equidistant_label.setMinimumWidth(100)
        self.equidistant_checkbox = QCheckBox()
        self.equidistant_checkbox.setChecked(True)
        self.add_fk_label = QLabel("Add FK:")
        self.add_fk_label.setMinimumWidth(100)
        self.add_fk_checkbox = QCheckBox()
        self.add_fk_checkbox.setChecked(True)
        self.drive_list_label = QLabel("Constraint Source:")
        self.drive_list_label.setMinimumWidth(100)
        self.drive_list_checkbox = QCheckBox()
        self.drive_list_checkbox.setChecked(True)
        self.parent_jnt_label = QLabel("Parent Skin Joints:")
        self.parent_jnt_label.setMinimumWidth(100)
        self.parent_jnt_checkbox = QCheckBox()
        self.parent_jnt_checkbox.setChecked(True)

        # Surface Data / Mode
        self.mode_label = QLabel("Mode:")
        self.mode_combo_box = QComboBox()
        self.mode_combo_box.addItems(["Ribbon Simple", "Ribbon from Surface", "Ribbon from List"])
        self.mode_combo_box.setStyleSheet("padding: 5;")

        self.surface_data_set_btn = QPushButton('Set Surface Data')
        self.surface_data_set_btn.setToolTip("Uses selection to determine surface data.")
        self.surface_data_set_btn.setStyleSheet("padding: 15;")
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
        self.surface_data_content_btn.setStyleSheet(resource_library.Stylesheet.btn_push_bright)
        qt_utils.center_window(self)

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

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(self.mode_label)
        mode_layout.addWidget(self.mode_combo_box)
        mode_layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        body_layout.addLayout(mode_layout)

        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(self.prefix_label)
        prefix_layout.addWidget(self.prefix_content)
        prefix_layout.addWidget(self.prefix_clear_btn)
        prefix_layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        body_layout.addLayout(prefix_layout)

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
        checkboxes_two_layout.addWidget(self.drive_list_label)
        checkboxes_two_layout.addWidget(self.drive_list_checkbox)

        body_layout.addLayout(checkboxes_two_layout)

        surface_layout = QtWidgets.QVBoxLayout()
        surface_data_layout = QtWidgets.QHBoxLayout()
        surface_data_layout.addWidget(self.surface_data_set_btn)
        surface_data_layout.addWidget(self.surface_data_content_btn)
        surface_layout.addLayout(surface_data_layout)
        surface_layout.setContentsMargins(15, 5, 15, 10)  # L-T-R-B
        body_layout.addLayout(body_layout)

        bottom_main_button_layout = QVBoxLayout()
        bottom_main_button_layout.addWidget(self.create_ribbon_btn)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        top_layout = QtWidgets.QVBoxLayout()
        bottom_layout = QtWidgets.QVBoxLayout()
        top_layout.addLayout(title_layout)
        top_layout.setContentsMargins(15, 15, 15, 10)  # L-T-R-B
        main_layout.addLayout(top_layout)
        main_layout.addLayout(body_layout)
        # main_layout.addLayout(surface_layout)
        main_layout.addWidget(separator)
        bottom_layout.addLayout(bottom_main_button_layout)
        bottom_layout.setContentsMargins(15, 0, 15, 15)  # L-T-R-B
        main_layout.addLayout(bottom_layout)

    def update_ui_from_mode(self, index):
        print("Changed!")
        # if index == 0:  # Ribbon simple
        #     self.button1.setEnabled(False)
        #     self.button2.setEnabled(False)
        #     self.checkbox.setEnabled(False)
        # elif index == 1:  # Ribbon from existing surface
        #     self.button1.setEnabled(True)
        #     self.button2.setEnabled(False)
        #     self.checkbox.setEnabled(False)
        # elif index == 2:  # Ribbon from object list
        #     self.button1.setEnabled(False)
        #     self.button2.setEnabled(True)
        #     self.checkbox.setEnabled(True)

    def close_window(self):
        """ Closes this window """
        self.close()


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = RibbonToolView(version="1.2.3")  # View
        window.show()
