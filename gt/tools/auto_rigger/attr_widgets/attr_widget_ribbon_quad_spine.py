"""
Auto Rigger Ribbon Quad Spine Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_ribbon_base import *

class AttrWidgetModuleRibbonQuadSpine(AttrWidgetModuleBaseRibbon):
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

        # ------------------------------------ Quadruped Spine Preferences ------------------------------------
        self.add_widget_separator_line(label_text="Quadruped Spine Preferences")
        # Naming
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.setup_name_field = self.add_setup_name_text_field(layout=_layout)
        self.add_module_attr_widget_text_field(
            attr_name="direction_name",
            nice_name="Direction Name",
            tooltip="Determines the name of the direction control.",
            layout=_layout,
        )
        self.setup_name_field.textEdited.connect(self.refresh_proxy_names)
        self.content_layout.addLayout(_layout)
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.base_field = self.add_module_attr_widget_text_field(
            attr_name="hips_name",
            nice_name="Hips Name (Base)",
            tooltip="Determines the name of the base control. In this case the hips of the spine.",
            layout=_layout,
        )
        self.end_field = self.add_module_attr_widget_text_field(
            attr_name="chest_name",
            nice_name="Chest Name (End)",
            tooltip="Determines the name of the end control. In this case the chest of the spine.",
            layout=_layout,
        )
        self.content_layout.addLayout(_layout)
        self.base_field.textEdited.connect(self.refresh_proxy_names)
        self.end_field.textEdited.connect(self.refresh_proxy_names)
        # Rotation Order
        self.add_module_rot_order_combobox()
        # Checkboxes
        self.refresh_mid_proxies_checkbox = None  # Created by "add_ribbon_checkboxes"
        self.add_ribbon_checkboxes(add_equidistant=False)
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
        self.refresh_proxy_names()

    def refresh_proxy_names(self, *args, **kwargs):
        """
        Refreshes the name of the proxies of this module, so they can be displayed in the UI.
        This is an override function made specifically for the quadruped spine module.
        """
        setup_name = self.setup_name_field.text()
        base_name = self.base_field.text()
        end_name = self.end_field.text()
        self.module.set_proxies_name(setup_name=setup_name, base=base_name, end=end_name)
        self.refresh_proxy_basic_table()
