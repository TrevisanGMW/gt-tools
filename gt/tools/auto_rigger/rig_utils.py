"""
Auto Rigger Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.attr_utils import add_separator_attr, hide_lock_default_attrs, connect_attr, add_attr
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
    JOINT_ATTR_UUID = "jointUUID"
    PROXY_ATTR_UUID = "proxyUUID"
    PROXY_ATTR_SCALE = "locatorScale"
    PROXY_META_PARENT = "metaParentUUID"  # Metadata key, may be different from actual parent (e.g. for lines)
    PROXY_META_TYPE = "proxyType"  # Metadata key, used to recognize rigged proxies within modules
    PROXY_CLR = "color"  # Metadata key, describes color to be used instead of side setup.
    # Separator Attributes
    SEPARATOR_STD_SUFFIX = "Options"  # Standard (Std) Separator attribute name (a.k.a. header attribute)
    SEPARATOR_BEHAVIOR = "Behavior"
    # Group Names
    GRP_GEOMETRY_NAME = f'geometry_{NamingConstants.Suffix.GRP}'
    GRP_SKELETON_NAME = f'skeleton_{NamingConstants.Suffix.GRP}'
    GRP_CONTROL_NAME = f'control_{NamingConstants.Suffix.GRP}'
    GRP_SETUP_NAME = f'setup_{NamingConstants.Suffix.GRP}'
    # Reference Attributes
    REF_ROOT_RIG_ATTR = "rigRootLookupAttr"
    REF_ROOT_PROXY_ATTR = "proxyRootLookupAttr"
    REF_ROOT_CONTROL_ATTR = "controlRootLookupAttr"
    REF_GEOMETRY_ATTR = "geometryLookupAttr"
    REF_SKELETON_ATTR = "skeletonLookupAttr"
    REF_CONTROL_ATTR = "controlLookupAttr"
    REF_SETUP_ATTR = "setupLookupAttr"


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
    result_list = set()
    for obj in obj_list:
        if transform_lookup and obj_type != "transform":
            _parent = cmds.listRelatives(obj, parent=True, fullPath=True) or []
            if _parent:
                obj = _parent[0]
        if cmds.objExists(f'{obj}.{attr_name}'):
            result_list.add(obj)
    return list(result_list)


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


def find_rig_root_transform_node():
    """
    Looks for the rig transform (group) by searching for objects containing the expected attribute.
    """
    return find_objects_with_attr(RiggerConstants.REF_ROOT_RIG_ATTR, obj_type="transform")


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
        generated_objects = []
        if built_proxy and parent_proxy and cmds.objExists(built_proxy) and cmds.objExists(parent_proxy):
            try:
                line_objects = create_connection_line(object_a=built_proxy,
                                                      object_b=parent_proxy) or []
                if lines_parent and cmds.objExists(lines_parent):
                    generated_objects += hierarchy_utils.parent(source_objects=line_objects,
                                                                target_parent=lines_parent) or []
                else:
                    generated_objects += line_objects
            except Exception as e:
                logger.debug(f'Failed to create visualization line. Issue: {str(e)}')


def create_root_curve(name="root", group_name="root"):
    """
    Creates a circle/arrow curve to be used as the root of a control rig or a proxy guide
    Args:
        name (str, optional): Name of the curve transform
        group_name (str, optional): Name of the parent group (transform) of the curve
    Returns:
        tuple: A tuple with the name of the curve transform and the name of the parent group
    """
    selection = cmds.ls(selection=True)
    root_crv = get_curve('_rig_root')
    root_crv.set_name(name=name)
    root_transform = root_crv.build()
    root_grp = cmds.group(empty=True, world=True, name=f"{group_name}_{NamingConstants.Suffix.GRP}")
    hide_lock_default_attrs(obj=root_grp)
    connect_attr(source_attr=f'{root_transform}.sy', target_attr_list=[f'{root_transform}.sx', f'{root_transform}.sz'])
    set_attr_state(obj_list=root_transform, attr_list=['sx', 'sz'], hidden=True)
    set_color_viewport(obj_list=root_transform, rgb_color=ColorConstants.RigProxy.CENTER)
    cmds.parent(root_transform, root_grp)
    cmds.select(clear=True)
    if selection:
        try:
            cmds.select(selection=True)
        except Exception as e:
            logger.debug(f'Unable to restore initial selection. Issue: {str(e)}')
    return root_transform, root_grp


def create_proxy_root_curve():
    """
    Creates a curve to be used as the root of a proxy skeleton
    Returns:
        tuple: A tuple with the name of the curve transform and the name of the parent group
    """
    root_transform, root_group = create_root_curve(name="root", group_name="rigger_proxy")
    hide_lock_default_attrs(obj=root_transform, scale=False)
    add_separator_attr(target_object=root_transform, attr_name=f'proxy{RiggerConstants.SEPARATOR_STD_SUFFIX}')
    add_attr(target_list=root_transform, attr_type="string", is_keyable=False,
             attributes=RiggerConstants.REF_ROOT_CONTROL_ATTR, verbose=True)
    add_attr(target_list=root_group, attr_type="string", is_keyable=False,
             attributes=RiggerConstants.REF_ROOT_PROXY_ATTR, verbose=True)
    set_curve_width(obj_list=root_transform, line_width=2)
    return root_transform, root_group


def create_control_root_curve():
    """
    Creates a curve to be used as the root of a control rig skeleton
    Returns:
        tuple: A tuple with the name of the curve transform and the name of the parent group
    """
    root_transform, root_group = create_root_curve(name="root_ctrl", group_name="rig")
    add_separator_attr(target_object=root_transform, attr_name=f'rig{RiggerConstants.SEPARATOR_STD_SUFFIX}')
    add_attr(target_list=root_transform, attr_type="string", is_keyable=False,
             attributes=RiggerConstants.REF_ROOT_RIG_ATTR, verbose=True)
    set_curve_width(obj_list=root_transform, line_width=3)
    set_color_viewport(obj_list=root_transform, rgb_color=ColorConstants.RigControl.ROOT)
    return root_transform, root_group


def create_category_groups(geometry=False, skeleton=False, control=False, setup=False, target_parent=None):
    """
    Creates category groups for the rig.
    This group holds invisible rigging elements used in the automation of the project.
    Args:
        geometry (bool, optional): If True, the geometry group is created.
        skeleton (bool, optional): If True, the skeleton group is created.
        control (bool, optional): If True, the control group is created.
        setup (bool, optional): If True, the setup group is created.
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
    out = create_category_groups(geometry=True, skeleton=True, setup=True, control=True, target_parent="rigger_proxy_grp")
