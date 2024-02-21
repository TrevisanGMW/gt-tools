"""
Ribbon Tool View/Window/UI
"""
from PySide2.QtWidgets import QPushButton, QLabel, QVBoxLayout, QFrame, QSpinBox, QHBoxLayout, QCheckBox, QLineEdit
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
        self.title_label = None
        self.help_btn = None
        # Prefix
        self.prefix_label = None
        self.prefix_content = None
        self.prefix_clear_btn = None
        # Num Controls and Joints
        self.num_controls_label = None
        self.num_joints_label = None
        self.num_controls_content = None
        self.num_joints_content = None
        # Checkboxes
        self.equidistant_label = None
        self.add_fk_label = None
        self.equidistant_checkbox = None
        self.add_fk_checkbox = None
        self.surface_data_btn = None
        # Surface Data
        self.surface_data_label = None
        self.surface_data_multiplier_label = None
        # Buttons
        self.surface_data_set_btn = None
        self.surface_data_content_btn = None
        self.create_ribbon_btn = None
        self.save_to_shelf_btn = None

        self.create_widgets()
        self.create_layout()

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
        self.setStyleSheet(stylesheet)
        self.create_ribbon_btn.setStyleSheet(resource_library.Stylesheet.btn_push_bright)
        self.surface_data_content_btn.setStyleSheet(resource_library.Stylesheet.btn_push_bright)
        qt_utils.resize_to_screen(self, percentage=5, width_percentage=25)
        qt_utils.center_window(self)

    def create_widgets(self):
        """Create the widgets for the window."""
        self.title_label = QtWidgets.QLabel(self.window_title)
        self.title_label.setStyleSheet('background-color: rgb(93, 93, 93); border: 0px solid rgb(93, 93, 93); \
                                        color: rgb(255, 255, 255); padding: 10px; margin-bottom: 0; text-align: left;')
        self.title_label.setFont(qt_utils.get_font(resource_library.Font.roboto))
        self.help_btn = QPushButton('Help')
        self.help_btn.setToolTip("Open Help Dialog.")
        self.help_btn.setStyleSheet('color: rgb(255, 255, 255); padding: 10px; '
                                    'padding-right: 15px; padding-left: 15px; margin: 0;')
        self.help_btn.setFont(qt_utils.get_font(resource_library.Font.roboto))

        self.prefix_label = QLabel("Prefix:")
        self.prefix_content = QLineEdit()
        self.prefix_clear_btn = QPushButton("Clear")
        self.prefix_clear_btn.setStyleSheet("padding: 7; border-radius: 5px;")

        self.num_controls_label = QLabel("Number of Controls:")
        self.num_controls_label.setMinimumWidth(170)
        self.num_controls_content = QSpinBox()
        self.num_controls_content.setMinimum(1)
        self.num_controls_content.setSingleStep(1)
        self.num_controls_content.setValue(6)

        self.num_joints_label = QLabel("Number of Joints:")
        self.num_joints_label.setMinimumWidth(170)
        self.num_joints_content = QSpinBox()
        self.num_joints_content.setMinimum(0)
        self.num_joints_content.setSingleStep(1)
        self.num_joints_content.setValue(8)

        self.equidistant_label = QLabel("Equidistant:")
        self.equidistant_checkbox = QCheckBox()
        self.equidistant_checkbox.setChecked(True)
        self.add_fk_label = QLabel("Add FK:")
        self.add_fk_checkbox = QCheckBox()
        self.add_fk_checkbox.setChecked(True)

        self.surface_data_set_btn = QPushButton('Set Surface Data')
        self.surface_data_set_btn.setToolTip("Uses selection to determine surface data.")
        self.surface_data_set_btn.setStyleSheet("padding: 15;")
        self.surface_data_content_btn = QPushButton("No Data")
        self.surface_data_content_btn.setToolTip('Current Surface Data (Click to Select It)')

        self.create_ribbon_btn = QPushButton("Create Ribbon")
        self.create_ribbon_btn.setStyleSheet("padding: 10;")
        self.create_ribbon_btn.setSizePolicy(self.create_ribbon_btn.sizePolicy().Expanding,
                                             self.create_ribbon_btn.sizePolicy().Expanding)

    def create_layout(self):
        """Create the layout for the window."""
        surface_data_layout = QtWidgets.QVBoxLayout()
        two_horizontal_btn_layout = QtWidgets.QHBoxLayout()
        two_horizontal_btn_layout.addWidget(self.surface_data_set_btn)
        two_horizontal_btn_layout.addWidget(self.surface_data_content_btn)
        surface_data_layout.addLayout(two_horizontal_btn_layout)
        surface_data_layout.setContentsMargins(15, 5, 15, 10)  # L-T-R-B

        mid_layout = QVBoxLayout()

        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(self.prefix_label)
        prefix_layout.addWidget(self.prefix_content)
        prefix_layout.addWidget(self.prefix_clear_btn)
        prefix_layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        mid_layout.addLayout(prefix_layout)

        num_controls_layout = QHBoxLayout()
        num_controls_layout.addWidget(self.num_controls_label)
        num_controls_layout.addWidget(self.num_controls_content)
        mid_layout.addLayout(num_controls_layout)

        num_joints_layout = QHBoxLayout()
        num_joints_layout.addWidget(self.num_joints_label)
        num_joints_layout.addWidget(self.num_joints_content)
        mid_layout.addLayout(num_joints_layout)

        checkboxes_layout = QHBoxLayout()
        checkboxes_layout.addWidget(self.equidistant_label)
        checkboxes_layout.addWidget(self.equidistant_checkbox)
        checkboxes_layout.addWidget(self.add_fk_label)
        checkboxes_layout.addWidget(self.add_fk_checkbox)
        mid_layout.addLayout(checkboxes_layout)

        mid_layout.setContentsMargins(15, 0, 15, 15)  # L-T-R-B

        bottom_main_button_layout = QVBoxLayout()
        bottom_main_button_layout.addWidget(self.create_ribbon_btn)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)

        separator_two = QFrame()
        separator_two.setFrameShape(QFrame.HLine)
        separator_two.setFrameShadow(QFrame.Sunken)

        title_layout = QtWidgets.QHBoxLayout()
        title_layout.setSpacing(0)
        title_layout.addWidget(self.title_label, 5)
        title_layout.addWidget(self.help_btn)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        top_layout = QtWidgets.QVBoxLayout()
        bottom_layout = QtWidgets.QVBoxLayout()
        top_layout.addLayout(title_layout)
        top_layout.setContentsMargins(15, 15, 15, 15)  # L-T-R-B
        main_layout.addLayout(top_layout)
        main_layout.addLayout(mid_layout)
        main_layout.addWidget(separator)
        main_layout.addLayout(surface_data_layout)
        main_layout.addWidget(separator_two)
        bottom_layout.addLayout(bottom_main_button_layout)
        bottom_layout.setContentsMargins(15, 0, 15, 15)  # L-T-R-B
        main_layout.addLayout(bottom_layout)

    def close_window(self):
        """ Closes this window """
        self.close()


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = RibbonToolView(version="1.2.3")  # View
        window.show()
