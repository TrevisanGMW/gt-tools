from PySide2.QtWidgets import QFrame, QWidget, QTextEdit, QHBoxLayout, QDialog, QVBoxLayout
from PySide2.QtGui import QPainter, QColor
from gt.ui import resource_library
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LineTextWidget(QFrame):
    """
    A custom widget for displaying line numbers alongside a QTextEdit.
    """
    class NumberBar(QWidget):
        """
        Widget for displaying line numbers.
        """

        def __init__(self, *args):
            super().__init__(*args)
            self.text_edit = None
            self.highest_line = 0  # This is used to update the width of the control.
            self.number_color = QColor(resource_library.Color.Hex.gray_lighter)
            self.number_bold_color = QColor(resource_library.Color.Hex.gray_lighter)
            self.bar_width_offset = 5

        def set_text_edit(self, edit):
            """
            Set the QTextEdit instance to be associated with this NumberBar.
            """
            self.text_edit = edit

        def update(self, *args):
            """
            Updates the number bar to display the current set of numbers.
            Also, adjusts the width of the number bar if necessary.
            """
            # The + 4 is used to compensate for the current line being bold.
            width = self.fontMetrics().boundingRect(str(self.highest_line)).width() + self.bar_width_offset
            if self.width() != width:
                self.setFixedWidth(width)
            super().update(*args)

        def paintEvent(self, event):
            """
            Paint the line numbers.
            """
            contents_y = self.text_edit.verticalScrollBar().value()
            page_bottom = contents_y + self.text_edit.viewport().height()
            font_metrics = self.fontMetrics()
            current_block = self.text_edit.document().findBlock(self.text_edit.textCursor().position())

            painter = QPainter(self)

            line_count = 0
            # Iterate over all text blocks in the document.
            block = self.text_edit.document().begin()
            while block.isValid():
                line_count += 1

                # The top left position of the block in the document
                position = self.text_edit.document().documentLayout().blockBoundingRect(block).topLeft()

                # Check if the position of the block is outside the visible area.
                if position.y() > page_bottom:
                    break

                painter.setPen(self.number_color)

                # We want the line number for the selected line to be bold.
                bold = False
                if block == current_block:
                    bold = True
                    font = painter.font()
                    font.setBold(True)
                    painter.setFont(font)
                    painter.setPen(self.number_bold_color)

                # Draw the line number right justified at the y position of the line.
                # 3 is a magic padding number. drawText(x, y, text).
                margins = self.text_edit.contentsMargins()
                text_width = font_metrics.boundingRect(str(line_count)).width()
                painter.drawText(self.width() - text_width - 3,
                                 round(position.y()) - contents_y + font_metrics.ascent() + margins.top(),
                                 str(line_count))

                # Remove the bold style if it was set previously.
                if bold:
                    font = painter.font()
                    font.setBold(False)
                    painter.setFont(font)
                    painter.setPen(self.number_color)

                block = block.next()

            self.highest_line = line_count
            painter.end()

            super().paintEvent(event)

    def __init__(self, *args):
        super().__init__(*args)

        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.setObjectName("LineTextFrame")
        self.edit = QTextEdit()

        self.edit.setFrameStyle(QFrame.NoFrame)
        self.edit.setLineWrapMode(QTextEdit.NoWrap)
        self.edit.setAcceptRichText(False)

        self.number_bar = self.NumberBar()
        self.number_bar.set_text_edit(self.edit)

        horizontal_layout = QHBoxLayout(self)
        horizontal_layout.setSpacing(0)
        horizontal_layout.setContentsMargins(0, 0, 0, 0)
        horizontal_layout.addWidget(self.number_bar)
        horizontal_layout.addWidget(self.edit)

        stylesheet = resource_library.Stylesheet.scroll_bar_dark
        stylesheet += resource_library.Stylesheet.maya_basic_dialog
        stylesheet += resource_library.Stylesheet.list_widget_dark
        self.setStyleSheet(stylesheet)

        frame_color = resource_library.Color.Hex.gray_darker
        border_radius = "5px"
        background_color = resource_library.Color.RGB.gray_darker_mid
        self.edit.setStyleSheet(f"QTextEdit {{ border: 2px solid {frame_color}; "
                                f"border-radius: {border_radius}; "
                                f"color: {resource_library.Color.RGB.white}; "
                                f"background-color: {background_color} }}")
        self.setStyleSheet(f"#LineTextFrame {{ border: 2px solid {frame_color}; "
                           f"border-radius: {border_radius}; background-color: {background_color}; }}")

        self.edit.installEventFilter(self)
        self.edit.viewport().installEventFilter(self)

    def eventFilter(self, obj, event):
        """
        Filter events to update line numbers.
        """
        if obj in (self.edit, self.edit.viewport()):
            self.number_bar.update()
            return False
        return super().eventFilter(obj, event)

    def set_line_number_color(self, color):
        """
        Sets the color of the line numbers.
        Args:
            color (QColor): New color to set the line numbers.
        """
        if not isinstance(color, QColor):
            logger.debug(f'Unable to set line number color. '
                         f'Expected "QColor" object, but received "{str(type(color))}"')
            return
        self.number_bar.number_color = color

    def line_number_bold_color(self, color):
        """
        Sets the color of the line numbers.
        Args:
            color (QColor): New color to set the line numbers.
        """
        if not isinstance(color, QColor):
            logger.debug(f'Unable to set line number bold color. '
                         f'Expected "QColor" object, but received "{str(type(color))}"')
            return
        self.number_bar.number_bold_color = color

    def get_text_edit(self):
        """
        Get the QTextEdit instance associated with this LineTextWidget.
        """
        return self.edit


if __name__ == "__main__":
    class ExampleDialog(QDialog):
        """
        Example dialog containing the LineTextWidget.
        """

        def __init__(self, parent=None):
            super().__init__(parent)

            self.setWindowTitle("Line Text Widget Example")
            self.setGeometry(100, 100, 800, 600)

            stylesheet = resource_library.Stylesheet.scroll_bar_dark
            stylesheet += resource_library.Stylesheet.maya_basic_dialog
            stylesheet += resource_library.Stylesheet.list_widget_dark
            self.setStyleSheet(stylesheet)

            line_text_widget = LineTextWidget(self)
            import inspect
            import sys
            from gt.ui.syntax_highlighter import PythonSyntaxHighlighter
            line_text_widget.get_text_edit().setText(inspect.getsource(sys.modules[__name__]))
            PythonSyntaxHighlighter(line_text_widget.get_text_edit().document())
            layout = QVBoxLayout(self)
            layout.addWidget(line_text_widget)
            self.setLayout(layout)

    from gt.ui import qt_utils
    with qt_utils.QtApplicationContext():
        window = ExampleDialog()
        window.show()
