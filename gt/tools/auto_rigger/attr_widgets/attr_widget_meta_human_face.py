"""
Auto Rigger Meta Human Face Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleMetaHumanFace(AttrWidget):
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
        self.add_widget_module_parent()
        self.add_widget_code_data_editor()
        self.add_widget_separator_line(label_text="MetaHuman Face Preferences")
        self.add_widget_auto_serialized_fields(ignore_attrs="file_path")
        self.add_module_attr_widget_path(attr_name="file_path")
        self.add_widget_action_buttons()
