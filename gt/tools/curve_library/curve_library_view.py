"""
Curve Library Window
"""
from PySide2.QtWidgets import QListWidget, QPushButton, QDialog, QWidget, QSplitter
from PySide2.QtGui import QIcon, QPainter, QPixmap
import gt.ui.resource_library as resource_library
from PySide2.QtCore import QRect, QSize
from PySide2 import QtWidgets, QtCore
import gt.ui.qt_utils as qt_utils
import sys


class SquaredWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.p = QPixmap()

    def setPixmap(self, p):
        self.p = p
        self.update()

    def paintEvent(self, event):
        if not self.p.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawPixmap(self.squareRect(), self.p)

    def squareRect(self):
        widget_rect = self.rect()
        size = min(widget_rect.width(), widget_rect.height())
        square_rect = QRect(0, 0, size, size)
        square_rect.moveCenter(widget_rect.center())
        return square_rect

    def resizeEvent(self, event):
        new_size = QSize(event.size().width(), event.size().height())
        square_size = min(new_size.width(), new_size.height())
        self.resize(square_size, square_size)
        super().resizeEvent(event)


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
        self.preview_image = None

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

    def update_preview_image(self, new_image_path):
        # Add check, in case it doesn't exist here
        self.preview_image.setPixmap(QPixmap(new_image_path))

    def create_widgets(self):
        self.item_list = QListWidget()
        self.build_button = QPushButton("Build")
        # self.preview_container = LabelBWidget(self)
        self.preview_image = SquaredWidget(self)
        self.update_preview_image(resource_library.Icon.curve_library_missing_file)

    def create_layout(self):
        list_button_container = QWidget()
        list_button_layout = QtWidgets.QVBoxLayout()
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

        splitter = QSplitter(self)
        splitter.setHandleWidth(5)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(list_button_container)
        splitter.addWidget(preview_container)
        splitter.setMaximumWidth(200)

        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 11)  # Make Margins Uniform LTRB
        main_layout.addWidget(splitter)

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
