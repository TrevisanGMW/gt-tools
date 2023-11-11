"""
Auto Rigger Controller
"""
from gt.tools.auto_rigger.rig_modules import RigModules
from gt.tools.auto_rigger import rigger_attr_widget
from gt.tools.auto_rigger import rig_framework
from PySide2.QtWidgets import QTreeWidgetItem
from PySide2.QtGui import QIcon
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

        # Show
        self.view.show()

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
            widget_obj = get_module_attr_widgets(module=data_obj)
            if widget_obj:
                self.view.set_module_widget(widget_obj(module=data_obj, project=self.model.get_project()))
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
