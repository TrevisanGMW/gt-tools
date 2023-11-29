"""
Auto Rigger Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.attr_utils import add_separator_attr, hide_lock_default_attrs, connect_attr, add_attr, set_attr
from gt.utils.color_utils import set_color_viewport, ColorConstants, set_color_outliner
from gt.utils.curve_utils import get_curve, set_curve_width, create_connection_line
from gt.utils.uuid_utils import get_object_from_uuid_attr
from gt.utils.naming_utils import NamingConstants
from gt.utils.attr_utils import set_attr_state
from gt.utils import hierarchy_utils
from gt.utils.node_utils import Node
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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

# ------------------------------------------ Lookup functions ------------------------------------------
def find_proxy_from_uuid(uuid_string):
    """
    Return a proxy if the provided UUID is present in the attribute RiggerConstants.PROXY_ATTR_UUID
    Args:
        uuid_string (str): UUID to look for (if it matches, then the proxy is found)
    Returns:
        str or None: If found, the proxy with the matching UUID, otherwise None
    """
    proxy = get_object_from_uuid_attr(uuid_string=uuid_string,
                                      attr_name=RiggerConstants.PROXY_ATTR_UUID,
                                      obj_type="transform")
    return proxy


def find_proxy_node_from_uuid(uuid_string):
    """
    Returns the found proxy as a "Node" object (gt.utils.node_utils)
    Args:
        uuid_string (str): UUID to look for (if it matches, then the proxy is found)
    Returns:
        Node or None: If found, the proxy (as a Node) with the matching UUID, otherwise None
    """
    proxy = find_proxy_from_uuid(uuid_string)
    if proxy:
        return Node(proxy)


def find_joint_from_uuid(uuid_string):
    """
    Return a joint if the provided UUID is present in the attribute RiggerConstants.JOINT_ATTR_UUID
    Args:
        uuid_string (str): UUID to look for (if it matches, then the joint is found)
    Returns:
        str or None: If found, the joint with the matching UUID, otherwise None
    """
    proxy = get_object_from_uuid_attr(uuid_string=uuid_string,
                                      attr_name=RiggerConstants.JOINT_ATTR_UUID,
                                      obj_type="joint")
    return proxy


def find_joint_node_from_uuid(uuid_string):
    """
    Returns the found joint as a "Node" object (gt.utils.node_utils)
    Args:
        uuid_string (str): UUID to look for (if it matches, then the joint is found)
    Returns:
        Node or None: If found, the joint (as a Node) with the matching UUID, otherwise None
    """
    proxy = find_joint_from_uuid(uuid_string)
    if proxy:
        return Node(proxy)


def find_objects_with_attr(attr_name, obj_type="transform", transform_lookup=True):
    """
    Return object if provided UUID is present in it
    Args:
        attr_name (string): Name of the attribute where the UUID is stored.
        obj_type (str, optional): Type of objects to look for (default is "transform")
        transform_lookup (bool, optional): When not a transform, it checks the item parent instead of the item itself.
    Returns:
        str, None: If found, the object with a matching UUID, otherwise None
    """
    obj_list = cmds.ls(typ=obj_type, long=True) or []
    for obj in obj_list:
        if transform_lookup and obj_type != "transform":
            _parent = cmds.listRelatives(obj, parent=True, fullPath=True) or []
            if _parent:
                obj = _parent[0]
        if cmds.objExists(f'{obj}.{attr_name}'):
            return Node(obj)


def find_proxy_root_group_node():
    """
    Looks for the proxy root transform (group) by searching for objects containing the expected attribute.
    Not to be confused with the root curve. This is the parent TRANSFORM.
    """
    return find_objects_with_attr(RiggerConstants.REF_ROOT_PROXY_ATTR, obj_type="transform")


def find_rig_root_group_node():
    """
    Looks for the rig root transform (group) by searching for objects containing the expected attribute.
    Not to be confused with the root control curve. This is the parent TRANSFORM.
    """
    return find_objects_with_attr(RiggerConstants.REF_ROOT_RIG_ATTR, obj_type="transform")


def find_control_root_curve_node(use_transform=False):
    """
    Looks for the control root curve by searching for objects containing the expected attribute.
    Args:
        use_transform (bool, optional): If active, it will use the type transform to look for the object.
                                        This can potentially make the operation less efficient, but will
                                        run a more complete search as it will include curves that had
                                        their shapes deleted.
    """
    obj_type = "nurbsCurve"
    if use_transform:
        obj_type = "transform"
    return find_objects_with_attr(RiggerConstants.REF_ROOT_CONTROL_ATTR, obj_type=obj_type)


def find_proxy_root_curve_node(use_transform=False):
    """
    Looks for the proxy root curve by searching for objects containing the expected attribute.
    Args:
        use_transform (bool, optional): If active, it will use the type transform to look for the object.
                                        This can potentially make the operation less efficient, but will
                                        run a more complete search as it will include curves that had
                                        their shapes deleted.
    """
    obj_type = "nurbsCurve"
    if use_transform:
        obj_type = "transform"
    return find_objects_with_attr(RiggerConstants.REF_ROOT_PROXY_ATTR, obj_type=obj_type)


def find_skeleton_group():
    """
    Looks for the rig skeleton transform (group) by searching for objects containing the expected attribute.
    """
    return find_objects_with_attr(RiggerConstants.REF_SKELETON_ATTR, obj_type="transform")


def find_vis_lines_from_uuid(parent_uuid=None, child_uuid=None):
    """
    Looks for a visualization line containing the parent or the child uuid.
    Args:
        parent_uuid (str, optional): The UUID of the parent proxy.
        child_uuid (str, optional): The UUID of the child proxy.
    Returns:
        tuple: A tuple of detected lines containing the requested parent or child uuids. Empty tuple otherwise.
    """
    # Try the group first to save time.
    lines_grp = find_objects_with_attr(attr_name=RiggerConstants.REF_LINES_ATTR)
    _lines = set()
    if lines_grp:
        _children = cmds.listRelatives(str(lines_grp), children=True, fullPath=True) or []
        for child in _children:
            if not cmds.objExists(f'{child}.{RiggerConstants.LINE_ATTR_PARENT_UUID}'):
                continue
            if parent_uuid:
                existing_uuid = cmds.getAttr(f'{child}.{RiggerConstants.LINE_ATTR_PARENT_UUID}')
                if existing_uuid == parent_uuid:
                    _lines.add(Node(child))
            if child_uuid:
                existing_uuid = cmds.getAttr(f'{child}.{RiggerConstants.LINE_ATTR_CHILD_UUID}')
                if existing_uuid == child_uuid:
                    _lines.add(Node(child))
    if _lines:
        return tuple(_lines)
    # If nothing was found, look through all transforms - Less optimized
    obj_list = cmds.ls(typ="nurbsCurve", long=True) or []
    valid_items = set()
    for obj in obj_list:
        _parent = cmds.listRelatives(obj, parent=True, fullPath=True) or []
        if _parent:
            obj = _parent[0]
        if cmds.objExists(f'{obj}.{RiggerConstants.LINE_ATTR_PARENT_UUID}'):
            valid_items.add(Node(obj))
    for item in valid_items:
        if parent_uuid:
            existing_uuid = cmds.getAttr(f'{item}.{RiggerConstants.LINE_ATTR_PARENT_UUID}')
            if existing_uuid == parent_uuid:
                _lines.add(Node(child))
        if child_uuid:
            existing_uuid = cmds.getAttr(f'{item}.{RiggerConstants.LINE_ATTR_CHILD_UUID}')
            if existing_uuid == child_uuid:
                _lines.add(Node(child))
    return tuple(_lines)

# ------------------------------------------ Create functions ------------------------------------------
def create_proxy_visualization_lines(proxy_list, lines_parent=None):
    """
    Creates visualization lines according to the proxy UUID parent attribute.
    If a proxy meta parent is found, this is used instead.
    Args:
        proxy_list (list): A list of Proxy objects to be parented.
                           UUID and parent UUID fields are required for the operation.
                           Objects without it will be ignored.
        lines_parent (str, optional): If provided, it will automatically parent all generated elements to this object.
                                      Must exist and allow objects to be parented to it. e.g. "pSphere1"
    Returns:
        list: List of generated elements.
    """
    for proxy in proxy_list:
        built_proxy = find_proxy_from_uuid(proxy.get_uuid())
        parent_proxy = find_proxy_from_uuid(proxy.get_parent_uuid())

        # Check for Meta Parent - OVERWRITES parent!
        metadata = proxy.get_metadata()
        if metadata:
            meta_parent = metadata.get(RiggerConstants.PROXY_META_PARENT, None)
            if meta_parent:
                parent_proxy = find_proxy_from_uuid(meta_parent)

        # Create Line
        if built_proxy and parent_proxy and cmds.objExists(built_proxy) and cmds.objExists(parent_proxy):
            try:
                line_objects = create_connection_line(object_a=built_proxy,
                                                      object_b=parent_proxy) or []
                if lines_parent and cmds.objExists(lines_parent):
                    hierarchy_utils.parent(source_objects=line_objects, target_parent=lines_parent) or []
                if line_objects:
                    line_crv = line_objects[0]
                    add_attr(target_list=line_crv,
                             attributes=RiggerConstants.LINE_ATTR_CHILD_UUID,
                             attr_type="string")
                    set_attr(attribute_path=f'{line_crv}.{RiggerConstants.LINE_ATTR_CHILD_UUID}',
                             value=proxy.get_uuid())
                    add_attr(target_list=line_crv,
                             attributes=RiggerConstants.LINE_ATTR_PARENT_UUID,
                             attr_type="string")
                    set_attr(attribute_path=f'{line_crv}.{RiggerConstants.LINE_ATTR_PARENT_UUID}',
                             value=proxy.get_parent_uuid())
            except Exception as e:
                logger.debug(f'Failed to create visualization line. Issue: {str(e)}')


def create_root_curve(name="root"):
    """
    Creates a circle/arrow curve to be used as the root of a control rig or a proxy guide
    Args:
        name (str, optional): Name of the curve transform
    Returns:
        Node, str: A Node containing the generated root curve
    """
    selection = cmds.ls(selection=True)
    root_crv = get_curve('_rig_root')
    root_crv.set_name(name=name)
    root_transform = root_crv.build()
    connect_attr(source_attr=f'{root_transform}.sy',
                 target_attr_list=[f'{root_transform}.sx', f'{root_transform}.sz'])
    set_attr_state(obj_list=root_transform, attr_list=['sx', 'sz'], hidden=True)
    set_color_viewport(obj_list=root_transform, rgb_color=ColorConstants.RigProxy.CENTER)
    cmds.select(clear=True)
    if selection:
        try:
            cmds.select(selection=True)
        except Exception as e:
            logger.debug(f'Unable to restore initial selection. Issue: {str(e)}')
    return Node(root_transform)


def create_root_group(is_proxy=False):
    """
    Creates a group to be used as the root of the current setup (rig or proxy)
    Args:
        is_proxy (bool, optional): If True, it will create the proxy group, instead of the main rig group
    """
    _name = RiggerConstants.GRP_RIG_NAME
    _attr = RiggerConstants.REF_ROOT_RIG_ATTR
    _color = ColorConstants.RigOutliner.GRP_ROOT_RIG
    if is_proxy:
        _name = RiggerConstants.GRP_PROXY_NAME
        _attr = RiggerConstants.REF_ROOT_PROXY_ATTR
        _color = ColorConstants.RigOutliner.GRP_ROOT_PROXY
    root_group = cmds.group(name=_name, empty=True, world=True)
    root_group = Node(root_group)
    hide_lock_default_attrs(obj=root_group)
    add_attr(target_list=root_group, attr_type="string", is_keyable=False,
             attributes=_attr, verbose=True)
    set_color_outliner(root_group, rgb_color=_color)
    return Node(root_group)


def create_proxy_root_curve():
    """
    Creates a curve to be used as the root of a proxy skeleton
    Returns:
        Node, str: A Node containing the generated root curve
    """
    root_transform = create_root_curve(name="root_proxy")
    hide_lock_default_attrs(obj=root_transform, scale=False)
    add_separator_attr(target_object=root_transform, attr_name=f'proxy{RiggerConstants.SEPARATOR_STD_SUFFIX}')
    add_attr(target_list=root_transform, attr_type="string", is_keyable=False,
             attributes=RiggerConstants.REF_ROOT_PROXY_ATTR, verbose=True)

    set_curve_width(obj_list=root_transform, line_width=2)
    return Node(root_transform)


def create_control_root_curve():
    """
    Creates a curve to be used as the root of a control rig skeleton
    Returns:
        Node, str: A Node containing the generated root curve
    """
    root_transform = create_root_curve(name=f'root_{NamingConstants.Suffix.CTRL}')
    add_separator_attr(target_object=root_transform, attr_name=f'rig{RiggerConstants.SEPARATOR_STD_SUFFIX}')
    add_attr(target_list=root_transform, attr_type="string", is_keyable=False,
             attributes=RiggerConstants.REF_ROOT_CONTROL_ATTR, verbose=True)
    set_curve_width(obj_list=root_transform, line_width=3)
    set_color_viewport(obj_list=root_transform, rgb_color=ColorConstants.RigControl.ROOT)
    return Node(root_transform)


def create_direction_curve():
    """
    Creates a curve to be used as the root of a control rig skeleton
    Returns:
        Node, str: A Node containing the generated root curve
    """
    direction_ctrl = cmds.circle(name=f'direction_{NamingConstants.Suffix.CTRL}',
                                 nr=(0, 1, 0), ch=False, radius=44.5)[0]
    add_separator_attr(target_object=direction_ctrl, attr_name=f'rig{RiggerConstants.SEPARATOR_STD_SUFFIX}')
    add_attr(target_list=direction_ctrl, attr_type="string", is_keyable=False,
             attributes=RiggerConstants.REF_DIR_CURVE_ATTR, verbose=True)
    set_color_viewport(obj_list=direction_ctrl, rgb_color=ColorConstants.RigControl.CENTER)
    return Node(direction_ctrl)


def create_utility_groups(geometry=False, skeleton=False, control=False,
                          setup=False, line=False, target_parent=None):
    """
    Creates category groups for the rig.
    This group holds invisible rigging elements used in the automation of the project.
    Args:
        geometry (bool, optional): If True, the geometry group is created.
        skeleton (bool, optional): If True, the skeleton group is created.
        control (bool, optional): If True, the control group is created.
        setup (bool, optional): If True, the setup group is created.
        line (bool, optional): If True, the visualization line group is created.
        target_parent (str, Node, optional): If provided, groups will be parented to this object after creation.
    Returns:
        dict: A dictionary with lookup attributes (RiggerConstants) as keys and "Node" objects as values.
              e.g. {RiggerConstants.REF_GEOMETRY_ATTR: Node("group_name")}
    """
    desired_groups = {}
    if geometry:
        _name = RiggerConstants.GRP_GEOMETRY_NAME
        _color = ColorConstants.RigOutliner.GRP_GEOMETRY
        desired_groups[RiggerConstants.REF_GEOMETRY_ATTR] = (_name, _color)
    if skeleton:
        _name = RiggerConstants.GRP_SKELETON_NAME
        _color = ColorConstants.RigOutliner.GRP_SKELETON
        desired_groups[RiggerConstants.REF_SKELETON_ATTR] = (_name, _color)
    if control:
        _name = RiggerConstants.GRP_CONTROL_NAME
        _color = ColorConstants.RigOutliner.GRP_CONTROL
        desired_groups[RiggerConstants.REF_CONTROL_ATTR] = (_name, _color)
    if setup:
        _name = RiggerConstants.GRP_SETUP_NAME
        _color = ColorConstants.RigOutliner.GRP_SETUP
        desired_groups[RiggerConstants.REF_SETUP_ATTR] = (_name, _color)
    if line:
        _name = RiggerConstants.GRP_LINE_NAME
        _color = None
        desired_groups[RiggerConstants.REF_LINES_ATTR] = (_name, _color)

    group_dict = {}
    for attr, (name, color) in desired_groups.items():
        group = cmds.group(name=name, empty=True, world=True)
        add_attr(target_list=group, attr_type="string", is_keyable=False,
                 attributes=attr, verbose=True)
        _node = Node(group)
        group_dict[attr] = _node
        if color:
            set_color_outliner(str(_node), rgb_color=color)
        if target_parent:
            hierarchy_utils.parent(source_objects=_node, target_parent=str(target_parent))
    return group_dict

# ------------------------------------------ Misc functions ------------------------------------------
def parent_proxies(proxy_list):
    """
    Parent proxy elements (and their offset groups) according to their parent UUID
    Args:
        proxy_list (list): A list of Proxy objects to be parented.
                           UUID and parent UUID fields are required for the operation.
                           Objects without it will be ignored.
    """
    # Parent Joints
    for proxy in proxy_list:
        built_proxy = find_proxy_from_uuid(proxy.get_uuid())
        parent_proxy = find_proxy_from_uuid(proxy.get_parent_uuid())
        if built_proxy and parent_proxy and cmds.objExists(built_proxy) and cmds.objExists(parent_proxy):
            offset = cmds.listRelatives(built_proxy, parent=True, fullPath=True)
            if offset:
                hierarchy_utils.parent(source_objects=offset, target_parent=parent_proxy)


def get_proxy_offset(proxy_name):
    """
    Return the offset transform (parent) of the provided proxy object. If not found, it returns "None"
    Args:
        proxy_name (string): Name of the attribute where the UUID is stored.
    Returns:
        str, None: If found, the offset object (parent of the proxy), otherwise None
    """
    if not proxy_name or not cmds.objExists(proxy_name):
        logger.debug(f'Unable to find offset for "{str(proxy_name)}".')
        return
    offset_list = cmds.listRelatives(proxy_name, parent=True, typ="transform", fullPath=True) or []
    for offset in offset_list:
        return offset


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    # cmds.file(new=True, force=True)
    # create_proxy_root_curve()
    # cmds.viewFit(all=True)
    # out = create_utility_groups(geometry=True, skeleton=True, setup=True, control=True,
    #                             target_parent="rigger_proxy_grp")
    print(find_control_root_curve_node())