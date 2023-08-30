"""
CurveToPythonView View/Window
"""
from PySide2.QtWidgets import QPushButton, QLabel, QVBoxLayout, QFrame
from gt.ui.syntax_highlighter import PythonSyntaxHighlighter
from gt.ui.line_text_widget import LineTextWidget
import gt.ui.resource_library as resource_library
from gt.ui.qt_utils import MayaWindowMeta
from PySide2 import QtWidgets, QtCore
import gt.ui.qt_utils as qt_utils
from PySide2.QtGui import QIcon


class CurveToPythonView(metaclass=MayaWindowMeta):
    def __init__(self, parent=None, controller=None, version=None):
        """
        Initialize the CurveToPythonView.
        This window represents the main GUI window of the tool.

        Args:
            parent (str): Parent for this window
            controller (CurveToPythonViewController): CurveToPythonViewController, not to be used, here so
                                                          it's not deleted by the garbage collector.  Defaults to None.
            version (str, optional): If provided, it will be used to determine the window title. e.g. Title - (v1.2.3)
        """
        super().__init__(parent=parent)

        self.controller = controller  # Only here so it doesn't get deleted by the garbage collectors

        # Window Title
        self.window_title = "GT Curve to Python"
        _window_title = self.window_title
        if version:
            _window_title += f' - (v{str(version)})'
        self.setWindowTitle(_window_title)

        # Labels
        self.title_label = None
        self.output_python_label = None
        # Buttons
        self.help_btn = None
        self.extract_crv_python_brn = None
        self.extract_shape_state_btn = None
        self.run_code_btn = None
        self.save_to_shelf_btn = None
        # Misc
        self.output_python_box = None

        self.create_widgets()
        self.create_layout()

        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.WindowMaximizeButtonHint |
                            QtCore.Qt.WindowMinimizeButtonHint)
        self.setWindowIcon(QIcon(resource_library.Icon.tool_attributes_to_python))

        stylesheet = resource_library.Stylesheet.scroll_bar_dark
        stylesheet += resource_library.Stylesheet.maya_basic_dialog
        stylesheet += resource_library.Stylesheet.list_widget_dark
        self.setStyleSheet(stylesheet)
        self.extract_crv_python_brn.setStyleSheet(resource_library.Stylesheet.push_button_bright)
        self.extract_shape_state_btn.setStyleSheet(resource_library.Stylesheet.push_button_bright)
        qt_utils.resize_to_screen(self, percentage=40, width_percentage=55)
        qt_utils.center_window(self)

    def create_widgets(self):
        """Create the widgets for the window."""
        self.title_label = QtWidgets.QLabel(self.window_title)
        self.title_label.setStyleSheet('background-color: rgb(93, 93, 93); border: 0px solid rgb(93, 93, 93); \
                                        color: rgb(255, 255, 255); padding: 10px; margin-bottom: 0; text-align: left;')
        self.title_label.setFont(qt_utils.get_font(resource_library.Font.roboto))
        self.help_btn = QPushButton('Help')
        self.help_btn.setToolTip("Open Help Dialog.")
        self.help_btn.setStyleSheet('color: rgb(255, 255, 255); padding: 10px; '
                                    'padding-right: 15px; padding-left: 15px; margin: 0;')
        self.help_btn.setFont(qt_utils.get_font(resource_library.Font.roboto))

        self.output_python_label = QLabel("Output Python Code:")
        self.output_python_label.setStyleSheet(f"font-weight: bold; font-size: 8; margin-top: 0; "
                                               f"color: {resource_library.Color.RGB.gray_lighter};")

        self.output_python_box = LineTextWidget(self)

        self.output_python_box.setMinimumHeight(150)
        PythonSyntaxHighlighter(self.output_python_box.get_text_edit().document())
        #
        self.output_python_label.setAlignment(QtCore.Qt.AlignCenter)
        self.output_python_label.setFont(qt_utils.get_font(resource_library.Font.roboto))
        #
        self.output_python_box.setSizePolicy(self.output_python_box.sizePolicy().Expanding,
                                             self.output_python_box.sizePolicy().Expanding)

        self.extract_crv_python_brn = QPushButton('Extract Curve to Python')
        self.extract_crv_python_brn.setToolTip("Extracts curves as python code. (New Curve)")
        self.extract_shape_state_btn = QPushButton("Extract Shape State to Python")
        self.extract_shape_state_btn.setToolTip('Extracts curve shape state. '
                                                '(Snapshot of the shape)')
        self.run_code_btn = QPushButton("Run Code")
        self.run_code_btn.setStyleSheet("padding: 10;")
        self.save_to_shelf_btn = QPushButton("Save to Shelf")
        self.save_to_shelf_btn.setStyleSheet("padding: 10;")

    def create_layout(self):
        """Create the layout for the window."""

        top_buttons_layout = QtWidgets.QVBoxLayout()
        two_horizontal_btn_layout = QtWidgets.QHBoxLayout()
        two_horizontal_btn_layout.addWidget(self.extract_crv_python_brn)
        two_horizontal_btn_layout.addWidget(self.extract_shape_state_btn)
        top_buttons_layout.addLayout(two_horizontal_btn_layout)

        mid_layout = QVBoxLayout()
        mid_layout.addWidget(self.output_python_label)
        mid_layout.addWidget(self.output_python_box)
        mid_layout.setContentsMargins(0, 5, 0, 5)  # L-T-R-B

        bottom_buttons_layout = QVBoxLayout()
        two_horizontal_btn_layout = QtWidgets.QHBoxLayout()
        two_horizontal_btn_layout.addWidget(self.run_code_btn)
        two_horizontal_btn_layout.addWidget(self.save_to_shelf_btn)
        bottom_buttons_layout.addLayout(two_horizontal_btn_layout)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)

        title_layout = QtWidgets.QHBoxLayout()
        title_layout.setSpacing(0)
        title_layout.addWidget(self.title_label, 5)
        title_layout.addWidget(self.help_btn)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        top_layout = QtWidgets.QVBoxLayout()
        bottom_layout = QtWidgets.QVBoxLayout()
        top_layout.addLayout(title_layout)
        top_layout.addLayout(top_buttons_layout)
        top_layout.setContentsMargins(15, 15, 15, 15)  # L-T-R-B
        main_layout.addLayout(top_layout)
        main_layout.addWidget(separator)
        bottom_layout.addLayout(mid_layout)
        bottom_layout.addLayout(bottom_buttons_layout)
        bottom_layout.setContentsMargins(15, 0, 15, 15)  # L-T-R-B
        main_layout.addLayout(bottom_layout)

    def clear_python_output(self):
        """ Removes all text from the changelog box """
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

    def close_window(self):
        """ Closes this window """
        self.close()


if __name__ == "__main__":
    import inspect
    import sys

    with qt_utils.QtApplicationContext():
        window = CurveToPythonView(version="1.2.3")  # View
        window.set_python_output_text(text=inspect.getsource(sys.modules[__name__]))
        window.show()
