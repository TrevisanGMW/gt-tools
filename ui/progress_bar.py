from PySide2 import QtGui
from PySide2.QtWidgets import QApplication, QMainWindow, QProgressBar, QPushButton, QTextEdit, QVBoxLayout, QWidget
from ui import resource_library, qt_utils
from PySide2.QtGui import QIcon
import sys


class ProgressBarWindow(QMainWindow):
    def __init__(self, parent=None, controller=None, output_text=True):
        super().__init__(parent=parent)
        self.controller = controller  # Only here so it doesn't get deleted by the garbage collectors

        # Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setTextVisible(False)

        # Output Window
        self.output_textbox = QTextEdit(self)
        self.output_textbox.setReadOnly(True)
        self.output_textbox.setFont(qt_utils.get_font(resource_library.Font.roboto))
        self.output_textbox.setFontPointSize(12)

        # Temp Test Button
        self.start_button = QPushButton("OK", self)
        self.start_button.clicked.connect(self.start_progress)

        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.output_textbox)
        layout.addWidget(self.start_button)

        # Central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Window
        _min_width = 500
        _min_height = 400
        self.setGeometry(0, 0, _min_width, _min_height)  # Args X, Y, W, H
        self.setMinimumWidth(300)
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

    def set_progress_value(self, value):
        """
        Sets a progress bar value
        Args:
            value (int): New value to set.
                         e.g. 10 = 10%
        """
        self.progress_bar.setValue(value)

    def increase_progress_value(self, increase_value=1):
        """
        Increases the progress bar value
        Args:
            increase_value (int, optional): Amount to increase the progress bar: Default 1
        """
        new_value = self.progress_bar.value() + increase_value
        self.set_progress_value(new_value)

    def append_text_to_output_box(self, new_text):
        self.output_textbox.append(new_text)

    def clear_output_box(self):
        self.output_textbox.clear()

    def start_progress(self):
        self.set_progress_value(5)
        # self.output_textbox.clear()

        index = 0
        while index < 100:
            # self.progress_bar.setValue(i)
            increase_value = 5
            self.increase_progress_value(increase_value)
            index += increase_value
            # self.append_text_to_output_box(f"Progress: {index}%")
            QApplication.processEvents()  # Updates the GUI and keeps it responsive
            # Simulate some work being done
            # Replace this with your actual work
            import time
            time.sleep(0.1)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # app.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)  # no auto scale
    window = ProgressBarWindow()
    window.append_text_to_output_box("""Initializing Maya Standalone...
Fetching requirements...
Removing previous install...
Copying required files...
Adding entry point to userSetup...
Checking installation integrity...

Installation completed successfully!""")
    window.show()
    sys.exit(app.exec_())
