"""
GT Transfer Bound Joints - Extract or transfer bound joints

"""
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_transfer_skin_cluster")
logger.setLevel(20)  # DEBUG 10, INFO 20, WARNING 30, ERROR 40, CRITICAL 50


def get_bound_joints(obj):
    """
    Gets a list of joints bound to the skin cluster of the object
    Args:
        obj: Name of the object to extract joints from (must contain a skinCluster node)

    Returns:
        joints (list): List of joints bound to this object
    """
    if not cmds.objExists(obj):
        logger.warning('Object "' + obj + '" was not found in the scene.')
        return

    history = cmds.listHistory(selection_source) or []
    skin_clusters = cmds.ls(history, type='skinCluster') or []

    if len(skin_clusters) != 0:
        skin_cluster = skin_clusters[0]
    else:
        logger.debug('history: ', str(history))
        logger.debug('skin_clusters: ', str(skin_clusters))
        logger.warning('Object "' + obj + "\" doesn't seem to be bound to any joints.")
        return

    connections = cmds.listConnections(skin_cluster + '.influenceColor') or []
    joints = []
    for obj in connections:
        if cmds.objectType(obj) == 'joint':
            joints.append(obj)
    return joints


if __name__ == '__main__':
    selection_source = cmds.ls(selection=True)[0]  # First selected object - Geo with skinCluster
    bound_joints = get_bound_joints(selection_source)
    print(bound_joints)
    # cmds.select(bound_joints, replace=True)
    # import gt_maya_utilities as gtu
    # gtu.output_string_to_notepad(bound_joints)
