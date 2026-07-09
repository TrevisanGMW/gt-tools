"""
Batch Processor Logging View
"""

import gt.ui.line_text_widget as ui_line_text_widget
import gt.ui.resource_library as ui_res_lib
import gt.ui.syntax_highlighter as ui_syntax_highlighter
import gt.ui.qt_utils as ui_qt_utils
import gt.ui.qt_import as ui_qt


class BatchProcessorLoggingView(metaclass=ui_qt_utils.MayaWindowMeta):
    """Standalone log window for the Batch Processor."""

    def __init__(self, parent=None):
        """Initializes the Batch Processor logging window.

        Args:
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Batch Processor Logging")
        self.setGeometry(100, 100, 800, 600)
        self._is_open = False

        stylesheet = ui_res_lib.Stylesheet.scroll_bar_base
        stylesheet += ui_res_lib.Stylesheet.maya_dialog_base
        stylesheet += ui_res_lib.Stylesheet.list_widget_base
        self.setStyleSheet(stylesheet)

        self.log_widget = ui_line_text_widget.LineTextWidget(self)
        self.highlighter = ui_syntax_highlighter.LogSyntaxHighlighter(self.log_widget.get_text_edit().document())
        secondary_format = ui_syntax_highlighter.get_text_format([239, 224, 187])
        operation_format = ui_syntax_highlighter.get_text_format([137, 202, 120])
        self.highlighter.add_pattern(r"(\s-\s\([^\)]+\))", secondary_format)
        self.highlighter.add_pattern(
            r"\[OPERATION\]\s-\s\([^\)]+\)\s-\s(.+)$",
            operation_format,
            capture_group=1,
        )
        self.log_widget.get_text_edit().setReadOnly(True)
        self.log_widget.get_text_edit().setContextMenuPolicy(ui_qt.QtCore.Qt.CustomContextMenu)
        self.log_widget.get_text_edit().customContextMenuRequested.connect(self.show_context_menu)

        layout = ui_qt.QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.log_widget)
        self.setLayout(layout)
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.dev_code))
        ui_qt_utils.resize_to_screen(self, percentage=20)
        ui_qt_utils.center_window(self)

    def append_log(self, message):
        """Appends a message to the log window.

        Args:
            message (str): Message to append.
        """
        text_edit = self.log_widget.get_text_edit()
        message = str(message).replace("(multi-instance)", "(Multi-instance)")
        text_edit.append(message)

    def clear_log_widget(self):
        """Clears the log widget."""
        self.log_widget.get_text_edit().clear()

    def show_if_not_visible(self):
        """Shows the window, or raises it when already visible."""
        if not self._is_open:
            self.show()
            self._is_open = True
        else:
            self.raise_()
            self.activateWindow()

    def closeEvent(self, event):
        """Updates the open state when the window closes.

        Args:
            event (QCloseEvent): Close event.
        """
        self._is_open = False
        super().closeEvent(event)

    def show_context_menu(self, position):
        """Shows a context menu for the log text edit.

        Args:
            position (QPoint): Context menu position.
        """
        text_edit = self.log_widget.get_text_edit()
        menu = text_edit.createStandardContextMenu()
        menu.addSeparator()
        clear_action = ui_qt.QtLib.QtGui.QAction("Clear", self)
        clear_action.triggered.connect(text_edit.clear)
        menu.addAction(clear_action)
        exec_method = getattr(menu, "exec_", None)
        if not exec_method:
            exec_method = getattr(menu, "exec")
        exec_method(text_edit.mapToGlobal(position))
