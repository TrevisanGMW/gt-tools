"""
Hierarchy Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.attr_utils import delete_user_defined_attrs, set_attr_state, DEFAULT_ATTRS
from gt.utils.naming_utils import get_long_name, get_short_name
from gt.utils.transform_utils import match_transform
from gt.utils.feedback_utils import log_when_true
from gt.utils.node_utils import Node
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
    if not target_parent or not cmds.objExists(str(target_parent)):
        log_when_true(input_logger=logger,
                      input_string=f'Unable to execute parenting operation.'
                                   f'Missing target parent object "{str(target_parent)}".',
                      do_log=verbose)
        return []
    if source_objects is None:
        log_when_true(input_logger=logger,
                      input_string=f'Missing source list. Operation ignored.',
                      do_log=verbose)
        return
    if source_objects and isinstance(source_objects, str):  # If a string, convert to list
        source_objects = [source_objects]
    parented_objects = []
    for child in source_objects:
        if not child or not cmds.objExists(str(child)):
            log_when_true(input_logger=logger,
                          input_string=f'Missing source object "{str(child)}" while '
                                       f'parenting it to "{str(target_parent)}".',
                          do_log=verbose)
            continue
        current_parent = cmds.listRelatives(str(child), parent=True, fullPath=True) or []
        if current_parent:
            current_parent = current_parent[0]
            if current_parent != get_long_name(str(target_parent)):
                for obj in cmds.parent(child, str(target_parent)) or []:
                    parented_objects.append(obj)
        else:
            for obj in cmds.parent(child, str(target_parent)) or []:
                parented_objects.append(obj)
    if store_selection:
        try:
            cmds.select(store_selection)
        except Exception as e:
            log_when_true(input_logger=logger,
                          input_string=f'Unable to recover previous selection. Issue: "{str(e)}".',
                          do_log=verbose,
                          level=logging.DEBUG)
    try:
        parented_objects_long = cmds.ls(parented_objects, long=True)
    except Exception as e:
        log_when_true(input_logger=logger,
                      input_string=f'Unable to convert parented to long names. Issue: "{str(e)}".',
                      do_log=verbose,
                      level=logging.DEBUG)
        parented_objects_long = parented_objects
    return parented_objects_long


def add_offset_transform(target_list, transform_type="group", pivot_source="target", transform_suffix="offset"):
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
        offset = f'{get_short_name(obj)}_{transform_suffix}'
        if transform_type.lower() == "group":
            offset = cmds.group(name=offset, empty=True, world=True)
        elif transform_type.lower() == "joint":
            offset = cmds.joint(name=offset)
        elif transform_type.lower() == "locator":
            offset = cmds.spaceLocator(name=offset)[0]
        offset_node = Node(offset)

        _parent = cmds.listRelatives(obj, parent=True, fullPath=True) or []

        if len(_parent) != 0 and pivot_source == "parent":
            match_transform(source=_parent[0], target_list=offset)
            cmds.parent(offset, _parent[0])
            cmds.parent(obj, offset)
        elif len(_parent) == 0 and pivot_source == "parent":
            cmds.parent(obj, offset)

        if len(_parent) != 0 and pivot_source == "target":
            match_transform(source=obj, target_list=offset)
            cmds.parent(offset, _parent[0])
            cmds.parent(obj, offset_node.get_long_name())
        elif len(_parent) == 0 and pivot_source == "target":
            match_transform(source=obj, target_list=offset)
            cmds.parent(obj, offset_node.get_long_name())

        offset_transforms.append(offset_node)
    return offset_transforms


def duplicate_object(obj, name=None, parent_to_world=True, reset_attributes=True,
                     parent_only=True, input_connections=False):
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
    duplicated_obj = Node(duplicated_obj)
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
    if reset_attributes:
        delete_user_defined_attrs(obj_list=duplicated_obj, delete_locked=True, verbose=False)
        set_attr_state(obj_list=duplicated_obj, attr_list=DEFAULT_ATTRS, locked=False, hidden=False)
    # Rename
    if name and isinstance(name, str):
        duplicated_obj.rename(name)
    # Manage Selection
    cmds.select(clear=True)
    if selection:
        try:
            cmds.select(selection)
        except Exception as e:
            logger.debug(f'Unable to restore previous selection. Issue: {e}')
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
        if mesh_component_type == 'vertices' or mesh_component_type == 'vtx':
            return cmds.ls(f"{shape}.vtx[*]", flatten=True, long=full_path)
        elif mesh_component_type == 'edges' or mesh_component_type == 'e':
            return cmds.ls(f"{shape}.e[*]", flatten=True, long=full_path)
        elif mesh_component_type == 'faces' or mesh_component_type == 'f':
            return cmds.ls(f"{shape}.f[*]", flatten=True, long=full_path)
        elif mesh_component_type == 'all':
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
    _parameters = {"empty": True,
                   "world": True}
    if name and isinstance(name, str):
        _parameters["name"] = name
    group = cmds.group(**_parameters)
    group = Node(group)
    # Parent children under the group
    if children:
        parent(source_objects=children, target_parent=group)
    return group


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    out = get_shape_components("pConeShape1")
    print(out)
