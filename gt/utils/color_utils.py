"""
Color Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.attr_utils import add_attr_double_three
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ColorConstants:
    def __init__(self):
        """
        Constant tuple RGB values used for element colors.
        """
    CENTER = (1, 1, 0.65)
    LEFT = (0, 0.5, 1)
    RIGHT = (1, 0.5, 0.5)


def set_color_viewport(obj_list, rgb_color=(1, 1, 1)):
    """
    Sets the overwrite viewport color for the provided object(s).
    Activates viewport override outliner color in case it's off.

    Args:
        obj_list (list, str): Name (path) to the object to be affected.
        rgb_color (tuple, list) : RGB values. e.g. Red = (1, 0, 0) - Must have at least 3 floats/integers.
    Returns:
        list: A list of objects that had their viewport colors changed.
    """
    if obj_list and isinstance(obj_list, str):
        obj_list = [obj_list]
    if obj_list and not isinstance(obj_list, list):
        logger.debug(f'Unable to set override viewport color. Unexpected object list type.')
        return []
    if not rgb_color or not isinstance(rgb_color, (list, tuple)) or len(rgb_color) < 3:
        logger.debug(f'Unable to set override viewport color. Unexpected RGB input.')
        return []
    result_list = []
    for obj in obj_list:
        if cmds.objExists(obj) and cmds.getAttr(f'{obj}.overrideEnabled', lock=True) is False:
            try:
                cmds.setAttr(f'{obj}.overrideEnabled', 1)
                cmds.setAttr(f'{obj}.overrideRGBColors', 1)
                cmds.setAttr(f'{obj}.overrideColorRGB', rgb_color[0], rgb_color[1], rgb_color[2])
                result_list.append(obj)
            except Exception as e:
                logger.debug(f'Unable to set override viewport color for "{obj}". Issue: {str(e)}')
    return result_list


def set_color_outliner(obj_list, rgb_color=(1, 1, 1)):
    """
    Sets the overwrite outliner color for the provided object(s).
    Activates override outliner color in case it's off.

    Args:
        obj_list (list, str): Name (path) to the object to be affected.
        rgb_color (tuple, list) : RGB values. e.g. Red = (1, 0, 0) - Must have at least 3 floats/integers.
    Returns:
        list: A list of objects that had their outliner colors changed.
    """
    if obj_list and isinstance(obj_list, str):
        obj_list = [obj_list]
    if obj_list and not isinstance(obj_list, list):
        logger.debug(f'Unable to set override outliner color. Unexpected object list type.')
        return []
    if not rgb_color or not isinstance(rgb_color, (list, tuple)) or len(rgb_color) < 3:
        logger.debug(f'Unable to set override outliner color. Unexpected RGB input.')
        return []
    result_list = []
    for obj in obj_list:
        try:
            if cmds.objExists(obj) and cmds.getAttr(f'{obj}.useOutlinerColor', lock=True) is False:
                cmds.setAttr(f'{obj}.useOutlinerColor', 1)
                cmds.setAttr(f'{obj}.outlinerColorR', rgb_color[0])
                cmds.setAttr(f'{obj}.outlinerColorG', rgb_color[1])
                cmds.setAttr(f'{obj}.outlinerColorB', rgb_color[2])
                result_list.append(obj)
        except Exception as e:
            logger.debug(f'Unable to set override outliner color for "{obj}". Issue: {str(e)}')
    return result_list


def add_side_color_setup(obj, color_attr_name="autoColor",
                         clr_default=ColorConstants.CENTER,
                         clr_left=ColorConstants.LEFT,
                         clr_right=ColorConstants.RIGHT):
    """
    This function sets up a side color setup for the specified object in the Maya scene.
    It creates connections and attributes to control the color of the object based on its position in the scene.

    Parameters:
        obj (str): The name of the object to set up the color for.
        color_attr_name (str, optional): Name of the attribute used to determine if auto color is active or not.
        clr_default (tuple, optional): The RGB color for when the object is in the center or not automatically defined.
        clr_left (tuple, optional): The RGB color for when on the left side. e.g. (0, 0.5, 1).
        clr_right (tuple, optional): The RGB color for when on the right side. e.g.(1, 0.5, 0.5).

    Example:
        # Example usage in Maya Python script editor:
        add_side_color_setup("pCube1", left_clr=(0, 1, 0), right_clr=(1, 0, 0))
    """
    if not obj or not cmds.objExists(obj):
        return

    # Setup Base Connections
    cmds.setAttr(obj + ".overrideEnabled", 1)
    cmds.setAttr(obj + ".overrideRGBColors", 1)
    clr_side_condition = cmds.createNode("condition", name=obj + "_clr_side_condition")
    clr_center_condition = cmds.createNode("condition", name=obj + "_clr_center_condition")
    decompose_matrix = cmds.createNode("decomposeMatrix", name=obj + "_decompose_matrix")
    cmds.connectAttr(obj + ".worldMatrix[0]", decompose_matrix + ".inputMatrix")
    cmds.connectAttr(decompose_matrix + ".outputTranslateX", clr_side_condition + ".firstTerm")
    cmds.connectAttr(decompose_matrix + ".outputTranslateX", clr_center_condition + ".firstTerm")
    cmds.connectAttr(clr_side_condition + ".outColor", clr_center_condition + ".colorIfFalse")
    cmds.setAttr(clr_side_condition + ".operation", 2)

    # Create Auto Color Attribute
    cmds.addAttr(obj, ln=color_attr_name, at='bool', k=True)
    cmds.setAttr(obj + "." + color_attr_name, 1)
    clr_auto_blend = cmds.createNode("blendColors", name=obj + "_clr_auto_blend")
    cmds.connectAttr(clr_auto_blend + ".output", obj + ".overrideColorRGB")
    cmds.connectAttr(clr_center_condition + ".outColor", clr_auto_blend + ".color1")
    cmds.connectAttr(obj + "." + color_attr_name, clr_auto_blend + ".blender")

    # Setup Color Attributes
    clr_attr = "colorDefault"
    add_attr_double_three(obj, clr_attr, keyable=False)
    cmds.setAttr(f'{obj}.{clr_attr}R', clr_default[0])
    cmds.setAttr(f'{obj}.{clr_attr}G', clr_default[1])
    cmds.setAttr(f'{obj}.{clr_attr}B', clr_default[2])
    cmds.connectAttr(f'{obj}.{clr_attr}R', clr_center_condition + ".colorIfTrueR")
    cmds.connectAttr(f'{obj}.{clr_attr}G', clr_center_condition + ".colorIfTrueG")
    cmds.connectAttr(f'{obj}.{clr_attr}B', clr_center_condition + ".colorIfTrueB")
    cmds.connectAttr(f'{obj}.{clr_attr}', clr_auto_blend + ".color2")  # Blend node input
    r_clr_attr = "colorRight"
    add_attr_double_three(obj, r_clr_attr, keyable=False)
    cmds.setAttr(obj + "." + r_clr_attr + "R", clr_left[0])
    cmds.setAttr(obj + "." + r_clr_attr + "G", clr_left[1])
    cmds.setAttr(obj + "." + r_clr_attr + "B", clr_left[2])
    cmds.connectAttr(obj + "." + r_clr_attr + "R", clr_side_condition + ".colorIfTrueR")
    cmds.connectAttr(obj + "." + r_clr_attr + "G", clr_side_condition + ".colorIfTrueG")
    cmds.connectAttr(obj + "." + r_clr_attr + "B", clr_side_condition + ".colorIfTrueB")
    l_clr_attr = "colorLeft"
    add_attr_double_three(obj, l_clr_attr, keyable=False)
    cmds.setAttr(obj + "." + l_clr_attr + "R", clr_right[0])
    cmds.setAttr(obj + "." + l_clr_attr + "G", clr_right[1])
    cmds.setAttr(obj + "." + l_clr_attr + "B", clr_right[2])
    cmds.connectAttr(obj + "." + l_clr_attr + "R", clr_side_condition + ".colorIfFalseR")
    cmds.connectAttr(obj + "." + l_clr_attr + "G", clr_side_condition + ".colorIfFalseG")
    cmds.connectAttr(obj + "." + l_clr_attr + "B", clr_side_condition + ".colorIfFalseB")


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    add_side_color_setup("pSphere1")
