"""
Auto Rigger Utilities

Import Line:
    import gt.tools.auto_rigger.rig_utils as tools_rig_utils
"""

import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.core.constraint as core_cnstr
import gt.core.namespace as core_nspace
import gt.core.transform as core_trans
import gt.core.hierarchy as core_hrchy
import gt.core.rigging as core_rigging
import gt.core.naming as core_naming
import gt.core.iterable as core_iter
import gt.core.curve as core_curve
import gt.core.color as core_color
import gt.core.logger as core_log
import gt.core.attr as core_attr
import gt.core.node as core_node
import gt.core.uuid as core_uuid
import gt.core.str as core_str
import gt.core.pose as core_pose
import maya.api.OpenMaya as OpenMayaApi
import maya.OpenMaya as OpenMaya
import maya.cmds as cmds
import logging
import json
import copy
import os

# Logging Setup
logger_name = core_log.get_logger_name(__name__)
logger = core_log.setup_common_logger(name=logger_name, propagate=True)
logger.setLevel(logging.INFO)
core_log.add_custom_log_levels()


# ------------------------------------------ Lookup functions ------------------------------------------
def cache_driver_uuids_to_dict():
    """
    Collects all transform nodes in the Maya scene that have the driver UUID attribute
    and groups them by their UUID.

    This function scans the scene for all objects of type "transform" and checks if they
    contain the attribute defined by `tools_rig_const.RiggerConstants.ATTR_DRIVER_UUID`.
    If present, the attribute's value (UUID) is retrieved, and the object is stored in a
    dictionary keyed by that UUID.

    Returns:
        dict[str, list[str]]:
            A dictionary mapping each found UUID (as a string) to a list of full
            object paths (long names) that share that UUID.
            - Keys: UUID strings.
            - Values: Lists of object long paths that have this UUID.
            If multiple objects share the same UUID, they are grouped in the same list.

    Example:
        {
            "ekmnpw3tuk6f-fk-lowerArm": [
                "|group1|driver1",
                "|group2|driver2"
            ],
            "ekmnpw3tuk6f-fk-hand": [
                "|group3|driver3"
            ]
        }
    """
    obj_list = cmds.ls(typ="transform", long=True) or []
    uuid_path_pairs = {}
    for obj in obj_list:
        attr_path = f"{obj}.{tools_rig_const.RiggerConstants.ATTR_DRIVER_UUID}"
        if cmds.objExists(attr_path):
            uuid = cmds.getAttr(attr_path)
            uuid_path_pairs.setdefault(uuid, []).append(obj)
    return uuid_path_pairs


def find_proxy_from_uuid(uuid_string):
    """
    Return a proxy if the provided UUID is present in the attribute RiggerConstants.PROXY_ATTR_UUID
    Args:
        uuid_string (str): UUID to look for (if it matches, then the proxy is found)
    Returns:
        Node or None: If found, the proxy with the matching UUID, otherwise None
    """
    proxy = core_uuid.get_object_from_uuid_attr(
        uuid_string=uuid_string, attr_name=tools_rig_const.RiggerConstants.ATTR_PROXY_UUID, obj_type="transform"
    )
    if proxy:
        return core_node.Node(proxy)


def find_joint_from_uuid(uuid_string):
    """
    Return a joint if the provided UUID is present in the attribute RiggerConstants.JOINT_ATTR_UUID
    Args:
        uuid_string (str): UUID to look for (if it matches, then the joint is found)
    Returns:
        Node or None: If found, the joint with the matching UUID, otherwise None
    """
    joint = core_uuid.get_object_from_uuid_attr(
        uuid_string=uuid_string, attr_name=tools_rig_const.RiggerConstants.ATTR_JOINT_UUID, obj_type="joint"
    )
    if joint:
        return core_node.Node(joint)


def find_driver_from_uuid(uuid_string):
    """
    Return a transform if the provided UUID matches the value of the attribute
    tools_rig_const.RiggerConstants.DRIVER_ATTR_UUID
    Args:
        uuid_string (str): UUID to look for (if it matches, then the driver is found)
    Returns:
        Node or None: If found, the joint with the matching UUID, otherwise None
    """
    driver = core_uuid.get_object_from_uuid_attr(
        uuid_string=uuid_string, attr_name=tools_rig_const.RiggerConstants.ATTR_DRIVER_UUID, obj_type="transform"
    )
    if driver:
        return core_node.Node(driver)


def find_drivers_from_joint(source_joint, as_list=False, create_missing_generic=False, skip_block_drivers=False):
    """
    Finds drivers according to the data described in the joint attributes.
    It's expected that the joint has this data available as string attributes.
    Args:
        source_joint (str, Node): The path to a joint. It's expected that this joint contains the drivers attribute.
        as_list (bool, optional): If True, it will return a list of Node objects.
                                  If False, a dictionary where the key is the driver name and the value its path (Node)
        create_missing_generic (bool, optional): If the driver is of the type generic, but no driver transform
                                                is found in the scene, a new transform is created to be used as generic.
                                                If no drivers are detected, then a generic driver is created and
                                                plugged populated in the "source_joint".
        skip_block_drivers (bool, optional): If True, when a block driver is detected an empty result becomes the
                                             result instead of the actual drivers. Useful for when creating the logic
                                             that blocks creation of control drivers.
    Returns:
        dict or list: A dictionary where the key is the driver name and the value its path (Node)
                      If "as_list" is True, then a list of Nodes containing the path to the drivers is returned.
    """
    driver_uuids = get_driver_uuids_from_joint(source_joint=source_joint, as_list=False)
    # Block lookup for None drivers
    if tools_rig_const.RiggerDriverTypes.BLOCK in driver_uuids.keys() and skip_block_drivers:
        return [] if as_list else {}
    found_drivers = {}
    # Handle listed drivers
    for index, (driver, uuid) in enumerate(driver_uuids.items()):
        _found_driver = find_driver_from_uuid(uuid_string=uuid)
        # If generic driver is the first option, but transform is missing, generate one that follows the parent joint
        if driver == tools_rig_const.RiggerDriverTypes.GENERIC and create_missing_generic and not _found_driver:
            _found_driver = get_generic_driver(source_joint=source_joint)
        if _found_driver:
            found_drivers[driver] = _found_driver
    # Handle empty driver list
    if cmds.objExists(source_joint) and not driver_uuids and create_missing_generic:
        _found_driver = get_generic_driver(source_joint=source_joint, add_missing_driver=True)
        if _found_driver:
            found_drivers[tools_rig_const.RiggerDriverTypes.GENERIC] = _found_driver
    # Convert to list
    if as_list:
        return list(found_drivers.values())
    return found_drivers


def find_object_with_attr(attr_name, obj_type="transform", transform_lookup=True, lookup_list=None):
    """
    Return object if provided UUID is present in it
    Args:
        attr_name (str): Name of the attribute where the UUID is stored.
        obj_type (str, optional): Type of objects to look for (default is "transform") - Used for optimization
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
        if cmds.objExists(f"{obj}.{attr_name}"):
            return core_node.Node(obj)


def find_root_group_proxy():
    """
    Looks for the proxy root transform (group) by searching for objects containing the expected lookup attribute.
    Not to be confused with the root curve. This is the parent TRANSFORM.
    Returns:
        Node or None: The existing root group (top proxy parent), otherwise None.
    """
    return find_object_with_attr(tools_rig_const.RiggerConstants.REF_ATTR_ROOT_PROXY, obj_type="transform")


def find_root_group_rig():
    """
    Looks for the rig root transform (group) by searching for objects containing the expected lookup attribute.
    Not to be confused with the root control curve. This is the parent TRANSFORM.
    Returns:
        Node or None: The existing rig group (top rig parent), otherwise None.
    """
    return find_object_with_attr(tools_rig_const.RiggerConstants.REF_ATTR_ROOT_RIG, obj_type="transform")


def find_ctrl_global(use_transform=False):
    """
    Looks for the control root/global curve by searching for objects containing the expected lookup attribute.
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
    return find_object_with_attr(tools_rig_const.RiggerConstants.REF_ATTR_CTRL_GLOBAL, obj_type=obj_type)


def find_ctrl_global_offset(use_transform=False):
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
    return find_object_with_attr(tools_rig_const.RiggerConstants.REF_ATTR_CTRL_GLOBAL_OFFSET, obj_type=obj_type)


def find_ctrl_global_proxy(use_transform=False):
    """
    Looks for the proxy global/root curve by searching for objects containing the expected attribute.
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
    return find_object_with_attr(tools_rig_const.RiggerConstants.REF_ATTR_CTRL_GLOBAL_PROXY, obj_type=obj_type)


def find_skeleton_group():
    """
    Looks for the rig skeleton group (transform) by searching for objects containing the expected attribute.
    Returns:
        Node or None: The existing skeleton group, otherwise None.
    """
    return find_object_with_attr(tools_rig_const.RiggerConstants.REF_ATTR_SKELETON, obj_type="transform")


def find_setup_group():
    """
    Looks for the rig setup group (transform) by searching for objects containing the expected attribute.
    Returns:
        Node or None: The existing setup group, otherwise None.
    """
    return find_object_with_attr(tools_rig_const.RiggerConstants.REF_ATTR_SETUP, obj_type="transform")


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
    lines_grp = find_object_with_attr(attr_name=tools_rig_const.RiggerConstants.REF_ATTR_LINES)
    _lines = set()
    if lines_grp:
        _children = cmds.listRelatives(str(lines_grp), children=True, fullPath=True) or []
        for child in _children:
            if not cmds.objExists(f"{child}.{tools_rig_const.RiggerConstants.ATTR_LINE_PARENT_UUID}"):
                continue
            if parent_uuid:
                existing_uuid = cmds.getAttr(f"{child}.{tools_rig_const.RiggerConstants.ATTR_LINE_PARENT_UUID}")
                if existing_uuid == parent_uuid:
                    _lines.add(core_node.Node(child))
            if child_uuid:
                existing_uuid = cmds.getAttr(f"{child}.{tools_rig_const.RiggerConstants.ATTR_LINE_CHILD_UUID}")
                if existing_uuid == child_uuid:
                    _lines.add(core_node.Node(child))
    if _lines:
        return tuple(_lines)
    # If nothing was found, look through all transforms - Less optimized
    obj_list = cmds.ls(typ="nurbsCurve", long=True) or []
    valid_items = set()
    for obj in obj_list:
        _parent = cmds.listRelatives(obj, parent=True, fullPath=True) or []
        if _parent:
            obj = _parent[0]
        if cmds.objExists(f"{obj}.{tools_rig_const.RiggerConstants.ATTR_LINE_PARENT_UUID}"):
            valid_items.add(core_node.Node(obj))
    for item in valid_items:
        if parent_uuid:
            existing_uuid = cmds.getAttr(f"{item}.{tools_rig_const.RiggerConstants.ATTR_LINE_PARENT_UUID}")
            if existing_uuid == parent_uuid:
                _lines.add(core_node.Node(child))
        if child_uuid:
            existing_uuid = cmds.getAttr(f"{item}.{tools_rig_const.RiggerConstants.ATTR_LINE_CHILD_UUID}")
            if existing_uuid == child_uuid:
                _lines.add(core_node.Node(child))
    return tuple(_lines)


def find_or_create_joint_automation_group():
    """
    Use the "find_or_create_automation_group" function to get the joint automation group.
    This is a group where extra joints used for automation (not skinning) are stored.
    Returns:
        str: Path to the automation group (or subgroup)
    """
    return get_automation_group(name="jointAutomation", rgb_color=core_color.ColorConstants.RigOutliner.GRP_SKELETON)


def find_drivers_from_module(
    source_uuid, filter_driver_type=None, filter_driver_purpose=None, cached_driver_uuids=None
):
    """
    Finds all drivers belonging to a module.
    Args:
        source_uuid (str, ModuleGeneric, RigProject): The used when filtering all existing drivers.
        filter_driver_type (str, list, optional): If provided, only drivers of this type are returned.
        filter_driver_purpose (str, list, optional): If provided, only drivers of this purpose are returned.
        cached_driver_uuids (dict, optional): If provided, this dictionary will be used to determine which objects
                                              are available in the scene. This is for optimizing the amount of checks
                                              required to find all drivers. Use "cache_driver_uuids_to_dict()" for that.
    Returns:
        list: A list of Nodes, each one is a driver belonging to the module uuid provided as argument.
    """
    if source_uuid and not isinstance(source_uuid, str):
        source_uuid = source_uuid.get_uuid()
    module_drivers = []
    transforms = cmds.ls(typ="transform", long=True) or []

    # Normalize filter parameters to lists for easier processing
    if isinstance(filter_driver_type, str):
        filter_driver_type = [filter_driver_type]
    if isinstance(filter_driver_purpose, str):
        filter_driver_purpose = [filter_driver_purpose]

    # Cached solution (Fast)
    if cached_driver_uuids and isinstance(cached_driver_uuids, dict):
        for drv_uuid, long_paths in cached_driver_uuids.items():
            # Split the attribute value into components
            attr_components = str(drv_uuid).split("-")
            if len(attr_components) != 3:
                continue  # Invalid UUID structure, skip it
            attr_type, attr_purpose = attr_components[1], attr_components[2]
            for path in long_paths:
                if attr_purpose == "unknown":
                    base_name_path = f"{path}.{tools_rig_const.RiggerConstants.ATTR_BASE_NAME}"
                    base_name_value = core_attr.get_attr(attribute_path=base_name_path, verbose=False)
                    attr_purpose = base_name_value
                # Filter by type
                if filter_driver_type and attr_type not in filter_driver_type:
                    continue  # Not of the desired type, skip it
                # Filter by purpose
                if filter_driver_purpose and attr_purpose not in filter_driver_purpose:
                    continue  # Not of the desired purpose, skip it
                if drv_uuid.startswith(source_uuid):
                    # for obj in long_paths:
                    module_drivers.append(core_node.Node(path))
        return module_drivers

    # Full Walkthrough (Slow)
    for trans in transforms:
        attr_path = f"{trans}.{tools_rig_const.RiggerConstants.ATTR_DRIVER_UUID}"
        if cmds.objExists(attr_path):
            attr_value = core_attr.get_attr(attribute_path=attr_path)
            if not attr_value:
                continue  # Missing UUID driver data, skip it
            # Split the attribute value into components
            attr_components = str(attr_value).split("-")
            if len(attr_components) != 3:
                continue  # Invalid UUID structure, skip it
            attr_type, attr_purpose = attr_components[1], attr_components[2]
            if attr_purpose == "unknown":
                base_name_path = f"{trans}.{tools_rig_const.RiggerConstants.ATTR_BASE_NAME}"
                base_name_value = core_attr.get_attr(attribute_path=base_name_path, verbose=False)
                attr_purpose = base_name_value
            # Filter by type
            if filter_driver_type and attr_type not in filter_driver_type:
                continue  # Not of the desired type, skip it
            # Filter by purpose
            if filter_driver_purpose and attr_purpose not in filter_driver_purpose:
                continue  # Not of the desired purpose, skip it
            if attr_value.startswith(source_uuid):
                module_drivers.append(core_node.Node(trans))

    # Find Supporting Drivers
    for driver in module_drivers:
        if not cmds.objExists(f"{driver}.{tools_rig_const.RiggerConstants.ATTR_DRIVER_UUID}"):
            continue
        supporting_drivers = get_supporting_drivers(source_driver=driver)
        if supporting_drivers:
            module_drivers.extend(supporting_drivers)
    return module_drivers


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
        list: List of tuples. Every tuple carries a list of generated elements.
              e.g. [('second_to_first', 'second_cluster', 'first_cluster')]
    """
    _lines = []
    for proxy in proxy_list:
        built_proxy = find_proxy_from_uuid(proxy.get_uuid())
        parent_proxy = find_proxy_from_uuid(proxy.get_parent_uuid())

        # Check for Meta Parent - OVERWRITES parent!
        metadata = proxy.get_metadata()
        if metadata:
            line_parent = metadata.get(tools_rig_const.RiggerConstants.META_PROXY_LINE_PARENT, None)
            if line_parent:
                parent_proxy = find_proxy_from_uuid(line_parent)

        # Create Line
        if built_proxy and parent_proxy and cmds.objExists(built_proxy) and cmds.objExists(parent_proxy):
            try:
                line_objects = core_curve.create_connection_line(object_a=built_proxy, object_b=parent_proxy) or []
                if lines_parent and cmds.objExists(lines_parent):
                    core_hrchy.parent(source_objects=line_objects, target_parent=lines_parent) or []
                if line_objects:
                    line_crv = line_objects[0]
                    core_attr.add_attr(
                        obj_list=line_crv,
                        attributes=tools_rig_const.RiggerConstants.ATTR_LINE_CHILD_UUID,
                        attr_type="string",
                    )
                    core_attr.set_attr(
                        attribute_path=f"{line_crv}.{tools_rig_const.RiggerConstants.ATTR_LINE_CHILD_UUID}",
                        value=proxy.get_uuid(),
                    )
                    core_attr.add_attr(
                        obj_list=line_crv,
                        attributes=tools_rig_const.RiggerConstants.ATTR_LINE_PARENT_UUID,
                        attr_type="string",
                    )
                    core_attr.set_attr(
                        attribute_path=f"{line_crv}.{tools_rig_const.RiggerConstants.ATTR_LINE_PARENT_UUID}",
                        value=proxy.get_parent_uuid(),
                    )
                _lines.append(line_objects)
            except Exception as e:
                logger.debug(f"Failed to create visualization line. Issue: {str(e)}")
    return _lines


def create_ctrl_rig_global(name=f"global_{core_naming.NamingConstants.Suffix.CTRL}"):
    """
    Creates a circle/arrow curve to be used as the root/global of a control rig or a proxy guide
    Args:
        name (str, optional): Name of the curve transform
    Returns:
        Node, str: A Node containing the generated root curve
    """
    selection = cmds.ls(selection=True)
    ctrl_crv = core_curve.get_curve("_rig_root")
    ctrl_crv.set_name(name=name)
    ctrl_transform = ctrl_crv.build()
    core_attr.connect_attr(
        source_attr=f"{ctrl_transform}.sy", target_attr_list=[f"{ctrl_transform}.sx", f"{ctrl_transform}.sz"]
    )
    core_attr.set_attr_state(obj_list=ctrl_transform, attr_list=["sx", "sz"], hidden=True)
    core_color.set_color_viewport(obj_list=ctrl_transform, rgb_color=core_color.ColorConstants.RigProxy.CENTER)
    cmds.select(clear=True)
    if selection:
        try:
            cmds.select(selection=True)
        except Exception as e:
            logger.debug(f"Unable to restore initial selection. Issue: {str(e)}")
    return core_node.Node(ctrl_transform)


def create_root_group(is_proxy=False):
    """
    Creates a group to be used as the root of the current setup (rig or proxy)
    Args:
        is_proxy (bool, optional): If True, it will create the proxy group, instead of the main rig group
    Returns:
        Node: A Node describing the path to the created root group.
    """
    _name = tools_rig_const.RiggerConstants.GRP_RIG_NAME
    _attr = tools_rig_const.RiggerConstants.REF_ATTR_ROOT_RIG
    _color = core_color.ColorConstants.RigOutliner.GRP_ROOT_RIG
    if is_proxy:
        _name = tools_rig_const.RiggerConstants.GRP_PROXY_NAME
        _attr = tools_rig_const.RiggerConstants.REF_ATTR_ROOT_PROXY
        _color = core_color.ColorConstants.RigOutliner.GRP_ROOT_PROXY
    root_group = cmds.group(name=_name, empty=True, world=True)
    root_group = core_node.Node(root_group)
    core_attr.hide_lock_default_attrs(obj_list=root_group, translate=True, rotate=True, scale=True)
    core_attr.add_attr(obj_list=root_group, attr_type="string", is_keyable=False, attributes=_attr, verbose=True)
    core_color.set_color_outliner(root_group, rgb_color=_color)
    return root_group


def create_ctrl_proxy_global(prefix=core_naming.NamingConstants.Prefix.CENTER):
    """
    Creates a curve to be used as the root of a proxy skeleton
    Args:
        prefix (str, optional): Prefix to be added to the control.
                                Default is the center prefix according to core naming module.
    Returns:
        Node, str: A Node containing the generated root curve
    """
    root_transform = create_ctrl_rig_global(name=f"{prefix}_globalProxy")
    core_attr.hide_lock_default_attrs(obj_list=root_transform, translate=True, rotate=True)

    core_attr.add_separator_attr(
        target_object=root_transform,
        attr_name=f"proxy{core_str.upper_first_char(core_rigging.RiggingConstants.SEPARATOR_CONTROL)}",
    )
    core_attr.add_attr(
        obj_list=root_transform,
        attr_type="string",
        is_keyable=False,
        attributes=tools_rig_const.RiggerConstants.REF_ATTR_CTRL_GLOBAL_PROXY,
        verbose=True,
    )

    core_curve.set_curve_width(obj_list=root_transform, line_width=2)
    return core_node.Node(root_transform)


def create_ctrl_default(name, curve_file_name=None, outliner_color=core_color.ColorConstants.RigOutliner.CTRL):
    """
    Creates a curve to be used as control within the auto rigger context.
    Args:
        name (str): Control name.
        curve_file_name (str, optional): Curve file name (from inside "gt/core/data/curves") e.g. "circle"
        outliner_color (str, None, optional): Outliner color used for the created control. Set to None to skip it.
    Returns:
        Node or None: Node with the generated control, otherwise None
    """
    if not curve_file_name:
        curve_file_name = "_cube"
    crv_obj = core_curve.get_curve(file_name=curve_file_name)
    crv_obj.set_name(name)
    crv = crv_obj.build()
    if crv:
        if outliner_color:
            core_color.set_color_outliner(crv, rgb_color=core_color.ColorConstants.RigOutliner.CTRL)
        return core_node.Node(crv)


def create_ctrl_global(prefix=core_naming.NamingConstants.Prefix.CENTER):
    """
    Creates a curve to be used as the root of a control rig skeleton
    Args:
        prefix (str, optional): Prefix to be added to the control.
                                Default is the center prefix according to core naming module.
    Returns:
        Node, str: A Node containing the generated root curve
    """
    global_trans = create_ctrl_rig_global(name=f"{prefix}_global_{core_naming.NamingConstants.Suffix.CTRL}")
    core_attr.add_separator_attr(
        target_object=global_trans,
        attr_name=f"rig{core_str.upper_first_char(core_rigging.RiggingConstants.SEPARATOR_CONTROL)}",
    )
    core_attr.add_attr(
        obj_list=global_trans,
        attr_type="string",
        is_keyable=False,
        attributes=tools_rig_const.RiggerConstants.REF_ATTR_CTRL_GLOBAL,
        verbose=True,
    )
    core_curve.set_curve_width(obj_list=global_trans, line_width=3)
    core_color.set_color_outliner(global_trans, rgb_color=core_color.ColorConstants.RigOutliner.CTRL)
    core_color.set_color_viewport(obj_list=global_trans, rgb_color=core_color.ColorConstants.RigControl.ROOT)
    return core_node.Node(global_trans)


def create_ctrl_global_offset(prefix=core_naming.NamingConstants.Prefix.CENTER):
    """
    Creates a curve to be used as the offset of the root/global control of a rig skeleton
    Args:
        prefix (str, optional): Defines a prefix for the created control.
    Returns:
        Node, str: A Node containing the generated root curve
    """
    global_offset_trans = cmds.circle(
        name=f"{prefix}_globalOffset_{core_naming.NamingConstants.Suffix.CTRL}", normal=(0, 1, 0), ch=False, radius=44.5
    )[0]
    cmds.rebuildCurve(global_offset_trans, ch=False, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=20, d=3, tol=0.01)
    core_attr.add_separator_attr(
        target_object=global_offset_trans,
        attr_name=f"rig{core_str.upper_first_char(core_rigging.RiggingConstants.SEPARATOR_CONTROL)}",
    )
    core_rigging.expose_rotation_order(global_offset_trans)
    core_attr.add_attr(
        obj_list=global_offset_trans,
        attr_type="string",
        is_keyable=False,
        attributes=tools_rig_const.RiggerConstants.REF_ATTR_CTRL_GLOBAL_OFFSET,
        verbose=True,
    )
    core_attr.hide_lock_default_attrs(global_offset_trans, scale=True, visibility=True)
    core_color.set_color_outliner(global_offset_trans, rgb_color=core_color.ColorConstants.RigOutliner.CTRL)
    core_color.set_color_viewport(obj_list=global_offset_trans, rgb_color=core_color.ColorConstants.RigControl.CENTER)
    return core_node.Node(global_offset_trans)


def create_utility_groups(geometry=False, skeleton=False, control=False, setup=False, line=False, target_parent=None):
    """
    Creates category groups for the rig.
    This group holds invisible rigging elements used in the automation of the project.
    Args:
        geometry (bool, optional): If True, the geometry group is created.
        skeleton (bool, optional): If True, the skeleton group is created.
        control (bool, optional): If True, the control group is created.
        setup (bool, optional): If True, the setup group is created.
        line (bool, optional): If True, the visualization line group gets created.
        target_parent (str, Node, optional): If provided, groups will be parented to this object after creation.
    Returns:
        dict: A dictionary with lookup attributes (tools_rig_const.RiggerConstants)
        as keys and "Node" objects as values.
              e.g. {tools_rig_const.RiggerConstants.REF_GEOMETRY_ATTR: core_node.Node("group_name")}
    """
    desired_groups = {}
    if geometry:
        _name = tools_rig_const.RiggerConstants.GRP_GEOMETRY_NAME
        _color = core_color.ColorConstants.RigOutliner.GRP_GEOMETRY
        desired_groups[tools_rig_const.RiggerConstants.REF_ATTR_GEOMETRY] = (_name, _color)
    if skeleton:
        _name = tools_rig_const.RiggerConstants.GRP_SKELETON_NAME
        _color = core_color.ColorConstants.RigOutliner.GRP_SKELETON
        desired_groups[tools_rig_const.RiggerConstants.REF_ATTR_SKELETON] = (_name, _color)
    if control:
        _name = tools_rig_const.RiggerConstants.GRP_CONTROL_NAME
        _color = core_color.ColorConstants.RigOutliner.GRP_CONTROL
        desired_groups[tools_rig_const.RiggerConstants.REF_ATTR_CONTROL] = (_name, _color)
    if setup:
        _name = tools_rig_const.RiggerConstants.GRP_SETUP_NAME
        _color = core_color.ColorConstants.RigOutliner.GRP_SETUP
        desired_groups[tools_rig_const.RiggerConstants.REF_ATTR_SETUP] = (_name, _color)
    if line:
        _name = tools_rig_const.RiggerConstants.GRP_LINE_NAME
        _color = None
        desired_groups[tools_rig_const.RiggerConstants.REF_ATTR_LINES] = (_name, _color)

    group_dict = {}
    for attr, (name, color) in desired_groups.items():
        group = cmds.group(name=name, empty=True, world=True)
        core_attr.add_attr(obj_list=group, attr_type="string", is_keyable=False, attributes=attr, verbose=True)
        _node = core_node.Node(group)
        group_dict[attr] = _node
        if color:
            core_color.set_color_outliner(str(_node), rgb_color=color)
        if target_parent:
            core_hrchy.parent(source_objects=_node, target_parent=str(target_parent))
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
                core_hrchy.parent(source_objects=offset, target_parent=parent_proxy)


def get_proxy_offset(proxy_name):
    """
    Return the offset transform (parent) of the provided proxy object. If not found, it returns "None"
    Args:
        proxy_name (str): Name of the attribute where the UUID is stored.
    Returns:
        str, None: If found, the offset object (parent of the proxy), otherwise None
    """
    if not proxy_name or not cmds.objExists(proxy_name):
        logger.debug(f'Unable to find offset for "{str(proxy_name)}".')
        return
    offset_list = cmds.listRelatives(proxy_name, parent=True, typ="transform", fullPath=True) or []
    for offset in offset_list:
        return offset


def get_meta_purpose_from_dict(metadata_dict):
    """
    Gets the meta type of the proxy. A meta type helps identify the purpose of a proxy within a module.
    For example, a type "knee" proxy describes that it will be influenced by the "hip" and "ankle" in a leg.
    This can also be seen as "pointers" to the correct proxy when receiving data from a dictionary.
    Args:
        metadata_dict (dict, None): A dictionary describing a proxy metadata.
    Returns:
        string or None: The meta type string or None when not detected/found.
    """
    if metadata_dict:
        meta_type = metadata_dict.get(tools_rig_const.RiggerConstants.META_PROXY_PURPOSE)
        return meta_type


def get_automation_group(
    name=f"generalAutomation",
    subgroup=None,
    rgb_color=core_color.ColorConstants.RigOutliner.AUTOMATION,
):
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
    _grp_path = f"{setup_grp}|{str(name)}"
    # Find or create automation group (base)
    if name and cmds.objExists(_grp_path):
        _grp_path = core_node.Node(_grp_path)
    else:
        _grp_path = cmds.group(name=name, empty=True, world=True)
        _grp_path = core_node.Node(_grp_path)
        core_color.set_color_outliner(obj_list=_grp_path, rgb_color=rgb_color)
        core_hrchy.parent(source_objects=_grp_path, target_parent=setup_grp)
        if not setup_grp:
            logger.debug(f'Automation group "{str(name)}" could not be properly parented. ' f"Missing setup group.")
    # Find or create automation subgroup (child of the base)
    if subgroup and isinstance(subgroup, str):
        _grp_path_base = _grp_path  # Store base for re-parenting
        _grp_path = f"{_grp_path}|{str(subgroup)}"
        if name and cmds.objExists(_grp_path):
            _grp_path = _grp_path
        else:
            _grp_path = cmds.group(name=subgroup, empty=True, world=True)
            _grp_path = core_node.Node(_grp_path)
            core_hrchy.parent(source_objects=_grp_path, target_parent=_grp_path_base)
            if not setup_grp:
                logger.debug(f'Automation group "{str(name)}" could not be properly parented. ' f"Missing setup group.")
    cmds.select(clear=True)
    if selection:
        try:
            cmds.select(selection=True)
        except Exception as e:
            logger.debug(f"Unable to restore initial selection. Issue: {str(e)}")
    return _grp_path


def get_driven_joint(uuid_string, suffix=core_naming.NamingConstants.Suffix.DRIVEN, constraint_to_source=True):
    """
    Gets the path to a driven joint or create it in case it's missing.
    Driven joints are used to control automation joints or joint hierarchies.
    Args:
        uuid_string (str): UUID str stored in "tools_rig_const.RiggerConstants.JOINT_ATTR_DRIVEN_UUID" used to identify.
        suffix (str, optional): Suffix to add to the newly created driven joint. Default is "driven".
        constraint_to_source (bool, optional): Parent constraint the joint to its source during creation.
                                               Does nothing if driver already exists and is found.
    Returns:
        Node, str: Path to the FK Driver - Node format has string as its base.

    """
    driven_jnt = core_uuid.get_object_from_uuid_attr(
        uuid_string=uuid_string, attr_name=tools_rig_const.RiggerConstants.ATTR_JOINT_DRIVEN_UUID, obj_type="joint"
    )
    if not driven_jnt:
        source_jnt = find_joint_from_uuid(uuid_string)
        if not source_jnt:
            return
        driven_jnt = core_rigging.duplicate_joint_for_automation(joint=source_jnt, suffix=suffix)
        core_attr.delete_user_defined_attrs(obj_list=driven_jnt)
        core_attr.add_attr(
            obj_list=driven_jnt, attr_type="string", attributes=tools_rig_const.RiggerConstants.ATTR_JOINT_DRIVEN_UUID
        )
        core_attr.set_attr(
            attribute_path=f"{driven_jnt}.{tools_rig_const.RiggerConstants.ATTR_JOINT_DRIVEN_UUID}", value=uuid_string
        )
        if constraint_to_source:
            constraint = cmds.parentConstraint(source_jnt, driven_jnt)
            cmds.setAttr(f"{constraint[0]}.interpType", 0)  # Set to No Flip
    return driven_jnt


def get_drivers_list_from_joint(source_joint):
    """
    Gets the list of drivers that are stored in a joint drivers attribute.
    If missing the attribute, it will return an empty list.
    If the string data stored in the attribute is corrupted, it will return an empty list.
    Args:
        source_joint (str): The name of the joint from which to read the drivers attribute.

    Returns:
        list: List of drivers or empty list if none found or invalid.
    """
    drivers = core_attr.get_attr(obj_name=source_joint, attr_name=tools_rig_const.RiggerConstants.ATTR_JOINT_DRIVERS)
    if drivers:
        try:
            drivers = eval(drivers)
            if not isinstance(drivers, list):
                logger.debug("Stored value was not a list.")
                drivers = None
        except Exception as e:
            logger.debug(f"Unable to read joint drivers data. Values will be overwritten. Issue: {e}")
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
    if isinstance(new_drivers, str):
        new_drivers = [new_drivers]
    drivers = get_drivers_list_from_joint(source_joint=target_joint)
    for new_driver in new_drivers:
        if new_driver not in drivers:
            drivers.append(new_driver)
    data = json.dumps(drivers)
    core_attr.set_attr(obj_list=target_joint, attr_list=tools_rig_const.RiggerConstants.ATTR_JOINT_DRIVERS, value=data)


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
        module_uuid = core_attr.get_attr(
            obj_name=source_joint, attr_name=tools_rig_const.RiggerConstants.ATTR_MODULE_UUID
        )
        joint_purpose = core_attr.get_attr(
            obj_name=source_joint, attr_name=tools_rig_const.RiggerConstants.ATTR_JOINT_PURPOSE
        )
        for driver in drivers:
            _driver_uuid = f"{module_uuid}-{driver}"
            if joint_purpose:
                _driver_uuid = f"{_driver_uuid}-{joint_purpose}"
            driver_uuids[driver] = _driver_uuid
    if as_list:
        return list(driver_uuids.values())
    return driver_uuids


def get_generic_driver(source_joint, add_missing_driver=False):
    """
    Gets the generic driver if it exists, or creates one if it doesn't exist.
    Args:
        source_joint (str, Node): The path to a joint. It's expected that this joint contains the drivers attribute.
        add_missing_driver (bool, optional): If active, it will add a generic module before creating a generic
                                             transform/driver that follows the source joint.
    Returns:
        Node, str: the created or found generic driver.
    """
    driver_uuids = get_driver_uuids_from_joint(source_joint=source_joint, as_list=False)
    if tools_rig_const.RiggerDriverTypes.GENERIC in driver_uuids.keys():  # Is Generic Driver available?
        driver_uuid = driver_uuids.get(tools_rig_const.RiggerDriverTypes.GENERIC)
        driver = core_uuid.get_object_from_uuid_attr(
            uuid_string=driver_uuid, attr_name=tools_rig_const.RiggerConstants.ATTR_DRIVER_UUID, obj_type="transform"
        )
        if driver:
            return driver
        # Driver not found, create one
        purpose = core_attr.get_attr(
            obj_name=source_joint, attr_name=tools_rig_const.RiggerConstants.ATTR_JOINT_PURPOSE
        )
        module_uuid = core_attr.get_attr(
            obj_name=source_joint, attr_name=tools_rig_const.RiggerConstants.ATTR_MODULE_UUID
        )
        # Driven Group (For Parented Controls)
        driver = core_hrchy.create_group(
            name=f"{core_naming.get_short_name(source_joint)}_{core_naming.NamingConstants.Suffix.DRIVER}"
        )
        add_driver_uuid_attr(
            target_driver=driver,
            module_uuid=module_uuid,
            driver_type=tools_rig_const.RiggerDriverTypes.GENERIC,
            proxy_purpose=purpose,
        )
        core_cnstr.constraint_targets(source_driver=source_joint, target_driven=driver, maintain_offset=False)
        direction_ctrl = find_ctrl_global_offset()
        if direction_ctrl:
            core_hrchy.parent(source_objects=driver, target_parent=direction_ctrl)
        return driver
    else:
        if add_missing_driver:
            add_driver_to_joint(target_joint=source_joint, new_drivers=tools_rig_const.RiggerDriverTypes.GENERIC)
            return get_generic_driver(source_joint=source_joint, add_missing_driver=False)


def add_driver_uuid_attr(target_driver, module_uuid, driver_type=None, proxy_purpose=None):
    """
    Adds an attributes to be used as driver UUID to the target object. (Target object is the driver/control)
    The value of the attribute is created using the module uuid, the driver type and proxy purpose combined.
    Following this pattern: "<module_uuid>-<driver_type>-<proxy_purpose>" e.g. "abcdef123456-fk-shoulder"
    Args:
        target_driver (str, Node): Path to the object that will receive the driver attributes. e.g. Driver/Control
        module_uuid (str): UUID for the module. This is used to determine the driver UUID value.
        driver_type (str, optional): A string or tag use to identify the control type. e.g. "fk", "ik", "offset"
                                     If not provided, it's assumed to be a generic driver. "RiggerDriverTypes.GENERIC"
        proxy_purpose (str, Proxy, optional): This is the proxy purpose. It can be a string, or the Proxy object.
                                        e.g. "shoulder" or the shoulder proxy object. If a Proxy object is provided,
                                        then the function tries to extract the meta "purpose" value from it.
                                        If not present or not provided, this portion of the data becomes "unknown".
    Returns:
        str: target UUID value created by the operation.
             Pattern: "<module_uuid>-<driver_type>-<proxy_purpose>" e.g. "abcdef123456-fk-shoulder"
    """
    if not module_uuid or not isinstance(module_uuid, str):
        module_uuid = "unknown"
    uuid = f"{module_uuid}"
    # Add Driver Type
    if not driver_type:
        driver_type = "unknown"  # Unknown driver / Missing
    uuid = f"{uuid}-{driver_type}"
    # Add Purpose
    if proxy_purpose and hasattr(proxy_purpose, "get_meta_purpose") and callable(proxy_purpose.get_meta_purpose):
        proxy_purpose = proxy_purpose.get_meta_purpose()
    if not proxy_purpose:
        proxy_purpose = "unknown"  # Unknown purpose / Missing
    uuid = f"{uuid}-{proxy_purpose}"
    # Add Attribute and Set Value
    if not target_driver or not cmds.objExists(target_driver):
        logger.warning(f"Unable to add UUID attribute. Target object is missing.")
        return
    uuid_attr = core_attr.add_attr(
        obj_list=target_driver,
        attr_type="string",
        is_keyable=False,
        attributes=tools_rig_const.RiggerConstants.ATTR_DRIVER_UUID,
        verbose=True,
    )[0]
    core_attr.set_attr(attribute_path=uuid_attr, value=str(uuid))
    return uuid


def connect_supporting_driver(source_parent_driver, target_child_driver):
    """
    Connects a driver that already has a driverUUID defined to a dependant auxiliary/supporting driver (child).
    This allows for a control to have multiple child drivers without requiring extra driver types for each one of them.

    Connection: <source_driver.driverUUID> -> <target_offset.driverChild>
    e.g. "cog_ctrl.driverUUID" -> "cog_offset_ctrl.driverChild"

    Args:
        source_parent_driver (str, Node): Driver (often controls) with already populated driverUUID attribute. (parent)
        target_child_driver (str, Node): Auxiliary control attr that receives data from "ATTR_DRIVER_PARENT". (child)
    Returns:
        list: List of created attributes. e.g. 'cog_offset_ctrl.driverChild'
    """
    if not source_parent_driver or not cmds.objExists(source_parent_driver):
        logger.debug(f"Unable to connect driver offset. Provided source driver is missing.")
        return
    if not target_child_driver or not cmds.objExists(target_child_driver):
        logger.debug(f"Unable to connect driver offset. Provided target is missing.")
        return
    is_uuid_present = cmds.objExists(f"{source_parent_driver}.{tools_rig_const.RiggerConstants.ATTR_DRIVER_UUID}")
    if not is_uuid_present:
        logger.debug(f'Unable to connect driver offset. Provided target does not have a "driverUUID" attribute.')
        return
    attr = core_attr.add_attr(
        obj_list=target_child_driver,
        attr_type="string",
        attributes=tools_rig_const.RiggerConstants.ATTR_DRIVER_CHILD,
    )
    core_attr.connect_attr(
        source_attr=f"{source_parent_driver}.{tools_rig_const.RiggerConstants.ATTR_DRIVER_UUID}",
        target_attr_list=f"{target_child_driver}.{tools_rig_const.RiggerConstants.ATTR_DRIVER_CHILD}",
    )
    if attr and isinstance(attr, list):
        return attr[0]


def get_supporting_drivers(source_driver):
    """
    Gets supporting drivers from the destination connection of the driverUUID of a source driver.

    Args:
        source_driver (str, Node): Driver (often controls) with already populated driverUUID attribute.
    Returns:
        list: A list of connection destination objects that are auxiliary/supporting drivers (child of the main driver)
    """
    if not source_driver or not cmds.objExists(source_driver):
        logger.debug(f"Unable to get driver offset. Provided source driver is missing.")
        return []
    source_attr_path = f"{source_driver}.{tools_rig_const.RiggerConstants.ATTR_DRIVER_UUID}"
    if not cmds.objExists(source_attr_path):
        logger.debug(f'Unable to get driver offset. Provided source driver does not have a "driverUUID" attribute.')
        return []
    supporting_drivers = []
    for destination in cmds.listConnections(source_attr_path, destination=True) or []:
        supporting_drivers.append(core_node.Node(destination))
    return supporting_drivers


def create_twist_joints(
    start_joint,
    end_joint,
    number_of_twist=2,
    copy_start=False,
    copy_end=False,
    aim_axis="X",
):
    """
    Creates the twist joints and connections in a joint chain.

    Args:
        start_joint (str): First Joint of the chain.
        end_joint (str): Last Joint of the chain.
        number_of_twist (index, float): Number of twist joints.
        copy_start (bool): Copy the first joint of the chain.
        copy_end (bool): Copy the last joint of the chain.
        aim_axis (str): Primary joint aim axis.

    Returns:
        list: A list of all the twist joints.

    """
    twist_joints = []
    chain_distance = cmds.getAttr(f"{end_joint}.translate{aim_axis}")
    twist_distance = chain_distance / (number_of_twist + 1)
    joint_name = start_joint.split("_JNT")[0]
    twist_index = 1
    if copy_start:
        start_twist = cmds.duplicate(start_joint, n=f"[{joint_name}Twist0{twist_index}_JNT", po=True)[0]
        twist_index += 1
        cmds.parent(start_twist, start_joint)
        twist_joints.append(start_twist)
    for number in range(number_of_twist):
        twist_joint = cmds.duplicate(start_joint, n=f"[{joint_name}Twist0{twist_index}_JNT", po=True)[0]
        cmds.parent(twist_joint, start_joint)
        cmds.setAttr(f"{twist_joint}.translate{aim_axis}", twist_distance * (number + 1))
        twist_index += 1
        twist_joints.append(twist_joint)
    if copy_end:
        end_twist = cmds.duplicate(start_joint, n=f"[{joint_name}Twist0{twist_index}_JNT", po=True)[0]
        cmds.parent(end_twist, start_joint)
        cmds.setAttr(f"{end_twist}.translate{aim_axis}", chain_distance)
        twist_joints.append(end_twist)

    for jnt in twist_joints:
        core_attr.set_attr(
            obj_list=jnt,
            attr_list=tools_rig_const.RiggerConstants.ATTR_JOINT_UUID,
            value=core_uuid.generate_uuid(remove_dashes=True),
        )
        core_attr.set_attr(
            obj_list=jnt,
            attr_list=tools_rig_const.RiggerConstants.ATTR_JOINT_PURPOSE,
            value=jnt.split("_")[1],
        )
        core_attr.set_attr(
            obj_list=jnt,
            attr_list=tools_rig_const.RiggerConstants.ATTR_JOINT_DRIVERS,
            value=tools_rig_const.RiggerDriverTypes.TWIST,
        )

    return twist_joints


def create_twist_setup(twist_jnt_list, mid_joints, side, reverse=False, reverse_matrix=False):
    """Creates native Maya twist extraction networks for a joint chain.

    Args:
        twist_jnt_list (list): List of all the joints.
        mid_joints (float): Number of joints that are not a duplicate of the start/end of the chain.
        side (str): Side of the operation.
        reverse (bool): Reverse the twist (usually for upperArm / upperLeg behaviour).
        reverse_matrix (bool): Additional operation for reversing the matrix (Usually for upperLeg).

    Returns:
        list: Native twist setup network nodes created for the joints.
    """
    twist_setup_nodes = []
    reverse_joints = list(reversed(twist_jnt_list))
    for index, jnt in enumerate(twist_jnt_list):
        twist_value = (index + 1) * (1 / (mid_joints + 1))
        driver_joint = cmds.listRelatives(cmds.listRelatives(jnt, p=True, fullPath=True))[0]
        if reverse:
            driver_joint = cmds.listRelatives(jnt, p=True, fullPath=True)[0]
            twist_value = -(reverse_joints.index(jnt) + 1) * (1 / (mid_joints + 1))

        driver_rest_offset_matrix = None
        if reverse_matrix:
            twist_value = -(reverse_joints.index(jnt) + 1) * (1 / (mid_joints + 1))
            if core_naming.NamingConstants.Prefix.RIGHT in side:
                driver_rest_offset_matrix = (
                    -1,
                    0,
                    0,
                    0,
                    0,
                    1,
                    0,
                    0,
                    0,
                    0,
                    -1,
                    0,
                    0,
                    0,
                    0,
                    1,
                )
            elif core_naming.NamingConstants.Prefix.LEFT in side:
                twist_value = (reverse_joints.index(jnt) + 1) * (1 / (mid_joints + 1))
                driver_rest_offset_matrix = (
                    1,
                    0,
                    0,
                    0,
                    0,
                    -1,
                    0,
                    0,
                    0,
                    0,
                    1,
                    0,
                    0,
                    0,
                    0,
                    1,
                )

        twist_setup = core_rigging.create_twist_extraction_network(
            driver=driver_joint,
            driven=jnt,
            twist_weight=twist_value,
            twist_axis=0,
            driver_rest_offset_matrix=driver_rest_offset_matrix,
            name=f"{jnt}_twistNode",
        )
        twist_setup_nodes.append(twist_setup)
    return twist_setup_nodes


def extract_twist_rotation(twist_jnt_list):
    """
    Resets the twist rotation targets for a list of twist joints by setting their
    corresponding native setup's targetRestMatrix attribute.

    This function temporarily suspends viewport refresh for performance,
    sets the character to A-pose, updates each twist setup's targetRestMatrix
    using the inverse of the joint's offsetParentMatrix, then resets the character
    to T-pose and resumes refresh.

    Args:
        twist_jnt_list (list[str]): List of twist joint names to process.
    """
    cmds.refresh(suspend=True)
    core_pose.set_apose()
    rest_mat = OpenMayaApi.MMatrix()
    for jnt in twist_jnt_list:
        twist_setup = core_rigging.get_twist_setup_from_target(jnt)
        if not twist_setup:
            cmds.warning(f'Unable to extract twist rotation. No twist setup found for "{jnt}".')
            continue
        cmds.setAttr(f"{twist_setup}.targetRestMatrix", rest_mat, type="matrix")
        twist_offset_parent_mat = cmds.getAttr(f"{jnt}.offsetParentMatrix")
        inverse_twist_offset_parent_mat = OpenMayaApi.MMatrix(twist_offset_parent_mat).inverse()
        cmds.setAttr(f"{twist_setup}.targetRestMatrix", inverse_twist_offset_parent_mat, type="matrix")
    core_pose.set_tpose()
    cmds.refresh(suspend=False)


def get_world_ref_loc(name=f"world_ref_{core_naming.NamingConstants.Suffix.LOC}"):
    """
    Gets the path to a world reference group or create it in case it can't be found.
    Args:
        name (str, optional): Name of the reference group (found inside the "setup_grp")
    Returns:
        Node, str: Path to the reference group - Node format has string as its base.
    """
    automation_grp = get_automation_group(name="spaceAutomation")
    cmds.setAttr(f"{automation_grp}.visibility", 0)
    # Find or create automation group (base)
    if name and cmds.objExists(name):
        _world_grp_path = name
    else:
        _world_grp_path = cmds.spaceLocator(n=name)[0]
        core_hrchy.parent(source_objects=_world_grp_path, target_parent=automation_grp)
        if not automation_grp:
            logger.debug(f'Reference group "{str(name)}" could not be properly parented. ' f"Missing automation group.")
    cmds.select(clear=True)
    return _world_grp_path


def create_follow_setup(
    control,
    parent,
    attr_name="followParent",
    ref_loc=True,
    default_value=1,
    constraint_type="orient",
):
    """
    Creates a double constraint and attribute in a control to follow the parent.
    Args:
        control (Node): Control to follow the parent/world orientation.
        parent (Node): Object that is driving the control, usually a joint or a group.
        attr_name (str): Name of the attribute to be drive the switch.
        ref_loc (bool): If reference groups are being used instead of direct constraint (useful for different rotation
        orders).
        default_value (int): 0 or 1, the default value of the attribute.
        constraint_type (str): "orient" by default, the other accepted values are "parent" and "point"
    Returns:
        str: Path to  the generated constraint.
    """
    if not isinstance(constraint_type, str):
        logger.warning(
            f"The supplied constraint type is not a string."
            f" Cannot create the follow setup for {core_naming.get_short_name(control)}"
        )
        return

    if constraint_type not in ["orient", "parent", "point"]:
        logger.warning(f"The supplied constraint type is not 'orient', 'parent' or 'point'. Cannot create the follow.")
        return

    # add follow attribute type
    follow_type_name_dict = {"orient": "Rotation", "point": "Position", "parent": ""}
    attr_name = f"{attr_name}{follow_type_name_dict[constraint_type]}"
    core_attr.add_attr(
        obj_list=control,
        attributes=attr_name,
        attr_type="float",
        maximum=1,
        minimum=0,
        default=default_value,
    )
    parent_offset_suffix = f"parentOffset{follow_type_name_dict[constraint_type]}"
    parent_offset = tools_rig_frm.ModuleGeneric().create_control_groups(
        control=control, suffix_list=parent_offset_suffix
    )[0]

    ctrl_parent = cmds.listRelatives(control, p=True, fullPath=True)[0]
    cmds.parent(parent_offset, ctrl_parent)
    cmds.parent(control, parent_offset)
    world_loc = get_world_ref_loc()
    cmds.setAttr(f"{world_loc}.visibility", 0)
    ref_rev = cmds.createNode("reverse", n=f"{parent_offset.get_short_name()}_rev")
    cmds.connectAttr(f"{control}.{attr_name}", f"{ref_rev}.inputX")

    if ref_loc:
        name = core_naming.get_short_name(parent).capitalize()
        parent_ref_loc = get_world_ref_loc(name=f"{name}_ref_{core_naming.NamingConstants.Suffix.LOC}")
        core_trans.match_translate(source=parent, target_list=parent_ref_loc)
        cmds.setAttr(f"{parent_ref_loc}.visibility", 0)
        cmds.parentConstraint(parent, parent_ref_loc, mo=True)
        source_cnstr = parent_ref_loc
    else:
        source_cnstr = ctrl_parent

    _constraint_func = core_cnstr.get_constraint_function(constraint_type)
    follow_constraint = _constraint_func(source_cnstr, world_loc, parent_offset, maintainOffset=True)[0]
    cmds.connectAttr(f"{control}.{attr_name}", f"{follow_constraint}.w0")
    cmds.connectAttr(f"{ref_rev}.outputX", f"{follow_constraint}.w1")

    return follow_constraint


def create_follow_enum_setup(
    control,
    parent_list,
    attribute_item=None,
    ref_loc=True,
    default_value=1,
    constraint_type="parent",
):
    """
    Creates a double constraint and attribute in a control to follow the parent.
    Args:
        control (Node): Control to follow the parent/world orientation.
        parent_list (list): List of objects that will be driving the ctrl.
        attribute_item (str, optional): Object that should receive the follow attribute. If None, control is used.
        ref_loc (bool): If reference groups are being used instead of direct constraint (useful for different rotation
        orders).
        default_value (int): 0 or 1, the default value of the attribute.
        constraint_type (str): "parent" by default, other accepted values are "parent" and "point".
    """

    if not isinstance(constraint_type, str):
        logger.warning(
            f"The supplied constraint type is not a string."
            f" Cannot create the follow setup for {core_naming.get_short_name(control)}"
        )
        return

    if constraint_type not in ["orient", "parent", "point"]:
        logger.warning(f"The supplied constraint type is not 'orient', 'parent' or 'point'. Cannot create the follow.")
        return

    # add enum attribute
    parent_grps = ["World"]
    for parent in parent_list:
        if cmds.nodeType(parent) == "joint":
            name = cmds.getAttr(f"{parent}.{tools_rig_const.RiggerConstants.ATTR_BASE_NAME}")
        elif (
            len(core_naming.get_short_name(parent).split("_")) <= 2
            or core_naming.get_short_name(parent).split("_")[1] == ""
        ):
            name = parent
        else:
            name = core_naming.get_short_name(parent).split("_")[1].capitalize()
        parent_grps.append(name)
    caps_parent_grps = []
    for grp in parent_grps:
        caps_parent_grps.append(grp.capitalize())
    attr_names = ":".join(caps_parent_grps)
    if not attribute_item:
        attribute_item = control
    core_attr.add_attr(
        obj_list=attribute_item,
        attributes="space",
        attr_type="enum",
        enum=attr_names,
        default=default_value,
    )
    parent_offset = tools_rig_frm.ModuleGeneric().create_control_groups(control=control, suffix_list="parentOffset")[0]
    ctrl_parent = cmds.listRelatives(control, p=True, fullPath=True)[0]
    cmds.parent(parent_offset, ctrl_parent)
    cmds.parent(control, parent_offset)
    world_loc = get_world_ref_loc()
    cmds.setAttr(f"{world_loc}.visibility", 0)

    if ref_loc:
        parent_loc_list = []
        for parent in parent_list:
            name = core_naming.get_short_name(parent).capitalize()
            parent_ref_loc = get_world_ref_loc(name=f"{name}_ref_{core_naming.NamingConstants.Suffix.LOC}")
            core_trans.match_translate(source=parent, target_list=parent_ref_loc)
            cmds.setAttr(f"{parent_ref_loc}.visibility", 0)
            cmds.parentConstraint(parent, parent_ref_loc, mo=True)
            parent_loc_list.append(parent_ref_loc)
        source_cnstr = parent_loc_list
    else:
        source_cnstr = ctrl_parent
    constraint_string = f"cmds.{constraint_type}Constraint(world_loc, source_cnstr, parent_offset, mo=True)"
    follow_constraint = eval(constraint_string)[0]
    for parent in parent_grps:
        for number in range(len(parent_grps)):
            if number == parent_grps.index(parent):
                value = 1
            else:
                value = 0
            cmds.setDrivenKeyframe(
                f"{follow_constraint}.w{parent_grps.index(parent)}",
                cd=f"{attribute_item}.space",
                dv=number,
                v=value,
            )

    return follow_constraint


def get_skeleton_joints(full_hierarchy=True, top_level_fallback=True):
    """
    Gets all joints found in the skeleton group of a rig (or alternatively joints found in the scene root/assemblies)
    Args:
        full_hierarchy (bool, optional): When True, the entire hierarchy of joints is returned, (a.k.a. their children)
                                         When False, only immediate children of the skeleton group is returned.
        top_level_fallback (bool, optional): If True, it will return top level (assemblies) joints when no joints
                                             are found inside the rig skeleton group.

    Returns:
        list: A list of joints found in the skeleton group for a rig or as top parents.
    """
    joints = []
    skl_grp = find_skeleton_group()

    # Rig Joints
    scene_joints = [jnt for jnt in cmds.ls(long=True) if cmds.nodeType(jnt) == "joint"]
    if scene_joints:
        for jnt in scene_joints:
            parent = cmds.listRelatives(jnt, p=True, fullPath=True)
            if parent and parent[0].endswith(str(skl_grp)):
                joints.append(jnt)

    # Top Level Fallback
    if top_level_fallback and not joints:
        joints = [jnt for jnt in cmds.ls(assemblies=True, long=True) if cmds.nodeType(jnt) == "joint"]

    # Full Hierarchy
    if full_hierarchy:
        descendants = []
        for jnt in joints:
            descendants += core_hrchy.get_hierarchy(root=jnt, maya_type=OpenMaya.MFn.kJoint, full_path=True)
        return descendants

    return joints


def get_single_skeleton_root_joint(top_level_fallback=True):
    """
    Gets the root joint. The first joint found in the skeleton group or the first joint found in the world.

    Args:
        top_level_fallback (bool, optional): If True, it will return top level (assemblies) joints when no joints
                                             are found inside the rig skeleton group.

    Returns:
        str: the root joint of the export skeleton.
    """
    joints = get_skeleton_joints(full_hierarchy=False, top_level_fallback=top_level_fallback)
    if joints:
        return joints[0]


def get_control_rig_control_pose_and_bind_pose_as_dict(control_pose_name=None):
    """
    Gets the control rig pose values and bind pose values in two dictionaries.
    This is supposed to be called at the end of the control rig building process, when it is in a "vanilla"
    state, without extra keys, ready for Animation. That's the state (T-pose/rig pose) that we want to store.

    Returns:
        tuple: Control attributes for the control rig pose and bind pose.
    """

    # T-POSE ---------------------------------------------------------------
    # Get rig controls from metadata
    _rigs_metadata = get_rigs_metadata()
    if not _rigs_metadata:
        logger.debug("Couldn't find the rig metadata in the scene.")
        return
    rig_uuid, rig_metadata = next(iter(_rigs_metadata.items()))
    controls = get_drivers_from_rig_metadata(rig_metadata=rig_metadata)
    if not controls:
        return

    # Get the dictionary of the attributes of the rig controls
    t_pose_controls_attrs_dict = {}
    for ctrl in controls:
        attr_dict = core_attr.get_attrs_as_dict(ctrl)
        t_pose_controls_attrs_dict.update(attr_dict)

    # A-POSE ---------------------------------------------------------------
    # Get mapping between joints and FK control drivers from metadata
    joint_control_map = {}
    rig_joints = get_joints_from_rig_metadata(rig_metadata, top_parents_only=False)
    for jnt in rig_joints:
        if cmds.attributeQuery(tools_rig_const.RiggerConstants.ATTR_JOINT_PURPOSE, node=jnt, ex=True):
            jnt_drivers = find_drivers_from_joint(jnt)
            if jnt_drivers:
                if tools_rig_const.RiggerDriverTypes.FK in jnt_drivers.keys():
                    joint_control_map[jnt] = jnt_drivers.get(tools_rig_const.RiggerDriverTypes.FK)

    # Set Global and COG special cases
    global_purpose_ctrl = get_drivers_from_rig_metadata(
        rig_metadata=rig_metadata, filter_driver_purpose=tools_rig_const.RiggerConstants.REF_VALUE_PURPOSE_GLOBAL
    )
    global_fk_ctrl = get_drivers_from_rig_metadata(
        rig_metadata=rig_metadata, filter_driver_type=tools_rig_const.RiggerDriverTypes.FK
    )
    global_ctrl = list(set(global_purpose_ctrl) & set(global_fk_ctrl))  # intersection of Global type and Fk purpose
    cog_ctrl = get_drivers_from_rig_metadata(
        rig_metadata=rig_metadata,
        filter_driver_type=tools_rig_const.RiggerDriverTypes.COG,
    )
    _attr_jnt_purpose = tools_rig_const.RiggerConstants.ATTR_JOINT_PURPOSE
    _joints_with_attributes = [jnt for jnt in rig_joints if cmds.attributeQuery(_attr_jnt_purpose, node=jnt, ex=True)]
    root_jnts = [jnt for jnt in _joints_with_attributes if cmds.getAttr(f"{jnt}.{_attr_jnt_purpose}") == "root"]
    hips_jnts = [jnt for jnt in _joints_with_attributes if cmds.getAttr(f"{jnt}.{_attr_jnt_purpose}") == "hips"]
    if global_ctrl:
        if root_jnts:
            joint_control_map[root_jnts[0]] = global_ctrl[0]
    if cog_ctrl:
        if hips_jnts:
            joint_control_map[hips_jnts[0]] = cog_ctrl[0]

    # Get T-pose translations
    # - We need the delta between T-pose and A-pose.
    # - Translations between T-pose and A-pose are supposed to happen only on main controls
    # - this is due to the preservation of the proportions between bind/rest/a-pose and the rig/t-pose
    # - for animation. With this assumption and the fact that the main Global control should remain at the origin,
    # - we target specifically the hips joint (biped pattern), the only one that could be moved to perhaps
    # - align better with the model, or for other character placement purposes.
    hips_t_pos = [0.0, 0.0, 0.0]
    if hips_jnts:
        hips_t_pos = cmds.xform(hips_jnts[0], query=True, translation=True, os=True)
        hips_t_pos = [float(format(p, ".4f")) for p in hips_t_pos]

    # Set Skeleton A-pose
    cmds.refresh(suspend=True)
    core_pose.set_apose()

    # Get A-pose rotations
    controls_rotations_dict = {}
    for jnt, control in joint_control_map.items():
        jnt_rot = cmds.xform(jnt, query=True, rotation=True, os=True)
        jnt_rot = [float(format(r, ".4f")) for r in jnt_rot]
        controls_rotations_dict[control] = jnt_rot

    # Get Delta translations
    hips_a_pos = [0.0, 0.0, 0.0]
    if hips_jnts:
        hips_a_pos = cmds.xform(hips_jnts[0], query=True, translation=True, os=True)
        hips_a_pos = [float(format(p, ".4f")) for p in hips_a_pos]
    hips_delta_pos = [hips_a_pos[i] - hips_t_pos[i] for i in range(len(hips_a_pos))]
    cmds.refresh(suspend=False)

    # Get the dictionary of the attributes of the rig controls
    a_pose_controls_attrs_dict = copy.deepcopy(t_pose_controls_attrs_dict)
    for jnt, control in joint_control_map.items():
        for ir, r_axis in enumerate(["rx", "ry", "rz"]):
            rot_attr = f"{control}.{r_axis}"
            a_pose_controls_attrs_dict[rot_attr] = controls_rotations_dict[control][ir]

    if hips_delta_pos != [0.0, 0.0, 0.0]:
        # The orientation is not the same between the hips_joint and the COG in the biped.
        # TODO: find another way, not hard-coded to get the right axis delta
        hips_delta_pos = [hips_delta_pos[2], hips_delta_pos[0], hips_delta_pos[1]]
        for ip, p_axis in enumerate(["tx", "ty", "tz"]):
            pos_attr = f"{joint_control_map[hips_jnts[0]]}.{p_axis}"
            a_pose_controls_attrs_dict[pos_attr] = hips_delta_pos[ip]

    core_pose.set_dagpose(pose_name=control_pose_name)

    return t_pose_controls_attrs_dict, a_pose_controls_attrs_dict


def get_control_rig_tpose_and_apose_as_dict():
    """Gets legacy T-pose and A-pose metadata dictionaries.

    This compatibility wrapper treats the T-pose slot as the project's generic control rig pose and the A-pose slot
    as its bind pose.

    Args:
        control_pose_name (str, optional): Skeleton DAG pose used as the control rig pose.

    Returns:
        tuple: Control attributes for the control rig pose and bind pose.
    """

    if not control_pose_name:
        control_pose_name = core_naming.NamingConstants.Poses.TPOSE
    return get_control_rig_control_pose_and_bind_pose_as_dict()


def create_control_visualization_line(control, end_obj):
    """
    Builds a line connected to start and end objects.

    Args:
        control (Node): start point for the line
        end_obj (Node): end point for the line
    """

    # variables
    _attr_show_aim = "showAimLine"
    _grp_aim_lines = f"aimLines_{core_naming.NamingConstants.Suffix.GRP}"

    # aim lines group
    aim_grp = get_automation_group(subgroup=_grp_aim_lines)
    cmds.setAttr(f"{aim_grp}.visibility", 0)

    # create line
    line_items = core_curve.create_connection_line(object_a=control, object_b=end_obj, line_width=2)
    line_curve = line_items[0]

    # parent
    core_hrchy.parent(source_objects=line_items, target_parent=aim_grp)
    core_hrchy.parent(source_objects=line_curve, target_parent=control)
    core_attr.set_attr(obj_list=line_curve, attr_list=["tx", "ty", "tz"], value=0)

    # visibility attribute
    core_attr.add_attr(obj_list=control, attributes=_attr_show_aim, attr_type="bool", default=1)
    cmds.connectAttr(f"{control}.showAimLine", f"{line_curve}.visibility")

    # attributes
    cmds.setAttr(f"{line_curve}.inheritsTransform", 0)  # So it can be parented to control
    cmds.setAttr(f"{line_curve}.overrideEnabled", 1)  # Enable Modes (So it can be seen as template)
    cmds.setAttr(f"{line_curve}.overrideDisplayType", 1)  # Template
    core_attr.hide_lock_default_attrs(obj_list=line_curve, translate=True, rotate=True, scale=True, visibility=True)

    # change line name based on control
    control_name = control.get_short_name()
    current_suffix = control_name.split("_")[-1]
    if any(current_suffix == value for key, value in core_naming.NamingConstants.Suffix.__dict__.items()):
        new_line_name = control_name.replace(f"_{current_suffix}", f"_{core_naming.NamingConstants.Suffix.LINE}")
    else:
        new_line_name = f"{control_name}_{core_naming.NamingConstants.Suffix.LINE}"
    line_curve = cmds.rename(line_curve, new_line_name)

    return line_curve


def get_rigs_metadata(namespace=None):
    """
    Looks for the rig root transforms (group) by searching for objects containing the expected lookup attribute.
    Not to be confused with the root control curve. This is the parent TRANSFORM.
    This function return all detected groups with such attribute. This is used to find all rigs in the scene.
    Args:
        namespace (str): by default None. If None, it returns all the rigs_metadata in the scene.
                         If a namespace is provided, it returns only the matching one.
                         If the namespace is an empty string ("") it returns only the rigs without namespace.
    Returns:
        dict: A dictionary with metadata about all rigs detected in the scene.
              Key is the UUID of the rig project, value is another dictionary metadata related to the rig.
              e.g.
              {"dz88fm": {"name": "My Character",
                          "project": {},
                          "meshes": "|rig|geometry_grp",
                          "skeleton": "|rig|skeleton_grp",
                          "controls": "|rig|control_grp",
                          "setup": "|rig|setup_grp",
                          "tPose": {},
                         }
              }
    """
    import json

    _lookup_attr = tools_rig_const.RiggerConstants.REF_ATTR_ROOT_RIG
    _attr_name = tools_rig_const.RiggerConstants.ATTR_RIG_PROJECT_NAME
    _attr_data = tools_rig_const.RiggerConstants.ATTR_RIG_PROJECT_DATA
    _attr_tpose_data = tools_rig_const.RiggerConstants.ATTR_RIG_TPOSE_DATA
    _attr_apose_data = tools_rig_const.RiggerConstants.ATTR_RIG_APOSE_DATA
    _attr_collections = tools_rig_const.RiggerConstants.ATTR_RIG_COLLECTIONS

    _attr_geo_grp = tools_rig_const.RiggerConstants.ATTR_RIG_GEOMETRY_GRP
    _attr_skm_grp = tools_rig_const.RiggerConstants.ATTR_RIG_SKELETON_GRP
    _attr_ctrl_grp = tools_rig_const.RiggerConstants.ATTR_RIG_CONTROL_GRP
    _attr_setup_grp = tools_rig_const.RiggerConstants.ATTR_RIG_SETUP_GRP
    dest_attrs = [_attr_geo_grp, _attr_skm_grp, _attr_ctrl_grp, _attr_setup_grp]

    obj_list = cmds.ls(typ="transform", long=True) or []

    rigs_metadata_dict = {}

    for obj in obj_list:
        if cmds.objExists(f"{obj}.{_lookup_attr}"):  # If missing this, it's a rig root group
            if namespace is not None:
                _obj_namespace = core_nspace.get_namespace(obj)
                if _obj_namespace != namespace:
                    continue

            metadata_dict = {}
            _uuid = core_attr.get_attr(attribute_path=f"{obj}.{_lookup_attr}")
            _name = core_attr.get_attr(attribute_path=f"{obj}.{_attr_name}")
            _data = core_attr.get_attr(attribute_path=f"{obj}.{_attr_data}")
            _tpose = None
            _apose = None
            if cmds.attributeQuery(_attr_tpose_data, node=obj, ex=True):  # backward compatibility
                _tpose = core_attr.get_attr(attribute_path=f"{obj}.{_attr_tpose_data}")
            if cmds.attributeQuery(_attr_apose_data, node=obj, ex=True):  # backward compatibility
                _apose = core_attr.get_attr(attribute_path=f"{obj}.{_attr_apose_data}")

            metadata_dict[_attr_name] = _name

            for _dest_attr in dest_attrs:
                metadata_dict[_dest_attr] = ""  # Initialize Attr
                dest_connections = cmds.listConnections(f"{obj}.{_dest_attr}", destination=True, plugs=True)
                if dest_connections:
                    for connection in dest_connections:
                        destination_object = connection.split(".")[0]
                        metadata_dict[_dest_attr] = destination_object

            metadata_dict[_attr_data] = json.loads(_data)
            metadata_dict[_attr_tpose_data] = {}
            metadata_dict[_attr_apose_data] = {}
            if _tpose:
                metadata_dict[_attr_tpose_data] = json.loads(_tpose)
            if _apose:
                metadata_dict[_attr_apose_data] = json.loads(_apose)

            # Collections
            metadata_dict[_attr_collections] = {}  # Initialize empty for backward compatibility
            if cmds.attributeQuery(_attr_collections, node=obj, ex=True):
                _collections = core_attr.get_attr(attribute_path=f"{obj}.{_attr_collections}")
                if _collections:  # Empty cannot be parsed
                    metadata_dict[_attr_collections] = json.loads(_collections)

            core_iter.add_unique_dict_key(input_dict=rigs_metadata_dict, new_key=_uuid, new_value=metadata_dict)

    return rigs_metadata_dict


def get_joints_from_rig_metadata(rig_metadata, top_parents_only=True):
    """
    Gets joints from a rig metadata (rigs found in the scene)
    Args:
        rig_metadata (dict): A rig metadata. This is the value stored in a dict generated using "get_rigs_metadata".
        top_parents_only (bool, optional): If True, only top parent joints (usually just one, the root) is returned.
                                           If False, all "rig|skeleton" joints (including children) are returned.

    Returns:
        list: The long path to the joints found in the skeleton group (these are the joints exported to another app)

    Example:
        rigs_metadata = get_rigs_metadata()
        rig_uuid, rig_metadata = next(iter(rigs_metadata.items()))
        joints_to_export = get_joints_from_rig_metadata(rig_metadata)
    """
    skeleton_grp = rig_metadata.get(tools_rig_const.RiggerConstants.ATTR_RIG_SKELETON_GRP)

    if not skeleton_grp or not cmds.objExists(skeleton_grp):
        return []

    if top_parents_only:
        # List only top parent joints in the skeleton group
        parent_joints = cmds.listRelatives(skeleton_grp, type="joint", children=True, fullPath=True) or []
        return parent_joints
    else:
        # List all joints under the skeleton group
        all_joints = cmds.listRelatives(skeleton_grp, type="joint", allDescendents=True, fullPath=True) or []
        return all_joints


def get_meshes_from_rig_metadata(rig_metadata, skinned_only=True):
    """
    Gets meshes from a rig metadata (rigs found in the scene)
    Args:
        rig_metadata (dict): A rig metadata. This is the value stored in a dict generated using "get_rigs_metadata".
        skinned_only (bool, optional): If True, only return transforms whose meshes are bound to joints.

    Returns:
        list: The long path to the joints found in the skeleton group (these are the joints exported to another app)

    Example:
        rigs_metadata = get_rigs_metadata()
        rig_uuid, rig_metadata = next(iter(rigs_metadata.items()))
        meshes_to_export = get_meshes_from_rig_metadata(a_rig_metadata, skinned_only=True)
    """
    geometry_grp = rig_metadata.get(tools_rig_const.RiggerConstants.ATTR_RIG_GEOMETRY_GRP)

    if not geometry_grp or not cmds.objExists(geometry_grp):
        return []

    descendants = cmds.listRelatives(geometry_grp, allDescendents=True, fullPath=True) or []

    # Filter out the meshes
    meshes = cmds.ls(descendants, type="mesh", long=True)

    if not meshes:
        return []

    # Get the transform nodes of the meshes
    transforms = cmds.listRelatives(meshes, parent=True, fullPath=True)

    if skinned_only:
        # Filter transforms whose meshes are skinned (bound to joints)
        skinned_transforms = []
        for mesh, transform in zip(meshes, transforms):
            # Get skin cluster associated with the mesh
            skin_clusters = cmds.ls(cmds.listHistory(mesh), type="skinCluster")
            if skin_clusters:
                skinned_transforms.append(transform)
        return skinned_transforms
    else:
        return list(set(transforms))


def get_module_uuids_from_rig_metadata(rig_metadata):
    """
    Gets a list of UUIDs from a rig metadata (rigs found in the scene)
    Args:
        rig_metadata (dict): A rig metadata. This is the value stored in a dict generated using "get_rigs_metadata".

    Returns:
        list: A list of module UUIDs. e.g. [""]

    Example:
        rigs_metadata = get_rigs_metadata()
        rig_uuid, rig_metadata = next(iter(rigs_metadata.items()))
        module_uuids = get_module_uuids_from_rig_metadata(a_rig_metadata)
    """
    project_dict = rig_metadata.get(tools_rig_const.RiggerConstants.ATTR_RIG_PROJECT_DATA)

    if "modules" not in project_dict.keys():
        logger.warning(f'Unable to get modules UUIDs. Rig metadata is missing the "modules" key.')
        return []

    modules = project_dict.get("modules")
    if not isinstance(modules, list):
        logger.warning(f'Unable to get modules UUIDs. Rig metadata "modules" is not carrying a list of modules.')
        return []

    uuids = []
    for module in modules:
        _uuid = module.get("uuid")
        if _uuid and isinstance(_uuid, str):
            uuids.append(_uuid)

    return uuids


def get_collections_from_rig_metadata(rig_metadata, exclude_private=False):
    """
    Gets a dictionary describing the collections defined for this rig.
    If nothing was defined, this will be an empty dictionary.

    If exclude_private is True, collections whose keys start with an underscore
    ('_') will be removed from the returned dictionary.

    Args:
        rig_metadata (dict): A rig metadata. This is the value stored in a dict
                             generated using "get_rigs_metadata".
        exclude_private (bool, optional): If True, filters out collections whose
                                          keys start with an underscore. Defaults to False.

    Returns:
        dict: A dictionary containing the collections defined for this rig,
              otherwise an empty dictionary.
    """
    # 1. Retrieve the base collections dictionary
    base_collections = rig_metadata.get(tools_rig_const.RiggerConstants.ATTR_RIG_COLLECTIONS, {})

    if not exclude_private:
        # If no exclusion is needed, return the base dictionary directly.
        return base_collections

    # 2. Filter out private collections using a dictionary comprehension
    # We copy the non-private items (keys that do NOT start with '_')
    filtered_collections = {key: value for key, value in base_collections.items() if not key.startswith("_")}
    return filtered_collections


def get_project_name_from_metadata(rig_metadata):
    """
    Gets the project name from the rig metadata. (The entire project JSON is stored in the metadata)
    Args:
        rig_metadata (dict): A rig metadata. This is the value stored in a dict generated using "get_rigs_metadata".

    Returns:
        str: The project name as it's stored in the rig metadata.

    Example:
        rigs_metadata = get_rigs_metadata()
        rig_uuid, rig_metadata = next(iter(rigs_metadata.items()))
        project_name = get_project_name_from_metadata(a_rig_metadata)
    """
    project_dict = rig_metadata.get(tools_rig_const.RiggerConstants.ATTR_RIG_PROJECT_DATA)

    key_name = "name"
    if key_name not in project_dict.keys():
        logger.warning(f'Unable to get project name. Rig metadata is missing the "{key_name}" key.')
        return ""

    return project_dict.get(key_name) or ""


def get_project_alias_from_metadata(rig_metadata, project_name_fallback=True):
    """
    Gets a list of UUIDs from a rig metadata (rigs found in the scene)
    Args:
        rig_metadata (dict): A rig metadata. This is the value stored in a dict generated using "get_rigs_metadata".
        project_name_fallback (bool, optional): If True, this function will return the project name when a project
                                                alias is not available or an empty string.

    Returns:
        str: The project alias as it's stored in the rig metadata or the project name when alias is not available.

    Example:
        rigs_metadata = get_rigs_metadata()
        rig_uuid, rig_metadata = next(iter(rigs_metadata.items()))
        project_alias = get_project_alias_from_metadata(a_rig_metadata, project_name_fallback=True)
    """
    project_dict = rig_metadata.get(tools_rig_const.RiggerConstants.ATTR_RIG_PROJECT_DATA)
    # Get Project Preferences
    project_prefs = {}
    key_prefs = "preferences"
    if key_prefs not in project_dict.keys():
        logger.warning(f'Unable to get project preferences. Rig metadata is missing the "{project_prefs}" key.')
    else:
        project_prefs = project_dict.get(key_prefs) or {}
    # Get Project Alias
    _alias = ""
    key_alias = "alias"
    if key_alias not in project_prefs.keys():  # Backwards compatibility (That's why the log is "debug")
        logger.debug(f'Unable to get project alias. Project data found in metadata is missing the "{key_alias}" key.')
    else:
        _alias = project_prefs.get(key_alias) or ""
    # Project Name Fallback
    if project_name_fallback and not _alias:
        _alias = get_project_name_from_metadata(rig_metadata=rig_metadata)

    return _alias


def get_drivers_from_rig_metadata(
    rig_metadata=None,
    filter_driver_type=None,
    filter_driver_purpose=None,
    filter_prefix=None,
    attr_selection=False,
    attr_keyable_only=True,
    controls_only=True,
    cache_driver_uuids=True,
):
    """
    Gets a list of detected drivers from a rig metadata (rigs found in the scene)
    Args:
        rig_metadata (dict, optional): A rig metadata. This is the value stored in a dict generated using
                                       "get_rigs_metadata". If None, it attempts to get the first rig in the scene.
        filter_driver_type (str, list, optional): If provided, only drivers of this type are returned.
        filter_driver_purpose (str, list, optional): If provided, only drivers of this purpose are returned.
        filter_prefix (str, list, optional): If provided, only elements containing the prefix are selected.
                                             The short name is used during filtering.
        attr_selection (bool): If True, retrieves attributes instead of objects.
        attr_keyable_only (bool): If True, retrieves only keyable attributes only. If False, retrieves all attributes.
        controls_only (bool): If True, retrieves only objects that have shapes.
        cache_driver_uuids (bool, optional): When True, this function becomes more optimized through the use of a
                                             caching system that reduces the needed maya calls during query.

    Returns:
        list: A list of Nodes (str) matching the drivers from the rig metadata. (Essentially the rig controls)

    Example:
        rigs_metadata = get_rigs_metadata()
        rig_uuid, rig_metadata = next(iter(rigs_metadata.items()))
        drivers_to_select = get_module_uuids_from_rig_metadata(a_rig_metadata)
    """
    if not rig_metadata:
        _rigs_metadata_list = get_rigs_metadata()
        if not _rigs_metadata_list:
            return []
        rig_uuid, rig_metadata = next(iter(_rigs_metadata_list.items()))

    # Initialize list with the controls connected directly to the rig (usually the globals)
    drivers = []
    project_data = rig_metadata.get(tools_rig_const.RiggerConstants.ATTR_RIG_PROJECT_DATA)
    project_uuid = project_data.get("uuid")

    # Get Cache
    _cached_driver_uuids = None
    if cache_driver_uuids:
        _cached_driver_uuids = cache_driver_uuids_to_dict()

    if project_uuid:
        drivers += find_drivers_from_module(
            source_uuid=project_uuid,
            filter_driver_type=filter_driver_type,
            filter_driver_purpose=filter_driver_purpose,
            cached_driver_uuids=_cached_driver_uuids,
        )

    # Add the modules controls
    module_uuids = get_module_uuids_from_rig_metadata(rig_metadata)
    for uuid in module_uuids:
        drivers += find_drivers_from_module(
            source_uuid=uuid,
            filter_driver_type=filter_driver_type,
            filter_driver_purpose=filter_driver_purpose,
            cached_driver_uuids=_cached_driver_uuids,
        )

    # Filters
    if filter_prefix:
        if isinstance(filter_prefix, str):
            filter_prefix = [filter_prefix]  # Convert to list for consistency
        _prefix_filtered = []
        for driver in drivers:
            # Get the short name (ignores hierarchy)
            short_name = core_naming.get_short_name(driver)

            # Remove the namespace if present
            if ":" in short_name:
                short_name = short_name.split(":")[-1]

            # Check if the short name starts with any of the prefixes
            if any(short_name.startswith(prefix) for prefix in filter_prefix):
                _prefix_filtered.append(driver)
        drivers = _prefix_filtered

    # Controls only
    if controls_only:
        if drivers:
            for driver in reversed(drivers):
                driver_shapes = cmds.listRelatives(driver, shapes=True, fullPath=True) or []
                if not driver_shapes:
                    drivers.remove(driver)

    # Filter Descendants inside rig parent (Fixes issues where rigs with the same UUID are loaded in the scene)
    controls_grp = rig_metadata.get(tools_rig_const.RiggerConstants.ATTR_RIG_CONTROL_GRP)
    if controls_grp and cmds.objExists(controls_grp):
        controls_grp = core_naming.get_long_name(controls_grp)
        drivers = [drv for drv in drivers if str(drv).startswith(f"{controls_grp}|")]

    # Not Attribute, return objects
    if not attr_selection:
        return drivers
    # Query type was attributes
    _attrs = []
    for obj in drivers:
        if not cmds.objExists(obj):
            cmds.warning(f"Object '{obj}' does not exist. Skipping...")
            continue
        # Retrieve attributes based on the keyable_only flag
        if attr_keyable_only:
            attrs = cmds.listAttr(obj, keyable=True)
        else:
            attrs = cmds.listAttr(obj)
        if attrs:
            # Create the object.attribute strings
            _attrs.extend([f"{obj}.{attr}" for attr in attrs])
    if not _attrs:
        return
    return _attrs


def get_tpose_from_rig_metadata(rig_metadata=None):
    """
    Gets the T-pose of the rig from the metadata (rigs found in the scene).
    Args:
        rig_metadata (dict, optional): A rig metadata. This is the value stored in a dict generated using
                                       "get_rigs_metadata". If None, it attempts to get the first rig in the scene.
    Returns:
        dict: The T-pose dictionary with the controls attributes and their values to set.
    """
    if not rig_metadata:
        _rigs_metadata = get_rigs_metadata()
        if not _rigs_metadata:
            return
        rig_uuid, rig_metadata = next(iter(_rigs_metadata.items()))
    if not isinstance(rig_metadata, dict):
        logger.debug("Given rig metadata must be a dict.")
        return
    if tools_rig_const.RiggerConstants.ATTR_RIG_TPOSE_DATA not in rig_metadata.keys():
        logger.debug("T-pose key missing from the given dictionary.")
        return

    tpose_dict = rig_metadata.get(tools_rig_const.RiggerConstants.ATTR_RIG_TPOSE_DATA)

    return tpose_dict


def get_apose_from_rig_metadata(rig_metadata=None):
    """
    Gets the A-pose of the rig from the metadata (rigs found in the scene).
    Args:
        rig_metadata (dict, optional): A rig metadata. This is the value stored in a dict generated using
                                       "get_rigs_metadata". If None, it attempts to get the first rig in the scene.
    Returns:
        dict: The A-pose dictionary with the controls attributes and their values to set.
    """
    if not rig_metadata:
        _rigs_metadata = get_rigs_metadata()
        if not _rigs_metadata:
            return
        rig_uuid, rig_metadata = next(iter(_rigs_metadata.items()))
    if not isinstance(rig_metadata, dict):
        logger.debug("Given rig metadata must be a dict.")
        return
    if tools_rig_const.RiggerConstants.ATTR_RIG_APOSE_DATA not in rig_metadata.keys():
        logger.debug("A-pose key missing from the given dictionary.")
        return

    apose_dict = rig_metadata.get(tools_rig_const.RiggerConstants.ATTR_RIG_APOSE_DATA)

    return apose_dict


def filter_elements_by_collection(
    elements_to_filter,
    collections_data,
    filter_query=None,
    ignore_namespaces=True,
    exclude_private=False,
    isolate_collections=False,
):
    """
    Filters a list of elements based on a query against named collections, supporting
    inclusion, exclusion, wildcard, private exclusion, and multi-collection isolation.

    Args:
        elements_to_filter (list[str]): A list of element names to be filtered.
        collections_data (dict): The dictionary containing all collection data.
        filter_query (str or list[str], optional): The query defining the rules.
        ignore_namespaces (bool, optional): If True, compares the short name of elements,
                                            ignoring namespaces. Defaults to True.
        exclude_private (bool, optional): If True, automatically excludes all collections
                                          whose keys in `collections_data` start with an
                                          underscore '_'. Defaults to False.
        isolate_collections (bool, optional): If True, and the `filter_query`
                                              all other collections are automatically
                                              added to the exclusion list. Defaults to False.

    Returns:
        list[str]: The filtered list of element names, preserving original order.
    """
    # 0. Initial checks and setup
    if not filter_query or filter_query == "*" or filter_query == ["*"]:
        if not exclude_private:
            return list(elements_to_filter)

    def _get_short_name_no_ns(node_name):
        """
        Strips namespace and gets short name.
        Args:
            node_name (str): Name of the node potentially with namespace and long.

        Returns:
            str: No namespace short version of the name.
        """
        no_ns = core_nspace.strip_namespace(node_name)
        return core_naming.get_short_name(no_ns)

    get_name = _get_short_name_no_ns if ignore_namespaces else core_naming.get_short_name
    initial_elements_set = {get_name(elem) for elem in elements_to_filter}

    # --- 1. Parse the filter query into tokens ---
    tokens = []
    if isinstance(filter_query, str):
        normalized_string = filter_query.replace(",", " ")
        tokens = [token for token in normalized_string.split(" ") if token]
    elif isinstance(filter_query, list):
        tokens = filter_query
    else:
        logger.warning(
            f"Invalid filter_query type: {type(filter_query)}. " "Expected str or list. Returning original list."
        )
        return list(elements_to_filter)

    # --- 2. Separate tokens into inclusion and exclusion collections ---
    include_collection_names = set()
    exclude_collection_names = set()
    is_wildcard_included = False

    for token in tokens:
        if token == "*":
            is_wildcard_included = True
        elif token.startswith("-"):
            has_exclusion_tokens = True  # Set flag if any exclusion token is found
            collection_name = token[1:]
            if collection_name:
                exclude_collection_names.add(collection_name)
        else:
            include_collection_names.add(token)

    # --- Isolation Filter Mode (isolate_collections) ---
    if isolate_collections and not is_wildcard_included and include_collection_names:
        # Isolation is activated if:
        # 1. The flag is True.
        # 2. No wildcard is present.
        # 3. At least one inclusion token is present.

        all_collection_keys = set(collections_data.keys())

        # Add all collections EXCEPT those being explicitly included to the exclusion set.
        collections_to_exclude = all_collection_keys.difference(include_collection_names)

        exclude_collection_names.update(collections_to_exclude)

    # --- 2.2 Existing Feature: Automatically exclude private collections ---
    if exclude_private:
        private_collections = {key for key in collections_data if key.startswith("_")}
        exclude_collection_names.update(private_collections)

        if is_wildcard_included and not include_collection_names:
            pass

            # --- 3. Build element sets from collections_data ---
    inclusion_sets = []
    elements_to_exclude = set()

    for name in include_collection_names:
        members = collections_data.get(name)
        if members:
            inclusion_sets.append({get_name(member) for member in members})
        else:
            logger.warning(f"Include collection '{name}' not found in metadata.")

    for name in exclude_collection_names:
        members = collections_data.get(name)
        if members:
            elements_to_exclude.update(get_name(member) for member in members)
        else:
            logger.warning(f"Exclude collection '{name}' not found in metadata.")

    # --- 4. Determine the final set of elements based on the logic ---
    working_set = set()

    if is_wildcard_included:
        # Scenario 1: Wildcard Mode
        working_set = initial_elements_set

        if inclusion_sets:
            inclusion_union = set.union(*inclusion_sets)
            working_set = working_set.intersection(inclusion_union)

    elif inclusion_sets:
        # Scenario 2: Inclusion Mode (This covers the 'isolate' case)
        inclusion_union = set.union(*inclusion_sets)
        working_set = inclusion_union.intersection(initial_elements_set)

    else:
        # Scenario 3: Exclusion-Only Mode
        all_collection_sets = []
        for name, members in collections_data.items():
            # Only use collections not destined for exclusion to build the base intersection.
            if name not in exclude_collection_names:
                all_collection_sets.append({get_name(member) for member in members})

        if all_collection_sets:
            base_set_all_collections = set.intersection(*all_collection_sets)
            working_set = initial_elements_set.intersection(base_set_all_collections)
        else:
            working_set = set()

    # Apply final exclusions (difference)
    final_set = working_set.difference(elements_to_exclude)

    # --- 5. Rebuild list, preserving original order ---
    return [elem for elem in elements_to_filter if get_name(elem) in final_set]


def filter_rig_joints_by_collection(
    rig_metadata, filter_query=None, ignore_namespaces=True, exclude_private=False, isolate_collections=False
):
    """
    Gets bind joints from rig metadata and filters them using a collection query.

    Args:
        rig_metadata (dict): The rig metadata dictionary.
        filter_query (str or list[str], optional): The query defining the inclusion and
                                                   exclusion rules. Defaults to None.
        ignore_namespaces (bool, optional): If True, namespaces are ignored during
                                            comparison. Defaults to True.
        exclude_private (bool, optional): When active, it will automatically ignore elements from private collections.
        isolate_collections (bool, optional): If True, and the `filter_query`
                                              all other collections are automatically
                                              added to the exclusion list. Defaults to False.
    Returns:
        list[str]: The filtered list of joint names. Returns an empty list if
                   no bind joints are found in the metadata.
    """
    all_bind_joints = get_joints_from_rig_metadata(rig_metadata=rig_metadata, top_parents_only=False)
    collections_data = get_collections_from_rig_metadata(rig_metadata=rig_metadata)

    if not all_bind_joints:
        return []

    return filter_elements_by_collection(
        elements_to_filter=all_bind_joints,
        collections_data=collections_data,
        filter_query=filter_query,
        ignore_namespaces=ignore_namespaces,
        exclude_private=exclude_private,
        isolate_collections=isolate_collections,
    )


def selected_joints_to_module_generic(auto_include_children=True):
    """
    Converts selected joints into
    Args:
        auto_include_children (bool, optional): If active, children joints will be automatically included.
    Returns:
        ModuleGeneric: A generic module containing selected joints.
    """
    # Manage Selection
    initial_selection = cmds.ls(selection=True, long=True)
    if auto_include_children:
        cmds.select(hierarchy=True)
    selection_joints = cmds.ls(selection=True, typ="joint", long=True)

    # Define UUIDs:
    jnt_mapping = {}
    for jnt in selection_joints:
        uuid_attr = f"{jnt}.{tools_rig_const.RiggerConstants.ATTR_JOINT_UUID}"
        _uuid = core_uuid.generate_uuid(remove_dashes=True)
        if cmds.objExists(uuid_attr):
            _uuid = cmds.getAttr(uuid_attr)
        jnt_mapping[jnt] = _uuid

    # Create Module and Proxies
    a_generic_module = tools_rig_frm.ModuleGeneric()

    # Set Orientation Method to "inherit"
    a_generic_module.set_orientation_method(method="inherit")

    for jnt, uuid in jnt_mapping.items():
        new_proxy = a_generic_module.add_new_proxy()
        new_proxy.set_uuid(uuid)
        new_proxy.set_name(core_naming.get_short_name(jnt))

        # Joint Parent (Maya Side)
        parent = cmds.listRelatives(jnt, parent=True, fullPath=True)
        if parent:
            parent_uuid = jnt_mapping.get(parent[0])
            new_proxy.set_parent_uuid(parent_uuid)

        new_proxy.read_data_from_scene(obj_path=jnt)

        _radius = cmds.getAttr(f"{jnt}.radius")
        new_proxy.set_locator_scale(_radius)

    # Recover Initial Selection
    if initial_selection:
        try:
            cmds.select(initial_selection)
        except Exception as e:
            logger.debug(f"Unable to recover initial selection. Issue: {e}")

    return a_generic_module


def set_rig_pose(namespace=None, pose="t"):
    """Sets a control rig pose using stored metadata values.
    Args:
        namespace (str, optional): the rig namespace.
                                   If Namespace is None, the code attempts to get it from the first element selected.
                                   Then if nothing is selected it sets the first of all the rigs in the scene.
                                   If Namespace is "", it sets the first of all the rigs without namespace.
                                   If Namespace is a string, it sets the matching rig, if it exists.
        pose (str, optional): it accepts only "t" or "a". "t" by default.
    """
    if namespace is False:
        namespace = None
    if namespace is None:
        _selection = cmds.ls(sl=True)
        if _selection:
            namespace = core_nspace.get_namespace(_selection[0])

    rigs_metadata = get_rigs_metadata(namespace=namespace)
    if not rigs_metadata:
        namespace_string = "without (empty string)" if namespace == "" else namespace
        logger.warning(f"Cannot retrieve metadata for the given namespace: {namespace_string}")
        return

    if pose != "a" and pose != "t":
        pose = "t"

    # Get rig metadata
    rig_uuid, rig_metadata = next(iter(rigs_metadata.items()))
    # Get the namespace from metadata Controls message
    controls_grp = rig_metadata.get(tools_rig_const.RiggerConstants.ATTR_RIG_CONTROL_GRP)
    controls_namespace = core_nspace.get_namespace(controls_grp)
    missing_attributes = []

    # Get pose attributes dictionary
    pose_dict = {}
    if pose == "t":
        pose_dict = get_tpose_from_rig_metadata(rig_metadata=rig_metadata)
        if not pose_dict:
            logger.warning("Control rig pose data retrieved by the rig metadata is empty.")
            return
    elif pose == "a":
        pose_dict = get_apose_from_rig_metadata(rig_metadata=rig_metadata)
        if not pose_dict:
            logger.warning("A-pose data retrieved by the rig metadata is empty.")
            return
    if not pose_dict:
        return

    # Set the pose
    cmds.undoInfo(openChunk=True)
    for attr_path, attr_value in pose_dict.items():
        if controls_namespace:
            attr_path = attr_path.replace("|", f"|{controls_namespace}:")
        if cmds.objExists(attr_path):
            core_attr.set_attr(attr_path, attr_value)
        else:
            missing_attributes.append(attr_path)
    if missing_attributes:
        _missing_string = "\n".join(attr for attr in missing_attributes)
        logger.warning(f"The following attributes are missing and won't be set for the rig pose:{missing_attributes}")
    cmds.undoInfo(closeChunk=True)


def set_rig_control_pose(namespace=None):
    """Sets the rig to its stored control rig pose.

    Args:
        namespace (str, optional): Namespace of the rig to update.
    """
    set_rig_pose(namespace=namespace, pose="t")


def set_rig_bind_pose(namespace=None):
    """Sets the rig to its stored bind pose.

    Args:
        namespace (str, optional): Namespace of the rig to update.
    """
    set_rig_pose(namespace=namespace, pose="a")


def set_rig_tpose(namespace=None):
    """Sets the control rig with the given namespace in T-pose using the stored metadata values.
    Args:
        namespace (str, optional): the rig namespace.
                                   If Namespace is None, the code attempts to get it from the first element selected.
                                   Then if nothing is selected it sets the first of all the rigs in the scene.
                                   If Namespace is "", it sets the first of all the rigs without namespace.
                                   If Namespace is a string, it sets the matching rig, if it exists.
    """
    set_rig_control_pose(namespace=namespace)


def set_rig_apose(namespace=None):
    """Sets the control rig with the given namespace in A-pose using the stored metadata values.
    Args:
        namespace (str, optional): the rig namespace.
                                   If Namespace is None, the code attempts to get it from the first element selected.
                                   Then if nothing is selected it sets the first of all the rigs in the scene.
                                   If Namespace is "", it sets the first of all the rigs without namespace.
                                   If Namespace is a string, it sets the matching rig, if it exists.
    """
    set_rig_bind_pose(namespace=namespace)


def update_uuids_in_dict(data, uuid_mapping):
    """
    Recursively updates UUIDs in a nested dictionary using the given UUID mapping.
    Args:
        data (dict): The original dictionary with UUIDs.
        uuid_mapping (dict): A dictionary where keys are old UUIDs, and values are the new UUIDs to replace them with.

    Returns:
        dict: Updated dictionary with replaced UUIDs.
    """
    if isinstance(data, dict):
        updated_dict = {}
        for key, value in data.items():
            # Recursively update nested dictionaries
            updated_key = uuid_mapping.get(key, key)
            updated_value = update_uuids_in_dict(value, uuid_mapping)

            # Check if the value is a string UUID and replace it
            if isinstance(updated_value, str):
                updated_value = uuid_mapping.get(updated_value, updated_value)

            updated_dict[updated_key] = updated_value
        return updated_dict

    elif isinstance(data, list):
        # Recursively handle lists
        return [update_uuids_in_dict(item, uuid_mapping) for item in data]

    elif isinstance(data, str):
        # Replace strings directly if they match a UUID
        return uuid_mapping.get(data, data)

    # Return the value unchanged if not dict, list, or string
    return data


def reference_and_attach_rig(file_path, target):
    """
    References a file and attaches it to the attachment target object
    Args:
        file_path (str): Path to the file that will be referenced.
        target (str): Path to the object that will drive the reference rig. e.g. a hand joint
    Returns:
        str: Path to the created constraints, None otherwise.
    """
    if not os.path.exists(file_path):
        logging.warning(f"Unable to reference file. File not found: {file_path}")
        return

    rigs_metadata = get_rigs_metadata()

    # Import Reference
    namespace = os.path.splitext(os.path.basename(file_path))[0]  # Filename as namespace
    _imported_cache = cmds.file(file_path, returnNewNodes=True, reference=True, namespace=namespace)

    # Get Global Control from Imported Rig
    updated_rigs_metadata = get_rigs_metadata()
    actual_new = {key: value for key, value in updated_rigs_metadata.items() if key not in rigs_metadata}
    imported_rig_uuid, imported_rig_metadata = next(iter(actual_new.items()))  # Grab first new rig metadata available
    _driver_purpose = tools_rig_const.RiggerConstants.REF_VALUE_PURPOSE_GLOBAL
    _driver_type = tools_rig_const.RiggerDriverTypes.FK
    global_control = get_drivers_from_rig_metadata(
        rig_metadata=imported_rig_metadata,
        controls_only=True,
        filter_driver_purpose=_driver_purpose,
        filter_driver_type=_driver_type,
    )

    if not global_control:
        logging.warning(f"Referenced file missing global control. Constraint operation was skipped. File: {file_path}")
        return
    global_control = global_control[0]
    if not target:
        logging.warning(f"Target attach object not found. Constraint operation was skipped. File: {file_path}")
        return

    return cmds.parentConstraint(target, global_control, maintainOffset=False)


def reference_and_attach_rig_to_driver(
    file_path,
    filter_prefix,
    filter_driver_type,
    filter_driver_purpose,
    use_multi_rig_qt_dialog=True,
):
    """
    References a file and attaches it to the first filtered object.
    Args:
        file_path (str): Path to the file that will be referenced.
        filter_driver_type (str, list): If provided, only drivers of this type are returned.
        filter_driver_purpose (str, list): If provided, only drivers of this purpose are returned.
        filter_prefix (str, list): If provided, only elements containing the prefix are selected.
                                             The short name is used during filtering.
        use_multi_rig_qt_dialog (bool, optional): If True, this function will show a dialog when multiple target rigs
                                                  are detected in the scene. When off, the first detected rig will be
                                                  automatically used for the attachment.
    Returns:
        str: Path to the created constraints, None otherwise.
    """
    if not os.path.exists(file_path):
        logging.warning(f"Unable to reference file. File not found: {file_path}")
        return

    rigs_metadata = get_rigs_metadata()
    rig_metadata = None  # Target rig

    if len(rigs_metadata) == 0:
        logging.warning(f"Unable to processed with operation. No rigs detected in the scene.")
        return

    if not use_multi_rig_qt_dialog and len(rigs_metadata) > 1:
        rig_uuid, rig_metadata = next(iter(rigs_metadata.items()))

    if len(rigs_metadata) > 1:
        try:
            import gt.ui.qt_import as ui_qt
            import gt.ui.qt_utils as ui_qt_utils

            maya_window = ui_qt_utils.get_maya_main_window()
            if not maya_window:
                raise Exception("No Maya window detected")

            # Show Save Dialog
            message_box = ui_qt.QtWidgets.QMessageBox(maya_window)
            message_box.setWindowTitle("Warning: Multiple rigs detected!")
            message_box.setText(
                "Multiple rigs were detected in the scene.\n"
                "Which rig would you like to use for the attach operation?"
            )

            metadata_button_pairs = {}
            for uuid, metadata in rigs_metadata.items():
                rig_name = metadata.get(f"name")
                if rig_name:
                    rig_button = message_box.addButton(rig_name, ui_qt.QtWidgets.QMessageBox.AcceptRole)
                    metadata_button_pairs[rig_button] = metadata

            # Add buttons
            cancel_button = message_box.addButton("Cancel", ui_qt.QtWidgets.QMessageBox.DestructiveRole)

            # Execute the message box and get the user response
            message_box.exec_()

            if message_box.clickedButton() in metadata_button_pairs:
                rig_metadata = metadata_button_pairs.get(message_box.clickedButton())

            elif message_box.clickedButton() == cancel_button:
                logging.info(f"Reference and attach operation was cancelled.")
                return
        except Exception as e:
            logging.warning(f"Unable to display rig selection dialog. Using first detected rig instead. Issue: {e}")
            rig_uuid, rig_metadata = next(iter(rigs_metadata.items()))
    else:
        rig_uuid, rig_metadata = next(iter(rigs_metadata.items()))

    if not rig_metadata:
        logging.warning(f"Unable to processed with operation. Rigs were detected but were missing metadata.")
        return

    target_driver = get_drivers_from_rig_metadata(
        rig_metadata=rig_metadata,
        controls_only=True,
        filter_prefix=filter_prefix,
        filter_driver_type=filter_driver_type,
        filter_driver_purpose=filter_driver_purpose,
    )

    if target_driver:
        target_driver = target_driver[0]
    else:
        logging.warning(
            f"Unable to find attachment target. Driver query didn't return anything. "
            f"(Prefix: {filter_prefix}, Type: {filter_driver_type}, Purpose: {filter_driver_purpose})"
        )

    return reference_and_attach_rig(file_path=file_path, target=target_driver)


def reference_and_attach_rig_to_selection(file_path):
    """
    Attaches a reference rig to a selected object. Operation is cancelled if nothing is selected.
    Args:
        file_path (str): Path to the file that will be referenced.

    Returns:
        str: Path to the created constraints, None otherwise.
    """
    selection = cmds.ls(selection=True)
    if not selection or len(selection) > 1:
        logging.warning(f"Please select one target object and try again.")
        return

    return reference_and_attach_rig(file_path=file_path, target=selection[0])


def reference_and_attach_rig_to_socket(file_path, side_prefix="L"):
    """
    Attaches a reference rig to a selected object. Operation is cancelled if nothing is selected.
    Args:
        file_path (str): Path to the file that will be referenced.
        side_prefix (str, optional): Used to define what side to look for when detecting the hand driver.
                                     In most cases, it can only be "L" for left, or "R" for right.
                                     The only exceptions would be complex creatures with more than two arms.

    Returns:
        str: Path to the created constraints, None otherwise.
    """
    import gt.tools.auto_rigger.modules.module_socket as tools_mod_socket

    return reference_and_attach_rig_to_driver(
        file_path=file_path,
        filter_prefix=side_prefix,
        filter_driver_type=tools_rig_const.RiggerDriverTypes.FK,
        filter_driver_purpose=[tools_mod_socket.PURPOSE_SOCKET_PARENT, tools_mod_socket.PURPOSE_SOCKET_CHILD],
    )


def show_dialog_reference_and_attach(ref_function, kwargs=None):
    """
    Shows a dialog asking for a rig file.
    If one is provided, it's reference and attached using the provided reference functions (ref_function)

    Args:
        ref_function (callable): A reference and attach functions to be used with the selected file.
                                 The only functions compatible with this are the ones named "reference_and_attach_*".
        kwargs (dict, optional): Keyword Arguments used by the callable reference and attach function.
    """
    import gt.ui.file_dialog as ui_file_dialog

    # File Path
    file_path = ui_file_dialog.file_dialog(
        write_mode=False,
        file_filter=tools_rig_const.RiggerConstants.MAYA_FILE_FILTER,
        ok_caption="Rig Maya File",
        cancel_caption="Cancel",
    )
    if not file_path:
        return  # Cancel operation

    if not kwargs:
        kwargs = {}

    ref_function(file_path=file_path, **kwargs)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    print("#" * 80)  # Separator
    scene_rigs_metadata = get_rigs_metadata()
    print(f"Number of detected rigs: {len(scene_rigs_metadata)}")
    a_rig_uuid, a_rig_metadata = next(iter(scene_rigs_metadata.items()))  # Grab first available rig
    print(f"Rig Metadata Keys: {len(a_rig_metadata)}")
    # joints_to_export = get_joints_from_rig_metadata(a_rig_metadata, top_parents_only=False)
    # print(f"Joint to Export: {joints_to_export}")
    # meshes_to_export = get_meshes_from_rig_metadata(a_rig_metadata, skinned_only=True)
    # print(f"Meshes to Export: {meshes_to_export}")
    # module_uuids_list = get_module_uuids_from_rig_metadata(a_rig_metadata)
    # print(f"Module UUIDs: {module_uuids_list}")
    # rig_drivers = get_drivers_from_rig_metadata(a_rig_metadata, controls_only=True)
    # print(f"Rig Drivers: {rig_drivers}")
    # cmds.select(rig_drivers)

    # New Collections Data and Query functions
    collections = get_collections_from_rig_metadata(a_rig_metadata)
    print(f"Collection Keys: {len(collections)}")

    # # ----------------------- Ignore Filter (All Joints) -----------------------
    # filtered_all_joints = filter_rig_joints_by_collection(
    #     rig_metadata=a_rig_metadata,
    #     filter_query=None,  # Can be none, string or List[str]
    # )
    # # print(f"Filtered (All Joints): {filtered_all_joints}")
    # print(f"Length Filtered (All Joints): {len(filtered_all_joints)}")  # When None or "*" it returns all elements.
    #
    # # --------------------- Ignore Filter (Include Filter) ---------------------
    # filtered_face_joints = filter_rig_joints_by_collection(
    #     rig_metadata=a_rig_metadata,
    #     filter_query="face",
    # )
    # # print(f"Filtered (Facial Joints Only): {filtered_face_joints}")
    # print(f"Length Filtered (Facial Joints Only): {len(filtered_face_joints)}")
    #
    # # ------------ Ignore Filter (Include Filter, Comma Separated) --------------
    # filtered_twist_corrective_joints = filter_rig_joints_by_collection(
    #     rig_metadata=a_rig_metadata,
    #     filter_query="twist, corrective",
    # )
    # # print(f"Filtered (Facial Joints Only): {filtered_twist_corrective_joints}")
    # print(f"Length Filtered (Twist and Corrective Joints Only): {len(filtered_twist_corrective_joints)}")
    #
    # # --------------------- Ignore Filter (Exclude Filter) ---------------------
    # filtered_body_joints = filter_rig_joints_by_collection(
    #     rig_metadata=a_rig_metadata,
    #     filter_query="-face -twist -corrective",
    # )
    # # print(f"Filtered (Body Joints Only): {filtered_body_joints}")
    # print(f"Length Filtered (Body Joints Only): {len(filtered_body_joints)}")
    #
    # # ------------------ Mixed Filter (Other Data Type Filter) ------s------------
    # filtered_body_joints_list = filter_rig_joints_by_collection(
    #     rig_metadata=a_rig_metadata,
    #     filter_query=["-face", "-_twist", "-_corrective"],
    # )
    # # print(f"Filtered From List (Body Joints Only): {filtered_body_joints_list}")
    # print(f"Length Filtered From List (Body Joints Only): {len(filtered_body_joints_list)}")
    #
    # # Check Length
    # result = f"Add numbers to check lengths: "
    # result += f"{len(filtered_face_joints)} + {len(filtered_twist_corrective_joints)} + {len(filtered_body_joints)}"
    # result += f" = {len(filtered_face_joints) + len(filtered_twist_corrective_joints) + len(filtered_body_joints)}"
    # print(result)

    # # ------------------------------ Collection Features ------------------------------
    # # --- Public/Private Collections ---
    # collections_all = get_collections_from_rig_metadata(a_rig_metadata, exclude_private=False)
    # print(f"All Collections: {list(collections_all.keys())}")  # = ['face', '_twist', '_corrective', 'body']
    #
    # collections_public = get_collections_from_rig_metadata(a_rig_metadata, exclude_private=True)
    # print(f"Public Collections: {list(collections_public.keys())}")  # = ['face', 'body']
    #
    # # --- Auto Exclude Private and Isolate Collections ---
    # # BODY ONLY
    # filtered_body_joints_list = filter_rig_joints_by_collection(
    #     rig_metadata=a_rig_metadata,
    #     filter_query="body",
    #     exclude_private=True,
    # )
    # print(f"Body Joints Only: {len(filtered_body_joints_list)}")  # No twist, corrective, or face joints
    #
    # # FACE ONLY
    # filtered_face_joints_list = filter_rig_joints_by_collection(
    #     rig_metadata=a_rig_metadata,
    #     filter_query="face",
    #     exclude_private=True,
    # )
    # print(f"Face Joints Only: {len(filtered_face_joints_list)}")  # No twist, corrective, or body joints

    # ------------------------------ Rig Alias ------------------------------
    project_name = get_project_name_from_metadata(a_rig_metadata)
    print(f'project_name: "{project_name}"')
    project_alias = get_project_alias_from_metadata(a_rig_metadata, project_name_fallback=True)
    print(f'project_alias: "{project_alias}"')
    project_alias = get_project_alias_from_metadata(a_rig_metadata, project_name_fallback=False)
    print(f'project_alias: "{project_alias}" (No project name fallback)')
