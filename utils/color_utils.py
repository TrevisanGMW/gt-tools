import maya.cmds as cmds
import logging
import math

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("attribute_utils")
logger.setLevel(logging.INFO)


def change_viewport_color(obj, rgb_color=(1, 1, 1)):
    """
    Sets the outliner color for the selected object

    Args:
        obj (str): Name (path) of the object to change.
        rgb_color (tuple) : A tuple of 3 floats, RGB values. e.g. Red = (1, 0, 0)

    """
    if cmds.objExists(obj) and cmds.getAttr(obj + '.overrideEnabled', lock=True) is False:
        cmds.setAttr(obj + '.overrideEnabled', 1)
        cmds.setAttr(obj + '.overrideRGBColors', 1)
        cmds.setAttr(obj + '.overrideColorRGB', rgb_color[0], rgb_color[1], rgb_color[2])


def set_color_outliner(obj_to_set):
    """
    Sets the outliner color for the selected object

    Args:
        obj_to_set (str): Name (path) of the object to affect.

    """
    extracted_r = math.pow(color[0], 0.454)
    extracted_g = math.pow(color[1], 0.454)
    extracted_b = math.pow(color[2], 0.454)

    cmds.setAttr(obj_to_set + '.useOutlinerColor', 1)
    cmds.setAttr(obj_to_set + '.outlinerColorR', extracted_r)
    cmds.setAttr(obj_to_set + '.outlinerColorG', extracted_g)
    cmds.setAttr(obj_to_set + '.outlinerColorB', extracted_b)
    return True


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    pprint(out)

