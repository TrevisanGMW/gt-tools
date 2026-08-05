"""
Auto Rigger Ribbon Base Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleBaseRibbon(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.setup_name_field = None  # Created by "add_setup_name_text_field"
        self.refresh_mid_proxies_checkbox = None  # Created by "add_ribbon_checkboxes"
        self.ribbon_num_slider = None  # Created by "add_ribbon_sliders"
        self.ctrls_slider_widget = None  # Created by "add_ribbon_sliders"

    def add_setup_name_text_field(self, layout=None):
        """
        Adds a setup name text field and a checkbox to control auto-renaming.
        Args:
            layout (QLayout): A layout to parent the setup name to. Default is None.
        Returns:
            ConfirmableQLineEdit: The "setup_name" textfield QT object.
        """
        # Create a horizontal layout to hold the text field and checkbox
        name_layout = ui_qt.QtWidgets.QHBoxLayout()
        name_layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B

        self.setup_name_field = self.add_module_attr_widget_text_field(
            attr_name="setup_name",
            nice_name="Setup Name",
            tooltip="Determines the base name of the ribbon and its proxies.",
            layout=name_layout,  # Add to the new horizontal layout
        )
        refresh_name_func = partial(self.refresh_proxy_names, field=self.setup_name_field)
        self.setup_name_field.textEdited.connect(refresh_name_func)

        self.add_module_attr_widget_checkbox(
            attr_name="proxy_inherit_name",  # The attribute on the module
            nice_name="Auto-rename Proxies",
            layout=name_layout,
            tooltip="When checked, changing the 'Setup Name' will automatically\n"
            "rename all proxies (e.g., 'mySetupBase').\n"
            "Uncheck this to manually rename proxies without them being overwritten.",
        )

        # Add the horizontal layout to the main content layout
        self.content_layout.addLayout(name_layout)

        return self.setup_name_field

    def add_ribbon_checkboxes(self, add_equidistant=True):
        """
        Adds checkboxes used to determine th preferences for a ribbon.
        Args:
            add_equidistant (bool, optional): Whether to include the "Equidistant" checkbox.
        """
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.refresh_mid_proxies_checkbox = self.add_module_attr_widget_checkbox(
            attr_name="middle_proxies_reset",
            nice_name="Middle Proxies Reset",
            layout=_layout,
            tooltip="When enabled, the positions of the middle proxies will be reset to maintain equal "
            "spacing whenever the number of divisions changes.\nThis behavior ensures consistent positioning and "
            "prevents unintended offsets from previous proxy data.\nIf you prefer to preserve all existing "
            "proxy positions regardless of division count updates, disable this option.",
        )
        self.add_module_attr_widget_checkbox(
            attr_name="cable_ctrls",
            attr_value=None,
            nice_name="Cable Controls",
            layout=_layout,
            tooltip="When active, FK controls remain independent allowing them to more easily act as a cable.\n"
            "This setup can help a ribbon be controlled by multiple parents where the start and end controls "
            "can follow different objects independently.",
        )
        if add_equidistant:
            self.add_module_attr_widget_checkbox(
                attr_name="equidistant",
                attr_value=None,
                nice_name="Equidistant",
                layout=_layout,
                tooltip="When active, an extra equidistant setup is added to the FK controls of the ribbon.\n"
                "This setup makes it so the global and effector controls influence the FK controls.\n"
                "This behavior can be controlled through an influence attribute added to the ribbon global control.\n"
                "The standard FK behavior will still happen when the equidistant influence is deactivated.",
            )
        self.add_module_attr_widget_checkbox(
            attr_name="rotate_ribbon",
            attr_value=None,
            nice_name="Rotate Ribbon",
            layout=_layout,
            tooltip="When active, the generated ribbon is rotated 90 degrees.\n"
            "A rotated ribbon will output slightly different rotation priorities to the skin joints.\n"
            "This happens because being a plane, the ribbon rotation determines how the curvature is interpreted.\n"
            "e.g. It might move parallel to one another or aim towards one another.",
        )
        self.content_layout.addLayout(_layout)

    def add_ribbon_sliders(self):
        """
        Adds sliders used to determine the number of divisions and controls in a ribbon.
        """
        _min_divisions_int = 1
        _max_divisions_int = 25
        self.ribbon_num_slider = self.add_module_attr_widget_int_slider(
            attr_name="divisions",
            min_int=_min_divisions_int,
            max_int=_max_divisions_int,
            nice_name="Number of Mid Joints",
            tooltip="Determines how many divisions the middle of the ribbon should have, "
            "which also determines the number of skinning middle.\n"
            "(Start and End joints are not counted in this number)",
        )
        refresh_proxies_func = partial(self.refresh_proxies_num, slider=self.ribbon_num_slider)
        self.ribbon_num_slider.intValueChanged.connect(refresh_proxies_func)
        self.ribbon_num_slider.intValueChanged.connect(self.refresh_max_ctrl_num)

        self.ctrls_slider_widget = self.add_module_attr_widget_int_slider(
            attr_name="num_ctrls",
            min_int=_min_divisions_int,
            max_int=_max_divisions_int,
            nice_name="Number of Mid Controls",
            tooltip="Determines the number of in-between controls generated by the ribbon.\n"
            "(Start and End controls are not counted in this number)",
        )
        refresh_ctrls_func = partial(self.refresh_num_ctrls, slider=self.ctrls_slider_widget)
        self.ctrls_slider_widget.intValueChanged.connect(self.refresh_max_ctrl_num)
        self.ctrls_slider_widget.intValueChanged.connect(refresh_ctrls_func)

        self.add_module_attr_widget_int_slider(
            attr_name="span_multiplier",
            min_int=1,
            max_int=10,
            nice_name="Span Multiplier",
            tooltip="Multiplies the number of spans on a generated ribbon.\n"
            "More spans can give the user more precise control over the skin weight of the ribbon.\n"
            "This can be used to create harder transitions between one control and another for different effects.",
        )

    def add_ribbon_shapes_text_fields(self):
        """Adds text-field responsible for the shapes used by this ribbon"""
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.add_module_attr_widget_text_field(attr_name="fk_ctrl_shapes", nice_name="FK Ctrl Shapes", layout=_layout)
        self.add_module_attr_widget_text_field(attr_name="ik_ctrl_shapes", nice_name="IK Ctrl Shapes", layout=_layout)
        self.content_layout.addLayout(_layout)

    def refresh_proxies_num(self, *args, slider):
        """
        Refreshes the proxy data and table to reflect updated preferences, specifically, the number of proxies.
        Args:
            slider (QSlider): Slider used to determine the number of divisions.
        """
        if slider and core_session.is_script_in_interactive_maya():
            # Set ribbon number
            divisions_num = int(slider.int_value())
            self.module.set_divisions_num(divisions=divisions_num)
            # Marking refresh middle proxies
            ribbon_base_item = tools_rig_utils.find_proxy_from_uuid(self.module.base_proxy.get_uuid())
            if ribbon_base_item:
                if self.refresh_mid_proxies_checkbox.isChecked():
                    self.module.middle_proxies_reset = True
            # Update num ctrls to not overpass divisions
            widget_num_ctrls = self.ctrls_slider_widget.value()
            if widget_num_ctrls > self.module.divisions:
                self.ctrls_slider_widget.set_int_value(self.module.divisions)
            # Refresh interface
            self.refresh_proxy_basic_table()

    def refresh_num_ctrls(self, *args, slider):
        """
        Refreshes the number of controls
        Args:
            slider (QSlider): QSlider used to extract the new number of controls.
        """
        if slider:
            widget_num_ctrls = int(slider.int_value())
            if widget_num_ctrls > self.module.divisions:
                slider.blockSignals(True)
                slider.set_int_value(self.module.divisions)
                slider.linked_spin_box.setValue(self.module.divisions)
                slider.blockSignals(False)

    def refresh_proxy_names(self, *args, field):
        """
        Refreshes the name of the proxies of this module. So they can be displayed in the UI.
        Args:
            field (QLineEdit): A field to get the name of the setup from.
        """
        if not args:  # Only run if triggered by a signal that sends arguments
            return

        if not self.module.proxy_inherit_name:
            return  # Exit early if auto-rename is off

        if field:
            module_name = field.text()
            self.module.set_proxies_name(module_name)
            self.refresh_proxy_basic_table()

    def refresh_max_ctrl_num(self):
        """Force the num of controls to be less than the number of divisions"""
        ribbon_num_slider_int = int(self.ribbon_num_slider.int_value())
        ctrls_slider_widget_int = int(self.ctrls_slider_widget.int_value())
        if ctrls_slider_widget_int > ribbon_num_slider_int:
            self.ctrls_slider_widget.set_int_value(ribbon_num_slider_int)
