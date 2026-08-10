"""
Auto Rigger Controller
"""

import gt.tools.auto_rigger.attr_widgets.attr_widgets as tools_rig_attr_widget
import gt.tools.auto_rigger.rigger_log_view as tools_rig_log_view
import gt.tools.auto_rigger.rig_templates as tools_rig_templates
import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.rig_modules as tools_rig_modules
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.ui.tree_widget_enhanced as ui_tree_enhanced
import gt.ui.resource_library as ui_res_lib
import gt.ui.file_dialog as ui_file_dialog
import gt.utils.system as utils_system
import gt.ui.qt_utils as ui_qt_utils
import gt.core.prefs as core_prefs
import gt.core.logger as core_log
import gt.ui.qt_import as ui_qt
import gt.core.str as core_str
import gt.core.io as core_io
from functools import partial
import logging
import json
import os
import sys

# Logging Setup
logger_name = core_log.get_logger_name(__name__)
logger = core_log.setup_common_logger(name=logger_name, propagate=False)
logger.setLevel(logging.INFO)
core_log.add_custom_log_levels()


def get_module_attr_widgets(module):
    """
    Gets the associated attribute widget used to populate the attribute editor in the main UI.
    Args:
        module (ModuleGeneric): The module instance for which to get the attribute widget.
    Returns:
        ModuleAttrWidget: Widget used to populate the attribute editor of the rigger window.
    """
    if type(module) is tools_rig_modules.RigModules.General.ModuleGeneric:
        return tools_rig_attr_widget.AttrWidgetModuleGeneric
    if type(module) is tools_rig_modules.RigModules.General.ModuleGenericFK:
        return tools_rig_attr_widget.AttrWidgetModuleGenericFK
    if type(module) is tools_rig_modules.RigModules.General.ModuleRoot:
        return tools_rig_attr_widget.AttrWidgetModuleRoot
    if isinstance(module, tools_rig_modules.RigModules.General.ModuleGenericIK):
        return tools_rig_attr_widget.AttrWidgetModuleGenericIK
    if isinstance(module, tools_rig_modules.RigModules.General.ModuleSpine):
        return tools_rig_attr_widget.AttrWidgetModuleSpine
    if isinstance(module, tools_rig_modules.RigModules.General.ModuleHead):
        return tools_rig_attr_widget.AttrWidgetModuleHead
    if isinstance(module, tools_rig_modules.RigModules.General.ModuleAttributeHub):
        return tools_rig_attr_widget.AttrWidgetModuleAttributeHub
    if isinstance(module, tools_rig_modules.RigModules.General.ModuleSocket):
        return tools_rig_attr_widget.AttrWidgetModuleSocket
    if isinstance(module, tools_rig_modules.RigModules.Biped.ModuleBipedArm):
        return tools_rig_attr_widget.AttrWidgetModuleBipedArm
    if isinstance(module, tools_rig_modules.RigModules.General.ModuleArm):
        return tools_rig_attr_widget.AttrWidgetModuleArm
    if isinstance(module, tools_rig_modules.RigModules.Biped.ModuleBipedLeg):
        return tools_rig_attr_widget.AttrWidgetModuleBipedLeg
    if isinstance(module, tools_rig_modules.RigModules.Biped.ModuleBipedFingers):
        return tools_rig_attr_widget.AttrWidgetModuleBipedFinger
    if isinstance(module, tools_rig_modules.RigModules.Biped.ModuleMetaHumanFace):
        return tools_rig_attr_widget.AttrWidgetModuleMetaHumanFace
    if isinstance(module, tools_rig_modules.RigModules.Biped.ModuleAnimMassReferences):
        return tools_rig_attr_widget.AttrWidgetModuleAnimMassReferences
    if isinstance(module, tools_rig_modules.RigModules.General.ModuleChain):
        return tools_rig_attr_widget.AttrWidgetModuleChain
    if isinstance(module, tools_rig_modules.RigModules.General.ModuleRibbon):
        return tools_rig_attr_widget.AttrWidgetModuleRibbonGeneric
    if type(module) is tools_rig_modules.RigModules.General.ModulePivot:
        return tools_rig_attr_widget.AttrWidgetModuleGenericFK
    if isinstance(module, tools_rig_modules.RigModules.Quadruped.ModuleQuadFrontLeg):
        return tools_rig_attr_widget.AttrWidgetModuleQuadFrontLeg
    if isinstance(module, tools_rig_modules.RigModules.Quadruped.ModuleQuadRearLeg):
        return tools_rig_attr_widget.AttrWidgetModuleQuadRearLeg
    if isinstance(module, tools_rig_modules.RigModules.Quadruped.ModuleQuadSpine):
        return tools_rig_attr_widget.AttrWidgetModuleRibbonQuadSpine
    if isinstance(module, tools_rig_modules.RigModules.General.ModulePiston):
        return tools_rig_attr_widget.AttrWidgetModulePiston
    # Correctives --------------------------------------------------------------
    if isinstance(module, tools_rig_modules.RigModules.Correctives.ModuleCorrectiveFK):
        return tools_rig_attr_widget.AttrWidgetModuleCorrectiveFK  # Needs to happen first due to inheritance
    if isinstance(module, tools_rig_modules.RigModules.Correctives.ModuleCorrectiveGeneric):
        return tools_rig_attr_widget.AttrWidgetModuleCorrectiveGeneric
    if isinstance(module, tools_rig_modules.RigModules.Correctives.ModuleRBFPoseLoader):
        return tools_rig_attr_widget.AttrWidgetModuleRBFLoad
    # Probes --------------------------------------------------------------
    if isinstance(module, tools_rig_modules.RigModules.Probes.ModuleProbeDistance):
        return tools_rig_attr_widget.AttrWidgetModuleProbeDistance
    if isinstance(module, tools_rig_modules.RigModules.Probes.ModuleProbeRotation):
        return tools_rig_attr_widget.AttrWidgetModuleProbeRotation
    # Utils ---------------------------------------------------------------
    if isinstance(module, tools_rig_modules.RigModules.Utils.ModuleGroup):
        return tools_rig_attr_widget.AttrWidgetModuleGroup
    if isinstance(module, tools_rig_modules.RigModules.Utils.ModuleNewScene):
        return tools_rig_attr_widget.AttrWidgetModuleNewScene
    if isinstance(module, tools_rig_modules.RigModules.Utils.ModuleImportFile):
        return tools_rig_attr_widget.AttrWidgetModuleImportFile
    if isinstance(module, tools_rig_modules.RigModules.Utils.ModuleSkinWeights):
        return tools_rig_attr_widget.AttrWidgetModuleSkinWeights
    if isinstance(module, tools_rig_modules.RigModules.Utils.ModuleNGSkinWeights):
        return tools_rig_attr_widget.AttrWidgetModuleNGSkinWeights
    if isinstance(module, tools_rig_modules.RigModules.Utils.ModuleExportSkeletalMesh):
        return tools_rig_attr_widget.AttrWidgetModuleExportSkeletalMesh
    if isinstance(module, tools_rig_modules.RigModules.Utils.ModuleSaveScene):
        return tools_rig_attr_widget.AttrWidgetModuleSaveScene
    if isinstance(module, tools_rig_modules.RigModules.Utils.ModuleLoadScene):
        return tools_rig_attr_widget.AttrWidgetModuleLoadScene
    if isinstance(module, tools_rig_modules.RigModules.Utils.ModulePython):
        return tools_rig_attr_widget.AttrWidgetModulePython
    if isinstance(module, tools_rig_modules.RigModules.Utils.ModuleShapesSnapshot):
        return tools_rig_attr_widget.AttrWidgetModuleShapesSnapshot
    if isinstance(module, tools_rig_modules.RigModules.Utils.ModuleNotes):
        return tools_rig_attr_widget.AttrWidgetModuleNotes
    if isinstance(module, tools_rig_modules.RigModules.Utils.ModuleCameraSetup):
        return tools_rig_attr_widget.AttrWidgetModuleCameraSetup
    if isinstance(module, tools_rig_modules.RigModules.Utils.ModuleThumbnailCapture):
        return tools_rig_attr_widget.AttrWidgetModuleThumbnailCapture
    if isinstance(module, tools_rig_modules.RigModules.Utils.ModulePlayblastCapture):
        return tools_rig_attr_widget.AttrWidgetModulePlayblastCapture
    if isinstance(module, tools_rig_modules.RigModules.Utils.ModuleROMLoader):
        return tools_rig_attr_widget.AttrWidgetModuleROMLoader
    if isinstance(module, tools_rig_modules.RigModules.Utils.ModuleEnumVariants):
        return tools_rig_attr_widget.AttrWidgetModuleEnumVariants
    if isinstance(module, tools_rig_modules.RigModules.Utils.ModulePickerData):
        return tools_rig_attr_widget.AttrWidgetModulePickerData
    if isinstance(module, tools_rig_modules.RigModules.Utils.ModuleCollections):
        return tools_rig_attr_widget.AttrWidgetModuleCollections
    if isinstance(module, tools_rig_modules.RigModules.Utils.ModuleValidation):
        return tools_rig_attr_widget.AttrWidgetModuleValidation
    else:
        return tools_rig_attr_widget.AttrWidgetCommon


class RiggerController:
    def __init__(self, model, view):
        """
        Initialize the RiggerController object.

        Args:
            model (RiggerModel): The RiggerModel object used for data manipulation.
            view (RiggerView): The view object to interact with the user interface.
        """
        self.model = model
        self.view = view
        self.view.controller = self
        self.log_view = tools_rig_log_view.RiggerLoggingView()


        self.populate_module_tree()

        # Connections
        self.view.module_tree.itemClicked.connect(self.on_tree_item_clicked)
        self.view.build_proxy_btn.clicked.connect(self.build_proxy)
        self.view.build_rig_btn.clicked.connect(self.build_rig)
        self.view.module_tree.setContextMenuPolicy(ui_qt.QtCore.Qt.CustomContextMenu)  # Allows context menu
        self.view.module_tree.customContextMenuRequested.connect(self.show_module_tree_context_menu)

        # State Variables
        self._opened_project = ""
        self._opened_project_initial_state = {}  # Used for comparison to find changes
        self._has_high_level_changes = False

        # Preferences
        self._prefs = core_prefs.Prefs(tools_rig_const.RiggerConstants.PREFS_FILENAME)
        self._recent_projects = core_prefs.RecentProjects(
            prefs=self._prefs,
            key=tools_rig_const.RiggerConstants.PREFS_KEY_RECENT_PROJECTS,
            max_count=tools_rig_const.RiggerConstants.MAX_RECENT_PROJECTS,
        )
        self._on_build_clear_log_window = self._prefs.get_bool(
            key=tools_rig_const.RiggerConstants.PREFS_KEY_ON_BUILD_CLEAR_LOG, default=True
        )
        self._on_build_show_log_view = self._prefs.get_bool(
            key=tools_rig_const.RiggerConstants.PREFS_KEY_ON_BUILD_SHOW_LOG, default=True
        )
        self._on_set_path_abs_to_relative = self._prefs.get_bool(
            key=tools_rig_const.RiggerConstants.PREFS_KEY_ON_SET_PATH_ABS_TO_RELATIVE, default=True
        )

        # Add Menubar
        self.add_menu_file()
        self.add_menu_modules()
        self.add_menu_utils()
        self.add_menu_log()
        self.add_menu_help()

        # Set Close Window Dialog
        self.view.set_close_event_function(func=self.show_unsaved_changes_warning_dialog)

        # Show
        self.view.show()

    # ------------------------------------------- Top Menu -------------------------------------------
    def add_menu_file(self):
        """
        Adds a file menu bar to the view
        """
        menu_file = self.view.add_menu_parent("File")
        action_new = ui_qt.QtLib.QtGui.QAction("New Project", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_new))
        action_new.triggered.connect(self.initialize_new_project)

        action_open = ui_qt.QtLib.QtGui.QAction("Open Project", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        action_open.triggered.connect(self.load_project_from_file)

        action_save = ui_qt.QtLib.QtGui.QAction("Save", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_save))
        action_save.triggered.connect(self.save_project_to_file)

        action_save_as = ui_qt.QtLib.QtGui.QAction("Save As", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_save))
        _save_as_func = partial(self.save_project_to_file, True)  # Save as keyword is True
        action_save_as.triggered.connect(_save_as_func)

        # Menu Assembly -------------------------------------------------------------------------------------
        self.view.add_menu_action(parent_menu=menu_file, action=action_new)
        self.view.add_menu_action(parent_menu=menu_file, action=action_open)

        self._recent_projects_menu = self.view.add_menu_submenu(
            parent_menu=menu_file,
            submenu_name="Recent Projects",
            icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open),
        )
        self._recent_projects_menu.aboutToShow.connect(self.refresh_recent_projects_menu)
        self.refresh_recent_projects_menu()

        self.view.add_menu_action(parent_menu=menu_file, action=action_save)
        self.view.add_menu_action(parent_menu=menu_file, action=action_save_as)

        # Templates
        self._templates_menu = self.view.add_menu_submenu(
            parent_menu=menu_file, submenu_name="Templates", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_templates)
        )
        self._template_menu_actions = []
        self._templates_menu.aboutToShow.connect(self.refresh_templates_menu)
        self.refresh_templates_menu()

    def refresh_templates_menu(self):
        """Rebuilds the template submenu from the current template directory."""
        if not ui_qt_utils.is_qt_object_valid(getattr(self, "_templates_menu", None)):
            return

        menu_templates = self._templates_menu
        self._template_menu_actions = []
        menu_templates.clear()
        rig_templates = tools_rig_templates.RigTemplates()  # Initializing populates it with file templates

        # Python Templates ---
        offer_python_templates = False  # To make it toggleable in the future.
        if offer_python_templates:
            ui_qt_utils.add_labeled_separator(menu=menu_templates, text="Python Templates")
            for name, template_func in rig_templates.get_dict_templates(include_file_templates=False).items():
                formatted_name = " ".join(core_str.camel_case_split(name))
                action_template = ui_qt.QtLib.QtGui.QAction(
                    formatted_name, icon=ui_qt.QtGui.QIcon(tools_rig_templates.RigTemplates.icon_python)
                )
                item_func = partial(self.replace_project, project=template_func)
                action_template.triggered.connect(item_func)
                self._template_menu_actions.append(action_template)
                menu_templates.addAction(action_template)

        # File Templates ---
        ui_qt_utils.add_labeled_separator(menu=menu_templates, text="File Templates")
        for name, template_func in rig_templates.get_dict_templates(include_py_templates=False).items():
            formatted_name = " ".join(core_str.camel_case_split(name))
            action_template = ui_qt.QtLib.QtGui.QAction(
                formatted_name, icon=ui_qt.QtGui.QIcon(rig_templates.icon_files)
            )
            item_func = partial(self.replace_project, project=template_func)
            action_template.triggered.connect(item_func)
            self._template_menu_actions.append(action_template)
            menu_templates.addAction(action_template)
        # Open Template Directories ---
        ui_qt_utils.add_labeled_separator(menu=menu_templates, text="Template Resources")
        action_open_templates = ui_qt.QtLib.QtGui.QAction(
            "Open Templates Folder", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir)
        )
        _open_templates_func = lambda *args: self.open_or_create_directory(
            tools_rig_templates.get_template_source_dir()
        )
        action_open_templates.triggered.connect(_open_templates_func)
        self._template_menu_actions.append(action_open_templates)
        menu_templates.addAction(action_open_templates)

        action_open_resources = ui_qt.QtLib.QtGui.QAction(
            "Open Resources Folder", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir)
        )
        _open_resources_func = lambda *args: self.open_or_create_directory(
            tools_rig_templates.get_template_resources_dir()
        )
        action_open_resources.triggered.connect(_open_resources_func)
        self._template_menu_actions.append(action_open_resources)
        menu_templates.addAction(action_open_resources)

        action_convert_template = ui_qt.QtLib.QtGui.QAction(
            "Save Current as Template", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_templates)
        )
        action_convert_template.triggered.connect(self.convert_current_project_to_template)
        self._template_menu_actions.append(action_convert_template)
        menu_templates.addAction(action_convert_template)

    def refresh_recent_projects_menu(self):
        """Rebuilds the recent-project submenu from stored preferences."""
        self._recent_projects_menu.clear()
        recent_paths = self._recent_projects.get_paths()
        if not recent_paths:
            empty_action = ui_qt.QtLib.QtGui.QAction("No Recent Projects", self.view)
            empty_action.setEnabled(False)
            self._recent_projects_menu.addAction(empty_action)
            return
        for index, file_path in enumerate(recent_paths, start=1):
            action_recent = ui_qt.QtLib.QtGui.QAction(
                ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open),
                f"{index}. {file_path}",
                self._recent_projects_menu,
            )
            action_recent.setToolTip(file_path)
            action_recent.triggered.connect(partial(self.load_project_from_path, file_path))
            self._recent_projects_menu.addAction(action_recent)
        self._recent_projects_menu.addSeparator()
        action_clear = ui_qt.QtLib.QtGui.QAction(
            ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete),
            "Clear Recent Projects",
            self._recent_projects_menu,
        )
        action_clear.triggered.connect(self.clear_recent_projects)
        self._recent_projects_menu.addAction(action_clear)

    def clear_recent_projects(self):
        """Clears the stored recent-project list and refreshes its menu."""
        self._recent_projects.clear()
        self.refresh_recent_projects_menu()
        logger.info("Cleared recent projects.")

    def open_project_folder(self, *args):
        """Opens the current project folder in the system file browser.

        Args:
            *args: Optional Qt signal arguments.
        """
        project_path = ""
        if self._opened_project:
            project_path = os.path.normpath(os.path.dirname(self._opened_project))
        if project_path and os.path.isdir(project_path):
            utils_system.open_file_dir(project_path)
            return
        ui_qt.QtWidgets.QMessageBox.warning(
            self.view,
            "Project Folder Unavailable",
            f"The project folder could not found:\n{project_path or 'No project folder configured.'}",
        )

    @staticmethod
    def open_or_create_directory(directory_path, *args):
        """Creates a directory when missing, then opens it in the system file browser.

        Args:
            directory_path (str): Directory path to open.
            *args: Optional Qt signal arguments.
        """
        if not directory_path:
            sys.stdout.write("Unable to open directory. Path was empty.\n")
            return
        directory_path = os.path.abspath(os.path.expanduser(str(directory_path)))
        if not os.path.isdir(directory_path):
            try:
                os.makedirs(directory_path, exist_ok=True)
                sys.stdout.write('Created directory: "{0}"\n'.format(directory_path))
            except OSError as exception:
                sys.stdout.write('Unable to create directory "{0}". Issue: {1}\n'.format(directory_path, exception))
                return
        if not os.path.isdir(directory_path):
            sys.stdout.write('Unable to open directory. Path does not exist: "{0}"\n'.format(directory_path))
            return
        utils_system.open_file_dir(directory_path)

    def add_menu_modules(self):
        """
        Adds a modules menu bar to the view
        """
        from gt.tools.auto_rigger.rig_modules import RigModules

        menu_modules = self.view.add_menu_parent("Modules")
        known_categories = RigModules.get_known_categories_dict()

        for name, module_name in RigModules.get_categorized_modules_dict().items():
            _icon_path = None
            _category_class = known_categories.get(name, None)
            if _category_class:
                _icon_path = _category_class.icon

            menu_templates = self.view.add_menu_submenu(
                parent_menu=menu_modules, submenu_name=name, icon=ui_qt.QtGui.QIcon(_icon_path)
            )
            if isinstance(module_name, list):
                for unique_mod in module_name:
                    module_list = RigModules.get_unique_modules_dict().get(unique_mod)
                    formatted_name = " ".join(core_str.camel_case_split(unique_mod))
                    action_mod = ui_qt.QtLib.QtGui.QAction(formatted_name, icon=ui_qt.QtGui.QIcon(module_list[0].icon))
                    item_func = partial(
                        self.add_module_to_project_from_list, module_name=formatted_name, module_list=module_list
                    )
                    action_mod.triggered.connect(item_func)
                    self.view.add_menu_action(parent_menu=menu_templates, action=action_mod)

    def add_menu_utils(self):
        """
        Adds utils menu bar to the view
        """
        menu_utils = self.view.add_menu_parent("Utilities")

        # Open Project Folder ------------------------------------------------------------------
        action_open_project_folder = ui_qt.QtLib.QtGui.QAction(
            "Open Project Folder", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open_external)
        )
        action_open_project_folder.triggered.connect(self.open_project_folder)
        self.view.add_menu_action(parent_menu=menu_utils, action=action_open_project_folder)

        # Get Env Vars -------------------------------------------------------------------------------
        action_get_environment_vars = ui_qt.QtLib.QtGui.QAction(
            "Get Environment Variables", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.root_dev)
        )
        action_get_environment_vars.triggered.connect(self.get_environment_variables)
        self.view.add_menu_action(parent_menu=menu_utils, action=action_get_environment_vars)

        # Extract Project ----------------------------------------------------------------------------
        action_extract_project_from_rig = ui_qt.QtLib.QtGui.QAction(
            "Get Project from Built Rig", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_extract_project)
        )
        action_extract_project_from_rig.triggered.connect(self.get_project_from_built_rig)
        self.view.add_menu_action(parent_menu=menu_utils, action=action_extract_project_from_rig)

        # Convert Jnt --------------------------------------------------------------------------------
        action_convert_joints_to_module = ui_qt.QtLib.QtGui.QAction(
            "Convert Joints to Module", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_module_generic_bw)
        )
        action_convert_joints_to_module.triggered.connect(self.add_selected_joints_module_generic)
        self.view.add_menu_action(parent_menu=menu_utils, action=action_convert_joints_to_module)

        # Geo Migration -------------------------------------------------------------------------------
        action_open_geo_preprocessor = ui_qt.QtLib.QtGui.QAction(
            "Geometry Preprocessor", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_geo_preprocessor)
        )
        action_open_geo_preprocessor.triggered.connect(self.open_geometry_preprocessor)
        self.view.add_menu_action(parent_menu=menu_utils, action=action_open_geo_preprocessor)

        # Poses -------------------------------------------------------------------------------------
        menu_templates = self.view.add_menu_submenu(
            parent_menu=menu_utils, submenu_name="Poses", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_templates)
        )

        import gt.core.pose as core_pose

        # A-Pose Skeleton ---
        action_sk_a_pose = ui_qt.QtLib.QtGui.QAction(
            "A-Pose (Skeleton)", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.root_animation)
        )
        action_sk_a_pose.triggered.connect(core_pose.set_apose)
        self.view.add_menu_action(parent_menu=menu_templates, action=action_sk_a_pose)

        # T-Pose Skeleton ---
        action_sk_t_pose = ui_qt.QtLib.QtGui.QAction(
            "T-Pose (Skeleton)", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.root_rigging)
        )
        action_sk_t_pose.triggered.connect(core_pose.set_tpose)
        self.view.add_menu_action(parent_menu=menu_templates, action=action_sk_t_pose)

        # A-Pose Control Rig ---
        action_ctrl_a_pose = ui_qt.QtLib.QtGui.QAction(
            "A-Pose (Control Rig)", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.root_animation)
        )
        action_ctrl_a_pose.triggered.connect(tools_rig_utils.set_rig_apose)
        self.view.add_menu_action(parent_menu=menu_templates, action=action_ctrl_a_pose)

        # T-Pose Control Rig ---
        action_ctrl_t_pose = ui_qt.QtLib.QtGui.QAction(
            "T-Pose (Control Rig)", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.root_rigging)
        )
        action_ctrl_t_pose.triggered.connect(tools_rig_utils.set_rig_tpose)
        self.view.add_menu_action(parent_menu=menu_templates, action=action_ctrl_t_pose)

        # Range of Motion ---------------------------------------------------------------------------
        menu_rom = self.view.add_menu_submenu(
            parent_menu=menu_utils,
            submenu_name="Range of Motion",
            icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.root_animation),
        )

        try:
            import gt.tools.retargeter.retargeter_constants as tools_rt_const
            import gt.tools.retargeter.retargeter_utils as tools_rt_utils

            rom_folder = tools_rt_const.RetargeterConstants.DEFAULT_ROM_DATA_FOLDER
            definitions = set()
            for file in os.listdir(rom_folder):
                if os.path.isfile(os.path.join(rom_folder, file)):
                    name_without_ext, _ = os.path.splitext(file)
                    definitions.add(name_without_ext)

            # Populate Sub-menu
            for definition in list(definitions):
                definition_nice_name = core_str.snake_to_title(definition)

                # Long Skin Tester Control Rig ---
                action_rom_item = ui_qt.QtLib.QtGui.QAction(
                    definition_nice_name, icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.root_rigging)
                )
                self.view.add_menu_action(parent_menu=menu_rom, action=action_rom_item)

                _func = partial(
                    tools_rt_utils.show_dialog_retarget_using_definition_from_directory,
                    directory_path=rom_folder,
                    target_definition=definition,
                )
                action_rom_item.triggered.connect(_func)

        except Exception as e:
            logger.debug(f"Unable to load ROM definitions as menu items. Issue: {e}")

        # Reference & Attach ------------------------------------------------------------------------
        menu_attachment = self.view.add_menu_submenu(
            parent_menu=menu_utils,
            submenu_name="Attachment",
            icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.misc_pin),
        )

        # Reference and Attach to Selection
        action_attach_selection = ui_qt.QtLib.QtGui.QAction(
            "Reference to Selection", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.misc_plug)
        )
        self.view.add_menu_action(parent_menu=menu_attachment, action=action_attach_selection)

        _func = partial(
            tools_rig_utils.show_dialog_reference_and_attach,
            ref_function=tools_rig_utils.reference_and_attach_rig_to_selection,
        )
        action_attach_selection.triggered.connect(_func)

        # Reference and Attach to Left Hand
        action_attach_left_socket = ui_qt.QtLib.QtGui.QAction(
            "Reference to Left Socket", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.misc_plug)
        )
        self.view.add_menu_action(parent_menu=menu_attachment, action=action_attach_left_socket)

        _func = partial(
            tools_rig_utils.show_dialog_reference_and_attach,
            ref_function=tools_rig_utils.reference_and_attach_rig_to_socket,
            kwargs={"side_prefix": "L"},
        )
        action_attach_left_socket.triggered.connect(_func)

        # Reference and Attach to Right Hand
        action_attach_right_socket = ui_qt.QtLib.QtGui.QAction(
            "Reference to Right Socket", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.misc_plug)
        )
        self.view.add_menu_action(parent_menu=menu_attachment, action=action_attach_right_socket)

        _func = partial(
            tools_rig_utils.show_dialog_reference_and_attach,
            ref_function=tools_rig_utils.reference_and_attach_rig_to_socket,
            kwargs={"side_prefix": "R"},
        )
        action_attach_right_socket.triggered.connect(_func)

        # Automations -------------------------------------------------------------------------------
        menu_prefs = self.view.add_menu_submenu(
            parent_menu=menu_utils,
            submenu_name="Automations",
            icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.root_general),
        )

        # On Set Path (From Path Text-field) Convert Absolute Paths to Relative Paths
        abs_path_to_relative_name = "Convert Absolute Paths to Relative"
        on_abs_paths_to_relative_action = ui_qt.QtLib.QtGui.QAction(abs_path_to_relative_name, checkable=True)
        on_abs_paths_to_relative_action.triggered.connect(self.toggle_on_set_path_abs_to_relative)
        tooltip = (
            "If enabled, paths that begin with the project directory will automatically have that portion "
            "replaced with the {project-dir} environment variable."
            "\nFor example, C:/a_project/geo will become {project-dir}/geo."
        )
        on_abs_paths_to_relative_action.setToolTip(tooltip)
        self.view.add_menu_action(parent_menu=menu_prefs, action=on_abs_paths_to_relative_action)
        on_abs_paths_to_relative_action.setChecked(self._on_set_path_abs_to_relative)

    def add_menu_log(self):
        """
        Adds log menu bar to the view
        """
        import gt.utils.system as utils_sys

        menu_log = self.view.add_menu_parent("Logging")

        # Open Logs Window
        action_open_logs_win = ui_qt.QtLib.QtGui.QAction(
            "Open Logs Window", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_templates)
        )
        open_logs_win_func = partial(self.log_view.show_if_not_visible)
        action_open_logs_win.triggered.connect(open_logs_win_func)
        self.view.add_menu_action(parent_menu=menu_log, action=action_open_logs_win)

        # Open Logs Dir
        action_open_logs_dir = ui_qt.QtLib.QtGui.QAction(
            "Open Logs Directory", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir)
        )
        _logs_dir = core_log.get_logs_dir()
        open_logs_dir_func = partial(utils_sys.open_file_dir, _logs_dir)
        action_open_logs_dir.triggered.connect(open_logs_dir_func)
        self.view.add_menu_action(parent_menu=menu_log, action=action_open_logs_dir)

        # On Build Show Log Window
        on_build_show_log_view_action = ui_qt.QtLib.QtGui.QAction("Build Shows Log Window", checkable=True)
        on_build_show_log_view_action.triggered.connect(self.toggle_on_build_show_log_view)
        self.view.add_menu_action(parent_menu=menu_log, action=on_build_show_log_view_action)
        on_build_show_log_view_action.setChecked(self._on_build_show_log_view)

        # On Build Clear Log Window
        on_build_clear_log_window_action = ui_qt.QtLib.QtGui.QAction("Build Clears Log Window", checkable=True)
        on_build_clear_log_window_action.triggered.connect(self.toggle_on_build_clear_log_window)
        self.view.add_menu_action(parent_menu=menu_log, action=on_build_clear_log_window_action)
        on_build_clear_log_window_action.setChecked(self._on_build_clear_log_window)

    def add_menu_help(self):
        """
        Adds help menu bar to the view
        """
        import gt.utils.request as utils_request

        menu_file = self.view.add_menu_parent("Help")

        # Open Docs
        package_docs_url = "https://github.com/TrevisanGMW/gt-tools/tree/release/docs"
        action_open_package_docs = ui_qt.QtLib.QtGui.QAction(
            "Open GT-Tools Documentation", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.root_help)
        )

        open_package_docs = partial(utils_request.open_url_in_browser, package_docs_url)
        action_open_package_docs.triggered.connect(open_package_docs)
        self.view.add_menu_action(parent_menu=menu_file, action=action_open_package_docs)


    def add_module_to_project(self, module):
        """
        Adds a module to the currently loaded module, then refresh the view.
        Args:
            module (ModuleGeneric): A module using ModuleGeneric as base to be added to the project.
        """
        initialized_module = module()
        self.model.add_to_modules(module=initialized_module)
        self.refresh_widgets()

    def add_module_to_project_from_list(self, module_name, module_list):
        """
        Adds a module to the currently loaded module, then refresh the view.
        Args:
            module_name (str): Name of the module
            module_list (list): A list of modules sharing the same base. e.g. [BipedLeg, BipedLegRight, BipedLegLeft]
        """
        # Not a list or missing module
        if not module_list or not isinstance(module_list, list):
            logger.debug(f"Unable to create module choice dialog")
            return
        # One Module
        if len(module_list) == 1:
            self.add_module_to_project(module=module_list[0])
            return
        # Multiple Options
        message_box = ui_qt.QtWidgets.QMessageBox(self.view)
        message_box.setWindowTitle(f'Which "{str(module_name)}" Module?')
        message_box.setText(f'Which variation of "{str(module_name)}"\nwould like to add?')

        question_icon = ui_qt.QtGui.QIcon(module_list[0].icon)
        message_box.setIconPixmap(question_icon.pixmap(64, 64))
        for mod in module_list:
            formatted_name = core_str.remove_prefix(input_string=str(mod.__name__), prefix="Module")
            formatted_name = " ".join(core_str.camel_case_split(formatted_name))
            message_box.addButton(formatted_name, ui_qt.QtLib.ButtonRoles.ActionRole)
        result = message_box.exec_()
        self.add_module_to_project(module=module_list[result])

    def initialize_new_project(self):
        """
        Re-initializes the project to an empty one and refreshes the view.
        """
        if self.show_unsaved_changes_warning_dialog(window=None, is_close_event=False):  # True when cancelled
            return
        self.model.clear_project()
        self.refresh_widgets()
        self.clear_opened_project()
        self._has_high_level_changes = False

    def save_project_to_file(self, save_as=False):
        """
        Shows a save file dialog offering to save the current project to a file. (JSON formatted)
        Args:
            save_as (bool, optional): If True, the file save dialog will appear even if the project already exists.

        Returns:
            bool: True when the project was saved.
        """
        _save_path = None
        _starting_directory = None
        # Check for known path
        if self._opened_project and os.path.exists(self._opened_project):
            _save_path = self._opened_project
            _starting_directory = os.path.dirname(self._opened_project)
        # Is Forcing Dialog?
        if save_as:
            _save_path = None
        # File Dialog
        if not _save_path:
            _save_path = ui_file_dialog.file_dialog(
                caption="Save Rig Project",
                write_mode=True,
                starting_directory=_starting_directory,
                file_filter=tools_rig_const.RiggerConstants.PROJECT_FILE_FILTER,
                ok_caption="Save Project",
                cancel_caption="Cancel",
            )
        # Save Project
        if _save_path:
            # If already present, make it modifiable
            if _save_path and os.path.exists(_save_path):
                core_io.set_file_permission_modifiable(_save_path)
            self.refresh_tree_expansion_state_variables()  # Get Qtree item expanded state
            self.model.save_project_to_file(path=_save_path)
            logger.info(f'Project saved to "{_save_path}".')
            self.set_opened_project(_save_path)
            self._has_high_level_changes = False
            return True
        return False

    def load_project_from_file(self, file_path=None):
        """
        Shows an open file dialog offering to load a new project from a file. (JSON formatted)
        Args:
            file_path (str, optional): If provided, it will try to load the project path using the provided path
                                       instead of opening a dialog.
        """
        if not file_path:
            file_path = ui_file_dialog.file_dialog(
                caption="Open Rig Project",
                write_mode=False,
                starting_directory=None,
                file_filter=tools_rig_const.RiggerConstants.PROJECT_FILE_FILTER,
                ok_caption="Open Project",
                cancel_caption="Cancel",
            )
        if file_path:
            return self.load_project_from_path(file_path)
        return False

    def load_project_from_path(self, file_path, *args):
        """Safely loads a project path after validating it and protecting changes.

        Args:
            file_path (str): Rig project file path to load.
            *args: Optional Qt signal arguments.

        Returns:
            bool: True when the project was loaded.
        """
        file_path = self._recent_projects.normalize_path(file_path)
        if not os.path.isfile(file_path):
            self._recent_projects.remove_path(file_path)
            self.refresh_recent_projects_menu()
            self.show_project_load_warning(
                title="Project Not Found",
                message=f'The project no longer exists:\n\n{file_path}',
            )
            return False
        if self.show_unsaved_changes_warning_dialog(window=self.view, is_close_event=False):
            return False
        try:
            self.model.load_project_from_file(path=file_path)
        except Exception as exception:
            logger.exception(f'Unable to load rig project: "{file_path}"')
            self.show_project_load_warning(
                title="Unable to Open Project",
                message=f'The project could not be opened and the current project was preserved.\n\n{exception}',
            )
            return False
        self.refresh_widgets()
        self.set_opened_project(path=file_path)
        self._has_high_level_changes = False
        return True

    def show_project_load_warning(self, title, message):
        """Shows a blocking warning for an invalid recent project.

        Args:
            title (str): Warning dialog title.
            message (str): Warning dialog message.
        """
        message_box = ui_qt.QtWidgets.QMessageBox(self.view)
        message_box.setWindowTitle(title)
        message_box.setText(message)
        try:
            message_box.setIcon(ui_qt.QtWidgets.QMessageBox.Warning)
        except AttributeError:
            message_box.setIcon(ui_qt.QtWidgets.QMessageBox.Icon.Warning)
        message_box.exec_()
        logger.warning(message.replace("\n", " "))

    def replace_project(self, project):
        """
        Replaces the current loaded project.
        Args:
            project (RigProject, callable): A RigProject objects to replace the current project.
                                            If a callable object is provided, it calls the function
                                            expecting a RigProject as the output.
        """
        if callable(project):
            project = project()
        if project:
            self.model.set_project(project=project)
            self.refresh_widgets()

    def convert_current_project_to_template(self, *args):
        """Saves the current project as a reusable file template.

        When the saved project directory contains additional files or folders,
        the user can also copy them into the matching template resources
        directory. The active project and its working directory are unchanged.

        Args:
            *args: Optional Qt signal arguments.

        Returns:
            bool: True when the template project file was created.
        """
        project = self.model.get_project()
        template_name = self.get_template_name_from_dialog(default_name=project.get_name())
        if not template_name:
            return False

        template_source_dir = tools_rig_templates.get_template_source_dir()
        try:
            os.makedirs(template_source_dir, exist_ok=True)
        except OSError as exception:
            self.show_project_load_warning(
                title="Unable to Create Template",
                message=f"The templates directory could not be created:\n\n{exception}",
            )
            return False

        template_extension = f".{tools_rig_const.RiggerConstants.PROJECT_EXTENSION}"
        template_path = os.path.join(template_source_dir, f"{template_name}{template_extension}")
        if os.path.isfile(template_path) and not self.show_template_overwrite_warning(template_path):
            return False

        template_data = tools_rig_templates.get_project_template_data(project)
        if not template_data:
            return False

        if os.path.isfile(template_path):
            core_io.set_file_permission_modifiable(template_path)
        saved_template_path = core_io.write_json(path=template_path, data=template_data)
        if not saved_template_path:
            self.show_project_load_warning(
                title="Unable to Create Template",
                message=f"The template could not be saved:\n\n{template_path}",
            )
            return False

        logger.info(f'Created template "{saved_template_path}".')
        ui_qt.QtCore.QTimer.singleShot(0, self.refresh_templates_menu)
        if not tools_rig_templates.project_directory_has_resources(project):
            return True

        resource_target_dir = os.path.join(tools_rig_templates.get_template_resources_dir(), template_name)
        if not self.show_template_resource_copy_dialog(resource_target_dir):
            return True

        copy_results = tools_rig_templates.copy_project_resources(project, resource_target_dir)
        if copy_results is None:
            self.show_project_load_warning(
                title="Unable to Copy Template Resources",
                message="The project resources could not be copied into the template resources directory.",
            )
            return True

        logger.info(
            f'Copied {copy_results["copied"]} template resource(s) to "{resource_target_dir}". '
            f'Skipped {copy_results["skipped"]} existing resource(s).'
        )
        return True

    def get_template_name_from_dialog(self, default_name):
        """Prompts the user for a safe file name for a new template.

        Args:
            default_name (str): Initial template name shown to the user.

        Returns:
            str: Sanitized template name without the project extension, or an
            empty string when cancelled or invalid.
        """
        template_name, accepted = ui_qt.QtWidgets.QInputDialog.getText(
            self.view,
            "Convert Project to Template",
            "Template Name:",
            text=default_name or "Untitled",
        )
        if not accepted:
            return ""

        template_name = utils_system.sanitize_filename(template_name)
        template_extension = f".{tools_rig_const.RiggerConstants.PROJECT_EXTENSION}"
        if template_name.lower().endswith(template_extension):
            template_name = template_name[: -len(template_extension)]
        if template_name:
            return template_name

        self.show_project_load_warning(
            title="Invalid Template Name",
            message="Enter a valid name for the template.",
        )
        return ""

    def show_template_overwrite_warning(self, template_path):
        """Asks the user before overwriting an existing template project file.

        Args:
            template_path (str): Existing template file that would be replaced.

        Returns:
            bool: True when the existing template may be replaced.
        """
        result = ui_qt.QtWidgets.QMessageBox.question(
            self.view,
            "Replace Existing Template",
            f"A template already exists at:\n\n{template_path}\n\nReplace its project data?",
            ui_qt.QtWidgets.QMessageBox.Yes | ui_qt.QtWidgets.QMessageBox.No,
            ui_qt.QtWidgets.QMessageBox.No,
        )
        return result == ui_qt.QtWidgets.QMessageBox.Yes

    def show_template_resource_copy_dialog(self, resource_target_dir):
        """Offers to copy detected project resources into a template folder.

        Args:
            resource_target_dir (str): Destination for the template resources.

        Returns:
            bool: True when the user requests a resource copy.
        """
        message_box = ui_qt.QtWidgets.QMessageBox(self.view)
        message_box.setWindowTitle("Project Resources Detected")
        message_box.setText(
            "The project directory contains files or folders in addition to the rig project.\n"
            "Would you like to copy them into this template's resources folder?\n\n"
            f"{resource_target_dir}\n\n"
            "Existing resource files will be retained."
        )
        copy_button = message_box.addButton("Copy Resources", ui_qt.QtWidgets.QMessageBox.AcceptRole)
        message_box.addButton("Skip Resources", ui_qt.QtWidgets.QMessageBox.RejectRole)
        message_box.exec_()
        return message_box.clickedButton() == copy_button

    # ----------------------------------------- Modules Tree -----------------------------------------
    def populate_module_tree(self):
        """
        Populate the module tree widget with the current project's modules.

        This method performs the following:
        - Refreshes and stores the expansion state of existing tree items.
        - Clears the current module tree view.
        - Adds the project as the top-level tree item with its icon.
        - Adds each module as a child item under the project, with icons and text.
        - Applies visual indicators for inactive modules.
        - Organizes the modules hierarchically by assigning children to their respective parent modules.
        - Restores the expansion state of the tree items after populating.

        The tree items are instances of QTreeItemEnhanced which support additional features such as
        """
        self.refresh_tree_expansion_state_variables()
        self.view.clear_module_tree()

        project = self.model.get_project()
        icon_project = ui_qt.QtGui.QIcon(project.icon)
        project_item = ui_tree_enhanced.QTreeItemEnhanced([project.get_name()])
        project_item.setIcon(0, icon_project)
        project_item.setData(1, 0, project)
        project_item.setFlags(project_item.flags() & ~ui_qt.QtLib.ItemFlag.ItemIsDragEnabled)
        self.view.add_item_to_module_tree(project_item)
        self.view.module_tree.set_drop_callback(self.on_drop_tree_module_item)

        modules = self.model.get_modules()
        tree_item_dict = {}
        for module in modules:
            icon = ui_qt.QtGui.QIcon(module.icon)
            module_type = module.get_description_name()
            tree_item = ui_tree_enhanced.QTreeItemEnhanced([module_type])
            tree_item.setIcon(0, icon)
            tree_item.setData(1, 0, module)
            project_item.addChild(tree_item)
            tree_item_dict[module] = tree_item
            tree_item.set_allow_parenting(state=module.allow_parenting)
            if not module.is_active() and not module.bypass_activation:
                tree_item.setForeground(0, ui_qt.QtGui.QColor(ui_res_lib.Color.Hex.gray_dim))

        # Create Hierarchy
        for module, tree_item in reversed(list(tree_item_dict.items())):
            parent_proxy_uuid = module.get_parent_uuid()
            if not parent_proxy_uuid or not isinstance(parent_proxy_uuid, str):
                continue
            parent_module = project.get_module_from_proxy_uuid(parent_proxy_uuid)
            if module == parent_module:
                continue
            parent_tree_item = tree_item_dict.get(parent_module)
            if parent_tree_item:
                index = project_item.indexOfChild(tree_item)
                child_item = project_item.takeChild(index)
                parent_tree_item.insertChild(0, child_item)

        self.apply_tree_expansion_state()

    def update_modules_order(self):
        """
        Updates the module order by matching the order of the QTreeWidget items in the project modules list
        """
        tree_items = self.view.module_tree.get_all_items()
        modules = [item.data(1, 0) for item in tree_items if isinstance(item.data(1, 0), tools_rig_frm.ModuleGeneric)]
        self.model.get_project().set_modules(modules)

    def update_module_parent(self):
        """
        Updates the module order by matching the order of the QTreeWidget items in the project modules list
        """
        source_item = self.view.module_tree.get_last_drop_source_item()
        target_item = self.view.module_tree.get_last_drop_target_item()

        if not source_item:
            self.refresh_widgets()
            return
        source_module = source_item.data(1, 0)

        if not target_item or target_item in self.view.module_tree.get_top_level_items():
            source_module.clear_parent_uuid()
            self.view.module_tree.setCurrentItem(source_item)
            return

        target_module = target_item.data(1, 0)
        target_proxies = []
        if target_module and hasattr(target_module, "get_proxies"):  # Is proxy
            target_proxies = target_module.get_proxies()
        if len(target_proxies) > 0:
            source_module.set_parent_uuid(target_proxies[0].get_uuid())
        self.view.module_tree.setCurrentItem(source_item)

    def on_drop_tree_module_item(self):
        """
        Function called when dropping a tree item
        """
        self.update_module_parent()
        self.update_modules_order()
        self.on_tree_item_clicked(item=self.view.module_tree.currentItem())  # Refresh Widget

    def show_module_tree_context_menu(self, position: ui_qt.QtCore.QPoint):
        """
        Shows the context menu for the module tree.
        Args:
            position (QPoint): Automatically passed when used with customContextMenuRequested.
                               Determines source of the RMB click.
        """
        item = self.view.module_tree.itemAt(position)
        if item is None:
            return

        menu = ui_qt.QtWidgets.QMenu()
        source_module = item.data(1, 0)

        # Expand All
        action_expand = ui_qt.QtLib.QtGui.QAction(
            "Expand Recursively", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_expand)
        )
        func_expand = partial(self.context_menu_expand_set_expanded_state_for_tree_items, item, True)
        action_expand.triggered.connect(func_expand)
        self.view.add_menu_action(parent_menu=menu, action=action_expand)

        # Collapse All
        action_collapse = ui_qt.QtLib.QtGui.QAction(
            "Collapse Recursively", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_collapse)
        )
        func_collapse = partial(self.context_menu_expand_set_expanded_state_for_tree_items, item, False)
        action_collapse.triggered.connect(func_collapse)
        self.view.add_menu_action(parent_menu=menu, action=action_collapse)

        # Un-parent
        action_unparent = ui_qt.QtLib.QtGui.QAction(
            "Unparent", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_unparent)
        )
        func_unparent_module = partial(self.context_menu_unparent_module, source_module)
        action_unparent.triggered.connect(func_unparent_module)
        action_unparent.triggered.connect(self.refresh_widgets)
        self.view.add_menu_action(parent_menu=menu, action=action_unparent)

        menu.addSeparator()

        # Duplicate
        action_duplicate = ui_qt.QtLib.QtGui.QAction(
            "Duplicate", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_duplicate)
        )
        func_duplicate_module = partial(self.model.get_project().duplicate_module, source_module)
        action_duplicate.triggered.connect(func_duplicate_module)
        action_duplicate.triggered.connect(self.refresh_widgets)
        self.view.add_menu_action(parent_menu=menu, action=action_duplicate)

        # Copy
        action_copy = ui_qt.QtLib.QtGui.QAction("Copy", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_copy))
        func_copy_module = partial(self.context_menu_copy_module, source_module)
        action_copy.triggered.connect(func_copy_module)
        self.view.add_menu_action(parent_menu=menu, action=action_copy)

        # Paste
        action_paste = ui_qt.QtLib.QtGui.QAction("Paste", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_paste))
        action_paste.triggered.connect(self.context_menu_paste_module)
        action_paste.triggered.connect(self.refresh_widgets)
        self.view.add_menu_action(parent_menu=menu, action=action_paste)

        # Export
        action_copy = ui_qt.QtLib.QtGui.QAction("Export", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_export))
        func_copy_module = partial(self.context_menu_export_module, source_module)
        action_copy.triggered.connect(func_copy_module)
        action_copy.triggered.connect(self.refresh_widgets)
        self.view.add_menu_action(parent_menu=menu, action=action_copy)

        # Import
        action_paste = ui_qt.QtLib.QtGui.QAction(
            "Import", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_import)
        )
        action_paste.triggered.connect(self.context_menu_import_module)
        action_paste.triggered.connect(self.refresh_widgets)
        self.view.add_menu_action(parent_menu=menu, action=action_paste)

        menu.addSeparator()

        # Delete
        action_delete = ui_qt.QtLib.QtGui.QAction("Delete", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_delete))
        func_delete_module = partial(self.delete_module_from_current_project, source_module)
        action_delete.triggered.connect(func_delete_module)
        action_delete.triggered.connect(self.view.clear_module_widget)
        action_delete.triggered.connect(self.refresh_widgets)
        self.view.add_menu_action(parent_menu=menu, action=action_delete)

        # Deactivate menu items when not a module
        if not source_module or not isinstance(source_module, tools_rig_frm.ModuleGeneric):
            action_unparent.setEnabled(False)
            action_duplicate.setEnabled(False)
            action_copy.setEnabled(False)
            action_delete.setEnabled(False)
        # Show Menu
        action = menu.exec_(self.view.module_tree.viewport().mapToGlobal(position))

    @staticmethod
    def context_menu_unparent_module(module):
        """
        Clears a module parent, so it's no longer part of a hierarchy
        Args:
            module (ModuleGeneric): A module to unparent from a hierarchy.
        """
        if not module.get_parent_uuid():
            logging.warning(f'Module "{module.get_name()}" already un-parented, operation was skipped.')
        else:
            module.clear_parent_uuid()
            logging.info(f'Module "{module.get_name()}" was un-parented.')

    @staticmethod
    def context_menu_copy_module(module):
        """
        Copies a module to the clipboard in a serialized dictionary format.
        Args:
            module (ModuleGeneric): A module to copy to the clip board.
                                    Gets converted to a dictionary and stored in the clipboard for later.
        """
        if not module or not isinstance(module, tools_rig_frm.ModuleGeneric):
            logger.warning('Unsupported data object. Please try again using a "ModuleGeneric" object.')
            return
        _as_dict = module.get_module_as_dict()
        _as_str = json.dumps(_as_dict, indent=4, ensure_ascii=False)
        ui_qt.QtWidgets.QApplication.clipboard().setText(_as_str)
        logger.info(f'"{module.get_name()}" was copied to the clipboard.')

    def context_menu_paste_module(self):
        """
        Attempt to interpret the clipboard content as a dictionary, and builds a module with the data when available.
        """
        try:
            clipboard_content = ui_qt.QtWidgets.QApplication.clipboard().text()
            clipboard_as_dict = json.loads(clipboard_content)
            self.model.get_project().add_module_from_dict(clipboard_as_dict)
        except Exception as e:
            logger.warning(f"Failed to paste module. Unsupported data type. Issue: {e}")

    @staticmethod
    def context_menu_export_module(module):
        """
        Exports a module to a file in a serialized JSON format.
        Args:
            module (ModuleGeneric): A module to export to the clip board.
                                    Gets converted to a dictionary and stored in the clipboard for later.
        """
        if not module or not isinstance(module, tools_rig_frm.ModuleGeneric):
            logger.warning('Unsupported data object. Please try again using a "ModuleGeneric" object.')
            return
        _as_dict = module.get_module_as_dict()
        _module_name = _as_dict.get("name", "")  # Default to the name of the module
        _save_path = ui_file_dialog.file_dialog(
            caption="Save Module",
            write_mode=True,
            starting_directory=_module_name,
            file_filter=tools_rig_const.RiggerConstants.PROJECT_FILE_FILTER,
            ok_caption="Save Module",
            cancel_caption="Cancel",
        )
        # Save Module
        if _save_path:
            # If already present, make it modifiable
            if _save_path and os.path.exists(_save_path):
                core_io.set_file_permission_modifiable(_save_path)
            core_io.write_json(path=_save_path, data=_as_dict)
            logger.info(f'Module "{_module_name}" saved to "{_save_path}".')

    def context_menu_import_module(self):
        """
        Attempt to interpret the clipboard content as a dictionary, and builds a module with the data when available.
        """

        file_path = ui_file_dialog.file_dialog(
            caption="Import module",
            write_mode=False,
            starting_directory=None,
            file_filter=tools_rig_const.RiggerConstants.MODULE_FILE_FILTER,
            ok_caption="Import module",
            cancel_caption="Cancel",
        )
        if file_path:
            try:
                module_data = core_io.read_data(file_path)
                _as_dict = json.loads(module_data)
                self.model.get_project().add_module_from_dict(_as_dict)
            except Exception as e:
                logger.warning(f"Failed to paste module. Unsupported data type. Issue: {e}")

    def delete_module_from_current_project(self, module):
        """
        Deletes the provided module and refreshes UI
        Args:
            module (ModuleGeneric): A model to be deleted.
        """
        self.model.get_project().remove_from_modules(module)

    def context_menu_expand_set_expanded_state_for_tree_items(self, item, state):
        """
        Expands all items
        Args:
            item (QTreeItem): Used as the parent of the expand operation. Only its children will be affected.
            state (bool): True is expanded, False if collapsed.
        """
        item.setExpanded(state)
        children = ui_qt_utils.get_all_tree_item_children(item)
        for child in children:
            child.setExpanded(state)
        self.refresh_widgets()

    def refresh_tree_expansion_state_variables(self):
        """
        Retrieve the expanded/collapsed state of all items in a QTreeWidget.

        This function recursively traverses the tree and refreshes the expanded state of the modules
        each module stores its own state as a boolean indicating whether the item is expanded.
        """
        _state_dict = {}

        def recurse(item):
            """
            Recursively visits each item in the tree starting from 'item',
            stores the expanded state of the associated module in _state_dict,
            and continues to traverse all child items.

            Args:
                item (QTreeWidgetItem): The current tree item to process.
            """
            source_module = item.data(1, 0)
            _state_dict[source_module] = item.isExpanded()
            for idx in range(item.childCount()):
                recurse(item.child(idx))

        for index in range(self.view.module_tree.topLevelItemCount()):
            recurse(self.view.module_tree.topLevelItem(index))

        for mod, state in _state_dict.items():
            if isinstance(mod, tools_rig_frm.ModuleGeneric):
                mod.set_expanded_state(state)

    def apply_tree_expansion_state(self):
        """
        Restore the expanded/collapsed state of items in the module QTreeWidget.

        This function traverses the tree and sets each item's expanded state based on
        a previously stored expanded state.
        """

        def recurse(item):
            """
            Recursively sets the expanded state of tree items based on their associated module type.

            Args:
                item (QTreeWidgetItem): The current tree item to check and update.
            """
            source_module = item.data(1, 0)
            if isinstance(source_module, tools_rig_frm.RigProject):  # Project is always expanded
                item.setExpanded(True)
            if isinstance(source_module, tools_rig_frm.ModuleGeneric):
                item.setExpanded(source_module.is_expanded())
            for idx in range(item.childCount()):
                recurse(item.child(idx))

        for index in range(self.view.module_tree.topLevelItemCount()):
            recurse(self.view.module_tree.topLevelItem(index))

    # ----------------------------------------- Quiting Event -----------------------------------------
    def show_unsaved_changes_warning_dialog(self, window, is_close_event=True, *args, **kwargs):
        """
        Save warning dialog used to prevent data loss. It offers options to save, don't save or cancel.
        Menu is only shown if unsaved changes are detected.
        Args:
            window (QDialog): A QT window to be made visible.
            is_close_event (bool, optional): When active, it assumes that a close event is happening and resets
                                             the visibility of the window when cancelling the operation.
            *args (any): Arguments (to capture potential events)
            **kwargs (any): Arguments (to capture potential events)
        Returns:
            bool: True if operation was cancelled.
        """
        # Check if there are changes to save
        if not self.has_unsaved_changes():
            return False
        # Show Save Dialog
        message_box = ui_qt.QtWidgets.QMessageBox(window)
        message_box.setWindowTitle("Warning: Unsaved changes!")
        message_box.setText("You have unsaved changes. What do you want to do?")

        # Add custom buttons for Save, Don't Save, and Cancel
        save_button = message_box.addButton("Save", ui_qt.QtWidgets.QMessageBox.AcceptRole)
        dont_save_button = message_box.addButton("Don't Save", ui_qt.QtWidgets.QMessageBox.DestructiveRole)
        cancel_button = message_box.addButton("Cancel", ui_qt.QtWidgets.QMessageBox.DestructiveRole)

        # Execute the message box and get the user response
        message_box.exec_()

        # Handle button clicks
        if message_box.clickedButton() == save_button:
            if not self.save_project_to_file():
                self.cancel_pending_operation(window=window, is_close_event=is_close_event, close_args=args)
                return True
            return False
        elif message_box.clickedButton() == dont_save_button:
            return False
        elif message_box.clickedButton() == cancel_button:
            self.cancel_pending_operation(window=window, is_close_event=is_close_event, close_args=args)
            return True
        return False

    @staticmethod
    def cancel_pending_operation(window, is_close_event=True, close_args=None):
        """Cancels a pending close or project-switch operation.

        Args:
            window (QDialog): Window associated with the operation.
            is_close_event (bool, optional): Whether a close event is active.
            close_args (tuple, optional): Possible close-event arguments.
        """
        if not is_close_event:
            return
        close_events = [arg for arg in close_args or [] if isinstance(arg, ui_qt.QtGui.QCloseEvent)]
        for close_event in close_events:
            close_event.ignore()
        if window and ui_qt_utils.is_qt_object_valid(window):
            visibility_func = partial(window.setVisible, True)
            ui_qt.QtCore.QTimer.singleShot(100, visibility_func)

    # --------------------------------------------- Misc ----------------------------------------------
    def add_selected_joints_module_generic(self):
        """
        Converts selected joints into a module generic.
        """
        new_generic_mod = tools_rig_utils.selected_joints_to_module_generic()
        if new_generic_mod:
            self.model.add_to_modules(module=new_generic_mod)
            self.refresh_widgets()

    def get_environment_variables(self):
        """
        Shows a window with the current environment variables and a refresh button.
        """

        def fetch_and_format_env_vars():
            """
            Gets the latest environment variables and formats them as a pretty JSON string.

            This nested function is passed to the UI to be called by the refresh button.

            Returns:
                str: A formatted string representation of the environment variables dictionary.
            """
            _project = self.model.get_project()
            _env_var_dict = tools_rig_frm.get_environment_variables(rig_project=_project)

            # Attempt to Get Module Data
            try:
                attr_widgets = self.view.get_module_widget()
                _env_var_dict = attr_widgets.module.get_module_environment_variables()
            except Exception as e:
                logger.debug(f"Unable to get environment variables from module. Module data was skipped. Issue: {e}")
            return json.dumps(_env_var_dict, indent=4, sort_keys=True)

        import gt.ui.python_output_view as ui_py_output

        py_output_win = ui_py_output.PythonOutputView(
            parent=self.view, button_label="Refresh", button_function=fetch_and_format_env_vars
        )

        # Set a more descriptive title for the window
        py_output_win.setWindowTitle("Environment Variables")

        # Set the initial text by calling the function once
        py_output_win.set_python_output_text(text=fetch_and_format_env_vars())

        py_output_win.show()

    def open_geometry_preprocessor(self):
        """
        Opens a tool used to adjust the geometry file paths before saving a rigging copy of it.
        """

        import gt.tools.auto_rigger.rigger_geo_preprocessor as tools_rig_geo_preprocess

        geo_migration_tool = tools_rig_geo_preprocess.GeometryPreprocessor(
            parent=ui_qt_utils.get_maya_main_window(), project=self.model.get_project()
        )
        geo_migration_tool.show()

    @staticmethod
    def get_project_from_built_rig():
        """
        Extracts and saves the project data associated with the single built rig in the current scene.

        This function retrieves metadata from the currently built rig using `tools_rig_utils.get_rigs_metadata`.
        It handles the following cases:
        - If no rigs are detected in the scene, a warning is logged.
        - If multiple rigs are present, a warning is logged and the function exits to avoid ambiguity.
        - If a single rig is found, it attempts to extract the project data from it.

        The user is then prompted with a file dialog to select a location to save the extracted project
        data as a JSON file. If the file already exists, its permissions are adjusted to allow writing,
        and the new data is written to it.
        """
        _rig_project = None
        scene_rigs_metadata = tools_rig_utils.get_rigs_metadata()
        if len(scene_rigs_metadata) == 0:
            logger.warning(f"No rigs detected in the scene.")
            return
        if len(scene_rigs_metadata) > 1:
            logger.warning(
                f"Unable to extract project from built rig because multiple rigs ({len(scene_rigs_metadata)}) were "
                f"detected in the scene. Remove other rigs and try again."
            )
            return

        _rig_uuid, _rig_project = next(iter(scene_rigs_metadata.items()))  # Grab first available rig
        if not _rig_project.get(tools_rig_const.RiggerConstants.ATTR_RIG_PROJECT_DATA):
            logger.warning(
                f"Something went wrong. A rig was detected, but the function failed to extract its data."
                f'You can try getting it manually under the string attribute "|rig.project".'
            )
            return

        # File Dialog
        _save_path = None
        _save_path = ui_file_dialog.file_dialog(
            caption="Save Rig Project",
            write_mode=True,
            starting_directory=_rig_project.get(tools_rig_const.RiggerConstants.ATTR_RIG_PROJECT_NAME, ""),
            file_filter=tools_rig_const.RiggerConstants.PROJECT_FILE_FILTER,
            ok_caption="Save Project",
            cancel_caption="Cancel",
        )
        # Save Project
        if _save_path:
            # If already present, make it modifiable
            if _save_path and os.path.exists(_save_path):
                core_io.set_file_permission_modifiable(_save_path)
            core_io.write_json(
                path=_save_path, data=_rig_project.get(tools_rig_const.RiggerConstants.ATTR_RIG_PROJECT_DATA)
            )
            logger.info(f'Extracted project saved to "{_save_path}".')

    def toggle_on_build_clear_log_window(self, checked):
        """
        Toggle the flag to clear the log window when building the rig.
        Args:
            checked (bool): The new state for clearing the log window on build.
        """
        self._on_build_clear_log_window = checked
        self._prefs.set_bool(key=tools_rig_const.RiggerConstants.PREFS_KEY_ON_BUILD_CLEAR_LOG, value=checked)
        self._prefs.save()

    def toggle_on_build_show_log_view(self, checked):
        """
        Toggle the flag to show the log view when building the rig.

        Args:
            checked (bool): The new state for showing the log view on build.
        """
        self._on_build_show_log_view = checked
        self._prefs.set_bool(key=tools_rig_const.RiggerConstants.PREFS_KEY_ON_BUILD_SHOW_LOG, value=checked)
        self._prefs.save()

    def toggle_on_set_path_abs_to_relative(self, checked):
        """
        Toggle the flag to convert absolute paths to relative paths when setting paths.

        Args:
            checked (bool): The new state for converting absolute paths to relative.
        """
        self._on_set_path_abs_to_relative = checked
        self._prefs.set_bool(key=tools_rig_const.RiggerConstants.PREFS_KEY_ON_SET_PATH_ABS_TO_RELATIVE, value=checked)
        self._prefs.save()

    # -------------------------------------------- General --------------------------------------------
    def set_opened_project(self, path):
        """
        Sets the currently opened project. Used to track warning and saving operations.
        Args:
            path (str): A path to the current project.
        """
        if os.path.exists(path):
            path = self._recent_projects.normalize_path(path)
            self._opened_project = path
            file_name = os.path.basename(path)
            self.view.set_window_title(prefix=file_name)
            self._opened_project_initial_state = self.model.get_project().get_project_as_dict()
            self._has_high_level_changes = False
            self._recent_projects.add_path(path)
            self.refresh_recent_projects_menu()

    def clear_opened_project(self):
        """
        Sets the opened project to an empty string. Used to track warning and saving operations.
        """
        self._opened_project = ""
        self._opened_project_initial_state = {}
        self.view.set_window_title(prefix=None)

    def has_unsaved_changes(self):
        """
        Determines if opened project has unsaved changes.
        Returns:
            bool: True if there are unsaved changes, False otherwise.
        """
        # Where there any high level changes?
        if self._has_high_level_changes:
            return True
        # Did the user update any modules?
        _current_dict = self.model.get_project().get_project_as_dict()
        _current_modules = _current_dict.get("modules")
        _initial_state_modules = self._opened_project_initial_state.get("modules", [])
        if _current_modules != _initial_state_modules:
            return True
        return False

    def refresh_widgets(self):
        """
        Refreshes widgets
        """
        self.populate_module_tree()
        self._has_high_level_changes = True

    def on_tree_item_clicked(self, item, *kwargs):
        """
        When an item from the tree is selected, it should populate the attribute editor with the available fields.
        This function determines which widget should be used an updates the view with the generated widgets.
        Args:
            item (QTreeWidgetItem): Clicked item (selected)
            **kwargs: Additional keyword arguments. Not used in this case. (Receives column key argument)
        """
        data_obj = item.data(1, 0)
        # Modules ---------------------------------------------------------------
        if isinstance(data_obj, tools_rig_frm.ModuleGeneric):
            widget_class = get_module_attr_widgets(module=data_obj)
            if widget_class:
                widget_object = widget_class(
                    module=data_obj, project=self.model.get_project(), refresh_parent_func=self.refresh_widgets
                )
                self.view.set_module_widget(widget_object)
                return
        # Project ---------------------------------------------------------------
        if isinstance(data_obj, tools_rig_frm.RigProject):
            widget_object = tools_rig_attr_widget.AttrWidgetProject(
                project=data_obj, refresh_parent_func=self.refresh_widgets
            )
            self.view.set_module_widget(widget_object)
            return
        # Unknown ---------------------------------------------------------------
        self.view.clear_module_widget()

    def preprocessing_validation(self):
        """
        Validates the scene to identify any potential conflicts before building proxy or rig.
        Returns:
            bool: True if operation was cancelled or an issue was detected.
                  False if operation is ready to proceed.
        """
        # Existing Proxy ------------------------------------------------------------------------
        proxy_grp = tools_rig_utils.find_root_group_proxy()
        if proxy_grp:
            message_box = ui_qt.QtWidgets.QMessageBox(self.view)
            message_box.setWindowTitle(f"Proxy detected in the scene.")
            message_box.setText(
                f"A pre-existing proxy was detected in the scene. \n" f"How would you like to proceed?"
            )

            message_box.addButton("Ignore Changes and Rebuild", ui_qt.QtLib.ButtonRoles.ActionRole)
            message_box.addButton("Read Changes and Rebuild", ui_qt.QtLib.ButtonRoles.ActionRole)
            message_box.addButton("Cancel", ui_qt.QtLib.ButtonRoles.RejectRole)
            question_icon = ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_exclamation)
            message_box.setIconPixmap(question_icon.pixmap(64, 64))
            result = message_box.exec_()
            if result == 0:
                import maya.cmds as cmds

                cmds.delete(proxy_grp)
            elif result == 1:
                import maya.cmds as cmds

                self.model.get_project().read_data_from_scene()
                cmds.delete(proxy_grp)
            else:
                return True
        # Existing Rig -------------------------------------------------------------------------
        rig_grp = tools_rig_utils.find_root_group_rig()
        if rig_grp:
            message_box = ui_qt.QtWidgets.QMessageBox(self.view)
            message_box.setWindowTitle(f"Existing rig detected in the scene.")
            message_box.setText(f"A pre-existing rig was detected in the scene. \n" f"How would you like to proceed?")

            message_box.addButton("Delete Current and Rebuild", ui_qt.QtLib.ButtonRoles.ActionRole)
            message_box.addButton("Cancel", ui_qt.QtLib.ButtonRoles.ActionRole)
            question_icon = ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_exclamation)
            message_box.setIconPixmap(question_icon.pixmap(64, 64))
            result = message_box.exec_()
            if result == 0:
                import maya.cmds as cmds

                cmds.delete(rig_grp)
            else:
                return True
        return False

    def build_proxy(self):
        """Builds Proxy using the project "build_proxy" function."""
        if self.preprocessing_validation():
            return

        # Log Preferences
        if self._on_build_clear_log_window:
            self.log_view.clear_log_widget()
        if self._on_build_show_log_view:
            self.log_view.show_if_not_visible()

        project = self.model.get_project()
        logger.operation(f'Initializing build proxy operation for "{project.get_name()}".')
        project.build_proxy()
        logger.success(f"Build proxy operation completed.")

    def build_rig(self):
        """Builds Rig using the project "build_rig" function."""
        if self.preprocessing_validation():
            return

        # Log Preferences
        if self._on_build_clear_log_window:
            self.log_view.clear_log_widget()
        if self._on_build_show_log_view:
            self.log_view.show_if_not_visible()

        project = self.model.get_project()

        logger.operation(f'Initializing build rig operation for "{project.get_name()}".')
        project.build_proxy(optimized=True)
        project.build_rig()
        logger.success(f'Build rig operation completed for "{project.get_name()}".')


if __name__ == "__main__":
    print('Run it from "__init__.py".')
