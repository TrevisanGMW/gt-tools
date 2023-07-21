"""
Sample Tool View. (GUI)
The View is responsible for presenting the data to the user in a human-readable format.
It's what the users see and interact with. The View's primary role is to display the information from the Model and
relay the user's actions (such as clicking buttons) back to the Controller.
It should NOT be coupled to the controller. You should be able to run the View independently and all it would do is
send signals.

It should be able to work independently of the view.
One should be able to import it and run the tool without its GUI.
"""
from PySide2.QtWidgets import QVBoxLayout, QListWidget, QPushButton, QWidget, QMainWindow
import gt.ui.resource_library as resource_library
from PySide2 import QtWidgets, QtCore
import gt.ui.qt_utils as qt_utils
from PySide2.QtGui import QIcon
import sys


class SampleToolWindow(QMainWindow):
    def __init__(self, parent=None, controller=None):
        """
        Initialize the SampleToolWindow.
        This window represents the main GUI window of the application.
        It contains a list of items, along with buttons to add and remove items.

        Parameters:
            parent (str): Parent for this window
            controller (SampleToolController): SampleToolController, not to be used, here so it's not deleted by
                                                 the garbage collector.
        """
        super().__init__(parent=parent)

        self.controller = controller  # Only here so it doesn't get deleted by the garbage collectors

        self.setWindowTitle("Sample Tool")
        self.setGeometry(100, 100, 400, 300)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.item_list = QListWidget()

        self.layout.addWidget(self.item_list)

        self.add_button = QPushButton("Add Item")
        self.layout.addWidget(self.add_button)

        self.remove_button = QPushButton("Remove Item")
        self.layout.addWidget(self.remove_button)

        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.WindowMaximizeButtonHint |
                            QtCore.Qt.WindowMinimizeButtonHint)
        self.setWindowIcon(QIcon(resource_library.Icon.cog_icon))

        sample_stylesheet = resource_library.Stylesheet.dark_scroll_bar
        sample_stylesheet += resource_library.Stylesheet.maya_basic_dialog
        sample_stylesheet += resource_library.Stylesheet.dark_list_widget
        self.setStyleSheet(sample_stylesheet)

    def update_view(self, items):
        """
        Updates the view with the provided items.

        Parameters:
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
    window = SampleToolWindow()  # View
    window.show()  # Open Windows
    sys.exit(app.exec_())
