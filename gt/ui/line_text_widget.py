import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_utils as ui_qt_utils
import gt.ui.qt_import as ui_qt
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def apply_text_font_size(text_edit, font_size):
    """Applies a font size to all existing text without changing selection.

    Args:
        text_edit (QTextEdit): Editor whose document text should be resized.
        font_size (int): Font size in points.
    """
    if not text_edit:
        return
    original_cursor = text_edit.textCursor()
    signals_blocked = text_edit.blockSignals(True)
    try:
        document_cursor = ui_qt.QtGui.QTextCursor(text_edit.document())
        if ui_qt.IS_PYSIDE6:
            document_selection = ui_qt.QtGui.QTextCursor.SelectionType.Document
        else:
            document_selection = ui_qt.QtGui.QTextCursor.Document
        document_cursor.select(document_selection)
        text_format = ui_qt.QtGui.QTextCharFormat()
        text_format.setFontPointSize(int(font_size or 14))
        document_cursor.mergeCharFormat(text_format)
    finally:
        text_edit.setTextCursor(original_cursor)
        text_edit.blockSignals(signals_blocked)


class LineTextWidget(ui_qt.QtWidgets.QFrame):
    """
    A custom widget for displaying line numbers alongside a QTextEdit.
    """

    class NumberBar(ui_qt.QtWidgets.QWidget):
        """
        Widget for displaying line numbers.
        """

        def __init__(self, *args):
            """
            Initializes the NumberBar widget.

            Sets default colors, font, and initial state for line numbering.

            Args:
                *args: Variable length argument list to pass to QWidget initializer.
            """
            super().__init__(*args)
            self.text_edit = None
            self.highest_line = 0  # This is used to update the width of the control.
            self.number_color = ui_qt.QtGui.QColor(ui_res_lib.Color.Hex.gray_lighter)
            self.number_bold_color = ui_qt.QtGui.QColor(ui_res_lib.Color.Hex.gray_lighter)
            self.bar_width_offset = 5

            # Set a font
            font = ui_qt.QtGui.QFont(ui_qt_utils.load_custom_font(ui_res_lib.Font.roboto))
            font.setPointSizeF(10)  # Adjust the desired font size
            self.setFont(font)

        def set_text_edit(self, edit):
            """
            Associates a QTextEdit widget with this NumberBar.

            This allows the NumberBar to track and display line numbers
            corresponding to the provided QTextEdit instance.

            Args:
                edit (QTextEdit): The QTextEdit widget to associate.
            """
            self.text_edit = edit

        def get_required_width(self):
            """Gets a stable gutter width for every line number in the document.

            Returns:
                int: Required line-number gutter width in pixels.
            """
            line_count = 1
            if self.text_edit and self.text_edit.document():
                line_count = max(1, self.text_edit.document().blockCount())
            widest_number = "9" * len(str(line_count))
            bold_font = ui_qt.QtGui.QFont(self.font())
            bold_font.setBold(True)
            font_metrics = ui_qt.QtGui.QFontMetrics(bold_font)
            return font_metrics.horizontalAdvance(widest_number) + self.bar_width_offset

        def update(self, *args):
            """
            Updates the number bar to display the current set of numbers.
            Also, adjusts the width of the number bar if necessary.
            """
            width = self.get_required_width()
            if self.width() != width:
                self.setFixedWidth(width)
            super().update(*args)

        def paintEvent(self, event):
            """
            Paints the line numbers next to the associated text edit widget.

            This method draws the line numbers for each visible text block in the
            document, highlighting the line number of the current cursor position in bold.
            It takes into account the scrolling offset and viewport height to only
            paint visible lines, optimizing performance.

            Args:
                event (QPaintEvent): The paint event triggering this repaint.
            """
            contents_y = self.text_edit.verticalScrollBar().value()
            page_bottom = contents_y + self.text_edit.viewport().height()
            font_metrics = self.fontMetrics()
            current_block = self.text_edit.document().findBlock(self.text_edit.textCursor().position())

            painter = ui_qt.QtGui.QPainter(self)

            line_count = 0
            # Iterate over all text blocks in the document.
            block = self.text_edit.document().begin()
            while block.isValid():
                line_count += 1

                block_rect = self.text_edit.document().documentLayout().blockBoundingRect(block)
                position = block_rect.topLeft()

                # Check if the position of the block is outside the visible area.
                if position.y() > page_bottom:
                    break
                if block_rect.bottom() < contents_y:
                    block = block.next()
                    continue

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
                # text_width = font_metrics.boundingRect(str(line_count)).width()
                # Calculate the text width using logical pixel units
                text_width = font_metrics.horizontalAdvance(str(line_count))
                painter.drawText(
                    self.width() - text_width - 3,
                    round(position.y()) - contents_y + font_metrics.ascent() + margins.top(),
                    str(line_count),
                )

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

    def __init__(self, parent=None, text_edit=None):
        """
        Initialize the widget containing a QTextEdit with a line number bar.

        Sets up the QTextEdit with no frame and no line wrapping, applies custom
        font and styles, creates a NumberBar for line numbering, and arranges
        them side by side in a horizontal layout. Also installs event filters on
        the text edit and its viewport to update the line numbers as needed.

        Args:
            parent (QWidget, optional): Parent widget.
            text_edit (QTextEdit, optional): Text editor displayed beside the line number bar.
        """
        super().__init__(parent=parent)

        self.setFrameStyle(ui_qt.QtLib.FrameStyle.StyledPanel | ui_qt.QtLib.FrameStyle.Sunken)
        self.setObjectName("LineTextFrame")
        self.edit = text_edit if text_edit is not None else ui_qt.QtWidgets.QTextEdit()

        self.edit.setFrameStyle(ui_qt.QtLib.FrameStyle.NoFrame)
        self.edit.setLineWrapMode(ui_qt.QtLib.LineWrapMode.NoWrap)
        self.edit.setAcceptRichText(False)
        font = ui_qt.QtGui.QFont(ui_qt_utils.load_custom_font(ui_res_lib.Font.roboto))
        font.setPointSizeF(10)
        self.edit.setFont(font)

        self.number_bar = self.NumberBar()
        self.number_bar.set_text_edit(self.edit)

        horizontal_layout = ui_qt.QtWidgets.QHBoxLayout(self)
        horizontal_layout.setSpacing(0)
        horizontal_layout.setContentsMargins(0, 0, 0, 0)
        horizontal_layout.addWidget(self.number_bar)
        horizontal_layout.addWidget(self.edit)

        stylesheet = ui_res_lib.Stylesheet.scroll_bar_base
        stylesheet += ui_res_lib.Stylesheet.maya_dialog_base
        stylesheet += ui_res_lib.Stylesheet.list_widget_base
        self.setStyleSheet(stylesheet)

        frame_color = ui_res_lib.Color.Hex.gray_darker
        border_radius = "5px"
        self.edit.setStyleSheet(
            f"QTextEdit {{ "
            f"border: 0px solid {frame_color}; "
            f"border-radius: {border_radius}; "
            f"color: {ui_res_lib.Color.RGB.white}; "
            f"background-color: {ui_res_lib.Color.RGB.gray_darker_mid} }}"
        )
        self.setStyleSheet(
            f"#LineTextFrame {{ "
            f"border: 2px solid {frame_color}; "
            f"border-radius: {border_radius}; "
            f"background-color: {ui_res_lib.Color.RGB.gray_darker}; }}"
        )

        self.edit.installEventFilter(self)
        self.edit.viewport().installEventFilter(self)

    def eventFilter(self, obj, event):
        """
        Filters events to update the line numbers when the associated text edit
        or its viewport receives an event.

        Args:
            obj (QObject): The object that received the event.
            event (QEvent): The event to be filtered.

        Returns:
            bool: False to allow normal event processing to continue, True to
            stop further processing.
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
        if not isinstance(color, ui_qt.QtGui.QColor):
            logger.debug(
                f"Unable to set line number color. " f'Expected "QColor" object, but received "{str(type(color))}"'
            )
            return
        self.number_bar.number_color = color

    def line_number_bold_color(self, color):
        """
        Sets the color of the line numbers.
        Args:
            color (QColor): New color to set the line numbers.
        """
        if not isinstance(color, ui_qt.QtGui.QColor):
            logger.debug(
                f"Unable to set line number bold color. " f'Expected "QColor" object, but received "{str(type(color))}"'
            )
            return
        self.number_bar.number_bold_color = color

    def get_text_edit(self):
        """
        Get the QTextEdit instance associated with this LineTextWidget.
        """
        return self.edit


if __name__ == "__main__":

    class ExampleDialog(ui_qt.QtWidgets.QDialog):
        """
        Example dialog containing the LineTextWidget.
        """

        def __init__(self, parent=None):
            super().__init__(parent)

            self.setWindowTitle("Line Text Widget Example")
            self.setGeometry(100, 100, 800, 600)

            stylesheet = ui_res_lib.Stylesheet.scroll_bar_base
            stylesheet += ui_res_lib.Stylesheet.maya_dialog_base
            stylesheet += ui_res_lib.Stylesheet.list_widget_base
            self.setStyleSheet(stylesheet)

            line_text_widget = LineTextWidget(self)
            import inspect
            import sys
            from gt.ui.syntax_highlighter import PythonSyntaxHighlighter

            line_text_widget.get_text_edit().setText(inspect.getsource(sys.modules[__name__]))
            PythonSyntaxHighlighter(line_text_widget.get_text_edit().document())
            layout = ui_qt.QtWidgets.QVBoxLayout(self)
            layout.addWidget(line_text_widget)
            self.setLayout(layout)

    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext():
        window = ExampleDialog()
        window.show()
