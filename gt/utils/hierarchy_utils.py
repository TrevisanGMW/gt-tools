"""
Hierarchy Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.naming_utils import get_long_name, get_short_name
from gt.utils.attr_utils import delete_user_defined_attrs
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
        list: A list of created in-between transforms (offsets) - Full paths
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

        offset_transforms.append(offset_node.get_long_name())
    return offset_transforms


def duplicate_as_node(to_duplicate, name=None, input_connections=False,
                      parent_only=False, delete_attrs=True):
    """
    Duplicates the input object with a few extra options, then return a "Node" version of it.
    Args:
        to_duplicate (str): Object to duplicate (must exist in the scene)
        name (str, optional): A name for the duplicated object
        input_connections (bool, optional):
        parent_only (bool, optional): If True, only the parent is duplicate. (Will exclude shapes)
        delete_attrs (bool, optional): If True, user-defined attributes will be removed from the duplicated object.
    Returns:
        Node, str: The duplicated object
    """
    selection = cmds.ls(selection=True)
    if not to_duplicate or not cmds.objExists(to_duplicate):
        logger.debug(f'Unable to duplicate object. Missing provided input: "{str(input)}".')
        return
    param = {"inputConnections": input_connections,
             "parentOnly": parent_only}
    if name and isinstance(name, str):
        param["name"] = name
    new_obj = cmds.duplicate(to_duplicate, **param)[0]
    new_obj = Node(new_obj)
    if delete_attrs:
        delete_user_defined_attrs(obj_list=new_obj)
    cmds.select(clear=True)
    if selection:
        try:
            cmds.select(selection=True)
        except Exception as e:
            logger.debug(f'Unable to restore initial selection. Issue: {str(e)}')
    return new_obj


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    out = duplicate_as_node(to_duplicate="pSphere1")
    print(out)
