"""
Auto Rigger Notes Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleNotes(AttrWidget):
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

        # Main layout for this specific widget's content
        _layout = ui_qt.QtWidgets.QVBoxLayout()

        # Bottom Layout for Preferences/Data
        _layout_top = ui_qt.QtWidgets.QHBoxLayout()
        self.add_widget_code_data_editor(
            add_activation=False, add_order_editor=True, add_code_editor=False, layout=_layout_top
        )
        self.add_module_attr_widget_checkbox(attr_name="show_warning", layout=_layout_top, nice_name="  Show Warning")
        self.content_layout.addLayout(_layout_top)

        # Font Size Slider
        self.font_size_slider = self.add_module_attr_widget_int_slider(
            attr_name="font_size",
            layout=_layout_top,
            min_int=8,
            max_int=24,
        )
        self.font_size_slider.valueChanged.connect(self.set_editor_font_size)

        # Note Edit
        self.notes_edit = ui_qt.QtWidgets.QTextEdit()
        self.notes_edit.setHtml(self.module.get_notes())
        self.notes_edit.setPlaceholderText("Start typing your notes here...")
        _layout.addWidget(self.notes_edit)
        self.content_layout.addLayout(_layout)

        # --- Initial Refresh ---
        self.set_editor_font_size(self.module.font_size)
        self.notes_edit.textChanged.connect(self.on_notes_text_change)

    def on_notes_text_change(self):
        """Function used to update the module with the text found in the notes text field"""
        current_html = self.notes_edit.toHtml()
        self.module.set_notes(current_html)

    def set_editor_font_size(self, size):
        """
        Updates the base font size for the entire document using a QTextCursor,
        preserving all other rich text formatting.

        Args:
            size (int): The new font size from the slider.
        """
        original_cursor = self.notes_edit.textCursor()

        # Create a new cursor to modify the document
        modifier_cursor = self.notes_edit.textCursor()
        modifier_cursor.select(ui_qt.QtGui.QTextCursor.Document)

        # Create a format that ONLY specifies font size
        char_format = ui_qt.QtGui.QTextCharFormat()
        char_format.setFontPointSize(size)

        # Temporarily set the document's cursor to the one with the full selection
        self.notes_edit.setTextCursor(modifier_cursor)
        self.notes_edit.mergeCurrentCharFormat(char_format)

        # Restore the user's original cursor position and selection
        self.notes_edit.setTextCursor(original_cursor)

        # Update tab stop width based on the new font size
        font = self.notes_edit.font()
        font.setPointSize(size)
        font_metrics = ui_qt.QtGui.QFontMetrics(font)
        space_width = font_metrics.horizontalAdvance(" ")
        self.notes_edit.setTabStopWidth(space_width * 4)


# Corrective Base (Used by other AttrWidgets)
