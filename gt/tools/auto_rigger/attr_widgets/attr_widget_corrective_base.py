"""
Auto Rigger Corrective Base Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleBaseCorrective(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for a corrective module.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)
        self.table_driver_lookup_wdg = None
        self.clear_target_dir_chk = None

    def add_widget_driver_lookup_table(self, table_minimum_height=150):
        """
        Adds a table widget to control driver attribute with options to determine parent or delete the proxy
        Args:
            table_minimum_height (int): The minimum height of the created table
        """
        _layout = ui_qt.QtWidgets.QVBoxLayout()
        # Setup Table
        self.table_driver_lookup_wdg = ui_qt.QtWidgets.QTableWidget()
        self.clear_proxy_parent_table()
        columns = [
            "",  # Icon
            "Driver",
            "Attribute",
            "",  # Set Driven Key
            "",  # Delete
        ]  # Icon, Driver, Attribute, Set Driven Key, Delete
        self.table_driver_lookup_wdg.setColumnCount(len(columns))
        self.table_driver_lookup_wdg.setHorizontalHeaderLabels(columns)
        header_view = ui_qt_utils.QHeaderWithWidgets()
        self.table_driver_lookup_wdg.setHorizontalHeader(header_view)
        header_view.setSectionResizeMode(0, ui_qt.QtLib.QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(1, ui_qt.QtLib.QHeaderView.Interactive)
        header_view.setSectionResizeMode(2, ui_qt.QtLib.QHeaderView.Stretch)
        header_view.setSectionResizeMode(3, ui_qt.QtLib.QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(4, ui_qt.QtLib.QHeaderView.ResizeToContents)
        _layout.addWidget(self.table_driver_lookup_wdg)
        self.table_driver_lookup_wdg.setColumnWidth(1, 110)
        self.table_driver_lookup_wdg.setMinimumHeight(table_minimum_height)

        # Add Attribute Placeholder Delegate
        delegate = ui_qt_utils.TablePlaceholderDelegate(
            "<attribute>",
            target_columns=[2],
            placeholder_color=ui_qt.QtGui.QColor(100, 100, 100),
            placeholder_alignment=ui_qt.QtLib.AlignmentFlag.AlignCenter,
        )
        self.table_driver_lookup_wdg.setItemDelegate(delegate)

        # Connect Cell Changes
        self.table_driver_lookup_wdg.cellChanged.connect(self.on_driver_lookup_table_cell_changed)

        # Add Button
        add_driver_btn = ui_qt.QtWidgets.QPushButton()
        add_driver_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_add))
        add_driver_btn.clicked.connect(self.on_button_add_driver_clicked)
        add_driver_btn.setToolTip("Add New Driver Attribute")
        header_view.add_widget(4, add_driver_btn)
        self.content_layout.addLayout(_layout)

    def add_widgets_multiplier_fields(self):
        """
        Creates widgets necessary to control the TRS multipliers on a corrective module.
        """
        _precision = 2
        _min = -20
        _max = 20
        _tooltip = (
            "TRS Multiplier modifies the stored valued when reading existing driven keys.\n"
            "These multipliers only influence the values read by the module. \n"
            "A value of 1 represents 100% influence, which is the default behavior."
        )
        self.add_widget_separator_line(label_text="Multiplier Preferences", tooltip=_tooltip)
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        self.add_module_attr_widget_double_spinbox(
            attr_name="translate_multiplier",
            min_double=_min,
            max_double=_max,
            precision=_precision,
            step=0.1,
            tooltip="Translate X, Y, and Z multiplier for the value of the applied driven keys. (1 = 100% influence)\n"
            "This means that a translate value of 10 when multiplier by 0.5 would become 5.\n"
            "This can help adjust driven keys created in a different rig scale so they work on a new scale.",
            layout=_layout,
        )
        self.add_module_attr_widget_double_spinbox(
            attr_name="rotate_multiplier",
            min_double=_min,
            max_double=_max,
            precision=_precision,
            step=0.1,
            tooltip="Rotate X, Y, and Z multiplier for the value of the applied driven keys. (1 = 100% influence)\n"
            "This means that a rotate value of 90 when multiplier by 2 would become 180.\n"
            "This allows for fine-tuning the amount of rotation read by the module, without writing new keys.",
            layout=_layout,
        )
        self.add_module_attr_widget_double_spinbox(
            attr_name="scale_multiplier",
            min_double=_min,
            max_double=_max,
            precision=_precision,
            step=0.1,
            tooltip="Scale X, Y, and Z multiplier for the value of the applied driven keys. (1 = 100% influence)\n"
            "This means that a scale value of 1 when multiplier by 0.5 would become 0.5.\n"
            "This allows for fine-tuning the amount of scale read by the module, without writing new keys.",
            layout=_layout,
        )

    def on_button_add_driver_clicked(self):
        """
        Adds a new proxy to the current module and refreshes the UI
        """
        self.module.add_new_driver_attr_path()
        self.refresh_driver_lookup_table()

    def clear_driver_lookup_table(self):
        """
        Clears the driver lookup table (No items)
        """
        if self.table_driver_lookup_wdg:
            self.table_driver_lookup_wdg.setRowCount(0)

    def refresh_driver_lookup_table(self):
        """
        Refresh the table with drivers associated with the module.
        """
        self.clear_driver_lookup_table()
        current_modules = self.project.get_modules()
        uuid_to_module = {module.get_uuid(): module for module in current_modules}

        self.table_driver_lookup_wdg.cellChanged.disconnect(
            self.on_driver_lookup_table_cell_changed
        )  # Fix recursion errors

        for row, driver_attr_dict in enumerate(self.module.driver_attr_paths):
            self.table_driver_lookup_wdg.insertRow(row)
            driver, attr = next(iter(driver_attr_dict.items()))

            # Icon -------------------------------------------------------------------------------
            default_icon = ui_res_lib.Icon.util_sel_non_unique
            if driver and driver in uuid_to_module:
                default_icon = uuid_to_module.get(driver).icon
            self.insert_item(
                row=row,
                column=0,
                table=self.table_driver_lookup_wdg,
                icon_path=default_icon,
                editable=False,
                centered=True,
            )

            # Driver -----------------------------------------------------------------------------
            combo_box = self.create_widget_probe_combobox(initial_probe=driver)
            combo_func = partial(self.on_table_driver_lookup_combo_box_changed, row=row, col=1)
            combo_box.currentIndexChanged.connect(combo_func)
            self.table_driver_lookup_wdg.setCellWidget(row, 1, combo_box)

            # Attribute ---------------------------------------------------------------------------
            if driver and driver in uuid_to_module:
                _probe = uuid_to_module.get(driver)
                _updated_attr = attr
                try:
                    _updated_attr = _probe.get_probe_output_attr_path()
                    self.module.update_driver_attr_path(index=row, new_mapping={driver: _updated_attr})
                except Exception as e:
                    logger.warning(f"Unable to refresh probe data from source. Issue: {e}")
                self.insert_item(
                    row=row,
                    column=2,
                    table=self.table_driver_lookup_wdg,
                    text=_updated_attr,
                    data_object=driver_attr_dict,
                    editable=False,
                )

                item = self.table_driver_lookup_wdg.item(row, 2)
                item.setForeground(ui_qt.QtGui.QBrush(ui_qt.QtGui.QColor(ui_res_lib.Color.Hex.purple_medium)))
            else:
                self.insert_item(
                    row=row,
                    column=2,
                    table=self.table_driver_lookup_wdg,
                    text=attr,
                    data_object=driver_attr_dict,
                )

            # Edit Proxy ---------------------------------------------------------------------
            set_driven_key_btn = ui_qt.QtWidgets.QPushButton("Set Driven Key")
            set_driven_key_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_testing_keys))
            set_driven_key_func = partial(self.on_btn_set_driven_key_clicked, index=row)
            set_driven_key_btn.clicked.connect(set_driven_key_func)
            set_driven_key_btn.setToolTip("Set Driven Key Using Driver")
            self.table_driver_lookup_wdg.setCellWidget(row, 3, set_driven_key_btn)

            # Delete Setup --------------------------------------------------------------------
            delete_driver_btn = ui_qt.QtWidgets.QPushButton()
            delete_driver_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete))
            delete_driver_func = partial(self.on_btn_delete_driver_clicked, index=row)
            delete_driver_btn.clicked.connect(delete_driver_func)
            delete_driver_btn.setToolTip("Delete Driver Attribute")
            self.table_driver_lookup_wdg.setCellWidget(row, 4, delete_driver_btn)

        self.table_driver_lookup_wdg.cellChanged.connect(
            self.on_driver_lookup_table_cell_changed
        )  # Fix recursion errors

    def create_widget_probe_combobox(self, initial_probe):
        """
        Creates a populated combobox with all potential probes to be used as drivers.
        An extra initial item called "Manually Set" is also added for user-defined custom attributes.
        Args:
            initial_probe (str, None): UUID of a probe module or None if not defined.
        Returns:
            QComboBox: A pre-populated combobox with potential probes. Initial probe is also pre-selected.
        """
        current_modules = self.project.get_modules()
        uuid_to_module = {module.get_uuid(): module for module in current_modules}

        category_attrs = vars(tools_rig_modules.RigModules.Probes)
        probe_module_classes = {name: value for name, value in category_attrs.items() if inspect.isclass(value)}

        combobox = ui_qt.QtWidgets.QComboBox()
        combobox.addItem("Manually Set", None)

        detected_probes = [obj for obj in current_modules if obj.__class__.__name__ in probe_module_classes]

        # Populate Combobox
        for _probe in detected_probes:
            _probe_name = _probe.get_name()
            combobox.addItem(_probe_name, _probe)

        # Set Initial or Add Unknown Initial Probe (Not present in project)
        if initial_probe is None:
            return combobox
        if initial_probe in uuid_to_module:
            for index in range(combobox.count()):
                _probe = combobox.itemData(index)
                if _probe and initial_probe == _probe.get_uuid():
                    combobox.setCurrentIndex(index)
        elif initial_probe and initial_probe not in uuid_to_module:
            description = f"unknown"
            description += f" (UUID: {str(initial_probe)})"
            combobox.addItem(description, None)
            combobox.setCurrentIndex(combobox.count() - 1)  # Last item, which was just added
        return combobox

    def on_btn_set_driven_key_clicked(self, index):
        """
        Opens the Maya dialog for setting driven keys with pre-populated values.
        Args:
            index (int): Index used to determine the driver attribute.
        """
        item = self.table_driver_lookup_wdg.item(index, 2)  # 2 = Attribute
        if item:
            import maya.cmds as cmds
            import maya.mel as mel

            driver_attr = item.text()
            if not cmds.objExists(driver_attr):
                logger.warning(f"Driver attribute not available. Make sure it exists and the rig built then try again.")
                return

            cor_joints = []
            for proxy in self.module.proxies:
                _joint = tools_rig_utils.find_joint_from_uuid(proxy.get_uuid())
                if _joint:
                    cor_joints.append(_joint)
            if not cor_joints:
                logger.warning(f"Missing driven joints. Make sure the rig is built then try again.")
                return

            cmds.select(cor_joints, replace=True)
            mel.eval('setDrivenKeyWindow "" {""};')
            driver = driver_attr
            if "." in driver_attr:
                driver = driver_attr.split(".")[0]
            cmds.select(driver, replace=True)
            mel.eval('updateSetDrivenWnd("driver", "", {""});')
            cmds.select(clear=True)
        else:
            logger.warning(f"No driver attribute provided.")

    def on_btn_delete_driver_clicked(self, index):
        """
        Removes driver attribute stored in the specified index
        Args:
            index (int): Index of the driver that should be deleted.
        """
        self.module.remove_driver_attr_path(index)
        self.refresh_driver_lookup_table()

    def on_driver_lookup_table_cell_changed(self, row, column):
        """
        Updates the name of the attributes in case the user writes a new name in the attribute cell.
        Args:
            row (int): Row where the cell changed.
            column (int): Column where the cell changed.
        """
        _source_table = self.table_driver_lookup_wdg
        _attr_cell = _source_table.item(row, 2)  # 2 = Attribute
        attr_dict = _attr_cell.data(self.PROXY_ROLE)
        driver, attribute = next(iter(attr_dict.items()))
        new_name = _attr_cell.text()
        if new_name:
            attr_dict[driver] = new_name
            self.module.update_driver_attr_path(index=row, new_mapping=attr_dict)
            self.refresh_driver_lookup_table()
        else:
            _attr_cell.setText(attribute)

    def on_table_driver_lookup_combo_box_changed(self, index, row, col):
        """
        Handle the change in the probe combo box for the driver table.

        Args:
            index (int): Index of the selected item.
            row (int): Row index.
            col (int): Column index.
        """
        _source_table = self.table_driver_lookup_wdg
        _combo_box = _source_table.cellWidget(row, col)
        _probe_mod = _combo_box.itemData(index)
        _attr_cell = _source_table.item(row, 2)  # 2 = Attribute
        if _probe_mod is None:
            self.module.update_driver_attr_path(index=row, new_mapping={None: ""})
        else:
            uuid = _probe_mod.get_uuid()
            attr_path = _probe_mod.get_probe_output_attr_path()
            self.module.update_driver_attr_path(index=row, new_mapping={uuid: attr_path})
        self.refresh_driver_lookup_table()

    def add_widget_read_write_buttons(self):
        """
        Adds actions buttons
        """
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        # Write Driven Keys
        write_keys_btn = ui_qt.QtWidgets.QPushButton("Write Driven Keys")
        write_keys_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_build))
        write_keys_btn.clicked.connect(self.write_driven_keys)
        write_keys_btn.setToolTip("Write Influences From Selection")

        # Open Dir
        open_dir_btn = ui_qt.QtWidgets.QPushButton("Open Directory")
        open_dir_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        open_dir_btn.clicked.connect(self.open_driven_keys_dir)
        open_dir_btn.setToolTip("Write Weights From Selection")
        # Layout
        _layout.addWidget(write_keys_btn)
        _layout.addWidget(open_dir_btn)
        self.scroll_content_layout.addLayout(_layout)

    def open_driven_keys_dir(self):
        """Opens the file path directory"""
        _parsed_path = self.module.parse_path(path=self.module.driven_keys_dir)
        if not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing directory. Path: "{str(_parsed_path)}".')
            return
        if not _parsed_path or _parsed_path == "." or not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing path: "{str(_parsed_path)}".')
            return
        utils_system.open_file_dir(_parsed_path)

    def write_driven_keys(self):
        """Writes influences to set directory"""
        clear_target_dir = self.clear_target_dir_chk.isChecked()
        self.module.write_driven_keys(clear_target_dir=clear_target_dir)
