"""
Auto Rigger Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.attr_utils import add_separator_attr, hide_lock_default_attrs, connect_attr, add_attr, set_attr, get_attr
from gt.utils.attr_utils import set_attr_state, delete_user_defined_attrs
from gt.utils.transform_utils import get_component_positions_as_dict, set_component_positions_from_dict
from gt.utils.color_utils import set_color_viewport, ColorConstants, set_color_outliner
from gt.utils.curve_utils import get_curve, set_curve_width, create_connection_line
from gt.tools.auto_rigger.rig_constants import RiggerConstants
from gt.utils.uuid_utils import get_object_from_uuid_attr
from gt.utils.hierarchy_utils import duplicate_as_node
from gt.utils.naming_utils import NamingConstants
from gt.utils import hierarchy_utils
from gt.utils.node_utils import Node
import maya.cmds as cmds
import logging
import json


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ------------------------------------------ Lookup functions ------------------------------------------
def find_proxy_from_uuid(uuid_string):
    """
    Return a proxy if the provided UUID is present in the attribute RiggerConstants.PROXY_ATTR_UUID
    Args:
        uuid_string (str): UUID to look for (if it matches, then the proxy is found)
    Returns:
        Node or None: If found, the proxy with the matching UUID, otherwise None
    """
    proxy = get_object_from_uuid_attr(uuid_string=uuid_string,
                                      attr_name=RiggerConstants.ATTR_PROXY_UUID,
                                      obj_type="transform")
    if proxy:
        return Node(proxy)


def find_joint_from_uuid(uuid_string):
    """
    Return a joint if the provided UUID is present in the attribute RiggerConstants.JOINT_ATTR_UUID
    Args:
        uuid_string (str): UUID to look for (if it matches, then the joint is found)
    Returns:
        Node or None: If found, the joint with the matching UUID, otherwise None
    """
    joint = get_object_from_uuid_attr(uuid_string=uuid_string,
                                      attr_name=RiggerConstants.ATTR_JOINT_UUID,
                                      obj_type="joint")
    if joint:
        return Node(joint)


def find_driver_from_uuid(uuid_string):
    """
    Return a transform if the provided UUID matches the value of the attribute RiggerConstants.DRIVER_ATTR_UUID
    Args:
        uuid_string (str): UUID to look for (if it matches, then the driver is found)
    Returns:
        Node or None: If found, the joint with the matching UUID, otherwise None
    """
    driver = get_object_from_uuid_attr(uuid_string=uuid_string,
                                       attr_name=RiggerConstants.ATTR_DRIVER_UUID,
                                       obj_type="transform")
    if driver:
        return Node(driver)


def find_drivers_from_joint(source_joint, as_list=False):
    """
    Finds drivers according to the data described in the joint attributes.
    It's expected that the joint has this data available as string attributes.
    Args:
        source_joint (str, Node): The path to a joint. It's expected that this joint contains the drivers attribute.
        as_list (bool, optional): If True, it will return a list of Node objects.
                                  If False, a dictionary where the key is the driver name and the value its path (Node)
    Returns:
        dict or list: A dictionary where the key is the driver name and the value its path (Node)
                      If "as_list" is True, then a list of Nodes containing the path to the drivers is returned.
    """
    driver_uuids = get_driver_uuids_from_joint(source_joint=source_joint, as_list=False)
    found_drivers = {}
    for driver, uuid in driver_uuids.items():
        _found_driver = find_driver_from_uuid(uuid_string=uuid)
        if _found_driver:
            found_drivers[driver] = _found_driver
    if as_list:
        return list(found_drivers.values())
    return found_drivers


def find_objects_with_attr(attr_name, obj_type="transform", transform_lookup=True, lookup_list=None):
    """
    Return object if provided UUID is present in it
    Args:
        attr_name (string): Name of the attribute where the UUID is stored.
        obj_type (str, optional): Type of objects to look for (default is "transform")
        transform_lookup (bool, optional): When not a transform, it checks the item parent instead of the item itself.
        lookup_list (list, optional): If provided, this list will be used instead of a full "ls" type query.
                                      This can be used to improve performance in case the element was already
                                      previously listed in another operation. List should use full paths.
                                      e.g. ["|itemOne", "|transform|itemTwo"]

    Returns:
        Node or None: If found, the object with a matching UUID, otherwise None
    """
    if isinstance(lookup_list, list):
        obj_list = lookup_list
    else:
        obj_list = cmds.ls(typ=obj_type, long=True) or []
    for obj in obj_list:
        if transform_lookup and obj_type != "transform":
            _parent = cmds.listRelatives(obj, parent=True, fullPath=True) or []
            if _parent:
                obj = _parent[0]
        if cmds.objExists(f'{obj}.{attr_name}'):
            return Node(obj)


def find_proxy_root_group():
    """
    Looks for the proxy root transform (group) by searching for objects containing the expected lookup attribute.
    Not to be confused with the root curve. This is the parent TRANSFORM.
    Returns:
        Node or None: The existing root group (top proxy parent), otherwise None.
    """
    return find_objects_with_attr(RiggerConstants.REF_ATTR_ROOT_PROXY, obj_type="transform")


def find_rig_root_group():
    """
    Looks for the rig root transform (group) by searching for objects containing the expected lookup attribute.
    Not to be confused with the root control curve. This is the parent TRANSFORM.
    Returns:
        Node or None: The existing rig group (top rig parent), otherwise None.
    """
    return find_objects_with_attr(RiggerConstants.REF_ATTR_ROOT_RIG, obj_type="transform")


def find_control_root_curve(use_transform=False):
    """
    Looks for the control root curve by searching for objects containing the expected lookup attribute.
    Args:
        use_transform (bool, optional): If active, it will use the type transform to look for the object.
                                        This can potentially make the operation less efficient, but will
                                        run a more complete search as it will include curves that had
                                        their shapes deleted.
    Returns:
        Node or None: The existing control root curve (a.k.a. main control), otherwise None.
    """
    obj_type = "nurbsCurve"
    if use_transform:
        obj_type = "transform"
    return find_objects_with_attr(RiggerConstants.REF_ATTR_ROOT_CONTROL, obj_type=obj_type)


def find_direction_curve(use_transform=False):
    """
    Looks for the direction curve by searching for objects containing the expected lookup attribute.
    Args:
        use_transform (bool, optional): If active, it will use the type transform to look for the object.
                                        This can potentially make the operation less efficient, but will
                                        run a more complete search as it will include curves that had
                                        their shapes deleted.
    Returns:
        Node or None: The existing direction curve, otherwise None.
    """
    obj_type = "nurbsCurve"
    if use_transform:
        obj_type = "transform"
    return find_objects_with_attr(RiggerConstants.REF_ATTR_DIR_CURVE, obj_type=obj_type)


def find_proxy_root_curve(use_transform=False):
    """
    Looks for the proxy root curve by searching for objects containing the expected attribute.
    Args:
        use_transform (bool, optional): If active, it will use the type transform to look for the object.
                                        This can potentially make the operation less efficient, but will
                                        run a more complete search as it will include curves that had
                                        their shapes deleted.
    Returns:
        Node or None: The existing proxy root curve, otherwise None.
    """
    obj_type = "nurbsCurve"
    if use_transform:
        obj_type = "transform"
    return find_objects_with_attr(RiggerConstants.REF_ATTR_ROOT_PROXY, obj_type=obj_type)


def find_skeleton_group():
    """
    Looks for the rig skeleton group (transform) by searching for objects containing the expected attribute.
    Returns:
        Node or None: The existing skeleton group, otherwise None.
    """
    return find_objects_with_attr(RiggerConstants.REF_ATTR_SKELETON, obj_type="transform")


def find_setup_group():
    """
    Looks for the rig setup group (transform) by searching for objects containing the expected attribute.
    Returns:
        Node or None: The existing setup group, otherwise None.
    """
    return find_objects_with_attr(RiggerConstants.REF_ATTR_SETUP, obj_type="transform")


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
    lines_grp = find_objects_with_attr(attr_name=RiggerConstants.REF_ATTR_LINES)
    _lines = set()
    if lines_grp:
        _children = cmds.listRelatives(str(lines_grp), children=True, fullPath=True) or []
        for child in _children:
            if not cmds.objExists(f'{child}.{RiggerConstants.ATTR_LINE_PARENT_UUID}'):
                continue
            if parent_uuid:
                existing_uuid = cmds.getAttr(f'{child}.{RiggerConstants.ATTR_LINE_PARENT_UUID}')
                if existing_uuid == parent_uuid:
                    _lines.add(Node(child))
            if child_uuid:
                existing_uuid = cmds.getAttr(f'{child}.{RiggerConstants.ATTR_LINE_CHILD_UUID}')
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
        if cmds.objExists(f'{obj}.{RiggerConstants.ATTR_LINE_PARENT_UUID}'):
            valid_items.add(Node(obj))
    for item in valid_items:
        if parent_uuid:
            existing_uuid = cmds.getAttr(f'{item}.{RiggerConstants.ATTR_LINE_PARENT_UUID}')
            if existing_uuid == parent_uuid:
                _lines.add(Node(child))
        if child_uuid:
            existing_uuid = cmds.getAttr(f'{item}.{RiggerConstants.ATTR_LINE_CHILD_UUID}')
            if existing_uuid == child_uuid:
                _lines.add(Node(child))
    return tuple(_lines)


def find_or_create_joint_automation_group():
    """
    Use the "find_or_create_automation_group" function to get the joint automation group.
    This is a group where extra joints used for automation (not skinning) are stored.
    Returns:
        str: Path to the automation group (or subgroup)
    """
    return get_automation_group(name="jointAutomation_grp",
                                rgb_color=ColorConstants.RigOutliner.GRP_SKELETON)


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
            line_parent = metadata.get(RiggerConstants.META_PROXY_LINE_PARENT, None)
            if line_parent:
                parent_proxy = find_proxy_from_uuid(line_parent)

        # Create Line
        if built_proxy and parent_proxy and cmds.objExists(built_proxy) and cmds.objExists(parent_proxy):
            try:
                line_objects = create_connection_line(object_a=built_proxy,
                                                      object_b=parent_proxy) or []
                if lines_parent and cmds.objExists(lines_parent):
                    hierarchy_utils.parent(source_objects=line_objects, target_parent=lines_parent) or []
                if line_objects:
                    line_crv = line_objects[0]
                    add_attr(obj_list=line_crv,
                             attributes=RiggerConstants.ATTR_LINE_CHILD_UUID,
                             attr_type="string")
                    set_attr(attribute_path=f'{line_crv}.{RiggerConstants.ATTR_LINE_CHILD_UUID}',
                             value=proxy.get_uuid())
                    add_attr(obj_list=line_crv,
                             attributes=RiggerConstants.ATTR_LINE_PARENT_UUID,
                             attr_type="string")
                    set_attr(attribute_path=f'{line_crv}.{RiggerConstants.ATTR_LINE_PARENT_UUID}',
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
    _attr = RiggerConstants.REF_ATTR_ROOT_RIG
    _color = ColorConstants.RigOutliner.GRP_ROOT_RIG
    if is_proxy:
        _name = RiggerConstants.GRP_PROXY_NAME
        _attr = RiggerConstants.REF_ATTR_ROOT_PROXY
        _color = ColorConstants.RigOutliner.GRP_ROOT_PROXY
    root_group = cmds.group(name=_name, empty=True, world=True)
    root_group = Node(root_group)
    hide_lock_default_attrs(obj_list=root_group, translate=True, rotate=True, scale=True)
    add_attr(obj_list=root_group, attr_type="string", is_keyable=False,
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
    hide_lock_default_attrs(obj_list=root_transform, translate=True, rotate=True)
    add_separator_attr(target_object=root_transform, attr_name=f'proxy{RiggerConstants.SEPARATOR_CONTROL.title()}')
    add_attr(obj_list=root_transform, attr_type="string", is_keyable=False,
             attributes=RiggerConstants.REF_ATTR_ROOT_PROXY, verbose=True)

    set_curve_width(obj_list=root_transform, line_width=2)
    return Node(root_transform)


def create_control_root_curve():
    """
    Creates a curve to be used as the root of a control rig skeleton
    Returns:
        Node, str: A Node containing the generated root curve
    """
    root_transform = create_root_curve(name=f'root_{NamingConstants.Suffix.CTRL}')
    add_separator_attr(target_object=root_transform, attr_name=f'rig{RiggerConstants.SEPARATOR_CONTROL.title()}')
    add_attr(obj_list=root_transform, attr_type="string", is_keyable=False,
             attributes=RiggerConstants.REF_ATTR_ROOT_CONTROL, verbose=True)
    set_curve_width(obj_list=root_transform, line_width=3)
    set_color_viewport(obj_list=root_transform, rgb_color=ColorConstants.RigControl.ROOT)
    return Node(root_transform)


def create_ctrl_curve(name, curve_file_name=None):
    """
    Creates a curve to be used as control within the auto rigger context.
    Args:
        name (str): Control name.
        curve_file_name (str, optional): Curve file name (from inside "gt/utils/data/curves") e.g. "circle"
    Returns:
        Node or None: Node with the generated control, otherwise None
    """
    if not curve_file_name:
        curve_file_name = "_cube"
    crv_obj = get_curve(file_name=curve_file_name)
    crv_obj.set_name(name)
    crv = crv_obj.build()
    if crv:
        return Node(crv)


def create_direction_curve():
    """
    Creates a curve to be used as the root of a control rig skeleton
    Returns:
        Node, str: A Node containing the generated root curve
    """
    direction_crv = cmds.circle(name=f'direction_{NamingConstants.Suffix.CTRL}',
                                 nr=(0, 1, 0), ch=False, radius=44.5)[0]
    cmds.rebuildCurve(direction_crv, ch=False, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=20, d=3, tol=0.01)
    add_separator_attr(target_object=direction_crv, attr_name=f'rig{RiggerConstants.SEPARATOR_CONTROL.title()}')
    add_attr(obj_list=direction_crv, attr_type="string", is_keyable=False,
             attributes=RiggerConstants.REF_ATTR_DIR_CURVE, verbose=True)
    set_color_viewport(obj_list=direction_crv, rgb_color=ColorConstants.RigControl.CENTER)
    return Node(direction_crv)


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
        desired_groups[RiggerConstants.REF_ATTR_GEOMETRY] = (_name, _color)
    if skeleton:
        _name = RiggerConstants.GRP_SKELETON_NAME
        _color = ColorConstants.RigOutliner.GRP_SKELETON
        desired_groups[RiggerConstants.REF_ATTR_SKELETON] = (_name, _color)
    if control:
        _name = RiggerConstants.GRP_CONTROL_NAME
        _color = ColorConstants.RigOutliner.GRP_CONTROL
        desired_groups[RiggerConstants.REF_ATTR_CONTROL] = (_name, _color)
    if setup:
        _name = RiggerConstants.GRP_SETUP_NAME
        _color = ColorConstants.RigOutliner.GRP_SETUP
        desired_groups[RiggerConstants.REF_ATTR_SETUP] = (_name, _color)
    if line:
        _name = RiggerConstants.GRP_LINE_NAME
        _color = None
        desired_groups[RiggerConstants.REF_ATTR_LINES] = (_name, _color)

    group_dict = {}
    for attr, (name, color) in desired_groups.items():
        group = cmds.group(name=name, empty=True, world=True)
        add_attr(obj_list=group, attr_type="string", is_keyable=False,
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


def get_meta_purpose_from_dict(proxy_dict):
    """
    Gets the meta type of the proxy. A meta type helps identify the purpose of a proxy within a module.
    For example, a type "knee" proxy describes that it will be influenced by the "hip" and "ankle" in a leg.
    This can also be seen as "pointers" to the correct proxy when receiving data from a dictionary.
    Args:
        proxy_dict (dict, None): A dictionary describing a proxy.
    Returns:
        string or None: The meta type string or None when not detected/found.
    """
    if proxy_dict:
        meta_type = proxy_dict.get(RiggerConstants.META_PROXY_PURPOSE)
        return meta_type


def get_automation_group(name=f'generalAutomation_{NamingConstants.Suffix.GRP}',
                         subgroup=None,
                         rgb_color=ColorConstants.RigOutliner.AUTOMATION):
    """
    Gets the path to an automation group (or subgroup) or create it in case it can't be found.
    Automation groups are found inside the "setup_grp" found using "find_setup_group"
    Args:
        name (str, optional): Name of the automation group (found inside the "setup_grp")
        subgroup (str, optional): If provided, this subgroup should exist inside the base automation group.
        rgb_color (tuple, optional): A tuple with three integers/floats describing a color (RGB).
    Returns:
        Node, str: Path to the automation group (or subgroup) - Node format has string as its base.
    Example:
        output_a = find_or_create_automation_group(name="generalAutomation_grp")
        print(output_a)  # |rig_grp|setup_grp|generalAutomation_grp
        output_b = find_or_create_automation_group(name="generalAutomation_grp", subgroup="baseConstraints_grp")
        print(output_b)  # |rig_grp|setup_grp|generalAutomation_grp|baseConstraints_grp
    """
    selection = cmds.ls(selection=True)
    setup_grp = find_setup_group()
    _grp_path = f'{setup_grp}|{str(name)}'
    # Find or create automation group (base)
    if name and cmds.objExists(_grp_path):
        _grp_path = Node(_grp_path)
    else:
        _grp_path = cmds.group(name=name, empty=True, world=True)
        _grp_path = Node(_grp_path)
        set_color_outliner(obj_list=_grp_path, rgb_color=rgb_color)
        hierarchy_utils.parent(source_objects=_grp_path, target_parent=setup_grp)
        if not setup_grp:
            logger.debug(f'Automation group "{str(name)}" could not be properly parented. '
                         f'Missing setup group.')
    # Find or create automation subgroup (child of the base)
    if subgroup and isinstance(subgroup, str):
        _grp_path_base = _grp_path  # Store base for re-parenting
        _grp_path = f'{_grp_path}|{str(subgroup)}'
        if name and cmds.objExists(_grp_path):
            _grp_path = _grp_path
        else:
            _grp_path = cmds.group(name=subgroup, empty=True, world=True)
            _grp_path = Node(_grp_path)
            hierarchy_utils.parent(source_objects=_grp_path, target_parent=_grp_path_base)
            if not setup_grp:
                logger.debug(f'Automation group "{str(name)}" could not be properly parented. '
                             f'Missing setup group.')
    cmds.select(clear=True)
    if selection:
        try:
            cmds.select(selection=True)
        except Exception as e:
            logger.debug(f'Unable to restore initial selection. Issue: {str(e)}')
    return _grp_path


def duplicate_joint_for_automation(joint, suffix=NamingConstants.Suffix.DRIVEN, parent=None, connect_rot_order=True):
    """
    Preset version of the "duplicate_as_node" function used to duplicate joints for automation.
    Args:
        joint (str, Node): The joint to be duplicated
        suffix (str, optional): The suffix to be added at the end of the duplicated joint.
        parent (str, optional): If provided, and it exists, the duplicated object will be parented to this object.
        connect_rot_order (bool, optional): If True, it will create a connection between the original joint rotate
                                            order and the duplicate joint rotate order.
                                            (duplicate receives from original)
    Returns:
        str, None: A node (that has a str base) of the duplicated object, or None if it failed.
    """
    if not joint or not cmds.objExists(str(joint)):
        return
    jnt_as_node = duplicate_as_node(to_duplicate=str(joint), name=f'{joint.get_short_name()}_{suffix}',
                                    parent_only=True, delete_attrs=True, input_connections=False)
    if connect_rot_order:
        connect_attr(source_attr=f'{str(joint)}.rotateOrder', target_attr_list=f'{jnt_as_node}.rotateOrder')
    if parent:
        hierarchy_utils.parent(source_objects=jnt_as_node, target_parent=parent)
    return jnt_as_node


def get_driven_joint(uuid_string, suffix=NamingConstants.Suffix.DRIVEN, constraint_to_source=True):
    """
    Gets the path to a driven joint or create it in case it's missing.
    Driven joints are used to control automation joints or joint hierarchies.
    Args:
        uuid_string (str): UUID string stored in "RiggerConstants.JOINT_ATTR_DRIVEN_UUID" used to identify.
        suffix (str, optional): Suffix to add to the newly created driven joint. Default is "driven".
        constraint_to_source (bool, optional): Parent constraint the joint to its source during creation.
                                               Does nothing if driver already exists and is found.
    Returns:
        Node, str: Path to the FK Driver - Node format has string as its base.

    """
    driven_jnt = get_object_from_uuid_attr(uuid_string=uuid_string,
                                           attr_name=RiggerConstants.ATTR_JOINT_DRIVEN_UUID,
                                           obj_type="joint")
    if not driven_jnt:
        source_jnt = find_joint_from_uuid(uuid_string)
        if not source_jnt:
            return
        driven_jnt = duplicate_joint_for_automation(joint=source_jnt, suffix=suffix)
        delete_user_defined_attrs(obj_list=driven_jnt)
        add_attr(obj_list=driven_jnt, attr_type="string", attributes=RiggerConstants.ATTR_JOINT_DRIVEN_UUID)
        set_attr(attribute_path=f'{driven_jnt}.{RiggerConstants.ATTR_JOINT_DRIVEN_UUID}', value=uuid_string)
        if constraint_to_source:
            constraint = cmds.parentConstraint(source_jnt, driven_jnt)
            cmds.setAttr(f'{constraint[0]}.interpType', 0)  # Set to No Flip
    return driven_jnt


def rescale_joint_radius(joint_list, multiplier):
    """
    Re-scales the joint radius attribute of the provided joints.
    It gets the original value and multiply it by the provided "multiplier" argument.
    Args:
        joint_list (list, str): Path to the target joints.
        multiplier (int, float): Value to multiply the radius by. For example "0.5" means 50% of the original value.
    """
    if joint_list and isinstance(joint_list, str):
        joint_list = [joint_list]
    for jnt in joint_list:
        if not cmds.objExists(f'{jnt}.radius'):
            continue
        scaled_radius = get_attr(f'{jnt}.radius') * multiplier
        cmds.setAttr(f'{jnt}.radius', scaled_radius)


def get_drivers_list_from_joint(source_joint):
    """
    Gets the list of drivers that are stored in a joint drivers attribute.
    If missing the attribute, it will return an empty list.
    If the string data stored in the attribute is corrupted, it will return an empty list.
    """
    drivers = get_attr(obj_name=source_joint, attr_name=RiggerConstants.ATTR_JOINT_DRIVERS)
    if drivers:
        try:
            drivers = eval(drivers)
            if not isinstance(drivers, list):
                logger.debug('Stored value was not a list.')
                drivers = None
        except Exception as e:
            logger.debug(f'Unable to read joint drivers data. Values will be overwritten. Issue: {e}')
            drivers = None
    if not drivers:
        return []
    return drivers


def add_driver_to_joint(target_joint, new_drivers):
    """
    Adds a new driver to the driver list of the target joint.
    The list is stored inside the drivers attribute of the joint.
    If the expected "joint drivers" attribute is not found, the operation is ignored.
    Args:
        target_joint (str, Node): The path to a joint. It's expected that this joint contains the drivers attribute.
        new_drivers (str, list): A new driver to be added to the drivers list. e.g. "fk". (Can be a list of drivers)
                                 This will only be added to the list and will not overwrite the existing items.
                                 The operation is ignored in case the item is already part of the list.
    """
    drivers = get_drivers_list_from_joint(source_joint=target_joint)
    for new_driver in new_drivers:
        if new_driver not in drivers:
            drivers.append(new_driver)
    data = json.dumps(drivers)
    set_attr(obj_list=target_joint, attr_list=RiggerConstants.ATTR_JOINT_DRIVERS, value=data)


def get_driver_uuids_from_joint(source_joint, as_list=False):
    """
    Gets a dictionary or list of drivers uuids from joint.
    It's expected that the joint has this data available as string attributes.
    Args:
        source_joint (str, Node): The path to a joint. It's expected that this joint contains the drivers attribute.
        as_list (bool, optional): If True, it will return a list of uuids. if False, the standard dictionary.
    Returns:
        dict or list: A dictionary where the key is the driver name and the value its uuid, or a list of uuids.
    """
    driver_uuids = {}
    if source_joint and cmds.objExists(source_joint):
        drivers = get_drivers_list_from_joint(source_joint=source_joint)
        module_uuid = get_attr(obj_name=source_joint, attr_name=RiggerConstants.ATTR_MODULE_UUID)
        joint_purpose = get_attr(obj_name=source_joint, attr_name=RiggerConstants.ATTR_JOINT_PURPOSE)
        for driver in drivers:
            _driver_uuid = f'{module_uuid}-{driver}'
            if joint_purpose:
                _driver_uuid = f'{_driver_uuid}-{joint_purpose}'
            driver_uuids[driver] = _driver_uuid
    if as_list:
        return list(driver_uuids.values())
    return driver_uuids


def expose_rotation_order(target):
    """
    Creates an attribute to control the rotation order of the target object and connects the attribute
    to the hidden "rotationOrder" attribute.
    Args:
        target (str): Path to the target object (usually a control)
    """
    cmds.addAttr(target, ln='rotationOrder', at='enum', keyable=True,
                 en=RiggerConstants.ENUM_ROTATE_ORDER, niceName='Rotate Order')
    cmds.connectAttr(f'{target}.rotationOrder', f'{target}.rotateOrder', f=True)


def offset_control_orientation(ctrl, offset_transform, orient_tuple):
    """
    Offsets orientation of the control offset transform, while maintaining the original curve shape point position.
    Args:
        ctrl (str, Node): Path to the control transform (with curve shapes)
        offset_transform (str, Node): Path to the control offset transform.
        orient_tuple (tuple): A tuple with X, Y and Z values used as offset.
                              e.g. (90, 0, 0)  # offsets orientation 90 in X
    """
    for obj in [ctrl, offset_transform]:
        if not obj or not cmds.objExists(obj):
            logger.debug(f'Unable to offset control orientation, not all objects were found in the scene. '
                         f'Missing: {str(obj)}')
            return
    cv_pos_dict = get_component_positions_as_dict(obj_transform=ctrl, full_path=True, world_space=True)
    cmds.rotate(*orient_tuple, offset_transform, relative=True, objectSpace=True)
    set_component_positions_from_dict(component_pos_dict=cv_pos_dict)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    # cmds.file(new=True, force=True)
    # cmds.viewFit(all=True)
    # create_direction_curve()
