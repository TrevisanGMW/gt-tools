"""
 GT Facial Rigger
 github.com/TrevisanGMW - 2021-12-06

 TODO:
    Auto calculate outer eyebrow gradient

"""
from gt_rigger_utilities import *
from gt_rigger_data import *
import maya.cmds as cmds
import random

# Script Name
script_name = 'GT Auto Facial Rigger'

# Version:
script_version = '0.3'

find_pre_existing_elements = True

# Debugging Vars
debugging = True

# Loaded Elements Dictionary
_facial_proxy_dict = {  # Pre Existing Elements
    'main_proxy_grp': 'auto_face_proxy' + '_' + GRP_SUFFIX,
    'main_root': 'auto_face_proxy' + '_' + PROXY_SUFFIX,

    # Center Elements
    'head_crv': 'headRoot' + '_' + PROXY_SUFFIX,
    'jaw_crv': 'jawRoot' + '_' + PROXY_SUFFIX,
    'left_eye_crv': 'eyeRoot_' + PROXY_SUFFIX,

    # Eyebrows
    'left_inner_brow_crv': 'innerBrow_' + PROXY_SUFFIX,
    'left_mid_brow_crv': 'midBrow_' + PROXY_SUFFIX,
    'left_outer_brow_crv': 'outerBrow_' + PROXY_SUFFIX,

    # Mouth
    'mid_upper_lip_crv': 'mid_upperLip_' + PROXY_SUFFIX,
    'mid_lower_lip_crv': 'mid_lowerLip_' + PROXY_SUFFIX,
    'left_upper_outer_lip_crv': 'upperOuterLip_' + PROXY_SUFFIX,
    'left_lower_outer_lip_crv': 'lowerOuterLip_' + PROXY_SUFFIX,
    'left_corner_lip_crv': 'cornerLip_' + PROXY_SUFFIX,
}

_preexisting_dict = {'neck_base_jnt': 'neckBase_jnt',
                     'head_jnt': 'head_jnt',
                     'jaw_jnt': 'jaw_jnt',
                     'left_eye_jnt': 'left_eye_jnt',
                     'right_eye_jnt': 'right_eye_jnt',
                     'head_ctrl': 'head_ctrl',
                     'jaw_ctrl': 'jaw_ctrl',
                     }

# Auto Populate Control Names (Copy from Left to Right) + Add prefixes
for item in list(_facial_proxy_dict):
    if item.startswith('left_'):
        _facial_proxy_dict[item] = 'left_' + _facial_proxy_dict.get(item)  # Add "left_" prefix
        _facial_proxy_dict[item.replace('left_', 'right_')] = _facial_proxy_dict.get(item).replace('left_',
                                                                                                   'right_')


def create_arched_control(end_joint, ctrl_name='', radius=0.5, create_offset_grp=False):
    """ TODO """

    # Validate necessary elements
    end_joint_parent = cmds.listRelatives(end_joint, parent=True)[0] or []
    if not end_joint_parent:
        cmds.warning("Provided joint doesn't have a parent.")
        return

    # Calculate System Scale
    system_scale = dist_center_to_center(end_joint, end_joint_parent)

    # Generate name in case one wasn't provided
    if not ctrl_name:
        ctrl_name = end_joint + '_ctrl'

    # Create control
    ctrl = cmds.curve(name=ctrl_name,
                      p=[[0.0, 0.28, 0.0], [-0.28, 0.001, 0.0], [0.0, 0.0, 0.28], [0.0, 0.28, 0.0], [0.28, 0.001, 0.0],
                         [0.0, 0.0, 0.28], [0.28, 0.001, 0.0], [0.0, 0.0, -0.28], [0.0, 0.28, 0.0], [0.0, 0.0, -0.28],
                         [-0.28, 0.001, 0.0], [0.0, -0.28, 0.0], [0.0, 0.0, -0.28], [0.28, 0.001, 0.0],
                         [0.0, -0.28, 0.0], [0.0, 0.0, 0.28]], d=1)
    ctrl_grp = cmds.group(name=ctrl_name + GRP_SUFFIX.capitalize(), world=True, empty=True)
    cmds.parent(ctrl, ctrl_grp)
    cmds.move(0, 0, radius * 1.5, ctrl)
    cmds.delete(cmds.pointConstraint(end_joint, ctrl_grp))
    desired_pivot = cmds.xform(end_joint, q=True, ws=True, t=True)
    cmds.xform(ctrl, piv=desired_pivot, ws=True)
    cmds.delete(cmds.orientConstraint(end_joint, ctrl))
    cmds.makeIdentity(ctrl, apply=True, scale=True, rotate=True, translate=True)

    # Create motion locator
    trans_loc = cmds.spaceLocator(name=end_joint + '_transLoc')[0]
    trans_loc_grp = cmds.group(name=trans_loc + GRP_SUFFIX, world=True, empty=True)
    cmds.parent(trans_loc, trans_loc_grp)
    cmds.delete(cmds.parentConstraint(ctrl, trans_loc_grp))
    cmds.pointConstraint(ctrl, trans_loc)
    cmds.orientConstraint(ctrl, trans_loc)
    cmds.setAttr(trans_loc + '.localScaleX', system_scale * .05)
    cmds.setAttr(trans_loc + '.localScaleY', system_scale * .05)
    cmds.setAttr(trans_loc + '.localScaleZ', system_scale * .05)

    # Add Custom Attributes
    cmds.addAttr(ctrl, ln='controlBehaviour', at='enum', en='-------------:', keyable=True)
    cmds.setAttr(ctrl + '.' + 'controlBehaviour', lock=True)
    cmds.addAttr(ctrl, ln='gradient', at='double', k=True)
    cmds.addAttr(ctrl, ln='zOffsetInfluence', at='double', k=True, min=0, max=1)
    cmds.addAttr(ctrl, ln='extraOffset', at='double', k=True)
    cmds.addAttr(ctrl, ln='movement', at='double', k=True)
    cmds.setAttr(ctrl + '.movement', int(system_scale))
    cmds.setAttr(ctrl + '.gradient', 0.1)
    cmds.setAttr(ctrl + '.zOffsetInfluence', 0)

    # Multiply Movement (Base Rot)
    base_rot_multiply_node = cmds.createNode('multiplyDivide', name=ctrl_name + 'baseRot_multiplyXY')
    cmds.connectAttr(trans_loc + '.tx', base_rot_multiply_node + '.input1X')
    cmds.connectAttr(trans_loc + '.ty', base_rot_multiply_node + '.input1Y')
    cmds.connectAttr(base_rot_multiply_node + '.outputX', end_joint_parent + '.ry')
    cmds.connectAttr(base_rot_multiply_node + '.outputY', end_joint_parent + '.rz')
    cmds.connectAttr(ctrl + '.movement', base_rot_multiply_node + '.input2X')
    cmds.connectAttr(ctrl + '.movement', base_rot_multiply_node + '.input2Y')

    # Multiply Gradient (Arch)
    gradient_inverse_multiply_node = cmds.createNode('multiplyDivide', name=ctrl_name + 'influenceGradient_inverse')
    cmds.connectAttr(ctrl + '.gradient', gradient_inverse_multiply_node + '.input1X')
    cmds.setAttr(gradient_inverse_multiply_node + '.input2X', -.5)

    gradient_influence_multiply_node = cmds.createNode('multiplyDivide', name=ctrl_name + 'influenceGradient_multiply')
    cmds.connectAttr(trans_loc + '.tx', gradient_influence_multiply_node + '.input1X')
    cmds.connectAttr(gradient_inverse_multiply_node + '.outputX', gradient_influence_multiply_node + '.input2X')

    end_gradient_multiply_node = cmds.createNode('multiplyDivide', name=ctrl_name + 'endGradient_multiplyX')
    cmds.connectAttr(trans_loc + '.tx', end_gradient_multiply_node + '.input1X')
    cmds.connectAttr(gradient_influence_multiply_node + '.outputX', end_gradient_multiply_node + '.input2X')

    gradient_sum_node = cmds.createNode('plusMinusAverage', name=ctrl_name + 'gradient_sum')
    cmds.connectAttr(end_joint + '.tx', gradient_sum_node + '.input1D[0]')
    cmds.disconnectAttr(end_joint + '.tx', gradient_sum_node + '.input1D[0]')  # Keep data as offset
    cmds.connectAttr(end_gradient_multiply_node + '.outputX', gradient_sum_node + '.input1D[1]')
    cmds.connectAttr(gradient_sum_node + '.output1D', end_joint + '.tx')

    cmds.connectAttr(ctrl + '.extraOffset', gradient_sum_node + '.input1D[2]')

    z_offset_multiply_node = cmds.createNode('multiplyDivide', name=ctrl_name + 'zOffset_multiply')

    cmds.connectAttr(trans_loc + '.tz', z_offset_multiply_node + '.input1Z')
    cmds.connectAttr(ctrl + '.zOffsetInfluence', z_offset_multiply_node + '.input2Z')
    cmds.connectAttr(z_offset_multiply_node + '.outputZ', gradient_sum_node + '.input1D[3]')

    cmds.orientConstraint(trans_loc, end_joint, mo=True)

    offset_grp = ''
    if create_offset_grp:
        offset_grp = cmds.group(name=ctrl_name + 'OffsetGrp', world=True, empty=True)
        cmds.delete(cmds.parentConstraint(ctrl, offset_grp))
        cmds.parent(offset_grp, ctrl_grp)
        cmds.parent(ctrl, offset_grp)

    return ctrl, ctrl_grp, trans_loc, trans_loc_grp, end_joint, offset_grp


def create_face_proxy():
    """ Creates a proxy (guide) skeleton used to later generate entire rig """

    # Main
    main_grp = cmds.group(empty=True, world=True, name=_facial_proxy_dict.get('main_proxy_grp'))
    main_root = create_main_control(_facial_proxy_dict.get('main_root'))
    change_viewport_color(main_root, (.6, 0, .6))
    cmds.parent(main_root, main_grp)
    cmds.setAttr(main_root + '.sx', .3)
    cmds.setAttr(main_root + '.sy', .3)
    cmds.setAttr(main_root + '.sz', .3)
    cmds.move(0, 137.1, 0, main_grp)
    cmds.makeIdentity(main_grp, apply=True, scale=True)

    # Head
    head_proxy_crv = create_joint_curve(_facial_proxy_dict.get('head_crv'), .55)
    head_proxy_grp = cmds.group(empty=True, world=True, name=head_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(head_proxy_crv, head_proxy_grp)
    cmds.move(0, 142.4, 0, head_proxy_grp)
    cmds.rotate(90, 0, 90, head_proxy_grp)
    cmds.parent(head_proxy_grp, main_root)
    change_viewport_color(head_proxy_crv, CENTER_PROXY_COLOR)

    # Jaw
    jaw_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('jaw_crv'), .20)
    cmds.rotate(-90, jaw_proxy_crv, rotateZ=True)
    cmds.makeIdentity(jaw_proxy_crv, apply=True, rotate=True)
    jaw_proxy_grp = cmds.group(empty=True, world=True, name=jaw_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(jaw_proxy_crv, jaw_proxy_grp)
    cmds.move(0.0, 147.4, 2.35, jaw_proxy_grp)
    cmds.rotate(-270, 240, 90, jaw_proxy_grp)
    cmds.parent(jaw_proxy_grp, head_proxy_crv)
    change_viewport_color(jaw_proxy_crv, CENTER_PROXY_COLOR)

    # Left Eye
    left_eye_proxy_crv = create_joint_curve(_facial_proxy_dict.get('left_eye_crv'), .5)
    cmds.rotate(90, left_eye_proxy_crv, rotateX=True)
    cmds.makeIdentity(left_eye_proxy_crv, apply=True, rotate=True)
    left_eye_proxy_grp = cmds.group(empty=True, world=True, name=left_eye_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_eye_proxy_crv, left_eye_proxy_grp)
    cmds.move(3.5, 151.2, 8.7, left_eye_proxy_grp)
    cmds.parent(left_eye_proxy_grp, head_proxy_crv)
    change_viewport_color(left_eye_proxy_crv, LEFT_PROXY_COLOR)

    # Right Eye
    right_eye_proxy_crv = create_joint_curve(_facial_proxy_dict.get('right_eye_crv'), .5)
    cmds.rotate(90, right_eye_proxy_crv, rotateX=True)
    cmds.makeIdentity(right_eye_proxy_crv, apply=True, rotate=True)
    right_eye_proxy_grp = cmds.group(empty=True, world=True, name=right_eye_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_eye_proxy_crv, right_eye_proxy_grp)
    cmds.move(-3.5, 151.2, 8.7, right_eye_proxy_grp)
    cmds.parent(right_eye_proxy_grp, head_proxy_crv)
    change_viewport_color(right_eye_proxy_crv, RIGHT_PROXY_COLOR)

    # ################ Eyebrows ################
    # Left Eyebrow Proxy
    left_inner_brow_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('left_inner_brow_crv'), .2)
    cmds.rotate(90, left_inner_brow_proxy_crv, rotateX=True)
    cmds.makeIdentity(left_inner_brow_proxy_crv, apply=True, rotate=True)
    left_inner_brow_proxy_grp = cmds.group(empty=True, world=True,
                                           name=left_inner_brow_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_inner_brow_proxy_crv, left_inner_brow_proxy_grp)
    cmds.move(1.2, 153.2, 13, left_inner_brow_proxy_grp)
    cmds.parent(left_inner_brow_proxy_grp, left_eye_proxy_crv)
    change_viewport_color(left_inner_brow_proxy_crv, LEFT_PROXY_COLOR)

    left_mid_brow_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('left_mid_brow_crv'), .2)
    cmds.rotate(90, left_mid_brow_proxy_crv, rotateX=True)
    cmds.makeIdentity(left_mid_brow_proxy_crv, apply=True, rotate=True)
    left_mid_brow_proxy_grp = cmds.group(empty=True, world=True, name=left_mid_brow_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_mid_brow_proxy_crv, left_mid_brow_proxy_grp)
    cmds.move(3.5, 154.2, 13, left_mid_brow_proxy_grp)
    cmds.parent(left_mid_brow_proxy_grp, left_eye_proxy_crv)
    change_viewport_color(left_mid_brow_proxy_crv, LEFT_PROXY_COLOR)

    left_outer_brow_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('left_outer_brow_crv'), .2)
    cmds.rotate(90, left_outer_brow_proxy_crv, rotateX=True)
    cmds.makeIdentity(left_outer_brow_proxy_crv, apply=True, rotate=True)
    left_outer_brow_proxy_grp = cmds.group(empty=True, world=True,
                                           name=left_outer_brow_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_outer_brow_proxy_crv, left_outer_brow_proxy_grp)
    cmds.move(5.8, 153.2, 13, left_outer_brow_proxy_grp)
    cmds.parent(left_outer_brow_proxy_grp, left_eye_proxy_crv)
    change_viewport_color(left_outer_brow_proxy_crv, LEFT_PROXY_COLOR)

    # Right Eyebrow Proxy
    right_inner_brow_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('right_inner_brow_crv'), .2)
    cmds.rotate(90, right_inner_brow_proxy_crv, rotateX=True)
    cmds.makeIdentity(right_inner_brow_proxy_crv, apply=True, rotate=True)
    right_inner_brow_proxy_grp = cmds.group(empty=True, world=True,
                                            name=right_inner_brow_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_inner_brow_proxy_crv, right_inner_brow_proxy_grp)
    cmds.move(-1.2, 153.2, 13, right_inner_brow_proxy_grp)
    cmds.parent(right_inner_brow_proxy_grp, right_eye_proxy_crv)
    change_viewport_color(right_inner_brow_proxy_crv, RIGHT_PROXY_COLOR)

    right_mid_brow_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('right_mid_brow_crv'), .2)
    cmds.rotate(90, right_mid_brow_proxy_crv, rotateX=True)
    cmds.makeIdentity(right_mid_brow_proxy_crv, apply=True, rotate=True)
    right_mid_brow_proxy_grp = cmds.group(empty=True, world=True,
                                          name=right_mid_brow_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_mid_brow_proxy_crv, right_mid_brow_proxy_grp)
    cmds.move(-3.5, 154.2, 13, right_mid_brow_proxy_grp)
    cmds.parent(right_mid_brow_proxy_grp, right_eye_proxy_crv)
    change_viewport_color(right_mid_brow_proxy_crv, RIGHT_PROXY_COLOR)

    right_outer_brow_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('right_outer_brow_crv'), .2)
    cmds.rotate(90, right_outer_brow_proxy_crv, rotateX=True)
    cmds.makeIdentity(right_outer_brow_proxy_crv, apply=True, rotate=True)
    right_outer_brow_proxy_grp = cmds.group(empty=True, world=True,
                                            name=right_outer_brow_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_outer_brow_proxy_crv, right_outer_brow_proxy_grp)
    cmds.move(-5.8, 153.2, 13, right_outer_brow_proxy_grp)
    cmds.parent(right_outer_brow_proxy_grp, right_eye_proxy_crv)
    change_viewport_color(right_outer_brow_proxy_crv, RIGHT_PROXY_COLOR)

    ################ Mouth ################
    # MID
    mid_upper_lip_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('mid_upper_lip_crv'), .1)
    cmds.rotate(90, mid_upper_lip_proxy_crv, rotateX=True)
    cmds.makeIdentity(mid_upper_lip_proxy_crv, apply=True, rotate=True)
    mid_upper_lip_proxy_grp = cmds.group(empty=True, world=True, name=mid_upper_lip_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(mid_upper_lip_proxy_crv, mid_upper_lip_proxy_grp)
    cmds.move(0.0, 144.8, 13.3, mid_upper_lip_proxy_grp)
    cmds.parent(mid_upper_lip_proxy_grp, main_root)
    change_viewport_color(mid_upper_lip_proxy_crv, CENTER_PROXY_COLOR)

    mid_lower_lip_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('mid_lower_lip_crv'), .1)
    cmds.rotate(90, mid_lower_lip_proxy_crv, rotateX=True)
    cmds.makeIdentity(mid_lower_lip_proxy_crv, apply=True, rotate=True)
    mid_lower_lip_proxy_grp = cmds.group(empty=True, world=True, name=mid_lower_lip_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(mid_lower_lip_proxy_crv, mid_lower_lip_proxy_grp)
    cmds.move(0.0, 143.8, 13.3, mid_lower_lip_proxy_grp)
    cmds.parent(mid_lower_lip_proxy_grp, main_root)
    change_viewport_color(mid_lower_lip_proxy_crv, CENTER_PROXY_COLOR)

    # LEFT OUTER
    left_upper_lip_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('left_upper_outer_lip_crv'), .07)
    cmds.rotate(90, left_upper_lip_proxy_crv, rotateX=True)
    cmds.makeIdentity(left_upper_lip_proxy_crv, apply=True, rotate=True)
    left_upper_lip_proxy_grp = cmds.group(empty=True, world=True,
                                          name=left_upper_lip_proxy_crv + GRP_SUFFIX.capitalize())
    left_upper_lip_proxy_offset_grp = cmds.group(empty=True, world=True,
                                                 name=left_upper_lip_proxy_crv + 'Offset' + GRP_SUFFIX.capitalize())
    cmds.parent(left_upper_lip_proxy_crv, left_upper_lip_proxy_offset_grp)
    cmds.parent(left_upper_lip_proxy_offset_grp, left_upper_lip_proxy_grp)
    cmds.move(1.45, 144.7, 12.7, left_upper_lip_proxy_grp)
    cmds.parent(left_upper_lip_proxy_grp, main_root)
    change_viewport_color(left_upper_lip_proxy_crv, LEFT_PROXY_COLOR)

    left_lower_lip_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('left_lower_outer_lip_crv'), .07)
    cmds.rotate(90, left_lower_lip_proxy_crv, rotateX=True)
    cmds.makeIdentity(left_lower_lip_proxy_crv, apply=True, rotate=True)
    left_lower_lip_proxy_grp = cmds.group(empty=True, world=True,
                                          name=left_lower_lip_proxy_crv + GRP_SUFFIX.capitalize())
    left_lower_lip_proxy_offset_grp = cmds.group(empty=True, world=True,
                                                 name=left_lower_lip_proxy_crv + 'Offset' + GRP_SUFFIX.capitalize())
    cmds.parent(left_lower_lip_proxy_crv, left_lower_lip_proxy_offset_grp)
    cmds.parent(left_lower_lip_proxy_offset_grp, left_lower_lip_proxy_grp)
    cmds.move(1.45, 144, 12.7, left_lower_lip_proxy_grp)
    cmds.parent(left_lower_lip_proxy_grp, main_root)
    change_viewport_color(left_lower_lip_proxy_crv, LEFT_PROXY_COLOR)

    # LEFT CORNER
    left_corner_lip_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('left_corner_lip_crv'), .05)
    cmds.rotate(90, left_corner_lip_proxy_crv, rotateX=True)
    cmds.makeIdentity(left_corner_lip_proxy_crv, apply=True, rotate=True)
    left_upper_corner_lip_proxy_grp = cmds.group(empty=True, world=True,
                                                 name=left_corner_lip_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_corner_lip_proxy_crv, left_upper_corner_lip_proxy_grp)
    cmds.move(2.6, 144.4, 12, left_upper_corner_lip_proxy_grp)
    cmds.rotate(0, 30, 0, left_corner_lip_proxy_crv)
    cmds.parent(left_upper_corner_lip_proxy_grp, main_root)
    change_viewport_color(left_corner_lip_proxy_crv, LEFT_PROXY_COLOR)

    # Auto Orient Outer Controls
    left_outer_rot_multiply_node = cmds.createNode('multiplyDivide', name='left_upperOuter_autoRot_multiply')
    cmds.connectAttr(left_corner_lip_proxy_crv + '.ry', left_outer_rot_multiply_node + '.input1Y')
    cmds.connectAttr(left_outer_rot_multiply_node + '.outputY', left_upper_lip_proxy_offset_grp + '.ry')
    cmds.connectAttr(left_outer_rot_multiply_node + '.outputY', left_lower_lip_proxy_offset_grp + '.ry')
    cmds.setAttr(left_outer_rot_multiply_node + '.input2Y', 0.5)

    # RIGHT OUTER
    right_upper_lip_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('right_upper_outer_lip_crv'), .07)
    cmds.rotate(90, right_upper_lip_proxy_crv, rotateX=True)
    cmds.makeIdentity(right_upper_lip_proxy_crv, apply=True, rotate=True)
    right_upper_lip_proxy_grp = cmds.group(empty=True, world=True,
                                           name=right_upper_lip_proxy_crv + GRP_SUFFIX.capitalize())
    right_upper_lip_proxy_offset_grp = cmds.group(empty=True, world=True,
                                                  name=right_upper_lip_proxy_crv + 'Offset' + GRP_SUFFIX.capitalize())
    cmds.parent(right_upper_lip_proxy_crv, right_upper_lip_proxy_offset_grp)
    cmds.parent(right_upper_lip_proxy_offset_grp, right_upper_lip_proxy_grp)
    cmds.move(-1.45, 144.7, 12.7, right_upper_lip_proxy_grp)
    cmds.parent(right_upper_lip_proxy_grp, main_root)
    change_viewport_color(right_upper_lip_proxy_crv, RIGHT_PROXY_COLOR)

    right_lower_lip_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('right_lower_outer_lip_crv'), .07)
    cmds.rotate(90, right_lower_lip_proxy_crv, rotateX=True)
    cmds.makeIdentity(right_lower_lip_proxy_crv, apply=True, rotate=True)
    right_lower_lip_proxy_grp = cmds.group(empty=True, world=True,
                                           name=right_lower_lip_proxy_crv + GRP_SUFFIX.capitalize())
    right_lower_lip_proxy_offset_grp = cmds.group(empty=True, world=True,
                                                  name=right_lower_lip_proxy_crv + 'Offset' + GRP_SUFFIX.capitalize())
    cmds.parent(right_lower_lip_proxy_crv, right_lower_lip_proxy_offset_grp)
    cmds.parent(right_lower_lip_proxy_offset_grp, right_lower_lip_proxy_grp)
    cmds.move(-1.45, 144, 12.7, right_lower_lip_proxy_grp)
    cmds.parent(right_lower_lip_proxy_grp, main_root)
    change_viewport_color(right_lower_lip_proxy_crv, RIGHT_PROXY_COLOR)

    # RIGHT CORNER
    right_corner_lip_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('right_corner_lip_crv'), .05)
    cmds.rotate(90, right_corner_lip_proxy_crv, rotateX=True)
    cmds.makeIdentity(right_corner_lip_proxy_crv, apply=True, rotate=True)
    right_upper_corner_lip_proxy_grp = cmds.group(empty=True, world=True,
                                                  name=right_corner_lip_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_corner_lip_proxy_crv, right_upper_corner_lip_proxy_grp)
    cmds.move(-2.6, 144.4, 12, right_upper_corner_lip_proxy_grp)
    cmds.rotate(0, -30, 0, right_corner_lip_proxy_crv)
    cmds.parent(right_upper_corner_lip_proxy_grp, main_root)
    change_viewport_color(right_corner_lip_proxy_crv, RIGHT_PROXY_COLOR)

    # Auto Orient Outer Controls
    right_outer_rot_multiply_node = cmds.createNode('multiplyDivide', name='right_upperOuter_autoRot_multiply')
    cmds.connectAttr(right_corner_lip_proxy_crv + '.ry', right_outer_rot_multiply_node + '.input1Y')
    cmds.connectAttr(right_outer_rot_multiply_node + '.outputY', right_upper_lip_proxy_offset_grp + '.ry')
    cmds.connectAttr(right_outer_rot_multiply_node + '.outputY', right_lower_lip_proxy_offset_grp + '.ry')
    cmds.setAttr(right_outer_rot_multiply_node + '.input2Y', 0.5)

    ################

    # Find Pre-existing Elements
    if find_pre_existing_elements:
        if cmds.objExists(_preexisting_dict.get('neck_base_jnt')):
            cmds.delete(cmds.pointConstraint(_preexisting_dict.get('neck_base_jnt'), main_root))

        if cmds.objExists(_preexisting_dict.get('head_jnt')):
            cmds.delete(cmds.pointConstraint(_preexisting_dict.get('head_jnt'), head_proxy_crv))

        if cmds.objExists(_preexisting_dict.get('jaw_jnt')):
            cmds.delete(cmds.parentConstraint(_preexisting_dict.get('jaw_jnt'), jaw_proxy_crv))

        if cmds.objExists(_preexisting_dict.get('left_eye_jnt')):
            cmds.delete(cmds.parentConstraint(_preexisting_dict.get('left_eye_jnt'), left_eye_proxy_crv))

        if cmds.objExists(_preexisting_dict.get('right_eye_jnt')):
            cmds.delete(cmds.parentConstraint(_preexisting_dict.get('right_eye_jnt'), right_eye_proxy_crv))

    # Re-parent elements to main curve
    to_re_parent = [left_inner_brow_proxy_grp,
                    left_mid_brow_proxy_grp,
                    left_outer_brow_proxy_grp,
                    jaw_proxy_grp,
                    left_eye_proxy_grp,
                    right_eye_proxy_grp,
                    ]
    for obj in to_re_parent:
        cmds.parent(obj, main_root)


def create_face_controls():
    """ Creates Facial Rig Controls """

    def rename_proxy(old_name):
        """
        Replaces a few parts of the old names for the creation of joints
        Replaces "proxy" with "jnt"
        Replaces "endProxy" with "endJnt"

                Parameters:
                    old_name (string): Name of the proxy element

                Returns:
                    new_name (string): Name of the joint to be created out of the element

        """
        return old_name.replace(PROXY_SUFFIX, JNT_SUFFIX).replace('end' + PROXY_SUFFIX.capitalize(),
                                                                  'end' + JNT_SUFFIX.capitalize())

    # Create Parent Groups
    face_prefix = 'facial_'

    rig_grp = cmds.group(name=face_prefix + 'rig_grp', empty=True, world=True)
    change_outliner_color(rig_grp, (1, .45, .7))

    skeleton_grp = cmds.group(name=(face_prefix + 'skeleton_' + GRP_SUFFIX), empty=True, world=True)
    change_outliner_color(skeleton_grp, (.75, .45, .95))  # Purple (Like a joint)

    controls_grp = cmds.group(name=face_prefix + 'controls_' + GRP_SUFFIX, empty=True, world=True)
    change_outliner_color(controls_grp, (1, 0.47, 0.18))

    rig_setup_grp = cmds.group(name=face_prefix + 'rig_setup_' + GRP_SUFFIX, empty=True, world=True)
    change_outliner_color(rig_setup_grp, (1, .26, .26))

    mouth_automation_grp = cmds.group(name='mouthAutomation_grp', world=True, empty=True)
    change_outliner_color(mouth_automation_grp, (1, .65, .45))

    cmds.parent(skeleton_grp, rig_grp)
    cmds.parent(controls_grp, rig_grp)
    cmds.parent(rig_setup_grp, rig_grp)
    cmds.parent(mouth_automation_grp, rig_setup_grp)

    # # Mouth Scale
    mouth_scale = 0
    mouth_scale += dist_center_to_center(_facial_proxy_dict.get('left_corner_lip_crv'),
                                         _facial_proxy_dict.get('mid_upper_lip_crv'))
    mouth_scale += dist_center_to_center(_facial_proxy_dict.get('mid_upper_lip_crv'),
                                         _facial_proxy_dict.get('right_corner_lip_crv'))

    ####################################### Create Joints #######################################
    _facial_joints_dict = {}
    ignore_crv_list = ['left_corner_lip_crv', 'right_corner_lip_crv']

    # Find existing elements
    for obj in _preexisting_dict:
        if 'ctrl' not in obj and 'neck' not in obj and cmds.objExists(_preexisting_dict.get(obj)):
            ignore_crv_list.append(obj.replace('jnt', 'crv'))
            _facial_joints_dict[obj] = obj

    # Create Joints
    for obj in _facial_proxy_dict:
        if obj.endswith('_crv') and obj not in ignore_crv_list:
            cmds.select(d=True)
            joint = cmds.joint(name=rename_proxy(_facial_proxy_dict.get(obj)), radius=.5)
            constraint = cmds.pointConstraint(_facial_proxy_dict.get(obj), joint)
            cmds.delete(constraint)
            temp_grp = cmds.group(name='temp_' + str(random.random()), empty=True, world=True)
            cmds.delete(cmds.parentConstraint(_facial_proxy_dict.get(obj), temp_grp))
            rotate_y = cmds.getAttr(temp_grp + '.ry')
            cmds.delete(temp_grp)
            cmds.rotate(0, rotate_y, 0, joint)
            cmds.makeIdentity(joint, apply=True, rotate=True)
            _facial_joints_dict[obj.replace('_crv', '_' + JNT_SUFFIX).replace('_proxy', '')] = joint

    # If jaw joint wasn't found, orient the created one
    jaw_ctrl = 'jaw_ctrl'
    jaw_ctrl_grp = 'jaw_ctrlGrp'
    is_new_jaw = False
    if not cmds.objExists(_preexisting_dict.get('jaw_jnt')):
        cmds.matchTransform(_facial_joints_dict.get('jaw_jnt'), _facial_proxy_dict.get('jaw_crv'), pos=1, rot=1)
        cmds.makeIdentity(_facial_joints_dict.get('jaw_jnt'), apply=True, rotate=True)
        jaw_end_jnt = cmds.duplicate(_facial_joints_dict.get('jaw_jnt'),
                                     name=_facial_joints_dict.get('jaw_jnt').replace(JNT_SUFFIX,
                                                                                     'end' + JNT_SUFFIX.capitalize()))[
            0]
        cmds.delete(cmds.pointConstraint(_facial_proxy_dict.get('mid_upper_lip_crv'), jaw_end_jnt))
        cmds.parent(jaw_end_jnt, _facial_joints_dict.get('jaw_jnt'))
        cmds.setAttr(jaw_end_jnt + '.ty', 0)
        cmds.setAttr(jaw_end_jnt + '.tz', 0)

        # Create Jaw Control (Since Jnt didn't exist...)
        jaw_ctrl = cmds.curve(name=jaw_ctrl,
                              p=[[0.013, 0.088, -0.088], [0.013, 0.016, -0.125], [0.013, 0.042, -0.088],
                                 [0.013, 0.078, -0.0], [0.013, 0.042, 0.088], [0.013, 0.016, 0.125],
                                 [0.013, 0.088, 0.088], [0.013, 0.125, 0.0], [0.013, 0.088, -0.088],
                                 [0.013, 0.016, -0.125], [0.013, 0.042, -0.088]], d=3, per=True,
                              k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        cmds.setAttr(jaw_ctrl + '.scaleX', mouth_scale * 2)
        cmds.setAttr(jaw_ctrl + '.scaleY', mouth_scale * 2)
        cmds.setAttr(jaw_ctrl + '.scaleZ', mouth_scale * 2)
        cmds.makeIdentity(jaw_ctrl, apply=True, scale=True)
        for shape in cmds.listRelatives(jaw_ctrl, s=True, f=True) or []:
            shape = cmds.rename(shape, '{0}Shape'.format(jaw_ctrl))
        change_viewport_color(jaw_ctrl, (.8, .8, 0))
        jaw_ctrl_grp = cmds.group(name=jaw_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
        cmds.parent(jaw_ctrl, jaw_ctrl_grp)
        cmds.delete(cmds.parentConstraint(_facial_joints_dict.get('jaw_jnt'), jaw_ctrl_grp))

        desired_pivot = cmds.xform(jaw_ctrl, q=True, ws=True, t=True)
        cmds.delete(cmds.parentConstraint(jaw_end_jnt, jaw_ctrl))
        cmds.xform(jaw_ctrl, piv=desired_pivot, ws=True)
        cmds.makeIdentity(jaw_ctrl, apply=True, scale=True, rotate=True, translate=True)
        cmds.parentConstraint(jaw_ctrl, _facial_joints_dict.get('jaw_jnt'), mo=True)
        cmds.parent(jaw_ctrl_grp, controls_grp)
        is_new_jaw = True
        cmds.parent(_facial_joints_dict.get('jaw_jnt'), skeleton_grp)
    else:
        jaw_ctrl = _preexisting_dict.get('jaw_ctrl')
        jaw_ctrl_grp = _preexisting_dict.get('jaw_ctrl') + CTRL_SUFFIX.capitalize()

    # If head joint wasn't found, orient the created one
    head_ctrl = 'head_ctrl'
    head_ctrl_grp = 'head_ctrlGrp'
    if not cmds.objExists(_preexisting_dict.get('head_jnt')):
        head_ctrl = cmds.curve(name=_preexisting_dict.get('head_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                               p=[[0.0, 0.0, 0.0], [-0.0, 0.0, -1.794], [-0.0, 0.067, -1.803], [-0.0, 0.128, -1.829],
                                  [-0.0, 0.181, -1.869], [-0.0, 0.222, -1.922], [-0.0, 0.247, -1.984],
                                  [-0.0, 0.256, -2.05], [-0.0, 0.0, -2.051], [-0.0, 0.0, -1.794],
                                  [-0.0, -0.067, -1.803], [-0.0, -0.129, -1.829], [-0.0, -0.181, -1.869],
                                  [-0.0, -0.222, -1.923], [-0.0, -0.247, -1.984], [-0.0, -0.257, -2.05],
                                  [-0.0, -0.248, -2.117], [-0.0, -0.222, -2.178], [-0.0, -0.181, -2.231],
                                  [-0.0, -0.128, -2.272], [-0.0, -0.067, -2.297], [-0.0, 0.0, -2.307],
                                  [-0.0, 0.066, -2.298], [-0.0, 0.128, -2.272], [-0.0, 0.181, -2.232],
                                  [-0.0, 0.221, -2.179], [-0.0, 0.247, -2.116], [-0.0, 0.256, -2.05],
                                  [-0.0, -0.257, -2.05], [-0.0, 0.0, -2.051], [-0.0, 0.0, -2.307]], d=1)
        cmds.setAttr(head_ctrl + '.scaleX', mouth_scale)
        cmds.setAttr(head_ctrl + '.scaleY', mouth_scale)
        cmds.setAttr(head_ctrl + '.scaleZ', mouth_scale)
        cmds.makeIdentity(head_ctrl, apply=True, scale=True)

        for shape in cmds.listRelatives(head_ctrl, s=True, f=True) or []:
            shape = cmds.rename(shape, '{0}Shape'.format(head_ctrl))

        change_viewport_color(head_ctrl, (.8, .8, 0))
        head_ctrl_grp = cmds.group(name=head_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
        cmds.parent(head_ctrl, head_ctrl_grp)
        cmds.delete(cmds.parentConstraint(_facial_joints_dict.get('head_jnt'), head_ctrl_grp))

        cmds.parentConstraint(head_ctrl, _facial_joints_dict.get('head_jnt'), mo=True)
        cmds.parent(head_ctrl_grp, controls_grp)
        if is_new_jaw:
            cmds.parent(jaw_ctrl_grp, head_ctrl)
            cmds.parent(_facial_joints_dict.get('jaw_jnt'), _facial_joints_dict.get('head_jnt'))
        cmds.parent(_facial_joints_dict.get('head_jnt'), skeleton_grp)
    else:
        head_ctrl = _preexisting_dict.get('head_ctrl')
        head_ctrl_grp = _preexisting_dict.get('head_ctrl') + CTRL_SUFFIX.capitalize()

    ######## Special Joint Cases ########
    # Mouth Corners
    for obj in ['left_corner_lip_crv', 'right_corner_lip_crv']:
        for case in ['upper', 'lower']:

            cmds.select(d=True)
            joint = cmds.joint(name=rename_proxy(_facial_proxy_dict.get(obj).replace('cornerLip', case + 'CornerLip')),
                               radius=.3)

            constraint = cmds.pointConstraint(_facial_proxy_dict.get(obj), joint)
            cmds.delete(constraint)
            temp_grp = cmds.group(name='temp_' + str(random.random()), empty=True, world=True)
            cmds.delete(cmds.parentConstraint(_facial_proxy_dict.get(obj), temp_grp))
            rotate_y = cmds.getAttr(temp_grp + '.ry')
            cmds.delete(temp_grp)
            cmds.rotate(0, rotate_y, 0, joint)
            cmds.makeIdentity(joint, apply=True, rotate=True)
            if case == 'upper':
                cmds.move(mouth_scale * .02, joint, moveY=True, relative=True)
            else:
                cmds.move(mouth_scale * -.02, joint, moveY=True, relative=True)
            key = obj.replace('_crv', '_' + JNT_SUFFIX).replace('_proxy', '').replace('corner_lip',
                                                                                      case + '_corner_lip')
            _facial_joints_dict[key] = joint

    # Parent Mouth Joints to Head
    to_head_parent = [_facial_joints_dict.get('left_inner_brow_jnt'),
                      _facial_joints_dict.get('left_mid_brow_jnt'),
                      _facial_joints_dict.get('left_outer_brow_jnt'),

                      _facial_joints_dict.get('right_inner_brow_jnt'),
                      _facial_joints_dict.get('right_mid_brow_jnt'),
                      _facial_joints_dict.get('right_outer_brow_jnt'),

                      _facial_joints_dict.get('mid_upper_lip_jnt'),
                      _facial_joints_dict.get('mid_lower_lip_jnt'),
                      _facial_joints_dict.get('left_upper_outer_lip_jnt'),
                      _facial_joints_dict.get('left_lower_outer_lip_jnt'),

                      _facial_joints_dict.get('right_upper_outer_lip_jnt'),
                      _facial_joints_dict.get('right_lower_outer_lip_jnt'),

                      _facial_joints_dict.get('left_upper_corner_lip_jnt'),
                      _facial_joints_dict.get('left_lower_corner_lip_jnt'),
                      _facial_joints_dict.get('right_upper_corner_lip_jnt'),
                      _facial_joints_dict.get('right_lower_corner_lip_jnt'),
                      ]
    for obj in to_head_parent:
        cmds.parent(obj, _facial_joints_dict.get('head_jnt'))

    # Create mouth driver joints
    mouth_joints = [_facial_joints_dict.get('mid_upper_lip_jnt'),
                    _facial_joints_dict.get('mid_lower_lip_jnt'),

                    _facial_joints_dict.get('left_upper_outer_lip_jnt'),
                    _facial_joints_dict.get('left_lower_outer_lip_jnt'),
                    _facial_joints_dict.get('left_upper_corner_lip_jnt'),
                    _facial_joints_dict.get('left_lower_corner_lip_jnt'),

                    _facial_joints_dict.get('right_upper_outer_lip_jnt'),
                    _facial_joints_dict.get('right_lower_outer_lip_jnt'),
                    _facial_joints_dict.get('right_upper_corner_lip_jnt'),
                    _facial_joints_dict.get('right_lower_corner_lip_jnt'),
                    ]

    cmds.select(clear=True)
    mouth_pivot_jnt = cmds.joint(name='mouth_pivot' + JNT_SUFFIX.capitalize(), radius=.5)
    cmds.delete(cmds.parentConstraint(_facial_joints_dict.get('jaw_jnt'), mouth_pivot_jnt))
    cmds.parentConstraint(_facial_joints_dict.get('head_jnt'), mouth_pivot_jnt, mo=True)
    cmds.parent(mouth_pivot_jnt, skeleton_grp)

    mouth_driver_joints = []
    mouth_root_joints = []
    for jnt in mouth_joints:
        cmds.select(clear=True)
        new_joint = cmds.joint(name=jnt.replace(JNT_SUFFIX, 'root' + JNT_SUFFIX.capitalize()), radius=.5)
        # Use different pivot?
        # cmds.delete(cmds.pointConstraint([jnt, _facial_joints_dict.get('jaw_jnt')], new_joint, skip=('x')))
        # cmds.delete(cmds.pointConstraint(jnt, new_joint, skip=('x', 'z')))
        cmds.delete(cmds.pointConstraint(_facial_joints_dict.get('jaw_jnt'), new_joint))
        driver_jnt = cmds.duplicate(jnt, name=jnt.replace(JNT_SUFFIX, 'driver' + JNT_SUFFIX.capitalize()), po=True)[0]
        cmds.parent(driver_jnt, new_joint)
        cmds.joint(new_joint, e=True, oj='xyz', secondaryAxisOrient='yup', zso=True, ch=True)
        cmds.parent(new_joint, mouth_pivot_jnt)
        cmds.parentConstraint(driver_jnt, jnt)
        mouth_driver_joints.append(driver_jnt)
        mouth_root_joints.append(new_joint)

    ####################################### Mouth #######################################

    mouth_controls = []
    for jnt in mouth_driver_joints:
        ctrl_objs = create_arched_control(jnt, ctrl_name=jnt.replace('driver' + JNT_SUFFIX.capitalize(), CTRL_SUFFIX),
                                          radius=mouth_scale * .05, create_offset_grp=True)
        mouth_controls.append(ctrl_objs)

    # Jaw Pivot (For lower mouth controls)
    jaw_pivot_grp = cmds.group(name='jawPivot_dataGrp', empty=True, world=True)
    jaw_pivot_data = cmds.group(name='jawPivot_data', empty=True, world=True)
    cmds.parent(jaw_pivot_data, jaw_pivot_grp)
    cmds.connectAttr(_facial_joints_dict.get('jaw_jnt') + '.rotate', jaw_pivot_data + '.rotate')
    cmds.connectAttr(_facial_joints_dict.get('jaw_jnt') + '.translate', jaw_pivot_data + '.translate')
    cmds.delete(cmds.parentConstraint(_facial_joints_dict.get('jaw_jnt'), jaw_pivot_grp))
    cmds.parent(jaw_pivot_grp, mouth_automation_grp)

    mouth_ctrls_grp = cmds.group(name='mouth_' + CTRL_SUFFIX + GRP_SUFFIX.capitalize(), empty=True, world=True)
    mouth_data_grp = cmds.group(name='mouth_data' + GRP_SUFFIX.capitalize(), empty=True, world=True)
    jaw_ctrls_grp = cmds.group(name='mouthJaw_' + CTRL_SUFFIX + GRP_SUFFIX.capitalize(), empty=True, world=True)
    jaw_data_grp = cmds.group(name='mouthJaw_data' + GRP_SUFFIX.capitalize(), empty=True, world=True)

    cmds.delete(cmds.parentConstraint(_facial_joints_dict.get('head_jnt'), mouth_ctrls_grp))
    cmds.delete(cmds.parentConstraint(_facial_joints_dict.get('head_jnt'), mouth_data_grp))
    cmds.delete(cmds.parentConstraint(_facial_joints_dict.get('jaw_jnt'), jaw_ctrls_grp))
    cmds.delete(cmds.parentConstraint(_facial_joints_dict.get('jaw_jnt'), jaw_data_grp))

    cmds.parent(mouth_ctrls_grp, head_ctrl)
    cmds.parent(mouth_data_grp, head_ctrl)
    cmds.parent(jaw_data_grp, jaw_ctrls_grp)
    cmds.parent(jaw_ctrls_grp, head_ctrl)

    _mouth_outer_automation_elements = {'left_upperOuterLip_ctrl': [],
                                        'left_lowerOuterLip_ctrl': [],
                                        'right_upperOuterLip_ctrl': [],
                                        'right_lowerOuterLip_ctrl': []
                                        }
    _corner_ctrls = []

    for ctrl_data in mouth_controls:
        # Unpack Data
        ctrl = ctrl_data[0]
        ctrl_grp = ctrl_data[1]
        trans_loc = ctrl_data[2]
        trans_loc_grp = ctrl_data[3]
        end_joint = ctrl_data[4]
        offset_grp = ctrl_data[5]

        # Rename Offset as Driven
        offset_grp = cmds.rename(offset_grp, offset_grp.replace('Offset', 'Driven'))

        # Organize Hierarchy
        cmds.parent(ctrl_grp, mouth_ctrls_grp)
        cmds.parent(trans_loc_grp, mouth_data_grp)

        # Adjust Controls
        cmds.setAttr(ctrl + '.movement', mouth_scale)
        cmds.setAttr(trans_loc + '.v', 0)

        # Find Skinned Joint
        skinned_jnt_parent_constraint = \
            cmds.listConnections(end_joint + '.translate', destination=True, type='parentConstraint')[0]
        skinned_jnt = cmds.listConnections(skinned_jnt_parent_constraint + '.constraintRotateX', type='joint')[0]
        pure_fk_constraint = cmds.parentConstraint(trans_loc, skinned_jnt, mo=True)

        # FK Override
        cmds.addAttr(ctrl, ln='fkOverride', at='double', k=True, maxValue=1, minValue=0, niceName='FK Override')
        switch_reverse_node = cmds.createNode('reverse', name=ctrl.replace(CTRL_SUFFIX, 'reverseSwitch'))
        cmds.connectAttr(ctrl + '.fkOverride', switch_reverse_node + '.inputX', f=True)
        cmds.connectAttr(switch_reverse_node + '.outputX', pure_fk_constraint[0] + '.w0', f=True)
        cmds.connectAttr(ctrl + '.fkOverride', pure_fk_constraint[0] + '.w1', f=True)

        if 'lower' in ctrl:
            cmds.addAttr(ctrl, ln='jawInfluence', at='double', k=True, maxValue=1, minValue=0)

            jaw_pivot_grp = cmds.duplicate(jaw_pivot_data, name=ctrl + 'Pivot')[0]
            cmds.parent(ctrl_grp, jaw_pivot_grp)
            jaw_influence_multiply_node = cmds.createNode('multiplyDivide', name=ctrl.replace(CTRL_SUFFIX, 'multiply'))

            cmds.connectAttr(jaw_pivot_data + '.rotate', jaw_influence_multiply_node + '.input1', force=True)
            cmds.connectAttr(jaw_influence_multiply_node + '.output', jaw_pivot_grp + '.rotate', force=True)

            cmds.connectAttr(ctrl + '.jawInfluence', jaw_influence_multiply_node + '.input2X', force=True)
            cmds.connectAttr(ctrl + '.jawInfluence', jaw_influence_multiply_node + '.input2Y', force=True)
            cmds.connectAttr(ctrl + '.jawInfluence', jaw_influence_multiply_node + '.input2Z', force=True)

            if 'Corner' in ctrl:
                cmds.setAttr(ctrl + '.jawInfluence', 0.5)
            elif 'Outer' in ctrl:
                cmds.setAttr(ctrl + '.jawInfluence', .8)
            else:
                cmds.setAttr(ctrl + '.jawInfluence', 1)

            cmds.parent(jaw_pivot_grp, jaw_data_grp)

        if 'Outer' in ctrl:
            new_offset_grp = cmds.group(name=ctrl + 'Offset' + GRP_SUFFIX.capitalize(), empty=True, world=True)
            cmds.delete(cmds.parentConstraint(offset_grp, new_offset_grp))
            cmds.parent(new_offset_grp, ctrl_grp)
            cmds.parent(offset_grp, new_offset_grp)
            mid_name = ctrl.replace('left_', 'mid_').replace('right_', 'mid_').replace('Outer', '')
            corner_name = ctrl.replace('Outer', 'Corner')
            _mouth_outer_automation_elements.get(ctrl).append(mid_name)
            _mouth_outer_automation_elements.get(ctrl).append(new_offset_grp)
            _mouth_outer_automation_elements.get(ctrl).append(corner_name)

        if 'Corner' in ctrl:
            _corner_ctrls.append(ctrl)

        # Color Controls
        if 'left_' in ctrl:
            change_viewport_color(ctrl, LEFT_CTRL_COLOR)
        elif 'right_' in ctrl:
            change_viewport_color(ctrl, RIGHT_CTRL_COLOR)
        else:
            change_viewport_color(ctrl, CENTER_CTRL_COLOR)

    # Create Mid Corner Constraint
    for ctrl in _mouth_outer_automation_elements:
        abc_joints = _mouth_outer_automation_elements.get(ctrl)
        constraint = cmds.parentConstraint([abc_joints[0], abc_joints[2], mouth_automation_grp], abc_joints[1], mo=True)
        cmds.addAttr(ctrl, ln='midCornerInfluence', at='double', k=True, maxValue=1, minValue=0)
        cmds.setAttr(ctrl + '.midCornerInfluence', 1)
        switch_reverse_node = cmds.createNode('reverse', name=ctrl.replace(CTRL_SUFFIX, 'reverseSwitch'))
        cmds.connectAttr(ctrl + '.midCornerInfluence', switch_reverse_node + '.inputX', f=True)

        cmds.connectAttr(ctrl + '.midCornerInfluence', constraint[0] + '.w0', f=True)
        cmds.connectAttr(ctrl + '.midCornerInfluence', constraint[0] + '.w1', f=True)
        cmds.connectAttr(switch_reverse_node + '.outputX', constraint[0] + '.w2', f=True)

    main_mouth_ctrl = cmds.curve(name='mainMouth_' + CTRL_SUFFIX,
                                 p=[[0.075, -0.075, -0.0], [0.226, -0.075, -0.0], [0.226, -0.151, -0.0],
                                    [0.377, 0.0, 0.0], [0.226, 0.151, 0.0], [0.226, 0.075, 0.0], [0.075, 0.075, 0.0],
                                    [0.075, 0.226, 0.0], [0.151, 0.226, 0.0], [0.0, 0.377, 0.0], [-0.151, 0.226, 0.0],
                                    [-0.075, 0.226, 0.0], [-0.075, 0.075, 0.0], [-0.226, 0.075, 0.0],
                                    [-0.226, 0.151, 0.0], [-0.377, 0.0, 0.0], [-0.226, -0.151, -0.0],
                                    [-0.226, -0.075, -0.0], [-0.075, -0.075, -0.0], [-0.075, -0.226, -0.0],
                                    [-0.151, -0.226, -0.0], [0.0, -0.377, -0.0], [0.151, -0.226, -0.0],
                                    [0.075, -0.226, -0.0], [0.075, -0.075, -0.0]], d=1)
    main_mouth_ctrl_grp = cmds.group(name=main_mouth_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    main_mouth_offset_grp = cmds.group(name=main_mouth_ctrl_grp.replace('ctrl', 'offset'), empty=True, world=True)
    cmds.parent(main_mouth_ctrl, main_mouth_offset_grp)
    cmds.parent(main_mouth_offset_grp, main_mouth_ctrl_grp)
    cmds.delete(cmds.pointConstraint(
        [_facial_joints_dict.get('mid_upper_lip_jnt'), _facial_joints_dict.get('mid_lower_lip_jnt')],
        main_mouth_ctrl_grp))
    cmds.move(mouth_scale * .8, main_mouth_ctrl_grp, moveX=True)
    cmds.parent(main_mouth_ctrl_grp, head_ctrl)
    cmds.parentConstraint(main_mouth_ctrl, jaw_ctrls_grp, mo=True)
    cmds.parentConstraint(main_mouth_ctrl, mouth_ctrls_grp, mo=True)
    change_viewport_color(main_mouth_ctrl, (1, .2, 1))

    # Create Mouth Corner Offset Controls
    left_offset_groups = []
    right_offset_groups = []
    for ctrl in _corner_ctrls:
        offset_grp = create_inbetween(ctrl, 'Corner')
        if 'left_' in ctrl:
            left_offset_groups.append(offset_grp)
        else:
            right_offset_groups.append(offset_grp)

    left_corner_ctrl = cmds.curve(p=[[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.784, -0.784, -0.0], [1.108, 0.0, -0.0],
                                     [0.784, 0.784, -0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0],
                                     [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.784, -0.784, -0.0]], d=3, per=True,
                                  k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                                  name='left_cornerLip_ctrl')

    right_corner_ctrl = cmds.curve(p=[[-0.0, 0.0, -0.0], [0.0, -0.0, -0.0], [-0.784, -0.784, 0.0], [-1.108, 0.0, 0.0],
                                      [-0.784, 0.784, 0.0], [-0.0, 0.0, 0.0], [-0.0, -0.0, 0.0], [0.0, 0.0, -0.0],
                                      [-0.0, 0.0, -0.0], [0.0, -0.0, -0.0], [-0.784, -0.784, 0.0]], d=3, per=True,
                                   k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                                   name='right_cornerLip_ctrl')
    rescale(left_corner_ctrl, mouth_scale*.2)
    rescale(right_corner_ctrl, mouth_scale*.2)
    change_viewport_color(left_corner_ctrl, LEFT_CTRL_COLOR)
    change_viewport_color(right_corner_ctrl, RIGHT_CTRL_COLOR)

    left_corner_ctrl_grp = cmds.group(name=left_corner_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    right_corner_ctrl_grp = cmds.group(name=right_corner_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)

    cmds.parent(left_corner_ctrl, left_corner_ctrl_grp)
    cmds.parent(right_corner_ctrl, right_corner_ctrl_grp)
    cmds.delete(cmds.parentConstraint(left_offset_groups, left_corner_ctrl_grp))
    cmds.delete(cmds.parentConstraint(right_offset_groups, right_corner_ctrl_grp))
    left_corner_offset_ctrl = create_inbetween(left_corner_ctrl, 'Driven')
    right_corner_offset_ctrl = create_inbetween(right_corner_ctrl, 'Driven')

    left_corner_sum_nodes = []
    for group in left_offset_groups:
        trans_sum_node = cmds.createNode('plusMinusAverage', name=group + '_trans_sum')
        rot_sum_node = cmds.createNode('plusMinusAverage', name=group + '_rot_sum')
        cmds.connectAttr(left_corner_ctrl + '.translate', trans_sum_node + '.input3D[0]', f=True)
        cmds.connectAttr(left_corner_ctrl + '.rotate', rot_sum_node + '.input3D[0]', f=True)
        cmds.connectAttr(trans_sum_node + '.output3D', group + '.translate', f=True)
        cmds.connectAttr(rot_sum_node + '.output3D', group + '.rotate', f=True)
        left_corner_sum_nodes.append([trans_sum_node, rot_sum_node])

    right_corner_sum_nodes = []
    for group in right_offset_groups:
        trans_sum_node = cmds.createNode('plusMinusAverage', name=group + '_trans_sum')
        rot_sum_node = cmds.createNode('plusMinusAverage', name=group + '_rot_sum')
        cmds.connectAttr(right_corner_ctrl + '.translate', trans_sum_node + '.input3D[0]', f=True)
        cmds.connectAttr(right_corner_ctrl + '.rotate', rot_sum_node + '.input3D[0]', f=True)
        cmds.connectAttr(trans_sum_node + '.output3D', group + '.translate', f=True)
        cmds.connectAttr(rot_sum_node + '.output3D', group + '.rotate', f=True)
        right_corner_sum_nodes.append([trans_sum_node, rot_sum_node])

    cmds.parent(left_corner_ctrl_grp, main_mouth_ctrl)
    cmds.parent(right_corner_ctrl_grp, main_mouth_ctrl)

    # ####################################### Eyebrows #######################################

    # Left Eyebrow Scale
    left_eyebrow_scale = 0
    left_eyebrow_scale += dist_center_to_center(_facial_joints_dict.get('left_inner_brow_jnt'),
                                                _facial_joints_dict.get('left_mid_brow_jnt'))
    left_eyebrow_scale += dist_center_to_center(_facial_joints_dict.get('left_mid_brow_jnt'),
                                                _facial_joints_dict.get('left_outer_brow_jnt'))

    cmds.select(clear=True)
    left_eyebrow_pivot_jnt = cmds.joint(name='left_eyebrow_pivot' + JNT_SUFFIX.capitalize(), radius=.5)
    temp_constraint = \
        cmds.pointConstraint([_facial_joints_dict.get('left_mid_brow_jnt'), _facial_joints_dict.get('head_jnt')],
                             left_eyebrow_pivot_jnt, skip=('x', 'z'))[0]
    cmds.setAttr(temp_constraint + ".w1", 0.2)
    cmds.delete(temp_constraint)
    temp_constraint = \
        cmds.pointConstraint([_facial_joints_dict.get('left_mid_brow_jnt'), _facial_joints_dict.get('head_jnt')],
                             left_eyebrow_pivot_jnt, skip=('x', 'y'))[0]
    cmds.setAttr(temp_constraint + ".w0", 0.3)
    cmds.delete(temp_constraint)
    cmds.parent(left_eyebrow_pivot_jnt, skeleton_grp)
    cmds.parentConstraint(_facial_joints_dict.get('head_jnt'), left_eyebrow_pivot_jnt, mo=True)

    # Create Controls
    left_eyebrow_driver_joints = []
    left_eyebrow_root_joints = []
    for jnt in [_facial_joints_dict.get('left_inner_brow_jnt'), _facial_joints_dict.get('left_mid_brow_jnt'),
                _facial_joints_dict.get('left_outer_brow_jnt')]:
        cmds.select(clear=True)
        new_joint = cmds.joint(name=jnt.replace(JNT_SUFFIX, 'root' + JNT_SUFFIX.capitalize()), radius=.5)

        cmds.delete(cmds.pointConstraint(left_eyebrow_pivot_jnt, new_joint))

        driver_jnt = cmds.duplicate(jnt, name=jnt.replace(JNT_SUFFIX, 'driver' + JNT_SUFFIX.capitalize()), po=True)[0]
        cmds.parent(driver_jnt, new_joint)
        cmds.joint(new_joint, e=True, oj='xyz', secondaryAxisOrient='yup', zso=True, ch=True)
        cmds.parent(new_joint, left_eyebrow_pivot_jnt)
        cmds.parentConstraint(driver_jnt, jnt)
        left_eyebrow_driver_joints.append(driver_jnt)
        left_eyebrow_root_joints.append(new_joint)

    eyebrow_controls = []
    for jnt in left_eyebrow_driver_joints:
        ctrl_objs = create_arched_control(jnt, ctrl_name=jnt.replace('driver' + JNT_SUFFIX.capitalize(), 'ctrl'),
                                          radius=left_eyebrow_scale * .05)
        eyebrow_controls.append(ctrl_objs)

    # Control Holder
    left_eyebrow_ctrls_grp = cmds.group(name='left_eyebrow_' + CTRL_SUFFIX + GRP_SUFFIX.capitalize(), empty=True,
                                        world=True)
    left_eyebrow_data_grp = cmds.group(name='left_eyebrow_data' + GRP_SUFFIX.capitalize(), empty=True, world=True)

    cmds.delete(cmds.parentConstraint(left_eyebrow_pivot_jnt, left_eyebrow_ctrls_grp))
    cmds.delete(cmds.parentConstraint(left_eyebrow_pivot_jnt, left_eyebrow_data_grp))

    cmds.parent(left_eyebrow_ctrls_grp, head_ctrl)
    cmds.parent(left_eyebrow_data_grp, head_ctrl)

    for ctrl_data in eyebrow_controls:
        # Unpack Data
        ctrl = ctrl_data[0]
        ctrl_grp = ctrl_data[1]
        trans_loc = ctrl_data[2]
        trans_loc_grp = ctrl_data[3]
        end_joint = ctrl_data[4]

        # # Organize Hierarchy
        cmds.parent(ctrl_grp, left_eyebrow_ctrls_grp)
        cmds.parent(trans_loc_grp, left_eyebrow_data_grp)

        # Adjust Controls
        cmds.setAttr(ctrl + '.movement', left_eyebrow_scale)
        cmds.setAttr(trans_loc + '.v', 0)

        # Find Skinned Joint
        skinned_jnt_parent_constraint = \
            cmds.listConnections(end_joint + '.translate', destination=True, type='parentConstraint')[0]
        skinned_jnt = cmds.listConnections(skinned_jnt_parent_constraint + '.constraintRotateX', type='joint')[0]
        pure_fk_constraint = cmds.parentConstraint(trans_loc, skinned_jnt, mo=True)

        # FK Override
        cmds.addAttr(ctrl, ln='fkOverride', at='double', k=True, maxValue=1, minValue=0, niceName='FK Override')
        cmds.setAttr(ctrl + '.fkOverride', 1)
        switch_reverse_node = cmds.createNode('reverse', name=ctrl.replace(CTRL_SUFFIX, 'reverseSwitch'))
        cmds.connectAttr(ctrl + '.fkOverride', switch_reverse_node + '.inputX', f=True)
        cmds.connectAttr(switch_reverse_node + '.outputX', pure_fk_constraint[0] + '.w0', f=True)
        cmds.connectAttr(ctrl + '.fkOverride', pure_fk_constraint[0] + '.w1', f=True)

        change_viewport_color(ctrl, LEFT_CTRL_COLOR)

    left_eyebrow_ctrl = cmds.curve(name='left_mainEyebrow_' + CTRL_SUFFIX,
                                   p=[[0.075, -0.075, -0.0], [0.226, -0.075, -0.0], [0.226, -0.151, -0.0],
                                      [0.377, 0.0, 0.0], [0.226, 0.151, 0.0], [0.226, 0.075, 0.0], [0.075, 0.075, 0.0],
                                      [0.075, 0.226, 0.0], [0.151, 0.226, 0.0], [0.0, 0.377, 0.0], [-0.151, 0.226, 0.0],
                                      [-0.075, 0.226, 0.0], [-0.075, 0.075, 0.0], [-0.226, 0.075, 0.0],
                                      [-0.226, 0.151, 0.0], [-0.377, 0.0, 0.0], [-0.226, -0.151, -0.0],
                                      [-0.226, -0.075, -0.0], [-0.075, -0.075, -0.0], [-0.075, -0.226, -0.0],
                                      [-0.151, -0.226, -0.0], [0.0, -0.377, -0.0], [0.151, -0.226, -0.0],
                                      [0.075, -0.226, -0.0], [0.075, -0.075, -0.0]], d=1)
    left_eyebrow_ctrl_grp = cmds.group(name=left_eyebrow_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(left_eyebrow_ctrl, left_eyebrow_ctrl_grp)
    cmds.delete(cmds.parentConstraint(
        [_facial_joints_dict.get('left_inner_brow_jnt'), _facial_joints_dict.get('left_outer_brow_jnt')],
        left_eyebrow_ctrl_grp))
    cmds.move(left_eyebrow_scale * .7, left_eyebrow_ctrl_grp, moveX=True, relative=True)
    cmds.parent(left_eyebrow_ctrl_grp, head_ctrl)
    cmds.parentConstraint(left_eyebrow_ctrl, left_eyebrow_ctrls_grp, mo=True)
    change_viewport_color(left_eyebrow_ctrl, (1, .2, 1))

    # Right Eyebrow Scale
    right_eyebrow_scale = 0
    right_eyebrow_scale += dist_center_to_center(_facial_joints_dict.get('right_inner_brow_jnt'),
                                                 _facial_joints_dict.get('right_mid_brow_jnt'))
    right_eyebrow_scale += dist_center_to_center(_facial_joints_dict.get('right_mid_brow_jnt'),
                                                 _facial_joints_dict.get('right_outer_brow_jnt'))

    cmds.select(clear=True)
    right_eyebrow_pivot_jnt = cmds.joint(name='right_eyebrow_pivot' + JNT_SUFFIX.capitalize(), radius=.5)
    temp_constraint = \
        cmds.pointConstraint([_facial_joints_dict.get('right_mid_brow_jnt'), _facial_joints_dict.get('head_jnt')],
                             right_eyebrow_pivot_jnt, skip=('x', 'z'))[0]
    cmds.setAttr(temp_constraint + ".w1", 0.2)
    cmds.delete(temp_constraint)
    temp_constraint = \
        cmds.pointConstraint([_facial_joints_dict.get('right_mid_brow_jnt'), _facial_joints_dict.get('head_jnt')],
                             right_eyebrow_pivot_jnt, skip=('x', 'y'))[0]
    cmds.setAttr(temp_constraint + ".w0", 0.3)
    cmds.delete(temp_constraint)
    cmds.parent(right_eyebrow_pivot_jnt, skeleton_grp)
    cmds.parentConstraint(_facial_joints_dict.get('head_jnt'), right_eyebrow_pivot_jnt, mo=True)

    # Create Controls
    right_eyebrow_driver_joints = []
    right_eyebrow_root_joints = []
    for jnt in [_facial_joints_dict.get('right_inner_brow_jnt'), _facial_joints_dict.get('right_mid_brow_jnt'),
                _facial_joints_dict.get('right_outer_brow_jnt')]:
        cmds.select(clear=True)
        new_joint = cmds.joint(name=jnt.replace(JNT_SUFFIX, 'root' + JNT_SUFFIX.capitalize()), radius=.5)

        cmds.delete(cmds.pointConstraint(right_eyebrow_pivot_jnt, new_joint))

        driver_jnt = cmds.duplicate(jnt, name=jnt.replace(JNT_SUFFIX, 'driver' + JNT_SUFFIX.capitalize()), po=True)[0]
        cmds.parent(driver_jnt, new_joint)
        cmds.joint(new_joint, e=True, oj='xyz', secondaryAxisOrient='yup', zso=True, ch=True)
        cmds.parent(new_joint, right_eyebrow_pivot_jnt)
        cmds.parentConstraint(driver_jnt, jnt)
        right_eyebrow_driver_joints.append(driver_jnt)
        right_eyebrow_root_joints.append(new_joint)

    eyebrow_controls = []
    for jnt in right_eyebrow_driver_joints:
        ctrl_objs = create_arched_control(jnt, ctrl_name=jnt.replace('driver' + JNT_SUFFIX.capitalize(), 'ctrl'),
                                          radius=right_eyebrow_scale * .05, create_offset_grp=True)
        eyebrow_controls.append(ctrl_objs)

    # Control Holder
    right_eyebrow_ctrls_grp = cmds.group(name='right_eyebrow_' + CTRL_SUFFIX + GRP_SUFFIX.capitalize(), empty=True,
                                         world=True)
    right_eyebrow_data_grp = cmds.group(name='right_eyebrow_data' + GRP_SUFFIX.capitalize(), empty=True, world=True)

    cmds.delete(cmds.parentConstraint(right_eyebrow_pivot_jnt, right_eyebrow_ctrls_grp))
    cmds.delete(cmds.parentConstraint(right_eyebrow_pivot_jnt, right_eyebrow_data_grp))

    cmds.parent(right_eyebrow_ctrls_grp, head_ctrl)
    cmds.parent(right_eyebrow_data_grp, head_ctrl)

    for ctrl_data in eyebrow_controls:
        # Unpack Data
        ctrl = ctrl_data[0]
        ctrl_grp = ctrl_data[1]
        trans_loc = ctrl_data[2]
        trans_loc_grp = ctrl_data[3]
        end_joint = ctrl_data[4]

        # # Organize Hierarchy
        cmds.parent(ctrl_grp, right_eyebrow_ctrls_grp)
        cmds.parent(trans_loc_grp, right_eyebrow_data_grp)

        # Adjust Controls
        cmds.setAttr(ctrl + '.movement', right_eyebrow_scale)
        cmds.setAttr(trans_loc + '.v', 0)

        # Find Skinned Joint
        skinned_jnt_parent_constraint = \
            cmds.listConnections(end_joint + '.translate', destination=True, type='parentConstraint')[0]
        skinned_jnt = cmds.listConnections(skinned_jnt_parent_constraint + '.constraintRotateX', type='joint')[0]
        pure_fk_constraint = cmds.parentConstraint(trans_loc, skinned_jnt, mo=True)

        # FK Override
        cmds.addAttr(ctrl, ln='fkOverride', at='double', k=True, maxValue=1, minValue=0, niceName='FK Override')
        cmds.setAttr(ctrl + '.fkOverride', 1)
        switch_reverse_node = cmds.createNode('reverse', name=ctrl.replace(CTRL_SUFFIX, 'reverseSwitch'))
        cmds.connectAttr(ctrl + '.fkOverride', switch_reverse_node + '.inputX', f=True)
        cmds.connectAttr(switch_reverse_node + '.outputX', pure_fk_constraint[0] + '.w0', f=True)
        cmds.connectAttr(ctrl + '.fkOverride', pure_fk_constraint[0] + '.w1', f=True)

        change_viewport_color(ctrl, RIGHT_CTRL_COLOR)

    right_eyebrow_ctrl = cmds.curve(name='right_mainEyebrow_' + CTRL_SUFFIX,
                                    p=[[0.075, -0.075, -0.0], [0.226, -0.075, -0.0], [0.226, -0.151, -0.0],
                                       [0.377, 0.0, 0.0], [0.226, 0.151, 0.0], [0.226, 0.075, 0.0], [0.075, 0.075, 0.0],
                                       [0.075, 0.226, 0.0], [0.151, 0.226, 0.0], [0.0, 0.377, 0.0],
                                       [-0.151, 0.226, 0.0], [-0.075, 0.226, 0.0], [-0.075, 0.075, 0.0],
                                       [-0.226, 0.075, 0.0], [-0.226, 0.151, 0.0], [-0.377, 0.0, 0.0],
                                       [-0.226, -0.151, -0.0], [-0.226, -0.075, -0.0], [-0.075, -0.075, -0.0],
                                       [-0.075, -0.226, -0.0], [-0.151, -0.226, -0.0], [0.0, -0.377, -0.0],
                                       [0.151, -0.226, -0.0], [0.075, -0.226, -0.0], [0.075, -0.075, -0.0]], d=1)
    right_eyebrow_ctrl_grp = cmds.group(name=right_eyebrow_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(right_eyebrow_ctrl, right_eyebrow_ctrl_grp)
    cmds.delete(cmds.parentConstraint(
        [_facial_joints_dict.get('right_inner_brow_jnt'), _facial_joints_dict.get('right_outer_brow_jnt')],
        right_eyebrow_ctrl_grp))
    cmds.move(right_eyebrow_scale * -.7, right_eyebrow_ctrl_grp, moveX=True, relative=True)
    cmds.parent(right_eyebrow_ctrl_grp, head_ctrl)
    cmds.parentConstraint(right_eyebrow_ctrl, right_eyebrow_ctrls_grp, mo=True)
    change_viewport_color(right_eyebrow_ctrl, (1, .2, 1))

    # Color Joints
    to_color = []
    for obj in _facial_joints_dict:
        to_color.append(_facial_joints_dict.get(obj))
    for obj in mouth_root_joints:
        to_color.append(obj)
    for obj in left_eyebrow_root_joints:
        to_color.append(obj)
    for obj in right_eyebrow_root_joints:
        to_color.append(obj)
    for jnt in to_color:
        if jnt not in ignore_crv_list:
            if 'left_' in jnt:
                change_viewport_color(jnt, LEFT_JNT_COLOR)
            elif 'right_' in jnt:
                change_viewport_color(jnt, RIGHT_JNT_COLOR)
            else:
                change_viewport_color(jnt, CENTER_JNT_COLOR)

    # ###### Side GUI ######
    general_head_scale = 0
    general_head_scale += dist_center_to_center(_facial_joints_dict.get('head_jnt'),
                                                _facial_joints_dict.get('mid_upper_lip_jnt'))

    facial_gui_grp = create_facial_controls()
    cmds.delete(cmds.pointConstraint(_facial_joints_dict.get('mid_upper_lip_jnt'), facial_gui_grp))
    cmds.parent(facial_gui_grp, head_ctrl)
    cmds.move(general_head_scale * 2, facial_gui_grp, moveX=True, relative=True)
    rescale(facial_gui_grp, general_head_scale * .02, freeze=False)
    mouth_offset_locators = []
    for ctrl_data in mouth_controls:
        ctrl_name = ctrl_data[0]
        ctrl_grp = ctrl_data[1]
        ctrl_offset = ctrl_data[5]
        ctrl_loc = cmds.spaceLocator(name=ctrl_name + 'OffsetLoc')[0]
        cmds.delete(cmds.parentConstraint(ctrl_name, ctrl_loc))
        cmds.parent(ctrl_loc, ctrl_grp)

        trans_multiply_node = cmds.createNode('multiplyDivide', name=ctrl_name + '_trans_multiply')
        rot_multiply_node = cmds.createNode('multiplyDivide', name=ctrl_name + '_rot_multiply')
        cmds.connectAttr(ctrl_loc + '.translate', trans_multiply_node + '.input1')
        cmds.connectAttr(ctrl_loc + '.rotate', rot_multiply_node + '.input1')
        cmds.connectAttr(trans_multiply_node + '.output', ctrl_offset.replace('Offset', 'Driven') + '.translate')
        cmds.connectAttr(rot_multiply_node + '.output', ctrl_offset.replace('Offset', 'Driven') + '.rotate')
        range_node = cmds.createNode('setRange', name=ctrl_name + '_range')

        cmds.connectAttr(ctrl_name.replace(CTRL_SUFFIX, 'offset_ctrl') + '.translateY', range_node + '.valueY')
        cmds.connectAttr(range_node + '.outValueY', trans_multiply_node + '.input2X')
        cmds.connectAttr(range_node + '.outValueY', trans_multiply_node + '.input2Y')
        cmds.connectAttr(range_node + '.outValueY', trans_multiply_node + '.input2Z')
        cmds.connectAttr(range_node + '.outValueY', rot_multiply_node + '.input2X')
        cmds.connectAttr(range_node + '.outValueY', rot_multiply_node + '.input2Y')
        cmds.connectAttr(range_node + '.outValueY', rot_multiply_node + '.input2Z')

        cmds.setAttr(range_node + '.oldMaxY', 5)
        cmds.setAttr(range_node + '.oldMinY', -5)

        if 'upper' in ctrl_name:
            cmds.setAttr(range_node + '.maxY', 1)
            cmds.setAttr(range_node + '.minY', -1)
            cmds.move(mouth_scale * 0.3, ctrl_loc, moveY=True, relative=True)
        elif 'lower' in ctrl_name:
            cmds.setAttr(range_node + '.maxY', -1)
            cmds.setAttr(range_node + '.minY', 1)
            cmds.move(mouth_scale * -0.3, ctrl_loc, moveY=True, relative=True)
        rescale(ctrl_loc, mouth_scale * 0.05, freeze=False)
        mouth_offset_locators.append(ctrl_loc)

    # Setup Other Controls
    jaw_offset_grp = create_inbetween(jaw_ctrl, 'Driven')

    # Control, [Offset Group, Type]
    _setup_offset_target = {main_mouth_ctrl: [main_mouth_offset_grp, '1d'],
                            jaw_ctrl: [jaw_offset_grp, '2d'],
                            left_corner_ctrl: [left_corner_offset_ctrl, '2d'],
                            right_corner_ctrl: [right_corner_offset_ctrl, '2d'],
                            }

    _offset_target_reposition = {}

    for ctrl_name, data in _setup_offset_target.items():
        ctrl_offset = data[0]
        ctrl_type = data[1]
        ctrl_grp = ctrl_name + GRP_SUFFIX.capitalize()
        ctrl_loc = cmds.spaceLocator(name=ctrl_name + 'OffsetLoc')[0]
        cmds.delete(cmds.parentConstraint(ctrl_name, ctrl_loc))
        cmds.parent(ctrl_loc, ctrl_grp)

        trans_multiply_node = cmds.createNode('multiplyDivide', name=ctrl_name + '_trans_multiply')
        rot_multiply_node = cmds.createNode('multiplyDivide', name=ctrl_name + '_rot_multiply')
        cmds.connectAttr(ctrl_loc + '.translate', trans_multiply_node + '.input1')
        cmds.connectAttr(ctrl_loc + '.rotate', rot_multiply_node + '.input1')
        cmds.connectAttr(trans_multiply_node + '.output', ctrl_offset.replace('Offset', 'Driven') + '.translate')
        cmds.connectAttr(rot_multiply_node + '.output', ctrl_offset.replace('Offset', 'Driven') + '.rotate')
        range_node = cmds.createNode('setRange', name=ctrl_name + '_range')

        cmds.connectAttr(ctrl_name.replace(CTRL_SUFFIX, 'offset_ctrl') + '.translateY', range_node + '.valueY')
        cmds.connectAttr(range_node + '.outValueY', trans_multiply_node + '.input2X')
        cmds.connectAttr(range_node + '.outValueY', trans_multiply_node + '.input2Y')
        cmds.connectAttr(range_node + '.outValueY', trans_multiply_node + '.input2Z')
        cmds.connectAttr(range_node + '.outValueY', rot_multiply_node + '.input2X')
        cmds.connectAttr(range_node + '.outValueY', rot_multiply_node + '.input2Y')
        cmds.connectAttr(range_node + '.outValueY', rot_multiply_node + '.input2Z')

        cmds.setAttr(range_node + '.oldMaxY', 5)
        cmds.setAttr(range_node + '.oldMinY', -5)
        cmds.setAttr(range_node + '.oldMaxX', 5)
        cmds.setAttr(range_node + '.oldMinX', -5)

        if ctrl_type == '2d':
            ctrl_loc = cmds.rename(ctrl_loc, ctrl_loc.replace('Offset', 'OffsetY'))
            trans_multiply_node = cmds.rename(trans_multiply_node, trans_multiply_node.replace('multiply', 'multiplyY'))
            rot_multiply_node = cmds.rename(rot_multiply_node, rot_multiply_node.replace('multiply', 'multiplyY'))
            ctrl_loc_x = cmds.spaceLocator(name=ctrl_name + 'OffsetXLoc')[0]
            trans_multiply_node_x = cmds.createNode('multiplyDivide', name=ctrl_name + 'trans_multiplyX')
            rot_multiply_node_x = cmds.createNode('multiplyDivide', name=ctrl_name + 'rot_multiplyX')
            cmds.connectAttr(ctrl_loc_x + '.translate', trans_multiply_node_x + '.input1')
            cmds.connectAttr(ctrl_loc_x + '.rotate', rot_multiply_node_x + '.input1')
            cmds.delete(cmds.parentConstraint(ctrl_name, ctrl_loc_x))
            cmds.parent(ctrl_loc_x, ctrl_grp)
            change_outliner_color(ctrl_loc_x, (1, .6, .6))
            change_outliner_color(ctrl_loc, (.6, 1, .6))
            rot_sum_node = cmds.createNode('plusMinusAverage', name=ctrl_name + '_rot_sum')
            trans_sum_node = cmds.createNode('plusMinusAverage', name=ctrl_name + '_trans_sum')
            cmds.connectAttr(trans_sum_node + '.output3D',
                             ctrl_offset.replace('Offset', 'Driven') + '.translate',
                             force=True)
            cmds.connectAttr(rot_sum_node + '.output3D',
                             ctrl_offset.replace('Offset', 'Driven') + '.rotate',
                             force=True)

            cmds.connectAttr(trans_multiply_node + '.output',
                             trans_sum_node + '.input3D[0]',
                             force=True)
            cmds.connectAttr(rot_multiply_node + '.output',
                             rot_sum_node + '.input3D[0]',
                             force=True)

            trans_multiply_node_x = cmds.createNode('multiplyDivide', name=ctrl_name + '_trans_multiply')
            rot_multiply_node_x = cmds.createNode('multiplyDivide', name=ctrl_name + '_rot_multiply')
            cmds.connectAttr(ctrl_loc_x + '.translate', trans_multiply_node_x + '.input1')
            cmds.connectAttr(ctrl_loc_x + '.rotate', rot_multiply_node_x + '.input1')
            cmds.connectAttr(trans_multiply_node_x + '.output', trans_sum_node + '.input3D[1]')
            cmds.connectAttr(rot_multiply_node_x + '.output', rot_sum_node + '.input3D[1]')

            cmds.connectAttr(ctrl_name.replace(CTRL_SUFFIX, 'offset_ctrl') + '.translateX', range_node + '.valueX')
            cmds.connectAttr(range_node + '.outValueX', trans_multiply_node_x + '.input2X')
            cmds.connectAttr(range_node + '.outValueX', trans_multiply_node_x + '.input2Y')
            cmds.connectAttr(range_node + '.outValueX', trans_multiply_node_x + '.input2Z')
            cmds.connectAttr(range_node + '.outValueX', rot_multiply_node_x + '.input2X')
            cmds.connectAttr(range_node + '.outValueX', rot_multiply_node_x + '.input2Y')
            cmds.connectAttr(range_node + '.outValueX', rot_multiply_node_x + '.input2Z')
            _offset_target_reposition[ctrl_loc_x] = mouth_scale * 0.3

            if ctrl_name == left_corner_ctrl:
                for sum_nodes in left_corner_sum_nodes:
                    trans_sum = sum_nodes[0]
                    rot_sum = sum_nodes[1]
                    cmds.connectAttr(trans_sum_node + '.output3D',
                                     trans_sum + '.input3D[1]',
                                     force=True)
                    cmds.connectAttr(rot_sum_node + '.output3D',
                                     rot_sum + '.input3D[1]',
                                     force=True)

            if ctrl_name == right_corner_ctrl:
                for sum_nodes in right_corner_sum_nodes:
                    trans_sum = sum_nodes[0]
                    rot_sum = sum_nodes[1]
                    cmds.connectAttr(trans_sum_node + '.output3D',
                                     trans_sum + '.input3D[1]',
                                     force=True)
                    cmds.connectAttr(rot_sum_node + '.output3D',
                                     rot_sum + '.input3D[1]',
                                     force=True)

        if 'lower' in ctrl_name:
            cmds.setAttr(range_node + '.maxY', -1)
            cmds.setAttr(range_node + '.minY', 1)
            cmds.setAttr(range_node + '.maxX', -1)
            cmds.setAttr(range_node + '.minX', 1)
            _offset_target_reposition[ctrl_loc] = mouth_scale * -0.3
        else:
            cmds.setAttr(range_node + '.maxY', 1)
            cmds.setAttr(range_node + '.minY', -1)
            cmds.setAttr(range_node + '.maxX', 1)
            cmds.setAttr(range_node + '.minX', -1)
            _offset_target_reposition[ctrl_loc] = mouth_scale * 0.3

    for ctrl_loc, float_value in _offset_target_reposition.items():
        if 'jaw_ctrlOffsetYLoc' in ctrl_loc:
            cmds.rotate(float_value * -15, ctrl_loc, rotateZ=True, relative=True)
        elif 'jaw_ctrlOffsetXLoc' in ctrl_loc:
            cmds.rotate(float_value * -15, ctrl_loc, rotateY=True, relative=True)
        elif '_cornerLip_ctrlOffsetXLoc' in ctrl_loc:
            cmds.move(float_value, ctrl_loc, moveX=True, relative=True)
        else:
            cmds.move(float_value, ctrl_loc, moveY=True, relative=True)
        rescale(ctrl_loc, mouth_scale * 0.05, freeze=False)

    # Delete Proxy
    if cmds.objExists(_facial_proxy_dict.get('main_proxy_grp')):
        cmds.delete(_facial_proxy_dict.get('main_proxy_grp'))

    # ###################################### Debugging #######################################
    if debugging:
        try:
            cmds.viewFit(head_ctrl)

            # Only if preexisting
            head_loc = cmds.spaceLocator(name='head_debuggingLoc')
            cmds.parentConstraint(_facial_joints_dict.get('head_jnt'), head_loc[0])
            cmds.parent(head_loc, _facial_joints_dict.get('head_jnt'))
            cmds.setAttr(_facial_joints_dict.get('head_jnt') + ".drawStyle", 2)

        except Exception as e:
            print(e)


if __name__ == '__main__':
    if debugging:
        import gt_maya_utilities
        gt_maya_utilities.gtu_reload_file()
        # cmds.file(new=True, force=True)
    create_face_proxy()
    create_face_controls()
