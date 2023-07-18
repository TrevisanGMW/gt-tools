"""
Sample Tool View. (GUI)
The View is responsible for presenting the data to the user in a human-readable format.
It's what the users see and interact with. The View's primary role is to display the information from the Model and
relay the user's actions (such as clicking buttons) back to the Controller.
It should NOT be coupled to the controller. You should be able to run the View independently and all it would do is
send signals.
"""
import gt.ui.resource_library as resource_library
from PySide2 import QtWidgets, QtCore
import gt.ui.qt_utils as qt_utils
from PySide2.QtGui import QIcon
import sys


class SampleToolWindow(QtWidgets.QDialog):
    ButtonSetClicked = QtCore.Signal()
    ButtonGetClicked = QtCore.Signal()
    ButtonWriteToDesktopClicked = QtCore.Signal()

    def __init__(self, parent=None, controller=None):
        """
        Initializes the Sample Tool Window.
        Args:
            parent (QWidget, optional): The parent widget. Default is None.
            controller (object, optional): The controller object used to manage the tool's behavior.
                                           Only here so it doesn't get deleted by the garbage collector.
        """
        super().__init__(parent=parent)
        self.controller = controller  # Only here so it doesn't get deleted by the garbage collector.
        # Data Output
        self.label_output = QtWidgets.QLabel("Stored Data:")
        self.stored_data = QtWidgets.QLabel("")
        # Data Input
        self.label_input = QtWidgets.QLabel("Input:")
        self.text_input_output = QtWidgets.QLineEdit()
        # Buttons
        self.set_data_btn = QtWidgets.QPushButton('Set Data')
        self.get_data_btn = QtWidgets.QPushButton('Get Data')
        self.write_to_desktop_btn = QtWidgets.QPushButton('Write Stored Data to Desktop')
        self.close_btn = QtWidgets.QPushButton('Cancel')
        # Layout

        # Misc
        _min_width = 400
        _min_height = 100
        self.setGeometry(0, 0, _min_width, _min_height)  # Args X, Y, W, H
        self.setWindowTitle("Sample Tool Window")
        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.WindowMaximizeButtonHint |
                            QtCore.Qt.WindowMinimizeButtonHint)
        self.setStyleSheet(resource_library.Stylesheet.maya_basic_dialog)
        self.setWindowIcon(QIcon(resource_library.Icon.cog_icon))

        self.create_layout()
        self.create_connections()
        self.center()

    def create_layout(self):
        """ Creates layout """
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label_output)
        layout.addWidget(self.stored_data)
        layout.addWidget(self.label_input)
        layout.addWidget(self.text_input_output)
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addWidget(self.set_data_btn)
        buttons_layout.addWidget(self.get_data_btn)
        buttons_layout.addWidget(self.write_to_desktop_btn)
        buttons_layout.addWidget(self.close_btn)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def center(self):
        """ Moves window to the center of the screen """
        rect = self.frameGeometry()
        center_position = qt_utils.get_screen_center()
        rect.moveCenter(center_position)
        self.move(rect.topLeft())

    def create_connections(self):
        """ Create Connections between buttons and functions that calls signals """
        self.set_data_btn.clicked.connect(self.button_set_clicked)
        self.get_data_btn.clicked.connect(self.button_get_clicked)
        self.write_to_desktop_btn.clicked.connect(self.button_write_desktop_clicked)
        self.close_btn.clicked.connect(self.close_window)

    def close_window(self):
        """ Closes this window """
        self.close()

    def button_set_clicked(self):
        """ Emits ButtonSetClicked signal """
        self.ButtonSetClicked.emit()

    def button_get_clicked(self):
        """ Emits ButtonGetClicked signal """
        self.ButtonGetClicked.emit()

    def button_write_desktop_clicked(self):
        """ Emits ButtonWriteToDesktopClicked signal """
        self.ButtonWriteToDesktopClicked.emit()

    def update_content_text_field(self, new_text):
        """
        Updates the content of the text input field with the specified new text.
        Args:
            new_text (str): The new text to be set in the text input field.
        """
        self.text_input_output.setText(new_text)

    def update_data_text(self, new_stored_data):
        """
        Updates the displayed stored data with the specified new data.
        Args:
            new_stored_data (str): The new data to be displayed in the stored_data field.
        """
        self.stored_data.setText(new_stored_data)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)  # Application - To launch without Maya
    window = SampleToolWindow()  # View
    window.show() # Open Windows
    sys.exit(app.exec_())
