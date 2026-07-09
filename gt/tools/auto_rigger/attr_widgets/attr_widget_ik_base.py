"""
Auto Rigger IK Base Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleBaseIK(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Used for generic nodes with options to edit parents and proxies directly.

        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

    def add_setup_name_field(self):
        """
        Adds a setup name text field.
        Returns:
            ConfirmableQLineEdit or tuple: The created QLineEdit object or a tuple with all created QT elements.
        """
        return self.add_module_attr_widget_text_field(
            attr_name="setup_name",
            nice_name="Setup Name",
            tooltip="Determines the name of the system."
            "\nThis is used as prefix by a few of the setup elements."
            "\nIdeally it should be unique, and describe the purpose of this module."
            '\ne.g. "thumb", "leg", or "arm".',
        )
