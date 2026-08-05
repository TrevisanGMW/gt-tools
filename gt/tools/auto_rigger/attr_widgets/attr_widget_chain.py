"""
Auto Rigger Chain Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleChain(AttrWidget):
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
        self.add_widget_separator_line(label_text="Chain Preferences")
        self.add_widget_auto_serialized_fields(
            ignore_attrs=["setup_name", "chain_base_name", "chain_num", "rot_order", "ctrl_shapes"]
        )
        setup_name_field = self.add_module_attr_widget_text_field(attr_name="setup_name", nice_name="Setup Name")
        refresh_name_func = partial(self.refresh_name, field=setup_name_field)
        setup_name_field.textEdited.connect(refresh_name_func)
        self.refresh_mid_proxies_checkbox = self.add_module_attr_widget_checkbox(
            attr_value=False,
            nice_name="Middle Proxies Refresh",
            tooltip="Toggles on and off the refresh of the middle proxies",
        )
        chain_num_slider = self.add_module_attr_widget_int_slider(
            attr_name="chain_num",
            min_int=0,
            nice_name="Chain Divisions",
            tooltip="Number of chain divisions.",
        )
        refresh_proxies_func = partial(self.refresh_proxies, slider=chain_num_slider)
        chain_num_slider.intValueChanged.connect(refresh_proxies_func)
        rot_order_slider = self.add_module_attr_widget_int_slider(
            attr_name="rot_order",
            min_int=0,
            max_int=5,
            nice_name="Rotation Order",
            tooltip="Rotation order of the joints and controls.",
        )
        refresh_rot_func = partial(self.refresh_rot_order, slider=rot_order_slider)
        rot_order_slider.intValueChanged.connect(refresh_rot_func)
        self.add_module_attr_widget_text_field(attr_name="ctrl_shapes", nice_name="Ctrl Shapes")

        self.add_widget_action_buttons()

        # Initial Refresh
        self.refresh_proxies(slider=chain_num_slider)
        self.refresh_rot_order(slider=rot_order_slider)
        self.refresh_name(field=setup_name_field)

    def refresh_proxies(self, *args, slider):
        """
        Refresh the proxies based on the slider value.

        Args:
            *args: Additional positional arguments (ignored).
            slider (QSlider): Slider controlling the number of proxies in the chain.
        """
        if slider:
            # set chain number
            chain_number = int(slider.int_value())
            self.module.set_chain_num(chain_number)
            chain_base_item = tools_rig_utils.find_proxy_from_uuid(self.module.chain_base_proxy.get_uuid())
            if chain_base_item:
                if self.refresh_mid_proxies_checkbox.isChecked():
                    self.module._refresh_middle_proxies = True
            # refresh interface
            self.refresh_proxy_basic_table()

    def refresh_rot_order(self, *args, slider):
        """
        Refresh the rotation order of the module based on the slider value.

        Args:
            *args: Additional positional arguments (ignored).
            slider (QSlider): Slider controlling the rotation order.
        """
        if slider:
            # set rot order
            rot_order = int(slider.int_value())
            self.module.set_rot_order(rot_order)
            # refresh interface
            self.refresh_proxy_basic_table()

    def refresh_name(self, *args, field):
        """
        Refresh the proxy names based on the text field content.

        Args:
            *args: Additional positional arguments (ignored).
            field (QLineEdit): Text field containing the new proxy name.
        """
        if field:
            module_name = field.text()
            self.module.set_proxies_name(module_name)
            self.refresh_proxy_basic_table()


# Ribbon Base (Used by other AttrWidgets)
