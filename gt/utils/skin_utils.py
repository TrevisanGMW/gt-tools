"""
Skin Utilities
github.com/TrevisanGMW/gt-tools
"""
import os.path

import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
        return []

    history = cmds.listHistory(obj) or []
    skin_clusters = cmds.ls(history, type='skinCluster') or []

    if len(skin_clusters) != 0:
        skin_cluster = skin_clusters[0]
    else:
        logger.debug('history: ', str(history))
        logger.debug('skin_clusters: ', str(skin_clusters))
        logger.warning('Object "' + obj + "\" doesn't seem to be bound to any joints.")
        return []

    connections = cmds.listConnections(skin_cluster + '.influenceColor') or []
    joints = []
    for obj in connections:
        if cmds.objectType(obj) == 'joint':
            joints.append(obj)
    return joints


def bind_skin(joints, objects, bind_method=1, smooth_weights=0.5, maximum_influences=4):
    current_selection = cmds.ls(selection=True) or []
    skin_nodes = []
    joints_found = []
    joints_missing = []
    objects_found = []
    objects_missing = []
    # Determine Existing Objects
    for jnt in joints:
        if cmds.objExists(jnt):
            joints_found.append(jnt)
        else:
            joints_missing.append(jnt)
    for geo in objects:
        if cmds.objExists(geo):
            objects_found.append(geo)
        else:
            objects_missing.append(geo)
    if objects_missing:
        logger.warning(f'Skin bound operation had missing objects: "{", ".join(objects_missing)}".')
    if joints_missing:
        logger.warning(f'Skin bound operation had missing joints: "{", ".join(joints_missing)}".')
    # Bind objects
    for geo in objects_found:
        skin_node = cmds.skinCluster(joints_found, geo,
                                     bindMethod=bind_method,
                                     toSelectedBones=True,
                                     smoothWeights=smooth_weights,
                                     maximumInfluences=maximum_influences) or []
        if skin_node:
            skin_nodes.extend(skin_node)

    if current_selection:
        try:
            cmds.select(current_selection)
        except Exception as e:
            logger.debug(f'Unable to recover previous selection. Issue: {str(e)}')
    return skin_nodes


def export_weights(objects, target_folder):
    if not os.path.exists(target_folder) or not os.path.isdir(target_folder):
        logger.warning(f'Unable to export skin weights. Missing target folder: {str(target_folder)}')
        return

    for obj in objects:
        file_name = obj + ".json"
        file_path = os.path.join(target_folder, file_name)
        wip.export_json(target=obj, file=file_path)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    selection = cmds.ls(selection=True) or []
    temp_joints = ['joint1', 'joint2', 'joint3']
    temp_geometries = ['pCylinder1', 'pCylinder2', 'pCylinder3']
    # out = bind_skin(temp_joints, temp_geometries)
    from gt.utils.system_utils import get_desktop_path
    export_weights(objects=['pCylinder1'], target_folder=get_desktop_path())

    pprint(out)
