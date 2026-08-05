"""
Auto Rigger Piston Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModulePiston(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """

        super().__init__(parent, *args, **kwargs)
        self._end_parent_combobox = None

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_parent()
        self.add_widget_module_end_combobox()
        self.add_widget_proxy_basic_table()
        self.add_widget_separator_line(label_text="Piston Preferences")

        name_layout = ui_qt.QtWidgets.QHBoxLayout()
        name_layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B

        self.setup_name_field = self.add_module_attr_widget_text_field(
            attr_name="setup_name",
            nice_name="Setup Name",
            tooltip="Determines the base name of the piston and its proxies.",
            layout=name_layout,
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

        self.add_module_attr_widget_text_field(attr_name="ctrl_shapes", nice_name="Control Shape")

        self.add_module_attr_widget_checkbox(
            attr_name="parent_end_joint",
            nice_name="Parent End Joint to Base Joint",
            tooltip="When checked, it will parent the end joint to the base joint.",
        )
        self.add_widget_action_buttons()
        self.refresh_proxy_names(field=self.setup_name_field)

    def add_widget_module_end_combobox(self):
        """
        Adds a combo box widget to select an alternative parent for the end piston ctrl.

        The combo box is populated with potential driver options, including a 'No Parent Override' choice.
        It sets the current selection based on the module's current attribute value and connects a handler
        to respond to user changes.

        """
        # Create Layout
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.content_layout.addLayout(_layout)
        # Create Widgets
        label = ui_qt.QtWidgets.QLabel(f"End Ctrl Parent:")
        label.setSizePolicy(ui_qt.QtLib.SizePolicy.Fixed, ui_qt.QtLib.SizePolicy.Preferred)
        self._end_parent_combobox = ui_qt.QtWidgets.QComboBox()
        self._end_parent_combobox.setFixedHeight(30)
        tooltip = "Determines an alternative parent for the End Piston control"
        label.setToolTip(tooltip)
        self._end_parent_combobox.setToolTip(tooltip)
        # Populate ComboBox
        driver_pairs = self.get_potential_parent_list(target=self.module)
        driver_pairs.insert(0, ["No Parent Override", None])  # Add None item (No Parent)
        for index, (nice_name, driver) in enumerate(driver_pairs):
            self._end_parent_combobox.addItem(nice_name)  # Add the nice name
            self._end_parent_combobox.setItemData(index, driver)  # Attach the internal value
        # Get Current Value And Set Combobox
        _module_value = getattr(self.module, "end_parent")
        self.set_end_parent_combobox(driver_uuid=_module_value)
        # Add to Widgets
        _layout.addWidget(label)
        _layout.addWidget(self._end_parent_combobox)
        # Connect
        self._end_parent_combobox.currentIndexChanged.connect(self.on_end_parent_piston_combo_box_changed)

    def on_end_parent_piston_combo_box_changed(self, index):
        """
        Handle the change in the parent combo box for the proxy table.

        Args:
            index (int): Index of the selected item.
        """
        internal_value = self._end_parent_combobox.itemData(index)
        end_parent_uuid = internal_value.get_uuid()
        setattr(self.module, "end_parent", end_parent_uuid)

    def set_end_parent_combobox(self, driver_uuid):
        """
        Sets the value of the COG Parent combobox
        Args:
            driver_uuid: The UUID to set. If unavailable, it will force add it.
        """
        # Loop through the items to find the one with matching internal value
        self.refresh_known_proxy_dict()
        for index in range(1, self._end_parent_combobox.count()):
            _parent_proxy = self._end_parent_combobox.itemData(index)
            _parent_uuid = _parent_proxy.get_uuid()
            if driver_uuid == _parent_uuid:
                self._end_parent_combobox.setCurrentIndex(index)
                return

        # If the value is not found, add it as a new item
        logger.warning(f'Driver "{driver_uuid}" was not available as an option.')
        self._end_parent_combobox.setCurrentIndex(0)

    def get_potential_parent_list(self, target, parent_filter=False):
        """
        Gets all potential parent targets.
        An extra initial item called "No Parent" is also added for the proxies without parents.
        Args:
            target (Proxy, Module): A proxy or module object used to determine current parent and pre-select it.
            parent_filter (bool, optional): If True, it will only populate the combobox with proxies available under
                                          the parent modules.
        Returns:
            QComboBox: A pre-populated combobox with potential parents. Current parent is also pre-selected.
        """
        self.refresh_known_proxy_dict()
        drivers_list = []
        # Get Variables
        _proxy_uuid = None
        if target and hasattr(target, "get_uuid"):  # Is proxy
            _proxy_uuid = target.get_uuid()
        _proxy_parent_uuid = target.get_parent_uuid()
        _parent_module = self.known_proxies.get(_proxy_parent_uuid, None)
        if _parent_module:
            _parent_module = _parent_module[1]  # Get second item in tuple (module)
        # Populate Combobox
        for key, (_proxy, _module) in self.known_proxies.items():
            if parent_filter and _parent_module and _parent_module != _module:
                continue
            if key == _proxy_uuid:
                continue  # Skip Itself
            description = f"{str(_proxy.get_name())}"
            module_name = _module.get_name()
            if module_name:
                description += f" : {str(module_name)}"
                drivers_list.append([description, _proxy])
        return drivers_list

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
            self.module.set_proxies_name(name=module_name)
            self.refresh_proxy_basic_table()
