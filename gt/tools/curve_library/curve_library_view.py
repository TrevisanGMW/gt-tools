"""
Curve Library Window - The main GUI window class for the Curve Library tool.
"""
from PySide2.QtWidgets import QListWidget, QPushButton, QDialog, QWidget, QSplitter, QLineEdit, QDesktopWidget
from PySide2.QtGui import QIcon, QPainter, QPixmap
import gt.ui.resource_library as resource_library
from PySide2.QtCore import QRect, QSize
from PySide2 import QtWidgets, QtCore
import gt.ui.qt_utils as qt_utils
import sys


class SquaredWidget(QWidget):
    def __init__(self, parent=None):
        """
        A custom QWidget that displays a square image.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent=parent)
        self.p = QPixmap()

    def setPixmap(self, p):
        """
        Set the QPixmap to be displayed in the widget.

        Args:
            p (QPixmap): The QPixmap to be displayed.
        """
        self.p = p
        self.update()

    def paintEvent(self, event):
        """
        Override the paintEvent to draw the QPixmap on the widget.

        Args:
            event (QPaintEvent): The paint event.
        """
        if not self.p.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawPixmap(self.squareRect(), self.p)

    def squareRect(self):
        """
        Calculate the square QRect within the widget.

        Returns:
            QRect: The QRect representing the square area.
        """
        widget_rect = self.rect()
        size = min(widget_rect.width(), widget_rect.height())
        square_rect = QRect(0, 0, size, size)
        square_rect.moveCenter(widget_rect.center())
        return square_rect

    def resizeEvent(self, event):
        """
        Override the resizeEvent to maintain a square aspect ratio.

        Args:
            event (QResizeEvent): The resize event.
        """
        new_size = QSize(event.size().width(), event.size().height())
        square_size = min(new_size.width(), new_size.height())
        self.resize(square_size, square_size)
        super().resizeEvent(event)


class CurveLibraryWindow(QDialog):
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

        self.setWindowTitle()
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
            self.preview_image.setPixmap(QPixmap(new_image_path))
        else:
            self.preview_image.setPixmap(QPixmap(resource_library.Icon.curve_library_missing_file))

    def create_widgets(self):
        """Create the widgets for the window."""
        self.item_list = QListWidget()
        self.build_button = QPushButton("Build")
        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText('Search...')
        self.preview_image = SquaredWidget(self)
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

        preview_image_layout = QtWidgets.QVBoxLayout()

        preview_image_layout.addWidget(self.preview_image)
        preview_image_layout.addWidget(self.build_button)
        preview_container.setLayout(preview_image_layout)
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
    app = QtWidgets.QApplication(sys.argv)  # Application - To launch without Maya
    window = CurveLibraryWindow()  # View
    window.show()  # Open Windows
    sys.exit(app.exec_())
