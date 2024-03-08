"""
Color Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.attr_utils import add_attr_double_three
from gt.utils.naming_utils import get_short_name
import maya.cmds as cmds
import logging


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ColorConstants:
    def __init__(self):
        """
        Constant tuple RGB values used as colors.
        """
    class RGB:
        def __init__(self):
            """
            A library of RGB colors.
            Type: tuple
            Format: (Red, Green, Blue)
            Value range: 0 to 1
            e.g. (1, 0, 0) = Red
            """

        # Red -------------------------------------------
        RED_MAROON = (0.502, 0, 0)
        RED_METALLIC_DARK = (0.545, 0, 0)
        RED_METALLIC = (0.686, 0.176, 0.176)
        RED_BROWN = (0.647, 0.165, 0.165)
        RED_FIREBRICK = (0.698, 0.133, 0.133)
        RED_CRIMSON = (0.863, 0.078, 0.235)
        RED = (1, 0, 0)
        RED_TOMATO = (1, 0.388, 0.278)
        RED_CORAL = (1, 0.498, 0.314)
        RED_INDIAN = (0.804, 0.361, 0.361)
        RED_MELON = (1, 0.667, 0.667)

        # Salmon -----------------------------------------
        SALMON_LIGHT_CORAL = (0.941, 0.502, 0.502)
        SALMON_DARK = (0.914, 0.588, 0.478)
        SALMON = (0.98, 0.502, 0.447)
        SALMON_LIGHT = (1, 0.627, 0.478)

        # Orange -----------------------------------------
        ORANGE_RED = (1, 0.271, 0)
        ORANGE_DARK = (1, 0.549, 0)
        ORANGE = (1, 0.647, 0)

        # Yellow -----------------------------------------
        YELLOW_GOLD = (1, 0.843, 0)
        YELLOW_DARK_GOLDEN_ROD = (0.722, 0.525, 0.043)
        YELLOW_GOLDEN_ROD = (0.855, 0.647, 0.125)
        YELLOW_PALE_GOLDEN_ROD = (0.933, 0.91, 0.667)
        YELLOW_DARK_KHAKI = (0.741, 0.718, 0.42)
        YELLOW_KHAKI = (0.941, 0.902, 0.549)
        YELLOW_OLIVE = (0.502, 0.502, 0)
        YELLOW = (1, 1, 0)
        YELLOW_GREEN = (0.604, 0.804, 0.196)

        # Green ------------------------------------------
        GREEN_DARK_OLIVE = (0.333, 0.42, 0.184)
        GREEN_OLIVE_DRAB = (0.42, 0.557, 0.137)
        GREEN_LAWN_GREEN = (0.486, 0.988, 0)
        GREEN_CHARTREUSE = (0.498, 1, 0)
        GREEN_YELLOW = (0.678, 1, 0.184)
        GREEN_DARK = (0, 0.392, 0)
        GREEN = (0, 0.502, 0)
        GREEN_FOREST = (0.133, 0.545, 0.133)
        GREEN_LIME_PURE = (0, 1, 0)
        GREEN_LIME = (0.196, 0.804, 0.196)
        GREEN_LIGHT = (0.565, 0.933, 0.565)
        GREEN_PALE = (0.596, 0.984, 0.596)
        GREEN_DARK_SEA = (0.561, 0.737, 0.561)
        GREEN_OXLEY = (0.376, 0.596, 0.506)
        GREEN_MEDIUM_SPRING = (0, 0.98, 0.604)
        GREEN_SPRING = (0, 1, 0.498)
        GREEN_SEA = (0.18, 0.545, 0.341)
        GREEN_MEDIUM_AQUA_MARINE = (0.4, 0.804, 0.667)
        GREEN_MEDIUM_SEA = (0.235, 0.702, 0.443)
        GREEN_LIGHT_SEA = (0.125, 0.698, 0.667)
        GREEN_TEAL = (0, 0.502, 0.502)
        GREEN_HONEYDEW = (0.941, 1, 0.941)
        GREEN_PEARL_AQUA = (0.565, 0.894, 0.757)
        GREEN_WINTERGREEN_DREAM = (0.345, 0.549, 0.467)

        # Cyan -------------------------------------------
        CYAN_DARK = (0, 0.545, 0.545)
        CYAN_AQUA = (0, 1, 1)
        CYAN = (0, 1, 1)
        CYAN_LIGHT = (0.878, 1, 1)

        # Turquoise ---------------------------------------
        TURQUOISE_DARK = (0, 0.808, 0.82)
        TURQUOISE = (0.251, 0.878, 0.816)
        TURQUOISE_MEDIUM = (0.282, 0.82, 0.8)
        TURQUOISE_PALE = (0.686, 0.933, 0.933)

        # Blue --------------------------------------------
        BLUE_AQUA_MARINE = (0.498, 1, 0.831)
        BLUE_POWDER = (0.69, 0.878, 0.902)
        BLUE_CADET = (0.373, 0.62, 0.627)
        BLUE_STEEL = (0.275, 0.51, 0.706)
        BLUE_CORN_FLOWER = (0.392, 0.584, 0.929)
        BLUE_DEEP_SKY = (0, 0.749, 1)
        BLUE_DODGER = (0.118, 0.565, 1)
        BLUE_LIGHT = (0.678, 0.847, 0.902)
        BLUE_SKY = (0.529, 0.808, 0.922)
        BLUE_LIGHT_SKY = (0.529, 0.808, 0.98)
        BLUE_MIDNIGHT = (0.098, 0.098, 0.439)
        BLUE_NAVY = (0, 0, 0.502)
        BLUE_DARK = (0, 0, 0.545)
        BLUE_MEDIUM = (0, 0, 0.804)
        BLUE = (0, 0, 1)
        BLUE_ROYAL = (0.255, 0.412, 0.882)
        BLUE_VIOLET = (0.541, 0.169, 0.886)
        BLUE_ALICE = (0.941, 0.973, 1)
        BLUE_AZURE = (0.941, 1, 1)
        BLUE_GHOSTED = (0, 0, 1)
        BLUE_LAVENDER = (0.741, 0.851, 1)
        BLUE_PASTEL = (0.322, 0.522, 0.651)
        BLUE_VIVID_CERULEAN = (0, 0.627, 0.91)
        BLUE_MEDIUM_PERSIAN = (0, 0.431, 0.627)

        # Purple -------------------------------------------
        PURPLE_INDIGO = (0.294, 0, 0.51)
        PURPLE_DARK_SLATE_BLUE = (0.282, 0.239, 0.545)
        PURPLE_SLATE_BLUE = (0.416, 0.353, 0.804)
        PURPLE_MEDIUM_SLATE_BLUE = (0.482, 0.408, 0.933)
        PURPLE_MEDIUM = (0.576, 0.439, 0.859)
        PURPLE_DARK_MAGENTA = (0.545, 0, 0.545)
        PURPLE_DARK_VIOLET = (0.58, 0, 0.827)
        PURPLE_DARK_ORCHID = (0.6, 0.196, 0.8)
        PURPLE_MEDIUM_ORCHID = (0.729, 0.333, 0.827)
        PURPLE = (0.502, 0, 0.502)

        # Magenta -------------------------------------------
        MAGENTA_THISTLE = (0.847, 0.749, 0.847)
        MAGENTA_PLUM = (0.867, 0.627, 0.867)
        MAGENTA_VIOLET = (0.933, 0.51, 0.933)
        MAGENTA_FUCHSIA = (1, 0, 1)
        MAGENTA_ORCHID = (0.855, 0.439, 0.839)
        MAGENTA_MEDIUM_VIOLET_RED = (0.78, 0.082, 0.522)
        MAGENTA_PALE_VIOLET_RED = (0.859, 0.439, 0.576)

        # Pink ---------------------------------------------
        PINK_DEEP = (1, 0.078, 0.576)
        PINK_HOT = (1, 0.412, 0.706)
        PINK_LIGHT = (1, 0.714, 0.757)
        PINK = (1, 0.753, 0.796)

        # Brown --------------------------------------------
        BROWN_SADDLE = (0.545, 0.271, 0.075)
        BROWN_SIENNA = (0.627, 0.322, 0.176)
        BROWN_CHOCOLATE = (0.824, 0.412, 0.118)
        BROWN_PERU = (0.804, 0.522, 0.247)
        BROWN_SANDY = (0.957, 0.643, 0.376)
        BROWN_BURLY_WOOD = (0.871, 0.722, 0.529)
        BROWN_TAN = (0.824, 0.706, 0.549)

        # White -----------------------------------------
        WHITE = (1, 1, 1)
        WHITE_FLORAL = (1, 0.98, 0.941)
        WHITE_GHOST = (0.973, 0.973, 1)
        WHITE_IVORY = (1, 1, 0.941)
        WHITE_SNOW = (1, 0.98, 0.98)
        WHITE_SMOKE = (0.961, 0.961, 0.961)
        WHITE_SMOKE_DARKER = (0.933, 0.933, 0.933)
        WHITE_SMOKE_DARKER_GHOSTED = (0.933, 0.933, 0.933)
        WHITE_ANTIQUE = (0.98, 0.922, 0.843)
        WHITE_BEIGE = (0.961, 0.961, 0.863)
        WHITE_BISQUE = (1, 0.894, 0.769)
        WHITE_BLANCHED_ALMOND = (1, 0.922, 0.804)
        WHITE_WHEAT = (0.961, 0.871, 0.702)
        WHITE_CORN_SILK = (1, 0.973, 0.863)
        WHITE_LEMON_CHIFFON = (1, 0.98, 0.804)
        WHITE_LIGHT_GOLDEN_ROD_YELLOW = (0.98, 0.98, 0.824)
        WHITE_LIGHT_YELLOW = (1, 1, 0.878)
        WHITE_BROWN_ROSY = (0.737, 0.561, 0.561)
        WHITE_BROWN_MOCCASIN = (1, 0.894, 0.71)
        WHITE_BROWN_NAVAJO = (1, 0.871, 0.678)
        WHITE_PEACH_PUFF = (1, 0.855, 0.725)
        WHITE_MISTY_ROSE = (1, 0.894, 0.882)
        WHITE_LAVENDER_BLUSH = (1, 0.941, 0.961)
        WHITE_LAVENDER = (0.902, 0.902, 0.98)
        WHITE_LINEN = (0.98, 0.941, 0.902)
        WHITE_OLD_LACE = (0.992, 0.961, 0.902)
        WHITE_PAPAYA_WHIP = (1, 0.937, 0.835)
        WHITE_SEA_SHELL = (1, 0.961, 0.933)
        WHITE_MINT_CREAM = (0.961, 1, 0.98)

        # Gray -------------------------------------------
        GRAY_DIM = (0.412, 0.412, 0.412)
        GRAY = (0.502, 0.502, 0.502)
        GRAY_DARK = (0.663, 0.663, 0.663)
        GRAY_SILVER = (0.753, 0.753, 0.753)
        GRAY_LIGHT = (0.827, 0.827, 0.827)
        GRAY_DARK_SLATE_GRAY = (0.184, 0.31, 0.31)
        GRAY_NERO = (0.078, 0.078, 0.078)
        GRAY_MUCH_DARKER = (0.114, 0.114, 0.114)
        GRAY_DARKER_MID = (0.137, 0.137, 0.137)
        GRAY_DARKER = (0.169, 0.169, 0.169)
        GRAY_DARKER_GHOSTED = (0.169, 0.169, 0.169)
        GRAY_MID_DARK = (0.267, 0.267, 0.267)
        GRAY_MID_DARK_GHOSTED = (0.267, 0.267, 0.267)
        GRAY_MID = (0.286, 0.286, 0.286)
        GRAY_MID_LIGHT = (0.322, 0.322, 0.322)
        GRAY_MID_LIGHTER = (0.365, 0.365, 0.365)
        GRAY_MID_MUCH_LIGHTER = (0.439, 0.439, 0.439)
        GREY_LIGHT = (0.569, 0.569, 0.569)
        GRAY_LIGHTER = (0.627, 0.627, 0.627)
        GRAY_DARK_SILVER = (0.706, 0.706, 0.706)
        GRAY_GAINSBORO = (0.863, 0.863, 0.863)
        GRAY_SLATE = (0.439, 0.502, 0.565)
        GRAY_LIGHT_SLATE = (0.467, 0.533, 0.6)
        GRAY_LIGHT_STEEL_BLUE = (0.69, 0.769, 0.871)

        # Misc -----------------------------------------
        BLACK = (0, 0, 0)

    class RigProxy:
        def __init__(self):
            """
            A library of RGB colors for rigs.
            Type: tuple
            Format: (Red, Green, Blue)
            Value range  0 to 1
            e.g. (1, 0, 0) = Red
            """
        CENTER = (1, 1, 0.65)  # Yellowish White
        LEFT = (0.2, 0.6, 1)  # Soft Blue
        RIGHT = (1, 0.4, 0.4)  # Soft Red
        PIVOT = (1, 0, 0)  # Red (Pure)
        FOLLOWER = (0.3, 0.3, 0)  # Dark Yellow
        TWEAK = (0.6, 0.2, 1)  # Pinkish Purple

    class RigControl:
        def __init__(self):
            """
            A library of RGB colors for rigs.
            Type: tuple
            Format: (Red, Green, Blue)
            Value range  0 to 1
            e.g. (1, 0, 0) = Red
            """
        ROOT = (1, 0.17, 0.44)  # Soft Pink
        CENTER = (1, 1, 0)  # Yellow
        LEFT = (0.21, 0.45, 1)  # Soft Blue
        LEFT_OFFSET = (0.4, 0.7, 1)
        RIGHT = (1, 0.15, 0.15)  # Soft Red
        RIGHT_OFFSET = (1, 0.5, 0.5)
        OFFSET = (0.4, 0.4, 0)  # Dark Yellow
        PIVOT = (.17, 0, .78)  # Deep Purple
        END = (1, 0, 0)
        TWEAK = (0.6, 0.2, 1)  # Pinkish Purple

    class RigJoint:
        def __init__(self):
            """
            A library of RGB colors for rigs.
            Type: tuple
            Format: (Red, Green, Blue)
            Value range  0 to 1
            e.g. (1, 0, 0) = Red
            """
        ROOT = (0.4, 0.4, 0.4)  # Gray
        GENERAL = (1, 1, 0)  # Yellow
        OFFSET = (0.4, 0.4, 0)  # Dark Yellow
        FK = (1, 0.5, .5)  # Soft Red
        IK = (0.5, 0.5, 1)  # Soft Blue/Purple
        END = (1, 0, 0)  # Red Pure
        UNIQUE = (0, 1, 0)  # Green
        AUTOMATION = (1, 0.17, 0.75)  # Hot Pink
        DATA_QUERY = (1, 1, 1)  # White

    class RigOutliner:
        def __init__(self):
            """
            A library of RGB colors for outliner.
            Type: tuple
            Format: (Red, Green, Blue)
            Value range  0 to 1
            e.g. (1, 0, 0) = Red
            """
        GRP_ROOT_RIG = (1, .45, .7)  # Salmon
        GRP_ROOT_PROXY = (1, .75, .85)  # Soft Salmon
        GRP_GEOMETRY = (.3, 1, .8)  # Bright Turquoise
        GRP_SKELETON = (.75, .45, .95)  # Purple
        GRP_CONTROL = (1, 0.45, 0.2)  # Orange
        GRP_SETUP = (1, .25, .25)  # Soft Red
        CTRL = (1, .65, .45)  # Soft Orange
        AUTOMATION = (1, .65, .45)  # Soft Orange
        FK = (1, .5, .5)  # Soft Red
        IK = (.5, .5, 1)  # Soft Blue
        DATA_QUERY = (1, 1, 1)  # White


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
        if cmds.objExists(str(obj)) and cmds.getAttr(f'{obj}.overrideEnabled', lock=True) is False:
            try:
                cmds.setAttr(f'{obj}.overrideEnabled', 1)
                cmds.setAttr(f'{obj}.overrideRGBColors', 1)
                cmds.setAttr(f'{obj}.overrideColorRGB', rgb_color[0], rgb_color[1], rgb_color[2])
                result_list.append(str(obj))
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
            if cmds.objExists(str(obj)) and cmds.getAttr(f'{obj}.useOutlinerColor', lock=True) is False:
                cmds.setAttr(f'{obj}.useOutlinerColor', 1)
                cmds.setAttr(f'{obj}.outlinerColorR', rgb_color[0])
                cmds.setAttr(f'{obj}.outlinerColorG', rgb_color[1])
                cmds.setAttr(f'{obj}.outlinerColorB', rgb_color[2])
                result_list.append(str(obj))
        except Exception as e:
            logger.debug(f'Unable to set override outliner color for "{obj}". Issue: {str(e)}')
    return result_list


def apply_gamma_correction_to_rgb(rgb_color, gamma_correction=2.2):
    """
    Convert RGB colors from display space to render space in Maya by applying gamma correction

    Args:
        rgb_color (tuple): RGB color as a tuple of three floats (Red, Green, Blue).
        gamma_correction (float, int): Gamma correction value

    Returns:
        tuple: RGB color in render space as a tuple of three floats (Red, Green, Blue).
    """
    # Apply gamma correction to each channel
    _new_rgb_color = (
        rgb_color[0] ** gamma_correction,
        rgb_color[1] ** gamma_correction,
        rgb_color[2] ** gamma_correction
    )
    return _new_rgb_color


def remove_gamma_correction_from_rgb(rgb_color, gamma_correction=2.2):
    """
    Convert RGB colors from render space to display space in Maya by removing gamma correction.

    Args:
        rgb_color (tuple): RGB color in render space as a tuple of three floats (Red, Green, Blue).
        gamma_correction (float, int): Gamma correction value

    Returns:
        tuple: RGB color in display space as a tuple of three floats (Red, Green, Blue).
    """
    # Remove gamma correction from each channel
    _new_rgb_color = (
        rgb_color[0] ** (1.0 / gamma_correction),
        rgb_color[1] ** (1.0 / gamma_correction),
        rgb_color[2] ** (1.0 / gamma_correction)
    )
    return _new_rgb_color


def add_side_color_setup(obj, color_attr_name="autoColor",
                         clr_default=ColorConstants.RigProxy.CENTER,
                         clr_left=ColorConstants.RigProxy.LEFT,
                         clr_right=ColorConstants.RigProxy.RIGHT):
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

    obj_name = get_short_name(obj)
    # Setup Base Connections
    cmds.setAttr(f'{obj}.overrideEnabled', 1)
    cmds.setAttr(f'{obj}.overrideRGBColors', 1)
    clr_side_condition = cmds.createNode("condition", name=f'{obj_name}_clr_side_condition')
    clr_center_condition = cmds.createNode("condition", name=f'{obj_name}_clr_center_condition')
    decompose_matrix = cmds.createNode("decomposeMatrix", name=f'{obj_name}_decompose_matrix')
    cmds.connectAttr(f'{obj}.worldMatrix[0]', f'{decompose_matrix}.inputMatrix')
    cmds.connectAttr(f"{decompose_matrix}.outputTranslateX", f"{clr_side_condition}.firstTerm")
    cmds.connectAttr(f"{decompose_matrix}.outputTranslateX", f"{clr_center_condition}.firstTerm")
    cmds.connectAttr(f"{clr_side_condition}.outColor", f"{clr_center_condition}.colorIfFalse")
    cmds.setAttr(f"{clr_side_condition}.operation", 2)

    # Create Auto Color Attribute
    cmds.addAttr(obj, ln=color_attr_name, at='bool', k=True)
    cmds.setAttr(f"{obj}.{color_attr_name}", 1)
    clr_auto_blend = cmds.createNode("blendColors", name=f"{obj_name}_clr_auto_blend")
    cmds.connectAttr(f"{clr_auto_blend}.output", f"{obj}.overrideColorRGB")
    cmds.connectAttr(clr_center_condition + ".outColor", clr_auto_blend + ".color1")
    cmds.connectAttr(f"{obj}.{color_attr_name}", f"{clr_auto_blend}.blender")

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
    cmds.setAttr(f"{obj}.{r_clr_attr}R", clr_left[0])
    cmds.setAttr(f"{obj}.{r_clr_attr}G", clr_left[1])
    cmds.setAttr(f"{obj}.{r_clr_attr}B", clr_left[2])
    cmds.connectAttr(f"{obj}.{r_clr_attr}R", f"{clr_side_condition}.colorIfTrueR")
    cmds.connectAttr(f"{obj}.{r_clr_attr}G", f"{clr_side_condition}.colorIfTrueG")
    cmds.connectAttr(f"{obj}.{r_clr_attr}B", f"{clr_side_condition}.colorIfTrueB")
    l_clr_attr = "colorLeft"
    add_attr_double_three(obj, l_clr_attr, keyable=False)
    cmds.setAttr(f"{obj}.{l_clr_attr}R", clr_right[0])
    cmds.setAttr(f"{obj}.{l_clr_attr}G", clr_right[1])
    cmds.setAttr(f"{obj}.{l_clr_attr}B", clr_right[2])
    cmds.connectAttr(f"{obj}.{l_clr_attr}R", f"{clr_side_condition}.colorIfFalseR")
    cmds.connectAttr(f"{obj}.{l_clr_attr}G", f"{clr_side_condition}.colorIfFalseG")
    cmds.connectAttr(f"{obj}.{l_clr_attr}B", f"{clr_side_condition}.colorIfFalseB")


def get_directional_color(object_name, axis="X",
                          negative_color=ColorConstants.RigControl.RIGHT,
                          center_color=ColorConstants.RigControl.CENTER,
                          positive_color=ColorConstants.RigControl.LEFT,
                          tolerance=0.001):  # Add the new tolerance argument with a default value
    """
    Retrieves the color based on the world position along a specified axis for the given object.

    Args:
        object_name (str): The name of the object whose position color needs to be determined.
        axis (str, optional): The axis along which to evaluate the object's position ('X', 'Y', or 'Z'). Defaults to 'X'.
        negative_color: The color constant representing the color for negative position values.
                        Defaults to ColorConstants.RigControl.LEFT.
        center_color: The color constant representing the color for position values equal to zero.
                      Defaults to ColorConstants.RigControl.CENTER.
        positive_color: The color constant representing the color for positive position values.
                        Defaults to ColorConstants.RigControl.RIGHT.
        tolerance (float, optional): Tolerance value to determine if the position is close enough to zero.
                                      Defaults to 1e-6.

    Returns:
        ColorConstant: The color constant corresponding to the object's position along the specified axis.
    """
    if not object_name or not cmds.objExists(object_name):
        logger.warning(f"Object '{str(object_name)}' does not exist.")
        return

    axis = axis.upper()
    if axis not in ["X", "Y", "Z"]:
        logger.warning(f"Invalid axis '{axis}'. Please use 'X', 'Y', or 'Z'.")
        return

    # Get the world position of the object
    world_position = cmds.xform(object_name, q=True, ws=True, translation=True)

    # Get the value along the specified axis
    position_value = world_position["XYZ" .index(axis)]

    # Determine the color based on the position value
    if position_value < -tolerance:
        color = negative_color
    elif position_value > tolerance:
        color = positive_color
    else:
        color = center_color

    return color


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    out = get_directional_color("pSphere1")
    print(out)
