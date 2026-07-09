"""
RBF module.
It contains the radial basis function python implementation and the related functions to solve
specific approximations, such as the positional retarget of the vertices of a mesh comparing the
distances obtained from a source and a target set of positions (e.g. the mesh of the male and the
mesh of the female that share and must share the same topology, vertex id and total number).

Import Line:
    import gt.core.rbf as core_rbf
"""

import scipy.spatial.distance as sci_distance
import gt.core.hierarchy as core_hrchy
import maya.OpenMaya as om
import maya.cmds as cmds
import logging
import numpy

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def rbf_retarget(subject_array, source_array, target_array=None, weights_array=None):
    """
    Retargets a given pre-defined subject array using the radial basis function to calculate the approximated
    delta between two input arrays of matching sizes (source and target).

    Args:
        subject_array (list of point): subject point array that will be retargeted.
        source_array (list of point): source point array.
        target_array (list of point, optional): target point array. None by default.
        weights_array (list of point deltas, optional): pre-calculated distances between a source and a target.

    Returns:
        retarget_array (list of point): retargeted subject point array
    """

    if not weights_array and not target_array:
        logger.error(
            "You need to supply a target_array or a pre-calculated weights_array. You cannot leave both empty."
        )
        return

    source_numpy_array = numpy.array(source_array)
    subject_numpy_array = numpy.array(subject_array)

    if target_array:
        target_numpy_array = numpy.array(target_array)

        # Compute distance between each pair of the two collections of inputs for the original vertices.
        # Give matrix size m (number of vertices) x n (number of vertices).
        source_distance_matrix = sci_distance.cdist(source_numpy_array, source_numpy_array)

        # Get the weights by solving the distances against the target control points
        # Give matrix size m (number of vertices) x n (dimensions - x, y, z position)
        weights_matrix = numpy.linalg.solve(source_distance_matrix, target_numpy_array)

    else:
        weights_matrix = numpy.array(weights_array)

    # Get the distance between the subject points and the source points
    # Give matrix size m (number of vertices in subject) x n (number of vertices in source)
    distance_subject = sci_distance.cdist(subject_numpy_array, source_numpy_array)

    # Multiply the distance by the weights, number of rows in first matrix must be equal to the number
    # of columns in second, returning matrix shape of column from first matrix * row from second matrix
    retarget_array = numpy.asarray(numpy.dot(distance_subject, weights_matrix))

    return retarget_array


def get_source_and_weights_arrays(source_mesh, target_mesh):
    """
    Calculates and returns the source matrix and weights matrix in form of python arrays.
    Those can be used later to run the RBF retarget.
    Supplied source_mesh and target_mesh must share the same topology and vertex count.

    Args:
        source_mesh (str): source mesh for the rbf comparison
        target_mesh (str): target mesh for the rbf comparison

    Returns:
        source_array, weights_array
    """
    source_mpoint_array = get_vertex_positions(source_mesh)
    source_array = convert_marray_to_pyarray(source_mpoint_array)
    source_numpy_array = numpy.array(source_array)
    target_mpoint_array = get_vertex_positions(target_mesh)
    target_array = convert_marray_to_pyarray(target_mpoint_array)
    target_numpy_array = numpy.array(target_array)

    # Compute distance between each pair of the two collections of inputs for the original vertices.
    # Give matrix size m (number of vertices) x n (number of vertices).
    source_distance_matrix = sci_distance.cdist(source_numpy_array, source_numpy_array)

    # Get the weights by solving the distances against the target control points
    # Give matrix size m (number of vertices) x n (dimensions - x, y, z position)
    weights_matrix = numpy.linalg.solve(source_distance_matrix, target_numpy_array)
    weights_array = weights_matrix.tolist()

    return source_array, weights_array


def retarget_mesh(
    subject_mesh,
    source_mesh=None,
    target_mesh=None,
    source_array=None,
    weights_array=None,
):
    """
    Retargets a mesh based on a common base mesh type.
    If the source_mesh and target_mesh are provided, the function will calculate first the
    weights through the RBF function, otherwise you can provide a pre-calculated source_array and weights_array.

    Args:
        source_mesh (str): source mesh for the rbf comparison
        target_mesh (str): target mesh for the rbf comparison
        subject_mesh (str): mesh to retarget
        source_array (list of point): source point array. None by default.
        weights_array (list of point deltas, optional): pre-calculated distances between a source and a target.

    Returns:
        subject_mesh (str): name of the retargeted mesh
    """

    if not source_mesh or not target_mesh:
        if not source_array or not weights_array:
            logger.error(
                "You must supply a source_mesh plus target_mesh or"
                "a pre-calculated source_array plus weights_array. You cannot leave all empty."
            )

    subject_mpoint_array = get_vertex_positions(subject_mesh)
    subject_array = convert_marray_to_pyarray(subject_mpoint_array)

    if not source_array and not weights_array:
        source_mpoint_array = get_vertex_positions(source_mesh)
        source_array = convert_marray_to_pyarray(source_mpoint_array)
        target_mpoint_array = get_vertex_positions(target_mesh)
        target_array = convert_marray_to_pyarray(target_mpoint_array)

        # Check that the arrays are the same length
        if len(source_array) != len(target_array):
            logging.error("The input objects have a different vertex count.")

    else:
        target_array = None

    # It works in centimeters, make sure of the scene units
    current_scene_unit = cmds.currentUnit(query=True, linear=True)
    if current_scene_unit != "cm":
        cmds.currentUnit(linear="cm")

    try:
        # Calculate the retargeted subject array with the RBF
        retarget_array = rbf_retarget(
            subject_array,
            source_array=source_array,
            target_array=target_array,
            weights_array=weights_array,
        )

        # Convert retarget array in MPointArray
        retarget_maya_array = om.MPointArray()
        retarget_maya_array.setLength(len(subject_array))
        for i in range(len(retarget_array)):
            p = retarget_array[i]
            retarget_maya_array.set(om.MPoint(p[0], p[1], p[2]), i)

        # Apply the retargeted positions
        dag_subject = core_hrchy.get_dagpath(subject_mesh)
        m_subject_mesh = om.MFnMesh(dag_subject)
        m_subject_mesh.setPoints(retarget_maya_array)
        retarget_result = True

    except Exception as e:
        logger.error(f"Rbf mesh retarget process failed: {e}")
        retarget_result = False

    # Restore unit if was not centimeters
    if current_scene_unit != "cm":
        cmds.currentUnit(linear=current_scene_unit)
    return retarget_result


def get_vertex_positions(input_mesh):
    """
    Returns vertex positions from a given mesh
    Args:
        input_mesh (str): given mesh
    Returns:
        maya_point_array (MPointArray): Maya point array of MPoint vertex world positions
    """
    dag = core_hrchy.get_dagpath(input_mesh)
    mesh_fn = om.MFnMesh(dag)
    maya_point_array = om.MPointArray()
    mesh_fn.getPoints(maya_point_array, om.MSpace.kWorld)
    return maya_point_array


def convert_marray_to_pyarray(maya_array):
    """
    Converts Maya array to python array.
    Args:
        maya_array (MPointArray/MVectorArray): Maya array to convert
    Returns:
        python_array (list float3)
    """
    return [[maya_array[i].x, maya_array[i].y, maya_array[i].z] for i in range(maya_array.length())]


def retarget_skeleton(
    joint_list, source_mesh=None, target_mesh=None, source_array=None, weights_array=None, original_pos_dict=None
):
    """
    Retargets a skeleton based on one mesh to another.

    Args:
        joint_list (list): list of target joints to retarget
        source_mesh (str): source mesh for the rbf comparison
        target_mesh (str): target mesh for the rbf comparison
        source_array (list of point): source point array. None by default.
        weights_array (list of point deltas, optional): pre-calculated distances between a source and a target.
        original_pos_dict (dict, optional): Optional dictionary with original joint positions.

    Returns:
        joint_list (list): list of retargeted joints
    """
    if not source_mesh or not target_mesh:
        if not source_array or not weights_array:
            logger.error(
                "You must supply a source_mesh plus target_mesh or"
                "a pre-calculated source_array plus weights_array. You cannot leave all empty."
            )

    if not source_array and not weights_array:
        source_mpoint_array = get_vertex_positions(source_mesh)
        source_array = convert_marray_to_pyarray(source_mpoint_array)
        target_mpoint_array = get_vertex_positions(target_mesh)
        target_array = convert_marray_to_pyarray(target_mpoint_array)

        # Check that the arrays are the same length
        if len(source_array) != len(target_array):
            logging.error("The input objects have a different vertex count.")

    else:
        target_array = None

    # It works in centimeters, make sure of the scene units
    current_scene_unit = cmds.currentUnit(query=True, linear=True)
    if current_scene_unit != "cm":
        cmds.currentUnit(linear="cm")
    try:
        # Get joint positions
        joint_pos_list = []

        if original_pos_dict:
            for jnt in joint_list:
                joint_pos_list.append(original_pos_dict[jnt])
        else:
            for jnt in joint_list:
                pos = cmds.xform(jnt, q=True, ws=True, t=True)
                joint_pos_list.append(pos)

        # Calculate the retargeted subject array with the RBF
        retarget_array = rbf_retarget(
            joint_pos_list, source_array=source_array, target_array=target_array, weights_array=weights_array
        )

        # Apply the retargeted positions
        for jnt, pos in zip(joint_list, retarget_array):
            cmds.xform(jnt, t=pos, ws=True)

        # Restore unit if was not centimeters
        if current_scene_unit != "cm":
            cmds.currentUnit(linear=current_scene_unit)
        return joint_list

    except Exception as e:
        logger.error(f"Rbf mesh retarget process failed: {e}")
