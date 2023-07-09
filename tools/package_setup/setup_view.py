"""
QT View example - This script should only emit signals and deal with UI (View) - No unrelated logic here
"""
import ui.resource_library as resource_library
import ui.qt_utils as qt_utils
import sys
from PySide2.QtGui import QPixmap, QIcon
from PySide2 import QtWidgets, QtCore


class PackageSetupWindow(QtWidgets.QDialog):
    ButtonInstallClicked = QtCore.Signal()
    ButtonUninstallClicked = QtCore.Signal()
    ButtonRunOnlyClicked = QtCore.Signal()

    def __init__(self, parent=None, controller=None):
        super().__init__(parent=parent)
        self.controller = controller  # Only here so it doesn't get deleted by the garbage collectors

        # Variable Initializations
        self.label_logo = None
        # Path
        self.text_field_installation_path = None
        self.label_text_field = None
        # Version and Status
        self.label_setup_version = None
        self.text_setup_version = None
        self.label_installed_version = None
        self.text_installed_version = None
        self.label_status = None
        self.text_status = None
        # Buttons
        self.install_btn = None
        self.uninstall_btn = None
        self.run_only_btn = None
        self.close_btn = None

        # Setup Window
        _min_width = 500
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
        # Logo
        self.label_logo = QtWidgets.QLabel(self)
        logo_pixmap = QPixmap(resource_library.Icon.package_logo)
        self.label_logo.setPixmap(logo_pixmap)
        self.label_logo.resize(logo_pixmap.width(), logo_pixmap.height())

        # Text-field path
        self.label_text_field = QtWidgets.QLabel("Installation Path:")
        self.text_field_installation_path = QtWidgets.QLineEdit()
        self.text_field_installation_path.setPlaceholderText('<installation_target_path_placeholder>')
        self.text_field_installation_path.setReadOnly(True)

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
        self.install_btn = QtWidgets.QPushButton('Install')
        self.uninstall_btn = QtWidgets.QPushButton('Uninstall')
        self.run_only_btn = QtWidgets.QPushButton('Run Only')
        self.close_btn = QtWidgets.QPushButton('Cancel')

    def create_layout(self):
        """ Creates layout """
        label_logo = QtWidgets.QHBoxLayout()
        label_logo.addWidget(self.label_logo)

        # Add Layout
        target_path_layout = QtWidgets.QHBoxLayout()
        target_path_layout.addWidget(self.label_text_field)
        target_path_layout.addWidget(self.text_field_installation_path)

        # Version Information
        version_layout = QtWidgets.QHBoxLayout()
        version_layout.addWidget(self.label_setup_version)
        version_layout.addWidget(self.text_setup_version)
        version_layout.addWidget(self.label_installed_version)
        version_layout.addWidget(self.text_installed_version)
        version_layout.addWidget(self.label_status)
        version_layout.addWidget(self.text_status)

        # Action Buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.install_btn)
        button_layout.addWidget(self.uninstall_btn)
        button_layout.addWidget(self.run_only_btn)
        button_layout.addWidget(self.close_btn)

        # Build Main Layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)  # Margins L, T, R, B
        main_layout.addLayout(label_logo)
        main_layout.addLayout(version_layout)
        main_layout.addLayout(target_path_layout)
        main_layout.addLayout(button_layout)

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
        self.text_field_installation_path.setText(new_path)

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
