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
        self.text_field = None
        self.label_text_field = None
        self.install_btn = None
        self.uninstall_btn = None
        self.close_btn = None
        # Setup Window
        _min_width = 500
        _min_height = 200
        self.setGeometry(0, 0, _min_width, _min_height)  # Args X, Y, W, H
        self.setMinimumWidth(_min_width)
        self.setMinimumHeight(_min_height)
        self.setWindowTitle("Package Setup Window")
        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.WindowMaximizeButtonHint |
                            QtCore.Qt.WindowMinimizeButtonHint)
        self.setStyleSheet(resource_library.Stylesheet.dark_style_stylesheet)  # Temporary
        self.setWindowIcon(QIcon(resource_library.Icon.cog_icon))
        # Widgets, Layout and Connections
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        # Adjust window
        self.adjustSize()
        self.setMinimumWidth(self.width())
        self.setMinimumHeight(self.height())
        self.center()

    def center(self):
        """ Move window to the center of the window """
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

        self.label_text_field = QtWidgets.QLabel("Text to print")
        self.text_field = QtWidgets.QLineEdit()
        self.text_field.setPlaceholderText('hello world')

        self.install_btn = QtWidgets.QPushButton('Install')
        self.uninstall_btn = QtWidgets.QPushButton('Uninstall')
        self.close_btn = QtWidgets.QPushButton('Cancel')

    def create_layout(self):
        """ Creates layout """
        label_logo = QtWidgets.QHBoxLayout()
        label_logo.addWidget(self.label_logo)

        # Add Brick
        label_layout = QtWidgets.QHBoxLayout()
        label_layout.addWidget(self.label_text_field)
        label_layout.addWidget(self.text_field)

        # Buttons Bottom
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.install_btn)
        button_layout.addWidget(self.uninstall_btn)
        button_layout.addWidget(self.close_btn)

        # Build Main Layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)  # Margins L, T, R, B
        main_layout.addLayout(label_logo)
        main_layout.addLayout(label_layout)
        main_layout.addLayout(button_layout)

    def create_connections(self):
        """ Create Connections """
        self.install_btn.clicked.connect(self.button_install_clicked)
        self.uninstall_btn.clicked.connect(self.button_uninstall_clicked)
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


if __name__ == "__main__":
    # Application - To launch without Maya
    app = QtWidgets.QApplication(sys.argv)
    # Connections
    window = PackageSetupWindow()  # View
    # Open Windows
    window.show()
    sys.exit(app.exec_())
