"""
Orient Joints View/Window
"""
from PySide2.QtWidgets import QPushButton, QLabel, QVBoxLayout, QFrame, QRadioButton, QComboBox
import gt.ui.resource_library as resource_library
from gt.ui.qt_utils import MayaWindowMeta
from PySide2 import QtWidgets, QtCore
import gt.ui.qt_utils as qt_utils
from PySide2.QtGui import QIcon


class OrientJointsView(metaclass=MayaWindowMeta):
    def __init__(self, parent=None, controller=None, version=None):
        """
        Initialize the OrientJointsView.
        This window represents the main GUI window of the tool.

        Args:
            parent (str): Parent for this window
            controller (OrientJointsViewController): OrientJointsViewController, not to be used, here so
                                                          it's not deleted by the garbage collector.  Defaults to None.
            version (str, optional): If provided, it will be used to determine the window title. e.g. Title - (v1.2.3)
        """
        super().__init__(parent=parent)

        self.controller = controller  # Only here so it doesn't get deleted by the garbage collectors

        # Window Title
        self.window_title = "GT Orient Joints"
        _window_title = self.window_title
        if version:
            _window_title += f' - (v{str(version)})'
        self.setWindowTitle(_window_title)

        # Labels
        self.title_label = None
        self.utilities_label = None
        self.settings_label = None
        self.target_label = None
        self.aim_axis_label = None
        self.up_axis_label = None
        self.up_dir_label = None
        # Buttons
        self.help_btn = None
        self.show_axis_btn = None
        self.hide_axis_btn = None
        self.copy_parent_btn = None
        self.copy_world_btn = None
        self.orient_joints_btn = None
        # Radial Btn
        self.target_selected = None
        self.target_hierarchy = None
        self.aim_axis_x = None
        self.aim_axis_y = None
        self.aim_axis_z = None
        self.up_axis_x = None
        self.up_axis_y = None
        self.up_axis_z = None
        self.up_dir_x = None
        self.up_dir_y = None
        self.up_dir_z = None
        # Combo Boxes
        self.aim_axis_mod = None
        self.up_axis_mod = None
        self.up_dir_mod = None

        self.create_widgets()
        self.create_layout()

        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.WindowMaximizeButtonHint |
                            QtCore.Qt.WindowMinimizeButtonHint)
        self.setWindowIcon(QIcon(resource_library.Icon.tool_attributes_to_python))

        stylesheet = resource_library.Stylesheet.scroll_bar_base
        stylesheet += resource_library.Stylesheet.maya_dialog_base
        stylesheet += resource_library.Stylesheet.list_widget_base
        self.setStyleSheet(stylesheet)

        self.show_axis_btn.setStyleSheet(resource_library.Stylesheet.push_button_base)
        self.hide_axis_btn.setStyleSheet(resource_library.Stylesheet.push_button_base)
        self.orient_joints_btn.setStyleSheet(resource_library.Stylesheet.push_button_bright)
        self.hide_axis_btn.setStyleSheet(resource_library.Stylesheet.push_button_base)
        self.copy_parent_btn.setStyleSheet(resource_library.Stylesheet.push_button_base)
        self.copy_world_btn.setStyleSheet(resource_library.Stylesheet.push_button_base)

        qt_utils.resize_to_screen(self, percentage=20, width_percentage=30)
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

        self.utilities_label = QLabel("Utilities:")
        self.utilities_label.setStyleSheet(f"font-weight: bold; font-size: 8; margin-top: 0; "
                                           f"color: {resource_library.Color.RGB.gray_lighter};")

        self.utilities_label.setAlignment(QtCore.Qt.AlignCenter)
        self.utilities_label.setFont(qt_utils.get_font(resource_library.Font.roboto))

        self.settings_label = QLabel("Orientation Settings:")
        self.settings_label.setStyleSheet(f"font-weight: bold; font-size: 8; margin-top: 0; "
                                          f"color: {resource_library.Color.RGB.gray_lighter};")

        self.settings_label.setAlignment(QtCore.Qt.AlignCenter)
        self.settings_label.setFont(qt_utils.get_font(resource_library.Font.roboto))

        self.show_axis_btn = QPushButton('Show Axis')
        self.show_axis_btn.setToolTip('Set the visibility of the local rotation axis to on (active)')
        self.show_axis_btn.setStyleSheet("padding: 10;")

        self.hide_axis_btn = QPushButton('Hide Axis')
        self.hide_axis_btn.setToolTip('Set the visibility of the local rotation axis to off (inactive)')
        self.hide_axis_btn.setStyleSheet("padding: 10;")

        self.copy_parent_btn = QPushButton('Copy Parent')
        self.copy_parent_btn.setToolTip("Match orientation of the parent")
        self.copy_parent_btn.setStyleSheet("padding: 10;")

        self.copy_world_btn = QPushButton("Copy World")
        self.copy_world_btn.setToolTip("Match orientation of the world (origin)")
        self.copy_world_btn.setStyleSheet("padding: 10;")

        self.target_label = QLabel("Target:")
        self.target_selected = QRadioButton('Selected')
        self.target_hierarchy = QRadioButton('Hierarchy')
        self.aim_axis_label = QLabel("Aim Axis:")
        self.aim_axis_x = QRadioButton('X')
        self.aim_axis_y = QRadioButton('Y')
        self.aim_axis_z = QRadioButton('Z')
        self.up_axis_label = QLabel("Up Axis:")
        self.up_axis_x = QRadioButton('X')
        self.up_axis_y = QRadioButton('Y')
        self.up_axis_z = QRadioButton('Z')
        self.up_dir_label = QLabel("Up Dir:")
        self.up_dir_x = QRadioButton('X')
        self.up_dir_y = QRadioButton('Y')
        self.up_dir_z = QRadioButton('Z')

        self.aim_axis_mod = QComboBox()
        self.up_axis_mod = QComboBox()
        self.up_dir_mod = QComboBox()

        self.orient_joints_btn = QPushButton("Orient Joints")
        self.orient_joints_btn.setStyleSheet("padding: 10;")

    def create_layout(self):
        """Create the layout for the window."""
        title_layout = QtWidgets.QHBoxLayout()
        title_layout.setSpacing(0)
        title_layout.addWidget(self.title_label, 5)
        title_layout.addWidget(self.help_btn)

        utility_layout = QtWidgets.QVBoxLayout()
        utility_layout.addWidget(self.utilities_label)
        axis_layout = QtWidgets.QHBoxLayout()
        axis_layout.addWidget(self.show_axis_btn)
        axis_layout.addWidget(self.hide_axis_btn)
        copy_layout = QtWidgets.QHBoxLayout()
        copy_layout.addWidget(self.copy_parent_btn)
        copy_layout.addWidget(self.copy_world_btn)
        utility_layout.addLayout(axis_layout)
        utility_layout.addLayout(copy_layout)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)

        body_layout = QVBoxLayout()
        body_layout.addWidget(self.settings_label)

        target_layout = QtWidgets.QGridLayout()
        target_layout.addWidget(self.target_label, 0, 0)
        target_layout.addWidget(self.target_selected, 0, 1)
        target_layout.addWidget(self.target_hierarchy, 0, 2)
        body_layout.addLayout(target_layout)

        aim_axis_layout = QtWidgets.QGridLayout()
        aim_axis_layout.addWidget(self.aim_axis_label, 0, 0)
        aim_axis_layout.addWidget(self.aim_axis_x, 0, 1)
        aim_axis_layout.addWidget(self.aim_axis_y, 0, 2)
        aim_axis_layout.addWidget(self.aim_axis_z, 0, 3)
        aim_axis_layout.addWidget(self.aim_axis_mod, 0, 4)
        body_layout.addLayout(aim_axis_layout)

        up_axis_layout = QtWidgets.QGridLayout()
        up_axis_layout.addWidget(self.up_axis_label, 0, 0)
        up_axis_layout.addWidget(self.up_axis_x, 0, 1)
        up_axis_layout.addWidget(self.up_axis_y, 0, 2)
        up_axis_layout.addWidget(self.up_axis_z, 0, 3)
        up_axis_layout.addWidget(self.up_axis_mod, 0, 4)
        body_layout.addLayout(up_axis_layout)

        up_dir_layout = QtWidgets.QGridLayout()
        up_dir_layout.addWidget(self.up_dir_label, 0, 0)
        up_dir_layout.addWidget(self.up_dir_x, 0, 1)
        up_dir_layout.addWidget(self.up_dir_y, 0, 2)
        up_dir_layout.addWidget(self.up_dir_z, 0, 3)
        up_dir_layout.addWidget(self.up_dir_mod, 0, 4)
        body_layout.addLayout(up_dir_layout)
        body_layout.setContentsMargins(20, 5, 20, 5)  # L-T-R-B

        action_layout = QVBoxLayout()
        action_layout.addWidget(self.orient_joints_btn)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        top_layout = QtWidgets.QVBoxLayout()
        bottom_layout = QtWidgets.QVBoxLayout()
        top_layout.addLayout(title_layout)
        top_layout.addLayout(utility_layout)
        top_layout.setContentsMargins(15, 15, 15, 15)  # L-T-R-B
        main_layout.addLayout(top_layout)
        main_layout.addWidget(separator)
        bottom_layout.addLayout(body_layout)
        bottom_layout.addLayout(action_layout)
        bottom_layout.setContentsMargins(15, 0, 15, 15)  # L-T-R-B
        main_layout.addLayout(bottom_layout)


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = OrientJointsView(version="1.2.3")  # View
        window.show()
