"""
Auto Rigger Common Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetCommon(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Used for modules that are missing a proper unique AttrWidget.
        The "AttrWidgetCommon" will show all proxies (with the edit options)
        And automatically list all available attributes.

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
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()
        self.add_widget_auto_serialized_fields()
        self.add_widget_action_buttons()


# -------------------------------------------------- Modules --------------------------------------------------
