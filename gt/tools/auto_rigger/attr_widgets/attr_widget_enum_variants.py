"""
Auto Rigger Enum Variants Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleEnumVariants(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        import gt.tools.auto_rigger.modules.module_enum_variants as tools_mod_enum_vars

        self._KEYS = tools_mod_enum_vars.EnumVariantsKeys

        self.add_widget_module_header()
        self.add_widget_code_data_editor()

        # Enum Section -----------------------------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Enum Variants")
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        _tooltip = "Name or path to the object that will receive the created ENUM. Often a control."
        self.add_module_attr_widget_text_field(
            attr_name="enum_target",
            layout=_layout,
            placeholder="C_visibility_CTRL",
            tooltip=_tooltip,
        )
        _tooltip = 'String used for when nothing should change in an ENUM. e.g. "None", or "Nothing".'
        self.add_module_attr_widget_text_field(
            attr_name="none_label",
            layout=_layout,
            placeholder="None",
            tooltip=_tooltip,
        )
        _tooltip = "Attribute to be updated using the ENUM. When the corresponding ENUM is selected, \n"
        _tooltip += 'this attribute is set to "1", when not selected, it is set to "0". Usually used with "visibility".'
        self.add_module_attr_widget_text_field(
            attr_name="driven_attr",
            layout=_layout,
            placeholder="visibility",
            tooltip=_tooltip,
        )
        # Expand/Collapse Button
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        self.toggle_enums_btn = ui_qt.QtWidgets.QPushButton()  # Label automatically updated when initializing
        self.toggle_enums_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_down_arrow))
        self.toggle_enums_btn.setCheckable(True)
        self.toggle_enums_btn.setChecked(self.module.enum_frame_expanded)
        self.toggle_enums_btn.clicked.connect(self.refresh_toggle_enums_collapsed_state)
        _layout.addWidget(self.toggle_enums_btn)
        # Add Enum Button
        add_enum_btn = ui_qt.QtWidgets.QPushButton("Add Enum")
        add_enum_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_add))
        add_enum_btn.setToolTip(_tooltip)
        _layout.addWidget(add_enum_btn)
        add_enum_btn.clicked.connect(self.on_add_enum_dict_clicked)

        # Scroll Area ---
        self.enum_scroll = ui_qt.QtWidgets.QScrollArea()
        self.enum_scroll.setWidgetResizable(True)
        self.enum_scroll.setMinimumHeight(220)  # minimum height, not fixed
        self.enum_container = ui_qt.QtWidgets.QWidget()
        self.enum_vbox = ui_qt.QtWidgets.QVBoxLayout(self.enum_container)
        self.enum_vbox.setContentsMargins(0, 0, 0, 0)
        self.enum_vbox.setSpacing(8)
        self.enum_vbox.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)  # Keep groups at top
        self.enum_scroll.setWidget(self.enum_container)
        self.content_layout.addWidget(self.enum_scroll)

        # Offset Section ---------------------------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Offset Conditions")
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        self.export_data_checkbox = self.add_module_attr_widget_checkbox(
            attr_name="offset_export_data", layout=_layout, nice_name="Export Offset Data"
        )
        self.export_path_field = self.add_module_attr_widget_path(
            attr_name="offset_export_path",
            layout=_layout,
            placeholder=r"{project-dir}\exports\offsets.json",
            nice_name="Export Path",
        )
        self.export_data_checkbox.toggled.connect(self.refresh_export_data_enabled)

        # Expand/Collapse Button
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        self.toggle_offsets_btn = ui_qt.QtWidgets.QPushButton()  # Label automatically updated when initializing
        self.toggle_offsets_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_down_arrow))
        self.toggle_offsets_btn.setCheckable(True)
        self.toggle_offsets_btn.setChecked(self.module.offset_frame_expanded)
        self.toggle_offsets_btn.clicked.connect(self.refresh_toggle_offsets_collapsed_state)
        _layout.addWidget(self.toggle_offsets_btn)
        # Add Offset Button
        add_offset_btn = ui_qt.QtWidgets.QPushButton("Add Offset")
        add_offset_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_add))
        add_offset_btn.setToolTip(_tooltip)
        add_offset_btn.clicked.connect(self.on_add_offset_dict_clicked)
        _layout.addWidget(add_offset_btn)

        # Scroll Area ---
        self.offset_scroll = ui_qt.QtWidgets.QScrollArea()
        self.offset_scroll.setWidgetResizable(True)
        self.offset_scroll.setMinimumHeight(220)
        self.offset_container = ui_qt.QtWidgets.QWidget()
        self.offset_vbox = ui_qt.QtWidgets.QVBoxLayout(self.offset_container)
        self.offset_vbox.setContentsMargins(0, 0, 0, 0)
        self.offset_vbox.setSpacing(8)
        self.offset_vbox.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)
        self.offset_scroll.setWidget(self.offset_container)
        self.content_layout.addWidget(self.offset_scroll)

        # Initial Refresh (Populate)
        self.refresh_current_widgets()

    # ------------------------------------- Interface Assemble -------------------------------------
    def add_enum_widget(self, enum_dict):
        """
        Create and add a new enum dictionary widget to the UI.

        Builds a framed widget with:
          - An attribute name line edit (with delete button).
          - A collapsible container for enum groups.
          - Buttons for expanding/collapsing groups and adding new groups.

        Also initializes any existing groups from the provided dictionary and
        connects signals for editing, adding, and deleting groups.

        Args:
            enum_dict (dict): The dictionary containing enum data with keys:
                - ENUM_ATTR_NAME (str): Attribute name for the enum.
                - ENUM_TARGETS (list[list[str]]): Targets for each group.
                - ENUM_DISPLAY_NAMES (list[str]): Display names for each group.
        """
        attr_name = enum_dict.get(self._KEYS.ENUM_ATTR_NAME, "")
        default_index = enum_dict.get(self._KEYS.ENUM_INDEX, 0)
        target_lists = enum_dict.get(self._KEYS.ENUM_TARGETS, [])
        display_names = enum_dict.get(self._KEYS.ENUM_DISPLAY_NAMES, [])

        dict_frame = ui_qt.QtWidgets.QFrame()
        dict_frame.setFrameShape(ui_qt.QtWidgets.QFrame.Box)
        dict_layout = ui_qt.QtWidgets.QVBoxLayout(dict_frame)

        # Header
        header_layout = ui_qt.QtWidgets.QHBoxLayout()
        dict_label = ui_qt.QtWidgets.QLabel("Enum Attribute:")
        dict_edit = ui_qt_utils.ConfirmableQLineEdit(attr_name)
        dict_edit.setPlaceholderText('Name of the new ENUM attribute. e.g. "hat". (Use camelCase)')
        _func = partial(self.on_enum_attr_name_change, target_dict=enum_dict)
        dict_edit.editingFinished.connect(_func)

        # Create Widgets
        index_label = ui_qt.QtWidgets.QLabel(f"Index:")
        index_spinbox = ui_qt.QtWidgets.QSpinBox()
        _tooltip = "Defines the default index of the created ENUM. \n"
        _tooltip += "0 would be the first element.\n1 the second, and so on"
        index_label.setToolTip(_tooltip)
        index_spinbox.setToolTip(_tooltip)
        index_spinbox.setValue(default_index)
        index_spinbox.setMinimumWidth(55)

        delete_btn = ui_qt.QtWidgets.QPushButton()
        delete_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_trash))
        header_layout.addWidget(dict_label)
        header_layout.addWidget(dict_edit)
        header_layout.addWidget(index_label)
        header_layout.addWidget(index_spinbox)
        header_layout.addWidget(delete_btn)
        dict_layout.addLayout(header_layout)

        # Groups area
        groups_layout = ui_qt.QtWidgets.QVBoxLayout()
        groups_container = ui_qt.QtWidgets.QWidget()
        groups_container.setLayout(groups_layout)
        groups_container.hide()  # start collapsed
        dict_layout.addWidget(groups_container)

        # Add Group + Collapse/Expand button
        btn_layout = ui_qt.QtWidgets.QHBoxLayout()
        toggle_btn = ui_qt.QtWidgets.QPushButton(" Expand Groups")
        toggle_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_arrow_down))
        add_group_btn = ui_qt.QtWidgets.QPushButton("Add Group")
        add_group_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_add))
        btn_layout.addWidget(toggle_btn)
        btn_layout.addWidget(add_group_btn)
        dict_layout.addLayout(btn_layout)

        # Place dict above stretch
        self.enum_vbox.addWidget(dict_frame)

        def toggle_groups(*args, force_state=None):
            """
            Toggle or force the visibility of the enum groups container.

            Updates the container’s visibility, the toggle button text, and its icon
            based on the desired state.

            Args:
                *args: Unused positional arguments (required for signal connections).
                force_state (bool, optional): If True, forces the container to be visible.
                    If False, forces it to be hidden. If None, the state is toggled
                    relative to the current visibility. Defaults to None.
            """
            # Determine the desired visibility state
            if force_state is not None:
                should_be_visible = force_state
            else:
                should_be_visible = not groups_container.isVisible()

            # Apply changes only if the state needs to be updated
            if groups_container.isVisible() != should_be_visible:
                if should_be_visible:
                    groups_container.show()
                    toggle_btn.setText(" Collapse Groups")
                    toggle_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_arrow_up))
                else:
                    groups_container.hide()
                    toggle_btn.setText(" Expand Groups")
                    toggle_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_arrow_down))

        toggle_btn.clicked.connect(toggle_groups)

        # Initial groups
        if target_lists and display_names:
            for display_name, targets in zip(display_names, target_lists):
                self.add_enum_group(
                    parent_layout=groups_layout,
                    display_name=display_name,
                    targets=targets,
                    enum_dict=enum_dict,
                )

        # Connections
        _func = partial(self.commit_enum_data_to_module)
        dict_edit.editingFinished.connect(_func)
        _func = partial(self.on_delete_enum_widget_clicked, to_delete=dict_frame)
        delete_btn.clicked.connect(_func)

        _add_num_func = partial(self.on_add_enum_group_clicked, groups_layout=groups_layout, enum_dict=enum_dict)
        add_group_btn.clicked.connect(_add_num_func)
        _force_expand_func = partial(toggle_groups, force_state=True)
        add_group_btn.clicked.connect(_force_expand_func)
        _func = partial(self.refresh_index_spinbox_limits, index_spinbox=index_spinbox, groups_layout=groups_layout)
        add_group_btn.clicked.connect(_func)

        _func = partial(self.refresh_index_spinbox_limits, index_spinbox=index_spinbox, groups_layout=groups_layout)
        index_spinbox.valueChanged.connect(_func)

    def add_enum_group(self, parent_layout, display_name, targets, enum_dict):
        """
        Create and add a new enum group widget to the given parent layout.

        Builds a framed widget with:
          - A display name field (with "None" checkbox and delete button).
          - A targets field with a "Get" button for populating from selection.

        Handles the "None" state by disabling/hiding fields and ensures that
        changes update the provided dictionary.

        Args:
            parent_layout (QLayout): The layout to insert the group widget into.
            display_name (str | None): The display name of the group, or None if disabled.
            targets (list[str] | None): The list of target strings, or None if disabled.
            enum_dict (dict): The dictionary associated with the enum data being updated.
        """
        # Determine is None
        none_checked = False
        if display_name is None or display_name is None:
            none_checked = True

        group_frame = ui_qt.QtWidgets.QFrame()
        group_frame.setFrameShape(ui_qt.QtWidgets.QFrame.StyledPanel)
        group_layout = ui_qt.QtWidgets.QVBoxLayout(group_frame)

        # Display name row
        _tooltip = "Display name used for the enum item. This is what appears in the enum drop-down combobox.\n"
        _tooltip += 'Feel free to use title case (nice names) for these. e.g. "Object 00".'
        display_layout = ui_qt.QtWidgets.QHBoxLayout()
        display_label = ui_qt.QtWidgets.QLabel("Display Name:")
        display_edit = ui_qt_utils.ConfirmableQLineEdit()
        display_label.setToolTip(_tooltip)
        display_edit.setToolTip(_tooltip)
        display_edit.setPlaceholderText('Drop-down enum name. e.g. "Object 00"')
        if display_name and isinstance(display_name, str):
            display_edit.setText(display_name)
        # None Checkbox
        _tooltip = 'If checked, this will be considered a "None" group, which means it will not drive anything.\n'
        _tooltip += "Useful when an item should not change anything in the scene, such as when nothing is selected.\n"
        _tooltip += 'e.g. groups could be "None", "Hat 1", "Hat 2". None would not change anything in the scene.'
        none_checkbox = ui_qt.QtWidgets.QCheckBox("None")
        none_checkbox.setToolTip(_tooltip)
        # Delete Button
        delete_btn = ui_qt.QtWidgets.QPushButton()
        delete_btn.setToolTip("Deletes this group.")
        delete_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_trash))
        display_layout.addWidget(display_label)
        display_layout.addWidget(display_edit)
        display_layout.addWidget(none_checkbox)
        display_layout.addWidget(delete_btn)
        group_layout.addLayout(display_layout)

        # Targets row
        _tooltip = 'Comma separated list of objects to be driven by the enum using the "Driven Attr" attribute.\n'
        _tooltip += 'For example "my_object_01, my_object_02".'
        targets_layout = ui_qt.QtWidgets.QHBoxLayout()
        targets_label = ui_qt.QtWidgets.QLabel("Targets:")
        targets_edit = ui_qt_utils.ConfirmableQLineEdit(self._list_to_string(targets))
        targets_label.setToolTip(_tooltip)
        targets_edit.setToolTip(_tooltip)
        targets_edit.setPlaceholderText('Command separated list of driven objects. e.g. "my_object_01, my_object_02"')
        # Get Object List Button (Driven Targets)
        get_objects_btn = ui_qt.QtWidgets.QPushButton("Get")
        get_objects_btn.setToolTip("Populates the target list with selected objects.")
        targets_layout.addWidget(targets_label)
        targets_layout.addWidget(targets_edit)
        targets_layout.addWidget(get_objects_btn)
        group_layout.addLayout(targets_layout)

        parent_layout.addWidget(group_frame)

        # Behavior for "None"
        def on_none_changed(state):
            """
            Handles the state change of a 'None' checkbox.

            Args:
                state (ui_qt.QtLib.CheckState): The new state of the checkbox.
                    Expected values are `ui_qt.QtLib.CheckState.Checked` or
                    `ui_qt.QtLib.CheckState.Unchecked`.
            """
            if state == ui_qt.QtLib.CheckState.Checked:
                display_edit.setText("None")
                display_edit.setDisabled(True)
                targets_edit.hide()
                get_objects_btn.hide()
                targets_label.hide()
            else:
                display_edit.setText("")
                display_edit.setDisabled(False)
                targets_edit.show()
                get_objects_btn.show()
                targets_label.show()

        # Find Index SpinBox
        container_widget = parent_layout.parentWidget()
        top_level_widget = container_widget.parentWidget()
        index_spinbox = top_level_widget.findChild(ui_qt.QtWidgets.QSpinBox)

        # Connections
        # Initialize if already "None"
        none_checkbox.stateChanged.connect(on_none_changed)
        if none_checked:
            none_checkbox.setChecked(True)
            on_none_changed(ui_qt.QtLib.CheckState.Checked)

        _func = partial(self.on_delete_enum_widget_clicked, to_delete=group_frame)
        delete_btn.clicked.connect(_func)
        _func = partial(self.refresh_index_spinbox_limits, index_spinbox=index_spinbox, groups_layout=parent_layout)
        delete_btn.clicked.connect(_func)

        # This function will now update the dict AND commit to the module
        _func_data_change = partial(self.on_enum_group_data_change, target_dict=enum_dict, groups_layout=parent_layout)

        display_edit.editingFinished.connect(_func_data_change)
        targets_edit.editingFinished.connect(_func_data_change)

        delete_btn.clicked.connect(_func_data_change)  # This is fine, deletion needs to trigger save
        none_checkbox.stateChanged.connect(_func_data_change)  # This is fine, state change needs to trigger save

        # Get Objects Button
        _get_func = partial(
            ui_qt_utils.populate_line_edit_with_selection,
            target_text_field=targets_edit,
            require_exact_count=False,
            selection_limit=None,
        )
        get_objects_btn.clicked.connect(_get_func)
        # ADDED: Ensure "Get" button also triggers a data save
        get_objects_btn.clicked.connect(_func_data_change)

    def add_offset_widget(self, offset_dict):
        """
        Create and add a new offset dictionary widget to the UI.

        Builds a framed widget with:
          - A mesh field with a "Get" button.
          - An offset transform field with "Get Position" and "Get Transform" buttons.
          - A condition field with a "Get Visibility" button.
          - A delete button.

        Tooltips are provided for guidance on usage. Signals are connected to
        commit changes to the module and handle "Get" operations.

        Args:
            offset_dict (dict): The dictionary containing offset data with keys:
                - OFFSET_MESH (str): Name of the target mesh.
                - OFFSET_TRANSFORM (tuple[float, ...]): Offset values as a tuple.
                - OFFSET_CONDITION (str): Condition string for applying the offset.
        """
        mesh_name = offset_dict.get(self._KEYS.OFFSET_MESH)
        offset_transform = offset_dict.get(self._KEYS.OFFSET_TRANSFORM)
        condition = offset_dict.get(self._KEYS.OFFSET_CONDITION)

        dict_frame = ui_qt.QtWidgets.QFrame()
        dict_frame.setFrameShape(ui_qt.QtWidgets.QFrame.Box)
        dict_layout = ui_qt.QtWidgets.QVBoxLayout(dict_frame)

        # Offset name row
        mesh_layout = ui_qt.QtWidgets.QHBoxLayout()
        _tooltip = "Name of the mesh to receive an offset. This can be the short or long name to the mesh transform.\n"
        _tooltip += 'e.g. "pSphere" or "|myGroup|pSphere"'
        mesh_label = ui_qt.QtWidgets.QLabel("Mesh:")
        mesh_edit = ui_qt_utils.ConfirmableQLineEdit(mesh_name)
        mesh_edit.setPlaceholderText('Name of the mesh that will receive an offset. e.g. "my_object"')
        mesh_label.setToolTip(_tooltip)
        mesh_edit.setToolTip(_tooltip)
        _tooltip = "Gets the selection as a target mesh and populates the text-field accordingly."
        get_mesh_btn = ui_qt.QtWidgets.QPushButton("Get")
        get_mesh_btn.setToolTip(_tooltip)
        delete_btn = ui_qt.QtWidgets.QPushButton()
        _tooltip = "Deletes this offset."
        delete_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_trash))
        delete_btn.setToolTip(_tooltip)
        mesh_layout.addWidget(mesh_label)
        mesh_layout.addWidget(mesh_edit)
        mesh_layout.addWidget(get_mesh_btn)
        mesh_layout.addWidget(delete_btn)
        dict_layout.addLayout(mesh_layout)

        # Offset Transform row
        _tooltip = "This is the offset applied through conditions to the drivers constraint of the offset.\n"
        _tooltip += 'Only numbers on a properly formated tuple wil be used. e.g. "(1, 2, 3)"\n'
        _tooltip += 'Tuples of 3, 6 or 9 numbers can be used. Each 3 numbers represent position, rotation and scale."'
        offset_transform_layout = ui_qt.QtWidgets.QHBoxLayout()
        offset_transform_label = ui_qt.QtWidgets.QLabel("Offset:")
        offset_transform_edit = ui_qt_utils.ConfirmableQLineEdit(str(tuple(offset_transform)))
        offset_transform_label.setToolTip(_tooltip)
        offset_transform_edit.setToolTip(_tooltip)
        offset_transform_edit.setPlaceholderText('Tuple used as offset. e.g. of +5 Z offset: "(0, 0, 5)"')
        get_pos_btn = ui_qt.QtWidgets.QPushButton("Get Position")
        get_pos_btn.setToolTip("Gets the position of the selected elements (local) as offset.")
        get_trans_btn = ui_qt.QtWidgets.QPushButton("Get Transform")
        get_trans_btn.setToolTip("Gets the transform (TRS) of the selected elements (local) as offset.")
        offset_transform_layout.addWidget(offset_transform_label)
        offset_transform_layout.addWidget(offset_transform_edit)
        offset_transform_layout.addWidget(get_pos_btn)
        offset_transform_layout.addWidget(get_trans_btn)
        dict_layout.addLayout(offset_transform_layout)

        # Condition row
        _tooltip = "Condition to apply the offset. Usually the visibility of another mesh.\n"
        _tooltip += "For example, when a bigger base mesh is visible, the offset should be applied.\n"
        _tooltip += "But when such mesh is not visible, the offset should be ignored."
        cond_layout = ui_qt.QtWidgets.QHBoxLayout()
        cond_label = ui_qt.QtWidgets.QLabel("Condition:")
        cond_edit = ui_qt_utils.ConfirmableQLineEdit(condition)
        cond_label.setToolTip(_tooltip)
        cond_edit.setToolTip(_tooltip)
        cond_edit.setPlaceholderText('Attribute path to the "True" condition for offset to happen. e.g. "obj.v"')
        get_vis_btn = ui_qt.QtWidgets.QPushButton("Get Visibility")
        get_vis_btn.setToolTip("Gets the visibility attribute of the selected element as condition.")
        cond_layout.addWidget(cond_label)
        cond_layout.addWidget(cond_edit)
        cond_layout.addWidget(get_vis_btn)
        dict_layout.addLayout(cond_layout)

        # Place dict above stretch
        self.offset_vbox.addWidget(dict_frame)

        # Connections
        _func = partial(self.commit_offset_data_to_module)
        mesh_edit.editingFinished.connect(_func)
        cond_edit.editingFinished.connect(_func)
        offset_transform_edit.editingFinished.connect(_func)

        _func_delete = partial(self.on_delete_offset_widget_clicked, to_delete=dict_frame)
        delete_btn.clicked.connect(_func_delete)

        _func_get_mesh = partial(ui_qt_utils.populate_line_edit_with_selection, mesh_edit)
        get_mesh_btn.clicked.connect(_func_get_mesh)
        _func_get_pos = partial(self.on_get_offset_clicked, line_edit=offset_transform_edit, mode="position")
        get_pos_btn.clicked.connect(_func_get_pos)
        _func_get_trans = partial(self.on_get_offset_clicked, line_edit=offset_transform_edit, mode="transform")
        get_trans_btn.clicked.connect(_func_get_trans)
        _func_get_vis = partial(self.on_get_condition_visibility_clicked, line_edit=cond_edit)
        get_vis_btn.clicked.connect(_func_get_vis)

        # ADDED: Ensure all "Get" buttons also trigger a data save
        get_mesh_btn.clicked.connect(_func)
        get_pos_btn.clicked.connect(_func)
        get_trans_btn.clicked.connect(_func)
        get_vis_btn.clicked.connect(_func)

    # -------------------------------------- Refresh Functions -------------------------------------

    def refresh_toggle_enums_collapsed_state(self, force_state=None):
        """
        Toggles the visibility of the enums scroll area.

        Args:
            force_state (bool, optional): If True, forces the area to expand.
                If False, forces it to collapse. If None, the state is toggled
                based on the button's checked state. Defaults to None.
        """
        if force_state is not None:
            if force_state:
                self.toggle_enums_btn.setChecked(True)
            else:
                self.toggle_enums_btn.setChecked(False)

        if self.toggle_enums_btn.isChecked():
            self.toggle_enums_btn.setText("Collapse Enums")
            self.toggle_enums_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_up_arrow))
            self.enum_scroll.show()
            self.module.enum_frame_expanded = True
        else:
            self.toggle_enums_btn.setText("Expand Enums")
            self.toggle_enums_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_down_arrow))
            self.enum_scroll.hide()
            self.module.enum_frame_expanded = False

    def refresh_toggle_offsets_collapsed_state(self, force_state=None):
        """
        Toggles the visibility of the offsets scroll area.

        Args:
            force_state (bool, optional): If True, forces the area to expand.
                If False, forces it to collapse. If None, the state is toggled
                based on the button's checked state. Defaults to None.
        """
        if force_state is not None:
            if force_state:
                self.toggle_offsets_btn.setChecked(True)
            else:
                self.toggle_offsets_btn.setChecked(False)

        if self.toggle_offsets_btn.isChecked():
            self.toggle_offsets_btn.setText("Collapse Offsets")
            self.toggle_offsets_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_up_arrow))
            self.offset_scroll.show()
            self.module.offset_frame_expanded = True
        else:
            self.toggle_offsets_btn.setText("Expand Offsets")
            self.toggle_offsets_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_down_arrow))
            self.offset_scroll.hide()
            self.module.offset_frame_expanded = False

    def refresh_export_data_enabled(self):
        """
        Enable or disable the export path field based on the export checkbox state.

        When the checkbox is checked, the field is enabled for input.
        When unchecked, the field is disabled.
        """
        self.export_path_field.setEnabled(self.export_data_checkbox.isChecked())

    def refresh_index_spinbox_limits(self, *args, index_spinbox, groups_layout):
        """
        Handle changes to an enum group layout.

        Extracts updated group data (targets and display names) from the layout
        and updates the corresponding dictionary.

        Args:
            index_spinbox (QSpinBox): The spinbox to change the maximum value.
            groups_layout (QLayout): The layout containing group widgets, used to determine maximum length.
        """
        groups_len = groups_layout.count()
        # Compensate for zero based index
        if groups_len > 0:
            groups_len -= 1
        index_spinbox.setMaximum(groups_len)
        self.commit_enum_data_to_module()

    def refresh_current_widgets(self):
        """
        Rebuild the UI widgets to match the module’s current state.

        - Creates enum and offset widgets from the dictionaries stored in the module.
        - Restores the expanded/collapsed state of the enums and offsets sections.
        - Updates the enabled state of the export path field based on the export checkbox.

        This function is typically called during initialization or when the module
        data needs to be fully re-synced with the UI.
        """
        # Load initial data
        for enum_dict in self.module.enum_dicts:
            self.add_enum_widget(enum_dict=enum_dict)
        for offset_dict in self.module.offset_dicts:
            self.add_offset_widget(offset_dict=offset_dict)
        # Expanded or Collapsed
        self.refresh_toggle_offsets_collapsed_state()
        self.refresh_toggle_enums_collapsed_state()
        # Exported State
        self.refresh_export_data_enabled()

    # ------------------------------------ Data Update Functions -----------------------------------
    def get_enum_dict_data_from_layout(self, attr_parent_layout):
        """
        Extract enum dictionary data from a parent layout.

        Iterates over all child widgets in the given layout, finding frames
        that represent enum attribute groups. For each group, retrieves
        the attribute name, targets, and display names, then assembles them
        into a dictionary.

        Args:
            attr_parent_layout (QLayout): The parent layout containing enum group widgets.

        Returns:
            list[dict]: A list of dictionaries, each containing:
                - ENUM_ATTR_NAME (str): Attribute name for the enum.
                - ENUM_TARGETS (list[list[str]] | list[None]): Targets for each enum group.
                - ENUM_DISPLAY_NAMES (list[str] | list[None]): Display names for each enum group.
        """
        # Get All Data and Assemble Dictionaries
        enum_dicts = []
        for idx in range(attr_parent_layout.count()):
            item = attr_parent_layout.itemAt(idx)

            widget = item.widget()

            # Find specific child widgets inside each frame, these are the text-field for the attributes.
            dict_widgets = widget.children()
            attr_name = None
            index = None
            enum_targets = None
            enum_display_names = None
            for dict_widget in dict_widgets:
                if isinstance(dict_widget, ui_qt.QtWidgets.QLineEdit):
                    attr_name = dict_widget.text()
                if isinstance(dict_widget, ui_qt.QtWidgets.QSpinBox):
                    index = dict_widget.value()
                if isinstance(dict_widget, ui_qt.QtWidgets.QWidget):
                    for grp_widget in dict_widget.children():
                        if isinstance(grp_widget, ui_qt.QtWidgets.QFrame):
                            grp_layout = grp_widget.parentWidget().layout()
                            enum_targets, enum_display_names = self.get_enum_group_data_from_layout(grp_layout)
            # Assemble New Dictionary
            new_dict = {
                self._KEYS.ENUM_ATTR_NAME: attr_name,
                self._KEYS.ENUM_TARGETS: enum_targets,
                self._KEYS.ENUM_DISPLAY_NAMES: enum_display_names,
                self._KEYS.ENUM_INDEX: index,
            }
            enum_dicts.append(new_dict)
        return enum_dicts

    def get_enum_group_data_from_layout(self, groups_layout):
        """
        Extract enum group data from a groups layout.

        Iterates over the child widgets in the given layout to retrieve the
        display names, target strings, and 'is none' state for each group.
        Converts text fields into structured lists and handles the case where
        a group is marked as 'None'.

        Args:
            groups_layout (QLayout): The layout containing enum group frames.

        Returns:
            tuple[list[list[str] | None], list[str | None]]:
                - A list of targets (list of strings or None) for each group.
                - A list of display names (strings or None) for each group.
        """
        enum_targets = []
        enum_display_names = []
        for idx in range(groups_layout.count()):
            item = groups_layout.itemAt(idx)
            widget = item.widget()
            frame_widgets = widget.children()
            le_list = []
            checkbox_list = []
            for frame_widget in frame_widgets:
                if isinstance(frame_widget, ui_qt.QtWidgets.QLineEdit):
                    le_list.append(frame_widget)
                if isinstance(frame_widget, ui_qt.QtWidgets.QCheckBox):
                    checkbox_list.append(frame_widget)
            if not le_list or not checkbox_list:
                continue
            # Find specific child widgets inside each list
            display_name_le, targets_le = le_list
            is_none_checkbox = checkbox_list[0]
            # Get Group Data
            is_none_group = is_none_checkbox.isChecked()
            targets_string = targets_le.text()
            targets = self._string_to_list(targets_string)
            display_name = display_name_le.text()
            if is_none_group:
                display_name = None
                targets = None
            enum_targets.append(targets)
            enum_display_names.append(display_name)
        return enum_targets, enum_display_names

    def get_offset_dict_data_from_layout(self, attr_parent_layout):
        """
        Extract offset dictionary data from a parent layout.

        Iterates over all child widgets in the given layout, retrieving
        mesh names, transforms, and conditions from line edits. Each set of
        data is assembled into a dictionary.

        Args:
            attr_parent_layout (QLayout): The parent layout containing offset data widgets.

        Returns:
            list[dict]: A list of dictionaries, each containing:
                - OFFSET_MESH (str): Name of the mesh.
                - OFFSET_TRANSFORM (tuple[float, float, float]): Transform values as a tuple.
                - OFFSET_CONDITION (str): Offset condition string.
        """
        # Get All Data and Assemble Dictionaries
        offset_dicts = []
        for idx in range(attr_parent_layout.count()):
            item = attr_parent_layout.itemAt(idx)

            widget = item.widget()

            # Find specific child widgets inside each frame, these are the text-field for the attributes.
            dict_widgets = widget.children()
            offset_mesh = None
            offset_transform = None
            offset_condition = None
            line_edits = []
            for dict_widget in dict_widgets:
                if isinstance(dict_widget, ui_qt.QtWidgets.QLineEdit):
                    line_edits.append(dict_widget)

            if not line_edits:
                continue
            offset_mesh = line_edits[0].text()
            offset_transform = line_edits[1].text()
            offset_condition = line_edits[2].text()

            # Assemble New Dictionary
            new_dict = {
                self._KEYS.OFFSET_MESH: offset_mesh,
                self._KEYS.OFFSET_TRANSFORM: self._string_to_tuple(offset_transform),
                self._KEYS.OFFSET_CONDITION: offset_condition,
            }
            offset_dicts.append(new_dict)
        return offset_dicts

    def commit_enum_data_to_module(self, *args):
        """
        Commit the latest enum dictionary data from the UI to the module.

        Extracts updated enum dictionaries from the enum parent layout and
        assigns them to the module instance.
        """
        _enum_dicts_updated = self.get_enum_dict_data_from_layout(attr_parent_layout=self.enum_vbox)
        self.module.enum_dicts = _enum_dicts_updated

    def commit_offset_data_to_module(self, *args):
        """
        Commit the latest offset dictionary data from the UI to the module.

        Extracts updated offset dictionaries from the offset parent layout and
        assigns them to the module instance.
        """
        _offset_dicts_updated = self.get_offset_dict_data_from_layout(attr_parent_layout=self.offset_vbox)
        self.module.offset_dicts = _offset_dicts_updated

    def on_add_enum_dict_clicked(self):
        """
        Handle the event of adding a new enum dictionary.

        Creates a new empty enum dictionary, adds a corresponding widget to
        the UI, refreshes the collapsed state of the enums section, and commits
        the updated enum data to the module.
        """
        _enum_dict = {
            self._KEYS.ENUM_ATTR_NAME: "",
            self._KEYS.ENUM_TARGETS: [],
            self._KEYS.ENUM_DISPLAY_NAMES: [],
        }
        self.add_enum_widget(enum_dict=_enum_dict)
        self.refresh_toggle_enums_collapsed_state(force_state=True)
        self.commit_enum_data_to_module()

    def on_add_offset_dict_clicked(self):
        """
        Handle the event of adding a new offset dictionary.

        Creates a new empty offset dictionary, adds a corresponding widget to
        the UI, refreshes the collapsed state of the offsets section, and commits
        the updated offset data to the module.
        """
        _offset_dict = {
            self._KEYS.OFFSET_MESH: "",
            self._KEYS.OFFSET_TRANSFORM: (0, 0, 0),
            self._KEYS.OFFSET_CONDITION: "",
        }
        self.add_offset_widget(offset_dict=_offset_dict)
        self.refresh_toggle_offsets_collapsed_state(force_state=True)
        self.commit_offset_data_to_module()

    def on_enum_attr_name_change(self, line_data, target_dict):
        """
        Handle changes to the enum attribute name field.

        Updates the target dictionary with the new attribute name.

        Args:
            line_data (QLineEdit): The updated attribute name from the line edit.
            target_dict (dict): The dictionary to update with the new name.
        """
        if target_dict:
            target_dict[self._KEYS.ENUM_ATTR_NAME] = line_data

    def on_enum_group_data_change(self, *args, target_dict, groups_layout):
        """
        Handle changes to an enum group layout.

        Extracts updated group data (targets and display names) from the layout,
        updates the corresponding dictionary, and commits all enum data to the
        module to ensure the changes are saved.

        Args:
            target_dict (dict): The dictionary to update with new group data.
            groups_layout (QLayout): The layout containing group widgets.
        """
        enum_targets, enum_display_names = self.get_enum_group_data_from_layout(groups_layout=groups_layout)
        target_dict[self._KEYS.ENUM_TARGETS] = enum_targets
        target_dict[self._KEYS.ENUM_DISPLAY_NAMES] = enum_display_names
        self.commit_enum_data_to_module()

    def on_add_enum_group_clicked(self, groups_layout, enum_dict):
        """
        Handle the event of adding a new enum group.

        Creates and inserts a new enum group widget into the given layout,
        then updates the target dictionary with the new group data.

        Args:
            groups_layout (QLayout): The layout to add the group to.
            enum_dict (dict): The dictionary associated with the enum data.
        """
        self.add_enum_group(
            parent_layout=groups_layout,
            display_name=None,
            targets=None,
            enum_dict=enum_dict,
        )
        self.on_enum_group_data_change(target_dict=enum_dict, groups_layout=groups_layout)

    def on_delete_enum_widget_clicked(self, to_delete):
        """
        Handle the deletion of an enum widget.

        Removes the widget from the UI and commits the updated enum data
        to the module.

        Args:
            to_delete (QWidget): The widget to remove.
        """
        self._remove_widget(to_delete)
        self.commit_enum_data_to_module()

    def on_delete_offset_widget_clicked(self, to_delete):
        """
        Handle the deletion of an offset widget.

        Removes the widget from the UI and commits the updated offset data
        to the module.

        Args:
            to_delete (QWidget): The widget to remove.
        """
        self._remove_widget(to_delete)
        self.commit_offset_data_to_module()

    @staticmethod
    def on_get_offset_clicked(line_edit, mode="position"):
        """
        Retrieves the transform values (position, rotation, and scale) of the
        selected object and displays them.

        Args:
            line_edit (QLineEdit): The line edit UI element to display the values in.
            mode (str, optional): A string to decide what attributes to retrieve.
                     Use "position" for translation only or "transform" for all nine transform attributes.
        """
        import maya.cmds as cmds

        selection = cmds.ls(selection=True) or []

        if not selection:
            logging.warning("Nothing selected.")
            return

        if len(selection) > 1:
            logging.warning("Unable to get offset, please select only one object.")
            return

        # Define attribute lists based on the 'mode' argument
        if mode == "position":
            attrs = ["tx", "ty", "tz"]
        elif mode == "transform":
            attrs = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]
        else:
            logging.error("Invalid mode. Use 'position' or 'transform'.")
            return

        # Get the values and set the text
        transform_values = [cmds.getAttr(f"{selection[0]}.{attr}") for attr in attrs]
        line_edit.setText(f"{tuple(transform_values)}")

    @staticmethod
    def on_get_condition_visibility_clicked(line_edit):
        """
        Retrieves the visibility attribute path of the selected object and populates a line edit with it.

        Args:
            line_edit (QLineEdit): The line edit UI element to display the values in.
        """
        import maya.cmds as cmds

        selection = cmds.ls(selection=True) or []

        if not selection:
            logging.warning("Nothing selected.")
            return

        if len(selection) > 1:
            logging.warning("Unable to get offset, please select only one object.")
            return

        line_edit.setText(f"{selection[0]}.visibility")

    # --------------------------------------- Utils Functions --------------------------------------
    @staticmethod
    def _list_to_string(lst):
        """
        Convert a list of items to a comma-separated string.

        Args:
            lst (list): List of items to convert.

        Returns:
            str: Comma-separated string of items.
        """
        if not lst:
            return ""
        return ", ".join(str(x) for x in lst)

    @staticmethod
    def _string_to_list(input_string):
        """
        Convert a string into a list of valid Maya names, ignoring spaces
        and invalid characters.

        Valid Maya name rules applied:
            - Only letters, numbers, and underscores.
            - Names cannot start with a number.

        Args:
            input_string (str): Input string with items separated by commas.

        Returns:
            list: List of cleaned, valid Maya-compatible names.
        """
        import re

        if not input_string:
            return []

        items = input_string.split(",")
        valid_names = []
        for item in items:
            item = item.strip()  # Remove leading/trailing spaces
            # Remove invalid characters
            item = re.sub(r"[^a-zA-Z0-9_]", "", item)
            # Ensure name does not start with a number
            if item and not item[0].isdigit():
                valid_names.append(item)

        return valid_names

    @staticmethod
    def _remove_widget(widget):
        """
        Remove a Qt widget from its parent and schedule it for deletion.

        Args:
            widget (QtWidgets.QWidget): The widget to remove and delete.
        """
        widget.setParent(None)
        widget.deleteLater()

    @staticmethod
    def _string_to_tuple(input_string, precision=4):
        """
        Converts a string of comma-separated numbers into a tuple of floats with a specified precision.

        This function gracefully handles broken or incomplete strings and rounds the output
        floats to the desired number of decimal places.

        Args:
            input_string (str): The string to be converted, e.g., "(0, 1.2, 1.5)"
            precision (int): The number of decimal places to round the floats to.

        Returns:
            tuple: A tuple containing the successfully parsed numbers. Empty tuple if failed to parse.
        """
        import re

        try:
            cleaned_string = input_string.strip().strip("() ")
            parts = re.split(r",\s*", cleaned_string)
            numbers = []

            for part in parts:
                if part:
                    try:
                        number = float(part)
                        rounded_number = round(number, precision)  # Round the float to the specified precision
                        numbers.append(rounded_number)
                    except ValueError:
                        continue
            return tuple(numbers)
        except Exception as e:
            logger.debug("Failed to convert string to tuple. Issue: {e}")
            return tuple()
