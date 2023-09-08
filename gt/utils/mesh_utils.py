"""
Mesh (Geometry) Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.data_utils import DataDirConstants
from gt.utils.transform_utils import Transform
import maya.cmds as cmds
import logging
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# Constants
MESH_TYPE_DEFAULT = "mesh"
MESH_TYPE_SURFACE = "nurbsSurface"
MESH_TYPES = [MESH_TYPE_DEFAULT, MESH_TYPE_SURFACE]
MESH_FILE_EXTENSION = "obj"


def get_mesh_path(file_name):
    """
    Get the path to a mesh data file. This file should exist inside the utils/data/meshes folder.
    Args:
        file_name (str): Name of the file. It doesn't need to contain its extension as it will always be "obj"
    Returns:
        str or None: Path to the mesh file. None if not found.
    """
    if not isinstance(file_name, str):
        logger.debug(f'Unable to retrieve mesh file. Incorrect argument type: "{str(type(file_name))}".')
        return
    if not file_name.endswith(f'.{MESH_FILE_EXTENSION}'):
        file_name = f'{file_name}.{MESH_FILE_EXTENSION}'
    path_to_mesh = os.path.join(DataDirConstants.DIR_MESHES, file_name)
    return path_to_mesh


def convert_bif_to_mesh():
    """
    Converts Bifrost geometry to Maya geometry
    """
    errors = ''
    function_name = 'Convert Bif to Mesh'
    try:
        cmds.undoInfo(openChunk=True, chunkName=function_name)
        valid_selection = True

        selection = cmds.ls(selection=True)
        bif_objects = []
        bif_graph_objects = []

        if len(selection) < 1:
            valid_selection = False
            cmds.warning('You need to select at least one bif object.')

        if valid_selection:
            for obj in selection:
                shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
                for shape in shapes:
                    if cmds.objectType(shape) == 'bifShape':
                        bif_objects.append(shape)
                    if cmds.objectType(shape) == 'bifrostGraphShape':
                        bif_graph_objects.append(shape)

            for bif in bif_objects:
                parent = cmds.listRelatives(bif, parent=True) or []
                for par in parent:
                    source_mesh = cmds.listConnections(par + '.inputSurface', source=True, plugs=True) or []
                    for sm in source_mesh:
                        conversion_node = cmds.createNode("bifrostGeoToMaya")
                        cmds.connectAttr(sm, conversion_node + '.bifrostGeo')
                        mesh_node = cmds.createNode("mesh")
                        mesh_transform = cmds.listRelatives(mesh_node, parent=True) or []
                        cmds.connectAttr(conversion_node + '.mayaMesh[0]', mesh_node + '.inMesh')
                        cmds.rename(mesh_transform[0], 'bifToGeo1')
                        try:
                            cmds.hyperShade(assign='lambert1')
                        except Exception as e:
                            logger.debug(str(e))

            for bif in bif_graph_objects:
                bifrost_attributes = cmds.listAttr(bif, fp=True, inUse=True, read=True) or []
                for output in bifrost_attributes:
                    conversion_node = cmds.createNode("bifrostGeoToMaya")
                    cmds.connectAttr(bif + '.' + output, conversion_node + '.bifrostGeo')
                    mesh_node = cmds.createNode("mesh")
                    mesh_transform = cmds.listRelatives(mesh_node, parent=True) or []
                    cmds.connectAttr(conversion_node + '.mayaMesh[0]', mesh_node + '.inMesh')
                    bif_mesh = cmds.rename(mesh_transform[0], 'bifToGeo1')
                    try:
                        cmds.hyperShade(assign='lambert1')
                    except Exception as e:
                        logger.debug(str(e))

                    vtx = cmds.ls(bif_mesh + '.vtx[*]', fl=True) or []
                    if len(vtx) == 0:
                        try:
                            cmds.delete(bif_mesh)
                        except Exception as e:
                            logger.debug(str(e))
    except Exception as e:
        errors += str(e) + '\n'
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    if errors != '':
        cmds.warning('An error occurred when converting bif to mesh. Open the script editor for more information.')
        print('######## Errors: ########')
        print(errors)


def get_vertices(mesh):
    """
    Retrieves the vertices of a given mesh.
    This function returns a list of vertex names that belong to the specified mesh.

    Args:
        mesh (str): The name of the mesh for which vertices will be retrieved.

    Returns:
        list[str]: A list of vertex names as strings, representing the vertices
                   of the specified mesh.

    Raises:
        ValueError: If the provided 'mesh' name does not correspond to an existing mesh.

    Examples:
        mesh_name = 'my_mesh'
        vertices = get_vertices(mesh_name)
        print(vertices)
        ['my_mesh.vtx[0]', 'my_mesh.vtx[1]', 'my_mesh.vtx[2]', ...]
    """

    if not cmds.objExists(mesh):
        raise ValueError(f'The mesh "{mesh}" does not exist.')
    vertices = cmds.ls(f"{mesh}.vtx[*]", flatten=True)
    return vertices


def import_obj_file(file_path):
    """
    Import an OBJ file into the scene and return the imported items.

    Args:
        file_path (str): The path to the OBJ file to be imported.

    Returns:
        List[str]: A list of the names of the imported items.

    Example:
        imported_items = import_obj_file("/path/to/my_model.obj")
    """
    imported_items = []
    if not file_path or not os.path.exists(file_path):
        logger.warning(f'Unable to import "obj" file. Missing provided path: "{str(file_path)}".')
        return imported_items

    imported_items = cmds.file(file_path, i=True, type=MESH_FILE_EXTENSION, ignoreVersion=True, renameAll=True,
                               mergeNamespacesOnClash=True, namespace=":", returnNewNodes=True)
    return imported_items


class MeshFile:
    def __init__(self,
                 file_path,
                 metadata=None):
        """
        Initializes a MeshFile object
        Args:
            file_path (str): Path to an existing mesh file.
            metadata (dict, optional): A dictionary with any extra information used to further describe a mesh file.
        """
        self.file_path = file_path
        self.is_file_valid(verbose=True)
        self.metadata = None
        if metadata:
            self.set_metadata_dict(new_metadata=metadata)

    def is_file_valid(self, verbose=False):
        """
        Checks if the file path is of the correct data type and if it points to a valid file.
        Args:
            verbose (bool, optional): If active, it will log errors.
        Returns:
            bool: True if it's valid (can create a mesh), False if invalid.
        """
        if not isinstance(self.file_path, str) or not os.path.exists(self.file_path):
            if verbose:
                logger.warning(f'Invalid MeshFile object. File path must be a string to an existing file.')
            return False
        if not self.file_path.endswith(MESH_FILE_EXTENSION):
            if verbose:
                logger.warning(f'Invalid MeshFile object. '
                               f'File path must end with expected file extension: "{MESH_FILE_EXTENSION}".')
            return False
        return True

    def build(self):
        """
        Use the file path to import the object into the scene.
        Returns:
            list: Name of the imported elements.
        """
        if not self.is_file_valid(verbose=True):
            return []
        imported_elements = import_obj_file(self.file_path) or []
        return imported_elements

    def set_metadata_dict(self, new_metadata):
        """
        Sets the metadata property. The metadata is any extra value used to further describe the mesh file.
        Args:
            new_metadata (dict): A dictionary describing extra information about the mesh file
        """
        if not isinstance(new_metadata, dict):
            logger.warning(f'Unable to set mesh file metadata. '
                           f'Expected a dictionary, but got: "{str(type(new_metadata))}"')
            return
        self.metadata = new_metadata

    def add_to_metadata(self, key, value):
        """
        Adds a new item to the metadata dictionary. Initializes it in case it was not yet initialized.
        If an element with the same key already exists in the metadata dictionary, it will be overwritten
        Args:
            key (str): Key of the new metadata element
            value (Any): Value of the new metadata element
        """
        if not self.metadata:  # Initialize metadata in case it was never used.
            self.metadata = {}
        self.metadata[key] = value

    def get_metadata(self):
        """
        Gets the metadata property.
        Returns:
            dict: Metadata dictionary
        """
        return self.metadata

    def get_file_name_without_extension(self):
        """
        Get the name of the file without its extension.

        Returns:
            str: The name of the file without its extension.
        """
        if not self.is_file_valid(verbose=True):
            return ""
        base_name = os.path.basename(self.file_path)
        name_without_extension, _ = os.path.splitext(base_name)
        return name_without_extension


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    out = get_mesh_path("qr_code_package_github")
    import_obj_file(out)
