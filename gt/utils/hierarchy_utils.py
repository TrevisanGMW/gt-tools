"""
Hierarchy Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.feedback_utils import log_when_true
from gt.utils.naming_utils import get_long_name
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
        current_parent = cmds.listRelatives(child, parent=True, fullPath=True) or []
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


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
