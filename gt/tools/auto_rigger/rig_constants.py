"""
Auto Rigger Constants

Import Line:
    import gt.tools.auto_rigger.rig_constants as tools_rig_const
"""

class RiggerConstants:
    def __init__(self):
        """
        Constant values used by the auto rigging system.
        e.g. Attribute names, dictionary keys or initial values.
        """

    # General Keys and Attributes
    PROJECT_EXTENSION = "rig"
    PROJECT_FILE_FILTER = f"Rig Project (*.{PROJECT_EXTENSION});;"
    MODULE_FILE_FILTER = f"Rig Module (*.{PROJECT_EXTENSION});;"
    MAYA_FILE_FILTER = f"Maya Files (*.ma *.mb);;"
    # Preferences
    PREFS_FILENAME = "auto_rigger"
    PREFS_KEY_ON_BUILD_SHOW_LOG = "on_build_show_log"
    PREFS_KEY_ON_BUILD_CLEAR_LOG = "on_build_clear_log"
    PREFS_KEY_ON_SET_PATH_ABS_TO_RELATIVE = "on_set_path_abs_to_relative"
    PREFS_KEY_SHOW_PACKAGE_TEMPLATES = "show_package_templates"
    PREFS_KEY_RECENT_PROJECTS = "recent_projects"
    MAX_RECENT_PROJECTS = 5
    # Basic System Attributes
    ATTR_BASE_NAME = "baseName"
    ATTR_PREFIX = "prefix"
    ATTR_SUFFIX = "suffix"
    ATTR_JOINT_UUID = "jointUUID"
    ATTR_MODULE_UUID = "moduleUUID"
    ATTR_PROXY_UUID = "proxyUUID"
    ATTR_JOINT_DRIVEN_UUID = "jointDrivenUUID"  # Duplicated joints used in automation
    ATTR_BLOCK_SELECTION = "blockSelection"  # Duplicated joints used in automation
    # Driver System Attributes
    ATTR_DRIVER_UUID = "driverUUID"  # Driver (often controls) used to animate joints
    ATTR_DRIVER_CHILD = "driverChild"  # Auxiliary control attr that receives data from "ATTR_DRIVER_UUID"
    ATTR_JOINT_PURPOSE = "jointPurpose"  # Proxy purpose is stored in this attribute when a joint is created
    ATTR_JOINT_DRIVERS = "jointDrivers"  # List of drivers is stored in this attribute when a joint is created
    # Misc Attributes
    ATTR_PROXY_SCALE = "locatorScale"
    ATTR_ROT_ORDER = "rotationOrder"  # Determines initial rotation order. Cannot be "rotateOrder", taken by Maya
    ATTR_ROT_ORDER_IK = "rotationOrderIK"  # Used to determine the rotation order of a control (only some modules)
    ATTR_LINE_CHILD_UUID = "lineProxySourceUUID"  # Used by the proxy lines to store source
    ATTR_LINE_PARENT_UUID = "lineProxyTargetUUID"  # Used by the proxy lines to store target
    ATTR_SOURCE_LOOKUP_UUID = "sourceUUID"  # Used by any object when they need to be found in the scene.
    ATTR_SHAPE_VIS = "shapeVisibility"  # Used to expose the visibility of the shapes of a control
    ATTR_PROBE_OUTPUT = "output"  # Name of the attribute used as output for probe modules
    # Rig Root Metadata Attrs
    ATTR_RIG_PROJECT_NAME = "name"
    ATTR_RIG_PROJECT_DATA = "project"
    ATTR_RIG_GEOMETRY_GRP = "meshes"
    ATTR_RIG_SKELETON_GRP = "skeleton"
    ATTR_RIG_CONTROL_GRP = "controls"
    ATTR_RIG_SETUP_GRP = "setup"
    ATTR_RIG_COLLECTIONS = "collections"
    ATTR_RIG_TPOSE_DATA = "tPose"  # string attribute that contains the data dict about the T-pose for the rig
    ATTR_RIG_APOSE_DATA = "aPose"  # string attribute that contains the data dict about the A-pose for the rig
    ATTR_RIG_EXPORT_ANIM_BS = "exportAnimBS"  # bool attribute to include blendshapes in the anim export process
    # Metadata Keys
    META_PROXY_LINE_PARENT = "lineParentUUID"  # Metadata key, line parent. Actual parent is ignored when present
    META_PROXY_PURPOSE = "proxyPurpose"  # Metadata key, used to recognize proxy purpose within modules
    META_PROXY_DRIVERS = "proxyDrivers"  # Metadata key, used to find drivers (aka controls) driving the created joint
    META_PROXY_CLR = "color"  # Metadata key, describes color to be used instead of side setup
    # Group Names
    GRP_RIG_NAME = f"rig"
    GRP_PROXY_NAME = f"rig_proxy"
    GRP_GEOMETRY_NAME = f"geometry"
    GRP_SKELETON_NAME = f"skeleton"
    GRP_CONTROL_NAME = f"controls"
    GRP_SETUP_NAME = f"setup"
    GRP_LINE_NAME = f"visualization_lines"
    # Reference Attributes
    REF_ATTR_ROOT_RIG = "rigLookupAttr"
    REF_ATTR_ROOT_PROXY = "rootProxyLookupAttr"
    REF_ATTR_CTRL_GLOBAL_PROXY = "globalProxyCtrlLookupAttr"
    REF_ATTR_CTRL_GLOBAL = "globalCtrlLookupAttr"
    REF_ATTR_CTRL_GLOBAL_OFFSET = "globalOffsetCtrlLookupAttr"
    REF_ATTR_GEOMETRY = "geometryGroupLookupAttr"
    REF_ATTR_SKELETON = "skeletonGroupLookupAttr"
    REF_ATTR_CONTROL = "controlsGroupLookupAttr"
    REF_ATTR_SETUP = "setupGroupLookupAttr"
    REF_ATTR_LINES = "linesGroupLookupAttr"
    REF_VALUE_PURPOSE_GLOBAL = "global"  # Used to define the purpose of the global controls
    # Multipliers
    LOC_RADIUS_MULTIPLIER_DRIVEN = 0.8
    LOC_RADIUS_MULTIPLIER_FK = 0.3
    LOC_RADIUS_MULTIPLIER_IK = 0.6
    LOC_RADIUS_MULTIPLIER_DATA_QUERY = 0.1
    # Framework Vars
    CLASS_ATTR_SKIP_AUTO_SERIALIZATION = [
        "name",
        "uuid",
        "prefix",
        "suffix",
        "active",
        "code",
        "proxies",
        "orientation",
        "parent_uuid",
        "mirror_uuid",
        "module_children_drivers",
    ]


class RiggerDriverTypes:
    def __init__(self):
        """
        Driver Type Constant values used by the drivers and controls.
        """

    BLOCK = "block"  # Does not accept children and blocks the automatic creation of generic drivers.
    GENERIC = "generic"  # Any transform/control. When not found, a following group is created.
    FK = "fk"  # Forward kinematics
    IK = "ik"  # Inverse kinematics
    COG = "cog"  # Center of Gravity
    PROXY = "proxy"  # proxy objects
    PIVOT = "pivot"
    SWITCH = "switch"  # Secondary driver that allows switching between systems. e.g. FK/IK
    OFFSET = "offset"  # Driver is the data of an offset control
    AIM = "aim"  # e.g. eyes
    TWIST = "twist"  # Twist Joints
    LINE = "line"  # connection lines for the controls
