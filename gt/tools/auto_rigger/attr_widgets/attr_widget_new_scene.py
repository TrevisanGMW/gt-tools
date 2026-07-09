"""
Auto Rigger New Scene Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleNewScene(AttrWidget):
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
        self.add_widget_code_data_editor()
        code_editor_tooltip = """Use the default dictionary as an example of potential scene options."""

        self.add_widget_separator_line(label_text="New Scene Preferences")

        self.add_module_attr_widget_dictionary_editor(
            attr_name="scene_options", dict_editor_tooltip=code_editor_tooltip
        )
