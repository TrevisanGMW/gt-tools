"""
Curve Library Window - The main GUI window class for the Curve Library tool.
"""
from PySide2.QtWidgets import QListWidget, QPushButton, QDialog, QWidget, QSplitter, QLineEdit, QDesktopWidget, QLabel
from PySide2.QtGui import QIcon, QPainter, QPixmap
import gt.ui.resource_library as resource_library
from PySide2.QtCore import QRect, QSize
from PySide2 import QtWidgets, QtCore
import gt.ui.qt_utils as qt_utils
import sys


class PackageUpdaterView(QDialog):
    def __init__(self, parent=None, controller=None):
        """
        Initialize the PackageUpdater.
        This window represents the main GUI window of the tool.

        Args:
            parent (str): Parent for this window
            controller (PackageUpdaterController): PackageUpdaterController, not to be used, here so it's not deleted
                                                   by the garbage collector.  Defaults to None.
        """
        super().__init__(parent=parent)
        self.controller = controller  # Only here so it doesn't get deleted by the garbage collectors
        # Labels
        self.title_label = None
        self.status_label = None
        self.status_label = None
        self.web_response_label = None
        self.installed_version_label = None
        self.latest_release_label = None
        self.changelog_box_title = None
        # Buttons
        self.update_button = None
        self.refresh_button = None
        self.interval_button = None
        self.auto_check_button = None
        # Misc
        self.changelog_box = None

        self.setWindowTitle("Package Updater")
        self.setGeometry(100, 100, 400, 300)

        self.create_widgets()
        self.create_layout()

        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.WindowMaximizeButtonHint |
                            QtCore.Qt.WindowMinimizeButtonHint)
        self.setWindowIcon(QIcon(resource_library.Icon.dev_screwdriver))

        stylesheet = resource_library.Stylesheet.dark_scroll_bar
        stylesheet += resource_library.Stylesheet.maya_basic_dialog
        stylesheet += resource_library.Stylesheet.dark_list_widget
        self.setStyleSheet(stylesheet)
        qt_utils.resize_to_screen(self)
        qt_utils.center_window(self)
        # self.setWindowFlag(QtCore.Qt.Tool, True)  # Stay On Top Modality - Fixes Mac order issue

    def create_widgets(self):
        """Create the widgets for the window."""
        self.title_label = QtWidgets.QLabel("Package Updater")
        self.title_label.setStyleSheet('background-color: rgb(93, 93, 93); \
                                                border: 0px solid rgb(93, 93, 93); \
                                                color: rgb(255, 255, 255);\
                                                font: bold 12px; \
                                                padding: 5px;')
        self.status_label = QLabel("Status:")
        self.web_response_label = QLabel("Web Response:")
        self.installed_version_label = QLabel("Installed Version:")
        self.latest_release_label = QLabel("Latest Release:")
        self.changelog_box_title = QLabel("Latest Release Changelog:")

        self.changelog_box = QLineEdit()

        self.update_button = QPushButton("Update")
        self.refresh_button = QPushButton("Refresh")
        self.interval_button = QPushButton("Auto Check For Updates: Activated")
        self.auto_check_button = QPushButton("Interval: 15 Days")

    def create_layout(self):
        """Create the layout for the window."""
        button_layout = QtWidgets.QVBoxLayout()
        button_layout.addWidget(self.title_label)
        button_layout.addWidget(self.status_label)
        button_layout.addWidget(self.web_response_label)
        button_layout.addWidget(self.installed_version_label)
        button_layout.addWidget(self.latest_release_label)
        button_layout.addWidget(self.changelog_box_title)

        button_layout.addWidget(self.changelog_box)

        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.interval_button)
        button_layout.addWidget(self.auto_check_button)

        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 11)  # Make Margins Uniform LTRB
        main_layout.addLayout(button_layout)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)  # Application - To launch without Maya
    window = PackageUpdaterView()  # View
    window.show()  # Open Windows
    sys.exit(app.exec_())
