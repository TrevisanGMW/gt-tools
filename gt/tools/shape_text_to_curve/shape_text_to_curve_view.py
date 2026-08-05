"""Qt view for the Shape Text to Curve tool."""

from gt.ui.qt_utils import MayaWindowMeta
import gt.ui.qt_import as ui_qt
import gt.ui.qt_utils as qt_utils
import gt.ui.resource_library as ui_res_lib


class ShapeTextToCurveView(metaclass=MayaWindowMeta):
    """Responsive main window for creating Maya text curves."""

    def __init__(self, parent=None, version=None):
        """Initializes the Shape Text to Curve view.

        Args:
            parent (QWidget, optional): Parent widget.
            version (str, optional): Tool version displayed in the title.
        """
        super().__init__(parent=parent)
        title = "Text Curve Generator"
        if version:
            title += f" - (v{version})"
        self.setWindowTitle(title)
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_crv_text))
        self.setMinimumWidth(300)
        self.setStyleSheet(self._build_stylesheet())
        self._build_widgets()
        self.adjustSize()
        qt_utils.center_window(self)

    def _build_widgets(self):
        """Builds and lays out all view widgets."""
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(9)

        main_layout.addWidget(self._build_title_bar())

        font_layout = ui_qt.QtWidgets.QHBoxLayout()
        font_layout.setSpacing(8)
        font_label = ui_qt.QtWidgets.QLabel("Current Font:")
        self.font_button = ui_qt.QtWidgets.QPushButton()
        self.font_button.setObjectName("fontButton")
        self.font_button.setMinimumHeight(24)
        self.font_button.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        self.font_button.setToolTip("Choose the font used to build new text curves.")
        font_layout.addWidget(font_label)
        font_layout.addWidget(self.font_button, 1)
        main_layout.addLayout(font_layout)

        main_layout.addWidget(self._build_labeled_separator("Text:"))

        self.text_field = ui_qt.QtWidgets.QPlainTextEdit()
        self.text_field.setMinimumHeight(48)
        self.text_field.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Expanding)
        self.text_field.setPlaceholderText("Enter text; separate multiple entries with commas or new lines")
        self.text_field.setToolTip("Use commas or new lines to create multiple text curves in one operation.")
        main_layout.addWidget(self.text_field, 1)

        self.generate_button = ui_qt.QtWidgets.QPushButton("Generate")
        self.generate_button.setObjectName("generateButton")
        self.generate_button.setMinimumHeight(30)
        self.generate_button.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        self.generate_button.setToolTip("Create one merged curve transform for each text entry.")
        main_layout.addWidget(self.generate_button)

        self.status_label = ui_qt.QtWidgets.QLabel()
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        self.status_label.setVisible(False)
        main_layout.addWidget(self.status_label)

        self._status_timer = ui_qt.QtCore.QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.setInterval(2000)
        self._status_timer.timeout.connect(lambda: self.set_status(""))

    def _build_title_bar(self):
        """Builds the title strip and help button.

        Returns:
            QFrame: Configured title strip.
        """
        title_bar = ui_qt.QtWidgets.QFrame()
        title_bar.setObjectName("titleBar")
        title_layout = ui_qt.QtWidgets.QHBoxLayout(title_bar)
        title_layout.setContentsMargins(9, 0, 0, 0)
        title_layout.setSpacing(6)

        title_label = ui_qt.QtWidgets.QLabel("Text Curve Generator")
        title_label.setObjectName("titleLabel")
        self.help_button = ui_qt.QtWidgets.QPushButton("Help")
        self.help_button.setObjectName("helpButton")
        self.help_button.setMinimumWidth(56)
        self.help_button.setSizePolicy(ui_qt.QtLib.SizePolicy.Fixed, ui_qt.QtLib.SizePolicy.Expanding)
        self.help_button.setToolTip("Show usage information for this tool.")

        title_layout.addWidget(title_label)
        title_layout.addStretch(1)
        title_layout.addWidget(self.help_button)
        return title_bar

    @staticmethod
    def _build_labeled_separator(text):
        """Builds a horizontal separator with a centered section label.

        Args:
            text (str): Section label shown between the two separator lines.

        Returns:
            QWidget: Separator widget with lines flanking the label.
        """
        widget = ui_qt.QtWidgets.QWidget()
        layout = ui_qt.QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)

        left_line = ui_qt.QtWidgets.QFrame()
        right_line = ui_qt.QtWidgets.QFrame()
        for line in [left_line, right_line]:
            line.setFrameShape(ui_qt.QtLib.FrameStyle.HLine)
            line.setFrameShadow(ui_qt.QtLib.FrameStyle.Sunken)

        label = ui_qt.QtWidgets.QLabel(text)
        label.setObjectName("separatorLabel")
        label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        layout.addWidget(left_line, 1)
        layout.addWidget(label)
        layout.addWidget(right_line, 1)
        return widget

    def resize_to_contents(self):
        """Shrinks a floating window to the smallest useful content size."""
        try:
            if hasattr(self, "isFloating") and not self.isFloating():
                return
        except (AttributeError, RuntimeError):
            pass
        self.updateGeometry()
        self.adjustSize()
        content_height = self.sizeHint().height()
        if content_height > 0:
            self.resize(max(self.minimumWidth(), self.sizeHint().width()), content_height)

    def get_text(self):
        """Gets the text currently entered by the user.

        Returns:
            str: Current text field value.
        """
        return self.text_field.toPlainText()

    def set_text(self, text):
        """Sets the text field value.

        Args:
            text (str): New text field value.
        """
        self.text_field.setPlainText(text)

    def set_font_name(self, font_name):
        """Updates the displayed font name.

        Args:
            font_name (str): Concise font family name.
        """
        self.font_button.setText(font_name)

    def set_status(self, message, is_error=False):
        """Shows a concise operation status below the action button.

        The message automatically clears after a short delay.

        Args:
            message (str): Status message. An empty value hides the label.
            is_error (bool, optional): Whether to use warning emphasis.
        """
        self.status_label.setProperty("error", is_error)
        self.status_label.setText(message)
        self.status_label.setVisible(bool(message))
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        if message:
            self._status_timer.start()
        else:
            self._status_timer.stop()

    def create_help_dialog(self):
        """Creates the non-modal help dialog.

        Returns:
            QDialog: Configured help dialog.
        """
        dialog = ui_qt.QtWidgets.QDialog(self)
        dialog.setWindowTitle("Text Curve Generator Help")
        dialog.setWindowIcon(ui_qt.QtGui.QIcon(":/question.png"))
        dialog.setMinimumSize(340, 250)
        dialog.resize(430, 310)
        dialog.setStyleSheet(self._build_stylesheet())

        layout = ui_qt.QtWidgets.QVBoxLayout(dialog)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        title_label = ui_qt.QtWidgets.QLabel("Text Curve Generator Help")
        title_label.setObjectName("helpTitle")
        title_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        description = ui_qt.QtWidgets.QLabel(
            "Creates merged Maya curves containing the text from the input field. "
            "All letter shapes for an entry are placed under one transform."
        )
        description.setWordWrap(True)
        multiple_entries = ui_qt.QtWidgets.QLabel(
            "Separate entries with commas to create multiple curves in one operation."
        )
        multiple_entries.setWordWrap(True)
        font_help = ui_qt.QtWidgets.QLabel(
            "Current Font: Click the font button to choose the font used for new curves."
        )
        font_help.setWordWrap(True)
        links = ui_qt.QtWidgets.QLabel(
            '<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a> &nbsp; '
            '<a href="https://github.com/TrevisanGMW">GitHub</a>'
        )
        links.setOpenExternalLinks(True)
        links.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        close_button = ui_qt.QtWidgets.QPushButton("OK")
        close_button.setMinimumHeight(30)
        close_button.clicked.connect(dialog.accept)

        layout.addWidget(title_label)
        layout.addWidget(description)
        layout.addWidget(multiple_entries)
        layout.addWidget(font_help)
        layout.addStretch(1)
        layout.addWidget(links)
        layout.addWidget(close_button)
        return dialog

    @staticmethod
    def _build_stylesheet():
        """Builds the tool stylesheet.

        Returns:
            str: Combined Maya and tool-specific stylesheet.
        """
        field_background = ui_res_lib.Color.RGB.gray_darker
        field_selection = ui_res_lib.Color.RGB.blue_pastel
        field_text = ui_res_lib.Color.RGB.white_smoke_darker
        return ui_res_lib.Stylesheet.maya_dialog_base + f"""
            QFrame#titleBar {{ background-color: #666666; border: none; }}
            QLabel#titleLabel, QLabel#helpTitle {{ color: #f0f0f0; font-weight: bold; }}
            QPushButton#helpButton {{ background-color: #666666; color: #eeeeee; padding: 2px 10px; }}
            QPushButton#helpButton:hover {{ background-color: #777777; }}
            QPushButton#fontButton {{ background-color: #5c5c5c; color: #dddddd; }}
            QPushButton#fontButton:hover {{ background-color: #696969; }}
            QPushButton#generateButton {{ background-color: #999999; color: #202020; font-weight: bold; }}
            QPushButton#generateButton:hover {{ background-color: #aaaaaa; }}
            QPushButton#generateButton:pressed {{ background-color: #777777; }}
            QLabel#separatorLabel {{ color: #909090; font-weight: normal; }}
            QLabel#statusLabel {{ color: #a8c7a0; font-weight: normal; }}
            QLabel#statusLabel[error="true"] {{ color: #d8a09a; }}
            QLineEdit, QPlainTextEdit {{ padding: 3px 5px; }}
            QPlainTextEdit {{
                background-color: {field_background};
                selection-background-color: {field_selection};
                color: {field_text};
                border: none;
            }}
        """


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = ShapeTextToCurveView(version="dev")
        window.show()
