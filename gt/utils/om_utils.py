"""
Open Maya (OM) Utilities
github.com/TrevisanGMW/gt-tools
"""
import maya.OpenMaya as OpenMaya
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_mobject_from_path(object_path):
    """
    Gets an MObject from a string path (path to the object in maya e.g. "|pSphere1")
    Args:
        object_path (str): Path to the object in maya e.g. "|pSphere1".
    Returns:
        MObject, None: MObject if the object exists, otherwise None.
    """
    selection_list = OpenMaya.MSelectionList()
    try:
        selection_list.add(object_path)
    except Exception as e:
        logger.debug(f'Unable to get MObject. Issue: {e}')
        return None  # Return None if the object path is not valid

    mobject = OpenMaya.MObject()
    selection_list.getDependNode(0, mobject)
    return mobject


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    import maya.cmds as cmds
    out = get_mobject_from_path("pSphere1")
    print(out)
