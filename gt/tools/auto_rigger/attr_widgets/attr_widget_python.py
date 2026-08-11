"""
Auto Rigger Python Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *
from gt.ui.line_text_widget import apply_text_font_size
from gt.ui.line_text_widget import LineTextWidget

class AttrWidgetModulePython(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()

        _layout = ui_qt.QtWidgets.QVBoxLayout()
        self.content_layout.addLayout(_layout)

        _layout_top_prefs = ui_qt.QtWidgets.QHBoxLayout()

        self.add_widget_code_data_editor(
            add_activation=False, add_order_editor=True, add_code_editor=False, layout=_layout_top_prefs
        )

        # Get Basic Items
        code_data = self.module.get_code_data()

        _value = code_data.get_execution_code()

        # Font Size
        _layout.addLayout(_layout_top_prefs)
        self.font_size_slider = self.add_module_attr_widget_int_slider(
            attr_name="font_size",
            layout=_layout_top_prefs,
            min_int=8,
            max_int=24,
        )
        self.font_size_slider.valueChanged.connect(self.set_editor_font_size)

        # Python Edit
        self.python_editor_widget = LineTextWidget(
            parent=self,
            text_edit=ui_qt.QtWidgets.QTextEdit(),
        )
        self.python_edit = self.python_editor_widget.get_text_edit()
        _layout.addWidget(self.python_editor_widget)
        self.python_edit.setPlaceholderText("Write Python code to run when this module executes.")
        self.python_edit.setText(_value)
        self.base_stylesheet = ""  # In case we want to add something later
        self.python_edit.setStyleSheet(self.base_stylesheet)
        self.python_edit_font = ui_qt_utils.get_font(ui_res_lib.Font.roboto)
        self.python_edit.setFont(self.python_edit_font)
        initial_font_size = self.module.font_size
        self.python_edit.setFontPointSize(initial_font_size)

        import gt.ui.syntax_highlighter as ui_syntax_highlighter

        self.highlighter = ui_syntax_highlighter.PythonSyntaxHighlighter(self.python_edit.document())

        # Run Button
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        run_code_btn = ui_qt.QtWidgets.QPushButton("Run Code")
        run_code_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.dev_code))
        run_code_btn.setToolTip("Execute the Python code in the text editor.")
        run_code_btn.clicked.connect(self.on_button_run_code_clicked)
        _layout.addWidget(run_code_btn)

        # Insert Selection Button
        insert_selection_btn = ui_qt.QtWidgets.QPushButton("Insert Selection")
        insert_selection_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.dev_filter))
        insert_selection_btn.setToolTip("Inserts the current selection as a Python list at the cursor.")
        insert_selection_btn.clicked.connect(self.on_insert_selection_clicked)
        _layout.addWidget(insert_selection_btn)

        # Save Button
        save_btn = ui_qt.QtWidgets.QPushButton("Save")
        save_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_save))
        save_btn.setToolTip("Save the current script to a file.")
        save_btn.clicked.connect(self.on_save_clicked)
        _layout.addWidget(save_btn)

        # Load Button
        load_btn = ui_qt.QtWidgets.QPushButton("Load")
        load_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        load_btn.setToolTip("Load a script from a file.")
        load_btn.clicked.connect(self.on_load_clicked)
        _layout.addWidget(load_btn)

        self.content_layout.addLayout(_layout)

        # Initial Refresh
        self.set_editor_font_size(initial_font_size)
        self._update_editor_stylesheet(initial_font_size)
        self.python_edit.textChanged.connect(self.on_text_changed)

    def on_button_run_code_clicked(self):
        """
        Executes the Python code from the text editor when the 'Run Code' button is clicked.


        """
        import gt.utils.system as utils_sys

        utils_sys.execute_python_code(code=self.python_edit.toPlainText(), import_cmds=True)

    def set_editor_font_size(self, size):
        """
        Updates the font size of the python text editor when the slider value changes.

        Args:
            size (int): The new font size from the slider.
        """
        font_size = int(size or 14)
        self.python_edit_font.setPointSize(font_size)
        self.python_edit.setFont(self.python_edit_font)
        apply_text_font_size(self.python_edit, font_size)
        self._update_editor_stylesheet(font_size)
        self.python_editor_widget.number_bar.setFont(self.python_edit.font())
        self.python_editor_widget.number_bar.update()

    def _update_editor_stylesheet(self, font_size):
        """
        Constructs and applies the full stylesheet for the Python text editor.

        Args:
            font_size (int): The font size to include in the stylesheet.
        """
        dynamic_stylesheet = self.base_stylesheet + f"; font-size: {font_size}pt;"
        self.python_edit.setStyleSheet(dynamic_stylesheet)

        # 2. Update the tab stop width to equal 4 spaces in the new font size
        font_metrics = ui_qt.QtGui.QFontMetrics(self.python_edit.font())
        space_width = font_metrics.horizontalAdvance(" ")
        try:
            self.python_edit.setTabStopWidth(space_width * 6)  # For some reason 6 aligns better in this font.
        except Exception as e:
            logger.debug(e)
            self.python_edit.setTabStopDistance(space_width * 6)  # For some reason 6 aligns better in this font.


    def on_save_clicked(self):
        """
        Opens a custom file dialog to save the content of the text editor.

        Uses the core_io module to handle the file writing.
        """
        file_path = ui_file_dialog.file_dialog(
            write_mode=True, caption="Save Python Script", file_filter="Python Files (*.py)"
        )

        if not file_path:
            return  # User cancelled the dialog

        content = self.python_edit.toPlainText()
        success = core_io.write_data(path=file_path, data=content)

        if not success:
            logger.error(f"Failed to save script to {file_path}")

    def on_load_clicked(self):
        """
        Opens a custom file dialog to load a .py file into the text editor.

        Uses the core_io module to handle the file reading.
        """
        file_path = ui_file_dialog.file_dialog(
            write_mode=False, caption="Open Python Script", file_filter="Python Files (*.py)"
        )

        if not file_path:
            return  # User cancelled the dialog

        content = core_io.read_data(path=file_path)

        if content is not None:
            self.python_edit.setText(content)
        else:
            logger.error(f"Failed to read script from {file_path}")

        self.on_text_changed()  # Refresh

    def on_insert_selection_clicked(self):
        """
        Gets the current Maya selection and inserts it as a formatted Python list
        at the cursor's current position in the text editor.
        """
        import gt.core.selection as core_sel

        selection = core_sel.ensure_selection_count(
            selection_limit=None,
            require_exact_count=False,
        )
        if selection:
            # The 'repr' function is great here as it ensures strings have quotes
            formatted_selection = repr(selection)

            cursor = self.python_edit.textCursor()
            cursor.insertText(formatted_selection)

    def on_text_changed(self):
        """
        Automatically saves the editor's content to the module's code data.
        """
        current_code = self.python_edit.toPlainText()
        self.module.set_execution_code(current_code)

        if self.font_size_slider:
            self._update_editor_stylesheet(self.font_size_slider.value())
        if self.python_edit_font:
            self.python_edit.setFont(self.python_edit_font)
