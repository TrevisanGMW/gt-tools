"""
Auto Rigger Controller
"""
from gt.tools.auto_rigger.rig_utils import RiggerConstants, find_proxy_root_group_node, find_rig_root_group_node
from PySide2.QtWidgets import QTreeWidgetItem, QAction, QMessageBox
from gt.utils.string_utils import camel_case_split, remove_prefix
from gt.tools.auto_rigger.rig_templates import RigTemplates
from gt.ui.tree_widget_enhanced import QTreeItemEnhanced
from gt.tools.auto_rigger.rig_modules import RigModules
from gt.tools.auto_rigger import rigger_attr_widget
from gt.tools.auto_rigger import rig_framework
from gt.ui.file_dialog import file_dialog
from gt.ui import resource_library
from PySide2.QtGui import QIcon, QColor
from PySide2.QtCore import Qt
from functools import partial
import logging


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_module_attr_widgets(module):
    """
    Gets the associated attribute widget used to populate the attribute editor in the main UI.
    Returns:
        ModuleAttrWidget: Widget used to populate the attribute editor of the rigger window.
    """
    if type(module) is RigModules.ModuleGeneric:
        return rigger_attr_widget.ModuleGenericAttrWidget
    if isinstance(module, RigModules.ModuleSpine):
        return rigger_attr_widget.ModuleSpineAttrWidget
    if isinstance(module, RigModules.ModuleBipedLeg):
        return rigger_attr_widget.ModuleSpineAttrWidget  # TODO TEMP @@@
    else:
        return rigger_attr_widget.ModuleSpineAttrWidget  # TODO TEMP @@@


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

        self.populate_module_tree()

        # Connections
        self.view.module_tree.itemClicked.connect(self.on_tree_item_clicked)
        self.view.build_proxy_btn.clicked.connect(self.build_proxy)
        self.view.build_rig_btn.clicked.connect(self.build_rig)
        # self.view.module_tree.set_drop_callback(self.refresh_widgets)  # TODO TEMP @@@

        # Add Menubar
        self.add_menu_file()
        self.add_menu_modules()

        # Show
        self.view.show()

    # ------------------------------------------- Top Menu -------------------------------------------
    def add_menu_file(self):
        """
        Adds a menu bar to the view
        """
        menu_file = self.view.add_menu_parent("File")
        action_new = QAction("New Project", icon=QIcon(resource_library.Icon.ui_new))
        action_new.triggered.connect(self.initialize_new_project)

        action_open = QAction("Open Project", icon=QIcon(resource_library.Icon.ui_open))
        action_open.triggered.connect(self.load_project_from_file)

        action_save = QAction("Save Project", icon=QIcon(resource_library.Icon.ui_save))
        action_save.triggered.connect(self.save_project_to_file)

        # Menu Assembly -------------------------------------------------------------------------------------
        self.view.add_menu_action(parent_menu=menu_file, action=action_new)
        self.view.add_menu_action(parent_menu=menu_file, action=action_open)
        self.view.add_menu_action(parent_menu=menu_file, action=action_save)
        # Templates
        menu_templates = self.view.add_menu_submenu(parent_menu=menu_file,
                                                    submenu_name="Templates",
                                                    icon=QIcon(resource_library.Icon.ui_templates))
        for name, template_func in RigTemplates.get_dict_templates().items():
            formatted_name = " ".join(camel_case_split(name))
            action_template = QAction(formatted_name, icon=QIcon(resource_library.Icon.rigger_template_biped))
            item_func = partial(self.replace_project, project=template_func)
            action_template.triggered.connect(item_func)
            self.view.add_menu_action(parent_menu=menu_templates, action=action_template)

    def add_menu_modules(self):
        """
        Adds a menu bar to the view
        """
        from gt.tools.auto_rigger.rig_modules import RigModulesCategories
        menu_modules = self.view.add_menu_parent("Modules")
        known_categories = RigModulesCategories.known_categories
        for name, module_name in RigModulesCategories.categories.items():
            _icon_path = known_categories.get(name, None)

            menu_templates = self.view.add_menu_submenu(parent_menu=menu_modules,
                                                        submenu_name=name,
                                                        icon=QIcon(_icon_path))
            if isinstance(module_name, list):
                for unique_mod in module_name:
                    module_list = RigModulesCategories.unique_modules.get(unique_mod)
                    formatted_name = " ".join(camel_case_split(unique_mod))
                    action_mod = QAction(formatted_name, icon=QIcon(module_list[0].icon))
                    item_func = partial(self.add_module_to_project_from_list,
                                        module_name=formatted_name,
                                        module_list=module_list)
                    action_mod.triggered.connect(item_func)
                    self.view.add_menu_action(parent_menu=menu_templates, action=action_mod)

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
            logger.debug(f'Unable to create module choice dialog')
            return
        # One Module
        if len(module_list) == 1:
            self.add_module_to_project(module=module_list[0])
            return
        # Multiple Options
        message_box = QMessageBox(self.view)
        message_box.setWindowTitle(f'Which "{str(module_name)}" Module?')
        message_box.setText(f'Which variation of "{str(module_name)}"\nwould like to add?')

        question_icon = QIcon(module_list[0].icon)
        message_box.setIconPixmap(question_icon.pixmap(64, 64))
        for mod in module_list:
            formatted_name = remove_prefix(input_string=str(mod.__name__), prefix="Module")
            formatted_name = " ".join(camel_case_split(formatted_name))
            message_box.addButton(formatted_name, QMessageBox.ActionRole)
        result = message_box.exec_()
        self.add_module_to_project(module=module_list[result])

    def initialize_new_project(self):
        """
        Re-initializes the project to an empty one and refreshes the view.
        """
        self.model.clear_project()
        self.refresh_widgets()

    def save_project_to_file(self):
        """
        Shows a save file dialog offering to save the current project to a file. (JSON formatted)
        """
        file_path = file_dialog(caption="Save Rig Project",
                                write_mode=True,
                                starting_directory=None,
                                file_filter=RiggerConstants.FILE_FILTER,
                                ok_caption="Save Project",
                                cancel_caption="Cancel")
        if file_path:
            self.model.save_project_to_file(path=file_path)

    def load_project_from_file(self):
        """
        Shows an open file dialog offering to load a new project from a file. (JSON formatted)
        """
        file_path = file_dialog(caption="Open Rig Project",
                                write_mode=False,
                                starting_directory=None,
                                file_filter=RiggerConstants.FILE_FILTER,
                                ok_caption="Open Project",
                                cancel_caption="Cancel")
        if file_path:
            self.model.load_project_from_file(path=file_path)
            self.refresh_widgets()

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

    # ----------------------------------------- Modules Tree -----------------------------------------
    def populate_module_tree(self):
        self.view.clear_module_tree()

        project = self.model.get_project()
        icon_project = QIcon(project.icon)
        project_item = QTreeItemEnhanced([project.get_name()])
        project_item.setIcon(0, icon_project)
        project_item.setData(1, 0, project)
        project_item.setFlags(project_item.flags() & ~Qt.ItemIsDragEnabled)
        self.view.add_item_to_module_tree(project_item)
        self.view.module_tree.set_drop_callback(self.on_drop_tree_module_item)

        modules = self.model.get_modules()
        tree_item_dict = {}
        for module in modules:
            icon = QIcon(module.icon)
            module_type = module.get_description_name()
            tree_item = QTreeItemEnhanced([module_type])
            tree_item.setIcon(0, icon)
            tree_item.setData(1, 0, module)
            project_item.addChild(tree_item)
            tree_item_dict[module] = tree_item
            tree_item.set_allow_parenting(state=module.allow_parenting)
            if not module.is_active():
                tree_item.setForeground(0, QColor(resource_library.Color.Hex.gray_dim))

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

        self.view.expand_all_module_tree_items()

    def update_modules_order(self):
        """
        Updates the module order by matching the order of the QTreeWidget items in the project modules list
        """
        tree_items = self.view.module_tree.get_all_items()
        modules = [item.data(1, 0) for item in tree_items if isinstance(item.data(1, 0), rig_framework.ModuleGeneric)]
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
        if target_module and hasattr(target_module, 'get_proxies'):  # Is proxy
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

    # ------------------------------------------- General --------------------------------------------
    def refresh_widgets(self):
        """
        Refreshes widgets
        """
        self.populate_module_tree()

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
        if isinstance(data_obj, rig_framework.ModuleGeneric):
            widget_class = get_module_attr_widgets(module=data_obj)
            if widget_class:
                widget_object = widget_class(module=data_obj,
                                             project=self.model.get_project(),
                                             refresh_parent_func=self.refresh_widgets)
                self.view.set_module_widget(widget_object)
                return
        # Project ---------------------------------------------------------------
        if isinstance(data_obj, rig_framework.RigProject):
            self.view.set_module_widget(rigger_attr_widget.ProjectAttrWidget(project=data_obj))
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
        proxy_grp = find_proxy_root_group_node()
        if proxy_grp:
            message_box = QMessageBox(self.view)
            message_box.setWindowTitle(f'Proxy detected in the scene.')
            message_box.setText(f'A pre-existing proxy was detected in the scene. \n'
                                f'How would you like to proceed?')

            message_box.addButton("Ignore Changes and Rebuild", QMessageBox.ActionRole)
            message_box.addButton("Read Changes and Rebuild", QMessageBox.ActionRole)
            message_box.addButton("Cancel", QMessageBox.RejectRole)
            question_icon = QIcon(resource_library.Icon.ui_exclamation)
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
        rig_grp = find_rig_root_group_node()
        if rig_grp:
            message_box = QMessageBox(self.view)
            message_box.setWindowTitle(f'Existing rig detected in the scene.')
            message_box.setText(f'A pre-existing rig was detected in the scene. \n'
                                f'How would you like to proceed?')

            message_box.addButton("Delete Current and Rebuild", QMessageBox.ActionRole)
            message_box.addButton("Unpack Geometries and Rebuild", QMessageBox.ActionRole)
            message_box.addButton("Cancel", QMessageBox.ActionRole)
            question_icon = QIcon(resource_library.Icon.ui_exclamation)
            message_box.setIconPixmap(question_icon.pixmap(64, 64))
            result = message_box.exec_()
            if result == 0:
                import maya.cmds as cmds
                cmds.delete(rig_grp)
            elif result == 1:
                import maya.cmds as cmds
                print("unpack here")  # TODO @@@
                cmds.delete(rig_grp)
            else:
                return True
        return False

    def build_proxy(self):
        if self.preprocessing_validation():
            return
        project = self.model.get_project()
        project.build_proxy()

    def build_rig(self):
        if self.preprocessing_validation():
            return
        project = self.model.get_project()
        project.build_proxy(optimized=True)
        project.build_rig()


if __name__ == "__main__":
    print('Run it from "__init__.py".')
