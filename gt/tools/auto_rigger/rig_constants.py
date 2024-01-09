"""
Auto Rigger Constants
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.naming_utils import NamingConstants


class RiggerConstants:
    def __init__(self):
        """
        Constant values used by the auto rigging system.
        e.g. Attribute names, dictionary keys or initial values.
        """
    # General Keys and Attributes
    PROJECT_EXTENSION = "rig"
    FILE_FILTER = f"Rig Project (*.{PROJECT_EXTENSION});;"
    # System Attributes
    ATTR_JOINT_UUID = "jointUUID"
    ATTR_MODULE_UUID = "moduleUUID"
    ATTR_PROXY_UUID = "proxyUUID"
    ATTR_DRIVER_UUID = "driverUUID"
    ATTR_JOINT_DRIVEN_UUID = "jointDrivenUUID"
    # Misc Attributes
    ATTR_PROXY_SCALE = "locatorScale"
    ATTR_LINE_CHILD_UUID = "lineProxySourceUUID"  # Used by the proxy lines to store source
    ATTR_LINE_PARENT_UUID = "lineProxyTargetUUID"  # Used by the proxy lines to store target
    # Metadata Keys
    META_PROXY_LINE_PARENT = "lineParentUUID"  # Metadata key, line parent. Actual parent is ignored when present.
    META_PROXY_PURPOSE = "proxyPurpose"  # Metadata key, used to recognize proxy purpose within modules
    META_PROXY_DRIVERS = "proxyDrivers"  # Metadata key, used to find drivers (aka controls) driving the created joint
    META_PROXY_CLR = "color"  # Metadata key, describes color to be used instead of side setup.
    # Separator Attributes
    SEPARATOR_STD_SUFFIX = "Options"  # Standard (Std) Separator attribute name (a.k.a. header attribute)
    SEPARATOR_BEHAVIOR = "Behavior"
    # Group Names
    GRP_RIG_NAME = f'rig_{NamingConstants.Suffix.GRP}'
    GRP_PROXY_NAME = f'rig_proxy_{NamingConstants.Suffix.GRP}'
    GRP_GEOMETRY_NAME = f'geometry_{NamingConstants.Suffix.GRP}'
    GRP_SKELETON_NAME = f'skeleton_{NamingConstants.Suffix.GRP}'
    GRP_CONTROL_NAME = f'control_{NamingConstants.Suffix.GRP}'
    GRP_SETUP_NAME = f'setup_{NamingConstants.Suffix.GRP}'
    GRP_LINE_NAME = f'visualization_lines'
    # Reference Attributes
    REF_ATTR_ROOT_RIG = "rootRigLookupAttr"
    REF_ATTR_ROOT_PROXY = "rootProxyLookupAttr"
    REF_ATTR_ROOT_CONTROL = "rootControlLookupAttr"
    REF_ATTR_DIR_CURVE = "dirCrvLookupAttr"
    REF_ATTR_GEOMETRY = "geometryGroupLookupAttr"
    REF_ATTR_SKELETON = "skeletonGroupLookupAttr"
    REF_ATTR_CONTROL = "controlGroupLookupAttr"
    REF_ATTR_SETUP = "setupGroupLookupAttr"
    REF_ATTR_LINES = "linesGroupLookupAttr"
    # Multipliers
    LOC_RADIUS_MULTIPLIER_DRIVEN = .8
    LOC_RADIUS_MULTIPLIER_FK = .3
    LOC_RADIUS_MULTIPLIER_IK = .6


class RiggerDriverTypes:
    def __init__(self):
        """
        Driver Type Constant values used by the drivers and controls.
        """
    FK = "fk"
    IK = "ik"
    OFFSET = "offset"
