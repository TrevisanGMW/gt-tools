"""
Skin Utilities

Import Line:
    import gt.core.skin as core_skin
"""

import gt.core.feedback as core_fback
import gt.core.naming as core_naming
import gt.core.io as core_io
import maya.api.OpenMayaAnim as oma2
import maya.api.OpenMaya as om2
import maya.OpenMaya as om
import maya.cmds as cmds
import maya.mel as mel
import os.path
import logging
import ast

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SkinWeightsData:
    WEIGHTS = "weights"
    MESH = "mesh"
    SURFACE = "surface"
    LONG_INFLUENCES = "long_influences"


class SkinInfluencesData:
    INFLUENCES = "influences"
    MESH = "mesh"
    SURFACE = "surface"
    MAX_INFLUENCES = "max_influences"
    MAINTAIN_MAX_INFL = "maintain_max_influences"


class SkinBindingTypes:
    MESH = "mesh"
    NURBS_SURFACE = "nurbsSurface"
    NURBS_CURVE = "nurbsCurve"


def is_mesh_bound(obj):
    """
    Check if the specified object is bound to a skeleton.

    Args:
        obj (str): The name of the object to check.

    Returns:
        bool: True if the object is bound to a skeleton, False otherwise.
    """
    skin_clusters = cmds.ls(cmds.listHistory(obj), type="skinCluster")
    return len(skin_clusters) > 0


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

    if not cmds.objExists(obj):
        raise ValueError(f'Invalid object name: "{obj}" does not exist.')

    mfn_skin_list = get_mfn_skin_from_geometry(obj)

    if not mfn_skin_list[0]:
        logger.debug(f"No skin clusters attached to the object: '{obj}'")
        return None

    skin_cluster = mfn_skin_list[1]
    return skin_cluster


def get_influences(skin_cluster, long=True):
    """
    Retrieves the joint influences associated with the given skin cluster.
    This function returns a list of joint names that influence the specified skin cluster.
    Args:
        skin_cluster (str): The name of the skin cluster to get influences of.
        long (bool): If True, it returns the long names list, otherwise a short names list.
    Returns:
        list[str]: A list of joint long names as strings, representing the joints
                   that influence the given skin cluster.

    Examples:
        skin_cluster_name = 'skinCluster1'
        influences = get_influences(skin_cluster_name)
        print(influences)
        ['|joint1', '|joint1|joint2', '|joint1|joint2|joint3', ...]
        influences = get_influences(skin_cluster_name, long=False)
        print(influences)
        ['joint1', 'joint2', 'joint3', ...]
    """
    joints_short_names = cmds.skinCluster(skin_cluster, weightedInfluence=True, query=True)
    if not long:
        return joints_short_names
    else:
        return [cmds.ls(jnt, long=True)[0] for jnt in joints_short_names]


def get_influences_long_dict(skin_cluster):
    """
    Gets the dictionary with the influences short names as keys and long names as values,
    related to the given skin cluster.
    Args:
        skin_cluster (str): the skin cluster to query.
    Returns:
        dict: dictionary with the influences short names as keys and long names as values.

    Examples:
        skin_cluster_name = 'skinCluster1'
        influences_dict = get_influences_long_dict(skin_cluster_name)
        print(influences_dict)
        {'joint1':'|joint1', 'joint2':'|joint1|joint2', 'joint3':'|joint1|joint2|joint3', ...}
    """
    joints_short_names = cmds.skinCluster(skin_cluster, weightedInfluence=True, query=True)
    joints_long_names = [cmds.ls(jnt, long=True)[0] for jnt in joints_short_names]
    return dict(zip(joints_short_names, joints_long_names))


def get_available_long_influence(influence):
    """
    Gets the available influence in the scene searching with the given name (long and short both accepted).
    This function checks first if there is available the short name, otherwise search recursively
    an available parent using the long name.

    Args:
        influence (str): The influence name to resolve. Can be a short or long path.

    Returns:
        str: the available long name joint influence or an empty string.
    """
    if not influence:
        # Critical. Influence is missing and there is no valid available parent.
        return ""

    short_name = core_naming.get_short_name(influence)
    long_name_occurrences = cmds.ls(short_name, l=True)  # make sure it's long format
    if long_name_occurrences:
        if len(long_name_occurrences) == 1:
            # Valid. There is only one occurrence of the short name from the given long name.
            available_influence = long_name_occurrences[0]
        else:
            if cmds.objExists(influence):
                # Valid. The given influence exists.
                available_influence = cmds.ls(influence, l=True)  # make sure it's long format
            else:
                # Warning. There are multiple occurrences of the short name and the long name does not exist.
                logger.warning(f"Multiple influences with the same name: {str(long_name_occurrences)}")
                logger.warning(f"Influence from data: {influence}\nInfluence applied: {long_name_occurrences[0]}")
                available_influence = long_name_occurrences[0]
        if cmds.nodeType(available_influence) == "joint":
            return available_influence
        else:
            return ""
    else:
        # given long name object does not exist, let's search an available parent.
        infl_tokens = influence.split("|")
        parent_long = "|".join(infl_tokens[:-1])
        return get_available_long_influence(parent_long)


def get_available_influences_list(long_influences_list):
    """
    Gets the available influences in the scene from a given influences list in which there are
    the influences long names.
    Args:
        long_influences_list (list): A list of influence long names to check.

    Returns:
        list: A list of valid and updated long influence names available in the scene.
    """
    available_influences_list = []
    for long_name in long_influences_list:
        available_long_influence = get_available_long_influence(long_name)
        available_influences_list.append(available_long_influence)
        if available_long_influence != long_name:
            logger.warning(f"Original influence {long_name} has been updated to: {available_long_influence}")

    return available_influences_list


def get_available_influences_dict(long_influences_dict, skinned_object=None):
    """
    Gets the available influences in the scene from a given influences dictionary in which the keys are
    the influences short names and the values are the influences long names.
    Args:
        long_influences_dict (dict): dict in which the keys are the influences short names and values are the long ones.
        skinned_object (str): the skinned object of which the skin data are referring to.
                              This is just for debugging purposes, to inform the user.
    Returns:
        dict: dictionary of available influences in which the keys are the short names of the original
              influences past as input and the values are the available influences long names.
    """
    related_object_string = ""
    if skinned_object:
        related_object_string = f"Skin weights for '{skinned_object}': "

    available_influences_dict = {}
    for s_i, l_i in long_influences_dict.items():
        available_long_influence = get_available_long_influence(l_i)
        available_influences_dict[s_i] = available_long_influence
        if available_long_influence != l_i:
            logger.warning(
                f"{related_object_string}Original influence {l_i} has been updated to: {available_long_influence}"
            )

    return available_influences_dict


def update_skin_data_with_available_influences(skin_data, long_influences, skinned_object=None):
    """
    Updates a given skin_data dictionary comparing the available influences.
    For more details regarding the skin_data dictionary, please take a look at get_skin_weights func.

    Args:
        skin_data (dict): dictionary of skin weights (see get_skin_weights func).
        long_influences (dict): dictionary in which the key is the influence short name and the value is the
                                influence long name. None by default. Used to reassign missing influences.
        skinned_object (str): the skinned object of which the skin data are referring to.
                              This is just for debugging purposes, to inform the user.
    Returns:
        (dict, list): updated skin weights dictionary and a list of missing influences.
    """

    updated_skin_data = {}
    inf_missing = []

    available_influences = get_available_influences_dict(long_influences, skinned_object)
    if not available_influences:
        return updated_skin_data, inf_missing

    for vert, weights in skin_data.items():
        updated_influences_values = {}

        # Make sure that every stored weight is assigned to an available influence
        for data_infl, data_weight in weights.items():
            if data_infl not in available_influences.keys() and data_infl not in inf_missing:
                inf_missing.append(data_infl)
            elif not available_influences[data_infl] and data_infl not in inf_missing:
                inf_missing.append(data_infl)
            else:
                infl_short_name = available_influences[data_infl].split("|")[-1]
                if infl_short_name in updated_influences_values.keys():
                    # Perform a sum when there is already a value - crucial
                    updated_influences_values[infl_short_name] = (
                        updated_influences_values[infl_short_name] + data_weight
                    )
                else:
                    # Insert value
                    updated_influences_values[infl_short_name] = data_weight
        updated_skin_data[vert] = updated_influences_values

    return updated_skin_data, inf_missing


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
        logger.debug("skin_clusters: ", str(skin_cluster))
        logger.warning('Object "' + obj + "\" doesn't seem to be bound to any joints.")
        return []
    else:
        influences = get_influences(skin_cluster)
        joints = []
        for obj in influences:
            if cmds.objectType(obj) == "joint":
                joints.append(obj)
        return joints


def get_geos_from_skin_cluster(skin_cluster):
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
        affected_geometry_list = get_skin_cluster_geometry(skin_cluster_name)
        print(affected_geometry_list)
        # Output: ['pCube1', 'pSphere1', 'pCylinder1']
    """

    if not cmds.objExists(skin_cluster):
        raise ValueError(f'Invalid skin cluster name: "{skin_cluster}" does not exist.')

    affected_geometry_list = []
    mfn_skin_cluster = get_mfn_skin_from_skin_cluster(skin_cluster)
    input_plugs = mfn_skin_cluster.findPlug("input", False)
    input_nums = input_plugs.evaluateNumElements()

    for inp_num in range(input_nums):
        shape_obj = mfn_skin_cluster.inputShapeAtIndex(inp_num)
        shape_dag_path = om.MDagPath.getAPathTo(shape_obj)
        transform_dag_path = om.MDagPath(shape_dag_path)
        transform_dag_path.pop()
        affected_geometry_list.append(transform_dag_path.partialPathName())

    return affected_geometry_list


def get_skin_weights(skinned_mesh, remove_unused_inf=True):
    """
    Retrieve skin weights data from a given skinned mesh.
    This function returns skin weight information for each vertex analysing the skin cluster
    related to the supplied skinned mesh.
    The skin weights represent the influence of each bone (influence object) on the vertices of the mesh.

    Args:
        skinned_mesh (str): The name of the skinned mesh
        remove_unused_inf (bool): removes unused influences at the end of the process

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
        # Assuming a valid 'pCube1' exists in the scene.
        weights_data = get_skin_weights('pCube1')
        # Resulting output will be a dictionary containing skin weight data for each vertex in the cluster.
    """
    if not cmds.objExists(skinned_mesh):
        raise ValueError("Mesh '{}' does not exist.".format(skinned_mesh))

    vertices_num = cmds.polyEvaluate(skinned_mesh, v=True)

    # get om2 mfn_skin_cluster
    sel_list = om2.MSelectionList()
    sel_list.add(skinned_mesh)
    mesh_dag = sel_list.getDagPath(0)
    mfn_skin_cluster, skin_cluster_name = get_mfn_skin_from_geometry(skinned_mesh)

    if not skin_cluster_name:
        raise ValueError("Mesh '{}' does not have a skin cluster.".format(skinned_mesh))

    # get om2 mfn mesh components
    components_ids = [c for c in range(vertices_num)]
    mfn_single_component = om2.MFnSingleIndexedComponent()
    mesh_vert_component = mfn_single_component.create(om2.MFn.kMeshVertComponent)
    mfn_single_component.addElements(components_ids)

    # get weights from the skin cluster
    weights, inf_num = mfn_skin_cluster.getWeights(mesh_dag, mesh_vert_component)

    # get the plugs for the influences
    weight_plug = mfn_skin_cluster.findPlug("weights", False)
    list_plug = mfn_skin_cluster.findPlug("weightList", False).attribute()
    inf_dags = mfn_skin_cluster.influenceObjects()
    inf_num = len(inf_dags)
    inf_names = [inf_dag.partialPathName() for inf_dag in inf_dags]
    sparse_map = {mfn_skin_cluster.indexForInfluenceObject(inf_dag): i for i, inf_dag in enumerate(inf_dags)}

    # create the dictionary for the skin data
    skin_data = {}
    for comp_id, vertex_num in enumerate(components_ids):
        weight_plug.selectAncestorLogicalIndex(vertex_num, list_plug)
        valid_ids = weight_plug.getExistingArrayAttributeIndices()

        # bitwise operation to ignore false positives if any
        valid_ids = set(valid_ids) & sparse_map.keys()

        comp_weights = {}
        flat_index = int(comp_id) * inf_num

        _useful_influences = []
        for valid_id in valid_ids:
            inf_index = sparse_map[valid_id]
            comp_weights[inf_names[inf_index]] = weights[flat_index + inf_index]
            if inf_names[inf_index] not in _useful_influences:
                _useful_influences.append(inf_names[inf_index])

        _unused_influences = list(set(inf_names) - set(_useful_influences))
        if not remove_unused_inf and _unused_influences:
            for infl in _unused_influences:
                comp_weights[infl] = 0.0

        skin_data[vertex_num] = comp_weights

    return skin_data


def get_influences_from_skin_data(skin_data):
    """
    Gets the influences (joint names) inside the supplied skin data.

    Args:
        skin_data (dict): check get_skin_weights for the pattern to use

    Returns:
        skin_influences (list)
    """
    skin_influences = []
    for vert, weights in skin_data.items():
        vert_inf = list(weights.keys())
        [skin_influences.append(vi) for vi in vert_inf if vi not in skin_influences]
    if skin_influences:
        skin_influences.sort()

    return skin_influences


def set_skin_weights(skinned_mesh, skin_data, remove_unused_inf=True, long_influences=None):
    """
    Sets the skin weights from a skin_data dictionary.

    Args:
        skinned_mesh (str): name of the skinned mesh to apply weights to.
        skin_data (dict): skin data dictionary that follows the pattern described in get_skin_weights.
        remove_unused_inf (bool): removes unused influences at the end of the process
        long_influences (dict): dictionary in which the key is the influence short name and the value is the
                                influence long name. None by default. Used to reassign missing influences.

    Raises:
        ValueError: If the influences between the skin data and the skin cluster of the mesh are not matching.

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
    if not cmds.objExists(skinned_mesh):
        logger.error(f"Mesh '{skinned_mesh}' does not exist.")

    sel_list = om2.MSelectionList()
    sel_list.add(skinned_mesh)
    mesh_dag = sel_list.getDagPath(0)
    mfn_skin_cluster, skin_cluster_name = get_mfn_skin_from_geometry(skinned_mesh)

    if not skin_cluster_name:
        logger.error(f"Mesh '{skinned_mesh}' does not have a skin cluster.")

    # get influences dictionary
    inf_dags = mfn_skin_cluster.influenceObjects()
    inf_count = len(inf_dags)
    inf_dict = {i_dag.partialPathName(): i_index for i_index, i_dag in enumerate(inf_dags)}

    # get influences indices MIntArray
    inf_indices = om2.MIntArray(len(inf_dags), 0)
    for x in range(len(inf_dags)):
        inf_indices[x] = int(mfn_skin_cluster.indexForInfluenceObject(inf_dags[x]))

    skin_data = {int(key): value for key, value in skin_data.items()}  # Without this JSON converted dictionaries break

    # Handling potential missing influences searching the available ones in the scene following the hierarchy
    updated_skin_data = None
    inf_missing = None
    if long_influences:
        updated_skin_data, inf_missing = update_skin_data_with_available_influences(
            skin_data, long_influences, skinned_object=skinned_mesh
        )
    if updated_skin_data:
        skin_data = updated_skin_data
    else:
        # Updated influences are not available, check if there are missing influences.
        data_inf_list = get_influences_from_skin_data(skin_data)
        inf_missing = [inf for inf in data_inf_list if not cmds.objExists(inf)]
    # Abort if there are missing influences
    if inf_missing:
        logger.error(f"Missing influences:\n {str(inf_missing)}")
        return False

    skin_data_vertices = sorted(list(skin_data.keys()))
    skin_data_vertices = sorted(skin_data_vertices)

    # initialize MDoubleArray for the weights
    weights = om2.MDoubleArray(len(skin_data_vertices) * inf_count, 0)

    # get om2 mfn mesh components
    vertices_num = cmds.polyEvaluate(skinned_mesh, v=True)
    components_ids = [c for c in range(vertices_num)]
    mfn_single_component = om2.MFnSingleIndexedComponent()
    mesh_vert_component = mfn_single_component.create(om2.MFn.kMeshVertComponent)
    mfn_single_component.addElements(components_ids)

    for data_i, vertex_num in enumerate(skin_data_vertices):
        start_id = data_i * inf_count

        for inf_name, weight in skin_data[vertex_num].items():
            inf_id = inf_dict[inf_name]

            # populate correctly the weights double array for the skin cluster
            weights[start_id + inf_id] = weight

    # set skin weights
    normalize = False
    return_old_weights = False

    try:
        logger.debug(f"Setting skin weights for mesh: '{core_naming.get_short_name(skinned_mesh)}'")
        mfn_skin_cluster.setWeights(mesh_dag, mesh_vert_component, inf_indices, weights, normalize, return_old_weights)
        if remove_unused_inf:
            logger.debug(f"Removing unused influences for skin cluster: '{skin_cluster_name}'")
            remove_unused_influences(skin_cluster_name)
        return True

    except Exception as e:
        logger.error(f"Couldn't set the skin weights for the skin cluster '{skin_cluster_name}': {e}")
        return False


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
    skin_data = core_io.read_json_dict(path=import_file_path)
    set_skin_weights(target_object, skin_data)


def is_valid_for_binding(target_object, verbose=True, level=logging.WARNING):
    """
    Checks if a target object is valid for binding.
    Ensures all its shapes are visible and of a valid type for binding.

    Args:
        target_object (str): The name of the object to check.
        verbose (bool, optional): If True, it will log warnings when invalid.
        level (int, optional): Logging level used for the verbose mode.

    Returns:
        bool: True if the object is valid for binding, False otherwise.
    """
    # Check if the object exists
    if not cmds.objExists(target_object):
        warning_msg = f'Missing object is not valid for biding: "{target_object}"".'
        core_fback.log_when_true(input_logger=logger, input_string=warning_msg, do_log=verbose, level=level)
        return False

    # Get the shapes of the target object
    shapes = cmds.listRelatives(target_object, shapes=True, fullPath=True) or []
    if not shapes:
        warning_msg = f'Object is not valid for binding as it has no shapes: "{target_object}".'
        core_fback.log_when_true(input_logger=logger, input_string=warning_msg, do_log=verbose, level=level)
        return False

    # Check each shape's type and visibility
    valid_types = {SkinBindingTypes.MESH, SkinBindingTypes.NURBS_SURFACE, SkinBindingTypes.NURBS_CURVE}
    for shape in shapes:
        # Check shape type
        shape_type = cmds.objectType(shape)
        if shape_type not in valid_types:
            warning_msg = f'Shape "{shape}" of type "{shape_type}" is not valid for binding.'
            core_fback.log_when_true(input_logger=logger, input_string=warning_msg, do_log=verbose, level=level)
            return False

        # Invisible shapes error out in Maya when binding. (It can be hidden after binding)
        if not cmds.getAttr(f"{shape}.visibility"):
            warning_msg = f'Unable to bind invisible shape: "{shape}".'
            core_fback.log_when_true(input_logger=logger, input_string=warning_msg, do_log=verbose, level=level)
            return False

    return True  # If all checks pass, the object is valid for binding


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

    # Handle missing joints/influences attempting using the joint long name to find a suitable parent
    # This tries fallbacks, but it can still return empty strings if nothing is suitable within the scene.
    joints = get_available_influences_list(joints)
    for jnt in joints:
        if jnt:
            joints_found.append(jnt)
        else:
            joints_missing.append(jnt)

    # Check target objects existence
    for target_obj in objects:
        if cmds.objExists(target_obj):
            objects_found.append(target_obj)
        else:
            objects_missing.append(target_obj)

    # Warnings
    if objects_missing:
        logger.warning(f'Skin bound operation had missing objects: "{", ".join(objects_missing)}".')
    if joints_missing:
        logger.warning(f'Skin bound operation had missing joints: "{", ".join(joints_missing)}".')

    # Bind objects
    for target_obj in objects_found:
        if not is_valid_for_binding(target_obj):
            continue
        skin_node = (
            cmds.skinCluster(
                joints_found,
                target_obj,
                obeyMaxInfluences=True,
                bindMethod=bind_method,
                toSelectedBones=True,
                smoothWeights=smooth_weights,
                removeUnusedInfluence=False,
                maximumInfluences=maximum_influences,
            )
            or []
        )
        if skin_node:
            skin_nodes.extend(skin_node)

    if current_selection:
        try:
            cmds.select(current_selection)
        except Exception as e:
            logger.debug(f"Unable to recover previous selection. Issue: {str(e)}")
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
        shapes = cmds.listRelatives(obj, shapes=True, children=False, fullPath=True) or []
        if shapes:
            if cmds.objectType(shapes[0]) == "mesh" or cmds.objectType(shapes[0]) == "nurbsSurface":
                valid_nodes.append(obj)

    commands = []
    for transform in valid_nodes:
        message = '# Joint influences found in "' + transform + '":'
        message += "\nbound_list = "
        bound_joints = get_bound_joints(transform)

        if not bound_joints:
            cmds.warning('Unable to find skinCluster for "' + transform + '".')
            continue

        if include_bound_mesh:
            bound_joints.insert(0, transform)

        message += str(bound_joints)

        if include_existing_filter:
            message += "\nbound_list = [jnt for jnt in bound_list if cmds.objExists(jnt)]"

        message += "\ncmds.select(bound_list)"

        commands.append(message)

    _code = ""
    for cmd in commands:
        _code += cmd + "\n\n"
    if _code.endswith("\n\n"):  # Removes unnecessary spaces at the end
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
        cmds.warning("Nothing selected. Please select a bound mesh and try again.")
        return
    return get_python_influences_code(
        obj_list=sel, include_bound_mesh=include_bound_mesh, include_existing_filter=include_existing_filter
    )


def add_influences_to_set(obj_list, include_bound_mesh=True, set_suffix="influenceSet"):
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
            if cmds.objectType(shapes[0]) == "mesh" or cmds.objectType(shapes[0]) == "nurbsSurface":
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
        cmds.warning("Nothing selected. Please select a bound mesh and try again.")
        return
    return add_influences_to_set(sel)


def get_skin_weights_from_surface(surface, remove_unused_inf=True, encode_key_as_str=False):
    """
    Retrieve skin weights data from a given skinned NURBS surface.
    This function extracts skin weight information for each CV of a NURBS surface
    by analyzing the skin cluster related to the surface.

    Args:
        surface (str): The name of the NURBS surface.
        remove_unused_inf (bool): Removes unused influences at the end of the process.
        encode_key_as_str (bool, optional): If True, tuples are converted to strings.

    Raises:
        ValueError: If the provided surface is not a valid NURBS surface or lacks a skin cluster.

    Returns:
        dict: A dictionary containing skin weight data for each CV on the NURBS surface.
        The dictionary is structured as follows:

        {
            (u_index, v_index): {'joint1': 0.75, 'joint2': 0.25},
            ...
        }
        This data assigns the weights for each CV (by its (u, v) index) to the respective joints.

    Example:
        # Assuming a valid skinned NURBS surface 'loftedSurface1' exists in the scene.
        weights_data = get_skin_weights_from_surface('loftedSurface1')
        # Resulting output will be a dictionary containing skin weight data for each CV.
    """
    if not cmds.objExists(surface):
        raise ValueError(f"Surface '{surface}' does not exist.")

    # Check if the object is a NURBS surface
    shape_node = cmds.listRelatives(surface, shapes=True, fullPath=True)
    if not shape_node or cmds.nodeType(shape_node[0]) != "nurbsSurface":
        raise ValueError(f"Object '{surface}' is not a valid NURBS surface.")

    shape_node = shape_node[0]

    # Find the connected skin cluster
    skin_cluster = None
    history = cmds.listHistory(shape_node, pruneDagObjects=True) or []
    for node in history:
        if cmds.nodeType(node) == "skinCluster":
            skin_cluster = node
            break

    if not skin_cluster:
        raise ValueError(f"Surface '{surface}' does not have a skin cluster.")

    # Get the influence objects and their names
    inf_objects = cmds.skinCluster(skin_cluster, query=True, influence=True) or []
    inf_names = [cmds.ls(inf, shortNames=True)[0] for inf in inf_objects]

    # Get the number of CVs in U and V directions
    u_count = cmds.getAttr(f"{surface}.spansU") + cmds.getAttr(f"{surface}.degreeU")
    v_count = cmds.getAttr(f"{surface}.spansV") + cmds.getAttr(f"{surface}.degreeV")

    # Build the dictionary for skin weights
    skin_data = {}
    for u_index in range(u_count + 1):  # Include end CVs
        for v_index in range(v_count + 1):  # Include end CVs
            cv_name = f"{surface}.cv[{u_index}][{v_index}]"
            cv_weights = cmds.skinPercent(skin_cluster, cv_name, query=True, value=True)

            comp_weights = {inf_name: weight for inf_name, weight in zip(inf_names, cv_weights) if weight > 0}

            # Add unused influences if requested
            if not remove_unused_inf:
                for infl in set(inf_names) - set(comp_weights.keys()):
                    comp_weights[infl] = 0.0

            skin_data[(u_index, v_index)] = comp_weights

    if encode_key_as_str:  # Tuple becomes strings. e.g. "(1, 2)" - This is, so they are compatible with JSON.
        return {str(key): value for key, value in skin_data.items()}
    return skin_data


def set_skin_weights_on_surface(skinned_surface, skin_data, decode_str_keys=False, long_influences=None):
    """
    Apply skin weights to a NURBS surface using a provided skin weights dictionary.

    Args:
        skinned_surface (str): The name of the NURBS surface to apply skin weights to.
        skin_data (dict): A dictionary containing skin weight data.
            The structure is expected to be:
            {
                (u_index, v_index): {'joint1': 0.5, 'joint2': 0.5},
                ...
            }
        decode_str_keys (bool, optional): Automatically converts str keys to tuples.
                                          This is used to keep JSON compatibility.
                                          If keys are already tuples, nothing changes. Works with mixed cases.
        long_influences (dict): dictionary in which the key is the influence short name and the value is the
                        influence long name. None by default. Used to reassign missing influences.

    Raises:
        ValueError: If the provided surface is not a valid NURBS surface or lacks a skin cluster.
    """
    if not cmds.objExists(skinned_surface):
        raise ValueError(f"Surface '{skinned_surface}' does not exist.")

    # Handling potential missing influences searching the available ones in the scene following the hierarchy
    updated_skin_data = None
    inf_missing = None
    if long_influences:
        updated_skin_data, inf_missing = update_skin_data_with_available_influences(
            skin_data, long_influences, skinned_object=skinned_surface
        )
    if updated_skin_data:
        skin_data = updated_skin_data
    else:
        # Updated influences are not available, check if there are missing influences.
        data_inf_list = get_influences_from_skin_data(skin_data)
        inf_missing = [inf for inf in data_inf_list if not cmds.objExists(inf)]
    # Abort if there are missing influences
    if inf_missing:
        logger.error(f"Missing influences:\n {str(inf_missing)}")
        return False

    # Decode Skin Data
    if decode_str_keys:
        temp_skin_data = {}
        for key, value in skin_data.items():
            if isinstance(key, str):  # If the key is a string, attempt to convert it
                try:
                    parsed_key = ast.literal_eval(key)
                    if isinstance(parsed_key, tuple):  # Ensure it's a tuple
                        temp_skin_data[parsed_key] = value
                except (ValueError, SyntaxError) as e:
                    logger.debug(f"Failed to decode UV coordinates in the surface skin data. Issue: {e}")
        skin_data = temp_skin_data

    # Validate that the object is a NURBS surface
    shape_node = cmds.listRelatives(skinned_surface, shapes=True, fullPath=True)
    if not shape_node or cmds.nodeType(shape_node[0]) != "nurbsSurface":
        raise ValueError(f"Object '{skinned_surface}' is not a valid NURBS surface.")

    shape_node = shape_node[0]

    # Find the connected skin cluster
    skin_cluster = None
    history = cmds.listHistory(shape_node, pruneDagObjects=True) or []
    for node in history:
        if cmds.nodeType(node) == "skinCluster":
            skin_cluster = node
            break

    if not skin_cluster:
        raise ValueError(f"Surface '{skinned_surface}' does not have a skin cluster.")

    # Get the influences (joints) for the skin cluster
    inf_objects = cmds.skinCluster(skin_cluster, query=True, influence=True) or []
    inf_names = [cmds.ls(inf, shortNames=True)[0] for inf in inf_objects]

    # Apply the weights for each CV
    for (u_index, v_index), weights in skin_data.items():
        cv_name = f"{skinned_surface}.cv[{u_index}][{v_index}]"

        # Prepare a list of influence and weight pairs
        weight_list = []
        for joint, weight in weights.items():
            if joint in inf_names:
                weight_list.append((joint, weight))

        # Set the weights using skinPercent
        for joint, weight in weight_list:
            cmds.skinPercent(skin_cluster, cv_name, transformValue=[(joint, weight)])

    # Normalize weights after assignment
    cmds.skinCluster(skin_cluster, edit=True, forceNormalizeWeights=True)


#  TODO: Not tested yet --------------------------------------------------------------------------------------------
def export_influences_to_target_folder(obj_list, target_folder, verbose=False):
    """
    Export influence data (joints affecting skin clusters) of specified objects to JSON files in a target folder.

    Args:
        obj_list (list[str] or str): List of object names or a single object name whose influences will be exported.
        target_folder (str): Path to the folder where influence JSON files will be saved.
        verbose (bool, optional): If True, prints status messages during export. Defaults to False.

    Returns:
        list[str]: List of file paths to the exported JSON files.

    TODO:
        add existing checks
        extract maximum influences and skin cluster options
        extract target name
    """

    if isinstance(obj_list, str):  # If a string is provided, convert it to list
        obj_list = [obj_list]

    if not os.path.exists(target_folder) or not os.path.isdir(target_folder):
        logger.warning(f"Unable to export influences. Missing target folder: {str(target_folder)}")
        return

    exported_files = set()
    for obj in obj_list:
        file_name = f"influences_{obj}.json"
        file_path = os.path.join(target_folder, file_name)
        joints = get_influences(get_skin_cluster(obj))
        influences_dict = {"obj_name": obj, "influences": joints}
        json_file = core_io.write_json(path=file_path, data=influences_dict)
        if json_file:
            exported_files.add(json_file)
            core_fback.print_when_true(
                input_string=f'Influences for "{obj}" exported to "{json_file}".', do_print=verbose
            )
    return list(exported_files)


def import_influences_from_target_folder(source_folder, verbose=False):
    """
    Import influence data from JSON files in the given source folder and apply them to their respective objects.

    Args:
        source_folder (str): Path to the folder containing JSON influence files.
        verbose (bool, optional): If True, prints status messages during import. Defaults to False.

    Returns:
        None
    """
    if not os.path.exists(source_folder) or not os.path.isdir(source_folder):
        logger.warning(f"Unable to import influences. Missing source folder: {str(source_folder)}")
        return

    for source_file_name in os.listdir(source_folder):
        file_path = os.path.join(source_folder, source_file_name)
        influences_dict = core_io.read_json_dict(file_path)
        obj_name = influences_dict.get("obj_name")
        joints = influences_dict.get("influences")
        bind_skin(joints, [obj_name])
        core_fback.print_when_true(
            input_string=f'Influences for {obj_name} imported from "{source_file_name}".', do_print=verbose
        )


def export_weights_to_target_folder(obj_list, target_folder, verbose=False, file_format=".json"):
    """
    Export skin weight data for a list of objects to a target folder as JSON files.

    Args:
        obj_list (list or str): List of objects (or a single object as string) whose skin weights will be exported.
        target_folder (str): Path to the folder where weight files will be saved.
        verbose (bool, optional): If True, prints status messages during export. Defaults to False.
        file_format (str, optional): File extension/format to save as (default is ".json").

    Returns:
        list: List of exported file paths. Empty if no files were exported or on error.
    """
    if isinstance(obj_list, str):  # If a string is provided, convert it to list
        obj_list = [obj_list]

    if not os.path.exists(target_folder) or not os.path.isdir(target_folder):
        logger.warning(f"Unable to export skin weights. Missing target folder: {str(target_folder)}")
        return

    exported_files = set()
    for obj in obj_list:
        import gt.core.naming as core_naming

        file_name = f"weights_{core_naming.get_short_name(obj)}.{file_format}"
        file_path = os.path.join(target_folder, file_name)
        skin_weights_data = get_skin_weights(obj)
        json_file = core_io.write_json(path=file_path, data=skin_weights_data)
        if json_file:
            exported_files.add(json_file)
            core_fback.print_when_true(input_string=f'Weights for "{obj}" exported to "{json_file}".', do_print=verbose)
    return list(exported_files)


def import_weights_from_target_folder(obj_list, target_folder, remove_unused_inf=True):
    """
    Imports the skin weights from a target folder.

    Args:
        obj_list (list): list of skinned meshes
        target_folder (string): folder path with exported skin data files
        remove_unused_inf (bool): remove unused influences after the process

    Returns:

    """
    import gt.core.joint as core_joint
    import gt.core.scene as core_scene

    if not os.path.exists(target_folder) or not os.path.isdir(target_folder):
        logger.warning(f"Unable to export skin weights. Missing target folder: {str(target_folder)}")
        return

    data_file_prefix = "weights_"
    data_file_ext = ".json"
    available_meshes_in_data = []
    weights_data = {}

    for weights_file_name in os.listdir(target_folder):
        if weights_file_name.startswith(data_file_prefix) and weights_file_name.endswith(data_file_ext):
            file_path = os.path.join(target_folder, weights_file_name)
            json_weights_dict = core_io.read_json_dict(file_path)

            # fix json string dictionary keys back to int
            weights_dict = {}
            for k, v in json_weights_dict.items():
                weights_dict[int(k)] = v

            data_mesh_name = weights_file_name.replace(data_file_prefix, "").replace(data_file_ext, "")
            available_meshes_in_data.append(data_mesh_name)
            weights_data[data_mesh_name] = weights_dict

    for obj in obj_list:
        if not cmds.objExists(obj):
            logger.warning(f"Skipped set weights for supplied mesh {obj}")
            continue

        skin_cluster_name = mel.eval('findRelatedSkinCluster "{}"'.format(obj))
        if not skin_cluster_name:
            logger.warning(f"Skipped set weights for supplied mesh {obj}. The SkinCluster is missing.")
            continue

        # set skin weights
        if obj in available_meshes_in_data:

            try:
                set_skin_weights(obj, weights_data[obj], remove_unused_inf=remove_unused_inf)

            except Exception as e:
                print(e)
                if "kInvalidParameter" not in str(e):
                    logger.error(e)
                    logger.warning(f"Skipped set weights for supplied mesh {obj}. Errors occur.")

                else:
                    # root joint from current influences
                    first_key = list(weights_data[obj].keys())[0]
                    first_joint = list(weights_data[obj][first_key].keys())[0]
                    root_joint = core_joint.get_root_from_joint(first_joint)
                    joint_hierarchy = core_scene.get_hierarchy(root_joint, maya_type=om.MFn.kJoint)
                    # re-bind
                    cmds.delete(obj, constructionHistory=True)
                    bind_skin(joint_hierarchy, [obj])
                    logger.info(f"Unused influences were removed. Successfully re-bound {obj} to the skeleton.")
                    set_skin_weights(obj, weights_data[obj], remove_unused_inf=remove_unused_inf)

        else:
            logger.warning(f"Skipped set weights for supplied mesh {obj}. Data not found.")


def get_mfn_skin_from_skin_cluster(skin_cluster):
    """
    Returns the MObject related to the supplied skinCluster node.

    Args:
        skin_cluster (str): Name of the skin cluster node.

    Returns:
        MFnSkinCluster: Maya function set for the skin cluster.
    """
    if not cmds.objExists(skin_cluster):
        raise ValueError(f'Skin cluster "{skin_cluster}" does not exist.')

    sel_list = om2.MSelectionList()
    sel_list.add(skin_cluster)
    skin_cluster_dep = sel_list.getDependNode(0)
    mfn_skin_cluster = oma2.MFnSkinCluster(skin_cluster_dep)

    return mfn_skin_cluster


def get_mfn_skin_from_geometry(geometry):
    """
    Returns the skin cluster MObject related to the supplied geometry.

    Args:
        geometry (str): Name of the geometry (polygon mesh or NURBS surface).

    Returns:
         tuple: A tuple containing:
            - skinCluster (MFnSkinCluster): Maya skin cluster function set
            - skinName (str): Name of the skin cluster node
    """
    # Ensure we are dealing with the shape node
    shapes = cmds.listRelatives(geometry, shapes=True, fullPath=True)
    if not shapes:
        raise ValueError(f'No shape node found for the given object: "{geometry}".')

    shape_node = shapes[0]

    # Attempt to find the related skin cluster
    skin_cluster_name = mel.eval(f'findRelatedSkinCluster "{shape_node}"')
    if not skin_cluster_name:
        return None, None

    mfn_skin_cluster = get_mfn_skin_from_skin_cluster(skin_cluster_name)
    return mfn_skin_cluster, skin_cluster_name


def get_unused_influences(skin_cluster):
    """
    Gets the unused influences as dagPaths.

    Args:
        skin_cluster: skin cluster node name

    Returns:
        unused_influences (dagPaths)
    """
    unused_influences = []
    mfn_skin_cluster = get_mfn_skin_from_skin_cluster(skin_cluster)
    influences = mfn_skin_cluster.influenceObjects()

    for inf in influences:
        comp_path, weights = mfn_skin_cluster.getPointsAffectedByInfluence(inf)

        if comp_path.length() == 0:
            unused_influences.append(inf)

    return unused_influences


def remove_unused_influences(skin_cluster):
    """
    Removes unused influences in a skin cluster.

    Args:
        skin_cluster: skin cluster node name
    """
    unused_influences = get_unused_influences(skin_cluster)
    if unused_influences:
        for inf in unused_influences:
            cmds.skinCluster(skin_cluster, edit=True, removeInfluence=inf.fullPathName())


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)

    import json

    # Meshes
    test_mesh = "cylinder"
    skin_data_test = get_skin_weights(skinned_mesh=test_mesh)
    print(skin_data_test)
    test_export_json = json.dumps(skin_data_test)
    test_import_json = json.loads(test_export_json)
    print(test_import_json)
    set_skin_weights(skinned_mesh=test_mesh, skin_data=test_import_json)

    # Surfaces
    test_sur = "loftedSurface"
    skin_data_test_sur = get_skin_weights_from_surface(test_sur)
    set_skin_weights_on_surface(skinned_surface=test_sur, skin_data=skin_data_test_sur)
