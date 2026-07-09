"""
Module to manage asset rig dag poses.

Import Line:
    import gt.core.poses as core_pose
"""

import gt.core.namespace as core_nspace
import gt.core.naming as core_naming
import gt.core.joint as core_joint
import gt.core.hierarchy as core_hrchy
import gt.core.transform as core_trans

import maya.OpenMayaAnim as oma
import maya.OpenMaya as om
import maya.cmds as cmds
import logging

import gt.core.node

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def zero_out_pose(root, tpose_name=None, apose_name=None, pose_to_freeze="t"):
    """
    Freezes the pose supplied (pose_to_freeze) and transfers the joint orient values on the other dag pose as rotations.
    Updates the dag poses.

    Args:
        root (str): the root of the skeleton hierarchy
        tpose_name (str): name for the tpose, if not provided, default "tpose" is taken
        apose_name (str): name for the apose, if not provided, default "apose" is taken
        pose_to_freeze (str): "a" or "t".
                              If "t", the T-pose will be frozen and the values will be put on the A-pose.
                              If "a", the other way round.
    """

    if not root:
        logger.debug("Cannot zero-out the pose. Supplied root is None.")
        return False

    if not tpose_name:
        tpose_name = core_naming.NamingConstants.Poses.TPOSE

    if not apose_name:
        apose_name = core_naming.NamingConstants.Poses.APOSE

    # undo
    cmds.undoInfo(openChunk=True)

    if not cmds.objExists(apose_name):
        create_dagpose(root=root, pose_name=apose_name)
        logger.info(f"{apose_name} was missing and it has been created with what you have in the scene.")

    if not cmds.objExists(tpose_name):
        create_dagpose(root=root, pose_name=tpose_name)
        logger.info(f"{tpose_name} was missing and it has been created with what you have in the scene.")

    joints_skel = core_hrchy.get_hierarchy(root=root, maya_type=om.MFn.kJoint)
    # joints_tpose = cmds.dagPose(tpose_name, query=True, members=True)
    joints_apose = cmds.dagPose(apose_name, query=True, members=True)

    # force members consistency in the apose
    if joints_skel != joints_apose:
        cmds.dagPose(apose_name, restore=True, g=True)
        cmds.delete(apose_name)
        cmds.dagPose(joints_skel, save=True, name=apose_name)

    # select the poses, by default the pose to freeze is "t"
    zero_pose = tpose_name
    values_pose = apose_name

    if pose_to_freeze == "a":
        zero_pose = apose_name
        values_pose = tpose_name

    # freeze and get the rotations from the zero_pose
    joints_fns = {}
    joints_orients = {}
    sel_list_jnt = om.MSelectionList()
    cmds.dagPose(zero_pose, restore=True, g=True)
    i = -1

    for jnt in joints_skel:
        if cmds.nodeType(jnt) == "joint":
            i += 1
            sel_list_jnt.add(jnt)
            jnt_dag_path = om.MDagPath()
            sel_list_jnt.getDagPath(i, jnt_dag_path)
            jnt_tr = om.MFnTransform(jnt_dag_path)

            # freeze joint
            cmds.makeIdentity(jnt, apply=True, t=0, r=1, s=0, n=0, pn=1)

            # get the rotation from joint orient
            jnt_fn = oma.MFnIkJoint(jnt_dag_path)
            jnt_orient = om.MEulerRotation()
            jnt_fn.getOrientation(jnt_orient)
            joints_fns[jnt] = jnt_fn
            joints_orients[jnt] = jnt_orient
            cmds.dagPose(jnt, reset=True, n=zero_pose)

    # apply rotations on the values_pose
    cmds.dagPose(values_pose, restore=True, g=True)

    for jnt in joints_skel:
        if cmds.nodeType(jnt) == "joint":
            rot_bp = cmds.xform(jnt, q=True, ro=True, ws=True)
            jnt_fn = joints_fns[jnt]
            jnt_orient = joints_orients[jnt]
            jnt_fn.setOrientation(jnt_orient)
            cmds.xform(jnt, ro=(rot_bp[0], rot_bp[1], rot_bp[2]), ws=True)
            cmds.dagPose(jnt, reset=True, n=values_pose)

    cmds.dagPose(zero_pose, restore=True, g=True)

    # undo
    cmds.undoInfo(closeChunk=True)


def create_apose(root, namespace=None):
    """
    Create apose from the current joints.

    Args:
        root (str): joint name
        namespace (str): namespace of the skeleton
    """

    if not root:
        logger.debug("Cannot create the dagPose. Supplied root is None.")
        return False

    apose_name = core_naming.NamingConstants.Poses.APOSE
    result = create_dagpose(root=root, pose_name=apose_name, namespace=namespace)
    return result


def create_dagpose(root, pose_name=None, delete_old=True, namespace=None):
    """
    Create a Dag pose from the current joints.

    Args:
        root (str): root joint of the skeleton
        pose_name (str): name to use for the dag pose
        delete_old (bool): delete the old one if it exists
        namespace (str): namespace of the skeleton
    """
    if not root:
        logger.debug("Cannot create the dagPose. Supplied root is None.")
        return False

    if pose_name:
        pose_name = core_nspace.apply_namespace_to_string(pose_name, namespace=namespace)

        # undo
        cmds.undoInfo(openChunk=True)

        result = True

        # dag poses within scene
        dag_poses = cmds.ls(type="dagPose")

        # handle old dag poses, if any
        old_pose = None
        for dp in dag_poses:
            if dp == pose_name:
                old_pose = dp
                break

        if old_pose:
            if delete_old:
                try:
                    cmds.delete(old_pose)
                except Exception as e:
                    logger.info(
                        "corePoses.create_dagpose - your supplied pose already exists in the scene."
                        "\nA new name has been associated. Please check the dag poses."
                    )
                    pass
            else:
                logger.info(
                    "corePoses.create_dagpose - your supplied pose already exists in the scene."
                    "\nA new name has been associated. Please check the dag poses."
                )

        if cmds.objExists(root):
            if not cmds.nodeType(root) == "joint":
                logger.info("corePoses.create_dagpose - the skeleton root type is not joint.")
                result = False
        else:
            logger.info(f"corePoses.create_dagpose - Cannot find the skeleton root: {root}.")
            result = False

        if result:
            # create the dag pose
            skeleton = core_hrchy.get_hierarchy(root=root, maya_type=om.MFn.kJoint)
            cmds.select(clear=True)
            cmds.select(skeleton)
            cmds.dagPose(save=True, selection=True, name=pose_name)
            cmds.select(clear=True)

        # undo
        cmds.undoInfo(closeChunk=True)

        return result

    else:
        logger.info("corePoses.create_dagpose - skipped, you need to supply a pose name.")
        return False


def set_dagpose(pose_name=None, namespace=""):
    """
    Set the pose supplied, if it exists.

    Args:
        pose_name (str): name of the pose
        namespace (str): namespace to find the right dag-pose
    """

    # pose name
    pose_name = str(pose_name)
    if namespace:
        pose_name = namespace + ":" + pose_name

    if pose_name:
        # dag poses within scene
        dag_poses = cmds.ls(type="dagPose")

        if pose_name in dag_poses:
            cmds.dagPose(pose_name, restore=True, g=True)
            return True

    logger.debug(f"corePoses.set_dagpose - specified dag pose does not exist: {pose_name}")
    return False


def set_tpose(namespace=""):
    """
    Set the T-pose defined in the global variable.

    Args:
        namespace (str): namespace to set the right dag-pose
    """
    tpose_name = core_naming.NamingConstants.Poses.TPOSE
    result = set_dagpose(pose_name=tpose_name, namespace=namespace)
    return result


def set_apose(namespace=""):
    """
    Set the a-pose defined in the global variable.

    Args:
        namespace (str): namespace to set the right dag-pose
    """
    apose_name = core_naming.NamingConstants.Poses.APOSE
    result = set_dagpose(pose_name=apose_name, namespace=namespace)
    return result


def delete_dagpose(pose_name=None):
    """
    Delete Dag Pose.

    Args:
        pose_name (str): if None, all the dag_poses will be deleted.
    """

    # dag poses within scene
    dag_poses = cmds.ls(type="dagPose")

    if pose_name:
        if str(pose_name) in dag_poses:
            cmds.delete(pose_name)

    else:
        for dagpose in dag_poses:
            cmds.delete(dagpose)


def check_dagpose(pose_name=None):
    """
    Check dag pose.

    Args:
        pose_name (str): name of the dag-pose

    Returns:
        dagpose_exists (bool)
    """

    if not pose_name:
        pose_name = core_naming.NamingConstants.Poses.APOSE

    # dag poses within scene
    dag_poses = cmds.ls(type="dagPose")
    dagpose_exists = False

    if str(pose_name) in dag_poses:
        dagpose_exists = True

    return dagpose_exists


def check_main_poses():
    """
    Check the existence of A pose and T pose.

    Returns:
        posesExist (boolean)
    """

    poses_exist = False
    apose_name = core_naming.NamingConstants.Poses.APOSE
    tpose_name = core_naming.NamingConstants.Poses.TPOSE
    if check_dagpose(tpose_name) and check_dagpose(apose_name):
        poses_exist = True

    return poses_exist


def check_dagpose_members(root, pose_name=None):
    """
    Compares Dag Pose items with the skeleton joints, they must match.

    Args:
        root (str): skeleton root object
        pose_name (str): dag pose object

    Returns:
        items_match (bool)
    """

    items_match = False

    if not root:
        logger.warning("Cannot check the dagPose members. Supplied root is None.")
        return False

    if not pose_name:
        pose_name = core_naming.NamingConstants.Poses.APOSE

    if not cmds.objExists(pose_name):
        logger.error(f"{pose_name} dagPose does not exist in the scene.")

    dag_joint_list = cmds.dagPose(pose_name, q=True, m=True)
    skel_joint_list = core_hrchy.get_hierarchy(root=root, maya_type=om.MFn.kJoint)

    if dag_joint_list == skel_joint_list:
        items_match = True

    return items_match


def delete_dagposes_except_main_ones():
    """
    Delete all the Dag Poses that are not tpose or apose.
    """

    # dag poses within scene
    dag_poses = cmds.ls(type="dagPose")

    for dagpose in dag_poses:
        apose_name = core_naming.NamingConstants.Poses.APOSE
        tpose_name = core_naming.NamingConstants.Poses.TPOSE
        if dagpose != apose_name and dagpose != tpose_name:
            cmds.delete(dagpose)


def straighten_objs_by_side(obj_list, skip_axis=None, forward_rot=0, point_down_rot=0, mirror_prefix=None):
    """
    Straighten all the objects in the supplied list bye side.

    Args:
        obj_list (list): list of string - maya objects.
        skip_axis (list): list of string - axis to skip during the constraint (e.g. ["y"]; ["z"]; ["y", "z"]; etc.).
        forward_rot (int): if not zero the constraint will constraint the object in order to face forward.
        point_down_rot (int): if not zero the constraint will constraint the object in order to point down.
        mirror_prefix (str): if defined, the function will follow a mirror behaviour for the objects starting with it.
    """

    if isinstance(obj_list, (list, tuple)):
        if len(obj_list) == 0:
            logger.debug("Given list is empty.")
            return

        for obj in obj_list:
            if not cmds.objExists(obj):
                logger.debug(f"The following object is missing: {str(obj)}")
                continue

            temp_loc = cmds.spaceLocator()[0]
            if mirror_prefix:
                obj_name = obj
                if isinstance(obj, gt.core.node.Node):
                    obj_name = obj.get_short_name()
                if obj_name.startswith(mirror_prefix):
                    cmds.setAttr(temp_loc + ".rotate", 0, 180, 180)
            if forward_rot:
                cmds.setAttr(temp_loc + ".rotateX", forward_rot)
            if point_down_rot:
                cmds.setAttr(temp_loc + ".rotateZ", point_down_rot)

            # straighten the object
            if skip_axis:
                temp_cnstr = cmds.orientConstraint(temp_loc, obj, mo=False, skip=skip_axis)[0]
            else:
                temp_cnstr = cmds.orientConstraint(temp_loc, obj, mo=False)[0]

            # clean
            cmds.delete(temp_cnstr)
            cmds.delete(temp_loc)


def get_pose_as_dict(joints, include_scale=False):
    """
    Captures the local transforms of the provided joints into a dictionary.
    This strips the namespace from the keys so the pose can be applied 
    to characters with different namespaces later.

    Args:
        joints (list): A list of joint names to query.
        include_scale (bool): Whether to include scale values in the dictionary.

    Returns:
        dict: A dictionary mapping base joint names to their local transforms.
    """
    pose_dict = {}
    
    attributes = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']
    if include_scale:
        attributes.extend(['sx', 'sy', 'sz'])
    
    for jnt in joints:
        if not cmds.objExists(jnt):
            continue
            
        # Strip namespace for the dictionary key
        base_name = jnt.split(':')[-1] if ':' in jnt else jnt
        pose_dict[base_name] = {}
        
        for attr in attributes:
            pose_dict[base_name][attr] = cmds.getAttr(f"{jnt}.{attr}")
            
    logger.info(f"Captured pose data for {len(pose_dict)} joints.")
    return pose_dict


def set_pose_from_dict(pose_dict, namespace=""):
    """
    Applies transform values from a pose dictionary to the scene joints.
    Safely ignores locked or connected channels.

    Args:
        pose_dict (dict): The dictionary generated by `get_pose_as_dict`.
        namespace (str, optional): A namespace to append to the dict keys when 
                                   searching for the joints in the scene.

    Returns:
        list: A list of joints that were successfully updated.
    """
    applied_joints = []
    
    for jnt, transforms in pose_dict.items():
        # Re-apply namespace if one is provided
        target_jnt = f"{namespace}:{jnt}" if namespace else jnt
            
        if not cmds.objExists(target_jnt):
            continue
            
        success = False
        for attr, val in transforms.items():
            plug = f"{target_jnt}.{attr}"
            
            # Only attempt to set if the attribute exists and isn't locked/connected
            if cmds.objExists(plug) and cmds.getAttr(plug, settable=True):
                try:
                    cmds.setAttr(plug, val)
                    success = True
                except Exception as e:
                    logger.debug(f"Failed to set {plug}. Issue: {e}")
                        
        if success:
            applied_joints.append(target_jnt)
            
    logger.info(f"Applied pose data to {len(applied_joints)} joints.")
    return applied_joints



if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    check_apose_result = check_dagpose()
    logger.debug(f"A-pose check result: {check_apose_result}")
