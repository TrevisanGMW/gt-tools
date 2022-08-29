"""
Script to help transfer motion capture data to custom rig controls
github.com/TrevisanGMW/gt-tools - 2022-02-18
    
v0.0.1 - 2022-02-18
Initial Test Version

v0.0.3 - 2022-03-02
Used parentConstraints to prevent undesired offset rotation

v0.0.5 - 2022-03-04
Simplified the script to avoid errors. It now detects joints and bakes FK and IK in one go

v0.1.0 - 2022-03-06
Updated UI and added button with explanations
Added custom help UI function

v0.1.1 - 2022-03-07
Added a sentence in the UI explaining basic behaviour regarding first frame use

v0.2.0 - 2022-03-07
Added leg stabilization, removed Transfer to IK option

v0.3.0 - 2022-07-07
PEP8 cleanup
Changed "Get Current" option, so it updates both fields
Added a few utility functions

v0.4.0 - 2022-07-12
Updated finger and spine functions to detect the source joint orientation
Added influence slider to "Connect Spine" help menu
Added invert rotation checkbox to "Connect Fingers" help menu
Added invert rotation checkboxes to "Reconnect Spine" help menu
Changed the name "Connect Spine" to "Reconnect Spine" for clarity
Added HIK properties' node selection button "P"

v0.4.1 - 2022-07-13
Deactivated "waist_ctrl.additionalFKCtrlsAutoRotate" when reconnecting spine
Activated "waist_ctrl.additionalFKCtrlsVisibility" when reconnecting spine

v0.4.2 - 2022-07-21
Updated help text

"""
from collections import namedtuple
from functools import partial
from PySide2.QtWidgets import QWidget
from PySide2.QtGui import QIcon
from shiboken2 import wrapInstance
from maya.api.OpenMaya import MVector
from maya import OpenMayaUI as OpenMayaUI
import maya.cmds as cmds
import maya.mel as mel
import logging
import random
import math
import sys

try:
    import gt_biped_rig_interface as switcher
except ModuleNotFoundError as error:
    try:
        print('Failed to load IK/FK Switcher. Attempting to import through "mayaTools"')
        from mayaTools import gt_biped_rig_interface as switcher
    except ModuleNotFoundError as error_sg:
        cmds.warning(str(error))
        cmds.warning(str(error_sg))
        cmds.warning("Fail to load required module. Open script editor for more information.")

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_rigger_retarget_assistant")
logger.setLevel(logging.INFO)

# General Variables
SCRIPT_VERSION = "0.4.3"
SCRIPT_NAME = 'Retarget Assistant'
MOCAP_RIG_GRP = 'mocap_rig_assistant_grp'

settings = {'connect_toes': True,
            'reconnect_spine': True,
            'spine_influence': 100,
            'is_spine_inverted_x': False,
            'is_spine_inverted_y': False,
            'is_spine_inverted_z': False,
            'connect_fingers': True,
            'is_finger_inverted': False,
            'leg_stabilization': True,
            'unlock_rotations': False,
            'merge_axis': False,
            }

hik_character = {'source': '',
                 'target': ''}

toe_ctrl_pairs = {'left_ball_ctrl': '',
                  'right_ball_ctrl': ''}

debugging_settings = {'is_debugging': False,
                      'reload_scene': False,
                      'source': '',
                      'target': '', }


def get_hik_current_character():
    """ Returns current HIK Character """
    return mel.eval('hikGetCurrentCharacter()') or ''


def hik_get_definition(character):
    hik_bones = {}
    hik_count = cmds.hikGetNodeCount()
    for i in range(hik_count):
        bone = mel.eval('hikGetSkNode( "%s" , %d )' % (character, i))
        if bone:
            hik_name = cmds.GetHIKNodeName(i)
            hik_bones[hik_name] = {'bone': bone, 'hikid': i}
    return hik_bones


def hik_update_tool():
    mel_code = """
        if ( hikIsCharacterizationToolUICmdPluginLoaded() )
        {
            hikUpdateCharacterList();
            hikUpdateCurrentCharacterFromUI();
            hikUpdateContextualUI();
            hikControlRigSelectionChangedCallback;

            hikUpdateSourceList();
            hikUpdateCurrentSourceFromUI();
            hikUpdateContextualUI();
            hikControlRigSelectionChangedCallback;
        }
        """
    try:
        mel.eval(mel_code)
    except Exception as e:
        logger.debug(str(e))


def hik_bake_animation():
    mel_code = """
        hikUpdateCharacterMenu;
        hikUpdateBakeMenu;
        hikBakeCharacter 0;
        hikSetCurrentSourceFromCharacter(hikGetCurrentCharacter());
        hikUpdateSourceList;
        hikUpdateContextualUI;
        """
    try:
        mel.eval(mel_code)
    except Exception as e:
        logger.debug(str(e))


def hik_set_current_character(character):
    mel.eval('hikSetCurrentCharacter("'+character+'")')
    mel.eval('hikUpdateCharacterList()')
    mel.eval('hikSetCurrentSourceFromCharacter("'+character+'")')
    mel.eval('hikUpdateSourceList()')


def hik_set_source(target_character, source_character):
    hik_set_current_character(target_character)
    _HUMAN_IK_SOURCE_MENU = "hikSourceList"
    _HUMAN_IK_SOURCE_MENU_OPTION = _HUMAN_IK_SOURCE_MENU + "|OptionMenu"

    menu_item_list = cmds.optionMenu(_HUMAN_IK_SOURCE_MENU_OPTION, q=True, itemListLong=True)

    desired_source_index = 1
    desired_source = None
    for index in range(len(menu_item_list)):
        current_item = cmds.menuItem(menu_item_list[index], q=True, label=True)
        if source_character == current_item.strip():
            desired_source = menu_item_list[index]
            desired_source_index = index + 1

    cmds.optionMenu(_HUMAN_IK_SOURCE_MENU_OPTION, e=True, sl=desired_source_index)
    mel.eval('hikUpdateCurrentSourceFromUI()')
    mel.eval('hikUpdateContextualUI()')
    mel.eval('hikControlRigSelectionChangedCallback')

    return desired_source


def find_item_no_namespace(search_obj, obj_type='transform'):
    found = []
    all_items = cmds.ls(type=obj_type)
    for obj in all_items:
        if ':' in obj:
            no_ns_obj = obj.split(':')[-1]
            if search_obj == no_ns_obj:
                found.append(obj)
        else:
            if search_obj in obj:
                found.append(obj)
    return found


def _get_object_namespaces(object_name):
    """
    Returns only the namespace of the object
    Args:
        object_name (string): Name of the object to extract the namespace from
    Returns:
        namespaces (string): Extracted namespaces combined into a string (without the name of the object)
                             e.g. Input = "One:Two:pSphere" Output = "One:Two:"
    """
    namespaces_list = object_name.split(':')
    object_namespace = ''
    for namespace in namespaces_list:
        if namespace != namespaces_list[-1]:
            object_namespace += namespace + ':'

    return object_namespace


def change_viewport_color(obj, rgb_color=(1, 1, 1)):
    """
    Changes the color of an object by changing the drawing override settings

    Args:
        obj (string): Name of the object to change color
        rgb_color (tuple): RGB color

    """
    if cmds.objExists(obj) and cmds.getAttr(obj + '.overrideEnabled', lock=True) is False:
        cmds.setAttr(obj + '.overrideEnabled', 1)
        cmds.setAttr(obj + '.overrideRGBColors', 1)
        cmds.setAttr(obj + '.overrideColorRGB', rgb_color[0], rgb_color[1], rgb_color[2])


def change_outliner_color(obj, rgb_color=(1, 1, 1)):
    """
    Sets the outliner color for the selected object

    Args:
        obj (str): Name (path) of the object to change.
        rgb_color (tuple) : A tuple of 3 floats, RGB values. e.g. Red = (1, 0, 0)

    """
    if cmds.objExists(obj) and cmds.getAttr(obj + '.useOutlinerColor', lock=True) is False:
        cmds.setAttr(obj + '.useOutlinerColor', 1)
        cmds.setAttr(obj + '.outlinerColorR', rgb_color[0])
        cmds.setAttr(obj + '.outlinerColorG', rgb_color[1])
        cmds.setAttr(obj + '.outlinerColorB', rgb_color[2])


def create_toe_mocap_rig():
    if cmds.objExists(MOCAP_RIG_GRP):
        warning = "This rig seems to already be connected to a mocap rig. Please delete it before creating a new one."
        cmds.warning(warning)
        return

    # Debug
    # toe_ctrl_pairs = {'left_ball_ctrl': 'LeftToeBase',
    #                   'right_ball_ctrl': 'RightToeBase'}

    for ctrl, target in toe_ctrl_pairs.items():
        if str(target) == '':
            cmds.warning('Mocap joints cannot be empty.')
            return

        if not cmds.objExists(str(target)):
            cmds.warning('The provided mocap joints cannot be found.')
            return

    created_controls = []

    for ctrl, target in toe_ctrl_pairs.items():

        # Determine Side
        side = 'right'
        if ctrl.startswith('left'):
            side = 'left'

        # target_parent = cmds.listRelatives(target, parent=True)[0]
        ctrl_ns = find_item_no_namespace(ctrl)[0]

        mocap_ctrl = cmds.curve(name=ctrl + '_retargetOffsetCtrl',
                                p=[[0.0, 0.0, 0.0], [0.0, -0.0, 11.055], [0.0, -0.405, 11.113], [0.0, -0.791, 11.267],
                                   [0.0, -1.119, 11.518], [0.0, -1.37, 11.846], [0.0, -1.524, 12.212],
                                   [0.0, -1.582, 12.637], [0.0, -0.0, 12.637], [0.0, -0.0, 11.055],
                                   [0.0, 0.405, 11.113], [0.0, 0.791, 11.267], [0.0, 1.119, 11.518],
                                   [0.0, 1.37, 11.846], [0.0, 1.524, 12.212], [0.0, 1.582, 12.637],
                                   [0.0, 1.524, 13.042], [0.0, 1.37, 13.409], [0.0, 1.119, 13.737],
                                   [0.0, 0.791, 14.007], [0.0, 0.405, 14.161], [0.0, -0.0, 14.219],
                                   [0.0, -0.405, 14.161], [0.0, -0.791, 14.007], [0.0, -1.119, 13.756],
                                   [0.0, -1.351, 13.428], [0.0, -1.524, 13.042], [0.0, -1.582, 12.637],
                                   [0.0, 1.582, 12.637], [0.0, -0.0, 12.637], [0.0, -0.0, 14.219]], d=1)
        change_viewport_color(mocap_ctrl, (0, 1, 0))
        mocap_data_loc = cmds.spaceLocator(name=ctrl + '_pureDataLoc')[0]
        multiplied_mocap_data_loc = cmds.spaceLocator(name=ctrl + '_processedDataLoc')[0]
        cmds.delete(cmds.parentConstraint(mocap_ctrl, mocap_data_loc))
        cmds.delete(cmds.parentConstraint(mocap_ctrl, multiplied_mocap_data_loc))

        if side == 'right':
            cmds.setAttr(mocap_ctrl + '.sz', -1)
            cmds.makeIdentity(mocap_ctrl, scale=True, apply=True)

        # Lock and Hide undesired attributes
        cmds.setAttr(mocap_ctrl + '.sx', lock=True, k=False, channelBox=False)
        cmds.setAttr(mocap_ctrl + '.sy', lock=True, k=False, channelBox=False)
        cmds.setAttr(mocap_ctrl + '.sz', lock=True, k=False, channelBox=False)

        mocap_ctrl_grp = cmds.group(name=ctrl + 'Grp', empty=True, world=True)
        cmds.parent(mocap_data_loc, mocap_ctrl_grp)
        cmds.parent(multiplied_mocap_data_loc, mocap_ctrl)
        cmds.delete(cmds.parentConstraint(ctrl_ns, mocap_ctrl))
        cmds.delete(cmds.parentConstraint(ctrl_ns, mocap_ctrl_grp))
        cmds.parent(mocap_ctrl, mocap_ctrl_grp)

        # if side == 'right':
        #     cmds.setAttr(mocap_data_loc + '.rx', -360)

        cmds.parentConstraint(multiplied_mocap_data_loc, ctrl_ns, mo=True)
        ankle_ctrl_ns = find_item_no_namespace(side + '_ankle_ctrl')[0]

        cmds.parentConstraint(ankle_ctrl_ns, mocap_ctrl_grp, mo=True)
        cmds.setAttr(mocap_data_loc + '.rx', 0)
        cmds.setAttr(mocap_data_loc + '.ry', 0)
        cmds.setAttr(mocap_data_loc + '.rz', 0)
        cmds.setAttr(mocap_data_loc + '.v', 0)
        cmds.setAttr(multiplied_mocap_data_loc + '.v', 0)

        cmds.delete(cmds.pointConstraint(target, mocap_data_loc))
        cmds.parentConstraint(target, mocap_data_loc, mo=True)

        rot_multiply_node = cmds.createNode('multiplyDivide', name=ctrl + 'retargetRotInfluence')
        cmds.connectAttr(mocap_data_loc + '.rotate', rot_multiply_node + '.input1')
        cmds.connectAttr(rot_multiply_node + '.output', multiplied_mocap_data_loc + '.rotate')

        cmds.addAttr(mocap_ctrl, ln='controlBehaviour', at='enum', en='-------------:', keyable=True)
        cmds.setAttr(mocap_ctrl + '.controlBehaviour', lock=True)
        cmds.addAttr(mocap_ctrl, ln='rotationInfluence', at='double', k=True, min=0)
        cmds.setAttr(mocap_ctrl + '.rotationInfluence', 1)
        cmds.connectAttr(mocap_ctrl + '.rotationInfluence', rot_multiply_node + '.input2X')
        cmds.connectAttr(mocap_ctrl + '.rotationInfluence', rot_multiply_node + '.input2Y')
        cmds.connectAttr(mocap_ctrl + '.rotationInfluence', rot_multiply_node + '.input2Z')
        created_controls.append(mocap_ctrl_grp)

    mocap_ctrl_grp = cmds.group(name=MOCAP_RIG_GRP, empty=True, world=True)
    change_outliner_color(mocap_ctrl_grp, (1, 0, 0))
    for grp in created_controls:
        cmds.parent(grp, mocap_ctrl_grp)
    sys.stdout.write('Mocap rig has been created.')
    controls_to_bake = []
    for ctrl, target in toe_ctrl_pairs.items():
        controls_to_bake.append(find_item_no_namespace(ctrl)[0])
    return controls_to_bake


def delete_toe_mocap_rig():
    """
    Deletes the mocap rig group, breaking all its connections and removing its elements.
    """
    if not cmds.objExists(MOCAP_RIG_GRP):
        warning = "Mocap rig group could not be found. Please maybe it has already been deleted?."
        cmds.warning(warning)
        return
    else:
        cmds.delete(MOCAP_RIG_GRP)
        sys.stdout.write('Mocap rig has been deleted.')


# ----------------------------------- Button Functions


def _btn_refresh_textfield_hik_data(*args):
    hik_character[args[0]] = args[1]


def _btn_refresh_textfield_settings_data(*args):
    settings[args[0]] = args[1]

    if settings.get('unlock_rotations'):
        cmds.checkBox('ch_merge_axis', e=True, en=True)
    else:
        cmds.checkBox('ch_merge_axis', e=True, value=False, en=False)
        settings['merge_axis'] = False


def hik_post_bake_mocap_rig(controls_to_bake):
    """
    Args:
        controls_to_bake (list) : A list of controls to be added in the baking process
    """
    start = cmds.playbackOptions(q=True, min=True)
    end = cmds.playbackOptions(q=True, max=True) + 1
    cmds.bakeResults(controls_to_bake, t=(start, end), simulation=True)


def transfer_fk_ik_toe_mocap_rig():
    left_ball_ctrl_ns = find_item_no_namespace('left_ball_ctrl')
    right_ball_ctrl_ns = find_item_no_namespace('right_ball_ctrl')

    if len(left_ball_ctrl_ns) == 0 or len(right_ball_ctrl_ns) == 0:
        cmds.warning('Controls could not be selected. Make sure you are using an updated version of the rig.')
        return
    else:
        left_ball_ctrl_ns = left_ball_ctrl_ns[0]
        right_ball_ctrl_ns = right_ball_ctrl_ns[0]

    # Setup Left Locator
    left_locator = cmds.spaceLocator(name='left_offset_loc')[0]
    cmds.delete(cmds.parentConstraint(left_ball_ctrl_ns, left_locator))
    cmds.rotate(-90, left_locator, rotateX=True, objectSpace=True, relative=True)
    cmds.rotate(-180, left_locator, rotateZ=True, objectSpace=True, relative=True)
    cmds.parentConstraint(left_ball_ctrl_ns, left_locator, mo=True)

    # Setup Right Locator
    right_locator = cmds.spaceLocator(name='right_offset_loc')[0]
    cmds.delete(cmds.parentConstraint(right_ball_ctrl_ns, right_locator))
    cmds.rotate(90, right_locator, rotateX=True, objectSpace=True, relative=True)
    cmds.rotate(180, right_locator, rotateZ=True, objectSpace=True, relative=True)
    cmds.parentConstraint(right_ball_ctrl_ns, right_locator, mo=True)

    # Connect Locators and Controls
    left_toe_ik_ctrl_ns = find_item_no_namespace('left_toe_ik_ctrl')[0]
    right_toe_ik_ctrl_ns = find_item_no_namespace('right_toe_ik_ctrl')[0]
    cmds.parentConstraint(left_locator, left_toe_ik_ctrl_ns)
    cmds.parentConstraint(right_locator, right_toe_ik_ctrl_ns)

    controls = [left_toe_ik_ctrl_ns, right_toe_ik_ctrl_ns]
    # controls.append(left_toe_ik_ctrl_ns)
    # controls.append(right_toe_ik_ctrl_ns)

    start = cmds.playbackOptions(q=True, min=True)
    end = cmds.playbackOptions(q=True, max=True) + 1
    cmds.bakeResults(controls, t=(start, end), simulation=True)
    for obj in [left_locator, right_locator]:
        if cmds.objExists(obj):
            cmds.delete(obj)


def switch_to_fk_influence(switch_ctrls):
    for ctrl in switch_ctrls:
        attributes = cmds.listAttr(ctrl, userDefined=True)
        influence_switch_attr = 'influenceSwitch'
        influence_spine_switch_attr = 'spineInfluenceSwitch'
        if influence_switch_attr in attributes:
            cmds.setAttr(ctrl + '.' + influence_switch_attr, 0)  # FK
        if influence_spine_switch_attr in attributes:
            cmds.setAttr(ctrl + '.' + influence_spine_switch_attr, 0)  # FK


def _btn_bake_mocap_with_fixes(*args):
    if debugging_settings.get('is_debugging'):
        if debugging_settings.get('source'):
            hik_character['source'] = debugging_settings.get('source')
        if debugging_settings.get('target'):
            hik_character['target'] = debugging_settings.get('target')

    logger.debug(str(args))

    hik_definition_source = hik_get_definition(hik_character.get('source'))
    hik_definition_target = hik_get_definition(hik_character.get('target'))

    if len(hik_definition_source) == 0:
        cmds.warning('Source character definition is empty. Make sure you loaded the correct HumanIK character.')
        return

    if len(hik_definition_target) == 0:
        cmds.warning('Target character definition is empty. Make sure you loaded the correct HumanIK character.')
        return

    left_leg_switch_ctrl_ns = find_item_no_namespace('left_leg_switch_ctrl')[0]
    right_leg_switch_ctrl_ns = find_item_no_namespace('right_leg_switch_ctrl')[0]
    left_arm_switch_ctrl_ns = find_item_no_namespace('left_arm_switch_ctrl')[0]
    right_arm_switch_ctrl_ns = find_item_no_namespace('right_arm_switch_ctrl')[0]
    waist_ctrl_switch_ctrl_ns = find_item_no_namespace('waist_ctrl')[0]

    switch_ctrls = [left_leg_switch_ctrl_ns,
                    right_leg_switch_ctrl_ns,
                    left_arm_switch_ctrl_ns,
                    right_arm_switch_ctrl_ns,
                    waist_ctrl_switch_ctrl_ns]

    switch_to_fk_influence(switch_ctrls)

    hik_set_source(target_character=hik_character.get('target'), source_character=hik_character.get('source'))

    start_time = cmds.playbackOptions(q=True, min=True)
    cmds.currentTime(start_time)

    source_right_foot = hik_definition_source.get('RightFoot')
    source_left_foot = hik_definition_source.get('LeftFoot')

    right_toe_jnt = cmds.listRelatives(source_right_foot.get('bone'), children=True) or []
    left_toe_jnt = cmds.listRelatives(source_left_foot.get('bone'), children=True) or []

    toe_ctrl_pairs['left_ball_ctrl'] = left_toe_jnt[0]
    toe_ctrl_pairs['right_ball_ctrl'] = right_toe_jnt[0]

    if settings.get('unlock_rotations'):
        to_unlock_rotations = ['left_knee_ctrl', 'right_knee_ctrl',
                               'left_elbow_ctrl', 'right_elbow_ctrl']
        for ctrl in to_unlock_rotations:
            ctrl_ns = find_item_no_namespace(ctrl)[0]
            attributes = cmds.listAttr(ctrl_ns, userDefined=True)
            for attr in attributes:
                if attr.startswith('lock'):
                    try:
                        cmds.setAttr(ctrl_ns + '.' + attr, 0)
                    except Exception as e:
                        logger.debug(str(e))

    # Leg Stabilization Setup
    to_unlock_rotations = {'left_knee_ctrl': [],
                           'right_knee_ctrl': [],
                           'left_elbow_ctrl': [],
                           'right_elbow_ctrl': [],
                           'left_ankle_ctrl': [],
                           'right_ankle_ctrl': [],
                           'left_hip_ctrl': [],
                           'right_hip_ctrl': [],
                           }
    if settings.get('leg_stabilization'):
        for ctrl in to_unlock_rotations:
            ctrl_ns = find_item_no_namespace(ctrl)[0]
            attributes = cmds.listAttr(ctrl_ns, userDefined=True)
            for attr in attributes:
                if attr.startswith('lock'):
                    try:
                        to_unlock_rotations.get(ctrl).append((ctrl_ns + '.' + attr, cmds.getAttr(ctrl_ns + '.' + attr)))
                        cmds.setAttr(ctrl_ns + '.' + attr, 0)
                    except Exception as e:
                        logger.debug(str(e))

    # Start Baking Process ------------------------------------------------------
    try:
        cmds.refresh(suspend=True)
        hik_bake_animation()

        controls_to_bake = []
        offset_nodes = []

        # Pole Vectors
        left_knee_switch_loc_ns = find_item_no_namespace('left_kneeSwitch_loc')[0]
        right_knee_switch_loc_ns = find_item_no_namespace('right_kneeSwitch_loc')[0]
        left_knee_ik_ctrl_ns = find_item_no_namespace('left_knee_ik_ctrl')[0]
        right_knee_ik_ctrl_ns = find_item_no_namespace('right_knee_ik_ctrl')[0]
        left_knee_constraint = cmds.pointConstraint(left_knee_switch_loc_ns, left_knee_ik_ctrl_ns)
        right_knee_constraint = cmds.pointConstraint(right_knee_switch_loc_ns, right_knee_ik_ctrl_ns)

        # left_elbowSwitch_loc_ns = find_item_no_namespace('left_elbowSwitch_loc')[0]
        # right_elbowSwitch_loc_ns = find_item_no_namespace('right_elbowSwitch_loc')[0]
        # left_elbow_ik_ctrl_ns = find_item_no_namespace('left_elbow_ik_ctrl')[0]
        # right_elbow_ik_ctrl_ns = find_item_no_namespace('right_elbow_ik_ctrl')[0]
        # left_elbow_constraint = cmds.pointConstraint(left_elbowSwitch_loc_ns, left_elbow_ik_ctrl_ns)
        # right_elbow_constraint = cmds.pointConstraint(right_elbowSwitch_loc_ns, right_elbow_ik_ctrl_ns)

        controls_to_bake.append(left_knee_ik_ctrl_ns)
        controls_to_bake.append(right_knee_ik_ctrl_ns)
        # controls_to_bake.append(left_elbow_ik_ctrl_ns)
        # controls_to_bake.append(right_elbow_ik_ctrl_ns)

        offset_nodes.append(left_knee_constraint)
        offset_nodes.append(right_knee_constraint)
        # offset_nodes.append(left_elbow_constraint)
        # offset_nodes.append(right_elbow_constraint)

        # Toes
        if settings.get('connect_toes'):
            toe_ctrls = create_toe_mocap_rig()
            if toe_ctrls:
                controls_to_bake = controls_to_bake + toe_ctrls

        # Spine
        if settings.get('reconnect_spine'):
            spine_ctrls, spine_offset_nodes = create_spine_mocap_rig(hik_definition_source)
            if spine_ctrls:
                controls_to_bake = controls_to_bake + spine_ctrls
            if spine_offset_nodes:
                offset_nodes = offset_nodes + spine_offset_nodes

        # Fingers
        if settings.get('connect_fingers'):
            finger_ctrls, finger_offset_nodes = create_finger_mocap_rig(hik_definition_source)
            if finger_ctrls:
                controls_to_bake = controls_to_bake + finger_ctrls
            if finger_offset_nodes:
                offset_nodes = offset_nodes + finger_offset_nodes

        # Bake
        cmds.currentTime(start_time)
        if controls_to_bake:
            hik_post_bake_mocap_rig(controls_to_bake)

        for node in offset_nodes:
            try:
                cmds.delete(node)
            except Exception as e:
                logger.debug(str(e))

        # FK/IK Legs
        left_leg_switch_ctrl_ns = find_item_no_namespace('left_leg_switch_ctrl')[0]
        rig_namespace = _get_object_namespaces(left_leg_switch_ctrl_ns)
        start = cmds.playbackOptions(q=True, min=True)
        end = cmds.playbackOptions(q=True, max=True) + 1

        if settings.get('leg_stabilization'):
            switcher.fk_ik_switch(switcher.left_leg_seamless_dict, direction='ik_to_fk', namespace=rig_namespace,
                                  keyframe=True, start_time=int(start), end_time=int(end), method='bake')
            switcher.fk_ik_switch(switcher.right_leg_seamless_dict, direction='ik_to_fk', namespace=rig_namespace,
                                  keyframe=True, start_time=int(start), end_time=int(end), method='bake')
            # Re-set locking options
            for ctrl, data in to_unlock_rotations.items():
                for attribute_value in data:
                    cmds.setAttr(attribute_value[0], attribute_value[1])

        else:
            # Setup Switcher
            switcher.fk_ik_switch(switcher.left_leg_seamless_dict, direction='fk_to_ik', namespace=rig_namespace,
                                  keyframe=True, start_time=int(start), end_time=int(end), method='bake')
            switcher.fk_ik_switch(switcher.right_leg_seamless_dict, direction='fk_to_ik', namespace=rig_namespace,
                                  keyframe=True, start_time=int(start), end_time=int(end), method='bake')

        # FK/IK Arms
        switcher.fk_ik_switch(switcher.left_arm_seamless_dict, direction='fk_to_ik', namespace=rig_namespace,
                              keyframe=True, start_time=int(start), end_time=int(end), method='bake')
        switcher.fk_ik_switch(switcher.right_arm_seamless_dict, direction='fk_to_ik', namespace=rig_namespace,
                              keyframe=True, start_time=int(start), end_time=int(end), method='bake')

        if settings.get('merge_axis'):
            switcher.fk_ik_switch(switcher.left_arm_seamless_dict, direction='ik_to_fk', namespace=rig_namespace,
                                  keyframe=True, start_time=int(start), end_time=int(end), method='bake')
            switcher.fk_ik_switch(switcher.right_arm_seamless_dict, direction='ik_to_fk', namespace=rig_namespace,
                                  keyframe=True, start_time=int(start), end_time=int(end), method='bake')

        transfer_fk_ik_toe_mocap_rig()

        if settings.get('connect_toes'):
            delete_toe_mocap_rig()
        switch_to_fk_influence(switch_ctrls)

        sys.stdout.write('Mocap Baking Completed')

    except Exception as e:
        raise e
    finally:
        cmds.refresh(suspend=False)


def create_finger_mocap_rig(hik_source_definition):
    fingers_dict = {'LeftHandIndex1': 'left_index01_ctrl',
                    'LeftHandIndex2': 'left_index02_ctrl',
                    'LeftHandIndex3': 'left_index03_ctrl',
                    'LeftHandMiddle1': 'left_middle01_ctrl',
                    'LeftHandMiddle2': 'left_middle02_ctrl',
                    'LeftHandMiddle3': 'left_middle03_ctrl',
                    'LeftHandPinky1': 'left_pinky01_ctrl',
                    'LeftHandPinky2': 'left_pinky02_ctrl',
                    'LeftHandPinky3': 'left_pinky03_ctrl',
                    'LeftHandRing1': 'left_ring01_ctrl',
                    'LeftHandRing2': 'left_ring02_ctrl',
                    'LeftHandRing3': 'left_ring03_ctrl',
                    'LeftHandThumb1': 'left_thumb01_ctrl',
                    'LeftHandThumb2': 'left_thumb02_ctrl',
                    'LeftHandThumb3': 'left_thumb03_ctrl',

                    'RightHandIndex1': 'right_index01_ctrl',
                    'RightHandIndex2': 'right_index02_ctrl',
                    'RightHandIndex3': 'right_index03_ctrl',
                    'RightHandMiddle1': 'right_middle01_ctrl',
                    'RightHandMiddle2': 'right_middle02_ctrl',
                    'RightHandMiddle3': 'right_middle03_ctrl',
                    'RightHandPinky1': 'right_pinky01_ctrl',
                    'RightHandPinky2': 'right_pinky02_ctrl',
                    'RightHandPinky3': 'right_pinky03_ctrl',
                    'RightHandRing1': 'right_ring01_ctrl',
                    'RightHandRing2': 'right_ring02_ctrl',
                    'RightHandRing3': 'right_ring03_ctrl',
                    'RightHandThumb1': 'right_thumb01_ctrl',
                    'RightHandThumb2': 'right_thumb02_ctrl',
                    'RightHandThumb3': 'right_thumb03_ctrl'}
    # locators = []
    connected_controls = []
    offset_nodes = []
    for source, target in fingers_dict.items():
        try:
            source_bone_dict = hik_source_definition.get(source)
            if source_bone_dict:
                source_bone = source_bone_dict.get('bone')

                target_ns = find_item_no_namespace(target)
                if target_ns:
                    target_ns = target_ns[0]

                    source_bone_rx = cmds.getAttr(source_bone + '.rx')
                    source_bone_ry = cmds.getAttr(source_bone + '.ry')
                    source_bone_rz = cmds.getAttr(source_bone + '.rz')

                    storage_node = cmds.createNode('multiplyDivide', name=source_bone + '_tempRotStorage')
                    cmds.setAttr(storage_node + '.input1X', source_bone_rx)
                    cmds.setAttr(storage_node + '.input1Y', source_bone_ry)
                    cmds.setAttr(storage_node + '.input1Z', source_bone_rz)

                    sum_node = cmds.createNode('plusMinusAverage', name=source_bone + '_tempOffsetOperation')
                    cmds.setAttr(sum_node + '.operation', 2)
                    cmds.connectAttr(storage_node + '.output', sum_node + '.input3D[1]')
                    cmds.connectAttr(source_bone + '.rotate', sum_node + '.input3D[0]')

                    offset_nodes.append(storage_node)
                    offset_nodes.append(sum_node)

                    source_orientation = get_joint_orientation(source_bone)
                    logger.debug(source_orientation)

                    neg_multiply_node = cmds.createNode('multiplyDivide', name=source_bone + '_tempNegOffsetOperation')
                    if settings.get('is_finger_inverted'):
                        cmds.setAttr(neg_multiply_node + '.input2X', -1)
                        cmds.setAttr(neg_multiply_node + '.input2Y', -1)
                        cmds.setAttr(neg_multiply_node + '.input2Z', -1)

                    cmds.connectAttr(sum_node + '.output3D' + source_orientation.aim_axis[-1],
                                     neg_multiply_node + '.input1X', force=True)
                    cmds.connectAttr(sum_node + '.output3D' + source_orientation.up_axis[-1],
                                     neg_multiply_node + '.input1Y', force=True)
                    cmds.connectAttr(sum_node + '.output3D' + source_orientation.main_axis[-1],
                                     neg_multiply_node + '.input1Z', force=True)

                    cmds.connectAttr(neg_multiply_node + '.output', target_ns + '.rotate', force=True)

                    connected_controls.append(target_ns)
        except Exception as e:
            logger.debug(str(e))

    return connected_controls, offset_nodes


def create_spine_mocap_rig(hik_source_definition):
    # Necessary Ctrls
    chest_ctrl_ns = find_item_no_namespace('chest_ctrl')[0]
    spine02_ctrl_ns = find_item_no_namespace('spine02_ctrl')[0]

    # Extra Controls
    spine01_ctrl_ns = find_item_no_namespace('spine01_ctrl')[0]
    spine03_ctrl_ns = find_item_no_namespace('spine03_ctrl')[0]

    try:
        waist_ctrl_switch_ctrl_ns = find_item_no_namespace('waist_ctrl')[0]
        cmds.setAttr(waist_ctrl_switch_ctrl_ns + '.additionalFKCtrlsAutoRotate', 0)
        cmds.setAttr(waist_ctrl_switch_ctrl_ns + '.additionalFKCtrlsVisibility', 1)
    except Exception as e:
        logger.debug(str(e))

    # Delete Keyframes
    for ctrl in [chest_ctrl_ns, spine02_ctrl_ns]:
        for axis in ['r']:
            logger.debug(str(axis))
            for dimension in ['x', 'y', 'z']:
                attr = cmds.listConnections(ctrl + '.' + 'r' + dimension, destination=False) or []
                if attr:
                    cmds.delete(attr)

    spines = hik_find_highest_spine(hik_source_definition)

    connected_controls = []
    offset_nodes = []
    control_pairs = {}
    if len(spines) == 2:
        control_pairs[spines[0]] = spine02_ctrl_ns
    elif len(spines) == 3:
        control_pairs[spines[0]] = spine01_ctrl_ns
        control_pairs[spines[1]] = spine02_ctrl_ns
    elif len(spines) == 4:
        control_pairs[spines[0]] = spine01_ctrl_ns
        control_pairs[spines[1]] = spine02_ctrl_ns
        control_pairs[spines[2]] = spine03_ctrl_ns

    control_pairs[spines[-1]] = chest_ctrl_ns

    for source, target in control_pairs.items():

        source_bone_rx = cmds.getAttr(source + '.rx')
        source_bone_ry = cmds.getAttr(source + '.ry')
        source_bone_rz = cmds.getAttr(source + '.rz')

        storage_node = cmds.createNode('multiplyDivide', name=source + '_tempRotStorage')
        cmds.setAttr(storage_node + '.input1X', source_bone_rx)
        cmds.setAttr(storage_node + '.input1Y', source_bone_ry)
        cmds.setAttr(storage_node + '.input1Z', source_bone_rz)

        sum_node = cmds.createNode('plusMinusAverage', name=source + '_tempOffsetOperation')
        cmds.setAttr(sum_node + '.operation', 2)
        cmds.connectAttr(storage_node + '.output', sum_node + '.input3D[1]')
        cmds.connectAttr(source + '.rotate', sum_node + '.input3D[0]')

        offset_nodes.append(storage_node)
        offset_nodes.append(sum_node)

        source_orientation = get_joint_orientation(source, expected_up=(1, 0, 0))
        logger.debug(source_orientation)

        neg_multiply_node = cmds.createNode('multiplyDivide', name=source + '_tempNegNode')
        influence_multiply_node = cmds.createNode('multiplyDivide', name=source + '_tempInfluenceNode')

        cmds.connectAttr(sum_node + '.output3D' + source_orientation.up_axis[-1],
                         neg_multiply_node + '.input1X', force=True)
        cmds.connectAttr(sum_node + '.output3D' + source_orientation.aim_axis[-1],
                         neg_multiply_node + '.input1Y', force=True)
        cmds.connectAttr(sum_node + '.output3D' + source_orientation.main_axis[-1],
                         neg_multiply_node + '.input1Z', force=True)

        if settings.get('is_spine_inverted_x'):
            cmds.setAttr(neg_multiply_node + '.input2X', -1)
        if settings.get('is_spine_inverted_y'):
            cmds.setAttr(neg_multiply_node + '.input2Y', -1)
        if settings.get('is_spine_inverted_z'):
            cmds.setAttr(neg_multiply_node + '.input2Z', -1)

        cmds.connectAttr(neg_multiply_node + '.output', influence_multiply_node + '.input1', force=True)
        cmds.connectAttr(influence_multiply_node + '.outputX', target + '.rx', force=True)
        cmds.connectAttr(influence_multiply_node + '.outputY', target + '.ry', force=True)
        cmds.connectAttr(influence_multiply_node + '.outputZ', target + '.rz', force=True)
        cmds.setAttr(influence_multiply_node + '.input2X', settings.get('spine_influence') * 0.01)
        cmds.setAttr(influence_multiply_node + '.input2Y', settings.get('spine_influence') * 0.01)
        cmds.setAttr(influence_multiply_node + '.input2Z', settings.get('spine_influence') * 0.01)

        # cmds.connectAttr(sum_node + '.output3D', target + '.rotate', force=True)

        connected_controls.append(target)

    return connected_controls, offset_nodes


def hik_find_highest_spine(hik_definition):
    spine_query = [hik_definition.get('Spine'), hik_definition.get('Spine1'), hik_definition.get('Spine2'),
                   hik_definition.get('Spine3'), hik_definition.get('Spine4'), hik_definition.get('Spine5'),
                   hik_definition.get('Spine6'), hik_definition.get('Spine7'), hik_definition.get('Spine8'),
                   hik_definition.get('Spine9')]
    spines = []
    for obj in spine_query:
        if obj:
            spines.append(obj.get('bone'))
    return spines


def build_gui_mocap_rig():
    """Creates simple GUI for Mocap Rig"""

    def _btn_target_source_textfield(*args):
        """
        Populates the provided text field with the selected object.
        """
        logger.debug(str(args))
        mel.eval("HIKCharacterControlsTool;")  # Focus on UI
        current_char = get_hik_current_character()

        # Update Dictionary and Textfield
        _btn_refresh_textfield_hik_data('target', current_char)
        cmds.textField(hik_target_textfield, e=True, text=current_char)

        hik_source = get_hik_source(current_char)
        if hik_source:
            hik_source = hik_source[1:]
            if hik_source == 'Stance':
                hik_source = ''
        _btn_refresh_textfield_hik_data('source', hik_source)
        cmds.textField(hik_source_textfield, e=True, text=hik_source)

    def _btn_select_properties(tf_source, *args):
        logger.debug(str(args))

        char = cmds.textField(tf_source, q=True, text=True)

        if char:
            if is_hik_character_valid(char):
                properties = get_hik_properties_node(char)
                cmds.AttributeEditor()
                cmds.select(properties)
                unique_message = '<' + str(random.random()) + '>'
                unique_message += '<span style=\"color:#FF0000;text-decoration:underline;\">"' + char + "\""
                unique_message += "</span><span style=\"color:#FFFFFF;\"> HIK Properties node is now selected."
                cmds.inViewMessage(amg=unique_message, pos='botLeft', fade=True, alpha=.9)
                sys.stdout.write('HIK Properties node for "' + char + "\" is now selected.")
            else:
                cmds.warning('Unable to select properties. "' + char + "\" doesn't.")
        else:
            cmds.warning('Unable to select properties. No HIK definition was provided.')

    window_name = "build_gui_mocap_rig"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)

    build_gui_world_space_baker = cmds.window(window_name,
                                              title=SCRIPT_NAME + '  (v' + SCRIPT_VERSION + ')',
                                              titleBar=True,
                                              minimizeButton=False,
                                              maximizeButton=False,
                                              sizeable=True)

    cmds.window(window_name, e=True, sizeable=True, widthHeight=[1, 1])
    content_main = cmds.columnLayout(adjustableColumn=True)

    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.rowColumnLayout(numberOfColumns=1,
                         columnWidth=[(1, 270)],
                         columnSpacing=[(1, 10)],
                         parent=content_main)  # Window Size Adjustment
    cmds.rowColumnLayout(numberOfColumns=4,
                         columnWidth=[(1, 10), (2, 220), (3, 40), (4, 10)],
                         columnSpacing=[(1, 10), (2, 0)],
                         parent=content_main)  # Title Column
    cmds.text(" ", backgroundColor=title_bgc_color, h=30)  # Tiny Empty Green Space
    cmds.text(SCRIPT_NAME, backgroundColor=title_bgc_color, fn="boldLabelFont", align="left")
    cmds.text("v" + SCRIPT_VERSION, backgroundColor=title_bgc_color, fn="boldLabelFont", align="left")
    cmds.separator(h=10, style='none')  # Empty Space

    cmds.rowColumnLayout(numberOfColumns=1, columnWidth=[(1, 240)],
                         columnSpacing=[(1, 25), (3, 5)], parent=content_main)
    cmds.separator(height=10, style='none')  # Empty Space
    cmds.text("First time-field frame will be used as neutral pose", bgc=(.3, .3, .3))

    # cmds.separator(height=15, style='none')  # Empty Space
    # cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 90), (2, 150)],
    #                      columnSpacing=[(1, 25)], parent=content_main)
    # cmds.text('Primary Target: ')
    # target_option_menu = cmds.optionMenu(label='')
    # cmds.menuItem(label=' Forward Kinematics (FK)')
    # cmds.menuItem(label=' Inverse Kinematics (IK)')

    # Text Fields and Checkboxes
    help_bgc_color = (.4, .4, .4)
    checkbox_cw = [(1, 105), (2, 10), (3, 105), (4, 10)]
    checkbox_cs = [(1, 25), (3, 15)]
    cmds.separator(height=10, style='none')  # Empty Space
    cmds.rowColumnLayout(numberOfColumns=4, columnWidth=checkbox_cw,
                         columnSpacing=checkbox_cs, parent=content_main)

    # CONNECT TOES AND SPINE
    cmds.checkBox(label='Connect Toes', value=settings.get('connect_toes'),
                  cc=partial(_btn_refresh_textfield_settings_data, 'connect_toes'))

    help_message_connect_toes = 'This option will look at the first child of the ankle joint and use it as the ' \
                                'toe joint. It will then extract the toe joint rotation based on the neutral ' \
                                'pose of the model (defined in the first frame of your timeline)\nFor better ' \
                                'results, make sure the pose of your mocap skeleton and your character very similar' \
                                'in the first frame of the timeline. If using "-1", make sure the current time ' \
                                'field has access to it within the range.'
    help_title_connect_toes = 'Connect Toes'

    cmds.button(l='?', bgc=help_bgc_color, height=5, c=partial(build_custom_help_window,
                                                               help_message_connect_toes,
                                                               help_title_connect_toes))

    cmds.checkBox(label='Reconnect Spine', value=settings.get('reconnect_spine'),
                  cc=partial(_btn_refresh_textfield_settings_data, 'reconnect_spine'))

    help_message_reconnect_spine = 'This option will replace the data received from HumanIK and transfer the ' \
                                   'rotation directly from the spine joints to the rig controls.\n\n' \
                                   'WARNING: It might sometimes look funny or exaggerated because there is no scale ' \
                                   'compensation happening.\nTo fix that, you can use the influence slider or ' \
                                   'compress/expand the entire animation till the desired result is achieved.'
    help_title_reconnect_spine = 'Reconnect Spine'

    cmds.button(l='?', bgc=help_bgc_color, height=5, c=partial(build_spine_help_window,
                                                               help_message_reconnect_spine,
                                                               help_title_reconnect_spine))

    cmds.separator(height=5, style='none')  # Empty Space
    cmds.rowColumnLayout(numberOfColumns=4, columnWidth=checkbox_cw,
                         columnSpacing=checkbox_cs, parent=content_main)

    # CONNECT FINGERS AND TRANSFER IK

    cmds.checkBox(label='Connect Fingers', value=settings.get('connect_fingers'),
                  cc=partial(_btn_refresh_textfield_settings_data, 'connect_fingers'))

    help_message_connect_fingers = 'This option will extract the rotation of the finger joints that were defined ' \
                                   'through the HumanIK definition. If nothing was defined, nothing will be ' \
                                   'transferred. Much like the toe option, this option extracts whatever pose was ' \
                                   'left under the first frame of your timeline.\n\nInvert Finger Rotation: ' \
                                   'Makes the main rotation (usually "Z") rotate in the opposite direction, which ' \
                                   'can help motion capture skeletons with unexpected orientations become compatible.'
    help_title_connect_fingers = 'Connect Fingers'

    cmds.button(l='?', bgc=help_bgc_color, height=5, c=partial(build_fingers_help_window,
                                                               help_message_connect_fingers,
                                                               help_title_connect_fingers))

    cmds.checkBox(label='Leg Stabilization', value=settings.get('leg_stabilization'),
                  cc=partial(_btn_refresh_textfield_settings_data, 'leg_stabilization'))

    help_message_leg_stabilization = 'This option will use the IK rig to collect the correct rotation data from ' \
                                     'the position of the mocap skeleton. This helps enforce the correct foot ' \
                                     'placement. This option only works with rigs published after 2022-Mar-07.'
    help_title_leg_stabilization = 'Leg Stabilization'

    cmds.button(l='?', bgc=help_bgc_color, height=5, c=partial(build_custom_help_window,
                                                               help_message_leg_stabilization,
                                                               help_title_leg_stabilization))

    cmds.separator(height=5, style='none')  # Empty Space
    cmds.rowColumnLayout(numberOfColumns=4, columnWidth=checkbox_cw,
                         columnSpacing=checkbox_cs, parent=content_main)

    # UNLOCK ROTATIONS AND MERGE FK AXIS
    cmds.checkBox(label='Unlock Rotations', value=settings.get('unlock_rotations'),
                  cc=partial(_btn_refresh_textfield_settings_data, 'unlock_rotations'))

    help_message_unlock_rotations = 'WARNING: This option should not be used for all bakes.\nIt will unlock all ' \
                                    'rotations allowing for the knee and elbow to receive rotation data into any ' \
                                    'axis. This might be desired in some cases when counter rotation is happening, ' \
                                    'but keep in mind that the data will lose some precision when transferred to IK,' \
                                    'due to plane rotation nature of the IK solver. Consider using the option "Merge' \
                                    ' FK axis" to re-bake the FK controls back into one single plane rotation.'
    help_title_unlock_rotations = 'Unlock Rotations'

    cmds.button(l='?', bgc=help_bgc_color, height=5, c=partial(build_custom_help_window,
                                                               help_message_unlock_rotations,
                                                               help_title_unlock_rotations))

    cmds.checkBox('ch_merge_axis', label='Merge FK Axis', value=settings.get('merge_axis'), en=False,
                  cc=partial(_btn_refresh_textfield_settings_data, 'merge_axis'))

    help_message_merge_fk_axis = 'This option can only be used when "Unlock Rotations" is active. ' \
                                 'It transfers the data to IK causing the channels to merge and then transfer ' \
                                 'it back into FK, making the animation live into only one channel instead of ' \
                                 'multiple channels.\nEven though it might look slightly incorrect, it ' \
                                 'might give you data that is easier to handle, essentially eliminating some ' \
                                 'counter rotations.'

    help_title_merge_fk_axis = 'Merge FK Axis'

    cmds.button(l='?', bgc=help_bgc_color, height=5, c=partial(build_custom_help_window,
                                                               help_message_merge_fk_axis,
                                                               help_title_merge_fk_axis))

    cmds.rowColumnLayout(numberOfColumns=1, columnWidth=[(1, 260), (2, 120)],
                         columnSpacing=[(1, 20)], parent=content_main)
    cmds.separator(height=15, style='none')  # Empty Space

    # Target TF
    cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 120), (2, 120), (3, 15)],
                         columnSpacing=[(1, 15), (3, 5)], parent=content_main)

    cmds.text('HIK Character / Target:')
    hik_target_textfield = cmds.textField(placeholderText='HIK Target Character',
                                          cc=partial(_btn_refresh_textfield_hik_data),
                                          ann='target')
    cmds.button(label="P", backgroundColor=(.3, .3, .3),
                c=partial(_btn_select_properties, hik_target_textfield))

    cmds.separator(height=5, style='none')  # Empty Space

    # Source TF
    cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 120), (2, 120), (3, 15)],
                         columnSpacing=[(1, 15), (3, 5)], parent=content_main)

    cmds.text('HIK Mocap / Source:')
    hik_source_textfield = cmds.textField(placeholderText='HIK Source Character',
                                          cc=partial(_btn_refresh_textfield_hik_data),
                                          ann='source')
    cmds.button(label="P", backgroundColor=(.3, .3, .3),
                c=partial(_btn_select_properties, hik_source_textfield))

    #  Buttons
    cmds.rowColumnLayout(numberOfColumns=1, columnWidth=[(1, 260), (2, 120)],
                         columnSpacing=[(1, 20)], parent=content_main)
    cmds.separator(height=15, style='none')  # Empty Space

    cmds.button(label="Get Current Target/Source", backgroundColor=(.3, .3, .3), c=_btn_target_source_textfield)

    cmds.separator(height=10, style='none')  # Empty Space

    cmds.button(label="Bake Mocap with Fixes", backgroundColor=(.3, .3, .3), c=_btn_bake_mocap_with_fixes)
    cmds.separator(height=5, style='none')  # Empty Space

    cmds.separator(height=15, style='none')  # Empty Space

    # Get Current - Refresh
    _btn_target_source_textfield()

    # Show and Lock Window
    cmds.showWindow(build_gui_world_space_baker)
    cmds.window(window_name, e=True, sizeable=False)


def build_custom_help_window(input_text, help_title='', *args):
    """
    Creates a help window to display the provided text

    Args:
        input_text (string): Text used as help, this is displayed in a scroll fields.
        help_title (optional, string)

    Returns:
        body_column: Used to add more UI elements in case the help menu needs it
    """
    logger.debug(str(args))
    window_name = help_title.replace(" ", "_").replace("-", "_").lower().strip() + "_help_window"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title=help_title + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    main_column = cmds.columnLayout(p=window_name)

    # Title Text
    cmds.separator(h=12, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p=main_column)  # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)  # Title Column
    cmds.text(help_title + ' Help', bgc=(.4, .4, .4), fn='boldLabelFont', align='center')
    cmds.separator(h=10, style='none', p=main_column)  # Empty Space

    # Body ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)

    help_scroll_field = cmds.scrollField(editable=False, wordWrap=True, fn='smallPlainLabelFont')

    cmds.scrollField(help_scroll_field, e=True, ip=0, it=input_text)
    cmds.scrollField(help_scroll_field, e=True, ip=1, it='')  # Bring Back to the Top

    return_column = cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)

    # Close Button
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)
    cmds.separator(h=10, style='none')
    cmds.button(l='OK', h=30, c=lambda x: close_help_gui())
    cmds.separator(h=8, style='none')

    # Show and Lock Window
    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/question.png')
    widget.setWindowIcon(icon)

    def close_help_gui():
        """ Closes help windows """
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)

    return return_column


def build_fingers_help_window(input_text, help_title='', *args):
    """
    Creates a help window to display the provided text

    Args:
        input_text (string): Text used as help, this is displayed in a scroll fields.
        help_title (optional, string)

    Returns:
        body_column: Used to add more UI elements in case the help menu needs it
    """
    def invert_finger_orientation(*current_state):
        logger.debug('is_finger_inverted: ' + str(current_state[0]))
        sys.stdout.write('\nInvert Finger Rotation Set To : ' + str(current_state[0]))
        settings['is_finger_inverted'] = current_state[0]

    logger.debug(str(args))
    column_extra_functions = build_custom_help_window(input_text, help_title=help_title)
    cmds.rowColumnLayout(column_extra_functions, e=True, nc=1, cw=[(1, 260)], cs=[(1, 30)])
    cmds.separator(h=10, style='none', p=column_extra_functions)
    cmds.checkBox(label='Invert Finger Rotation (Opposite Rotate Direction)',
                  value=settings.get('is_finger_inverted'),
                  p=column_extra_functions, cc=invert_finger_orientation)


def build_spine_help_window(input_text, help_title='', *args):
    """
    Creates a help window to display the provided text

    Args:
        input_text (string): Text used as help, this is displayed in a scroll fields.
        help_title (optional, string)

    Returns:
        body_column: Used to add more UI elements in case the help menu needs it
    """
    def set_spine_influence(*current_state):
        logger.debug('spine_influence: ' + str(current_state[0]))
        sys.stdout.write('\nSpine Influence Set To : ' + '% 6.2f' % current_state[0])
        settings['spine_influence'] = current_state[0]

    def set_spine_inversion(*current_state):
        logger.debug(current_state[0] + ': ' + str(current_state[1]))
        dimension = current_state[0].replace('is_spine_inverted_', '')
        sys.stdout.write('\nInvert Spine ' + dimension.capitalize() + ' Rotation Set To : ' + str(current_state[1]))
        settings[current_state[0]] = current_state[1]

    logger.debug(str(args))
    column_extra_functions = build_custom_help_window(input_text, help_title=help_title)
    cmds.separator(h=10, style='none', p=column_extra_functions)
    cmds.rowColumnLayout(column_extra_functions, e=True, nc=1, cw=[(1, 260)], cs=[(1, 30)])
    column_inversion = cmds.rowColumnLayout(nc=3, cw=[(1, 60), (2, 60), (3, 60)],
                                            cs=[(1, 10), (2, 30), (3, 30)],
                                            p=column_extra_functions)
    cmds.checkBox(label='Invert X',
                  value=settings.get('is_spine_inverted_x'),
                  p=column_inversion, cc=partial(set_spine_inversion, 'is_spine_inverted_x'))
    cmds.checkBox(label='Invert Y',
                  value=settings.get('is_spine_inverted_y'),
                  p=column_inversion, cc=partial(set_spine_inversion, 'is_spine_inverted_y'))
    cmds.checkBox(label='Invert Z',
                  value=settings.get('is_spine_inverted_z'),
                  p=column_inversion, cc=partial(set_spine_inversion, 'is_spine_inverted_z'))

    cmds.separator(h=10, style='none', p=column_extra_functions)
    cmds.floatSliderGrp(label='Spine Influence', field=True, minValue=0, maxValue=100, fieldMinValue=0,
                        fieldMaxValue=10000, value=settings.get('spine_influence'), cw=([1, 70], [2, 70]),
                        p=column_extra_functions, cc=set_spine_influence)


def is_hik_character_valid(char):
    """
    Checks if a HumanIK character definition is valid
    Args:
        char (string): Name of the HIK Character
    """
    if not cmds.objExists(char):
        return False

    if cmds.objectType(char) != 'HIKCharacterNode':
        return False
    return True


def get_hik_properties_node(char):
    if not is_hik_character_valid(char):
        raise Exception("Couldn't find character definition for: \"" + char + '".')
    try:
        property_node = mel.eval('catchQuiet(getProperty2StateFrocmdsharacter("' + char + '"))')
        if property_node == 1:
            raise Exception("MEL getProperty2State command failed.")
    except Exception as e:
        logger.debug(str(e))
        source_connection = cmds.listConnections(char + '.propertyState', s=True, d=False) or []
        if not source_connection:
            raise Exception("Couldn't find \"HIKProperty2State\" node from character \"" + char + "\".")

        elif len(source_connection) > 1:
            logger.info("Multiple \"HIKProperty2State\" nodes found. First source connection will be used.")

        property_node = source_connection[0]
    return property_node


def get_hik_retarget_node(char):
    if not is_hik_character_valid(char):
        raise Exception("Couldn't find character definition for: \"" + char + '".')

    source_connection = cmds.ls(cmds.listConnections(char + '.OutputCharacterDefinition', d=True, s=False) or [],
                                typ='HIKRetargeterNode')
    if not source_connection:
        logger.info("Couldn't find \"HIKRetargeterNode\" node from character \"" + char + "\".")
        return ''

    if len(source_connection) > 1:
        logger.info("Multiple \"HIKRetargeterNode\" nodes found. First target connection will be used.")

    return source_connection[0]


def get_hik_solver_node(char):
    if not is_hik_character_valid(char):
        raise Exception("Couldn't find character definition for: \"" + char + '".')

    source_connection = cmds.ls(cmds.listConnections(char + '.OutputCharacterDefinition', d=True, s=False) or [],
                                typ='HIKSolverNode')
    if not source_connection:
        raise Exception("Couldn't find \"HIKSolverNode\" node from character \"" + char + "\".")

    if len(source_connection) > 1:
        logger.info("Multiple \"HIKSolverNode\" nodes found. First target connection will be used.")

    return source_connection[0]


def get_hik_source(char):
    # Try to get it through the menu
    try:
        option_menu_group_list = cmds.lsUI(l=True, type="optionMenuGrp")
        ui_hik_source = None
        for ui in option_menu_group_list:
            if "hikSourceList" in ui:
                ui_hik_source = cmds.optionMenuGrp(ui, q=True, value=True)
        if ui_hik_source:
            if ui_hik_source == " None":
                return ''
            else:
                return ui_hik_source
    # Attempt to find through nodes
    except Exception as exception:
        logger.info(str(exception))
        logger.info('Failed to get HIK Source through Menu, attempting to find node through connections.')

        if not is_hik_character_valid(char):
            logger.debug("Couldn't find character definition for: \"" + char + '".')
            return ''

        retarget_node = get_hik_retarget_node(char)
        if retarget_node:
            source_connection = cmds.ls(cmds.listConnections(retarget_node + '.InputCharacterDefinitionSrc',
                                                             d=False, s=True) or [], typ='HIKCharacterNode')
            if not source_connection:
                return ''

            if len(source_connection) > 1:
                logger.info("Multiple \"HIKCharacterNode\" nodes found. First target connection will be used.")

            return source_connection[0]
        else:
            return ''


def get_orientation(obj, return_type='point'):
    """
    Get an objects' orientation WIP

    Args:
        obj (str)(obj) = The object to get the orientation of.
        return_type (str) = The desired returned value type. (valid: 'point', 'vector') (default: 'point')

    Returns:
        output_tuple (tuple):
    """
    obj = cmds.ls(obj)[0]

    world_matrix = cmds.xform(obj, q=True, m=True, ws=True)
    r_axis = cmds.getAttr(obj + '.rotateAxis') or []
    if r_axis:
        r_axis = r_axis[0]
    if any((r_axis[0], r_axis[1], r_axis[2])):
        logger.info('"' + obj + '" has a modified .rotateAxis which is included in the orientation result')

    if return_type is 'vector':
        output_tuple = (MVector(world_matrix[0:3]),
                        MVector(world_matrix[4:7]),
                        MVector(world_matrix[8:11]))
    else:
        output_tuple = (world_matrix[0:3],
                        world_matrix[4:7],
                        world_matrix[8:11])

    x_up = MVector(output_tuple[0]) * MVector(1, 0, 0)
    y_up = MVector(output_tuple[1]) * MVector(0, 1, 0)
    z_up = MVector(output_tuple[2]) * MVector(0, 0, 1)
    print('x_up"' + str(x_up))
    print('y_up"' + str(y_up))
    print('z_up"' + str(z_up))
    # print(output_tuple)
    return output_tuple


def dist_center_to_center(obj_a, obj_b):
    """
    Calculates the position between the center of one object (A)  to the center of another object (B)

    Args:
        obj_a (string) : Name of object A
        obj_b (string) : Name of object B

    Returns:
        distance (float): A distance value between object A and B. For example : 4.0
    """

    def dist_position_to_position(pos_a_x, pos_a_y, pos_a_z, pos_b_x, pos_b_y, pos_b_z):
        """
            Calculates the distance between XYZ position A and XYZ position B

            Args:
                    pos_a_x (float) : Object A Position X
                    pos_a_y (float) : Object A Position Y
                    pos_a_z (float) : Object A Position Z
                    pos_b_x (float) : Object B Position X
                    pos_b_y (float) : Object B Position Y
                    pos_b_z (float) : Object B Position Z

            Returns:
                distance (float): A distance value between object A and B. For example : 4.0
            """
        dx = pos_a_x - pos_b_x
        dy = pos_a_y - pos_b_y
        dz = pos_a_z - pos_b_z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    # WS Center to Center Distance:
    cmds.select(obj_a, r=True)
    ws_pos_a = cmds.xform(q=True, ws=True, t=True)
    cmds.select(obj_b, r=True)
    ws_pos_b = cmds.xform(q=True, ws=True, t=True)
    return dist_position_to_position(ws_pos_a[0], ws_pos_a[1], ws_pos_a[2], ws_pos_b[0], ws_pos_b[1], ws_pos_b[2])


def get_joint_orientation(obj, expected_up=(0, 1, 0)):
    unique_name = '_' + str(random.random())
    obj_child = cmds.listRelatives(obj, children=True, fullPath=True) or []
    if obj_child:
        obj_child = obj_child[0]

    distance_from_child = dist_center_to_center(obj, obj_child)

    temp_loc = cmds.spaceLocator(name=obj + unique_name)[0]
    temp_loc_grp = cmds.group(world=True, empty=True, name=obj + 'Grp' + unique_name)
    temp_child_loc = cmds.spaceLocator(name=obj + 'Child' + unique_name)[0]
    temp_child_loc_grp = cmds.group(world=True, empty=True, name=obj + 'ChildGrp' + unique_name)
    cmds.parent(temp_loc, temp_loc_grp)
    cmds.parent(temp_child_loc, temp_child_loc_grp)
    cmds.delete(cmds.parentConstraint(obj, temp_loc_grp))
    cmds.delete(cmds.parentConstraint(obj_child, temp_child_loc_grp))

    # Find Aim Axis
    aim_distance_xyz = {'x': 0, 'y': 0, 'z': 0}
    aim_distance_state_xyz = {'x': '', 'y': '', 'z': ''}
    move_distance = distance_from_child * .5
    # X
    cmds.move(move_distance, 0, 0, temp_loc, relative=True, os=True)
    pos_x = dist_center_to_center(temp_loc, obj_child)
    cmds.delete(cmds.parentConstraint(obj, temp_loc))
    cmds.move(-move_distance, 0, 0, temp_loc, relative=True, os=True)
    neg_x = dist_center_to_center(temp_loc, obj_child)
    aim_distance_x = min([pos_x, neg_x])
    if aim_distance_x == pos_x:
        aim_distance_state_xyz['x'] = "+"
    else:
        aim_distance_state_xyz['x'] = "-"
    aim_distance_xyz['x'] = aim_distance_x
    cmds.delete(cmds.parentConstraint(obj, temp_loc))  # Reset Loc
    # Y
    cmds.move(0, move_distance, 0, temp_loc, relative=True, os=True)
    pos_y = dist_center_to_center(temp_loc, obj_child)
    cmds.delete(cmds.parentConstraint(obj, temp_loc))
    cmds.move(0, -move_distance, 0, temp_loc, relative=True, os=True)
    neg_y = dist_center_to_center(temp_loc, obj_child)
    aim_distance_y = min([pos_y, neg_y])
    if aim_distance_y == pos_y:
        aim_distance_state_xyz['y'] = "+"
    else:
        aim_distance_state_xyz['y'] = "-"
    aim_distance_xyz['y'] = aim_distance_y
    cmds.delete(cmds.parentConstraint(obj, temp_loc))  # Reset Loc
    # Z
    cmds.move(0, 0, move_distance, temp_loc, relative=True, os=True)
    pos_z = dist_center_to_center(temp_loc, obj_child)
    cmds.delete(cmds.parentConstraint(obj, temp_loc))
    cmds.move(0, 0, -move_distance, temp_loc, relative=True, os=True)
    neg_z = dist_center_to_center(temp_loc, obj_child)
    aim_distance_z = min([pos_z, neg_z])
    if aim_distance_z == pos_z:
        aim_distance_state_xyz['z'] = "+"
    else:
        aim_distance_state_xyz['z'] = "-"
    aim_distance_xyz['z'] = aim_distance_z
    cmds.delete(cmds.parentConstraint(obj, temp_loc))  # Reset Loc

    orientation_aim_axis = min(aim_distance_xyz, key=aim_distance_xyz.get)

    # Find Up
    temp_world_up_loc = cmds.spaceLocator(name=obj + 'worldUp' + unique_name)[0]
    up_distance_xyz = {'x': None, 'y': None, 'z': None}
    up_distance_state_xyz = {'x': '', 'y': '', 'z': ''}
    # X Up
    if orientation_aim_axis != 'x':
        cmds.delete(cmds.pointConstraint(obj, temp_world_up_loc))
        cmds.move(expected_up[0]*move_distance, expected_up[1]*move_distance, expected_up[2]*move_distance,
                  temp_world_up_loc, relative=True, os=True)
        cmds.move(move_distance, 0, 0, temp_loc, relative=True, os=True)
        pos_x = dist_center_to_center(temp_loc, temp_world_up_loc)
        cmds.delete(cmds.parentConstraint(obj, temp_loc))
        cmds.move(-move_distance, 0, 0, temp_loc, relative=True, os=True)
        neg_x = dist_center_to_center(temp_loc, temp_world_up_loc)
        up_distance_x = min([pos_x, neg_x])
        if up_distance_x == pos_x:
            up_distance_state_xyz['x'] = "+"
        else:
            up_distance_state_xyz['x'] = "-"
        up_distance_xyz['x'] = up_distance_x
    # Y Up
    if orientation_aim_axis != 'y':
        cmds.delete(cmds.pointConstraint(obj, temp_world_up_loc))
        cmds.move(expected_up[0] * move_distance, expected_up[1] * move_distance, expected_up[2] * move_distance,
                  temp_world_up_loc, relative=True, os=True)
        cmds.move(0, move_distance, 0, temp_loc, relative=True, os=True)
        pos_y = dist_center_to_center(temp_loc, temp_world_up_loc)
        cmds.delete(cmds.parentConstraint(obj, temp_loc))
        cmds.move(0, -move_distance, 0, temp_loc, relative=True, os=True)
        neg_y = dist_center_to_center(temp_loc, temp_world_up_loc)
        up_distance_y = min([pos_y, neg_y])
        if up_distance_y == pos_y:
            up_distance_state_xyz['y'] = "+"
        else:
            up_distance_state_xyz['y'] = "-"
        up_distance_xyz['y'] = up_distance_y
    # Z Up
    if orientation_aim_axis != 'z':
        cmds.delete(cmds.pointConstraint(obj, temp_world_up_loc))
        cmds.move(expected_up[0] * move_distance, expected_up[1] * move_distance, expected_up[2] * move_distance,
                  temp_world_up_loc, relative=True, os=True)
        cmds.move(0, 0, move_distance, temp_loc, relative=True, os=True)
        pos_z = dist_center_to_center(temp_loc, temp_world_up_loc)
        cmds.delete(cmds.parentConstraint(obj, temp_loc))
        cmds.move(0, 0, -move_distance, temp_loc, relative=True, os=True)
        neg_z = dist_center_to_center(temp_loc, temp_world_up_loc)
        up_distance_z = min([pos_z, neg_z])
        if up_distance_z == pos_z:
            up_distance_state_xyz['z'] = "+"
        else:
            up_distance_state_xyz['z'] = "-"
        up_distance_xyz['z'] = up_distance_z

    remaining_axis = {}
    for key in up_distance_xyz:
        if up_distance_xyz.get(key) is not None:
            remaining_axis[key] = up_distance_xyz.get(key)

    orientation_up_axis = min(remaining_axis, key=remaining_axis.get)
    # orientation_main_axis = max(remaining_axis, key=remaining_axis.get)
    orientation_main_axis = 'xyz'.replace(orientation_up_axis, '').replace(orientation_aim_axis, '')  # Remaining Axis

    cmds.delete([temp_loc_grp, temp_child_loc_grp, temp_world_up_loc])

    if aim_distance_state_xyz.get(orientation_aim_axis).startswith('+'):
        up_distance_state_xyz[orientation_main_axis] = '+'
    else:
        up_distance_state_xyz[orientation_main_axis] = '-'

    aim_axis = str(aim_distance_state_xyz.get(orientation_aim_axis)) + str(orientation_aim_axis)
    up_axis = str(up_distance_state_xyz.get(orientation_up_axis)) + str(orientation_up_axis)

    main_axis = str(up_distance_state_xyz.get(orientation_main_axis)) + str(orientation_main_axis)

    # Pose Object Setup
    Orientation = namedtuple('Orientation', ['aim_axis', 'up_axis', 'main_axis'])

    cmds.select(obj)
    return Orientation(aim_axis=aim_axis, up_axis=up_axis, main_axis=main_axis)


# Build GUI / Tests
if __name__ == '__main__':
    # Debug Lines
    debugging_settings['is_debugging'] = False
    if debugging_settings.get('is_debugging'):
        logger.setLevel(logging.DEBUG)
        logger.debug('Logging Level Set To: ' + str(logger.level))

        # Enforce Pre-defined Character Names
        # debugging_settings['source'] = 'Source_Mocap'
        # debugging_settings['target'] = 'Target_Char'

        # Change Default Values
        settings['connect_toes'] = False
        settings['reconnect_spine'] = True
        settings['connect_fingers'] = False
        settings['leg_stabilization'] = False
        settings['unlock_rotations'] = False
        settings['merge_axis'] = False

        # Get/Set Camera Pos/Rot
        debugging_settings['reload_scene'] = True
        if debugging_settings.get('reload_scene'):
            persp_pos = cmds.getAttr('persp.translate')[0]
            persp_rot = cmds.getAttr('persp.rotate')[0]
            import gt_maya_utilities
            gt_maya_utilities.force_reload_file()
            cmds.viewFit(all=True)
            cmds.setAttr('persp.tx', persp_pos[0])
            cmds.setAttr('persp.ty', persp_pos[1])
            cmds.setAttr('persp.tz', persp_pos[2])
            cmds.setAttr('persp.rx', persp_rot[0])
            cmds.setAttr('persp.ry', persp_rot[1])
            cmds.setAttr('persp.rz', persp_rot[2])

    # Build GUI
    build_gui_mocap_rig()
