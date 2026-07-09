"""
Auto Rigger Generic Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleGeneric(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Used for generic nodes with options to edit parents and proxies directly.

        Args:
            parent (QWidget): The parent widget.
            module: The module associated with this widget.
            project: The project associated with this widget.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_orientation()
        self.add_widget_code_data_editor(add_activation=True, add_order_editor=True, add_code_editor=True)
        self.add_widget_proxy_parent_table()
        self.add_widget_action_buttons()
