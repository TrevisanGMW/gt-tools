"""
Math Utilities
github.com/TrevisanGMW/gt-tools
"""
import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds
import logging

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


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
