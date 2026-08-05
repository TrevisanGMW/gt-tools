"""
Sine Attributes View

This module contains the SineAttributesView class and SineAttributesHelpDialog,
representing the user interface for the Sine Attributes tool.
"""
from gt.ui.qt_utils import MayaWindowMeta
import gt.ui.qt_utils as qt_utils
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt


class SineAttributesView(metaclass=MayaWindowMeta):
    """View class for the Sine Attributes tool."""

    def __init__(self, parent=None, version=None):
        """Initializes the SineAttributesView.

        Args:
            parent (QWidget, optional): Parent widget for this window.
            version (str, optional): Version of the tool.
        """
        super().__init__(parent=parent)
        self.version = version

        # Set Window Title and Attributes
        window_title = "Add Sine Attributes"
        if version:
            window_title += f"  (v{version})"
        self.setWindowTitle(window_title)
        self.setMinimumWidth(300)

        # Window Flags and Icons
        self.setWindowFlags(
            self.windowFlags()
            | ui_qt.QtLib.WindowFlag.WindowMaximizeButtonHint
            | ui_qt.QtLib.WindowFlag.WindowMinimizeButtonHint
        )
        self.setWindowIcon(ui_qt.QtGui.QIcon(":/sineCurveProfile.png"))

        # Create UI elements
        self.create_widgets()
        self.create_layout()
        self.apply_stylesheet()

        # Adjust size to minimum and center
        self.adjustSize()
        qt_utils.center_window(self)

    def create_widgets(self):
        """Creates the widgets for the view."""
        # Title Label
        self.title_label = ui_qt.QtWidgets.QLabel("Add Sine Attributes")
        self.title_label.setObjectName("sineTitleLabel")
        self.title_label.setFont(qt_utils.get_font(ui_res_lib.Font.roboto))

        # Help Button
        self.help_btn = ui_qt.QtWidgets.QPushButton("Help")
        self.help_btn.setObjectName("helpButton")
        self.help_btn.setFont(qt_utils.get_font(ui_res_lib.Font.roboto))
        self.help_btn.setToolTip("Open Help Dialog.")

        # Body Instruction Label
        self.instruction_label = ui_qt.QtWidgets.QLabel("Select attribute holder first, then run script.")
        self.instruction_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        self.instruction_label.setFont(qt_utils.get_font(ui_res_lib.Font.roboto))

        # Prefix Label and QLineEdit
        self.prefix_label = ui_qt.QtWidgets.QLabel("Sine Attributes Prefix:")
        self.prefix_field = ui_qt.QtWidgets.QLineEdit()
        self.prefix_field.setPlaceholderText("Sine Attributes Prefix (Optional)")

        # Checkboxes
        self.add_abs_checkbox = ui_qt.QtWidgets.QCheckBox("Add Abs Output")
        self.add_abs_checkbox.setToolTip("Creates an output version that gives only positive values.")
        self.add_prefix_nn_checkbox = ui_qt.QtWidgets.QCheckBox("Add Prefix to Nice Name")
        self.add_prefix_nn_checkbox.setToolTip("Determines if the prefix should be added to the nice name.")

        # Main Button
        self.add_sine_btn = ui_qt.QtWidgets.QPushButton("Add Sine Attributes")
        self.add_sine_btn.setObjectName("primaryButton")
        self.add_sine_btn.setFont(qt_utils.get_font(ui_res_lib.Font.roboto))

    def create_layout(self):
        """Assembles layouts for the view."""
        # Main Layout
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Title Bar Frame
        title_bar_frame = ui_qt.QtWidgets.QFrame()
        title_bar_frame.setObjectName("titleBar")
        title_bar_layout = ui_qt.QtWidgets.QHBoxLayout(title_bar_frame)
        title_bar_layout.setContentsMargins(8, 4, 4, 4)
        title_bar_layout.setSpacing(4)
        title_bar_layout.addWidget(self.title_label)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(self.help_btn)

        # Inputs layout
        form_layout = ui_qt.QtWidgets.QVBoxLayout()
        form_layout.setSpacing(6)
        form_layout.addWidget(self.prefix_label)
        form_layout.addWidget(self.prefix_field)

        # Checkbox Layout
        checkbox_layout = ui_qt.QtWidgets.QHBoxLayout()
        checkbox_layout.addWidget(self.add_abs_checkbox)
        checkbox_layout.addWidget(self.add_prefix_nn_checkbox)

        # Add all to main layout
        main_layout.addWidget(title_bar_frame)
        main_layout.addWidget(self.instruction_label)
        main_layout.addSpacing(5)
        main_layout.addLayout(form_layout)
        main_layout.addLayout(checkbox_layout)
        main_layout.addSpacing(5)
        main_layout.addWidget(self.add_sine_btn)

    def apply_stylesheet(self):
        """Applies repository and custom UI styles."""
        stylesheet = ui_res_lib.Stylesheet.maya_dialog_base
        stylesheet += ui_res_lib.Stylesheet.line_edit_base
        stylesheet += ui_res_lib.Stylesheet.checkbox_base
        stylesheet += ui_res_lib.Stylesheet.btn_push_base
        stylesheet += """
            QFrame#titleBar {
                background-color: #555555;
                border: 1px solid #626262;
            }
            QLabel#sineTitleLabel {
                color: #f0f0f0;
                font-weight: bold;
            }
            QPushButton#helpButton {
                background: transparent;
                border: none;
                color: #e5e5e5;
                padding: 4px 10px;
            }
            QPushButton#helpButton:hover {
                background-color: #666666;
            }
            QPushButton#primaryButton {
                background-color: #9a9a9a;
                color: #202020;
                font-weight: bold;
                border: 1px solid #7d7d7d;
                padding: 6px 10px;
            }
            QPushButton#primaryButton:hover {
                background-color: #aaaaaa;
            }
            QPushButton#primaryButton:pressed {
                background-color: #4b4b4b;
                color: #dddddd;
            }
        """
        self.setStyleSheet(stylesheet)

    def get_prefix(self):
        """Gets the prefix text from the QLineEdit field.

        Returns:
            str: Cleaned prefix name or empty string.
        """
        return self.prefix_field.text().strip()

    def set_prefix(self, text):
        """Sets the text for the prefix QLineEdit field.

        Args:
            text (str): Prefix text.
        """
        self.prefix_field.setText(str(text))

    def get_add_abs(self):
        """Gets whether absolute output creation is checked.

        Returns:
            bool: Checked state.
        """
        return self.add_abs_checkbox.isChecked()

    def set_add_abs(self, state):
        """Sets the checked state for absolute output checkbox.

        Args:
            state (bool): Checkbox state.
        """
        self.add_abs_checkbox.setChecked(bool(state))

    def get_add_prefix_nn(self):
        """Gets whether nice name prefixing is checked.

        Returns:
            bool: Checked state.
        """
        return self.add_prefix_nn_checkbox.isChecked()

    def set_add_prefix_nn(self, state):
        """Sets the checked state for nice name prefixing checkbox.

        Args:
            state (bool): Checkbox state.
        """
        self.add_prefix_nn_checkbox.setChecked(bool(state))


class SineAttributesHelpDialog(ui_qt.QtWidgets.QDialog):
    """Help dialog for the Sine Attributes tool."""

    def __init__(self, parent=None):
        """Initializes the SineAttributesHelpDialog.

        Args:
            parent (QWidget, optional): Parent widget for the dialog.
        """
        super().__init__(parent=parent)
        self.setWindowTitle("Add Sine Attributes Help")
        self.setMinimumWidth(320)
        self.setWindowFlags(self.windowFlags() ^ ui_qt.QtLib.WindowFlag.WindowContextHelpButtonHint)
        self.setWindowIcon(ui_qt.QtGui.QIcon(":/question.png"))

        # Create widgets
        title_label = ui_qt.QtWidgets.QLabel("Add Sine Attributes Help")
        title_label.setObjectName("helpTitleLabel")
        title_label.setFont(qt_utils.get_font(ui_res_lib.Font.roboto))
        title_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)

        help_text = (
            "Create Sine attributes without using<br>"
            "third-party plugins or expressions.<br><br>"
            "Select an object, then click on \"Add Sine Attributes\".<br><br>"
            "<b>Sine Attributes:</b><br>"
            "&bull; <b>Time:</b> Multiplier for the time input (tick)<br>"
            "&bull; <b>Amplitude:</b> Wave amplitude (how high it gets)<br>"
            "&bull; <b>Frequency:</b> Wave frequency (how often it happens)<br>"
            "&bull; <b>Offset:</b> Value added after calculation, offset.<br>"
            "&bull; <b>Tick:</b> Time as seen by the sine system.<br>"
            "&bull; <b>Output:</b> Result of the sine operation.<br>"
            "&bull; <b>Abs Output:</b> Absolute output (no negative values)<br>"
        )

        text_label = ui_qt.QtWidgets.QLabel(help_text)
        text_label.setFont(qt_utils.get_font(ui_res_lib.Font.roboto))
        text_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignLeft)
        text_label.setWordWrap(True)

        author_layout = ui_qt.QtWidgets.QFormLayout()
        author_layout.setSpacing(5)

        author_label = ui_qt.QtWidgets.QLabel("Guilherme Trevisan")
        email_label = ui_qt.QtWidgets.QLabel('<a href="mailto:trevisangmw@gmail.com" style="color: #ffffff;">TrevisanGMW@gmail.com</a>')
        email_label.setOpenExternalLinks(True)
        github_label = ui_qt.QtWidgets.QLabel('<a href="https://github.com/TrevisanGMW" style="color: #ffffff;">Github</a>')
        github_label.setOpenExternalLinks(True)

        author_layout.addRow("Author: ", author_label)
        author_layout.addRow("Email: ", email_label)
        author_layout.addRow("Github: ", github_label)

        ok_btn = ui_qt.QtWidgets.QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setFixedHeight(30)
        ok_btn.setFont(qt_utils.get_font(ui_res_lib.Font.roboto))

        # Layout
        layout = ui_qt.QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        layout.addWidget(title_label)
        layout.addWidget(text_label)
        layout.addSpacing(5)
        layout.addLayout(author_layout)
        layout.addSpacing(5)
        layout.addWidget(ok_btn)

        # Style
        stylesheet = ui_res_lib.Stylesheet.maya_dialog_base
        stylesheet += ui_res_lib.Stylesheet.btn_push_base
        stylesheet += """
            QLabel#helpTitleLabel {
                font-weight: bold;
                font-size: 14px;
                color: #ffffff;
                background-color: #555555;
                padding: 6px;
                border: 1px solid #626262;
            }
        """
        self.setStyleSheet(stylesheet)
        self.adjustSize()


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = SineAttributesView(version="1.0.0")
        window.show()
