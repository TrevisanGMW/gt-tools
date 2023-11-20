"""
Naming Utilities
github.com/TrevisanGMW/gt-tools
"""
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class NamingConstants:
    def __init__(self):
        """
        Naming Constants. Must be a string.
        These are expected naming strings, such as prefixes, suffixes or anything that will help describe an object.
        Default naming convention:
            <side>_<position>_<description><sequence>_<type>
            <side> : Initial side of the element. e.g. "left", "right", "center" (usually X+ vs X-)
            <position> : Position of the element. e.g. "mid", "upper", "lower"...
            <description> : camelCase description of the object. e.g. "circleDirection"
            <sequence> : multiple objects with the same name, may include a number or letter. e.g. "01" or "B"
            <type> : object type (what it represents in the scene) e.g. "jnt" for joint or "grp" for group.
            e.g. "lf_mid_eyebrow01_jnt", "cn_hip_jnt", "cn_jaw_jnt"
        """
    class Prefix:
        # Prefixes
        LEFT = "lf"
        RIGHT = "rt"
        CENTER = "cn"

    class Suffix:
        # Suffixes
        END = "end"  # Last object in a hierarchy
        CTRL = 'ctrl'  # Control
        CRV = 'crv'  # Curve
        GRP = 'grp'  # Group
        JNT = 'jnt'  # Joint
        MAT = 'mat'  # Material
        LOC = 'loc'  # Locator
        OFFSET = 'offset'  # Offset Transform
        PROXY = 'proxy'
        IK_HANDLE_SC = "ikSC"
        IK_HANDLE_RP = "ikRP"
        IK_HANDLE_SPRING = "ikSpring"

    class Position:
        MID = "mid"  # - center (other positions go clockwise starting at 12 o'clock)
        UPPER = "upper"  # ^
        INNER_UP = "inUp"  # >^
        INNER = "inner"  # >
        INNER_LO = "inLo"  # >v
        LOWER = "lower"  # v
        OUTER_LO = "outLo"  # <v
        OUTER = "outer"  # <
        OUTER_UP = "outUp"  # <^

    class Description:
        OFFSET = "offset"
        PIVOT = "pivot"


def get_long_name(short_name):
    """
    Returns the long name of the object based on its short name.

    Args:
        short_name (str): The short name of the object.

    Returns:
        str: The long name of the object.
    """
    try:
        long_name = cmds.ls(short_name, long=True)[0]
        return long_name
    except (IndexError, RuntimeError) as e:
        logger.debug(f'Unable to retrieve long name. Issue: {str(e)}')
    return None


def get_short_name(long_name, remove_namespace=False):
    """
    Get the name of the objects without its path (Maya returns full path if name is not unique)
    e.g. "|group|item" returns "item".

    Args:
        long_name (str): Object to extract short name.
        remove_namespace (bool, optional): If True, it will also remove namespaces from the short name.
                                           e.g. "|group|ns:item" returns "item".
    Returns:
        str: Short name for the provided object.
    """
    output_short_name = ''
    if long_name == '':
        return ''
    split_path = long_name.split('|')
    if len(split_path) >= 1:
        output_short_name = split_path[len(split_path) - 1]
    if remove_namespace:
        output_short_name = output_short_name.split(":")[-1]
    return output_short_name


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
