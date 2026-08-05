"""
Naming module

Import Line:
    import gt.core.naming as core_naming
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
        OFFSET_DATA = "offsetData"
        PIVOT = "pivot"
        FK = "fk"  # Forward kinematics
        IK = "ik"  # Inverse kinematics
        DATA = "data"
        DATA_QUERY = "dataQuery"
        RIBBON = "ribbon"
        END = "end"

    class Prefix:
        LEFT = "L"
        RIGHT = "R"
        CENTER = "C"
        MAT = "M"  # Material

    class Suffix:
        # Main Elements
        CTRL = "CTRL"  # Control
        JNT = "JNT"  # Joint
        END = "END"  # Last object in a hierarchy
        # Auxiliary Elements
        GRP = "grp"  # Group
        CRV = "crv"  # Curve
        LOC = "loc"  # Locator
        SUR = "sur"  # Surface
        OFFSET = "offset"  # Offset Transform (control parent)
        PROXY = "proxy"  # Intermediary or placeholder for another object
        DRIVEN = "driven"  # Is controlled by something (driven)
        DRIVER = "driver"  # Controls something (driver)
        IK_HANDLE_SC = "ikSC"  # Single-Chain Solver
        IK_HANDLE_RP = "ikRP"  # Rotate-Plane Solver
        IK_HANDLE_SPRING = "ikSpring"  # Spring Solver
        LINE = "line"  # Connection lines

    class Control:
        """
        Control suffixes are distinct from those in the "Suffix" category to ensure simplicity.
        Suffixes used by controls are usually more intricate, potentially diminishing code completion efficiency.
        """

        _CTRL = "CTRL"
        _DATA = "DATA"
        OFFSET = f"Offset"  # Offset control of an existing control
        OFFSET_DATA = f"offset_{_DATA}"  # Offset data from an offset control
        # SWITCH = "Switch"  # Influence Switch Control (A-B System)
        IK = "IK"  # IK description that can be use for the control name

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

    class Poses:
        APOSE = "apose"
        TPOSE = "tpose"
        NPOSE = "npose"


def get_long_name(short_name, absolute=False):
    """
    Returns the long name of the object based on its short name.

    Args:
        short_name (str): The short name of the object.
        absolute (bool): cmds.ls absoluteName option.
                         The absolute name of the namespace is a full namespace path,
                         starting from the root namespace ":" and including all parent namespaces.
                         For example ":ns:ball" is an absolute namespace name while "ns:ball" is not.
                         The absolute namespace name is invariant and is not affected by the current
                         namespace or relative namespace modes.
    Returns:
        str: The long name of the object.
    """
    try:
        long_name = cmds.ls(short_name, long=True, absoluteName=absolute)[0]
        return long_name
    except (IndexError, RuntimeError) as e:
        logger.debug(f"Unable to retrieve long name. Issue: {str(e)}")
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
    output_short_name = ""
    if long_name == "":
        return ""
    split_path = str(long_name).split("|")
    if len(split_path) >= 1:
        output_short_name = split_path[len(split_path) - 1]
    if remove_namespace:
        output_short_name = output_short_name.split(":")[-1]
    return output_short_name


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
