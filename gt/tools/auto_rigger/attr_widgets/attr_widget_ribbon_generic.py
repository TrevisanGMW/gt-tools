"""
Auto Rigger Ribbon Generic Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_ribbon_base import *

class AttrWidgetModuleRibbonGeneric(AttrWidgetModuleBaseRibbon):
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
        self.add_widget_module_orientation()
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()
        # --------------------------------------- Ribbon Preferences ---------------------------------------
        self.add_widget_separator_line(label_text="Ribbon Preferences")
        # Naming
        self.setup_name_field = None  # Created by "add_setup_name_text_field"
        self.add_setup_name_text_field()
        # Rotation Order
        self.add_module_rot_order_combobox()
        # Checkboxes
        self.refresh_mid_proxies_checkbox = None  # Created by "add_ribbon_checkboxes"
        self.add_ribbon_checkboxes()
        # Sliders
        self.ribbon_num_slider = None  # Created by "add_ribbon_sliders"
        self.ctrls_slider_widget = None  # Created by "add_ribbon_sliders"
        self.add_ribbon_sliders()
        # Shapes
        self.add_ribbon_shapes_text_fields()
        # Action Buttons
        self.add_widget_action_buttons()
        # Initial Refresh
        self.refresh_proxies_num(slider=self.ribbon_num_slider)
        self.refresh_proxy_names(field=self.setup_name_field)
