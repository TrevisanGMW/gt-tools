"""
Auto Rigger Project Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *
import gt.tools.auto_rigger.control_rig_pose as tools_control_pose


class AttrWidgetProject(AttrWidget):
    def __init__(
        self,
        parent=None,
        project=None,
        refresh_parent_func=None,
        control_pose_mode_func=None,
        capture_control_pose_func=None,
        validate_control_pose_func=None,
        view_control_pose_func=None,
        clear_control_pose_func=None,
        *args,
        **kwargs,
    ):
        """
        Initialize the project attribute widget panel.

        This widget is designed to display and edit project-level attributes
        and preferences in the UI. It includes project name and prefix fields,
        preference checkboxes, directory path selector, and a mirror proxies table.

        Args:
            parent (QWidget, optional): Parent widget for this UI element.
            project (Project, optional): The project instance whose attributes will be edited.
            refresh_parent_func (callable, optional): Function to call to refresh the parent UI
                after changes. If provided, it is set internally.
            control_pose_mode_func (callable, optional): Function used to change the control pose mode.
            capture_control_pose_func (callable, optional): Function used to capture the current rig pose.
            validate_control_pose_func (callable, optional): Function used to validate stored custom pose data.
            view_control_pose_func (callable, optional): Function used to show stored pose data.
            clear_control_pose_func (callable, optional): Function used to clear stored custom pose data.
            *args: Additional positional arguments passed to the base AttrWidget.
            **kwargs: Additional keyword arguments passed to the base AttrWidget.
        """
        super().__init__(parent, *args, **kwargs)

        # Basic Variables
        self.project = project
        self.project_name_field = None
        self.project_prefix_field = None
        self.refresh_parent_func = None
        self.table_mirror_wdg = None
        self.control_pose_mode_combo = None
        self.control_pose_status_label = None
        self.control_pose_mode_func = control_pose_mode_func
        self.capture_control_pose_func = capture_control_pose_func
        self.validate_control_pose_func = validate_control_pose_func
        self.view_control_pose_func = view_control_pose_func
        self.clear_control_pose_func = clear_control_pose_func

        if refresh_parent_func:
            self.set_refresh_parent_func(refresh_parent_func)

        self.add_widget_project_header()

        # Preferences
        self.add_widget_separator_line(label_text="Preferences")
        self.add_project_preferences_attr_widget_path(
            attr_name="project_dir",
            nice_name="Project Directory",
            dir_only=True,
            ok_caption="Set Directory",
            placeholder='Project Directory (defaults to env-var: "{project-file-dir}")',
        )

        # Preferences
        _tooltip = (
            "An alias or alternative name for the project. Used when a different name is necessary in "
            "another pipeline step, for example when exporting."
        )
        self.add_project_preferences_attr_widget_text_field(
            attr_name="alias",
            nice_name="Project Alias",
            placeholder='Project Alias (env-var: "{project-alias}")',
            tooltip=_tooltip,
        )
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.add_project_preferences_attr_widget_checkbox(attr_name="delete_proxy_after_build", layout=_layout)
        self.add_project_preferences_attr_widget_checkbox(attr_name="hide_skeleton", layout=_layout)
        self.content_layout.addLayout(_layout)
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.add_project_preferences_attr_widget_checkbox(attr_name="view_fit_skeleton", layout=_layout)
        self.content_layout.addLayout(_layout)
        _export_anim_bs_tooltip = (
            "If checked, the generated rig will flag to the Exporter that animations "
            "should include extra geometry describing animated blendshapes."
        )
        self.add_project_preferences_attr_widget_checkbox(
            attr_name="export_anim_blendshapes", layout=_layout, tooltip=_export_anim_bs_tooltip
        )

        # Control Rig Pose -------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Control Rig Pose")
        self.add_widget_control_rig_pose()

        # Mirror Table -------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Mirror Proxies")
        self.add_widget_mirror_table()
        self.add_widget_mirror_buttons()

    def add_widget_control_rig_pose(self):
        """Adds mode, capture, validation, viewing, and clear controls for the control rig pose."""
        mode_layout = ui_qt.QtWidgets.QHBoxLayout()
        mode_layout.setContentsMargins(0, 0, 0, 5)
        mode_tooltip = (
            "Chooses which pose is used while building the control rig. This does not change the mesh bind pose.\n\n"
            "Automatic: runs each module's pose helper, normally producing a biped T-pose.\n\n"
            "Custom Stored Pose: applies the arbitrary skeleton pose captured from a previously built rig.\n\n"
            "Disabled: builds controls in the same pose used by the mesh and skeleton."
        )
        mode_label = ui_qt.QtWidgets.QLabel("Mode:")
        mode_label.setObjectName("control_pose_mode_label")
        mode_label.setToolTip(mode_tooltip)
        mode_label.setFixedWidth(mode_label.sizeHint().width())
        self.control_pose_mode_combo = ui_qt.QtWidgets.QComboBox()
        self.control_pose_mode_combo.setObjectName("control_pose_mode_combo")
        self.control_pose_mode_combo.addItem(
            "Automatic (Biped T-Pose Helper)", tools_control_pose.ControlRigPoseMode.AUTOMATIC
        )
        self.control_pose_mode_combo.addItem("Custom Stored Pose", tools_control_pose.ControlRigPoseMode.CUSTOM)
        self.control_pose_mode_combo.addItem("Disabled", tools_control_pose.ControlRigPoseMode.DISABLED)
        mode_index = self.control_pose_mode_combo.findData(self.project.get_control_rig_pose_mode())
        self.control_pose_mode_combo.setCurrentIndex(max(mode_index, 0))
        self.control_pose_mode_combo.currentIndexChanged.connect(self.on_control_pose_mode_changed)
        self.control_pose_mode_combo.setToolTip(mode_tooltip)
        mode_tooltips = [
            "Runs module pose helpers during each build. Biped arm and leg helpers normally create a T-pose, "
            "while the mesh and skeleton remain bound in their original pose.",
            "Uses the stored per-joint world matrices as the control-build pose. Capture this data from a built "
            "rig after posing it with its controls. The pose may be any shape, not only a T-pose.",
            "Does not create a separate control rig pose. Controls are built directly in the mesh and skeleton "
            "bind pose; any stored custom pose remains saved but inactive.",
        ]
        qt_enum = ui_qt.QtCore.Qt
        item_data_role = getattr(qt_enum, "ItemDataRole", None)
        tooltip_role = item_data_role.ToolTipRole if item_data_role else qt_enum.ToolTipRole
        for index, tooltip in enumerate(mode_tooltips):
            self.control_pose_mode_combo.setItemData(index, tooltip, tooltip_role)
        mode_layout.addWidget(mode_label, 0)
        mode_layout.addWidget(self.control_pose_mode_combo, 1)
        self.content_layout.addLayout(mode_layout)

        self.control_pose_status_label = ui_qt.QtWidgets.QLabel()
        self.control_pose_status_label.setObjectName("control_pose_status_label")
        self.control_pose_status_label.setWordWrap(True)
        self.content_layout.addWidget(self.control_pose_status_label)

        button_layout = ui_qt.QtWidgets.QHBoxLayout()
        capture_button = ui_qt.QtWidgets.QPushButton("Capture Current Rig Pose")
        capture_button.setObjectName("capture_control_pose_button")
        capture_button.setToolTip(
            "Captures the evaluated skeleton pose from the built rig that matches this project. First pose the rig "
            "with any combination of controls, then click this button. The per-joint matrices are stored in the "
            "project, Custom Stored Pose is activated, and the next rig build uses that pose for its controls."
        )
        capture_button.clicked.connect(self.on_capture_control_pose)
        button_layout.addWidget(capture_button)

        validate_button = ui_qt.QtWidgets.QPushButton("Validate")
        validate_button.setObjectName("validate_control_pose_button")
        validate_button.setToolTip(
            "Checks the stored schema, project identity, proxy configuration, target coverage, and matrix values. "
            "Validation does not change the Maya scene or the stored pose."
        )
        validate_button.clicked.connect(self.on_validate_control_pose)
        button_layout.addWidget(validate_button)

        view_button = ui_qt.QtWidgets.QPushButton("View Data")
        view_button.setObjectName("view_control_pose_button")
        view_button.setToolTip(
            "Opens a read-only, line-numbered, syntax-highlighted window showing every stored matrix together "
            "with its target joint name and proxy UUID."
        )
        view_button.clicked.connect(self.on_view_control_pose)
        button_layout.addWidget(view_button)

        clear_button = ui_qt.QtWidgets.QPushButton("Clear")
        clear_button.setObjectName("clear_control_pose_button")
        clear_button.setToolTip(
            "Removes all stored custom pose matrices from this project and switches the mode to Automatic. "
            "The deletion becomes persistent when the project is saved."
        )
        clear_button.clicked.connect(self.on_clear_control_pose)
        button_layout.addWidget(clear_button)
        self.content_layout.addLayout(button_layout)
        self.refresh_control_pose_status()

    def set_control_pose_status(self, message, is_error=False):
        """Updates the control rig pose status label.

        Args:
            message (str): Message to display.
            is_error (bool, optional): Whether to display the message as an error.
        """
        self.control_pose_status_label.setText(message)
        color = ui_res_lib.Color.Hex.red_melon if is_error else ui_res_lib.Color.Hex.gray_light
        self.control_pose_status_label.setStyleSheet(f"color: {color};")

    def refresh_control_pose_status(self):
        """Refreshes the stored pose summary without rebuilding the project widget."""
        pose_data = self.project.get_control_rig_pose_data()
        pose_mode = self.project.get_control_rig_pose_mode()
        if pose_data.has_pose() and pose_mode == tools_control_pose.ControlRigPoseMode.CUSTOM:
            self.set_control_pose_status(
                f"Active custom pose: {pose_data.get_transform_count()} joint transforms."
            )
        elif pose_data.has_pose():
            self.set_control_pose_status(
                f"Stored custom pose: {pose_data.get_transform_count()} joint transforms (currently inactive)."
            )
        elif pose_mode == tools_control_pose.ControlRigPoseMode.CUSTOM:
            self.set_control_pose_status(
                "Custom mode requires a captured pose before the rig can be built.", is_error=True
            )
        elif pose_mode == tools_control_pose.ControlRigPoseMode.AUTOMATIC:
            self.set_control_pose_status("Module helpers will generate the control rig pose during the next build.")
        else:
            self.set_control_pose_status("Controls will be built directly in the bind pose.")

    def on_control_pose_mode_changed(self, *args):
        """Updates the project when the user selects a control rig pose mode.

        Args:
            *args: Qt signal arguments.
        """
        mode = self.control_pose_mode_combo.currentData()
        if self.control_pose_mode_func:
            self.control_pose_mode_func(mode)
        else:
            self.project.set_control_rig_pose_mode(mode)
        self.refresh_control_pose_status()

    def on_capture_control_pose(self, *args):
        """Captures the current evaluated rig pose using the controller callback.

        Args:
            *args: Qt signal arguments.
        """
        if not self.capture_control_pose_func:
            self.set_control_pose_status(
                "Pose capture is unavailable without an active rigger controller.", is_error=True
            )
            return
        try:
            message = self.capture_control_pose_func()
            custom_index = self.control_pose_mode_combo.findData(tools_control_pose.ControlRigPoseMode.CUSTOM)
            self.control_pose_mode_combo.blockSignals(True)
            self.control_pose_mode_combo.setCurrentIndex(custom_index)
            self.control_pose_mode_combo.blockSignals(False)
            self.set_control_pose_status(message or "Captured the current rig pose.")
        except Exception as error:
            self.set_control_pose_status(str(error), is_error=True)

    def on_validate_control_pose(self, *args):
        """Validates the stored custom pose using the controller callback.

        Args:
            *args: Qt signal arguments.
        """
        if not self.validate_control_pose_func:
            validation = self.project.validate_control_rig_pose_data()
        else:
            validation = self.validate_control_pose_func()
        errors = validation.get("errors") or []
        warnings = validation.get("warnings") or []
        if errors:
            self.set_control_pose_status(" ".join(errors), is_error=True)
        elif warnings:
            self.set_control_pose_status(" ".join(warnings))
        else:
            count = validation.get("transform_count", 0)
            self.set_control_pose_status(f"Stored custom pose is valid ({count} joint transforms).")

    def on_clear_control_pose(self, *args):
        """Clears the stored custom pose using the controller callback.

        Args:
            *args: Qt signal arguments.
        """
        if self.clear_control_pose_func:
            message = self.clear_control_pose_func()
        else:
            self.project.clear_control_rig_pose_data()
            self.project.set_control_rig_pose_mode(tools_control_pose.ControlRigPoseMode.AUTOMATIC)
            message = "Cleared the stored custom pose. Automatic mode is active."
        automatic_index = self.control_pose_mode_combo.findData(tools_control_pose.ControlRigPoseMode.AUTOMATIC)
        self.control_pose_mode_combo.blockSignals(True)
        self.control_pose_mode_combo.setCurrentIndex(automatic_index)
        self.control_pose_mode_combo.blockSignals(False)
        self.set_control_pose_status(message)

    def on_view_control_pose(self, *args):
        """Shows the stored custom pose data using the controller callback.

        Args:
            *args: Qt signal arguments.
        """
        if self.view_control_pose_func:
            self.view_control_pose_func()
        else:
            self.set_control_pose_status(
                "Stored pose viewing is unavailable without an active rigger controller.", is_error=True
            )

    # Parameter Widgets ----------------------------------------------------------------------------------------
    def add_widget_project_header(self):
        """
        Adds the header for controlling a project. With Icon, Name and modify button.
        """
        # Project Header (Icon, Name, Buttons)
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        _layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)

        # Icon
        icon = ui_qt.QtGui.QIcon(self.project.icon)
        icon_label = ui_qt.QtWidgets.QLabel()
        icon_label.setPixmap(icon.pixmap(32, 32))
        label_tooltip = "Rig Project"
        icon_label.setToolTip(label_tooltip)
        _layout.addWidget(icon_label)

        # Name (User Custom)
        name = self.project.get_name()
        self.project_name_field = ui_qt_utils.ConfirmableQLineEdit()
        self.project_name_field.setFixedHeight(35)
        if name:
            self.project_name_field.setText(name)
        self.project_name_field.editingFinished.connect(self.set_project_name)
        _layout.addWidget(self.project_name_field)

        # Edit Button
        edit_project_btn = ui_qt.QtWidgets.QPushButton()
        edit_project_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_dict))
        edit_project_btn.setToolTip("Edit Raw Data")
        edit_project_btn.clicked.connect(self.on_button_edit_project_clicked)
        _layout.addWidget(edit_project_btn)
        self.content_layout.addLayout(_layout)

    def on_button_edit_project_clicked(self, skip_modules=True, *args):
        """
        Shows a text-editor window with the project converted to a dictionary (raw data)
        If the user applies the changes, and they are considered valid, the module is updated with it.
        Args:
            skip_modules (bool, optional): If active, the "modules" key will be ignored.
            *args: Variable-length argument list. - Here to avoid issues with the "skip_modules" argument.
        """
        project_name = self.project.get_name()
        param_win = ui_input_window_text.InputWindowText(
            parent=self,
            message=f'Editing Raw Data for the Project "{project_name}"',
            window_title=f'Raw data for "{project_name}"',
            image=ui_res_lib.Icon.rigger_dict,
            window_icon=ui_res_lib.Icon.library_parameters,
            image_scale_pct=10,
            is_python_code=True,
        )
        param_win.set_confirm_button_text("Apply")
        project_raw_data = self.project.get_project_as_dict()
        if "modules" in project_raw_data and skip_modules:
            project_raw_data.pop("modules")
        formatted_dict = core_iter.dict_as_formatted_str(project_raw_data, one_key_per_line=True)
        param_win.set_text_field_text(formatted_dict)
        confirm_button_func = partial(self.update_project_from_raw_data, param_win.get_text_field_text, self.project)
        param_win.confirm_button.clicked.connect(confirm_button_func)
        param_win.show()

    # Setters --------------------------------------------------------------------------------------------------
    def set_project_name(self):
        """
        Sets the project name based on the text from the project name input field.

        Retrieves the current text from the project name field, defaults to an empty string
        if the field is empty, updates the project name, and triggers a refresh in the parent.
        """
        new_name = self.project_name_field.text() or ""
        self.project.set_name(new_name)
        self.call_parent_refresh()

    def update_project_from_raw_data(self, data_getter, project):
        """
        Updates a project description using raw string data.
        Used with "on_button_edit_project_clicked" to update a project from raw data.
        Args:
            data_getter (callable): A function used to retrieve the data string. e.g. Get a string from a textfield.
            project (RigProject): A rig project object to be updated using the provided data.
        """
        data = data_getter()
        try:
            _data_as_dict = ast.literal_eval(data)
            project.read_data_from_dict(module_dict=_data_as_dict, clear_modules=False)
            self.refresh_current_widgets()
            self.call_parent_refresh()
        except Exception as e:
            raise Exception(f'Unable to set project attributes from provided raw data. Issue: "{e}".')

    def add_widget_mirror_table(self):
        """
        Adds a table widget to handle the mirroring of the proxies for the listed modules
        """
        _layout = ui_qt.QtWidgets.QVBoxLayout()
        # Mirror table
        self.table_mirror_wdg = ui_qt.QtWidgets.QTableWidget()
        self.clear_mirror_table()
        columns = ["Source Module", "", "Target Module"]  # Source, Direction, Target
        self.table_mirror_wdg.setColumnCount(len(columns))
        self.table_mirror_wdg.setHorizontalHeaderLabels(columns)
        header_view = self.table_mirror_wdg.horizontalHeader()
        header_view.setSectionResizeMode(0, ui_qt.QtLib.QHeaderView.Stretch)
        header_view.setSectionResizeMode(1, ui_qt.QtLib.QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(2, ui_qt.QtLib.QHeaderView.Stretch)
        _layout.addWidget(self.table_mirror_wdg)
        self.refresh_mirror_table()
        self.scroll_content_layout.addLayout(_layout)

    def clear_mirror_table(self):
        """
        Clears all rows from the mirror table widget, effectively emptying the table.
        """
        if self.table_mirror_wdg:
            self.table_mirror_wdg.setRowCount(0)

    def get_available_mirror_modules(self):
        """
        Gets the modules of the project allowed to be mirrored.

        Returns:
            list: mirror modules
        """
        mirror_modules = []
        mirror_cat = list(tools_rig_modules.get_mirror_category().keys())
        for module in self.project.get_modules():
            if not any(m_cat in module.__class__.__name__ for m_cat in mirror_cat):
                continue
            mirror_modules.append(module)
        return mirror_modules

    def get_auto_assigned_mirror_map(self, source_prefix=None, target_prefix=None):
        """
        Gets a dictionary with the automatic mirror modules assignment.

        Args:
            source_prefix (str, optional): Prefix identifying source-side modules (e.g., "L_").
                                           Defaults to core_naming.NamingConstants.Prefix.LEFT.
            target_prefix (str, optional): Prefix identifying target-side modules (e.g., "R_").
                                           Defaults to core_naming.NamingConstants.Prefix.RIGHT.

        Returns:
            dict: A mapping where keys are source module names and values are corresponding target module names
                  if a mirror exists, or None if no mirror target is found.
        """

        if not source_prefix:
            source_prefix = core_naming.NamingConstants.Prefix.LEFT
        if not target_prefix:
            target_prefix = core_naming.NamingConstants.Prefix.RIGHT

        auto_assigned_mirror = {}

        mod_list = self.project.get_modules()
        for s_mod in mod_list:
            s_mod_name = s_mod.get_name()
            s_mod_name_no_sides = self._remove_side_from_module_name(s_mod_name)
            s_mod_c_name = s_mod.__module__  # s_mod.get_module_class_name()
            if s_mod.get_prefix() == source_prefix:
                for t_mod in mod_list:
                    t_mod_name = t_mod.get_name()
                    t_mod_name_no_sides = self._remove_side_from_module_name(t_mod_name)
                    t_mod_c_name = t_mod.__module__  # t_mod.get_module_class_name()
                    t_mod_prefix = t_mod.get_prefix()
                    if (
                        s_mod_c_name == t_mod_c_name
                        and t_mod_prefix == target_prefix
                        and s_mod_name_no_sides == t_mod_name_no_sides
                    ):
                        auto_assigned_mirror[s_mod_name] = t_mod_name
            if s_mod_name not in auto_assigned_mirror.keys():
                auto_assigned_mirror[s_mod_name] = None

        return auto_assigned_mirror

    @staticmethod
    def _remove_side_from_module_name(module_name):
        """
        Helper func that returns the module name without sides.
        Args:
            module_name (str): string to filter
        Returns:
            filtered_name: given name without sides
        """
        filtered_name = module_name
        lower_name = module_name.lower()
        separators = ["_", " "]
        sides = ["l", "r", "rt", "lf", "rx", "lt", "left", "right"]

        # clean the start
        for sd in sides:
            for sp in separators:
                full_start_side = sd + sp
                if lower_name.startswith(full_start_side):
                    char_id = len(full_start_side)
                    filtered_name = module_name[char_id:]
                    break

        # clean the rest
        for sd in sides:
            for sp in separators:
                full_inbetween_side = sp + sd + sp
                filtered_name = filtered_name.replace(full_inbetween_side, "")
                full_inbetween_side = sp + sd.capitalize() + sp
                filtered_name = filtered_name.replace(full_inbetween_side, "")
                full_inbetween_side = sp + sd.upper() + sp
                filtered_name = filtered_name.replace(full_inbetween_side, "")

        return filtered_name

    def refresh_mirror_table(self):
        """
        Refresh the mirror table with the module list.
        """
        self.clear_mirror_table()
        mirror_modules = self.get_available_mirror_modules()

        for row, module in enumerate(mirror_modules):
            self.table_mirror_wdg.insertRow(row)

            # Source module
            self.insert_item(
                row=row,
                column=0,
                table=self.table_mirror_wdg,
                text=module.get_name(),
                editable=False,
                data_object=module,
            )

            # Direction
            self.insert_item(
                row=row,
                column=1,
                table=self.table_mirror_wdg,
                icon_path=ui_res_lib.Icon.ui_thin_arrow_right,
                icon_size=22,
                editable=False,
                centered=True,
            )

            # Target module
            combo_mirror_mod_list = self.create_widget_mirror_module_combobox(exclude_mod=[module])
            combo_mirror_mod_list.currentIndexChanged.connect(self.update_table_mirror_target_status)
            self.table_mirror_wdg.setCellWidget(row, 2, combo_mirror_mod_list)

    def create_widget_mirror_module_combobox(self, exclude_mod=None):
        """
        Creates a populated combobox with the mirror modules available.
        Args:
            exclude_mod (list): list of modules to exclude in the combobox
        Returns:
            QComboBox: A pre-populated combobox with the mirror modules.
        """
        mirror_modules = self.get_available_mirror_modules()
        combobox = ui_qt.QtWidgets.QComboBox()
        combobox.setEditable(True)
        combobox.lineEdit().setAlignment(ui_qt.QtCore.Qt.AlignCenter)

        # Populate Combobox
        combobox.addItem("---", None)
        exclude_mod_uuids = []
        if exclude_mod:
            exclude_mod_uuids = [mod.uuid for mod in exclude_mod]
        for module in mirror_modules:
            if module.uuid in exclude_mod_uuids:
                continue
            combobox.addItem(module.get_name(), module)

        # Set No Parent at the beginning
        combobox.setCurrentIndex(0)
        combobox.setProperty("lastindex", 0)

        return combobox

    def add_widget_mirror_buttons(self):
        """
        Adds actions buttons (auto assign, mirror proxies)
        """
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        # Auto Assign mirror module
        auto_assign_mirror_btn = ui_qt.QtWidgets.QPushButton("Auto Assign Mirror Targets")
        auto_assign_mirror_btn.clicked.connect(self.on_button_auto_assign_mirror)
        auto_assign_mirror_btn.setToolTip("Auto Assign Mirror Targets")
        _layout.addWidget(auto_assign_mirror_btn)
        # Mirror Proxies
        mirror_proxies_btn = ui_qt.QtWidgets.QPushButton("Mirror Proxies")
        mirror_proxies_btn.clicked.connect(self.on_button_mirror_proxies)
        mirror_proxies_btn.setToolTip("Mirror Proxies")
        _layout.addWidget(mirror_proxies_btn)
        self.scroll_content_layout.addLayout(_layout)

    def on_button_auto_assign_mirror(self):
        """
        Auto-assigns the mirror modules in the mirror table.
        """

        mirror_mod_map = self.get_auto_assigned_mirror_map()
        if not any(mirror_mod_map.values()):
            message_box = ui_qt.QtWidgets.QMessageBox(self)
            message_box.setWindowTitle("Mirror Auto Assign")
            message_box.setText(f"No suitable modules found to auto-assign as mirror targets.")
            question_icon = ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_exclamation)
            message_box.setIconPixmap(question_icon.pixmap(64, 64))
            result = message_box.exec_()

        rows_to_disable = []
        for row_num in range(self.table_mirror_wdg.rowCount()):
            source_mod_name = self.table_mirror_wdg.item(row_num, 0).text()
            target_name_assigned = mirror_mod_map[source_mod_name]
            if not target_name_assigned:
                continue
            combo_target_item = self.table_mirror_wdg.cellWidget(row_num, 2)
            target_index = combo_target_item.findText(target_name_assigned)
            combo_target_item.setCurrentIndex(target_index)

            for t_num in range(self.table_mirror_wdg.rowCount()):
                t_name = self.table_mirror_wdg.item(t_num, 0).text()
                if t_name == target_name_assigned:
                    rows_to_disable.append(t_num)

        self.set_table_mirror_rows_status(row_list=rows_to_disable, status=False)

    def on_button_mirror_proxies(self):
        """
        Initiates the mirroring process for proxies between source and target modules as specified in the mirror table.
        """
        mirrored_modules = []
        failed_modules = {}
        for row_num in range(self.table_mirror_wdg.rowCount()):
            combo_target_item = self.table_mirror_wdg.cellWidget(row_num, 2)
            combo_target_module_obj = combo_target_item.currentData()

            if combo_target_module_obj:
                target_name = combo_target_module_obj.get_name()
                source_module = self.table_mirror_wdg.item(row_num, 0).data(self.PROXY_ROLE)
                source_module_uuid = source_module.get_uuid()
                # check scene proxies
                try:
                    source_mod_proxies = tools_rig_utils.find_drivers_from_module(
                        source_uuid=source_module_uuid,
                        filter_driver_type=tools_rig_const.RiggerDriverTypes.PROXY,
                    )
                    if source_mod_proxies:
                        combo_target_module_obj.set_mirror_uuid(source_module_uuid)
                        combo_target_module_obj.get_proxies_mirrored()
                        mirrored_modules.append(target_name)
                    else:
                        failed_modules[target_name] = "Cannot find source proxies."
                except Exception as e:
                    failed_modules[target_name] = e

        combined_msg = ""
        failed_msg = ""
        mirrored_msg = ""
        msg_icon = ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_green_circle)

        if failed_modules:
            failed_msg = "The following modules failed the mirroring process:"
            for mod_name, error in failed_modules.items():
                failed_msg += f"\n - {mod_name}: {error}"
            logger.warning(failed_msg)
            msg_icon = ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_yellow_circle)
            combined_msg = failed_msg + "\n\n"

        if mirrored_modules:
            mirrored_msg = f"The following modules have been mirrored: {str(mirrored_modules)}"
            combined_msg += mirrored_msg
            logger.info(mirrored_msg)

        message_box = ui_qt.QtWidgets.QMessageBox(self)
        message_box.setWindowTitle("Mirror Proxies")
        message_box.setText(combined_msg)
        message_box.setIconPixmap(msg_icon.pixmap(64, 64))
        result = message_box.exec_()

    def update_table_mirror_target_status(self, target_index):
        """
        Updates the enabled/disabled status of mirror target widgets in the mirror table
        based on the change in the combo box selection.

        Args:
            target_index (int): The newly selected index in the combo box.
        """
        combo_item = self.sender()
        last_index = combo_item.property("lastindex")
        last_name = combo_item.itemText(last_index)
        new_name = combo_item.itemText(target_index)

        # update status
        for row_num in range(self.table_mirror_wdg.rowCount()):
            source_module_name = self.table_mirror_wdg.item(row_num, 0).text()
            target_module_item = self.table_mirror_wdg.cellWidget(row_num, 2)
            if source_module_name == last_name:
                target_module_item.setEnabled(True)
            if source_module_name == new_name:
                target_module_item.setEnabled(False)

        # update combobox item value
        combo_item.setProperty("lastindex", target_index)

    def set_table_mirror_rows_status(self, row_list=None, status=True):
        """
        Sets the given table row status.
        If row_list is None, the status will be applied to all the rows.

        Args:
            row_list (list): row indices of the rows to edit
            status (bool): set enabled or disabled
        """
        if not row_list:
            row_list = [row_num for row_num in range(self.table_mirror_wdg.rowCount())]
        for row_num in range(self.table_mirror_wdg.rowCount()):
            source_module_item = self.table_mirror_wdg.item(row_num, 0)
            target_module_item = self.table_mirror_wdg.cellWidget(row_num, 2)
            if row_num in row_list:
                target_module_item.setEnabled(status)
            else:
                target_module_item.setEnabled(not status)

    def refresh_current_widgets(self):
        """
        Refreshes available widgets. For example, text-fields, so they display the correct data.
        """
        if self.project_name_field:
            _name = self.project.get_name()
            if _name:
                self.project_name_field.setText(_name)

        self.refresh_mirror_table()

    # Parameter Widgets ----------------------------------------------------------------------------------------
    def add_project_preferences_attr_widget_path(
        self,
        attr_name,
        attr_value=None,
        nice_name=None,
        placeholder=None,
        layout=None,
        ok_caption="Set Path",
        file_filter="All Files (*);;JSON Files (*.json)",
        dir_only=False,
    ):
        """
        Creates a project attribute text field widget that carries a path.
        Args:
            attr_name (str): The name of the attribute found in the module class (name of the variable)
                       This name is used to find the variable and set its value in the module instance.
            attr_value (str, optional): The initial value of the attribute used to set the value
                                        of the created widget.
                                        (WARNING: This forces this value instead of reading module data)
            nice_name (str, optional): If a nice name is provided, that's what is shown in the UI, otherwise an auto
                                       formatted version of the variable name is used instead (title case)
            placeholder (str, optional): If a placeholder is provided, that will be set as the textfield placeholder,
                                         otherwise the attribute name is used instead.
            layout (QBoxLayout, optional): If provided, this layout receives the created element instead of creating
                                           a new QHBoxLayout.
            ok_caption (str, optional): Caption use for to accept (ok) function.
            file_filter (str, optional): File filter used by the dialog
            dir_only (bool, optional): If True, the path should point to a directory, otherwise a file.

        Returns:
            ConfirmableQLineEdit or tuple: The created QLineEdit object or a tuple with all created QT elements.
        """

        _formatted_attr_name = core_str.snake_to_title(attr_name)
        if nice_name:
            _formatted_attr_name = nice_name
        # Create Layout
        if layout is not None:
            _layout = layout
        else:
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)
        # Create Widgets
        label = ui_qt.QtWidgets.QLabel(f"{_formatted_attr_name}:")
        text_field = ui_qt_utils.ConfirmableQLineEdit()
        path_btn = ui_qt.QtWidgets.QPushButton()
        path_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        path_btn.setToolTip("Use file dialog to set path")
        env_var_btn = ui_qt.QtWidgets.QPushButton()
        env_var_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_env_var))
        env_var_btn.setToolTip("Get more information about the current path.")
        if attr_value is None:
            attr_value = getattr(self.project.get_preferences(), attr_name)
        if placeholder is None:
            placeholder = f"<{attr_name}>"
        text_field.setText(attr_value)
        text_field.setFixedHeight(35)
        text_field.setPlaceholderText(placeholder)
        # Add to Widgets
        _layout.addWidget(label)
        _layout.addWidget(text_field)
        _layout.addWidget(env_var_btn)
        _layout.addWidget(path_btn)
        # Connect
        _func = partial(self.set_project_preferences_attr_value_from_field, attr=attr_name, field=text_field)
        text_field.textChanged.connect(_func)
        _btn_func = partial(
            self.open_module_attr_file_dialog,
            field=text_field,
            ok_caption=ok_caption,
            file_filter=file_filter,
            dir_only=dir_only,
        )
        path_btn.clicked.connect(_btn_func)
        _func = partial(self.open_env_var_feedback_dialog, field=text_field)
        env_var_btn.clicked.connect(_func)
        return text_field

    def add_project_preferences_attr_widget_checkbox(
        self, attr_name, attr_value=None, nice_name=None, layout=None, tooltip=None
    ):
        """
        Creates a project preferences attribute checkbox.
        Args:
            attr_name (str): The name of the attribute found in the module class (name of the variable)
                       This name is used to find the variable and set its value in the module instance.
            attr_value (bool, optional): The initial value of the attribute used to set the value
                                        of the created widget.
            nice_name (str, optional): If a nice name is provided, that's what is shown in the UI, otherwise an auto
                                       formatted version of the variable name is used instead (title case)
            layout (QBoxLayout, optional): If provided, this layout is used instead of creating a new QHBoxLayout.
            tooltip (str, optional): If provided, this becomes the tooltip for the created element.

        Returns:
            QCheckBox: A QCheckBox object.
        """
        _formatted_attr_name = core_str.snake_to_title(attr_name)
        if nice_name:
            _formatted_attr_name = nice_name
        # Create Layout
        if layout is not None:
            _layout = layout
        else:
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)
        # Create Widgets
        label = ui_qt.QtWidgets.QLabel(f"{_formatted_attr_name}:")
        checkbox = ui_qt.QtWidgets.QCheckBox()
        if attr_value is None:
            attr_value = getattr(self.project.get_preferences(), attr_name)
        checkbox.setChecked(attr_value)
        if tooltip:
            checkbox.setToolTip(tooltip)
            label.setToolTip(tooltip)
        # Add to Widgets
        _layout.addWidget(label)
        _layout.addWidget(checkbox)
        # Connect
        _func = partial(self.set_project_preferences_attr_value_from_field, attr=attr_name, field=checkbox)
        checkbox.stateChanged.connect(_func)
        return checkbox

    def add_project_preferences_attr_widget_text_field(
        self,
        attr_name,
        attr_value=None,
        nice_name=None,
        placeholder=None,
        tooltip=None,
        layout=None,
    ):
        """
        Creates a project attribute text field widget that carries a path.
        Args:
            attr_name (str): The name of the attribute found in the module class (name of the variable)
                       This name is used to find the variable and set its value in the module instance.
            attr_value (str, optional): The initial value of the attribute used to set the value
                                        of the created widget.
                                        (WARNING: This forces this value instead of reading module data)
            nice_name (str, optional): If a nice name is provided, that's what is shown in the UI, otherwise an auto
                                       formatted version of the variable name is used instead (title case)
            placeholder (str, optional): If a placeholder is provided, that will be set as the textfield placeholder,
                                         otherwise the attribute name is used instead.
            tooltip (str, optional): If provided, this becomes the tooltip for the created element.
            layout (QBoxLayout, optional): If provided, this layout receives the created element instead of creating
                                           a new QHBoxLayout.
        Returns:
            ConfirmableQLineEdit or tuple: The created QLineEdit object or a tuple with all created QT elements.
        """

        _formatted_attr_name = core_str.snake_to_title(attr_name)
        if nice_name:
            _formatted_attr_name = nice_name
        # Create Layout
        if layout is not None:
            _layout = layout
        else:
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)
        # Create Widgets
        label = ui_qt.QtWidgets.QLabel(f"{_formatted_attr_name}:")
        text_field = ui_qt_utils.ConfirmableQLineEdit()
        if attr_value is None:
            attr_value = getattr(self.project.get_preferences(), attr_name)
        if placeholder is None:
            placeholder = f"<{attr_name}>"
        text_field.setText(attr_value)
        text_field.setFixedHeight(35)
        text_field.setPlaceholderText(placeholder)
        # Tooltip
        if tooltip and isinstance(tooltip, str):
            label.setToolTip(tooltip)
            text_field.setToolTip(tooltip)
        # Add to Widgets
        _layout.addWidget(label)
        _layout.addWidget(text_field)
        # Connect
        _func = partial(self.set_project_preferences_attr_value_from_field, attr=attr_name, field=text_field)
        text_field.textChanged.connect(_func)
        return text_field

    def set_project_preferences_attr_value_from_field(self, *args, attr, field):
        """
        If the provided attribute name is available in the project preferences, this functions tries to set it.
        Args:
            args (any): Used to receive the change from the incoming QtWidget
            attr (str): Name of the attribute.
            field (QtWidget): A QtWidget object to get the value from
        """
        _value = None
        if isinstance(field, ui_qt.QtWidgets.QLineEdit):
            _value = field.text()
        if isinstance(field, ui_qt_utils.QDoubleSlider):
            _value = field.double_value()
        if isinstance(field, ui_qt_utils.QIntSlider):
            _value = field.int_value()
        if isinstance(field, ui_qt.QtWidgets.QCheckBox):
            _value = field.isChecked()
        if isinstance(field, ui_qt.QtWidgets.QComboBox):
            _value = field.currentText()
        if hasattr(self.project.get_preferences(), attr):
            setattr(self.project.get_preferences(), attr, _value)
        else:
            logger.warning(f'Unable to set missing attribute project preference attribute. Attr: "{attr}".')


if __name__ == "__main__":
    print('Run it from "__init__.py".')
