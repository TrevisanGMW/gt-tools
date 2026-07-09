"""
Reusable Inline Python Editor Widget
"""

from gt.tools.batch_processor.widgets import attr_widget_base
import gt.ui.file_dialog as ui_file_dialog
import gt.ui.qt_utils as ui_qt_utils
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt
import os
import sys


class PythonCodeTextEdit(ui_qt.QtWidgets.QTextEdit):
    """QTextEdit variant that keeps Python indentation space-based."""

    TAB_SPACES = 4

    def keyPressEvent(self, event):
        """Handles tab indentation before falling back to the base editor.

        Args:
            event (QKeyEvent): Key event received by the editor.
        """
        key = event.key()
        if key == get_qt_key("Key_Tab"):
            self.indent_selection()
            return
        if key == get_qt_key("Key_Backtab"):
            self.outdent_selection()
            return
        super().keyPressEvent(event)

    def insertFromMimeData(self, source):
        """Expands pasted tabs into spaces.

        Args:
            source (QMimeData): Pasted mime data.
        """
        if source and source.hasText():
            self.textCursor().insertText(source.text().replace("\t", " " * self.TAB_SPACES))
            return
        super().insertFromMimeData(source)

    def indent_selection(self):
        """Indents the current line or selected lines using spaces."""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            cursor.insertText(" " * self.TAB_SPACES)
            return
        self.edit_selected_blocks(add_spaces=True)

    def outdent_selection(self):
        """Outdents the current line or selected lines."""
        self.edit_selected_blocks(add_spaces=False)

    def edit_selected_blocks(self, add_spaces=True):
        """Indents or outdents all blocks touched by the selection.

        Args:
            add_spaces (bool, optional): Whether to indent instead of outdent.
        """
        cursor = self.textCursor()
        document = self.document()
        selection_start = cursor.selectionStart()
        selection_end = cursor.selectionEnd()
        if selection_start == selection_end:
            selection_start = cursor.block().position()
            selection_end = selection_start + cursor.block().length()
        end_position = max(selection_start, selection_end - 1)
        block = document.findBlock(selection_start)
        end_block = document.findBlock(end_position)
        cursor.beginEditBlock()
        while block.isValid() and block.position() <= end_block.position():
            block_cursor = ui_qt.QtGui.QTextCursor(block)
            if add_spaces:
                block_cursor.insertText(" " * self.TAB_SPACES)
            else:
                remove_count = get_outdent_count(block.text(), self.TAB_SPACES)
                if remove_count:
                    block_cursor.setPosition(block.position() + remove_count, ui_qt.QtLib.TextCursor.KeepAnchor)
                    block_cursor.removeSelectedText()
            block = block.next()
        cursor.endEditBlock()


def get_qt_key(key_name):
    """Gets a Qt key value across PySide versions.

    Args:
        key_name (str): Key enum name, for example `Key_Tab`.

    Returns:
        object: Qt key enum value.
    """
    if ui_qt.IS_PYSIDE6:
        return getattr(ui_qt.QtCore.Qt.Key, key_name)
    return getattr(ui_qt.QtCore.Qt, key_name)


def get_outdent_count(text, tab_spaces=4):
    """Gets how many leading characters should be removed for one outdent.

    Args:
        text (str): Block text.
        tab_spaces (int, optional): Number of spaces used for one tab.

    Returns:
        int: Number of leading characters to remove.
    """
    if not text:
        return 0
    if text.startswith("\t"):
        return 1
    count = 0
    for character in text[:tab_spaces]:
        if character != " ":
            break
        count += 1
    return count


class InlinePythonEditorWidget(ui_qt.QtWidgets.QWidget):
    """Shared Python editor used by batch task attribute widgets."""

    def __init__(
        self,
        parent=None,
        owner=None,
        text="",
        placeholder="",
        tooltip="",
        text_changed_callback=None,
        font_size=14,
        font_size_changed_callback=None,
    ):
        """Initializes the inline Python editor.

        Args:
            parent (QWidget, optional): Parent widget.
            owner (QWidget, optional): Attribute widget owning this editor.
            text (str, optional): Initial Python code.
            placeholder (str, optional): Placeholder text.
            tooltip (str, optional): Editor tooltip.
            text_changed_callback (callable, optional): Called when editor text changes.
            font_size (int, optional): Initial editor font size.
            font_size_changed_callback (callable, optional): Called when font size changes.
        """
        super().__init__(parent=parent)
        self.owner = owner
        self.text_changed_callback = text_changed_callback
        self.font_size_changed_callback = font_size_changed_callback
        self.python_edit = None
        self.python_edit_font = None
        self.font_size_slider = None
        self.font_size_value_label = None
        self.highlighter = None
        self.base_stylesheet = ""
        self._build_widgets(text=text, placeholder=placeholder, tooltip=tooltip, font_size=font_size)

    def _build_widgets(self, text, placeholder, tooltip, font_size):
        """Builds editor controls.

        Args:
            text (str): Initial editor text.
            placeholder (str): Placeholder text.
            tooltip (str): Editor tooltip.
            font_size (int): Initial font size.
        """
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        self.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Expanding)

        top_layout = ui_qt.QtWidgets.QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 5)

        run_code_btn = ui_qt.QtWidgets.QPushButton("Run Code")
        run_code_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.dev_code))
        run_code_btn.setToolTip("Execute the Python code in the text editor.")
        run_code_btn.clicked.connect(self.on_button_run_code_clicked)
        top_layout.addWidget(run_code_btn)

        insert_selection_btn = ui_qt.QtWidgets.QPushButton("Insert Selection")
        insert_selection_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.dev_filter))
        insert_selection_btn.setToolTip("Insert the current Maya selection as a Python list at the cursor.")
        insert_selection_btn.clicked.connect(self.on_insert_selection_clicked)
        top_layout.addWidget(insert_selection_btn)

        save_btn = ui_qt.QtWidgets.QPushButton("Save")
        save_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_save))
        save_btn.setToolTip("Save the current script to a file.")
        save_btn.clicked.connect(self.on_save_clicked)
        top_layout.addWidget(save_btn)

        load_btn = ui_qt.QtWidgets.QPushButton("Load")
        load_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        load_btn.setToolTip("Load a script from a file.")
        load_btn.clicked.connect(self.on_load_clicked)
        top_layout.addWidget(load_btn)
        top_layout.addStretch()

        font_label = ui_qt.QtWidgets.QLabel("Font Size:")
        attr_widget_base.configure_label_for_scaled_displays(font_label)
        font_label.setToolTip("Python editor font size.")
        top_layout.addWidget(font_label)
        self.font_size_slider = ui_qt.QtWidgets.QSlider(ui_qt.QtLib.Orientation.Horizontal)
        self.font_size_slider.setRange(8, 24)
        self.font_size_slider.setMinimumWidth(125)
        initial_font_size = int(font_size or 14)
        self.font_size_slider.setValue(initial_font_size)
        self.font_size_slider.valueChanged.connect(self.set_editor_font_size)
        top_layout.addWidget(self.font_size_slider)
        self.font_size_value_label = ui_qt.QtWidgets.QLabel(str(initial_font_size))
        attr_widget_base.configure_label_for_scaled_displays(self.font_size_value_label)
        self.font_size_value_label.setMinimumWidth(24)
        top_layout.addWidget(self.font_size_value_label)
        main_layout.addLayout(top_layout)

        self.python_edit = PythonCodeTextEdit()
        self.python_edit.setMinimumHeight(180)
        self.python_edit.setMinimumWidth(1)
        self.python_edit.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Expanding)
        self.python_edit.setPlainText(str(text or ""))
        self.python_edit.setPlaceholderText(str(placeholder or "Enter Python code."))
        self.python_edit.setToolTip(str(tooltip or "Python code executed by this task."))
        self.python_edit_font = ui_qt_utils.get_font(ui_res_lib.Font.roboto)
        self.python_edit.setFont(self.python_edit_font)
        self.python_edit.setStyleSheet(self.base_stylesheet)
        main_layout.addWidget(self.python_edit, 1)

        try:
            import gt.ui.syntax_highlighter as ui_syntax_highlighter

            self.highlighter = ui_syntax_highlighter.PythonSyntaxHighlighter(self.python_edit.document())
        except Exception:
            self.highlighter = None

        self.set_editor_font_size(initial_font_size)
        self.python_edit.textChanged.connect(self.on_text_changed)

    def get_text(self):
        """Gets the editor text.

        Returns:
            str: Current Python code.
        """
        if not self.python_edit:
            return ""
        return self.python_edit.toPlainText()

    def set_text(self, text):
        """Sets editor text.

        Args:
            text (str): New editor text.
        """
        if not self.python_edit:
            return
        self.python_edit.setPlainText(str(text or ""))

    def on_button_run_code_clicked(self):
        """Executes the Python code from the text editor."""
        import gt.utils.system as utils_sys

        utils_sys.execute_python_code(code=self.get_text(), import_cmds=True)
        self.emit_status_message("Executed Python editor code.")

    def set_editor_font_size(self, size):
        """Updates the Python editor font size.

        Args:
            size (int): New editor font size.
        """
        size = int(size or 14)
        if self.font_size_value_label:
            self.font_size_value_label.setText(str(size))
        if callable(self.font_size_changed_callback):
            self.font_size_changed_callback(size)
        self._update_editor_stylesheet(size)

    def _update_editor_stylesheet(self, font_size):
        """Applies font size and tab width to the Python editor.

        Args:
            font_size (int): Font size.
        """
        if not self.python_edit:
            return
        dynamic_stylesheet = self.base_stylesheet + "; font-size: {0}pt;".format(int(font_size or 14))
        self.python_edit.setStyleSheet(dynamic_stylesheet)
        font_metrics = ui_qt.QtGui.QFontMetrics(self.python_edit.font())
        if hasattr(font_metrics, "horizontalAdvance"):
            space_width = font_metrics.horizontalAdvance(" ")
        else:
            space_width = font_metrics.width(" ")
        try:
            self.python_edit.setTabStopWidth(space_width * 6)
        except Exception:
            self.python_edit.setTabStopDistance(space_width * 6)

    def on_save_clicked(self):
        """Saves the current editor contents to a Python file."""
        import gt.core.io as core_io

        file_path = ui_file_dialog.file_dialog(
            parent=self,
            write_mode=True,
            caption="Save Python Script",
            starting_directory=self.get_dialog_starting_directory(),
            file_filter="Python Files (*.py)",
        )
        if not file_path:
            return
        success = core_io.write_data(path=file_path, data=self.get_text())
        if success:
            self.emit_status_message("Saved Python script: {0}".format(file_path))
        else:
            self.emit_status_message("Warning: Failed to save script: {0}".format(file_path), status="warning")

    def on_load_clicked(self):
        """Loads a Python file into the editor."""
        import gt.core.io as core_io

        file_path = ui_file_dialog.file_dialog(
            parent=self,
            write_mode=False,
            caption="Open Python Script",
            starting_directory=self.get_dialog_starting_directory(),
            file_filter="Python Files (*.py)",
        )
        if not file_path:
            return
        content = core_io.read_data(path=file_path)
        if content is not None:
            self.python_edit.setText(content)
            self.on_text_changed()
            self.emit_status_message("Loaded Python script: {0}".format(file_path))
        else:
            self.emit_status_message("Warning: Failed to read script: {0}".format(file_path), status="warning")

    def on_insert_selection_clicked(self):
        """Inserts the current Maya selection as a Python list at the cursor."""
        try:
            import gt.core.selection as core_sel

            selection = core_sel.ensure_selection_count(selection_limit=None, require_exact_count=False)
        except Exception as exception:
            self.emit_status_message(
                "Warning: Unable to insert Maya selection: {0}".format(exception),
                status="warning",
            )
            return
        if selection and self.python_edit:
            cursor = self.python_edit.textCursor()
            cursor.insertText(repr(selection))

    def on_text_changed(self):
        """Stores the editor content through the configured callback."""
        if callable(self.text_changed_callback):
            self.text_changed_callback(self.get_text())
        if self.font_size_slider:
            self._update_editor_stylesheet(self.font_size_slider.value())
        if self.python_edit and self.python_edit_font:
            self.python_edit.setFont(self.python_edit_font)

    def get_dialog_starting_directory(self):
        """Gets a good starting folder for save/load dialogs.

        Returns:
            str: Existing directory path.
        """
        if self.owner and hasattr(self.owner, "get_dialog_starting_directory"):
            try:
                directory_path = self.owner.get_dialog_starting_directory()
                if directory_path and os.path.isdir(directory_path):
                    return directory_path
            except Exception:
                pass
        project = getattr(self.owner, "project", None)
        if project and hasattr(project, "get_project_dir"):
            directory_path = project.get_project_dir()
            if directory_path and os.path.isdir(directory_path):
                return directory_path
        return os.getcwd()

    def emit_status_message(self, message, status="info"):
        """Emits a status message through the owner when possible.

        Args:
            message (str): Message text.
            status (str, optional): Status level.
        """
        if self.owner and hasattr(self.owner, "emit_status_message"):
            self.owner.emit_status_message(message, status=status)
            return
        sys.stdout.write(str(message) + "\n")
