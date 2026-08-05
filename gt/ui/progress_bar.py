import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_utils as ui_qt_utils
import gt.ui.qt_import as ui_qt
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


MIN_HEIGHT = 100
MIN_HEIGHT_OUTPUT_TEXT = 400


class ProgressBarWindow(ui_qt.QtWidgets.QMainWindow):
    CloseParentView = ui_qt.QtCore.Signal()

    def __init__(self, parent=None, output_text=True, has_second_button=False, on_top=True):
        """
        Initializes the progress bar window with optional output text area and buttons.

        Sets up a window containing a progress bar, an optional read-only text output,
        and one or two buttons ("OK" and optionally "Cancel"). Configures window
        size, layout, styles, and modality.

        Args:
            parent (QWidget, optional): The parent widget for this window. Defaults to None.
            output_text (bool, optional): Whether to include a read-only text output box. Defaults to True.
            has_second_button (bool, optional): Whether to include a second button labeled "Cancel". Defaults to False.
            on_top (bool, optional): Whether the window should stay on top of others. Defaults to True.
        """
        super().__init__(parent=parent)

        # Basic Variables
        _min_width = 500
        _min_height = MIN_HEIGHT
        self.output_text_font = ui_qt_utils.get_font(ui_res_lib.Font.roboto)
        self.output_text_size = 12

        # Progress Bar
        self.progress_bar = ui_qt.QtWidgets.QProgressBar(self)
        self.progress_bar.setTextVisible(False)

        # Output Window
        self.output_textbox = ui_qt.QtWidgets.QTextEdit(self)
        self.output_textbox.setReadOnly(True)
        self.output_textbox.setFont(self.output_text_font)
        self.output_textbox.setFontPointSize(self.output_text_size)

        # Buttons
        self.first_button = ui_qt.QtWidgets.QPushButton("OK", self)
        self.second_button = None  # Created later

        # Main layout
        layout = ui_qt.QtWidgets.QVBoxLayout()
        layout.addWidget(self.progress_bar)
        if output_text:
            layout.addWidget(self.output_textbox)
            _min_height = MIN_HEIGHT_OUTPUT_TEXT
        buttons_layout = ui_qt.QtWidgets.QHBoxLayout()
        buttons_layout.addWidget(self.first_button)
        if has_second_button:
            self.second_button = ui_qt.QtWidgets.QPushButton("Cancel", self)  # Second Button
            buttons_layout.addWidget(self.second_button)
        layout.addLayout(buttons_layout)

        # Central widget
        central_widget = ui_qt.QtWidgets.QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Window
        self.setGeometry(0, 0, _min_width, _min_height)  # Args X, Y, W, H
        self.setMinimumWidth(_min_width * 0.8)  # 80% of the maximum width
        ui_qt_utils.resize_to_screen(
            window=self, height_percentage=20, width_percentage=25, dpi_scale=True, dpi_percentage=20
        )
        ui_qt_utils.center_window(self)
        # Window Details
        self.setWindowTitle("Progress Bar")
        progress_bar_stylesheet = ui_res_lib.Stylesheet.maya_dialog_base
        progress_bar_stylesheet += ui_res_lib.Stylesheet.progress_bar_base
        progress_bar_stylesheet += ui_res_lib.Stylesheet.scroll_bar_base
        progress_bar_stylesheet += ui_res_lib.Stylesheet.text_edit_base
        self.setStyleSheet(progress_bar_stylesheet)
        self.set_window_icon(ui_res_lib.Icon.ui_progress)

        if on_top:
            self.setWindowFlags(ui_qt.QtLib.WindowFlag.WindowStaysOnTopHint)  # Stay On Top Modality

    def set_window_icon(self, icon_path):
        """
        Sets a new icon for the progress bar window
        Args:
            icon_path (str): Path to an image to be used as an icon.
        """
        self.setWindowIcon(ui_qt.QtGui.QIcon(icon_path))

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
        text_format = ui_qt.QtGui.QTextCharFormat()
        text_format.setFont(self.output_text_font)
        text_format.setFontPointSize(self.output_text_size)

        # Determine if color is being set
        if color:
            text_format.setForeground(ui_qt_utils.get_qt_color(color))

        # Move the cursor to the end of the text edit
        cursor = self.output_textbox.textCursor()
        cursor.movePosition(ui_qt.QtLib.TextCursor.End)

        # Apply the text char format to the newly appended text
        cursor.setCharFormat(text_format)

        # Check if the text edit is empty
        is_empty = self.output_textbox.toPlainText() == ""

        # Append a newline character and the text to the text edit
        new_line_symbol = ""
        if as_new_line:
            new_line_symbol = "\n"
        cursor.insertText(new_line_symbol + str(input_string) if not is_empty else str(input_string))

        # Scroll the text edit to the end
        self.output_textbox.ensureCursorVisible()

        # self.output_textbox.append(str(append_string))
        ui_qt.QtWidgets.QApplication.processEvents()  # Updates the GUI and keeps it responsive

    def clear_output_box(self):
        """Clears the output_textbox"""
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
        cursor.movePosition(ui_qt.QtLib.TextCursor.Start)
        cursor.movePosition(ui_qt.QtLib.TextCursor.Down, ui_qt.QtLib.TextCursor.MoveAnchor, line_number - 1)
        cursor.movePosition(ui_qt.QtLib.TextCursor.StartOfLine, ui_qt.QtLib.TextCursor.MoveAnchor)
        cursor.movePosition(ui_qt.QtLib.TextCursor.EndOfLine, ui_qt.QtLib.TextCursor.KeepAnchor)
        format_line = ui_qt.QtGui.QTextCharFormat()
        format_line.setForeground(ui_qt_utils.get_qt_color(color))
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
        cursor = ui_qt.QtGui.QTextCursor(self.output_textbox.document())
        format_line = ui_qt.QtGui.QTextCharFormat()
        format_line.setForeground(ui_qt_utils.get_qt_color(color))
        format_line.setFont(self.output_text_font)
        format_line.setFontPointSize(self.output_text_size)

        if start_from_bottom:
            cursor.movePosition(ui_qt.QtLib.TextCursor.End)
            while not cursor.isNull() and not cursor.atStart():
                cursor = self.output_textbox.document().find(target_text, cursor, ui_qt.QtLib.TextDocument.FindBackward)
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
        """
        Retrieves the last line of text from the output textbox.

        Returns:
            str or None: The last line of text if any lines exist; otherwise, None.
        """
        raw_text = self.output_textbox.toPlainText()
        lines = raw_text.split("\n")
        if lines:
            return lines[-1]

    def set_line_color(self, line, color):
        """
        Sets the text color of a specific line in the output textbox.

        Searches the textbox for a line matching the given text and applies the
        specified color to it.

        Args:
            line (str): The exact text of the line to color.
            color (str or QColor): The color to apply to the line text.
        """
        cursor = self.output_textbox.textCursor()
        cursor.movePosition(ui_qt.QtLib.TextCursor.Start)
        while cursor.movePosition(ui_qt.QtLib.TextCursor.NextBlock):
            if cursor.block().text() == line:
                format_line = ui_qt.QtGui.QTextCharFormat()
                format_line.setForeground(ui_qt_utils.get_qt_color(color))
                cursor.mergeCharFormat(format_line)
                break

    def close_window(self):
        """Closes this window"""
        self.close()

    def close_parent_window(self):
        """Emits Signal to close parent window"""
        self.CloseView.emit()


if __name__ == "__main__":
    import sys

    app = ui_qt.QtWidgets.QApplication(sys.argv)
    # app.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)  # no auto scale
    window = ProgressBarWindow()
    window.show()

    window.set_progress_bar_name("Installing Script Package...")
    # Create connections
    window.first_button.clicked.connect(window.close_window)

    window.set_progress_bar_max_value(8)
    # window.set_progress_bar_done()
    # import core.setup_utils as setup_utils
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
    window.change_line_color(2, ui_qt.QtGui.QColor("red"))  # Change color of line 2 to red
    window.change_last_line_color("#0000FF")
    out = window.get_output_box_plain_text()
    print(out)
    sys.exit(app.exec_())
