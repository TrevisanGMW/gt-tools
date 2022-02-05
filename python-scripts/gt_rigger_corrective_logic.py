"""
 GT Corrective Rigger
 Creates joints for the knees, wrists and shoulders to be used as correctives
 github.com/TrevisanGMW - 2022-01-10

"""
from collections import namedtuple
from gt_rigger_utilities import *
from gt_rigger_data import *
from gt_plane_angle_calculator import *
import maya.cmds as cmds
import random

# Script Name
script_name = 'GT Corrective Rigger'

# Version:
script_version = '0.2'

# General Vars
debugging = True
PROXY_COLOR = (1, 0, 1)
PROXY_DRIVEN_COLOR = (1, .5, 1)

# Loaded Elements Dictionary
_corrective_proxy_dict = {  # Pre Existing Elements
    'main_proxy_grp': 'auto_corrective_proxy' + '_' + GRP_SUFFIX,
    'main_root': 'auto_corrective_proxy' + '_' + PROXY_SUFFIX,
    #
    # # Center Elements
    # 'head_crv': 'headRoot' + '_' + PROXY_SUFFIX,
    # 'jaw_crv': 'jawRoot' + '_' + PROXY_SUFFIX,
    # 'left_eye_crv': 'eyeRoot_' + PROXY_SUFFIX,

    # Wrists
    'left_main_wrist_crv': 'mainWrist_' + PROXY_SUFFIX,
    'left_upper_wrist_crv': 'upperWrist_' + PROXY_SUFFIX,
    'left_lower_wrist_crv': 'lowerWrist_' + PROXY_SUFFIX,

    # Knees
    'left_main_knee_crv': 'mainKnee_' + PROXY_SUFFIX,
    'left_back_knee_crv': 'backKnee_' + PROXY_SUFFIX,
    'left_front_knee_crv': 'frontKnee_' + PROXY_SUFFIX,

    # # Eyebrows
    # 'left_inner_brow_crv': 'innerBrow_' + PROXY_SUFFIX,
    # 'left_mid_brow_crv': 'midBrow_' + PROXY_SUFFIX,
    # 'left_outer_brow_crv': 'outerBrow_' + PROXY_SUFFIX,
    #
    # # Mouth
    # 'mid_upper_lip_crv': 'mid_upperLip_' + PROXY_SUFFIX,
    # 'mid_lower_lip_crv': 'mid_lowerLip_' + PROXY_SUFFIX,
    # 'left_upper_outer_lip_crv': 'upperOuterLip_' + PROXY_SUFFIX,
    # 'left_lower_outer_lip_crv': 'lowerOuterLip_' + PROXY_SUFFIX,
    # 'left_corner_lip_crv': 'cornerLip_' + PROXY_SUFFIX,
}

_preexisting_dict = {'left_wrist_jnt': 'left_wrist_jnt',
                     'right_wrist_jnt': 'right_wrist_jnt',
                     'left_knee_jnt': 'left_knee_jnt',
                     'right_knee_jnt': 'right_knee_jnt',
                     'left_forearm_jnt': 'left_forearm_jnt',
                     'right_forearm_jnt': 'right_forearm_jnt',
                     'left_wrist_aimJnt': 'left_wrist_aimJnt',
                     'right_wrist_aimJnt': 'right_wrist_aimJnt'
                     }

# Auto Populate Control Names (Copy from Left to Right) + Add prefixes
for item in list(_corrective_proxy_dict):
    if item.startswith('left_'):
        _corrective_proxy_dict[item] = 'left_' + _corrective_proxy_dict.get(item)  # Add "left_" prefix
        _corrective_proxy_dict[item.replace('left_', 'right_')] = \
            _corrective_proxy_dict.get(item).replace('left_', 'right_')


def create_corrective_proxy():
    """ Creates a proxy (guide) skeleton used to later generate setup """
    # Main
    main_proxies = []
    main_grp = cmds.group(empty=True, world=True, name=_corrective_proxy_dict.get('main_proxy_grp'))
    main_root_a = cmds.curve(p=[[-8.0, 0.0, 37.0], [-11.707, 0.0, 36.483], [-14.701, 0.0, 35.305],
                                [-17.886, 0.0, 33.69], [-19.313, 0.0, 32.876], [-23.408, 0.0, 30.311],
                                [-28.717, 0.0, 25.982], [-34.84, 0.0, 16.747], [-37.396, 0.0, 8.698],
                                [-38.244, 0.0, 1.548], [-38.098, 0.0, -4.119], [-36.945, 0.0, -10.08],
                                [-35.815, 0.0, -13.515], [-34.083, 0.0, -17.628], [-31.943, 0.0, -21.218],
                                [-27.222, 0.0, -27.046], [-21.139, 0.0, -32.357], [-12.707, 0.0, -36.213],
                                [-5.456, 0.0, -37.811], [1.802, 0.0, -38.358], [10.995, 0.0, -36.987],
                                [21.154, 0.0, -32.356], [27.216, 0.0, -27.046], [31.947, 0.0, -21.218],
                                [34.081, 0.0, -17.629], [35.815, 0.0, -13.515], [36.945, 0.0, -10.08],
                                [38.098, 0.0, -4.118], [38.245, 0.0, 1.547], [37.395, 0.0, 8.7],
                                [34.845, 0.0, 16.742], [29.22, 0.0, 25.22], [24.224, 0.0, 29.641],
                                [20.359, 0.0, 32.26], [18.087, 0.0, 33.59], [14.714, 0.0, 35.297],
                                [11.699, 0.0, 36.488], [8.0, 0.0, 37.0]], d=3)

    main_root_b = cmds.curve(p=[[-8.0, 0.0, 37.0], [-8.0, 0.0, 62.709], [-14.467, 0.0, 62.709],
                                [0.0, 0.0, 77.176], [14.467, 0.0, 62.709], [8.0, 0.0, 62.709],
                                [8.0, 0.0, 37.0]], d=1)
    main_root = combine_curves_list([main_root_a, main_root_b])
    main_root = cmds.rename(main_root, _corrective_proxy_dict.get('main_root'))
    change_viewport_color(main_root, (.171, .033, .787))
    cmds.parent(main_root, main_grp)
    for shape in cmds.listRelatives(main_root, s=True, f=True) or []:
        cmds.setAttr(shape + '.lineWidth', 3)

    # ### Left Wrist ###
    left_main_wrist_proxy_crv = create_joint_curve(_corrective_proxy_dict.get('left_main_wrist_crv'), .5)
    left_main_wrist_proxy_grp = cmds.group(empty=True, world=True,
                                           name=left_main_wrist_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_main_wrist_proxy_crv, left_main_wrist_proxy_grp)
    cmds.move(58.2, 130.4, 0, left_main_wrist_proxy_grp)
    cmds.rotate(-90, left_main_wrist_proxy_grp, rotateX=True)
    cmds.parent(left_main_wrist_proxy_grp, main_root)
    change_viewport_color(left_main_wrist_proxy_crv, PROXY_COLOR)
    main_proxies.append(left_main_wrist_proxy_crv)

    # Left Upper Wrist
    left_upper_wrist_proxy_crv = create_directional_joint_curve(_corrective_proxy_dict.get('left_upper_wrist_crv'), .2)
    left_upper_wrist_proxy_grp = cmds.group(empty=True, world=True,
                                            name=left_upper_wrist_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_upper_wrist_proxy_crv, left_upper_wrist_proxy_grp)
    cmds.move(58.2, 131.615, 0, left_upper_wrist_proxy_grp)
    cmds.parent(left_upper_wrist_proxy_grp, left_main_wrist_proxy_crv)
    change_viewport_color(left_upper_wrist_proxy_crv, PROXY_DRIVEN_COLOR)

    # Left Lower Wrist
    left_lower_wrist_proxy_crv = create_directional_joint_curve(_corrective_proxy_dict.get('left_lower_wrist_crv'), .2)
    left_lower_wrist_proxy_grp = cmds.group(empty=True, world=True,
                                            name=left_lower_wrist_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_lower_wrist_proxy_crv, left_lower_wrist_proxy_grp)
    cmds.move(58.2, 129.196, 0, left_lower_wrist_proxy_grp)
    cmds.rotate(-180, left_lower_wrist_proxy_grp, rotateZ=True)
    cmds.parent(left_lower_wrist_proxy_grp, left_main_wrist_proxy_crv)
    change_viewport_color(left_lower_wrist_proxy_crv, PROXY_DRIVEN_COLOR)

    # ### Right Wrist ###
    right_main_wrist_proxy_crv = create_joint_curve(_corrective_proxy_dict.get('right_main_wrist_crv'), .5)
    right_main_wrist_proxy_grp = cmds.group(empty=True, world=True,
                                            name=right_main_wrist_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_main_wrist_proxy_crv, right_main_wrist_proxy_grp)
    cmds.move(-58.2, 130.4, 0, right_main_wrist_proxy_grp)
    cmds.rotate(90, right_main_wrist_proxy_grp, rotateX=True)
    cmds.rotate(180, right_main_wrist_proxy_grp, rotateY=True)
    cmds.parent(right_main_wrist_proxy_grp, main_root)
    change_viewport_color(right_main_wrist_proxy_crv, PROXY_COLOR)
    main_proxies.append(right_main_wrist_proxy_crv)

    # Right Upper Wrist
    right_upper_wrist_proxy_crv = create_directional_joint_curve(_corrective_proxy_dict.get('right_upper_wrist_crv'),
                                                                 .2)
    right_upper_wrist_proxy_grp = cmds.group(empty=True, world=True,
                                             name=right_upper_wrist_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_upper_wrist_proxy_crv, right_upper_wrist_proxy_grp)
    cmds.move(-58.2, 131.615, 0, right_upper_wrist_proxy_grp)
    cmds.parent(right_upper_wrist_proxy_grp, right_main_wrist_proxy_crv)
    change_viewport_color(right_upper_wrist_proxy_crv, PROXY_DRIVEN_COLOR)

    # Right Lower Wrist
    right_lower_wrist_proxy_crv = create_directional_joint_curve(_corrective_proxy_dict.get('right_lower_wrist_crv'),
                                                                 .2)
    right_lower_wrist_proxy_grp = cmds.group(empty=True, world=True,
                                             name=right_lower_wrist_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_lower_wrist_proxy_crv, right_lower_wrist_proxy_grp)
    cmds.move(-58.2, 129.196, 0, right_lower_wrist_proxy_grp)
    cmds.rotate(-180, right_lower_wrist_proxy_grp, rotateZ=True)
    cmds.parent(right_lower_wrist_proxy_grp, right_main_wrist_proxy_crv)
    change_viewport_color(right_lower_wrist_proxy_crv, PROXY_DRIVEN_COLOR)

    # ################ Knees ################
    # Left Main Knee
    left_main_knee_proxy_crv = create_joint_curve(_corrective_proxy_dict.get('left_main_knee_crv'), .2)
    left_main_knee_proxy_grp = cmds.group(empty=True, world=True,
                                          name=left_main_knee_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_main_knee_proxy_crv, left_main_knee_proxy_grp)
    cmds.move(10.2, 47.05, 0, left_main_knee_proxy_grp)
    cmds.rotate(90, left_main_knee_proxy_grp, rotateX=True)
    cmds.rotate(-90, left_main_knee_proxy_grp, rotateZ=True)
    cmds.parent(left_main_knee_proxy_grp, main_root)
    change_viewport_color(left_main_knee_proxy_crv, PROXY_COLOR)
    main_proxies.append(left_main_knee_proxy_crv)

    # Left Back Knee
    left_back_knee_proxy_crv = create_directional_joint_curve(_corrective_proxy_dict.get('left_back_knee_crv'), .2)
    left_back_knee_proxy_grp = cmds.group(empty=True, world=True,
                                             name=left_back_knee_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_back_knee_proxy_crv, left_back_knee_proxy_grp)
    cmds.move(10.2, 47.05, -4, left_back_knee_proxy_grp)
    cmds.rotate(-90, left_back_knee_proxy_grp, rotateX=True)
    cmds.parent(left_back_knee_proxy_grp, left_main_knee_proxy_crv)
    change_viewport_color(left_back_knee_proxy_crv, PROXY_DRIVEN_COLOR)

    # Left Front Knee
    left_front_knee_proxy_crv = create_directional_joint_curve(_corrective_proxy_dict.get('left_front_knee_crv'), .2)
    left_front_knee_proxy_grp = cmds.group(empty=True, world=True,
                                           name=left_front_knee_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_front_knee_proxy_crv, left_front_knee_proxy_grp)
    cmds.move(10.2, 47.05, 4, left_front_knee_proxy_grp)
    cmds.rotate(90, left_front_knee_proxy_grp, rotateX=True)
    cmds.parent(left_front_knee_proxy_grp, left_main_knee_proxy_crv)
    change_viewport_color(left_front_knee_proxy_crv, PROXY_DRIVEN_COLOR)

    # Right Main Knee
    right_main_knee_proxy_crv = create_joint_curve(_corrective_proxy_dict.get('right_main_knee_crv'), .2)
    right_main_knee_proxy_grp = cmds.group(empty=True, world=True,
                                           name=right_main_knee_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_main_knee_proxy_crv, right_main_knee_proxy_grp)
    cmds.move(-10.2, 47.05, 0, right_main_knee_proxy_grp)
    cmds.rotate(270, right_main_knee_proxy_grp, rotateX=True)
    cmds.rotate(90, right_main_knee_proxy_grp, rotateZ=True)
    cmds.parent(right_main_knee_proxy_grp, main_root)
    change_viewport_color(right_main_knee_proxy_crv, PROXY_COLOR)
    main_proxies.append(right_main_knee_proxy_crv)

    # Right Lower Knee
    right_back_knee_proxy_crv = create_directional_joint_curve(_corrective_proxy_dict.get('right_back_knee_crv'), .2)
    right_back_knee_proxy_grp = cmds.group(empty=True, world=True,
                                            name=right_back_knee_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_back_knee_proxy_crv, right_back_knee_proxy_grp)
    cmds.move(-10.2, 47.05, -4, right_back_knee_proxy_grp)
    cmds.rotate(-90, right_back_knee_proxy_grp, rotateX=True)
    cmds.parent(right_back_knee_proxy_grp, right_main_knee_proxy_crv)
    change_viewport_color(right_back_knee_proxy_crv, PROXY_DRIVEN_COLOR)

    # Right Front Knee
    right_front_knee_proxy_crv = create_directional_joint_curve(_corrective_proxy_dict.get('right_front_knee_crv'), .2)
    right_front_knee_proxy_grp = cmds.group(empty=True, world=True,
                                           name=right_front_knee_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_front_knee_proxy_crv, right_front_knee_proxy_grp)
    cmds.move(-10.2, 47.05, 4, right_front_knee_proxy_grp)
    cmds.rotate(90, right_front_knee_proxy_grp, rotateX=True)
    cmds.parent(right_front_knee_proxy_grp, right_main_knee_proxy_crv)
    change_viewport_color(right_front_knee_proxy_crv, PROXY_DRIVEN_COLOR)

    for key, data in _preexisting_dict.items():
        if cmds.objExists(data):
            side = 'left'
            if 'right' in data:
                side = 'right'

            if 'wrist' in data:
                cmds.delete(cmds.parentConstraint(data, _corrective_proxy_dict.get(side + '_main_wrist_crv')))

            if 'knee' in data:
                cmds.delete(cmds.parentConstraint(data, _corrective_proxy_dict.get(side + '_main_knee_crv')))

    # Improve Main Proxy Visibility
    for proxy in main_proxies:
        for shape in cmds.listRelatives(proxy, s=True, f=True) or []:
            cmds.setAttr(shape + '.lineWidth', 3)


def create_corrective_setup():
    """ Creates Corrective Rig Setup """

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
        new_name = old_name.replace(PROXY_SUFFIX, 'driver' + JNT_SUFFIX.capitalize())
        return new_name.replace('driverEnd' + PROXY_SUFFIX.capitalize(), 'driverEnd' + JNT_SUFFIX.capitalize())

    # Cancel operation if missing elements
    missing_objs = []
    for key, data in _preexisting_dict.items():
        if not cmds.objExists(data):
            missing_objs.append(data)

    if len(missing_objs) > 0:
        cmds.warning('Missing necessary joints. Check script editor for details.')
        print("#"*80)
        for obj in missing_objs:
            print('"' + obj + '" is missing.')
        print("#"*80)
        return False

    # Create Parent Groups
    corrective_prefix = 'corrective_'
    rig_grp = cmds.group(name=corrective_prefix + 'rig_grp', empty=True, world=True)
    change_outliner_color(rig_grp, (1, .45, .7))

    skeleton_grp = cmds.group(name=(corrective_prefix + 'skeleton_' + GRP_SUFFIX), empty=True, world=True)
    change_outliner_color(skeleton_grp, (.75, .45, .95))  # Purple (Like a joint)

    controls_grp = cmds.group(name=corrective_prefix + 'controls_' + GRP_SUFFIX, empty=True, world=True)
    change_outliner_color(controls_grp, (1, 0.47, 0.18))

    rig_setup_grp = cmds.group(name=corrective_prefix + 'rig_setup_' + GRP_SUFFIX, empty=True, world=True)
    change_outliner_color(rig_setup_grp, (1, .26, .26))

    automation_grp = cmds.group(name='correctiveAutomation_grp', world=True, empty=True)
    change_outliner_color(automation_grp, (1, .65, .45))

    cmds.parent(skeleton_grp, rig_grp)
    cmds.parent(controls_grp, rig_grp)
    cmds.parent(rig_setup_grp, rig_grp)
    cmds.parent(automation_grp, rig_setup_grp)
    cmds.setAttr(rig_setup_grp + '.v', 0)

    # Create Driver Joints
    _cor_joints_dict = {}
    ignore_crv_list = ['']
    for obj in _corrective_proxy_dict:
        if obj.endswith('_crv') and obj not in ignore_crv_list:
            cmds.select(d=True)
            joint = cmds.joint(name=rename_proxy(_corrective_proxy_dict.get(obj)), radius=.5)
            cmds.delete(cmds.parentConstraint(_corrective_proxy_dict.get(obj), joint))
            cmds.makeIdentity(joint, apply=True, rotate=True)
            _cor_joints_dict[obj.replace('_crv', '_' + JNT_SUFFIX).replace('_proxy', '')] = joint

    # Create Main Ctrl Attributes
    main_ctrl = 'main_ctrl'
    cmds.addAttr(main_ctrl, ln='correctiveControls', at='enum', en='-------------:', keyable=True)
    cmds.setAttr(main_ctrl + '.correctiveControls', lock=True)
    ctrl_visibility_attr = 'correctiveVisibility'
    cmds.addAttr(main_ctrl, ln=ctrl_visibility_attr, at='bool', k=True, niceName='Corrective Visibility')
    loc_visibility_attr = 'correctiveGoalLocVisibility'
    cmds.addAttr(main_ctrl, ln=loc_visibility_attr, at='bool', k=True, niceName='Goal Loc Visibility')

    # Setup Driver Joints
    # Wrists
    cmds.parent(_cor_joints_dict.get('left_upper_wrist_jnt'), _cor_joints_dict.get('left_main_wrist_jnt'))
    cmds.parent(_cor_joints_dict.get('left_lower_wrist_jnt'), _cor_joints_dict.get('left_main_wrist_jnt'))
    cmds.parentConstraint(_preexisting_dict.get('left_wrist_jnt'), _cor_joints_dict.get('left_main_wrist_jnt'))

    cmds.parent(_cor_joints_dict.get('right_upper_wrist_jnt'), _cor_joints_dict.get('right_main_wrist_jnt'))
    cmds.parent(_cor_joints_dict.get('right_lower_wrist_jnt'), _cor_joints_dict.get('right_main_wrist_jnt'))
    cmds.parentConstraint(_preexisting_dict.get('right_wrist_jnt'), _cor_joints_dict.get('right_main_wrist_jnt'))

    # Knees
    cmds.parent(_cor_joints_dict.get('left_back_knee_jnt'), _cor_joints_dict.get('left_main_knee_jnt'))
    cmds.parent(_cor_joints_dict.get('left_front_knee_jnt'), _cor_joints_dict.get('left_main_knee_jnt'))
    cmds.parentConstraint(_preexisting_dict.get('left_knee_jnt'), _cor_joints_dict.get('left_main_knee_jnt'))

    cmds.parent(_cor_joints_dict.get('right_back_knee_jnt'), _cor_joints_dict.get('right_main_knee_jnt'))
    cmds.parent(_cor_joints_dict.get('right_front_knee_jnt'), _cor_joints_dict.get('right_main_knee_jnt'))
    cmds.parentConstraint(_preexisting_dict.get('right_knee_jnt'), _cor_joints_dict.get('right_main_knee_jnt'))



    # Wrist Accessories
    left_wrist_main_outfit_jnt = cmds.duplicate(_preexisting_dict.get('left_forearm_jnt'),
                                     name='left_wrist_mainOutfit_driverJnt', po=True)[0]
    right_wrist_main_outfit_jnt = cmds.duplicate(_preexisting_dict.get('right_forearm_jnt'),
                                      name='right_wrist_mainOutfit_driverJnt', po=True)[0]
    cmds.parent(left_wrist_main_outfit_jnt, world=True)
    cmds.parent(right_wrist_main_outfit_jnt, world=True)
    cmds.delete(cmds.pointConstraint(_preexisting_dict.get('left_wrist_jnt'), left_wrist_main_outfit_jnt))
    cmds.delete(cmds.pointConstraint(_preexisting_dict.get('right_wrist_jnt'), right_wrist_main_outfit_jnt))
    cmds.parentConstraint(_preexisting_dict.get('left_wrist_aimJnt'), left_wrist_main_outfit_jnt, mo=True)
    cmds.parentConstraint(_preexisting_dict.get('right_wrist_aimJnt'), right_wrist_main_outfit_jnt, mo=True)

    cmds.setAttr(left_wrist_main_outfit_jnt + '.radius', 0.5)
    cmds.setAttr(right_wrist_main_outfit_jnt + '.radius', 0.5)

    left_wrist_outfit_jnt = cmds.duplicate(left_wrist_main_outfit_jnt,
                                                name='left_wrist_outfit_driverJnt', po=True)[0]
    right_wrist_outfit_jnt = cmds.duplicate(right_wrist_main_outfit_jnt,
                                                 name='right_wrist_outfit_driverJnt', po=True)[0]
    cmds.parent(left_wrist_outfit_jnt, left_wrist_main_outfit_jnt)
    cmds.parent(right_wrist_outfit_jnt, right_wrist_main_outfit_jnt)

    # Basic Organization
    cmds.parent(_cor_joints_dict.get('left_main_wrist_jnt'), skeleton_grp)
    cmds.parent(_cor_joints_dict.get('right_main_wrist_jnt'), skeleton_grp)
    cmds.parent(_cor_joints_dict.get('left_main_knee_jnt'), skeleton_grp)
    cmds.parent(_cor_joints_dict.get('right_main_knee_jnt'), skeleton_grp)
    cmds.parent(left_wrist_main_outfit_jnt, skeleton_grp)
    cmds.parent(right_wrist_main_outfit_jnt, skeleton_grp)

    # Left Wrist Setup
    Pose = namedtuple('Pose', ['name',
                               'driver',
                               'driver_bound',
                               'driver_range',
                               'driven',
                               'driven_offset',
                               'setup'])
    poses = [
            # Wrist Left
            Pose(name='upperWristExtension',
                 driver='left_mainWrist_driverJnt',
                 driver_bound='left_wrist_jnt',
                 driver_range=[0, -150],
                 driven='left_upperWrist_driverJnt',
                 driven_offset=[5.61, 0.0, 6.32, 0.0, 17, 0.0, 0.42, 1.0, 1.0],  # TRS e.g. [T, T, T, R, R, R, S, S, S]
                 setup='upper_wrist'),

            Pose(name='upperWristFlexion',
                 driver='left_mainWrist_driverJnt',
                 driver_bound='left_wrist_jnt',
                 driver_range=[0, 110],
                 driven='left_upperWrist_driverJnt',
                 driven_offset=[-0.13, 0.0, -2.08, 0.0, -32.51, 0.0, 1.0, 1.0, 1.0],
                 setup='upper_wrist'),

            Pose(name='lowerWristExtension',
                 driver='left_mainWrist_driverJnt',
                 driver_bound='left_wrist_jnt',
                 driver_range=[0, 110],
                 driven='left_lowerWrist_driverJnt',
                 driven_offset=[4.0, 0.0, -5.2, 0.0, -15.0, 0.0, 0.01, 1.8, 1.0],
                 setup='lower_wrist'),

            Pose(name='lowerWristFlexion',
                 driver='left_mainWrist_driverJnt',
                 driver_bound='left_wrist_jnt',
                 driver_range=[0, -150],
                 driven='left_lowerWrist_driverJnt',
                 driven_offset=[-0.2, 0.2, 0.21, 0.0, 122.72, 0.0, 1.0, 1.0, 1.0],
                 setup='lower_wrist'),

            # Wrist Right
            Pose(name='upperWristExtension',
                 driver='right_mainWrist_driverJnt',
                 driver_bound='right_wrist_jnt',
                 driver_range=[0, -150],
                 driven='right_upperWrist_driverJnt',
                 driven_offset=[-5.61, -0.0, -6.32, 0.0, 16.98, 0.0, 0.42, 1.0, 1.0],
                 setup='upper_wrist'),

            Pose(name='upperWristFlexion',
                 driver='right_mainWrist_driverJnt',
                 driver_bound='right_wrist_jnt',
                 driver_range=[0, 110],
                 driven='right_upperWrist_driverJnt',
                 driven_offset=[0.13, 0.0, 2.08, 0.0, -32.51, 0.0, 1.0, 1.0, 1.0],
                 setup='upper_wrist'),

            Pose(name='lowerWristExtension',
                 driver='right_mainWrist_driverJnt',
                 driver_bound='right_wrist_jnt',
                 driver_range=[0, 110],
                 driven='right_lowerWrist_driverJnt',
                 driven_offset=[-4.0, 0.0, 5.2, 0.0, -15.0, 0.0, 0.01, 1.8, 1.0],
                 setup='lower_wrist'),

            Pose(name='lowerWristFlexion',
                 driver='right_mainWrist_driverJnt',
                 driver_bound='right_wrist_jnt',
                 driver_range=[0, -150],
                 driven='right_lowerWrist_driverJnt',
                 driven_offset=[0.2, -0.2, -0.21, 0.0, 122.72, 0.0, 1.0, 1.0, 1.0],
                 setup='lower_wrist'),

            # Knee Left ------------------
            Pose(name='kneeFlexion',
                 driver='left_mainKnee_driverJnt',
                 driver_bound='left_knee_jnt',
                 driver_range=[0, -93],
                 driven='left_backKnee_driverJnt',
                 driven_offset=[9.469, -15.484, 0, 0, 0, 40, 0.005, 1, 1],
                 setup='back_knee'),

            # Knee Right
            Pose(name='kneeFlexion',
                 driver='right_mainKnee_driverJnt',
                 driver_bound='right_knee_jnt',
                 driver_range=[0, -93],
                 driven='right_backKnee_driverJnt',
                 driven_offset=[-9.469, 15.484, 0, 0, 0, 40, 0.005, 1, 1],
                 setup='back_knee'),

            Pose(name='kneeFlexion',
                 driver='left_mainKnee_driverJnt',
                 driver_bound='left_knee_jnt',
                 driver_range=[0, -93],
                 driven='left_frontKnee_driverJnt',
                 driven_offset=[0, 4, 0],
                 setup='back_knee'),

            # Knee Right
            Pose(name='kneeFlexion',
                 driver='right_mainKnee_driverJnt',
                 driver_bound='right_knee_jnt',
                 driver_range=[0, -93],
                 driven='right_frontKnee_driverJnt',
                 driven_offset=[0, -4, 0],
                 setup='back_knee'),

            # Outfit Correctives ------------------
            Pose(name='outfitExtension',
                 driver='left_wrist_mainOutfit_driverJnt',
                 driver_bound='left_wrist_jnt',
                 driver_range=[0, -100],
                 driven='left_wrist_outfit_driverJnt',
                 driven_offset=[-0.92, 0.27, 1.28, 0.0, 24.26, 0.0, 1.0, 1.0, 1.0],
                 setup='outfit_wrist'),

            Pose(name='outfitFlexion',
                 driver='left_wrist_mainOutfit_driverJnt',
                 driver_bound='left_wrist_jnt',
                 driver_range=[0, 75],
                 driven='left_wrist_outfit_driverJnt',
                 driven_offset=[-0.29, -0.0, -0.24, 0.0, -21.31, 0.0, 1.0, 1.0, 1.0],
                 setup='outfit_wrist'),

            Pose(name='outfitExtension',
                 driver='right_wrist_mainOutfit_driverJnt',
                 driver_bound='right_wrist_jnt',
                 driver_range=[0, -100],
                 driven='right_wrist_outfit_driverJnt',
                 driven_offset=[1.37, 0.03, -0.98, 0.0, -14.99, 0.0, 1.0, 1.0, 1.0],
                 setup='outfit_wrist'),

            Pose(name='outfitFlexion',
                 driver='right_wrist_mainOutfit_driverJnt',
                 driver_bound='right_wrist_jnt',
                 driver_range=[0, 75],
                 driven='right_wrist_outfit_driverJnt',
                 driven_offset=[0.98, -0.0, 0.01, 0.0, 18.5, 0.0, 1.0, 1.0, 1.0],
                 setup='outfit_wrist'),

    ]

    corrective_ctrls = []
    # ################################# Pose Assembly #################################
    for pose in poses:
        # Unpack
        name = pose.name
        driver = pose.driver  # Driver
        driver_bound = pose.driver_bound
        driver_range = pose.driver_range
        driven = pose.driven  # Driven
        driven_offset = pose.driven_offset
        setup = pose.setup

        # Determine Side
        side = 'left'
        if driver.startswith('right'):
            side = 'right'

        # Clean Rot Setup
        rot_angle_parent = driver_bound.replace('_' + JNT_SUFFIX, '_upAim' + JNT_SUFFIX.capitalize())
        rot_angle_child = rot_angle_parent.replace('upAim', 'dirAim')
        if not cmds.objExists(rot_angle_parent):
            dir_value = 1
            if side == 'right':
                dir_value = -1
            if setup.endswith('wrist'):
                twist_aim_jnt = side + '_wrist_aimJnt'
                cmds.duplicate(twist_aim_jnt, name=rot_angle_parent, parentOnly=True)
                cmds.delete(cmds.pointConstraint(twist_aim_jnt, rot_angle_parent))
                dir_jnt = cmds.duplicate(rot_angle_parent,
                                         name=rot_angle_child,
                                         parentOnly=True)[0]
                cmds.parent(dir_jnt, rot_angle_parent)
                cmds.parent(rot_angle_parent, twist_aim_jnt)

                cmds.setAttr(dir_jnt + '.ty', dir_value*.5)
                dir_loc = cmds.spaceLocator(name=rot_angle_parent.replace(JNT_SUFFIX.capitalize(), 'Loc'))[0]
                change_viewport_color(dir_loc, (1, 0, 1))
                change_viewport_color(rot_angle_parent, (1, 1, 1))
                change_viewport_color(dir_jnt, (1, 1, 1))

                cmds.delete(cmds.parentConstraint(dir_jnt, dir_loc))
                cmds.move(-dir_value, dir_loc, moveZ=True, relative=True, objectSpace=True)
                cmds.parentConstraint(driver_bound, dir_loc, mo=True)
                cmds.aimConstraint(rot_angle_parent, dir_jnt,
                                   aimVector=(0, dir_value*-1, 0),
                                   upVector=(0, 0, dir_value*-1),
                                   worldUpType="object",
                                   worldUpObject=dir_loc)
                cmds.setAttr(dir_jnt + '.rotateOrder', 2)  # ZXY
                new_radius = cmds.getAttr(rot_angle_parent + '.radius') * .5
                cmds.setAttr(rot_angle_parent + '.radius', new_radius)
                cmds.setAttr(dir_jnt + '.radius', new_radius * .5)
                cmds.parent(dir_loc, automation_grp)
            if setup.endswith('knee'):
                twist_aim_jnt = side + '_knee_jnt'
                cmds.duplicate(twist_aim_jnt, name=rot_angle_parent, parentOnly=True)
                cmds.delete(cmds.pointConstraint(twist_aim_jnt, rot_angle_parent))
                dir_jnt = cmds.duplicate(rot_angle_parent,
                                         name=rot_angle_child,
                                         parentOnly=True)[0]
                for dimension in ['x', 'y', 'z']:
                    cmds.setAttr(rot_angle_parent + '.r' + dimension, 0)
                    cmds.setAttr(dir_jnt + '.r' + dimension, 0)
                cmds.parent(dir_jnt, rot_angle_parent)
                cmds.parent(rot_angle_parent, twist_aim_jnt)
                cmds.setAttr(dir_jnt + '.tz', dir_value * .5)
                dir_loc = cmds.spaceLocator(name=rot_angle_parent.replace(JNT_SUFFIX.capitalize(), 'Loc'))[0]
                change_viewport_color(dir_loc, (1, 0, 1))
                change_viewport_color(rot_angle_parent, (1, 1, 1))
                change_viewport_color(dir_jnt, (1, 1, 1))

                cmds.delete(cmds.parentConstraint(dir_jnt, dir_loc))
                cmds.move(-dir_value, dir_loc, moveY=True, relative=True, objectSpace=True)
                cmds.parentConstraint(driver_bound, dir_loc, mo=True)
                cmds.aimConstraint(rot_angle_parent, dir_jnt,
                                   aimVector=(0, 0, dir_value * -1),
                                   upVector=(0, dir_value * -1, 0),
                                   worldUpType="object",
                                   worldUpObject=dir_loc)
                # cmds.setAttr(dir_jnt + '.rotateOrder', 2)  # ZXY
                new_radius = cmds.getAttr(rot_angle_parent + '.radius') * .5
                cmds.setAttr(rot_angle_parent + '.radius', new_radius)
                cmds.setAttr(dir_jnt + '.radius', new_radius * .5)
                cmds.parent(dir_loc, automation_grp)
                cmds.parent(rot_angle_parent, skeleton_grp)
                cmds.parentConstraint(side + '_hip_' + JNT_SUFFIX, rot_angle_parent, mo=True)

        # Visibility Setup
        cmds.setAttr(driver + '.drawStyle', 2)
        cmds.setAttr(driven + '.drawStyle', 2)

        # ##### Corrective Posing #####
        # Basic Variables and Elements
        driven_prefix = driven.replace('_' + JNT_SUFFIX, '')
        ctrl = driven_prefix + '_' + CTRL_SUFFIX
        ctrl_grp = ctrl + GRP_SUFFIX.capitalize()
        offset_grp = ctrl + 'Offset' + GRP_SUFFIX.capitalize()
        if not cmds.objExists(ctrl):
            ctrl = create_joint_curve(ctrl, .5)
            change_viewport_color(ctrl, (1, 0, 0))
            ctrl_grp = cmds.group(name=ctrl_grp, world=True, empty=True)
            offset_grp = cmds.group(name=offset_grp, world=True, empty=True)
            cmds.parent(offset_grp, ctrl_grp)
            cmds.parent(ctrl, offset_grp)
            cmds.delete(cmds.parentConstraint(driven, ctrl_grp))
            cmds.parentConstraint(driven, offset_grp)
            cmds.scaleConstraint(driven, offset_grp)
            cmds.parent(ctrl_grp, controls_grp)
            corrective_ctrls.append(ctrl)
        change_outliner_color(ctrl_grp, (1, .7, .7))

        # Create Bound Joint
        bound_joint = driven.replace('driver' + JNT_SUFFIX.capitalize(), JNT_SUFFIX)
        # if setup == 'outfit_wrist':
        #     bound_joint = bound_joint.replace('outfit_', '').replace('driver', 'outfit')

        if not cmds.objExists(bound_joint):
            cmds.select(d=True)
            bound_joint = cmds.joint(name=bound_joint, radius=.4)
            cmds.parentConstraint(ctrl, bound_joint)
            cmds.scaleConstraint(ctrl, bound_joint)
            cmds.parent(bound_joint, driver_bound)
            if setup == 'outfit_wrist':
                cmds.parent(bound_joint, side + '_forearm_jnt')
                change_viewport_color(bound_joint, (0, 1, 0))

        # Create necessary nodes
        pose_loc = cmds.spaceLocator(name=driven_prefix + '_' + name + '_loc')[0]
        change_viewport_color(pose_loc, (0, 1, 0))
        cmds.delete(cmds.parentConstraint(driver, pose_loc))
        cmds.parent(pose_loc, driver)
        blend_pos_node = cmds.createNode('blendColors', name=driven_prefix + '_' + name + '_posBlend')
        blend_rot_node = cmds.createNode('blendColors', name=driven_prefix + '_' + name + '_rotBlend')
        blend_sca_node = cmds.createNode('blendColors', name=driven_prefix + '_' + name + '_scaBlend')
        range_node = cmds.createNode('remapValue', name=driven_prefix + '_' + name + '_range')

        sum_pos_node = driven_prefix + '_posSum'
        sum_rot_node = driven_prefix + '_rotSum'
        sum_sca_node = driven_prefix + '_scaSum'
        if not cmds.objExists(sum_pos_node):
            sum_pos_node = cmds.createNode('plusMinusAverage', name=sum_pos_node)
        if not cmds.objExists(sum_rot_node):
            sum_rot_node = cmds.createNode('plusMinusAverage', name=sum_rot_node)
        if not cmds.objExists(sum_sca_node):
            sum_sca_node = cmds.createNode('plusMinusAverage', name=sum_sca_node)

        # Store Original Position
        pos_original = driven_prefix + '_posOriginal'
        rot_original = driven_prefix + '_rotOriginal'
        sca_original = driven_prefix + '_scaOriginal'
        if not cmds.objExists(pos_original):
            pos_original = cmds.createNode('multiplyDivide', name=pos_original)
            pos_next_slot = get_plus_minus_average_available_slot(sum_pos_node)
            cmds.connectAttr(pos_original + '.output', sum_pos_node + '.input3D[' + str(pos_next_slot) + ']')
        if not cmds.objExists(rot_original):
            rot_original = cmds.createNode('multiplyDivide', name=rot_original)
            rot_next_slot = get_plus_minus_average_available_slot(sum_rot_node)
            cmds.connectAttr(rot_original + '.output', sum_rot_node + '.input3D[' + str(rot_next_slot) + ']')
        if not cmds.objExists(sca_original):
            sca_original = cmds.createNode('multiplyDivide', name=sca_original)
            sca_next_slot = get_plus_minus_average_available_slot(sum_sca_node)
            cmds.connectAttr(sca_original + '.output', sum_sca_node + '.input3D[' + str(sca_next_slot) + ']')
        sca_offset_subtract = cmds.createNode('multiplyDivide', name=name + '_offsetSubtract')

        # Copy original transforms to blends
        xyz_rgb = {'x': 'R', 'y': 'G', 'z': 'B'}
        for dimension, color in xyz_rgb.items():
            pos_data = cmds.getAttr(driven + '.t' + dimension)
            rot_data = cmds.getAttr(driven + '.r' + dimension)
            sca_data = cmds.getAttr(driven + '.s' + dimension)
            cmds.setAttr(pos_original + '.input1' + dimension.capitalize(), pos_data)
            cmds.setAttr(rot_original + '.input1' + dimension.capitalize(), rot_data)
            cmds.setAttr(sca_original + '.input1' + dimension.capitalize(), sca_data)
            cmds.setAttr(sca_offset_subtract + '.input1' + dimension.capitalize(), 1)  # Subtract Output

        # Zero Blends
        for dimension, color in xyz_rgb.items():
            cmds.setAttr(blend_pos_node + '.color2' + color, 0)
            cmds.setAttr(blend_rot_node + '.color2' + color, 0)
            cmds.setAttr(blend_sca_node + '.color2' + color, 0)

        # Create Original Correction Nodes
        subtract_pos_node = driven_prefix + '_' + name + '_removePosOffset'
        subtract_rot_node = driven_prefix + '_' + name + '_removeRotOffset'
        subtract_sca_node = driven_prefix + '_' + name + '_removeRotOffset'
        subtract_pos_node = cmds.createNode('plusMinusAverage', name=subtract_pos_node)
        subtract_rot_node = cmds.createNode('plusMinusAverage', name=subtract_rot_node)
        subtract_sca_node = cmds.createNode('plusMinusAverage', name=subtract_sca_node)
        cmds.setAttr(subtract_pos_node + '.operation', 2)  # Subtract
        cmds.setAttr(subtract_rot_node + '.operation', 2)  # Subtract
        cmds.setAttr(subtract_sca_node + '.operation', 2)  # Subtract

        # Create Basic Connections
        if setup.endswith('wrist'):
            cmds.connectAttr(rot_angle_child + '.ry', range_node + '.inputValue')
        if setup.endswith('knee'):
            cmds.connectAttr(rot_angle_child + '.rz', range_node + '.inputValue')

        cmds.connectAttr(pose_loc + '.translate', subtract_pos_node + '.input3D[0]')
        cmds.connectAttr(pose_loc + '.rotate', subtract_rot_node + '.input3D[0]')
        cmds.connectAttr(pos_original + '.output', subtract_pos_node + '.input3D[1]')
        cmds.connectAttr(rot_original + '.output', subtract_rot_node + '.input3D[1]')
        cmds.connectAttr(subtract_pos_node + '.output3D', blend_pos_node + '.color1')
        cmds.connectAttr(subtract_rot_node + '.output3D', blend_rot_node + '.color1')
        cmds.connectAttr(pose_loc + '.scale', subtract_sca_node + '.input3D[0]')
        cmds.connectAttr(sca_offset_subtract + '.output', subtract_sca_node + '.input3D[1]')
        cmds.connectAttr(subtract_sca_node + '.output3D', blend_sca_node + '.color1')

        # Blender Connections
        general_influence = driven_prefix + '_' + name + '_influence'
        general_influence = cmds.createNode('multiplyDivide', name=general_influence)
        cmds.connectAttr(range_node + '.outValue', general_influence + '.input1X')
        cmds.connectAttr(range_node + '.outValue', general_influence + '.input1Y')
        cmds.connectAttr(range_node + '.outValue', general_influence + '.input1Z')
        cmds.connectAttr(general_influence + '.outputX', blend_pos_node + '.blender')
        cmds.connectAttr(general_influence + '.outputY', blend_rot_node + '.blender')
        cmds.connectAttr(general_influence + '.outputZ', blend_sca_node + '.blender')

        pos_next_slot = get_plus_minus_average_available_slot(sum_pos_node)
        rot_next_slot = get_plus_minus_average_available_slot(sum_rot_node)
        sca_next_slot = get_plus_minus_average_available_slot(sum_sca_node)

        # Rotate to Sum
        reverse_rot_output = driven_prefix.replace('driver' + JNT_SUFFIX.capitalize(), '') + name + '_reverseOutputY'
        reverse_rot_output = cmds.createNode('multiplyDivide', name=reverse_rot_output)
        if setup == 'upper_wrist':
            cmds.setAttr(reverse_rot_output + '.input2Z', -1)
            if side == 'right':
                cmds.setAttr(reverse_rot_output + '.input2Y', -1)
                cmds.setAttr(reverse_rot_output + '.input2X', -1)
            cmds.connectAttr(blend_rot_node + '.outputR', reverse_rot_output + '.input1X', force=True)
            cmds.connectAttr(blend_rot_node + '.outputB', reverse_rot_output + '.input1Y', force=True)
            cmds.connectAttr(blend_rot_node + '.outputG', reverse_rot_output + '.input1Z', force=True)
        if setup == 'lower_wrist':
            cmds.setAttr(reverse_rot_output + '.input2Z', -1)
            cmds.setAttr(reverse_rot_output + '.input2Y', -1)
            cmds.setAttr(reverse_rot_output + '.input2X', -1)
            if side == 'right':
                cmds.setAttr(reverse_rot_output + '.input2Y', 1)
                cmds.setAttr(reverse_rot_output + '.input2X', 1)
            cmds.connectAttr(blend_rot_node + '.outputR', reverse_rot_output + '.input1X', force=True)
            cmds.connectAttr(blend_rot_node + '.outputB', reverse_rot_output + '.input1Y', force=True)
            cmds.connectAttr(blend_rot_node + '.outputG', reverse_rot_output + '.input1Z', force=True)
        if setup == 'back_knee':
            cmds.setAttr(reverse_rot_output + '.input2Z', -1)
            cmds.setAttr(reverse_rot_output + '.input2Y', -1)
            cmds.setAttr(reverse_rot_output + '.input2X', -1)
            if side == 'right':
                cmds.setAttr(reverse_rot_output + '.input2Y', 1)
                cmds.setAttr(reverse_rot_output + '.input2Z', 1)
                pass
            cmds.connectAttr(blend_rot_node + '.outputB', reverse_rot_output + '.input1X', force=True)
            cmds.connectAttr(blend_rot_node + '.outputG', reverse_rot_output + '.input1Y', force=True)
            cmds.connectAttr(blend_rot_node + '.outputR', reverse_rot_output + '.input1Z', force=True)
        if setup == 'outfit_wrist':
            cmds.setAttr(reverse_rot_output + '.input2Y', -1)
            cmds.setAttr(reverse_rot_output + '.input2X', -1)
            if side == 'right':
                cmds.setAttr(reverse_rot_output + '.input2Y', 1)
                cmds.setAttr(reverse_rot_output + '.input2X', 1)
            cmds.connectAttr(blend_rot_node + '.outputR', reverse_rot_output + '.input1X', force=True)
            cmds.connectAttr(blend_rot_node + '.outputG', reverse_rot_output + '.input1Y', force=True)
            cmds.connectAttr(blend_rot_node + '.outputB', reverse_rot_output + '.input1Z', force=True)

        cmds.connectAttr(reverse_rot_output + '.output', sum_rot_node + '.input3D[' + str(rot_next_slot) + ']')
        # Translate to Sum
        cmds.connectAttr(blend_pos_node + '.output', sum_pos_node + '.input3D[' + str(pos_next_slot) + ']')
        # Scale to Sum
        reverse_sca_output = driven_prefix.replace('driver' + JNT_SUFFIX.capitalize(), '') + name + '_scaleInbetween'
        reverse_sca_output = cmds.createNode('multiplyDivide', name=reverse_sca_output)
        if setup == 'back_knee':
            cmds.connectAttr(blend_sca_node + '.outputB', reverse_sca_output + '.input1X', force=True)
            cmds.connectAttr(blend_sca_node + '.outputG', reverse_sca_output + '.input1Y', force=True)
            cmds.connectAttr(blend_sca_node + '.outputR', reverse_sca_output + '.input1Z', force=True)
        else:
            cmds.connectAttr(blend_sca_node + '.outputR', reverse_sca_output + '.input1X', force=True)
            cmds.connectAttr(blend_sca_node + '.outputB', reverse_sca_output + '.input1Y', force=True)
            cmds.connectAttr(blend_sca_node + '.outputG', reverse_sca_output + '.input1Z', force=True)
        cmds.connectAttr(reverse_sca_output + '.output', sum_sca_node + '.input3D[' + str(sca_next_slot) + ']')
        if not cmds.listConnections(driven + '.translate', source=True, destination=False):
            cmds.connectAttr(sum_pos_node + '.output3D', driven + '.translate', force=True)
        if not cmds.listConnections(driven + '.rotate', source=True, destination=False):
            cmds.connectAttr(sum_rot_node + '.output3D', driven + '.rotate', force=True)
        if not cmds.listConnections(driven + '.scale', source=True, destination=False):
            cmds.connectAttr(sum_sca_node + '.output3D', driven + '.scale', force=True)

        # Set Initial Locator Position (Pose)
        cmds.setAttr(pose_loc + '.tx', driven_offset[0])
        cmds.setAttr(pose_loc + '.ty', driven_offset[1])
        cmds.setAttr(pose_loc + '.tz', driven_offset[2])
        if len(driven_offset) > 3:
            cmds.setAttr(pose_loc + '.rx', driven_offset[3])
            cmds.setAttr(pose_loc + '.ry', driven_offset[4])
            cmds.setAttr(pose_loc + '.rz', driven_offset[5])
        if len(driven_offset) > 6:
            cmds.setAttr(pose_loc + '.sx', driven_offset[6])
            cmds.setAttr(pose_loc + '.sy', driven_offset[7])
            cmds.setAttr(pose_loc + '.sz', driven_offset[8])

        # Create Ctrl Attributes and Set Initial Values
        general_influence_attr = name + 'GeneralInfluence'
        min_influence_attr = name + 'MinInfluence'
        max_influence_attr = name + 'MaxInfluence'

        reverse_influence_attr = name + 'reverseInfluence'
        cmds.setAttr(ctrl + '.visibility', k=False, l=True)
        cmds.addAttr(ctrl, ln=name, at='enum', en='-------------:', keyable=True)
        cmds.setAttr(ctrl + '.' + name, lock=True)
        cmds.addAttr(ctrl, ln=general_influence_attr, at='double', k=True, niceName='Influence')
        cmds.setAttr(ctrl + '.' + general_influence_attr, 1)
        cmds.addAttr(ctrl, ln=min_influence_attr, at='double', k=True, niceName='Start Value')
        cmds.addAttr(ctrl, ln=max_influence_attr, at='double', k=True, niceName='End Value')
        cmds.addAttr(ctrl, ln=reverse_influence_attr, at='bool', k=False, niceName='Positive Start')
        reverse_min_max = cmds.createNode('reverse', name=name + '_reverseInfluence')

        cmds.connectAttr(ctrl + '.' + reverse_influence_attr, reverse_min_max + '.inputX')
        cmds.connectAttr(reverse_min_max + '.outputX', range_node + '.outputMin')
        cmds.connectAttr(ctrl + '.' + reverse_influence_attr, range_node + '.outputMax')
        cmds.connectAttr(ctrl + '.' + min_influence_attr, range_node + '.inputMin')
        cmds.connectAttr(ctrl + '.' + max_influence_attr, range_node + '.inputMax')

        cmds.connectAttr(ctrl + '.' + general_influence_attr, general_influence + '.input2X')
        cmds.connectAttr(ctrl + '.' + general_influence_attr, general_influence + '.input2Y')
        cmds.connectAttr(ctrl + '.' + general_influence_attr, general_influence + '.input2Z')
        cmds.connectAttr(main_ctrl + '.' + loc_visibility_attr, pose_loc + '.v')
        if not cmds.isConnected(main_ctrl + '.' + ctrl_visibility_attr, offset_grp + '.v'):
            cmds.connectAttr(main_ctrl + '.' + ctrl_visibility_attr, offset_grp + '.v')

        if driver_range[0] < 0:
            cmds.setAttr(ctrl + '.' + reverse_influence_attr, 0)
            cmds.setAttr(ctrl + '.' + min_influence_attr, driver_range[0])
            cmds.setAttr(ctrl + '.' + max_influence_attr, driver_range[1])
        else:
            cmds.setAttr(ctrl + '.' + reverse_influence_attr, 1)
            cmds.setAttr(ctrl + '.' + min_influence_attr, driver_range[0])
            cmds.setAttr(ctrl + '.' + max_influence_attr, driver_range[1])

    # Delete Proxy
    if cmds.objExists(_corrective_proxy_dict.get('main_proxy_grp')):
        cmds.delete(_corrective_proxy_dict.get('main_proxy_grp'))

    # ###################################### Debugging #######################################
    if debugging:
        try:
            # Make Locators Visible
            for ctrl in corrective_ctrls:
                attributes = cmds.listAttr(ctrl, userDefined=True) or []
                for attr in attributes:
                    if attr.endswith('LocVisibility'):
                        cmds.setAttr(ctrl + '.' + attr, 1)
            cmds.setAttr('corrective_rig_setup_grp.v', 1)
            cmds.setAttr('left_elbow_aimJnt.v', 1)
            cmds.setAttr('right_elbow_aimJnt.v', 1)

        except Exception as e:
            print(e)


def merge_corrective_elements():
    corrective_rig_grp = 'corrective_rig_grp'
    skeleton_grp = 'skeleton_grp'
    direction_ctrl = 'direction_ctrl'
    rig_setup_grp = 'rig_setup_grp'
    corrective_joints = cmds.listRelatives('corrective_skeleton_grp', children=True)
    corrective_ctrls = cmds.listRelatives('corrective_controls_grp', children=True)
    rig_setup_grps = cmds.listRelatives('corrective_rig_setup_grp', children=True)

    for jnt in corrective_joints:
        cmds.parent(jnt, skeleton_grp)
    for ctrl in corrective_ctrls:
        cmds.parent(ctrl, direction_ctrl)
    for grp in rig_setup_grps:
        cmds.parent(grp, rig_setup_grp)

    cmds.delete(corrective_rig_grp)


if __name__ == '__main__':
    debugging = False
    # debugging = True
    # if debugging:
    #     import gt_maya_utilities
    #     gt_maya_utilities.gtu_reload_file()
    #     # cmds.file(new=True, force=True)

    create_corrective_proxy()
    create_corrective_setup()
    merge_corrective_elements()

    # cmds.setAttr('main_ctrl.correctiveVisibility', 1)
    # cmds.setAttr('main_ctrl.correctiveGoalLocVisibility', 1)
    #

