"""
Auto Rigger Controller
"""
from gt.tools.auto_rigger.rigger_attr_widget import ModuleAttrWidget, ProjectAttrWidget, ModuleGenericAttrWidget
from PySide2.QtWidgets import QTreeWidgetItem
from PySide2.QtGui import QIcon
import logging

from gt.tools.auto_rigger import rig_framework

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RiggerController:
    widget_connections = {}

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
        self.view.module_tree.itemClicked.connect(self.item_clicked)
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

    def item_clicked(self, item, column):
        print("Clicked item:", item.text(column))
        data_obj = item.data(1, 0)
        if isinstance(data_obj, rig_framework.ModuleGeneric):  # Modules
            if type(data_obj) is rig_framework.ModuleGeneric:
                self.view.set_module_widget(ModuleGenericAttrWidget(module=data_obj, project=self.model.get_project()))
            else:
                self.view.set_module_widget(ModuleAttrWidget(module=data_obj, project=self.model.get_project()))
        elif isinstance(data_obj, rig_framework.RigProject):  # Project
            self.view.set_module_widget(ProjectAttrWidget(project=data_obj))
        else:
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
