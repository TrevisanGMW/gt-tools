from PySide2.QtWidgets import QMainWindow, QProgressBar, QPushButton, QTextEdit, QVBoxLayout, QWidget, QHBoxLayout
from ui import resource_library, qt_utils
from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QIcon
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

        # Size Variables
        _min_width = 500
        _min_height = MIN_HEIGHT

        # Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setTextVisible(False)

        # Output Window
        self.output_textbox = QTextEdit(self)
        self.output_textbox.setReadOnly(True)
        self.output_textbox.setFont(qt_utils.get_font(resource_library.Font.roboto))
        self.output_textbox.setFontPointSize(12)

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
        self.center()
        # Window Details
        self.setWindowTitle("Progress Bar")
        self.setStyleSheet(resource_library.Stylesheet.maya_progress_bar)
        self.setWindowIcon(QIcon(resource_library.Icon.package_icon))

    def center(self):
        """ Moves window to the center of the screen """
        rect = self.frameGeometry()
        center_position = qt_utils.get_screen_center()
        rect.moveCenter(center_position)
        self.move(rect.topLeft())

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

    def append_text_to_output_box(self, new_text):
        """
        Appends new_text to the output_textbox.
        Args:
           new_text (str): The text to be appended to the output_textbox.
        """
        self.output_textbox.append(str(new_text))
        QtWidgets.QApplication.processEvents()  # Updates the GUI and keeps it responsive

    def clear_output_box(self):
        """ Clears the output_textbox """
        self.output_textbox.clear()

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
    window.set_progress_bar_done()
    # import utils.setup_utils as setup_utils
    # setup_utils.install_package(passthrough_functions=[window.append_text_to_output_box,
    #                                                    window.increase_progress_bar_value])

    index = 0
    import time
    while index < 7:
        increase_value = 1
        window.increase_progress_bar_value(increase_value)
        window.append_text_to_output_box(str(index))
        index += increase_value
        # self.append_text_to_output_box(f"Progress: {index}%")
        time.sleep(0.5)

    sys.exit(app.exec_())

