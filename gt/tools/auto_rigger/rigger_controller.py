"""
Auto Rigger Controller
"""
from gt.tools.auto_rigger.rig_modules import RigModules
from gt.tools.auto_rigger import rigger_attr_widget
from gt.tools.auto_rigger import rig_framework
from PySide2.QtWidgets import QTreeWidgetItem, QAction
from gt.ui import resource_library
from PySide2.QtGui import QIcon
import logging

from ui.file_dialog import file_dialog

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

        # Add Menubar
        self.add_menu_bar()

        # Show
        self.view.show()

    def add_menu_bar(self):
        """
        Adds a menu bar to the view
        """
        # Menubar
        submenu_file = self.view.add_submenu("File")
        new_action = QAction("New Project", icon=QIcon(resource_library.Icon.dev_trowel))
        new_action.triggered.connect(self.initialize_new_project)
        open_action = QAction("Open Project", icon=QIcon(resource_library.Icon.dev_brain))
        open_action.triggered.connect(self.load_project_from_file)
        save_action = QAction("Save Project", icon=QIcon(resource_library.Icon.dev_code))
        save_action.triggered.connect(self.save_project_to_file)
        exit_action = QAction("Exit", icon=QIcon(resource_library.Icon.dev_chainsaw))
        exit_action.triggered.connect(self.view.close)
        self.view.add_action_to_submenu(submenu=submenu_file, action=new_action)
        self.view.add_action_to_submenu(submenu=submenu_file, action=open_action)
        self.view.add_action_to_submenu(submenu=submenu_file, action=save_action)
        self.view.add_action_to_submenu(submenu=submenu_file, action=exit_action)

    def initialize_new_project(self):
        """
        Re-initializes the project to an empty one and refreshes the view.
        """
        self.model.clear_project()
        self.populate_module_tree()

    def save_project_to_file(self):
        """
        Shows a save file dialog offering to save the current project to a file. (JSON formatted)
        """
        file_path = file_dialog(caption="Save Rig Project",
                                write_mode=True,
                                starting_directory=None,
                                file_filter="All Files (*);;",
                                ok_caption="Save Project",
                                cancel_caption="Cancel")
        if file_path:
            self.model.save_project_to_file(path=file_path)
            self.populate_module_tree()

    def load_project_from_file(self):
        """
        Shows an open file dialog offering to load a new project from a file. (JSON formatted)
        """
        file_path = file_dialog(caption="Open Rig Project",
                                write_mode=False,
                                starting_directory=None,
                                file_filter="All Files (*);;",
                                ok_caption="Open Project",
                                cancel_caption="Cancel")
        if file_path:
            self.model.load_project_from_file(path=file_path)
            self.populate_module_tree()

    def populate_module_tree(self):
        self.view.clear_module_tree()
        project = self.model.get_project()
        icon_project = QIcon(project.icon)
        project_item = QTreeWidgetItem([project.get_name()])
        project_item.setIcon(0, icon_project)
        project_item.setData(1, 0, project)
        self.view.add_item_to_module_tree(project_item)

        modules = self.model.get_modules()
        for module in modules:
            icon = QIcon(module.icon)
            module_type = module.get_module_class_name(remove_module_prefix=True)
            tree_item = QTreeWidgetItem([module_type])
            tree_item.setIcon(0, icon)
            tree_item.setData(1, 0, module)
            project_item.addChild(tree_item)

        self.view.expand_all_module_tree_items()

    def refresh_widgets(self):
        self.populate_module_tree()

    def on_tree_item_clicked(self, item, column):
        """
        When an item from the tree is selected, it should populate the attribute editor with the available fields.
        This function determines which widget should be used an updates the view with the generated widgets.
        Args:
            item (QTreeWidgetItem): Clicked item (selected)
            column (int): Source column.
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

    def get_selected_module(self):
        pass

    def save_project(self):
        pass

    def load_project(self):
        pass

    def build_proxy(self):
        project = self.model.get_project()
        project.build_proxy()

    def build_rig(self):
        project = self.model.get_project()
        project.build_rig()


if __name__ == "__main__":
    print('Run it from "__init__.py".')
