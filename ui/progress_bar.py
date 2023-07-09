from PySide2.QtWidgets import QApplication, QMainWindow, QProgressBar, QPushButton, QTextEdit
from PySide2.QtGui import QIcon
from ui import resource_library
from ui import qt_utils
import sys


class ProgressBarWindow(QMainWindow):
    def __init__(self, parent=None, controller=None, output_window=True):
        super().__init__(parent=parent)
        self.controller = controller  # Only here so it doesn't get deleted by the garbage collectors

        # Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(50, 50, 400, 50)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid gray;
                border-radius: 5px;
                border-style: solid;
                text-align: center;
                background-color: #f0f0f0;
                background-color: #808080

            }
            QProgressBar::chunk {
                background-color: #6AA2BB;
                width: 5;
                margin 22;
                border-radius: 5px;
            }
        """)

        # Output Window
        self.output_textbox = QTextEdit(self)
        self.output_textbox.setGeometry(50, 120, 400, 200)

        # Temp Test Button
        self.start_button = QPushButton("Start", self)
        self.start_button.setGeometry(50, 340, 75, 25)
        self.start_button.clicked.connect(self.start_progress)

        # Window
        _min_width = 500
        _min_height = 400
        self.setGeometry(0, 0, _min_width, _min_height)  # Args X, Y, W, H
        self.setMinimumWidth(_min_width)
        self.setMinimumHeight(_min_height)
        # Window Adjust
        self.adjustSize()
        self.setMinimumWidth(self.width())
        self.setMinimumHeight(self.height())
        self.center()
        # Window Details
        self.setWindowTitle("Progress Bar Example")
        self.setStyleSheet(resource_library.Stylesheet.maya_basic_dialog)
        self.setWindowIcon(QIcon(resource_library.Icon.package_icon))

    def center(self):
        """ Move window to the center of the screen """
        rect = self.frameGeometry()
        center_position = qt_utils.get_screen_center()
        rect.moveCenter(center_position)
        self.move(rect.topLeft())

    def set_progress_value(self, value):
        self.progress_bar.setValue(value)

    def increase_progress_value(self, increase_value=1):
        new_value = self.progress_bar.value() + increase_value
        self.progress_bar.setValue(new_value)

    def start_progress(self):
        self.set_progress_value(5)
        self.output_textbox.clear()

        for i in range(1, 101):
            # self.progress_bar.setValue(i)
            self.increase_progress_value()
            self.output_textbox.append(f"Progress: {i}%")
            QApplication.processEvents()  # Updates the GUI and keeps it responsive
            # Simulate some work being done
            # Replace this with your actual work
            import time
            time.sleep(0.1)

        # self.progress_bar.setValue(0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # app.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)  # no auto scale
    window = ProgressBarWindow()
    window.show()
    sys.exit(app.exec_())
