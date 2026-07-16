"""
Animation Retargeter View
"""

import gt.tools.retargeter.retargeter_constants as tools_retargeter_const
import gt.tools.retargeter.retargeter_preferences as tools_retargeter_prefs
import gt.tools.retargeter.retargeter_widget as tools_retarget_widget
import gt.ui.resource_library as ui_res_lib
import gt.core.session as core_session
import gt.ui.qt_utils as ui_qt_utils
import gt.ui.qt_import as ui_qt
from functools import partial
import logging
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModelPreference:
    """Descriptor that exposes model-owned preferences to existing view bindings."""

    def __init__(self, key):
        """Initializes the descriptor.

        Args:
            key (str): Preference key.
        """
        self.key = key

    def __get__(self, instance, owner):
        """Gets a preference from the model-owned preference store.

        Args:
            instance (RetargeterView): View instance.
            owner (type): View class.

        Returns:
            object: Preference value or this descriptor for class access.
        """
        if instance is None:
            return self
        return instance._preferences.get(self.key)

    def __set__(self, instance, value):
        """Sets a preference in the model-owned preference store.

        Args:
            instance (RetargeterView): View instance.
            value (object): Preference value.
        """
        instance._preferences.set(self.key, value)


class RetargeterView(metaclass=ui_qt_utils.MayaWindowMeta):
    """Qt view for configuring and running animation retargeting."""

    for _preference_name in tools_retargeter_prefs.PREFERENCE_DEFAULTS:
        locals()[_preference_name] = ModelPreference(_preference_name)
    del _preference_name

    def __init__(self, parent=None, controller=None, model=None, version=None):
        """
        Initialize the RetargeterView (Animation Retargeter View/UI)
        This window represents the main GUI window of the tool.

        Args:
            parent (str): Parent for this window
            controller (ResourceLibraryController): RetargeterController, not to be used.
                                                    Here to avoid the garbage collector.  Defaults to None.
            model (RetargeterModel, optional): Model that owns persistent preferences.
            version (str, optional): If provided, it will be used to determine the window title. e.g. Title - (v1.2.3)
        """
        super().__init__(parent=parent)
        self.controller = controller  # Only here so it doesn't get deleted by the garbage collectors
        self.model = model
        self._preferences = model.preferences if model else tools_retargeter_prefs.RetargeterPreferences()

        # Set Window
        window_title = "Animation Retargeter"
        if version:
            window_title += f" - (v{str(version)})"
        self.setWindowTitle(window_title)
        self.setMinimumSize(640, 560)
        self.resize(760, 700)
        self.setWindowFlags(
            self.windowFlags()
            | ui_qt.QtLib.WindowFlag.WindowMaximizeButtonHint
            | ui_qt.QtLib.WindowFlag.WindowMinimizeButtonHint
        )
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_retargeter))

        # Style Window
        stylesheet = ui_res_lib.Stylesheet.scroll_bar_base
        stylesheet += ui_res_lib.Stylesheet.maya_dialog_base
        stylesheet += ui_res_lib.Stylesheet.combobox_base
        stylesheet += ui_res_lib.Stylesheet.tree_widget_base
        stylesheet += ui_res_lib.Stylesheet.table_widget_base
        stylesheet += ui_res_lib.Stylesheet.checkbox_base
        stylesheet += ui_res_lib.Stylesheet.line_edit_base
        stylesheet += ui_res_lib.Stylesheet.spin_box_base
        stylesheet += ui_res_lib.Stylesheet.slider_base
        stylesheet += ui_res_lib.Stylesheet.tab_widget_base
        stylesheet += ui_res_lib.Stylesheet.btn_push_base
        if not core_session.is_script_in_interactive_maya():
            stylesheet += ui_res_lib.Stylesheet.menu_base
        stylesheet += """
        QLabel#RetargeterIntro {
            color: rgb(175, 175, 175);
            padding: 2px 2px 8px 2px;
        }
        QPushButton#RetargeterPrimaryButton {
            background-color: rgb(188, 188, 188);
            color: rgb(28, 28, 28);
            font-weight: bold;
            min-height: 34px;
        }
        QPushButton#RetargeterPrimaryButton:hover {
            background-color: rgb(205, 205, 205);
        }
        """
        self.setStyleSheet(stylesheet)

        # Interface items and settings
        self._default_source_namespace = "source"
        self._default_target_namespace = "target"
        self._tab_layout_list = []
        self._batch_anim_list = None
        self._definition_tab_layout_list = None
        self._browse_width = 30
        self._user_role = ui_qt.QtLib.ItemDataRole.UserRole

        # Other Elements (Defined in "Create Widgets")
        self.batch_check_box = None
        self.batch_settings_widget = None
        self.source_anim_path_widget = None
        self.target_rig_path_widget = None
        self.definition_widget = None
        self.retarget_tab_spacer = None
        self.retarget_btn = None
        self.edit_definition_widget = None
        self.new_definition_btn = None
        self.source_path_widget = None
        self.target_path_widget = None
        self.source_namespace_widget = None
        self.target_namespace_widget = None
        self.edit_mode_btn = None
        self.edit_save_definition_btn = None
        self.save_source_skel_pose_btn = None
        self.clear_source_skel_pose_btn = None
        self.mapping_table_widget = None
        self.add_controls_btn = None
        self.delete_targets_btn = None
        self.autofix_mapping_names_btn = None
        self.addon_scene_options_widget = None
        self.addon_source_setup_widget = None
        self.addon_post_bake_widget = None
        self.addon_patches_widget = None
        self.addon_python_script_widget = None
        self.option_boxes_widget = None
        self.timed_message_label = None
        self.override_options_widget = None
        # Settings
        self.reset_definition_btn = None
        self.definition_dir_widget = None
        self.skip_existing_files_chk = None
        self.multi_process_batch_mode_chk = None
        self.multi_process_max_instances_spinbox = None
        self.multi_write_log_file_chk = None

        # Populate UI
        self.create_layout()
        self.create_widgets()
        self.update_batch_settings_fields()

        # Init batch list
        if self.batch_source_folder:
            self.update_animation_list()

        # Init definition drop-down
        if self.definition_folder:
            self.update_definition_combobox()

        # Final Adjustments
        self.resize_to_available_screen()
        ui_qt_utils.center_window(self)

    def resize_to_available_screen(self):
        """Limits the preferred window size to the available screen geometry."""
        if ui_qt.IS_PYSIDE6:
            screen_geometry = ui_qt.QtGui.QGuiApplication.primaryScreen().availableGeometry()
        else:
            screen_geometry = ui_qt.QtWidgets.QDesktopWidget().availableGeometry(self)
        width = min(760, int(screen_geometry.width() * 0.8))
        height = min(700, int(screen_geometry.height() * 0.85))
        self.resize(width, height)

    def attach_model(self, model):
        """Attaches the model that owns persistent preferences.

        Args:
            model (RetargeterModel): Tool model.
        """
        self.model = model
        self._preferences = model.preferences

    def eventFilter(self, object, event):
        """
        Retargeter View Event Filter.

        Args:
            object (QObject): The object that the event is being filtered for.
            event (QEvent): The event to be processed.
        """
        if event.type() == ui_qt.QtCore.QEvent.ContextMenu and object is self._batch_anim_list:
            batch_list_menu = ui_qt.QtWidgets.QMenu()

            action_select_all = ui_qt.QtLib.QtGui.QAction("Select all")
            _select_all_func = partial(self.select_all_batch_list_items, True)
            action_select_all.triggered.connect(_select_all_func)
            batch_list_menu.addAction(action_select_all)
            action_unselect_all = ui_qt.QtLib.QtGui.QAction("Unselect all")
            _unselect_all_func = partial(self.select_all_batch_list_items, False)
            action_unselect_all.triggered.connect(_unselect_all_func)
            batch_list_menu.addAction(action_unselect_all)

            if batch_list_menu.exec_(event.globalPos()):
                item = object.itemAt(event.pos())
            return True

        return super().eventFilter(object, event)

    def create_layout(self):
        """Create the layout for the window."""
        # Main Layout
        main_layout = ui_qt.QtWidgets.QVBoxLayout()

        # Top Tabs
        _tab_title_list = ["Retarget", "Definition Editor", "Preferences"]
        tab_widget = tools_retarget_widget.TabWidget(self, _tab_title_list, margin=10)
        _tab_func = partial(
            tools_retarget_widget.set_value_from_field,
            parent=self,
            var="active_tab",
            field=tab_widget,
        )
        tab_widget.currentChanged.connect(_tab_func)
        self._tab_layout_list = tab_widget.layout_list
        tab_widget.setCurrentIndex(self.active_tab)

        # Label widget for timed messages
        self.timed_message_label = tools_retarget_widget.TimedLabel(self)

        main_layout.setContentsMargins(12, 10, 12, 12)
        main_layout.setSpacing(0)
        main_layout.addWidget(tab_widget)
        main_layout.addWidget(self.timed_message_label)
        self.setLayout(main_layout)

    def create_widgets(self):
        """Creates the widgets for the defined tabs."""

        # Retarget Tab ------------------------------------------------
        self.add_retarget_tab_widgets(self._tab_layout_list[0])

        # Definition Tab ----------------------------------------------
        self.add_setup_tab_widgets(self._tab_layout_list[1])

        # Settings Tab ------------------------------------------------
        self.add_settings_tab_widgets(self._tab_layout_list[2])

    def add_retarget_tab_widgets(self, layout):
        """
        Adds the required widgets to the retarget tab.
        Args:
            layout (QLayout): The layout to which the retarget tab widgets will be added.
        """
        _label_width = 100

        intro_label = ui_qt.QtWidgets.QLabel(
            "Choose an animation, target rig, and definition. Use folder mode to process multiple files."
        )
        intro_label.setObjectName("RetargeterIntro")
        intro_label.setWordWrap(True)

        # ---- Batch check box
        batch_check_box_layout = ui_qt.QtWidgets.QHBoxLayout()
        batch_check_box_layout.setAlignment(ui_qt.QtCore.Qt.AlignLeft)
        self.batch_check_box = ui_qt.QtWidgets.QCheckBox("Process a Folder (Batch)")
        self.batch_check_box.setToolTip("Process checked animation files from a source folder.")
        self.batch_check_box.setChecked(self.batch_status)
        self.batch_check_box.stateChanged.connect(self.toggle_batch_settings)
        batch_check_box_layout.addWidget(self.batch_check_box)

        # ---- Batch settings widget
        self.batch_settings_widget = ui_qt.QtWidgets.QWidget()
        batch_layout = ui_qt.QtWidgets.QVBoxLayout()
        batch_layout.setContentsMargins(0, 0, 0, 0)
        self.batch_settings_widget.setLayout(batch_layout)

        self._batch_anim_list = ui_qt.QtWidgets.QListWidget()
        self._batch_anim_list.installEventFilter(self)
        self._batch_anim_list.setMinimumSize(20, 20)
        self._batch_anim_list.setSpacing(1)
        batch_list_layout = ui_qt.QtWidgets.QHBoxLayout()
        batch_list_layout.addWidget(self._batch_anim_list)
        batch_list_layout.setContentsMargins(_label_width + 5, 0, self._browse_width + 9, 0)

        batch_source_dir_widget = tools_retarget_widget.TextBrowseFileWidget(
            self,
            var_name="batch_source_folder",
            nice_name="Source Folder",
            var_value=self.batch_source_folder,
            file_filter=tools_retargeter_const.RetargeterConstants.RETARGET_FILTER,
            label_width=_label_width,
            browse_width=self._browse_width,
            dir_only=True,
        )
        batch_source_dir_widget.text_field.textChanged.connect(self.update_animation_list)

        batch_target_dir_widget = tools_retarget_widget.TextBrowseFileWidget(
            self,
            var_name="batch_target_folder",
            nice_name="Target Folder",
            var_value=self.batch_target_folder,
            file_filter=tools_retargeter_const.RetargeterConstants.RETARGET_FILTER,
            label_width=_label_width,
            browse_width=self._browse_width,
            dir_only=True,
        )

        batch_layout.addWidget(batch_source_dir_widget)
        batch_layout.addLayout(batch_list_layout)
        batch_layout.addWidget(batch_target_dir_widget)

        # ---- Paths
        self.source_anim_path_widget = tools_retarget_widget.TextBrowseFileWidget(
            self,
            var_name="source_animation_path",
            nice_name="Source Animation",
            var_value=self.source_animation_path,
            file_filter=tools_retargeter_const.RetargeterConstants.RETARGET_FILTER,
            label_width=_label_width,
            browse_width=self._browse_width,
        )
        self.target_rig_path_widget = tools_retarget_widget.TextBrowseFileWidget(
            self,
            var_name="target_rig_path",
            nice_name="Target Rig",
            var_value=self.target_rig_path,
            file_filter=tools_retargeter_const.RetargeterConstants.RETARGET_FILTER,
            label_width=_label_width,
            browse_width=self._browse_width,
        )

        self.definition_widget = tools_retarget_widget.DropDownWidget(
            self,
            var_name="definition_filename",
            nice_name="Definition",
            tooltip="Retarget definition",
            label_width=_label_width,
            end_margin=self._browse_width,
        )

        self.override_options_widget = tools_retarget_widget.OverrideOptionsWidget(self)

        # ---- Stretch
        self.retarget_tab_spacer = ui_qt.QtWidgets.QSpacerItem(
            20, 40, ui_qt.QtWidgets.QSizePolicy.Minimum, ui_qt.QtWidgets.QSizePolicy.Expanding
        )

        # ---- Buttons
        self.retarget_btn = ui_qt.QtWidgets.QPushButton("Retarget")
        self.retarget_btn.setObjectName("RetargeterPrimaryButton")
        self.retarget_btn.setToolTip("Run retargeting with the settings above.")

        layout.addWidget(intro_label)
        layout.addWidget(tools_retarget_widget.HLineWidget(label_text="Source Animation"))
        layout.addLayout(batch_check_box_layout)
        layout.addWidget(self.batch_settings_widget)
        layout.addWidget(self.source_anim_path_widget)
        layout.addWidget(tools_retarget_widget.HLineWidget(label_text="Target Setup"))
        layout.addWidget(self.target_rig_path_widget)
        layout.addWidget(self.definition_widget)
        layout.addWidget(tools_retarget_widget.HLineWidget(label_text="Output Options"))
        layout.addWidget(self.override_options_widget)
        layout.addItem(self.retarget_tab_spacer)
        layout.addWidget(self.retarget_btn)

    def add_setup_tab_widgets(self, layout):
        """
        Adds the required widgets to the definition setup tab.
        Args:
            layout (QLayout): The parent layout where the widgets will be added.
        """

        _label_width = 110

        _definition_tab_title_list = [
            "Mapping",
            "Scene",
            "Source Setup",
            "Post Bake",
            "Patches",
            "Scripts",
        ]
        definition_tab_widget = tools_retarget_widget.TabWidget(self, _definition_tab_title_list, margin=4)
        self._definition_tab_layout_list = definition_tab_widget.layout_list

        self.edit_definition_widget = tools_retarget_widget.DropDownWidget(
            self,
            var_name="definition_setup_filename",
            nice_name="Definition",
            tooltip="Retarget definition",
            label_width=_label_width,
        )
        # New-definition button
        self.new_definition_btn = ui_qt.QtWidgets.QPushButton()
        self.new_definition_btn.setFixedWidth(28)
        self.new_definition_btn.setToolTip("Create a new definition")
        self.new_definition_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_plus))
        self.edit_definition_widget.layout.addWidget(self.new_definition_btn)

        self.source_path_widget = tools_retarget_widget.TextBrowseFileWidget(
            self,
            var_name="source_path",
            nice_name="Source Rig",
            file_filter=tools_retargeter_const.RetargeterConstants.RETARGET_FILTER,
            label_width=_label_width,
            browse_width=self._browse_width,
        )

        self.target_path_widget = tools_retarget_widget.TextBrowseFileWidget(
            self,
            var_name="target_path",
            nice_name="Target Rig",
            file_filter=tools_retargeter_const.RetargeterConstants.RETARGET_FILTER,
            label_width=_label_width,
            browse_width=self._browse_width,
        )

        _init_source_namespace_value = self._default_source_namespace
        if self.source_namespace:
            _init_source_namespace_value = self.source_namespace
        self.source_namespace_widget = tools_retarget_widget.TextBrowseFileWidget(
            self,
            var_name="source_namespace",
            var_value=_init_source_namespace_value,
            browse=False,
            label_width=_label_width,
            browse_width=self._browse_width,
            align_end=True,
        )
        _init_target_namespace_value = self._default_target_namespace
        if self.target_namespace:
            _init_target_namespace_value = self.target_namespace
        self.target_namespace_widget = tools_retarget_widget.TextBrowseFileWidget(
            self,
            var_name="target_namespace",
            var_value=_init_target_namespace_value,
            browse=False,
            label_width=_label_width,
            browse_width=self._browse_width,
            align_end=True,
        )

        # ---- Edit Mode (Import/Reload)
        self.edit_mode_btn = ui_qt.QtWidgets.QPushButton("Load Definition in Scene")
        self.edit_mode_btn.setToolTip("Import or reload the source and target rigs for editing.")

        linked_check_box = ui_qt.QtWidgets.QCheckBox("Linked")
        linked_check_box.setChecked(self.linked_status)
        linked_check_box.setSizePolicy(ui_qt.QtWidgets.QSizePolicy.Fixed, ui_qt.QtWidgets.QSizePolicy.Fixed)
        _btn_func = partial(
            tools_retarget_widget.set_value_from_field, parent=self, var="linked_status", field=linked_check_box
        )
        linked_check_box.stateChanged.connect(_btn_func)
        edit_mode_layout = ui_qt.QtWidgets.QHBoxLayout()
        edit_mode_layout.addWidget(self.edit_mode_btn)
        edit_mode_layout.addWidget(linked_check_box)

        # ---- Save Button
        self.edit_save_definition_btn = ui_qt.QtWidgets.QPushButton("Save Definition")
        self.edit_save_definition_btn.setObjectName("RetargeterPrimaryButton")
        self.edit_save_definition_btn.setToolTip("Save the selected definition with the current mapping and settings.")

        # ---- Skeleton Pose Buttons
        skel_pose_layout = ui_qt.QtWidgets.QHBoxLayout()
        skel_pose_layout.setContentsMargins(0, 0, 0, 0)
        skel_pose_layout.setSpacing(8)
        self.save_source_skel_pose_btn = ui_qt.QtWidgets.QPushButton("Capture Source Pose")
        self.save_source_skel_pose_btn.setToolTip("Save the source skeleton current pose.")
        self.clear_source_skel_pose_btn = ui_qt.QtWidgets.QPushButton("Clear Source Pose")
        self.clear_source_skel_pose_btn.setToolTip("Clear the source skeleton current pose.")
        skel_pose_layout.addWidget(self.save_source_skel_pose_btn)
        skel_pose_layout.addWidget(self.clear_source_skel_pose_btn)

        # ---- Table
        self.mapping_table_widget = tools_retarget_widget.MappingTableWidget(self)

        # ---- Setup Panel
        _panel_width = 160

        layout_setup_scroll = ui_qt.QtWidgets.QVBoxLayout()
        layout_setup_scroll.setContentsMargins(0, 0, 0, 0)
        layout_setup_scroll.setSpacing(2)
        setup_scroll_area = ui_qt.QtWidgets.QScrollArea()
        setup_scroll_area.setWidgetResizable(True)
        setup_scroll_area.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)
        layout_setup_scroll.addWidget(setup_scroll_area)

        grp_options_widget = ui_qt.QtWidgets.QGroupBox("Mapping Tools")
        layout_options = ui_qt.QtWidgets.QVBoxLayout()
        grp_options_widget.setLayout(layout_options)
        setup_scroll_area.setWidget(grp_options_widget)

        self.add_controls_btn = ui_qt.QtWidgets.QPushButton("Add Selected Controls")
        self.delete_targets_btn = ui_qt.QtWidgets.QPushButton("Remove Selected Targets")
        self.autofix_mapping_names_btn = ui_qt.QtWidgets.QPushButton("Resolve Mapping Names")
        self.option_boxes_widget = tools_retarget_widget.DefinitionOptionsWidget(self)

        layout_options.addWidget(self.add_controls_btn)
        layout_options.addWidget(self.delete_targets_btn)
        layout_options.addWidget(tools_retarget_widget.HLineWidget())
        layout_options.addWidget(self.autofix_mapping_names_btn)
        layout_options.addWidget(tools_retarget_widget.HLineWidget())
        layout_options.addWidget(self.option_boxes_widget)
        layout_options.addStretch()

        # ---- Select scene targets and sources checkboxes
        layout_select_scene_objs = ui_qt.QtWidgets.QHBoxLayout()
        layout_select_scene_objs.setContentsMargins(0, 0, 0, 0)
        layout_select_scene_objs.setSpacing(4)
        layout_setup_scroll.addLayout(layout_select_scene_objs)

        select_scene_targets_check_box = ui_qt.QtWidgets.QCheckBox("Select Scene Targets")
        select_scene_targets_check_box.setToolTip("Select also scene targets when table targets are selected.")
        select_scene_targets_check_box.setChecked(self.select_scene_targets)
        select_scene_targets_check_box.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Fixed, ui_qt.QtWidgets.QSizePolicy.Fixed
        )
        _check_func = partial(
            tools_retarget_widget.set_value_from_field,
            parent=self,
            var="select_scene_targets",
            field=select_scene_targets_check_box,
        )
        select_scene_targets_check_box.stateChanged.connect(_check_func)
        layout_select_scene_objs.addWidget(select_scene_targets_check_box)

        select_scene_sources_check_box = ui_qt.QtWidgets.QCheckBox("Select Scene Sources")
        select_scene_sources_check_box.setToolTip("Select also scene sources when table sources are selected.")
        select_scene_sources_check_box.setChecked(self.select_scene_sources)
        select_scene_sources_check_box.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Fixed, ui_qt.QtWidgets.QSizePolicy.Fixed
        )
        _check_func = partial(
            tools_retarget_widget.set_value_from_field,
            parent=self,
            var="select_scene_sources",
            field=select_scene_sources_check_box,
        )
        select_scene_sources_check_box.stateChanged.connect(_check_func)
        layout_select_scene_objs.addWidget(select_scene_sources_check_box)
        layout_select_scene_objs.addStretch()

        # ---- Fill setup tab
        layout_setup_mapping = ui_qt.QtWidgets.QHBoxLayout()
        layout_setup_mapping.setContentsMargins(0, 0, 0, 0)
        layout_setup_mapping.setSpacing(2)
        layout_setup_mapping.addWidget(self.mapping_table_widget)
        layout_setup_mapping.addLayout(layout_setup_scroll)
        self._definition_tab_layout_list[0].addLayout(layout_setup_mapping)

        # ---- Addons
        # -------------------- Scene Options --------------------
        addon_scene_options_scroll_area = ui_qt.QtWidgets.QScrollArea()
        addon_scene_options_scroll_area.setWidgetResizable(True)
        addon_scene_options_scroll_area.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)
        self.addon_scene_options_widget = tools_retarget_widget.AddonSceneOptionsWidget(self)
        addon_scene_options_scroll_area.setWidget(self.addon_scene_options_widget)
        self._definition_tab_layout_list[1].addWidget(addon_scene_options_scroll_area)

        # -------------------- Source Setup --------------------
        addon_source_setup_scroll_area = ui_qt.QtWidgets.QScrollArea()
        addon_source_setup_scroll_area.setWidgetResizable(True)
        addon_source_setup_scroll_area.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)
        self.addon_source_setup_widget = tools_retarget_widget.AddonSourceSetupWidget(self)
        addon_source_setup_scroll_area.setWidget(self.addon_source_setup_widget)
        self._definition_tab_layout_list[2].addWidget(addon_source_setup_scroll_area)

        # -------------------- Post Bake --------------------
        addon_post_bake_scroll_area = ui_qt.QtWidgets.QScrollArea()
        addon_post_bake_scroll_area.setWidgetResizable(True)
        addon_post_bake_scroll_area.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)
        self.addon_post_bake_widget = tools_retarget_widget.AddonPostBakeWidget(self)
        addon_post_bake_scroll_area.setWidget(self.addon_post_bake_widget)
        self._definition_tab_layout_list[3].addWidget(addon_post_bake_scroll_area)

        # -------------------- Patches --------------------
        addon_patches_scroll_area = ui_qt.QtWidgets.QScrollArea()
        addon_patches_scroll_area.setWidgetResizable(True)
        addon_patches_scroll_area.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)
        self.addon_patches_widget = tools_retarget_widget.AddonPatchesWidget(self)
        addon_patches_scroll_area.setWidget(self.addon_patches_widget)
        self._definition_tab_layout_list[4].addWidget(addon_patches_scroll_area)

        # -------------------- Python Scripts --------------------
        addon_python_script_scroll_area = ui_qt.QtWidgets.QScrollArea()
        addon_python_script_scroll_area.setWidgetResizable(True)
        addon_python_script_scroll_area.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)
        self.addon_python_script_widget = tools_retarget_widget.AddonPythonScriptWidget(self)
        addon_python_script_scroll_area.setWidget(self.addon_python_script_widget)
        self._definition_tab_layout_list[5].addWidget(addon_python_script_scroll_area)

        layout.addWidget(self.edit_definition_widget)
        layout.addWidget(tools_retarget_widget.HLineWidget())
        layout.addWidget(self.source_path_widget)
        layout.addWidget(self.target_path_widget)
        layout.addWidget(self.source_namespace_widget)
        layout.addWidget(self.target_namespace_widget)
        layout.addLayout(edit_mode_layout)
        layout.addWidget(self.edit_save_definition_btn)
        layout.addLayout(skel_pose_layout)
        layout.addWidget(tools_retarget_widget.HLineWidget())
        layout.addWidget(definition_tab_widget)

    def add_settings_tab_widgets(self, layout):
        """
        Add the required widgets to the settings tab layout.

        This includes a "General Settings" group for the definition folder
        and file skipping, and a "Batch Processing" group.

        Args:
            layout (PySide2.QtWidgets.QLayout): The layout to which the widgets
                                                 will be added.
        """
        # -------------------------------------- General Settings --------------------------------------
        general_group_box = ui_qt.QtWidgets.QGroupBox("Definitions and Output")
        general_layout = ui_qt.QtWidgets.QVBoxLayout()

        # --- Layout Spacing ---
        general_layout.addSpacing(5)
        general_layout.setSpacing(6)

        # --- Definition Folder ---
        if not self.definition_folder:
            _default_definition_folder = tools_retargeter_const.RetargeterConstants.DEFAULT_DEFINITION_FOLDER
            self.definition_folder = _default_definition_folder

        _label_width = 110
        self.definition_dir_widget = tools_retarget_widget.TextBrowseFileWidget(
            self,
            var_name="definition_folder",
            var_value=self.definition_folder,
            file_filter=tools_retargeter_const.RetargeterConstants.DATA_FILTER,
            label_width=_label_width,
            browse_width=self._browse_width,
            dir_only=True,
        )

        # Reset folder button
        self.reset_definition_btn = ui_qt.QtWidgets.QPushButton()
        self.reset_definition_btn.setFixedWidth(28)
        self.reset_definition_btn.setToolTip("Reset definition folder")
        self.reset_definition_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_reset))
        self.definition_dir_widget.layout.addWidget(self.reset_definition_btn)
        self.definition_dir_widget.layout.addSpacing(5)

        general_layout.addWidget(self.definition_dir_widget)

        # --- Skip Existing Checkbox ---
        self.skip_existing_files_chk = ui_qt.QtWidgets.QCheckBox("Skip Existing Files")
        self.skip_existing_files_chk.setToolTip(
            "If checked, any existing retargeted files with the same name will be skipped and NOT overwritten."
        )
        # Set checkbox state from the existing attribute
        self.skip_existing_files_chk.setChecked(self.skip_existing_files)
        general_layout.addWidget(self.skip_existing_files_chk)

        # Finalize General GroupBox
        general_group_box.setLayout(general_layout)
        layout.addWidget(general_group_box)

        # -------------------------------------- Batch Processing --------------------------------------
        batch_group_box = ui_qt.QtWidgets.QGroupBox("Multi-Process Batch (Experimental)")
        batch_layout = ui_qt.QtWidgets.QVBoxLayout()

        # --- Layout Spacing ---
        batch_layout.addSpacing(5)
        batch_layout.setSpacing(6)  # Add spacing between batch widgets

        batch_description = ui_qt.QtWidgets.QLabel(
            "Runs files in separate Maya processes. Increase the limit gradually for your workstation."
        )
        batch_description.setWordWrap(True)
        batch_description.setStyleSheet("color: grey;")
        batch_layout.addWidget(batch_description)

        # --- Create a horizontal layout for all batch controls ---
        batch_controls_layout = ui_qt.QtWidgets.QHBoxLayout()

        # --- Enable Batch Mode Checkbox ---
        self.multi_process_batch_mode_chk = ui_qt.QtWidgets.QCheckBox("Enable")
        self.multi_process_batch_mode_chk.setToolTip(
            "EXPERIMENTAL: Launches multiple Maya instances to process files in parallel.\n" "Use with caution."
        )
        # Set checkbox state from the existing attribute
        self.multi_process_batch_mode_chk.setChecked(self.multi_process_batch)
        batch_controls_layout.addWidget(self.multi_process_batch_mode_chk)

        # --- Max Instances Label ---
        max_instances_label = ui_qt.QtWidgets.QLabel("Concurrent Maya Processes:")
        max_instances_label.setContentsMargins(10, 0, 0, 0)
        batch_controls_layout.addWidget(max_instances_label)

        # --- Max Instances SpinBox ---
        self.multi_process_max_instances_spinbox = ui_qt.QtWidgets.QSpinBox()
        self.multi_process_max_instances_spinbox.setRange(1, 20)
        self.multi_process_max_instances_spinbox.setToolTip("Maximum number of concurrent Maya instances (1-20).")
        # Set spinbox value from the existing attribute
        self.multi_process_max_instances_spinbox.setValue(self.multi_process_max_instances)
        batch_controls_layout.addWidget(self.multi_process_max_instances_spinbox)
        batch_controls_layout.addStretch()

        # Add the horizontal layout to the group's main vertical layout
        batch_layout.addLayout(batch_controls_layout)

        # --- Write Log File Checkbox ---
        self.multi_write_log_file_chk = ui_qt.QtWidgets.QCheckBox("Write Log Files")
        self.multi_write_log_file_chk.setToolTip(
            "If checked, log files (.log) will be created in case errors are detected."
        )
        # Set checkbox state from the existing attribute (assuming self.multi_write_log exists)
        self.multi_write_log_file_chk.setChecked(self.multi_write_log_file)
        batch_layout.addWidget(self.multi_write_log_file_chk)

        # --- Finalize GroupBox ---
        batch_group_box.setLayout(batch_layout)
        layout.addWidget(batch_group_box)

        # --- Slot Functions for Connections ---
        def _on_skip_existing_changed(checked):
            """
            Slot method for when the 'Skip Existing Files' checkbox is toggled.

            Updates the 'skip_existing_files' attribute and saves preferences.

            Args:
                checked (bool): The new state of the checkbox.
            """
            self.skip_existing_files = checked
            self.save_preferences()

        def _on_batch_mode_changed(checked):
            """
            Slot method for when the 'Enable Multi-Process' checkbox is toggled.

            Updates the 'multi_process_batch' attribute, enables/disables the
            max instances UI widgets, and saves preferences.

            Args:
                checked (bool): The new state of the checkbox.
            """
            self.multi_process_batch = checked
            max_instances_label.setEnabled(checked)
            self.multi_process_max_instances_spinbox.setEnabled(checked)
            self.save_preferences()

        def _on_max_instances_changed(value):
            """
            Slot method for when the 'Max Instances' spinbox value is changed.

            Updates the 'multi_process_max_instances' attribute and saves
            preferences.

            Args:
                value (int): The new value from the spinbox.
            """
            self.multi_process_max_instances = value
            self.save_preferences()

        def _on_write_log_file_changed(checked):
            """
            Slot method for when the 'Write Log File' checkbox is toggled.

            Updates the 'multi_write_log_file' attribute and saves preferences.

            Args:
                checked (bool): The new state of the checkbox.
            """
            self.multi_write_log_file = checked
            self.save_preferences()

        # --- Connections and Initial State ---
        # Set initial UI state based on loaded attributes
        max_instances_label.setEnabled(self.multi_process_batch)
        self.multi_process_max_instances_spinbox.setEnabled(self.multi_process_batch)

        # Connect signals to new slots
        self.skip_existing_files_chk.toggled.connect(_on_skip_existing_changed)
        self.multi_process_batch_mode_chk.toggled.connect(_on_batch_mode_changed)
        self.multi_process_max_instances_spinbox.valueChanged.connect(_on_max_instances_changed)
        self.multi_write_log_file_chk.toggled.connect(_on_write_log_file_changed)

        # --- Add stretch to push all content to the top ---
        layout.addStretch()

    def set_source_path(self, source_path):
        """Sets the edit source path.

        Args:
            source_path (str): source path to set
        """
        if not isinstance(source_path, str):
            logger.debug("Given source path is not a string.")
            self.source_path_widget.text_field.setText("")
            return

        source_path = source_path.replace("\\", "/")

        if not os.path.isfile(source_path):
            logger.warning(f"Given source path is missing: {source_path}")
            self.source_path_widget.text_field.setText(source_path)
            return

        # Valid path found
        self.source_path_widget.text_field.setText(source_path)

    def set_target_path(self, target_path):
        """Sets the edit target path.

        Args:
            target_path (str): target path to set
        """
        if not isinstance(target_path, str):
            logger.debug("Given target path is not a string.")
            self.target_path_widget.text_field.setText("")
            return

        target_path = target_path.replace("\\", "/")

        if not os.path.isfile(target_path):
            logger.warning(f"Given target path is missing: {target_path}")
            self.target_path_widget.text_field.setText(target_path)
            return

        # Valid path found
        self.target_path_widget.text_field.setText(target_path)

    def set_target_rig_path(self, target_rig_path):
        """Sets the target rig path in the retarget tab.

        Args:
            target_rig_path (str): target rig path to set
        """
        if not isinstance(target_rig_path, str):
            logger.debug("Given target rig path is not a string.")
            self.target_rig_path_widget.text_field.setText("")
            return

        target_rig_path = target_rig_path.replace("\\", "/")

        if not os.path.isfile(target_rig_path):
            logger.warning(f"Given target rig path is missing: {target_rig_path}")
            self.target_rig_path_widget.text_field.setText(target_rig_path)
            return

        # Valid path found
        self.target_rig_path_widget.text_field.setText(target_rig_path)

    def set_source_namespace(self, source_namespace):
        """Sets the source namespace.

        Args:
            source_namespace (str): source namespace to set
        """
        self.source_namespace_widget.text_field.setText(source_namespace)

    def set_target_namespace(self, target_namespace):
        """Sets the target namespace.

        Args:
            target_namespace (str): target namespace to set
        """
        self.target_namespace_widget.text_field.setText(target_namespace)

    def update_animation_list(self):
        """Updates the list of animation files to retarget in batch mode."""

        self._batch_anim_list.clear()
        _source_dir = self.batch_source_folder

        if not _source_dir:
            return
        if not os.path.isdir(_source_dir):
            return

        # Get source files
        _source_file_list = []
        for filename in os.listdir(_source_dir):
            _file_ext = filename.split(".")[-1]
            _anim_extension_list = [
                tools_retargeter_const.RetargeterConstants.RIG_MA_EXTENSION,
                tools_retargeter_const.RetargeterConstants.RIG_MB_EXTENSION,
                tools_retargeter_const.RetargeterConstants.FBX_EXTENSION,
            ]
            if _file_ext.lower() in _anim_extension_list:
                file_path = os.path.normpath(os.path.join(_source_dir, filename))
                _source_file_list.append(file_path)

        # Populate list widget
        for source_path in _source_file_list:
            text = os.path.basename(source_path)
            item = ui_qt.QtWidgets.QListWidgetItem(text)
            item.setData(self._user_role, source_path)
            item.setCheckState(ui_qt.QtCore.Qt.Checked)
            self._batch_anim_list.addItem(item)

    def update_definition_combobox(self):
        """Updates the definition dropdown with the files found in the definition folder."""

        # Disable signal
        self.definition_widget.combobox.blockSignals(True)
        self.edit_definition_widget.combobox.blockSignals(True)

        # Get values - attempt to apply/re-apply default value
        _default_option = None
        if not self.definition_filename:
            _index = self.definition_widget.combobox.currentIndex()
            _current_combobox_data = self.definition_widget.combobox.itemData(_index)
            if _current_combobox_data:
                self.definition_filename = _current_combobox_data
        # strip extension if it exists
        if self.definition_filename:
            _default_option = self.definition_filename.split(".")[0]

        _default_edit_option = None
        if not self.definition_setup_filename:
            _index = self.edit_definition_widget.combobox.currentIndex()
            _current_edit_combobox_data = self.edit_definition_widget.combobox.itemData(_index)
            if _current_edit_combobox_data:
                self.definition_setup_filename = _current_edit_combobox_data
        # strip extension if it exists
        if self.definition_setup_filename:
            _default_edit_option = self.definition_setup_filename.split(".")[0]

        # Clear
        self.definition_widget.combobox.clear()
        self.edit_definition_widget.combobox.clear()

        # Get definition folder
        _definition_dir = self.definition_folder
        if not _definition_dir:
            return
        if not os.path.isdir(_definition_dir):
            return

        # Get definition files
        _definition_file_list = []
        for filename in os.listdir(_definition_dir):
            file_label = filename.split(".")[0]
            _file_ext = filename.split(".")[-1]
            if _file_ext in [tools_retargeter_const.RetargeterConstants.DATA_EXTENSION, "json"]:
                _definition_file_list.append([file_label, filename])  # label - data

        # Populate combobox
        self.definition_widget.combobox.setEnabled(True)
        self.edit_definition_widget.combobox.setEnabled(True)
        if not _definition_file_list:
            _definition_file_list = [
                "<No definition files found. Select a different definition folder.>",
                None,
            ]
            self.definition_widget.combobox.setEnabled(False)
            self.edit_definition_widget.combobox.setEnabled(False)
        self.definition_widget.populate_list(
            _definition_file_list,
            default_option=_default_option,
            add_none=False,
        )
        self.edit_definition_widget.populate_list(
            _definition_file_list,
            default_option=_default_edit_option,
            add_none=False,
        )

        # Check and update definition filenames
        _index = self.definition_widget.combobox.currentIndex()
        _current_combobox_data = self.definition_widget.combobox.itemData(_index)
        if self.definition_filename != _current_combobox_data:
            self.definition_filename = _current_combobox_data
        _index = self.edit_definition_widget.combobox.currentIndex()
        _current_edit_combobox_data = self.edit_definition_widget.combobox.itemData(_index)
        if self.definition_setup_filename != _current_edit_combobox_data:
            self.definition_setup_filename = _current_edit_combobox_data

        # Enable signal
        self.definition_widget.combobox.blockSignals(False)
        self.edit_definition_widget.combobox.blockSignals(False)

    def toggle_batch_settings(self):
        """Toggles batch status."""
        tools_retarget_widget.set_value_from_field(parent=self, var="batch_status", field=self.batch_check_box)
        self.update_batch_settings_fields()

    def select_all_batch_list_items(self, status=True):
        """
        Select or unselect all items of the batch animation list.

        Args:
            status (bool): check or uncheck.
        """
        if status:
            _state = ui_qt.QtCore.Qt.Checked
        else:
            _state = ui_qt.QtCore.Qt.Unchecked
        [self._batch_anim_list.item(i).setCheckState(_state) for i in range(self._batch_anim_list.count())]

    def update_batch_settings_fields(self):
        """Applies batch status."""
        if self.batch_status:
            self.batch_settings_widget.setMinimumSize(80, 120)
            self.batch_settings_widget.setMaximumSize(9999, 9999)
            self.retarget_tab_spacer.changeSize(0, 0)
            self.source_anim_path_widget.setFixedHeight(0)
        else:
            self.batch_settings_widget.setFixedHeight(0)
            self.source_anim_path_widget.setFixedHeight(35)
            self.retarget_tab_spacer.changeSize(
                20, 40, ui_qt.QtWidgets.QSizePolicy.Minimum, ui_qt.QtWidgets.QSizePolicy.Expanding
            )

    def update_mapping_table(
        self, health_score_dict=None, source_joints=None, source_namespace=None, target_namespace=None
    ):
        """Updates the mapping table widget.

        Args:
            health_score_dict (dict, optional): health score dictionary from model.
                                                If None, the function will clear the table.
            source_joints (list): source joint list from the scene.
            source_namespace (str): source namespace to use.
            target_namespace (str): target namespace to use.
        """
        self.mapping_table_widget.update_table(health_score_dict=health_score_dict, source_joints=source_joints)

    def get_batch_list_selected_paths(self):
        """Gets the selected source files paths inside the batch list.

        Returns:
            list: selected source file paths
        """
        batch_source_paths = []
        for i in range(self._batch_anim_list.count()):
            if self._batch_anim_list.item(i).checkState() == ui_qt.QtCore.Qt.Checked:
                batch_source_paths.append(self._batch_anim_list.item(i).data(self._user_role))
        return batch_source_paths

    @staticmethod
    def get_retargeter_addons_names():
        """
        Retrieve the list of addon names from the retargeter addons dictionary.

        Returns:
            list[str]: List of addon names, or empty list if no addons found.
        """
        import gt.tools.retargeter.retargeter_addons as tools_retargeter_addons

        addons_dict = tools_retargeter_addons.Addons.get_addons_dict()
        if not addons_dict:
            return []
        return [addon_class().name for addon_ame, addon_class in addons_dict.items()]

    def save_preferences(self):
        """Delegates preference persistence to the model-owned store."""
        if self.model:
            self.model.save_preferences()
        else:
            self._preferences.save()


if __name__ == "__main__":
    with ui_qt_utils.QtApplicationContext():
        window = RetargeterView()
        window.show()
