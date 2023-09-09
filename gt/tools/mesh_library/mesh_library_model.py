"""
Mesh Library Model
"""
from gt.utils.mesh_utils import Meshes, MeshFile, ParametricMesh
from gt.ui import resource_library
import logging
import os


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MeshLibraryModel:
    def __init__(self):
        """
        Initialize the MeshLibraryModel object.
        """
        self.base_meshes = {}
        self.user_meshes = {}  # User-defined meshes
        self.param_meshes = {}
        self.import_package_library()

    def is_conflicting_name(self, name):
        """
        Checks if item name already exists in any of the lists
        Args:
            name (str): Name of the item to check
        Returns:
            bool: True if it's conflict (already in the list), False if not.
        """
        current_names = self.get_all_mesh_names()
        if name in current_names:
            return True
        return False

    def validate_item(self, item):
        """
        Validates object to make sure it's valid
        Args:
            item (MeshFile, ParametricMesh, any): A MeshFile, ParametricMesh or any element to be validated
        Returns:
            bool: True if valid (can be built, has expected attributes, etc...), False if not.
        """
        if not item:
            logger.debug(f'Invalid Mesh detected. "None" or empty element')
            return False
        if not item.is_valid():
            logger.debug(f'Invalid Mesh. Missing required elements for a mesh: {item}')
            return False
        if self.is_conflicting_name(item.get_name()):
            logger.debug(f'Invalid Name. This mesh name is already in the list. No duplicates allowed.')
            return False
        return True

    def add_base_mesh(self, mesh):
        """
        Add a mesh file to the base list.
        Args:
            mesh (MeshFile): The mesh file to be added.
        """
        if not self.validate_item(mesh):
            logger.debug(f'Unable to add MeshFile to package meshes. Mesh failed validation.')
            return
        self.base_meshes[mesh.get_name()] = mesh

    def add_user_mesh(self, user_mesh):
        """
        Add a mesh to the user meshes list.
        Args:
            user_mesh (MeshFile): The mesh file to be added.
        """
        if not self.validate_item(user_mesh):
            logger.debug(f'Unable to add MeshFile to user-defined meshes. MeshFile failed validation.')
            return
        self.base_meshes[user_mesh.get_name()] = user_mesh

    def add_param_mesh(self, param_mesh):
        """
        Add a ParametricMesh to the parametric meshes list.
        Args:
            param_mesh (ParametricMesh): The parametric mesh to be added
        """
        if not self.validate_item(param_mesh):
            logger.debug(f'Unable to add ParametricMesh to mesh list. ParametricMesh failed validation.')
            return
        self.base_meshes[param_mesh.get_name()] = param_mesh

    def get_base_meshes(self):
        """
        Get all meshes
        Returns:
            list: A list containing all the meshes in the MeshLibraryModel.
        """
        return self.base_meshes

    def get_user_meshes(self):
        """
        Get all user-defined meshes
        Returns:
            list: A list containing all the user-defined meshes in the MeshLibraryModel.
        """
        return self.user_meshes

    def get_param_meshes(self):
        """
        Get all parametric meshes
        Returns:
            list: A list containing all the parametric meshes in the MeshLibraryModel.
        """
        return self.param_meshes

    def get_all_mesh_names(self):
        """
        Get the list of names from all meshes found in the model (package, user and parametric)
        Returns:
            list: A list containing all the items in the MeshLibraryModel.
        """
        base_names = list(self.base_meshes.keys())
        user_names = list(self.user_meshes.keys())
        param_names = list(self.param_meshes.keys())
        return base_names + user_names + param_names

    def import_package_library(self):
        """
        Imports all meshes found in "mesh_utils.Meshes" to the MeshLibraryModel base meshes list
        """
        attributes = vars(Meshes)
        keys = [attr for attr in attributes if not (attr.startswith('__') and attr.endswith('__'))]
        for mesh_key in keys:
            mesh_file = getattr(Meshes, mesh_key)
            self.add_base_mesh(mesh_file)

    def import_user_mesh_library(self, source_dir, reset_user_meshes=True):
        """
        Imports all user meshes found in the user-defined meshes directory to the MeshLibraryModel user meshes list
        Args:
            source_dir (str): Path to a folder with mesh files. ("obj" files)
            reset_user_meshes (bool, optional): If active, user mesh list will be first reset before importing.
        """
        if reset_user_meshes:
            self.user_meshes = []
        if not source_dir:
            logger.debug('Invalid user meshes directory')
            return
        if not os.path.exists(source_dir):
            logger.debug("User meshes directory is missing.")
            return
        for file in os.listdir(source_dir):
            if file.endswith(".obj"):
                try:
                    user_mesh = MeshFile(file_path=os.path.join(source_dir, file))
                    if user_mesh.is_valid():
                        self.add_user_mesh(user_mesh)
                except Exception as e:
                    logger.debug(f'Failed to read user-defined mesh. Issue: {e}')

    def build_mesh_from_name(self, mesh_name):
        """
        Builds a mesh based on the provided name. (Mesh name, not necessary file name)
        In this context, a mesh is considered anything found inside the base meshes, user meshes or parametric meshes.
        Args:
            mesh_name (str): Name of the element to build. Must exist in one of the mesh lists.
        Returns:
            str or None: Name of the built item.
        """
        crv = self.get_mesh_from_name(mesh_name)
        result = None
        if crv:
            result = crv.build()
        return result

    def get_all_meshes(self):
        """
        Get all package meshes, parametric meshes and user-defined meshes. (All elements stored in this model)
        Returns:
            dict: A list containing all the user-defined meshes in the MeshLibraryModel.
        """
        all_meshes = self.base_meshes.copy()
        all_meshes.update(self.user_meshes)
        all_meshes.update(self.param_meshes)
        return all_meshes

    def get_mesh_from_name(self, item_name):
        """
        Gets a mesh based on the provided name. (Mesh name, not file name)
        Args:
            item_name (str): Name of the mesh to build
        Returns:
            MeshFile, ParametricMesh or None: Item object with the requested name. None if not found.
        """
        all_meshes = self.get_all_meshes()
        for key, value in all_meshes.items():
            if key == item_name:
                return value

    def get_preview_image(self, object_name):
        """
        Gets the preview image path for the given mesh name.

        Args:
            object_name (str): Name of the mesh

        Returns:
            str: The path to the preview image, or the path to the default missing file icon if the image is not found.
        """
        mesh = self.get_mesh_from_name(object_name)
        preview_image = None
        if mesh and isinstance(mesh, MeshFile):
            preview_image = ""  # get_mesh_preview_image_path(object_name) # TODO create function @@
        if mesh and isinstance(mesh, ParametricMesh):
            preview_image = ""  # get_param_mesh_preview_image_path(object_name) # TODO create function @@
        if preview_image:
            return preview_image
        else:
            return resource_library.Icon.library_missing_file

    @staticmethod
    def build_mesh_with_custom_parameters(parameters, target_parametric_mesh):
        """
        Attempts to build a mesh using custom parameters
        Args:
            parameters (Callable, dict): Function used to get parameters or dictionary with parameters.
            target_parametric_mesh (ParametricMesh): ParametricMesh object to build
        """
        new_parameters = None
        if callable(parameters):
            new_parameters = parameters()
        elif isinstance(parameters, dict):
            new_parameters = parameters
        if new_parameters:
            try:
                target_parametric_mesh.set_parameters(new_parameters)
                target_parametric_mesh.build()
            except Exception as e:
                logger.warning(f'Unable to build mesh. Issue: "{e}".')
            finally:
                target_parametric_mesh.reset_parameters()

    def get_potential_user_mesh_from_selection(self):
        """
        Gets a user-defined mesh if it's unique and valid. (Uses user selection in Maya)
        Returns:
            MeshFile or None: The custom mesh file if the selection was valid. None if it failed.
        """
        import maya.cmds as cmds
        selection = cmds.ls(selection=True) or []
        if not selection:
            cmds.warning("Nothing selected. Select an existing mesh in your scene and try again.")
            return
        if len(selection) != 1:
            cmds.warning("Select only one object and try again.")
            return
        file_path = ""  # TODO TEMP @@@ - Function to export selected mesh as obj here
        mesh = MeshFile(file_path=file_path)
        if mesh.is_valid():
            mesh_name = mesh.get_name()
            if mesh_name in self.get_all_mesh_names():
                cmds.warning("Unable to add mesh. Mesh name already exists in the library. Rename it and try again.")
                return
            return mesh


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    model = MeshLibraryModel()
    print(model.get_all_meshes())
