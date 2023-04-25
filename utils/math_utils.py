import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("math_utils")
logger.setLevel(logging.INFO)


def get_dot_product(vector_a, vector_b):
    """
    Returns dot product
        Args:
            vector_a (list, MVector): first vector
            vector_b (list, MVector): second vector
    """
    if type(vector_a) != 'OpenMaya.MVector':
        vector_a = OpenMaya.MVector(vector_a)
    if type(vector_b) != 'OpenMaya.MVector':
        vector_b = OpenMaya.MVector(vector_b)
    return vector_a * vector_b


def get_cross_product(vector_a, vector_b, vector_c):
    """
    Get Cross Product
        Args:
            vector_a (list): A list of floats
            vector_b (list): A list of floats
            vector_c (list): A list of floats
        Returns:
            MVector: cross product
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


def get_cross_direction(obj_a, obj_b, obj_c):
    """
    Get Cross Direction
        Args:
            obj_a (string): Name of the first object. (Must exist in scene)
            obj_b (string): Name of the second object. (Must exist in scene)
            obj_c (string): Name of the third object. (Must exist in scene)
        Returns:
            MVector: cross direction of the objects
    """
    cross = [0, 0, 0]
    for obj in [obj_a, obj_b, obj_c]:
        if not cmds.objExists(obj):
            return cross
    pos_a = cmds.xform(obj_a, q=True, ws=True, rp=True)
    pos_b = cmds.xform(obj_b, q=True, ws=True, rp=True)
    pos_c = cmds.xform(obj_c, q=True, ws=True, rp=True)

    return get_cross_product(pos_a, pos_b, pos_c).normal()


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


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    pprint(out)
