"""Create FK Driver view."""

import gt.ui.qt_import as ui_qt
import gt.ui.qt_utils as qt_utils
import gt.ui.resource_library as ui_res_lib


class CreateFkDriverView(metaclass=qt_utils.MayaWindowMeta):
    """Qt interface for Create FK Driver."""

    def __init__(self, parent=None, version=None):
        """Initializes the view.

        Args:
            parent (QWidget, optional): Parent widget.
            version (str, optional): Tool version.
        """
        super().__init__(parent=parent)
        title = "Create FK Driver"
        if version:
            title += " - (v{})".format(version)
        self.setWindowTitle(title)
        self.setMinimumWidth(390)
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_create_fk))
        self.setStyleSheet(ui_res_lib.Stylesheet.maya_dialog_base + ui_res_lib.Stylesheet.combobox_base)
        self._build_widgets()
        qt_utils.center_window(self)

    def _build_widgets(self):
        """Builds the complete interface with comfortable outer spacing."""
        layout = ui_qt.QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(10)
        description = ui_qt.QtWidgets.QLabel(
            "Create animator controls and offset groups for selected joints. Controls can follow the joint hierarchy."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        behavior_group = ui_qt.QtWidgets.QGroupBox("Behavior")
        behavior_layout = ui_qt.QtWidgets.QGridLayout(behavior_group)
        behavior_layout.setContentsMargins(12, 14, 12, 12)
        behavior_layout.setHorizontalSpacing(12)
        behavior_layout.setVerticalSpacing(8)
        self.mimic_hierarchy_checkbox = ui_qt.QtWidgets.QCheckBox("Mimic Joint Hierarchy")
        self.constraint_joints_checkbox = ui_qt.QtWidgets.QCheckBox("Constrain Joints")
        self.colorize_controls_checkbox = ui_qt.QtWidgets.QCheckBox("Colorize Controls")
        self.include_hierarchy_checkbox = ui_qt.QtWidgets.QCheckBox("Include Joint Hierarchy")
        behavior_layout.addWidget(self.mimic_hierarchy_checkbox, 0, 0)
        behavior_layout.addWidget(self.constraint_joints_checkbox, 0, 1)
        behavior_layout.addWidget(self.colorize_controls_checkbox, 1, 0)
        behavior_layout.addWidget(self.include_hierarchy_checkbox, 1, 1)
        layout.addWidget(behavior_group)

        shape_group = ui_qt.QtWidgets.QGroupBox("Control Shape")
        shape_layout = ui_qt.QtWidgets.QGridLayout(shape_group)
        shape_layout.setContentsMargins(12, 14, 12, 12)
        shape_layout.setSpacing(8)
        self.curve_type_combo = ui_qt.QtWidgets.QComboBox()
        self.curve_type_combo.addItems(["Circle", "Cube", "Pin", "Custom Python"])
        self.radius_spinbox = ui_qt.QtWidgets.QDoubleSpinBox()
        self.radius_spinbox.setRange(0.001, 100000.0)
        self.radius_spinbox.setDecimals(3)
        self.radius_spinbox.setSingleStep(0.1)
        self.custom_curve_edit = ui_qt.QtWidgets.QPlainTextEdit()
        self.custom_curve_edit.setPlaceholderText("Python code that creates one Maya curve transform using cmds.")
        self.custom_curve_edit.setMinimumHeight(80)
        self.custom_curve_edit.setToolTip("Advanced: trusted Python code executed when Custom Python is selected.")
        shape_layout.addWidget(ui_qt.QtWidgets.QLabel("Shape"), 0, 0)
        shape_layout.addWidget(self.curve_type_combo, 0, 1)
        shape_layout.addWidget(ui_qt.QtWidgets.QLabel("Radius"), 0, 2)
        shape_layout.addWidget(self.radius_spinbox, 0, 3)
        shape_layout.addWidget(self.custom_curve_edit, 1, 0, 1, 4)
        layout.addWidget(shape_group)

        naming_group = ui_qt.QtWidgets.QGroupBox("Naming")
        naming_layout = ui_qt.QtWidgets.QGridLayout(naming_group)
        naming_layout.setContentsMargins(12, 14, 12, 12)
        naming_layout.setSpacing(8)
        self.joint_suffix_field = ui_qt.QtWidgets.QLineEdit()
        self.control_suffix_field = ui_qt.QtWidgets.QLineEdit()
        self.control_group_suffix_field = ui_qt.QtWidgets.QLineEdit()
        self.ignored_strings_field = ui_qt.QtWidgets.QLineEdit()
        for column, (label, field) in enumerate([
            ("Joint Suffix", self.joint_suffix_field),
            ("Control Suffix", self.control_suffix_field),
            ("Group Suffix", self.control_group_suffix_field),
        ]):
            naming_layout.addWidget(ui_qt.QtWidgets.QLabel(label), 0, column)
            naming_layout.addWidget(field, 1, column)
        naming_layout.addWidget(ui_qt.QtWidgets.QLabel("Ignore joints containing (comma separated)"), 2, 0, 1, 3)
        naming_layout.addWidget(self.ignored_strings_field, 3, 0, 1, 3)
        layout.addWidget(naming_group)

        button_layout = ui_qt.QtWidgets.QHBoxLayout()
        button_layout.setSpacing(8)
        self.reset_button = ui_qt.QtWidgets.QPushButton("Reset Settings")
        self.generate_button = ui_qt.QtWidgets.QPushButton("Create FK Drivers")
        self.reset_button.setMinimumHeight(34)
        self.generate_button.setMinimumHeight(40)
        self.generate_button.setStyleSheet(ui_res_lib.Stylesheet.btn_push_bright)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.generate_button, 1)
        layout.addLayout(button_layout)

    def set_custom_curve_visible(self, visible):
        """Shows the custom curve editor only when it is relevant.

        Args:
            visible (bool): Custom editor visibility.
        """
        self.custom_curve_edit.setVisible(bool(visible))


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = CreateFkDriverView()
        window.show()
