"""
Sample Tool View

Small GUI used as the package's MVC sample tool.
"""

from gt.ui.qt_utils import MayaWindowMeta
import gt.ui.qt_utils as qt_utils
import gt.ui.qt_import as ui_qt


class SampleToolWindow(metaclass=MayaWindowMeta):
    """Main window for the sample text saver tool."""

    def __init__(self, parent=None, controller=None, version=None):
        """Initializes the SampleToolWindow.

        Args:
            parent (QWidget, optional): Parent for this window.
            controller (SampleToolController, optional): Controller reference kept to avoid garbage collection.
            version (str, optional): Optional version displayed in the title.
        """
        super().__init__(parent=parent)
        self.controller = controller
        self.text_field = None
        self.save_button = None

        window_title = "Sample Tool"
        if version:
            window_title += " - (v{0})".format(str(version))
        self.setWindowTitle(window_title)
        self.setGeometry(100, 100, 300, 150)

        self.text_field = ui_qt.QtWidgets.QLineEdit(self)
        self.text_field.setPlaceholderText("Enter text to save...")

        self.save_button = ui_qt.QtWidgets.QPushButton("Save to File")

        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.addWidget(self.text_field)
        main_layout.addWidget(self.save_button)

        qt_utils.center_window(self)

    def get_text(self):
        """Gets the current text from the text field.

        Returns:
            str: Text entered by the user.
        """
        return self.text_field.text()


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = SampleToolWindow()
        window.show()
