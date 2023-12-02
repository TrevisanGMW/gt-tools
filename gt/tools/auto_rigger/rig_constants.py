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
    JOINT_ATTR_UUID = "jointUUID"
    PROXY_ATTR_UUID = "proxyUUID"
    PROXY_ATTR_SCALE = "locatorScale"
    PROXY_META_PARENT = "metaParentUUID"  # Metadata key, may be different from actual parent (e.g. for lines)
    PROXY_META_TYPE = "proxyType"  # Metadata key, used to recognize rigged proxies within modules
    PROXY_CLR = "color"  # Metadata key, describes color to be used instead of side setup.
    LINE_ATTR_CHILD_UUID = "lineProxySourceUUID"  # Used by the proxy lines to store source
    LINE_ATTR_PARENT_UUID = "lineProxyTargetUUID"  # Used by the proxy lines to store target
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
    REF_ROOT_RIG_ATTR = "rootRigLookupAttr"
    REF_ROOT_PROXY_ATTR = "rootProxyLookupAttr"
    REF_ROOT_CONTROL_ATTR = "rootControlLookupAttr"
    REF_DIR_CURVE_ATTR = "dirCrvLookupAttr"
    REF_GEOMETRY_ATTR = "geometryGroupLookupAttr"
    REF_SKELETON_ATTR = "skeletonGroupLookupAttr"
    REF_CONTROL_ATTR = "controlGroupLookupAttr"
    REF_SETUP_ATTR = "setupGroupLookupAttr"
    REF_LINES_ATTR = "linesGroupLookupAttr"
