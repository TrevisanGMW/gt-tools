"""
Naming Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.string_utils import upper_first_char
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
            Simple:
                <side>_<description>_<type>
            Complete:
                <side>_<position><description><sequence>_<type>

            <side> : Initial side of the element. e.g. "left", "right", "center" (usually X+ vs X-)
            <position> : Position of the element. e.g. "mid", "upper", "lower"...
            <description> : camelCase description of the object. e.g. "circleDirection"
            <sequence> : multiple objects with the same name, may include a number or letter. e.g. "01" or "B"
            <type> : object type (what it represents in the scene) e.g. "jnt" for joint or "grp" for group.
            e.g.
                "rt_inner_eyelid01_ik_ctrl",
                "lf_mid_eyebrow01_jnt",
                "cn_hip_jnt",
                "cn_jaw_jnt"
        """
    class Description:
        OFFSET = 'offset'
        PIVOT = 'pivot'
        FK = 'fk'  # Forward kinematics
        IK = 'ik'  # Inverse kinematics
        DATA = 'data'
        DATA_QUERY = 'dataQuery'
        RIBBON = "ribbon"

    class Prefix:
        LEFT = 'L'
        RIGHT = 'R'
        CENTER = 'C'

    class Suffix:
        CTRL = 'ctrl'  # Control
        CRV = 'crv'  # Curve
        GRP = 'grp'  # Group
        JNT = 'jnt'  # Joint
        MAT = 'mat'  # Material
        LOC = 'loc'  # Locator
        SUR = 'sur'  # Surface
        END = 'end'  # Last object in a hierarchy
        OFFSET = 'offset'  # Offset Transform (control parent)
        # OFFSET_CTRL = 'offsetCtrl'
        # OFFSET_DATA = 'offsetData'
        PROXY = 'proxy'  # Intermediary or placeholder for another object
        DRIVEN = 'driven'  # Is controlled by something (driven)
        DRIVER = 'driver'  # Controls something (driver)
        IK_HANDLE_SC = 'ikSC'  # Single-Chain Solver
        IK_HANDLE_RP = 'ikRP'  # Rotate-Plane Solver
        IK_HANDLE_SPRING = 'ikSpring'  # Spring Solver

    class Control:
        """
        Control suffixes are distinct from those in the "Suffix" category to ensure simplicity.
        Suffixes used by controls are usually more intricate, potentially diminishing code completion efficiency.
        """
        # Common Suffixes (Private)
        _CTRL = "ctrl"
        _DATA = "data"
        OFFSET_CTRL = f'offset_{_CTRL}'  # Offset control of an existing control
        OFFSET_DATA = f'offset_{_DATA}'  # Offset data from an offset control
        # IK Suffixes
        SWITCH_CTRL = f'switch_{_CTRL}'  # Influence Switch Control (A-B System)
        IK_CTRL = f'ik_{_CTRL}'  # Same as CTRL but with an extra "ik" description
        IK_O_CTRL = f'ik_{OFFSET_CTRL}'  # Offset Control
        IK_O_DATA = f'ik_{OFFSET_DATA}'  # Offset Data
        # Automation
        ROLL_CTRL = f'roll_{_CTRL}'
        UP_DOWN_CTRL = f'upDown_{_CTRL}'
        CURL_CTRL = f'curl_{_CTRL}'
        # Pivot Manipulation
        PIVOT_CTRL = f'pivot_{_CTRL}'

    class Position:
        MID = 'mid'  # - center (other positions go clockwise starting at 12 o'clock)
        UPPER = 'upper'  # ^
        INNER_UP = 'inUp'  # >^
        INNER = 'inner'  # >
        INNER_LO = 'inLo'  # >v
        LOWER = 'lower'  # v
        OUTER_LO = 'outLo'  # <v
        OUTER = 'outer'  # <
        OUTER_UP = 'outUp'  # <^


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
    split_path = str(long_name).split('|')
    if len(split_path) >= 1:
        output_short_name = split_path[len(split_path) - 1]
    if remove_namespace:
        output_short_name = output_short_name.split(":")[-1]
    return output_short_name


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
