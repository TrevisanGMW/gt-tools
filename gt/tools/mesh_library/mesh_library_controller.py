"""
Mesh Library Controller

This module contains the MeshLibraryController class responsible for managing interactions between the
MeshLibraryModel and the user interface.
"""
from PySide2.QtWidgets import QMessageBox, QAbstractItemView
from gt.ui.input_window_text import InputWindowText
from gt.utils.prefs_utils import Prefs
from gt.utils import iterable_utils
from gt.ui import resource_library
from PySide2.QtGui import QIcon
from functools import partial
from PySide2.QtCore import Qt
import logging
import sys
import os


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MeshLibraryController:
    MESH_TYPE_BASE = "Mesh"
    MESH_TYPE_USER = "User Mesh"
    MESH_TYPE_PARAM = "Parametric Mesh"

    def __init__(self, model, view):
        """
        Initialize the MeshLibraryController object.

        Args:
            model: The MeshLibraryModel object used for data manipulation.
            view: The view object to interact with the user interface.
        """
        self.model = model
        self.view = view
        self.view.controller = self
        # Preferences
        self.preferences = Prefs("mesh_library")
        self.preferences.set_user_files_sub_folder("user_meshes")
        user_meshes_dir = self.preferences.get_user_files_dir_path(create_if_missing=False)
        self.model.import_user_mesh_library(source_dir=user_meshes_dir)
        # Connections
        self.view.build_button.clicked.connect(self.build_view_selected_mesh)
        self.view.item_list.itemSelectionChanged.connect(self.on_item_selection_changed)
        self.view.search_bar.textChanged.connect(self.filter_list)
        self.view.parameters_button.clicked.connect(self.open_parameter_editor)
        self.view.add_custom_button.clicked.connect(self.add_user_mesh)
        self.view.delete_custom_button.clicked.connect(self.remove_user_mesh)
        self.view.snapshot_button.clicked.connect(self.render_mesh_snapshot)
        self.populate_mesh_library()
        self.view.show()

    def on_item_selection_changed(self):
        """
        Update the preview image in the view when the selected item in the list changes.
        """
        item = self.view.item_list.currentItem()
        if not item:
            logger.debug(f'No item selected. Skipping UI update.')
            return
        item_name = self.view.item_list.currentItem().text()
        metadata = item.data(Qt.UserRole)
        new_preview_image = self.model.get_preview_image(object_name=item_name)
        if new_preview_image:
            self.view.update_preview_image(new_image_path=new_preview_image)
        if metadata and "item_type" in metadata:
            self.view.update_item_description(metadata.get("item_type"), item_name)
            if metadata.get("item_type") == self.MESH_TYPE_BASE:
                self.set_view_base_mesh_mode()
            elif metadata.get("item_type") == self.MESH_TYPE_USER:
                self.set_view_user_mesh_mode()
                user_preview_image = self.get_custom_mesh_preview_image()
                self.view.update_preview_image(new_image_path=user_preview_image)
            elif metadata.get("item_type") == self.MESH_TYPE_PARAM:
                self.set_view_parametric_mesh_mode()

    def set_view_base_mesh_mode(self):
        """ Changes the UI to look like you have a package mesh (base) selected """
        self.view.set_snapshot_button_enabled(False)
        self.view.set_parameters_button_enabled(False)
        self.view.set_delete_button_enabled(False)

    def set_view_user_mesh_mode(self):
        """ Changes the UI to look like you have a user-defined mesh selected """
        self.view.set_snapshot_button_enabled(True)
        self.view.set_parameters_button_enabled(False)
        self.view.set_delete_button_enabled(True)

    def set_view_parametric_mesh_mode(self):
        """ Changes the UI to look like you have a package parametric mesh selected """
        self.view.set_snapshot_button_enabled(False)
        self.view.set_parameters_button_enabled(True)
        self.view.set_delete_button_enabled(False)

    def filter_list(self):
        """
        Filter the mesh library list based on the search text entered by the user.
        """
        search_text = self.view.search_bar.text().lower()
        self.populate_mesh_library(filter_str=search_text)

    def build_view_selected_mesh(self):
        """
        Build the selected mesh from the mesh library in the model.
        """
        current_mesh = self.get_selected_item_object()
        self.model.build_mesh(mesh=current_mesh)

    def get_selected_item_object(self):
        """
        Gets the mesh of the currently selected element in the list
        Returns:
            MeshFile, ParametricMesh or None: Object stored in the metadata of the selected item.
                                              None if not found or nothing selected.
        """
        item = self.view.item_list.currentItem()
        if not item:
            logger.debug(f'No item selected.')
            return
        metadata = item.data(Qt.UserRole)
        if not metadata or not metadata.get("object"):
            logger.debug(f'Selected item "{item}" is missing the metadata necessary to retrieve a mesh.')
            return
        return metadata.get("object")

    def select_item_by_name(self, item_name):
        """
        Selects item based on its name
        Returns:
            bool: True if item was found and selected. False if item with given name was not found.
        """
        list_widget = self.view.item_list
        for index in range(list_widget.count()):
            item = list_widget.item(index)
            if item.text() == item_name:
                item.setSelected(True)
                list_widget.scrollToItem(item, QAbstractItemView.PositionAtCenter)
                self.view.item_list.setCurrentItem(item)
                self.on_item_selection_changed()
                return True
        return False

    def populate_mesh_library(self, filter_str=None):
        """
        Update the view with the current list of items from the model.
        Args:
            filter_str (str, None): If provided, it will be used to filter desired objects when populating the list.
        """
        self.view.clear_view_library()
        meshes_base = self.model.get_base_meshes()
        meshes_param = self.model.get_param_meshes()
        meshes_user = self.model.get_user_meshes()

        icon_base_mesh = QIcon(resource_library.Icon.mesh_library_base)
        icon_param_mesh = QIcon(resource_library.Icon.mesh_library_param)
        icon_user_mesh = QIcon(resource_library.Icon.mesh_library_user)

        for mesh_name, mesh in meshes_base.items():
            if filter_str and filter_str not in mesh_name:
                continue
            metadata_base_mesh = {"object": mesh, "item_type": self.MESH_TYPE_BASE}
            self.view.add_item_view_library(item_name=mesh_name, icon=icon_base_mesh, metadata=metadata_base_mesh)
        for mesh_name, param_mesh in meshes_param.items():
            if filter_str and filter_str not in mesh_name:
                continue
            metadata_param_mesh = {"object": param_mesh, "item_type": self.MESH_TYPE_PARAM}
            self.view.add_item_view_library(item_name=mesh_name, icon=icon_param_mesh, metadata=metadata_param_mesh)
        for mesh_name, user_mesh in meshes_user.items():
            if filter_str and filter_str not in user_mesh.get_name():
                continue
            metadata_user_mesh = {"object": user_mesh, "item_type": self.MESH_TYPE_USER}
            self.view.add_item_view_library(item_name=mesh_name, icon=icon_user_mesh, metadata=metadata_user_mesh)
        self.view.item_list.setCurrentRow(0)  # Select index 0

    def open_parameter_editor(self):
        """ Opens an input window so the user can update the parameters of a parametric mesh """
        item = self.view.item_list.currentItem()
        if not item:
            logger.warning(f'No item selected. Unable to open parameter editor.')
            return
        item_name = self.view.item_list.currentItem().text()
        param_mesh = self.get_selected_item_object()
        parameters = param_mesh.get_parameters()
        if not parameters:
            logger.debug(f'Selected parametric mesh does not have any parameters.')
            parameters = "{\n# This parametric mesh does not have any parameters.\n}"
        from gt.utils.mesh_utils import ParametricMesh
        if not isinstance(param_mesh, ParametricMesh):
            logger.warning(f'Unable to edit parameters. Selected item is not of the type "ParametricMesh."')
            return
        param_win = InputWindowText(parent=self.view,
                                    message=param_mesh.get_docstrings(),
                                    window_title=f'Parameters for "{item_name}"',
                                    image=resource_library.Icon.mesh_library_param,
                                    window_icon=resource_library.Icon.library_parameters,
                                    image_scale_pct=10,
                                    is_python_code=True)
        param_win.set_confirm_button_text("Build")
        formatted_dict = None
        if isinstance(parameters, dict):
            formatted_dict = iterable_utils.dict_as_formatted_str(parameters, one_key_per_line=True)
        elif isinstance(parameters, str):
            formatted_dict = parameters
        param_win.set_text_field_text(formatted_dict)
        param_win.confirm_button.clicked.connect(partial(self.model.build_mesh_with_custom_parameters,
                                                         param_win.get_text_field_text, param_mesh))
        param_win.show()

    def add_user_mesh(self):
        """
        Attempts to create a user-defined mesh (saved to the preferences' folder)
        Nothing is created in case operation fails.
        """
        path_dir = self.preferences.get_user_files_dir_path()
        mesh = self.model.export_potential_user_mesh_from_selection(target_dir_path=path_dir)
        if mesh:
            mesh_name = mesh.get_name()
            if os.path.exists(path_dir):
                # Refresh model and view
                self.model.import_user_mesh_library(source_dir=path_dir)
                self.populate_mesh_library()
                self.select_item_by_name(mesh_name)
                self.set_view_user_mesh_mode()

    def remove_user_mesh(self):
        """
        Deletes selected mesh (only user meshes) - Asks for confirmation through a dialog before deleting it.
        """
        mesh = self.get_selected_item_object()
        if not mesh:
            logger.warning(f'Unable to retrieve mesh object associated to selected item.')
            return
        mesh_name = mesh.get_name()
        user_choice = QMessageBox.question(None, f'Mesh: "{mesh.get_name()}"',
                                           f'Are you sure you want to delete mesh "{mesh_name}"?',
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if user_choice == QMessageBox.Yes:
            path_dir = self.preferences.get_user_files_dir_path()
            path_file = os.path.join(path_dir, f'{mesh_name}.obj')
            path_mtl_file = os.path.join(path_dir, f'{mesh_name}.mtl')
            path_preview_image = os.path.join(path_dir, f'{mesh_name}.jpg')
            from gt.utils.data_utils import delete_paths
            delete_paths([path_file, path_mtl_file, path_preview_image])
            self.model.import_user_mesh_library(source_dir=path_dir)
            selected_item = self.view.item_list.currentItem()
            if selected_item:
                self.view.item_list.takeItem(self.view.item_list.row(selected_item))
            sys.stdout.write(f'Mesh "{mesh_name}" was deleted.\n')

    def render_mesh_snapshot(self):
        """ Saves a snapshot to be used as preview image for a custom user mesh """
        mesh = self.get_selected_item_object()
        if not mesh:
            logger.warning(f'Unable to retrieve mesh object associated to selected item.')
            return
        mesh_name = mesh.get_name()
        path_dir = self.preferences.get_user_files_dir_path()
        from gt.utils.playblast_utils import render_viewport_snapshot
        path_file = render_viewport_snapshot(file_name=mesh_name, target_dir=path_dir)
        if path_file and os.path.exists(path_file):
            sys.stdout.write(f'Snapshot written to: "{path_file}".')
            self.on_item_selection_changed()
        else:
            logger.warning(f'Unable to save snapshot. Failed to create image file.')

    def get_custom_mesh_preview_image(self):
        """
        Gets the preview image for a custom mesh (in case it exists)
        Returns:
            str: Path to the preview image or the path to the missing file image.
        """
        mesh = self.get_selected_item_object()
        if not mesh:
            logger.warning(f'Unable to retrieve mesh object associated to selected item.')
            return
        mesh_name = mesh.get_name()
        path_dir = self.preferences.get_user_files_dir_path()
        preview_image = os.path.join(path_dir, f'{mesh_name}.jpg')
        if os.path.exists(preview_image):
            return preview_image
        else:
            return resource_library.Icon.library_missing_file


if __name__ == "__main__":
    print('Run it from "__init__.py".')
