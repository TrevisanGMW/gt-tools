"""
Auto Rigger Anim Mass References Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleAnimMassReferences(AttrWidget):
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
        self.add_widget_separator_line(label_text="Animation Mass References Preferences")

        attributes = vars(self.module)
        weight_attrs = [attr for attr in attributes if attr.endswith("_weight")]
        color_attrs = [attr for attr in attributes if attr.endswith("_color")]

        self.add_module_attr_widget_int_slider(
            attr_name="com_locator_scale",
            attr_value=None,
            min_int=1,
            max_int=50,
            tooltip="Size of the center of mass locator.",
        )

        self.add_widget_auto_serialized_fields(ignore_attrs=weight_attrs + color_attrs + ["com_locator_scale"])

        for attr in weight_attrs:
            self.add_module_attr_widget_double_slider(
                attr_name=attr,
                min_double=0,
                max_double=50,
                precision=3,
            )

        for attr in color_attrs:
            self.add_module_attr_widget_double3_spinbox(
                attr_name=attr,
                precision=3,
            )
