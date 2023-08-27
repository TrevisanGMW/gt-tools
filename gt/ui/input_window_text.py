from PySide2.QtWidgets import QPushButton, QTextEdit, QVBoxLayout, QWidget, QHBoxLayout
from gt.ui.syntax_highlighter import PythonSyntaxHighlighter
from gt.ui import resource_library, qt_utils
from gt.ui.qt_utils import MayaWindowMeta
from PySide2.QtWidgets import QLabel
from PySide2.QtGui import QIcon
from PySide2.QtCore import Qt
import logging
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class InputWindowText(metaclass=MayaWindowMeta):
    ALIGN_TOP = "top"
    ALIGN_BOTTOM = "bottom"
    ALIGN_LEFT = "left"
    ALIGN_RIGHT = "right"
    ALIGN_CENTER = [ALIGN_TOP, ALIGN_BOTTOM]

    def __init__(self, parent=None, message=None, window_title=None, window_icon=None,
                 image=None, image_scale_pct=100, image_align="top", is_python_code=False):
        """
        Initialize the InputWindowText widget.

        Args:
            parent (QWidget): The parent widget.
            message (str): The description message to display.
            window_title (str): The title of the window.
            window_icon (str): The path to the window icon image file.
                               If a window icon is not provided, this will also become the window icon.
            image (str): The path to the image file to display. (Ignored if file does not exist)
            image_scale_pct (int): The percentage to scale the image by. (Ignored if an image is not provided)
            image_align (str): The alignment of the image ('top', 'bottom', 'left', or 'right').
            is_python_code (bool, optional): If active, it will apply syntax highlighting rules to the text.
        """
        super().__init__(parent)

        # Basic Vars
        if not window_title:
            window_title = "Text Input Window"
        self.setWindowTitle(window_title)
        self.setGeometry(100, 100, 500, 400)
        self.input_text_font = qt_utils.get_font(resource_library.Font.roboto)
        self.input_text_size = 12

        # Determine Window Icon
        self.window_icon = None
        if window_icon and isinstance(window_icon, str) and os.path.exists(window_icon):
            self.window_icon = window_icon
            self.setWindowIcon(QIcon(window_icon))
        else:
            self.setWindowIcon(QIcon(resource_library.Icon.root_help))

        # Determine Image Settings
        self.image_align = image_align
        self.image_label = None
        if image and os.path.exists(str(image)):
            self.image_label = QLabel()
            if image_align in self.ALIGN_CENTER:
                self.image_label.setAlignment(Qt.AlignCenter)
            pixmap = qt_utils.load_and_scale_pixmap(image_path=image, scale_percentage=image_scale_pct)
            self.image_label.setPixmap(pixmap)
            if not self.window_icon:
                self.setWindowIcon(QIcon(image))

        # Create Description
        self.description_label = QLabel("<description>")
        if message:
            self.set_message(message)

        # Create Text-field
        self.text_field = QTextEdit()
        text_stylesheet = f"padding: {10}; background-color: {resource_library.Color.Hex.gray_dark}"
        self.text_field.setStyleSheet(text_stylesheet)
        if is_python_code:
            PythonSyntaxHighlighter(self.text_field.document())
        self.text_field.setFont(self.input_text_font)
        self.text_field.setFontPointSize(self.input_text_size)

        # Create Buttons
        self.confirm_button = QPushButton("Confirm")
        self.cancel_button = QPushButton("Cancel")

        # Setup Layout
        self.create_layout()

        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint | Qt.WindowModal)

        # Determine Style
        progress_bar_stylesheet = resource_library.Stylesheet.maya_basic_dialog
        progress_bar_stylesheet += resource_library.Stylesheet.scroll_bar_dark
        self.setStyleSheet(progress_bar_stylesheet)

        # Create connections
        self.cancel_button.clicked.connect(self.close_window)

        # Adjust window
        qt_utils.resize_to_screen(self, percentage=20)
        qt_utils.center_window(self)

    def set_confirm_button_text(self, text):
        """
        Set the text for the confirm button.

        Args:
            text (str): The text to set for the confirm button.
        """
        if text and isinstance(text, str):
            self.confirm_button.setText(text)

    def set_message(self, message):
        """
        Set the description message.

        Args:
            message (str): The description message to display.
        """
        if message and isinstance(message, str):
            self.description_label.setText(message)

    def set_window_title(self, window_title):
        """
        Set the window title.

        Args:
            window_title (str): The title to set for the window.
        """
        if window_title and isinstance(window_title, str):
            self.setWindowTitle(window_title)

    def set_text_field_text(self, text):
        """
        Set the text in the text field.

        Args:
            text (str): The text to set in the text field.
        """
        if text and isinstance(text, str):
            self.text_field.setText(text)

    def get_text_field_text(self):
        """
        Get the current text from the text field.

        Returns:
            str: The current text in the text field.
        """
        return self.text_field.toPlainText()

    def set_text_field_placeholder(self, text):
        """
        Set the placeholder text for the text field.

        Args:
            text (str): The placeholder text to set for the text field.
        """
        if text and isinstance(text, str):
            self.text_field.setPlaceholderText(text)

    def create_layout(self):
        """
        Create the layout for the widget.
        This method sets up the layout for the description label, text field, and buttons.
        """
        # ------------------------------- Description Layout Start -------------------------------
        # Determine Layout (left/right = Horizontal, top/bottom = Vertical)
        if self.image_label and self.image_align == self.ALIGN_LEFT or self.image_align == self.ALIGN_RIGHT:
            layout_description = QHBoxLayout()
        else:
            layout_description = QVBoxLayout()
        layout_description.setAlignment(Qt.AlignCenter)  # Align the labels to the center
        # Image Alignment - Top
        if self.image_label and (self.image_align is self.ALIGN_TOP or self.image_align is self.ALIGN_LEFT):
            layout_description.addWidget(self.image_label)
        # Description
        layout_description.addWidget(self.description_label)
        # Image Alignment - Bottom
        if self.image_label and (self.image_align is self.ALIGN_BOTTOM or self.image_align is self.ALIGN_RIGHT):
            layout_description.addWidget(self.image_label)
        layout_description.setAlignment(Qt.AlignCenter)  # Align the labels to the center
        layout_description.setContentsMargins(15, 15, 15, 15)
        # -------------------------------- Description Layout End --------------------------------

        layout_input = QVBoxLayout()
        layout_input.setContentsMargins(0, 15, 0, 0)
        layout_input.addWidget(self.text_field)

        layout_button = QHBoxLayout()
        layout_button.addWidget(self.confirm_button)
        layout_button.addWidget(self.cancel_button)

        layout_main = QVBoxLayout()
        layout_main.addLayout(layout_description)
        layout_main.addLayout(layout_input)
        layout_main.addLayout(layout_button)
        self.setLayout(layout_main)

    def close_window(self):
        """ Closes Input Window """
        self.close()


if __name__ == "__main__":
    sample_dict = {
        'name': 'John Doe',
        'age': 30,
        'city': 'Vancouver',
        'email': 'john@example.com',
        'is_alive': True
    }
    from gt.utils import iterable_utils
    formatted_dict = iterable_utils.format_dict_with_keys_per_line(sample_dict, keys_per_line=1,
                                                                   bracket_new_line=True)

    with qt_utils.QtApplicationContext():
        mocked_message = r"Mocked Message. Mocked Message. Mocked Message. Mocked Message. Mocked Message."
        text_input_window = InputWindowText(message=mocked_message,
                                            image=resource_library.Icon.dev_screwdriver,
                                            image_scale_pct=10,
                                            is_python_code=True)
        text_input_window.set_text_field_placeholder("placeholder")
        text_input_window.set_text_field_text(formatted_dict)
        text_input_window.set_window_title("New Window Title")
        text_input_window.show()
