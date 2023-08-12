from PySide2.QtCore import QRect, QSize
from PySide2.QtGui import QPixmap, QPainter
from PySide2.QtWidgets import QWidget


class SquaredWidget(QWidget):
    def __init__(self, parent=None, center_x=True, center_y=True):
        """
        A custom QWidget that displays a square image.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent=parent)
        self.pixmap = QPixmap()
        self.center_x = center_x
        self.center_y = center_y

    def center(self, center_x=True, center_y=False):
        """
        Centers the widget horizontally and/or vertically within its parent widget.

        Args:
            center_x (bool, optional): Whether to center the widget horizontally. Default is True.
            center_y (bool, optional): Whether to center the widget vertically. Default is False.
        """
        parent_geometry = self.parent().geometry()

        y = self.geometry().y()
        x = self.geometry().x()

        if center_y:
            y = (parent_geometry.height() - self.height()) / 2

        if center_x:
            x = (parent_geometry.width() - self.width()) / 2
        self.move(x, y)

    def set_pixmap(self, pixmap):
        """
        Set the QPixmap to be displayed in the widget.

        Args:
            pixmap (QPixmap): The QPixmap to be displayed.
        """
        self.pixmap = pixmap
        self.update()

    def paintEvent(self, event):
        """
        Override the paintEvent to draw the QPixmap on the widget.

        Args:
            event (QPaintEvent): The paint event.
        """
        if not self.pixmap.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawPixmap(self.square_rect(), self.pixmap)
            self.center(center_x=self.center_x, center_y=self.center_y)

    def square_rect(self):
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


if __name__ == "__main__":
    from PySide2.QtWidgets import QApplication, QMainWindow, QVBoxLayout
    from gt.ui.resource_library import Icon
    import sys

    app = QApplication(sys.argv)
    main_window = QMainWindow()
    central_widget = SquaredWidget(center_y=False)
    pixmap = QPixmap(Icon.curve_library_missing_file)
    central_widget.set_pixmap(pixmap)
    main_window.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)
    center_widget = QWidget()
    layout.addWidget(center_widget)
    main_window.show()
    sys.exit(app.exec_())
