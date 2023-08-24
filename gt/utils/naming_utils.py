"""
Naming Utilities
github.com/TrevisanGMW/gt-tools
"""
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


def get_short_name(long_name):
    """
    Get the name of the objects without its path (Maya returns full path if name is not unique)

    Args:
        long_name (string) - object to extract short name
    """
    output_short_name = ''
    if long_name == '':
        return ''
    split_path = long_name.split('|')
    if len(split_path) >= 1:
        output_short_name = split_path[len(split_path) - 1]
    return output_short_name
