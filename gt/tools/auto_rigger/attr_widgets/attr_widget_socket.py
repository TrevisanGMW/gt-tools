"""
Auto Rigger Socket Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleSocket(AttrWidget):
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
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()

        self.add_widget_separator_line(label_text="Socket Preferences")

        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.content_layout.addLayout(_layout)

        _checkbox = self.add_module_attr_widget_checkbox(attr_name="add_child", layout=_layout)
        parent_text_field = self.add_module_attr_widget_text_field(attr_name="parent_tag", layout=_layout)
        child_text_field = self.add_module_attr_widget_text_field(attr_name="child_tag", layout=_layout)

        _layout.setEnabled(_checkbox.isChecked())
        # Create Enabled Connection
        _checkbox.stateChanged.connect(parent_text_field.setEnabled)
        _checkbox.stateChanged.connect(child_text_field.setEnabled)

        self.add_widget_action_buttons()
