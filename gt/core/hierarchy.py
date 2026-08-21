"""
Hierarchy module

Import Line:
    import gt.core.hierarchy as core_hrchy
"""

import gt.core.transform as core_trans
import gt.core.feedback as core_fback
import gt.core.naming as core_naming
import gt.core.attr as core_attr
import gt.core.node as core_node
import maya.api.OpenMaya as om2
import maya.OpenMaya as om
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_JOINT_PARENT_COMPENSATION_ATTR = "gtJointParentCompensation"
_JOINT_PARENT_TARGET_ATTR = "gtJointParentTarget"


def _parent_joint_preserve_world(child, target_parent=None):
    """Parents a joint directly while preserving its world matrix.

    Maya's default absolute joint parenting can insert an unnamed transform when
    the requested world transform cannot be represented by translate and
    jointOrient alone. Parenting relatively first and restoring the world matrix
    prevents that hidden compensation node from becoming part of the hierarchy.

    Args:
        child (str, Node): Joint to reparent.
        target_parent (str, Node, optional): New parent. None parents to world.

    Returns:
        list: Names returned by Maya for the reparented joint.
    """
    world_matrix = om2.MMatrix(cmds.xform(str(child), query=True, matrix=True, worldSpace=True))
    if target_parent:
        parented_objects = cmds.parent(str(child), str(target_parent), relative=True) or []
    else:
        parented_objects = cmds.parent(str(child), world=True, relative=True) or []
    if parented_objects:
        parented_joint = parented_objects[0]
        local_matrix = om2.MMatrix(cmds.getAttr(f"{parented_joint}.matrix"))
        parent_world_matrix = om2.MMatrix()
        if target_parent:
            parent_world_matrix = om2.MMatrix(cmds.getAttr(f"{target_parent}.worldMatrix[0]"))
        offset_parent_matrix = local_matrix.inverse() * world_matrix * parent_world_matrix.inverse()
        cmds.setAttr(f"{parented_joint}.offsetParentMatrix", offset_parent_matrix, type="matrix")
    return parented_objects


def _mark_inserted_joint_parent_compensation(child, target_parent=None):
    """Marks a transform Maya inserted above a joint during parenting.

    Args:
        child (str, Node): Joint that was just parented.
        target_parent (str, Node, optional): Parent requested by the caller.

    Returns:
        str or None: Marked compensation transform, if one was found.
    """
    child_path = str(child)
    if not cmds.objExists(child_path) or cmds.nodeType(child_path) != "joint":
        return
    actual_parent = cmds.listRelatives(child_path, parent=True, fullPath=True) or []
    expected_parent = core_naming.get_long_name(str(target_parent)) if target_parent else None
    if not actual_parent or actual_parent[0] == expected_parent:
        return
    compensation_transform = actual_parent[0]
    if cmds.nodeType(compensation_transform) != "transform":
        return
    if not cmds.attributeQuery(_JOINT_PARENT_COMPENSATION_ATTR, node=compensation_transform, exists=True):
        cmds.addAttr(
            compensation_transform,
            longName=_JOINT_PARENT_COMPENSATION_ATTR,
            attributeType="bool",
        )
    cmds.setAttr(f"{compensation_transform}.{_JOINT_PARENT_COMPENSATION_ATTR}", True)
    if target_parent:
        if not cmds.attributeQuery(_JOINT_PARENT_TARGET_ATTR, node=compensation_transform, exists=True):
            cmds.addAttr(compensation_transform, longName=_JOINT_PARENT_TARGET_ATTR, attributeType="message")
        target_attr = f"{compensation_transform}.{_JOINT_PARENT_TARGET_ATTR}"
        existing_targets = cmds.listConnections(target_attr, source=True, destination=False) or []
        if not existing_targets:
            cmds.connectAttr(f"{target_parent}.message", target_attr)
    return compensation_transform


def cleanup_joint_parent_compensation_transforms():
    """Removes compensation transforms inserted by Maya joint parenting.

    Marked wrappers are flattened after rig construction by moving their matrix
    compensation to the child joint's offsetParentMatrix. Empty marked wrappers
    are deleted directly. Joint channels and evaluated world matrices are
    preserved.

    Returns:
        list: Long names of compensation transforms that were removed.
    """
    marked_attributes = cmds.ls(f"*.{_JOINT_PARENT_COMPENSATION_ATTR}", long=True) or []
    compensation_transforms = [attribute.rsplit(".", 1)[0] for attribute in marked_attributes]
    compensation_transforms = sorted(set(compensation_transforms), key=lambda item: item.count("|"), reverse=True)
    removed_transforms = []
    for compensation_transform in compensation_transforms:
        if not cmds.objExists(compensation_transform):
            continue
        children = cmds.listRelatives(compensation_transform, children=True, fullPath=True) or []
        shapes = cmds.listRelatives(compensation_transform, shapes=True, fullPath=True) or []
        if shapes or len(children) > 1:
            logger.warning(
                f'Unable to remove joint compensation transform "{compensation_transform}". '
                "The transform contains unsupported children or shapes."
            )
            continue
        short_name = core_naming.get_short_name(compensation_transform)
        if not children:
            cmds.delete(compensation_transform)
            removed_transforms.append(short_name)
            continue
        child = children[0]
        if cmds.nodeType(child) != "joint":
            continue
        target_attr = f"{compensation_transform}.{_JOINT_PARENT_TARGET_ATTR}"
        target_parent = []
        if cmds.objExists(target_attr):
            target_parent = cmds.listConnections(target_attr, source=True, destination=False) or []
        if not target_parent:
            target_parent = cmds.listRelatives(compensation_transform, parent=True, fullPath=True) or []
        target_parent = target_parent[0] if target_parent else None
        _parent_joint_preserve_world(child=child, target_parent=target_parent)
        cmds.delete(compensation_transform)
        removed_transforms.append(short_name)
    return removed_transforms


def parent(source_objects, target_parent, verbose=False):
    """
    Makes sure that the provided object is really parented under the desired parent element.
    Args:
        source_objects (list, str): Name of the source objects (children) to be parented (e.g. "pSphere1" or ["obj"])
        target_parent (str, list): Name of the desired parent object.
                                   If a list is provided, it will attempt to use the first object found
        verbose (bool, optional): If True, it will print feedback in case the operation failed. Default is False.
    Returns:
        list: A list of the parented objects. (Long if not unique)
    """
    store_selection = cmds.ls(selection=True) or []
    if target_parent and isinstance(target_parent, list) and len(target_parent) > 0:
        target_parent = target_parent[0]
    if target_parent and not cmds.objExists(str(target_parent)):
        target_short_name = core_naming.get_short_name(str(target_parent))
        matching_targets = cmds.ls(target_short_name, long=True) or []
        if len(matching_targets) == 1:
            target_parent = matching_targets[0]
    if not target_parent or not cmds.objExists(str(target_parent)):
        core_fback.log_when_true(
            input_logger=logger,
            input_string=f"Unable to execute parenting operation."
            f'Missing target parent object "{str(target_parent)}".',
            do_log=verbose,
        )
        return []
    if source_objects is None:
        core_fback.log_when_true(
            input_logger=logger, input_string=f"Missing source list. Operation ignored.", do_log=verbose
        )
        return
    if source_objects and isinstance(source_objects, str):  # If a string, convert to list
        source_objects = [source_objects]
    parented_objects = []
    for child in source_objects:
        if not child or not cmds.objExists(str(child)):
            core_fback.log_when_true(
                input_logger=logger,
                input_string=f'Missing source object "{str(child)}" while ' f'parenting it to "{str(target_parent)}".',
                do_log=verbose,
            )
            continue
        current_parent = cmds.listRelatives(str(child), parent=True, fullPath=True) or []
        child_node = core_node.Node(child) if cmds.nodeType(str(child)) == "joint" else None
        if current_parent:
            current_parent = current_parent[0]
            if current_parent != core_naming.get_long_name(str(target_parent)):
                for obj in cmds.parent(child, str(target_parent)) or []:
                    parented_objects.append(obj)
        else:
            for obj in cmds.parent(child, str(target_parent)) or []:
                parented_objects.append(obj)
        if child_node:
            _mark_inserted_joint_parent_compensation(child=child_node, target_parent=target_parent)
    if store_selection:
        try:
            cmds.select(store_selection)
        except Exception as e:
            core_fback.log_when_true(
                input_logger=logger,
                input_string=f'Unable to recover previous selection. Issue: "{str(e)}".',
                do_log=verbose,
                level=logging.DEBUG,
            )
    try:
        parented_objects_long = cmds.ls(parented_objects, long=True)
    except Exception as e:
        core_fback.log_when_true(
            input_logger=logger,
            input_string=f'Unable to convert parented to long names. Issue: "{str(e)}".',
            do_log=verbose,
            level=logging.DEBUG,
        )
        parented_objects_long = parented_objects
    return parented_objects_long


def add_offset_transform(
    target_list,
    transform_type="group",
    pivot_source="target",
    transform_suffix=core_naming.NamingConstants.Suffix.OFFSET,
):
    """
    Adds an in-between offset transform to the target object.
    Args:
        target_list (list, str): Objects to receive a new parent offset transform
        transform_type (str, optional): Transform type to be created. Can be "group", "joint", or "locator"
        pivot_source (str, optional): Source of the pivot of the new transform. Can be "parent" or "target"
                                      "parent" means that it will use the pivot of the parent of the provided object.
                                      "target" means that it will use the pivot of the object (self)
        transform_suffix (str, optional): Suffix of the new transform. Name will be "<object-name>_<transform_suffix>"
    Returns:
        list: A list of created in-between transforms (offsets) - As Nodes
    """
    offset_transforms = []
    if target_list and isinstance(target_list, str):
        target_list = [target_list]
    for obj in target_list:
        cmds.select(clear=True)
        offset = f"{core_naming.get_short_name(obj)}_{transform_suffix}"
        if transform_type.lower() == "group":
            offset = cmds.group(name=offset, empty=True, world=True)
        elif transform_type.lower() == "joint":
            offset = cmds.joint(name=offset)
        elif transform_type.lower() == "locator":
            offset = cmds.spaceLocator(name=offset)[0]
        offset_node = core_node.Node(offset)

        _parent = cmds.listRelatives(obj, parent=True, fullPath=True) or []

        if len(_parent) != 0 and pivot_source == "parent":
            core_trans.match_transform(source=_parent[0], target_list=offset)
            cmds.parent(offset, _parent[0])
            cmds.parent(obj, offset)
        elif len(_parent) == 0 and pivot_source == "parent":
            cmds.parent(obj, offset)

        if len(_parent) != 0 and pivot_source == "target":
            core_trans.match_transform(source=obj, target_list=offset)
            cmds.parent(offset, _parent[0])
            cmds.parent(obj, offset_node.get_long_name())
        elif len(_parent) == 0 and pivot_source == "target":
            core_trans.match_transform(source=obj, target_list=offset)
            cmds.parent(obj, offset_node.get_long_name())

        offset_transforms.append(offset_node)
    return offset_transforms


def duplicate_object(
    obj, name=None, parent_to_world=True, reset_attributes=True, parent_only=True, input_connections=False
):
    """
    Duplicate provided object. If a transform duplicate its shapes too.

    Args:
        obj (str, Node): The name/path of the object to duplicate.
        name (str, optional): If provided, the transform of the duplicated object is renamed using this string.
        parent_to_world (bool, optional): If True, makes sure parent is parented to the world.
        reset_attributes (bool, optional): If True, it removes all user-defined attributes and un-hides/un-locks
                                           default attributes such as translate, rotate, scale, visibility.
                                           This option does not change TRS+V values, only un-hides/unlocks them.
        parent_only (bool, optional): When True, it deletes all children (but keeps shapes)
        input_connections (bool, optional): When True, it retains any incoming connections/inputs.
    Returns:
        Node: A node with the path/name of the duplicated object.
    """
    # Store Selection
    selection = cmds.ls(selection=True) or []
    # Duplicate
    duplicated_obj = cmds.duplicate(obj, renameChildren=True, inputConnections=input_connections)[0]
    duplicated_obj = core_node.Node(duplicated_obj)
    # Remove children
    if parent_only:
        shapes = cmds.listRelatives(duplicated_obj, shapes=True) or []
        children = cmds.listRelatives(duplicated_obj, children=True) or []
        for child in children:
            if child not in shapes:
                cmds.delete(child)
    # Parent to World
    has_parent = bool(cmds.listRelatives(duplicated_obj, parent=True))
    if has_parent and parent_to_world:
        cmds.parent(duplicated_obj, world=True)
        _mark_inserted_joint_parent_compensation(child=duplicated_obj)
    if reset_attributes:
        core_attr.delete_user_defined_attrs(obj_list=duplicated_obj, delete_locked=True, verbose=False)
        core_attr.set_attr_state(
            obj_list=duplicated_obj,
            attr_list=core_attr.DEFAULT_ATTRS,
            locked=False,
            hidden=False,
        )
    # Rename
    if name and isinstance(name, str):
        duplicated_obj.rename(name)
    # Manage Selection
    cmds.select(clear=True)
    if selection:
        try:
            cmds.select(selection)
        except Exception as e:
            logger.debug(f"Unable to restore previous selection. Issue: {e}")
    # Return Duplicated Object
    return duplicated_obj


def get_shape_components(shape, mesh_component_type="vertices", full_path=False):
    """
    Get all components of a shape.
    Args:
        shape (str): The shape node.
        mesh_component_type (str, optional): The type of component to return when the shape is of the type "mesh".
                                             Can be: "vertices"/"vtx", "edges"/"e", "faces"/"f", or "all".
                                             If the type is unrecognized, it will return an empty list. e.g. []
        full_path (bool, optional): when True, returns the full path to the components instead of their short name.
    Returns:
        List[str]: List of all components for the given shape.
    Example:
        out = get_shape_components(shape=transform, mesh_component_type="faces")
        print (out)  # ['cube_one.f[0]', 'cube_one.f[1]']
    """
    if not shape or not cmds.objExists(shape):
        return []
    if cmds.nodeType(shape) == "mesh":
        if mesh_component_type == "vertices" or mesh_component_type == "vtx":
            return cmds.ls(f"{shape}.vtx[*]", flatten=True, long=full_path)
        elif mesh_component_type == "edges" or mesh_component_type == "e":
            return cmds.ls(f"{shape}.e[*]", flatten=True, long=full_path)
        elif mesh_component_type == "faces" or mesh_component_type == "f":
            return cmds.ls(f"{shape}.f[*]", flatten=True, long=full_path)
        elif mesh_component_type == "all":
            components = cmds.ls(f"{shape}.vtx[*]", flatten=True, long=full_path)
            components += cmds.ls(f"{shape}.e[*]", flatten=True, long=full_path)
            components += cmds.ls(f"{shape}.f[*]", flatten=True, long=full_path)
            return components
        return []
    elif cmds.nodeType(shape) == "nurbsSurface":
        return cmds.ls(f"{shape}.cv[*][*]", flatten=True, long=full_path)
    elif cmds.nodeType(shape) == "nurbsCurve":
        return cmds.ls(f"{shape}.cv[*]", flatten=True, long=full_path)
    else:
        return []


def create_group(name=None, children=None):
    """
    Creates an empty group in Maya.
    Args:
        name (str): The name of the group to be created. Defaults to None.
        children (list, optional): List of child objects to be parented under the group. Defaults to None.
    Returns:
        Node: A Node object with the path to the created group.
    """
    # Create an empty group
    _parameters = {"empty": True, "world": True}
    if name and isinstance(name, str):
        _parameters["name"] = name
    group = cmds.group(**_parameters)
    group = core_node.Node(group)
    # Parent children under the group
    if children:
        parent(source_objects=children, target_parent=group)
    return group


def get_dagpath(object_name=None):
    """
    Returns dag path to a scene object

    Args:
        object_name (string): Name of scene object from which to retrieve a dag path

    Returns:
        MDagPath: Maya MDagPath object for scene item
    """

    if object_name:
        sel = om.MSelectionList()
        sel.add(object_name)
    else:
        sel = om.MSelectionList()
        om.MGlobal.getActiveSelectionList(sel)

    dagpath = om.MDagPath()

    if sel.length() == 0:
        logger.debug("getDagPath: No item specified")
        return

    sel.getDagPath(0, dagpath)

    return dagpath


def get_hierarchy(root=None, maya_type=None, remove_parent=False, full_path=False):
    """
    Performs a Dag Iteration on everything underneath the supplied root scene object.

    Args:
        root (str): root name. If not supplied the entire scene is traversed.
        maya_type (API type): if not None, it returns the passed type.
        remove_parent (bool): return the list without the parent.
        full_path (bool): return the full path name instead of the short one.

    Returns:
        List[str]: list of scene objects sorted by hierarchy
    """

    if maya_type:
        dag_it = om.MItDag(om.MItDag.kDepthFirst, maya_type)
    else:
        dag_it = om.MItDag(om.MItDag.kDepthFirst)

    hierarchy = []

    if root:
        dag = get_dagpath(root)
        if maya_type:
            dag_it.reset(dag, om.MItDag.kDepthFirst, maya_type)
        else:
            dag_it.reset(dag)

    while not dag_it.isDone():
        path = om.MDagPath()
        dag_it.getPath(path)
        if full_path:
            hierarchy.append(path.fullPathName())
        else:
            hierarchy.append(path.partialPathName())
        dag_it.next()

    if remove_parent:
        hierarchy.remove(root)

    return hierarchy


def dict_parent_sort(map_item_parent):
    """
    Sorts by parent relation a given string dictionary in which the keys are the main items and
    the values are the parents. This can be useful with UUID relation.

    Args:
        map_item_parent (dict): keys are the main items, values are the related parents.
                                Example: {"seed": "apple", "apple": "branch", "branch": "tree"}
    Returns:
        list: sorted list by parent, from roots to leaves. Roots are items with no parent or with
              a parent that is not one of the items. Leaves are items that are not parent of
              another item inside the given dictionary.
    """
    item_list = list(map_item_parent.keys())
    parent_list = list(map_item_parent.values())
    sorted_list = []

    # cycle check
    for i_id, p_id in zip(item_list, parent_list):
        for i_it, p_it in zip(item_list, parent_list):
            if i_id == p_it and i_it == p_id:
                logger.warning("Sort skipped, cycle, the following item is the parent of its parent:")
                logger.warning(f"<{i_id}> is child of <{p_id}>, and <{i_it}> is child of <{p_it}>.")
                return item_list

    while len(sorted_list) != len(item_list):
        for i_id, p_id in zip(item_list, parent_list):
            if p_id not in item_list and i_id not in sorted_list:
                sorted_list.insert(0, i_id)
            if p_id in sorted_list and i_id not in sorted_list:
                sorted_list.append(i_id)

    return sorted_list


def list_hierarchy_path(start_object, end_object):
    """
    Lists the hierarchy path from the start object to the end object.

    Args:
        start_object (str): The starting object in the hierarchy.
        end_object (str): The target object in the hierarchy.

    Returns:
        list[str]: A list of object names from start to end if the end object is within the hierarchy,
                   otherwise an empty list.

    Raises:
        ValueError: If the start or end object does not exist.
    """
    if not cmds.objExists(start_object) or not cmds.objExists(end_object):
        raise ValueError("Start or end object does not exist.")

    # Convert to full paths if given as short names
    start_object = cmds.ls(start_object, long=True)[0]
    end_object = cmds.ls(end_object, long=True)[0]

    # Check hierarchy by comparing names
    if not end_object.startswith(start_object):
        return []  # End object is not within the hierarchy

    # Traverse from start to end object
    path = []
    current = end_object
    while current:
        path.append(current)
        if current == start_object:
            break
        current = cmds.listRelatives(current, parent=True, fullPath=True)
        current = current[0] if current else None

    return path[::-1]  # Reverse to get start -> ... -> end


def find_top_parent(obj, target_type=None):
    """
    Finds the topmost parent of a given object.
    If a target_type is provided, only parents of that type are considered.

    Args:
        obj (str): The name of the object to start from.
        target_type (str, optional): The Maya node type to filter by (e.g., 'joint').
                                     If None, returns the topmost parent regardless of type.

    Returns:
        str or None: The topmost parent (of the given type if specified), or None if none is found.
    """
    if not cmds.objExists(obj):
        cmds.warning(f"Object '{obj}' does not exist.")
        return None

    current = obj
    top_match = current if (target_type is None or cmds.nodeType(current) == target_type) else None

    while True:
        found_parent = cmds.listRelatives(current, parent=True)
        if not found_parent:
            break
        found_parent = found_parent[0]
        if target_type is None or cmds.nodeType(found_parent) == target_type:
            top_match = found_parent
        current = found_parent

    return top_match


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    out = get_shape_components("pConeShape1")
    print(out)
