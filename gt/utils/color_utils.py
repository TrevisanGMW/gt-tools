"""
Color Utilities
github.com/TrevisanGMW/gt-tools
"""
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def set_color_override_viewport(obj, rgb_color=(1, 1, 1)):
    """
    Sets the outliner color for the selected object

    Args:
        obj (str): Name (path) of the object to change.
        rgb_color (tuple) : A tuple of 3 floats, RGB values. e.g. Red = (1, 0, 0)
    Returns:
        Set color if operation was successful. None if it failed
    """
    if cmds.objExists(obj) and cmds.getAttr(f'{obj}.overrideEnabled', lock=True) is False:
        cmds.setAttr(f'{obj}.overrideEnabled', 1)
        cmds.setAttr(f'{obj}.overrideRGBColors', 1)
        cmds.setAttr(f'{obj}.overrideColorRGB', rgb_color[0], rgb_color[1], rgb_color[2])
        set_color = cmds.getAttr(f'{obj}.overrideColorRGB') or []
        if set_color and len(set_color) > 0:
            return set_color[0]


def set_color_override_outliner(obj, rgb_color=(1, 1, 1)):
    """
    Sets the outliner color for the selected object

    Args:
        obj (str): Name of the object to change.
        rgb_color (tuple) : A tuple of 3 floats, RGB values. e.g. Red = (1, 0, 0) - Range 0 to 1
    Returns:
        Set color if operation was successful. None if it failed
    """
    if cmds.objExists(obj) and cmds.getAttr(f'{obj}.useOutlinerColor', lock=True) is False:
        cmds.setAttr(f'{obj}.useOutlinerColor', 1)
        cmds.setAttr(f'{obj}.outlinerColorR', rgb_color[0])
        cmds.setAttr(f'{obj}.outlinerColorG', rgb_color[1])
        cmds.setAttr(f'{obj}.outlinerColorB', rgb_color[2])
        set_color = cmds.getAttr(f'{obj}.outlinerColor') or []
        if set_color and len(set_color) > 0:
            return set_color[0]


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    pprint(out)

