"""
Python Output Window

Import Line:
    import gt.ui.python_output_view as ui_py_output
"""

from gt.ui.syntax_highlighter import PythonSyntaxHighlighter
from gt.ui.line_text_widget import LineTextWidget
from gt.ui.qt_utils import MayaWindowMeta
import gt.ui.qt_utils as ui_qt_utils
import gt.ui.qt_import as ui_qt
from gt.ui import resource_library
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class PythonOutputView(metaclass=MayaWindowMeta):
    def __init__(self, parent=None, editable=False, button_label=None, button_function=None):
        """
        Initialize the AttributesToPythonView.
        This window represents the main GUI window of the tool.

        Args:
            parent (str, optional): Parent for this window. Defaults to None.
            editable (bool, optional): If True, the text area is editable. Defaults to False.
            button_label (str, optional): The text label for a button at the bottom of the window.
                                          Requires `button_function` to be set. Defaults to None.
            button_function (callable, optional): A function to execute when the button is clicked.
                                                  The return value of this function will update the text area.
                                                  Defaults to None.
        """
        super().__init__(parent=parent)

        # Window Title
        self.window_title = "Python Output"
        self.setWindowTitle(self.window_title)

        # Store button function and initial state
        self.button_function = button_function
        self.button_label = button_label
        self.is_initially_editable = editable

        # Widgets
        self.output_python_box = None
        self.action_button = None

        self.create_widgets()
        self.create_layout()

        self.setWindowFlags(
            self.windowFlags() | ui_qt.QtLib.WindowFlag.WindowMaximizeButtonHint | ui_qt.QtLib.WindowFlag.WindowMinimizeButtonHint
        )
        self.setWindowIcon(ui_qt.QtGui.QIcon(resource_library.Icon.dev_code))

        stylesheet = resource_library.Stylesheet.scroll_bar_base
        stylesheet += resource_library.Stylesheet.maya_dialog_base
        stylesheet += resource_library.Stylesheet.list_widget_base
        self.setStyleSheet(stylesheet)
        ui_qt_utils.resize_to_screen(self, percentage=35, width_percentage=55)
        ui_qt_utils.center_window(self)

    def create_widgets(self):
        """Create the widgets for the window."""
        self.output_python_box = LineTextWidget(self)
        self.output_python_box.setMinimumHeight(150)
        PythonSyntaxHighlighter(self.output_python_box.get_text_edit().document())

        # Cross-version QSizePolicy enum (PySide2 / PySide6)
        q_size_policy_enum = getattr(ui_qt.QtWidgets.QSizePolicy, "Policy", ui_qt.QtWidgets.QSizePolicy)

        self.output_python_box.setSizePolicy(
            q_size_policy_enum.Expanding,
            q_size_policy_enum.Expanding
        )

        self.set_editable(self.is_initially_editable)

        if self.button_label and callable(self.button_function):
            self.action_button = ui_qt.QtWidgets.QPushButton(self.button_label)
            self.action_button.clicked.connect(self._execute_action_button_command)

    def create_layout(self):
        """Create the layout for the window."""
        mid_layout = ui_qt.QtWidgets.QVBoxLayout()
        mid_layout.addWidget(self.output_python_box)
        mid_layout.setContentsMargins(0, 5, 0, 5)  # L-T-R-B

        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        top_layout = ui_qt.QtWidgets.QVBoxLayout()
        bottom_layout = ui_qt.QtWidgets.QVBoxLayout()

        top_layout.setContentsMargins(15, 0, 15, 15)  # L-T-R-B
        main_layout.addLayout(top_layout)

        bottom_layout.addLayout(mid_layout)
        # The button is added here, below the text area, if it was created
        if self.action_button:
            bottom_layout.addWidget(self.action_button)
        bottom_layout.setContentsMargins(15, 0, 15, 15)  # L-T-R-B
        main_layout.addLayout(bottom_layout)

    def _execute_action_button_command(self):
        """
        Executes the function provided during initialization and updates the text area with the result.
        """
        if not callable(self.button_function):
            logger.warning("No valid function provided for the action button.")
            return

        try:
            result = self.button_function()
            self.set_python_output_text(str(result))
        except Exception as e:
            error_message = f"Error executing button function: {e}"
            logger.error(error_message)
            self.set_python_output_text(error_message)

    def clear_python_output(self):
        """Removes all text from the changelog box."""
        self.output_python_box.get_text_edit().clear()

    def set_python_output_text(self, text):
        """
        Add text to the python output box.

        Args:
            text (str): The text to set.
        """
        self.output_python_box.get_text_edit().setText(text)

    def get_python_output_text(self):
        """
        Gets the plain text found in the python output box.

        Returns:
            str: Text found inside the python output text edit box.
        """
        return self.output_python_box.get_text_edit().toPlainText()

    def set_editable(self, is_editable):
        """
        Sets the editable state of the python output box.

        Args:
            is_editable (bool): If True, the text box can be edited. If False, it is read-only.
        """
        self.output_python_box.get_text_edit().setReadOnly(not is_editable)

    def is_editable(self):
        """
        Gets the current editable state of the python output box.

        Returns:
            bool: True if the text box is editable, False otherwise.
        """
        return not self.output_python_box.get_text_edit().isReadOnly()

    def close_window(self):
        """Closes this window."""
        self.close()


if __name__ == "__main__":
    import inspect
    import sys
    import datetime

    def get_time():
        """A simple function to demonstrate the button functionality by getting the time."""
        time_stamp = f"# Refreshed at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        return time_stamp

    with ui_qt_utils.QtApplicationContext():
        window = PythonOutputView(
            button_label="Refresh", button_function=get_time  # Pass the function itself, don't call it
        )

        # Set the INITIAL text without calling the refresh function to prevent "auto-refresh"
        initial_text = inspect.getsource(sys.modules[__name__])
        window.set_python_output_text(text=initial_text)

        window.show()
