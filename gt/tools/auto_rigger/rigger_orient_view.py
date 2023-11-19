"""
OrientationData View
"""
from PySide2.QtWidgets import QPushButton, QLabel, QVBoxLayout, QRadioButton, QComboBox, QButtonGroup, QHBoxLayout
import gt.ui.resource_library as resource_library
from gt.ui.qt_utils import MayaWindowMeta
from PySide2 import QtWidgets, QtCore
import gt.ui.qt_utils as qt_utils
from PySide2.QtGui import QIcon
from PySide2.QtCore import Qt
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RiggerOrientView(metaclass=MayaWindowMeta):
    def __init__(self, parent=None, module=None):
        """
        Initialize the RiggerOrientView.
        This window represents the main GUI window of the tool.

        Args:
            parent (str): Parent for this window
            module (ModuleGeneric): Used to apply changes and populate initial description.
        """
        super().__init__(parent=parent)

        self.module = module

        self.setWindowTitle("Editing Orientation Data")

        self.settings_label = None
        self.target_label = None
        self.aim_axis_label = None
        self.up_axis_label = None
        self.up_dir_label = None

        # Buttons
        self.cancel_btn = None
        self.save_orient_btn = None

        # Radial Btn Groups
        self.aim_axis_grp = None
        self.aim_axis_x = None
        self.aim_axis_y = None
        self.aim_axis_z = None

        self.up_axis_grp = None
        self.up_axis_x = None
        self.up_axis_y = None
        self.up_axis_z = None

        self.up_dir_grp = None
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
        self.setWindowIcon(QIcon(resource_library.Icon.tool_orient_joints))

        stylesheet = resource_library.Stylesheet.scroll_bar_base
        stylesheet += resource_library.Stylesheet.maya_dialog_base
        stylesheet += resource_library.Stylesheet.list_widget_base
        stylesheet += resource_library.Stylesheet.btn_radio_base
        stylesheet += resource_library.Stylesheet.combobox_base
        self.setStyleSheet(stylesheet)

        self.save_orient_btn.setStyleSheet(resource_library.Stylesheet.btn_push_bright)
        self.cancel_btn.setStyleSheet(resource_library.Stylesheet.btn_push_base)

        # Connections
        self.save_orient_btn.clicked.connect(self.save_orientation_to_module)
        self.cancel_btn.clicked.connect(self.close_view)

        # Initial Selection (Default)
        self.set_view_to_module_data()

        qt_utils.resize_to_screen(self, percentage=5, width_percentage=30)
        qt_utils.center_window(self)

    def create_widgets(self):
        """Create the widgets for the window."""

        _module_name = self.module.get_name() or ""
        _module_class = self.module.get_module_class_name(remove_module_prefix=False)
        if _module_name:
            _module_name = f'\n"{_module_name}" ({_module_class})'
        else:
            _module_name = f'\n{_module_class}'

        self.settings_label = QLabel(f'Orientation Data for {_module_name}')
        self.settings_label.setStyleSheet(f"font-weight: bold; font-size: 8; margin-top: 0; "
                                          f"color: {resource_library.Color.RGB.gray_lighter};")
        self.settings_label.setAlignment(Qt.AlignCenter)
        self.settings_label.setFont(qt_utils.get_font(resource_library.Font.roboto))
        self.settings_label.setFixedHeight(self.settings_label.sizeHint().height())

        self.aim_axis_label = QLabel("Aim Axis:")
        self.aim_axis_grp = QButtonGroup()
        self.aim_axis_x = QRadioButton('X')
        self.aim_axis_y = QRadioButton('Y')
        self.aim_axis_z = QRadioButton('Z')
        self.aim_axis_grp.addButton(self.aim_axis_x)
        self.aim_axis_grp.addButton(self.aim_axis_y)
        self.aim_axis_grp.addButton(self.aim_axis_z)
        self.up_axis_label = QLabel("Up Axis:")
        self.up_axis_grp = QButtonGroup()
        self.up_axis_x = QRadioButton('X')
        self.up_axis_y = QRadioButton('Y')
        self.up_axis_z = QRadioButton('Z')
        self.up_axis_grp.addButton(self.up_axis_x)
        self.up_axis_grp.addButton(self.up_axis_y)
        self.up_axis_grp.addButton(self.up_axis_z)
        self.up_dir_label = QLabel("Up Dir:")
        self.up_dir_grp = QButtonGroup()
        self.up_dir_x = QRadioButton('X')
        self.up_dir_y = QRadioButton('Y')
        self.up_dir_z = QRadioButton('Z')
        self.up_dir_grp.addButton(self.up_dir_x)
        self.up_dir_grp.addButton(self.up_dir_y)
        self.up_dir_grp.addButton(self.up_dir_z)

        self.aim_axis_mod = QComboBox()
        self.up_axis_mod = QComboBox()
        self.up_dir_mod = QComboBox()
        for combobox in [self.aim_axis_mod, self.up_axis_mod, self.up_dir_mod]:
            combobox.addItem("+")
            combobox.addItem("-")
            combobox.setMaximumWidth(50)
            combobox.setMinimumWidth(50)

        self.save_orient_btn = QPushButton("Save Orientation")
        self.save_orient_btn.setStyleSheet("padding: 10;")
        self.save_orient_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("padding: 10;")
        self.cancel_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def create_layout(self):
        """Create the layout for the window."""
        body_layout = QVBoxLayout()
        body_layout.addWidget(self.settings_label)

        aim_axis_layout = QtWidgets.QGridLayout()
        aim_axis_layout.setContentsMargins(0, 15, 0, 0)  # L-T-R-B
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

        action_layout = QHBoxLayout()
        action_layout.addWidget(self.save_orient_btn)
        action_layout.addWidget(self.cancel_btn)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        top_layout = QtWidgets.QVBoxLayout()
        top_layout.setContentsMargins(15, 15, 15, 15)  # L-T-R-B
        top_layout.addLayout(body_layout)
        bottom_layout = QtWidgets.QVBoxLayout()
        bottom_layout.setContentsMargins(15, 0, 15, 15)  # L-T-R-B
        bottom_layout.addLayout(action_layout)
        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)

    @staticmethod
    def _get_mod_value_as_int(combobox):
        """
        Converts the modifier combobox value into an integer
        Returns:
            int: An integer representing the value to be used in the vector.
                 If "+" = 1, if "-" = -1
        """
        combobox_text = combobox.currentText()
        _value = 1
        if combobox_text == "-":
            _value = -1
        return _value

    def get_aim_axis_tuple(self):
        """
        Gets a tuple with the aim axis data. e.g. (1, 0, 0) = X+
        Returns:
            tuple: A tuple describing the aim axis data
        """
        aim_axis_buttons = self.aim_axis_grp.buttons()
        _mod_value = self._get_mod_value_as_int(self.aim_axis_mod)
        _aim_list = []
        for btn in aim_axis_buttons:
            if btn.isChecked():
                _aim_list.append(_mod_value)
            else:
                _aim_list.append(0)
        return tuple(_aim_list)

    def get_up_axis_tuple(self):
        """
        Gets a tuple with the up axis data. e.g. (1, 0, 0) = X+
        Returns:
            tuple: A tuple describing the up axis data
        """
        up_axis_buttons = self.up_axis_grp.buttons()
        _mod_value = self._get_mod_value_as_int(self.up_axis_mod)
        _up_list = []
        for btn in up_axis_buttons:
            if btn.isChecked():
                _up_list.append(_mod_value)
            else:
                _up_list.append(0)
        return tuple(_up_list)

    def get_up_dir_tuple(self):
        """
        Gets a tuple with the up dir data. e.g. (1, 0, 0) = X+
        Returns:
            tuple: A tuple describing the up dir data
        """
        up_dir_buttons = self.up_dir_grp.buttons()
        _mod_value = self._get_mod_value_as_int(self.up_dir_mod)
        _up_dir_list = []
        for btn in up_dir_buttons:
            if btn.isChecked():
                _up_dir_list.append(_mod_value)
            else:
                _up_dir_list.append(0)
        return tuple(_up_dir_list)

    def set_view_to_module_data(self):
        """
        Extracts the current data stored in the module and configures the view to match it
        """
        self.aim_axis_x.setChecked(True)
        self.up_axis_y.setChecked(True)
        self.up_dir_y.setChecked(True)
        _orientation = self.module.get_orientation_data()

        try:
            x, y, z = _orientation.get_aim_axis() or (0, 0, 0)
            if x != 0:
                self.aim_axis_x.setChecked(True)
            elif y != 0:
                self.aim_axis_y.setChecked(True)
            elif z != 0:
                self.aim_axis_z.setChecked(True)
            # Modifier
            _mod_value = x + y + z
            if _mod_value > 0:
                self.aim_axis_mod.setCurrentIndex(0)
            else:
                self.aim_axis_mod.setCurrentIndex(1)
        except Exception as e:
            logger.debug(f'Unable to retrieve aim axis from OrientationData. Issue: {e}')

        try:
            x, y, z = _orientation.get_up_axis() or (0, 0, 0)
            if x != 0:
                self.up_axis_x.setChecked(True)
            elif y != 0:
                self.up_axis_y.setChecked(True)
            elif z != 0:
                self.up_axis_z.setChecked(True)
            # Modifier
            _mod_value = x + y + z
            if _mod_value > 0:
                self.up_axis_mod.setCurrentIndex(0)
            else:
                self.up_axis_mod.setCurrentIndex(1)
        except Exception as e:
            logger.debug(f'Unable to retrieve up axis from OrientationData. Issue: {e}')

        try:
            x, y, z = _orientation.get_up_dir() or (0, 0, 0)
            if x != 0:
                self.up_dir_x.setChecked(True)
            elif y != 0:
                self.up_dir_y.setChecked(True)
            elif z != 0:
                self.up_dir_z.setChecked(True)
            # Modifier
            _mod_value = x + y + z
            if _mod_value > 0:
                self.up_dir_mod.setCurrentIndex(0)
            else:
                self.up_dir_mod.setCurrentIndex(1)
        except Exception as e:
            logger.debug(f'Unable to retrieve up direction from OrientationData. Issue: {e}')

    def save_orientation_to_module(self):
        """
        Saves the orientation described in the view back into the module
        """
        _new_orientation = OrientationData()
        _new_orientation.set_aim_axis(aim_axis=self.get_aim_axis_tuple())
        _new_orientation.set_up_axis(up_axis=self.get_up_axis_tuple())
        _new_orientation.set_up_dir(up_dir=self.get_up_dir_tuple())
        self.module.set_orientation(orientation_data=_new_orientation)
        self.close_view()

    def close_view(self):
        self.close()


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from gt.tools.auto_rigger.rig_framework import ModuleGeneric, OrientationData

    _a_module = ModuleGeneric(name="My Module")
    _an_orientation = OrientationData(method=OrientationData.Methods.automatic,
                                      aim_axis=(0, -1, 0), up_axis=(1, 0, 0), up_dir=(0, 0, -1))
    _a_module.set_orientation(orientation_data=_an_orientation)

    with qt_utils.QtApplicationContext():
        window = RiggerOrientView(module=_a_module)  # View
        window.show()
