"""
Curve Library Window - The main GUI window class for the Curve Library tool.
"""
from PySide2.QtWidgets import QListWidget, QPushButton, QWidget, QSplitter, QLineEdit, QDesktopWidget
import gt.ui.resource_library as resource_library
from gt.ui.squared_widget import SquaredWidget
from gt.ui.qt_utils import MayaWindowMeta
from PySide2.QtGui import QIcon, QPixmap
from PySide2 import QtWidgets, QtCore
import gt.ui.qt_utils as qt_utils


class CurveLibraryWindow(metaclass=MayaWindowMeta):
    def __init__(self, parent=None, controller=None, version=None):
        """
        Initialize the CurveLibraryWindow.
        This window represents the main GUI window of the tool.

        Args:
            parent (str): Parent for this window
            controller (CurveLibraryController): CurveLibraryController, not to be used, here so it's not deleted by
                                                 the garbage collector.  Defaults to None.
            version (str, optional): If provided, it will be used to determine the window title. e.g. Title - (v1.2.3)
        """
        # super(CurveLibraryWindow, self).__init__(parent=parent)
        super().__init__(parent=parent)
        self.controller = controller  # Only here so it doesn't get deleted by the garbage collectors
        self.splitter = None
        self.search_edit = None
        self.item_list = None
        self.build_button = None
        self.preview_image = None

        window_title = "GT Curve Library"
        if version:
            window_title += f' - (v{str(version)})'
        self.setWindowTitle(window_title)

        self.setGeometry(100, 100, 400, 300)

        self.create_widgets()
        self.create_layout()

        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.WindowMaximizeButtonHint |
                            QtCore.Qt.WindowMinimizeButtonHint)
        self.setWindowIcon(QIcon(resource_library.Icon.tool_crv_library))

        stylesheet = resource_library.Stylesheet.dark_scroll_bar
        stylesheet += resource_library.Stylesheet.maya_basic_dialog
        stylesheet += resource_library.Stylesheet.dark_list_widget
        self.setStyleSheet(stylesheet)
        self.resize_to_screen()
        self.center()
        # self.setWindowFlag(QtCore.Qt.Tool, True)  # Stay On Top Modality - Fixes Mac order issue

    def update_preview_image(self, new_image_path=None):
        """
        Update the preview image displayed in the window.

        Args:
            new_image_path (str, optional): The path to the new image file.
                                            Defaults to None, which becomes "missing_preview_file"
        """
        if new_image_path:
            self.preview_image.set_pixmap(QPixmap(new_image_path))
        else:
            self.preview_image.set_pixmap(QPixmap(resource_library.Icon.curve_library_missing_file))

    def create_widgets(self):
        """Create the widgets for the window."""
        self.item_list = QListWidget()
        self.build_button = QPushButton("Build")
        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText('Search...')
        self.preview_image = SquaredWidget(self, center_y=False)
        self.update_preview_image()

    def create_layout(self):
        """Create the layout for the window."""
        list_button_container = QWidget()
        list_button_layout = QtWidgets.QVBoxLayout()
        list_button_layout.addWidget(self.search_edit)
        list_button_layout.addWidget(self.item_list)
        list_button_layout.addWidget(self.build_button)
        list_button_container.setLayout(list_button_layout)
        list_button_container.setMinimumWidth(200)
        list_button_container.setMinimumHeight(200)

        preview_container = QWidget()
        # preview_container.setStyleSheet(f"background-color: #FFA500;")

        side_menu_layout = QtWidgets.QVBoxLayout()
        # preview_image_layout = QtWidgets.QVBoxLayout()
        side_menu_layout.addWidget(self.preview_image)
        # preview_image_layout.setAlignment(Qt.AlignCenter)
        # side_menu_layout.addLayout(preview_image_layout)
        side_menu_layout.addWidget(self.build_button)
        preview_container.setLayout(side_menu_layout)
        preview_container.setMinimumWidth(200)
        preview_container.setMinimumHeight(200)

        self.splitter = QSplitter(self)
        self.splitter.setHandleWidth(5)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(list_button_container)
        self.splitter.addWidget(preview_container)

        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 11)  # Make Margins Uniform LTRB
        main_layout.addWidget(self.splitter)

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

    def resize_to_screen(self, percentage=20):
        """
        Resizes the window to match a percentage of the screen size.

        Args:
            percentage (int, optional): The percentage of the screen size that the window should inherit.
                                        Must be a value between 0 and 100. Default is 20.

        Raises:
            ValueError: If the percentage is not within the range [0, 100].
        """
        if not 0 <= percentage <= 100:
            raise ValueError("Percentage should be between 0 and 100")

        screen_geometry = QDesktopWidget().availableGeometry(self)
        width = screen_geometry.width() * percentage / 100
        height = screen_geometry.height() * percentage / 100
        self.splitter.setSizes([width*.70, width*.65])
        self.setGeometry(0, 0, width, height)


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = CurveLibraryWindow()
        window.update_view_library(["curve_one", "curve_two"])
        window.show()
