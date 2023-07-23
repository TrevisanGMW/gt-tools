"""
Hierarchy Utilities
github.com/TrevisanGMW/gt-tools
"""
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def enforce_parent(obj_name, desired_parent):
    """
    Makes sure that the provided object is really parented under the desired parent element.
    Args:
        obj_name (str): Name of the source object enforce parenting (e.g. "pSphere1")
        desired_parent (str): Name of the desired parent element. You would expect to find obj_name inside it.

    Returns: True if re-parented, false if not re-parented or not found
    """
    if not obj_name or not cmds.objExists(obj_name):
        return False  # Source Object doesn't exist
    if not desired_parent or not cmds.objExists(desired_parent):
        return False  # Target Object doesn't exist
    current_parent = cmds.listRelatives(obj_name, parent=True) or []
    if current_parent:
        current_parent = current_parent[0]
        if current_parent != desired_parent:
            cmds.parent(obj_name, desired_parent)
    else:
        cmds.parent(obj_name, desired_parent)