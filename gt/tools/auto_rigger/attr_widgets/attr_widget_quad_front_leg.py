"""
Auto Rigger Quad Front Leg Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleQuadFrontLeg(AttrWidget):
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
        self.add_widget_separator_line(label_text="Quad Front Leg Preferences")
        self.add_widget_auto_serialized_fields(
            ignore_attrs=[
                "setup_name",
                "dir_rot",
                "upperleg_dir_curve",
                "lowerleg_dir_curve",
                "dir_curve",
            ]
        )
        setup_name_field = self.add_module_attr_widget_text_field(attr_name="setup_name", nice_name="Setup Name")
        refresh_name_func = partial(self.refresh_name, field=setup_name_field)
        self.add_widget_action_buttons()

    def refresh_name(self, *args, field):
        """
        Update the module's proxies name based on the text from the given input field
        and refresh the proxy table UI.

        Args:
            *args: Additional positional arguments (ignored).
            field (QLineEdit): The text input widget containing the new proxy name.
        """
        if field:
            module_name = field.text()
            self.module.set_proxies_name(module_name)
            self.refresh_proxy_basic_table()
