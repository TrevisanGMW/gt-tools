"""
Skin Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.data_utils import write_json, read_json_dict
from gt.utils.feedback_utils import print_when_true
from gt.utils.string_utils import extract_digits
from gt.utils.geometry_utils import get_vertices
import maya.cmds as cmds
import os.path
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_skin_cluster(obj):
    """
    Retrieves the skin cluster associated with the given object.

    This function looks for a skin cluster connected to the provided object and returns
    the name of the skin cluster if found.

    Args:
        obj (str): The name of the Maya object, usually a mesh.

    Returns:
        str or None: The name of the skin cluster associated with the given mesh,
                     or None if no skin cluster is found.

    Examples:
        skin_cluster_name = get_skin_cluster(mesh_name)
        print(skin_cluster_name)
    """
    mesh_history = cmds.listHistory(obj, pruneDagObjects=True)
    skin_clusters = cmds.ls(mesh_history, type="skinCluster") or []
    if not skin_clusters:
        logger.debug(f"No skin clusters attached to the object: '{obj}'")
        return None
    skin_cluster = skin_clusters[0]
    return skin_cluster


def get_influences(skin_cluster):
    """
    Retrieves the joint influences associated with the given skin cluster.
    This function returns a list of joint names that influence the specified skin cluster.
    Args:
        skin_cluster (str): The name of the skin cluster to get influences of.

    Returns:
        list[str]: A list of joint names as strings, representing the joints
                   that influence the given skin cluster.

    Examples:
        skin_cluster_name = 'skinCluster1'
        influences = get_influences(skin_cluster_name)
        print(influences)
        ['joint1', 'joint2', 'joint3', ...]
    """
    joints = cmds.skinCluster(skin_cluster, weightedInfluence=True, query=True)
    return joints


def get_bound_joints(obj):
    """
    Gets a list of joints bound to the skin cluster of the object
    Args:
        obj: Name of the object to extract joints from (must contain a skinCluster node)

    Returns:
        list: List of joints bound to this object
    """
    if not cmds.objExists(obj):
        logger.warning(f'Object "{obj}" was not found.')
        return []

    skin_cluster = get_skin_cluster(obj)
    if not skin_cluster:
        logger.debug('skin_clusters: ', str(skin_cluster))
        logger.warning('Object "' + obj + "\" doesn't seem to be bound to any joints.")
        return []
    else:
        influences = get_influences(skin_cluster)
        joints = []
        for obj in influences:
            if cmds.objectType(obj) == 'joint':
                joints.append(obj)
        return joints


def get_skin_cluster_from_geometry(skin_cluster):
    """
    Retrieve the connected geometry from the given skin cluster.

    This function takes the name of a skin cluster as input and returns a list of connected
    geometry affected by the skin cluster.

    Args:
        skin_cluster (str): The name of the skin cluster to query.

    Returns:
        list: A list of strings containing the names of connected geometries affected by the skin cluster.

    Raises:
        ValueError: If the provided skin cluster name does not exist in the scene.

    Example:
        # Get the skin cluster name
        skin_cluster_name = "skinCluster1"
        # Retrieve connected geometry
        affected_geometry = get_skin_cluster_geometry(skin_cluster_name)
        print(affected_geometry)
        # Output: ['pCube1', 'pSphere1', 'pCylinder1']
    """
    # Check if the given name is a valid skin cluster
    if not cmds.objExists(skin_cluster):
        raise ValueError(f'Invalid skin cluster name: "{skin_cluster}" does not exist.')
    # Find the connected geometry to the skin cluster
    affected_geometry = set()
    skin_cluster_info = cmds.listConnections(skin_cluster + ".outputGeometry", source=False, destination=True)
    if skin_cluster_info:
        for obj in skin_cluster_info:
            affected_geometry.add(obj)
    return list(affected_geometry)


def get_skin_weights(skin_cluster):
    """
    Retrieve skin weights data for a given skin cluster.
    This function returns skin weight information for each vertex in a specified skin cluster.
    The skin weights represent the influence of each bone (influence object) on the vertices of the geometry
    associated with the skin cluster.

    Args:
        skin_cluster (str): The name of the skin cluster to query.

    Raises:
        ValueError: If the provided skin_cluster does not exist in the scene.

    Returns:
        dict: A dictionary containing skin weight data for each vertex in the skin cluster. The dictionary is
        structured as follows:

        {
            0: {'joint1': 0.75, 'joint2': 0.25},
            1: {'joint2': 1.0},
            2: {'joint3': 0.5, 'joint1': 0.5},
            ...
        }
        This data assigns the weights for each vertex (index 0, 1, 2, ...) to the respective joints.

    Example:
        # Assuming a valid 'skinCluster1' exists in the scene.
        weights_data = get_skin_weights('skinCluster1')
        # Resulting output will be a dictionary containing skin weight data for each vertex in the cluster.
    """
    if not cmds.objExists(skin_cluster):
        raise ValueError("Skin cluster '{}' does not exist.".format(skin_cluster))

    skin_data = {}
    influences = get_influences(skin_cluster)
    obj_name = get_skin_cluster_from_geometry(skin_cluster)
    vertices = get_vertices(obj_name[0])

    for vertex in vertices:
        vert_id_split = vertex.split(".")
        vert_id = extract_digits(vert_id_split[-1])  # get only vertex id
        skin_data[vert_id] = {}
        vert_influences = cmds.skinPercent(skin_cluster, vertex, query=True, transform=None, ignoreBelow=0.00000001)

        for joint in vert_influences:
            weight_val = cmds.skinPercent(skin_cluster, vertex, transform=joint, query=True)
            skin_data[vert_id][joint] = weight_val
    return skin_data


def set_skin_weights(skin_cluster, skin_data):
    """
    Import skin weights from a JSON file and apply them to a given skin cluster.

    Args:
        skin_cluster (str): Name of the skin cluster to apply weights to.
        skin_data (dict): File path of the JSON data containing skin weights.

    Raises:
        ValueError: If the specified skin cluster does not exist in the scene.

    Example:
        The skin_data should look like this:
        {
            0: {'joint1': 0.75, 'joint2': 0.25},
            1: {'joint2': 1.0},
            2: {'joint3': 0.5, 'joint1': 0.5},
            ...
        }
        This data assigns the weights for each vertex (index 0, 1, 2, ...) to the respective joints.
    """
    if not cmds.objExists(skin_cluster):
        raise ValueError(f'Skin cluster "{skin_cluster}" does not exist.')
    obj_name = get_skin_cluster_from_geometry(skin_cluster)[0]
    for vertex_id in skin_data:
        mesh_vertex = f"{obj_name}.vtx[{vertex_id}]"
        for joint in skin_data[vertex_id].keys():
            weight = skin_data[vertex_id][joint]
            joint_weight_pair = [cmds.ls(joint, shortNames=True)[0], weight]
            cmds.skinPercent(skin_cluster, mesh_vertex, transformValue=joint_weight_pair)


def import_skin_weights_from_json(target_object, import_file_path):
    """
    Imports skin weights from a JSON file and applies them to the specified target object's skin cluster.

    Args:
        target_object (str): The name or reference of the target object to apply the skin weights to.
        import_file_path (str): The file path of the JSON file containing the skin weight data.

    Raises:
        IOError: If the JSON file cannot be read or is not found.

    Note:
        This function assumes that the JSON file contains data matching the pattern found in  "get_skin_weights()".
    """
    skin_data = read_json_dict(path=import_file_path)
    skin_cluster = get_skin_cluster(target_object)
    set_skin_weights(skin_cluster=skin_cluster, skin_data=skin_data)


def bind_skin(joints, objects, bind_method=1, smooth_weights=0.5, maximum_influences=4):
    """
    Binds the specified joints to the given objects using the skinCluster command in Maya.

    Args:
        joints (list): A list of joint names to be used as influences in the skinCluster.
        objects (list, str): A list of object names (geometries) to bind the skin to.
                              If a string it becomes a list with a single element in it. e.g. [objects]
        bind_method (int, optional): The binding method used by the skinCluster command.
                                    Default is 1, which stands for 'Classic Linear'.
                                    Other options are available based on the Maya documentation.
        smooth_weights (float, optional): The smoothness level of the skin weights.
                                         It should be a value between 0.0 and 1.0.
                                         Default is 0.5.
        maximum_influences (int, optional): The maximum number of joint influences allowed per vertex.
                                           Default is 4.

    Returns:
        list: A list of skinCluster node names created during the binding process.

    Example:
        # Bind 'joints_list' to 'objects_list' with the default binding settings:
        result = bind_skin(joints_list, objects_list)

        # Bind 'joints_list' to 'objects_list' with custom binding options:
        result = bind_skin(joints_list, objects_list, bind_method=2, smooth_weights=0.8, maximum_influences=3)
    """
    if isinstance(objects, str):
        objects = [objects]
    current_selection = cmds.ls(selection=True) or []
    skin_nodes = []
    joints_found = []
    joints_missing = []
    objects_found = []
    objects_missing = []
    # Determine Existing Objects
    for jnt in joints:
        if cmds.objExists(jnt):
            joints_found.append(jnt)
        else:
            joints_missing.append(jnt)
    for geo in objects:
        if cmds.objExists(geo):
            objects_found.append(geo)
        else:
            objects_missing.append(geo)
    if objects_missing:
        logger.warning(f'Skin bound operation had missing objects: "{", ".join(objects_missing)}".')
    if joints_missing:
        logger.warning(f'Skin bound operation had missing joints: "{", ".join(joints_missing)}".')
    # Bind objects
    for geo in objects_found:
        skin_node = cmds.skinCluster(joints_found, geo,
                                     obeyMaxInfluences=True,
                                     bindMethod=bind_method,
                                     toSelectedBones=True,
                                     smoothWeights=smooth_weights,
                                     removeUnusedInfluence=False,
                                     maximumInfluences=maximum_influences) or []
        if skin_node:
            skin_nodes.extend(skin_node)

    if current_selection:
        try:
            cmds.select(current_selection)
        except Exception as e:
            logger.debug(f'Unable to recover previous selection. Issue: {str(e)}')
    return skin_nodes


def get_python_influences_code(obj_list, include_bound_mesh=True, include_existing_filter=True):
    """
    Extracts the python code necessary to select influence joints. (bound joints)
    Args:
        obj_list (list, str): Items to extract influence from. If a string is provided it becomes a list with one item.
        include_bound_mesh (bool, optional): If active, it will include the bound mesh in the return list.
        include_existing_filter (bool, optional): If active, it will include a filter for existing items.
    Returns:
        str or None: Returns the code to select influence joints or None there was an issue.
    """
    if isinstance(obj_list, str):
        obj_list = [obj_list]
    valid_nodes = []
    for obj in obj_list:
        shapes = cmds.listRelatives(obj, shapes=True, children=False) or []
        if shapes:
            if cmds.objectType(shapes[0]) == 'mesh' or cmds.objectType(shapes[0]) == 'nurbsSurface':
                valid_nodes.append(obj)

    commands = []
    for transform in valid_nodes:
        message = '# Joint influences found in "' + transform + '":'
        message += '\nbound_list = '
        bound_joints = get_bound_joints(transform)

        if not bound_joints:
            cmds.warning('Unable to find skinCluster for "' + transform + '".')
            continue

        if include_bound_mesh:
            bound_joints.insert(0, transform)

        message += str(bound_joints)

        if include_existing_filter:
            message += '\nbound_list = [jnt for jnt in bound_list if cmds.objExists(jnt)]'

        message += '\ncmds.select(bound_list)'

        commands.append(message)

    _code = ''
    for cmd in commands:
        _code += cmd + '\n\n'
    if _code.endswith('\n\n'):  # Removes unnecessary spaces at the end
        _code = _code[:-2]
    return _code


def selected_get_python_influences_code(include_bound_mesh=True, include_existing_filter=True):
    """
    Uses selection when extracting influence joints python code.
    Args:
        include_bound_mesh (bool, optional): If active, it will include the bound mesh in the return list.
        include_existing_filter (bool, optional): If active, it will include a filter for existing items.
    Returns:
        str or None: Returns the code to select influence joints or None there was an issue.
    """
    sel = cmds.ls(selection=True) or []

    if len(sel) == 0:
        cmds.warning('Nothing selected. Please select a bound mesh and try again.')
        return
    return get_python_influences_code(obj_list=sel,
                                      include_bound_mesh=include_bound_mesh,
                                      include_existing_filter=include_existing_filter)


def add_influences_to_set(obj_list, include_bound_mesh=True, set_suffix='influenceSet'):
    """
    Create selection sets with the influence joints of the provided elements.
    Args:
        obj_list (list, str): Items to extract influence from. If a string is provided it becomes a list with one item.
        include_bound_mesh (bool, optional): If active, it will include the bound mesh in the set.
        set_suffix (str, optional): Added as a suffix to the created set.
    Returns:
        list: A list of created selection sets (sorted list)
    """
    selection_sets = set()
    if isinstance(obj_list, str):
        obj_list = [obj_list]
    valid_nodes = []
    for obj in obj_list:
        shapes = cmds.listRelatives(obj, shapes=True, children=False) or []
        if shapes:
            if cmds.objectType(shapes[0]) == 'mesh' or cmds.objectType(shapes[0]) == 'nurbsSurface':
                valid_nodes.append(obj)

    for transform in valid_nodes:
        bound_joints = get_bound_joints(transform)
        if include_bound_mesh:
            bound_joints.insert(0, transform)
        new_set = cmds.sets(name=f"{transform}_{set_suffix}", empty=True)
        for jnt in bound_joints:
            selection_sets.add(cmds.sets(jnt, add=new_set))
    return sorted(list(selection_sets))


def selected_add_influences_to_set():
    """
    Uses selection when extracting influence joints to a selection set.
    Returns:
        str or None: Returns the code to select influence joints or None there was an issue.
    """
    sel = cmds.ls(selection=True) or []

    if len(sel) == 0:
        cmds.warning('Nothing selected. Please select a bound mesh and try again.')
        return
    return add_influences_to_set(sel)


#  TODO: Not yet tested --------------------------------------------------------------------------------------------
def export_influences_to_target_folder(obj_list, target_folder, verbose=False):
    """
    WIP Function
        TODO:
            add existing checks
            extract maximum influences and skin cluster options
            extract target name
    """

    if isinstance(obj_list, str):  # If a string is provided, convert it to list
        obj_list = [obj_list]

    if not os.path.exists(target_folder) or not os.path.isdir(target_folder):
        logger.warning(f'Unable to export influences. Missing target folder: {str(target_folder)}')
        return

    exported_files = set()
    for obj in obj_list:
        file_name = f"influences_{obj}.json"
        file_path = os.path.join(target_folder, file_name)
        joints = get_influences(get_skin_cluster(obj))
        influences_dict = {"obj_name": obj, "influences": joints}
        json_file = write_json(path=file_path, data=influences_dict)
        if json_file:
            exported_files.add(json_file)
            print_when_true(input_string=f'Influences for "{obj}" exported to "{json_file}".', do_print=verbose)
    return list(exported_files)


def import_influences_from_target_folder(source_folder, verbose=False):
    """
    WIP
    TODO:
        Check if exists, add existing checks, check pattern before using it
    """

    if not os.path.exists(source_folder) or not os.path.isdir(source_folder):
        logger.warning(f'Unable to import influences. Missing source folder: {str(source_folder)}')
        return

    for source_file_name in os.listdir(source_folder):
        file_path = os.path.join(source_folder, source_file_name)
        influences_dict = read_json_dict(file_path)
        obj_name = influences_dict.get("obj_name")
        joints = influences_dict.get("influences")
        bind_skin(joints, [obj_name])
        print_when_true(input_string=f'Influences for {obj_name} imported from "{source_file_name}".', do_print=verbose)


def export_weights_to_target_folder(obj_list, target_folder, verbose=False):
    """
    WIP
    TODO:
        Check if exists, add existing checks, check pattern before using it Add suffix?
    """
    if isinstance(obj_list, str):  # If a string is provided, convert it to list
        obj_list = [obj_list]

    if not os.path.exists(target_folder) or not os.path.isdir(target_folder):
        logger.warning(f'Unable to export skin weights. Missing target folder: {str(target_folder)}')
        return

    exported_files = set()
    for obj in obj_list:
        file_name = f"weights_{obj}.json"
        file_path = os.path.join(target_folder, file_name)
        skin_cluster = get_skin_cluster(obj=obj)
        skin_weights_data = get_skin_weights(skin_cluster=skin_cluster)
        json_file = write_json(path=file_path, data=skin_weights_data)
        if json_file:
            exported_files.add(json_file)
            print_when_true(input_string=f'Weights for "{obj}" exported to "{json_file}".', do_print=verbose)
    return list(exported_files)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
