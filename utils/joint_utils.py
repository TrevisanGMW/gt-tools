import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("joint_utils")
logger.setLevel(logging.INFO)


def orient_joint(joint_list,
                 aim_axis=(1, 0, 0),
                 up_axis=(1, 0, 0),
                 up_dir=(1, 0, 0),
                 detect_up_dir=False):
    """
    Orient Joint list in a more predictable way (when compared to Maya)
    Args:
        joint_list (list): A list of joints (strings) - Name of the joints
        aim_axis (optional, tuple): Aim axis
        up_axis (optional, tuple):
        up_dir (optional, tuple):
        detect_up_dir (optional, bool): If it should attempt to auto-detect up direction
    """
    starting_up = OpenMaya.MVector((0, 0, 0))
    index = 0
    for jnt in joint_list:

        # Store Parent
        parent = cmds.listRelatives(jnt, parent=True) or []
        if len(parent) != 0:
            parent = parent[0]

        # Un-parent children
        children = cmds.listRelatives(jnt, children=True, typ="transform") or []
        children += cmds.listRelatives(jnt, children=True, typ="joint") or []
        if len(children) > 0:
            children = cmds.parent(children, w=True)

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
                    aim_children = cmds.listRelatives(aim_target, children=True) or []
                    aim_child = ""

                    for child in aim_children:
                        if cmds.nodeType(child) == "joint":
                            aim_child = child

                    up_vec = get_cross_direction(jnt, aim_target, aim_child)
                else:
                    print("parent", parent)
                    print("jnt", jnt)
                    print("aim_target", aim_target)
                    up_vec = get_cross_direction(parent, jnt, aim_target)

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
            dot = get_dot_product(current_up, starting_up)
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


def get_dot_product(vector_a, vector_b):
    """
    Returns dot product
        Args:
            vector_a (list, MVector): first vector
            vector_b (list, MVector): second vector
    """
    if type(vector_a) != 'OpenMaya.MVector':
        vector_a = OpenMaya.MVector(vector_a)
    if type(vector_b) != 'OpenMaya.MVector':
        vector_b = OpenMaya.MVector(vector_b)
    return vector_a * vector_b


def get_cross_product(vector_a, vector_b, vector_c):
    """
    Get Cross Product
        Args:
            vector_a (list): A list of floats
            vector_b (list): A list of floats
            vector_c (list): A list of floats
        Returns:
            MVector: cross product
    """
    if type(vector_a) != 'OpenMaya.MVector':
        vector_a = OpenMaya.MVector(vector_a)
    if type(vector_b) != 'OpenMaya.MVector':
        vector_b = OpenMaya.MVector(vector_b)
    if type(vector_c) != 'OpenMaya.MVector':
        vector_c = OpenMaya.MVector(vector_c)

    vector_a = OpenMaya.MVector([vector_a[0] - vector_b[0],
                                 vector_a[1] - vector_b[1],
                                 vector_a[2] - vector_b[2]])

    vector_b = OpenMaya.MVector([vector_c[0] - vector_b[0],
                                 vector_c[1] - vector_b[1],
                                 vector_c[2] - vector_b[2]])

    return vector_a ^ vector_b


def get_cross_direction(obj_a, obj_b, obj_c):
    """
    Get Cross Direction
        Args:
            obj_a (str): Name of the first object. (Must exist in scene)
            obj_b (str): Name of the second object. (Must exist in scene)
            obj_c (str): Name of the third object. (Must exist in scene)
        Returns:
            MVector: cross direction of the objects
    """
    cross = [0, 0, 0]
    for obj in [obj_a, obj_b, obj_c]:
        if not cmds.objExists(obj):
            return cross
    pos_a = cmds.xform(obj_a, q=True, ws=True, rp=True)
    pos_b = cmds.xform(obj_b, q=True, ws=True, rp=True)
    pos_c = cmds.xform(obj_c, q=True, ws=True, rp=True)

    return get_cross_product(pos_a, pos_b, pos_c).normal()


def convert_joints_to_mesh(combine_mesh=True):
    """
    Converts a joint hierarchy into a mesh representation of it (Helpful when sending it to sculpting apps)
    Args:
        combine_mesh: Combines generated meshes into one

    Returns:
        A list of generated meshes
    """
    selection = cmds.ls(selection=True, type='joint')
    if len(selection) != 1:
        cmds.warning('Please selection only the root joint and try again.')
        return
    cmds.select(selection[0], replace=True)
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
    if combine_mesh:
        cmds.select(generated_mesh, replace=True)
        mesh = cmds.polyUnite()
        cmds.select(clear=True)
        cmds.delete(mesh, constructionHistory=True)
        mesh = cmds.rename(mesh[0], selection[0] + 'AsMesh')
        return [mesh]
    else:
        return generated_mesh


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    convert_joints_to_mesh()
    out = None
    pprint(out)
