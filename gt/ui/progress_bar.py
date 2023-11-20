from PySide2.QtWidgets import QMainWindow, QProgressBar, QPushButton, QTextEdit, QVBoxLayout, QWidget, QHBoxLayout
from PySide2.QtGui import QIcon, QTextCursor, QTextCharFormat, QColor, QTextDocument
from gt.ui import resource_library, qt_utils
from PySide2 import QtCore, QtWidgets
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


MIN_HEIGHT = 100
MIN_HEIGHT_OUTPUT_TEXT = 400


class ProgressBarWindow(QMainWindow):
    CloseParentView = QtCore.Signal()

    def __init__(self, parent=None, output_text=True, has_second_button=False):
        super().__init__(parent=parent)

        # Basic Variables
        _min_width = 500
        _min_height = MIN_HEIGHT
        self.output_text_font = qt_utils.get_font(resource_library.Font.roboto)
        self.output_text_size = 12

        # Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setTextVisible(False)

        # Output Window
        self.output_textbox = QTextEdit(self)
        self.output_textbox.setReadOnly(True)
        self.output_textbox.setFont(self.output_text_font)
        self.output_textbox.setFontPointSize(self.output_text_size)

        # Buttons
        self.first_button = QPushButton("OK", self)
        self.second_button = None  # Created later

        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(self.progress_bar)
        if output_text:
            layout.addWidget(self.output_textbox)
            _min_height = MIN_HEIGHT_OUTPUT_TEXT
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.first_button)
        if has_second_button:
            self.second_button = QPushButton("Cancel", self)  # Second Button
            buttons_layout.addWidget(self.second_button)
        layout.addLayout(buttons_layout)

        # Central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Window
        self.setGeometry(0, 0, _min_width, _min_height)  # Args X, Y, W, H
        self.setMinimumWidth(_min_width*.8)  # 80% of the maximum width
        qt_utils.resize_to_screen(window=self, height_percentage=20, width_percentage=25,
                                  dpi_scale=True, dpi_percentage=20)
        qt_utils.center_window(self)
        # Window Details
        self.setWindowTitle("Progress Bar")
        progress_bar_stylesheet = resource_library.Stylesheet.maya_dialog_base
        progress_bar_stylesheet += resource_library.Stylesheet.progress_bar_base
        progress_bar_stylesheet += resource_library.Stylesheet.scroll_bar_base
        progress_bar_stylesheet += resource_library.Stylesheet.text_edit_base
        self.setStyleSheet(progress_bar_stylesheet)
        self.set_window_icon(resource_library.Icon.package_icon)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)  # Stay On Top Modality

    def set_window_icon(self, icon_path):
        """
        Sets a new icon for the progress bar window
        Args:
            icon_path (str): Path to an image to be used as an icon.
        """
        self.setWindowIcon(QIcon(icon_path))

    def set_progress_bar_name(self, name):
        """
        Sets the name of the progress bar.
        Args:
            name (str): The name to be set for the progress bar.
        """
        self.setWindowTitle(str(name))

    def set_progress_bar_value(self, value):
        """
        Sets a progress bar value
        Args:
            value (int): New value to set.
                         e.g. 10 = 10%
        """
        self.progress_bar.setValue(value)

    def set_progress_bar_max_value(self, value):
        """
        Sets a progress bar value
        Args:
            value (int): New value to set.
                         e.g. 10 = 10%
        """
        self.progress_bar.setMaximum(value)

    def set_progress_bar_done(self):
        """
        Sets a progress bar value to max (complete status)
        """
        self.progress_bar.setValue(self.progress_bar.maximum())

    def increase_progress_bar_value(self, *args, increase_value=1):
        """
        Increases the progress bar value
        Args:
            increase_value (int, optional): Amount to increase the progress bar: Default 1
        """
        logger.debug(f"Args: {args}")
        new_value = self.progress_bar.value() + increase_value
        self.set_progress_bar_value(new_value)

    def get_output_box_plain_text(self):
        """
        Returns the content found in the "output_textbox" QTextEdit object as a string.
        Returns:
            str: Content found in the "output_textbox" QTextEdit object. If not available, it returns "" (empty string)
        """
        if not self.output_textbox:
            return ""
        return self.output_textbox.toPlainText()

    def add_text_to_output_box(self, input_string, color=None, as_new_line=True):
        """
        Appends new_text to the output_textbox.
        Args:
           input_string (str): The text to be appended to the output_textbox.
           color (QColor, str): QColor or Hex color used to determine the color of the input text.
                                e.g. "#FF0000" or QColor("#FF0000")
           as_new_line (bool, optional): If true, added text is appended as a new line. (e.g. "\n" + append_string)
                                         If false it's appended in the same line (e.g. append_string)
        """
        # Create a text char format with the specified color
        text_format = QTextCharFormat()
        text_format.setFont(self.output_text_font)
        text_format.setFontPointSize(self.output_text_size)

        # Determine if color is being set
        if color:
            text_format.setForeground(qt_utils.get_qt_color(color))

        # Move the cursor to the end of the text edit
        cursor = self.output_textbox.textCursor()
        cursor.movePosition(cursor.End)

        # Apply the text char format to the newly appended text
        cursor.setCharFormat(text_format)

        # Check if the text edit is empty
        is_empty = self.output_textbox.toPlainText() == ''

        # Append a newline character and the text to the text edit
        new_line_symbol = ''
        if as_new_line:
            new_line_symbol = '\n'
        cursor.insertText(new_line_symbol + str(input_string) if not is_empty else str(input_string))

        # Scroll the text edit to the end
        self.output_textbox.ensureCursorVisible()

        # self.output_textbox.append(str(append_string))
        QtWidgets.QApplication.processEvents()  # Updates the GUI and keeps it responsive

    def clear_output_box(self):
        """ Clears the output_textbox """
        self.output_textbox.clear()

    def change_line_color(self, line_number, color):
        """
        Changes the color of a specific line in the text document.
        Args:
           line_number (int): The line number (1-indexed) of the line to be changed.
           color (QColor, str): QColor or Hex color used to determine the color of the used text.
                                e.g. "#FF0000" or QColor("#FF0000")
        """
        cursor = self.output_textbox.textCursor()
        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, line_number - 1)
        cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        format_line = QTextCharFormat()
        format_line.setForeground(qt_utils.get_qt_color(color))
        format_line.setFont(self.output_text_font)
        format_line.setFontPointSize(self.output_text_size)
        cursor.setCharFormat(format_line)

    def edit_text_color_of_first_match(self, color, target_text, start_from_bottom=False):
        """
        Edits the text color of the first occurrence of the target text in the output textbox.

        Args:
            color (QColor, str): The color to set for the matched text. (e.g. "#FF0000" = Red)
                                 This should be a valid color name or hex code or a QColor object.
            target_text (str): The text to search for in the output textbox.
            start_from_bottom (bool, optional): If True, the search starts from the bottom of the output textbox.
                Defaults to False, meaning the search starts from the top.

        Returns:
            bool: True if text was found.
        """
        cursor = QTextCursor(self.output_textbox.document())
        format_line = QTextCharFormat()
        format_line.setForeground(qt_utils.get_qt_color(color))
        format_line.setFont(self.output_text_font)
        format_line.setFontPointSize(self.output_text_size)

        if start_from_bottom:
            cursor.movePosition(QTextCursor.End)
            while not cursor.isNull() and not cursor.atStart():
                cursor = self.output_textbox.document().find(target_text, cursor, QTextDocument.FindBackward)
                if not cursor.isNull():
                    cursor.mergeCharFormat(format_line)
                    return True
        else:
            while not cursor.isNull() and not cursor.atEnd():
                cursor = self.output_textbox.document().find(target_text, cursor)
                if not cursor.isNull():
                    cursor.mergeCharFormat(format_line)
                    return True

    def change_last_line_color(self, color):
        """
        Changes the color of a specific line in the text document.
        Args:
           color (QColor, str): QColor or Hex color used to determine the color of the text.
                                e.g. "#FF0000" or QColor("#FF0000")
        """
        last_line = self.get_latest_raw_line()
        self.edit_text_color_of_first_match(color=color, target_text=last_line, start_from_bottom=True)

    def get_latest_raw_line(self):
        raw_text = self.output_textbox.toPlainText()
        lines = raw_text.split('\n')
        if lines:
            return lines[-1]

    def set_line_color(self, line, color):
        cursor = self.output_textbox.textCursor()
        cursor.movePosition(QTextCursor.Start)
        while cursor.movePosition(QTextCursor.NextBlock):
            if cursor.block().text() == line:
                format_line = QTextCharFormat()
                format_line.setForeground(qt_utils.get_qt_color(color))
                cursor.mergeCharFormat(format_line)
                break

    def close_window(self):
        """ Closes this window """
        self.close()

    def close_parent_window(self):
        """ Emits Signal to close parent window """
        self.CloseView.emit()


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    # app.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)  # no auto scale
    window = ProgressBarWindow()
    window.show()

    window.set_progress_bar_name("Installing Script Package...")
    # Create connections
    window.first_button.clicked.connect(window.close_window)

    window.set_progress_bar_max_value(8)
    # window.set_progress_bar_done()
    # import utils.setup_utils as setup_utils
    # setup_utils.install_package(passthrough_functions=[window.append_text_to_output_box,
    #                                                    window.increase_progress_bar_value])

    index = 0
    import time
    while index < 7:
        increase_val = 1
        window.increase_progress_bar_value(increase_val)
        window.add_text_to_output_box(str(index), color="#00FF00")
        index += increase_val
        # self.append_text_to_output_box(f"Progress: {index}%")
        time.sleep(0.1)
    window.change_line_color(2, QColor("red"))  # Change color of line 2 to red
    window.change_last_line_color("#0000FF")
    out = window.get_output_box_plain_text()
    print(out)
    sys.exit(app.exec_())
