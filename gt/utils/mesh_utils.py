"""
Mesh (Geometry) Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.data.param_meshes import scale_volume
from gt.utils import system_utils, iterable_utils
from gt.utils.data_utils import DataDirConstants
import maya.cmds as cmds
import logging
import ast
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


def get_mesh_preview_image_path(mesh_name, parametric=False):
    """
    Get the path to a mesh image file. This file should exist inside the utils/data/meshes folder.
    Args:
        mesh_name (str): Name of the Mesh (same as mesh file). It doesn't need to contain extension.
                         Function will automatically look for JPG or PNG files.
        parametric (bool, optional): If active, it will look in the parametric meshes folder instead of the regular dir.
    Returns:
        str or None: Path to the mesh preview image file. None if not found.
    """
    if not isinstance(mesh_name, str):
        logger.debug(f'Unable to retrieve mesh preview image. Incorrect argument type: "{str(type(mesh_name))}".')
        return

    _dir = DataDirConstants.DIR_MESHES
    if parametric:
        _dir = os.path.join(DataDirConstants.DIR_DATA, "param_meshes", "preview_images")
    for ext in ["jpg", "png"]:
        path_to_image = os.path.join(_dir, f'{mesh_name}.{ext}')
        if os.path.exists(path_to_image):
            return path_to_image


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
                 file_path=None,
                 metadata=None):
        """
        Initializes a MeshFile object
        Args:
            file_path (str): Path to an existing mesh file.
            metadata (dict, optional): A dictionary with any extra information used to further describe a mesh file.
        """
        self.file_path = file_path
        self.is_valid(verbose=True)
        self.metadata = None
        if metadata:
            self.set_metadata_dict(new_metadata=metadata)

    def is_valid(self, verbose=False):
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
        if not self.is_valid(verbose=True):
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
        if not self.is_valid(verbose=True):
            return ""
        base_name = os.path.basename(self.file_path)
        name_without_extension, _ = os.path.splitext(base_name)
        return name_without_extension

    def get_name(self):
        """
        Get the name of the file without its extension.

        Returns:
            str: The name of the file without its extension. (aka the name of the mesh)
        """
        return self.get_file_name_without_extension()


class ParametricMesh(MeshFile):
    def __init__(self, name=None, build_function=None):
        """
        Initializes a ParametricMesh (MeshFile) object. Essentially a function based mesh with extra logic and elements.
        Args:
            name (str, optional): Mesh  transform name.
                                  If not provided, it will attempt to extract it from the arguments of the build
                                  function. If it's also not found there, it will be None.
                                  If provided at the same time as the "build_function", name arg will take priority.
                                  Priority order: 1: name, 2: build_function keyword argument.
            build_function (callable): function used to build the mesh.
        """
        super().__init__()  # Call the parent class constructor
        self._original_parameters = {}
        self.parameters = {}
        self.name = None
        self.build_function = None
        self.set_build_function(build_function=build_function)
        self.last_callable_output = None
        if name:
            self.set_name(name=name)

    def _set_original_parameters(self, parameters):
        """
        Sets the original parametric mesh parameters (a copy to be compared for validation)
        Args:
            parameters (dict, str): A dictionary with the keyword arguments of the parametric mesh.
                                    It can also be a JSON formatted string.
        """
        if parameters and isinstance(parameters, dict):
            self._original_parameters = parameters

    def reset_parameters(self):
        """ Resets parameters to the original value """
        self.parameters = self._original_parameters

    def set_parameters(self, parameters):
        """
        Sets the parametric mesh parameters
        Args:
            parameters (dict, str): A dictionary with the keyword arguments of the parametric mesh.
                                        It can also be a JSON formatted string.
        """
        if parameters and isinstance(parameters, dict):
            self.parameters = parameters
        if parameters and isinstance(parameters, str):
            try:
                _parameters = ast.literal_eval(parameters)
                self.parameters = _parameters
            except Exception as e:
                logger.warning(f'Unable to set ParametricMesh parameters. Invalid dictionary. Issue: {str(e)}')

    def get_parameters(self):
        """
        Gets the parametric mesh parameters.
        Returns:
            dict: Parameters used to create the parametric mesh.
        """
        return self.parameters

    def get_docstrings(self, strip=True, strip_new_lines=True):
        """
        Returns the docstrings from the build function.
        Args:
            strip (bool, optional): If True, leading empty space will be removed from each line of the docstring.
            strip_new_lines (bool, optional): If True, it will remove new lines from start and end.
        Returns:
            str or None: Docstring of the build function.
                         None in case no function was set or function doesn't have a docstring
        """
        if not self.build_function:
            logger.debug(f'Build function was not yet set. Returning None as docstrings.')
            return
        return system_utils.get_docstring(func=self.build_function, strip=strip, strip_new_lines=strip_new_lines)

    def validate_parameters(self):
        """
        Validates parameters before building mesh
        If parameters have new keys or different value types, the validation fails.
        Returns:
            bool: True if valid, False if invalid
        """
        if not iterable_utils.compare_identical_dict_keys(self.parameters, self._original_parameters):
            logger.debug(f"Invalid parameters, new unrecognized keys were added.")
            return False
        if not iterable_utils.compare_identical_dict_values_types(self.parameters, self._original_parameters):
            logger.debug(f"Invalid parameters, values were assign new types.")
            return False
        return True

    def set_build_function(self, build_function):
        """
        Sets the build function for this parametric mesh
        Args:
            build_function (callable): A function used to build the mesh
        """
        if callable(build_function):
            self.build_function = build_function
            try:
                _args, _kwargs = system_utils.get_function_arguments(build_function, kwargs_as_dict=True)
                if _kwargs and len(_kwargs) > 0:
                    self.set_parameters(_kwargs)
                    self._set_original_parameters(_kwargs)
                    self.extract_name_from_parameters()
            except Exception as e:
                logger.debug(f'Unable to extract parameters from build function. Issue: {str(e)}')

    def build(self):
        """
        Use the provided callable function to generate/create a parametric mesh.
        Returns:
            str or Any: Name of the transform of the newly generated mesh. (Result of the callable function)
                       "None" if mesh is invalid (does not have a callable function)
        """
        if not self.is_valid():
            logger.warning("ParametricMesh object is missing a callable function.")
            return
        try:
            if self.validate_parameters():
                callable_result = self.build_function(**self.parameters)
            else:
                callable_result = self.build_function(**self._original_parameters)
                logger.warning(f'Invalid custom parameters. Original parameters were used instead. '
                               f'Original: {self._original_parameters}')
            self.last_callable_output = callable_result
            return callable_result
        except Exception as e:
            logger.warning(f'Unable to build mesh. Build function raised an error: {e}')

    def has_callable_function(self):
        """
        Checks if a callable function was provided or not
        Returns:
            bool: True if a function is present, False if not (None)
        """
        if self.build_function is not None:
            return True
        return False

    def is_valid(self, verbose=False):
        """
        Checks if the ParametricMesh object has enough data to create/generate a mesh.
        Args:
            verbose (bool, optional): If active, it will log issues.
        Returns:
            bool: True if it's valid (can create a mesh), False if invalid.
                  In this case it's valid if it has a callable function.
        """
        if self.has_callable_function:
            return True
        return False

    def get_last_callable_output(self):
        """
        Returns the last output received from the build call
        Returns:
            any: Anything received as the last output from the callable function. If it was never called, it is None.
        """
        return self.last_callable_output

    def get_name(self):
        """
        Gets parametric mesh name.
        Returns:
            str or None: String if a name was set or retrieved from arguments. None if missing.
        """
        return self.name

    def set_name(self, name):
        """
        Sets a new Mesh name (Parametric Mesh in this case).
        Used to also update the parameter "name" in case it exists.

        Args:
            name (str): New name to use on the parametric mesh. (Also used in the function parameter)
        """
        if not name or not isinstance(name, str):
            logger.debug(f'Unable to set name. Invalid input, expected string but got "{str(type(name))}".')
            return
        if name and isinstance(name, str) and "name" in self.get_parameters():
            self.parameters["name"] = name
        self.name = name

    def extract_name_from_parameters(self):
        """
        Checks to see if the keyword "name" exists in the parameters' dictionary.
        If it does, overwrite the parametric mesh name with it.
        """
        parameters = self.get_parameters()
        if "name" in parameters:
            param_name = parameters.get("name")
            if param_name:
                self.set_name(param_name)


class Meshes:
    def __init__(self):
        """
        A library of mesh objects.
        Use "build()" to create them in Maya.
        """
    qr_code_package_github = MeshFile(file_path=get_mesh_path("qr_code_package_github"))


class ParametricMeshes:
    def __init__(self):
        """
        A library of mesh objects.
        Use "build()" to create them in Maya.
        """

    scale_cube = ParametricMesh(build_function=scale_volume.create_scale_cube)
    scale_kitchen_cabinet = ParametricMesh(build_function=scale_volume.create_kitchen_cabinet)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    ParametricMeshes.scale_kitchen_cabinet.build()
