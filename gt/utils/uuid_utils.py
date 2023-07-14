"""
UUID Utilities
"""
from dataclasses import dataclass
import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds
import logging
import re

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def find_object_with_uuid(uuid_string, attr_name, obj_type="transform"):
    """
    Return object if provided UUID is present in it
    Args:
        uuid_string (string): UUID to look for (if it matches, then the object is found)
        attr_name (string): Name of the attribute where the UUID is stored.
        obj_type (optional, string): Type of objects to look for (default is "transform")
    Returns:
        If found, the object with a matching UUID, otherwise None
    """
    transforms = cmds.ls(typ=obj_type, long=True) or []
    for transform in transforms:
        user_attributes = cmds.listAttr(transform, userDefined=True) or []
        if attr_name in user_attributes:
            existing_uuid = cmds.getAttr(transform + "." + attr_name) or ""
            if uuid_string == existing_uuid:
                return transform
    return
    

def is_uuid_valid(uuid_string):
    """
    Use regex to determine if UUID is valid (it should match the pattern found in uuid1)
    Args:
        uuid_string (string): UUID to be checked. If it follows th expected pattern, it's valid

    Returns:
        True if valid, False if invalid
    """
    pattern = re.compile("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
    if pattern.match(uuid_string):
        return True
    else:
        return False
