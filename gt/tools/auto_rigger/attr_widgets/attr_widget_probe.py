"""
Auto Rigger Probe Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleProbe(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for a probe module. This is used as base for other probe modules.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)
        self._output_attr_path_widget = None

    def add_widget_probe_output_text_field(self):
        """Adds a line edit widget showing the output attribute path for the probe"""
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        label = ui_qt.QtWidgets.QLabel(f"Output Attribute Path:")
        self._output_attr_path_widget = ui_qt.QtWidgets.QLineEdit()
        self._output_attr_path_widget.setReadOnly(True)
        text_color = ui_res_lib.Color.RGB.purple_medium
        self._output_attr_path_widget.setStyleSheet(f"color: {text_color};")

        # Get Start Button
        copy_attr_path_clipboard_btn = ui_qt.QtWidgets.QPushButton("COPY TO CLIPBOARD")
        copy_attr_path_clipboard_btn.clicked.connect(self.copy_output_attr_path_to_clipboard)

        # Create Layout
        _layout.addWidget(label)
        _layout.addWidget(self._output_attr_path_widget)
        _layout.addWidget(copy_attr_path_clipboard_btn)
        self.scroll_content_layout.addLayout(_layout)
        self.refresh_output_attr_path_text_field()

    def refresh_output_attr_path_text_field(self):
        """Refreshes the output attribute path text field with updated data."""
        _attr_path = self.module.get_probe_output_attr_path()
        self._output_attr_path_widget.setText(_attr_path)

    def copy_output_attr_path_to_clipboard(self):
        """Copies the text content from the output attribute path to the clipboard"""
        _attr_path = self._output_attr_path_widget.text()
        utils_system.copy_to_clipboard(_attr_path)
        logger.info(f"Probe output attribute path copied to clipboard.")
