"""
Skin Utilities
github.com/TrevisanGMW/gt-tools
"""
from geometry_utils import get_vertices
from data_utils import write_json
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

    Parameters:
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
    Parameters:
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
    Parameters:
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


def get_skin_cluster_geometry(skin_cluster):
    """
    Retrieve the connected geometry to the given skin cluster.

    This function takes the name of a skin cluster as input and returns a list of connected
    geometry affected by the skin cluster.

    Parameters:
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

    Parameters:
        skin_cluster (str): The name of the skin cluster to query.

    Raises:
        ValueError: If the provided skin_cluster does not exist in the scene.

    Returns:
        dict: A dictionary containing skin weight data for each vertex in the skin cluster. The dictionary is
        structured as follows:

        {
            vertex_id_1: {
                influence_name_1: weight_value,
                influence_name_2: weight_value,
                ...
            },
            vertex_id_2: {
                influence_name_1: weight_value,
                influence_name_2: weight_value,
                ...
            },
            ...
        }

        Each vertex_id is a unique identifier for a vertex in the geometry, and each influence_name represents
        the name of a bone or influence object associated with the skin cluster. The weight_value is a float
        representing the weight of the influence on the vertex.

    Example:
        # Assuming a valid 'skinCluster1' exists in the scene.
        weights_data = get_skin_weights('skinCluster1')
        # Resulting output will be a dictionary containing skin weight data for each vertex in the cluster.
    """
    if not cmds.objExists(skin_cluster):
        raise ValueError("Skin cluster '{}' does not exist.".format(skin_cluster))

    skin_data = {}
    influences = get_influences(skin_cluster)
    obj_name = get_skin_cluster_geometry(skin_cluster)
    vertices = get_vertices(obj_name[0])

    for vertex in vertices:
        skin_data[vertex] = {}
        for influence in influences:
            weight = cmds.skinPercent(skin_cluster, vertex,
                                      transform=influence, query=True,
                                      ignoreBelow=0.00000001)
            skin_data[vertex][influence] = weight
    return skin_data


def export_skin_weights_to_json(output_file_path, skin_weight_data):
    """
    Exports skin weight data to a JSON file.

    This function takes the provided skin_weight_data, which is a dictionary containing
    skin weight information for a model, and exports it to a JSON file specified
    by the output_file_path.

    Parameters:
        output_file_path (str): The file path where the JSON data will be written.
        skin_weight_data (dict): A dictionary containing skin weight data for a model.

    Returns:
        str: Path if successful, None if it failed
    """
    return write_json(path=output_file_path, data=skin_weight_data)


def bind_skin(joints, objects, bind_method=1, smooth_weights=0.5, maximum_influences=4):
    """
    Binds the specified joints to the given objects using the skinCluster command in Maya.

    Parameters:
        joints (list): A list of joint names to be used as influences in the skinCluster.
        objects (list): A list of object names (geometries) to bind the skin to.
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
                                     bindMethod=bind_method,
                                     toSelectedBones=True,
                                     smoothWeights=smooth_weights,
                                     maximumInfluences=maximum_influences) or []
        if skin_node:
            skin_nodes.extend(skin_node)

    if current_selection:
        try:
            cmds.select(current_selection)
        except Exception as e:
            logger.debug(f'Unable to recover previous selection. Issue: {str(e)}')
    return skin_nodes


def export_weights_to_target_folder(objects, target_folder):
    """
    Export skin weights for multiple objects to JSON files and save them in the target folder.

    This function takes a list of object names and exports their skin weight data to individual
    JSON files in the target folder. The function first checks if the target folder exists and
    is a directory. If the folder does not exist or is not a directory, it logs a warning and
    returns without performing any exports.

    Parameters:
        objects (list[str]): A list of object names for which skin weights will be exported.
        target_folder (str): The path to the folder where the JSON files will be saved.

    Returns:
        list: A list of the exported files

    Example:
        objects_list = ['mesh1', 'mesh2', 'mesh3']
        target_folder_path = '/path/to/target/folder/'
        export_weights_to_target_folder(objects_list, target_folder_path)
    """
    if not os.path.exists(target_folder) or not os.path.isdir(target_folder):
        logger.warning(f'Unable to export skin weights. Missing target folder: {str(target_folder)}')
        return

    exported_files = set()
    for obj in objects:
        file_name = obj + ".json"
        file_path = os.path.join(target_folder, file_name)
        skin_cluster = get_skin_cluster(obj=obj)
        skin_weights_data = get_skin_weights(skin_cluster=skin_cluster)
        file = export_skin_weights_to_json(output_file_path=file_path, skin_weight_data=skin_weights_data)
        if file:
            exported_files.add(file)
    return list(exported_files)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    selection = cmds.ls(selection=True) or []
    temp_joints = ['joint1', 'joint2', 'joint3']
    temp_geometries = ['pCylinder1', 'pCylinder2', 'pCylinder3']
    out = get_bound_joints('pCylinder1')
    out = get_skin_weights(get_skin_cluster('pCylinder1'))
    export_weights_to_target_folder(temp_geometries, r'C:\Users\guilherme.trevisan\Desktop\temp')
    pprint(out)
