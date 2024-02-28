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


def get_bbox_position(obj_list, alignment=None, axis="x"):
    """
    Get the center point of the bounding box for the specified object or list of objects.

    Args:
        obj_list (str, list): The name of the object(s) to get the bounding box position. Meshes or surfaces only.
        alignment (str, None): Alignment option, can be None (center), "+" (max), or "-" (min).
                               When "None" (which is center) the axis is ignored.
        axis (str): Axis option, can be "x", "y", or "z". Defaults to "x". (ignored if alignment is None)

    Returns:
        tuple: A tuple containing the X, Y, and Z coordinates of the bounding box position.

    Example:
        result_single = get_bbox_center('myObject')
        (x_coordinate, y_coordinate, z_coordinate)

        result_multiple = get_bbox_center(['obj1', 'obj2', 'obj3'])
        (x_combined_center, y_combined_center, z_combined_center)

        result_multiple = get_bbox_center(['obj1', 'obj2', 'obj3'])
        (x_combined_center, y_combined_center, z_combined_center)
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
            if cmds.objectType(shape) == 'nurbsSurface' or cmds.objectType(shape) == 'nurbsCurve':
                cvs_count = cmds.getAttr(f'{shape}.controlPoints', size=True)
                points.append(f'{shape}.cv[0:{cvs_count - 1}]')
            else:
                vertex_count = cmds.polyEvaluate(shape, vertex=True)
                points.append(f'{shape}.vtx[0:{vertex_count - 1}]')

        all_points.extend(points)

    if not all_points:
        return 0, 0, 0

    bbox = cmds.exactWorldBoundingBox(all_points)
    bb_min = bbox[:3]
    bb_max = bbox[3:6]
    mid_point = list((b_max + b_min) / 2 for b_min, b_max in zip(bb_min, bb_max))

    index = {"x": 0, "y": 1, "z": 2}[axis]
    if alignment == "+":
        mid_point[index] = bb_max[index]
    elif alignment == "-":
        mid_point[index] = bb_min[index]

    return tuple(mid_point)


def get_transforms_center_position(transform_list):
    """
    Get the center position of a list of transform nodes.
    Missing objects are ignored. If none of the objects are found, the origin (0, 0, 0) is returned instead.

    Args:
        transform_list (list): List of transform node paths/names.

    Returns:
        tuple: Center position as a tuple (x, y, z).
    """
    # Initialize variables to store total position and count
    total_position = [0, 0, 0]
    num_transforms = 0

    # Iterate through each transform
    for transform_name in transform_list:
        # Check if the transform exists
        if cmds.objExists(transform_name):
            # Get the translation values of the transform
            transform_position = cmds.xform(transform_name, query=True, translation=True, worldSpace=True)
            # Add the position values to the total
            total_position[0] += transform_position[0]
            total_position[1] += transform_position[1]
            total_position[2] += transform_position[2]
            num_transforms += 1  # Increment the count of existing transforms

    # Check if any transforms exist
    if num_transforms == 0:
        # If no transforms exist, return the origin
        return 0, 0, 0

    # Calculate the average position by dividing the total by the number of existing transforms
    center_position = (
        total_position[0] / num_transforms,
        total_position[1] / num_transforms,
        total_position[2] / num_transforms
    )

    return center_position


def remap_value(value, old_range, new_range):
    """
    Remap a value from one range to another.

    Args:
        value (float): The input value to be remapped.
        old_range (tuple, list): The range of the input value, specified as a tuple (min, max).
        new_range (tuple, list): The desired range for the normalized value, specified as a tuple (min, max).

    Returns:
        float: The remapped value.

    Example:
        out = remap_value(value=50, old_range=(0, 100), new_range=(0, 1))
        print(out)  # 0.5
    """
    return (value - old_range[0]) * (new_range[1] - new_range[0]) / (old_range[1] - old_range[0]) + new_range[0]


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    # center = get_bbox_position("pSphere1")
    # print(center)
    # x, y, z = center
    # locator = cmds.spaceLocator()[0]
    # cmds.move(x, y, z, locator)
    print(get_bbox_position("combined_curve_01"))
