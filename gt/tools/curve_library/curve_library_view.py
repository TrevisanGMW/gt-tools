"""
Curve Library Window
"""
from PySide2.QtWidgets import QListWidget, QPushButton, QDialog
import gt.ui.resource_library as resource_library
from PySide2 import QtWidgets, QtCore
import gt.ui.qt_utils as qt_utils
from PySide2.QtGui import QIcon
import sys


class CurveLibraryWindow(QDialog):
    def __init__(self, parent=None, controller=None):
        """
        Initialize the CurveLibraryWindow.
        This window represents the main GUI window of the tool.

        Args:
            parent (str): Parent for this window
            controller (CurveLibraryController): CurveLibraryController, not to be used, here so it's not deleted by
                                                 the garbage collector.
        """
        super().__init__(parent=parent)

        self.controller = controller  # Only here so it doesn't get deleted by the garbage collectors
        self.item_list = None
        self.build_button = None

        self.setWindowTitle("GT Curve Library")
        self.setGeometry(100, 100, 400, 300)

        self.create_widgets()
        self.create_layout()

        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.WindowMaximizeButtonHint |
                            QtCore.Qt.WindowMinimizeButtonHint)
        self.setWindowIcon(QIcon(resource_library.Icon.dev_screwdriver))

        sample_stylesheet = resource_library.Stylesheet.dark_scroll_bar
        sample_stylesheet += resource_library.Stylesheet.maya_basic_dialog
        sample_stylesheet += resource_library.Stylesheet.dark_list_widget
        self.setStyleSheet(sample_stylesheet)

        # self.setWindowFlag(QtCore.Qt.Tool, True)  # Stay On Top Modality - Fixes Mac order issue

    def create_widgets(self):
        self.item_list = QListWidget()
        self.build_button = QPushButton("Build")

    def create_layout(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 11)  # Make Margins Uniform LTRB
        main_layout.addWidget(self.item_list)
        main_layout.addWidget(self.build_button)

    def update_view_library(self, items):
        """
        Updates the view with the provided items.

        Args:
            items (list): A list of items to be displayed in the view.
        """
        self.item_list.clear()
        for item in items:
            self.item_list.addItem(item)

    def center(self):
        """ Moves window to the center of the screen """
        rect = self.frameGeometry()
        center_position = qt_utils.get_screen_center()
        rect.moveCenter(center_position)
        self.move(rect.topLeft())


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)  # Application - To launch without Maya
    window = CurveLibraryWindow()  # View
    window.show()  # Open Windows
    sys.exit(app.exec_())
