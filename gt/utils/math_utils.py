"""
Math Utilities
github.com/TrevisanGMW/gt-tools
"""

import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds
import logging
import math

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def matrix_mult(mat1, mat2):
    """
    Multiply two matrices.

    Args:
        mat1 (list of lists): The first matrix.
        mat2 (list of lists): The second matrix.

    Returns:
        list of lists: The result of matrix multiplication.
    """
    result = []
    for i in range(len(mat1)):
        row = []
        for j in range(len(mat2[0])):
            value = 0
            for k in range(len(mat1[0])):
                value += mat1[i][k] * mat2[k][j]
            row.append(value)
        result.append(row)
    return result


def dot_product(vector_a, vector_b):
    """
    Returns the dot product of two vectors.

    Args:
        vector_a (iterable): The first vector (list, tuple, Vector3, etc.).
        vector_b (iterable): The second vector (list, tuple, Vector3, etc.).

    Returns:
        float: The dot product of the two input vectors.
    """
    from gt.utils.transform_utils import Vector3
    if isinstance(vector_a, Vector3):
        vector_a = vector_a.get_as_tuple()
    if isinstance(vector_b, Vector3):
        vector_b = vector_b.get_as_tuple()
    _dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    return _dot_product


def is_float_equal(x, y, tolerance=0.00001):
    """
    Compares two float values and returns their difference
        Args:
            x (float): First float value to compare
            y (float): Second float value to compare
            tolerance (float): Comparison tolerance
        Returns:
            boolean, true if below tolerance threshold
    """
    return abs(x-y) < tolerance


def cross_product(vector_a, vector_b):
    """
    Get Cross Product
        Args:
            vector_a (tuple, list): A tuple or list with three floats/integers
            vector_b (tuple, list): A tuple or list with three floats/integers
        Returns:
            list: Cross product
    """
    result = [
        vector_a[1] * vector_b[2] - vector_a[2] * vector_b[1],
        vector_a[2] * vector_b[0] - vector_a[0] * vector_b[2],
        vector_a[0] * vector_b[1] - vector_a[1] * vector_b[0]
    ]
    return result


def cross_product_differences(vector_a, vector_b, vector_c):
    """
    This function calculates the cross product of the differences between
    "vector_a" and "vector_b" and between "vector_c" and "vector_b".
        Args:
            vector_a (tuple, list): A tuple or list with three floats/integers
            vector_b (tuple, list): A tuple or list with three floats/integers
            vector_c (tuple, list): A tuple or list with three floats/integers
        Returns:
            MVector: cross product of differences
    """
    if type(vector_a) != 'OpenMaya.MVector':
        vector_a = OpenMaya.MVector(vector_a)
    if type(vector_b) != 'OpenMaya.MVector':
        vector_b = OpenMaya.MVector(vector_b)
    if type(vector_c) != 'OpenMaya.MVector':
        vector_c = OpenMaya.MVector(vector_c)
    vector_a = OpenMaya.MVector([vector_a[0] - vector_b[0],
                                 vector_a[1] - vector_b[1],
                                 vector_a[2] - vector_b[2]])
    vector_b = OpenMaya.MVector([vector_c[0] - vector_b[0],
                                 vector_c[1] - vector_b[1],
                                 vector_c[2] - vector_b[2]])
    return vector_a ^ vector_b


def objects_cross_direction(obj_a, obj_b, obj_c):
    """
    Get Cross Direction
        Args:
            obj_a (str): Name of the first object. (Must exist in scene)
            obj_b (str): Name of the second object. (Must exist in scene)
            obj_c (str): Name of the third object. (Must exist in scene)
        Returns:
            tuple: cross direction of the objects
    """
    cross = [0, 0, 0]
    for obj in [obj_a, obj_b, obj_c]:
        if not cmds.objExists(obj):
            return cross
    pos_a = cmds.xform(obj_a, q=True, worldSpace=True, rotatePivot=True)
    pos_b = cmds.xform(obj_b, q=True, worldSpace=True, rotatePivot=True)
    pos_c = cmds.xform(obj_c, q=True, worldSpace=True, rotatePivot=True)

    result = cross_product_differences(pos_a, pos_b, pos_c).normal()
    return tuple(result)


def dist_xyz_to_xyz(pos_a_x, pos_a_y, pos_a_z, pos_b_x, pos_b_y, pos_b_z):
    """
    Calculates the distance between XYZ position A and XYZ position B

    Args:
            pos_a_x (float) : A float/integer for Position X (A)
            pos_a_y (float) : A float/integer for Position Y (A)
            pos_a_z (float) : A float/integer for Position Z (A)
            pos_b_x (float) : A float/integer for Position X (B)
            pos_b_y (float) : A float/integer for Position Y (B)
            pos_b_z (float) : A float/integer for Position Z (YB)

    Returns:
        distance (float): A distance value between object A and B. For example : 4.0
    """
    dx = pos_a_x - pos_b_x
    dy = pos_a_y - pos_b_y
    dz = pos_a_z - pos_b_z
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def dist_center_to_center(obj_a, obj_b):
    """
    Calculates the position between the center of one object (A)  to the center of another object (B)

    Args:
        obj_a (string) : Name of object A
        obj_b (string) : Name of object B

    Returns:
        float: A distance value between object A and B. For example : 4.0 (or 0 if operation failed)
    """
    # WS Center to Center Distance:
    for obj in [obj_a, obj_b]:
        if not obj_a or not cmds.objExists(obj):
            logger.debug(f'Unable to calculate distance. Missing provided object: {str(obj_a)}')
            return 0
    ws_pos_a = cmds.xform(obj_a, q=True, ws=True, t=True)
    ws_pos_b = cmds.xform(obj_b, q=True, ws=True, t=True)
    return dist_xyz_to_xyz(ws_pos_a[0], ws_pos_a[1], ws_pos_a[2], ws_pos_b[0], ws_pos_b[1], ws_pos_b[2])


def get_bbox_center(obj_list):
    """
    Get the center point of the bounding box for the specified object or list of objects.

    Args:
        obj_list (str or list): The name of the object or a list of objects to calculate
            the bounding box center for. (meshes or surfaces only)

    Returns:
        list: A list containing the X, Y, and Z coordinates of the bounding box center.

    Note:
        This function works with a single object or a list of objects. If multiple objects
        are provided, it calculates the bounding box center that encompasses all of them.

    Example:
        result_single = get_bbox_center('myObject')
        [x_coordinate, y_coordinate, z_coordinate]

        result_multiple = get_bbox_center(['obj1', 'obj2', 'obj3'])
        [x_combined_center, y_combined_center, z_combined_center]
    """
    if not isinstance(obj_list, list):
        obj_list = [obj_list]

    all_points = []
    for obj in obj_list:
        shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
        if not shapes:
            logger.debug(f'Unable to get bbox center for {obj}. Input does not have shapes.')
            continue

        points = []
        for shape in shapes:
            if cmds.objectType(shape) == 'nurbsSurface':
                cvs_count = cmds.getAttr(f'{shape}.controlPoints', size=True)
                points.append(f'{shape}.cv[0:{cvs_count - 1}]')
            else:
                vertex_count = cmds.polyEvaluate(shape, vertex=True)
                points.append(f'{shape}.vtx[0:{vertex_count - 1}]')

        all_points.extend(points)

    if not all_points:
        return [0, 0, 0]

    bbox = cmds.exactWorldBoundingBox(all_points)
    bb_min = bbox[:3]
    bb_max = bbox[3:6]
    mid_point = [(b_max + b_min) / 2 for b_min, b_max in zip(bb_min, bb_max)]
    return mid_point


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    center = get_bbox_center(cmds.ls(selection=True))
    x, y, z = center
    locator = cmds.spaceLocator()[0]
    cmds.move(x, y, z, locator)
