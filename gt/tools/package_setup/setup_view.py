"""
Package Setup View
This script should only emit signals and deal with UI (View) - No unrelated logic here
"""
from PySide2.QtWidgets import QToolButton, QSizePolicy
import gt.ui.resource_library as resource_library
from PySide2 import QtWidgets, QtCore
import gt.ui.qt_utils as qt_utils
from PySide2.QtGui import QIcon
from PySide2.QtCore import Qt
import sys


class PackageSetupWindow(QtWidgets.QDialog):
    ButtonInstallClicked = QtCore.Signal()
    ButtonUninstallClicked = QtCore.Signal()
    ButtonRunOnlyClicked = QtCore.Signal()

    def __init__(self, parent=None, controller=None):
        """
        Initializes package setup model object
        Parameters:
            parent (str): Parent for this window
            controller (PackageSetupController): PackageSetupController, not to be used, but to not be deleted by
                                                 the garbage collector.
        """
        super().__init__(parent=parent)
        self.controller = controller  # Only here so it doesn't get deleted by the garbage collectors

        # Variable Initializations
        # Buttons
        self.install_btn = None
        self.uninstall_btn = None
        self.run_only_btn = None
        self.close_btn = None
        # Path
        self.label_installation_path = None
        self.line_edit_installation_path = None
        # Version and Status
        self.label_setup_version = None
        self.text_setup_version = None
        self.label_installed_version = None
        self.text_installed_version = None
        self.label_status = None
        self.text_status = None

        # Setup Window
        _min_width = 200
        _min_height = 200
        self.setGeometry(0, 0, _min_width, _min_height)  # Args X, Y, W, H
        self.setMinimumWidth(_min_width)
        self.setMinimumHeight(_min_height)
        self.setWindowTitle("GT Tools - Package Setup Window")
        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.WindowMaximizeButtonHint |
                            QtCore.Qt.WindowMinimizeButtonHint)
        self.setStyleSheet(resource_library.Stylesheet.maya_basic_dialog)
        self.setWindowIcon(QIcon(resource_library.Icon.package_icon))
        # Widgets, Layout and Connections
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        # Adjust window
        self.adjustSize()
        self.setMinimumWidth(self.width())
        self.setMinimumHeight(self.height())
        # self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
        self.center()

    def center(self):
        """ Moves window to the center of the screen """
        rect = self.frameGeometry()
        center_position = qt_utils.get_screen_center()
        rect.moveCenter(center_position)
        self.move(rect.topLeft())

    def create_widgets(self):
        """ Creates widgets """

        # Text-field path
        self.label_installation_path = QtWidgets.QLabel("Installation Path:")
        self.line_edit_installation_path = QtWidgets.QLineEdit()
        self.line_edit_installation_path.setPlaceholderText('<installation_target_path_placeholder>')
        self.line_edit_installation_path.setReadOnly(True)

        # Versions and Status
        self.label_setup_version = QtWidgets.QLabel("Setup Version:")
        self.text_setup_version = QtWidgets.QLabel("?.?.?")
        self.text_setup_version.setStyleSheet("color: green; font-weight: bold;")
        self.label_installed_version = QtWidgets.QLabel("Installed Version:")
        self.text_installed_version = QtWidgets.QLabel("?.?.?")
        self.text_installed_version.setStyleSheet("color: green; font-weight: bold;")
        self.label_status = QtWidgets.QLabel("Status:")
        self.text_status = QtWidgets.QLabel("<status_placeholder>")
        self.text_status.setStyleSheet("color: green; font-weight: bold;")

        # Buttons
        self.install_btn = QToolButton()
        self.uninstall_btn = QToolButton()
        self.run_only_btn = QToolButton()
        self.close_btn = QToolButton()
        self.install_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.uninstall_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.run_only_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.close_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.install_btn.setText("Install")
        self.uninstall_btn.setText("Uninstall")
        self.run_only_btn.setText("Run Only")
        self.close_btn.setText("Cancel")

        button_size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.install_btn.setSizePolicy(button_size_policy)
        self.uninstall_btn.setSizePolicy(button_size_policy)
        self.run_only_btn.setSizePolicy(button_size_policy)
        self.close_btn.setSizePolicy(button_size_policy)

        self.install_btn.setStyleSheet(resource_library.Stylesheet.metro_tool_button_blue)
        self.uninstall_btn.setStyleSheet(resource_library.Stylesheet.metro_tool_button_red)
        self.run_only_btn.setStyleSheet(resource_library.Stylesheet.metro_tool_button_green)
        self.close_btn.setStyleSheet(resource_library.Stylesheet.metro_tool_button)

        # Icons
        icon_sizes = QtCore.QSize(50, 50)
        icon_install = QIcon(resource_library.Icon.setup_install)
        self.install_btn.setIcon(icon_install)
        self.install_btn.setIconSize(icon_sizes)
        icon_uninstall = QIcon(resource_library.Icon.setup_uninstall)
        self.uninstall_btn.setIcon(icon_uninstall)
        self.uninstall_btn.setIconSize(icon_sizes)
        icon_run = QIcon(resource_library.Icon.setup_run_only)
        self.run_only_btn.setIcon(icon_run)
        self.run_only_btn.setIconSize(icon_sizes)
        icon_close = QIcon(resource_library.Icon.setup_close)
        self.close_btn.setIcon(icon_close)
        self.close_btn.setIconSize(icon_sizes)

        # button_size = 150
        # self.install_btn.setFixedSize(button_size, button_size)
        # self.uninstall_btn.setFixedSize(button_size, button_size)
        # self.run_only_btn.setFixedSize(button_size, button_size)
        # self.close_btn.setFixedSize(button_size, button_size)

    def create_layout(self):
        """ Creates layout """

        # Buttons
        button_layout = QtWidgets.QGridLayout()
        button_layout.addWidget(self.install_btn, 0, 0)
        button_layout.addWidget(self.uninstall_btn, 0, 1)
        button_layout.addWidget(self.run_only_btn, 0, 2)
        button_layout.addWidget(self.close_btn, 0, 3)
        button_layout.setColumnStretch(0, 1)
        button_layout.setColumnStretch(1, 1)
        button_layout.setColumnStretch(2, 1)
        button_layout.setColumnStretch(3, 1)

        # Add Layout
        target_path_layout = QtWidgets.QHBoxLayout()
        target_path_layout.addWidget(self.label_installation_path)
        target_path_layout.addWidget(self.line_edit_installation_path)

        # Version Information
        version_layout = QtWidgets.QHBoxLayout()
        version_layout.addWidget(self.label_setup_version)
        version_layout.addWidget(self.text_setup_version)
        version_layout.addWidget(self.label_installed_version)
        version_layout.addWidget(self.text_installed_version)
        version_layout.addWidget(self.label_status)
        version_layout.addWidget(self.text_status)

        # Build Main Layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)  # Margins L, T, R, B
        main_layout.addLayout(button_layout)
        main_layout.addLayout(target_path_layout)
        main_layout.addLayout(version_layout)

    def create_connections(self):
        """ Create Connections """
        self.install_btn.clicked.connect(self.button_install_clicked)
        self.uninstall_btn.clicked.connect(self.button_uninstall_clicked)
        self.run_only_btn.clicked.connect(self.button_run_only_clicked)
        self.close_btn.clicked.connect(self.close_window)

    def close_window(self):
        """ Closes this window """
        self.close()

    def button_install_clicked(self):
        """ Emits ButtonInstallClicked signal """
        self.ButtonInstallClicked.emit()

    def button_uninstall_clicked(self):
        """ Emits ButtonUninstallClicked signal """
        self.ButtonUninstallClicked.emit()

    def button_run_only_clicked(self):
        """ Emits ButtonRunOnlyClicked signal """
        self.ButtonRunOnlyClicked.emit()

    def update_installation_path_text_field(self, new_path):
        self.line_edit_installation_path.setText(new_path)

    def update_version_texts(self, new_setup_version, new_installed_version):
        self.text_setup_version.setText(new_setup_version)
        self.text_installed_version.setText(new_installed_version)

    def update_status_text(self, new_status):
        self.text_status.setText(new_status)


if __name__ == "__main__":
    # Application - To launch without Maya
    app = QtWidgets.QApplication(sys.argv)
    # Connections
    window = PackageSetupWindow()  # View
    # Open Windows
    window.show()
    sys.exit(app.exec_())
