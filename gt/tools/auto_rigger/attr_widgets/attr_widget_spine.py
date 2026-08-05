"""
Auto Rigger Spine Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleSpine(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)
        self._cog_parent_combobox = None

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_orientation()
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()
        self.add_widget_separator_line(label_text="Spine Preferences")
        self.add_widget_auto_serialized_fields(
            ignore_attrs=["spine_number", "dropoff_rate", "cog_parent", "world_ctrls"]
        )  # those have specific ranges
        spine_num_slider = self.add_module_attr_widget_int_slider(
            attr_name="spine_number",
            min_int=1,
            tooltip="Number of spine elements between the hip and the chest.",
        )
        refresh_proxies_func = partial(self.refresh_proxies, slider=spine_num_slider)
        spine_num_slider.intValueChanged.connect(refresh_proxies_func)
        self.add_module_attr_widget_double_slider(
            attr_name="dropoff_rate",
            min_double=0.1,
            max_double=10,
            tooltip="Dropoff value applied to the spine ribbon skin weights.",
        )
        self.add_module_attr_widget_checkbox(
            attr_name="world_ctrls",
            nice_name="World Oriented Ctrls",
            tooltip="Sets the spine ctrls in world orientation.",
        )
        self.add_cog_parent_combobox()
        self.add_widget_action_buttons()

    def refresh_proxies(self, *args, slider):
        """
        Refreshes the proxies based on the value from the provided slider.

        Args:
            *args: Additional arguments (ignored).
            slider (QtSlider or similar): Slider widget providing the spine number value.
        """
        if slider:
            # set spine number
            spine_number = int(slider.int_value())
            self.module.set_spine_number(spine_number)
            # refresh interface
            self.refresh_proxy_basic_table()

    def add_cog_parent_combobox(self, cog_parent_attr="cog_parent"):
        """
        Adds a combo box widget to select an alternative parent for the COG control.

        The combo box is populated with potential driver options, including a 'No Parent Override' choice.
        It sets the current selection based on the module's current attribute value and connects a handler
        to respond to user changes.

        Args:
            cog_parent_attr (str): The attribute name on the module representing the current COG parent.
                                   Defaults to "cog_parent".
        """
        # Create Layout
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.content_layout.addLayout(_layout)
        # Create Widgets
        label = ui_qt.QtWidgets.QLabel(f"COG Parent:")
        label.setSizePolicy(ui_qt.QtLib.SizePolicy.Fixed, ui_qt.QtLib.SizePolicy.Preferred)
        self._cog_parent_combobox = ui_qt.QtWidgets.QComboBox()
        self._cog_parent_combobox.setFixedHeight(30)
        tooltip = "Determines an alternative parent for the COG control"
        label.setToolTip(tooltip)
        self._cog_parent_combobox.setToolTip(tooltip)
        # Populate ComboBox
        driver_pairs = self.get_potential_drivers_list(as_nice_name_pairs=True)
        driver_pairs.insert(0, [None, "No Parent Override"])  # Add None item (No Parent)
        for index, (driver_uuid, nice_name) in enumerate(driver_pairs):
            self._cog_parent_combobox.addItem(nice_name)  # Add the nice name
            self._cog_parent_combobox.setItemData(index, driver_uuid)  # Attach the internal value
        # Get Current Value And Set Combobox
        _module_value = getattr(self.module, cog_parent_attr)
        self.set_cog_parent_combobox(_module_value)
        # Add to Widgets
        _layout.addWidget(label)
        _layout.addWidget(self._cog_parent_combobox)
        # Connect
        self._cog_parent_combobox.currentIndexChanged.connect(self.on_cog_parent_combobox_change)

    def on_cog_parent_combobox_change(self, index):
        """
        If the COG parent combobox changes, it updates the module variable value according to the driver_uuid value.
        Args:
            index: Index the combobox was changed to
        """
        internal_value = self._cog_parent_combobox.itemData(index)
        setattr(self.module, "cog_parent", internal_value)

    def set_cog_parent_combobox(self, driver_uuid):
        """
        Sets the value of the COG Parent combobox
        Args:
            driver_uuid: The UUID to set. If unavailable, it will force add it.
        """
        # Loop through the items to find the one with matching internal value
        for index in range(self._cog_parent_combobox.count()):
            if self._cog_parent_combobox.itemData(index) == driver_uuid:
                self._cog_parent_combobox.setCurrentIndex(index)
                return

        # If the value is not found, add it as a new item
        logger.warning(f'Driver "{driver_uuid}" was not available as an option but was force added.')
        self._cog_parent_combobox.addItem(driver_uuid)  # Use the internal value as the "nice name"
        new_index = self._cog_parent_combobox.count() - 1
        self._cog_parent_combobox.setItemData(new_index, driver_uuid)  # Attach the internal value
        self._cog_parent_combobox.setCurrentIndex(new_index)  # Set the new item as the current index
