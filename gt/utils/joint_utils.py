"""
Joint Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.math_utils import dot_product, objects_cross_direction
import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def orient_joint(joint_list,
                 aim_axis=(1, 0, 0),
                 up_axis=(0, 1, 0),
                 up_dir=(0, 1, 0),
                 detect_up_dir=False):
    """
    Orient a list of joints in a predictable way.

    Args:
        joint_list (list): A list of joints (strings) - Name of the joints.
        aim_axis (tuple, optional): The axis the joints should aim at in XYZ. Defaults to X+ (1, 0, 0).
                                    Commonly used as twist joint (aims towards its child)
        up_axis (tuple, optional): The axis pointing upwards for the joints. Defaults to (0, 1, 0).
        up_dir (tuple, optional): The up direction vector. Defaults to (0, 1, 0).
        detect_up_dir (bool, optional): If True, attempt to auto-detect the up direction. Defaults to False.
    """
    stored_selection = cmds.ls(selection=True) or []
    starting_up = OpenMaya.MVector((0, 0, 0))
    index = 0
    for jnt in joint_list:
        jnt = str(jnt)
        # Store Parent
        parent = cmds.listRelatives(jnt, parent=True, fullPath=True) or []
        if len(parent) != 0:
            parent = parent[0]

        # Un-parent children
        children = cmds.listRelatives(jnt, children=True, typ="transform", fullPath=True) or []
        children += cmds.listRelatives(jnt, children=True, typ="joint", fullPath=True) or []
        if len(children) > 0:
            children = cmds.parent(children, world=True)

        # Determine aim joint (if available)
        aim_target = ""
        for child in children:
            if cmds.nodeType(child) == "joint":
                aim_target = child

        if aim_target != "":
            up_vec = (0, 0, 0)

            if detect_up_dir:
                pos_jnt_ws = cmds.xform(jnt, q=True, ws=True, rp=True)

                # Use itself in case it doesn't have a parent
                pos_parent_ws = pos_jnt_ws
                if parent != "":
                    pos_parent_ws = cmds.xform(parent, q=True, ws=True, rp=True)

                tolerance = 0.0001
                if parent == "" or (abs(pos_jnt_ws[0] - pos_parent_ws[0]) <= tolerance and
                                    abs(pos_jnt_ws[1] - pos_parent_ws[1]) <= tolerance and
                                    abs(pos_jnt_ws[2] - pos_parent_ws[2]) <= tolerance):
                    aim_children = cmds.listRelatives(aim_target, children=True, fullPath=True) or []
                    aim_child = ""

                    for child in aim_children:
                        if cmds.nodeType(child) == "joint":
                            aim_child = child

                    up_vec = objects_cross_direction(jnt, aim_target, aim_child)
                else:
                    up_vec = objects_cross_direction(parent, jnt, aim_target)

            if not detect_up_dir or (up_vec[0] == 0.0 and
                                     up_vec[1] == 0.0 and
                                     up_vec[2] == 0.0):
                up_vec = up_dir

            cmds.delete(cmds.aimConstraint(aim_target, jnt,
                                           aim=aim_axis,
                                           upVector=up_axis,
                                           worldUpVector=up_vec,
                                           worldUpType="vector"))

            current_up = OpenMaya.MVector(up_vec).normal()
            dot = dot_product(current_up, starting_up)
            starting_up = OpenMaya.MVector(up_vec).normal()

            # Flip in case dot is negative (wrong way)
            if index > 0 and dot <= 0.0:
                cmds.xform(jnt, r=True, os=True, ra=(aim_axis[0] * 180.0, aim_axis[1] * 180.0, aim_axis[2] * 180.0))
                starting_up *= -1.0

            cmds.joint(jnt, e=True, zeroScaleOrient=True)
            cmds.makeIdentity(jnt, apply=True)
        elif parent != "":
            cmds.delete(cmds.orientConstraint(parent, jnt, weight=1))
            cmds.joint(jnt, e=True, zeroScaleOrient=True)
            cmds.makeIdentity(jnt, apply=True)

        if len(children) > 0:
            cmds.parent(children, jnt)
        index += 1
    # Update selection
    cmds.select(clear=True)
    if stored_selection:
        try:
            cmds.select(stored_selection)
        except Exception as e:
            logger.debug(f'Unable to retrieve previous selection. Issue: {e}')


def copy_parent_orients(joint_list):
    """
    Copy the orientations from its world (parent)
    Args:
        joint_list (list, str): A list of joints to receive the orientation of their parents.
                                   If a string is given instead, it will be auto converted into a list for processing.
    """
    if isinstance(joint_list, str):
        joint_list = [joint_list]
    for jnt in joint_list:
        cmds.joint(jnt, e=True, orientJoint="none", zeroScaleOrient=True)


def convert_joints_to_mesh(root_jnt=None, combine_mesh=True, verbose=True):
    """
    Converts a joint hierarchy into a mesh representation of it (Helpful when sending it to sculpting apps)
    Args:
        root_jnt (list, str, optional): Path to the root joint of the skeleton used in the conversion.
                                        If not provided, the selection is used instead.
                                        If a list, must contain exactly one object, the root joint. (top parent joint)
        combine_mesh: Combines generated meshes into one. Each joint produces a mesh.
                      when combining, the output is one single combined mesh. (Entire skeleton)
        verbose (bool, optional): If True, it will return feedback about the operation.

    Returns:
        list: A list of generated meshes
    """
    _joints = None
    if root_jnt and isinstance(root_jnt, list):
        _joints = root_jnt
    if root_jnt and isinstance(root_jnt, str):
        _joints = [root_jnt]
    if not _joints:
        _joints = cmds.ls(selection=True, typ="joint") or []

    if len(_joints) != 1:
        if verbose:
            cmds.warning('Please selection only the root joint and try again.')
        return
    cmds.select(_joints[0], replace=True)
    cmds.select(hierarchy=True)
    joints = cmds.ls(selection=True, type='joint', long=True)

    generated_mesh = []
    for obj in reversed(joints):
        if cmds.objExists(obj):
            joint_name = obj.split('|')[-1]
            radius = cmds.getAttr(obj + '.radius')
            joint_sphere = cmds.polySphere(radius=radius * .5,
                                           subdivisionsAxis=8,
                                           subdivisionsHeight=8,
                                           axis=[1, 0, 0],
                                           name=joint_name + 'JointMesh',
                                           ch=False)
            generated_mesh.append(joint_sphere[0])
            cmds.delete(cmds.parentConstraint(obj, joint_sphere))
            joint_parent = cmds.listRelatives(obj, parent=True, fullPath=True) or []
            if len(joint_parent) > 0:
                joint_parent = joint_parent[0]
            if joint_parent and joint_parent in joints:
                joint_cone = cmds.polyCone(radius=radius * .5,
                                           subdivisionsAxis=4,
                                           name=joint_name + 'BoneMesh',
                                           ch=False)
                generated_mesh.append(joint_cone[0])
                bbox = cmds.exactWorldBoundingBox(joint_cone)
                bottom = [(bbox[0] + bbox[3]) / 2, bbox[1], (bbox[2] + bbox[5]) / 2]
                cmds.xform(joint_cone, piv=bottom, ws=True)
                cmds.move(1, joint_cone, moveY=True)
                cmds.rotate(90, joint_cone, rotateX=True)
                cmds.rotate(90, joint_cone, rotateY=True)
                cmds.makeIdentity(joint_cone, rotate=True, apply=True)

                cmds.delete(cmds.parentConstraint(joint_parent, joint_cone))
                cmds.delete(cmds.aimConstraint(obj, joint_cone))

                child_pos = cmds.xform(obj, t=True, ws=True, query=True)
                cmds.xform(joint_cone[0] + '.vtx[4]', t=child_pos, ws=True)
    if combine_mesh and len(generated_mesh) > 1:  # Needs at least two meshes to combine
        cmds.select(generated_mesh, replace=True)
        mesh = cmds.polyUnite()
        cmds.select(clear=True)
        cmds.delete(mesh, constructionHistory=True)
        mesh = cmds.rename(mesh[0], _joints[0] + 'AsMesh')
        return [mesh]
    else:
        cmds.select(clear=True)
        return generated_mesh


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    temp_list = []
    from gt.utils.node_utils import Node
    for item in ['joint1', 'joint2', 'joint3']:
        temp_list.append(Node(item))
    orient_joint(joint_list=temp_list, aim_axis=(1, 0, 0), up_axis=(0, -1, 0), up_dir=(0, 1, 0))
