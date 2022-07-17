"""
 GT Facial Rigger
 github.com/TrevisanGMW/gt-tools -  2021-12-06

 0.0.1 - 2021-12-10
 Created Facial Controls

 0.0.2 - 2021-12-15
 Created Side GUI

 0.0.3 - 2021-12-20
 Created all side GUI connections

 0.0.4 - 2022-02-06
 Inverted orientation of the right side controls, so it's easy to mirror movements

 0.0.5 - 2022-02-07
 Create tongue joints, ctrls and side GUI connections

 0.0.6 - 2022-03-09
 Minor fixes to proxy generation
 Added fleshy eyes (eye rotation influence over eyelids)

 0.0.7 - 2022-03-17
 Added a bigger range to eye controls (so you can open them wide now)

 0.0.8 - 2022-03-22
 Fixed issue where the head_offset control wouldn't properly influence the facial controls

 0.0.9 - 2022-04-20
 Added limit to jaw closing movement

 0.0.10 - 2022-04-29
 Created pose system (replaced simple directional movement)
 Added cheek proxy

 0.0.11 - 2022-04-30
 Added cheek controls
 Added scale control to tongue

 0.0.12 - 2022-06-24
 Changed merge rig function to keep scale constraints at the bottom of the stack

 0.0.13 - 2022-07-01
 Fixed functionality of finding pre-existing joints
 Added attribute to store proxy as a string to the "head_ctrl" (Used to extract proxy from generated rig)

 0.0.14 - 2022-07-04
 Re-added cheek and nose controls
 Added visibility options to proxy controls

 0.0.15 - 2022-07-13
 Minor Adjustments to 'head_jnt' visibility

 0.0.16 to 17 - 2022-07-14
 Parented nose and cheek controls initially to the head for when creating without a biped base
 Added cheek and nose controls to head_ctrl visibility attribute

 TODO:
     Polish mouth up poses (rotation is unpredictable at the moment)
     Add main nose control
     Add nose and cheek automation to side GUI
     Improve tongue scale control system
     Look for existing biped proxy (not only joints) when creating facial proxy
"""
from collections import namedtuple
from gt_utilities import remove_strings_from_string
from gt_rigger_utilities import *
from gt_rigger_data import *
import maya.cmds as cmds
import random


def create_arched_control(end_joint,
                          ctrl_name='',
                          radius=0.5,
                          create_offset_grp=False,
                          invert_orientation=False,
                          suppress_scale=False):
    """
    Creates a control that arches according to its position. Helpful to follow the curvature of the head.
    Args:
        end_joint: Name of the end joint for the system (two joints are necessary, base and end)
        ctrl_name: Name of the control to be generated
        radius: Radius of the new control
        create_offset_grp: Whether to create an offset group between the control and its offset group
        invert_orientation: Inverts the orientation of the control (helpful for when creating the right side ctrl)
        suppress_scale: If active, scale attributes will not be created ("jointScale" vector)

    Returns: A tuple with ("ctrl", "ctrl_grp", "trans_loc", "trans_loc_grp", "end_joint", "offset_grp")

    """

    # Validate necessary elements
    end_joint_parent = cmds.listRelatives(end_joint, parent=True)[0] or []
    if not end_joint_parent:
        cmds.warning("Provided joint doesn't have a parent.")
        return

    # Calculate System Scale
    system_scale = dist_center_to_center(end_joint, str(end_joint_parent))

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

    offset_grp = ''
    if create_offset_grp:
        offset_grp = cmds.group(name=ctrl_name + 'OffsetGrp', world=True, empty=True)
        cmds.delete(cmds.parentConstraint(ctrl, offset_grp))
        cmds.parent(offset_grp, ctrl_grp)
        cmds.parent(ctrl, offset_grp)

    if invert_orientation:
        invert_grp = cmds.group(name=ctrl_name + '_invertOrient' + GRP_SUFFIX.capitalize(), world=True, empty=True)
        cmds.delete(cmds.parentConstraint(ctrl, invert_grp))
        ctrl_parent = cmds.listRelatives(ctrl, parent=True)[0]
        cmds.parent(ctrl, invert_grp)
        cmds.rotate(-180, invert_grp, rotateX=True)
        cmds.rotate(-180, ctrl, rotateX=True)
        for dimension in ['x', 'y', 'z']:
            cmds.setAttr(ctrl + '.s' + dimension, -1)
        cmds.makeIdentity(ctrl, rotate=True, scale=True, apply=True)
        cmds.parent(invert_grp, ctrl_parent)

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
    scale_attr = 'jointScale'
    if not suppress_scale:
        cmds.addAttr(ctrl, ln=scale_attr, at='double3', k=True)
        cmds.addAttr(ctrl, ln=scale_attr + 'X', at='double', k=True, parent=scale_attr, niceName='Scale Joint X')
        cmds.addAttr(ctrl, ln=scale_attr + 'Y', at='double', k=True, parent=scale_attr, niceName='Scale Joint Y')
        cmds.addAttr(ctrl, ln=scale_attr + 'Z', at='double', k=True, parent=scale_attr, niceName='Scale Joint Z')
        cmds.setAttr(ctrl + '.' + scale_attr + 'X', 1)
        cmds.setAttr(ctrl + '.' + scale_attr + 'Y', 1)
        cmds.setAttr(ctrl + '.' + scale_attr + 'Z', 1)
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
    base_rot_multiply_node = cmds.createNode('multiplyDivide', name=ctrl_name + '_baseRot_multiplyXY')
    cmds.connectAttr(trans_loc + '.tx', base_rot_multiply_node + '.input1X')
    cmds.connectAttr(trans_loc + '.ty', base_rot_multiply_node + '.input1Y')
    if invert_orientation:
        invert_multiply_node = cmds.createNode('multiplyDivide', name=ctrl_name + '_redirectInvertXY')
        cmds.connectAttr(base_rot_multiply_node + '.outputX', invert_multiply_node + '.input1Y')
        cmds.connectAttr(base_rot_multiply_node + '.outputY', invert_multiply_node + '.input1Z')
        cmds.setAttr(invert_multiply_node + '.input2Z', -1)
        cmds.connectAttr(invert_multiply_node + '.outputY', str(end_joint_parent) + '.ry')
        cmds.connectAttr(invert_multiply_node + '.outputZ', str(end_joint_parent) + '.rz')
    else:
        cmds.connectAttr(base_rot_multiply_node + '.outputX', str(end_joint_parent) + '.ry')
        cmds.connectAttr(base_rot_multiply_node + '.outputY', str(end_joint_parent) + '.rz')

    cmds.connectAttr(ctrl + '.movement', base_rot_multiply_node + '.input2X')
    cmds.connectAttr(ctrl + '.movement', base_rot_multiply_node + '.input2Y')
    #
    # Multiply Gradient (Arch)
    gradient_inverse_multiply_node = cmds.createNode('multiplyDivide', name=ctrl_name + '_influenceGradient_inverse')
    cmds.connectAttr(ctrl + '.gradient', gradient_inverse_multiply_node + '.input1X')
    cmds.setAttr(gradient_inverse_multiply_node + '.input2X', -.5)

    gradient_influence_multiply_node = cmds.createNode('multiplyDivide', name=ctrl_name + '_influenceGradient_multiply')
    cmds.connectAttr(trans_loc + '.tx', gradient_influence_multiply_node + '.input1X')
    cmds.connectAttr(gradient_inverse_multiply_node + '.outputX', gradient_influence_multiply_node + '.input2X')

    end_gradient_multiply_node = cmds.createNode('multiplyDivide', name=ctrl_name + '_endGradient_multiplyX')
    cmds.connectAttr(trans_loc + '.tx', end_gradient_multiply_node + '.input1X')
    cmds.connectAttr(gradient_influence_multiply_node + '.outputX', end_gradient_multiply_node + '.input2X')

    gradient_sum_node = cmds.createNode('plusMinusAverage', name=ctrl_name + '_gradient_sum')
    cmds.connectAttr(end_joint + '.tx', gradient_sum_node + '.input1D[0]')
    cmds.disconnectAttr(end_joint + '.tx', gradient_sum_node + '.input1D[0]')  # Keep data as offset
    cmds.connectAttr(end_gradient_multiply_node + '.outputX', gradient_sum_node + '.input1D[1]')
    cmds.connectAttr(gradient_sum_node + '.output1D', end_joint + '.tx')

    cmds.connectAttr(ctrl + '.extraOffset', gradient_sum_node + '.input1D[2]')

    z_offset_multiply_node = cmds.createNode('multiplyDivide', name=ctrl_name + '_zOffset_multiply')

    cmds.connectAttr(trans_loc + '.tz', z_offset_multiply_node + '.input1Z')
    cmds.connectAttr(ctrl + '.zOffsetInfluence', z_offset_multiply_node + '.input2Z')
    if invert_orientation:
        invert_multiply_node = cmds.createNode('multiplyDivide', name=ctrl_name + '_redirectInvertZ')
        cmds.connectAttr(ctrl + '.zOffsetInfluence', invert_multiply_node + '.input1Z')
        cmds.setAttr(invert_multiply_node + '.input2Z', -1)

    cmds.connectAttr(z_offset_multiply_node + '.outputZ', gradient_sum_node + '.input1D[3]')

    cmds.orientConstraint(trans_loc, end_joint, mo=True)

    return ctrl, ctrl_grp, trans_loc, trans_loc_grp, end_joint, offset_grp


def create_facial_proxy(facial_data):
    """
    Creates a proxy (guide) skeleton used to later generate entire rig

    Args:
        facial_data (GTBipedRiggerFacialData) : Object containing naming and settings for the proxy creation

    """

    proxy_curves = []

    # Unpack elements
    _facial_proxy_dict = facial_data.elements
    _preexisting_dict = facial_data.preexisting_dict
    _settings = facial_data.settings
    _settings = {'find_pre_existing_elements': True,
                 'setup_nose_cheek': False}  # @@@ TODO TEMP

    # Validate before creating
    if cmds.objExists(_facial_proxy_dict.get('main_proxy_grp')):
        cmds.warning('Proxy creation already in progress, please finish or delete it first.')
        return

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

    # Main Group Attribute Setup
    lock_hide_default_attr(main_grp, visibility=False)
    cmds.addAttr(main_grp, ln="proxyVisibility", at='enum', en='-------------:', keyable=True)
    cmds.setAttr(main_grp + '.proxyVisibility', e=True, lock=True)
    cmds.addAttr(main_grp, ln="browsVisibility", at='bool', keyable=True)
    cmds.setAttr(main_grp + ".browsVisibility", 1)
    cmds.addAttr(main_grp, ln="eyesVisibility", at='bool', keyable=True)
    cmds.setAttr(main_grp + ".eyesVisibility", 1)
    cmds.addAttr(main_grp, ln="eyelidsVisibility", at='bool', keyable=True)
    cmds.setAttr(main_grp + ".eyelidsVisibility", 1)
    cmds.addAttr(main_grp, ln="cheekNoseVisibility", at='bool', keyable=True, niceName='Cheek/Nose Visibility')
    cmds.setAttr(main_grp + ".cheekNoseVisibility", 1)
    cmds.addAttr(main_grp, ln="mouthVisibility", at='bool', keyable=True)
    cmds.setAttr(main_grp + ".mouthVisibility", 1)
    cmds.addAttr(main_grp, ln="tongueVisibility", at='bool', keyable=True)
    cmds.setAttr(main_grp + ".tongueVisibility", 1)

    # Head
    head_proxy_crv = create_joint_curve(_facial_proxy_dict.get('head_crv'), .55)
    head_proxy_grp = cmds.group(empty=True, world=True, name=head_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(head_proxy_crv, head_proxy_grp)
    cmds.move(0, 142.4, 0, head_proxy_grp)
    cmds.rotate(90, 0, 90, head_proxy_grp)
    cmds.parent(head_proxy_grp, main_root)
    change_viewport_color(head_proxy_crv, CENTER_PROXY_COLOR)
    proxy_curves.append(head_proxy_crv)

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
    proxy_curves.append(jaw_proxy_crv)

    # Left Eye
    left_eye_proxy_crv = create_joint_curve(_facial_proxy_dict.get('left_eye_crv'), .5)
    cmds.rotate(90, left_eye_proxy_crv, rotateX=True)
    cmds.makeIdentity(left_eye_proxy_crv, apply=True, rotate=True)
    left_eye_proxy_grp = cmds.group(empty=True, world=True, name=left_eye_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_eye_proxy_crv, left_eye_proxy_grp)
    cmds.move(3.5, 151.2, 8.7, left_eye_proxy_grp)
    cmds.parent(left_eye_proxy_grp, head_proxy_crv)
    change_viewport_color(left_eye_proxy_crv, LEFT_PROXY_COLOR)
    proxy_curves.append(left_eye_proxy_crv)

    # Left Upper Eyelid
    left_upper_eyelid_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('left_upper_eyelid_crv'), .1)
    cmds.rotate(90, left_upper_eyelid_proxy_crv, rotateX=True)
    cmds.makeIdentity(left_upper_eyelid_proxy_crv, apply=True, rotate=True)
    left_upper_eyelid_proxy_grp = cmds.group(empty=True, world=True,
                                             name=left_upper_eyelid_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_upper_eyelid_proxy_crv, left_upper_eyelid_proxy_grp)
    cmds.move(3.5, 152, 13, left_upper_eyelid_proxy_grp)
    cmds.parent(left_upper_eyelid_proxy_grp, left_eye_proxy_crv)
    change_viewport_color(left_upper_eyelid_proxy_crv, (0.4, 0.7, 1))
    proxy_curves.append(left_upper_eyelid_proxy_crv)

    # Left Lower Eyelid
    left_lower_eyelid_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('left_lower_eyelid_crv'), .1)
    cmds.rotate(90, left_lower_eyelid_proxy_crv, rotateX=True)
    cmds.makeIdentity(left_lower_eyelid_proxy_crv, apply=True, rotate=True)
    left_lower_eyelid_proxy_grp = cmds.group(empty=True, world=True,
                                             name=left_lower_eyelid_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_lower_eyelid_proxy_crv, left_lower_eyelid_proxy_grp)
    cmds.move(3.5, 150, 13, left_lower_eyelid_proxy_grp)
    cmds.parent(left_lower_eyelid_proxy_grp, left_eye_proxy_crv)
    change_viewport_color(left_lower_eyelid_proxy_crv, (0.4, 0.7, 1))
    proxy_curves.append(left_lower_eyelid_proxy_crv)

    # Right Eye
    right_eye_proxy_crv = create_joint_curve(_facial_proxy_dict.get('right_eye_crv'), .5)
    cmds.rotate(90, right_eye_proxy_crv, rotateX=True)
    cmds.makeIdentity(right_eye_proxy_crv, apply=True, rotate=True)
    right_eye_proxy_grp = cmds.group(empty=True, world=True, name=right_eye_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_eye_proxy_crv, right_eye_proxy_grp)
    cmds.move(-3.5, 151.2, 8.7, right_eye_proxy_grp)
    cmds.parent(right_eye_proxy_grp, head_proxy_crv)
    change_viewport_color(right_eye_proxy_crv, RIGHT_PROXY_COLOR)
    proxy_curves.append(right_eye_proxy_crv)

    # Right Upper Eyelid
    right_upper_eyelid_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('right_upper_eyelid_crv'), .1)
    cmds.rotate(90, right_upper_eyelid_proxy_crv, rotateX=True)
    cmds.makeIdentity(right_upper_eyelid_proxy_crv, apply=True, rotate=True)
    right_upper_eyelid_proxy_grp = cmds.group(empty=True, world=True,
                                              name=right_upper_eyelid_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_upper_eyelid_proxy_crv, right_upper_eyelid_proxy_grp)
    cmds.move(-3.5, 152, 13, right_upper_eyelid_proxy_grp)
    cmds.parent(right_upper_eyelid_proxy_grp, right_eye_proxy_crv)
    change_viewport_color(right_upper_eyelid_proxy_crv, (1, 0.7, 0.7))
    proxy_curves.append(right_upper_eyelid_proxy_crv)

    # Right Lower Eyelid
    right_lower_eyelid_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('right_lower_eyelid_crv'), .1)
    cmds.rotate(90, right_lower_eyelid_proxy_crv, rotateX=True)
    cmds.makeIdentity(right_lower_eyelid_proxy_crv, apply=True, rotate=True)
    right_lower_eyelid_proxy_grp = cmds.group(empty=True, world=True,
                                              name=right_lower_eyelid_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_lower_eyelid_proxy_crv, right_lower_eyelid_proxy_grp)
    cmds.move(-3.5, 150, 13, right_lower_eyelid_proxy_grp)
    cmds.parent(right_lower_eyelid_proxy_grp, right_eye_proxy_crv)
    change_viewport_color(right_lower_eyelid_proxy_crv, (1, 0.7, 0.7))
    proxy_curves.append(right_lower_eyelid_proxy_crv)

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
    proxy_curves.append(left_inner_brow_proxy_crv)

    left_mid_brow_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('left_mid_brow_crv'), .2)
    cmds.rotate(90, left_mid_brow_proxy_crv, rotateX=True)
    cmds.makeIdentity(left_mid_brow_proxy_crv, apply=True, rotate=True)
    left_mid_brow_proxy_grp = cmds.group(empty=True, world=True, name=left_mid_brow_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_mid_brow_proxy_crv, left_mid_brow_proxy_grp)
    cmds.move(3.5, 154.2, 13, left_mid_brow_proxy_grp)
    cmds.parent(left_mid_brow_proxy_grp, left_eye_proxy_crv)
    change_viewport_color(left_mid_brow_proxy_crv, LEFT_PROXY_COLOR)
    proxy_curves.append(left_mid_brow_proxy_crv)

    left_outer_brow_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('left_outer_brow_crv'), .2)
    cmds.rotate(90, left_outer_brow_proxy_crv, rotateX=True)
    cmds.makeIdentity(left_outer_brow_proxy_crv, apply=True, rotate=True)
    left_outer_brow_proxy_grp = cmds.group(empty=True, world=True,
                                           name=left_outer_brow_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_outer_brow_proxy_crv, left_outer_brow_proxy_grp)
    cmds.move(5.8, 153.2, 13, left_outer_brow_proxy_grp)
    cmds.parent(left_outer_brow_proxy_grp, left_eye_proxy_crv)
    change_viewport_color(left_outer_brow_proxy_crv, LEFT_PROXY_COLOR)
    proxy_curves.append(left_outer_brow_proxy_crv)

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
    proxy_curves.append(right_inner_brow_proxy_crv)

    right_mid_brow_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('right_mid_brow_crv'), .2)
    cmds.rotate(90, right_mid_brow_proxy_crv, rotateX=True)
    cmds.makeIdentity(right_mid_brow_proxy_crv, apply=True, rotate=True)
    right_mid_brow_proxy_grp = cmds.group(empty=True, world=True,
                                          name=right_mid_brow_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_mid_brow_proxy_crv, right_mid_brow_proxy_grp)
    cmds.move(-3.5, 154.2, 13, right_mid_brow_proxy_grp)
    cmds.parent(right_mid_brow_proxy_grp, right_eye_proxy_crv)
    change_viewport_color(right_mid_brow_proxy_crv, RIGHT_PROXY_COLOR)
    proxy_curves.append(right_mid_brow_proxy_crv)

    right_outer_brow_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('right_outer_brow_crv'), .2)
    cmds.rotate(90, right_outer_brow_proxy_crv, rotateX=True)
    cmds.makeIdentity(right_outer_brow_proxy_crv, apply=True, rotate=True)
    right_outer_brow_proxy_grp = cmds.group(empty=True, world=True,
                                            name=right_outer_brow_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_outer_brow_proxy_crv, right_outer_brow_proxy_grp)
    cmds.move(-5.8, 153.2, 13, right_outer_brow_proxy_grp)
    cmds.parent(right_outer_brow_proxy_grp, right_eye_proxy_crv)
    change_viewport_color(right_outer_brow_proxy_crv, RIGHT_PROXY_COLOR)
    proxy_curves.append(right_outer_brow_proxy_crv)

    # ################ Mouth ################
    # MID
    mid_upper_lip_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('mid_upper_lip_crv'), .1)
    cmds.rotate(90, mid_upper_lip_proxy_crv, rotateX=True)
    cmds.makeIdentity(mid_upper_lip_proxy_crv, apply=True, rotate=True)
    mid_upper_lip_proxy_grp = cmds.group(empty=True, world=True, name=mid_upper_lip_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(mid_upper_lip_proxy_crv, mid_upper_lip_proxy_grp)
    cmds.move(0.0, 144.8, 13.3, mid_upper_lip_proxy_grp)
    cmds.parent(mid_upper_lip_proxy_grp, main_root)
    change_viewport_color(mid_upper_lip_proxy_crv, CENTER_PROXY_COLOR)
    proxy_curves.append(mid_upper_lip_proxy_crv)

    mid_lower_lip_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('mid_lower_lip_crv'), .1)
    cmds.rotate(90, mid_lower_lip_proxy_crv, rotateX=True)
    cmds.makeIdentity(mid_lower_lip_proxy_crv, apply=True, rotate=True)
    mid_lower_lip_proxy_grp = cmds.group(empty=True, world=True, name=mid_lower_lip_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(mid_lower_lip_proxy_crv, mid_lower_lip_proxy_grp)
    cmds.move(0.0, 143.8, 13.3, mid_lower_lip_proxy_grp)
    cmds.parent(mid_lower_lip_proxy_grp, main_root)
    change_viewport_color(mid_lower_lip_proxy_crv, CENTER_PROXY_COLOR)
    proxy_curves.append(mid_lower_lip_proxy_crv)

    # Left Outer
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
    proxy_curves.append(left_upper_lip_proxy_crv)

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
    proxy_curves.append(left_lower_lip_proxy_crv)

    # Left Corner
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
    proxy_curves.append(left_corner_lip_proxy_crv)

    # Auto Orient Outer Controls
    left_outer_rot_multiply_node = cmds.createNode('multiplyDivide', name='left_upperOuter_autoRot_multiply')
    cmds.connectAttr(left_corner_lip_proxy_crv + '.ry', left_outer_rot_multiply_node + '.input1Y')
    cmds.connectAttr(left_outer_rot_multiply_node + '.outputY', left_upper_lip_proxy_offset_grp + '.ry')
    cmds.connectAttr(left_outer_rot_multiply_node + '.outputY', left_lower_lip_proxy_offset_grp + '.ry')
    cmds.setAttr(left_outer_rot_multiply_node + '.input2Y', 0.5)

    # Right Outer
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
    proxy_curves.append(right_upper_lip_proxy_crv)

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
    proxy_curves.append(right_lower_lip_proxy_crv)

    # Right Corner
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
    proxy_curves.append(right_corner_lip_proxy_crv)

    # Base Tongue
    base_tongue_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('base_tongue_crv'), .06)
    cmds.makeIdentity(base_tongue_proxy_crv, apply=True, rotate=True)
    base_tongue_proxy_grp = cmds.group(empty=True, world=True, name=base_tongue_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(base_tongue_proxy_crv, base_tongue_proxy_grp)
    cmds.move(0.0, 143.8, 7, base_tongue_proxy_grp)
    cmds.parent(base_tongue_proxy_grp, main_root)
    change_viewport_color(base_tongue_proxy_crv, (.6, .3, .6))
    proxy_curves.append(base_tongue_proxy_crv)

    # Tip Tongue
    tongue_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('mid_tongue_crv'), .06)
    cmds.makeIdentity(tongue_proxy_crv, apply=True, rotate=True)
    tongue_proxy_grp = cmds.group(empty=True, world=True, name=tongue_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(tongue_proxy_crv, tongue_proxy_grp)
    cmds.move(0.0, 143.8, 8.5, tongue_proxy_grp)
    cmds.parent(tongue_proxy_grp, base_tongue_proxy_crv)
    change_viewport_color(tongue_proxy_crv, (.6, .3, .6))
    proxy_curves.append(tongue_proxy_crv)

    # End Tongue
    tip_tongue_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('tip_tongue_crv'), .03)
    cmds.makeIdentity(tip_tongue_proxy_crv, apply=True, rotate=True)
    tip_tongue_proxy_grp = cmds.group(empty=True, world=True, name=tip_tongue_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(tip_tongue_proxy_crv, tip_tongue_proxy_grp)
    cmds.move(0.0, 143.8, 10, tip_tongue_proxy_grp)
    cmds.parent(tip_tongue_proxy_grp, tongue_proxy_crv)
    change_viewport_color(tip_tongue_proxy_crv, (.7, .3, .7))
    proxy_curves.append(tip_tongue_proxy_crv)

    # Left Cheeks
    left_cheek_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('left_cheek_crv'), .06)
    cmds.makeIdentity(left_cheek_proxy_crv, apply=True, rotate=True)
    left_cheek_proxy_crv_grp = cmds.group(empty=True, world=True, name=left_cheek_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_cheek_proxy_crv, left_cheek_proxy_crv_grp)
    cmds.move(4, 148, 12, left_cheek_proxy_crv_grp)
    cmds.rotate(45, 0, -90, left_cheek_proxy_crv_grp)
    cmds.parent(left_cheek_proxy_crv_grp, main_root)
    change_viewport_color(left_cheek_proxy_crv, (.6, .3, .6))
    proxy_curves.append(left_cheek_proxy_crv)

    # Right Cheeks
    right_cheek_proxy_crv = create_directional_joint_curve(_facial_proxy_dict.get('right_cheek_crv'), .06)
    cmds.makeIdentity(right_cheek_proxy_crv, apply=True, rotate=True)
    right_cheek_proxy_crv_grp = cmds.group(empty=True, world=True, name=right_cheek_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_cheek_proxy_crv, right_cheek_proxy_crv_grp)
    cmds.move(-4, 148, 12, right_cheek_proxy_crv_grp)
    cmds.rotate(135, 0, -90, right_cheek_proxy_crv_grp)
    cmds.parent(right_cheek_proxy_crv_grp, main_root)
    change_viewport_color(right_cheek_proxy_crv, (.6, .3, .6))
    proxy_curves.append(right_cheek_proxy_crv)

    # Left Nose
    left_nose_proxy_crv = create_joint_curve(_facial_proxy_dict.get('left_nose_crv'), .06)
    cmds.makeIdentity(left_nose_proxy_crv, apply=True, rotate=True)
    left_nose_proxy_crv_grp = cmds.group(empty=True, world=True, name=left_nose_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_nose_proxy_crv, left_nose_proxy_crv_grp)
    cmds.move(1.2, 149.1, 12.5, left_nose_proxy_crv_grp)
    cmds.parent(left_nose_proxy_crv_grp, main_root)
    change_viewport_color(left_nose_proxy_crv, (.6, .3, .6))
    proxy_curves.append(left_nose_proxy_crv)

    # Right Nose
    right_nose_proxy_crv = create_joint_curve(_facial_proxy_dict.get('right_nose_crv'), .06)
    cmds.makeIdentity(right_nose_proxy_crv, apply=True, rotate=True)
    right_nose_proxy_crv_grp = cmds.group(empty=True, world=True, name=right_nose_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_nose_proxy_crv, right_nose_proxy_crv_grp)
    cmds.move(-1.2, 149.1, 12.5, right_nose_proxy_crv_grp)
    cmds.parent(right_nose_proxy_crv_grp, main_root)
    change_viewport_color(right_nose_proxy_crv, (.6, .3, .6))
    proxy_curves.append(right_nose_proxy_crv)

    # Auto Orient Outer Controls
    right_outer_rot_multiply_node = cmds.createNode('multiplyDivide', name='right_upperOuter_autoRot_multiply')
    cmds.connectAttr(right_corner_lip_proxy_crv + '.ry', right_outer_rot_multiply_node + '.input1Y')
    cmds.connectAttr(right_outer_rot_multiply_node + '.outputY', right_upper_lip_proxy_offset_grp + '.ry')
    cmds.connectAttr(right_outer_rot_multiply_node + '.outputY', right_lower_lip_proxy_offset_grp + '.ry')
    cmds.setAttr(right_outer_rot_multiply_node + '.input2Y', 0.5)

    ################

    # Find Pre-existing Elements
    if facial_data.settings.get('find_pre_existing_elements'):
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
                    right_inner_brow_proxy_grp,
                    right_mid_brow_proxy_grp,
                    right_outer_brow_proxy_grp,
                    jaw_proxy_grp,
                    left_eye_proxy_grp,
                    right_eye_proxy_grp,
                    left_upper_eyelid_proxy_grp,
                    right_upper_eyelid_proxy_grp,
                    left_lower_eyelid_proxy_grp,
                    right_lower_eyelid_proxy_grp,
                    ]
    for obj in to_re_parent:
        cmds.parent(obj, main_root)

    to_follow_eyes = [left_inner_brow_proxy_grp,
                      left_mid_brow_proxy_grp,
                      left_outer_brow_proxy_grp,
                      right_inner_brow_proxy_grp,
                      right_mid_brow_proxy_grp,
                      right_outer_brow_proxy_grp,
                      left_upper_eyelid_proxy_grp,
                      right_upper_eyelid_proxy_grp,
                      left_lower_eyelid_proxy_grp,
                      right_lower_eyelid_proxy_grp,
                      ]

    for obj in to_follow_eyes:
        ctrl = cmds.listRelatives(obj, children=True)[0]
        if obj.startswith('right'):
            constraint = cmds.parentConstraint(right_eye_proxy_crv, obj, mo=True)[0]
        else:
            constraint = cmds.parentConstraint(left_eye_proxy_crv, obj, mo=True)[0]
        cmds.addAttr(ctrl, ln='controlBehaviour', at='enum', en='-------------:', keyable=True)
        cmds.setAttr(ctrl + '.' + 'controlBehaviour', lock=True)
        cmds.addAttr(ctrl, ln='followEye', at='bool', keyable=True)
        cmds.setAttr(ctrl + '.followEye', 1)
        cmds.connectAttr(ctrl + '.followEye', constraint + '.w0')

    # Mouth Main Control
    main_mouth_proxy_crv = cmds.curve(name="main_mouth_proxy_crv", p=[[1.5, 0.0, 1.5], [0.0, 0.0, 3.0],
                                                                      [-1.5, 0.0, 1.5], [-0.9, 0.0, 1.5],
                                                                      [0.0, 0.0, 2.4], [0.9, 0.0, 1.5],
                                                                      [1.5, 0.0, 1.5]], d=1)
    change_viewport_color(main_mouth_proxy_crv, (1, 0, 1))
    main_mouth_proxy_grp = cmds.group(name=main_mouth_proxy_crv + GRP_SUFFIX.capitalize(), empty=True, world=True)
    proxy_curves.append(main_mouth_proxy_crv)
    cmds.parent(main_mouth_proxy_crv, main_mouth_proxy_grp)
    cmds.delete(cmds.pointConstraint([mid_upper_lip_proxy_crv, mid_lower_lip_proxy_crv], main_mouth_proxy_grp))
    cmds.parent(main_mouth_proxy_grp, main_root)
    # cmds.parent(base_tongue_proxy_grp, main_mouth_proxy_crv)
    cmds.parent(mid_upper_lip_proxy_grp, main_mouth_proxy_crv)
    cmds.parent(mid_lower_lip_proxy_grp, main_mouth_proxy_crv)
    cmds.parent(right_upper_lip_proxy_grp, main_mouth_proxy_crv)
    cmds.parent(right_lower_lip_proxy_grp, main_mouth_proxy_crv)
    cmds.parent(right_upper_corner_lip_proxy_grp, main_mouth_proxy_crv)
    cmds.parent(left_upper_lip_proxy_grp, main_mouth_proxy_crv)
    cmds.parent(left_lower_lip_proxy_grp, main_mouth_proxy_crv)
    cmds.parent(left_upper_corner_lip_proxy_grp, main_mouth_proxy_crv)

    # Clean Unnecessary Channels
    lock_hide_default_attr(main_root, translate=False, rotate=False)
    for crv in proxy_curves:
        lock_hide_default_attr(crv, translate=False, rotate=False)

    # Setup Visibility
    cmds.connectAttr(main_grp + '.browsVisibility', left_inner_brow_proxy_grp + '.v')
    cmds.connectAttr(main_grp + '.browsVisibility', left_mid_brow_proxy_grp + '.v')
    cmds.connectAttr(main_grp + '.browsVisibility', left_outer_brow_proxy_grp + '.v')
    cmds.connectAttr(main_grp + '.browsVisibility', right_inner_brow_proxy_grp + '.v')
    cmds.connectAttr(main_grp + '.browsVisibility', right_mid_brow_proxy_grp + '.v')
    cmds.connectAttr(main_grp + '.browsVisibility', right_outer_brow_proxy_grp + '.v')
    cmds.connectAttr(main_grp + '.eyesVisibility', left_eye_proxy_grp + '.v')
    cmds.connectAttr(main_grp + '.eyesVisibility', right_eye_proxy_grp + '.v')
    cmds.connectAttr(main_grp + '.eyelidsVisibility', left_lower_eyelid_proxy_grp + '.v')
    cmds.connectAttr(main_grp + '.eyelidsVisibility', left_upper_eyelid_proxy_grp + '.v')
    cmds.connectAttr(main_grp + '.eyelidsVisibility', right_lower_eyelid_proxy_grp + '.v')
    cmds.connectAttr(main_grp + '.eyelidsVisibility', right_upper_eyelid_proxy_grp + '.v')
    cmds.connectAttr(main_grp + '.cheekNoseVisibility', left_cheek_proxy_crv_grp + '.v')
    cmds.connectAttr(main_grp + '.cheekNoseVisibility', right_cheek_proxy_crv_grp + '.v')
    cmds.connectAttr(main_grp + '.cheekNoseVisibility', left_nose_proxy_crv_grp + '.v')
    cmds.connectAttr(main_grp + '.cheekNoseVisibility', right_nose_proxy_crv_grp + '.v')
    cmds.connectAttr(main_grp + '.mouthVisibility', main_mouth_proxy_grp + '.v')
    cmds.connectAttr(main_grp + '.tongueVisibility', base_tongue_proxy_grp + '.v')
    # if not _settings.get("setup_nose_cheek"):
    #     cmds.setAttr(main_grp + ".wristsVisibility", 0)

    # Clean Selection
    cmds.select(d=True)


def create_facial_controls(facial_data):
    """ Creates Facial Rig Controls

    Args:
        facial_data (GTBipedRiggerFacialData) : Object containing naming and settings for the proxy creation

    """

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

    # Unpack elements
    _settings = facial_data.settings
    _facial_proxy_dict = facial_data.elements
    _preexisting_dict = facial_data.preexisting_dict

    # Create Parent Groups
    face_prefix = 'facial_'

    rig_grp = cmds.group(name=face_prefix + 'rig_grp', empty=True, world=True)
    change_outliner_color(rig_grp, (1, .45, .7))

    skeleton_grp = cmds.group(name=(face_prefix + 'skeleton_' + GRP_SUFFIX), empty=True, world=True)
    change_outliner_color(skeleton_grp, (.75, .45, .95))  # Purple (Like a joint)

    controls_grp = cmds.group(name=face_prefix + 'controls_' + GRP_SUFFIX, empty=True, world=True)
    change_outliner_color(controls_grp, (1, 0.47, 0.18))

    rig_setup_grp = cmds.group(name=face_prefix + 'rig_setup_' + GRP_SUFFIX, empty=True, world=True)
    cmds.setAttr(rig_setup_grp + '.v', 0)
    change_outliner_color(rig_setup_grp, (1, .26, .26))

    general_automation_grp = cmds.group(name='facialAutomation_grp', world=True, empty=True)
    change_outliner_color(general_automation_grp, (1, .65, .45))

    mouth_automation_grp = cmds.group(name='mouthAutomation_grp', world=True, empty=True)
    change_outliner_color(mouth_automation_grp, (1, .65, .45))

    cmds.parent(skeleton_grp, rig_grp)
    cmds.parent(controls_grp, rig_grp)
    cmds.parent(rig_setup_grp, rig_grp)
    cmds.parent(general_automation_grp, rig_setup_grp)
    cmds.parent(mouth_automation_grp, rig_setup_grp)

    # # Mouth Scale
    mouth_scale = 0
    mouth_scale += dist_center_to_center(_facial_proxy_dict.get('left_corner_lip_crv'),
                                         _facial_proxy_dict.get('mid_upper_lip_crv'))
    mouth_scale += dist_center_to_center(_facial_proxy_dict.get('mid_upper_lip_crv'),
                                         _facial_proxy_dict.get('right_corner_lip_crv'))

    # ###################################### Create Joints #######################################
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

    # Re-parent Generated Eyes
    generated_eyes = [_facial_proxy_dict.get('left_eye_crv'), _facial_proxy_dict.get('right_eye_crv')]
    for eye in generated_eyes:
        generated_eye = eye.replace(PROXY_SUFFIX, JNT_SUFFIX)
        if cmds.objExists(generated_eye):
            cmds.parent(generated_eye, _facial_joints_dict.get('head_jnt'))
            cmds.setAttr(generated_eye + '.radius', mouth_scale * .3)

    # If jaw joint wasn't found, orient the created one
    jaw_ctrl = 'jaw_ctrl'
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
            cmds.rename(shape, '{0}Shape'.format(jaw_ctrl))
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
            cmds.rename(shape, '{0}Shape'.format(head_ctrl))

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

    # ####### Special Joint Cases ########
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

                      _facial_joints_dict.get('left_cheek_jnt'),
                      _facial_joints_dict.get('right_cheek_jnt'),
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
        new_base_jnt = cmds.joint(name=jnt.replace(JNT_SUFFIX, 'root' + JNT_SUFFIX.capitalize()), radius=.5)
        # Use different pivot?
        # cmds.delete(cmds.pointConstraint([jnt, _facial_joints_dict.get('jaw_jnt')], new_joint, skip=('x')))
        # cmds.delete(cmds.pointConstraint(jnt, new_joint, skip=('x', 'z')))
        cmds.delete(cmds.pointConstraint(_facial_joints_dict.get('jaw_jnt'), new_base_jnt))
        driver_jnt = cmds.duplicate(jnt, name=jnt.replace(JNT_SUFFIX, 'driver' + JNT_SUFFIX.capitalize()), po=True)[0]
        cmds.parent(driver_jnt, new_base_jnt)
        cmds.joint(new_base_jnt, e=True, oj='xyz', secondaryAxisOrient='yup', zso=True, ch=True)
        cmds.parent(new_base_jnt, mouth_pivot_jnt)
        cmds.parentConstraint(driver_jnt, jnt)
        mouth_driver_joints.append(driver_jnt)
        mouth_root_joints.append(new_base_jnt)

    # ####################################### Mouth #######################################

    mouth_controls = []
    for jnt in mouth_driver_joints:
        ctrl_name = jnt.replace('driver' + JNT_SUFFIX.capitalize(), CTRL_SUFFIX)
        if 'right' in jnt:
            ctrl_objs = create_arched_control(jnt, ctrl_name=ctrl_name, radius=mouth_scale * .05,
                                              create_offset_grp=True, invert_orientation=True)
        else:
            ctrl_objs = create_arched_control(jnt, ctrl_name=ctrl_name, radius=mouth_scale * .05,
                                              create_offset_grp=True)
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
    _right_ctrls = []

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

        # Connect Scale
        cmds.connectAttr(ctrl + '.jointScale', skinned_jnt + '.scale')

        # FK Override
        cmds.addAttr(ctrl, ln='fkOverride', at='double', k=True, maxValue=1, minValue=0, niceName='FK Override')
        switch_reverse_node = cmds.createNode('reverse', name=ctrl.replace(CTRL_SUFFIX, 'reverseSwitch'))
        cmds.connectAttr(ctrl + '.fkOverride', switch_reverse_node + '.inputX', f=True)
        cmds.connectAttr(switch_reverse_node + '.outputX', pure_fk_constraint[0] + '.w0', f=True)
        cmds.connectAttr(ctrl + '.fkOverride', pure_fk_constraint[0] + '.w1', f=True)

        if 'lower' in ctrl and 'Corner' not in ctrl:
            cmds.setAttr(ctrl + '.fkOverride', 1)

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

        # Color Controls (And invert right side scales)
        if 'left_' in ctrl:
            change_viewport_color(ctrl, LEFT_CTRL_COLOR)
        elif 'right_' in ctrl:
            change_viewport_color(ctrl, RIGHT_CTRL_COLOR)
            _right_ctrls.append(ctrl)
        else:
            change_viewport_color(ctrl, CENTER_CTRL_COLOR)

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

    right_corner_ctrl = cmds.curve(p=[[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.784, -0.784, -0.0], [1.108, 0.0, -0.0],
                                      [0.784, 0.784, -0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0],
                                      [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.784, -0.784, -0.0]], d=3, per=True,
                                   k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                                   name='right_cornerLip_ctrl')

    rescale(left_corner_ctrl, mouth_scale * .2)
    rescale(right_corner_ctrl, mouth_scale * .2)

    change_viewport_color(left_corner_ctrl, LEFT_CTRL_COLOR)
    change_viewport_color(right_corner_ctrl, RIGHT_CTRL_COLOR)

    left_corner_ctrl_grp = cmds.group(name=left_corner_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    right_corner_ctrl_grp = cmds.group(name=right_corner_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)

    cmds.parent(left_corner_ctrl, left_corner_ctrl_grp)
    cmds.parent(right_corner_ctrl, right_corner_ctrl_grp)
    cmds.delete(cmds.parentConstraint(left_offset_groups, left_corner_ctrl_grp))
    cmds.delete(cmds.parentConstraint(right_offset_groups, right_corner_ctrl_grp))
    create_inbetween(left_corner_ctrl, 'Driven')
    create_inbetween(right_corner_ctrl, 'Driven')

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

    # Reinforce right mouth corner Inverted Rotation
    if cmds.getAttr(right_corner_ctrl_grp + '.rx') == 0:
        cmds.setAttr(right_corner_ctrl_grp + '.rx', 180)

    # Post Mouth Adjustments
    for r_ctrl in _right_ctrls:
        cmds.setAttr(r_ctrl + '.sx', -1)
        cmds.setAttr(r_ctrl + '.sy', -1)
        cmds.setAttr(r_ctrl + '.sz', -1)

    # Create Mid-Corner Constraint
    for ctrl in _mouth_outer_automation_elements:
        abc_joints = _mouth_outer_automation_elements.get(ctrl)
        constraint = cmds.parentConstraint([abc_joints[0], abc_joints[2], mouth_automation_grp], abc_joints[1],
                                           mo=True)
        cmds.setAttr(constraint[0] + '.interpType', 2)
        cmds.addAttr(ctrl, ln='midCornerInfluence', at='double', k=True, maxValue=1, minValue=0)
        cmds.setAttr(ctrl + '.midCornerInfluence', 1)
        switch_reverse_node = cmds.createNode('reverse', name=ctrl.replace(CTRL_SUFFIX, 'reverseSwitch'))
        cmds.connectAttr(ctrl + '.midCornerInfluence', switch_reverse_node + '.inputX', f=True)

        cmds.connectAttr(ctrl + '.midCornerInfluence', constraint[0] + '.w0', f=True)
        cmds.connectAttr(ctrl + '.midCornerInfluence', constraint[0] + '.w1', f=True)
        cmds.connectAttr(switch_reverse_node + '.outputX', constraint[0] + '.w2', f=True)

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
        new_base_jnt = cmds.joint(name=jnt.replace(JNT_SUFFIX, 'root' + JNT_SUFFIX.capitalize()), radius=.5)

        cmds.delete(cmds.pointConstraint(left_eyebrow_pivot_jnt, new_base_jnt))

        driver_jnt = cmds.duplicate(jnt, name=jnt.replace(JNT_SUFFIX, 'driver' + JNT_SUFFIX.capitalize()), po=True)[0]
        cmds.parent(driver_jnt, new_base_jnt)
        cmds.joint(new_base_jnt, e=True, oj='xyz', secondaryAxisOrient='yup', zso=True, ch=True)
        cmds.parent(new_base_jnt, left_eyebrow_pivot_jnt)
        cmds.parentConstraint(driver_jnt, jnt)
        left_eyebrow_driver_joints.append(driver_jnt)
        left_eyebrow_root_joints.append(new_base_jnt)

    left_eyebrow_controls = []
    for jnt in left_eyebrow_driver_joints:
        ctrl_objs = create_arched_control(jnt, ctrl_name=jnt.replace('driver' + JNT_SUFFIX.capitalize(), 'ctrl'),
                                          radius=left_eyebrow_scale * .05, create_offset_grp=True)
        left_eyebrow_controls.append(ctrl_objs)

    # Control Holder
    left_eyebrow_ctrls_grp = cmds.group(name='left_eyebrow_' + CTRL_SUFFIX + GRP_SUFFIX.capitalize(), empty=True,
                                        world=True)
    left_eyebrow_data_grp = cmds.group(name='left_eyebrow_data' + GRP_SUFFIX.capitalize(), empty=True, world=True)

    cmds.delete(cmds.parentConstraint(left_eyebrow_pivot_jnt, left_eyebrow_ctrls_grp))
    cmds.delete(cmds.parentConstraint(left_eyebrow_pivot_jnt, left_eyebrow_data_grp))

    cmds.parent(left_eyebrow_ctrls_grp, head_ctrl)
    cmds.parent(left_eyebrow_data_grp, head_ctrl)

    for ctrl_data in left_eyebrow_controls:
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

        # Connect Scale
        cmds.connectAttr(ctrl + '.jointScale', skinned_jnt + '.scale')
        lock_hide_default_attr(ctrl, translate=False, rotate=False)

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
        new_base_jnt = cmds.joint(name=jnt.replace(JNT_SUFFIX, 'root' + JNT_SUFFIX.capitalize()), radius=.5)

        cmds.delete(cmds.pointConstraint(right_eyebrow_pivot_jnt, new_base_jnt))

        driver_jnt = cmds.duplicate(jnt, name=jnt.replace(JNT_SUFFIX, 'driver' + JNT_SUFFIX.capitalize()), po=True)[0]
        cmds.parent(driver_jnt, new_base_jnt)
        cmds.joint(new_base_jnt, e=True, oj='xyz', secondaryAxisOrient='yup', zso=True, ch=True)
        cmds.parent(new_base_jnt, right_eyebrow_pivot_jnt)
        cmds.parentConstraint(driver_jnt, jnt)
        right_eyebrow_driver_joints.append(driver_jnt)
        right_eyebrow_root_joints.append(new_base_jnt)

    right_eyebrow_controls = []
    for jnt in right_eyebrow_driver_joints:
        ctrl_objs = create_arched_control(jnt, ctrl_name=jnt.replace('driver' + JNT_SUFFIX.capitalize(), 'ctrl'),
                                          radius=right_eyebrow_scale * .05, create_offset_grp=True,
                                          invert_orientation=True)
        for dimension in ['x', 'y', 'z']:
            cmds.setAttr(ctrl_objs[0] + '.s' + dimension, -1)

        right_eyebrow_controls.append(ctrl_objs)

    # Control Holder
    right_eyebrow_ctrls_grp = cmds.group(name='right_eyebrow_' + CTRL_SUFFIX + GRP_SUFFIX.capitalize(), empty=True,
                                         world=True)
    right_eyebrow_data_grp = cmds.group(name='right_eyebrow_data' + GRP_SUFFIX.capitalize(), empty=True, world=True)

    cmds.delete(cmds.parentConstraint(right_eyebrow_pivot_jnt, right_eyebrow_ctrls_grp))
    cmds.delete(cmds.parentConstraint(right_eyebrow_pivot_jnt, right_eyebrow_data_grp))

    cmds.parent(right_eyebrow_ctrls_grp, head_ctrl)
    cmds.parent(right_eyebrow_data_grp, head_ctrl)

    for ctrl_data in right_eyebrow_controls:
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

        # Connect Scale
        cmds.connectAttr(ctrl + '.jointScale', skinned_jnt + '.scale')
        lock_hide_default_attr(ctrl, translate=False, rotate=False)
        cmds.setAttr(ctrl + '.rotateZ', 0)

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
    # Right Side Invert
    cmds.rotate(-180, right_eyebrow_ctrl_grp, rotateX=True)
    for dimension in ['x', 'y', 'z']:
        cmds.setAttr(right_eyebrow_ctrl + '.s' + dimension, -1)
    cmds.parentConstraint(right_eyebrow_ctrl, right_eyebrow_ctrls_grp, mo=True)
    change_viewport_color(right_eyebrow_ctrl, (1, .2, 1))

    # ####################################### Eyelids #######################################

    # ## Left Eyelids ##
    left_eyelids_scale = 0
    left_eyelids_scale += dist_center_to_center(_facial_joints_dict.get('left_upper_eyelid_jnt'),
                                                _facial_joints_dict.get('left_lower_eyelid_jnt')) * 5

    cmds.select(clear=True)
    left_eyelid_pivot_jnt = cmds.joint(name='left_eyelid_pivot' + JNT_SUFFIX.capitalize(), radius=.5)
    cmds.delete(cmds.pointConstraint(_facial_joints_dict.get('left_eye_jnt'), left_eyelid_pivot_jnt))
    cmds.parent(left_eyelid_pivot_jnt, skeleton_grp)
    cmds.parentConstraint(_facial_joints_dict.get('head_jnt'), left_eyelid_pivot_jnt, mo=True)

    # Create Controls
    left_eyelid_driver_joints = []
    left_eyelid_root_joints = []
    for jnt in [_facial_joints_dict.get('left_upper_eyelid_jnt'), _facial_joints_dict.get('left_lower_eyelid_jnt')]:
        cmds.select(clear=True)
        new_base_jnt = cmds.joint(name=jnt.replace(JNT_SUFFIX, 'root' + JNT_SUFFIX.capitalize()), radius=.5)

        cmds.delete(cmds.pointConstraint(left_eyelid_pivot_jnt, new_base_jnt))

        driver_jnt = cmds.duplicate(jnt, name=jnt.replace(JNT_SUFFIX, 'driver' + JNT_SUFFIX.capitalize()), po=True)[0]
        cmds.parent(driver_jnt, new_base_jnt)
        cmds.joint(new_base_jnt, e=True, oj='xyz', secondaryAxisOrient='yup', zso=True, ch=True)
        cmds.parent(new_base_jnt, left_eyelid_pivot_jnt)
        cmds.parentConstraint(driver_jnt, jnt)
        left_eyelid_driver_joints.append(driver_jnt)
        left_eyelid_root_joints.append(new_base_jnt)

    left_eyelid_controls = []
    for jnt in left_eyelid_driver_joints:
        ctrl_objs = create_arched_control(jnt, ctrl_name=jnt.replace('driver' + JNT_SUFFIX.capitalize(), 'ctrl'),
                                          radius=left_eyelids_scale * .05, create_offset_grp=True, suppress_scale=True)
        left_eyelid_controls.append(ctrl_objs)

    # Control Holder
    left_eyelids_ctrls_grp = cmds.group(name='left_eyelids_' + CTRL_SUFFIX + GRP_SUFFIX.capitalize(), empty=True,
                                        world=True)
    left_eyelids_data_grp = cmds.group(name='left_eyelids_data' + GRP_SUFFIX.capitalize(), empty=True, world=True)

    cmds.delete(cmds.parentConstraint(left_eyelid_pivot_jnt, left_eyelids_ctrls_grp))
    cmds.delete(cmds.parentConstraint(left_eyelid_pivot_jnt, left_eyelids_data_grp))

    cmds.parent(left_eyelids_ctrls_grp, head_ctrl)
    cmds.parent(left_eyelids_data_grp, head_ctrl)

    for ctrl_data in left_eyelid_controls:
        # Unpack Data
        ctrl = ctrl_data[0]
        ctrl_grp = ctrl_data[1]
        trans_loc = ctrl_data[2]
        trans_loc_grp = ctrl_data[3]
        end_joint = ctrl_data[4]

        # # Organize Hierarchy
        cmds.parent(ctrl_grp, left_eyelids_ctrls_grp)
        cmds.parent(trans_loc_grp, left_eyelids_data_grp)

        # Adjust Controls
        cmds.setAttr(ctrl + '.movement', left_eyelids_scale * 1.4)
        cmds.setAttr(trans_loc + '.v', 0)

        cmds.setAttr(ctrl + '.zOffsetInfluence', k=False)
        cmds.setAttr(ctrl + '.extraOffset', k=False)

        # Find Skinned Joint And Delete it
        skinned_jnt_parent_constraint = \
            cmds.listConnections(end_joint + '.translate', destination=True, type='parentConstraint')[0]
        skinned_jnt = cmds.listConnections(skinned_jnt_parent_constraint + '.constraintRotateX', type='joint')[0]
        cmds.delete(skinned_jnt)

        change_viewport_color(ctrl, LEFT_CTRL_COLOR)

    # ## Right Eyelids ##
    right_eyelids_scale = 0
    right_eyelids_scale += dist_center_to_center(_facial_joints_dict.get('right_upper_eyelid_jnt'),
                                                 _facial_joints_dict.get('right_lower_eyelid_jnt')) * 5

    cmds.select(clear=True)
    right_eyelid_pivot_jnt = cmds.joint(name='right_eyelid_pivot' + JNT_SUFFIX.capitalize(), radius=.5)
    cmds.delete(cmds.pointConstraint(_facial_joints_dict.get('right_eye_jnt'), right_eyelid_pivot_jnt))
    cmds.parent(right_eyelid_pivot_jnt, skeleton_grp)
    cmds.parentConstraint(_facial_joints_dict.get('head_jnt'), right_eyelid_pivot_jnt, mo=True)

    # Create Controls
    right_eyelid_driver_joints = []
    right_eyelid_root_joints = []
    for jnt in [_facial_joints_dict.get('right_upper_eyelid_jnt'),
                _facial_joints_dict.get('right_lower_eyelid_jnt')]:
        cmds.select(clear=True)
        new_base_jnt = cmds.joint(name=jnt.replace(JNT_SUFFIX, 'root' + JNT_SUFFIX.capitalize()), radius=.5)

        cmds.delete(cmds.pointConstraint(right_eyelid_pivot_jnt, new_base_jnt))

        driver_jnt = cmds.duplicate(jnt, name=jnt.replace(JNT_SUFFIX, 'driver' + JNT_SUFFIX.capitalize()), po=True)[0]
        cmds.parent(driver_jnt, new_base_jnt)
        cmds.joint(new_base_jnt, e=True, oj='xyz', secondaryAxisOrient='yup', zso=True, ch=True)
        cmds.parent(new_base_jnt, right_eyelid_pivot_jnt)
        cmds.parentConstraint(driver_jnt, jnt)
        right_eyelid_driver_joints.append(driver_jnt)
        right_eyelid_root_joints.append(new_base_jnt)

    right_eyelid_controls = []
    for jnt in right_eyelid_driver_joints:
        ctrl_objs = create_arched_control(jnt, ctrl_name=jnt.replace('driver' + JNT_SUFFIX.capitalize(), 'ctrl'),
                                          radius=right_eyelids_scale * .05, create_offset_grp=True, suppress_scale=True)
        right_eyelid_controls.append(ctrl_objs)

    # Control Holder
    right_eyelids_ctrls_grp = cmds.group(name='right_eyelids_' + CTRL_SUFFIX + GRP_SUFFIX.capitalize(), empty=True,
                                         world=True)
    right_eyelids_data_grp = cmds.group(name='right_eyelids_data' + GRP_SUFFIX.capitalize(), empty=True, world=True)

    cmds.delete(cmds.parentConstraint(right_eyelid_pivot_jnt, right_eyelids_ctrls_grp))
    cmds.delete(cmds.parentConstraint(right_eyelid_pivot_jnt, right_eyelids_data_grp))

    cmds.parent(right_eyelids_ctrls_grp, head_ctrl)
    cmds.parent(right_eyelids_data_grp, head_ctrl)

    for ctrl_data in right_eyelid_controls:
        # Unpack Data
        ctrl = ctrl_data[0]
        ctrl_grp = ctrl_data[1]
        trans_loc = ctrl_data[2]
        trans_loc_grp = ctrl_data[3]
        end_joint = ctrl_data[4]

        # # Organize Hierarchy
        cmds.parent(ctrl_grp, right_eyelids_ctrls_grp)
        cmds.parent(trans_loc_grp, right_eyelids_data_grp)

        # Adjust Controls
        if 'upper' in ctrl:
            cmds.setAttr(ctrl + '.movement', right_eyelids_scale * 5.35)
        else:
            cmds.setAttr(ctrl + '.movement', right_eyelids_scale * 1.5)
        cmds.setAttr(trans_loc + '.v', 0)

        cmds.setAttr(ctrl + '.zOffsetInfluence', k=False)
        cmds.setAttr(ctrl + '.extraOffset', k=False)

        # Find Skinned Joint And Delete it
        skinned_jnt_parent_constraint = \
            cmds.listConnections(end_joint + '.translate', destination=True, type='parentConstraint')[0]
        skinned_jnt = cmds.listConnections(skinned_jnt_parent_constraint + '.constraintRotateX', type='joint')[0]
        cmds.delete(skinned_jnt)

        change_viewport_color(ctrl, RIGHT_CTRL_COLOR)

    # Create Skinned Joints
    eyelid_root_joints = right_eyelid_root_joints + left_eyelid_root_joints
    for jnt in eyelid_root_joints:
        skinned_jnt = cmds.duplicate(jnt, name=jnt.replace('rootJnt', JNT_SUFFIX), parentOnly=True)[0]
        cmds.parent(skinned_jnt, _facial_joints_dict.get('head_jnt'))
        cmds.parentConstraint(jnt, skinned_jnt)

    # #### Color Joints ####
    to_color = []
    for obj in _facial_joints_dict:
        to_color.append(_facial_joints_dict.get(obj))
    for obj in mouth_root_joints:
        to_color.append(obj)
    for obj in left_eyebrow_root_joints:
        to_color.append(obj)
    for obj in right_eyebrow_root_joints:
        to_color.append(obj)
    for obj in left_eyelid_root_joints:
        to_color.append(obj)
    for obj in right_eyelid_root_joints:
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

    facial_gui_grp = create_facial_side_gui()
    cmds.delete(cmds.pointConstraint(_facial_joints_dict.get('mid_upper_lip_jnt'), facial_gui_grp))
    cmds.parent(facial_gui_grp, head_ctrl)
    cmds.move(general_head_scale * 2, facial_gui_grp, moveX=True, relative=True)
    rescale(facial_gui_grp, general_head_scale * .02, freeze=False)
    offset_locators = []
    for ctrl_data in mouth_controls:
        ctrl_name = ctrl_data[0]
        ctrl_grp = ctrl_data[1]
        ctrl_offset = ctrl_data[5]
        ctrl_loc = cmds.spaceLocator(name=ctrl_name + 'OffsetLoc')[0]
        offset_locators.append(ctrl_loc)
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

    # Setup Other Controls
    jaw_offset_grp = create_inbetween(jaw_ctrl, 'Driven')

    # Control, [Offset Group, Type]
    _setup_offset_target = {main_mouth_ctrl: [main_mouth_offset_grp, '1d'],
                            jaw_ctrl: [jaw_offset_grp, '2d'],
                            }

    eyelid_controls = left_eyelid_controls + right_eyelid_controls
    for obj in eyelid_controls:
        ctrl = obj[0]
        offset_ctrl = obj[5]
        offset_ctrl = cmds.rename(offset_ctrl, offset_ctrl.replace('Offset', 'Driven'))
        _setup_offset_target[ctrl] = [offset_ctrl, '1d']

    _offset_target_reposition = {}

    for ctrl_name, data in _setup_offset_target.items():
        ctrl_offset = data[0]
        ctrl_type = data[1]
        ctrl_grp = ctrl_name + GRP_SUFFIX.capitalize()
        ctrl_loc = cmds.spaceLocator(name=ctrl_name + 'OffsetLoc')[0]
        offset_locators.append(ctrl_loc)
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
            offset_locators.append(ctrl_loc)
            trans_multiply_node = cmds.rename(trans_multiply_node, trans_multiply_node.replace('multiply', 'multiplyY'))
            rot_multiply_node = cmds.rename(rot_multiply_node, rot_multiply_node.replace('multiply', 'multiplyY'))
            ctrl_loc_x = cmds.spaceLocator(name=ctrl_name + 'OffsetXLoc')[0]
            offset_locators.append(ctrl_loc_x)
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

    # Find main control and check if it needs to set rot differently
    is_uniform = False
    main_rig_ctrl = find_transform('main_ctrl', item_type='transform', log_fail=False)
    if main_rig_ctrl:
        metadata = get_metadata(main_rig_ctrl)
        if metadata:
            if "uniform_ctrl_orient" in metadata:
                is_uniform = metadata.get("uniform_ctrl_orient")

    # Set locator initial values
    for ctrl_loc, float_value in _offset_target_reposition.items():
        if 'jaw_ctrlOffsetYLoc' in ctrl_loc:
            cmds.rotate(float_value * -15, ctrl_loc, rotateZ=True, relative=True)
            if is_uniform:
                cmds.setAttr(ctrl_loc + '.rz', 0)
                cmds.rotate(float_value * 15, ctrl_loc, rotateX=True, relative=True, objectSpace=True)
        elif 'jaw_ctrlOffsetXLoc' in ctrl_loc:
            cmds.rotate(float_value * -15, ctrl_loc, rotateY=True, relative=True)
        elif 'left_cornerLip_ctrlOffsetXLoc' in ctrl_loc:
            cmds.move(float_value, ctrl_loc, moveX=True, relative=True)
        elif 'right_cornerLip_ctrlOffsetXLoc' in ctrl_loc:
            cmds.move(-float_value, ctrl_loc, moveX=True, relative=True)
        elif 'left_innerBrow_ctrlOffsetXLoc' in ctrl_loc:
            cmds.setAttr(ctrl_loc + '.ty', 0)
            cmds.move(float_value * 1.2, ctrl_loc, moveX=True, relative=True)
        elif 'right_innerBrow_ctrlOffsetXLoc' in ctrl_loc:
            cmds.setAttr(ctrl_loc + '.ty', 0)
            cmds.move(-float_value * 1.2, ctrl_loc, moveX=True, relative=True)
        elif 'Eyelid_ctrlOffsetLoc' in ctrl_loc:
            side = 'left'
            if 'right' in ctrl_loc:
                side = 'right'
            cmds.delete(cmds.pointConstraint(_facial_joints_dict.get(side + '_eye_jnt'), ctrl_loc, skip=('x', 'z')))
        else:
            cmds.move(float_value, ctrl_loc, moveY=True, relative=True)
        rescale(ctrl_loc, mouth_scale * 0.05, freeze=False)

    # # Jaw Upper Movement Limit
    # jaw_offset_ctrl = jaw_ctrl.replace(CTRL_SUFFIX, 'offset_ctrl')
    # cmds.addAttr(jaw_offset_ctrl, ln='controlBehaviour', at='enum', en='-------------:', keyable=True)
    # cmds.setAttr(jaw_offset_ctrl + '.' + 'controlBehaviour', lock=True)
    # cmds.addAttr(jaw_offset_ctrl, ln='limitJawClosing', at='double', k=True, min=0)
    # cmds.setAttr(jaw_offset_ctrl + '.limitJawClosing', 5)
    # cmds.connectAttr(jaw_offset_ctrl + '.limitJawClosing', jaw_offset_grp + '.maxRotXLimit')
    # cmds.setAttr(jaw_offset_grp + '.maxRotXLimitEnable', 1)

    # Eyelids Changes
    for obj in eyelid_controls:
        ctrl = obj[0]
        offset_ctrl = obj[5]
        offset_ctrl = offset_ctrl.replace('Offset', 'Driven')
        multiply_node = cmds.listConnections(offset_ctrl + '.translate', source=True)[0]
        range_node = cmds.listConnections(multiply_node + '.input2X', source=True)[0]
        offset_ctrl = cmds.listConnections(range_node + '.valueY', source=True)[0]

        invert_node = cmds.createNode('multiplyDivide', name=ctrl.replace(CTRL_SUFFIX, 'invertedRange'))
        sum_node = cmds.createNode('plusMinusAverage', name=ctrl.replace(CTRL_SUFFIX, 'blinkSum'))
        cmds.connectAttr(offset_ctrl + '.ty', sum_node + '.input1D[0]', force=True)
        cmds.connectAttr(invert_node + '.outputY', range_node + '.valueY', force=True)
        cmds.setAttr(invert_node + '.input2X', -.5)
        cmds.setAttr(invert_node + '.input2Y', -.5)
        cmds.setAttr(invert_node + '.input2Z', -.5)
        cmds.connectAttr(sum_node + '.output1D', invert_node + '.input1Y', force=True)

        blink_offset_ctrl = 'left_blinkEyelid_ctrl'
        if ctrl.startswith('right'):
            blink_offset_ctrl = 'right_blinkEyelid_ctrl'

        if 'upper' in ctrl:
            cmds.connectAttr(blink_offset_ctrl + '.ty', sum_node + '.input1D[1]', force=True)
        else:
            extra_invert_node = cmds.createNode('multiplyDivide', name=ctrl.replace(CTRL_SUFFIX, 'invertedOutput'))
            cmds.connectAttr(blink_offset_ctrl + '.ty', extra_invert_node + '.input1Y', force=True)
            cmds.setAttr(extra_invert_node + '.input2X', -1)
            cmds.setAttr(extra_invert_node + '.input2Y', -1)
            cmds.setAttr(extra_invert_node + '.input2Z', -1)
            cmds.connectAttr(extra_invert_node + '.outputY', sum_node + '.input1D[1]', force=True)

    # Invert Right Orientation
    for ctrl in eyelid_controls:
        ctrl = ctrl[0]
        if 'right' in ctrl:
            offset_grp = create_inbetween(ctrl)
            cmds.rotate(-180, offset_grp, rotateX=True)
            cmds.rotate(-180, offset_grp, rotateZ=True)
            cmds.setAttr(ctrl + '.sz', -1)
            cmds.rename(offset_grp, ctrl + 'Offset' + GRP_SUFFIX.capitalize())

    # Hide Pivot Joints
    all_joints = cmds.ls(type='joint')
    for jnt in all_joints:
        if jnt.endswith('pivotJnt'):
            cmds.setAttr(jnt + '.v', 0)

    # Create Hide Attribute
    cmds.addAttr(head_ctrl, ln='sideGUICtrlVisibility', at='bool', keyable=True, niceName='Facial Side GUI Visibility')
    cmds.setAttr(head_ctrl + '.sideGUICtrlVisibility', 1)
    cmds.connectAttr(head_ctrl + '.sideGUICtrlVisibility', facial_gui_grp + '.v')
    cmds.addAttr(head_ctrl, ln='facialCtrlsVisibility', at='bool', keyable=True, niceName='Facial Ctrls Visibility')
    cmds.setAttr(head_ctrl + '.facialCtrlsVisibility', 1)
    cmds.addAttr(head_ctrl, ln='facialOffsetVisibility', at='bool', keyable=True, niceName='Offset Locators Visibility')
    cmds.setAttr(head_ctrl + '.facialOffsetVisibility', 0)

    cmds.connectAttr(head_ctrl + '.facialCtrlsVisibility', left_eyebrow_ctrl_grp + '.v')
    cmds.connectAttr(head_ctrl + '.facialCtrlsVisibility', right_eyebrow_ctrl_grp + '.v')
    cmds.connectAttr(head_ctrl + '.facialCtrlsVisibility', left_eyebrow_ctrls_grp + '.v')
    cmds.connectAttr(head_ctrl + '.facialCtrlsVisibility', right_eyebrow_ctrls_grp + '.v')
    cmds.connectAttr(head_ctrl + '.facialCtrlsVisibility', left_eyelids_ctrls_grp + '.v')
    cmds.connectAttr(head_ctrl + '.facialCtrlsVisibility', right_eyelids_ctrls_grp + '.v')
    cmds.connectAttr(head_ctrl + '.facialCtrlsVisibility', mouth_ctrls_grp + '.v')
    cmds.connectAttr(head_ctrl + '.facialCtrlsVisibility', jaw_ctrls_grp + '.v')
    cmds.connectAttr(head_ctrl + '.facialCtrlsVisibility', main_mouth_ctrl_grp + '.v')

    # Behavior Adjustment
    cmds.setAttr(right_corner_ctrl + '.sx', -1)
    cmds.setAttr(right_corner_ctrl + '.sy', -1)
    cmds.setAttr(right_corner_ctrl + '.sz', -1)

    # Tongue Ctrl
    tongue_scale = dist_center_to_center(_facial_joints_dict.get('tip_tongue_jnt'),
                                         _facial_joints_dict.get('mid_tongue_jnt'))
    tongue_scale += dist_center_to_center(_facial_joints_dict.get('mid_tongue_jnt'),
                                          _facial_joints_dict.get('base_tongue_jnt'))

    cmds.parent(_facial_joints_dict.get('tip_tongue_jnt'), _facial_joints_dict.get('mid_tongue_jnt'))
    cmds.parent(_facial_joints_dict.get('mid_tongue_jnt'), _facial_joints_dict.get('base_tongue_jnt'))
    cmds.parent(_facial_joints_dict.get('base_tongue_jnt'), _facial_joints_dict.get('jaw_jnt'))

    cmds.joint(_facial_joints_dict.get('base_tongue_jnt'), e=True, oj='xyz',
               secondaryAxisOrient='yup', ch=True, zso=True)
    cmds.joint(_facial_joints_dict.get('tip_tongue_jnt'), e=True, oj='none', ch=True, zso=True)

    tongue_jnt_color = (.3, 0, 0)
    change_viewport_color(_facial_joints_dict.get('base_tongue_jnt'), tongue_jnt_color)
    change_viewport_color(_facial_joints_dict.get('mid_tongue_jnt'), tongue_jnt_color)
    change_viewport_color(_facial_joints_dict.get('tip_tongue_jnt'), tongue_jnt_color)
    cmds.setAttr(_facial_joints_dict.get('base_tongue_jnt') + '.radius', .7)
    cmds.setAttr(_facial_joints_dict.get('mid_tongue_jnt') + '.radius', .5)
    cmds.setAttr(_facial_joints_dict.get('tip_tongue_jnt') + '.radius', .3)

    tongue_joints = [_facial_joints_dict.get('base_tongue_jnt'),
                     _facial_joints_dict.get('mid_tongue_jnt'),
                     _facial_joints_dict.get('tip_tongue_jnt')]
    tongue_ctrl_objects = []
    for jnt in tongue_joints:
        ctrl = create_pin_control(jnt, 1)
        parent_jnt = cmds.listRelatives(jnt, parent=True)[0]

        if cmds.objExists(parent_jnt.replace(JNT_SUFFIX, CTRL_SUFFIX)):
            cmds.parent(ctrl[1], parent_jnt.replace(JNT_SUFFIX, CTRL_SUFFIX))
        else:
            cmds.parent(ctrl[1], jaw_ctrl)
        cmds.parentConstraint(ctrl[0], jnt)
        change_viewport_color(ctrl[0], (1, 0, 1))
        tongue_ctrl_objects.append(ctrl)

        # Add Joint Scale Control to Tongue Controls
        scale_attr = 'jointScale'
        ctrl = ctrl[0]  # Unpack Control Curve
        cmds.addAttr(ctrl, ln=scale_attr, at='double3', k=True)
        cmds.addAttr(ctrl, ln=scale_attr + 'X', at='double', k=True, parent=scale_attr, niceName='Scale Joint X')
        cmds.addAttr(ctrl, ln=scale_attr + 'Y', at='double', k=True, parent=scale_attr, niceName='Scale Joint Y')
        cmds.addAttr(ctrl, ln=scale_attr + 'Z', at='double', k=True, parent=scale_attr, niceName='Scale Joint Z')
        cmds.setAttr(ctrl + '.' + scale_attr + 'X', 1)
        cmds.setAttr(ctrl + '.' + scale_attr + 'Y', 1)
        cmds.setAttr(ctrl + '.' + scale_attr + 'Z', 1)
        cmds.connectAttr(ctrl + '.jointScaleX', jnt + '.sx')
        cmds.connectAttr(ctrl + '.jointScaleY', jnt + '.sy')
        cmds.connectAttr(ctrl + '.jointScaleZ', jnt + '.sz')

    # Side GUI Tongue Connection
    in_out_base_loc = cmds.spaceLocator(name='inOutTongueBase_targetLoc')[0]
    in_out_mid_loc = cmds.spaceLocator(name='inOutTongueMid_targetLoc')[0]
    change_viewport_color(in_out_base_loc, (0, 1, 0))
    change_viewport_color(in_out_mid_loc, (0, 1, 0))
    rescale(in_out_base_loc, .5, freeze=False)
    rescale(in_out_mid_loc, .5, freeze=False)
    cmds.delete(cmds.parentConstraint(_facial_joints_dict.get('base_tongue_jnt'), in_out_base_loc))
    cmds.delete(cmds.parentConstraint(_facial_joints_dict.get('mid_tongue_jnt'), in_out_mid_loc))

    # Unpack
    base_tongue_ctrl = tongue_ctrl_objects[0][0]
    mid_tongue_ctrl = tongue_ctrl_objects[1][0]
    tip_tongue_ctrl = tongue_ctrl_objects[2][0]
    base_tongue_ctrl_offset = tongue_ctrl_objects[0][2]
    base_tongue_ctrl_grp = tongue_ctrl_objects[0][1]
    mid_tongue_ctrl_grp = tongue_ctrl_objects[1][1]
    mid_tongue_ctrl_offset = tongue_ctrl_objects[1][2]
    tip_tongue_ctrl_offset = tongue_ctrl_objects[2][2]

    base_tongue_extra_offset = create_inbetween(base_tongue_ctrl, offset_suffix='Rot')
    mid_tongue_extra_offset = create_inbetween(mid_tongue_ctrl, offset_suffix='Rot')

    cmds.move(tongue_scale * 1.5, in_out_base_loc, moveZ=True, relative=True)
    cmds.move(tongue_scale * .2, in_out_base_loc, moveY=True, relative=True)
    cmds.parent(in_out_base_loc, base_tongue_ctrl_grp)

    cmds.move(tongue_scale * 1.5, in_out_mid_loc, moveZ=True, relative=True)
    cmds.move(tongue_scale * .2, in_out_mid_loc, moveY=True, relative=True)
    cmds.parent(in_out_mid_loc, mid_tongue_ctrl_grp)

    # Setup Blends
    pos_blend = cmds.createNode('blendColors', name=base_tongue_ctrl.replace(CTRL_SUFFIX, '') + 'posBlend')
    rot_blend = cmds.createNode('blendColors', name=base_tongue_ctrl.replace(CTRL_SUFFIX, '') + 'rotBlend')
    range_node = cmds.createNode('remapColor', name=base_tongue_ctrl.replace(CTRL_SUFFIX, '') + 'range')

    for node in [pos_blend, rot_blend]:
        cmds.setAttr(node + '.color2R', 0)
        cmds.setAttr(node + '.color2G', 0)
        cmds.setAttr(node + '.color2B', 0)

    # Setup Conditions
    condition_rot = cmds.createNode('condition', name='tongue_rotOffsetCondition')
    condition_pos = cmds.createNode('condition', name='tongue_posOffsetCondition')
    base_condition_rot = cmds.createNode('condition', name='base_tongue_rotOffsetCondition')
    base_condition_pos = cmds.createNode('condition', name='base_tongue_posOffsetCondition')
    mid_condition_rot = cmds.createNode('condition', name='mid_tongue_rotOffsetCondition')
    mid_condition_pos = cmds.createNode('condition', name='mid_tongue_posOffsetCondition')

    condition_nodes = [base_condition_pos, base_condition_rot, mid_condition_rot, mid_condition_pos]
    for condition in condition_nodes:
        cmds.setAttr(condition + '.colorIfFalseR', 0)
        cmds.setAttr(condition + '.colorIfFalseG', 0)
        cmds.setAttr(condition + '.colorIfFalseB', 0)
    cmds.setAttr(base_condition_pos + '.secondTerm', 1)
    cmds.setAttr(base_condition_pos + '.secondTerm', 1)

    # Create Connections
    in_out_tongue_offset_ctrl = 'inOutTongue_offset_ctrl'
    cmds.addAttr(in_out_tongue_offset_ctrl, ln='controlBehaviour', at='enum', en='-------------:', keyable=True)
    cmds.setAttr(in_out_tongue_offset_ctrl + '.' + 'controlBehaviour', lock=True)
    cmds.addAttr(in_out_tongue_offset_ctrl, ln='offsetTarget', at='enum', en='Base Tongue:Mid Tongue', k=True)
    cmds.setAttr(in_out_tongue_offset_ctrl + '.offsetTarget', 1)

    cmds.connectAttr(in_out_base_loc + '.translate', condition_pos + '.colorIfTrue')
    cmds.connectAttr(in_out_base_loc + '.rotate', condition_rot + '.colorIfTrue')
    cmds.connectAttr(in_out_mid_loc + '.translate', condition_pos + '.colorIfFalse')
    cmds.connectAttr(in_out_mid_loc + '.rotate', condition_rot + '.colorIfFalse')
    cmds.connectAttr(in_out_tongue_offset_ctrl + '.offsetTarget', condition_rot + '.firstTerm')
    cmds.connectAttr(in_out_tongue_offset_ctrl + '.offsetTarget', condition_pos + '.firstTerm')
    cmds.connectAttr(condition_pos + '.outColor', pos_blend + '.color1')
    cmds.connectAttr(condition_rot + '.outColor', rot_blend + '.color1')

    cmds.connectAttr('inOutTongue_offset_ctrl' + '.ty', range_node + '.colorG')
    cmds.setAttr(range_node + '.inputMax', 0)
    cmds.setAttr(range_node + '.inputMin', -10)
    cmds.setAttr(range_node + '.outputMin', 1)
    cmds.setAttr(range_node + '.outputMax', 0)
    cmds.connectAttr(range_node + '.outColorG', pos_blend + '.blender')
    cmds.connectAttr(range_node + '.outColorG', rot_blend + '.blender')

    cmds.connectAttr(rot_blend + '.output', base_condition_rot + '.colorIfTrue')
    cmds.connectAttr(rot_blend + '.output', mid_condition_rot + '.colorIfTrue')
    cmds.connectAttr(pos_blend + '.output', base_condition_pos + '.colorIfTrue')
    cmds.connectAttr(pos_blend + '.output', mid_condition_pos + '.colorIfTrue')
    cmds.connectAttr(in_out_tongue_offset_ctrl + '.offsetTarget', base_condition_rot + '.firstTerm')
    cmds.connectAttr(in_out_tongue_offset_ctrl + '.offsetTarget', mid_condition_rot + '.firstTerm')
    cmds.connectAttr(in_out_tongue_offset_ctrl + '.offsetTarget', base_condition_pos + '.firstTerm')
    cmds.connectAttr(in_out_tongue_offset_ctrl + '.offsetTarget', mid_condition_pos + '.firstTerm')
    cmds.setAttr(mid_condition_rot + '.secondTerm', 1)
    cmds.setAttr(mid_condition_pos + '.secondTerm', 1)
    cmds.setAttr(base_condition_rot + '.secondTerm', 0)
    cmds.setAttr(base_condition_pos + '.secondTerm', 0)
    cmds.connectAttr(base_condition_rot + '.outColor', base_tongue_ctrl_offset + '.rotate')
    cmds.connectAttr(mid_condition_rot + '.outColor', mid_tongue_ctrl_offset + '.rotate')
    cmds.connectAttr(base_condition_pos + '.outColor', base_tongue_ctrl_offset + '.translate')
    cmds.connectAttr(mid_condition_pos + '.outColor', mid_tongue_ctrl_offset + '.translate')

    tongue_offset_ctrl = 'tongue_offset_ctrl'
    cmds.addAttr(tongue_offset_ctrl, ln='controlBehaviour', at='enum', en='-------------:', keyable=True)
    cmds.setAttr(tongue_offset_ctrl + '.' + 'controlBehaviour', lock=True)
    cmds.addAttr(tongue_offset_ctrl, ln='rotationAmount', at='double', k=True, min=0)
    cmds.setAttr(tongue_offset_ctrl + '.rotationAmount', 10)
    cmds.addAttr(tongue_offset_ctrl, ln='baseInfluence', at='double', k=True, min=0, max=1)
    cmds.setAttr(tongue_offset_ctrl + '.baseInfluence', 0)

    rot_influence = cmds.createNode('multiplyDivide', name='tongue_rotInfluence')
    cmds.connectAttr(tongue_offset_ctrl + '.rotationAmount', rot_influence + '.input1X')
    cmds.connectAttr(tongue_offset_ctrl + '.rotationAmount', rot_influence + '.input1Y')
    cmds.connectAttr(tongue_offset_ctrl + '.rotationAmount', rot_influence + '.input1Z')
    cmds.setAttr(rot_influence + '.input2X', 0)
    cmds.connectAttr(tongue_offset_ctrl + '.ty', rot_influence + '.input2Z')
    cmds.connectAttr(tongue_offset_ctrl + '.tx', rot_influence + '.input2Y')
    cmds.connectAttr(rot_influence + '.output', mid_tongue_extra_offset + '.rotate')
    cmds.connectAttr(rot_influence + '.output', tip_tongue_ctrl_offset + '.rotate')

    base_rot_influence = cmds.createNode('multiplyDivide', name='tongue_rotBaseInfluence')
    cmds.connectAttr(rot_influence + '.output', base_rot_influence + '.input1')
    cmds.connectAttr(tongue_offset_ctrl + '.baseInfluence', base_rot_influence + '.input2X')
    cmds.connectAttr(tongue_offset_ctrl + '.baseInfluence', base_rot_influence + '.input2Y')
    cmds.connectAttr(tongue_offset_ctrl + '.baseInfluence', base_rot_influence + '.input2Z')
    cmds.connectAttr(base_rot_influence + '.output', base_tongue_extra_offset + '.rotate')

    # Set Offset Locator Visibility
    offset_locators.append(in_out_base_loc)
    offset_locators.append(in_out_mid_loc)
    for obj in offset_locators:
        if cmds.objExists(obj):
            cmds.connectAttr(head_ctrl + '.facialOffsetVisibility', obj + '.v')
            if 'jaw' not in obj:
                cmds.setAttr(obj + '.rx', 0)

    # Bullet Proof Controls
    tongue_controls = [base_tongue_ctrl, mid_tongue_ctrl, tip_tongue_ctrl]
    main_facial_ctrls = [main_mouth_ctrl, left_eyebrow_ctrl, right_eyebrow_ctrl]
    mouth_corner_ctrls = [left_corner_ctrl, right_corner_ctrl]
    lock_scale_list = mouth_corner_ctrls + mouth_controls
    # lock_scale_list += eyebrow_ctrls + eyelid_controls
    lock_scale_list += eyelid_controls
    lock_scale_list += main_facial_ctrls
    lock_scale_list += tongue_controls

    for ctrl in lock_scale_list:
        if isinstance(ctrl, tuple):
            ctrl = ctrl[0]
        lock_hide_default_attr(ctrl, translate=False, rotate=False)

    # -------------- Fleshy Eyes --------------
    parent_to_head = []
    left_eye_rotation_dir_loc = cmds.spaceLocator(name='left_eyeRotation_dirLoc')[0]
    change_viewport_color(left_eye_rotation_dir_loc, (0, 1, 0))
    cmds.setAttr(left_eye_rotation_dir_loc + '.localScaleX', .5)
    cmds.setAttr(left_eye_rotation_dir_loc + '.localScaleY', .5)
    cmds.setAttr(left_eye_rotation_dir_loc + '.localScaleZ', .5)
    cmds.setAttr(left_eye_rotation_dir_loc + '.v', 0)
    right_eye_rotation_dir_loc = cmds.duplicate(left_eye_rotation_dir_loc, name='right_eyeRotation_dirLoc')[0]
    left_eye_rotation_up_down_loc = cmds.duplicate(left_eye_rotation_dir_loc, name='left_eyeRotation_upDownLoc')[0]
    right_eye_rotation_up_down_loc = cmds.duplicate(left_eye_rotation_dir_loc, name='right_eyeRotation_upDownLoc')[0]
    parent_to_head.append(left_eye_rotation_dir_loc)
    parent_to_head.append(right_eye_rotation_dir_loc)
    left_upper_eyelid_ctrl = left_eyelid_controls[0][0]
    left_lower_eyelid_ctrl = left_eyelid_controls[1][0]
    right_upper_eyelid_ctrl = right_eyelid_controls[0][0]
    right_lower_eyelid_ctrl = right_eyelid_controls[1][0]
    # cmds.deleteAttr(left_upper_eyelid_ctrl, at='jointScale')

    cmds.delete(cmds.pointConstraint([left_upper_eyelid_ctrl, left_lower_eyelid_ctrl], left_eye_rotation_dir_loc))
    cmds.delete(cmds.pointConstraint([right_upper_eyelid_ctrl, right_lower_eyelid_ctrl], right_eye_rotation_dir_loc))
    cmds.parentConstraint([_facial_joints_dict.get('left_eye_jnt')], left_eye_rotation_dir_loc, mo=True)
    cmds.parentConstraint([_facial_joints_dict.get('right_eye_jnt')], right_eye_rotation_dir_loc, mo=True)
    # Up and Down Locs
    left_eye_rotation_up_down_grp = cmds.group(name='left_eyeRotation_upDownGrp', world=True, empty=True)
    right_eye_rotation_up_down_grp = cmds.group(name='right_eyeRotation_upDownGrp', world=True, empty=True)
    cmds.parent(left_eye_rotation_up_down_loc, left_eye_rotation_up_down_grp)
    cmds.parent(right_eye_rotation_up_down_loc, right_eye_rotation_up_down_grp)
    cmds.delete(cmds.pointConstraint(left_eye_rotation_dir_loc, left_eye_rotation_up_down_grp))
    cmds.delete(cmds.pointConstraint(right_eye_rotation_dir_loc, right_eye_rotation_up_down_grp))
    parent_to_head.append(left_eye_rotation_up_down_grp)
    parent_to_head.append(right_eye_rotation_up_down_grp)
    cmds.pointConstraint(left_eye_rotation_dir_loc, left_eye_rotation_up_down_loc, skip="z")
    cmds.pointConstraint(right_eye_rotation_dir_loc, right_eye_rotation_up_down_loc, skip="z")

    # Connections --- Controller: Source Locator
    create_inbetween_sum = {left_upper_eyelid_ctrl: left_eye_rotation_up_down_loc,
                            left_lower_eyelid_ctrl: left_eye_rotation_up_down_loc,
                            right_upper_eyelid_ctrl: right_eye_rotation_up_down_loc,
                            right_lower_eyelid_ctrl: right_eye_rotation_up_down_loc,
                            }
    main_eye_ctrl = 'main_eye_ctrl'
    fleshy_eyes_attr = 'fleshyEyesInfluence'
    if cmds.objExists(main_eye_ctrl):
        cmds.addAttr(main_eye_ctrl, ln=fleshy_eyes_attr, at='double', k=True, min=0, max=1)
        cmds.setAttr(main_eye_ctrl + '.' + fleshy_eyes_attr, 1)
    for ctrl, source_loc in create_inbetween_sum.items():
        ctrl_driven_grp = cmds.listRelatives(ctrl, parent=True)[0]
        if 'right' in ctrl:
            ctrl_driven_grp = cmds.listRelatives(ctrl_driven_grp, parent=True)[0]
        source_connection = cmds.listConnections(ctrl_driven_grp + '.translate', destination=False, plugs=True)[0]
        general_influence_multiply_node = cmds.createNode('multiplyDivide', name='eyelid_fleshyEyesGeneralInfluence')
        ctrl_influence_multiply_node = cmds.createNode('multiplyDivide', name=ctrl + '_fleshEyesCtrlInfluence')
        ctrl_influence_sum_node = cmds.createNode('plusMinusAverage', name=ctrl + '_incomingDrivenSum')
        cmds.disconnectAttr(source_connection, ctrl_driven_grp + '.translate')
        cmds.connectAttr(source_connection, ctrl_influence_sum_node + '.input3D[0]')
        cmds.connectAttr(ctrl_influence_sum_node + '.output3D', ctrl_driven_grp + '.translate')
        cmds.connectAttr(ctrl_influence_multiply_node + '.output', general_influence_multiply_node + '.input1')
        cmds.connectAttr(general_influence_multiply_node + '.output', ctrl_influence_sum_node + '.input3D[1]')
        cmds.connectAttr(source_loc + '.translate', ctrl_influence_multiply_node + '.input1')
        for dimension in ['X', 'Y', 'Z']:
            if cmds.objExists(main_eye_ctrl):
                cmds.connectAttr(main_eye_ctrl + '.' + fleshy_eyes_attr,
                                 general_influence_multiply_node + '.input2' + dimension)

        cmds.addAttr(ctrl, ln='inheritEyeMovement', at='double', k=True, min=0, max=1)
        cmds.setAttr(ctrl + '.inheritEyeMovement', .5)
        cmds.connectAttr(ctrl + '.inheritEyeMovement', ctrl_influence_multiply_node + '.input2X')
        cmds.connectAttr(ctrl + '.inheritEyeMovement', ctrl_influence_multiply_node + '.input2Y')
        cmds.connectAttr(ctrl + '.inheritEyeMovement', ctrl_influence_multiply_node + '.input2Z')

    # Create Cheek Controls -----------------------------------------------------------------------------------
    # Calculate Scale Offset
    cheeks_scale_offset = 0
    cheeks_scale_offset += dist_center_to_center(_facial_joints_dict.get('left_cheek_jnt'),
                                                 _facial_joints_dict.get('right_cheek_jnt'))

    # Control Holder
    cmds.delete(cmds.parentConstraint(_facial_proxy_dict.get('left_cheek_crv'),
                                      _facial_joints_dict.get('left_cheek_jnt')))

    cmds.rotate(-90, 90, 0, _facial_joints_dict.get('left_cheek_jnt'), os=True, relative=True)
    left_cheek_ctrl = cmds.curve(name='left_cheek_' + CTRL_SUFFIX,
                                 p=[[0.0, 0.0, 0.0], [0.001, 0.001, 0.636], [-0.257, 0.001, 0.636],
                                    [-0.247, 0.068, 0.636], [-0.221, 0.129, 0.636], [-0.181, 0.181, 0.636],
                                    [-0.128, 0.223, 0.636], [-0.066, 0.247, 0.636], [-0.0, 0.257, 0.636],
                                    [0.001, 0.001, 0.636], [-0.256, 0.001, 0.636], [-0.247, -0.066, 0.636],
                                    [-0.221, -0.129, 0.636], [-0.181, -0.181, 0.636], [-0.127, -0.222, 0.636],
                                    [-0.066, -0.247, 0.636], [-0.0, -0.257, 0.636], [0.067, -0.248, 0.636],
                                    [0.128, -0.222, 0.636], [0.181, -0.181, 0.636], [0.222, -0.128, 0.636],
                                    [0.247, -0.066, 0.636], [0.257, 0.001, 0.636], [0.248, 0.067, 0.636],
                                    [0.222, 0.129, 0.636], [0.182, 0.181, 0.636], [0.129, 0.221, 0.636],
                                    [0.066, 0.247, 0.636], [-0.0, 0.257, 0.636], [-0.0, -0.257, 0.636],
                                    [0.001, 0.001, 0.636], [0.257, 0.001, 0.636]], d=1)
    rescale(left_cheek_ctrl, cheeks_scale_offset * .1)
    left_cheek_ctrl_grp = cmds.group(name=left_cheek_ctrl + GRP_SUFFIX.capitalize(),
                                     empty=True, world=True)
    cmds.parent(left_cheek_ctrl, left_cheek_ctrl_grp)
    cmds.delete(cmds.parentConstraint(_facial_joints_dict.get('left_cheek_jnt'), left_cheek_ctrl_grp))
    change_viewport_color(left_cheek_ctrl, LEFT_CTRL_COLOR)
    cmds.parentConstraint(left_cheek_ctrl, _facial_joints_dict.get('left_cheek_jnt'))
    cmds.scaleConstraint(left_cheek_ctrl, _facial_joints_dict.get('left_cheek_jnt'))

    cmds.delete(cmds.parentConstraint(_facial_proxy_dict.get('right_cheek_crv'),
                                      _facial_joints_dict.get('right_cheek_jnt')))
    cmds.parent(left_cheek_ctrl_grp, head_ctrl)

    cmds.rotate(-90, 90, 0, _facial_joints_dict.get('right_cheek_jnt'), os=True, relative=True)
    right_cheek_ctrl = cmds.curve(name='right_cheek_' + CTRL_SUFFIX,
                                  p=[[0.0, 0.0, 0.0], [0.001, 0.001, 0.636], [-0.257, 0.001, 0.636],
                                     [-0.247, 0.068, 0.636], [-0.221, 0.129, 0.636], [-0.181, 0.181, 0.636],
                                     [-0.128, 0.223, 0.636], [-0.066, 0.247, 0.636], [-0.0, 0.257, 0.636],
                                     [0.001, 0.001, 0.636], [-0.256, 0.001, 0.636], [-0.247, -0.066, 0.636],
                                     [-0.221, -0.129, 0.636], [-0.181, -0.181, 0.636], [-0.127, -0.222, 0.636],
                                     [-0.066, -0.247, 0.636], [-0.0, -0.257, 0.636], [0.067, -0.248, 0.636],
                                     [0.128, -0.222, 0.636], [0.181, -0.181, 0.636], [0.222, -0.128, 0.636],
                                     [0.247, -0.066, 0.636], [0.257, 0.001, 0.636], [0.248, 0.067, 0.636],
                                     [0.222, 0.129, 0.636], [0.182, 0.181, 0.636], [0.129, 0.221, 0.636],
                                     [0.066, 0.247, 0.636], [-0.0, 0.257, 0.636], [-0.0, -0.257, 0.636],
                                     [0.001, 0.001, 0.636], [0.257, 0.001, 0.636]], d=1)
    rescale(right_cheek_ctrl, cheeks_scale_offset * .1)
    right_cheek_ctrl_grp = cmds.group(name=right_cheek_ctrl + GRP_SUFFIX.capitalize(),
                                      empty=True, world=True)
    cmds.parent(right_cheek_ctrl, right_cheek_ctrl_grp)
    cmds.delete(cmds.parentConstraint(_facial_joints_dict.get('right_cheek_jnt'), right_cheek_ctrl_grp))
    change_viewport_color(right_cheek_ctrl, RIGHT_CTRL_COLOR)
    cmds.parentConstraint(right_cheek_ctrl, _facial_joints_dict.get('right_cheek_jnt'))
    cmds.scaleConstraint(right_cheek_ctrl, _facial_joints_dict.get('right_cheek_jnt'))
    cmds.parent(right_cheek_ctrl_grp, head_ctrl)

    # Create Nose Controls -----------------------------------------------------------------------------------
    cmds.parent(_facial_joints_dict.get('left_nose_jnt'), _facial_joints_dict.get('head_jnt'))
    cmds.parent(_facial_joints_dict.get('right_nose_jnt'), _facial_joints_dict.get('head_jnt'))

    nose_scale_offset = 0
    nose_scale_offset += dist_center_to_center(_facial_joints_dict.get('left_nose_jnt'),
                                               _facial_joints_dict.get('right_nose_jnt'))

    cmds.delete(cmds.parentConstraint(_facial_proxy_dict.get('left_nose_crv'),
                                      _facial_joints_dict.get('left_nose_jnt')))

    left_nose_ctrl = cmds.circle(name='left_nose_' + CTRL_SUFFIX, normal=[0, 0, 1],
                                 ch=False, radius=nose_scale_offset * .2)[0]
    cmds.setAttr(_facial_joints_dict.get('left_nose_jnt') + '.rx', 0)
    cmds.setAttr(_facial_joints_dict.get('left_nose_jnt') + '.ry', 0)
    cmds.setAttr(_facial_joints_dict.get('left_nose_jnt') + '.rz', 0)
    left_nose_ctrl_grp = cmds.group(name=left_nose_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(left_nose_ctrl, left_nose_ctrl_grp)
    cmds.delete(cmds.pointConstraint(_facial_joints_dict.get('left_nose_jnt'), left_nose_ctrl_grp))
    cmds.parentConstraint(left_nose_ctrl, _facial_joints_dict.get('left_nose_jnt'))
    cmds.scaleConstraint(left_nose_ctrl, _facial_joints_dict.get('left_nose_jnt'))
    lock_hide_default_attr(left_nose_ctrl, translate=False, scale=False, rotate=False)  # Hide Visibility
    change_viewport_color(left_nose_ctrl, LEFT_CTRL_COLOR)
    cmds.parent(left_nose_ctrl_grp, head_ctrl)

    cmds.delete(cmds.parentConstraint(_facial_proxy_dict.get('right_nose_crv'),
                                      _facial_joints_dict.get('right_nose_jnt')))

    right_nose_ctrl = cmds.circle(name='right_nose_' + CTRL_SUFFIX, normal=[0, 0, 1],
                                  ch=False, radius=nose_scale_offset * .2)[0]
    cmds.setAttr(_facial_joints_dict.get('right_nose_jnt') + '.rx', 0)
    cmds.setAttr(_facial_joints_dict.get('right_nose_jnt') + '.ry', 0)
    cmds.setAttr(_facial_joints_dict.get('right_nose_jnt') + '.rz', 0)
    right_nose_ctrl_grp = cmds.group(name=right_nose_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(right_nose_ctrl, right_nose_ctrl_grp)
    cmds.delete(cmds.pointConstraint(_facial_joints_dict.get('right_nose_jnt'), right_nose_ctrl_grp))
    cmds.parentConstraint(right_nose_ctrl, _facial_joints_dict.get('right_nose_jnt'))
    cmds.scaleConstraint(right_nose_ctrl, _facial_joints_dict.get('right_nose_jnt'))
    lock_hide_default_attr(right_nose_ctrl, translate=False, scale=False, rotate=False)  # Hide Visibility
    change_viewport_color(right_nose_ctrl, RIGHT_CTRL_COLOR)
    cmds.parent(right_nose_ctrl_grp, head_ctrl)

    # Head Controls Ctrl Visibility
    cmds.connectAttr(head_ctrl + '.facialCtrlsVisibility', left_cheek_ctrl_grp + '.v')
    cmds.connectAttr(head_ctrl + '.facialCtrlsVisibility', right_cheek_ctrl_grp + '.v')
    cmds.connectAttr(head_ctrl + '.facialCtrlsVisibility', left_nose_ctrl_grp + '.v')
    cmds.connectAttr(head_ctrl + '.facialCtrlsVisibility', right_nose_ctrl_grp + '.v')

    # Flesh Eyes Hierarchy
    head_offset_ctrl = 'head_offsetCtrl'
    if cmds.objExists(head_offset_ctrl):
        for obj in parent_to_head:
            enforce_parent(obj, head_offset_ctrl)
    else:
        for obj in parent_to_head:
            enforce_parent(obj, head_ctrl)

    parent_to_head_offset = [mouth_ctrls_grp,
                             mouth_data_grp,
                             jaw_ctrls_grp,
                             main_mouth_ctrl_grp,
                             left_eyebrow_ctrls_grp,
                             left_eyebrow_data_grp,
                             left_eyebrow_ctrl_grp,
                             right_eyebrow_ctrls_grp,
                             right_eyebrow_data_grp,
                             right_eyebrow_ctrl_grp,
                             left_eyelids_ctrls_grp,
                             left_eyelids_data_grp,
                             right_eyelids_ctrls_grp,
                             right_eyelids_data_grp,
                             facial_gui_grp,
                             left_cheek_ctrl_grp,
                             right_cheek_ctrl_grp,
                             left_nose_ctrl_grp,
                             right_nose_ctrl_grp,
                             ]

    # Check if Head offset control is available for re-parenting
    head_offset_ctrl_data = 'head_offsetDataGrp'
    if cmds.objExists(head_offset_ctrl_data):
        for obj in parent_to_head_offset:
            enforce_parent(obj, head_offset_ctrl_data)

    # Setup Pose System  ---------------------------------------------------------------------------------------

    # Create Missing Drivers
    to_create_driver = right_eyebrow_controls
    for ctrl in mouth_controls:
        if 'Outer' in ctrl[0]:
            to_create_driver.append(ctrl)
    for ctrl in right_eyebrow_controls:
        if 'right' in ctrl[0]:
            driven_control = create_inbetween(ctrl[0], 'driver')
            cmds.rename(driven_control, remove_strings_from_string(driven_control, ['invertOrient']))
            cmds.setAttr(ctrl[0] + '.rotateZ', 0)
    # for ctrl in [left_cheek_ctrl, right_cheek_ctrl, left_nose_ctrl, right_nose_ctrl]:
    #     print(ctrl) # @@@

    # Pose Object Setup
    Pose = namedtuple('Pose', ['name',
                               'driver',
                               'driver_range',
                               'driver_end_dir',
                               'driven',
                               'driven_offset',
                               'setup'])
    poses = []

    poses += [
        # Mouth - Counter Clockwise Starting 12PM -----------------------------------------------------
        # Mouth Up ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑
        Pose(name='left_cornerLip_up',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='y',
             driven=['left_cornerLip_ctrl', 'left_upperCornerLip_ctrl', 'left_lowerCornerLip_ctrl'],
             driven_offset=[0, 1, 0, 0, 0, 18, 1, 1, 1],  # TRS e.g. [T, T, T, R, R, R, S, S, S]
             setup='corner_lip'),

        # Mouth Up In  ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖
        Pose(name='left_cornerLip_upIn',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['left_cornerLip_ctrl'],
             driven_offset=[-1, 0.8, 0, 0, 0, 0, 1, 1, 1],
             setup='inner_corner_lip'),
        Pose(name='left_cornerLip_upIn',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['left_upperCornerLip_ctrl'],
             driven_offset=[-1, 0.8, 0, 0, 0, 0, 1, 1, 1],
             setup='inner_corner_lip'),
        Pose(name='left_cornerLip_upIn',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['left_lowerCornerLip_ctrl'],
             driven_offset=[-1, 0.8, 0, 0, 0, 0, 1, 1, 1],
             setup='inner_corner_lip'),
        Pose(name='left_cornerLip_upIn',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['mid_upperLip_ctrl'],  # MID UPPER LIP
             driven_offset=[0, 0, 0, -20, 0, 0, 1, 1, 1],
             setup='inner_corner_lip'),
        Pose(name='left_cornerLip_upIn',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['mid_lowerLip_ctrl'],  # MID LOWER LIP
             driven_offset=[0, 0.2, 0, 25, 0, 0, 1, 1, 1],
             setup='inner_corner_lip'),
        Pose(name='left_cornerLip_upIn',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['left_upperOuterLip_ctrl'],  # OUTER UPPER LIP
             driven_offset=[-0.2, 0.1, 0, 0, 0, 0, 1, 1, 1],
             setup='inner_corner_lip'),
        Pose(name='left_cornerLip_upIn',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['left_lowerOuterLip_ctrl'],  # OUTER LOWER LIP
             driven_offset=[-0.2, 0, 0, 0, 0, 0, 1, 1, 1],
             setup='inner_corner_lip'),

        # Mouth In < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < <
        Pose(name='left_cornerLip_in',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='x',
             driven=['left_cornerLip_ctrl', 'left_upperCornerLip_ctrl', 'left_lowerCornerLip_ctrl'],
             driven_offset=[-1.5, -0.18, 0, 0, 0, 0, 1, 1, 1],
             setup='inner_corner_lip'),
        Pose(name='left_cornerLip_in',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='x',
             driven=['mid_upperLip_ctrl'],  # MID UPPER LIP
             driven_offset=[0, 0, 0, -23, 0, 0, 1, 1, 1],
             setup='inner_corner_lip'),
        Pose(name='left_cornerLip_in',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='x',
             driven=['mid_lowerLip_ctrl'],  # MID LOWER LIP
             driven_offset=[0, 0, 0, 25, 0, 0, 1, 1, 1],
             setup='inner_corner_lip'),
        Pose(name='left_cornerLip_in',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='x',
             driven=['left_upperOuterLip_ctrl'],  # OUTER UPPER LIP
             driven_offset=[-0.2, 0, 0, 0, 0, 0, 1, 1, 1],
             setup='inner_corner_lip'),
        Pose(name='left_cornerLip_in',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='x',
             driven=['left_lowerOuterLip_ctrl'],  # OUTER LOWER LIP
             driven_offset=[0, -0.05, 0, 0, 0, 0, 1.3, 1, 1],
             setup='inner_corner_lip'),

        # Mouth Down In ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙
        Pose(name='left_cornerLip_downIn',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, -5],
             driver_end_dir='xy',
             driven=['left_cornerLip_ctrl', 'left_upperCornerLip_ctrl', 'left_lowerCornerLip_ctrl'],
             driven_offset=[-1.2, -.9, 0, 0, 0, -25, 1, 1, 1],
             setup='inner_corner_lip'),
        Pose(name='left_cornerLip_downIn',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, -5],
             driver_end_dir='xy',
             driven=['mid_upperLip_ctrl'],  # MID UPPER LIP
             driven_offset=[0, -0.4, 0, -20, 0, 0, 1, 1, 1],
             setup='inner_corner_lip'),
        Pose(name='left_cornerLip_downIn',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, -5],
             driver_end_dir='xy',
             driven=['mid_lowerLip_ctrl'],  # MID LOWER LIP
             driven_offset=[0, -0.15, 0, 25, 0, 0, 1, 1, 1],
             setup='inner_corner_lip'),
        Pose(name='left_cornerLip_downIn',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, -5],
             driver_end_dir='xy',
             driven=['left_upperOuterLip_ctrl'],  # OUTER UPPER LIP
             driven_offset=[-0.2, 0.04, 0, 0, 0, 0, 1, 1, 1],
             setup='inner_corner_lip'),
        Pose(name='left_cornerLip_downIn',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, -5],
             driver_end_dir='xy',
             driven=['left_lowerOuterLip_ctrl'],  # OUTER UPPER LIP
             driven_offset=[0, -0.5, 0.1, 0, 0, 0, 1, 1, 1],
             setup='inner_corner_lip'),

        # Mouth Down ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓
        Pose(name='left_cornerLip_down',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, -5],
             driver_end_dir='y',
             driven=['left_cornerLip_ctrl', 'left_upperCornerLip_ctrl', 'left_lowerCornerLip_ctrl'],
             driven_offset=[-0.1, -1.2, 0, 0, 0, -30, 1, 1, 1],
             setup='corner_lip'),

        # Mouth Down Out ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘
        Pose(name='left_cornerLip_downOut',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, -5],
             driver_end_dir='xy',
             driven=['left_cornerLip_ctrl'],
             driven_offset=[1, -1.7, 0, 0, 0, -35, 1, 1, 1],
             setup='outer_corner_lip'),
        Pose(name='left_cornerLip_downOut',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, -5],
             driver_end_dir='xy',
             driven=['left_upperCornerLip_ctrl'],  # UPPER CORNER LIP
             driven_offset=[1, -1.7, 0, 0, 0, -35, .3, 1, .5],
             setup='outer_corner_lip'),
        Pose(name='left_cornerLip_downOut',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, -5],
             driver_end_dir='xy',
             driven=['left_lowerCornerLip_ctrl'],  # LOWER CORNER LIP
             driven_offset=[1, -1.7, 0, 0, 0, -35, 1, .5, .1],
             setup='outer_corner_lip'),
        Pose(name='left_cornerLip_downOut',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, -5],
             driver_end_dir='xy',
             driven=['mid_lowerLip_ctrl'],  # MID LOWER LIP
             driven_offset=[0, 0.1, 0, 0, 0, 0, 1, 1, 1],
             setup='outer_corner_lip'),

        # Mouth Out → → → → → → → → → → → → → → → → → → → → → → → → → → → → → → → → → → → → → → → → →
        Pose(name='left_cornerLip_out',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='x',
             driven=['left_cornerLip_ctrl', 'left_upperCornerLip_ctrl', 'left_lowerCornerLip_ctrl'],
             driven_offset=[1.5, 0, 0, 0, 0, 0, 1, 1, 1],
             setup='outer_corner_lip'),

        # Mouth Up Out ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗
        Pose(name='left_cornerLip_upOut',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['left_cornerLip_ctrl'],
             driven_offset=[1.2, 1.25, 0, 0, 0, 15, 1, 1, 1],
             setup='outer_corner_lip'),
        Pose(name='left_cornerLip_upOut',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['left_upperCornerLip_ctrl'],
             driven_offset=[1.2, 1.25, 0, 0, 0, 15, 1, 1, 1],
             setup='outer_corner_lip'),
        Pose(name='left_cornerLip_upOut',
             driver='left_cornerLip_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['left_lowerCornerLip_ctrl'],
             driven_offset=[1.2, 1.25, 0, 0, 0, 15, 1, 1, 1],
             setup='outer_corner_lip'),
    ]

    poses += [
        # Inner Eyebrows --------------------------------------------------------------------------------
        # Inner Eyebrows Up  ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑
        Pose(name='left_innerBrow_up',
             driver='left_innerBrow_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='y',
             driven=['left_innerBrow_ctrl'],
             driven_offset=[0, 1.5, 0, 0, 0, 0, 1, 1, 1],
             setup='eyebrow'),

        # Inner Eyebrows Up In  ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖
        Pose(name='left_innerBrow_upIn',
             driver='left_innerBrow_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['left_innerBrow_ctrl'],
             driven_offset=[-1.46, 1.47, 0.43, 0, 0, 10.06, 1, 1, 1],
             setup='inner_eyebrow'),
        Pose(name='left_innerBrow_upIn',  # MID brow
             driver='left_innerBrow_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['left_midBrow_ctrl'],
             driven_offset=[-0.95, 1.16, 0.32, 0, 0, -23.01, 1, 1, 1],
             setup='inner_eyebrow'),

        # Inner Eyebrows In < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < <
        Pose(name='left_innerBrow_in',
             driver='left_innerBrow_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='x',
             driven=['left_innerBrow_ctrl'],
             driven_offset=[-1.54, 0, 0.1, 0, 0, 0, 1, 1, 1],
             setup='inner_eyebrow'),
        Pose(name='left_innerBrow_in',  # MID brow
             driver='left_innerBrow_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='x',
             driven=['left_midBrow_ctrl'],
             driven_offset=[-1.17, -0.16, 0.06, 0, 0, -7.25, 1, 1, 1],
             setup='inner_eyebrow'),

        # Inner Eyebrows Down In ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙
        Pose(name='left_innerBrow_downIn',
             driver='left_innerBrow_offset_ctrl',
             driver_range=[0, -5],
             driver_end_dir='xy',
             driven=['left_innerBrow_ctrl'],
             driven_offset=[-1.54, -1.38, 0.1, 0, 0, 0, 1, 1, 1],
             setup='inner_eyebrow'),
        Pose(name='left_innerBrow_downIn',  # MID brow
             driver='left_innerBrow_offset_ctrl',
             driver_range=[0, -5],
             driver_end_dir='xy',
             driven=['left_midBrow_ctrl'],
             driven_offset=[-1.17, -0.16, 0.06, 0, 0, -23, 1, 1, 1],
             setup='inner_eyebrow'),

        # Inner Eyebrows Down ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓
        Pose(name='left_innerBrow_down',
             driver='left_innerBrow_offset_ctrl',
             driver_range=[0, -5],
             driver_end_dir='y',
             driven=['left_innerBrow_ctrl'],
             driven_offset=[0, -1.5, 0, 0, 0, 0, 1, 1, 1],
             setup='eyebrow'),

        # Mid Eyebrows -----------------------------------------------------------------------------------
        # Mid Eyebrows Up  ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑
        Pose(name='left_midBrow_up',
             driver='left_midBrow_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='y',
             driven=['left_midBrow_ctrl'],
             driven_offset=[0, 1.5, 0, 0, 0, 0, 1, 1, 1],
             setup='eyebrow'),

        # Mid Eyebrows Down ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓
        Pose(name='left_midBrow_down',
             driver='left_midBrow_offset_ctrl',
             driver_range=[0, -5],
             driver_end_dir='y',
             driven=['left_midBrow_ctrl'],
             driven_offset=[0, -1.5, 0, 0, 0, 0, 1, 1, 1],
             setup='eyebrow'),

        # Outer EyeBrow ----------------------------------------------------------------------------------
        # Outer EyeBrow Up  ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑
        Pose(name='left_outerBrow_up',
             driver='left_outerBrow_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='y',
             driven=['left_outerBrow_ctrl'],
             driven_offset=[0, 1.5, 0, 0, 0, 0, 1, 1, 1],
             setup='eyebrow'),

        # Outer EyeBrow Down ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓
        Pose(name='left_outerBrow_down',
             driver='left_outerBrow_offset_ctrl',
             driver_range=[0, -5],
             driver_end_dir='y',
             driven=['left_outerBrow_ctrl'],
             driven_offset=[0, -1.5, 0, 0, 0, 0, 1, 1, 1],
             setup='eyebrow'),
    ]

    poses += [
        # Misc ----------------------------------------------------------------------------------
        # Jaw Up  ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑
        Pose(name='jaw_up',
             driver='jaw_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='y',
             driven=['jaw_ctrl'],
             driven_offset=[0, 0, 0, -19, 0, 0, 1, 1, 1],
             setup='jaw'),
        Pose(name='jaw_up',
             driver='jaw_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='y',
             driven=['mid_upperLip_ctrl'],
             driven_offset=[0, 0.95, 0.4, -9.3, 0, 0, 1, 1.1, 1],
             setup='jaw'),
        Pose(name='jaw_up',
             driver='jaw_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='y',
             driven=['mid_lowerLip_ctrl'],
             driven_offset=[0, 0.3, 0, 25, 0, 0, 1, 0.78, 1],
             setup='jaw'),
        Pose(name='jaw_up',
             driver='jaw_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='y',
             driven=['left_cornerLip_ctrl', 'left_lowerCornerLip_ctrl', 'left_upperCornerLip_ctrl'],
             driven_offset=[0, 1, 0, 0, 0, 0, 1, 1, 1],
             setup='jaw'),
        Pose(name='right_jaw_up',
             driver='jaw_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='y',
             driven=['right_cornerLip_ctrl', 'right_lowerCornerLip_ctrl', 'right_upperCornerLip_ctrl'],
             driven_offset=[0, -1, 0, 0, 0, 0, 1, 1, 1],
             setup='jaw'),

        # Jaw Up Out  ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗ ↗
        Pose(name='jaw_upOut',
             driver='jaw_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['jaw_ctrl'],
             driven_offset=[0, 0, 0, -19, 14.23, -10.83, 1, 1, 1],
             setup='outer_jaw'),
        Pose(name='jaw_upOut',
             driver='jaw_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['mid_lowerLip_ctrl'],
             driven_offset=[-0.9, 0.4, 0, 25, 0, 0, 1, 0.78, 1],
             setup='outer_jaw'),
        Pose(name='jaw_upOut',
             driver='jaw_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['left_cornerLip_ctrl', 'left_lowerCornerLip_ctrl', 'left_upperCornerLip_ctrl'],
             driven_offset=[0, 1, 0, 0, 0, 0, 1, 1, 1],
             setup='outer_jaw'),
        Pose(name='rightCorner_jaw_upOut',
             driver='jaw_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['right_cornerLip_ctrl', 'right_lowerCornerLip_ctrl', 'right_upperCornerLip_ctrl'],
             driven_offset=[-0.38, -1, 0, 0, 0, 0, 1, 1, 1],
             setup='outer_jaw'),
        Pose(name='jaw_upOut',
             driver='jaw_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['mid_upperLip_ctrl'],
             driven_offset=[1.1, 0.95, 0.4, 15, 0, 0, 1, 1.1, 1],
             setup='jaw'),
        Pose(name='jaw_upOut',
             driver='jaw_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['right_upperCornerLip_ctrl'],
             driven_offset=[0.9, -0.25, 0.35, 0, 0, 0, 1, 1, 1],
             setup='jaw'),

        # Jaw Up In  ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖ ↖
        Pose(name='jaw_upIn',
             driver='jaw_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['jaw_ctrl'],
             driven_offset=[0, 0, 0, -19, -14.23, 10.83, 1, 1, 1],  # Invert YZ
             setup='inner_jaw'),
        Pose(name='jaw_upIn',
             driver='jaw_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['mid_lowerLip_ctrl'],
             driven_offset=[0.9, 0.4, 0, 25, 0, 0, 1, 0.78, 1],
             setup='inner_jaw'),
        Pose(name='jaw_upIn',
             driver='jaw_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['left_cornerLip_ctrl', 'left_lowerCornerLip_ctrl', 'left_upperCornerLip_ctrl'],
             driven_offset=[0, 1, 0, 0, 0, 0, 1, 1, 1],
             setup='inner_jaw'),
        Pose(name='right_jaw_upIn',
             driver='jaw_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['right_cornerLip_ctrl', 'right_lowerCornerLip_ctrl', 'right_upperCornerLip_ctrl'],
             driven_offset=[-0.38, -1, 0, 0, 0, 0, 1, 1, 1],
             setup='inner_jaw'),
        Pose(name='right_jaw_upIn',
             driver='jaw_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['mid_upperLip_ctrl'],
             driven_offset=[-1.1, 0.95, 0.4, 15, 0, 0, 1, 1.1, 1],
             setup='jaw'),
        Pose(name='right_jaw_upIn',
             driver='jaw_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='xy',
             driven=['right_upperCornerLip_ctrl'],
             driven_offset=[-0.9, -0.25, 0.35, 0, 0, 0, 1, 1, 1],
             setup='jaw'),

        # Jaw In  < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < < <
        Pose(name='jaw_in',
             driver='jaw_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='x',
             driven=['jaw_ctrl'],
             driven_offset=[0, 0, 0, -2.53, -12.79, 2.28, 1, 1, 1],
             setup='inner_jaw'),
        Pose(name='jaw_in',
             driver='jaw_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='x',
             driven=['mid_lowerLip_ctrl'],
             driven_offset=[0.9, 0.3, 0.3, 0, 0, 0, 1, 1, 1],
             setup='inner_jaw'),

        # Jaw Out → → → → → → → → → → → → → → → → → → → → → → → → → → → → → → → → → → → → → → → → →
        Pose(name='jaw_out',
             driver='jaw_offset_ctrl',
             driver_range=[0, -5],
             driver_end_dir='x',
             driven=['jaw_ctrl'],
             driven_offset=[0, 0, 0, -2.53, 12.79, -2.28, 1, 1, 1],  # Invert YZ
             setup='inner_jaw'),
        Pose(name='jaw_out',
             driver='jaw_offset_ctrl',
             driver_range=[0, -5],
             driver_end_dir='x',
             driven=['mid_lowerLip_ctrl'],
             driven_offset=[-0.9, 0.3, 0.3, 0, 0, 0, 1, 1, 1],
             setup='inner_jaw'),

        # Jaw Down In ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙ ↙
        Pose(name='jaw_downIn',
             driver='jaw_offset_ctrl',
             driver_range=[0, -5],
             driver_end_dir='xy',
             driven=['jaw_ctrl'],
             driven_offset=[0, 0, 0, -3, -15, -2.5, 1, 1, 1],
             setup='jaw'),

        # Jaw Down Out ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘ ↘
        Pose(name='jaw_downOut',
             driver='jaw_offset_ctrl',
             driver_range=[0, -5],
             driver_end_dir='xy',
             driven=['jaw_ctrl'],
             driven_offset=[0, 0, 0, -3, 15, 2.5, 1, 1, 1],
             setup='outer_jaw'),
    ]

    poses += [
        # Mouth ----------------------------------------------------------------------------------
        # Mouth Up  ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑
        Pose(name='mouth_up',
             driver='mainMouth_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='y',
             driven=['mainMouth_ctrl'],
             driven_offset=[0, -0.2, 0],
             setup='mouth'),
        Pose(name='mouth_up',
             driver='mainMouth_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='y',
             driven=['mid_upperLip_ctrl'],
             driven_offset=[0, -0.6, 0],
             setup='mouth'),
        Pose(name='mouth_up',
             driver='mainMouth_offset_ctrl',
             driver_range=[0, 5],
             driver_end_dir='y',
             driven=['mid_lowerLip_ctrl'],
             driven_offset=[0, -0.7, 0.27, 0, 0, 0, 1, 1, 1],
             setup='mouth'),

        # Mouth Down  ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓
        Pose(name='mouth_down',
             driver='mainMouth_offset_ctrl',
             driver_range=[0, -5],
             driver_end_dir='y',
             driven=['mainMouth_ctrl'],
             driven_offset=[0, .2, 0, 0, 0, 0, 1, 1, 1],
             setup='mouth'),
        Pose(name='mouth_down',
             driver='mainMouth_offset_ctrl',
             driver_range=[0, -5],
             driver_end_dir='y',
             driven=['mid_lowerLip_ctrl'],
             driven_offset=[0, 0.81, -0.1, 0, 0, 0, 1, 0.8, 1],
             setup='mouth'),
        Pose(name='mouth_down',
             driver='mainMouth_offset_ctrl',
             driver_range=[0, -5],
             driver_end_dir='y',
             driven=['left_lowerOuterLip_ctrl'],
             driven_offset=[0, 0.31, -0.05, 0, 0, 0, 1, 0.8, 1],
             setup='mouth'),
        Pose(name='right_mouth_down',
             driver='mainMouth_offset_ctrl',
             driver_range=[0, -5],
             driver_end_dir='y',
             driven=['right_lowerOuterLip_ctrl'],
             driven_offset=[0, -0.31, -0.05, 0, 0, 0, 1, 0.8, 1],
             setup='mouth'),

    ]

    # Auto Populate Right Side -------------------------------------------------------------------------------
    poses_right = []
    for pose in poses:
        if 'left' in pose.name:
            new_driven = []
            for original_driven in pose.driven:
                new_driven.append(original_driven.replace('left', 'right'))
            right_pose = Pose(name=pose.name.replace('left', 'right'),
                              driver=pose.driver.replace('left', 'right'),
                              driver_range=pose.driver_range,
                              driver_end_dir=pose.driver_end_dir,
                              driven=new_driven,
                              driven_offset=pose.driven_offset,
                              setup=pose.setup),
            poses_right.append(right_pose[0])
    poses += poses_right

    # Build Pose System --------------------------------------------------------------------------------------
    for pose in poses:
        # Unpack
        name = pose.name
        driver = pose.driver  # Driver
        driver_range = pose.driver_range
        driver_end_dir = pose.driver_end_dir
        driven_list = pose.driven  # Driven
        driven_offset = pose.driven_offset
        setup = pose.setup
        # Determine Side
        side = 'left'
        if driver.startswith('right'):
            side = 'right'
        # Useful Data
        main_driver_parent = cmds.listRelatives(driver, parent=True)[0]

        # Determine Distance Loc Position ---------------------------------------------------------------------
        pos_start = (1, 2, 3)  # Later Overwritten
        pos_end = (4, 5, 6)  # Later Overwritten

        distance_node = name + '_distanceNode'
        distance_transform = distance_node.replace('Node', 'Transform')
        loc_start = name + '_startLoc'
        loc_end = name + '_endLoc'
        if not cmds.objExists(distance_node):
            distance_shape = cmds.distanceDimension(endPoint=(pos_end[0], pos_end[1], pos_end[2]),
                                                    startPoint=(pos_start[0], pos_start[1], pos_start[2]))
            loc_start_unnamed = cmds.listConnections(distance_shape + '.startPoint')[0]
            loc_end_unnamed = cmds.listConnections(distance_shape + '.endPoint')[0]
            distance_node = cmds.rename(distance_shape, distance_node)
            loc_start = cmds.rename(loc_start_unnamed, loc_start)
            loc_end = cmds.rename(loc_end_unnamed, loc_end)
            cmds.setAttr(loc_start + '.v', 0)
            # cmds.setAttr(loc_end + '.v', 0)
            distance_transform = cmds.listRelatives(distance_node, parent=True)[0]
            distance_transform = cmds.rename(distance_transform, distance_node.replace('Node', 'Transform'))
            cmds.setAttr(distance_transform + '.overrideEnabled', 1)
            cmds.setAttr(distance_transform + '.overrideDisplayType', 1)
            cmds.delete(cmds.parentConstraint(driver, loc_start))

            # Adjust End Loc Position ------------------------------------------------------------------------------
            current_values = {}
            for char in driver_end_dir:
                current_attr_value = cmds.getAttr(driver + '.t' + char)
                current_values[driver + '.t' + char] = current_attr_value
                offset = driver_range[1]

                if setup.startswith('inner') and char == 'x' and 'down' not in name:
                    offset = -offset
                if setup.startswith('outer') and char == 'x':
                    offset = abs(offset)

                cmds.setAttr(driver + '.t' + char, offset)
            cmds.delete(cmds.pointConstraint(driver, loc_end))
            for target, value in current_values.items():
                cmds.setAttr(target, value)

            # Reshape Stand/End Locators ----------------------------------------------------------------------------
            change_viewport_color(loc_start, (1, 0, 0))
            change_viewport_color(loc_end, (1, 0, 1))
            for dimension in ['X', 'Y', 'Z']:
                for locator in [loc_start, loc_end]:
                    cmds.setAttr(locator + '.localScale' + dimension, .5)

            # Organize Hierarchy -----------------------------------------------------------------------------------
            cmds.parent(loc_start, driver)
            cmds.parent(loc_end, main_driver_parent)
            cmds.makeIdentity(loc_start, translate=True, rotate=True, scale=True, apply=True)
            cmds.makeIdentity(loc_end, translate=True, rotate=True, scale=True, apply=True)

        clean_driven = remove_strings_from_string(driven_list[0], ['left', 'right', 'ctrl', '_'])
        target_loc = name + "_" + clean_driven + 'PoseLoc'
        if not cmds.objExists(target_loc):
            target_loc = cmds.spaceLocator(name=target_loc)[0]
        main_driven_parent = cmds.listRelatives(driven_list[0], parent=True)[0]  # Use first driven parent as main
        main_driven_parent_grp = cmds.listRelatives(main_driven_parent, parent=True)[0]
        cmds.delete(cmds.parentConstraint(main_driven_parent, target_loc))
        enforce_parent(target_loc, main_driven_parent_grp)
        enforce_parent(distance_transform, general_automation_grp)

        for dimension in ['X', 'Y', 'Z']:
            cmds.setAttr(target_loc + '.localScale' + dimension, .2)

        # Create Range Sampler ---------------------------------------------------------------------------------
        range_sampler = driver + '_distanceRangeNode'
        if not cmds.objExists(range_sampler):
            distance_range = cmds.distanceDimension(endPoint=(pos_end[0] + 1, pos_end[1], pos_end[2]),
                                                    startPoint=(pos_start[0] + 1, pos_start[1], pos_start[2]))
            loc_range_start = cmds.listConnections(distance_range + '.startPoint')[0]
            loc_range_end = cmds.listConnections(distance_range + '.endPoint')[0]
            loc_range_start = cmds.rename(loc_range_start, driver + '_startRangeLoc')
            loc_range_end = cmds.rename(loc_range_end, driver + '_endRangeLoc')
            cmds.delete(cmds.parentConstraint(loc_start, loc_range_start))
            cmds.delete(cmds.parentConstraint(loc_end, loc_range_end))
            distance_range_node = cmds.rename(distance_range, range_sampler)
            distance_range_transform = cmds.listRelatives(distance_range_node, parent=True)[0]
            distance_range_transform = cmds.rename(distance_range_transform, range_sampler.replace('Node', 'Transform'))
            cmds.parent(distance_range_transform, general_automation_grp)
            cmds.parent(loc_range_start, main_driver_parent)
            cmds.parent(loc_range_end, main_driver_parent)
            cmds.setAttr(loc_range_start + '.v', 0)
            cmds.setAttr(loc_range_end + '.v', 0)
            cmds.makeIdentity(loc_range_start, translate=True, rotate=True, scale=True, apply=True)
            cmds.makeIdentity(loc_range_end, translate=True, rotate=True, scale=True, apply=True)
            change_outliner_color(distance_range_transform, (.7, .3, .3))
            cmds.setAttr(distance_range_transform + '.overrideEnabled', 1)
            cmds.setAttr(distance_range_transform + '.overrideDisplayType', 1)

            for dimension in ['X', 'Y', 'Z']:
                for locator in [loc_range_start, loc_range_end]:
                    cmds.setAttr(locator + '.localScale' + dimension, .4)
                    change_viewport_color(locator, (1, 1, 0))

        # Setup Control Attributes
        separator_attr = 'poseSystemAttributes'
        user_defined_attributes = cmds.listAttr(driver, userDefined=True) or []
        if separator_attr not in user_defined_attributes:
            cmds.addAttr(driver, ln=separator_attr, at='enum', en='-------------:', keyable=True)
            cmds.setAttr(driver + '.' + separator_attr, lock=True)

        direction_tag = name.split('_')[-1]
        locator_visibility_attr = direction_tag + 'Targets'
        if locator_visibility_attr not in user_defined_attributes:
            cmds.addAttr(driver, ln=locator_visibility_attr, at='bool', k=True)
        if not cmds.isConnected(driver + '.' + locator_visibility_attr, target_loc + '.v'):
            cmds.connectAttr(driver + '.' + locator_visibility_attr, target_loc + '.v')
        if not cmds.listConnections(loc_end + '.v', destination=False):
            cmds.connectAttr(driver + '.' + locator_visibility_attr, loc_end + '.v')

        # Driven List Connections Start -----------------------------------------------------------------------------
        for driven in driven_list:
            default_trans_source_sum = driver + '_trans_sum'
            default_rot_source_sum = driver + '_rot_sum'
            default_sca_source_sum = driver + '_sca_sum'
            driven_parent = cmds.listRelatives(driven, parent=True)[0]
            driven_trans_source = cmds.listConnections(driven_parent + '.translate', destination=False,
                                                       plugs=False, skipConversionNodes=True) or []
            driven_rot_source = cmds.listConnections(driven_parent + '.rotate', destination=False,
                                                     plugs=False, skipConversionNodes=True) or []

            # Translation
            if not driven_trans_source:
                trans_sum_node = cmds.createNode('plusMinusAverage', name=default_trans_source_sum)
                cmds.connectAttr(trans_sum_node + '.output3D', driven_parent + '.translate')
            elif cmds.objectType(driven_trans_source[0]) != 'plusMinusAverage':
                trans_source = cmds.listConnections(driven_parent + '.translate', destination=False,
                                                    plugs=True, skipConversionNodes=True)[0]  # Pre-existing connection
                cmds.disconnectAttr(trans_source, driven_parent + '.translate')
                trans_sum_node = cmds.createNode('plusMinusAverage', name=default_rot_source_sum)
                cmds.connectAttr(trans_sum_node + '.output3D', driven_parent + '.translate')
                cmds.connectAttr(trans_source, trans_sum_node + '.input3D[0]')
            else:
                trans_sum_node = driven_trans_source[0]

            # Rotation
            if not driven_rot_source:
                rot_sum_node = cmds.createNode('plusMinusAverage', name=default_rot_source_sum)
                cmds.connectAttr(rot_sum_node + '.output3D', driven_parent + '.rotate')
            elif cmds.objectType(driven_trans_source[0]) != 'plusMinusAverage':
                rot_source = cmds.listConnections(driven_parent + '.rotate', destination=False,
                                                  plugs=True, skipConversionNodes=True)[0]  # Pre-existing connection
                cmds.disconnectAttr(rot_source, driven_parent + '.rotate')
                rot_sum_node = cmds.createNode('plusMinusAverage', name=default_rot_source_sum)
                cmds.connectAttr(rot_sum_node + '.output3D', driven_parent + '.rotate')
                cmds.connectAttr(rot_source, rot_sum_node + '.input3D[0]')
            else:
                rot_sum_node = driven_rot_source[0]

            # Send Data to Sum Nodes
            next_slot_trans = get_plus_minus_average_available_slot(trans_sum_node)
            next_slot_rot = get_plus_minus_average_available_slot(rot_sum_node)

            offset_range_node = cmds.createNode('remapValue', name=name + '_rangeOffset')
            multiply_node_trans = cmds.createNode('multiplyDivide', name=name + '_influenceMultiplyTrans')
            multiply_node_rot = cmds.createNode('multiplyDivide', name=name + '_influenceMultiplyRot')
            cmds.connectAttr(target_loc + '.translate', multiply_node_trans + '.input1')
            cmds.connectAttr(target_loc + '.rotate', multiply_node_rot + '.input1')
            cmds.connectAttr(distance_transform + '.distance', offset_range_node + '.inputValue')

            cmds.setAttr(offset_range_node + '.inputMax', 0)
            cmds.connectAttr(range_sampler + '.distance', offset_range_node + '.inputMin')
            cmds.setAttr(offset_range_node + '.outputMin', 0)
            cmds.setAttr(offset_range_node + '.outputMax', 1)

            cmds.connectAttr(offset_range_node + '.outValue', multiply_node_trans + '.input2X')
            cmds.connectAttr(offset_range_node + '.outValue', multiply_node_trans + '.input2Y')
            cmds.connectAttr(offset_range_node + '.outValue', multiply_node_trans + '.input2Z')
            cmds.connectAttr(offset_range_node + '.outValue', multiply_node_rot + '.input2X')
            cmds.connectAttr(offset_range_node + '.outValue', multiply_node_rot + '.input2Y')
            cmds.connectAttr(offset_range_node + '.outValue', multiply_node_rot + '.input2Z')

            cmds.connectAttr(multiply_node_trans + '.output', trans_sum_node + '.input3D[' + str(next_slot_trans) + ']')
            cmds.connectAttr(multiply_node_rot + '.output', rot_sum_node + '.input3D[' + str(next_slot_rot) + ']')

            # Scale
            is_scale_available = cmds.objExists(driven + '.jointScale')
            if is_scale_available:
                driven_joint = driven.replace('_ctrl', '_jnt')

                if cmds.objectType(driven_joint) != 'plusMinusAverage':
                    driven_sca_source = cmds.listConnections(driven_joint + '.scale', destination=True,
                                                             plugs=False, skipConversionNodes=True) or []
                else:
                    driven_sca_source = driven_joint

                if not driven_sca_source:
                    sca_sum_node = cmds.createNode('plusMinusAverage', name=default_sca_source_sum)
                    cmds.connectAttr(sca_sum_node + '.output3D', driven_joint + '.scale')
                elif cmds.objectType(driven_sca_source[0]) != 'plusMinusAverage':
                    sca_source = cmds.listConnections(driven_joint + '.scale', destination=False,
                                                      plugs=True, skipConversionNodes=True)[0]
                    cmds.disconnectAttr(sca_source, driven_joint + '.scale')
                    sca_sum_node = cmds.createNode('plusMinusAverage', name=default_sca_source_sum)
                    cmds.connectAttr(sca_sum_node + '.output3D', driven_joint + '.scale')
                    cmds.connectAttr(sca_source, sca_sum_node + '.input3D[0]')
                else:
                    sca_sum_node = driven_sca_source[0]

                clean_driven = remove_strings_from_string(driven, ['_ctrl', 'right_', 'left_'])
                multiply_node_sca = name + '_' + clean_driven + '_influenceMultiplySca'
                multiply_node_sca = cmds.createNode('multiplyDivide', name=multiply_node_sca)
                multiply_node_remove_default = name + '_' + clean_driven + '_reverseDefaultSca'
                multiply_node_remove_default = cmds.createNode('multiplyDivide', name=multiply_node_remove_default)
                multiply_node_sca_reverse = name + '_' + clean_driven + '_reverseSca'
                multiply_node_sca_reverse = cmds.createNode('multiplyDivide', name=multiply_node_sca_reverse)

                # cmds.connectAttr(driven + '.jointScale', multiply_node_sca_reverse + '.input1')
                cmds.setAttr(multiply_node_sca_reverse + '.input2X', -1)
                cmds.setAttr(multiply_node_sca_reverse + '.input2Y', -1)
                cmds.setAttr(multiply_node_sca_reverse + '.input2Z', -1)
                cmds.setAttr(multiply_node_sca_reverse + '.input1X', 1)
                cmds.setAttr(multiply_node_sca_reverse + '.input1Y', 1)
                cmds.setAttr(multiply_node_sca_reverse + '.input1Z', 1)

                # cmds.connectAttr(target_loc + '.scale', multiply_node_remove_default + '.input1')
                cmds.connectAttr(multiply_node_sca_reverse + '.output', multiply_node_remove_default + '.input1')
                cmds.connectAttr(target_loc + '.scale', multiply_node_sca + '.input1')

                cmds.connectAttr(offset_range_node + '.outValue', multiply_node_remove_default + '.input2X')
                cmds.connectAttr(offset_range_node + '.outValue', multiply_node_remove_default + '.input2Y')
                cmds.connectAttr(offset_range_node + '.outValue', multiply_node_remove_default + '.input2Z')

                cmds.connectAttr(offset_range_node + '.outValue', multiply_node_sca + '.input2X')
                cmds.connectAttr(offset_range_node + '.outValue', multiply_node_sca + '.input2Y')
                cmds.connectAttr(offset_range_node + '.outValue', multiply_node_sca + '.input2Z')
                next_slot_sca = get_plus_minus_average_available_slot(sca_sum_node)
                cmds.connectAttr(multiply_node_sca + '.output', sca_sum_node + '.input3D[' + str(next_slot_sca) + ']')
                next_slot_sca = get_plus_minus_average_available_slot(sca_sum_node)
                cmds.connectAttr(multiply_node_remove_default + '.output',
                                 sca_sum_node + '.input3D[' + str(next_slot_sca) + ']')

        # Driven List Connections End -----------------------------------------------------------------------------

        # Set Initial Locator Position (Pose)
        if len(driven_offset):
            cmds.setAttr(target_loc + '.tx', driven_offset[0])
            cmds.setAttr(target_loc + '.ty', driven_offset[1])
            cmds.setAttr(target_loc + '.tz', driven_offset[2])
            if side == "right":
                cmds.setAttr(target_loc + '.tx', -driven_offset[0])
                cmds.setAttr(target_loc + '.ty', -driven_offset[1])
                cmds.setAttr(target_loc + '.tz', -driven_offset[2])
        if len(driven_offset) > 3:
            cmds.setAttr(target_loc + '.rx', driven_offset[3])
            cmds.setAttr(target_loc + '.ry', driven_offset[4])
            cmds.setAttr(target_loc + '.rz', driven_offset[5])
        if len(driven_offset) > 6:
            cmds.setAttr(target_loc + '.sx', driven_offset[6])
            cmds.setAttr(target_loc + '.sy', driven_offset[7])
            cmds.setAttr(target_loc + '.sz', driven_offset[8])

    # TODO END ------------------------------------------------------------------------------------------------------

    # Visibility Adjustments
    cmds.setAttr(_facial_joints_dict.get('head_jnt') + ".drawStyle", 2)

    # Store Proxy as String Attribute
    store_proxy_as_string(head_ctrl, 'facial_proxy_pose', facial_data)

    # Delete Proxy
    if cmds.objExists(_facial_proxy_dict.get('main_proxy_grp')):
        cmds.delete(_facial_proxy_dict.get('main_proxy_grp'))

    # ------------------------------------- Debugging -------------------------------------
    if facial_data.debugging:
        try:
            pass

            cmds.setAttr("head_ctrl.showOffsetCtrl", 1)

        except Exception as e:
            print(e)


def merge_facial_elements():
    necessary_elements = []
    facial_rig_grp = 'facial_rig_grp'
    skeleton_grp = 'skeleton_grp'
    rig_setup_grp = 'rig_setup_grp'
    necessary_elements.append(facial_rig_grp)
    necessary_elements.append(skeleton_grp)
    necessary_elements.append(rig_setup_grp)
    for obj in necessary_elements:
        if not cmds.objExists(obj):
            cmds.warning(f'Missing a require element. "{obj}"')
            return

    facial_joints = cmds.listRelatives('facial_skeleton_grp', children=True)
    facial_rig_setup_grps = cmds.listRelatives('facial_rig_setup_grp', children=True)
    rig_setup_scale_constraints = cmds.listRelatives(rig_setup_grp, children=True, type='scaleConstraint')

    for jnt in facial_joints:
        cmds.parent(jnt, skeleton_grp)
    for grp in facial_rig_setup_grps:
        cmds.parent(grp, rig_setup_grp)
    for constraint in rig_setup_scale_constraints:
        cmds.reorder(constraint, back=True)  # Keeps constraint at the bottom

    cmds.delete(facial_rig_grp)


if __name__ == '__main__':
    data_facial = GTBipedRiggerFacialData()
    data_facial.debugging = False
    debugging = data_facial.debugging
    # Camera Debugging -------------------------------------------------------------------------------------------
    if data_facial.debugging:
        # Get/Set Camera Pos/Rot
        persp_pos = cmds.getAttr('persp.translate')[0]
        persp_rot = cmds.getAttr('persp.rotate')[0]
        import gt_maya_utilities

        gt_maya_utilities.gtu_reload_file()
        cmds.viewFit(all=True)
        cmds.setAttr('persp.tx', persp_pos[0])
        cmds.setAttr('persp.ty', persp_pos[1])
        cmds.setAttr('persp.tz', persp_pos[2])
        cmds.setAttr('persp.rx', persp_rot[0])
        cmds.setAttr('persp.ry', persp_rot[1])
        cmds.setAttr('persp.rz', persp_rot[2])

    # Core Functions ---------------------------------------------------------------------------------------------

    create_facial_proxy(data_facial)
    create_facial_controls(data_facial)
    merge_facial_elements()

    # Bind Debugging ---------------------------------------------------------------------------------------------
    if data_facial.debugging:
        pass
        cmds.select(['root_jnt'], hierarchy=True)
        selection = cmds.ls(selection=True)
        cmds.skinCluster(selection, 'body_geo', bindMethod=1, toSelectedBones=True, smoothWeights=0.5,
                         maximumInfluences=4)

        from ngSkinTools2 import api as ng_tools_api
        from ngSkinTools2.api import InfluenceMappingConfig, VertexTransferMode

        config = InfluenceMappingConfig()
        config.use_distance_matching = True
        config.use_name_matching = True

        source_file_name = 'C:\\body.json'

        # Import Skin Weights
        ng_tools_api.import_json(
            "body_geo",
            file=source_file_name,
            vertex_transfer_mode=VertexTransferMode.vertexId,
            # vertex_transfer_mode=ng_tools_api.VertexTransferMode.closestPoint,
            influences_mapping_config=config,
        )
