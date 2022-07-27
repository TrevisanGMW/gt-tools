"""
 GT Biped Rigger Logic
 github.com/TrevisanGMW - 2020-12-08

 1.0 - 2020-12-29
 Initial Release

 1.1 - 2021-01-03
 Renamed shapes
 Added joint labelling
 Added icons to buttons
 Added curves (lines) between proxies
 Changed and added a few notes
 Added manip default to all main controls
 Locked default channels for the main rig group
 Made rig setup elements visible after creation
 Updated stretchy system to avoid cycles or errors
 Updated stretchy system to account for any curvature
 Fixed possible scale cycle happening during control creation

 1.2 - 2021-01-04
 Changed stretchy system so it doesn't use floatConstant nodes
 Updated the import proxy function so it doesn't give an error when importing a different scale
 Added utility to automatically create and define a HumanIK character from the rig
 Added utility to toggle the visibility of all joint labels
 Created utility to add a seamless FK/IK switch script to the current shelf
 "followHip" (ankle proxies) attribute is not longer activated by default
 Fixed an issue where left arm ik would be generated with an offset in extreme angles

 1.3 - 2021-01-19
 Updated help window to better accommodate a high volume of text
 Added new utility to extract proxy pose from generated rig
 Updated export/import functions to be compatible with world-space
 Added version check to importer for backwards compatibility
 Added auto load for HumanIK plugin in case it's not loaded when attaching rig
 Patched a few small bugs, added colors to a few controls and updated the help text
 Changed forearm joints hierarchy so the rig can be easily exported in to game engines
 Moved the mechanics of the roll joints into the rig setup folder
 Updated the order of the groups inside the rig setup folder
 Added joint inflation/deflation system
 Switch the order and name of a few custom attributes (none of the keyable ones
 Switch the order of a few custom attributes (influenceSwitch was moved up)
 Added activation attribute to the main control for the joint inflation/deflation system
 Added counter rotation system to neckMid control so the shape stays in place when automated
 Fixed an issue where the right thumb wouldn't orient correctly
 Added finger abduction/adduction control and updated the name of a few attributes

 1.4 - 2021-01-25
 Created auto breathing system
 Added check for geometry group (common name)
 Updated "orient_to_target" function to enforce proxy direction properly
 Added manip default to the foot roll controls
 Fixed an issue where you wouldn't be able to import a JSON file for the beta versions
 Added negative rotation to adduction for more flexibility
 Added auto knuckle compression system (Translation Z Offset)
 Changed the data transfer type of the wrists from parentConstraint to raw to prevent flipping
 Created sin function without expressions
 Created a trigonometry sine function that doesn't use third-party plugins or expressions
 Added debugging option to auto import proxy templates and auto bind geometry
 Added a check for required plugins before running the script
 Changed the data transfer type of the clavicles to allow for offsets (for auto breathing)
 Added notes to the knee proxies (similar to elbows)

 1.5 - 2021-01-26
 Changed the names of a few nodes
 Updated the entire forearm and wrist joints system as they would sometimes flip
 Added attribute to head control to determine the visibility of the eye controls
 Updated right forearm connections so it goes into the correct direction
 Fixed undesired offset inherited from a broken node inside the auto breathing system
 Fixed an issue where the shape of some controls would stay opened
 Updated most curves to be created as periodic curves to avoid creation issues
 Fixed the direction of the right side FK/IK switch shapes

 1.6 - 2021-01-28
 Fixed an issue where the fingers would still move even when the stretchy system was deactivated
 Fixed another issue where the wrist joints would flip flipping
 Fixed issue where the spine controls would look locked when moving the cog control

 1.7 - 2021-02-05
 Fixed issue where the ik shoulders would sometimes flip during a main control rotation
 Unlocked translate Z for hip proxies

 1.7.1 - 2021-02-14
 Fixed issue where "right_forearm_jnt" would rotate to the wrong direction

 1.7.2 - 2021-05-10
 Made script compatible with Python 3 (Maya 2022+)

 1.7.3 - 2021-08-07
 Fixed an issue where the foot would sometimes be flipped when the angle of the leg is not perfectly straight (
 Enforce footToe ikHandle position)

 1.7.4 - 2021-10-10
 Fixed an issue where the rig would start flickering when following motion capture using a custom rig setup (HumanIK)
 Modified inflation/deflation system to use controls instead of inverseMatrix nodes (less convenient, but more robust)
 Removed extraction of hip rotation from the "Extra Proxy Pose From Generated Rig" to fix flipped issue
 Added debugging warning to GUI for when debugging mode is activated (Replaces script title next to help)
 Changed the "followName" attribute data type for the pole vector controls to float so interpolation is possible

 1.7.5 - 2021-10-19
 Added option to generate secondary skeleton used for game engines (no Segment Scale Compensate)
 Added option to create lines between pole vectors and their targets

 1.7.6 - 2021-10-20
 Created "settings" button and the GUI updates necessary to display it
 Created the base for persistent settings and implemented "User Real-time Skeleton" option
 Created a custom help window that takes strings as help inputs to display it to the user

 1.7.7 - 2021-10-21
 Changed the behavior for when creating a real-time skeleton so it overwrites the original skeleton

 1.7.8 - 2021-10-24
 Added aim lines to pole vectors and eye controls
 Added some missing documentation
 Fixed a missing connection between follow attributes and their constraints (pole vectors and eyes)

 1.7.9 - 2021-10-26
 Fixed an issue where the right IK switcher curve would sometimes not orient itself correctly
 Added parenting options to IK Switchers (chest, clavicle, world)

 1.7.10 - 2021-10-28
 Created more debugging options
 Created ribbon setup for the spine (IK Spine)
 Created IK/FK switcher for the new spine setup
 Made proxy limits optional
 Add option to mirror rigged pose. IK Only. (for animators)
 Added option to reset pose

 1.7.11 - 2021-10-29
 Changed the name of the seamless FK/IK button to "Custom Rig Interface" as it now carries pose management functions
 Big update to Custom Rig Interface. It can now mirror, reset, import and export poses.
 Created utility to toggle rigging specific attributes

 1.7.12 - 2021-11-01
 Minor patches applied to Custom Rig Interface script
 Created finger specific curl controls
 Added option to control visibility of the fingers

 1.7.13 - 2021-11-03
 Modified control notes a bit
 Changed the radius of the IK spine joints
 Created IK finger controls
 Included cog_ctrl IK visibility attributes under rigging specific attributes
 Updated order of the custom attributes under the finger controls (no more top separator)
 Fixed an issue where the right hand would receive an unnecessary offset on its abduction system

 1.7.14 - 2021-11-04
 Exposed rotation order attribute for a few controls

 1.7.15 - 2021-11-05
 Added missing rotation order attribute to feet
 Added a tagged version of the rotation order to the wrist
 Updated custom rig interface GUI
 Replaced a few repeating strings with general variables

 1.7.16 - 2021-11-08
 Big update to custom rig interface

 1.7.17 - 2021-11-08
 Fixed an issue where IK fingers wouldn't follow the correct preferred angle

 1.8.0 - 2021-11-15
 Changed IK Spine to cube control (With 3 hidden adjustment controls. Not visible by default)
 Changed IK Spine to be the default influence
 Secondary chest adjustment control only affects the chest, not the head (so you can keep line of sight)
 Arm pole vector controls now follow arm's plane instead of wrist
 Moved pole vector custom attributes to wrist for ease of access
 Added twist attributes to the pole vector controls for the arms (found under wrists)
 Added 3D visibility type shapes to IK feet and IK wrists
 Changed the source constraint for the feet stretchy system so it accounts for the roll controls

 1.8.1 - 2021-11-16
 Brought back the follow wrist option for the elbow pole vector controls
 Fixed elbow control issue (pole vector) would sometimes receive rotation from the spine (missing aim up dir)
 Slightly changed the shape of the IK spine control for a better starting point
 Moved the pole vector controls little bit further away during creation
 Created pole vector twist and parenting system for legs

 1.8.2 - 2021-11-17
 Slightly changed the initial hand and spine box shapes to better conform to the body shape
 Created auto clavicle system. Clavicle rotates based on wrist position (according to influence % under the wrist ctrl)
 Added option to define heel roll as a proxy step (This should allow for a quicker rig profile import/export)
 Gave proxy pose a default extension ".ppose" instead of just ".json" to avoid confusion with other scripts

 1.8.3 - 2021-11-18
 Added offset controls to wrists, chest, cog

 1.8.4 - 2021-11-19
 Added offset controls to feet

 1.8.5 - 2021-11-23
 Fixed an issue where right arm pole vector was receiving undesired offset due to new twisting system

 1.8.6 - 2021-11-24
 Created uniform orientation option
 Redefined the scale calculation system to rely on position calculation rather than joint X distance
 Updated stretchy system to accept different joint scale channels
 Removed tagged version of the rotation order enum

 1.8.7 - 2021-11-25
 Changed the general scale calculation slightly
 Fixed issue where spine04_ctrl curve would be rotated incorrectly when using uniform orients

 1.8.8 - 2021-11-29
 Updated the distance calculation method for legs and arms
 Created an option to output world-space IK controls instead of inheriting from the joints
 Changed rotation source for auto clavicle to account for world-space ik controls
 Recreated the IK Spine to support stretchy system and limit positioning while attached to the ribbon setup
 Added world-space IK support to IK spine
 Added refresh suspend function before operations to speedup rig creation
 Added metadata in form of an attribute (type string) attached to the main control (dictionary/json format)
 Added new FK/IK switching references to account for new wrist orientations

 1.8.9 - 2021-12-01
 Re-create the uniform orientation option to keep the orientation of the joints intact (use offset instead)

 1.8.10 - 2021-12-02
 Replaced "uniform_ctrl_orient" functionality to drive new offset orientation system
 Created new neck head influence system
 Added offset control to neck

 1.8.11 - 2021-12-10
 Fixed an issue where spine wouldn't move properly in Maya 2022 (Python 3)
 Split biped rigger file into a more MVC format (controller, model, view)

 1.8.12 - 2021-12-20
 Fixed flipping spine control
 Deactivated auto clavicle when switching to FK

 1.8.13 - 2021-12-21
 Added option to simplify spine
 Added option to eliminate center hip joint
 Renamed auto clavicle joints to "driver" instead of auto
 Renamed "cog" joint to be called "waist" to better describe it
 Renamed "spine04" joint to be called "chest" so it makes sense when simplified
 Fixed some code repetition for the finger abduction system
 Created sum input node for abduction system
 Added rotation to abduction system

 1.8.14 - 2021-12-22
 Fixed an issue where the finger compression system would pop when adjusted

 1.9.0 - 2022-01-15
 Dropped Python 2 support
 Separated scripts into logic, gui and data modules
 Added option to make FK controls uniform  - 2022-01-06
 Added reference locators with offset data to drive the FK/IK switch system
 Fixed junk data left in the chest offset control
 Ribbon controls are now affected by the uniform orientation option
 Updated auto clavicle system to use point constraints and not account for orientation
 Changed the default value of the neck to head influence to zero - 2022-01-07
 Commented out joint labelling section - 2022-01-13

 1.9.1 - 2022-01-15
 Commented out joint labelling section
 Fixed an issue where the ball ik handles for the feet would be inverted
 Created a more robust system for the forearm twist (aimLoc)
 Fixed an issue where the simplification of the spine would cause a rotation offset to happen to the upper body joints
 Changed output hierarchy so pelvis (hip) goes under the root joint for more retargeting compatibility

 1.9.2 to 1.9.12
 Fixed an issue where the ball ik handles for the feet would be inverted - 2022-01-17
 Created a more robust system for the forearm twist (aimLoc)  - 2022-01-28
 Fixed an issue where the simplification of the spine would cause a rotation offset to happen to the upper body joints
 Changed output hierarchy so pelvis (hip) goes under the root joint for more retargeting compatibility
 Added Distal Multiplier to automatic finger rotation system - 2022-01-31
 Added manual compression controls to the fingers - 2022-02-01
 Changed orientation of the right wrist to be uniform with left side (inverted scale) - 2022-02-02
 Added new toe_ik_ctrl to IK feet - 2022-02-22
 Fixed issue where right automation controls wouldn't follow the offset control
 Added inherit head roll and converge options to the eyes - 2022-03-08
 Changed the shape of the spine controls - 2022-03-15
 Changed the auto rotate spine attribute names to be the same
 Added shape switching system to FK spine controls
 Updated automated generated chest IK control for a better position prediction
 Changed the proxy skeleton (moved clavicles closer to one another and spine closer to hip)
 Added Z limit to auto clavicle system - 2022-04-20
 Added ramp-up system to auto clavicle system

 1.9.13 - 2022-06-30
 Added "biped_proxy_pose" stored as a string to main_ctrl

 1.9.14 - 2022-07-23
 Added logging
 Some PEP8 Cleanup

 1.9.15 - 2022-07-25
 Some PEP8 Cleanup

 TODO Biped Rigger:
    Transfer scale information from ik spine limit spine to spines
    Add option to leave all lock translation attributes off
    Allow Knee Pole Vector offset to be controlled by the hip_ctrl instead of the direction_ctrl only (with influence %)
    Make scale system and breathing system optional
    Add more roll joints (upper part of the arm, legs, etc)
    Add option to auto create proxy geo
    Fix "Use Real-time Skeleton" option (broken after new UI setup)
"""
from gt_rigger_utilities import *
from gt_rigger_data import *
from gt_shape_offset import offset_curve_shape
import maya.cmds as cmds
import logging
import random
import json
import re

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_rigger_biped_logic")
logger.setLevel(logging.INFO)


def create_proxy(data_biped):
    """
    Creates a proxy (guide) skeleton used to later generate entire rig

    Args:
        data_biped (GTBipedRiggerData) : Object containing naming and settings for the proxy creation
    """
    elements_default = data_biped.elements_default
    elements = data_biped.elements
    settings = data_biped.settings
    colorize_proxy = True
    proxy_finger_scale = 0.3
    proxy_end_joint_scale = 0.2

    if cmds.objExists(elements.get('main_proxy_grp')):
        cmds.warning('Proxy creation already in progress, please finish or delete it first.')
        return

    # Main
    main_crv = create_main_control(elements_default.get('main_crv'))
    main_grp = cmds.group(empty=True, world=True, name=elements_default.get('main_proxy_grp'))
    cmds.parent(main_crv, main_grp)

    # Root
    cog_proxy_crv = create_joint_curve(elements_default.get('cog_proxy_crv'), 1)
    root_proxy_grp = cmds.group(empty=True, world=True, name=cog_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(cog_proxy_crv, root_proxy_grp)
    cmds.move(0, 89.2, 0, root_proxy_grp)

    # Spine 1
    spine01_proxy_crv = create_joint_curve(elements_default.get('spine01_proxy_crv'), 0.5)
    spine01_proxy_grp = cmds.group(empty=True, world=True, name=spine01_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(spine01_proxy_crv, spine01_proxy_grp)
    cmds.move(0, 98.5, 0, spine01_proxy_grp)

    # Spine 2
    spine02_proxy_crv = create_joint_curve(elements_default.get('spine02_proxy_crv'), 0.5)
    spine02_proxy_grp = cmds.group(empty=True, world=True, name=spine02_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(spine02_proxy_crv, spine02_proxy_grp)
    cmds.move(0, 104.5, 0, spine02_proxy_grp)

    # Spine 3
    spine03_proxy_crv = create_joint_curve(elements_default.get('spine03_proxy_crv'), 0.5)
    spine03_proxy_grp = cmds.group(empty=True, world=True, name=spine03_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(spine03_proxy_crv, spine03_proxy_grp)
    cmds.move(0, 109.5, 0, spine03_proxy_grp)

    # Spine 4
    spine04_proxy_crv = create_joint_curve(elements_default.get('spine04_proxy_crv'), 1)
    spine04_proxy_grp = cmds.group(empty=True, world=True, name=spine04_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(spine04_proxy_crv, spine04_proxy_grp)
    cmds.move(0, 114.5, 0, spine04_proxy_grp)

    # Neck Base
    neck_base_proxy_crv = create_joint_curve(elements_default.get('neck_base_proxy_crv'), .5)
    neck_base_proxy_grp = cmds.group(empty=True, world=True, name=neck_base_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(neck_base_proxy_crv, neck_base_proxy_grp)
    cmds.move(0, 137.1, 0, neck_base_proxy_grp)

    # Neck Mid
    neck_mid_proxy_crv = create_joint_curve(elements_default.get('neck_mid_proxy_crv'), .2)
    neck_mid_proxy_grp = cmds.group(empty=True, world=True, name=neck_mid_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(neck_mid_proxy_crv, neck_mid_proxy_grp)
    cmds.move(0, 139.8, 0, neck_mid_proxy_grp)

    # Head
    head_proxy_crv = create_joint_curve(elements_default.get('head_proxy_crv'), .5)
    head_proxy_grp = cmds.group(empty=True, world=True, name=head_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(head_proxy_crv, head_proxy_grp)
    cmds.move(0, 142.4, 0, head_proxy_grp)

    # Head End
    head_end_proxy_crv = create_joint_curve(elements_default.get('head_end_proxy_crv'), .2)
    head_end_proxy_grp = cmds.group(empty=True, world=True, name=head_end_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(head_end_proxy_crv, head_end_proxy_grp)
    cmds.move(0, 160, 0, head_end_proxy_grp)

    # Jaw
    jaw_proxy_crv = create_joint_curve(elements_default.get('jaw_proxy_crv'), .5)
    jaw_proxy_grp = cmds.group(empty=True, world=True, name=jaw_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(jaw_proxy_crv, jaw_proxy_grp)
    cmds.move(0, 147.4, 2.35, jaw_proxy_grp)

    # Jaw End
    jaw_end_proxy_crv = create_joint_curve(elements_default.get('jaw_end_proxy_crv'), .2)
    jaw_end_proxy_grp = cmds.group(empty=True, world=True, name=jaw_end_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(jaw_end_proxy_crv, jaw_end_proxy_grp)
    cmds.move(0, 142.7, 10.8, jaw_end_proxy_grp)

    # Right Eye
    right_eye_proxy_crv = create_loc_joint_curve(elements_default.get('right_eye_proxy_crv'), .6)
    right_eye_proxy_grp = cmds.group(empty=True, world=True, name=right_eye_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_eye_proxy_crv, right_eye_proxy_grp)
    cmds.move(-3.5, 151.2, 8.7, right_eye_proxy_grp)

    # Left Eye
    left_eye_proxy_crv = create_loc_joint_curve(elements_default.get('left_eye_proxy_crv'), .6)
    left_eye_proxy_grp = cmds.group(empty=True, world=True, name=left_eye_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_eye_proxy_crv, left_eye_proxy_grp)
    cmds.move(3.5, 151.2, 8.7, left_eye_proxy_grp)

    # ################# Left Arm #################
    # Left Clavicle
    left_clavicle_proxy_crv = create_directional_joint_curve(elements_default.get('left_clavicle_proxy_crv'),
                                                             .5)
    left_clavicle_proxy_grp = cmds.group(empty=True, world=True, name=left_clavicle_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_clavicle_proxy_crv, left_clavicle_proxy_grp)
    cmds.move(3, 130.4, 0, left_clavicle_proxy_grp)

    # Left Shoulder
    left_shoulder_proxy_crv = create_joint_curve(elements_default.get('left_shoulder_proxy_crv'), .5)
    left_shoulder_proxy_grp = cmds.group(empty=True, world=True, name=left_shoulder_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_shoulder_proxy_crv, left_shoulder_proxy_grp)
    cmds.move(17.2, 130.4, 0, left_shoulder_proxy_grp)

    # Left Elbow
    left_elbow_proxy_crv = create_aim_joint_curve(elements_default.get('left_elbow_proxy_crv'), .5)
    left_elbow_proxy_grp = cmds.group(empty=True, world=True, name=left_elbow_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_elbow_proxy_crv, left_elbow_proxy_grp)
    cmds.move(37.7, 130.4, 0, left_elbow_proxy_grp)

    # Left Wrist
    left_wrist_proxy_crv = create_directional_joint_curve(elements_default.get('left_wrist_proxy_crv'), .6)
    left_wrist_proxy_grp = cmds.group(empty=True, world=True, name=left_wrist_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_wrist_proxy_crv, left_wrist_proxy_grp)
    cmds.move(58.2, 130.4, 0, left_wrist_proxy_grp)

    # Left Thumb
    left_thumb01_proxy_crv = create_directional_joint_curve(elements_default.get('left_thumb01_proxy_crv'),
                                                            proxy_finger_scale)
    left_thumb01_proxy_grp = cmds.group(empty=True, world=True, name=left_thumb01_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_thumb01_proxy_crv, left_thumb01_proxy_grp)
    cmds.move(60.8, 130.4, 2.9, left_thumb01_proxy_grp)

    left_thumb02_proxy_crv = create_directional_joint_curve(elements_default.get('left_thumb02_proxy_crv'),
                                                            proxy_finger_scale)
    left_thumb02_proxy_grp = cmds.group(empty=True, world=True, name=left_thumb02_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_thumb02_proxy_crv, left_thumb02_proxy_grp)
    cmds.move(60.8, 130.4, 7.3, left_thumb02_proxy_grp)

    left_thumb03_proxy_crv = create_directional_joint_curve(elements_default.get('left_thumb03_proxy_crv'),
                                                            proxy_finger_scale)
    left_thumb03_proxy_grp = cmds.group(empty=True, world=True, name=left_thumb03_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_thumb03_proxy_crv, left_thumb03_proxy_grp)
    cmds.move(60.8, 130.4, 11.7, left_thumb03_proxy_grp)

    left_thumb04_proxy_crv = create_directional_joint_curve(elements_default.get('left_thumb04_proxy_crv'),
                                                            proxy_end_joint_scale)
    left_thumb04_proxy_grp = cmds.group(empty=True, world=True, name=left_thumb04_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_thumb04_proxy_crv, left_thumb04_proxy_grp)
    cmds.move(60.8, 130.4, 16.3, left_thumb04_proxy_grp)

    # Left Index
    left_index01_proxy_crv = create_directional_joint_curve(elements_default.get('left_index01_proxy_crv'),
                                                            proxy_finger_scale)
    left_index01_proxy_grp = cmds.group(empty=True, world=True, name=left_index01_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_index01_proxy_crv, left_index01_proxy_grp)
    cmds.move(66.9, 130.4, 3.5, left_index01_proxy_grp)

    left_index02_proxy_crv = create_directional_joint_curve(elements_default.get('left_index02_proxy_crv'),
                                                            proxy_finger_scale)
    left_index02_proxy_grp = cmds.group(empty=True, world=True, name=left_index02_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_index02_proxy_crv, left_index02_proxy_grp)
    cmds.move(70.1, 130.4, 3.5, left_index02_proxy_grp)

    left_index03_proxy_crv = create_directional_joint_curve(elements_default.get('left_index03_proxy_crv'),
                                                            proxy_finger_scale)
    left_index03_proxy_grp = cmds.group(empty=True, world=True, name=left_index03_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_index03_proxy_crv, left_index03_proxy_grp)
    cmds.move(74.2, 130.4, 3.5, left_index03_proxy_grp)

    left_index04_proxy_crv = create_directional_joint_curve(elements_default.get('left_index04_proxy_crv'),
                                                            proxy_end_joint_scale)
    left_index04_proxy_grp = cmds.group(empty=True, world=True, name=left_index04_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_index04_proxy_crv, left_index04_proxy_grp)
    cmds.move(77.5, 130.4, 3.5, left_index04_proxy_grp)

    # Left Middle
    left_middle01_proxy_crv = create_directional_joint_curve(elements_default.get('left_middle01_proxy_crv'),
                                                             proxy_finger_scale)
    left_middle01_proxy_grp = cmds.group(empty=True, world=True, name=left_middle01_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_middle01_proxy_crv, left_middle01_proxy_grp)
    cmds.move(66.9, 130.4, 1.1, left_middle01_proxy_grp)

    left_middle02_proxy_crv = create_directional_joint_curve(elements_default.get('left_middle02_proxy_crv'),
                                                             proxy_finger_scale)
    left_middle02_proxy_grp = cmds.group(empty=True, world=True, name=left_middle02_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_middle02_proxy_crv, left_middle02_proxy_grp)
    cmds.move(70.7, 130.4, 1.1, left_middle02_proxy_grp)

    left_middle03_proxy_crv = create_directional_joint_curve(elements_default.get('left_middle03_proxy_crv'),
                                                             proxy_finger_scale)
    left_middle03_proxy_grp = cmds.group(empty=True, world=True, name=left_middle03_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_middle03_proxy_crv, left_middle03_proxy_grp)
    cmds.move(74.4, 130.4, 1.1, left_middle03_proxy_grp)

    left_middle04_proxy_crv = create_directional_joint_curve(elements_default.get('left_middle04_proxy_crv'),
                                                             proxy_end_joint_scale)
    left_middle04_proxy_grp = cmds.group(empty=True, world=True, name=left_middle04_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_middle04_proxy_crv, left_middle04_proxy_grp)
    cmds.move(78.0, 130.4, 1.1, left_middle04_proxy_grp)

    # Left Ring
    left_ring01_proxy_crv = create_directional_joint_curve(elements_default.get('left_ring01_proxy_crv'),
                                                           proxy_finger_scale)
    left_ring01_proxy_grp = cmds.group(empty=True, world=True, name=left_ring01_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_ring01_proxy_crv, left_ring01_proxy_grp)
    cmds.move(66.9, 130.4, -1.1, left_ring01_proxy_grp)

    left_ring02_proxy_crv = create_directional_joint_curve(elements_default.get('left_ring02_proxy_crv'),
                                                           proxy_finger_scale)
    left_ring02_proxy_grp = cmds.group(empty=True, world=True, name=left_ring02_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_ring02_proxy_crv, left_ring02_proxy_grp)
    cmds.move(70.4, 130.4, -1.1, left_ring02_proxy_grp)

    left_ring03_proxy_crv = create_directional_joint_curve(elements_default.get('left_ring03_proxy_crv'),
                                                           proxy_finger_scale)
    left_ring03_proxy_grp = cmds.group(empty=True, world=True, name=left_ring03_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_ring03_proxy_crv, left_ring03_proxy_grp)
    cmds.move(74, 130.4, -1.1, left_ring03_proxy_grp)

    left_ring04_proxy_crv = create_directional_joint_curve(elements_default.get('left_ring04_proxy_crv'),
                                                           proxy_end_joint_scale)
    left_ring04_proxy_grp = cmds.group(empty=True, world=True, name=left_ring04_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_ring04_proxy_crv, left_ring04_proxy_grp)
    cmds.move(77.5, 130.4, -1.1, left_ring04_proxy_grp)

    # Left Pinky
    left_pinky01_proxy_crv = create_directional_joint_curve(elements_default.get('left_pinky01_proxy_crv'),
                                                            proxy_finger_scale)
    left_pinky01_proxy_grp = cmds.group(empty=True, world=True, name=left_pinky01_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_pinky01_proxy_crv, left_pinky01_proxy_grp)
    cmds.move(66.3, 130.4, -3.2, left_pinky01_proxy_grp)

    left_pinky02_proxy_crv = create_directional_joint_curve(elements_default.get('left_pinky02_proxy_crv'),
                                                            proxy_finger_scale)
    left_pinky02_proxy_grp = cmds.group(empty=True, world=True, name=left_pinky02_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_pinky02_proxy_crv, left_pinky02_proxy_grp)
    cmds.move(69.6, 130.4, -3.2, left_pinky02_proxy_grp)

    left_pinky03_proxy_crv = create_directional_joint_curve(elements_default.get('left_pinky03_proxy_crv'),
                                                            proxy_finger_scale)
    left_pinky03_proxy_grp = cmds.group(empty=True, world=True, name=left_pinky03_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_pinky03_proxy_crv, left_pinky03_proxy_grp)
    cmds.move(72.8, 130.4, -3.2, left_pinky03_proxy_grp)

    left_pinky04_proxy_crv = create_directional_joint_curve(elements_default.get('left_pinky04_proxy_crv'),
                                                            proxy_end_joint_scale)
    left_pinky04_proxy_grp = cmds.group(empty=True, world=True, name=left_pinky04_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_pinky04_proxy_crv, left_pinky04_proxy_grp)
    cmds.move(76.3, 130.4, -3.2, left_pinky04_proxy_grp)

    # ################# Right Arm #################
    # Right Clavicle
    right_clavicle_proxy_crv = create_directional_joint_curve(
        elements_default.get('right_clavicle_proxy_crv'), .5)
    right_clavicle_proxy_grp = cmds.group(empty=True, world=True,
                                          name=right_clavicle_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_clavicle_proxy_crv, right_clavicle_proxy_grp)
    cmds.move(-3, 130.4, 0, right_clavicle_proxy_grp)

    # Right Shoulder
    right_shoulder_proxy_crv = create_joint_curve(elements_default.get('right_shoulder_proxy_crv'), .5)
    right_shoulder_proxy_grp = cmds.group(empty=True, world=True,
                                          name=right_shoulder_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_shoulder_proxy_crv, right_shoulder_proxy_grp)
    cmds.move(-17.2, 130.4, 0, right_shoulder_proxy_grp)

    # Right Elbow
    right_elbow_proxy_crv = create_aim_joint_curve(elements_default.get('right_elbow_proxy_crv'), .5)
    right_elbow_proxy_grp = cmds.group(empty=True, world=True, name=right_elbow_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_elbow_proxy_crv, right_elbow_proxy_grp)
    cmds.move(-37.7, 130.4, 0, right_elbow_proxy_grp)

    # Right Wrist
    right_wrist_proxy_crv = create_directional_joint_curve(elements_default.get('right_wrist_proxy_crv'), .6)
    right_wrist_proxy_grp = cmds.group(empty=True, world=True, name=right_wrist_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_wrist_proxy_crv, right_wrist_proxy_grp)
    cmds.move(-58.2, 130.4, 0, right_wrist_proxy_grp)

    # Right Thumb
    right_thumb01_proxy_crv = create_directional_joint_curve(elements_default.get('right_thumb01_proxy_crv'),
                                                             proxy_finger_scale)
    right_thumb01_proxy_grp = cmds.group(empty=True, world=True, name=right_thumb01_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_thumb01_proxy_crv, right_thumb01_proxy_grp)
    cmds.move(-60.8, 130.4, 2.9, right_thumb01_proxy_grp)

    right_thumb02_proxy_crv = create_directional_joint_curve(elements_default.get('right_thumb02_proxy_crv'),
                                                             proxy_finger_scale)
    right_thumb02_proxy_grp = cmds.group(empty=True, world=True, name=right_thumb02_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_thumb02_proxy_crv, right_thumb02_proxy_grp)
    cmds.move(-60.8, 130.4, 7.3, right_thumb02_proxy_grp)

    right_thumb03_proxy_crv = create_directional_joint_curve(elements_default.get('right_thumb03_proxy_crv'),
                                                             proxy_finger_scale)
    right_thumb03_proxy_grp = cmds.group(empty=True, world=True, name=right_thumb03_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_thumb03_proxy_crv, right_thumb03_proxy_grp)
    cmds.move(-60.8, 130.4, 11.7, right_thumb03_proxy_grp)

    right_thumb04_proxy_crv = create_directional_joint_curve(elements_default.get('right_thumb04_proxy_crv'),
                                                             proxy_end_joint_scale)
    right_thumb04_proxy_grp = cmds.group(empty=True, world=True, name=right_thumb04_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_thumb04_proxy_crv, right_thumb04_proxy_grp)
    cmds.move(-60.8, 130.4, 16.3, right_thumb04_proxy_grp)

    # Right Index
    right_index01_proxy_crv = create_directional_joint_curve(elements_default.get('right_index01_proxy_crv'),
                                                             proxy_finger_scale)
    right_index01_proxy_grp = cmds.group(empty=True, world=True, name=right_index01_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_index01_proxy_crv, right_index01_proxy_grp)
    cmds.move(-66.9, 130.4, 3.5, right_index01_proxy_grp)

    right_index02_proxy_crv = create_directional_joint_curve(elements_default.get('right_index02_proxy_crv'),
                                                             proxy_finger_scale)
    right_index02_proxy_grp = cmds.group(empty=True, world=True, name=right_index02_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_index02_proxy_crv, right_index02_proxy_grp)
    cmds.move(-70.1, 130.4, 3.5, right_index02_proxy_grp)

    right_index03_proxy_crv = create_directional_joint_curve(elements_default.get('right_index03_proxy_crv'),
                                                             proxy_finger_scale)
    right_index03_proxy_grp = cmds.group(empty=True, world=True, name=right_index03_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_index03_proxy_crv, right_index03_proxy_grp)
    cmds.move(-74.2, 130.4, 3.5, right_index03_proxy_grp)

    right_index04_proxy_crv = create_directional_joint_curve(elements_default.get('right_index04_proxy_crv'),
                                                             proxy_end_joint_scale)
    right_index04_proxy_grp = cmds.group(empty=True, world=True, name=right_index04_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_index04_proxy_crv, right_index04_proxy_grp)
    cmds.move(-77.5, 130.4, 3.5, right_index04_proxy_grp)

    # Right Middle
    right_middle01_proxy_crv = create_directional_joint_curve(
        elements_default.get('right_middle01_proxy_crv'),
        proxy_finger_scale)
    right_middle01_proxy_grp = cmds.group(empty=True, world=True,
                                          name=right_middle01_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_middle01_proxy_crv, right_middle01_proxy_grp)
    cmds.move(-66.9, 130.4, 1.1, right_middle01_proxy_grp)

    right_middle02_proxy_crv = create_directional_joint_curve(
        elements_default.get('right_middle02_proxy_crv'),
        proxy_finger_scale)
    right_middle02_proxy_grp = cmds.group(empty=True, world=True,
                                          name=right_middle02_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_middle02_proxy_crv, right_middle02_proxy_grp)
    cmds.move(-70.7, 130.4, 1.1, right_middle02_proxy_grp)

    right_middle03_proxy_crv = create_directional_joint_curve(
        elements_default.get('right_middle03_proxy_crv'),
        proxy_finger_scale)
    right_middle03_proxy_grp = cmds.group(empty=True, world=True,
                                          name=right_middle03_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_middle03_proxy_crv, right_middle03_proxy_grp)
    cmds.move(-74.4, 130.4, 1.1, right_middle03_proxy_grp)

    right_middle04_proxy_crv = create_directional_joint_curve(
        elements_default.get('right_middle04_proxy_crv'),
        proxy_end_joint_scale)
    right_middle04_proxy_grp = cmds.group(empty=True, world=True,
                                          name=right_middle04_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_middle04_proxy_crv, right_middle04_proxy_grp)
    cmds.move(-78, 130.4, 1.1, right_middle04_proxy_grp)

    # Right Ring
    right_ring01_proxy_crv = create_directional_joint_curve(elements_default.get('right_ring01_proxy_crv'),
                                                            proxy_finger_scale)
    right_ring01_proxy_grp = cmds.group(empty=True, world=True, name=right_ring01_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_ring01_proxy_crv, right_ring01_proxy_grp)
    cmds.move(-66.9, 130.4, -1.1, right_ring01_proxy_grp)

    right_ring02_proxy_crv = create_directional_joint_curve(elements_default.get('right_ring02_proxy_crv'),
                                                            proxy_finger_scale)
    right_ring02_proxy_grp = cmds.group(empty=True, world=True, name=right_ring02_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_ring02_proxy_crv, right_ring02_proxy_grp)
    cmds.move(-70.4, 130.4, -1.1, right_ring02_proxy_grp)

    right_ring03_proxy_crv = create_directional_joint_curve(elements_default.get('right_ring03_proxy_crv'),
                                                            proxy_finger_scale)
    right_ring03_proxy_grp = cmds.group(empty=True, world=True, name=right_ring03_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_ring03_proxy_crv, right_ring03_proxy_grp)
    cmds.move(-74, 130.4, -1.1, right_ring03_proxy_grp)

    right_ring04_proxy_crv = create_directional_joint_curve(elements_default.get('right_ring04_proxy_crv'),
                                                            proxy_end_joint_scale)
    right_ring04_proxy_grp = cmds.group(empty=True, world=True, name=right_ring04_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_ring04_proxy_crv, right_ring04_proxy_grp)
    cmds.move(-77.5, 130.4, -1.1, right_ring04_proxy_grp)

    # Right Pinky
    right_pinky01_proxy_crv = create_directional_joint_curve(elements_default.get('right_pinky01_proxy_crv'),
                                                             proxy_finger_scale)
    right_pinky01_proxy_grp = cmds.group(empty=True, world=True, name=right_pinky01_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_pinky01_proxy_crv, right_pinky01_proxy_grp)
    cmds.move(-66.3, 130.4, -3.2, right_pinky01_proxy_grp)

    right_pinky02_proxy_crv = create_directional_joint_curve(elements_default.get('right_pinky02_proxy_crv'),
                                                             proxy_finger_scale)
    right_pinky02_proxy_grp = cmds.group(empty=True, world=True, name=right_pinky02_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_pinky02_proxy_crv, right_pinky02_proxy_grp)
    cmds.move(-69.6, 130.4, -3.2, right_pinky02_proxy_grp)

    right_pinky03_proxy_crv = create_directional_joint_curve(elements_default.get('right_pinky03_proxy_crv'),
                                                             proxy_finger_scale)
    right_pinky03_proxy_grp = cmds.group(empty=True, world=True, name=right_pinky03_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_pinky03_proxy_crv, right_pinky03_proxy_grp)
    cmds.move(-72.8, 130.4, -3.2, right_pinky03_proxy_grp)

    right_pinky04_proxy_crv = create_directional_joint_curve(elements_default.get('right_pinky04_proxy_crv'),
                                                             proxy_end_joint_scale)
    right_pinky04_proxy_grp = cmds.group(empty=True, world=True, name=right_pinky04_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_pinky04_proxy_crv, right_pinky04_proxy_grp)
    cmds.move(-76.3, 130.4, -3.2, right_pinky04_proxy_grp)

    # Hip
    hip_proxy_crv = create_joint_curve(elements_default.get('hip_proxy_crv'), .4)
    hip_proxy_grp = cmds.group(empty=True, world=True, name=hip_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(hip_proxy_crv, hip_proxy_grp)
    cmds.move(0, 84.5, 0, hip_proxy_grp)

    # ################# Left Leg #################
    # Left Hip
    left_hip_proxy_crv = create_joint_curve(elements_default.get('left_hip_proxy_crv'), .4)
    left_hip_proxy_grp = cmds.group(empty=True, world=True, name=left_hip_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_hip_proxy_crv, left_hip_proxy_grp)
    cmds.move(10.2, 84.5, 0, left_hip_proxy_grp)

    # Left Knee
    left_knee_proxy_crv = create_aim_joint_curve(elements_default.get('left_knee_proxy_crv'), .5)
    cmds.rotate(0, 180, 90, left_knee_proxy_crv)
    cmds.makeIdentity(left_knee_proxy_crv, apply=True, translate=True, scale=True, rotate=True)
    left_knee_proxy_grp = cmds.group(empty=True, world=True, name=left_knee_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_knee_proxy_crv, left_knee_proxy_grp)
    cmds.move(10.2, 46.8, 0, left_knee_proxy_grp)

    # Left Ankle
    left_ankle_proxy_crv = create_joint_curve(elements_default.get('left_ankle_proxy_crv'), .4)
    left_ankle_proxy_grp = cmds.group(empty=True, world=True, name=left_ankle_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_ankle_proxy_crv, left_ankle_proxy_grp)
    cmds.move(10.2, 9.6, 0, left_ankle_proxy_grp)

    # Left Ball
    left_ball_proxy_crv = create_joint_curve(elements_default.get('left_ball_proxy_crv'), .4)
    left_ball_proxy_grp = cmds.group(empty=True, world=True, name=left_ball_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_ball_proxy_crv, left_ball_proxy_grp)
    cmds.move(10.2, 0, 13.1, left_ball_proxy_grp)

    # Left Toe
    left_toe_proxy_crv = create_joint_curve(elements_default.get('left_toe_proxy_crv'), .35)
    left_toe_proxy_grp = cmds.group(empty=True, world=True, name=left_toe_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_toe_proxy_crv, left_toe_proxy_grp)
    cmds.move(10.2, 0, 23.4, left_toe_proxy_grp)

    # Left Heel Roll Pivot
    left_heel_proxy_crv = create_joint_curve(elements_default.get('left_heel_proxy_pivot'), .1)
    left_heel_proxy_grp = cmds.group(empty=True, world=True, name=left_heel_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(left_heel_proxy_crv, left_heel_proxy_grp)
    cmds.parent(left_heel_proxy_grp, left_ankle_proxy_grp)
    cmds.move(10.2, 0, 0, left_heel_proxy_grp)
    change_viewport_color(left_heel_proxy_crv, (1, 0, 0))
    cmds.addAttr(left_heel_proxy_crv, ln="proxyControl", at='enum', en='-------------:', keyable=True)
    cmds.setAttr(left_heel_proxy_crv + '.proxyControl', e=True, lock=True)
    cmds.addAttr(left_heel_proxy_crv, ln="followAnkle", at="bool", keyable=True)
    cmds.setAttr(left_heel_proxy_crv + '.followAnkle', 1)
    constraint = cmds.pointConstraint(left_ankle_proxy_crv, left_heel_proxy_grp, skip='y')
    cmds.connectAttr(left_heel_proxy_crv + '.followAnkle', constraint[0] + '.w0')
    cmds.setAttr(left_heel_proxy_crv + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(left_heel_proxy_crv + '.scale', l=True, k=False, channelBox=False)
    cmds.setAttr(left_heel_proxy_crv + '.v', l=True, k=False, channelBox=False)

    # ################# Right Leg #################
    # Right Hip
    right_hip_proxy_crv = create_joint_curve(elements_default.get('right_hip_proxy_crv'), .4)
    right_hip_proxy_grp = cmds.group(empty=True, world=True, name=right_hip_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_hip_proxy_crv, right_hip_proxy_grp)
    cmds.move(-10.2, 84.5, 0, right_hip_proxy_grp)

    # Right Knee
    right_knee_proxy_crv = create_aim_joint_curve(elements_default.get('right_knee_proxy_crv'), .5)
    cmds.rotate(0, 180, 90, right_knee_proxy_crv)
    cmds.makeIdentity(right_knee_proxy_crv, apply=True, translate=True, scale=True, rotate=True)
    right_knee_proxy_grp = cmds.group(empty=True, world=True, name=right_knee_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_knee_proxy_crv, right_knee_proxy_grp)
    cmds.move(-1.75, 8, 0, right_knee_proxy_grp)

    # Right Ankle
    right_ankle_proxy_crv = create_joint_curve(elements_default.get('right_ankle_proxy_crv'), .4)
    right_ankle_proxy_grp = cmds.group(empty=True, world=True, name=right_ankle_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_ankle_proxy_crv, right_ankle_proxy_grp)
    cmds.move(-10.2, 9.6, 0, right_ankle_proxy_grp)

    # Right Ball
    right_ball_proxy_crv = create_joint_curve(elements_default.get('right_ball_proxy_crv'), .4)
    right_ball_proxy_grp = cmds.group(empty=True, world=True, name=right_ball_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_ball_proxy_crv, right_ball_proxy_grp)
    cmds.move(-10.2, 0, 13.1, right_ball_proxy_grp)

    # Right Toe
    right_toe_proxy_crv = create_joint_curve(elements_default.get('right_toe_proxy_crv'), .35)
    right_toe_proxy_grp = cmds.group(empty=True, world=True, name=right_toe_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_toe_proxy_crv, right_toe_proxy_grp)
    cmds.move(-10.2, 0, 23.4, right_toe_proxy_grp)

    # Right Heel Roll Pivot
    right_heel_proxy_crv = create_joint_curve(elements_default.get('right_heel_proxy_pivot'), .1)
    right_heel_proxy_grp = cmds.group(empty=True, world=True, name=right_heel_proxy_crv + GRP_SUFFIX.capitalize())
    cmds.parent(right_heel_proxy_crv, right_heel_proxy_grp)
    cmds.parent(right_heel_proxy_grp, right_ankle_proxy_grp)
    cmds.move(10.2, 0, 0, right_heel_proxy_grp)
    change_viewport_color(right_heel_proxy_crv, (1, 0, 0))
    cmds.addAttr(right_heel_proxy_crv, ln="proxyControl", at='enum', en='-------------:', keyable=True)
    cmds.setAttr(right_heel_proxy_crv + '.proxyControl', e=True, lock=True)
    cmds.addAttr(right_heel_proxy_crv, ln="followAnkle", at="bool", keyable=True)
    cmds.setAttr(right_heel_proxy_crv + '.followAnkle', 1)
    constraint = cmds.pointConstraint(right_ankle_proxy_crv, right_heel_proxy_grp, skip='y')
    cmds.connectAttr(right_heel_proxy_crv + '.followAnkle', constraint[0] + '.w0')
    cmds.setAttr(right_heel_proxy_crv + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(right_heel_proxy_crv + '.scale', l=True, k=False, channelBox=False)
    cmds.setAttr(right_heel_proxy_crv + '.v', l=True, k=False, channelBox=False)

    # Assemble Hierarchy
    cmds.parent(root_proxy_grp, main_crv)

    cmds.parent(spine01_proxy_grp, main_crv)
    cmds.parent(spine02_proxy_grp, main_crv)
    cmds.parent(spine03_proxy_grp, main_crv)
    cmds.parent(spine04_proxy_grp, main_crv)

    cmds.parent(left_shoulder_proxy_grp, left_clavicle_proxy_crv)
    cmds.parent(right_shoulder_proxy_grp, right_clavicle_proxy_crv)

    cmds.parent(hip_proxy_grp, cog_proxy_crv)
    cmds.parent(left_hip_proxy_grp, hip_proxy_grp)
    cmds.parent(right_hip_proxy_grp, hip_proxy_grp)

    # Neck and Head
    cmds.parent(neck_base_proxy_grp, spine04_proxy_crv)
    cmds.parent(neck_mid_proxy_grp, neck_base_proxy_crv)
    cmds.parent(head_proxy_grp, neck_base_proxy_crv)
    cmds.parent(jaw_proxy_grp, head_proxy_crv)
    cmds.parent(jaw_end_proxy_grp, jaw_proxy_crv)
    cmds.parent(head_end_proxy_grp, head_proxy_crv)
    cmds.parent(left_eye_proxy_grp, head_proxy_crv)
    cmds.parent(right_eye_proxy_grp, head_proxy_crv)

    # Arms
    cmds.parent(left_clavicle_proxy_grp, spine04_proxy_crv)
    cmds.parent(right_clavicle_proxy_grp, spine04_proxy_crv)

    cmds.parent(left_elbow_proxy_grp, main_crv)
    cmds.parent(left_wrist_proxy_grp, main_crv)

    cmds.parent(right_elbow_proxy_grp, main_crv)
    cmds.parent(right_wrist_proxy_grp, main_crv)

    # Legs
    cmds.parent(left_hip_proxy_grp, main_crv)
    cmds.parent(left_knee_proxy_grp, main_crv)
    cmds.parent(left_ankle_proxy_grp, main_crv)

    cmds.parent(right_hip_proxy_grp, main_crv)
    cmds.parent(right_knee_proxy_grp, main_crv)
    cmds.parent(right_ankle_proxy_grp, main_crv)

    # Fingers
    cmds.parent(left_thumb01_proxy_grp, left_wrist_proxy_crv)
    cmds.parent(left_thumb02_proxy_grp, left_thumb01_proxy_crv)
    cmds.parent(left_thumb03_proxy_grp, left_thumb02_proxy_crv)
    cmds.parent(left_thumb04_proxy_grp, left_thumb03_proxy_crv)

    cmds.parent(left_index01_proxy_grp, left_wrist_proxy_crv)
    cmds.parent(left_index02_proxy_grp, left_index01_proxy_crv)
    cmds.parent(left_index03_proxy_grp, left_index02_proxy_crv)
    cmds.parent(left_index04_proxy_grp, left_index03_proxy_crv)

    cmds.parent(left_middle01_proxy_grp, left_wrist_proxy_crv)
    cmds.parent(left_middle02_proxy_grp, left_middle01_proxy_crv)
    cmds.parent(left_middle03_proxy_grp, left_middle02_proxy_crv)
    cmds.parent(left_middle04_proxy_grp, left_middle03_proxy_crv)

    cmds.parent(left_ring01_proxy_grp, left_wrist_proxy_crv)
    cmds.parent(left_ring02_proxy_grp, left_ring01_proxy_crv)
    cmds.parent(left_ring03_proxy_grp, left_ring02_proxy_crv)
    cmds.parent(left_ring04_proxy_grp, left_ring03_proxy_crv)

    cmds.parent(left_pinky01_proxy_grp, left_wrist_proxy_crv)
    cmds.parent(left_pinky02_proxy_grp, left_pinky01_proxy_crv)
    cmds.parent(left_pinky03_proxy_grp, left_pinky02_proxy_crv)
    cmds.parent(left_pinky04_proxy_grp, left_pinky03_proxy_crv)

    cmds.parent(right_thumb01_proxy_grp, right_wrist_proxy_crv)
    cmds.parent(right_thumb02_proxy_grp, right_thumb01_proxy_crv)
    cmds.parent(right_thumb03_proxy_grp, right_thumb02_proxy_crv)
    cmds.parent(right_thumb04_proxy_grp, right_thumb03_proxy_crv)

    cmds.parent(right_index01_proxy_grp, right_wrist_proxy_crv)
    cmds.parent(right_index02_proxy_grp, right_index01_proxy_crv)
    cmds.parent(right_index03_proxy_grp, right_index02_proxy_crv)
    cmds.parent(right_index04_proxy_grp, right_index03_proxy_crv)

    cmds.parent(right_middle01_proxy_grp, right_wrist_proxy_crv)
    cmds.parent(right_middle02_proxy_grp, right_middle01_proxy_crv)
    cmds.parent(right_middle03_proxy_grp, right_middle02_proxy_crv)
    cmds.parent(right_middle04_proxy_grp, right_middle03_proxy_crv)

    cmds.parent(right_ring01_proxy_grp, right_wrist_proxy_crv)
    cmds.parent(right_ring02_proxy_grp, right_ring01_proxy_crv)
    cmds.parent(right_ring03_proxy_grp, right_ring02_proxy_crv)
    cmds.parent(right_ring04_proxy_grp, right_ring03_proxy_crv)

    cmds.parent(right_pinky01_proxy_grp, right_wrist_proxy_crv)
    cmds.parent(right_pinky02_proxy_grp, right_pinky01_proxy_crv)
    cmds.parent(right_pinky03_proxy_grp, right_pinky02_proxy_crv)
    cmds.parent(right_pinky04_proxy_grp, right_pinky03_proxy_crv)

    # Constrain Spine Joints
    pc_s1 = cmds.pointConstraint([cog_proxy_crv, spine04_proxy_crv], spine01_proxy_grp, offset=(0, 0, 0), skip='x')
    cmds.setAttr(pc_s1[0] + '.' + cog_proxy_crv + 'W0', 3)

    cmds.pointConstraint([cog_proxy_crv, spine04_proxy_crv], spine02_proxy_grp, offset=(0, 0, 0), skip='x')

    pc_s3 = cmds.pointConstraint([cog_proxy_crv, spine04_proxy_crv], spine03_proxy_grp, offset=(0, 0, 0), skip='x')
    cmds.setAttr(pc_s3[0] + '.' + spine04_proxy_crv + 'W1', 3)

    # Constraint Neck Mid
    cmds.pointConstraint([neck_base_proxy_crv, head_proxy_crv], neck_mid_proxy_grp, offset=(0, 0, 0), skip='x')

    # Constrain Left Elbow Between Shoulder and Wrist
    cmds.pointConstraint([left_shoulder_proxy_crv, left_wrist_proxy_crv], left_elbow_proxy_grp)
    cmds.pointConstraint([right_shoulder_proxy_crv, right_wrist_proxy_crv], right_elbow_proxy_grp)

    # Constraint Left Knee Between Hip and Ankle
    cmds.pointConstraint([left_hip_proxy_crv, left_ankle_proxy_crv], left_knee_proxy_grp)
    cmds.pointConstraint([right_hip_proxy_crv, right_ankle_proxy_crv], right_knee_proxy_grp)

    cmds.parent(left_toe_proxy_grp, left_ball_proxy_crv)
    cmds.parent(left_ball_proxy_grp, left_ankle_proxy_crv)
    cmds.parent(right_toe_proxy_grp, right_ball_proxy_crv)
    cmds.parent(right_ball_proxy_grp, right_ankle_proxy_crv)

    # Left Elbow Constraints
    # Left Elbow Pole Vector Dir
    left_elbow_pv_loc = cmds.spaceLocator(name=elements_default.get('left_elbow_pv_dir'))
    cmds.delete(cmds.pointConstraint(elements_default.get('left_elbow_proxy_crv'), left_elbow_pv_loc[0]))
    cmds.parent(left_elbow_pv_loc[0], elements_default.get('left_elbow_proxy_crv'))
    cmds.move(0, 0, -9.6, left_elbow_pv_loc[0], relative=True)

    left_elbow_dir_loc = cmds.spaceLocator(name=elements_default.get('left_elbow_dir_loc'))
    left_elbow_aim_loc = cmds.spaceLocator(name=elements_default.get('left_elbow_aim_loc'))
    left_elbow_upvec_loc = cmds.spaceLocator(name=elements_default.get('left_elbow_upvec_loc'))
    left_elbow_upvec_loc_grp = cmds.group(empty=True, world=True,
                                          name=left_elbow_upvec_loc[0] + GRP_SUFFIX.capitalize())

    cmds.parent(left_elbow_aim_loc, left_elbow_dir_loc)
    cmds.parent(left_elbow_dir_loc, main_crv)
    cmds.parent(left_elbow_upvec_loc, left_elbow_upvec_loc_grp)
    cmds.parent(left_elbow_upvec_loc_grp, main_crv)

    cmds.pointConstraint(left_shoulder_proxy_crv, left_elbow_dir_loc)
    cmds.pointConstraint([left_wrist_proxy_crv, left_shoulder_proxy_crv], left_elbow_aim_loc)
    cmds.aimConstraint(left_wrist_proxy_crv, left_elbow_dir_loc)

    cmds.pointConstraint(left_shoulder_proxy_crv, left_elbow_upvec_loc_grp, skip=['x', 'z'])

    left_elbow_divide_node = cmds.createNode('multiplyDivide',
                                             name=elements_default.get('left_elbow_divide_node'))

    cmds.setAttr(left_elbow_divide_node + '.operation', 2)  # Make Divide
    cmds.setAttr(left_elbow_divide_node + '.input2X', -2)
    cmds.connectAttr(left_wrist_proxy_crv + '.ty', left_elbow_divide_node + '.input1X')
    cmds.connectAttr(left_elbow_divide_node + '.outputX', left_elbow_upvec_loc[0] + '.ty', force=True)

    cmds.pointConstraint(left_shoulder_proxy_crv, left_elbow_dir_loc)
    cmds.pointConstraint([left_shoulder_proxy_crv, left_wrist_proxy_crv], left_elbow_aim_loc[0])

    cmds.connectAttr(left_elbow_dir_loc[0] + '.rotate', left_elbow_proxy_grp + '.rotate')

    cmds.aimConstraint(left_wrist_proxy_crv, left_elbow_dir_loc[0], aimVector=(1, 0, 0), upVector=(-1, 0, 0),
                       worldUpType='object', worldUpObject=left_elbow_upvec_loc[0])
    cmds.aimConstraint(left_elbow_aim_loc[0], left_elbow_proxy_crv, aimVector=(0, 0, 1), upVector=(0, 1, 0),
                       worldUpType='none', skip=['y', 'z'])  # Possible Issue

    # Right Elbow Constraints
    # Right Elbow Pole Vector Dir
    right_elbow_pv_loc = cmds.spaceLocator(name=elements_default.get('right_elbow_pv_dir'))
    cmds.delete(cmds.pointConstraint(elements_default.get('right_elbow_proxy_crv'), right_elbow_pv_loc[0]))
    cmds.parent(right_elbow_pv_loc[0], elements_default.get('right_elbow_proxy_crv'))
    cmds.move(0, 0, -9.6, right_elbow_pv_loc[0], relative=True)

    right_elbow_dir_loc = cmds.spaceLocator(name=elements_default.get('right_elbow_dir_loc'))
    right_elbow_aim_loc = cmds.spaceLocator(name=elements_default.get('right_elbow_aim_loc'))
    right_elbow_upvec_loc = cmds.spaceLocator(name=elements_default.get('right_elbow_upvec_loc'))
    right_elbow_upvec_loc_grp = cmds.group(empty=True, world=True,
                                           name=right_elbow_upvec_loc[0] + GRP_SUFFIX.capitalize())

    cmds.parent(right_elbow_aim_loc, right_elbow_dir_loc)
    cmds.parent(right_elbow_dir_loc, main_crv)
    cmds.parent(right_elbow_upvec_loc, right_elbow_upvec_loc_grp)
    cmds.parent(right_elbow_upvec_loc_grp, main_crv)

    cmds.pointConstraint(right_shoulder_proxy_crv, right_elbow_dir_loc)
    cmds.pointConstraint([right_wrist_proxy_crv, right_shoulder_proxy_crv], right_elbow_aim_loc)
    cmds.aimConstraint(right_wrist_proxy_crv, right_elbow_dir_loc)

    cmds.pointConstraint(right_shoulder_proxy_crv, right_elbow_upvec_loc_grp, skip=['x', 'z'])

    right_elbow_divide_node = cmds.createNode('multiplyDivide',
                                              name=elements_default.get('right_elbow_divide_node'))

    cmds.setAttr(right_elbow_divide_node + '.operation', 2)  # Make Divide
    cmds.setAttr(right_elbow_divide_node + '.input2X', -2)
    cmds.connectAttr(right_wrist_proxy_crv + '.ty', right_elbow_divide_node + '.input1X')
    cmds.connectAttr(right_elbow_divide_node + '.outputX', right_elbow_upvec_loc[0] + '.ty', force=True)

    cmds.pointConstraint(right_shoulder_proxy_crv, right_elbow_dir_loc)
    cmds.pointConstraint([right_shoulder_proxy_crv, right_wrist_proxy_crv], right_elbow_aim_loc[0])

    cmds.connectAttr(right_elbow_dir_loc[0] + '.rotate', right_elbow_proxy_grp + '.rotate')

    cmds.aimConstraint(right_wrist_proxy_crv, right_elbow_dir_loc[0], aimVector=(-1, 0, 0), upVector=(1, 0, 0),
                       worldUpType='object', worldUpObject=right_elbow_upvec_loc[0])
    cmds.aimConstraint(right_elbow_aim_loc[0], right_elbow_proxy_crv, aimVector=(0, 0, 1), upVector=(0, 1, 0),
                       worldUpType='none', skip=['y', 'z'])  # Possible Issue

    # Left Knee Setup
    left_knee_pv_dir = cmds.spaceLocator(name=elements_default.get('left_knee_pv_dir'))
    temp = cmds.pointConstraint(left_knee_proxy_crv, left_knee_pv_dir)
    cmds.delete(temp)
    cmds.move(0, 0, 12.9, left_knee_pv_dir, relative=True)
    cmds.parent(left_knee_pv_dir[0], left_knee_proxy_crv)

    # Right Knee Setup
    right_knee_pv_dir = cmds.spaceLocator(name=elements_default.get('right_knee_pv_dir'))
    temp = cmds.pointConstraint(right_knee_proxy_crv, right_knee_pv_dir)
    cmds.delete(temp)
    cmds.move(0, 0, 12.9, right_knee_pv_dir, relative=True)
    cmds.parent(right_knee_pv_dir[0], right_knee_proxy_crv)

    # Left Knee Constraints
    left_knee_dir_loc = cmds.spaceLocator(name=elements_default.get('left_knee_dir_loc'))
    left_knee_aim_loc = cmds.spaceLocator(name=elements_default.get('left_knee_aim_loc'))
    left_knee_upvec_loc = cmds.spaceLocator(name=elements_default.get('left_knee_upvec_loc'))
    left_knee_upvec_loc_grp = cmds.group(empty=True, world=True, name=left_knee_upvec_loc[0] + GRP_SUFFIX.capitalize())
    cmds.parent(left_knee_upvec_loc, left_knee_upvec_loc_grp)
    cmds.parent(left_knee_upvec_loc_grp, main_crv)
    cmds.parent(left_knee_dir_loc[0], main_crv)
    cmds.parent(left_knee_aim_loc[0], left_knee_dir_loc[0])

    left_knee_divide_node = cmds.createNode('multiplyDivide',
                                            name=elements_default.get('left_knee_divide_node'))
    cmds.setAttr(left_knee_divide_node + '.operation', 2)  # Make Divide
    cmds.setAttr(left_knee_divide_node + '.input2X', -2)
    cmds.connectAttr(left_ankle_proxy_crv + '.tx', left_knee_divide_node + '.input1X')
    cmds.connectAttr(left_knee_divide_node + '.outputX', left_knee_upvec_loc[0] + '.tx', force=True)

    cmds.move(0, 11.7, 0, left_knee_upvec_loc[0])
    cmds.pointConstraint(left_hip_proxy_crv, left_knee_upvec_loc_grp)
    cmds.pointConstraint(left_hip_proxy_crv, left_knee_dir_loc[0])
    cmds.pointConstraint([left_hip_proxy_crv, left_ankle_proxy_crv], left_knee_aim_loc[0])

    cmds.connectAttr(left_knee_dir_loc[0] + '.rotate', left_knee_proxy_grp + '.rotate', force=True)

    cmds.aimConstraint(left_ankle_proxy_crv, left_knee_dir_loc[0], aimVector=(0, -1, 0), upVector=(0, -1, 0),
                       worldUpType='object', worldUpObject=left_knee_upvec_loc[0])
    cmds.aimConstraint(left_knee_aim_loc[0], left_knee_proxy_crv, aimVector=(0, 0, -1), upVector=(0, 1, 0),
                       worldUpType='none', skip=['x', 'z'])  # Possible Issue

    # Right Knee Constraints
    right_knee_dir_loc = cmds.spaceLocator(name=elements_default.get('right_knee_dir_loc'))
    right_knee_aim_loc = cmds.spaceLocator(name=elements_default.get('right_knee_aim_loc'))
    right_knee_upvec_loc = cmds.spaceLocator(name=elements_default.get('right_knee_upvec_loc'))
    right_knee_upvec_loc_grp = cmds.group(empty=True, world=True,
                                          name=right_knee_upvec_loc[0] + GRP_SUFFIX.capitalize())
    cmds.parent(right_knee_upvec_loc, right_knee_upvec_loc_grp)
    cmds.parent(right_knee_upvec_loc_grp, main_crv)
    cmds.parent(right_knee_dir_loc[0], main_crv)
    cmds.parent(right_knee_aim_loc[0], right_knee_dir_loc[0])

    right_knee_divide_node = cmds.createNode('multiplyDivide',
                                             name=elements_default.get('right_knee_divide_node'))
    cmds.setAttr(right_knee_divide_node + '.operation', 2)  # Make Divide
    cmds.setAttr(right_knee_divide_node + '.input2X', -2)
    cmds.connectAttr(right_ankle_proxy_crv + '.tx', right_knee_divide_node + '.input1X')
    cmds.connectAttr(right_knee_divide_node + '.outputX', right_knee_upvec_loc[0] + '.tx', force=True)

    cmds.move(0, 11.7, 0, right_knee_upvec_loc[0])
    cmds.pointConstraint(right_hip_proxy_crv, right_knee_upvec_loc_grp)
    cmds.pointConstraint(right_hip_proxy_crv, right_knee_dir_loc[0])
    cmds.pointConstraint([right_hip_proxy_crv, right_ankle_proxy_crv], right_knee_aim_loc[0])

    cmds.connectAttr(right_knee_dir_loc[0] + '.rotate', right_knee_proxy_grp + '.rotate', force=True)

    cmds.aimConstraint(right_ankle_proxy_crv, right_knee_dir_loc[0], aimVector=(0, -1, 0), upVector=(0, -1, 0),
                       worldUpType='object', worldUpObject=right_knee_upvec_loc[0])
    cmds.aimConstraint(right_knee_aim_loc[0], right_knee_proxy_crv, aimVector=(0, 0, -1), upVector=(0, 1, 0),
                       worldUpType='none', skip=['x', 'z'])  # Possible Issue

    # Left Rolls
    left_ball_pivot_grp = cmds.group(empty=True, world=True,
                                     name=elements_default.get('left_ball_pivot_grp'))
    cmds.parent(left_ball_pivot_grp, main_crv)
    ankle_pos = cmds.xform(left_ankle_proxy_crv, q=True, ws=True, rp=True)
    cmds.move(ankle_pos[0], left_ball_pivot_grp, moveX=True)

    cmds.pointConstraint(left_ankle_proxy_crv, left_ball_pivot_grp, maintainOffset=True, skip=['y'])
    cmds.orientConstraint(left_ankle_proxy_crv, left_ball_pivot_grp, maintainOffset=True, skip=['x', 'z'])
    cmds.scaleConstraint(left_ankle_proxy_crv, left_ball_pivot_grp, skip=['y'])
    cmds.parent(left_ball_proxy_grp, left_ball_pivot_grp)

    # Right Rolls
    right_ball_pivot_grp = cmds.group(empty=True, world=True,
                                      name=elements_default.get('right_ball_pivot_grp'))
    cmds.parent(right_ball_pivot_grp, main_crv)
    ankle_pos = cmds.xform(right_ankle_proxy_crv, q=True, ws=True, rp=True)
    cmds.move(ankle_pos[0], right_ball_pivot_grp, moveX=True)

    cmds.pointConstraint(right_ankle_proxy_crv, right_ball_pivot_grp, maintainOffset=True, skip=['y'])
    cmds.orientConstraint(right_ankle_proxy_crv, right_ball_pivot_grp, maintainOffset=True, skip=['x', 'z'])
    cmds.scaleConstraint(right_ankle_proxy_crv, right_ball_pivot_grp, skip=['y'])
    cmds.parent(right_ball_proxy_grp, right_ball_pivot_grp)

    # Limits and Locks
    cmds.transformLimits(left_elbow_proxy_crv, tz=(-1, -0.01), etz=(0, 1))
    cmds.transformLimits(right_elbow_proxy_crv, tz=(-1, -0.01), etz=(0, 1))

    cmds.transformLimits(left_knee_proxy_crv, tz=(0, 1), etz=(1, 0))
    cmds.transformLimits(right_knee_proxy_crv, tz=(0, 1), etz=(1, 0))

    # Left Ankle
    cmds.setAttr(left_ankle_proxy_crv + '.rx', l=True, k=False, channelBox=False)
    cmds.setAttr(left_ankle_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    cmds.transformLimits(left_ankle_proxy_crv, ry=(-80, 80), ery=(1, 1))

    # Right Ankle
    cmds.setAttr(right_ankle_proxy_crv + '.rx', l=True, k=False, channelBox=False)
    cmds.setAttr(right_ankle_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    cmds.transformLimits(right_ankle_proxy_crv, ry=(-80, 80), ery=(1, 1))

    # Main Control
    cmds.setAttr(main_crv + '.translate', l=True, k=False, channelBox=False)
    cmds.setAttr(main_crv + '.rotate', l=True, k=False, channelBox=False)

    # Other Center Joints
    cmds.setAttr(head_end_proxy_crv + '.ry', l=True, k=False, channelBox=False)
    cmds.setAttr(spine01_proxy_crv + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(spine02_proxy_crv + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(spine03_proxy_crv + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(spine01_proxy_crv + '.scale', l=True, k=False, channelBox=False)
    cmds.setAttr(spine02_proxy_crv + '.scale', l=True, k=False, channelBox=False)
    cmds.setAttr(spine03_proxy_crv + '.scale', l=True, k=False, channelBox=False)
    cmds.setAttr(spine04_proxy_crv + '.ry', l=True, k=False, channelBox=False)
    cmds.setAttr(spine04_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    cmds.setAttr(neck_base_proxy_crv + '.ry', l=True, k=False, channelBox=False)
    cmds.setAttr(head_end_proxy_crv + '.ry', l=True, k=False, channelBox=False)
    cmds.setAttr(jaw_proxy_crv + '.ry', l=True, k=False, channelBox=False)
    cmds.setAttr(jaw_end_proxy_crv + '.ry', l=True, k=False, channelBox=False)
    cmds.setAttr(head_end_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    cmds.setAttr(cog_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    cmds.setAttr(neck_base_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    cmds.setAttr(jaw_end_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    cmds.setAttr(head_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    cmds.setAttr(jaw_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    cmds.setAttr(jaw_end_proxy_crv + '.rz', l=True, k=False, channelBox=False)

    cmds.setAttr(hip_proxy_crv + '.tx', l=True, k=False, channelBox=False)
    cmds.setAttr(hip_proxy_crv + '.ry', l=True, k=False, channelBox=False)
    cmds.setAttr(hip_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    cmds.setAttr(hip_proxy_crv + '.scale', l=True, k=False, channelBox=False)

    # Proxy Groups
    cmds.setAttr(spine01_proxy_grp + '.translate', l=True, k=False, channelBox=False)
    cmds.setAttr(spine02_proxy_grp + '.translate', l=True, k=False, channelBox=False)
    cmds.setAttr(spine03_proxy_grp + '.translate', l=True, k=False, channelBox=False)
    cmds.setAttr(spine01_proxy_grp + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(spine02_proxy_grp + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(spine03_proxy_grp + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(spine01_proxy_grp + '.scale', l=True, k=False, channelBox=False)
    cmds.setAttr(spine02_proxy_grp + '.scale', l=True, k=False, channelBox=False)
    cmds.setAttr(spine03_proxy_grp + '.scale', l=True, k=False, channelBox=False)
    cmds.setAttr(spine01_proxy_grp + '.v', l=True, k=False, channelBox=False)
    cmds.setAttr(spine02_proxy_grp + '.v', l=True, k=False, channelBox=False)
    cmds.setAttr(spine03_proxy_grp + '.v', l=True, k=False, channelBox=False)

    # Arms
    cmds.setAttr(left_shoulder_proxy_crv + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(right_shoulder_proxy_crv + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(left_shoulder_proxy_crv + '.scale', l=True, k=False, channelBox=False)
    cmds.setAttr(right_shoulder_proxy_crv + '.scale', l=True, k=False, channelBox=False)

    cmds.setAttr(left_elbow_proxy_crv + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(right_elbow_proxy_crv + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(left_elbow_proxy_crv + '.scale', l=True, k=False, channelBox=False)
    cmds.setAttr(right_elbow_proxy_crv + '.scale', l=True, k=False, channelBox=False)

    # Legs
    # cmds.setAttr(right_hip_proxy_crv + '.tz', l=True, k=False, channelBox=False)
    # cmds.setAttr(left_hip_proxy_crv + '.tz', l=True, k=False, channelBox=False)

    cmds.setAttr(right_hip_proxy_crv + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(left_hip_proxy_crv + '.rotate', l=True, k=False, channelBox=False)

    cmds.setAttr(right_hip_proxy_crv + '.scale', l=True, k=False, channelBox=False)
    cmds.setAttr(left_hip_proxy_crv + '.scale', l=True, k=False, channelBox=False)

    cmds.setAttr(right_knee_proxy_crv + '.rotate', l=True, k=False, channelBox=False)
    cmds.setAttr(left_knee_proxy_crv + '.rotate', l=True, k=False, channelBox=False)

    cmds.setAttr(right_knee_proxy_crv + '.scale', l=True, k=False, channelBox=False)
    cmds.setAttr(left_knee_proxy_crv + '.scale', l=True, k=False, channelBox=False)

    # Feet
    cmds.setAttr(right_ball_proxy_crv + '.rz', l=True, k=False, channelBox=False)
    cmds.setAttr(right_ball_proxy_crv + '.rx', l=True, k=False, channelBox=False)

    cmds.setAttr(right_toe_proxy_crv + '.rx', l=True, k=False, channelBox=False)
    cmds.setAttr(right_toe_proxy_crv + '.rz', l=True, k=False, channelBox=False)

    cmds.setAttr(left_ball_proxy_crv + '.rx', l=True, k=False, channelBox=False)
    cmds.setAttr(left_ball_proxy_crv + '.rz', l=True, k=False, channelBox=False)

    cmds.setAttr(left_toe_proxy_crv + '.rx', l=True, k=False, channelBox=False)
    cmds.setAttr(left_toe_proxy_crv + '.rz', l=True, k=False, channelBox=False)

    # Special Cases
    if settings.get('proxy_limits'):
        cmds.setAttr(left_ball_proxy_crv + '.ty', l=True, k=False, channelBox=False)
        cmds.setAttr(left_toe_proxy_crv + '.ty', l=True, k=False, channelBox=False)
        cmds.setAttr(right_ball_proxy_crv + '.ty', l=True, k=False, channelBox=False)
        cmds.setAttr(right_toe_proxy_crv + '.ty', l=True, k=False, channelBox=False)

        cmds.setAttr(cog_proxy_crv + '.tx', l=True, k=False, channelBox=False)
        cmds.setAttr(spine01_proxy_crv + '.tx', l=True, k=False, channelBox=False)
        cmds.setAttr(spine01_proxy_crv + '.ty', l=True, k=False, channelBox=False)
        cmds.setAttr(spine02_proxy_crv + '.tx', l=True, k=False, channelBox=False)
        cmds.setAttr(spine02_proxy_crv + '.ty', l=True, k=False, channelBox=False)
        cmds.setAttr(spine03_proxy_crv + '.tx', l=True, k=False, channelBox=False)
        cmds.setAttr(spine03_proxy_crv + '.ty', l=True, k=False, channelBox=False)
        cmds.setAttr(spine04_proxy_crv + '.tx', l=True, k=False, channelBox=False)

        cmds.setAttr(neck_base_proxy_crv + '.tx', l=True, k=False, channelBox=False)
        cmds.setAttr(neck_mid_proxy_crv + '.tx', l=True, k=False, channelBox=False)

        cmds.setAttr(head_proxy_crv + '.tx', l=True, k=False, channelBox=False)
        cmds.setAttr(head_end_proxy_crv + '.tx', l=True, k=False, channelBox=False)

        cmds.setAttr(jaw_proxy_crv + '.tx', l=True, k=False, channelBox=False)
        cmds.setAttr(jaw_end_proxy_crv + '.tx', l=True, k=False, channelBox=False)

    # Set Loc Visibility
    cmds.setAttr(left_knee_upvec_loc[0] + '.v', 0)
    cmds.setAttr(left_knee_aim_loc[0] + '.v', 0)
    cmds.setAttr(left_knee_dir_loc[0] + '.v', 0)
    cmds.setAttr(left_knee_pv_dir[0] + '.v', 0)

    cmds.setAttr(left_elbow_pv_loc[0] + '.v', 0)
    cmds.setAttr(left_elbow_aim_loc[0] + '.v', 0)
    cmds.setAttr(left_elbow_dir_loc[0] + '.v', 0)
    cmds.setAttr(left_elbow_upvec_loc[0] + '.v', 0)

    cmds.setAttr(right_knee_upvec_loc[0] + '.v', 0)
    cmds.setAttr(right_knee_aim_loc[0] + '.v', 0)
    cmds.setAttr(right_knee_dir_loc[0] + '.v', 0)
    cmds.setAttr(right_knee_pv_dir[0] + '.v', 0)

    cmds.setAttr(right_elbow_pv_loc[0] + '.v', 0)
    cmds.setAttr(right_elbow_aim_loc[0] + '.v', 0)
    cmds.setAttr(right_elbow_dir_loc[0] + '.v', 0)
    cmds.setAttr(right_elbow_upvec_loc[0] + '.v', 0)

    # Hide in the Outliner
    cmds.setAttr(left_knee_upvec_loc_grp + '.hiddenInOutliner', 1)
    cmds.setAttr(left_knee_aim_loc[0] + '.hiddenInOutliner', 1)
    cmds.setAttr(left_knee_dir_loc[0] + '.hiddenInOutliner', 1)
    cmds.setAttr(left_knee_pv_dir[0] + '.hiddenInOutliner', 1)

    cmds.setAttr(left_elbow_pv_loc[0] + '.hiddenInOutliner', 1)
    cmds.setAttr(left_elbow_aim_loc[0] + '.hiddenInOutliner', 1)
    cmds.setAttr(left_elbow_dir_loc[0] + '.hiddenInOutliner', 1)
    cmds.setAttr(left_elbow_upvec_loc_grp + '.hiddenInOutliner', 1)

    cmds.setAttr(right_knee_upvec_loc_grp + '.hiddenInOutliner', 1)
    cmds.setAttr(right_knee_aim_loc[0] + '.hiddenInOutliner', 1)
    cmds.setAttr(right_knee_dir_loc[0] + '.hiddenInOutliner', 1)
    cmds.setAttr(right_knee_pv_dir[0] + '.hiddenInOutliner', 1)

    cmds.setAttr(right_elbow_pv_loc[0] + '.hiddenInOutliner', 1)
    cmds.setAttr(right_elbow_aim_loc[0] + '.hiddenInOutliner', 1)
    cmds.setAttr(right_elbow_dir_loc[0] + '.hiddenInOutliner', 1)
    cmds.setAttr(right_elbow_upvec_loc_grp + '.hiddenInOutliner', 1)

    # Ankle can follow Hip
    cmds.addAttr(left_ankle_proxy_crv, ln="proxyControl", at='enum', en='-------------:', keyable=True)
    cmds.setAttr(left_ankle_proxy_crv + '.proxyControl', e=True, lock=True)
    cmds.addAttr(left_ankle_proxy_crv, ln="followHip", at="bool", keyable=True)
    cmds.setAttr(left_ankle_proxy_crv + '.followHip', 0)
    constraint = cmds.pointConstraint(left_hip_proxy_crv, left_ankle_proxy_grp, maintainOffset=True)
    cmds.connectAttr(left_ankle_proxy_crv + '.followHip', constraint[0] + '.w0')

    cmds.addAttr(right_ankle_proxy_crv, ln="proxyControl", at='enum', en='-------------:', keyable=True)
    cmds.setAttr(right_ankle_proxy_crv + '.proxyControl', e=True, lock=True)
    cmds.addAttr(right_ankle_proxy_crv, ln="followHip", at="bool", keyable=True)
    cmds.setAttr(right_ankle_proxy_crv + '.followHip', 0)
    constraint = cmds.pointConstraint(right_hip_proxy_crv, right_ankle_proxy_grp, maintainOffset=True)
    cmds.connectAttr(right_ankle_proxy_crv + '.followHip', constraint[0] + '.w0')

    # Store new names into settings in case they were modified
    elements['main_crv'] = main_crv
    elements['cog_proxy_crv'] = cog_proxy_crv
    elements['spine01_proxy_crv'] = spine01_proxy_crv
    elements['spine02_proxy_crv'] = spine02_proxy_crv
    elements['spine03_proxy_crv'] = spine03_proxy_crv
    elements['spine04_proxy_crv'] = spine04_proxy_crv
    elements['neck_base_proxy_crv'] = neck_base_proxy_crv
    elements['neck_mid_proxy_crv'] = neck_mid_proxy_crv
    elements['head_proxy_crv'] = head_proxy_crv
    elements['head_end_proxy_crv'] = head_end_proxy_crv
    elements['jaw_proxy_crv'] = jaw_proxy_crv
    elements['jaw_end_proxy_crv'] = jaw_end_proxy_crv
    elements['hip_proxy_crv'] = hip_proxy_crv
    # Left Side Elements
    elements['left_eye_proxy_crv'] = left_eye_proxy_crv
    elements['left_clavicle_proxy_crv'] = left_clavicle_proxy_crv
    elements['left_shoulder_proxy_crv'] = left_shoulder_proxy_crv
    elements['left_elbow_proxy_crv'] = left_elbow_proxy_crv
    elements['left_wrist_proxy_crv'] = left_wrist_proxy_crv
    elements['left_thumb01_proxy_crv'] = left_thumb01_proxy_crv
    elements['left_thumb02_proxy_crv'] = left_thumb02_proxy_crv
    elements['left_thumb03_proxy_crv'] = left_thumb03_proxy_crv
    elements['left_thumb04_proxy_crv'] = left_thumb04_proxy_crv
    elements['left_index01_proxy_crv'] = left_index01_proxy_crv
    elements['left_index02_proxy_crv'] = left_index02_proxy_crv
    elements['left_index03_proxy_crv'] = left_index03_proxy_crv
    elements['left_index04_proxy_crv'] = left_index04_proxy_crv
    elements['left_middle01_proxy_crv'] = left_middle01_proxy_crv
    elements['left_middle02_proxy_crv'] = left_middle02_proxy_crv
    elements['left_middle03_proxy_crv'] = left_middle03_proxy_crv
    elements['left_middle04_proxy_crv'] = left_middle04_proxy_crv
    elements['left_ring01_proxy_crv'] = left_ring01_proxy_crv
    elements['left_ring02_proxy_crv'] = left_ring02_proxy_crv
    elements['left_ring03_proxy_crv'] = left_ring03_proxy_crv
    elements['left_ring04_proxy_crv'] = left_ring04_proxy_crv
    elements['left_pinky01_proxy_crv'] = left_pinky01_proxy_crv
    elements['left_pinky02_proxy_crv'] = left_pinky02_proxy_crv
    elements['left_pinky03_proxy_crv'] = left_pinky03_proxy_crv
    elements['left_pinky04_proxy_crv'] = left_pinky04_proxy_crv
    elements['left_hip_proxy_crv'] = left_hip_proxy_crv
    elements['left_knee_proxy_crv'] = left_knee_proxy_crv
    elements['left_ankle_proxy_crv'] = left_ankle_proxy_crv
    elements['left_ball_proxy_crv'] = left_ball_proxy_crv
    elements['left_toe_proxy_crv'] = left_toe_proxy_crv
    elements['left_elbow_pv_loc'] = left_elbow_pv_loc[0]
    elements['left_elbow_dir_loc'] = left_elbow_dir_loc[0]
    elements['left_elbow_aim_loc'] = left_elbow_aim_loc[0]
    elements['left_elbow_upvec_loc'] = left_elbow_upvec_loc[0]
    elements['left_elbow_divide_node'] = left_elbow_divide_node
    elements['left_knee_pv_dir'] = left_knee_pv_dir[0]
    elements['left_knee_dir_loc'] = left_knee_dir_loc[0]
    elements['left_knee_aim_loc'] = left_knee_aim_loc[0]
    elements['left_knee_upvec_loc'] = left_knee_upvec_loc[0]
    elements['left_knee_divide_node'] = left_knee_divide_node
    elements['left_ball_pivot_grp'] = left_ball_pivot_grp
    # Right Side Elements
    elements['right_eye_proxy_crv'] = right_eye_proxy_crv
    elements['right_clavicle_proxy_crv'] = right_clavicle_proxy_crv
    elements['right_shoulder_proxy_crv'] = right_shoulder_proxy_crv
    elements['right_elbow_proxy_crv'] = right_elbow_proxy_crv
    elements['right_wrist_proxy_crv'] = right_wrist_proxy_crv
    elements['right_thumb01_proxy_crv'] = right_thumb01_proxy_crv
    elements['right_thumb02_proxy_crv'] = right_thumb02_proxy_crv
    elements['right_thumb03_proxy_crv'] = right_thumb03_proxy_crv
    elements['right_thumb04_proxy_crv'] = right_thumb04_proxy_crv
    elements['right_index01_proxy_crv'] = right_index01_proxy_crv
    elements['right_index02_proxy_crv'] = right_index02_proxy_crv
    elements['right_index03_proxy_crv'] = right_index03_proxy_crv
    elements['right_index04_proxy_crv'] = right_index04_proxy_crv
    elements['right_middle01_proxy_crv'] = right_middle01_proxy_crv
    elements['right_middle02_proxy_crv'] = right_middle02_proxy_crv
    elements['right_middle03_proxy_crv'] = right_middle03_proxy_crv
    elements['right_middle04_proxy_crv'] = right_middle04_proxy_crv
    elements['right_ring01_proxy_crv'] = right_ring01_proxy_crv
    elements['right_ring02_proxy_crv'] = right_ring02_proxy_crv
    elements['right_ring03_proxy_crv'] = right_ring03_proxy_crv
    elements['right_ring04_proxy_crv'] = right_ring04_proxy_crv
    elements['right_pinky01_proxy_crv'] = right_pinky01_proxy_crv
    elements['right_pinky02_proxy_crv'] = right_pinky02_proxy_crv
    elements['right_pinky03_proxy_crv'] = right_pinky03_proxy_crv
    elements['right_pinky04_proxy_crv'] = right_pinky04_proxy_crv
    elements['right_hip_proxy_crv'] = right_hip_proxy_crv
    elements['right_knee_proxy_crv'] = right_knee_proxy_crv
    elements['right_ankle_proxy_crv'] = right_ankle_proxy_crv
    elements['right_ball_proxy_crv'] = right_ball_proxy_crv
    elements['right_toe_proxy_crv'] = right_toe_proxy_crv
    elements['right_elbow_pv_loc'] = right_elbow_pv_loc[0]
    elements['right_elbow_dir_loc'] = right_elbow_dir_loc[0]
    elements['right_elbow_aim_loc'] = right_elbow_aim_loc[0]
    elements['right_elbow_upvec_loc'] = right_elbow_upvec_loc[0]
    elements['right_elbow_divide_node'] = right_elbow_divide_node
    elements['right_knee_pv_dir'] = right_knee_pv_dir[0]
    elements['right_knee_dir_loc'] = right_knee_dir_loc[0]
    elements['right_knee_aim_loc'] = right_knee_aim_loc[0]
    elements['right_knee_upvec_loc'] = right_knee_upvec_loc[0]
    elements['right_knee_divide_node'] = right_knee_divide_node
    elements['right_ball_pivot_grp'] = right_ball_pivot_grp

    elements = data_biped.elements

    # Visibility Adjustments
    for obj in elements:
        if obj.endswith('_crv'):
            proxy_crv = elements.get(obj)
            is_end_jnt = False
            if '_endProxy' in proxy_crv:
                note = 'This is an end proxy. This element will be used to determine the orientation of its parent. ' \
                       'For example:\n"jaw_endProxy" determines the orientation of the "jaw_proxy".\n\nEven' \
                       ' though a joint will be generated it mostly likely should not be an influence when skinning.'
                add_node_note(proxy_crv, note)
                color = (.5, .5, 0)
                is_end_jnt = True
            elif elements.get('neck_mid_proxy_crv') in proxy_crv:
                note = 'This is the neckMid proxy. This element will be automated to receive part of its transforms ' \
                       'from the neckBase and the other part from the head.'
                add_node_note(proxy_crv, note)
                color = (.3, .3, 0)
            elif elements.get('left_toe_proxy_crv') in proxy_crv or elements.get(
                    'right_toe_proxy_crv') in proxy_crv:
                note = 'This is a toe proxy. This element will be used to automate toe poses. Much like an end proxy,' \
                       ' it will generate a joint that most likely should not be used as an influence when skinning.' \
                       '\n\nThis joint should be placed at the end of the longest toe.'
                add_node_note(proxy_crv, note)
                color = (.3, .3, 0)
                is_end_jnt = True
            elif proxy_crv.startswith('right_'):
                color = (1, .4, .4)
            elif proxy_crv.startswith('left_'):
                color = (.2, .6, 1)
            elif elements.get('spine01_proxy_crv') in proxy_crv or elements.get(
                    'spine02_proxy_crv') in proxy_crv or elements.get('spine03_proxy_crv') in proxy_crv:
                color = (.3, .3, 0)
            else:
                color = (1, 1, .65)

            # Notes Only
            if elements.get('left_eye_proxy_crv') in proxy_crv or elements.get(
                    'right_eye_proxy_crv') in proxy_crv:
                add_node_note(proxy_crv,
                              'This is an eye proxy.\nThis element should be snapped to the center of the eye '
                              'geometry.\nYou can see the center of the eye by selecting the eye geometry then '
                              'going to "Display > Transform Display > Local Rotation Axes".\nYou can then use '
                              'this axis to snap the joint to its center. (Using "Ctrl + V")\n\nPS: If for some '
                              'reason the pivot point is not in the center of the eye, you can reset it first: '
                              '"Modify > Center Pivot".')

            if elements.get('left_elbow_proxy_crv') in proxy_crv or elements.get(
                    'right_elbow_proxy_crv') in proxy_crv:
                add_node_note(proxy_crv,
                              'This is an elbow proxy.\nThe movement of this element is intentionally limited to '
                              'attempt to keep the joints in one single plane. For better results keep the arm '
                              'joints in "T" or "A" pose.')

            if elements.get('left_knee_proxy_crv') in proxy_crv or elements.get(
                    'right_knee_proxy_crv') in proxy_crv:
                add_node_note(proxy_crv,
                              'This is a knee proxy.\nThe movement of this element is intentionally limited to '
                              'attempt to keep the joints in one single plane. For better results keep the leg '
                              'joints in "T" or "A" pose.')

            if colorize_proxy:
                change_viewport_color(proxy_crv, color)
            if colorize_proxy and is_end_jnt:
                change_outliner_color(proxy_crv, (.8, .8, 0))

    # Create Lines
    line_list = [create_visualization_line(elements.get('cog_proxy_crv'),
                                           elements.get('hip_proxy_crv')),
                 create_visualization_line(elements.get('cog_proxy_crv'),
                                           elements.get('hip_proxy_crv')),
                 create_visualization_line(elements.get('cog_proxy_crv'),
                                           elements.get('spine01_proxy_crv')),
                 create_visualization_line(elements.get('spine01_proxy_crv'),
                                           elements.get('spine02_proxy_crv')),
                 create_visualization_line(elements.get('spine02_proxy_crv'),
                                           elements.get('spine03_proxy_crv')),
                 create_visualization_line(elements.get('spine03_proxy_crv'),
                                           elements.get('spine04_proxy_crv')),
                 create_visualization_line(elements.get('spine04_proxy_crv'),
                                           elements.get('neck_base_proxy_crv')),
                 create_visualization_line(elements.get('neck_base_proxy_crv'),
                                           elements.get('neck_mid_proxy_crv')),
                 create_visualization_line(elements.get('neck_mid_proxy_crv'),
                                           elements.get('head_proxy_crv')),
                 create_visualization_line(elements.get('head_proxy_crv'),
                                           elements.get('head_end_proxy_crv')),
                 create_visualization_line(elements.get('head_proxy_crv'),
                                           elements.get('jaw_proxy_crv')),
                 create_visualization_line(elements.get('jaw_proxy_crv'),
                                           elements.get('jaw_end_proxy_crv')),
                 create_visualization_line(elements.get('head_proxy_crv'),
                                           elements.get('left_eye_proxy_crv')),
                 create_visualization_line(elements.get('head_proxy_crv'),
                                           elements.get('right_eye_proxy_crv')),
                 # Left Side
                 create_visualization_line(elements.get('hip_proxy_crv'),
                                           elements.get('left_hip_proxy_crv')),
                 create_visualization_line(elements.get('left_hip_proxy_crv'),
                                           elements.get('left_knee_proxy_crv')),
                 create_visualization_line(elements.get('left_knee_proxy_crv'),
                                           elements.get('left_ankle_proxy_crv')),
                 create_visualization_line(elements.get('left_ankle_proxy_crv'),
                                           elements.get('left_ball_proxy_crv')),
                 create_visualization_line(elements.get('left_ball_proxy_crv'),
                                           elements.get('left_toe_proxy_crv')),
                 create_visualization_line(elements.get('spine04_proxy_crv'),
                                           elements.get('left_clavicle_proxy_crv')),
                 create_visualization_line(elements.get('left_clavicle_proxy_crv'),
                                           elements.get('left_shoulder_proxy_crv')),
                 create_visualization_line(elements.get('left_shoulder_proxy_crv'),
                                           elements.get('left_elbow_proxy_crv')),
                 create_visualization_line(elements.get('left_elbow_proxy_crv'),
                                           elements.get('left_wrist_proxy_crv')),
                 # Left Fingers
                 create_visualization_line(elements.get('left_wrist_proxy_crv'),
                                           elements.get('left_thumb01_proxy_crv')),
                 create_visualization_line(elements.get('left_thumb01_proxy_crv'),
                                           elements.get('left_thumb02_proxy_crv')),
                 create_visualization_line(elements.get('left_thumb02_proxy_crv'),
                                           elements.get('left_thumb03_proxy_crv')),
                 create_visualization_line(elements.get('left_thumb03_proxy_crv'),
                                           elements.get('left_thumb04_proxy_crv')),
                 create_visualization_line(elements.get('left_wrist_proxy_crv'),
                                           elements.get('left_index01_proxy_crv')),
                 create_visualization_line(elements.get('left_index01_proxy_crv'),
                                           elements.get('left_index02_proxy_crv')),
                 create_visualization_line(elements.get('left_index02_proxy_crv'),
                                           elements.get('left_index03_proxy_crv')),
                 create_visualization_line(elements.get('left_index03_proxy_crv'),
                                           elements.get('left_index04_proxy_crv')),
                 create_visualization_line(elements.get('left_wrist_proxy_crv'),
                                           elements.get('left_middle01_proxy_crv')),
                 create_visualization_line(elements.get('left_middle01_proxy_crv'),
                                           elements.get('left_middle02_proxy_crv')),
                 create_visualization_line(elements.get('left_middle02_proxy_crv'),
                                           elements.get('left_middle03_proxy_crv')),
                 create_visualization_line(elements.get('left_middle03_proxy_crv'),
                                           elements.get('left_middle04_proxy_crv')),
                 create_visualization_line(elements.get('left_wrist_proxy_crv'),
                                           elements.get('left_ring01_proxy_crv')),
                 create_visualization_line(elements.get('left_ring01_proxy_crv'),
                                           elements.get('left_ring02_proxy_crv')),
                 create_visualization_line(elements.get('left_ring02_proxy_crv'),
                                           elements.get('left_ring03_proxy_crv')),
                 create_visualization_line(elements.get('left_ring03_proxy_crv'),
                                           elements.get('left_ring04_proxy_crv')),
                 create_visualization_line(elements.get('left_wrist_proxy_crv'),
                                           elements.get('left_pinky01_proxy_crv')),
                 create_visualization_line(elements.get('left_pinky01_proxy_crv'),
                                           elements.get('left_pinky02_proxy_crv')),
                 create_visualization_line(elements.get('left_pinky02_proxy_crv'),
                                           elements.get('left_pinky03_proxy_crv')),
                 create_visualization_line(elements.get('left_pinky03_proxy_crv'),
                                           elements.get('left_pinky04_proxy_crv')),
                 # Right Side

                 create_visualization_line(elements.get('hip_proxy_crv'),
                                           elements.get('right_hip_proxy_crv')),
                 create_visualization_line(elements.get('right_hip_proxy_crv'),
                                           elements.get('right_knee_proxy_crv')),
                 create_visualization_line(elements.get('right_knee_proxy_crv'),
                                           elements.get('right_ankle_proxy_crv')),
                 create_visualization_line(elements.get('right_ankle_proxy_crv'),
                                           elements.get('right_ball_proxy_crv')),

                 create_visualization_line(elements.get('right_ball_proxy_crv'),
                                           elements.get('right_toe_proxy_crv')),
                 create_visualization_line(elements.get('spine04_proxy_crv'),
                                           elements.get('right_clavicle_proxy_crv')),
                 create_visualization_line(elements.get('right_clavicle_proxy_crv'),
                                           elements.get('right_shoulder_proxy_crv')),
                 create_visualization_line(elements.get('right_shoulder_proxy_crv'),
                                           elements.get('right_elbow_proxy_crv')),
                 create_visualization_line(elements.get('right_elbow_proxy_crv'),
                                           elements.get('right_wrist_proxy_crv')),
                 # Right Fingers
                 create_visualization_line(elements.get('right_wrist_proxy_crv'),
                                           elements.get('right_thumb01_proxy_crv')),
                 create_visualization_line(elements.get('right_thumb01_proxy_crv'),
                                           elements.get('right_thumb02_proxy_crv')),
                 create_visualization_line(elements.get('right_thumb02_proxy_crv'),
                                           elements.get('right_thumb03_proxy_crv')),
                 create_visualization_line(elements.get('right_thumb03_proxy_crv'),
                                           elements.get('right_thumb04_proxy_crv')),
                 create_visualization_line(elements.get('right_wrist_proxy_crv'),
                                           elements.get('right_index01_proxy_crv')),
                 create_visualization_line(elements.get('right_index01_proxy_crv'),
                                           elements.get('right_index02_proxy_crv')),
                 create_visualization_line(elements.get('right_index02_proxy_crv'),
                                           elements.get('right_index03_proxy_crv')),
                 create_visualization_line(elements.get('right_index03_proxy_crv'),
                                           elements.get('right_index04_proxy_crv')),
                 create_visualization_line(elements.get('right_wrist_proxy_crv'),
                                           elements.get('right_middle01_proxy_crv')),
                 create_visualization_line(elements.get('right_middle01_proxy_crv'),
                                           elements.get('right_middle02_proxy_crv')),
                 create_visualization_line(elements.get('right_middle02_proxy_crv'),
                                           elements.get('right_middle03_proxy_crv')),
                 create_visualization_line(elements.get('right_middle03_proxy_crv'),
                                           elements.get('right_middle04_proxy_crv')),
                 create_visualization_line(elements.get('right_wrist_proxy_crv'),
                                           elements.get('right_ring01_proxy_crv')),
                 create_visualization_line(elements.get('right_ring01_proxy_crv'),
                                           elements.get('right_ring02_proxy_crv')),
                 create_visualization_line(elements.get('right_ring02_proxy_crv'),
                                           elements.get('right_ring03_proxy_crv')),
                 create_visualization_line(elements.get('right_ring03_proxy_crv'),
                                           elements.get('right_ring04_proxy_crv')),
                 create_visualization_line(elements.get('right_wrist_proxy_crv'),
                                           elements.get('right_pinky01_proxy_crv')),
                 create_visualization_line(elements.get('right_pinky01_proxy_crv'),
                                           elements.get('right_pinky02_proxy_crv')),
                 create_visualization_line(elements.get('right_pinky02_proxy_crv'),
                                           elements.get('right_pinky03_proxy_crv')),
                 create_visualization_line(elements.get('right_pinky03_proxy_crv'),
                                           elements.get('right_pinky04_proxy_crv'))
                 ]

    lines_grp = cmds.group(name='visualization_lines', empty=True, world=True)
    cmds.setAttr(lines_grp + '.overrideEnabled', 1)
    cmds.setAttr(lines_grp + '.overrideDisplayType', 1)
    for line_objs in line_list:
        for obj in line_objs:
            cmds.parent(obj, lines_grp)

    cmds.parent(lines_grp, elements.get('main_proxy_grp'))

    cmds.addAttr(elements.get('main_crv'), ln="proxyOptions", at='enum', en='-------------:', keyable=True)
    cmds.setAttr(elements.get('main_crv') + '.proxyOptions', lock=True)
    cmds.addAttr(elements.get('main_crv'), ln="linesVisibility", at="bool", keyable=True)
    cmds.setAttr(elements.get('main_crv') + '.linesVisibility', 1)
    cmds.connectAttr(elements.get('main_crv') + '.linesVisibility', lines_grp + '.v', f=True)

    # Main Proxy Control Scale
    cmds.connectAttr(elements.get('main_crv') + '.sy', elements.get('main_crv') + '.sx', f=True)
    cmds.connectAttr(elements.get('main_crv') + '.sy', elements.get('main_crv') + '.sz', f=True)
    cmds.setAttr(elements.get('main_crv') + '.sx', k=False)
    cmds.setAttr(elements.get('main_crv') + '.sz', k=False)

    # Clean Selection and Print Feedback
    cmds.select(d=True)
    unique_message = '<' + str(random.random()) + '>'
    cmds.inViewMessage(
        amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">'
                             'Proxy</span><span style=\"color:#FFFFFF;\"> was created!</span>',
        pos='botLeft', fade=True, alpha=.9)


def create_controls(data_biped):
    """ Creates rig using the previously created proxy/guide """

    def rename_proxy(old_name):
        """
        Replaces a few parts of the old names for the creation of joints
        Replaces "proxy" with "jnt"
        Replaces "endProxy" with "endJnt"

        Args:
            old_name (string): Name of the proxy element

        Returns:
            new_name (string): Name of the joint to be created out of the element

        """
        return old_name.replace(PROXY_SUFFIX, JNT_SUFFIX).replace('end' + PROXY_SUFFIX.capitalize(),
                                                                  'end' + JNT_SUFFIX.capitalize())

    def orient_to_target(obj_name, target, orientation_offset=(0, 0, 0), proxy_obj=None,
                         aim_vec=(1, 0, 0), up_vec=(0, -1, 0), brute_force=False):
        """
        Orients an object based on a target object

        Args:
            obj_name (string): Name of the object to orient (usually a joint)
            target (string): Name of the target object (usually the element that will be the child of "obj")
            orientation_offset (tuple): A tuple containing three 32b floats, used as a rotation offset to change the
                                  result orientation.
            proxy_obj (string): The name of the proxy element (used as extra rotation input)
            aim_vec (tuple): A tuple of floats used for the aim vector of the aim constraint. Default: (1, 0, 0)
            up_vec (tuple):  A tuple of floats used for the up vector of the aim constraint. Default: (0, -1, 0)
            brute_force (bool): Creates up and dir points to determine orientation (Uses proxy object)
        """
        if proxy_obj:
            cmds.delete(cmds.orientConstraint(proxy_obj, obj_name, offset=(0, 0, 0)))
            cmds.makeIdentity(obj_name, apply=True, rotate=True)

        cmds.setAttr(obj_name + '.rotateX', orientation_offset[0])
        cmds.setAttr(obj_name + '.rotateY', orientation_offset[1])
        cmds.setAttr(obj_name + '.rotateZ', orientation_offset[2])
        cmds.makeIdentity(obj_name, apply=True, rotate=True)

        cmds.delete(
            cmds.aimConstraint(target, obj_name, offset=(0, 0, 0), aimVector=aim_vec, upVector=up_vec,
                               worldUpType='vector', worldUpVector=(0, 1, 0), skip='x'))

        if proxy_obj and brute_force:
            temp_grp_up = cmds.group(name='temp_up_' + str(random.random()), world=True, empty=True)
            # cmds.setAttr(temp_grp_up + ".displayLocalAxis", 1) # Show LRA Debugging
            cmds.delete(cmds.parentConstraint(proxy_obj, temp_grp_up))
            cmds.move(1, temp_grp_up, y=True, relative=True, objectSpace=True)
            temp_grp_dir = cmds.group(name='temp_dir_' + str(random.random()), world=True, empty=True)
            cmds.delete(cmds.parentConstraint(obj_name, temp_grp_dir))
            # cmds.setAttr(temp_grp_dir + ".displayLocalAxis", 1) # Show LRA Debugging
            cmds.move(1, temp_grp_dir, x=True, relative=True, objectSpace=True)
            cmds.delete(
                cmds.aimConstraint(temp_grp_dir, obj_name, aimVector=(1, 0, 0), upVector=(0, 1, 0),
                                   worldUpType="object", worldUpObject=temp_grp_up, worldUpVector=(0, 1, 0)))
            cmds.delete(temp_grp_up)
            cmds.delete(temp_grp_dir)

        cmds.makeIdentity(obj_name, apply=True, rotate=True)

    def add_orient_offset(obj_name, orientation_offset=(0, 0, 0), apply=True):
        """
        Rotates the target then freezes its transformation (used to quickly re-orient an object)

        Args:
            obj_name (string): Name of the object to orient (usually a joint)
            orientation_offset (tuple): A tuple containing three 32b floats, used as a rotation offset to change
                                  the result orientation.
            apply (optional, bool): Whether to execute the function
        """
        if apply:
            cmds.setAttr(obj_name + '.rotateX', orientation_offset[0])
            cmds.setAttr(obj_name + '.rotateY', orientation_offset[1])
            cmds.setAttr(obj_name + '.rotateZ', orientation_offset[2])
            cmds.makeIdentity(obj_name, apply=True, rotate=True)

    def remove_numbers(string):
        """
        Removes all numbers (digits) from the provided string

        Args:
            string (string): input string (numbers will be removed from it)

        Returns:
            string (string): output string without numbers (digits)
        """
        return ''.join([i for i in string if not i.isdigit()])

    # Extract Biped Data
    elements_default = data_biped.elements_default
    elements = data_biped.elements
    settings = data_biped.settings
    rig_joints_default = data_biped.joints_default

    # Store selection and symmetry states
    cmds.select(d=True)  # Clear Selection
    cmds.symmetricModelling(e=True, symmetry=False)  # Turn off symmetry

    # Create Joints
    rig_joints = {}
    for obj in elements:
        if obj.endswith('_crv'):
            cmds.select(d=True)
            joint = cmds.joint(name=rename_proxy(elements.get(obj)), radius=1)
            constraint = cmds.pointConstraint(elements.get(obj), joint)
            cmds.delete(constraint)
            rig_joints[obj.replace('_crv', '_' + JNT_SUFFIX).replace('_proxy', '')] = joint

    # General Orients
    orient_to_target(rig_joints.get('spine01_jnt'), rig_joints.get('spine02_jnt'), (90, 0, 90))
    orient_to_target(rig_joints.get('spine02_jnt'), rig_joints.get('spine03_jnt'), (90, 0, 90))
    orient_to_target(rig_joints.get('spine03_jnt'), rig_joints.get('spine04_jnt'), (90, 0, 90))
    orient_to_target(rig_joints.get('spine04_jnt'), rig_joints.get('neck_base_jnt'), (90, 0, 90))
    orient_to_target(rig_joints.get('neck_base_jnt'), rig_joints.get('neck_mid_jnt'), (90, 0, 90))
    orient_to_target(rig_joints.get('neck_mid_jnt'), rig_joints.get('head_jnt'), (90, 0, 90))
    orient_to_target(rig_joints.get('head_jnt'), rig_joints.get('head_end_jnt'), (90, 0, 90))
    orient_to_target(rig_joints.get('jaw_jnt'), rig_joints.get('jaw_end_jnt'), (90, 0, 90))

    # Left Finger Orients
    orient_to_target(rig_joints.get('left_thumb01_jnt'), rig_joints.get('left_thumb02_jnt'), (0, 0, 0),
                     elements.get('left_thumb01_proxy_crv'), up_vec=(0, 1, 0), brute_force=True)
    orient_to_target(rig_joints.get('left_thumb02_jnt'), rig_joints.get('left_thumb03_jnt'), (0, 0, 0),
                     elements.get('left_thumb02_proxy_crv'), up_vec=(0, 1, 0), brute_force=True)
    orient_to_target(rig_joints.get('left_thumb03_jnt'), rig_joints.get('left_thumb04_jnt'), (0, 0, 0),
                     elements.get('left_thumb03_proxy_crv'), up_vec=(0, 1, 0), brute_force=True)

    orient_to_target(rig_joints.get('left_index01_jnt'), rig_joints.get('left_index02_jnt'), (0, 0, 90),
                     elements.get('left_index01_proxy_crv'), up_vec=(0, 1, 0), brute_force=True)
    orient_to_target(rig_joints.get('left_index02_jnt'), rig_joints.get('left_index03_jnt'), (0, 0, 90),
                     elements.get('left_index02_proxy_crv'), up_vec=(0, 1, 0), brute_force=True)
    orient_to_target(rig_joints.get('left_index03_jnt'), rig_joints.get('left_index04_jnt'), (0, 0, 90),
                     elements.get('left_index03_proxy_crv'), up_vec=(0, 1, 0), brute_force=True)

    orient_to_target(rig_joints.get('left_middle01_jnt'), rig_joints.get('left_middle02_jnt'), (0, 0, 90),
                     elements.get('left_middle01_proxy_crv'), up_vec=(0, 1, 0), brute_force=True)
    orient_to_target(rig_joints.get('left_middle02_jnt'), rig_joints.get('left_middle03_jnt'), (0, 0, 90),
                     elements.get('left_middle02_proxy_crv'), up_vec=(0, 1, 0), brute_force=True)
    orient_to_target(rig_joints.get('left_middle03_jnt'), rig_joints.get('left_middle04_jnt'), (0, 0, 90),
                     elements.get('left_middle03_proxy_crv'), up_vec=(0, 1, 0), brute_force=True)

    orient_to_target(rig_joints.get('left_ring01_jnt'), rig_joints.get('left_ring02_jnt'), (0, 0, 90),
                     elements.get('left_ring01_proxy_crv'), up_vec=(0, 1, 0), brute_force=True)
    orient_to_target(rig_joints.get('left_ring02_jnt'), rig_joints.get('left_ring03_jnt'), (0, 0, 90),
                     elements.get('left_ring02_proxy_crv'), up_vec=(0, 1, 0), brute_force=True)
    orient_to_target(rig_joints.get('left_ring03_jnt'), rig_joints.get('left_ring04_jnt'), (0, 0, 90),
                     elements.get('left_ring03_proxy_crv'), up_vec=(0, 1, 0), brute_force=True)

    orient_to_target(rig_joints.get('left_pinky01_jnt'), rig_joints.get('left_pinky02_jnt'), (0, 0, 90),
                     elements.get('left_pinky01_proxy_crv'), up_vec=(0, 1, 0), brute_force=True)
    orient_to_target(rig_joints.get('left_pinky02_jnt'), rig_joints.get('left_pinky03_jnt'), (0, 0, 90),
                     elements.get('left_pinky02_proxy_crv'), up_vec=(0, 1, 0), brute_force=True)
    orient_to_target(rig_joints.get('left_pinky03_jnt'), rig_joints.get('left_pinky04_jnt'), (0, 0, 90),
                     elements.get('left_pinky03_proxy_crv'), up_vec=(0, 1, 0), brute_force=True)

    # Right Finger Orients
    orient_to_target(rig_joints.get('right_thumb01_jnt'), rig_joints.get('right_thumb02_jnt'), (0, 180, 0),
                     elements.get('right_thumb01_proxy_crv'), up_vec=(0, -1, 0), aim_vec=(1, 0, 0),
                     brute_force=True)
    orient_to_target(rig_joints.get('right_thumb02_jnt'), rig_joints.get('right_thumb03_jnt'), (0, 180, 0),
                     elements.get('right_thumb02_proxy_crv'), up_vec=(0, -1, 0), aim_vec=(1, 0, 0),
                     brute_force=True)
    orient_to_target(rig_joints.get('right_thumb03_jnt'), rig_joints.get('right_thumb04_jnt'), (0, 180, 0),
                     elements.get('right_thumb03_proxy_crv'), up_vec=(0, -1, 0), aim_vec=(1, 0, 0),
                     brute_force=True)

    orient_to_target(rig_joints.get('right_index01_jnt'), rig_joints.get('right_index02_jnt'), (0, 180, 0),
                     elements.get('right_index01_proxy_crv'), up_vec=(0, 1, 0), aim_vec=(1, 0, 0),
                     brute_force=True)
    orient_to_target(rig_joints.get('right_index02_jnt'), rig_joints.get('right_index03_jnt'), (0, 180, 0),
                     elements.get('right_index02_proxy_crv'), up_vec=(0, 1, 0), aim_vec=(1, 0, 0),
                     brute_force=True)
    orient_to_target(rig_joints.get('right_index03_jnt'), rig_joints.get('right_index04_jnt'), (0, 180, 0),
                     elements.get('right_index03_proxy_crv'), up_vec=(0, 1, 0), aim_vec=(1, 0, 0),
                     brute_force=True)

    orient_to_target(rig_joints.get('right_middle01_jnt'), rig_joints.get('right_middle02_jnt'), (0, 180, 0),
                     elements.get('right_middle01_proxy_crv'), up_vec=(0, 1, 0), aim_vec=(1, 0, 0),
                     brute_force=True)
    orient_to_target(rig_joints.get('right_middle02_jnt'), rig_joints.get('right_middle03_jnt'), (0, 180, 0),
                     elements.get('right_middle02_proxy_crv'), up_vec=(0, 1, 0), aim_vec=(1, 0, 0),
                     brute_force=True)
    orient_to_target(rig_joints.get('right_middle03_jnt'), rig_joints.get('right_middle04_jnt'), (0, 180, 0),
                     elements.get('right_middle03_proxy_crv'), up_vec=(0, 1, 0), aim_vec=(1, 0, 0),
                     brute_force=True)

    orient_to_target(rig_joints.get('right_ring01_jnt'), rig_joints.get('right_ring02_jnt'), (0, 180, 0),
                     elements.get('right_ring01_proxy_crv'), up_vec=(0, 1, 0), aim_vec=(1, 0, 0),
                     brute_force=True)
    orient_to_target(rig_joints.get('right_ring02_jnt'), rig_joints.get('right_ring03_jnt'), (0, 180, 0),
                     elements.get('right_ring02_proxy_crv'), up_vec=(0, 1, 0), aim_vec=(1, 0, 0),
                     brute_force=True)
    orient_to_target(rig_joints.get('right_ring03_jnt'), rig_joints.get('right_ring04_jnt'), (0, 180, 0),
                     elements.get('right_ring03_proxy_crv'), up_vec=(0, 1, 0), aim_vec=(1, 0, 0),
                     brute_force=True)

    orient_to_target(rig_joints.get('right_pinky01_jnt'), rig_joints.get('right_pinky02_jnt'), (0, 180, 0),
                     elements.get('right_pinky01_proxy_crv'), up_vec=(0, 1, 0), aim_vec=(1, 0, 0),
                     brute_force=True)
    orient_to_target(rig_joints.get('right_pinky02_jnt'), rig_joints.get('right_pinky03_jnt'), (0, 180, 0),
                     elements.get('right_pinky02_proxy_crv'), up_vec=(0, 1, 0), aim_vec=(1, 0, 0),
                     brute_force=True)
    orient_to_target(rig_joints.get('right_pinky03_jnt'), rig_joints.get('right_pinky04_jnt'), (0, 180, 0),
                     elements.get('right_pinky03_proxy_crv'), up_vec=(0, 1, 0), aim_vec=(1, 0, 0),
                     brute_force=True)

    # Set Arm Orientation
    orient_to_target(rig_joints.get('left_clavicle_jnt'), rig_joints.get('left_shoulder_jnt'), (-90, 0, 0),
                     elements.get('left_clavicle_proxy_crv'))
    orient_to_target(rig_joints.get('left_shoulder_jnt'), rig_joints.get('left_elbow_jnt'), (-90, 0, 0))
    orient_to_target(rig_joints.get('left_elbow_jnt'), rig_joints.get('left_wrist_jnt'), (-90, 0, 0),
                     elements.get('left_elbow_proxy_crv'))

    orient_to_target(rig_joints.get('right_clavicle_jnt'), rig_joints.get('right_shoulder_jnt'), (90, 0, 0),
                     elements.get('right_clavicle_proxy_crv'), (-1, 0, 0))
    orient_to_target(rig_joints.get('right_shoulder_jnt'), rig_joints.get('right_elbow_jnt'), (90, 0, 0),
                     aim_vec=(-1, 0, 0))
    orient_to_target(rig_joints.get('right_elbow_jnt'), rig_joints.get('right_wrist_jnt'), (90, 0, 0),
                     elements.get('right_elbow_proxy_crv'), aim_vec=(-1, 0, 0))

    # Set Leg Orientation
    orient_to_target(rig_joints.get('left_hip_jnt'), rig_joints.get('left_knee_jnt'), (90, 0, -90))
    orient_to_target(rig_joints.get('left_knee_jnt'), rig_joints.get('left_ankle_jnt'), (90, 0, -90),
                     elements.get('left_knee_proxy_crv'))

    orient_to_target(rig_joints.get('right_hip_jnt'), rig_joints.get('right_knee_jnt'), (90, 0, -90),
                     aim_vec=(-1, 0, 0))
    orient_to_target(rig_joints.get('right_knee_jnt'), rig_joints.get('right_ankle_jnt'), (90, 0, -90),
                     elements.get('right_knee_proxy_crv'), (-1, 0, 0))

    # Set Foot Orientation
    orient_to_target(rig_joints.get('left_ankle_jnt'), rig_joints.get('left_ball_jnt'), (90, 0, -90),
                     elements.get('left_ankle_proxy_crv'))
    orient_to_target(rig_joints.get('left_ball_jnt'), rig_joints.get('left_toe_jnt'), (90, 0, -90),
                     elements.get('left_ball_proxy_crv'))

    orient_to_target(rig_joints.get('right_ankle_jnt'), rig_joints.get('right_ball_jnt'), (90, 0, -90),
                     elements.get('right_ankle_proxy_crv'), (-1, 0, 0))
    orient_to_target(rig_joints.get('right_ball_jnt'), rig_joints.get('right_toe_jnt'), (90, 0, -90),
                     elements.get('right_ball_proxy_crv'), (-1, 0, 0))

    # # Enforce Right Hip Orientation
    # cmds.joint(rig_joints.get('cog_jnt'), e=True, oj='none', zso=True)  # ch

    # Center Parenting
    cmds.parent(rig_joints.get('spine01_jnt'), rig_joints.get('cog_jnt'))
    cmds.parent(rig_joints.get('spine02_jnt'), rig_joints.get('spine01_jnt'))
    cmds.parent(rig_joints.get('spine03_jnt'), rig_joints.get('spine02_jnt'))
    cmds.parent(rig_joints.get('spine04_jnt'), rig_joints.get('spine03_jnt'))
    cmds.parent(rig_joints.get('neck_base_jnt'), rig_joints.get('spine04_jnt'))
    cmds.parent(rig_joints.get('neck_mid_jnt'), rig_joints.get('neck_base_jnt'))
    cmds.parent(rig_joints.get('head_jnt'), rig_joints.get('neck_mid_jnt'))
    cmds.parent(rig_joints.get('head_end_jnt'), rig_joints.get('head_jnt'))
    cmds.parent(rig_joints.get('jaw_end_jnt'), rig_joints.get('jaw_jnt'))

    # Left Fingers Parenting
    cmds.parent(rig_joints.get('left_thumb01_jnt'), rig_joints.get('left_wrist_jnt'))
    cmds.parent(rig_joints.get('left_thumb02_jnt'), rig_joints.get('left_thumb01_jnt'))
    cmds.parent(rig_joints.get('left_thumb03_jnt'), rig_joints.get('left_thumb02_jnt'))
    cmds.parent(rig_joints.get('left_thumb04_jnt'), rig_joints.get('left_thumb03_jnt'))

    cmds.parent(rig_joints.get('left_index01_jnt'), rig_joints.get('left_wrist_jnt'))
    cmds.parent(rig_joints.get('left_index02_jnt'), rig_joints.get('left_index01_jnt'))
    cmds.parent(rig_joints.get('left_index03_jnt'), rig_joints.get('left_index02_jnt'))
    cmds.parent(rig_joints.get('left_index04_jnt'), rig_joints.get('left_index03_jnt'))

    cmds.parent(rig_joints.get('left_middle01_jnt'), rig_joints.get('left_wrist_jnt'))
    cmds.parent(rig_joints.get('left_middle02_jnt'), rig_joints.get('left_middle01_jnt'))
    cmds.parent(rig_joints.get('left_middle03_jnt'), rig_joints.get('left_middle02_jnt'))
    cmds.parent(rig_joints.get('left_middle04_jnt'), rig_joints.get('left_middle03_jnt'))

    cmds.parent(rig_joints.get('left_ring01_jnt'), rig_joints.get('left_wrist_jnt'))
    cmds.parent(rig_joints.get('left_ring02_jnt'), rig_joints.get('left_ring01_jnt'))
    cmds.parent(rig_joints.get('left_ring03_jnt'), rig_joints.get('left_ring02_jnt'))
    cmds.parent(rig_joints.get('left_ring04_jnt'), rig_joints.get('left_ring03_jnt'))

    cmds.parent(rig_joints.get('left_pinky01_jnt'), rig_joints.get('left_wrist_jnt'))
    cmds.parent(rig_joints.get('left_pinky02_jnt'), rig_joints.get('left_pinky01_jnt'))
    cmds.parent(rig_joints.get('left_pinky03_jnt'), rig_joints.get('left_pinky02_jnt'))
    cmds.parent(rig_joints.get('left_pinky04_jnt'), rig_joints.get('left_pinky03_jnt'))

    # Right Fingers Parenting
    cmds.parent(rig_joints.get('right_thumb01_jnt'), rig_joints.get('right_wrist_jnt'))
    cmds.parent(rig_joints.get('right_thumb02_jnt'), rig_joints.get('right_thumb01_jnt'))
    cmds.parent(rig_joints.get('right_thumb03_jnt'), rig_joints.get('right_thumb02_jnt'))
    cmds.parent(rig_joints.get('right_thumb04_jnt'), rig_joints.get('right_thumb03_jnt'))

    cmds.parent(rig_joints.get('right_index01_jnt'), rig_joints.get('right_wrist_jnt'))
    cmds.parent(rig_joints.get('right_index02_jnt'), rig_joints.get('right_index01_jnt'))
    cmds.parent(rig_joints.get('right_index03_jnt'), rig_joints.get('right_index02_jnt'))
    cmds.parent(rig_joints.get('right_index04_jnt'), rig_joints.get('right_index03_jnt'))

    cmds.parent(rig_joints.get('right_middle01_jnt'), rig_joints.get('right_wrist_jnt'))
    cmds.parent(rig_joints.get('right_middle02_jnt'), rig_joints.get('right_middle01_jnt'))
    cmds.parent(rig_joints.get('right_middle03_jnt'), rig_joints.get('right_middle02_jnt'))
    cmds.parent(rig_joints.get('right_middle04_jnt'), rig_joints.get('right_middle03_jnt'))

    cmds.parent(rig_joints.get('right_ring01_jnt'), rig_joints.get('right_wrist_jnt'))
    cmds.parent(rig_joints.get('right_ring02_jnt'), rig_joints.get('right_ring01_jnt'))
    cmds.parent(rig_joints.get('right_ring03_jnt'), rig_joints.get('right_ring02_jnt'))
    cmds.parent(rig_joints.get('right_ring04_jnt'), rig_joints.get('right_ring03_jnt'))

    cmds.parent(rig_joints.get('right_pinky01_jnt'), rig_joints.get('right_wrist_jnt'))
    cmds.parent(rig_joints.get('right_pinky02_jnt'), rig_joints.get('right_pinky01_jnt'))
    cmds.parent(rig_joints.get('right_pinky03_jnt'), rig_joints.get('right_pinky02_jnt'))
    cmds.parent(rig_joints.get('right_pinky04_jnt'), rig_joints.get('right_pinky03_jnt'))

    # Extract General Scale Offset
    general_scale_offset = 0.0
    general_scale_offset += dist_center_to_center(rig_joints.get('hip_jnt'), rig_joints.get('spine01_jnt'))
    general_scale_offset += dist_center_to_center(rig_joints.get('spine01_jnt'), rig_joints.get('spine02_jnt'))
    general_scale_offset += dist_center_to_center(rig_joints.get('spine02_jnt'), rig_joints.get('spine03_jnt'))
    general_scale_offset += dist_center_to_center(rig_joints.get('spine03_jnt'), rig_joints.get('spine04_jnt'))
    general_scale_offset += dist_center_to_center(rig_joints.get('spine04_jnt'), rig_joints.get('neck_base_jnt'))
    general_scale_offset += dist_center_to_center(rig_joints.get('neck_base_jnt'), rig_joints.get('neck_mid_jnt'))
    general_scale_offset += dist_center_to_center(rig_joints.get('neck_base_jnt'), rig_joints.get('head_jnt'))
    general_scale_offset = general_scale_offset * .29

    # Adjust Joint Visibility
    joint_scale_offset = general_scale_offset * .06
    for jnt in rig_joints:
        joint = rig_joints.get(jnt)
        # End Joints
        if 'endJnt' in joint or rig_joints.get('right_toe_jnt') in joint or rig_joints.get('left_toe_jnt') in joint:
            cmds.setAttr(joint + '.radius', .6 * joint_scale_offset)
            add_node_note(joint,
                          "This is an end joint. This means that this joint shouldn't be an influence when skinning.")
            change_outliner_color(joint, (1, 0, 0))
            change_viewport_color(joint, (1, 0, 0))
        # Eye Joints
        elif rig_joints.get('left_eye_jnt') in joint or rig_joints.get('right_eye_jnt') in joint:
            cmds.setAttr(joint + '.radius', 3 * joint_scale_offset)
            change_viewport_color(joint, (0, 1, 0))
        # Finger Joints
        elif 'thumb' in joint or 'index' in joint or 'middle' in joint or 'ring' in joint or 'pinky' in joint:
            cmds.setAttr(joint + '.radius', 1 * joint_scale_offset)
            change_viewport_color(joint, (.3, .3, 0))
        # Side Joints
        elif 'left_' in joint or 'right_' in joint:
            cmds.setAttr(joint + '.radius', 2 * joint_scale_offset)
            change_viewport_color(joint, (.3, .3, 0))
        # Center Joints
        else:
            cmds.setAttr(joint + '.radius', 1.5 * joint_scale_offset)
            change_viewport_color(joint, (1, 1, 0))

        # Skeleton (Main) Joint
        if rig_joints.get('main_jnt') in joint:
            cmds.setAttr(joint + '.radius', .6 * joint_scale_offset)
            change_viewport_color(joint, (.4, .4, .4))
        elif rig_joints.get('head_jnt') in joint:
            cmds.setAttr(joint + '.radius', 3.5 * joint_scale_offset)
        elif rig_joints.get('neck_base_jnt') in joint or rig_joints.get('jaw_jnt') in joint:
            cmds.setAttr(joint + '.radius', 1.2 * joint_scale_offset)
        elif rig_joints.get('neck_mid_jnt') in joint:
            cmds.setAttr(joint + '.radius', .6 * joint_scale_offset)
            change_viewport_color(joint, (.3, .3, 0))

    # Left Arm Parenting
    cmds.parent(rig_joints.get('left_clavicle_jnt'), rig_joints.get('spine04_jnt'))
    cmds.parent(rig_joints.get('left_shoulder_jnt'), rig_joints.get('left_clavicle_jnt'))
    cmds.parent(rig_joints.get('left_elbow_jnt'), rig_joints.get('left_shoulder_jnt'))
    cmds.parent(rig_joints.get('left_wrist_jnt'), rig_joints.get('left_elbow_jnt'))

    # Right Arm Parenting
    cmds.parent(rig_joints.get('right_clavicle_jnt'), rig_joints.get('spine04_jnt'))
    cmds.parent(rig_joints.get('right_shoulder_jnt'), rig_joints.get('right_clavicle_jnt'))
    cmds.parent(rig_joints.get('right_elbow_jnt'), rig_joints.get('right_shoulder_jnt'))
    cmds.parent(rig_joints.get('right_wrist_jnt'), rig_joints.get('right_elbow_jnt'))

    # Left-Hand Hierarchy and Orients
    # Left Remove Fingers
    cmds.parent(rig_joints.get('left_wrist_jnt'), world=True)
    cmds.parent(rig_joints.get('left_thumb01_jnt'), world=True)
    cmds.parent(rig_joints.get('left_index01_jnt'), world=True)
    cmds.parent(rig_joints.get('left_middle01_jnt'), world=True)
    cmds.parent(rig_joints.get('left_ring01_jnt'), world=True)
    cmds.parent(rig_joints.get('left_pinky01_jnt'), world=True)

    # Left Wrist Orient
    temp_transform = cmds.group(empty=True, world=True,
                                name=elements.get('left_wrist_proxy_crv') + '_orient_target')
    constraint = cmds.parentConstraint(elements.get('left_wrist_proxy_crv'), temp_transform)
    cmds.delete(constraint)
    cmds.parent(temp_transform, elements.get('left_wrist_proxy_crv'))
    cmds.setAttr(temp_transform + '.tx', 1)
    orient_to_target(rig_joints.get('left_wrist_jnt'), temp_transform, (-90, 0, 0),
                     elements.get('left_wrist_proxy_crv'))
    cmds.delete(temp_transform)

    # Left Add Fingers
    cmds.parent(rig_joints.get('left_wrist_jnt'), rig_joints.get('left_elbow_jnt'))
    cmds.parent(rig_joints.get('left_thumb01_jnt'), rig_joints.get('left_wrist_jnt'))
    cmds.parent(rig_joints.get('left_index01_jnt'), rig_joints.get('left_wrist_jnt'))
    cmds.parent(rig_joints.get('left_middle01_jnt'), rig_joints.get('left_wrist_jnt'))
    cmds.parent(rig_joints.get('left_ring01_jnt'), rig_joints.get('left_wrist_jnt'))
    cmds.parent(rig_joints.get('left_pinky01_jnt'), rig_joints.get('left_wrist_jnt'))

    # Right-Hand Hierarchy and Orients
    # Right Remove Fingers
    cmds.parent(rig_joints.get('right_wrist_jnt'), world=True)
    cmds.parent(rig_joints.get('right_thumb01_jnt'), world=True)
    cmds.parent(rig_joints.get('right_index01_jnt'), world=True)
    cmds.parent(rig_joints.get('right_middle01_jnt'), world=True)
    cmds.parent(rig_joints.get('right_ring01_jnt'), world=True)
    cmds.parent(rig_joints.get('right_pinky01_jnt'), world=True)

    # Right Wrist Orient
    temp_transform = cmds.group(empty=True, world=True,
                                name=elements.get('right_wrist_proxy_crv') + '_orient_target')
    constraint = cmds.parentConstraint(elements.get('right_wrist_proxy_crv'), temp_transform)
    cmds.delete(constraint)
    cmds.parent(temp_transform, elements.get('right_wrist_proxy_crv'))
    cmds.setAttr(temp_transform + '.tx', -1)
    orient_to_target(rig_joints.get('right_wrist_jnt'), temp_transform, (90, 0, 0),
                     elements.get('right_wrist_proxy_crv'), (-1, 0, 0))
    cmds.delete(temp_transform)

    # Right Add Fingers
    cmds.parent(rig_joints.get('right_wrist_jnt'), rig_joints.get('right_elbow_jnt'))
    cmds.parent(rig_joints.get('right_thumb01_jnt'), rig_joints.get('right_wrist_jnt'))
    cmds.parent(rig_joints.get('right_index01_jnt'), rig_joints.get('right_wrist_jnt'))
    cmds.parent(rig_joints.get('right_middle01_jnt'), rig_joints.get('right_wrist_jnt'))
    cmds.parent(rig_joints.get('right_ring01_jnt'), rig_joints.get('right_wrist_jnt'))
    cmds.parent(rig_joints.get('right_pinky01_jnt'), rig_joints.get('right_wrist_jnt'))

    # The rest of the parenting and orients
    cmds.parent(rig_joints.get('left_eye_jnt'), rig_joints.get('head_jnt'))
    cmds.parent(rig_joints.get('right_eye_jnt'), rig_joints.get('head_jnt'))
    cmds.parent(rig_joints.get('jaw_jnt'), rig_joints.get('head_jnt'))

    cmds.parent(rig_joints.get('spine01_jnt'), world=True)

    # Root Orients
    cog_orients = cmds.xform(elements.get('cog_proxy_crv'), q=True, ro=True)
    cmds.joint(rig_joints.get('cog_jnt'), e=True, oj='none', zso=True)  # ch
    cmds.setAttr(rig_joints.get('cog_jnt') + '.jointOrientX', 90)
    cmds.setAttr(rig_joints.get('cog_jnt') + '.jointOrientY', 0)
    cmds.setAttr(rig_joints.get('cog_jnt') + '.jointOrientZ', 90)
    cmds.setAttr(rig_joints.get('cog_jnt') + '.rz', cog_orients[0])
    cmds.makeIdentity(rig_joints.get('cog_jnt'), apply=True, rotate=True)

    # Hip Orients
    hip_orients = cmds.xform(elements.get('hip_proxy_crv'), q=True, ro=True)
    cmds.joint(rig_joints.get('hip_jnt'), e=True, oj='none', zso=True)
    cmds.setAttr(rig_joints.get('hip_jnt') + '.jointOrientX', 90)
    cmds.setAttr(rig_joints.get('hip_jnt') + '.jointOrientY', 0)
    cmds.setAttr(rig_joints.get('hip_jnt') + '.jointOrientZ', 90)
    cmds.setAttr(rig_joints.get('hip_jnt') + '.rz', hip_orients[0])
    cmds.makeIdentity(rig_joints.get('hip_jnt'), apply=True, rotate=True)

    # Right Leg Parenting
    cmds.parent(rig_joints.get('right_knee_jnt'), rig_joints.get('right_hip_jnt'))
    cmds.parent(rig_joints.get('right_ankle_jnt'), rig_joints.get('right_knee_jnt'))
    cmds.parent(rig_joints.get('right_ball_jnt'), rig_joints.get('right_ankle_jnt'))
    cmds.parent(rig_joints.get('right_toe_jnt'), rig_joints.get('right_ball_jnt'))

    # Left Leg Parenting
    cmds.parent(rig_joints.get('left_knee_jnt'), rig_joints.get('left_hip_jnt'))
    cmds.parent(rig_joints.get('left_ankle_jnt'), rig_joints.get('left_knee_jnt'))
    cmds.parent(rig_joints.get('left_ball_jnt'), rig_joints.get('left_ankle_jnt'))
    cmds.parent(rig_joints.get('left_toe_jnt'), rig_joints.get('left_ball_jnt'))

    # Re-parenting
    cmds.parent(rig_joints.get('hip_jnt'), rig_joints.get('cog_jnt'))
    cmds.parent(rig_joints.get('left_hip_jnt'), rig_joints.get('hip_jnt'))
    cmds.parent(rig_joints.get('right_hip_jnt'), rig_joints.get('hip_jnt'))
    cmds.parent(rig_joints.get('spine01_jnt'), rig_joints.get('cog_jnt'))
    cmds.parent(rig_joints.get('cog_jnt'), rig_joints.get('main_jnt'))

    # Oriented to their parent (end joints)
    for jnt in rig_joints:
        joint = rig_joints.get(jnt)
        if 'endJnt' in joint or rig_joints.get('right_toe_jnt') in joint or rig_joints.get('left_toe_jnt') in joint:
            cmds.setAttr(joint + '.jointOrientX', 0)
            cmds.setAttr(joint + '.jointOrientY', 0)
            cmds.setAttr(joint + '.jointOrientZ', 0)

    # Left Forearm Joint
    cmds.select(d=True)
    left_forearm_jnt = cmds.joint(name='left_forearm_' + JNT_SUFFIX,
                                  radius=cmds.getAttr(rig_joints.get('left_wrist_jnt') + '.radius') * .8)
    rig_joints['left_forearm_' + JNT_SUFFIX] = left_forearm_jnt
    cmds.delete(cmds.pointConstraint([rig_joints.get('left_wrist_jnt'), rig_joints.get('left_elbow_jnt')],
                                     rig_joints.get('left_forearm_jnt')))
    orient_to_target(rig_joints.get('left_forearm_jnt'), rig_joints.get('left_wrist_jnt'), (-90, 0, 0))
    cmds.parent(rig_joints.get('left_forearm_jnt'), rig_joints.get('left_elbow_jnt'))
    change_viewport_color(rig_joints.get('left_forearm_jnt'), (1, 1, 0))

    # Right Forearm Joint
    cmds.select(d=True)
    right_forearm_jnt = cmds.joint(name='right_forearm_' + JNT_SUFFIX,
                                   radius=cmds.getAttr(rig_joints.get('right_wrist_jnt') + '.radius') * .8)
    rig_joints['right_forearm_' + JNT_SUFFIX] = right_forearm_jnt
    cmds.delete(cmds.pointConstraint([rig_joints.get('right_wrist_jnt'), rig_joints.get('right_elbow_jnt')],
                                     rig_joints.get('right_forearm_jnt')))
    orient_to_target(rig_joints.get('right_forearm_jnt'), rig_joints.get('right_wrist_jnt'), (90, 0, 0),
                     aim_vec=(-1, 0, 0))
    cmds.parent(rig_joints.get('right_forearm_jnt'), rig_joints.get('right_elbow_jnt'))
    change_viewport_color(rig_joints.get('right_forearm_jnt'), (1, 1, 0))

    # ###### Create Organization Groups ######
    # Create Skeleton Group
    skeleton_grp = cmds.group(name=('skeleton_' + GRP_SUFFIX), empty=True, world=True)
    change_outliner_color(skeleton_grp, (.75, .45, .95))  # Purple (Like a joint)
    cmds.parent(rig_joints.get('main_jnt'), skeleton_grp)
    # Rig Setup Group
    rig_setup_grp = cmds.group(name='rig_setup_' + GRP_SUFFIX, empty=True, world=True)
    ik_solvers_grp = cmds.group(name='ikSolvers_' + GRP_SUFFIX, empty=True, world=True)
    change_outliner_color(rig_setup_grp, (1, .26, .26))
    change_outliner_color(ik_solvers_grp, (1, 1, .35))
    cmds.parent(ik_solvers_grp, rig_setup_grp)

    # Set Preferred Angles
    cmds.setAttr(rig_joints.get('left_hip_jnt') + '.preferredAngleZ', 90)
    cmds.setAttr(rig_joints.get('right_hip_jnt') + '.preferredAngleZ', 90)
    cmds.setAttr(rig_joints.get('left_knee_jnt') + '.preferredAngleZ', -90)
    cmds.setAttr(rig_joints.get('right_knee_jnt') + '.preferredAngleZ', -90)

    # Start Duplicating For IK/FK Switch
    ikfk_jnt_color = (1, .5, 1)
    ik_jnt_scale = cmds.getAttr(rig_joints.get('main_jnt') + '.radius') * 1.5
    ik_jnt_color = (.5, .5, 1)
    fk_jnt_scale = ik_jnt_scale / 2
    fk_jnt_color = (1, .5, .5)
    automation_jnt_color = (1, .17, .45)

    # Left Arms FK/IK
    left_clavicle_switch_jnt = cmds.duplicate(rig_joints.get('left_clavicle_jnt'),
                                              name=rig_joints.get('left_clavicle_jnt').replace(JNT_SUFFIX,
                                                                                               'switch_' + JNT_SUFFIX),
                                              parentOnly=True)[0]
    cmds.setAttr(left_clavicle_switch_jnt + '.radius', ik_jnt_scale)
    change_viewport_color(left_clavicle_switch_jnt, ikfk_jnt_color)
    cmds.parent(left_clavicle_switch_jnt, skeleton_grp)
    left_clavicle_switch_constraint = cmds.parentConstraint(rig_joints.get('left_clavicle_jnt'),
                                                            left_clavicle_switch_jnt)
    cmds.setAttr(left_clavicle_switch_constraint[0] + '.interpType', 0)

    # Left Arm IK
    left_shoulder_ik_jnt = cmds.duplicate(rig_joints.get('left_shoulder_jnt'),
                                          name=rig_joints.get('left_shoulder_jnt').replace(JNT_SUFFIX,
                                                                                           'ik_' + JNT_SUFFIX),
                                          parentOnly=True)[0]
    left_elbow_ik_jnt = cmds.duplicate(rig_joints.get('left_elbow_jnt'),
                                       name=rig_joints.get('left_elbow_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX),
                                       parentOnly=True)[0]
    left_wrist_ik_jnt = cmds.duplicate(rig_joints.get('left_wrist_jnt'),
                                       name=rig_joints.get('left_wrist_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX),
                                       parentOnly=True)[0]

    cmds.connectAttr(rig_joints.get('left_shoulder_jnt') + '.rotateOrder', left_shoulder_ik_jnt + '.rotateOrder',
                     f=True)
    cmds.connectAttr(rig_joints.get('left_elbow_jnt') + '.rotateOrder', left_elbow_ik_jnt + '.rotateOrder', f=True)
    cmds.connectAttr(rig_joints.get('left_wrist_jnt') + '.rotateOrder', left_wrist_ik_jnt + '.rotateOrder', f=True)

    cmds.setAttr(left_shoulder_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(left_elbow_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(left_wrist_ik_jnt + '.radius', ik_jnt_scale)

    change_viewport_color(left_shoulder_ik_jnt, ik_jnt_color)
    change_viewport_color(left_elbow_ik_jnt, ik_jnt_color)
    change_viewport_color(left_wrist_ik_jnt, ik_jnt_color)
    change_outliner_color(left_shoulder_ik_jnt, ik_jnt_color)
    change_outliner_color(left_elbow_ik_jnt, ik_jnt_color)
    change_outliner_color(left_wrist_ik_jnt, ik_jnt_color)

    cmds.parent(left_elbow_ik_jnt, left_shoulder_ik_jnt)
    cmds.parent(left_wrist_ik_jnt, left_elbow_ik_jnt)

    # Left Arm FK
    left_shoulder_fk_jnt = cmds.duplicate(rig_joints.get('left_shoulder_jnt'),
                                          name=rig_joints.get('left_shoulder_jnt').replace(JNT_SUFFIX,
                                                                                           'fk_' + JNT_SUFFIX),
                                          parentOnly=True)[0]
    left_elbow_fk_jnt = cmds.duplicate(rig_joints.get('left_elbow_jnt'),
                                       name=rig_joints.get('left_elbow_jnt').replace(JNT_SUFFIX, 'fk_' + JNT_SUFFIX),
                                       parentOnly=True)[0]
    left_wrist_fk_jnt = cmds.duplicate(rig_joints.get('left_wrist_jnt'),
                                       name=rig_joints.get('left_wrist_jnt').replace(JNT_SUFFIX, 'fk_' + JNT_SUFFIX),
                                       parentOnly=True)[0]

    cmds.connectAttr(rig_joints.get('left_shoulder_jnt') + '.rotateOrder', left_shoulder_fk_jnt + '.rotateOrder',
                     f=True)
    cmds.connectAttr(rig_joints.get('left_elbow_jnt') + '.rotateOrder', left_elbow_fk_jnt + '.rotateOrder', f=True)
    cmds.connectAttr(rig_joints.get('left_wrist_jnt') + '.rotateOrder', left_wrist_fk_jnt + '.rotateOrder', f=True)

    cmds.setAttr(left_shoulder_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(left_elbow_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(left_wrist_fk_jnt + '.radius', fk_jnt_scale)

    change_viewport_color(left_shoulder_fk_jnt, fk_jnt_color)
    change_viewport_color(left_elbow_fk_jnt, fk_jnt_color)
    change_viewport_color(left_wrist_fk_jnt, fk_jnt_color)
    change_outliner_color(left_shoulder_fk_jnt, fk_jnt_color)
    change_outliner_color(left_elbow_fk_jnt, fk_jnt_color)
    change_outliner_color(left_wrist_fk_jnt, fk_jnt_color)

    cmds.parent(left_shoulder_fk_jnt, left_clavicle_switch_jnt)
    cmds.parent(left_elbow_fk_jnt, left_shoulder_fk_jnt)
    cmds.parent(left_wrist_fk_jnt, left_elbow_fk_jnt)

    # Right Arms FK/IK
    right_clavicle_switch_jnt = rig_joints.get('right_clavicle_jnt').replace(JNT_SUFFIX, 'switch_' + JNT_SUFFIX)
    right_clavicle_switch_jnt = cmds.duplicate(rig_joints.get('right_clavicle_jnt'),
                                               name=right_clavicle_switch_jnt, parentOnly=True)[0]
    cmds.setAttr(right_clavicle_switch_jnt + '.radius', ik_jnt_scale)
    change_viewport_color(right_clavicle_switch_jnt, ikfk_jnt_color)
    cmds.parent(right_clavicle_switch_jnt, skeleton_grp)
    right_clavicle_switch_constraint = cmds.parentConstraint(rig_joints.get('right_clavicle_jnt'),
                                                             right_clavicle_switch_jnt)
    cmds.setAttr(right_clavicle_switch_constraint[0] + '.interpType', 0)

    # Right Arm IK
    right_shoulder_ik_jnt = cmds.duplicate(rig_joints.get('right_shoulder_jnt'),
                                           name=rig_joints.get('right_shoulder_jnt').replace(JNT_SUFFIX,
                                                                                             'ik_' + JNT_SUFFIX),
                                           parentOnly=True)[0]
    right_elbow_ik_jnt = cmds.duplicate(rig_joints.get('right_elbow_jnt'),
                                        name=rig_joints.get('right_elbow_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX),
                                        parentOnly=True)[0]
    right_wrist_ik_jnt = cmds.duplicate(rig_joints.get('right_wrist_jnt'),
                                        name=rig_joints.get('right_wrist_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX),
                                        parentOnly=True)[0]

    cmds.connectAttr(rig_joints.get('right_shoulder_jnt') + '.rotateOrder', right_shoulder_ik_jnt + '.rotateOrder',
                     f=True)
    cmds.connectAttr(rig_joints.get('right_elbow_jnt') + '.rotateOrder', right_elbow_ik_jnt + '.rotateOrder', f=True)
    cmds.connectAttr(rig_joints.get('right_wrist_jnt') + '.rotateOrder', right_wrist_ik_jnt + '.rotateOrder', f=True)

    cmds.setAttr(right_shoulder_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(right_elbow_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(right_wrist_ik_jnt + '.radius', ik_jnt_scale)

    change_viewport_color(right_shoulder_ik_jnt, ik_jnt_color)
    change_viewport_color(right_elbow_ik_jnt, ik_jnt_color)
    change_viewport_color(right_wrist_ik_jnt, ik_jnt_color)
    change_outliner_color(right_shoulder_ik_jnt, ik_jnt_color)
    change_outliner_color(right_elbow_ik_jnt, ik_jnt_color)
    change_outliner_color(right_wrist_ik_jnt, ik_jnt_color)

    cmds.parent(right_elbow_ik_jnt, right_shoulder_ik_jnt)
    cmds.parent(right_wrist_ik_jnt, right_elbow_ik_jnt)

    # Right Arm FK
    right_shoulder_fk_jnt = cmds.duplicate(rig_joints.get('right_shoulder_jnt'),
                                           name=rig_joints.get('right_shoulder_jnt').replace(JNT_SUFFIX,
                                                                                             'fk_' + JNT_SUFFIX),
                                           parentOnly=True)[0]
    right_elbow_fk_jnt = cmds.duplicate(rig_joints.get('right_elbow_jnt'),
                                        name=rig_joints.get('right_elbow_jnt').replace(JNT_SUFFIX, 'fk_' + JNT_SUFFIX),
                                        parentOnly=True)[0]
    right_wrist_fk_jnt = cmds.duplicate(rig_joints.get('right_wrist_jnt'),
                                        name=rig_joints.get('right_wrist_jnt').replace(JNT_SUFFIX, 'fk_' + JNT_SUFFIX),
                                        parentOnly=True)[0]

    cmds.connectAttr(rig_joints.get('right_shoulder_jnt') + '.rotateOrder', right_shoulder_fk_jnt + '.rotateOrder',
                     f=True)
    cmds.connectAttr(rig_joints.get('right_elbow_jnt') + '.rotateOrder', right_elbow_fk_jnt + '.rotateOrder', f=True)
    cmds.connectAttr(rig_joints.get('right_wrist_jnt') + '.rotateOrder', right_wrist_fk_jnt + '.rotateOrder', f=True)

    cmds.setAttr(right_shoulder_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(right_elbow_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(right_wrist_fk_jnt + '.radius', fk_jnt_scale)

    change_viewport_color(right_shoulder_fk_jnt, fk_jnt_color)
    change_viewport_color(right_elbow_fk_jnt, fk_jnt_color)
    change_viewport_color(right_wrist_fk_jnt, fk_jnt_color)
    change_outliner_color(right_shoulder_fk_jnt, fk_jnt_color)
    change_outliner_color(right_elbow_fk_jnt, fk_jnt_color)
    change_outliner_color(right_wrist_fk_jnt, fk_jnt_color)

    cmds.parent(right_shoulder_fk_jnt, right_clavicle_switch_jnt)
    cmds.parent(right_elbow_fk_jnt, right_shoulder_fk_jnt)
    cmds.parent(right_wrist_fk_jnt, right_elbow_fk_jnt)

    # Legs FK/IK Switch
    hip_switch_jnt = cmds.duplicate(rig_joints.get('hip_jnt'),
                                    name=rig_joints.get('hip_jnt').replace(JNT_SUFFIX, 'switch_' + JNT_SUFFIX),
                                    parentOnly=True)[0]
    cmds.setAttr(hip_switch_jnt + '.radius', ik_jnt_scale)
    change_viewport_color(hip_switch_jnt, ikfk_jnt_color)
    cmds.parent(hip_switch_jnt, skeleton_grp)
    hip_switch_constraint = cmds.parentConstraint(rig_joints.get('hip_jnt'), hip_switch_jnt)
    cmds.setAttr(hip_switch_constraint[0] + '.interpType', 0)

    # Left Leg IK
    left_hip_ik_jnt = cmds.duplicate(rig_joints.get('left_hip_jnt'),
                                     name=rig_joints.get('left_hip_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX),
                                     parentOnly=True)[0]
    left_knee_ik_jnt = cmds.duplicate(rig_joints.get('left_knee_jnt'),
                                      name=rig_joints.get('left_knee_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX),
                                      parentOnly=True)[0]
    left_ankle_ik_jnt = cmds.duplicate(rig_joints.get('left_ankle_jnt'),
                                       name=rig_joints.get('left_ankle_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX),
                                       parentOnly=True)[0]
    left_ball_ik_jnt = cmds.duplicate(rig_joints.get('left_ball_jnt'),
                                      name=rig_joints.get('left_ball_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX),
                                      parentOnly=True)[0]
    left_toe_ik_jnt = cmds.duplicate(rig_joints.get('left_toe_jnt'),
                                     name=rig_joints.get('left_toe_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX),
                                     parentOnly=True)[0]

    cmds.connectAttr(rig_joints.get('left_hip_jnt') + '.rotateOrder', left_hip_ik_jnt + '.rotateOrder', f=True)
    cmds.connectAttr(rig_joints.get('left_knee_jnt') + '.rotateOrder', left_knee_ik_jnt + '.rotateOrder', f=True)
    cmds.connectAttr(rig_joints.get('left_ankle_jnt') + '.rotateOrder', left_ankle_ik_jnt + '.rotateOrder', f=True)
    cmds.connectAttr(rig_joints.get('left_ball_jnt') + '.rotateOrder', left_ball_ik_jnt + '.rotateOrder', f=True)
    cmds.connectAttr(rig_joints.get('left_toe_jnt') + '.rotateOrder', left_toe_ik_jnt + '.rotateOrder', f=True)

    cmds.setAttr(left_hip_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(left_knee_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(left_ankle_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(left_ball_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(left_toe_ik_jnt + '.radius', ik_jnt_scale)

    change_viewport_color(left_hip_ik_jnt, ik_jnt_color)
    change_viewport_color(left_knee_ik_jnt, ik_jnt_color)
    change_viewport_color(left_ankle_ik_jnt, ik_jnt_color)
    change_viewport_color(left_ball_ik_jnt, ik_jnt_color)
    change_viewport_color(left_toe_ik_jnt, ik_jnt_color)

    change_outliner_color(left_hip_ik_jnt, ik_jnt_color)
    change_outliner_color(left_knee_ik_jnt, ik_jnt_color)
    change_outliner_color(left_ankle_ik_jnt, ik_jnt_color)
    change_outliner_color(left_ball_ik_jnt, ik_jnt_color)
    change_outliner_color(left_toe_ik_jnt, ik_jnt_color)

    cmds.parent(left_hip_ik_jnt, hip_switch_jnt)
    cmds.parent(left_knee_ik_jnt, left_hip_ik_jnt)
    cmds.parent(left_ankle_ik_jnt, left_knee_ik_jnt)
    cmds.parent(left_ball_ik_jnt, left_ankle_ik_jnt)
    cmds.parent(left_toe_ik_jnt, left_ball_ik_jnt)

    # Left Leg FK
    left_hip_fk_jnt = cmds.duplicate(rig_joints.get('left_hip_jnt'),
                                     name=rig_joints.get('left_hip_jnt').replace(JNT_SUFFIX, 'fk_' + JNT_SUFFIX),
                                     parentOnly=True)[0]
    left_knee_fk_jnt = cmds.duplicate(rig_joints.get('left_knee_jnt'),
                                      name=rig_joints.get('left_knee_jnt').replace(JNT_SUFFIX, 'fk_' + JNT_SUFFIX),
                                      parentOnly=True)[0]
    left_ankle_fk_jnt = cmds.duplicate(rig_joints.get('left_ankle_jnt'),
                                       name=rig_joints.get('left_ankle_jnt').replace(JNT_SUFFIX, 'fk_' + JNT_SUFFIX),
                                       parentOnly=True)[0]
    left_ball_fk_jnt = cmds.duplicate(rig_joints.get('left_ball_jnt'),
                                      name=rig_joints.get('left_ball_jnt').replace(JNT_SUFFIX, 'fk_' + JNT_SUFFIX),
                                      parentOnly=True)[0]
    left_toe_fk_jnt = cmds.duplicate(rig_joints.get('left_toe_jnt'),
                                     name=rig_joints.get('left_toe_jnt').replace(JNT_SUFFIX, 'fk_' + JNT_SUFFIX),
                                     parentOnly=True)[0]

    cmds.connectAttr(rig_joints.get('left_hip_jnt') + '.rotateOrder', left_hip_fk_jnt + '.rotateOrder', f=True)
    cmds.connectAttr(rig_joints.get('left_knee_jnt') + '.rotateOrder', left_knee_fk_jnt + '.rotateOrder', f=True)
    cmds.connectAttr(rig_joints.get('left_ankle_jnt') + '.rotateOrder', left_ankle_fk_jnt + '.rotateOrder', f=True)
    cmds.connectAttr(rig_joints.get('left_ball_jnt') + '.rotateOrder', left_ball_fk_jnt + '.rotateOrder', f=True)
    cmds.connectAttr(rig_joints.get('left_toe_jnt') + '.rotateOrder', left_toe_fk_jnt + '.rotateOrder', f=True)

    cmds.setAttr(left_hip_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(left_knee_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(left_ankle_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(left_ball_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(left_toe_fk_jnt + '.radius', fk_jnt_scale)

    change_viewport_color(left_hip_fk_jnt, fk_jnt_color)
    change_viewport_color(left_knee_fk_jnt, fk_jnt_color)
    change_viewport_color(left_ankle_fk_jnt, fk_jnt_color)
    change_viewport_color(left_ball_fk_jnt, fk_jnt_color)
    change_viewport_color(left_toe_fk_jnt, fk_jnt_color)

    change_outliner_color(left_hip_fk_jnt, fk_jnt_color)
    change_outliner_color(left_knee_fk_jnt, fk_jnt_color)
    change_outliner_color(left_ankle_fk_jnt, fk_jnt_color)
    change_outliner_color(left_ball_fk_jnt, fk_jnt_color)
    change_outliner_color(left_toe_fk_jnt, fk_jnt_color)

    cmds.parent(left_hip_fk_jnt, hip_switch_jnt)
    cmds.parent(left_knee_fk_jnt, left_hip_fk_jnt)
    cmds.parent(left_ankle_fk_jnt, left_knee_fk_jnt)
    cmds.parent(left_ball_fk_jnt, left_ankle_fk_jnt)
    cmds.parent(left_toe_fk_jnt, left_ball_fk_jnt)

    # Right Leg IK
    right_hip_ik_jnt = cmds.duplicate(rig_joints.get('right_hip_jnt'),
                                      name=rig_joints.get('right_hip_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX),
                                      parentOnly=True)[0]
    right_knee_ik_jnt = cmds.duplicate(rig_joints.get('right_knee_jnt'),
                                       name=rig_joints.get('right_knee_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX),
                                       parentOnly=True)[0]
    right_ankle_ik_jnt = cmds.duplicate(rig_joints.get('right_ankle_jnt'),
                                        name=rig_joints.get('right_ankle_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX),
                                        parentOnly=True)[0]
    right_ball_ik_jnt = cmds.duplicate(rig_joints.get('right_ball_jnt'),
                                       name=rig_joints.get('right_ball_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX),
                                       parentOnly=True)[0]
    right_toe_ik_jnt = cmds.duplicate(rig_joints.get('right_toe_jnt'),
                                      name=rig_joints.get('right_toe_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX),
                                      parentOnly=True)[0]

    cmds.connectAttr(rig_joints.get('right_hip_jnt') + '.rotateOrder', right_hip_ik_jnt + '.rotateOrder', f=True)
    cmds.connectAttr(rig_joints.get('right_knee_jnt') + '.rotateOrder', right_knee_ik_jnt + '.rotateOrder', f=True)
    cmds.connectAttr(rig_joints.get('right_ankle_jnt') + '.rotateOrder', right_ankle_ik_jnt + '.rotateOrder', f=True)
    cmds.connectAttr(rig_joints.get('right_ball_jnt') + '.rotateOrder', right_ball_ik_jnt + '.rotateOrder', f=True)
    cmds.connectAttr(rig_joints.get('right_toe_jnt') + '.rotateOrder', right_toe_ik_jnt + '.rotateOrder', f=True)

    cmds.setAttr(right_hip_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(right_knee_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(right_ankle_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(right_ball_ik_jnt + '.radius', ik_jnt_scale)
    cmds.setAttr(right_toe_ik_jnt + '.radius', ik_jnt_scale)

    change_viewport_color(right_hip_ik_jnt, ik_jnt_color)
    change_viewport_color(right_knee_ik_jnt, ik_jnt_color)
    change_viewport_color(right_ankle_ik_jnt, ik_jnt_color)
    change_viewport_color(right_ball_ik_jnt, ik_jnt_color)
    change_viewport_color(right_toe_ik_jnt, ik_jnt_color)

    change_outliner_color(right_hip_ik_jnt, ik_jnt_color)
    change_outliner_color(right_knee_ik_jnt, ik_jnt_color)
    change_outliner_color(right_ankle_ik_jnt, ik_jnt_color)
    change_outliner_color(right_ball_ik_jnt, ik_jnt_color)
    change_outliner_color(right_toe_ik_jnt, ik_jnt_color)

    cmds.parent(right_hip_ik_jnt, hip_switch_jnt)
    cmds.parent(right_knee_ik_jnt, right_hip_ik_jnt)
    cmds.parent(right_ankle_ik_jnt, right_knee_ik_jnt)
    cmds.parent(right_ball_ik_jnt, right_ankle_ik_jnt)
    cmds.parent(right_toe_ik_jnt, right_ball_ik_jnt)

    # Right Leg FK
    right_hip_fk_jnt = cmds.duplicate(rig_joints.get('right_hip_jnt'),
                                      name=rig_joints.get('right_hip_jnt').replace(JNT_SUFFIX, 'fk_' + JNT_SUFFIX),
                                      parentOnly=True)[0]
    right_knee_fk_jnt = cmds.duplicate(rig_joints.get('right_knee_jnt'),
                                       name=rig_joints.get('right_knee_jnt').replace(JNT_SUFFIX, 'fk_' + JNT_SUFFIX),
                                       parentOnly=True)[0]
    right_ankle_fk_jnt = cmds.duplicate(rig_joints.get('right_ankle_jnt'),
                                        name=rig_joints.get('right_ankle_jnt').replace(JNT_SUFFIX, 'fk_' + JNT_SUFFIX),
                                        parentOnly=True)[0]
    right_ball_fk_jnt = cmds.duplicate(rig_joints.get('right_ball_jnt'),
                                       name=rig_joints.get('right_ball_jnt').replace(JNT_SUFFIX, 'fk_' + JNT_SUFFIX),
                                       parentOnly=True)[0]
    right_toe_fk_jnt = cmds.duplicate(rig_joints.get('right_toe_jnt'),
                                      name=rig_joints.get('right_toe_jnt').replace(JNT_SUFFIX, 'fk_' + JNT_SUFFIX),
                                      parentOnly=True)[0]

    cmds.connectAttr(rig_joints.get('right_hip_jnt') + '.rotateOrder', right_hip_fk_jnt + '.rotateOrder', f=True)
    cmds.connectAttr(rig_joints.get('right_knee_jnt') + '.rotateOrder', right_knee_fk_jnt + '.rotateOrder', f=True)
    cmds.connectAttr(rig_joints.get('right_ankle_jnt') + '.rotateOrder', right_ankle_fk_jnt + '.rotateOrder', f=True)
    cmds.connectAttr(rig_joints.get('right_ball_jnt') + '.rotateOrder', right_ball_fk_jnt + '.rotateOrder', f=True)
    cmds.connectAttr(rig_joints.get('right_toe_jnt') + '.rotateOrder', right_toe_fk_jnt + '.rotateOrder', f=True)

    cmds.setAttr(right_hip_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(right_knee_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(right_ankle_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(right_ball_fk_jnt + '.radius', fk_jnt_scale)
    cmds.setAttr(right_toe_fk_jnt + '.radius', fk_jnt_scale)

    change_viewport_color(right_hip_fk_jnt, fk_jnt_color)
    change_viewport_color(right_knee_fk_jnt, fk_jnt_color)
    change_viewport_color(right_ankle_fk_jnt, fk_jnt_color)
    change_viewport_color(right_ball_fk_jnt, fk_jnt_color)
    change_viewport_color(right_toe_fk_jnt, fk_jnt_color)

    change_outliner_color(right_hip_fk_jnt, fk_jnt_color)
    change_outliner_color(right_knee_fk_jnt, fk_jnt_color)
    change_outliner_color(right_ankle_fk_jnt, fk_jnt_color)
    change_outliner_color(right_ball_fk_jnt, fk_jnt_color)
    change_outliner_color(right_toe_fk_jnt, fk_jnt_color)

    cmds.parent(right_hip_fk_jnt, hip_switch_jnt)
    cmds.parent(right_knee_fk_jnt, right_hip_fk_jnt)
    cmds.parent(right_ankle_fk_jnt, right_knee_fk_jnt)
    cmds.parent(right_ball_fk_jnt, right_ankle_fk_jnt)
    cmds.parent(right_toe_fk_jnt, right_ball_fk_jnt)

    # ########################## Start Creating Controls ##########################

    # General Automation Hierarchy - Used for misc systems such as auto breathing and aim lines
    general_automation_grp = cmds.group(name='generalAutomation_grp', world=True, empty=True)
    change_outliner_color(general_automation_grp, (1, .65, .45))

    controls_grp = cmds.group(name='controls_' + GRP_SUFFIX, empty=True, world=True)
    change_outliner_color(controls_grp, (1, 0.47, 0.18))

    arms_automation_grp = cmds.group(name='armsAutomation_' + GRP_SUFFIX, empty=True, world=True)
    change_outliner_color(arms_automation_grp, (1, .65, .45))

    # Main Ctrl
    main_ctrl = create_main_control(name='main_' + CTRL_SUFFIX)
    main_ctrl_scale = cmds.xform(elements.get('main_crv'), q=True, ws=True, scale=True)
    cmds.scale(main_ctrl_scale[1], main_ctrl_scale[1], main_ctrl_scale[1], main_ctrl)

    cmds.makeIdentity(main_ctrl, apply=True, scale=True)
    for shape in cmds.listRelatives(main_ctrl, s=True, f=True) or []:
        try:
            cmds.setAttr(shape + '.lineWidth', 3)
        except Exception as e:
            logger.debug(str(e))

    change_viewport_color(main_ctrl, (1, 0.171, 0.448))
    main_ctrl_grp = cmds.group(name=main_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(main_ctrl, main_ctrl_grp)
    cmds.parent(main_ctrl_grp, controls_grp)

    # Direction Control
    direction_ctrl = cmds.circle(name='direction_' + CTRL_SUFFIX, nr=(0, 1, 0), ch=False, radius=44.5)[0]
    for shape in cmds.listRelatives(direction_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(direction_ctrl))
    change_viewport_color(direction_ctrl, (1, 1, 0))
    cmds.delete(cmds.scaleConstraint(elements.get('main_crv'), direction_ctrl))
    cmds.makeIdentity(direction_ctrl, apply=True, scale=True)
    direction_ctrl_grp = cmds.group(name=direction_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(direction_ctrl, direction_ctrl_grp)
    cmds.parent(direction_ctrl_grp, main_ctrl)
    cmds.rebuildCurve(direction_ctrl, ch=False, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=20, d=3, tol=0.01)

    # COG Control
    cog_ctrl_a = cmds.circle(name=rig_joints.get('cog_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX, nr=(1, 0, 0),
                             ch=False, radius=general_scale_offset)[0]
    cog_ctrl_b = cmds.curve(
        p=[[0.0, 0.0, 0.0], [0.0, -18.225, 0.0], [0.681, -18.317, 0.0], [1.301, -18.581, 0.0], [1.838, -18.988, 0.0],
           [2.254, -19.526, 0.0], [2.509, -20.155, 0.0], [2.6, -20.825, 0.0], [0.0, -20.835, 0.0], [0.0, -18.225, 0.0],
           [-0.681, -18.317, 0.0], [-1.311, -18.581, 0.0], [-1.838, -18.988, 0.0], [-2.254, -19.536, 0.0],
           [-2.509, -20.155, 0.0], [-2.61, -20.825, 0.0], [-2.519, -21.507, 0.0], [-2.254, -22.126, 0.0],
           [-1.838, -22.665, 0.0], [-1.301, -23.082, 0.0], [-0.681, -23.336, 0.0], [0.0, -23.437, 0.0],
           [0.67, -23.346, 0.0], [1.301, -23.082, 0.0], [1.838, -22.675, 0.0], [2.244, -22.136, 0.0],
           [2.509, -21.496, 0.0], [2.6, -20.825, 0.0], [-2.61, -20.825, 0.0], [0.0, -20.835, 0.0], [0.0, -23.437, 0.0]],
        d=1)

    add_orient_offset(cog_ctrl_a, (90, 0, -90), apply=settings.get('uniform_ctrl_orient'))
    add_orient_offset(cog_ctrl_b, (90, 0, -90), apply=settings.get('uniform_ctrl_orient'))

    cog_ctrl = combine_curves_list([cog_ctrl_a, cog_ctrl_b])

    shapes = cmds.listRelatives(cog_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format(cog_ctrl.replace(CTRL_SUFFIX, 'circle')))
    cmds.rename(shapes[1], '{0}Shape'.format(cog_ctrl.replace(CTRL_SUFFIX, 'pin')))

    change_viewport_color(cog_ctrl, (1, 1, 0))
    cmds.makeIdentity(cog_ctrl, apply=True, scale=True)
    cog_ctrl_grp = cmds.group(name=cog_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(cog_ctrl, cog_ctrl_grp)

    cmds.delete(cmds.parentConstraint(rig_joints.get('cog_jnt'), cog_ctrl_grp))
    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(-90, -90, 0, cog_ctrl_grp, os=True, relative=True)

    cmds.parent(cog_ctrl_grp, direction_ctrl)

    # Add Separator
    cmds.addAttr(cog_ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
    cmds.setAttr(cog_ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)

    # Expose Custom Rotate Order
    cmds.addAttr(cog_ctrl, ln='rotationOrder', at='enum', en=ROTATE_ORDER_ENUM, keyable=True, niceName='Rotate Order')
    cmds.connectAttr(cog_ctrl + '.rotationOrder', cog_ctrl + '.rotateOrder', f=True)

    # Setup Shape Switch
    setup_shape_switch(cog_ctrl, attr='controlShape', shape_names=['circle', 'pin'], shape_enum=['Circle', 'Pin'])

    # Show Scale Ctrl
    cmds.addAttr(cog_ctrl, ln='showScaleCtrl', at='bool', keyable=True)

    # Cog In-Between Offset
    cog_offset_ctrl = \
        cmds.duplicate(cog_ctrl, name=cog_ctrl.replace('_' + CTRL_SUFFIX, '_offset' + CTRL_SUFFIX.capitalize()))[0]
    cmds.deleteAttr(cog_offset_ctrl, at='showScaleCtrl')
    cmds.setAttr(cog_offset_ctrl + '.scaleX', .9)
    cmds.setAttr(cog_offset_ctrl + '.scaleY', .9)
    cmds.setAttr(cog_offset_ctrl + '.scaleZ', .9)
    cmds.makeIdentity(cog_offset_ctrl, apply=True, scale=True)
    change_viewport_color(cog_offset_ctrl, (.4, .4, 0))
    lock_hide_default_attr(cog_offset_ctrl, translate=False, rotate=False, visibility=False)
    cmds.setAttr(cog_offset_ctrl + '.v', k=False, channelBox=False)
    setup_shape_switch(cog_offset_ctrl, attr='controlShape', shape_names=['circle', 'pin'],
                       shape_enum=['Circle', 'Pin'])

    # Recreate Connections
    cmds.connectAttr(cog_offset_ctrl + '.rotationOrder', cog_offset_ctrl + '.rotateOrder', f=True)

    cog_offset_ctrl_grp = cmds.group(name=cog_offset_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cog_offset_data_grp = cmds.group(
        name=cog_offset_ctrl.replace(CTRL_SUFFIX.capitalize(), 'Data') + GRP_SUFFIX.capitalize(), empty=True,
        world=True)
    cmds.connectAttr(cog_offset_ctrl + '.rotationOrder', cog_offset_data_grp + '.rotateOrder', f=True)
    cmds.parent(cog_offset_data_grp, cog_offset_ctrl_grp)
    cmds.delete(cmds.parentConstraint(cog_offset_ctrl, cog_offset_ctrl_grp))

    cmds.parent(cog_offset_ctrl, cog_offset_ctrl_grp)
    cmds.parent(cog_offset_ctrl_grp, cog_ctrl)

    cmds.connectAttr(cog_offset_ctrl + '.translate', cog_offset_data_grp + '.translate', f=True)
    cmds.connectAttr(cog_offset_ctrl + '.rotate', cog_offset_data_grp + '.rotate', f=True)

    cmds.addAttr(cog_ctrl, ln='showOffsetCtrl', at='bool', k=True)
    cmds.connectAttr(cog_ctrl + '.showOffsetCtrl', cog_offset_ctrl + '.v', f=True)

    # #### End Cog In-Between Offset

    # Hip Control
    hip_ctrl_a = cmds.curve(name=rig_joints.get('hip_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                            p=[[-0.159, 0.671, -0.185], [-0.185, 0.674, -0.001], [-0.159, 0.65, 0.185],
                               [-0.05, 0.592, 0.366], [0.037, 0.515, 0.493], [0.12, 0.406, 0.632],
                               [-0.062, -0.0, 0.818], [0.12, -0.406, 0.632], [0.037, -0.515, 0.493],
                               [-0.05, -0.592, 0.366], [-0.159, -0.65, 0.185], [-0.183, -0.671, -0.001],
                               [-0.159, -0.65, -0.185], [-0.05, -0.592, -0.366], [0.037, -0.515, -0.493],
                               [0.12, -0.406, -0.632], [-0.062, 0.0, -0.818], [0.12, 0.406, -0.632],
                               [0.037, 0.515, -0.493], [-0.05, 0.606, -0.366], [-0.159, 0.671, -0.185],
                               [-0.185, 0.674, -0.001], [-0.159, 0.65, 0.185]], d=3, per=True,
                            k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0,
                               14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0])
    hip_ctrl_b = cmds.curve(
        p=[[0.0, 0.0, 0.0], [0.0, -0.754, 0.0], [0.03, -0.761, 0.0], [0.054, -0.769, 0.0], [0.077, -0.787, 0.0],
           [0.095, -0.808, 0.0], [0.104, -0.834, 0.0], [0.109, -0.864, 0.0], [0.0, -0.864, 0.0], [0.0, -0.754, 0.0],
           [-0.03, -0.761, 0.0], [-0.054, -0.769, 0.0], [-0.077, -0.787, 0.0], [-0.095, -0.811, 0.0],
           [-0.104, -0.834, 0.0], [-0.109, -0.864, 0.0], [-0.104, -0.891, 0.0], [-0.095, -0.917, 0.0],
           [-0.077, -0.941, 0.0], [-0.054, -0.955, 0.0], [-0.03, -0.967, 0.0], [0.0, -0.971, 0.0], [0.026, -0.967, 0.0],
           [0.054, -0.955, 0.0], [0.077, -0.941, 0.0], [0.092, -0.917, 0.0], [0.104, -0.891, 0.0], [0.109, -0.864, 0.0],
           [-0.109, -0.864, 0.0], [0.0, -0.864, 0.0], [0.0, -0.971, 0.0]], d=1)

    add_orient_offset(hip_ctrl_a, (90, 0, 90), apply=settings.get('uniform_ctrl_orient'))
    add_orient_offset(hip_ctrl_b, (90, 0, 90), apply=settings.get('uniform_ctrl_orient'))

    hip_ctrl = combine_curves_list([hip_ctrl_a, hip_ctrl_b])

    shapes = cmds.listRelatives(hip_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format(hip_ctrl.replace(CTRL_SUFFIX, 'default')))
    cmds.rename(shapes[1], '{0}Shape'.format(hip_ctrl.replace(CTRL_SUFFIX, 'pin')))

    cmds.setAttr(hip_ctrl + '.scaleX', general_scale_offset)
    cmds.setAttr(hip_ctrl + '.scaleY', general_scale_offset)
    cmds.setAttr(hip_ctrl + '.scaleZ', general_scale_offset)
    cmds.makeIdentity(hip_ctrl, apply=True, scale=True)

    change_viewport_color(hip_ctrl, (.8, .8, 0))
    hip_ctrl_grp = cmds.group(name=hip_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(hip_ctrl, hip_ctrl_grp)
    cmds.delete(cmds.parentConstraint(rig_joints.get('hip_jnt'), hip_ctrl_grp))
    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(-90, -90, 0, hip_ctrl_grp, os=True, relative=True)

    cmds.parent(hip_ctrl_grp, cog_offset_data_grp)

    # Add Separator
    cmds.addAttr(hip_ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
    cmds.setAttr(hip_ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)

    # Expose Custom Rotate Order
    cmds.addAttr(hip_ctrl, ln='rotationOrder', at='enum', en=ROTATE_ORDER_ENUM, keyable=True, niceName='Rotate Order')
    cmds.connectAttr(hip_ctrl + '.rotationOrder', hip_ctrl + '.rotateOrder', f=True)

    # Setup Shape Switch
    setup_shape_switch(hip_ctrl, attr='controlShape', shape_names=['default', 'pin'], shape_enum=['Default', 'Pin'])

    # Show Scale Ctrl
    cmds.addAttr(hip_ctrl, ln='showScaleCtrl', at='bool', keyable=True)

    # Hip In-Between Offset
    hip_offset_ctrl = \
        cmds.duplicate(hip_ctrl, name=hip_ctrl.replace('_' + CTRL_SUFFIX, '_offset' + CTRL_SUFFIX.capitalize()))[0]
    cmds.deleteAttr(hip_offset_ctrl, at='showScaleCtrl')
    cmds.setAttr(hip_offset_ctrl + '.scaleX', .9)
    cmds.setAttr(hip_offset_ctrl + '.scaleY', .9)
    cmds.setAttr(hip_offset_ctrl + '.scaleZ', .9)
    cmds.makeIdentity(hip_offset_ctrl, apply=True, scale=True)
    change_viewport_color(hip_offset_ctrl, (.4, .4, 0))
    lock_hide_default_attr(hip_offset_ctrl, translate=False, rotate=False, visibility=False)
    cmds.setAttr(hip_offset_ctrl + '.v', k=False, channelBox=False)

    # Recreate Connections
    cmds.connectAttr(hip_offset_ctrl + '.rotationOrder', hip_offset_ctrl + '.rotateOrder', f=True)

    setup_shape_switch(hip_offset_ctrl, attr='controlShape', shape_names=['default', 'pin'],
                       shape_enum=['Default', 'Pin'])

    hip_offset_ctrl_grp = cmds.group(name=hip_offset_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    hip_offset_data_grp = cmds.group(
        name=hip_offset_ctrl.replace(CTRL_SUFFIX.capitalize(), 'Data') + GRP_SUFFIX.capitalize(), empty=True,
        world=True)
    cmds.connectAttr(hip_offset_ctrl + '.rotationOrder', hip_offset_data_grp + '.rotateOrder', f=True)
    cmds.parent(hip_offset_data_grp, hip_offset_ctrl_grp)
    cmds.delete(cmds.parentConstraint(hip_offset_ctrl, hip_offset_ctrl_grp))

    cmds.parent(hip_offset_ctrl, hip_offset_ctrl_grp)
    cmds.parent(hip_offset_ctrl_grp, hip_ctrl)

    cmds.connectAttr(hip_offset_ctrl + '.translate', hip_offset_data_grp + '.translate', f=True)
    cmds.connectAttr(hip_offset_ctrl + '.rotate', hip_offset_data_grp + '.rotate', f=True)

    cmds.addAttr(hip_ctrl, ln='showOffsetCtrl', at='bool', k=True)
    cmds.connectAttr(hip_ctrl + '.showOffsetCtrl', hip_offset_ctrl + '.v', f=True)
    # #### End Chest In-Between Offset

    # Spine01 Control
    spine01_ctrl_a = cmds.curve(name=rig_joints.get('spine01_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                p=[[-0.087, 0.604, 0.768], [0.087, 0.604, 0.768], [0.087, 0.604, -0.768],
                                   [-0.087, 0.604, -0.768], [-0.087, 0.604, 0.768], [-0.087, -0.604, 0.768],
                                   [-0.087, -0.604, -0.768], [0.087, -0.604, -0.768], [0.087, -0.604, 0.768],
                                   [-0.087, -0.604, 0.768], [0.087, -0.604, 0.768], [0.087, 0.604, 0.768],
                                   [0.087, 0.604, -0.768], [0.087, -0.604, -0.768], [-0.087, -0.604, -0.768],
                                   [-0.087, 0.604, -0.768]], d=1)
    spine01_ctrl_b = cmds.curve(name=rig_joints.get('spine01_jnt').replace(JNT_SUFFIX, '') + 'flat',
                                p=[[0.121, -0.836, -0.299], [0.0, -0.836, -0.299], [-0.121, -0.836, -0.299],
                                   [-0.061, -0.895, -0.126], [-0.061, -0.912, -0.002], [-0.061, -0.894, 0.13],
                                   [-0.121, -0.836, 0.299], [0.0, -0.836, 0.299], [0.121, -0.836, 0.299],
                                   [0.061, -0.894, 0.13], [0.061, -0.912, -0.002], [0.061, -0.895, -0.126],
                                   [0.121, -0.836, -0.299], [0.0, -0.836, -0.299], [-0.121, -0.836, -0.299]], d=3,
                                per=True,
                                k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0,
                                   14.0])
    spine01_ctrl_c = cmds.curve(name=rig_joints.get('spine01_jnt').replace(JNT_SUFFIX, '') + 'pin',
                                p=[[0.0, 0.0, 0.0], [0.0, -1.003, 0.0], [0.037, -1.007, 0.0], [0.072, -1.022, 0.0],
                                   [0.101, -1.046, 0.0], [0.124, -1.075, 0.0], [0.138, -1.109, 0.0],
                                   [0.143, -1.146, 0.0], [0.0, -1.146, 0.0], [0.0, -1.003, 0.0],
                                   [-0.037, -1.007, 0.0], [-0.072, -1.022, 0.0], [-0.101, -1.046, 0.0],
                                   [-0.124, -1.075, 0.0], [-0.138, -1.109, 0.0], [-0.144, -1.146, 0.0],
                                   [-0.138, -1.184, 0.0], [-0.124, -1.218, 0.0], [-0.101, -1.247, 0.0],
                                   [-0.072, -1.271, 0.0], [-0.037, -1.284, 0.0], [0.0, -1.29, 0.0],
                                   [0.037, -1.284, 0.0], [0.072, -1.271, 0.0], [0.101, -1.248, 0.0],
                                   [0.123, -1.218, 0.0], [0.138, -1.184, 0.0], [0.143, -1.146, 0.0],
                                   [-0.144, -1.146, 0.0], [0.0, -1.146, 0.0], [0.0, -1.29, 0.0]], d=1)

    add_orient_offset(spine01_ctrl_a, (90, 0, -90), apply=settings.get('uniform_ctrl_orient'))
    add_orient_offset(spine01_ctrl_b, (90, 0, -90), apply=settings.get('uniform_ctrl_orient'))
    add_orient_offset(spine01_ctrl_c, (90, 0, -90), apply=settings.get('uniform_ctrl_orient'))

    spine01_ctrl = combine_curves_list([spine01_ctrl_a, spine01_ctrl_b, spine01_ctrl_c])

    cmds.setAttr(spine01_ctrl + '.scaleX', general_scale_offset)
    cmds.setAttr(spine01_ctrl + '.scaleY', general_scale_offset)
    cmds.setAttr(spine01_ctrl + '.scaleZ', general_scale_offset)
    cmds.makeIdentity(spine01_ctrl, apply=True, scale=True)

    shapes = cmds.listRelatives(spine01_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format(spine01_ctrl.replace(CTRL_SUFFIX, 'box')))
    cmds.rename(shapes[1], '{0}Shape'.format(spine01_ctrl.replace(CTRL_SUFFIX, 'flat')))
    cmds.rename(shapes[2], '{0}Shape'.format(spine01_ctrl.replace(CTRL_SUFFIX, 'pin')))

    change_viewport_color(spine01_ctrl, AUTO_CTRL_COLOR)
    spine01_ctrl_grp = cmds.group(name=spine01_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(spine01_ctrl, spine01_ctrl_grp)
    cmds.delete(cmds.parentConstraint(rig_joints.get('spine01_jnt'), spine01_ctrl_grp))
    cmds.parent(spine01_ctrl_grp, cog_offset_data_grp)

    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(-90, -90, 0, spine01_ctrl_grp, os=True, relative=True)

    # Spine02 Control
    spine02_ctrl_a = cmds.curve(name=rig_joints.get('spine02_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                p=[[-0.087, 0.604, 0.768], [0.087, 0.604, 0.768], [0.087, 0.604, -0.768],
                                   [-0.087, 0.604, -0.768], [-0.087, 0.604, 0.768], [-0.087, -0.604, 0.768],
                                   [-0.087, -0.604, -0.768], [0.087, -0.604, -0.768], [0.087, -0.604, 0.768],
                                   [-0.087, -0.604, 0.768], [0.087, -0.604, 0.768], [0.087, 0.604, 0.768],
                                   [0.087, 0.604, -0.768], [0.087, -0.604, -0.768], [-0.087, -0.604, -0.768],
                                   [-0.087, 0.604, -0.768]], d=1)
    spine02_ctrl_b = cmds.curve(name=rig_joints.get('spine02_jnt').replace(JNT_SUFFIX, '') + 'flat',
                                p=[[0.121, -0.836, -0.299], [0.0, -0.836, -0.299], [-0.121, -0.836, -0.299],
                                   [-0.061, -0.895, -0.126], [-0.061, -0.912, -0.002], [-0.061, -0.894, 0.13],
                                   [-0.121, -0.836, 0.299], [0.0, -0.836, 0.299], [0.121, -0.836, 0.299],
                                   [0.061, -0.894, 0.13], [0.061, -0.912, -0.002], [0.061, -0.895, -0.126],
                                   [0.121, -0.836, -0.299], [0.0, -0.836, -0.299], [-0.121, -0.836, -0.299]], d=3,
                                per=True,
                                k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0,
                                   14.0])
    spine02_ctrl_c = cmds.curve(name=rig_joints.get('spine02_jnt').replace(JNT_SUFFIX, '') + 'pin',
                                p=[[0.0, 0.0, 0.0], [0.0, -1.315, 0.0], [0.049, -1.321, 0.0], [0.095, -1.34, 0.0],
                                   [0.132, -1.371, 0.0], [0.162, -1.409, 0.0], [0.181, -1.454, 0.0],
                                   [0.187, -1.503, 0.0], [0.0, -1.503, 0.0], [0.0, -1.315, 0.0],
                                   [-0.049, -1.321, 0.0], [-0.095, -1.34, 0.0], [-0.132, -1.371, 0.0],
                                   [-0.162, -1.41, 0.0], [-0.181, -1.454, 0.0], [-0.189, -1.503, 0.0],
                                   [-0.181, -1.552, 0.0], [-0.162, -1.597, 0.0], [-0.132, -1.635, 0.0],
                                   [-0.095, -1.666, 0.0], [-0.049, -1.684, 0.0], [0.0, -1.691, 0.0],
                                   [0.048, -1.684, 0.0], [0.095, -1.666, 0.0], [0.132, -1.636, 0.0],
                                   [0.161, -1.597, 0.0], [0.181, -1.552, 0.0], [0.187, -1.503, 0.0],
                                   [-0.189, -1.503, 0.0], [0.0, -1.503, 0.0], [0.0, -1.691, 0.0]], d=1)

    add_orient_offset(spine02_ctrl_a, (90, 0, -90), apply=settings.get('uniform_ctrl_orient'))
    add_orient_offset(spine02_ctrl_b, (90, 0, -90), apply=settings.get('uniform_ctrl_orient'))
    add_orient_offset(spine02_ctrl_c, (90, 0, -90), apply=settings.get('uniform_ctrl_orient'))

    spine02_ctrl = combine_curves_list([spine02_ctrl_a, spine02_ctrl_b, spine02_ctrl_c])

    cmds.setAttr(spine02_ctrl + '.scaleX', general_scale_offset)
    cmds.setAttr(spine02_ctrl + '.scaleY', general_scale_offset)
    cmds.setAttr(spine02_ctrl + '.scaleZ', general_scale_offset)
    cmds.makeIdentity(spine02_ctrl, apply=True, scale=True)

    shapes = cmds.listRelatives(spine02_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format(spine02_ctrl.replace(CTRL_SUFFIX, 'box')))
    cmds.rename(shapes[1], '{0}Shape'.format(spine02_ctrl.replace(CTRL_SUFFIX, 'flat')))
    cmds.rename(shapes[2], '{0}Shape'.format(spine02_ctrl.replace(CTRL_SUFFIX, 'pin')))

    change_viewport_color(spine02_ctrl, (.8, .8, 0))
    spine02_ctrl_grp = cmds.group(name=spine02_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(spine02_ctrl, spine02_ctrl_grp)
    cmds.delete(cmds.parentConstraint(rig_joints.get('spine02_jnt'), spine02_ctrl_grp))
    cmds.parent(spine02_ctrl_grp, spine01_ctrl)

    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(-90, -90, 0, spine02_ctrl_grp, os=True, relative=True)

    # Spine03 Control
    spine03_ctrl_a = cmds.curve(name=rig_joints.get('spine03_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                p=[[-0.087, 0.604, 0.768], [0.087, 0.604, 0.768], [0.087, 0.604, -0.768],
                                   [-0.087, 0.604, -0.768], [-0.087, 0.604, 0.768], [-0.087, -0.604, 0.768],
                                   [-0.087, -0.604, -0.768], [0.087, -0.604, -0.768], [0.087, -0.604, 0.768],
                                   [-0.087, -0.604, 0.768], [0.087, -0.604, 0.768], [0.087, 0.604, 0.768],
                                   [0.087, 0.604, -0.768], [0.087, -0.604, -0.768], [-0.087, -0.604, -0.768],
                                   [-0.087, 0.604, -0.768]], d=1)
    spine03_ctrl_b = cmds.curve(name=rig_joints.get('spine03_jnt').replace(JNT_SUFFIX, '') + 'flat',
                                p=[[0.121, -0.836, -0.299], [0.0, -0.836, -0.299], [-0.121, -0.836, -0.299],
                                   [-0.061, -0.895, -0.126], [-0.061, -0.912, -0.002], [-0.061, -0.894, 0.13],
                                   [-0.121, -0.836, 0.299], [0.0, -0.836, 0.299], [0.121, -0.836, 0.299],
                                   [0.061, -0.894, 0.13], [0.061, -0.912, -0.002], [0.061, -0.895, -0.126],
                                   [0.121, -0.836, -0.299], [0.0, -0.836, -0.299], [-0.121, -0.836, -0.299]], d=3,
                                per=True,
                                k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0,
                                   14.0])
    spine03_ctrl_c = cmds.curve(name=rig_joints.get('spine03_jnt').replace(JNT_SUFFIX, '') + 'pin',
                                p=[[0.0, 0.0, 0.0], [0.0, -1.003, 0.0], [0.037, -1.007, 0.0], [0.072, -1.022, 0.0],
                                   [0.101, -1.046, 0.0], [0.124, -1.075, 0.0], [0.138, -1.109, 0.0],
                                   [0.143, -1.146, 0.0], [0.0, -1.146, 0.0], [0.0, -1.003, 0.0], [-0.037, -1.007, 0.0],
                                   [-0.072, -1.022, 0.0], [-0.101, -1.046, 0.0], [-0.124, -1.075, 0.0],
                                   [-0.138, -1.109, 0.0], [-0.144, -1.146, 0.0], [-0.138, -1.184, 0.0],
                                   [-0.124, -1.218, 0.0], [-0.101, -1.247, 0.0], [-0.072, -1.271, 0.0],
                                   [-0.037, -1.284, 0.0], [0.0, -1.29, 0.0], [0.037, -1.284, 0.0],
                                   [0.072, -1.271, 0.0], [0.101, -1.248, 0.0], [0.123, -1.218, 0.0],
                                   [0.138, -1.184, 0.0], [0.143, -1.146, 0.0], [-0.144, -1.146, 0.0],
                                   [0.0, -1.146, 0.0], [0.0, -1.29, 0.0]], d=1)

    add_orient_offset(spine03_ctrl_a, (90, 0, -90), apply=settings.get('uniform_ctrl_orient'))
    add_orient_offset(spine03_ctrl_b, (90, 0, -90), apply=settings.get('uniform_ctrl_orient'))
    add_orient_offset(spine03_ctrl_c, (90, 0, -90), apply=settings.get('uniform_ctrl_orient'))

    spine03_ctrl = combine_curves_list([spine03_ctrl_a, spine03_ctrl_b, spine03_ctrl_c])

    cmds.setAttr(spine03_ctrl + '.scaleX', general_scale_offset)
    cmds.setAttr(spine03_ctrl + '.scaleY', general_scale_offset)
    cmds.setAttr(spine03_ctrl + '.scaleZ', general_scale_offset)
    cmds.makeIdentity(spine03_ctrl, apply=True, scale=True)
    shapes = cmds.listRelatives(spine03_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format(spine03_ctrl.replace(CTRL_SUFFIX, 'box')))
    cmds.rename(shapes[1], '{0}Shape'.format(spine03_ctrl.replace(CTRL_SUFFIX, 'flat')))
    cmds.rename(shapes[2], '{0}Shape'.format(spine03_ctrl.replace(CTRL_SUFFIX, 'pin')))

    change_viewport_color(spine03_ctrl, AUTO_CTRL_COLOR)
    spine03_ctrl_grp = cmds.group(name=spine03_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(spine03_ctrl, spine03_ctrl_grp)
    cmds.delete(cmds.parentConstraint(rig_joints.get('spine03_jnt'), spine03_ctrl_grp))
    cmds.parent(spine03_ctrl_grp, spine02_ctrl)

    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(-90, -90, 0, spine03_ctrl_grp, os=True, relative=True)

    # Spine04 Control
    spine04_ctrl_a = cmds.curve(name=rig_joints.get('spine04_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                p=[[-0.087, 0.604, 0.768], [0.087, 0.604, 0.768], [0.087, 0.604, -0.768],
                                   [-0.087, 0.604, -0.768], [-0.087, 0.604, 0.768], [-0.087, -0.604, 0.768],
                                   [-0.087, -0.604, -0.768], [0.087, -0.604, -0.768], [0.087, -0.604, 0.768],
                                   [-0.087, -0.604, 0.768], [0.087, -0.604, 0.768], [0.087, 0.604, 0.768],
                                   [0.087, 0.604, -0.768], [0.087, -0.604, -0.768], [-0.087, -0.604, -0.768],
                                   [-0.087, 0.604, -0.768]], d=1)
    spine04_ctrl_b = cmds.curve(name=rig_joints.get('spine04_jnt').replace(JNT_SUFFIX, '') + 'flat',
                                p=[[0.121, -0.836, -0.299], [0.0, -0.836, -0.299], [-0.121, -0.836, -0.299],
                                   [-0.061, -0.895, -0.126], [-0.061, -0.912, -0.002], [-0.061, -0.894, 0.13],
                                   [-0.121, -0.836, 0.299], [0.0, -0.836, 0.299], [0.121, -0.836, 0.299],
                                   [0.061, -0.894, 0.13], [0.061, -0.912, -0.002], [0.061, -0.895, -0.126],
                                   [0.121, -0.836, -0.299], [0.0, -0.836, -0.299], [-0.121, -0.836, -0.299]], d=3,
                                per=True,
                                k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0,
                                   14.0])
    spine04_ctrl_c = cmds.curve(name=rig_joints.get('spine04_jnt').replace(JNT_SUFFIX, '') + 'pin',
                                p=[[0.0, 0.0, 0.0], [0.0, -1.315, 0.0], [0.049, -1.321, 0.0], [0.095, -1.34, 0.0],
                                   [0.132, -1.371, 0.0], [0.162, -1.409, 0.0], [0.181, -1.454, 0.0],
                                   [0.187, -1.503, 0.0], [0.0, -1.503, 0.0], [0.0, -1.315, 0.0],
                                   [-0.049, -1.321, 0.0], [-0.095, -1.34, 0.0], [-0.132, -1.371, 0.0],
                                   [-0.162, -1.41, 0.0], [-0.181, -1.454, 0.0], [-0.189, -1.503, 0.0],
                                   [-0.181, -1.552, 0.0], [-0.162, -1.597, 0.0], [-0.132, -1.635, 0.0],
                                   [-0.095, -1.666, 0.0], [-0.049, -1.684, 0.0], [0.0, -1.691, 0.0],
                                   [0.048, -1.684, 0.0], [0.095, -1.666, 0.0], [0.132, -1.636, 0.0],
                                   [0.161, -1.597, 0.0], [0.181, -1.552, 0.0], [0.187, -1.503, 0.0],
                                   [-0.189, -1.503, 0.0], [0.0, -1.503, 0.0], [0.0, -1.691, 0.0]], d=1)

    add_orient_offset(spine04_ctrl_a, (90, 0, -90), apply=settings.get('uniform_ctrl_orient'))
    add_orient_offset(spine04_ctrl_b, (90, 0, -90), apply=settings.get('uniform_ctrl_orient'))
    add_orient_offset(spine04_ctrl_c, (90, 0, -90), apply=settings.get('uniform_ctrl_orient'))

    spine04_ctrl = combine_curves_list([spine04_ctrl_a, spine04_ctrl_b, spine04_ctrl_c])

    cmds.setAttr(spine04_ctrl + '.scaleX', general_scale_offset)
    cmds.setAttr(spine04_ctrl + '.scaleY', general_scale_offset)
    cmds.setAttr(spine04_ctrl + '.scaleZ', general_scale_offset)
    cmds.makeIdentity(spine04_ctrl, apply=True, scale=True)
    shapes = cmds.listRelatives(spine04_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format(spine04_ctrl.replace(CTRL_SUFFIX, 'box')))
    cmds.rename(shapes[1], '{0}Shape'.format(spine04_ctrl.replace(CTRL_SUFFIX, 'flat')))
    cmds.rename(shapes[2], '{0}Shape'.format(spine04_ctrl.replace(CTRL_SUFFIX, 'pin')))
    change_viewport_color(spine04_ctrl, (.8, .8, 0))
    spine04_ctrl_grp = cmds.group(name=spine04_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(spine04_ctrl, spine04_ctrl_grp)
    cmds.delete(cmds.parentConstraint(rig_joints.get('spine04_jnt'), spine04_ctrl_grp))
    cmds.parent(spine04_ctrl_grp, spine03_ctrl)

    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(-90, -90, 0, spine04_ctrl_grp, os=True, relative=True)

    # Neck Base Control
    neck_base_ctrl = cmds.curve(name=rig_joints.get('neck_base_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                p=[[0.0, 0.0, 0.0], [0.0, -1.794, 0.0], [0.067, -1.803, 0.0], [0.128, -1.829, 0.0],
                                   [0.181, -1.869, 0.0], [0.222, -1.922, 0.0], [0.247, -1.984, 0.0],
                                   [0.256, -2.05, 0.0], [0.0, -2.051, 0.0], [0.0, -1.794, 0.0], [-0.067, -1.803, 0.0],
                                   [-0.129, -1.829, 0.0], [-0.181, -1.869, 0.0], [-0.222, -1.923, 0.0],
                                   [-0.247, -1.984, 0.0], [-0.257, -2.05, 0.0], [-0.248, -2.117, 0.0],
                                   [-0.222, -2.178, 0.0], [-0.181, -2.231, 0.0], [-0.128, -2.272, 0.0],
                                   [-0.067, -2.297, 0.0], [0.0, -2.307, 0.0], [0.066, -2.298, 0.0],
                                   [0.128, -2.272, 0.0], [0.181, -2.232, 0.0], [0.221, -2.179, 0.0],
                                   [0.247, -2.116, 0.0], [0.256, -2.05, 0.0], [-0.257, -2.05, 0.0], [0.0, -2.051, 0.0],
                                   [0.0, -2.307, 0.0]], d=1)

    add_orient_offset(neck_base_ctrl, (90, 0, -90), apply=settings.get('uniform_ctrl_orient'))

    cmds.setAttr(neck_base_ctrl + '.scaleX', general_scale_offset * .5)
    cmds.setAttr(neck_base_ctrl + '.scaleY', general_scale_offset * .5)
    cmds.setAttr(neck_base_ctrl + '.scaleZ', general_scale_offset * .5)
    cmds.makeIdentity(neck_base_ctrl, apply=True, scale=True)

    for shape in cmds.listRelatives(neck_base_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(neck_base_ctrl))
    change_viewport_color(neck_base_ctrl, (.8, .8, 0))
    neck_base_ctrl_grp = cmds.group(name=neck_base_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(neck_base_ctrl, neck_base_ctrl_grp)
    cmds.delete(cmds.parentConstraint(rig_joints.get('neck_base_jnt'), neck_base_ctrl_grp))

    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(-90, -90, 0, neck_base_ctrl_grp, os=True, relative=True)

    # Neck-Mid Control
    neck_mid_ctrl = cmds.curve(name=rig_joints.get('neck_mid_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                               p=[[0.0, 0.0, 0.0], [0.0, -1.794, 0.0], [0.067, -1.803, 0.0], [0.128, -1.829, 0.0],
                                  [0.181, -1.869, 0.0], [0.222, -1.922, 0.0], [0.247, -1.984, 0.0], [0.256, -2.05, 0.0],
                                  [0.0, -2.051, 0.0], [0.0, -1.794, 0.0], [-0.067, -1.803, 0.0], [-0.129, -1.829, 0.0],
                                  [-0.181, -1.869, 0.0], [-0.222, -1.923, 0.0], [-0.247, -1.984, 0.0],
                                  [-0.257, -2.05, 0.0], [-0.248, -2.117, 0.0], [-0.222, -2.178, 0.0],
                                  [-0.181, -2.231, 0.0], [-0.128, -2.272, 0.0], [-0.067, -2.297, 0.0],
                                  [0.0, -2.307, 0.0], [0.066, -2.298, 0.0], [0.128, -2.272, 0.0], [0.181, -2.232, 0.0],
                                  [0.221, -2.179, 0.0], [0.247, -2.116, 0.0], [0.256, -2.05, 0.0], [-0.257, -2.05, 0.0],
                                  [0.0, -2.051, 0.0], [0.0, -2.307, 0.0]], d=1)

    add_orient_offset(neck_mid_ctrl, (90, 0, -90), apply=settings.get('uniform_ctrl_orient'))

    cmds.setAttr(neck_mid_ctrl + '.scaleX', general_scale_offset * .3)
    cmds.setAttr(neck_mid_ctrl + '.scaleY', general_scale_offset * .3)
    cmds.setAttr(neck_mid_ctrl + '.scaleZ', general_scale_offset * .3)
    cmds.makeIdentity(neck_mid_ctrl, apply=True, scale=True)
    for shape in cmds.listRelatives(neck_mid_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(neck_mid_ctrl))
    change_viewport_color(neck_mid_ctrl, AUTO_CTRL_COLOR)
    neck_mid_ctrl_grp = cmds.group(name=neck_mid_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(neck_mid_ctrl, neck_mid_ctrl_grp)
    cmds.parent(neck_mid_ctrl_grp, neck_base_ctrl)

    cmds.delete(cmds.parentConstraint(rig_joints.get('neck_mid_jnt'), neck_mid_ctrl_grp))

    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(-90, -90, 0, neck_mid_ctrl_grp, os=True, relative=True)

    # Head Control
    head_ctrl = cmds.curve(name=rig_joints.get('head_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                           p=[[0.0, 0.529, -0.529], [0.0, 0.0, -0.748], [0.0, -0.529, -0.529], [0.0, -0.748, 0.0],
                              [0.0, -0.529, 0.529], [0.0, 0.0, 0.748], [0.0, 0.529, 0.529], [0.0, 0.748, 0.0],
                              [0.0, 0.529, -0.529], [0.0, 0.0, -0.748], [0.0, -0.529, -0.529]], d=3, per=True,
                           k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    add_orient_offset(head_ctrl, (90, 0, 0), apply=settings.get('uniform_ctrl_orient'))
    cmds.setAttr(head_ctrl + '.scaleX', general_scale_offset)
    cmds.setAttr(head_ctrl + '.scaleY', general_scale_offset)
    cmds.setAttr(head_ctrl + '.scaleZ', general_scale_offset)
    cmds.makeIdentity(head_ctrl, apply=True, scale=True)
    for shape in cmds.listRelatives(head_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(head_ctrl))
    change_viewport_color(head_ctrl, (.8, .8, 0))
    head_ctrl_grp = cmds.group(name=head_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(head_ctrl, head_ctrl_grp)
    cmds.parent(head_ctrl_grp, neck_mid_ctrl)
    cmds.delete(cmds.parentConstraint(rig_joints.get('head_jnt'), head_ctrl_grp))

    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(-90, -90, 0, head_ctrl_grp, os=True, relative=True)

    desired_pivot = cmds.xform(head_ctrl, q=True, ws=True, t=True)
    cmds.delete(cmds.parentConstraint(rig_joints.get('head_end_jnt'), head_ctrl))
    cmds.xform(head_ctrl, piv=desired_pivot, ws=True)
    cmds.makeIdentity(head_ctrl, apply=True, scale=True, rotate=True, translate=True)

    # Create Separator
    cmds.addAttr(head_ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
    cmds.setAttr(head_ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)

    # Expose Custom Rotate Order
    cmds.addAttr(head_ctrl, ln='rotationOrder', at='enum', en=ROTATE_ORDER_ENUM, keyable=True, niceName='Rotate Order')
    cmds.connectAttr(head_ctrl + '.rotationOrder', head_ctrl + '.rotateOrder', f=True)

    # Head In-Between Offset
    head_offset_ctrl_a = cmds.curve(name=head_ctrl.replace('_' + CTRL_SUFFIX, '_offset' + CTRL_SUFFIX.capitalize()),
                                    p=[[0.0, 0.529, -0.529], [0.0, 0.0, -0.748], [0.0, -0.529, -0.529],
                                       [0.0, -0.748, 0.0], [0.0, -0.529, 0.529], [0.0, 0.0, 0.748], [0.0, 0.529, 0.529],
                                       [0.0, 0.748, 0.0], [0.0, 0.529, -0.529], [0.0, 0.0, -0.748],
                                       [0.0, -0.529, -0.529]], d=3, per=True,
                                    k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    head_offset_ctrl_b = cmds.curve(
        p=[[-6.0, 0.0, 0.0], [0.0, -0.003, 0.0], [0.0, -18.225, 0.0], [0.681, -18.317, 0.0], [1.301, -18.581, 0.0],
           [1.838, -18.988, 0.0], [2.254, -19.526, 0.0], [2.509, -20.155, 0.0], [2.6, -20.825, 0.0],
           [0.0, -20.835, 0.0], [0.0, -18.225, 0.0], [-0.681, -18.317, 0.0], [-1.311, -18.581, 0.0],
           [-1.838, -18.988, 0.0], [-2.254, -19.536, 0.0], [-2.509, -20.155, 0.0], [-2.61, -20.825, 0.0],
           [-2.519, -21.507, 0.0], [-2.254, -22.126, 0.0], [-1.838, -22.665, 0.0], [-1.301, -23.082, 0.0],
           [-0.681, -23.336, 0.0], [0.0, -23.437, 0.0], [0.67, -23.346, 0.0], [1.301, -23.082, 0.0],
           [1.838, -22.675, 0.0], [2.244, -22.136, 0.0], [2.509, -21.496, 0.0], [2.6, -20.825, 0.0],
           [-2.61, -20.825, 0.0], [0.0, -20.835, 0.0], [0.0, -23.437, 0.0]], d=1)
    cmds.setAttr(head_offset_ctrl_b + '.scaleX', .06)
    cmds.setAttr(head_offset_ctrl_b + '.scaleY', .06)
    cmds.setAttr(head_offset_ctrl_b + '.scaleZ', .06)
    head_offset_ctrl = combine_curves_list([head_offset_ctrl_a, head_offset_ctrl_b])

    shapes = cmds.listRelatives(head_offset_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format(head_offset_ctrl.replace('offset' + CTRL_SUFFIX.capitalize(), 'circle')))
    pin_shape = cmds.rename(shapes[1],
                            '{0}Shape'.format(head_offset_ctrl.replace('offset' + CTRL_SUFFIX.capitalize(), 'pin')))

    # Add Separator
    cmds.addAttr(head_offset_ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
    cmds.setAttr(head_offset_ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)

    # Setup Shape Switch
    setup_shape_switch(head_offset_ctrl, attr='controlShape', shape_names=['circle', 'pin'],
                       shape_enum=['Circle', 'Pin'])

    cmds.setAttr(head_offset_ctrl + '.scaleX', general_scale_offset * .83)
    cmds.setAttr(head_offset_ctrl + '.scaleY', general_scale_offset * .83)
    cmds.setAttr(head_offset_ctrl + '.scaleZ', general_scale_offset * .83)
    cmds.makeIdentity(head_offset_ctrl, apply=True, scale=True)

    change_viewport_color(head_offset_ctrl, (.4, .4, 0))
    cmds.delete(cmds.parentConstraint(head_ctrl, head_offset_ctrl))
    cmds.parent(head_offset_ctrl, head_ctrl)
    desired_pivot = cmds.xform(head_offset_ctrl, q=True, ws=True, t=True)
    cmds.delete(cmds.parentConstraint(rig_joints.get('head_end_jnt'), head_offset_ctrl))
    cmds.xform(head_offset_ctrl, piv=desired_pivot, ws=True)
    cmds.makeIdentity(head_offset_ctrl, apply=True, scale=True, rotate=True, translate=True)

    head_jnt_pos = cmds.xform(rig_joints.get('head_jnt'), q=True, t=True, ws=True)
    cmds.xform(pin_shape + '.cv[0]', t=head_jnt_pos, ws=True)

    lock_hide_default_attr(head_offset_ctrl, translate=False, rotate=False, visibility=False)
    cmds.setAttr(head_offset_ctrl + '.v', k=False, channelBox=False)

    # Expose Custom Rotate Order
    cmds.addAttr(head_offset_ctrl, ln='rotationOrder', at='enum', en=ROTATE_ORDER_ENUM, keyable=True,
                 niceName='Rotate Order')
    cmds.connectAttr(head_offset_ctrl + '.rotationOrder', head_offset_ctrl + '.rotateOrder', f=True)

    head_offset_data_grp = cmds.group(
        name=head_offset_ctrl.replace(CTRL_SUFFIX.capitalize(), 'Data') + GRP_SUFFIX.capitalize(), empty=True,
        world=True)
    cmds.delete(cmds.parentConstraint(head_offset_ctrl, head_offset_data_grp))
    cmds.parent(head_offset_data_grp, head_ctrl)

    cmds.connectAttr(head_offset_ctrl + '.translate', head_offset_data_grp + '.translate', f=True)
    cmds.connectAttr(head_offset_ctrl + '.rotate', head_offset_data_grp + '.rotate', f=True)

    cmds.addAttr(head_ctrl, ln='showOffsetCtrl', at='bool', k=True)
    cmds.connectAttr(head_ctrl + '.showOffsetCtrl', head_offset_ctrl + '.v', f=True)

    # #### End Head In-Between Offset

    # Jaw Control
    jaw_ctrl = cmds.curve(name=rig_joints.get('jaw_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                          p=[[0.013, 0.088, -0.088], [0.013, 0.016, -0.125], [0.013, 0.042, -0.088],
                             [0.013, 0.078, -0.0], [0.013, 0.042, 0.088], [0.013, 0.016, 0.125], [0.013, 0.088, 0.088],
                             [0.013, 0.125, 0.0], [0.013, 0.088, -0.088], [0.013, 0.016, -0.125],
                             [0.013, 0.042, -0.088]], d=3, per=True,
                          k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])

    cmds.setAttr(jaw_ctrl + '.scaleX', general_scale_offset)
    cmds.setAttr(jaw_ctrl + '.scaleY', general_scale_offset)
    cmds.setAttr(jaw_ctrl + '.scaleZ', general_scale_offset)
    cmds.makeIdentity(jaw_ctrl, apply=True, scale=True)
    for shape in cmds.listRelatives(jaw_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(jaw_ctrl))
    change_viewport_color(jaw_ctrl, (.8, .8, 0))
    jaw_ctrl_grp = cmds.group(name=jaw_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(jaw_ctrl, jaw_ctrl_grp)
    cmds.parent(jaw_ctrl_grp, head_offset_data_grp)
    cmds.delete(cmds.parentConstraint(rig_joints.get('jaw_jnt'), jaw_ctrl_grp))

    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(0, 90, 0, jaw_ctrl_grp, os=True, relative=True)

    desired_pivot = cmds.xform(jaw_ctrl, q=True, ws=True, t=True)
    cmds.delete(cmds.parentConstraint(rig_joints.get('jaw_end_jnt'), jaw_ctrl))
    cmds.xform(jaw_ctrl, piv=desired_pivot, ws=True)
    cmds.makeIdentity(jaw_ctrl, apply=True, scale=True, rotate=True, translate=True)

    # Eye Controls
    left_eye_ctrl = cmds.curve(name=rig_joints.get('left_eye_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                               p=[[0.098, -0.098, -0.0], [0.139, -0.0, -0.0], [0.098, 0.098, 0.0], [0.0, 0.139, 0.0],
                                  [-0.098, 0.098, 0.0], [-0.139, 0.0, 0.0], [-0.098, -0.098, -0.0],
                                  [-0.0, -0.139, -0.0], [0.098, -0.098, -0.0], [0.139, -0.0, -0.0],
                                  [0.098, 0.098, 0.0]], d=3, per=True,
                               k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    right_eye_ctrl = cmds.curve(name=rig_joints.get('right_eye_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                p=[[0.098, -0.098, -0.0], [0.139, -0.0, -0.0], [0.098, 0.098, 0.0], [0.0, 0.139, 0.0],
                                   [-0.098, 0.098, 0.0], [-0.139, 0.0, 0.0], [-0.098, -0.098, -0.0],
                                   [-0.0, -0.139, -0.0], [0.098, -0.098, -0.0], [0.139, -0.0, -0.0],
                                   [0.098, 0.098, 0.0]], d=3, per=True,
                                k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    main_eye_ctrl = cmds.curve(
        name=rig_joints.get('right_eye_jnt').replace(JNT_SUFFIX, '').replace('right', 'main') + CTRL_SUFFIX,
        p=[[0.315, -0.242, -0.0], [0.446, -0.0, -0.0], [0.315, 0.242, 0.0], [0.0, 0.105, 0.0], [-0.315, 0.242, 0.0],
           [-0.446, 0.0, 0.0], [-0.315, -0.242, -0.0], [-0.0, -0.105, -0.0], [0.315, -0.242, -0.0], [0.446, -0.0, -0.0],
           [0.315, 0.242, 0.0]], d=3, per=True, k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    temp_transform = cmds.group(name='temporary_eye_finder_transform', empty=True, world=True)

    # Rename Shapes
    for shape in cmds.listRelatives(left_eye_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(left_eye_ctrl))
    for shape in cmds.listRelatives(right_eye_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(right_eye_ctrl))
    for shape in cmds.listRelatives(main_eye_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(main_eye_ctrl))

    # Create Control Groups
    main_eye_ctrl_grp = cmds.group(name=main_eye_ctrl + '_' + GRP_SUFFIX, empty=True, world=True)
    main_eye_ctrl_offset_grp = cmds.group(name=main_eye_ctrl + '_dataOffset', empty=True, world=True)
    left_eye_ctrl_grp = cmds.group(name=left_eye_ctrl + '_' + GRP_SUFFIX, empty=True, world=True)
    right_eye_ctrl_grp = cmds.group(name=right_eye_ctrl + '_' + GRP_SUFFIX, empty=True, world=True)
    left_eye_ctrl_offset_grp = cmds.group(name=left_eye_ctrl + '_' + GRP_SUFFIX + 'Offset', empty=True, world=True)
    right_eye_ctrl_offset_grp = cmds.group(name=right_eye_ctrl + '_' + GRP_SUFFIX + 'Offset', empty=True, world=True)

    # Assemble Hierarchy
    cmds.parent(left_eye_ctrl, left_eye_ctrl_offset_grp)
    cmds.parent(left_eye_ctrl_offset_grp, left_eye_ctrl_grp)
    cmds.parent(right_eye_ctrl, right_eye_ctrl_offset_grp)
    cmds.parent(right_eye_ctrl_offset_grp, right_eye_ctrl_grp)
    cmds.parent(main_eye_ctrl, main_eye_ctrl_grp)
    cmds.parent(main_eye_ctrl_offset_grp, main_eye_ctrl)
    cmds.parent(left_eye_ctrl_grp, main_eye_ctrl_offset_grp)
    cmds.parent(right_eye_ctrl_grp, main_eye_ctrl_offset_grp)

    # Position Elements
    cmds.move(.2, 0, 0, left_eye_ctrl_grp)
    cmds.move(-.2, 0, 0, right_eye_ctrl_grp)

    # Find Position
    cmds.delete(cmds.pointConstraint([rig_joints.get('left_eye_jnt'), rig_joints.get('right_eye_jnt')], temp_transform))
    cmds.move(0, 0, general_scale_offset * 2, temp_transform, relative=True)
    desired_position = cmds.xform(temp_transform, q=True, t=True)
    cmds.delete(temp_transform)
    cmds.move(desired_position[0], desired_position[1], desired_position[2], main_eye_ctrl_grp)

    # Find Scale
    left_eye_position = abs(cmds.xform(rig_joints.get('left_eye_jnt'), q=True, ws=True, t=True)[0])
    right_eye_position = abs(cmds.xform(rig_joints.get('right_eye_jnt'), q=True, ws=True, t=True)[0])

    main_eye_scale = (right_eye_position + left_eye_position) * 3

    cmds.setAttr(main_eye_ctrl_grp + '.scaleX', main_eye_scale)
    cmds.setAttr(main_eye_ctrl_grp + '.scaleY', main_eye_scale)
    cmds.setAttr(main_eye_ctrl_grp + '.scaleZ', main_eye_scale)
    cmds.makeIdentity(main_eye_ctrl_grp, apply=True, scale=True)

    change_viewport_color(left_eye_ctrl, LEFT_CTRL_COLOR)
    change_viewport_color(right_eye_ctrl, RIGHT_CTRL_COLOR)
    change_viewport_color(main_eye_ctrl_grp, (1, 1, 0))

    cmds.parent(main_eye_ctrl_grp, head_ctrl)

    # ################# Left Leg FK #################
    # Calculate Scale Offset
    left_leg_scale_offset = 0
    left_leg_scale_offset += dist_center_to_center(rig_joints.get('left_knee_jnt'), rig_joints.get('left_ankle_jnt'))
    left_leg_scale_offset += dist_center_to_center(rig_joints.get('left_hip_jnt'), rig_joints.get('left_knee_jnt'))

    # Left Hip FK
    left_hip_ctrl = cmds.curve(name=rig_joints.get('left_hip_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                               p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098], [0.0, 0.139, -0.0],
                                  [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098], [-0.0, -0.139, 0.0],
                                  [-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098]], d=3, per=True,
                               k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    left_hip_ctrl_grp = cmds.group(name=left_hip_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)

    cmds.parent(left_hip_ctrl, left_hip_ctrl_grp)

    for shape in cmds.listRelatives(left_hip_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(left_hip_ctrl))

    cmds.setAttr(left_hip_ctrl + '.scaleX', left_leg_scale_offset)
    cmds.setAttr(left_hip_ctrl + '.scaleY', left_leg_scale_offset)
    cmds.setAttr(left_hip_ctrl + '.scaleZ', left_leg_scale_offset)
    cmds.makeIdentity(left_hip_ctrl, apply=True, scale=True)

    cmds.delete(cmds.parentConstraint(rig_joints.get('left_hip_jnt'), left_hip_ctrl_grp))

    add_orient_offset(left_hip_ctrl, (0, 0, -90), apply=settings.get('uniform_ctrl_orient'))
    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(0, -90, -90, left_hip_ctrl_grp, os=True, relative=True)

    change_viewport_color(left_hip_ctrl, LEFT_CTRL_COLOR)
    cmds.parent(left_hip_ctrl_grp, hip_offset_data_grp)

    # Adjust Size
    left_leg_scale_offset = left_leg_scale_offset * .8

    # Left Knee FK
    left_knee_ctrl = cmds.curve(name=rig_joints.get('left_knee_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098],
                                   [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098],
                                   [-0.0, -0.139, 0.0], [-0.0, -0.098, -0.098], [0.0, -0.0, -0.139],
                                   [0.0, 0.098, -0.098]], d=3, per=True,
                                k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    left_knee_ctrl_grp = cmds.group(name=left_knee_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(left_knee_ctrl, left_knee_ctrl_grp)

    for shape in cmds.listRelatives(left_knee_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(left_knee_ctrl))

    cmds.setAttr(left_knee_ctrl + '.scaleX', left_leg_scale_offset)
    cmds.setAttr(left_knee_ctrl + '.scaleY', left_leg_scale_offset)
    cmds.setAttr(left_knee_ctrl + '.scaleZ', left_leg_scale_offset)
    cmds.makeIdentity(left_knee_ctrl, apply=True, scale=True)

    cmds.delete(cmds.parentConstraint(rig_joints.get('left_knee_jnt'), left_knee_ctrl_grp))

    add_orient_offset(left_knee_ctrl, (0, 0, -90), apply=settings.get('uniform_ctrl_orient'))
    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(0, -90, -90, left_knee_ctrl_grp, os=True, relative=True)

    change_viewport_color(left_knee_ctrl, LEFT_CTRL_COLOR)
    cmds.parent(left_knee_ctrl_grp, left_hip_ctrl)

    # Left Ankle FK
    left_ankle_ctrl = cmds.curve(name=rig_joints.get('left_ankle_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                 p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098],
                                    [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098],
                                    [-0.0, -0.139, 0.0], [-0.0, -0.098, -0.098], [0.0, -0.0, -0.139],
                                    [0.0, 0.098, -0.098]], d=3, per=True,
                                 k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    left_ankle_ctrl_grp = cmds.group(name=left_ankle_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(left_ankle_ctrl, left_ankle_ctrl_grp)

    for shape in cmds.listRelatives(left_ankle_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(left_ankle_ctrl))

    cmds.setAttr(left_ankle_ctrl + '.scaleX', left_leg_scale_offset)
    cmds.setAttr(left_ankle_ctrl + '.scaleY', left_leg_scale_offset)
    cmds.setAttr(left_ankle_ctrl + '.scaleZ', left_leg_scale_offset)

    cmds.makeIdentity(left_ankle_ctrl, apply=True, scale=True)

    cmds.delete(cmds.parentConstraint(rig_joints.get('left_ankle_jnt'), left_ankle_ctrl_grp))

    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(0, -90, -90, left_ankle_ctrl_grp, os=True, relative=True)

    change_viewport_color(left_ankle_ctrl, LEFT_CTRL_COLOR)

    temp_transform = cmds.group(name=left_ankle_ctrl + '_rotExtraction', empty=True, world=True)
    cmds.delete(cmds.pointConstraint(rig_joints.get('left_toe_jnt'), temp_transform))
    cmds.delete(cmds.pointConstraint(rig_joints.get('left_ankle_jnt'), temp_transform, skip=['x', 'z']))
    cmds.delete(
        cmds.aimConstraint(temp_transform, left_ankle_ctrl, offset=(0, 0, 0), aimVector=(0, 1, 0), upVector=(1, 0, 0),
                           worldUpType='vector', worldUpVector=(0, -1, 0)))
    cmds.delete(temp_transform)
    cmds.makeIdentity(left_ankle_ctrl, apply=True, rotate=True)
    cmds.parent(left_ankle_ctrl_grp, left_knee_ctrl)

    # Left Ball FK
    left_ball_ctrl = cmds.curve(name=rig_joints.get('left_ball_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098],
                                   [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098],
                                   [-0.0, -0.139, 0.0], [-0.0, -0.098, -0.098], [0.0, -0.0, -0.139],
                                   [0.0, 0.098, -0.098]], d=3, per=True,
                                k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    left_ball_ctrl_grp = cmds.group(name=left_ball_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(left_ball_ctrl, left_ball_ctrl_grp)

    for shape in cmds.listRelatives(left_ball_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(left_ball_ctrl))

    cmds.setAttr(left_ball_ctrl + '.scaleX', left_leg_scale_offset)
    cmds.setAttr(left_ball_ctrl + '.scaleY', left_leg_scale_offset)
    cmds.setAttr(left_ball_ctrl + '.scaleZ', left_leg_scale_offset)
    cmds.makeIdentity(left_ball_ctrl, apply=True, scale=True)

    cmds.delete(cmds.parentConstraint(rig_joints.get('left_ball_jnt'), left_ball_ctrl_grp))

    add_orient_offset(left_ball_ctrl, (0, 0, 90), apply=settings.get('uniform_ctrl_orient'))
    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(-90, -90, 0, left_ball_ctrl_grp, os=True, relative=True)

    change_viewport_color(left_ball_ctrl, LEFT_CTRL_COLOR)
    cmds.parent(left_ball_ctrl_grp, left_ankle_ctrl)

    # ################# Left Leg IK Control #################
    left_knee_scale_offset = 0
    left_knee_scale_offset += dist_center_to_center(rig_joints.get('left_knee_jnt'), rig_joints.get('left_ankle_jnt'))
    left_knee_scale_offset += dist_center_to_center(rig_joints.get('left_hip_jnt'), rig_joints.get('left_knee_jnt'))
    left_knee_scale_offset = left_knee_scale_offset / 2

    # Left Knee Pole Vector Ctrl
    left_knee_ik_ctrl = cmds.curve(name=rig_joints.get('left_knee_jnt').replace(JNT_SUFFIX, 'ik_') + CTRL_SUFFIX,
                                   p=[[-0.125, 0.0, 0.0], [0.125, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.125],
                                      [0.0, 0.0, -0.125], [0.0, 0.0, 0.0], [0.0, 0.125, 0.0], [0.0, -0.125, 0.0]], d=1)
    left_knee_ik_ctrl_grp = cmds.group(name=left_knee_ik_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(left_knee_ik_ctrl, left_knee_ik_ctrl_grp)

    for shape in cmds.listRelatives(left_knee_ik_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(left_knee_ik_ctrl))

    # Left Knee Find Position
    temp_transform = cmds.group(name=left_knee_ik_ctrl + '_rotExtraction', empty=True, world=True)
    cmds.delete(cmds.pointConstraint(elements.get('left_knee_proxy_crv'), temp_transform))
    cmds.delete(
        cmds.aimConstraint(elements.get('left_knee_pv_dir'), temp_transform, offset=(0, 0, 0),
                           aimVector=(1, 0, 0),
                           upVector=(0, -1, 0), worldUpType='vector', worldUpVector=(0, 1, 0)))
    cmds.move(left_knee_scale_offset * 1.2, 0, 0, temp_transform, os=True, relative=True)
    cmds.delete(cmds.pointConstraint(temp_transform, left_knee_ik_ctrl_grp))
    cmds.delete(temp_transform)

    # Left Knee Pole Vec Visibility and Parenting
    cmds.setAttr(left_knee_ik_ctrl + '.scaleX', left_knee_scale_offset)
    cmds.setAttr(left_knee_ik_ctrl + '.scaleY', left_knee_scale_offset)
    cmds.setAttr(left_knee_ik_ctrl + '.scaleZ', left_knee_scale_offset)
    cmds.makeIdentity(left_knee_ik_ctrl, apply=True, scale=True)
    change_viewport_color(left_knee_ik_ctrl, LEFT_CTRL_COLOR)
    cmds.parent(left_knee_ik_ctrl_grp, direction_ctrl)

    # ################# Left Foot IK Control #################
    left_foot_ik_ctrl_a = cmds.curve(name='left_foot_ik_' + CTRL_SUFFIX,
                                     p=[[0.267, 0.0, -0.641], [0.267, 0.0, 0.671], [-0.267, 0.0, 0.671],
                                        [-0.267, 0.0, -0.641], [0.267, 0.0, -0.641], [0.267, 0.321, -0.641],
                                        [-0.267, 0.321, -0.641], [-0.267, 0.321, 0.671], [0.267, 0.321, 0.671],
                                        [0.267, 0.321, -0.641], [0.267, 0.321, 0.671], [0.267, 0.0, 0.671],
                                        [-0.267, 0.0, 0.671], [-0.267, 0.321, 0.671], [-0.267, 0.321, -0.641],
                                        [-0.267, 0.0, -0.641]], d=1)
    left_foot_ik_ctrl_b = cmds.curve(
        p=[[-0.183, 0.0, -0.323], [-0.197, 0.0, -0.428], [-0.184, 0.0, -0.521], [-0.15, 0.0, -0.575],
           [-0.114, 0.0, -0.611], [-0.076, 0.0, -0.631], [-0.036, 0.0, -0.641], [0.006, 0.0, -0.635],
           [0.047, 0.0, -0.62], [0.087, 0.0, -0.587], [0.127, 0.0, -0.538], [0.149, 0.0, -0.447], [0.146, 0.0, -0.34],
           [0.153, 0.0, -0.235], [0.173, 0.0, -0.136], [0.202, 0.0, -0.05], [0.23, 0.0, 0.039], [0.259, 0.0, 0.154],
           [0.27, 0.0, 0.234], [0.267, 0.0, 0.338], [0.247, 0.0, 0.426], [0.22, 0.0, 0.496], [0.187, 0.0, 0.553],
           [0.153, 0.0, 0.597], [0.116, 0.0, 0.628], [0.076, 0.0, 0.65], [0.036, 0.0, 0.66], [-0.006, 0.0, 0.656],
           [-0.045, 0.0, 0.638], [-0.087, 0.0, 0.611], [-0.127, 0.0, 0.571], [-0.164, 0.0, 0.517], [-0.199, 0.0, 0.451],
           [-0.228, 0.0, 0.366], [-0.242, 0.0, 0.263], [-0.239, 0.0, 0.181], [-0.224, 0.0, 0.063],
           [-0.206, 0.0, -0.028], [-0.187, 0.0, -0.117], [-0.177, 0.0, -0.216], [-0.183, 0.0, -0.323]], d=1)
    left_foot_ik_ctrl_c = cmds.curve(
        p=[[0.0, 0.0, 0.0], [0.573, 0.0, 0.0], [0.576, -0.021, 0.0], [0.584, -0.041, 0.0], [0.597, -0.058, 0.0],
           [0.614, -0.071, 0.0], [0.633, -0.079, 0.0], [0.655, -0.082, 0.0], [0.655, 0.0, 0.0], [0.573, 0.0, 0.0],
           [0.576, 0.021, 0.0], [0.584, 0.041, 0.0], [0.597, 0.058, 0.0], [0.614, 0.071, 0.0], [0.633, 0.079, 0.0],
           [0.655, 0.082, 0.0], [0.676, 0.079, 0.0], [0.695, 0.071, 0.0], [0.712, 0.058, 0.0], [0.726, 0.041, 0.0],
           [0.734, 0.021, 0.0], [0.737, 0.0, 0.0], [0.734, -0.021, 0.0], [0.726, -0.041, 0.0], [0.713, -0.058, 0.0],
           [0.696, -0.07, 0.0], [0.676, -0.079, 0.0], [0.655, -0.082, 0.0], [0.655, 0.082, 0.0], [0.655, 0.0, 0.0],
           [0.737, 0.0, 0.0]], d=1)
    left_foot_ik_ctrl = combine_curves_list([left_foot_ik_ctrl_a, left_foot_ik_ctrl_b, left_foot_ik_ctrl_c])

    left_foot_ik_ctrl_grp = cmds.group(name=left_foot_ik_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(left_foot_ik_ctrl, left_foot_ik_ctrl_grp)

    shapes = cmds.listRelatives(left_foot_ik_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format(left_foot_ik_ctrl.replace(CTRL_SUFFIX, 'box')))
    cmds.rename(shapes[1], '{0}Shape'.format(left_foot_ik_ctrl.replace(CTRL_SUFFIX, 'flat')))
    cmds.rename(shapes[2], '{0}Shape'.format(left_foot_ik_ctrl.replace(CTRL_SUFFIX, 'pin')))

    # Left Foot Scale
    left_foot_scale_offset = 0
    left_foot_scale_offset += dist_center_to_center(rig_joints.get('left_ankle_jnt'), rig_joints.get('left_ball_jnt'))
    left_foot_scale_offset += dist_center_to_center(rig_joints.get('left_ball_jnt'), rig_joints.get('left_toe_jnt'))

    cmds.setAttr(left_foot_ik_ctrl + '.scaleX', left_foot_scale_offset)
    cmds.setAttr(left_foot_ik_ctrl + '.scaleY', left_foot_scale_offset)
    cmds.setAttr(left_foot_ik_ctrl + '.scaleZ', left_foot_scale_offset)
    cmds.makeIdentity(left_foot_ik_ctrl, apply=True, scale=True)

    # Left Foot Position
    cmds.delete(cmds.pointConstraint([rig_joints.get('left_ankle_jnt'),
                                      rig_joints.get('left_toe_jnt')], left_foot_ik_ctrl_grp, skip='y'))
    desired_rotation = cmds.xform(elements.get('left_ankle_proxy_crv'), q=True, ro=True)
    desired_translation = cmds.xform(elements.get('left_ankle_proxy_crv'), q=True, t=True, ws=True)
    if settings.get('worldspace_ik_orient'):
        cmds.setAttr(left_foot_ik_ctrl + '.ry', desired_rotation[1])
        cmds.makeIdentity(left_foot_ik_ctrl, apply=True, rotate=True)
    else:
        cmds.setAttr(left_foot_ik_ctrl_grp + '.ry', desired_rotation[1])

    # Left Foot Pivot Adjustment
    cmds.xform(left_foot_ik_ctrl_grp, piv=desired_translation, ws=True)
    cmds.xform(left_foot_ik_ctrl, piv=desired_translation, ws=True)

    # Duplicate for Offset Control And Create Data Transform
    left_foot_offset_ik_ctrl = cmds.duplicate(left_foot_ik_ctrl, renameChildren=True,
                                              name=left_foot_ik_ctrl.replace('_' + CTRL_SUFFIX,
                                                                             '_offset' + CTRL_SUFFIX.capitalize()))[0]
    left_foot_offset_ik_ctrl_grp = \
        cmds.duplicate(left_foot_ik_ctrl, po=True, name=left_foot_offset_ik_ctrl + GRP_SUFFIX.capitalize())[
            0]  # group command generates junk data
    left_foot_offset_data_grp = \
        cmds.duplicate(left_foot_ik_ctrl, po=True,
                       name=left_foot_offset_ik_ctrl.replace(CTRL_SUFFIX.capitalize(), 'Data'))[
            0]  # group command generates junk data
    cmds.parent(left_foot_offset_data_grp, left_foot_offset_ik_ctrl_grp)
    cmds.delete(cmds.parentConstraint(left_foot_ik_ctrl, left_foot_offset_ik_ctrl_grp))
    cmds.delete(cmds.parentConstraint(left_foot_ik_ctrl, left_foot_offset_data_grp))
    cmds.connectAttr(left_foot_offset_ik_ctrl + '.translate', left_foot_offset_data_grp + '.translate', f=True)
    cmds.connectAttr(left_foot_offset_ik_ctrl + '.rotate', left_foot_offset_data_grp + '.rotate', f=True)

    # Left Foot General Adjustments
    change_viewport_color(left_foot_ik_ctrl, LEFT_CTRL_COLOR)
    cmds.parent(left_foot_ik_ctrl_grp, direction_ctrl)

    # Add Separator (Control Behavior)
    cmds.addAttr(left_foot_ik_ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
    cmds.setAttr(left_foot_ik_ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)

    # Expose Custom Rotate Order
    cmds.addAttr(left_foot_ik_ctrl, ln='rotationOrder', at='enum', en=ROTATE_ORDER_ENUM, keyable=True,
                 niceName='Rotate Order')
    cmds.connectAttr(left_foot_ik_ctrl + '.rotationOrder', left_foot_ik_ctrl + '.rotateOrder', f=True)

    # ################# Right Leg FK #################

    # Calculate Scale Offset
    right_leg_scale_offset = 0
    right_leg_scale_offset -= dist_center_to_center(rig_joints.get('right_knee_jnt'), rig_joints.get('right_ankle_jnt'))
    right_leg_scale_offset -= dist_center_to_center(rig_joints.get('right_hip_jnt'), rig_joints.get('right_knee_jnt'))

    # Right Hip FK
    right_hip_ctrl = cmds.curve(name=rig_joints.get('right_hip_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098],
                                   [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098],
                                   [-0.0, -0.139, 0.0], [-0.0, -0.098, -0.098], [0.0, -0.0, -0.139],
                                   [0.0, 0.098, -0.098]], d=3, per=True,
                                k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    right_hip_ctrl_grp = cmds.group(name=right_hip_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(right_hip_ctrl, right_hip_ctrl_grp)

    for shape in cmds.listRelatives(right_hip_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(right_hip_ctrl))

    cmds.setAttr(right_hip_ctrl + '.scaleX', right_leg_scale_offset)
    cmds.setAttr(right_hip_ctrl + '.scaleY', right_leg_scale_offset)
    cmds.setAttr(right_hip_ctrl + '.scaleZ', right_leg_scale_offset)
    cmds.makeIdentity(right_hip_ctrl, apply=True, scale=True)

    cmds.delete(cmds.parentConstraint(rig_joints.get('right_hip_jnt'), right_hip_ctrl_grp))

    add_orient_offset(right_hip_ctrl, (0, 0, -90), apply=settings.get('uniform_ctrl_orient'))
    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(0, -90, -90, right_hip_ctrl_grp, os=True, relative=True)

    change_viewport_color(right_hip_ctrl, RIGHT_CTRL_COLOR)
    cmds.parent(right_hip_ctrl_grp, hip_offset_data_grp)

    # Adjust Size
    right_leg_scale_offset = right_leg_scale_offset * .8

    # Right Knee FK
    right_knee_ctrl = cmds.curve(name=rig_joints.get('right_knee_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                 p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098],
                                    [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098],
                                    [-0.0, -0.139, 0.0], [-0.0, -0.098, -0.098], [0.0, -0.0, -0.139],
                                    [0.0, 0.098, -0.098]], d=3, per=True,
                                 k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    right_knee_ctrl_grp = cmds.group(name=right_knee_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(right_knee_ctrl, right_knee_ctrl_grp)

    for shape in cmds.listRelatives(right_knee_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(right_knee_ctrl))

    cmds.setAttr(right_knee_ctrl + '.scaleX', right_leg_scale_offset)
    cmds.setAttr(right_knee_ctrl + '.scaleY', right_leg_scale_offset)
    cmds.setAttr(right_knee_ctrl + '.scaleZ', right_leg_scale_offset)
    cmds.makeIdentity(right_knee_ctrl, apply=True, scale=True)

    cmds.delete(cmds.parentConstraint(rig_joints.get('right_knee_jnt'), right_knee_ctrl_grp))

    add_orient_offset(right_knee_ctrl, (0, 0, -90), apply=settings.get('uniform_ctrl_orient'))
    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(0, -90, -90, right_knee_ctrl_grp, os=True, relative=True)

    change_viewport_color(right_knee_ctrl, RIGHT_CTRL_COLOR)
    cmds.parent(right_knee_ctrl_grp, right_hip_ctrl)

    # Right Ankle FK
    right_ankle_ctrl = cmds.curve(name=rig_joints.get('right_ankle_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                  p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098],
                                     [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098],
                                     [-0.0, -0.139, 0.0], [-0.0, -0.098, -0.098], [0.0, -0.0, -0.139],
                                     [0.0, 0.098, -0.098]], d=3, per=True,
                                  k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    right_ankle_ctrl_grp = cmds.group(name=right_ankle_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(right_ankle_ctrl, right_ankle_ctrl_grp)

    for shape in cmds.listRelatives(right_ankle_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(right_ankle_ctrl))

    cmds.setAttr(right_ankle_ctrl + '.scaleX', right_leg_scale_offset)
    cmds.setAttr(right_ankle_ctrl + '.scaleY', right_leg_scale_offset)
    cmds.setAttr(right_ankle_ctrl + '.scaleZ', right_leg_scale_offset)

    cmds.makeIdentity(right_ankle_ctrl, apply=True, scale=True)

    cmds.delete(cmds.parentConstraint(rig_joints.get('right_ankle_jnt'), right_ankle_ctrl_grp))

    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(0, -90, -90, right_ankle_ctrl_grp, os=True, relative=True)

    change_viewport_color(right_ankle_ctrl, RIGHT_CTRL_COLOR)

    temp_transform = cmds.group(name=right_ankle_ctrl + '_rotExtraction', empty=True, world=True)
    cmds.delete(cmds.pointConstraint(rig_joints.get('right_toe_jnt'), temp_transform))
    cmds.delete(cmds.pointConstraint(rig_joints.get('right_ankle_jnt'), temp_transform, skip=['x', 'z']))
    cmds.delete(
        cmds.aimConstraint(temp_transform, right_ankle_ctrl, offset=(0, 0, 0), aimVector=(0, 1, 0), upVector=(1, 0, 0),
                           worldUpType='vector', worldUpVector=(0, -1, 0)))
    cmds.delete(temp_transform)
    cmds.makeIdentity(right_ankle_ctrl, apply=True, rotate=True)
    cmds.parent(right_ankle_ctrl_grp, right_knee_ctrl)

    # Right Ball FK
    right_ball_ctrl = cmds.curve(name=rig_joints.get('right_ball_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                 p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098],
                                    [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098],
                                    [-0.0, -0.139, 0.0], [-0.0, -0.098, -0.098], [0.0, -0.0, -0.139],
                                    [0.0, 0.098, -0.098]], d=3, per=True,
                                 k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    right_ball_ctrl_grp = cmds.group(name=right_ball_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(right_ball_ctrl, right_ball_ctrl_grp)

    for shape in cmds.listRelatives(right_ball_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(right_ball_ctrl))

    cmds.setAttr(right_ball_ctrl + '.scaleX', right_leg_scale_offset)
    cmds.setAttr(right_ball_ctrl + '.scaleY', right_leg_scale_offset)
    cmds.setAttr(right_ball_ctrl + '.scaleZ', right_leg_scale_offset)
    cmds.makeIdentity(right_ball_ctrl, apply=True, scale=True)

    cmds.delete(cmds.parentConstraint(rig_joints.get('right_ball_jnt'), right_ball_ctrl_grp))

    add_orient_offset(right_ball_ctrl, (0, 0, -90), apply=settings.get('uniform_ctrl_orient'))
    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(0, -90, -90, right_ball_ctrl_grp, os=True, relative=True)

    change_viewport_color(right_ball_ctrl, RIGHT_CTRL_COLOR)
    cmds.parent(right_ball_ctrl_grp, right_ankle_ctrl)

    # ################# Right Leg IK Control #################
    # Calculate Scale Offset
    right_knee_scale_offset = 0
    right_knee_scale_offset += dist_center_to_center(rig_joints.get('right_knee_jnt'),
                                                     rig_joints.get('right_ankle_jnt'))
    right_knee_scale_offset += dist_center_to_center(rig_joints.get('right_hip_jnt'), rig_joints.get('right_knee_jnt'))
    right_knee_scale_offset = (right_knee_scale_offset / 2) * -1

    # Right Knee Pole Vector Ctrl
    right_knee_ik_ctrl = cmds.curve(name=rig_joints.get('right_knee_jnt').replace(JNT_SUFFIX, 'ik_') + CTRL_SUFFIX,
                                    p=[[-0.125, 0.0, 0.0], [0.125, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.125],
                                       [0.0, 0.0, -0.125], [0.0, 0.0, 0.0], [0.0, 0.125, 0.0], [0.0, -0.125, 0.0]], d=1)
    right_knee_ik_ctrl_grp = cmds.group(name=right_knee_ik_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(right_knee_ik_ctrl, right_knee_ik_ctrl_grp)

    for shape in cmds.listRelatives(right_knee_ik_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(right_knee_ik_ctrl))

    # Right Knee Find Position
    temp_transform = cmds.group(name=right_knee_ik_ctrl + '_rotExtraction', empty=True, world=True)
    cmds.delete(cmds.pointConstraint(elements.get('right_knee_proxy_crv'), temp_transform))
    cmds.delete(cmds.aimConstraint(elements.get('right_knee_pv_dir'), temp_transform, offset=(0, 0, 0),
                                   aimVector=(1, 0, 0), upVector=(0, -1, 0), worldUpType='vector',
                                   worldUpVector=(0, 1, 0)))
    cmds.move(right_knee_scale_offset * -1.2, 0, 0, temp_transform, os=True, relative=True)
    cmds.delete(cmds.pointConstraint(temp_transform, right_knee_ik_ctrl_grp))
    cmds.delete(temp_transform)

    # Right Knee Pole Vec Visibility and Parenting
    cmds.setAttr(right_knee_ik_ctrl + '.scaleX', right_knee_scale_offset)
    cmds.setAttr(right_knee_ik_ctrl + '.scaleY', right_knee_scale_offset)
    cmds.setAttr(right_knee_ik_ctrl + '.scaleZ', right_knee_scale_offset)
    cmds.makeIdentity(right_knee_ik_ctrl, apply=True, scale=True)
    change_viewport_color(right_knee_ik_ctrl, RIGHT_CTRL_COLOR)
    cmds.parent(right_knee_ik_ctrl_grp, direction_ctrl)

    # ################# Right Foot IK Control #################
    right_foot_ik_ctrl_a = cmds.curve(name='right_foot_ik_' + CTRL_SUFFIX,
                                      p=[[0.267, 0.0, -0.641], [0.267, 0.0, 0.671], [-0.267, 0.0, 0.671],
                                         [-0.267, 0.0, -0.641], [0.267, 0.0, -0.641], [0.267, -0.321, -0.641],
                                         [-0.267, -0.321, -0.641], [-0.267, -0.321, 0.671], [0.267, -0.321, 0.671],
                                         [0.267, -0.321, -0.641], [0.267, -0.321, 0.671], [0.267, 0.0, 0.671],
                                         [-0.267, 0.0, 0.671], [-0.267, -0.321, 0.671], [-0.267, -0.321, -0.641],
                                         [-0.267, 0.0, -0.641]], d=1)
    right_foot_ik_ctrl_b = cmds.curve(
        p=[[-0.183, 0.0, -0.323], [-0.197, 0.0, -0.428], [-0.184, 0.0, -0.521], [-0.15, 0.0, -0.575],
           [-0.114, 0.0, -0.611], [-0.076, 0.0, -0.631], [-0.036, 0.0, -0.641], [0.006, 0.0, -0.635],
           [0.047, 0.0, -0.62], [0.087, 0.0, -0.587], [0.127, 0.0, -0.538], [0.149, 0.0, -0.447], [0.146, 0.0, -0.34],
           [0.153, 0.0, -0.235], [0.173, 0.0, -0.136], [0.202, 0.0, -0.05], [0.23, 0.0, 0.039], [0.259, 0.0, 0.154],
           [0.27, 0.0, 0.234], [0.267, 0.0, 0.338], [0.247, 0.0, 0.426], [0.22, 0.0, 0.496], [0.187, 0.0, 0.553],
           [0.153, 0.0, 0.597], [0.116, 0.0, 0.628], [0.076, 0.0, 0.65], [0.036, 0.0, 0.66], [-0.006, 0.0, 0.656],
           [-0.045, 0.0, 0.638], [-0.087, 0.0, 0.611], [-0.127, 0.0, 0.571], [-0.164, 0.0, 0.517], [-0.199, 0.0, 0.451],
           [-0.228, 0.0, 0.366], [-0.242, 0.0, 0.263], [-0.239, 0.0, 0.181], [-0.224, 0.0, 0.063],
           [-0.206, 0.0, -0.028], [-0.187, 0.0, -0.117], [-0.177, 0.0, -0.216], [-0.183, 0.0, -0.323]], d=1)
    right_foot_ik_ctrl_c = cmds.curve(
        p=[[0.0, 0.0, 0.0], [0.573, 0.0, 0.0], [0.576, -0.021, 0.0], [0.584, -0.041, 0.0], [0.597, -0.058, 0.0],
           [0.614, -0.071, 0.0], [0.633, -0.079, 0.0], [0.655, -0.082, 0.0], [0.655, 0.0, 0.0], [0.573, 0.0, 0.0],
           [0.576, 0.021, 0.0], [0.584, 0.041, 0.0], [0.597, 0.058, 0.0], [0.614, 0.071, 0.0], [0.633, 0.079, 0.0],
           [0.655, 0.082, 0.0], [0.676, 0.079, 0.0], [0.695, 0.071, 0.0], [0.712, 0.058, 0.0], [0.726, 0.041, 0.0],
           [0.734, 0.021, 0.0], [0.737, 0.0, 0.0], [0.734, -0.021, 0.0], [0.726, -0.041, 0.0], [0.713, -0.058, 0.0],
           [0.696, -0.07, 0.0], [0.676, -0.079, 0.0], [0.655, -0.082, 0.0], [0.655, 0.082, 0.0], [0.655, 0.0, 0.0],
           [0.737, 0.0, 0.0]], d=1)
    right_foot_ik_ctrl = combine_curves_list([right_foot_ik_ctrl_a, right_foot_ik_ctrl_b, right_foot_ik_ctrl_c])

    right_foot_ik_ctrl_grp = cmds.group(name=right_foot_ik_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(right_foot_ik_ctrl, right_foot_ik_ctrl_grp)

    shapes = cmds.listRelatives(right_foot_ik_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format(right_foot_ik_ctrl.replace(CTRL_SUFFIX, 'box')))
    cmds.rename(shapes[1], '{0}Shape'.format(right_foot_ik_ctrl.replace(CTRL_SUFFIX, 'flat')))
    cmds.rename(shapes[2], '{0}Shape'.format(right_foot_ik_ctrl.replace(CTRL_SUFFIX, 'pin')))

    # Right Foot Scale
    right_foot_scale_offset = 0
    right_foot_scale_offset += dist_center_to_center(rig_joints.get('right_ankle_jnt'),
                                                     rig_joints.get('right_ball_jnt'))
    right_foot_scale_offset += dist_center_to_center(rig_joints.get('right_ball_jnt'), rig_joints.get('right_toe_jnt'))
    right_foot_scale_offset = right_foot_scale_offset * -1

    cmds.setAttr(right_foot_ik_ctrl + '.scaleX', right_foot_scale_offset)
    cmds.setAttr(right_foot_ik_ctrl + '.scaleY', right_foot_scale_offset)
    cmds.setAttr(right_foot_ik_ctrl + '.scaleZ', right_foot_scale_offset * -1)
    cmds.makeIdentity(right_foot_ik_ctrl, apply=True, scale=True)

    # Right Foot Position
    cmds.delete(cmds.pointConstraint([rig_joints.get('right_ankle_jnt'), rig_joints.get('right_toe_jnt')],
                                     right_foot_ik_ctrl_grp, skip='y'))
    desired_rotation = cmds.xform(elements.get('right_ankle_proxy_crv'), q=True, ro=True)
    desired_translation = cmds.xform(elements.get('right_ankle_proxy_crv'), q=True, t=True, ws=True)
    if settings.get('worldspace_ik_orient'):
        cmds.setAttr(right_foot_ik_ctrl + '.ry', desired_rotation[1])
        cmds.makeIdentity(right_foot_ik_ctrl, apply=True, rotate=True)
    else:
        cmds.setAttr(right_foot_ik_ctrl_grp + '.ry', desired_rotation[1])

    # Right Foot Pivot Adjustment
    cmds.xform(right_foot_ik_ctrl_grp, piv=desired_translation, ws=True)
    cmds.xform(right_foot_ik_ctrl, piv=desired_translation, ws=True)

    # Duplicate for Offset Control And Create Data Transform
    right_foot_offset_ik_ctrl = cmds.duplicate(right_foot_ik_ctrl, renameChildren=True,
                                               name=right_foot_ik_ctrl.replace('_' + CTRL_SUFFIX,
                                                                               '_offset' + CTRL_SUFFIX.capitalize()))[0]
    right_foot_offset_ik_ctrl_grp = \
        cmds.duplicate(right_foot_ik_ctrl, po=True, name=right_foot_offset_ik_ctrl + GRP_SUFFIX.capitalize())[
            0]  # group command generates junk data
    right_foot_offset_data_grp = cmds.duplicate(right_foot_ik_ctrl, po=True,
                                                name=right_foot_offset_ik_ctrl.replace(CTRL_SUFFIX.capitalize(),
                                                                                       'Data'))[
        0]  # group command generates junk data
    cmds.parent(right_foot_offset_data_grp, right_foot_offset_ik_ctrl_grp)
    cmds.delete(cmds.parentConstraint(right_foot_ik_ctrl, right_foot_offset_ik_ctrl_grp))
    cmds.delete(cmds.parentConstraint(right_foot_ik_ctrl, right_foot_offset_data_grp))
    cmds.connectAttr(right_foot_offset_ik_ctrl + '.translate', right_foot_offset_data_grp + '.translate', f=True)
    cmds.connectAttr(right_foot_offset_ik_ctrl + '.rotate', right_foot_offset_data_grp + '.rotate', f=True)

    # Right Foot General Adjustments
    change_viewport_color(right_foot_ik_ctrl, RIGHT_CTRL_COLOR)
    cmds.parent(right_foot_ik_ctrl_grp, direction_ctrl)

    # Add Separator (Control Behavior)
    cmds.addAttr(right_foot_ik_ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
    cmds.setAttr(right_foot_ik_ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)

    # Expose Custom Rotate Order
    cmds.addAttr(right_foot_ik_ctrl, ln='rotationOrder', at='enum', en=ROTATE_ORDER_ENUM, keyable=True,
                 niceName='Rotate Order')
    cmds.connectAttr(right_foot_ik_ctrl + '.rotationOrder', right_foot_ik_ctrl + '.rotateOrder', f=True)

    # ################# Left Arm #################
    # Left Clavicle FK
    left_clavicle_ctrl = cmds.curve(name=rig_joints.get('left_clavicle_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                    p=[[0.0, 0.0, 0.0], [0.897, 1.554, 0.0], [0.959, 1.528, 0.0], [1.025, 1.52, 0.0],
                                       [1.091, 1.528, 0.0], [1.153, 1.554, 0.0], [1.206, 1.595, 0.0],
                                       [1.247, 1.647, 0.0], [1.025, 1.776, 0.0], [0.897, 1.554, 0.0],
                                       [0.844, 1.595, 0.0], [0.803, 1.648, 0.0], [0.778, 1.709, 0.0],
                                       [0.769, 1.776, 0.0], [0.778, 1.842, 0.0], [0.803, 1.904, 0.0],
                                       [0.844, 1.957, 0.0], [0.897, 1.997, 0.0], [0.959, 2.023, 0.0],
                                       [1.025, 2.032, 0.0], [1.091, 2.023, 0.0], [1.153, 1.998, 0.0],
                                       [1.206, 1.957, 0.0], [1.247, 1.904, 0.0], [1.273, 1.842, 0.0],
                                       [1.281, 1.776, 0.0], [1.272, 1.709, 0.0], [1.247, 1.647, 0.0],
                                       [0.803, 1.904, 0.0], [1.025, 1.776, 0.0], [1.153, 1.998, 0.0]], d=1)
    left_clavicle_ctrl_grp = cmds.group(name=left_clavicle_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)

    for shape in cmds.listRelatives(left_clavicle_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(left_clavicle_ctrl))

    # Left Clavicle Scale
    cmds.setAttr(left_clavicle_ctrl + '.scaleX', general_scale_offset * .25)
    cmds.setAttr(left_clavicle_ctrl + '.scaleY', general_scale_offset * .25)
    cmds.setAttr(left_clavicle_ctrl + '.scaleZ', general_scale_offset * .25)
    cmds.makeIdentity(left_clavicle_ctrl, apply=True, scale=True)

    # Left Clavicle Position
    cmds.delete(cmds.parentConstraint(rig_joints.get('left_clavicle_jnt'), left_clavicle_ctrl_grp))
    cmds.delete(cmds.pointConstraint(rig_joints.get('left_clavicle_jnt'), left_clavicle_ctrl))
    cmds.parent(left_clavicle_ctrl, left_clavicle_ctrl_grp)
    cmds.makeIdentity(left_clavicle_ctrl, apply=True, rotate=True)

    if settings.get('uniform_ctrl_orient'):
        add_orient_offset(left_clavicle_ctrl, (-90, 0, 0))
        cmds.rotate(90, 0, 0, left_clavicle_ctrl_grp, os=True, relative=True)

    # Left Clavicle General Adjustments
    change_viewport_color(left_clavicle_ctrl, LEFT_CTRL_COLOR)

    # Add Separator (Control Behavior)
    cmds.addAttr(left_clavicle_ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
    cmds.setAttr(left_clavicle_ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)

    # Expose Rotation Order
    cmds.addAttr(left_clavicle_ctrl, ln='rotationOrder', at='enum', en=ROTATE_ORDER_ENUM, keyable=True,
                 niceName='Rotate Order')
    cmds.connectAttr(left_clavicle_ctrl + '.rotationOrder', left_clavicle_ctrl + '.rotateOrder', f=True)

    # Left Shoulder FK
    left_shoulder_ctrl = cmds.curve(name=rig_joints.get('left_shoulder_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                    p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098],
                                       [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139],
                                       [-0.0, -0.098, 0.098], [-0.0, -0.139, 0.0], [-0.0, -0.098, -0.098],
                                       [0.0, -0.0, -0.139], [0.0, 0.098, -0.098]], d=3, per=True,
                                    k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    left_shoulder_ctrl_grp = cmds.group(name=left_shoulder_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(left_shoulder_ctrl, left_shoulder_ctrl_grp)

    for shape in cmds.listRelatives(left_shoulder_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(left_shoulder_ctrl))

    left_shoulder_scale_offset = cmds.xform(rig_joints.get('left_shoulder_jnt'), q=True, t=True)[0] * 6.5

    cmds.setAttr(left_shoulder_ctrl + '.scaleX', left_shoulder_scale_offset)
    cmds.setAttr(left_shoulder_ctrl + '.scaleY', left_shoulder_scale_offset)
    cmds.setAttr(left_shoulder_ctrl + '.scaleZ', left_shoulder_scale_offset)
    cmds.makeIdentity(left_shoulder_ctrl, apply=True, scale=True)

    cmds.delete(cmds.parentConstraint(rig_joints.get('left_shoulder_jnt'), left_shoulder_ctrl_grp))

    add_orient_offset(left_shoulder_ctrl, (0, 0, -90), apply=settings.get('uniform_ctrl_orient'))
    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(0, -90, -90, left_shoulder_ctrl_grp, os=True, relative=True)

    change_viewport_color(left_shoulder_ctrl, LEFT_CTRL_COLOR)
    cmds.parent(left_shoulder_ctrl_grp, left_clavicle_ctrl)

    # Left Elbow FK
    left_elbow_ctrl = cmds.curve(name=rig_joints.get('left_elbow_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                 p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098],
                                    [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098],
                                    [-0.0, -0.139, 0.0], [-0.0, -0.098, -0.098], [0.0, -0.0, -0.139],
                                    [0.0, 0.098, -0.098]], d=3, per=True,
                                 k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    left_elbow_ctrl_grp = cmds.group(name=left_elbow_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(left_elbow_ctrl, left_elbow_ctrl_grp)

    for shape in cmds.listRelatives(left_elbow_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(left_elbow_ctrl))

    left_arm_scale_offset = dist_center_to_center(rig_joints.get('left_shoulder_jnt'), rig_joints.get('left_elbow_jnt'))
    left_arm_scale_offset += dist_center_to_center(rig_joints.get('left_elbow_jnt'), rig_joints.get('left_wrist_jnt'))
    left_arm_scale_offset = left_arm_scale_offset * 1.35

    cmds.setAttr(left_elbow_ctrl + '.scaleX', left_arm_scale_offset)
    cmds.setAttr(left_elbow_ctrl + '.scaleY', left_arm_scale_offset)
    cmds.setAttr(left_elbow_ctrl + '.scaleZ', left_arm_scale_offset)
    cmds.makeIdentity(left_elbow_ctrl, apply=True, scale=True)

    cmds.delete(cmds.parentConstraint(rig_joints.get('left_elbow_jnt'), left_elbow_ctrl_grp))

    add_orient_offset(left_elbow_ctrl, (0, 0, -90), apply=settings.get('uniform_ctrl_orient'))
    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(0, -90, -90, left_elbow_ctrl_grp, os=True, relative=True)

    change_viewport_color(left_elbow_ctrl, LEFT_CTRL_COLOR)
    cmds.parent(left_elbow_ctrl_grp, left_shoulder_ctrl)

    # Left Wrist FK
    left_wrist_ctrl = cmds.curve(name=rig_joints.get('left_wrist_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                 p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098],
                                    [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098],
                                    [-0.0, -0.139, 0.0], [-0.0, -0.098, -0.098], [0.0, -0.0, -0.139],
                                    [0.0, 0.098, -0.098]], d=3, per=True,
                                 k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])

    left_wrist_ctrl_grp = cmds.group(name=left_wrist_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(left_wrist_ctrl, left_wrist_ctrl_grp)

    for shape in cmds.listRelatives(left_wrist_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(left_wrist_ctrl))

    left_arm_scale_offset = left_arm_scale_offset * .9

    cmds.setAttr(left_wrist_ctrl + '.scaleX', left_arm_scale_offset)
    cmds.setAttr(left_wrist_ctrl + '.scaleY', left_arm_scale_offset)
    cmds.setAttr(left_wrist_ctrl + '.scaleZ', left_arm_scale_offset)
    cmds.makeIdentity(left_wrist_ctrl, apply=True, scale=True)

    cmds.delete(cmds.parentConstraint(rig_joints.get('left_wrist_jnt'), left_wrist_ctrl_grp))

    add_orient_offset(left_wrist_ctrl, (0, 0, -90), apply=settings.get('uniform_ctrl_orient'))
    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(0, -90, -90, left_wrist_ctrl_grp, os=True, relative=True)

    change_viewport_color(left_wrist_ctrl, LEFT_CTRL_COLOR)
    cmds.parent(left_wrist_ctrl_grp, left_elbow_ctrl)

    # ################# Left Fingers FK #################
    # Left Fingers Parent
    left_hand_grp = cmds.group(name='left_hand_' + GRP_SUFFIX, empty=True, world=True)
    cmds.delete(cmds.parentConstraint(rig_joints.get('left_wrist_jnt'), left_hand_grp))
    cmds.parent(left_hand_grp, direction_ctrl)

    # Left Index Finger
    index_scale_offset = cmds.xform(rig_joints.get('left_index02_jnt'), q=True, t=True)[0]
    index_scale_offset += cmds.xform(rig_joints.get('left_index03_jnt'), q=True, t=True)[0]
    index_scale_offset += cmds.xform(rig_joints.get('left_index04_jnt'), q=True, t=True)[0]
    index_scale_offset = index_scale_offset / 3

    left_index01_ctrl_list = create_pin_control(rig_joints.get('left_index01_jnt'), index_scale_offset)
    left_index02_ctrl_list = create_pin_control(rig_joints.get('left_index02_jnt'), index_scale_offset)
    left_index03_ctrl_list = create_pin_control(rig_joints.get('left_index03_jnt'), index_scale_offset)

    cmds.parent(left_index01_ctrl_list[1], left_hand_grp)
    cmds.parent(left_index02_ctrl_list[1], left_index01_ctrl_list[0])
    cmds.parent(left_index03_ctrl_list[1], left_index02_ctrl_list[0])

    # Left Middle Finger
    middle_scale_offset = cmds.xform(rig_joints.get('left_middle02_jnt'), q=True, t=True)[0]
    middle_scale_offset += cmds.xform(rig_joints.get('left_middle03_jnt'), q=True, t=True)[0]
    middle_scale_offset += cmds.xform(rig_joints.get('left_middle04_jnt'), q=True, t=True)[0]
    middle_scale_offset = middle_scale_offset / 3

    left_middle01_ctrl_list = create_pin_control(rig_joints.get('left_middle01_jnt'), middle_scale_offset)
    left_middle02_ctrl_list = create_pin_control(rig_joints.get('left_middle02_jnt'), middle_scale_offset)
    left_middle03_ctrl_list = create_pin_control(rig_joints.get('left_middle03_jnt'), middle_scale_offset)

    cmds.parent(left_middle01_ctrl_list[1], left_hand_grp)
    cmds.parent(left_middle02_ctrl_list[1], left_middle01_ctrl_list[0])
    cmds.parent(left_middle03_ctrl_list[1], left_middle02_ctrl_list[0])

    # Left Ring Finger
    ring_scale_offset = cmds.xform(rig_joints.get('left_ring02_jnt'), q=True, t=True)[0]
    ring_scale_offset += cmds.xform(rig_joints.get('left_ring03_jnt'), q=True, t=True)[0]
    ring_scale_offset += cmds.xform(rig_joints.get('left_ring04_jnt'), q=True, t=True)[0]
    ring_scale_offset = ring_scale_offset / 3

    left_ring01_ctrl_list = create_pin_control(rig_joints.get('left_ring01_jnt'), ring_scale_offset)
    left_ring02_ctrl_list = create_pin_control(rig_joints.get('left_ring02_jnt'), ring_scale_offset)
    left_ring03_ctrl_list = create_pin_control(rig_joints.get('left_ring03_jnt'), ring_scale_offset)

    cmds.parent(left_ring01_ctrl_list[1], left_hand_grp)
    cmds.parent(left_ring02_ctrl_list[1], left_ring01_ctrl_list[0])
    cmds.parent(left_ring03_ctrl_list[1], left_ring02_ctrl_list[0])

    # Left Pinky Finger
    pinky_scale_offset = cmds.xform(rig_joints.get('left_pinky02_jnt'), q=True, t=True)[0]
    pinky_scale_offset += cmds.xform(rig_joints.get('left_pinky03_jnt'), q=True, t=True)[0]
    pinky_scale_offset += cmds.xform(rig_joints.get('left_pinky04_jnt'), q=True, t=True)[0]
    pinky_scale_offset = pinky_scale_offset / 3

    left_pinky01_ctrl_list = create_pin_control(rig_joints.get('left_pinky01_jnt'), pinky_scale_offset)
    left_pinky02_ctrl_list = create_pin_control(rig_joints.get('left_pinky02_jnt'), pinky_scale_offset)
    left_pinky03_ctrl_list = create_pin_control(rig_joints.get('left_pinky03_jnt'), pinky_scale_offset)

    cmds.parent(left_pinky01_ctrl_list[1], left_hand_grp)
    cmds.parent(left_pinky02_ctrl_list[1], left_pinky01_ctrl_list[0])
    cmds.parent(left_pinky03_ctrl_list[1], left_pinky02_ctrl_list[0])

    # Left Thumb Finger
    thumb_scale_offset = cmds.xform(rig_joints.get('left_thumb02_jnt'), q=True, t=True)[0]
    thumb_scale_offset += cmds.xform(rig_joints.get('left_thumb03_jnt'), q=True, t=True)[0]
    thumb_scale_offset += cmds.xform(rig_joints.get('left_thumb04_jnt'), q=True, t=True)[0]
    thumb_scale_offset = thumb_scale_offset / 3

    left_thumb01_ctrl_list = create_pin_control(rig_joints.get('left_thumb01_jnt'), thumb_scale_offset)
    left_thumb02_ctrl_list = create_pin_control(rig_joints.get('left_thumb02_jnt'), thumb_scale_offset)
    left_thumb03_ctrl_list = create_pin_control(rig_joints.get('left_thumb03_jnt'), thumb_scale_offset)

    cmds.parent(left_thumb01_ctrl_list[1], left_hand_grp)
    cmds.parent(left_thumb02_ctrl_list[1], left_thumb01_ctrl_list[0])
    cmds.parent(left_thumb03_ctrl_list[1], left_thumb02_ctrl_list[0])

    # Left Wrist IK
    left_wrist_ik_ctrl_a = cmds.curve(name=rig_joints.get('left_wrist_jnt').replace(JNT_SUFFIX, 'ik_') + CTRL_SUFFIX,
                                      p=[[0.267, -1.0, 0.0], [0.158, -1.0, 0.0], [0.158, -0.906, 0.0],
                                         [0.158, -0.524, 0.0], [0.158, 0.0, 0.0], [0.158, 0.523, -0.0],
                                         [0.158, 0.906, -0.0], [0.158, 1.0, -0.0], [0.267, 1.0, -0.0],
                                         [1.665, 1.0, -0.0], [2.409, 0.0, 0.0], [1.665, -1.0, 0.0], [0.267, -1.0, 0.0],
                                         [0.158, -1.0, 0.0], [0.158, -0.906, 0.0]], d=3, per=True,
                                      k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0,
                                         13.0, 14.0])
    left_wrist_ik_ctrl_b = cmds.curve(name=left_wrist_ik_ctrl_a + 'b',
                                      p=[[0.0, 0.0, 0.0], [0.157, 0.0, 0.0], [0.157, 0.743, 0.0], [0.19, 0.747, 0.0],
                                         [0.221, 0.76, 0.0], [0.248, 0.781, 0.0], [0.268, 0.807, 0.0],
                                         [0.281, 0.838, 0.0], [0.285, 0.871, 0.0], [0.157, 0.871, 0.0],
                                         [0.157, 0.743, 0.0], [0.124, 0.747, 0.0], [0.093, 0.76, 0.0],
                                         [0.066, 0.781, 0.0], [0.046, 0.807, 0.0], [0.033, 0.838, 0.0],
                                         [0.029, 0.871, 0.0], [0.033, 0.904, 0.0], [0.046, 0.935, 0.0],
                                         [0.066, 0.962, 0.0], [0.093, 0.982, 0.0], [0.124, 0.995, 0.0],
                                         [0.157, 0.999, 0.0], [0.19, 0.995, 0.0], [0.221, 0.982, 0.0],
                                         [0.248, 0.962, 0.0], [0.268, 0.935, 0.0], [0.281, 0.904, 0.0],
                                         [0.285, 0.871, 0.0], [0.029, 0.871, 0.0], [0.157, 0.871, 0.0],
                                         [0.157, 0.999, 0.0]], d=1)
    left_wrist_ik_ctrl_c = cmds.curve(
        p=[[0.0, 1.0, -0.351], [2.0, 1.0, -0.351], [2.0, -1.0, -0.351], [0.0, -1.0, -0.351], [0.0, 1.0, -0.351],
           [0.0, 1.0, 0.351], [0.0, -1.0, 0.351], [2.0, -1.0, 0.351], [2.0, 1.0, 0.351], [0.0, 1.0, 0.351],
           [2.0, 1.0, 0.351], [2.0, 1.0, -0.351], [2.0, -1.0, -0.351], [2.0, -1.0, 0.351], [0.0, -1.0, 0.351],
           [0.0, -1.0, -0.351]], d=1)
    left_wrist_ik_ctrl = combine_curves_list([left_wrist_ik_ctrl_a, left_wrist_ik_ctrl_b, left_wrist_ik_ctrl_c])

    shapes = cmds.listRelatives(left_wrist_ik_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format(rig_joints.get('left_wrist_jnt').replace(JNT_SUFFIX, 'semiCircle')))
    cmds.rename(shapes[1], '{0}Shape'.format(rig_joints.get('left_wrist_jnt').replace(JNT_SUFFIX, 'pin')))
    cmds.rename(shapes[2], '{0}Shape'.format(rig_joints.get('left_wrist_jnt').replace(JNT_SUFFIX, 'box')))

    left_wrist_ik_ctrl_grp = cmds.group(name=left_wrist_ik_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(left_wrist_ik_ctrl, left_wrist_ik_ctrl_grp)

    left_wrist_scale_offset = cmds.xform(rig_joints.get('left_middle01_jnt'), q=True, t=True)[0]
    left_wrist_scale_offset += cmds.xform(rig_joints.get('left_middle02_jnt'), q=True, t=True)[0]
    left_wrist_scale_offset += cmds.xform(rig_joints.get('left_middle03_jnt'), q=True, t=True)[0]
    left_wrist_scale_offset += cmds.xform(rig_joints.get('left_middle04_jnt'), q=True, t=True)[0]
    left_wrist_scale_offset = left_wrist_scale_offset / 2

    cmds.setAttr(left_wrist_ik_ctrl + '.scaleX', left_wrist_scale_offset)
    cmds.setAttr(left_wrist_ik_ctrl + '.scaleY', left_wrist_scale_offset)
    cmds.setAttr(left_wrist_ik_ctrl + '.scaleZ', left_wrist_scale_offset * .5)
    cmds.makeIdentity(left_wrist_ik_ctrl, apply=True, scale=True)

    if settings.get('worldspace_ik_orient'):
        cmds.delete(cmds.orientConstraint(rig_joints.get('left_wrist_jnt'), left_wrist_ik_ctrl))
        cmds.makeIdentity(left_wrist_ik_ctrl, apply=True, rotate=True)
        cmds.delete(cmds.pointConstraint(rig_joints.get('left_wrist_jnt'), left_wrist_ik_ctrl_grp))
    elif settings.get('uniform_ctrl_orient'):
        add_orient_offset(left_wrist_ik_ctrl, (-90, 0, 0))
        cmds.delete(cmds.parentConstraint(rig_joints.get('left_wrist_jnt'), left_wrist_ik_ctrl_grp))
        cmds.rotate(90, 0, 0, left_wrist_ik_ctrl_grp, os=True, relative=True)
    else:
        cmds.delete(cmds.parentConstraint(rig_joints.get('left_wrist_jnt'), left_wrist_ik_ctrl_grp))

    change_viewport_color(left_wrist_ik_ctrl, LEFT_CTRL_COLOR)
    cmds.parent(left_wrist_ik_ctrl_grp, direction_ctrl)

    # Add Separator (Control Behavior)
    cmds.addAttr(left_wrist_ik_ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
    cmds.setAttr(left_wrist_ik_ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)

    # Expose Custom Rotate Order
    cmds.addAttr(left_wrist_ik_ctrl, ln='rotationOrder', at='enum', en=ROTATE_ORDER_ENUM, keyable=True,
                 niceName='Rotate Order')
    cmds.connectAttr(left_wrist_ik_ctrl + '.rotationOrder', left_wrist_ik_ctrl + '.rotateOrder', f=True)

    # Left-Hand Ctrl Visibility Type
    setup_shape_switch(left_wrist_ik_ctrl)

    # Left Wrist In-Between Offset
    left_wrist_offset_ik_ctrl = left_wrist_ik_ctrl.replace('_' + CTRL_SUFFIX, '_offset' + CTRL_SUFFIX.capitalize())
    left_wrist_offset_ik_ctrl = cmds.duplicate(left_wrist_ik_ctrl, name=left_wrist_offset_ik_ctrl)[0]
    cmds.setAttr(left_wrist_offset_ik_ctrl + '.scaleX', .9)
    cmds.setAttr(left_wrist_offset_ik_ctrl + '.scaleY', .9)
    cmds.setAttr(left_wrist_offset_ik_ctrl + '.scaleZ', .9)
    cmds.makeIdentity(left_wrist_offset_ik_ctrl, apply=True, scale=True)
    change_viewport_color(left_wrist_offset_ik_ctrl, (.3, .6, 1))
    lock_hide_default_attr(left_wrist_offset_ik_ctrl, translate=False, rotate=False)
    # Recreate Connections
    cmds.connectAttr(left_wrist_offset_ik_ctrl + '.rotationOrder', left_wrist_offset_ik_ctrl + '.rotateOrder', f=True)
    setup_shape_switch(left_wrist_offset_ik_ctrl)
    cmds.parent(left_wrist_offset_ik_ctrl, left_wrist_ik_ctrl)

    left_wrist_offset_ik_ctrl_grp = cmds.group(name=left_wrist_offset_ik_ctrl + GRP_SUFFIX.capitalize(), empty=True,
                                               world=True)
    cmds.delete(cmds.parentConstraint(left_wrist_offset_ik_ctrl, left_wrist_offset_ik_ctrl_grp))
    cmds.parent(left_wrist_offset_ik_ctrl, left_wrist_offset_ik_ctrl_grp)
    cmds.parent(left_wrist_offset_ik_ctrl_grp, left_wrist_ik_ctrl)

    # Show Scale Ctrl
    cmds.addAttr(left_wrist_ik_ctrl, ln='showScaleCtrl', at='bool', keyable=True)

    cmds.addAttr(left_wrist_ik_ctrl, ln='showOffsetCtrl', at='bool', k=True)
    cmds.connectAttr(left_wrist_ik_ctrl + '.showOffsetCtrl', left_wrist_offset_ik_ctrl_grp + '.v', f=True)
    # #### End Wrist In-Between Offset

    # Left Elbow IK Pole Vector Ctrl
    left_elbow_ik_ctrl = cmds.curve(name=rig_joints.get('left_elbow_jnt').replace(JNT_SUFFIX, 'ik_') + CTRL_SUFFIX,
                                    p=[[-0.125, 0.0, 0.0], [0.125, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.125],
                                       [0.0, 0.0, -0.125], [0.0, 0.0, 0.0], [0.0, 0.125, 0.0], [0.0, -0.125, 0.0]], d=1)
    left_elbow_ik_ctrl_grp = cmds.group(name=left_elbow_ik_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(left_elbow_ik_ctrl, left_elbow_ik_ctrl_grp)

    for shape in cmds.listRelatives(left_elbow_ik_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(left_elbow_ik_ctrl))

    # Left Elbow Find Position
    left_arm_scale_offset = left_arm_scale_offset * .5
    temp_transform = cmds.group(name=left_elbow_ik_ctrl + '_rotExtraction', empty=True, world=True)
    cmds.delete(cmds.pointConstraint(elements.get('left_elbow_proxy_crv'), temp_transform))
    cmds.delete(cmds.aimConstraint(elements.get('left_elbow_pv_dir'), temp_transform, offset=(0, 0, 0),
                                   aimVector=(1, 0, 0), upVector=(0, -1, 0), worldUpType='vector',
                                   worldUpVector=(0, 1, 0)))
    cmds.move(left_arm_scale_offset * 1.2, 0, 0, temp_transform, os=True, relative=True)
    cmds.delete(cmds.pointConstraint(temp_transform, left_elbow_ik_ctrl_grp))
    cmds.delete(temp_transform)

    # Left Arm Pole Vec Visibility and Parenting
    cmds.setAttr(left_elbow_ik_ctrl + '.scaleX', left_arm_scale_offset)
    cmds.setAttr(left_elbow_ik_ctrl + '.scaleY', left_arm_scale_offset)
    cmds.setAttr(left_elbow_ik_ctrl + '.scaleZ', left_arm_scale_offset)
    cmds.makeIdentity(left_elbow_ik_ctrl, apply=True, scale=True)
    change_viewport_color(left_elbow_ik_ctrl, LEFT_CTRL_COLOR)
    cmds.parent(left_elbow_ik_ctrl_grp, direction_ctrl)

    # ################# Right Arm #################
    # Right Clavicle FK
    right_clavicle_ctrl = cmds.curve(name=rig_joints.get('right_clavicle_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                     p=[[0.0, 0.0, 0.0], [0.897, 1.554, 0.0], [0.959, 1.528, 0.0], [1.025, 1.52, 0.0],
                                        [1.091, 1.528, 0.0], [1.153, 1.554, 0.0], [1.206, 1.595, 0.0],
                                        [1.247, 1.647, 0.0], [1.025, 1.776, 0.0], [0.897, 1.554, 0.0],
                                        [0.844, 1.595, 0.0], [0.803, 1.648, 0.0], [0.778, 1.709, 0.0],
                                        [0.769, 1.776, 0.0], [0.778, 1.842, 0.0], [0.803, 1.904, 0.0],
                                        [0.844, 1.957, 0.0], [0.897, 1.997, 0.0], [0.959, 2.023, 0.0],
                                        [1.025, 2.032, 0.0], [1.091, 2.023, 0.0], [1.153, 1.998, 0.0],
                                        [1.206, 1.957, 0.0], [1.247, 1.904, 0.0], [1.273, 1.842, 0.0],
                                        [1.281, 1.776, 0.0], [1.272, 1.709, 0.0], [1.247, 1.647, 0.0],
                                        [0.803, 1.904, 0.0], [1.025, 1.776, 0.0], [1.153, 1.998, 0.0]], d=1)
    right_clavicle_ctrl_grp = cmds.group(name=right_clavicle_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)

    for shape in cmds.listRelatives(right_clavicle_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(right_clavicle_ctrl))

    # Right Clavicle Scale
    cmds.setAttr(right_clavicle_ctrl + '.scaleX', (general_scale_offset * .25) * -1)
    cmds.setAttr(right_clavicle_ctrl + '.scaleY', general_scale_offset * .25)
    cmds.setAttr(right_clavicle_ctrl + '.scaleZ', general_scale_offset * .25)
    cmds.makeIdentity(right_clavicle_ctrl, apply=True, scale=True)

    # Right Clavicle Position
    cmds.delete(cmds.parentConstraint(rig_joints.get('right_clavicle_jnt'), right_clavicle_ctrl_grp))
    cmds.delete(cmds.pointConstraint(rig_joints.get('right_clavicle_jnt'), right_clavicle_ctrl))
    cmds.parent(right_clavicle_ctrl, right_clavicle_ctrl_grp)
    cmds.makeIdentity(right_clavicle_ctrl, apply=True, rotate=True)

    if settings.get('uniform_ctrl_orient'):
        add_orient_offset(right_clavicle_ctrl, (-90, 0, 0))
        cmds.rotate(90, 0, 0, right_clavicle_ctrl_grp, os=True, relative=True)

    # Right Clavicle General Adjustments
    change_viewport_color(right_clavicle_ctrl, RIGHT_CTRL_COLOR)

    # Add Separator (Control Behavior)
    cmds.addAttr(right_clavicle_ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
    cmds.setAttr(right_clavicle_ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)

    # Expose Rotation Order
    cmds.addAttr(right_clavicle_ctrl, ln='rotationOrder', at='enum', en=ROTATE_ORDER_ENUM, keyable=True,
                 niceName='Rotate Order')
    cmds.connectAttr(right_clavicle_ctrl + '.rotationOrder', right_clavicle_ctrl + '.rotateOrder', f=True)

    # Right Shoulder FK
    right_shoulder_ctrl = cmds.curve(name=rig_joints.get('right_shoulder_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                     p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098],
                                        [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139],
                                        [-0.0, -0.098, 0.098], [-0.0, -0.139, 0.0], [-0.0, -0.098, -0.098],
                                        [0.0, -0.0, -0.139], [0.0, 0.098, -0.098]], d=3, per=True,
                                     k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    right_shoulder_ctrl_grp = cmds.group(name=right_shoulder_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(right_shoulder_ctrl, right_shoulder_ctrl_grp)

    for shape in cmds.listRelatives(right_shoulder_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(right_shoulder_ctrl))

    right_shoulder_scale_offset = cmds.xform(rig_joints.get('right_shoulder_jnt'), q=True, t=True)[0] * 6.5

    cmds.setAttr(right_shoulder_ctrl + '.scaleX', right_shoulder_scale_offset)
    cmds.setAttr(right_shoulder_ctrl + '.scaleY', right_shoulder_scale_offset)
    cmds.setAttr(right_shoulder_ctrl + '.scaleZ', right_shoulder_scale_offset)
    cmds.makeIdentity(right_shoulder_ctrl, apply=True, scale=True)

    cmds.delete(cmds.parentConstraint(rig_joints.get('right_shoulder_jnt'), right_shoulder_ctrl_grp))

    add_orient_offset(right_shoulder_ctrl, (0, 0, -90), apply=settings.get('uniform_ctrl_orient'))
    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(0, -90, -90, right_shoulder_ctrl_grp, os=True, relative=True)

    change_viewport_color(right_shoulder_ctrl, RIGHT_CTRL_COLOR)
    cmds.parent(right_shoulder_ctrl_grp, right_clavicle_ctrl)

    # Right Elbow FK
    right_elbow_ctrl = cmds.curve(name=rig_joints.get('right_elbow_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                  p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098],
                                     [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098],
                                     [-0.0, -0.139, 0.0], [-0.0, -0.098, -0.098], [0.0, -0.0, -0.139],
                                     [0.0, 0.098, -0.098]], d=3, per=True,
                                  k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    right_elbow_ctrl_grp = cmds.group(name=right_elbow_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(right_elbow_ctrl, right_elbow_ctrl_grp)

    for shape in cmds.listRelatives(right_elbow_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(right_elbow_ctrl))

    right_arm_scale_offset = dist_center_to_center(rig_joints.get('right_shoulder_jnt'),
                                                   rig_joints.get('right_elbow_jnt'))
    right_arm_scale_offset += dist_center_to_center(rig_joints.get('right_elbow_jnt'),
                                                    rig_joints.get('right_wrist_jnt'))
    right_arm_scale_offset = right_arm_scale_offset * 1.35

    cmds.setAttr(right_elbow_ctrl + '.scaleX', right_arm_scale_offset)
    cmds.setAttr(right_elbow_ctrl + '.scaleY', right_arm_scale_offset)
    cmds.setAttr(right_elbow_ctrl + '.scaleZ', right_arm_scale_offset)
    cmds.makeIdentity(right_elbow_ctrl, apply=True, scale=True)

    cmds.delete(cmds.parentConstraint(rig_joints.get('right_elbow_jnt'), right_elbow_ctrl_grp))

    add_orient_offset(right_elbow_ctrl, (0, 0, -90), apply=settings.get('uniform_ctrl_orient'))
    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(0, -90, -90, right_elbow_ctrl_grp, os=True, relative=True)

    change_viewport_color(right_elbow_ctrl, RIGHT_CTRL_COLOR)
    cmds.parent(right_elbow_ctrl_grp, right_shoulder_ctrl)

    # Right Wrist FK
    right_wrist_ctrl = cmds.curve(name=rig_joints.get('right_wrist_jnt').replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                  p=[[-0.0, -0.098, -0.098], [0.0, -0.0, -0.139], [0.0, 0.098, -0.098],
                                     [0.0, 0.139, -0.0], [0.0, 0.098, 0.098], [-0.0, 0.0, 0.139], [-0.0, -0.098, 0.098],
                                     [-0.0, -0.139, 0.0], [-0.0, -0.098, -0.098], [0.0, -0.0, -0.139],
                                     [0.0, 0.098, -0.098]], d=3, per=True,
                                  k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    right_wrist_ctrl_grp = cmds.group(name=right_wrist_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(right_wrist_ctrl, right_wrist_ctrl_grp)

    for shape in cmds.listRelatives(right_wrist_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(right_wrist_ctrl))

    right_arm_scale_offset = right_arm_scale_offset * .9

    cmds.setAttr(right_wrist_ctrl + '.scaleX', right_arm_scale_offset)
    cmds.setAttr(right_wrist_ctrl + '.scaleY', right_arm_scale_offset)
    cmds.setAttr(right_wrist_ctrl + '.scaleZ', right_arm_scale_offset)
    cmds.makeIdentity(right_wrist_ctrl, apply=True, scale=True)

    cmds.delete(cmds.parentConstraint(rig_joints.get('right_wrist_jnt'), right_wrist_ctrl_grp))

    add_orient_offset(right_wrist_ctrl, (0, 0, -90), apply=settings.get('uniform_ctrl_orient'))
    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(0, -90, -90, right_wrist_ctrl_grp, os=True, relative=True)

    change_viewport_color(right_wrist_ctrl, RIGHT_CTRL_COLOR)
    cmds.parent(right_wrist_ctrl_grp, right_elbow_ctrl)

    # ################# Right Fingers FK #################
    # Right Fingers Parent
    right_hand_grp = cmds.group(name='right_hand_' + GRP_SUFFIX, empty=True, world=True)
    cmds.delete(cmds.parentConstraint(rig_joints.get('right_wrist_jnt'), right_hand_grp))
    cmds.parent(right_hand_grp, direction_ctrl)

    # Right Index Finger
    index_scale_offset = cmds.xform(rig_joints.get('right_index02_jnt'), q=True, t=True)[0]
    index_scale_offset += cmds.xform(rig_joints.get('right_index03_jnt'), q=True, t=True)[0]
    index_scale_offset += cmds.xform(rig_joints.get('right_index04_jnt'), q=True, t=True)[0]
    index_scale_offset = index_scale_offset / 3

    right_index01_ctrl_list = create_pin_control(rig_joints.get('right_index01_jnt'), index_scale_offset)
    right_index02_ctrl_list = create_pin_control(rig_joints.get('right_index02_jnt'), index_scale_offset)
    right_index03_ctrl_list = create_pin_control(rig_joints.get('right_index03_jnt'), index_scale_offset)

    cmds.parent(right_index01_ctrl_list[1], right_hand_grp)
    cmds.parent(right_index02_ctrl_list[1], right_index01_ctrl_list[0])
    cmds.parent(right_index03_ctrl_list[1], right_index02_ctrl_list[0])

    # Right Middle Finger
    middle_scale_offset = cmds.xform(rig_joints.get('right_middle02_jnt'), q=True, t=True)[0]
    middle_scale_offset += cmds.xform(rig_joints.get('right_middle03_jnt'), q=True, t=True)[0]
    middle_scale_offset += cmds.xform(rig_joints.get('right_middle04_jnt'), q=True, t=True)[0]
    middle_scale_offset = middle_scale_offset / 3

    right_middle01_ctrl_list = create_pin_control(rig_joints.get('right_middle01_jnt'), middle_scale_offset)
    right_middle02_ctrl_list = create_pin_control(rig_joints.get('right_middle02_jnt'), middle_scale_offset)
    right_middle03_ctrl_list = create_pin_control(rig_joints.get('right_middle03_jnt'), middle_scale_offset)

    cmds.parent(right_middle01_ctrl_list[1], right_hand_grp)
    cmds.parent(right_middle02_ctrl_list[1], right_middle01_ctrl_list[0])
    cmds.parent(right_middle03_ctrl_list[1], right_middle02_ctrl_list[0])

    # Right Ring Finger
    ring_scale_offset = cmds.xform(rig_joints.get('right_ring02_jnt'), q=True, t=True)[0]
    ring_scale_offset += cmds.xform(rig_joints.get('right_ring03_jnt'), q=True, t=True)[0]
    ring_scale_offset += cmds.xform(rig_joints.get('right_ring04_jnt'), q=True, t=True)[0]
    ring_scale_offset = ring_scale_offset / 3

    right_ring01_ctrl_list = create_pin_control(rig_joints.get('right_ring01_jnt'), ring_scale_offset)
    right_ring02_ctrl_list = create_pin_control(rig_joints.get('right_ring02_jnt'), ring_scale_offset)
    right_ring03_ctrl_list = create_pin_control(rig_joints.get('right_ring03_jnt'), ring_scale_offset)

    cmds.parent(right_ring01_ctrl_list[1], right_hand_grp)
    cmds.parent(right_ring02_ctrl_list[1], right_ring01_ctrl_list[0])
    cmds.parent(right_ring03_ctrl_list[1], right_ring02_ctrl_list[0])

    # Right Pinky Finger
    pinky_scale_offset = cmds.xform(rig_joints.get('right_pinky02_jnt'), q=True, t=True)[0]
    pinky_scale_offset += cmds.xform(rig_joints.get('right_pinky03_jnt'), q=True, t=True)[0]
    pinky_scale_offset += cmds.xform(rig_joints.get('right_pinky04_jnt'), q=True, t=True)[0]
    pinky_scale_offset = pinky_scale_offset / 3

    right_pinky01_ctrl_list = create_pin_control(rig_joints.get('right_pinky01_jnt'), pinky_scale_offset)
    right_pinky02_ctrl_list = create_pin_control(rig_joints.get('right_pinky02_jnt'), pinky_scale_offset)
    right_pinky03_ctrl_list = create_pin_control(rig_joints.get('right_pinky03_jnt'), pinky_scale_offset)

    cmds.parent(right_pinky01_ctrl_list[1], right_hand_grp)
    cmds.parent(right_pinky02_ctrl_list[1], right_pinky01_ctrl_list[0])
    cmds.parent(right_pinky03_ctrl_list[1], right_pinky02_ctrl_list[0])

    # Right Thumb Finger
    thumb_scale_offset = cmds.xform(rig_joints.get('right_thumb02_jnt'), q=True, t=True)[0]
    thumb_scale_offset += cmds.xform(rig_joints.get('right_thumb03_jnt'), q=True, t=True)[0]
    thumb_scale_offset += cmds.xform(rig_joints.get('right_thumb04_jnt'), q=True, t=True)[0]
    thumb_scale_offset = thumb_scale_offset / 3

    right_thumb01_ctrl_list = create_pin_control(rig_joints.get('right_thumb01_jnt'), thumb_scale_offset)
    right_thumb02_ctrl_list = create_pin_control(rig_joints.get('right_thumb02_jnt'), thumb_scale_offset)
    right_thumb03_ctrl_list = create_pin_control(rig_joints.get('right_thumb03_jnt'), thumb_scale_offset)

    cmds.parent(right_thumb01_ctrl_list[1], right_hand_grp)
    cmds.parent(right_thumb02_ctrl_list[1], right_thumb01_ctrl_list[0])
    cmds.parent(right_thumb03_ctrl_list[1], right_thumb02_ctrl_list[0])

    # Right Wrist IK
    right_wrist_ik_ctrl_a = cmds.curve(name=rig_joints.get('right_wrist_jnt').replace(JNT_SUFFIX, 'ik_') + CTRL_SUFFIX,
                                       p=[[0.267, -1.0, 0.0], [0.158, -1.0, 0.0], [0.158, -0.906, 0.0],
                                          [0.158, -0.524, 0.0], [0.158, 0.0, 0.0], [0.158, 0.523, -0.0],
                                          [0.158, 0.906, -0.0], [0.158, 1.0, -0.0], [0.267, 1.0, -0.0],
                                          [1.665, 1.0, -0.0], [2.409, 0.0, 0.0], [1.665, -1.0, 0.0], [0.267, -1.0, 0.0],
                                          [0.158, -1.0, 0.0], [0.158, -0.906, 0.0]], d=3, per=True,
                                       k=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0,
                                          12.0, 13.0, 14.0])
    right_wrist_ik_ctrl_b = cmds.curve(name=right_wrist_ik_ctrl_a + 'b',
                                       p=[[0.0, 0.0, 0.0], [0.157, 0.0, 0.0], [0.157, 0.743, 0.0], [0.19, 0.747, 0.0],
                                          [0.221, 0.76, 0.0], [0.248, 0.781, 0.0], [0.268, 0.807, 0.0],
                                          [0.281, 0.838, 0.0], [0.285, 0.871, 0.0], [0.157, 0.871, 0.0],
                                          [0.157, 0.743, 0.0], [0.124, 0.747, 0.0], [0.093, 0.76, 0.0],
                                          [0.066, 0.781, 0.0], [0.046, 0.807, 0.0], [0.033, 0.838, 0.0],
                                          [0.029, 0.871, 0.0], [0.033, 0.904, 0.0], [0.046, 0.935, 0.0],
                                          [0.066, 0.962, 0.0], [0.093, 0.982, 0.0], [0.124, 0.995, 0.0],
                                          [0.157, 0.999, 0.0], [0.19, 0.995, 0.0], [0.221, 0.982, 0.0],
                                          [0.248, 0.962, 0.0], [0.268, 0.935, 0.0], [0.281, 0.904, 0.0],
                                          [0.285, 0.871, 0.0], [0.029, 0.871, 0.0], [0.157, 0.871, 0.0],
                                          [0.157, 0.999, 0.0]], d=1)
    right_wrist_ik_ctrl_c = cmds.curve(
        p=[[0.0, 1.0, -0.351], [2.0, 1.0, -0.351], [2.0, -1.0, -0.351], [0.0, -1.0, -0.351], [0.0, 1.0, -0.351],
           [0.0, 1.0, 0.351], [0.0, -1.0, 0.351], [2.0, -1.0, 0.351], [2.0, 1.0, 0.351], [0.0, 1.0, 0.351],
           [2.0, 1.0, 0.351], [2.0, 1.0, -0.351], [2.0, -1.0, -0.351], [2.0, -1.0, 0.351], [0.0, -1.0, 0.351],
           [0.0, -1.0, -0.351]], d=1)

    right_wrist_ik_ctrl = combine_curves_list([right_wrist_ik_ctrl_a, right_wrist_ik_ctrl_b, right_wrist_ik_ctrl_c])

    shapes = cmds.listRelatives(right_wrist_ik_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format(rig_joints.get('right_wrist_jnt').replace(JNT_SUFFIX, 'semiCircle')))
    cmds.rename(shapes[1], '{0}Shape'.format(rig_joints.get('right_wrist_jnt').replace(JNT_SUFFIX, 'pin')))
    cmds.rename(shapes[2], '{0}Shape'.format(rig_joints.get('right_wrist_jnt').replace(JNT_SUFFIX, 'box')))

    right_wrist_ik_ctrl_grp = cmds.group(name=right_wrist_ik_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(right_wrist_ik_ctrl, right_wrist_ik_ctrl_grp)

    right_wrist_scale_offset = abs(cmds.xform(rig_joints.get('right_middle01_jnt'), q=True, t=True)[0])
    right_wrist_scale_offset += abs(cmds.xform(rig_joints.get('right_middle02_jnt'), q=True, t=True)[0])
    right_wrist_scale_offset += abs(cmds.xform(rig_joints.get('right_middle03_jnt'), q=True, t=True)[0])
    right_wrist_scale_offset += abs(cmds.xform(rig_joints.get('right_middle04_jnt'), q=True, t=True)[0])
    right_wrist_scale_offset = right_wrist_scale_offset / 2

    if settings.get('uniform_ctrl_orient') and not settings.get('worldspace_ik_orient'):
        cmds.setAttr(right_wrist_ik_ctrl + '.scaleX', right_wrist_scale_offset * 1)
    else:
        cmds.setAttr(right_wrist_ik_ctrl + '.scaleX', right_wrist_scale_offset * -1)
    cmds.setAttr(right_wrist_ik_ctrl + '.scaleY', right_wrist_scale_offset * -1)
    cmds.setAttr(right_wrist_ik_ctrl + '.scaleZ', (right_wrist_scale_offset * -1) * .5)
    cmds.makeIdentity(right_wrist_ik_ctrl, apply=True, scale=True)

    if settings.get('worldspace_ik_orient'):
        cmds.delete(cmds.orientConstraint(rig_joints.get('right_wrist_jnt'), right_wrist_ik_ctrl))
        cmds.makeIdentity(right_wrist_ik_ctrl, apply=True, rotate=True)
        cmds.delete(cmds.pointConstraint(rig_joints.get('right_wrist_jnt'), right_wrist_ik_ctrl_grp))
    elif settings.get('uniform_ctrl_orient'):
        add_orient_offset(right_wrist_ik_ctrl, (-90, 0, 0))
        cmds.delete(cmds.parentConstraint(rig_joints.get('right_wrist_jnt'), right_wrist_ik_ctrl_grp))
        cmds.rotate(270, 0, 0, right_wrist_ik_ctrl_grp, os=True, relative=True)
        cmds.setAttr(right_wrist_ik_ctrl_grp + '.sx', -1)
    else:
        cmds.delete(cmds.parentConstraint(rig_joints.get('right_wrist_jnt'), right_wrist_ik_ctrl_grp))

    change_viewport_color(right_wrist_ik_ctrl, RIGHT_CTRL_COLOR)
    cmds.parent(right_wrist_ik_ctrl_grp, direction_ctrl)

    # Add Separator (Control Behavior)
    cmds.addAttr(right_wrist_ik_ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
    cmds.setAttr(right_wrist_ik_ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)

    # Expose Custom Rotate Order
    cmds.addAttr(right_wrist_ik_ctrl, ln='rotationOrder', at='enum', en=ROTATE_ORDER_ENUM, keyable=True,
                 niceName='Rotate Order')
    cmds.connectAttr(right_wrist_ik_ctrl + '.rotationOrder', right_wrist_ik_ctrl + '.rotateOrder', f=True)

    # Right-Hand Ctrl Visibility Type
    setup_shape_switch(right_wrist_ik_ctrl)

    # Right Wrist In-Between Offset
    right_wrist_offset_ik_ctrl = right_wrist_ik_ctrl.replace('_' + CTRL_SUFFIX, '_offset' + CTRL_SUFFIX.capitalize())
    right_wrist_offset_ik_ctrl = cmds.duplicate(right_wrist_ik_ctrl, name=right_wrist_offset_ik_ctrl)[0]
    cmds.setAttr(right_wrist_offset_ik_ctrl + '.scaleX', .9)
    cmds.setAttr(right_wrist_offset_ik_ctrl + '.scaleY', .9)
    cmds.setAttr(right_wrist_offset_ik_ctrl + '.scaleZ', .9)
    cmds.makeIdentity(right_wrist_offset_ik_ctrl, apply=True, scale=True)
    change_viewport_color(right_wrist_offset_ik_ctrl, (1, .3, .3))
    lock_hide_default_attr(right_wrist_offset_ik_ctrl, translate=False, rotate=False)
    # Recreate Connections
    cmds.connectAttr(right_wrist_offset_ik_ctrl + '.rotationOrder', right_wrist_offset_ik_ctrl + '.rotateOrder', f=True)
    setup_shape_switch(right_wrist_offset_ik_ctrl)
    cmds.parent(right_wrist_offset_ik_ctrl, right_wrist_ik_ctrl)

    right_wrist_offset_ik_ctrl_grp = cmds.group(name=right_wrist_offset_ik_ctrl + GRP_SUFFIX.capitalize(), empty=True,
                                                world=True)
    cmds.delete(cmds.parentConstraint(right_wrist_offset_ik_ctrl, right_wrist_offset_ik_ctrl_grp))
    cmds.parent(right_wrist_offset_ik_ctrl, right_wrist_offset_ik_ctrl_grp)
    cmds.parent(right_wrist_offset_ik_ctrl_grp, right_wrist_ik_ctrl)
    # Show Scale Ctrl
    cmds.addAttr(right_wrist_ik_ctrl, ln='showScaleCtrl', at='bool', keyable=True)

    cmds.addAttr(right_wrist_ik_ctrl, ln='showOffsetCtrl', at='bool', k=True)
    cmds.connectAttr(right_wrist_ik_ctrl + '.showOffsetCtrl', right_wrist_offset_ik_ctrl_grp + '.v', f=True)
    # Account for Inverted Scale
    cmds.setAttr(right_wrist_offset_ik_ctrl_grp + '.sz', 1)
    cmds.setAttr(right_wrist_offset_ik_ctrl + '.rz', 0)
    cmds.setAttr(right_wrist_offset_ik_ctrl_grp + '.rz', 0)

    right_wrist_offset_ik_ctrl_data = right_wrist_offset_ik_ctrl
    if settings.get('uniform_ctrl_orient') and not settings.get('worldspace_ik_orient'):
        right_wrist_offset_ik_ctrl_data = cmds.group(name=right_wrist_offset_ik_ctrl + 'Data', world=True, empty=True)
        cmds.parentConstraint(right_wrist_offset_ik_ctrl, right_wrist_offset_ik_ctrl_data)
        cmds.parent(right_wrist_offset_ik_ctrl_data, direction_ctrl)

    # #### End Wrist In-Between Offset

    # Right Elbow IK Pole Vector Ctrl
    right_elbow_ik_ctrl = cmds.curve(name=rig_joints.get('right_elbow_jnt').replace(JNT_SUFFIX, 'ik_') + CTRL_SUFFIX,
                                     p=[[-0.125, 0.0, 0.0], [0.125, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.125],
                                        [0.0, 0.0, -0.125], [0.0, 0.0, 0.0], [0.0, 0.125, 0.0], [0.0, -0.125, 0.0]],
                                     d=1)
    right_elbow_ik_ctrl_grp = cmds.group(name=right_elbow_ik_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(right_elbow_ik_ctrl, right_elbow_ik_ctrl_grp)

    for shape in cmds.listRelatives(right_elbow_ik_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(right_elbow_ik_ctrl))

    # Right Elbow Find Position
    right_arm_scale_offset = abs(right_arm_scale_offset) * .5
    temp_transform = cmds.group(name=right_elbow_ik_ctrl + '_rotExtraction', empty=True, world=True)
    cmds.delete(cmds.pointConstraint(elements.get('right_elbow_proxy_crv'), temp_transform))
    cmds.delete(cmds.aimConstraint(elements.get('right_elbow_pv_dir'), temp_transform, offset=(0, 0, 0),
                                   aimVector=(1, 0, 0), upVector=(0, 1, 0), worldUpType='vector',
                                   worldUpVector=(0, 1, 0)))
    cmds.move(right_arm_scale_offset * 1.2, 0, 0, temp_transform, os=True, relative=True)
    cmds.delete(cmds.pointConstraint(temp_transform, right_elbow_ik_ctrl_grp))
    cmds.delete(temp_transform)

    # Right Elbow Pole Vec Visibility and Parenting
    cmds.setAttr(right_elbow_ik_ctrl + '.scaleX', right_arm_scale_offset * 1)
    cmds.setAttr(right_elbow_ik_ctrl + '.scaleY', right_arm_scale_offset)
    cmds.setAttr(right_elbow_ik_ctrl + '.scaleZ', right_arm_scale_offset)
    cmds.makeIdentity(right_elbow_ik_ctrl, apply=True, scale=True)
    change_viewport_color(right_elbow_ik_ctrl, RIGHT_CTRL_COLOR)
    cmds.parent(right_elbow_ik_ctrl_grp, direction_ctrl)

    # IK/FK Switches
    # Left Arm
    left_arm_switch = cmds.curve(name='left_arm_switch_' + CTRL_SUFFIX,
                                 p=[[0.273, 0.0, -1.87], [0.273, -0.465, -2.568], [0.273, -0.233, -2.568],
                                    [0.273, -0.233, -3.295], [0.273, 0.233, -3.295], [0.273, 0.233, -2.568],
                                    [0.273, 0.465, -2.568], [0.273, 0.0, -1.87], [0.273, 0.0, -1.87],
                                    [0.738, 0.0, -2.568], [0.506, 0.0, -2.568], [0.506, 0.0, -3.295],
                                    [0.04, 0.0, -3.295], [0.04, 0.0, -2.568], [-0.192, 0.0, -2.568],
                                    [0.273, 0.0, -1.87]], d=1)
    left_arm_switch_a = cmds.curve(name='left_arm_fk_a_' + CTRL_SUFFIX,
                                   p=[[0.092, 0.0, -3.811], [0.092, 0.0, -3.591], [0.226, 0.0, -3.591],
                                      [0.226, 0.0, -3.802], [0.282, 0.0, -3.802], [0.282, 0.0, -3.591],
                                      [0.51, 0.0, -3.591], [0.51, 0.0, -3.528], [0.036, 0.0, -3.528],
                                      [0.036, 0.0, -3.811], [0.092, 0.0, -3.811], [0.092, 0.0, -3.591]], d=1)
    left_arm_switch_b = cmds.curve(name='left_arm_fk_b_' + CTRL_SUFFIX,
                                   p=[[0.51, 0.0, -4.212], [0.51, 0.0, -4.131], [0.289, 0.0, -3.958],
                                      [0.321, 0.0, -3.93], [0.51, 0.0, -3.93], [0.51, 0.0, -3.867],
                                      [0.036, 0.0, -3.867], [0.036, 0.0, -3.93], [0.254, 0.0, -3.93],
                                      [0.036, 0.0, -4.124], [0.036, 0.0, -4.201], [0.248, 0.0, -4.005],
                                      [0.51, 0.0, -4.212], [0.51, 0.0, -4.131]], d=1)
    left_arm_switch_c = cmds.curve(name='left_arm_ik_c_' + CTRL_SUFFIX,
                                   p=[[0.51, 0.0, -3.751], [0.51, 0.0, -3.567], [0.461, 0.0, -3.567],
                                      [0.461, 0.0, -3.627], [0.085, 0.0, -3.627], [0.085, 0.0, -3.567],
                                      [0.036, 0.0, -3.567], [0.036, 0.0, -3.751], [0.085, 0.0, -3.751],
                                      [0.085, 0.0, -3.69], [0.461, 0.0, -3.69], [0.461, 0.0, -3.751],
                                      [0.51, 0.0, -3.751], [0.51, 0.0, -3.567]], d=1)
    left_arm_switch_d = cmds.curve(name='left_arm_ik_d_' + CTRL_SUFFIX,
                                   p=[[0.51, 0.0, -4.173], [0.51, 0.0, -4.091], [0.289, 0.0, -3.919],
                                      [0.321, 0.0, -3.891], [0.51, 0.0, -3.891], [0.51, 0.0, -3.828],
                                      [0.036, 0.0, -3.828], [0.036, 0.0, -3.891], [0.254, 0.0, -3.891],
                                      [0.036, 0.0, -4.085], [0.036, 0.0, -4.162], [0.248, 0.0, -3.966],
                                      [0.51, 0.0, -4.173], [0.51, 0.0, -4.091]], d=1)

    for crv in [left_arm_switch, left_arm_switch_a, left_arm_switch_b, left_arm_switch_c, left_arm_switch_d]:
        cmds.setAttr(crv + '.scaleX', left_arm_scale_offset / 4)
        cmds.setAttr(crv + '.scaleY', left_arm_scale_offset / 4)
        cmds.setAttr(crv + '.scaleZ', left_arm_scale_offset / 4)
        cmds.makeIdentity(crv, apply=True, scale=True)

    left_arm_switch = combine_curves_list(
        [left_arm_switch, left_arm_switch_a, left_arm_switch_b, left_arm_switch_c, left_arm_switch_d])

    shapes = cmds.listRelatives(left_arm_switch, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format('arrow'))
    cmds.rename(shapes[1], '{0}Shape'.format('fk_f'))
    cmds.rename(shapes[2], '{0}Shape'.format('fk_k'))
    cmds.rename(shapes[3], '{0}Shape'.format('ik_i'))
    cmds.rename(shapes[4], '{0}Shape'.format('ik_k'))

    left_arm_switch_grp = cmds.group(name=left_arm_switch + '_' + GRP_SUFFIX, empty=True, world=True)
    cmds.parent(left_arm_switch, left_arm_switch_grp)

    change_viewport_color(left_arm_switch, LEFT_CTRL_COLOR)
    cmds.delete(cmds.parentConstraint(elements.get('left_wrist_proxy_crv'), left_arm_switch_grp))
    cmds.parent(left_arm_switch_grp, main_ctrl)

    # Right Arm
    right_arm_switch = cmds.curve(name='right_arm_switch_' + CTRL_SUFFIX,
                                  p=[[0.273, 0.0, -1.87], [0.273, -0.465, -2.568], [0.273, -0.233, -2.568],
                                     [0.273, -0.233, -3.295], [0.273, 0.233, -3.295], [0.273, 0.233, -2.568],
                                     [0.273, 0.465, -2.568], [0.273, 0.0, -1.87], [0.273, 0.0, -1.87],
                                     [0.738, 0.0, -2.568], [0.506, 0.0, -2.568], [0.506, 0.0, -3.295],
                                     [0.04, 0.0, -3.295], [0.04, 0.0, -2.568], [-0.192, 0.0, -2.568],
                                     [0.273, 0.0, -1.87]], d=1)
    right_arm_switch_a = cmds.curve(name='right_arm_fk_a_' + CTRL_SUFFIX,
                                    p=[[0.092, 0.0, -3.929], [0.092, 0.0, -4.149], [0.226, 0.0, -4.149],
                                       [0.226, 0.0, -3.938], [0.282, 0.0, -3.938], [0.282, 0.0, -4.149],
                                       [0.51, 0.0, -4.149], [0.51, 0.0, -4.212], [0.036, 0.0, -4.212],
                                       [0.036, 0.0, -3.929], [0.092, 0.0, -3.929], [0.092, 0.0, -4.149]], d=1)
    right_arm_switch_b = cmds.curve(name='right_arm_fk_b_' + CTRL_SUFFIX,
                                    p=[[0.51, -0.0, -3.467], [0.51, -0.0, -3.548], [0.289, -0.0, -3.721],
                                       [0.321, -0.0, -3.749], [0.51, -0.0, -3.749], [0.51, -0.0, -3.812],
                                       [0.036, 0.0, -3.812], [0.036, -0.0, -3.749], [0.254, -0.0, -3.749],
                                       [0.036, -0.0, -3.555], [0.036, -0.0, -3.478], [0.248, -0.0, -3.674],
                                       [0.51, -0.0, -3.467], [0.51, -0.0, -3.548]], d=1)
    right_arm_switch_c = cmds.curve(name='right_arm_ik_c_' + CTRL_SUFFIX,
                                    p=[[0.036, 0.0, -3.971], [0.036, 0.0, -4.155], [0.085, 0.0, -4.155],
                                       [0.085, 0.0, -4.095], [0.461, 0.0, -4.095], [0.461, 0.0, -4.155],
                                       [0.51, 0.0, -4.155], [0.51, 0.0, -3.971], [0.461, 0.0, -3.971],
                                       [0.461, 0.0, -4.032], [0.085, 0.0, -4.032], [0.085, 0.0, -3.971],
                                       [0.036, 0.0, -3.971], [0.036, 0.0, -4.155]], d=1)
    right_arm_switch_d = cmds.curve(name='right_arm_ik_d_' + CTRL_SUFFIX,
                                    p=[[0.036, -0.0, -3.535], [0.036, -0.0, -3.617], [0.257, -0.0, -3.789],
                                       [0.225, -0.0, -3.817], [0.036, -0.0, -3.817], [0.036, -0.0, -3.88],
                                       [0.51, 0.0, -3.88], [0.51, 0.0, -3.817], [0.292, -0.0, -3.817],
                                       [0.51, -0.0, -3.623], [0.51, -0.0, -3.546], [0.298, -0.0, -3.742],
                                       [0.036, -0.0, -3.535], [0.036, -0.0, -3.617]], d=1)

    for crv in [right_arm_switch, right_arm_switch_a, right_arm_switch_b, right_arm_switch_c, right_arm_switch_d]:
        cmds.setAttr(crv + '.scaleX', -right_arm_scale_offset / 4)
        cmds.setAttr(crv + '.scaleY', right_arm_scale_offset / 4)
        cmds.setAttr(crv + '.scaleZ', right_arm_scale_offset / 4)
        cmds.makeIdentity(crv, apply=True, scale=True)

    right_arm_switch = combine_curves_list(
        [right_arm_switch, right_arm_switch_a, right_arm_switch_b, right_arm_switch_c, right_arm_switch_d])

    shapes = cmds.listRelatives(right_arm_switch, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format('arrow'))
    cmds.rename(shapes[1], '{0}Shape'.format('fk_f'))
    cmds.rename(shapes[2], '{0}Shape'.format('fk_k'))
    cmds.rename(shapes[3], '{0}Shape'.format('ik_i'))
    cmds.rename(shapes[4], '{0}Shape'.format('ik_k'))

    right_arm_switch_grp = cmds.group(name=right_arm_switch + '_' + GRP_SUFFIX, empty=True, world=True)
    cmds.parent(right_arm_switch, right_arm_switch_grp)

    change_viewport_color(right_arm_switch, RIGHT_CTRL_COLOR)
    cmds.delete(cmds.parentConstraint(elements.get('right_wrist_proxy_crv'), right_arm_switch_grp))
    cmds.parent(right_arm_switch_grp, main_ctrl)

    # Left Leg
    left_leg_switch = cmds.curve(name='left_leg_switch_' + CTRL_SUFFIX,
                                 p=[[-0.0, 0.0, -1.87], [-0.0, -0.465, -2.568], [-0.0, -0.233, -2.568],
                                    [-0.0, -0.233, -3.295], [-0.0, 0.233, -3.295], [-0.0, 0.233, -2.568],
                                    [-0.0, 0.465, -2.568], [-0.0, 0.0, -1.87], [-0.0, 0.0, -1.87], [0.465, 0.0, -2.568],
                                    [0.233, 0.0, -2.568], [0.233, 0.0, -3.295], [-0.233, 0.0, -3.295],
                                    [-0.233, 0.0, -2.568], [-0.465, 0.0, -2.568], [-0.0, 0.0, -1.87]], d=1)
    left_leg_switch_a = cmds.curve(name='left_leg_fk_a_' + CTRL_SUFFIX,
                                   p=[[-0.181, 0.0, -3.811], [-0.181, 0.0, -3.591], [-0.047, 0.0, -3.591],
                                      [-0.047, 0.0, -3.802], [0.009, 0.0, -3.802], [0.009, 0.0, -3.591],
                                      [0.237, 0.0, -3.591], [0.237, 0.0, -3.528], [-0.237, 0.0, -3.528],
                                      [-0.237, 0.0, -3.811], [-0.181, 0.0, -3.811], [-0.181, 0.0, -3.591]], d=1)
    left_leg_switch_b = cmds.curve(name='left_leg_fk_b_' + CTRL_SUFFIX,
                                   p=[[0.237, 0.0, -4.212], [0.237, 0.0, -4.131], [0.016, 0.0, -3.958],
                                      [0.048, 0.0, -3.93], [0.237, 0.0, -3.93], [0.237, 0.0, -3.867],
                                      [-0.237, 0.0, -3.867], [-0.237, 0.0, -3.93], [-0.019, 0.0, -3.93],
                                      [-0.237, 0.0, -4.124], [-0.237, 0.0, -4.201], [-0.025, 0.0, -4.005],
                                      [0.237, 0.0, -4.212], [0.237, 0.0, -4.131]], d=1)
    left_leg_switch_c = cmds.curve(name='left_leg_ik_c_' + CTRL_SUFFIX,
                                   p=[[0.237, 0.0, -3.751], [0.237, 0.0, -3.567], [0.188, 0.0, -3.567],
                                      [0.188, 0.0, -3.627], [-0.188, 0.0, -3.627], [-0.188, 0.0, -3.567],
                                      [-0.237, 0.0, -3.567], [-0.237, 0.0, -3.751], [-0.188, 0.0, -3.751],
                                      [-0.188, 0.0, -3.69], [0.188, 0.0, -3.69], [0.188, 0.0, -3.751],
                                      [0.237, 0.0, -3.751], [0.237, 0.0, -3.567]], d=1)
    left_leg_switch_d = cmds.curve(name='left_leg_ik_d_' + CTRL_SUFFIX,
                                   p=[[0.237, 0.0, -4.173], [0.237, 0.0, -4.091], [0.016, 0.0, -3.919],
                                      [0.048, 0.0, -3.891], [0.237, 0.0, -3.891], [0.237, 0.0, -3.828],
                                      [-0.237, 0.0, -3.828], [-0.237, 0.0, -3.891], [-0.019, 0.0, -3.891],
                                      [-0.237, 0.0, -4.085], [-0.237, 0.0, -4.162], [-0.025, 0.0, -3.966],
                                      [0.237, 0.0, -4.173], [0.237, 0.0, -4.091]], d=1)

    for crv in [left_leg_switch, left_leg_switch_a, left_leg_switch_b, left_leg_switch_c, left_leg_switch_d]:
        cmds.setAttr(crv + '.scaleX', left_foot_scale_offset / 6.5)
        cmds.setAttr(crv + '.scaleY', left_foot_scale_offset / 6.5)
        cmds.setAttr(crv + '.scaleZ', left_foot_scale_offset / 6.5)
        cmds.makeIdentity(crv, apply=True, scale=True)

    left_leg_switch = combine_curves_list(
        [left_leg_switch, left_leg_switch_a, left_leg_switch_b, left_leg_switch_c, left_leg_switch_d])

    shapes = cmds.listRelatives(left_leg_switch, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format('arrow'))
    cmds.rename(shapes[1], '{0}Shape'.format('fk_f'))
    cmds.rename(shapes[2], '{0}Shape'.format('fk_k'))
    cmds.rename(shapes[3], '{0}Shape'.format('ik_i'))
    cmds.rename(shapes[4], '{0}Shape'.format('ik_k'))

    left_leg_switch_grp = cmds.group(name=left_leg_switch + '_' + GRP_SUFFIX, empty=True, world=True)
    cmds.parent(left_leg_switch, left_leg_switch_grp)

    change_viewport_color(left_leg_switch, LEFT_CTRL_COLOR)
    cmds.delete(cmds.pointConstraint(elements.get('left_ankle_proxy_crv'), left_leg_switch_grp))

    desired_rotation = cmds.xform(elements.get('left_ankle_proxy_crv'), q=True, ro=True)
    cmds.setAttr(left_leg_switch_grp + '.ry', desired_rotation[1])

    cmds.parent(left_leg_switch_grp, main_ctrl)

    # Right Leg
    right_leg_switch = cmds.curve(name='right_leg_switch_' + CTRL_SUFFIX,
                                  p=[[-0.0, 0.0, -1.87], [-0.0, -0.465, -2.568], [-0.0, -0.233, -2.568],
                                     [-0.0, -0.233, -3.295], [-0.0, 0.233, -3.295], [-0.0, 0.233, -2.568],
                                     [-0.0, 0.465, -2.568], [-0.0, 0.0, -1.87], [-0.0, 0.0, -1.87],
                                     [0.465, 0.0, -2.568], [0.233, 0.0, -2.568], [0.233, 0.0, -3.295],
                                     [-0.233, 0.0, -3.295], [-0.233, 0.0, -2.568], [-0.465, 0.0, -2.568],
                                     [-0.0, 0.0, -1.87]], d=1)
    right_leg_switch_a = cmds.curve(name='right_leg_fk_a_' + CTRL_SUFFIX,
                                    p=[[-0.181, 0.0, -3.929], [-0.181, 0.0, -4.149], [-0.047, 0.0, -4.149],
                                       [-0.047, 0.0, -3.938], [0.009, 0.0, -3.938], [0.009, 0.0, -4.149],
                                       [0.237, 0.0, -4.149], [0.237, 0.0, -4.212], [-0.237, 0.0, -4.212],
                                       [-0.237, 0.0, -3.929], [-0.181, 0.0, -3.929], [-0.181, 0.0, -4.149]], d=1)
    right_leg_switch_b = cmds.curve(name='right_leg_fk_b_' + CTRL_SUFFIX,
                                    p=[[0.237, -0.0, -3.467], [0.237, -0.0, -3.548], [0.016, -0.0, -3.721],
                                       [0.048, -0.0, -3.749], [0.237, -0.0, -3.749], [0.237, -0.0, -3.812],
                                       [-0.237, 0.0, -3.812], [-0.237, -0.0, -3.749], [-0.019, -0.0, -3.749],
                                       [-0.237, -0.0, -3.555], [-0.237, -0.0, -3.478], [-0.025, -0.0, -3.674],
                                       [0.237, -0.0, -3.467], [0.237, -0.0, -3.548]], d=1)
    right_leg_switch_c = cmds.curve(name='right_leg_ik_c_' + CTRL_SUFFIX,
                                    p=[[0.237, 0.0, -3.991], [0.237, 0.0, -4.175], [0.188, 0.0, -4.175],
                                       [0.188, 0.0, -4.115], [-0.188, 0.0, -4.115], [-0.188, 0.0, -4.175],
                                       [-0.237, 0.0, -4.175], [-0.237, 0.0, -3.991], [-0.188, 0.0, -3.991],
                                       [-0.188, 0.0, -4.052], [0.188, 0.0, -4.052], [0.188, 0.0, -3.991],
                                       [0.237, 0.0, -3.991], [0.237, 0.0, -4.175]], d=1)
    right_leg_switch_d = cmds.curve(name='right_leg_ik_d_' + CTRL_SUFFIX,
                                    p=[[0.237, -0.0, -3.554], [0.237, -0.0, -3.636], [0.016, -0.0, -3.808],
                                       [0.048, -0.0, -3.836], [0.237, -0.0, -3.836], [0.237, -0.0, -3.899],
                                       [-0.237, 0.0, -3.899], [-0.237, 0.0, -3.836], [-0.019, -0.0, -3.836],
                                       [-0.237, -0.0, -3.642], [-0.237, -0.0, -3.565], [-0.025, -0.0, -3.761],
                                       [0.237, -0.0, -3.554], [0.237, -0.0, -3.636]], d=1)

    for crv in [right_leg_switch, right_leg_switch_a, right_leg_switch_b, right_leg_switch_c, right_leg_switch_d]:
        cmds.setAttr(crv + '.scaleX', right_foot_scale_offset / 6.5)
        cmds.setAttr(crv + '.scaleY', right_foot_scale_offset / 6.5)
        cmds.setAttr(crv + '.scaleZ', -right_foot_scale_offset / 6.5)
        cmds.makeIdentity(crv, apply=True, scale=True)

    right_leg_switch = combine_curves_list(
        [right_leg_switch, right_leg_switch_a, right_leg_switch_b, right_leg_switch_c, right_leg_switch_d])

    shapes = cmds.listRelatives(right_leg_switch, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format('arrow'))
    cmds.rename(shapes[1], '{0}Shape'.format('fk_f'))
    cmds.rename(shapes[2], '{0}Shape'.format('fk_k'))
    cmds.rename(shapes[3], '{0}Shape'.format('ik_i'))
    cmds.rename(shapes[4], '{0}Shape'.format('ik_k'))

    right_leg_switch_grp = cmds.group(name=right_leg_switch + '_' + GRP_SUFFIX, empty=True, world=True)
    cmds.parent(right_leg_switch, right_leg_switch_grp)

    change_viewport_color(right_leg_switch, RIGHT_CTRL_COLOR)
    cmds.delete(cmds.pointConstraint(elements.get('right_ankle_proxy_crv'), right_leg_switch_grp))
    cmds.parent(right_leg_switch_grp, main_ctrl)

    # Left Foot Automation Controls
    # Left Toe Roll
    left_toe_roll_ctrl_a = cmds.curve(name='left_toeRoll_' + CTRL_SUFFIX,
                                      p=[[0.0, -0.095, 0.38], [0.035, -0.145, 0.354], [0.059, -0.177, 0.335],
                                         [0.092, -0.218, 0.312], [0.118, -0.248, 0.286], [0.152, -0.272, 0.254],
                                         [0.152, -0.272, 0.254], [0.152, -0.272, 0.254], [0.127, -0.279, 0.246],
                                         [0.127, -0.279, 0.246], [0.127, -0.279, 0.246], [0.127, -0.279, 0.246],
                                         [0.096, -0.259, 0.275], [0.068, -0.232, 0.3], [0.046, -0.201, 0.32],
                                         [0.046, -0.201, 0.32], [0.046, -0.201, 0.32], [0.046, -0.339, 0.2],
                                         [0.046, -0.387, -0.018], [0.046, -0.332, -0.173], [0.046, -0.265, -0.256],
                                         [0.046, -0.167, -0.332], [0.046, 0.0, -0.38], [0.046, 0.167, -0.332],
                                         [0.046, 0.265, -0.256], [0.046, 0.332, -0.173], [0.046, 0.387, -0.018],
                                         [0.046, 0.339, 0.2], [0.046, 0.201, 0.32], [0.046, 0.201, 0.32],
                                         [0.046, 0.201, 0.32], [0.068, 0.232, 0.3], [0.096, 0.259, 0.275],
                                         [0.127, 0.279, 0.246], [0.127, 0.279, 0.246], [0.127, 0.279, 0.246],
                                         [0.127, 0.279, 0.246], [0.152, 0.272, 0.254], [0.152, 0.272, 0.254],
                                         [0.152, 0.272, 0.254], [0.118, 0.248, 0.286], [0.092, 0.218, 0.312],
                                         [0.059, 0.177, 0.335], [0.035, 0.145, 0.354], [0.0, 0.095, 0.38]], d=3)
    left_toe_roll_ctrl_b = cmds.curve(
        p=[[-0.0, -0.095, 0.38], [-0.035, -0.145, 0.354], [-0.059, -0.177, 0.335], [-0.092, -0.218, 0.312],
           [-0.118, -0.248, 0.286], [-0.152, -0.272, 0.254], [-0.152, -0.272, 0.254], [-0.152, -0.272, 0.254],
           [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246],
           [-0.096, -0.259, 0.275], [-0.068, -0.232, 0.3], [-0.046, -0.201, 0.32], [-0.046, -0.201, 0.32],
           [-0.046, -0.201, 0.32], [-0.046, -0.339, 0.2], [-0.046, -0.387, -0.018], [-0.046, -0.332, -0.173],
           [-0.046, -0.265, -0.256], [-0.046, -0.167, -0.332], [-0.046, 0.0, -0.38], [-0.046, 0.167, -0.332],
           [-0.046, 0.265, -0.256], [-0.046, 0.332, -0.173], [-0.046, 0.387, -0.018], [-0.046, 0.339, 0.2],
           [-0.046, 0.201, 0.32], [-0.046, 0.201, 0.32], [-0.046, 0.201, 0.32], [-0.068, 0.232, 0.3],
           [-0.096, 0.259, 0.275], [-0.127, 0.279, 0.246], [-0.127, 0.279, 0.246], [-0.127, 0.279, 0.246],
           [-0.127, 0.279, 0.246], [-0.152, 0.272, 0.254], [-0.152, 0.272, 0.254], [-0.152, 0.272, 0.254],
           [-0.118, 0.248, 0.286], [-0.092, 0.218, 0.312], [-0.059, 0.177, 0.335], [-0.035, 0.145, 0.354],
           [-0.0, 0.095, 0.38]], d=3)
    left_toe_roll_ctrl = combine_curves_list([left_toe_roll_ctrl_a, left_toe_roll_ctrl_b])

    shapes = cmds.listRelatives(left_toe_roll_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format(left_toe_roll_ctrl + FIRST_SHAPE_SUFFIX))
    cmds.rename(shapes[1], '{0}Shape'.format(left_toe_roll_ctrl + SECOND_SHAPE_SUFFIX))

    left_toe_roll_ctrl_grp = cmds.group(name=left_toe_roll_ctrl + '_' + GRP_SUFFIX, empty=True, world=True)
    cmds.parent(left_toe_roll_ctrl, left_toe_roll_ctrl_grp)

    # Left Toe Roll Scale
    cmds.setAttr(left_toe_roll_ctrl_grp + '.scaleX', left_foot_scale_offset / 5)
    cmds.setAttr(left_toe_roll_ctrl_grp + '.scaleY', left_foot_scale_offset / 5)
    cmds.setAttr(left_toe_roll_ctrl_grp + '.scaleZ', left_foot_scale_offset / 5)
    cmds.makeIdentity(left_toe_roll_ctrl_grp, apply=True, scale=True)

    # Left Toe Position and Visibility
    cmds.delete(cmds.pointConstraint(rig_joints.get('left_toe_jnt'), left_toe_roll_ctrl_grp, skip='y'))
    desired_rotation = cmds.xform(elements.get('left_ankle_proxy_crv'), q=True, ro=True)
    cmds.setAttr(left_toe_roll_ctrl_grp + '.ry', desired_rotation[1])
    cmds.move(left_foot_scale_offset / 4, left_toe_roll_ctrl_grp, z=True, relative=True, objectSpace=True)

    change_viewport_color(left_toe_roll_ctrl, LEFT_CTRL_COLOR)
    cmds.parent(left_toe_roll_ctrl_grp, left_foot_offset_data_grp)

    # Left Toe Up/Down
    left_toe_up_down_ctrl = cmds.curve(name='left_toe_upDown_' + CTRL_SUFFIX,
                                       p=[[0.0, 0.351, 0.0], [0.0, 0.21, -0.14], [0.0, 0.21, -0.037],
                                          [-0.0, -0.21, -0.037], [-0.0, -0.21, -0.14], [-0.0, -0.351, 0.0],
                                          [-0.0, -0.21, 0.14], [-0.0, -0.21, 0.037], [0.0, 0.21, 0.037],
                                          [0.0, 0.21, 0.14], [0.0, 0.351, 0.0]], d=1)

    for shape in cmds.listRelatives(left_toe_up_down_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(left_toe_up_down_ctrl))

    left_toe_up_down_ctrl_grp = cmds.group(name=left_toe_up_down_ctrl + '_' + GRP_SUFFIX, empty=True, world=True)
    cmds.parent(left_toe_up_down_ctrl, left_toe_up_down_ctrl_grp)

    # Left Toe Roll Scale
    cmds.setAttr(left_toe_up_down_ctrl_grp + '.scaleX', left_foot_scale_offset / 5)
    cmds.setAttr(left_toe_up_down_ctrl_grp + '.scaleY', left_foot_scale_offset / 5)
    cmds.setAttr(left_toe_up_down_ctrl_grp + '.scaleZ', left_foot_scale_offset / 5)
    cmds.makeIdentity(left_toe_up_down_ctrl_grp, apply=True, scale=True)

    # Left Toe Position and Visibility
    cmds.delete(cmds.pointConstraint(rig_joints.get('left_toe_jnt'), left_toe_up_down_ctrl_grp, skip='y'))
    desired_rotation = cmds.xform(elements.get('left_ankle_proxy_crv'), q=True, ro=True)
    cmds.setAttr(left_toe_up_down_ctrl_grp + '.ry', desired_rotation[1])
    cmds.move(left_foot_scale_offset / 2.6, left_toe_up_down_ctrl_grp, z=True, relative=True, objectSpace=True)

    change_viewport_color(left_toe_up_down_ctrl, LEFT_CTRL_COLOR)
    cmds.parent(left_toe_up_down_ctrl_grp, left_foot_offset_data_grp)

    # Left Ball Roll
    left_ball_roll_ctrl_a = cmds.curve(name='left_ballRoll_' + CTRL_SUFFIX,
                                       p=[[0.0, -0.095, 0.38], [0.035, -0.145, 0.354], [0.059, -0.177, 0.335],
                                          [0.092, -0.218, 0.312], [0.118, -0.248, 0.286], [0.152, -0.272, 0.254],
                                          [0.152, -0.272, 0.254], [0.152, -0.272, 0.254], [0.127, -0.279, 0.246],
                                          [0.127, -0.279, 0.246], [0.127, -0.279, 0.246], [0.127, -0.279, 0.246],
                                          [0.096, -0.259, 0.275], [0.068, -0.232, 0.3], [0.046, -0.201, 0.32],
                                          [0.046, -0.201, 0.32], [0.046, -0.201, 0.32], [0.046, -0.339, 0.2],
                                          [0.046, -0.387, -0.018], [0.046, -0.332, -0.173], [0.046, -0.265, -0.256],
                                          [0.046, -0.167, -0.332], [0.046, 0.0, -0.38], [0.046, 0.167, -0.332],
                                          [0.046, 0.265, -0.256], [0.046, 0.332, -0.173], [0.046, 0.387, -0.018],
                                          [0.046, 0.339, 0.2], [0.046, 0.201, 0.32], [0.046, 0.201, 0.32],
                                          [0.046, 0.201, 0.32], [0.068, 0.232, 0.3], [0.096, 0.259, 0.275],
                                          [0.127, 0.279, 0.246], [0.127, 0.279, 0.246], [0.127, 0.279, 0.246],
                                          [0.127, 0.279, 0.246], [0.152, 0.272, 0.254], [0.152, 0.272, 0.254],
                                          [0.152, 0.272, 0.254], [0.118, 0.248, 0.286], [0.092, 0.218, 0.312],
                                          [0.059, 0.177, 0.335], [0.035, 0.145, 0.354], [0.0, 0.095, 0.38]], d=3)
    left_ball_roll_ctrl_b = cmds.curve(
        p=[[-0.0, -0.095, 0.38], [-0.035, -0.145, 0.354], [-0.059, -0.177, 0.335], [-0.092, -0.218, 0.312],
           [-0.118, -0.248, 0.286], [-0.152, -0.272, 0.254], [-0.152, -0.272, 0.254], [-0.152, -0.272, 0.254],
           [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246],
           [-0.096, -0.259, 0.275], [-0.068, -0.232, 0.3], [-0.046, -0.201, 0.32], [-0.046, -0.201, 0.32],
           [-0.046, -0.201, 0.32], [-0.046, -0.339, 0.2], [-0.046, -0.387, -0.018], [-0.046, -0.332, -0.173],
           [-0.046, -0.265, -0.256], [-0.046, -0.167, -0.332], [-0.046, 0.0, -0.38], [-0.046, 0.167, -0.332],
           [-0.046, 0.265, -0.256], [-0.046, 0.332, -0.173], [-0.046, 0.387, -0.018], [-0.046, 0.339, 0.2],
           [-0.046, 0.201, 0.32], [-0.046, 0.201, 0.32], [-0.046, 0.201, 0.32], [-0.068, 0.232, 0.3],
           [-0.096, 0.259, 0.275], [-0.127, 0.279, 0.246], [-0.127, 0.279, 0.246], [-0.127, 0.279, 0.246],
           [-0.127, 0.279, 0.246], [-0.152, 0.272, 0.254], [-0.152, 0.272, 0.254], [-0.152, 0.272, 0.254],
           [-0.118, 0.248, 0.286], [-0.092, 0.218, 0.312], [-0.059, 0.177, 0.335], [-0.035, 0.145, 0.354],
           [-0.0, 0.095, 0.38]], d=3)
    left_ball_roll_ctrl = combine_curves_list([left_ball_roll_ctrl_a, left_ball_roll_ctrl_b])

    shapes = cmds.listRelatives(left_ball_roll_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format(left_ball_roll_ctrl + FIRST_SHAPE_SUFFIX))
    cmds.rename(shapes[1], '{0}Shape'.format(left_ball_roll_ctrl + SECOND_SHAPE_SUFFIX))

    left_ball_roll_ctrl_grp = cmds.group(name=left_ball_roll_ctrl + '_' + GRP_SUFFIX, empty=True, world=True)
    cmds.parent(left_ball_roll_ctrl, left_ball_roll_ctrl_grp)

    # Left Ball Roll Scale
    cmds.setAttr(left_ball_roll_ctrl_grp + '.scaleX', left_foot_scale_offset / 6)
    cmds.setAttr(left_ball_roll_ctrl_grp + '.scaleY', left_foot_scale_offset / 6)
    cmds.setAttr(left_ball_roll_ctrl_grp + '.scaleZ', left_foot_scale_offset / 6)
    cmds.makeIdentity(left_ball_roll_ctrl_grp, apply=True, scale=True)

    # Left Ball Position and Visibility
    cmds.delete(cmds.pointConstraint(rig_joints.get('left_ball_jnt'), left_ball_roll_ctrl_grp, skip='y'))
    desired_rotation = cmds.xform(elements.get('left_ankle_proxy_crv'), q=True, ro=True)
    cmds.setAttr(left_ball_roll_ctrl_grp + '.ry', desired_rotation[1])
    cmds.move(left_foot_scale_offset / 3, left_ball_roll_ctrl_grp, x=True, relative=True, objectSpace=True)

    change_viewport_color(left_ball_roll_ctrl, LEFT_CTRL_COLOR)
    cmds.parent(left_ball_roll_ctrl_grp, left_foot_offset_data_grp)

    # Left Heel Roll
    left_heel_roll_ctrl_a = cmds.curve(name='left_heelRoll_' + CTRL_SUFFIX,
                                       p=[[0.0, 0.095, -0.38], [0.035, 0.145, -0.354], [0.059, 0.177, -0.335],
                                          [0.092, 0.218, -0.312], [0.118, 0.248, -0.286], [0.152, 0.272, -0.254],
                                          [0.152, 0.272, -0.254], [0.152, 0.272, -0.254], [0.127, 0.279, -0.246],
                                          [0.127, 0.279, -0.246], [0.127, 0.279, -0.246], [0.127, 0.279, -0.246],
                                          [0.096, 0.259, -0.275], [0.068, 0.232, -0.3], [0.046, 0.201, -0.32],
                                          [0.046, 0.201, -0.32], [0.046, 0.201, -0.32], [0.046, 0.339, -0.2],
                                          [0.046, 0.387, 0.018], [0.046, 0.332, 0.173], [0.046, 0.265, 0.256],
                                          [0.046, 0.167, 0.332], [0.046, -0.0, 0.38], [0.046, -0.167, 0.332],
                                          [0.046, -0.265, 0.256], [0.046, -0.332, 0.173], [0.046, -0.387, 0.018],
                                          [0.046, -0.339, -0.2], [0.046, -0.201, -0.32], [0.046, -0.201, -0.32],
                                          [0.046, -0.201, -0.32], [0.068, -0.232, -0.3], [0.096, -0.259, -0.275],
                                          [0.127, -0.279, -0.246], [0.127, -0.279, -0.246], [0.127, -0.279, -0.246],
                                          [0.127, -0.279, -0.246], [0.152, -0.272, -0.254], [0.152, -0.272, -0.254],
                                          [0.152, -0.272, -0.254], [0.118, -0.248, -0.286], [0.092, -0.218, -0.312],
                                          [0.059, -0.177, -0.335], [0.035, -0.145, -0.354], [0.0, -0.095, -0.38]], d=3)
    left_heel_roll_ctrl_b = cmds.curve(
        p=[[0.0, 0.095, -0.38], [-0.035, 0.145, -0.354], [-0.059, 0.177, -0.335], [-0.092, 0.218, -0.312],
           [-0.118, 0.248, -0.286], [-0.152, 0.272, -0.254], [-0.152, 0.272, -0.254], [-0.152, 0.272, -0.254],
           [-0.127, 0.279, -0.246], [-0.127, 0.279, -0.246], [-0.127, 0.279, -0.246], [-0.127, 0.279, -0.246],
           [-0.096, 0.259, -0.275], [-0.068, 0.232, -0.3], [-0.046, 0.201, -0.32], [-0.046, 0.201, -0.32],
           [-0.046, 0.201, -0.32], [-0.046, 0.339, -0.2], [-0.046, 0.387, 0.018], [-0.046, 0.332, 0.173],
           [-0.046, 0.265, 0.256], [-0.046, 0.167, 0.332], [-0.046, -0.0, 0.38], [-0.046, -0.167, 0.332],
           [-0.046, -0.265, 0.256], [-0.046, -0.332, 0.173], [-0.046, -0.387, 0.018], [-0.046, -0.339, -0.2],
           [-0.046, -0.201, -0.32], [-0.046, -0.201, -0.32], [-0.046, -0.201, -0.32], [-0.068, -0.232, -0.3],
           [-0.096, -0.259, -0.275], [-0.127, -0.279, -0.246], [-0.127, -0.279, -0.246], [-0.127, -0.279, -0.246],
           [-0.127, -0.279, -0.246], [-0.152, -0.272, -0.254], [-0.152, -0.272, -0.254], [-0.152, -0.272, -0.254],
           [-0.118, -0.248, -0.286], [-0.092, -0.218, -0.312], [-0.059, -0.177, -0.335], [-0.035, -0.145, -0.354],
           [0.0, -0.095, -0.38]], d=3)
    left_heel_roll_ctrl = combine_curves_list([left_heel_roll_ctrl_a, left_heel_roll_ctrl_b])

    shapes = cmds.listRelatives(left_heel_roll_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format(left_heel_roll_ctrl + FIRST_SHAPE_SUFFIX))
    cmds.rename(shapes[1], '{0}Shape'.format(left_heel_roll_ctrl + SECOND_SHAPE_SUFFIX))

    left_heel_roll_ctrl_grp = cmds.group(name=left_heel_roll_ctrl + '_' + GRP_SUFFIX, empty=True, world=True)
    cmds.parent(left_heel_roll_ctrl, left_heel_roll_ctrl_grp)

    # Left Heel Roll Scale
    cmds.setAttr(left_heel_roll_ctrl_grp + '.scaleX', left_foot_scale_offset / 6)
    cmds.setAttr(left_heel_roll_ctrl_grp + '.scaleY', left_foot_scale_offset / 6)
    cmds.setAttr(left_heel_roll_ctrl_grp + '.scaleZ', left_foot_scale_offset / 6)
    cmds.makeIdentity(left_heel_roll_ctrl_grp, apply=True, scale=True)

    # Left Heel Position and Visibility
    cmds.delete(cmds.pointConstraint(rig_joints.get('left_ankle_jnt'), left_heel_roll_ctrl_grp, skip='y'))
    desired_rotation = cmds.xform(elements.get('left_ankle_proxy_crv'), q=True, ro=True)
    cmds.setAttr(left_heel_roll_ctrl_grp + '.ry', desired_rotation[1])
    cmds.move(left_foot_scale_offset / 3.5 * -1, left_heel_roll_ctrl_grp, z=True, relative=True, objectSpace=True)

    change_viewport_color(left_heel_roll_ctrl, LEFT_CTRL_COLOR)
    cmds.parent(left_heel_roll_ctrl_grp, left_foot_offset_data_grp)

    # Right Foot Automation Controls
    # Right Toe Roll
    right_toe_roll_ctrl_a = cmds.curve(name='right_toeRoll_' + CTRL_SUFFIX,
                                       p=[[0.0, -0.095, 0.38], [0.035, -0.145, 0.354], [0.059, -0.177, 0.335],
                                          [0.092, -0.218, 0.312], [0.118, -0.248, 0.286], [0.152, -0.272, 0.254],
                                          [0.152, -0.272, 0.254], [0.152, -0.272, 0.254], [0.127, -0.279, 0.246],
                                          [0.127, -0.279, 0.246], [0.127, -0.279, 0.246], [0.127, -0.279, 0.246],
                                          [0.096, -0.259, 0.275], [0.068, -0.232, 0.3], [0.046, -0.201, 0.32],
                                          [0.046, -0.201, 0.32], [0.046, -0.201, 0.32], [0.046, -0.339, 0.2],
                                          [0.046, -0.387, -0.018], [0.046, -0.332, -0.173], [0.046, -0.265, -0.256],
                                          [0.046, -0.167, -0.332], [0.046, 0.0, -0.38], [0.046, 0.167, -0.332],
                                          [0.046, 0.265, -0.256], [0.046, 0.332, -0.173], [0.046, 0.387, -0.018],
                                          [0.046, 0.339, 0.2], [0.046, 0.201, 0.32], [0.046, 0.201, 0.32],
                                          [0.046, 0.201, 0.32], [0.068, 0.232, 0.3], [0.096, 0.259, 0.275],
                                          [0.127, 0.279, 0.246], [0.127, 0.279, 0.246], [0.127, 0.279, 0.246],
                                          [0.127, 0.279, 0.246], [0.152, 0.272, 0.254], [0.152, 0.272, 0.254],
                                          [0.152, 0.272, 0.254], [0.118, 0.248, 0.286], [0.092, 0.218, 0.312],
                                          [0.059, 0.177, 0.335], [0.035, 0.145, 0.354], [0.0, 0.095, 0.38]], d=3)
    right_toe_roll_ctrl_b = cmds.curve(
        p=[[-0.0, -0.095, 0.38], [-0.035, -0.145, 0.354], [-0.059, -0.177, 0.335], [-0.092, -0.218, 0.312],
           [-0.118, -0.248, 0.286], [-0.152, -0.272, 0.254], [-0.152, -0.272, 0.254], [-0.152, -0.272, 0.254],
           [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246],
           [-0.096, -0.259, 0.275], [-0.068, -0.232, 0.3], [-0.046, -0.201, 0.32], [-0.046, -0.201, 0.32],
           [-0.046, -0.201, 0.32], [-0.046, -0.339, 0.2], [-0.046, -0.387, -0.018], [-0.046, -0.332, -0.173],
           [-0.046, -0.265, -0.256], [-0.046, -0.167, -0.332], [-0.046, 0.0, -0.38], [-0.046, 0.167, -0.332],
           [-0.046, 0.265, -0.256], [-0.046, 0.332, -0.173], [-0.046, 0.387, -0.018], [-0.046, 0.339, 0.2],
           [-0.046, 0.201, 0.32], [-0.046, 0.201, 0.32], [-0.046, 0.201, 0.32], [-0.068, 0.232, 0.3],
           [-0.096, 0.259, 0.275], [-0.127, 0.279, 0.246], [-0.127, 0.279, 0.246], [-0.127, 0.279, 0.246],
           [-0.127, 0.279, 0.246], [-0.152, 0.272, 0.254], [-0.152, 0.272, 0.254], [-0.152, 0.272, 0.254],
           [-0.118, 0.248, 0.286], [-0.092, 0.218, 0.312], [-0.059, 0.177, 0.335], [-0.035, 0.145, 0.354],
           [-0.0, 0.095, 0.38]], d=3)
    right_toe_roll_ctrl = combine_curves_list([right_toe_roll_ctrl_a, right_toe_roll_ctrl_b])

    shapes = cmds.listRelatives(right_toe_roll_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format(right_toe_roll_ctrl + FIRST_SHAPE_SUFFIX))
    cmds.rename(shapes[1], '{0}Shape'.format(right_toe_roll_ctrl + SECOND_SHAPE_SUFFIX))

    # Match Right Side Look
    cmds.setAttr(right_toe_roll_ctrl + '.rotateY', -180)
    cmds.makeIdentity(right_toe_roll_ctrl, apply=True, rotate=True)

    right_toe_roll_ctrl_grp = cmds.group(name=right_toe_roll_ctrl + '_' + GRP_SUFFIX, empty=True, world=True)
    cmds.parent(right_toe_roll_ctrl, right_toe_roll_ctrl_grp)

    # Right Toe Roll Scale
    cmds.setAttr(right_toe_roll_ctrl_grp + '.scaleX', right_foot_scale_offset / 5)
    cmds.setAttr(right_toe_roll_ctrl_grp + '.scaleY', right_foot_scale_offset / 5)
    cmds.setAttr(right_toe_roll_ctrl_grp + '.scaleZ', right_foot_scale_offset / 5)
    cmds.makeIdentity(right_toe_roll_ctrl_grp, apply=True, scale=True)

    # Right Toe Position and Visibility
    cmds.delete(cmds.pointConstraint(rig_joints.get('right_toe_jnt'), right_toe_roll_ctrl_grp, skip='y'))
    desired_rotation = cmds.xform(elements.get('right_ankle_proxy_crv'), q=True, ro=True)
    cmds.setAttr(right_toe_roll_ctrl_grp + '.ry', desired_rotation[1])
    cmds.move(-right_foot_scale_offset / 4, right_toe_roll_ctrl_grp, z=True, relative=True, objectSpace=True)

    change_viewport_color(right_toe_roll_ctrl, RIGHT_CTRL_COLOR)
    cmds.parent(right_toe_roll_ctrl_grp, right_foot_offset_data_grp)

    # Right Toe Up/Down
    right_toe_up_down_ctrl = cmds.curve(name='right_toe_upDown_' + CTRL_SUFFIX,
                                        p=[[0.0, 0.351, 0.0], [0.0, 0.21, -0.14], [0.0, 0.21, -0.037],
                                           [-0.0, -0.21, -0.037], [-0.0, -0.21, -0.14], [-0.0, -0.351, 0.0],
                                           [-0.0, -0.21, 0.14], [-0.0, -0.21, 0.037], [0.0, 0.21, 0.037],
                                           [0.0, 0.21, 0.14], [0.0, 0.351, 0.0]], d=1)

    for shape in cmds.listRelatives(right_toe_up_down_ctrl, s=True, f=True) or []:
        cmds.rename(shape, '{0}Shape'.format(right_toe_up_down_ctrl))

    right_toe_up_down_ctrl_grp = cmds.group(name=right_toe_up_down_ctrl + '_' + GRP_SUFFIX, empty=True, world=True)
    cmds.parent(right_toe_up_down_ctrl, right_toe_up_down_ctrl_grp)

    # Right Toe Roll Scale
    cmds.setAttr(right_toe_up_down_ctrl_grp + '.scaleX', right_foot_scale_offset / 5)
    cmds.setAttr(right_toe_up_down_ctrl_grp + '.scaleY', right_foot_scale_offset / 5)
    cmds.setAttr(right_toe_up_down_ctrl_grp + '.scaleZ', right_foot_scale_offset / 5)
    cmds.makeIdentity(right_toe_up_down_ctrl_grp, apply=True, scale=True)

    # Right Toe Position and Visibility
    cmds.delete(cmds.pointConstraint(rig_joints.get('right_toe_jnt'), right_toe_up_down_ctrl_grp, skip='y'))
    desired_rotation = cmds.xform(elements.get('right_ankle_proxy_crv'), q=True, ro=True)
    cmds.setAttr(right_toe_up_down_ctrl_grp + '.ry', desired_rotation[1])
    cmds.move(-right_foot_scale_offset / 2.6, right_toe_up_down_ctrl_grp, z=True, relative=True, objectSpace=True)

    change_viewport_color(right_toe_up_down_ctrl, RIGHT_CTRL_COLOR)
    cmds.parent(right_toe_up_down_ctrl_grp, right_foot_offset_data_grp)

    # Right Ball Roll
    right_ball_roll_ctrl_a = cmds.curve(name='right_ballRoll_' + CTRL_SUFFIX,
                                        p=[[0.0, -0.095, 0.38], [0.035, -0.145, 0.354], [0.059, -0.177, 0.335],
                                           [0.092, -0.218, 0.312], [0.118, -0.248, 0.286], [0.152, -0.272, 0.254],
                                           [0.152, -0.272, 0.254], [0.152, -0.272, 0.254], [0.127, -0.279, 0.246],
                                           [0.127, -0.279, 0.246], [0.127, -0.279, 0.246], [0.127, -0.279, 0.246],
                                           [0.096, -0.259, 0.275], [0.068, -0.232, 0.3], [0.046, -0.201, 0.32],
                                           [0.046, -0.201, 0.32], [0.046, -0.201, 0.32], [0.046, -0.339, 0.2],
                                           [0.046, -0.387, -0.018], [0.046, -0.332, -0.173], [0.046, -0.265, -0.256],
                                           [0.046, -0.167, -0.332], [0.046, 0.0, -0.38], [0.046, 0.167, -0.332],
                                           [0.046, 0.265, -0.256], [0.046, 0.332, -0.173], [0.046, 0.387, -0.018],
                                           [0.046, 0.339, 0.2], [0.046, 0.201, 0.32], [0.046, 0.201, 0.32],
                                           [0.046, 0.201, 0.32], [0.068, 0.232, 0.3], [0.096, 0.259, 0.275],
                                           [0.127, 0.279, 0.246], [0.127, 0.279, 0.246], [0.127, 0.279, 0.246],
                                           [0.127, 0.279, 0.246], [0.152, 0.272, 0.254], [0.152, 0.272, 0.254],
                                           [0.152, 0.272, 0.254], [0.118, 0.248, 0.286], [0.092, 0.218, 0.312],
                                           [0.059, 0.177, 0.335], [0.035, 0.145, 0.354], [0.0, 0.095, 0.38]], d=3)
    right_ball_roll_ctrl_b = cmds.curve(
        p=[[-0.0, -0.095, 0.38], [-0.035, -0.145, 0.354], [-0.059, -0.177, 0.335], [-0.092, -0.218, 0.312],
           [-0.118, -0.248, 0.286], [-0.152, -0.272, 0.254], [-0.152, -0.272, 0.254], [-0.152, -0.272, 0.254],
           [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246], [-0.127, -0.279, 0.246],
           [-0.096, -0.259, 0.275], [-0.068, -0.232, 0.3], [-0.046, -0.201, 0.32], [-0.046, -0.201, 0.32],
           [-0.046, -0.201, 0.32], [-0.046, -0.339, 0.2], [-0.046, -0.387, -0.018], [-0.046, -0.332, -0.173],
           [-0.046, -0.265, -0.256], [-0.046, -0.167, -0.332], [-0.046, 0.0, -0.38], [-0.046, 0.167, -0.332],
           [-0.046, 0.265, -0.256], [-0.046, 0.332, -0.173], [-0.046, 0.387, -0.018], [-0.046, 0.339, 0.2],
           [-0.046, 0.201, 0.32], [-0.046, 0.201, 0.32], [-0.046, 0.201, 0.32], [-0.068, 0.232, 0.3],
           [-0.096, 0.259, 0.275], [-0.127, 0.279, 0.246], [-0.127, 0.279, 0.246], [-0.127, 0.279, 0.246],
           [-0.127, 0.279, 0.246], [-0.152, 0.272, 0.254], [-0.152, 0.272, 0.254], [-0.152, 0.272, 0.254],
           [-0.118, 0.248, 0.286], [-0.092, 0.218, 0.312], [-0.059, 0.177, 0.335], [-0.035, 0.145, 0.354],
           [-0.0, 0.095, 0.38]], d=3)
    right_ball_roll_ctrl = combine_curves_list([right_ball_roll_ctrl_a, right_ball_roll_ctrl_b])

    shapes = cmds.listRelatives(right_ball_roll_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format(right_ball_roll_ctrl + FIRST_SHAPE_SUFFIX))
    cmds.rename(shapes[1], '{0}Shape'.format(right_ball_roll_ctrl + SECOND_SHAPE_SUFFIX))

    # Match Right Side Look
    cmds.setAttr(right_ball_roll_ctrl + '.rotateY', -180)
    cmds.makeIdentity(right_ball_roll_ctrl, apply=True, rotate=True)

    right_ball_roll_ctrl_grp = cmds.group(name=right_ball_roll_ctrl + '_' + GRP_SUFFIX, empty=True, world=True)
    cmds.parent(right_ball_roll_ctrl, right_ball_roll_ctrl_grp)

    # Right Ball Roll Scale
    cmds.setAttr(right_ball_roll_ctrl_grp + '.scaleX', right_foot_scale_offset / 6)
    cmds.setAttr(right_ball_roll_ctrl_grp + '.scaleY', right_foot_scale_offset / 6)
    cmds.setAttr(right_ball_roll_ctrl_grp + '.scaleZ', right_foot_scale_offset / 6)
    cmds.makeIdentity(right_ball_roll_ctrl_grp, apply=True, scale=True)

    # Right Ball Position and Visibility
    cmds.delete(cmds.pointConstraint(rig_joints.get('right_ball_jnt'), right_ball_roll_ctrl_grp, skip='y'))
    desired_rotation = cmds.xform(elements.get('right_ankle_proxy_crv'), q=True, ro=True)
    cmds.setAttr(right_ball_roll_ctrl_grp + '.ry', desired_rotation[1])
    cmds.move(right_foot_scale_offset / 3, right_ball_roll_ctrl_grp, x=True, relative=True, objectSpace=True)

    change_viewport_color(right_ball_roll_ctrl, RIGHT_CTRL_COLOR)
    cmds.parent(right_ball_roll_ctrl_grp, right_foot_offset_data_grp)

    # Right Heel Roll
    right_heel_roll_ctrl_a = cmds.curve(name='right_heelRoll_' + CTRL_SUFFIX,
                                        p=[[0.0, 0.095, -0.38], [0.035, 0.145, -0.354], [0.059, 0.177, -0.335],
                                           [0.092, 0.218, -0.312], [0.118, 0.248, -0.286], [0.152, 0.272, -0.254],
                                           [0.152, 0.272, -0.254], [0.152, 0.272, -0.254], [0.127, 0.279, -0.246],
                                           [0.127, 0.279, -0.246], [0.127, 0.279, -0.246], [0.127, 0.279, -0.246],
                                           [0.096, 0.259, -0.275], [0.068, 0.232, -0.3], [0.046, 0.201, -0.32],
                                           [0.046, 0.201, -0.32], [0.046, 0.201, -0.32], [0.046, 0.339, -0.2],
                                           [0.046, 0.387, 0.018], [0.046, 0.332, 0.173], [0.046, 0.265, 0.256],
                                           [0.046, 0.167, 0.332], [0.046, -0.0, 0.38], [0.046, -0.167, 0.332],
                                           [0.046, -0.265, 0.256], [0.046, -0.332, 0.173], [0.046, -0.387, 0.018],
                                           [0.046, -0.339, -0.2], [0.046, -0.201, -0.32], [0.046, -0.201, -0.32],
                                           [0.046, -0.201, -0.32], [0.068, -0.232, -0.3], [0.096, -0.259, -0.275],
                                           [0.127, -0.279, -0.246], [0.127, -0.279, -0.246], [0.127, -0.279, -0.246],
                                           [0.127, -0.279, -0.246], [0.152, -0.272, -0.254], [0.152, -0.272, -0.254],
                                           [0.152, -0.272, -0.254], [0.118, -0.248, -0.286], [0.092, -0.218, -0.312],
                                           [0.059, -0.177, -0.335], [0.035, -0.145, -0.354], [0.0, -0.095, -0.38]], d=3)
    right_heel_roll_ctrl_b = cmds.curve(
        p=[[0.0, 0.095, -0.38], [-0.035, 0.145, -0.354], [-0.059, 0.177, -0.335], [-0.092, 0.218, -0.312],
           [-0.118, 0.248, -0.286], [-0.152, 0.272, -0.254], [-0.152, 0.272, -0.254], [-0.152, 0.272, -0.254],
           [-0.127, 0.279, -0.246], [-0.127, 0.279, -0.246], [-0.127, 0.279, -0.246], [-0.127, 0.279, -0.246],
           [-0.096, 0.259, -0.275], [-0.068, 0.232, -0.3], [-0.046, 0.201, -0.32], [-0.046, 0.201, -0.32],
           [-0.046, 0.201, -0.32], [-0.046, 0.339, -0.2], [-0.046, 0.387, 0.018], [-0.046, 0.332, 0.173],
           [-0.046, 0.265, 0.256], [-0.046, 0.167, 0.332], [-0.046, -0.0, 0.38], [-0.046, -0.167, 0.332],
           [-0.046, -0.265, 0.256], [-0.046, -0.332, 0.173], [-0.046, -0.387, 0.018], [-0.046, -0.339, -0.2],
           [-0.046, -0.201, -0.32], [-0.046, -0.201, -0.32], [-0.046, -0.201, -0.32], [-0.068, -0.232, -0.3],
           [-0.096, -0.259, -0.275], [-0.127, -0.279, -0.246], [-0.127, -0.279, -0.246], [-0.127, -0.279, -0.246],
           [-0.127, -0.279, -0.246], [-0.152, -0.272, -0.254], [-0.152, -0.272, -0.254], [-0.152, -0.272, -0.254],
           [-0.118, -0.248, -0.286], [-0.092, -0.218, -0.312], [-0.059, -0.177, -0.335], [-0.035, -0.145, -0.354],
           [0.0, -0.095, -0.38]], d=3)
    right_heel_roll_ctrl = combine_curves_list([right_heel_roll_ctrl_a, right_heel_roll_ctrl_b])

    shapes = cmds.listRelatives(right_heel_roll_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format(right_heel_roll_ctrl + FIRST_SHAPE_SUFFIX))
    cmds.rename(shapes[1], '{0}Shape'.format(right_heel_roll_ctrl + SECOND_SHAPE_SUFFIX))

    # Match Right Side Look
    cmds.setAttr(right_heel_roll_ctrl + '.rotateY', -180)
    cmds.makeIdentity(right_heel_roll_ctrl, apply=True, rotate=True)

    right_heel_roll_ctrl_grp = cmds.group(name=right_heel_roll_ctrl + '_' + GRP_SUFFIX, empty=True, world=True)
    cmds.parent(right_heel_roll_ctrl, right_heel_roll_ctrl_grp)

    # Right Heel Roll Scale
    cmds.setAttr(right_heel_roll_ctrl_grp + '.scaleX', right_foot_scale_offset / 6)
    cmds.setAttr(right_heel_roll_ctrl_grp + '.scaleY', right_foot_scale_offset / 6)
    cmds.setAttr(right_heel_roll_ctrl_grp + '.scaleZ', right_foot_scale_offset / 6)
    cmds.makeIdentity(right_heel_roll_ctrl_grp, apply=True, scale=True)

    # Right Heel Position and Visibility
    cmds.delete(cmds.pointConstraint(rig_joints.get('right_ankle_jnt'), right_heel_roll_ctrl_grp, skip='y'))
    desired_rotation = cmds.xform(elements.get('right_ankle_proxy_crv'), q=True, ro=True)
    cmds.setAttr(right_heel_roll_ctrl_grp + '.ry', desired_rotation[1])
    cmds.move(-right_foot_scale_offset / 3.5 * -1, right_heel_roll_ctrl_grp, z=True, relative=True, objectSpace=True)

    change_viewport_color(right_heel_roll_ctrl, RIGHT_CTRL_COLOR)
    cmds.parent(right_heel_roll_ctrl_grp, right_foot_offset_data_grp)

    # ####### Left Finger Automation Controls #######
    # Left Fingers
    left_fingers_ctrl_a = cmds.curve(name='left_fingers_' + CTRL_SUFFIX,
                                     p=[[0.0, 0.127, -0.509], [0.047, 0.194, -0.474], [0.079, 0.237, -0.449],
                                        [0.123, 0.292, -0.418], [0.158, 0.332, -0.383], [0.204, 0.364, -0.34],
                                        [0.204, 0.364, -0.34], [0.204, 0.364, -0.34], [0.17, 0.374, -0.33],
                                        [0.17, 0.374, -0.33], [0.17, 0.374, -0.33], [0.17, 0.374, -0.33],
                                        [0.129, 0.347, -0.368], [0.091, 0.311, -0.402], [0.062, 0.269, -0.429],
                                        [0.062, 0.269, -0.429], [0.062, 0.269, -0.429], [0.062, 0.454, -0.268],
                                        [0.062, 0.519, 0.024], [0.062, 0.445, 0.232], [0.062, 0.355, 0.343],
                                        [0.062, 0.224, 0.445], [0.062, 0.0, 0.509], [0.062, -0.224, 0.445],
                                        [0.062, -0.355, 0.343], [0.062, -0.445, 0.232], [0.062, -0.519, 0.024],
                                        [0.062, -0.454, -0.268], [0.062, -0.269, -0.429], [0.062, -0.269, -0.429],
                                        [0.062, -0.269, -0.429], [0.091, -0.311, -0.402], [0.129, -0.347, -0.368],
                                        [0.17, -0.374, -0.33], [0.17, -0.374, -0.33], [0.17, -0.374, -0.33],
                                        [0.17, -0.374, -0.33], [0.204, -0.364, -0.34], [0.204, -0.364, -0.34],
                                        [0.204, -0.364, -0.34], [0.158, -0.332, -0.383], [0.123, -0.292, -0.418],
                                        [0.079, -0.237, -0.449], [0.047, -0.194, -0.474], [0.0, -0.127, -0.509]], d=3)
    left_fingers_ctrl_b = cmds.curve(name=left_wrist_ik_ctrl_a + 'b',
                                     p=[[0.0, 0.127, -0.509], [-0.047, 0.194, -0.474], [-0.079, 0.237, -0.449],
                                        [-0.123, 0.292, -0.418], [-0.158, 0.332, -0.383], [-0.204, 0.364, -0.34],
                                        [-0.204, 0.364, -0.34], [-0.204, 0.364, -0.34], [-0.17, 0.374, -0.33],
                                        [-0.17, 0.374, -0.33], [-0.17, 0.374, -0.33], [-0.17, 0.374, -0.33],
                                        [-0.129, 0.347, -0.368], [-0.091, 0.311, -0.402], [-0.062, 0.269, -0.429],
                                        [-0.062, 0.269, -0.429], [-0.062, 0.269, -0.429], [-0.062, 0.454, -0.268],
                                        [-0.062, 0.519, 0.024], [-0.062, 0.445, 0.232], [-0.062, 0.355, 0.343],
                                        [-0.062, 0.224, 0.445], [-0.062, 0.0, 0.509], [-0.062, -0.224, 0.445],
                                        [-0.062, -0.355, 0.343], [-0.062, -0.445, 0.232], [-0.062, -0.519, 0.024],
                                        [-0.062, -0.454, -0.268], [-0.062, -0.269, -0.429], [-0.062, -0.269, -0.429],
                                        [-0.062, -0.269, -0.429], [-0.091, -0.311, -0.402], [-0.129, -0.347, -0.368],
                                        [-0.17, -0.374, -0.33], [-0.17, -0.374, -0.33], [-0.17, -0.374, -0.33],
                                        [-0.17, -0.374, -0.33], [-0.204, -0.364, -0.34], [-0.204, -0.364, -0.34],
                                        [-0.204, -0.364, -0.34], [-0.158, -0.332, -0.383], [-0.123, -0.292, -0.418],
                                        [-0.079, -0.237, -0.449], [-0.047, -0.194, -0.474], [0.0, -0.127, -0.509]], d=3)
    left_fingers_ctrl_c = cmds.curve(name=left_wrist_ik_ctrl_a + 'c',
                                     p=[[0.048, -0.0, 0.126], [0.073, 0.013, 0.139], [0.089, 0.023, 0.149],
                                        [0.109, 0.035, 0.16], [0.124, 0.046, 0.173], [0.136, 0.059, 0.189],
                                        [0.136, 0.059, 0.189], [0.136, 0.059, 0.189], [0.14, 0.049, 0.193],
                                        [0.14, 0.049, 0.193], [0.14, 0.049, 0.193], [0.14, 0.049, 0.193],
                                        [0.13, 0.037, 0.179], [0.116, 0.026, 0.166], [0.101, 0.018, 0.156],
                                        [0.101, 0.018, 0.156], [0.101, 0.018, 0.156], [0.17, 0.018, 0.216],
                                        [0.194, 0.018, 0.325], [0.166, 0.018, 0.403], [0.133, 0.018, 0.444],
                                        [0.084, 0.018, 0.482], [0.0, 0.018, 0.506], [-0.084, 0.018, 0.482],
                                        [-0.133, 0.018, 0.444], [-0.166, 0.018, 0.403], [-0.194, 0.018, 0.325],
                                        [-0.17, 0.018, 0.216], [-0.101, 0.018, 0.156], [-0.101, 0.018, 0.156],
                                        [-0.101, 0.018, 0.156], [-0.116, 0.026, 0.166], [-0.13, 0.037, 0.179],
                                        [-0.14, 0.049, 0.193], [-0.14, 0.049, 0.193], [-0.14, 0.049, 0.193],
                                        [-0.14, 0.049, 0.193], [-0.136, 0.059, 0.189], [-0.136, 0.059, 0.189],
                                        [-0.136, 0.059, 0.189], [-0.124, 0.046, 0.173], [-0.109, 0.035, 0.16],
                                        [-0.089, 0.023, 0.149], [-0.073, 0.013, 0.139], [-0.048, 0.0, 0.126]], d=3)
    left_fingers_ctrl_d = cmds.curve(name=left_wrist_ik_ctrl_a + 'd',
                                     p=[[0.048, -0.0, 0.126], [0.073, -0.013, 0.139], [0.089, -0.023, 0.149],
                                        [0.109, -0.035, 0.16], [0.124, -0.046, 0.173], [0.136, -0.059, 0.189],
                                        [0.136, -0.059, 0.189], [0.136, -0.059, 0.189], [0.14, -0.049, 0.193],
                                        [0.14, -0.049, 0.193], [0.14, -0.049, 0.193], [0.14, -0.049, 0.193],
                                        [0.13, -0.037, 0.179], [0.116, -0.026, 0.166], [0.101, -0.018, 0.156],
                                        [0.101, -0.018, 0.156], [0.101, -0.018, 0.156], [0.17, -0.018, 0.216],
                                        [0.194, -0.018, 0.325], [0.166, -0.018, 0.403], [0.133, -0.018, 0.444],
                                        [0.084, -0.018, 0.482], [-0.0, -0.018, 0.506], [-0.084, -0.018, 0.482],
                                        [-0.133, -0.018, 0.444], [-0.166, -0.018, 0.403], [-0.194, -0.018, 0.325],
                                        [-0.17, -0.018, 0.216], [-0.101, -0.018, 0.156], [-0.101, -0.018, 0.156],
                                        [-0.101, -0.018, 0.156], [-0.116, -0.026, 0.166], [-0.13, -0.037, 0.179],
                                        [-0.14, -0.049, 0.193], [-0.14, -0.049, 0.193], [-0.14, -0.049, 0.193],
                                        [-0.14, -0.049, 0.193], [-0.136, -0.059, 0.189], [-0.136, -0.059, 0.189],
                                        [-0.136, -0.059, 0.189], [-0.124, -0.046, 0.173], [-0.109, -0.035, 0.16],
                                        [-0.089, -0.023, 0.149], [-0.073, -0.013, 0.139], [-0.048, 0.0, 0.126]], d=3)

    left_fingers_ctrl = combine_curves_list(
        [left_fingers_ctrl_a, left_fingers_ctrl_b, left_fingers_ctrl_c, left_fingers_ctrl_d])

    shapes = cmds.listRelatives(left_fingers_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format('big_arrow_l'))
    cmds.rename(shapes[1], '{0}Shape'.format('big_arrow_r'))
    cmds.rename(shapes[2], '{0}Shape'.format('small_arrow_u'))
    cmds.rename(shapes[3], '{0}Shape'.format('small_arrow_d'))

    left_fingers_ctrl_grp = cmds.group(name=left_fingers_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(left_fingers_ctrl, left_fingers_ctrl_grp)

    cmds.setAttr(left_fingers_ctrl + '.rotateY', -90)
    cmds.setAttr(left_fingers_ctrl + '.scaleX', left_wrist_scale_offset * .3)
    cmds.setAttr(left_fingers_ctrl + '.scaleY', left_wrist_scale_offset * .3)
    cmds.setAttr(left_fingers_ctrl + '.scaleZ', left_wrist_scale_offset * .3)
    cmds.makeIdentity(left_fingers_ctrl, apply=True, scale=True, rotate=True)

    # Create Abduction Finger Setup
    left_fingers_abduction_ctrl = create_scalable_arrow('left_open_finger_' + CTRL_SUFFIX, left_wrist_scale_offset * .1)
    cmds.parent(left_fingers_abduction_ctrl[0], left_fingers_ctrl_grp)
    cmds.setAttr(left_fingers_abduction_ctrl[0] + '.overrideEnabled', 1)
    cmds.setAttr(left_fingers_abduction_ctrl[0] + '.overrideDisplayType', 1)

    # ############ Left Fingers Control Behavior Attributes ############
    cmds.addAttr(left_fingers_ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
    cmds.setAttr(left_fingers_ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)

    # Right Fingers Curl Visibility (Attributes)
    cmds.addAttr(left_fingers_ctrl, ln='showCurlControls', at='bool', k=True)
    cmds.addAttr(left_fingers_ctrl, ln='showFkFingerCtrls', at='bool', k=True, niceName='Show FK Finger Ctrls')

    # Right Fingers Limits (Attributes)
    cmds.addAttr(left_fingers_ctrl, ln='maximumRotationZ', at='double', k=True)
    cmds.setAttr(left_fingers_ctrl + '.maximumRotationZ', 10)
    cmds.addAttr(left_fingers_ctrl, ln='minimumRotationZ', at='double', k=True)
    cmds.setAttr(left_fingers_ctrl + '.minimumRotationZ', -130)

    cmds.addAttr(left_fingers_ctrl, ln='rotateShape', at='bool', k=True)
    cmds.setAttr(left_fingers_ctrl + '.rotateShape', 1)

    cmds.setAttr(left_fingers_ctrl + '.maxRotZLimitEnable', 1)
    cmds.setAttr(left_fingers_ctrl + '.minRotZLimitEnable', 1)

    # Curl Controls
    distance_from_parent = .4
    left_curl_thumb_ctrl = create_finger_curl_ctrl('left_thumbCurl_' + CTRL_SUFFIX, left_fingers_ctrl_grp,
                                                   left_wrist_scale_offset, distance_from_parent, .55)
    left_curl_thumb_ctrl_grp = cmds.group(name=left_curl_thumb_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.delete(cmds.parentConstraint(left_curl_thumb_ctrl, left_curl_thumb_ctrl_grp))
    cmds.parent(left_curl_thumb_ctrl, left_curl_thumb_ctrl_grp)
    cmds.setAttr(left_curl_thumb_ctrl_grp + '.rotateY', -90)
    cmds.parent(left_curl_thumb_ctrl_grp, left_fingers_ctrl_grp)

    left_curl_index_ctrl = create_finger_curl_ctrl('left_indexCurl_' + CTRL_SUFFIX, left_fingers_ctrl_grp,
                                                   left_wrist_scale_offset, distance_from_parent, .35)
    left_curl_middle_ctrl = create_finger_curl_ctrl('left_middleCurl_' + CTRL_SUFFIX, left_fingers_ctrl_grp,
                                                    left_wrist_scale_offset, distance_from_parent, .15)
    left_curl_ring_ctrl = create_finger_curl_ctrl('left_ringCurl_' + CTRL_SUFFIX, left_fingers_ctrl_grp,
                                                  left_wrist_scale_offset, distance_from_parent, -.05)
    left_curl_pinky_ctrl = create_finger_curl_ctrl('left_pinkyCurl_' + CTRL_SUFFIX, left_fingers_ctrl_grp,
                                                   left_wrist_scale_offset, distance_from_parent, -.25)
    left_curl_controls = [left_curl_thumb_ctrl, left_curl_index_ctrl, left_curl_middle_ctrl, left_curl_ring_ctrl,
                          left_curl_pinky_ctrl]

    for curl_ctrl in left_curl_controls:
        change_viewport_color(curl_ctrl, (LEFT_CTRL_COLOR[0] * 1.3, LEFT_CTRL_COLOR[1] * 1.3, LEFT_CTRL_COLOR[2] * 1.3))
        cmds.setAttr(curl_ctrl + '.tx', lock=True, keyable=False)
        cmds.setAttr(curl_ctrl + '.ty', lock=True, keyable=False)
        cmds.setAttr(curl_ctrl + '.tz', lock=True, keyable=False)
        cmds.setAttr(curl_ctrl + '.rx', lock=True, keyable=False)
        cmds.setAttr(curl_ctrl + '.ry', lock=True, keyable=False)
        cmds.setAttr(curl_ctrl + '.sx', lock=True, keyable=False)
        cmds.setAttr(curl_ctrl + '.sy', lock=True, keyable=False)
        cmds.setAttr(curl_ctrl + '.sz', lock=True, keyable=False)
        cmds.setAttr(curl_ctrl + '.v', lock=True, keyable=False)

    # Position
    cmds.delete(cmds.parentConstraint(rig_joints.get('left_wrist_jnt'), left_fingers_ctrl_grp))
    cmds.move(left_wrist_scale_offset * 2.3, left_fingers_ctrl_grp, x=True, relative=True, objectSpace=True)
    cmds.setAttr(left_fingers_ctrl_grp + '.rotateX', 0)

    # Hierarchy
    change_viewport_color(left_fingers_ctrl, LEFT_CTRL_COLOR)
    cmds.parent(left_fingers_ctrl_grp, left_hand_grp)

    # Right Finger Automation Controls
    # Right Fingers
    right_fingers_ctrl_a = cmds.curve(name='right_fingers_' + CTRL_SUFFIX,
                                      p=[[0.0, 0.127, -0.509], [0.047, 0.194, -0.474], [0.079, 0.237, -0.449],
                                         [0.123, 0.292, -0.418], [0.158, 0.332, -0.383], [0.204, 0.364, -0.34],
                                         [0.204, 0.364, -0.34], [0.204, 0.364, -0.34], [0.17, 0.374, -0.33],
                                         [0.17, 0.374, -0.33], [0.17, 0.374, -0.33], [0.17, 0.374, -0.33],
                                         [0.129, 0.347, -0.368], [0.091, 0.311, -0.402], [0.062, 0.269, -0.429],
                                         [0.062, 0.269, -0.429], [0.062, 0.269, -0.429], [0.062, 0.454, -0.268],
                                         [0.062, 0.519, 0.024], [0.062, 0.445, 0.232], [0.062, 0.355, 0.343],
                                         [0.062, 0.224, 0.445], [0.062, 0.0, 0.509], [0.062, -0.224, 0.445],
                                         [0.062, -0.355, 0.343], [0.062, -0.445, 0.232], [0.062, -0.519, 0.024],
                                         [0.062, -0.454, -0.268], [0.062, -0.269, -0.429], [0.062, -0.269, -0.429],
                                         [0.062, -0.269, -0.429], [0.091, -0.311, -0.402], [0.129, -0.347, -0.368],
                                         [0.17, -0.374, -0.33], [0.17, -0.374, -0.33], [0.17, -0.374, -0.33],
                                         [0.17, -0.374, -0.33], [0.204, -0.364, -0.34], [0.204, -0.364, -0.34],
                                         [0.204, -0.364, -0.34], [0.158, -0.332, -0.383], [0.123, -0.292, -0.418],
                                         [0.079, -0.237, -0.449], [0.047, -0.194, -0.474], [0.0, -0.127, -0.509]], d=3)
    right_fingers_ctrl_b = cmds.curve(name=right_wrist_ik_ctrl_a + 'b',
                                      p=[[0.0, 0.127, -0.509], [-0.047, 0.194, -0.474], [-0.079, 0.237, -0.449],
                                         [-0.123, 0.292, -0.418], [-0.158, 0.332, -0.383], [-0.204, 0.364, -0.34],
                                         [-0.204, 0.364, -0.34], [-0.204, 0.364, -0.34], [-0.17, 0.374, -0.33],
                                         [-0.17, 0.374, -0.33], [-0.17, 0.374, -0.33], [-0.17, 0.374, -0.33],
                                         [-0.129, 0.347, -0.368], [-0.091, 0.311, -0.402], [-0.062, 0.269, -0.429],
                                         [-0.062, 0.269, -0.429], [-0.062, 0.269, -0.429], [-0.062, 0.454, -0.268],
                                         [-0.062, 0.519, 0.024], [-0.062, 0.445, 0.232], [-0.062, 0.355, 0.343],
                                         [-0.062, 0.224, 0.445], [-0.062, 0.0, 0.509], [-0.062, -0.224, 0.445],
                                         [-0.062, -0.355, 0.343], [-0.062, -0.445, 0.232], [-0.062, -0.519, 0.024],
                                         [-0.062, -0.454, -0.268], [-0.062, -0.269, -0.429], [-0.062, -0.269, -0.429],
                                         [-0.062, -0.269, -0.429], [-0.091, -0.311, -0.402], [-0.129, -0.347, -0.368],
                                         [-0.17, -0.374, -0.33], [-0.17, -0.374, -0.33], [-0.17, -0.374, -0.33],
                                         [-0.17, -0.374, -0.33], [-0.204, -0.364, -0.34], [-0.204, -0.364, -0.34],
                                         [-0.204, -0.364, -0.34], [-0.158, -0.332, -0.383], [-0.123, -0.292, -0.418],
                                         [-0.079, -0.237, -0.449], [-0.047, -0.194, -0.474], [0.0, -0.127, -0.509]],
                                      d=3)
    right_fingers_ctrl_c = cmds.curve(name=right_wrist_ik_ctrl_a + 'c',
                                      p=[[0.048, -0.0, 0.126], [0.073, 0.013, 0.139], [0.089, 0.023, 0.149],
                                         [0.109, 0.035, 0.16], [0.124, 0.046, 0.173], [0.136, 0.059, 0.189],
                                         [0.136, 0.059, 0.189], [0.136, 0.059, 0.189], [0.14, 0.049, 0.193],
                                         [0.14, 0.049, 0.193], [0.14, 0.049, 0.193], [0.14, 0.049, 0.193],
                                         [0.13, 0.037, 0.179], [0.116, 0.026, 0.166], [0.101, 0.018, 0.156],
                                         [0.101, 0.018, 0.156], [0.101, 0.018, 0.156], [0.17, 0.018, 0.216],
                                         [0.194, 0.018, 0.325], [0.166, 0.018, 0.403], [0.133, 0.018, 0.444],
                                         [0.084, 0.018, 0.482], [0.0, 0.018, 0.506], [-0.084, 0.018, 0.482],
                                         [-0.133, 0.018, 0.444], [-0.166, 0.018, 0.403], [-0.194, 0.018, 0.325],
                                         [-0.17, 0.018, 0.216], [-0.101, 0.018, 0.156], [-0.101, 0.018, 0.156],
                                         [-0.101, 0.018, 0.156], [-0.116, 0.026, 0.166], [-0.13, 0.037, 0.179],
                                         [-0.14, 0.049, 0.193], [-0.14, 0.049, 0.193], [-0.14, 0.049, 0.193],
                                         [-0.14, 0.049, 0.193], [-0.136, 0.059, 0.189], [-0.136, 0.059, 0.189],
                                         [-0.136, 0.059, 0.189], [-0.124, 0.046, 0.173], [-0.109, 0.035, 0.16],
                                         [-0.089, 0.023, 0.149], [-0.073, 0.013, 0.139], [-0.048, 0.0, 0.126]], d=3)
    right_fingers_ctrl_d = cmds.curve(name=right_wrist_ik_ctrl_a + 'd',
                                      p=[[0.048, -0.0, 0.126], [0.073, -0.013, 0.139], [0.089, -0.023, 0.149],
                                         [0.109, -0.035, 0.16], [0.124, -0.046, 0.173], [0.136, -0.059, 0.189],
                                         [0.136, -0.059, 0.189], [0.136, -0.059, 0.189], [0.14, -0.049, 0.193],
                                         [0.14, -0.049, 0.193], [0.14, -0.049, 0.193], [0.14, -0.049, 0.193],
                                         [0.13, -0.037, 0.179], [0.116, -0.026, 0.166], [0.101, -0.018, 0.156],
                                         [0.101, -0.018, 0.156], [0.101, -0.018, 0.156], [0.17, -0.018, 0.216],
                                         [0.194, -0.018, 0.325], [0.166, -0.018, 0.403], [0.133, -0.018, 0.444],
                                         [0.084, -0.018, 0.482], [-0.0, -0.018, 0.506], [-0.084, -0.018, 0.482],
                                         [-0.133, -0.018, 0.444], [-0.166, -0.018, 0.403], [-0.194, -0.018, 0.325],
                                         [-0.17, -0.018, 0.216], [-0.101, -0.018, 0.156], [-0.101, -0.018, 0.156],
                                         [-0.101, -0.018, 0.156], [-0.116, -0.026, 0.166], [-0.13, -0.037, 0.179],
                                         [-0.14, -0.049, 0.193], [-0.14, -0.049, 0.193], [-0.14, -0.049, 0.193],
                                         [-0.14, -0.049, 0.193], [-0.136, -0.059, 0.189], [-0.136, -0.059, 0.189],
                                         [-0.136, -0.059, 0.189], [-0.124, -0.046, 0.173], [-0.109, -0.035, 0.16],
                                         [-0.089, -0.023, 0.149], [-0.073, -0.013, 0.139], [-0.048, 0.0, 0.126]], d=3)

    right_fingers_ctrl = combine_curves_list(
        [right_fingers_ctrl_a, right_fingers_ctrl_b, right_fingers_ctrl_c, right_fingers_ctrl_d])

    shapes = cmds.listRelatives(right_fingers_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format('big_arrow_l'))
    cmds.rename(shapes[1], '{0}Shape'.format('big_arrow_r'))
    cmds.rename(shapes[2], '{0}Shape'.format('small_arrow_u'))
    cmds.rename(shapes[3], '{0}Shape'.format('small_arrow_d'))

    right_fingers_ctrl_grp = cmds.group(name=right_fingers_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(right_fingers_ctrl, right_fingers_ctrl_grp)

    cmds.setAttr(right_fingers_ctrl + '.rotateY', -90)
    cmds.setAttr(right_fingers_ctrl + '.scaleX', right_wrist_scale_offset * .3)
    cmds.setAttr(right_fingers_ctrl + '.scaleY', right_wrist_scale_offset * .3)
    cmds.setAttr(right_fingers_ctrl + '.scaleZ', -right_wrist_scale_offset * .3)
    cmds.makeIdentity(right_fingers_ctrl, apply=True, scale=True, rotate=True)

    # Create Abduction Finger Setup
    right_fingers_abduction_ctrl = create_scalable_arrow('right_open_finger_' + CTRL_SUFFIX,
                                                         right_wrist_scale_offset * .1)
    cmds.parent(right_fingers_abduction_ctrl[0], right_fingers_ctrl_grp)
    cmds.setAttr(right_fingers_abduction_ctrl[0] + '.overrideEnabled', 1)
    cmds.setAttr(right_fingers_abduction_ctrl[0] + '.overrideDisplayType', 1)

    # ########### Right Fingers Control Behavior Attributes ############
    cmds.addAttr(right_fingers_ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
    cmds.setAttr(right_fingers_ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)

    # Right Fingers Curl Visibility (Attributes)
    cmds.addAttr(right_fingers_ctrl, ln='showCurlControls', at='bool', k=True)
    cmds.addAttr(right_fingers_ctrl, ln='showFkFingerCtrls', at='bool', k=True, niceName='Show FK Finger Ctrls')

    # Right Fingers Limits (Attributes)
    cmds.addAttr(right_fingers_ctrl, ln='maximumRotationZ', at='double', k=True)
    cmds.setAttr(right_fingers_ctrl + '.maximumRotationZ', 10)
    cmds.addAttr(right_fingers_ctrl, ln='minimumRotationZ', at='double', k=True)
    cmds.setAttr(right_fingers_ctrl + '.minimumRotationZ', -130)

    cmds.addAttr(right_fingers_ctrl, ln='rotateShape', at='bool', k=True)
    cmds.setAttr(right_fingers_ctrl + '.rotateShape', 1)

    cmds.setAttr(right_fingers_ctrl + '.maxRotZLimitEnable', 1)
    cmds.setAttr(right_fingers_ctrl + '.minRotZLimitEnable', 1)

    # Curl Controls
    distance_from_parent = -.4
    right_curl_thumb_ctrl = create_finger_curl_ctrl('right_thumbCurl_' + CTRL_SUFFIX, right_fingers_ctrl_grp,
                                                    right_wrist_scale_offset, distance_from_parent, -.55)
    right_curl_thumb_ctrl_grp = cmds.group(name=right_curl_thumb_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.delete(cmds.parentConstraint(right_curl_thumb_ctrl, right_curl_thumb_ctrl_grp))
    cmds.parent(right_curl_thumb_ctrl, right_curl_thumb_ctrl_grp)
    cmds.setAttr(right_curl_thumb_ctrl_grp + '.rotateY', -90)
    cmds.parent(right_curl_thumb_ctrl_grp, right_fingers_ctrl_grp)

    right_curl_index_ctrl = create_finger_curl_ctrl('right_indexCurl_' + CTRL_SUFFIX, right_fingers_ctrl_grp,
                                                    right_wrist_scale_offset, distance_from_parent, -.35)
    right_curl_middle_ctrl = create_finger_curl_ctrl('right_middleCurl_' + CTRL_SUFFIX, right_fingers_ctrl_grp,
                                                     right_wrist_scale_offset, distance_from_parent, -.15)
    right_curl_ring_ctrl = create_finger_curl_ctrl('right_ringCurl_' + CTRL_SUFFIX, right_fingers_ctrl_grp,
                                                   right_wrist_scale_offset, distance_from_parent, .05)
    right_curl_pinky_ctrl = create_finger_curl_ctrl('right_pinkyCurl_' + CTRL_SUFFIX, right_fingers_ctrl_grp,
                                                    right_wrist_scale_offset, distance_from_parent, .25)
    right_curl_controls = [right_curl_thumb_ctrl, right_curl_index_ctrl, right_curl_middle_ctrl, right_curl_ring_ctrl,
                           right_curl_pinky_ctrl]

    for curl_ctrl in right_curl_controls:
        change_viewport_color(curl_ctrl,
                              (RIGHT_CTRL_COLOR[0] * 1.3, RIGHT_CTRL_COLOR[1] * 1.3, RIGHT_CTRL_COLOR[2] * 1.3))
        cmds.setAttr(curl_ctrl + '.ry', -180)  # Account for mirrored pose
        cmds.setAttr(curl_ctrl + '.tx', lock=True, keyable=False)
        cmds.setAttr(curl_ctrl + '.ty', lock=True, keyable=False)
        cmds.setAttr(curl_ctrl + '.tz', lock=True, keyable=False)
        cmds.setAttr(curl_ctrl + '.rx', lock=True, keyable=False)
        cmds.setAttr(curl_ctrl + '.ry', lock=True, keyable=False)
        cmds.setAttr(curl_ctrl + '.sx', lock=True, keyable=False)
        cmds.setAttr(curl_ctrl + '.sy', lock=True, keyable=False)
        cmds.setAttr(curl_ctrl + '.sz', lock=True, keyable=False)
        cmds.setAttr(curl_ctrl + '.v', lock=True, keyable=False)

    # Position
    cmds.delete(cmds.parentConstraint(rig_joints.get('right_wrist_jnt'), right_fingers_ctrl_grp))
    cmds.move(-right_wrist_scale_offset * 2.3, right_fingers_ctrl_grp, x=True, relative=True, objectSpace=True)
    cmds.setAttr(right_fingers_ctrl_grp + '.rotateX', -180)

    # Hierarchy
    change_viewport_color(right_fingers_ctrl, RIGHT_CTRL_COLOR)
    cmds.parent(right_fingers_ctrl_grp, right_hand_grp)

    # ################ ======= Rig Mechanics ======= #################

    # Main Scale
    cmds.connectAttr(main_ctrl + '.sy', main_ctrl + '.sx', f=True)
    cmds.connectAttr(main_ctrl + '.sy', main_ctrl + '.sz', f=True)

    # ################ Center FK #################
    cmds.parentConstraint(main_ctrl, rig_joints.get('main_jnt'))

    # ############# IK Spine (Ribbon) ##############
    spine_automation_grp = cmds.group(name='spineAutomation_' + GRP_SUFFIX, empty=True, world=True)
    spine_ik_grp = cmds.group(name='spineRibbon_grp', empty=True)
    cmds.setAttr(spine_ik_grp + '.inheritsTransform', 0)
    cog_ws_pos = cmds.xform(rig_joints.get('cog_jnt'), q=1, ws=1, rp=1)
    spine01_ws_pos = cmds.xform(rig_joints.get('spine01_jnt'), q=1, ws=1, rp=1)
    spine02_ws_pos = cmds.xform(rig_joints.get('spine02_jnt'), q=1, ws=1, rp=1)
    spine03_ws_pos = cmds.xform(rig_joints.get('spine03_jnt'), q=1, ws=1, rp=1)
    spine04_ws_pos = cmds.xform(rig_joints.get('spine04_jnt'), q=1, ws=1, rp=1)

    ribbon_one_crv = cmds.curve(name='spine_ribbon_crv_one',
                                p=[cog_ws_pos, spine01_ws_pos, spine02_ws_pos, spine03_ws_pos, spine04_ws_pos])
    ribbon_two_crv = cmds.duplicate(ribbon_one_crv, name='spine_ribbon_crv_two')
    cmds.move(general_scale_offset * .1, ribbon_one_crv, x=True, absolute=True)
    cmds.move(general_scale_offset * -.1, ribbon_two_crv, x=True, absolute=True)
    ribbon_sur = cmds.loft(ribbon_two_crv, ribbon_one_crv, name='spine_ribbon_sur', ch=False, rn=True, ar=False)[0]
    cmds.delete(ribbon_one_crv)
    cmds.delete(ribbon_two_crv)

    cmds.parent(ribbon_sur, spine_ik_grp)

    # Key: follicle, Value: its V position
    spine_follicles = {'spine01_follicle': 0.2,
                       'spine02_follicle': 0.5,
                       'spine03_follicle': 0.8}

    for follicle_data in spine_follicles:
        follicle = cmds.createNode('follicle')
        cmds.setAttr(follicle + '.parameterU', .5)  # Center
        cmds.setAttr(follicle + '.parameterV', spine_follicles.get(follicle_data))

        follicle_transform = cmds.listRelatives(follicle, allParents=True)[0]
        cmds.connectAttr(main_ctrl + '.scale', follicle_transform + '.scale')  # Inherit Scale from Main Ctrl
        cmds.connectAttr(ribbon_sur + '.local',
                         follicle + '.inputSurface')  # Connect the nurbs object on the follicle
        cmds.connectAttr(ribbon_sur + '.worldMatrix', follicle + '.inputWorldMatrix',
                         force=True)  # Connect transforms to follicle (so it knows where it is)
        cmds.connectAttr(follicle + '.outTranslate', follicle_transform + '.translate',
                         force=True)  # Connects follicleShape position to its transform (default behavior)
        cmds.connectAttr(follicle + '.outRotate', follicle_transform + '.rotate',
                         force=True)  # Connects follicleShape rotate to its transform (default behavior)
        follicle_transform = cmds.rename(follicle_transform, follicle_data)
        cmds.parent(follicle_transform, spine_ik_grp)
        spine_follicles[follicle_data] = follicle_transform

    # Create Ribbon IK Chain
    ik_cog_jnt = cmds.duplicate(rig_joints.get('cog_jnt'),
                                name=rig_joints.get('cog_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX), po=True)
    ik_spine01_jnt = cmds.duplicate(rig_joints.get('spine01_jnt'),
                                    name=rig_joints.get('spine01_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX), po=True)
    ik_spine02_jnt = cmds.duplicate(rig_joints.get('spine02_jnt'),
                                    name=rig_joints.get('spine02_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX), po=True)
    ik_spine03_jnt = cmds.duplicate(rig_joints.get('spine03_jnt'),
                                    name=rig_joints.get('spine03_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX), po=True)
    ik_spine04_jnt = cmds.duplicate(rig_joints.get('spine04_jnt'),
                                    name=rig_joints.get('spine04_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX), po=True)
    cmds.setAttr(ik_spine01_jnt[0] + '.radius', (cmds.getAttr(ik_spine01_jnt[0] + '.radius') * .7))
    cmds.setAttr(ik_spine02_jnt[0] + '.radius', (cmds.getAttr(ik_spine02_jnt[0] + '.radius') * .7))
    cmds.setAttr(ik_spine03_jnt[0] + '.radius', (cmds.getAttr(ik_spine03_jnt[0] + '.radius') * .7))
    cmds.setAttr(ik_spine04_jnt[0] + '.radius', (cmds.getAttr(ik_spine04_jnt[0] + '.radius') * .7))
    change_viewport_color(ik_cog_jnt[0], ik_jnt_color)
    change_viewport_color(ik_spine01_jnt[0], ik_jnt_color)
    change_viewport_color(ik_spine02_jnt[0], ik_jnt_color)
    change_viewport_color(ik_spine03_jnt[0], ik_jnt_color)
    change_viewport_color(ik_spine04_jnt[0], ik_jnt_color)
    cmds.parent(ik_cog_jnt, world=True)
    cmds.parent(ik_spine01_jnt, ik_cog_jnt)
    cmds.parent(ik_spine02_jnt, ik_spine01_jnt)
    cmds.parent(ik_spine03_jnt, ik_spine02_jnt)
    cmds.parent(ik_spine04_jnt, ik_spine03_jnt)
    ik_spine_joints = [ik_cog_jnt[0], ik_spine01_jnt[0], ik_spine02_jnt[0], ik_spine03_jnt[0], ik_spine04_jnt[0]]

    # Create Limit Jnt Chain
    cmds.duplicate(ik_cog_jnt, rc=True)
    ik_spine_constraint_joints = []
    for jnt in ik_spine_joints:
        ik_spine_constraint_joints.append(
            cmds.rename(jnt + '1', jnt.replace(JNT_SUFFIX, 'limit' + JNT_SUFFIX.capitalize())))

    cmds.setAttr(ik_spine_constraint_joints[0] + '.v', 0)
    ik_spine_constraint_handle = cmds.ikHandle(n='spineConstraint_SC_ikHandle', sj=ik_spine_constraint_joints[0],
                                               ee=ik_spine_constraint_joints[-1], sol='ikSCsolver')

    cmds.addAttr(cog_ctrl, ln="squashStretch", at='enum', en='-------------:', keyable=True)
    cmds.setAttr(cog_ctrl + '.squashStretch', lock=True)

    spine_stretchy_elements = make_stretchy_ik(ik_spine_constraint_handle[0], 'spine', cog_ctrl)

    cmds.parent(ik_spine_constraint_joints[0], skeleton_grp)
    cmds.parentConstraint(rig_joints.get('cog_jnt'), ik_spine_constraint_joints[0])

    # Change Stretchy System to be compatible with other controls
    for child in cmds.listRelatives(spine_stretchy_elements[0], children=True) or []:
        if 'Constraint' in child:
            cmds.delete(child)

    chest_pivot_grp = cmds.group(name='chest_pivot' + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.delete(cmds.parentConstraint(ik_spine_constraint_joints[-1], chest_pivot_grp))

    cmds.parentConstraint(chest_pivot_grp, spine_stretchy_elements[0])
    cmds.parent(ik_spine_constraint_handle[0], chest_pivot_grp)

    chest_pivot_parent_grp = \
        cmds.duplicate(chest_pivot_grp, name='chest_pivotParent' + GRP_SUFFIX.capitalize(), po=True)[0]
    chest_pivot_data_grp = cmds.duplicate(chest_pivot_grp, name='chest_data', po=True)[0]
    cmds.parent(chest_pivot_grp, chest_pivot_parent_grp)
    cmds.pointConstraint(ik_spine_constraint_joints[-1], chest_pivot_data_grp)

    cmds.parent(chest_pivot_parent_grp, spine_automation_grp)
    cmds.parent(spine_stretchy_elements[1], spine_automation_grp)

    cmds.parentConstraint(spine_follicles.get('spine01_follicle'), ik_spine01_jnt, mo=True)
    cmds.parentConstraint(spine_follicles.get('spine02_follicle'), ik_spine02_jnt, mo=True)
    cmds.parentConstraint(spine_follicles.get('spine03_follicle'), ik_spine03_jnt, mo=True)

    # Create Ribbon Joints
    ribbon_cog_jnt = cmds.duplicate(rig_joints.get('cog_jnt'),
                                    name=rig_joints.get('cog_jnt').replace(JNT_SUFFIX, 'ribbon_' + JNT_SUFFIX), po=True)
    ribbon_spine02_jnt = cmds.duplicate(rig_joints.get('spine02_jnt'), name='spine_ribbon_' + JNT_SUFFIX, po=True)
    ribbon_spine04_jnt = cmds.duplicate(rig_joints.get('spine04_jnt'), name='chest_ribbon_' + JNT_SUFFIX, po=True)
    change_viewport_color(ribbon_cog_jnt[0], automation_jnt_color)
    change_viewport_color(ribbon_spine02_jnt[0], automation_jnt_color)
    change_viewport_color(ribbon_spine04_jnt[0], automation_jnt_color)
    cmds.parent(ribbon_cog_jnt, world=True)
    cmds.parent(ribbon_spine02_jnt, world=True)
    cmds.parent(ribbon_spine04_jnt, world=True)
    cmds.setAttr(ribbon_cog_jnt[0] + '.radius', (cmds.getAttr(ribbon_cog_jnt[0] + '.radius') * 1.4))
    cmds.setAttr(ribbon_spine02_jnt[0] + '.radius', (cmds.getAttr(ribbon_spine02_jnt[0] + '.radius') * 1.4))
    cmds.setAttr(ribbon_spine04_jnt[0] + '.radius', (cmds.getAttr(ribbon_spine04_jnt[0] + '.radius') * 1.4))

    cmds.skinCluster([ribbon_cog_jnt[0], ribbon_spine02_jnt[0], ribbon_spine04_jnt[0]], ribbon_sur, bindMethod=1,
                     toSelectedBones=True, smoothWeights=0.5, maximumInfluences=4, hmf=.5)

    # Ribbon Controls and Connections
    cmds.parentConstraint(ribbon_cog_jnt[0], ik_cog_jnt[0], mo=True)
    cmds.parentConstraint(ribbon_spine04_jnt[0], ik_spine04_jnt[0], mo=True)

    # Chest Ctrl
    chest_ribbon_ctrl_a = cmds.curve(name=ribbon_spine04_jnt[0].replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                     p=[[0.0, 0.0, 0.0], [0.464, -1.733, 0.0], [0.531, -1.724, 0.0],
                                        [0.597, -1.734, 0.0], [0.659, -1.758, 0.0], [0.712, -1.799, 0.0],
                                        [0.752, -1.852, 0.0], [0.778, -1.914, 0.0], [0.531, -1.981, 0.0],
                                        [0.464, -1.733, 0.0], [0.402, -1.759, 0.0], [0.349, -1.8, 0.0],
                                        [0.309, -1.852, 0.0], [0.283, -1.915, 0.0], [0.275, -1.98, 0.0],
                                        [0.282, -2.047, 0.0], [0.308, -2.109, 0.0], [0.349, -2.161, 0.0],
                                        [0.403, -2.202, 0.0], [0.464, -2.228, 0.0], [0.53, -2.236, 0.0],
                                        [0.597, -2.228, 0.0], [0.659, -2.203, 0.0], [0.712, -2.161, 0.0],
                                        [0.753, -2.109, 0.0], [0.777, -2.048, 0.0], [0.786, -1.98, 0.0],
                                        [0.778, -1.914, 0.0], [0.282, -2.047, 0.0], [0.531, -1.981, 0.0],
                                        [0.597, -2.228, 0.0]], d=1)
    chest_ribbon_ctrl_b = cmds.curve(
        p=[[-0.5, 0.689, 0.5], [0.5, 0.5, 0.5], [0.5, 0.5, -0.5], [-0.5, 0.689, -0.5], [-0.5, 0.689, 0.5],
           [-0.5, -0.689, 0.5], [-0.5, -0.689, -0.5], [0.5, -0.5, -0.5], [0.5, -0.5, 0.5], [-0.5, -0.689, 0.5],
           [0.5, -0.5, 0.5], [0.5, 0.5, 0.5], [0.5, 0.5, -0.5], [0.5, -0.5, -0.5], [-0.5, -0.689, -0.5],
           [-0.5, 0.689, -0.5]], d=1)

    cmds.setAttr(chest_ribbon_ctrl_a + '.sx', general_scale_offset * .55)
    cmds.setAttr(chest_ribbon_ctrl_a + '.sy', general_scale_offset * .55)
    cmds.setAttr(chest_ribbon_ctrl_a + '.sz', general_scale_offset * .55)
    cmds.setAttr(chest_ribbon_ctrl_b + '.sx', general_scale_offset * 1.2)
    cmds.setAttr(chest_ribbon_ctrl_b + '.sy', general_scale_offset * .8)
    cmds.setAttr(chest_ribbon_ctrl_b + '.sz', general_scale_offset * 1.5)

    cmds.makeIdentity(chest_ribbon_ctrl_a, apply=True, scale=True, rotate=True)
    cmds.makeIdentity(chest_ribbon_ctrl_b, apply=True, scale=True, rotate=True)

    chest_ribbon_ctrl = combine_curves_list([chest_ribbon_ctrl_a, chest_ribbon_ctrl_b])
    chest_ribbon_ctrl_grp = cmds.group(name=chest_ribbon_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)

    shapes = cmds.listRelatives(chest_ribbon_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format('chest_pin'))
    cmds.rename(shapes[1], '{0}Shape'.format('chest_box'))

    # Add Separator
    cmds.addAttr(chest_ribbon_ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
    cmds.setAttr(chest_ribbon_ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)

    # Expose Custom Rotate Order
    cmds.addAttr(chest_ribbon_ctrl, ln='rotationOrder', at='enum', en=ROTATE_ORDER_ENUM, keyable=True,
                 niceName='Rotate Order')
    cmds.connectAttr(chest_ribbon_ctrl + '.rotationOrder', chest_ribbon_ctrl + '.rotateOrder', f=True)

    # Chest Ctrl Visibility Switch
    setup_shape_switch(chest_ribbon_ctrl, attr='controlShape', shape_names=['box', 'pin'], shape_enum=['Box', 'Pin'])

    cmds.parent(chest_ribbon_ctrl, chest_ribbon_ctrl_grp)

    cmds.delete(cmds.orientConstraint(ribbon_spine04_jnt[0], chest_ribbon_ctrl))
    cmds.makeIdentity(chest_ribbon_ctrl, apply=True, rotate=True)
    cmds.delete(cmds.pointConstraint(ribbon_spine04_jnt[0], chest_ribbon_ctrl_grp))

    change_viewport_color(chest_ribbon_ctrl, (1, 1, 0))

    # Create Duplicate for FK Global Control
    chest_global_fk_ctrl = cmds.duplicate(chest_ribbon_ctrl, name='chest_global_fk_' + CTRL_SUFFIX)[0]

    # Chest In-Between Offset
    chest_ribbon_offset_ctrl = cmds.duplicate(chest_ribbon_ctrl,
                                              name=chest_ribbon_ctrl.replace('_' + CTRL_SUFFIX, '_offset' +
                                                                             CTRL_SUFFIX.capitalize()))[0]
    cmds.setAttr(chest_ribbon_offset_ctrl + '.scaleX', .9)
    cmds.setAttr(chest_ribbon_offset_ctrl + '.scaleY', .9)
    cmds.setAttr(chest_ribbon_offset_ctrl + '.scaleZ', .9)
    cmds.makeIdentity(chest_ribbon_offset_ctrl, apply=True, scale=True)
    change_viewport_color(chest_ribbon_offset_ctrl, (.4, .4, 0))
    lock_hide_default_attr(chest_ribbon_offset_ctrl, translate=False, rotate=False, visibility=False)
    cmds.setAttr(chest_ribbon_offset_ctrl + '.v', k=False, channelBox=False)

    # Recreate Connections
    cmds.connectAttr(chest_ribbon_offset_ctrl + '.rotationOrder', chest_ribbon_offset_ctrl + '.rotateOrder', f=True)
    setup_shape_switch(chest_ribbon_offset_ctrl, attr='controlShape', shape_names=['box', 'pin'],
                       shape_enum=['Box', 'Pin'])

    chest_ribbon_offset_ctrl_grp = cmds.group(name=chest_ribbon_offset_ctrl + GRP_SUFFIX.capitalize(), empty=True,
                                              world=True)
    cmds.delete(cmds.parentConstraint(chest_ribbon_offset_ctrl, chest_ribbon_offset_ctrl_grp))

    cmds.parent(chest_ribbon_offset_ctrl, chest_ribbon_offset_ctrl_grp)
    cmds.parent(chest_ribbon_offset_ctrl_grp, chest_ribbon_ctrl)

    cmds.addAttr(chest_ribbon_ctrl, ln='showOffsetCtrl', at='bool', k=True)
    cmds.connectAttr(chest_ribbon_ctrl + '.showOffsetCtrl', chest_ribbon_offset_ctrl + '.v', f=True)

    # Set New Pivot
    desired_pivot = cmds.xform(rig_joints.get('spine03_jnt'), q=True, ws=True, t=True)
    cmds.xform(chest_ribbon_ctrl, piv=desired_pivot, ws=True)
    cmds.xform(chest_ribbon_offset_ctrl, piv=desired_pivot, ws=True)

    # ### End Chest In-Between Offset

    # Chest Adjustment Ctrl
    chest_ribbon_adjustment_ctrl_a = cmds.curve(name=chest_ribbon_ctrl.replace('_ribbon_', '_ribbon_adjustment_'),
                                                p=[[0.0, 0.0, 0.0], [0.0, -1.794, 0.0], [0.067, -1.803, 0.0],
                                                   [0.128, -1.829, 0.0], [0.181, -1.869, 0.0], [0.222, -1.922, 0.0],
                                                   [0.247, -1.984, 0.0], [0.256, -2.05, 0.0], [0.0, -2.051, 0.0],
                                                   [0.0, -1.794, 0.0], [-0.067, -1.803, 0.0], [-0.129, -1.829, 0.0],
                                                   [-0.181, -1.869, 0.0], [-0.222, -1.923, 0.0], [-0.247, -1.984, 0.0],
                                                   [-0.257, -2.05, 0.0], [-0.248, -2.117, 0.0], [-0.222, -2.178, 0.0],
                                                   [-0.181, -2.231, 0.0], [-0.128, -2.272, 0.0], [-0.067, -2.297, 0.0],
                                                   [0.0, -2.307, 0.0], [0.066, -2.298, 0.0], [0.128, -2.272, 0.0],
                                                   [0.181, -2.232, 0.0], [0.221, -2.179, 0.0], [0.247, -2.116, 0.0],
                                                   [0.256, -2.05, 0.0], [-0.257, -2.05, 0.0], [0.0, -2.051, 0.0],
                                                   [0.0, -2.307, 0.0]], d=1)
    chest_ribbon_adjustment_ctrl_b = cmds.curve(
        p=[[-0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [0.5, 0.5, -0.5], [-0.5, 0.5, -0.5], [-0.5, 0.5, 0.5], [-0.5, -0.5, 0.5],
           [-0.5, -0.5, -0.5], [0.5, -0.5, -0.5], [0.5, -0.5, 0.5], [-0.5, -0.5, 0.5], [0.5, -0.5, 0.5],
           [0.5, 0.5, 0.5], [0.5, 0.5, -0.5], [0.5, -0.5, -0.5], [-0.5, -0.5, -0.5], [-0.5, 0.5, -0.5]], d=1)

    cmds.setAttr(chest_ribbon_adjustment_ctrl_a + '.sx', general_scale_offset * .44)
    cmds.setAttr(chest_ribbon_adjustment_ctrl_a + '.sy', general_scale_offset * .44)
    cmds.setAttr(chest_ribbon_adjustment_ctrl_a + '.sz', general_scale_offset * .44)
    cmds.setAttr(chest_ribbon_adjustment_ctrl_b + '.sx', general_scale_offset)
    cmds.setAttr(chest_ribbon_adjustment_ctrl_b + '.sy', general_scale_offset * .6)
    cmds.setAttr(chest_ribbon_adjustment_ctrl_b + '.sz', general_scale_offset)
    cmds.makeIdentity(chest_ribbon_adjustment_ctrl_a, apply=True, scale=True, rotate=True)
    cmds.makeIdentity(chest_ribbon_adjustment_ctrl_b, apply=True, scale=True, rotate=True)

    chest_ribbon_adjustment_ctrl = combine_curves_list([chest_ribbon_adjustment_ctrl_a, chest_ribbon_adjustment_ctrl_b])
    chest_ribbon_adjustment_ctrl_grp = cmds.group(name=chest_ribbon_adjustment_ctrl + GRP_SUFFIX.capitalize(),
                                                  empty=True, world=True)

    shapes = cmds.listRelatives(chest_ribbon_adjustment_ctrl, s=True, f=True) or []
    cmds.rename(shapes[0], '{0}Shape'.format('chest_adjustment_pin'))
    cmds.rename(shapes[1], '{0}Shape'.format('chest_adjustment_box'))

    # # Chest Adjustment Ctrl Visibility Switch
    setup_shape_switch(chest_ribbon_adjustment_ctrl, attr='controlShape', shape_names=['box', 'pin'],
                       shape_enum=['Box', 'Pin'])
    cmds.setAttr(chest_ribbon_adjustment_ctrl + '.controlShape', 1)

    cmds.parent(chest_ribbon_adjustment_ctrl, chest_ribbon_adjustment_ctrl_grp)
    cmds.delete(cmds.parentConstraint(ribbon_spine04_jnt[0], chest_ribbon_adjustment_ctrl_grp))

    add_orient_offset(chest_ribbon_adjustment_ctrl, (90, 0, 90), apply=settings.get('uniform_ctrl_orient'))
    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(0, -90, -90, chest_ribbon_adjustment_ctrl_grp, os=True, relative=True)

    cmds.parentConstraint(chest_ribbon_adjustment_ctrl, ribbon_spine04_jnt[0], mo=True)
    change_viewport_color(chest_ribbon_adjustment_ctrl, AUTO_CTRL_COLOR)
    cmds.parent(chest_ribbon_adjustment_ctrl_grp,
                chest_ribbon_offset_ctrl_grp)  # Make Chest Control the main driver
    cmds.parent(chest_pivot_data_grp, chest_pivot_parent_grp)

    cmds.parentConstraint(chest_pivot_data_grp, chest_ribbon_adjustment_ctrl_grp, mo=True)

    chest_pivot_input_grp = cmds.duplicate(chest_pivot_data_grp, po=True,
                                           name='chest_dataInput' + GRP_SUFFIX.capitalize())
    cmds.parentConstraint(chest_ribbon_offset_ctrl, chest_pivot_input_grp, mo=True)
    cmds.pointConstraint(chest_pivot_input_grp, chest_pivot_grp, mo=True)
    cmds.orientConstraint(chest_pivot_input_grp, chest_pivot_data_grp, mo=True)

    # Chest Curve Shape Reposition
    # Y Offset
    temp_clavicle_average_grp = cmds.group(name='temp_dir_' + str(random.random()), world=True, empty=True)
    cmds.delete(cmds.pointConstraint([rig_joints.get('right_clavicle_jnt'), rig_joints.get('left_clavicle_jnt')],
                                     temp_clavicle_average_grp))
    chest_ctrl_y_offset = dist_center_to_center(temp_clavicle_average_grp, rig_joints.get('spine04_jnt'))
    cmds.delete(cmds.pointConstraint(rig_joints.get('spine04_jnt'), temp_clavicle_average_grp, skip=['x', 'z']))
    cv_pos_bottom = cmds.getAttr(chest_ribbon_ctrl + '.cv[0]')[1]
    cv_pos_top = cmds.getAttr(chest_ribbon_ctrl + '.cv[1]')[1]
    chest_ctrl_y_offset = chest_ctrl_y_offset - (cv_pos_bottom[1] + cv_pos_top[1]) * 1.3

    # Z Offset
    chest_ctrl_z_offset = dist_center_to_center(temp_clavicle_average_grp, rig_joints.get('spine04_jnt'))
    z_original_difference = cmds.xform(chest_ribbon_ctrl, q=True, ws=True, t=True)
    z_offset_difference = cmds.xform(temp_clavicle_average_grp, q=True, ws=True, t=True)
    if z_offset_difference[2] < z_original_difference[2]:
        chest_ctrl_z_offset = -chest_ctrl_z_offset
    offset_curve_shape([chest_ribbon_ctrl, chest_ribbon_offset_ctrl, chest_global_fk_ctrl],
                       [0, chest_ctrl_y_offset, chest_ctrl_z_offset * .5])
    cmds.delete(temp_clavicle_average_grp)

    # Spine Ctrl
    spine_ribbon_ctrl = cmds.curve(name=ribbon_spine02_jnt[0].replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                   p=[[0.0, 0.0, 0.0], [0.0, -1.794, 0.0], [0.067, -1.803, 0.0], [0.128, -1.829, 0.0],
                                      [0.181, -1.869, 0.0], [0.222, -1.922, 0.0], [0.247, -1.984, 0.0],
                                      [0.256, -2.05, 0.0], [0.0, -2.051, 0.0], [0.0, -1.794, 0.0],
                                      [-0.067, -1.803, 0.0], [-0.129, -1.829, 0.0], [-0.181, -1.869, 0.0],
                                      [-0.222, -1.923, 0.0], [-0.247, -1.984, 0.0], [-0.257, -2.05, 0.0],
                                      [-0.248, -2.117, 0.0], [-0.222, -2.178, 0.0], [-0.181, -2.231, 0.0],
                                      [-0.128, -2.272, 0.0], [-0.067, -2.297, 0.0], [0.0, -2.307, 0.0],
                                      [0.066, -2.298, 0.0], [0.128, -2.272, 0.0], [0.181, -2.232, 0.0],
                                      [0.221, -2.179, 0.0], [0.247, -2.116, 0.0], [0.256, -2.05, 0.0],
                                      [-0.257, -2.05, 0.0], [0.0, -2.051, 0.0], [0.0, -2.307, 0.0]], d=1)

    spine_ribbon_ctrl_grp = cmds.group(name=spine_ribbon_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.setAttr(spine_ribbon_ctrl + '.sx', general_scale_offset * .55)
    cmds.setAttr(spine_ribbon_ctrl + '.sy', general_scale_offset * .55)
    cmds.setAttr(spine_ribbon_ctrl + '.sz', general_scale_offset * .55)
    cmds.makeIdentity(spine_ribbon_ctrl, apply=True, scale=True, rotate=True)
    cmds.parent(spine_ribbon_ctrl, spine_ribbon_ctrl_grp)
    cmds.delete(cmds.parentConstraint(ribbon_spine02_jnt[0], spine_ribbon_ctrl_grp))

    add_orient_offset(spine_ribbon_ctrl, (90, 0, 90), apply=settings.get('uniform_ctrl_orient'))
    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(0, -90, -90, spine_ribbon_ctrl_grp, os=True, relative=True)

    cmds.parentConstraint(spine_ribbon_ctrl, ribbon_spine02_jnt[0], mo=True)
    change_viewport_color(spine_ribbon_ctrl, AUTO_CTRL_COLOR)

    # Cog Ctrl
    cog_ribbon_ctrl = cmds.curve(name=ribbon_cog_jnt[0].replace(JNT_SUFFIX, '') + CTRL_SUFFIX,
                                 p=[[0.0, 0.0, 0.0], [0.0, -1.794, 0.0], [0.067, -1.803, 0.0], [0.128, -1.829, 0.0],
                                    [0.181, -1.869, 0.0], [0.222, -1.922, 0.0], [0.247, -1.984, 0.0],
                                    [0.256, -2.05, 0.0], [0.0, -2.051, 0.0], [0.0, -1.794, 0.0], [-0.067, -1.803, 0.0],
                                    [-0.129, -1.829, 0.0], [-0.181, -1.869, 0.0], [-0.222, -1.923, 0.0],
                                    [-0.247, -1.984, 0.0], [-0.257, -2.05, 0.0], [-0.248, -2.117, 0.0],
                                    [-0.222, -2.178, 0.0], [-0.181, -2.231, 0.0], [-0.128, -2.272, 0.0],
                                    [-0.067, -2.297, 0.0], [0.0, -2.307, 0.0], [0.066, -2.298, 0.0],
                                    [0.128, -2.272, 0.0], [0.181, -2.232, 0.0], [0.221, -2.179, 0.0],
                                    [0.247, -2.116, 0.0], [0.256, -2.05, 0.0], [-0.257, -2.05, 0.0], [0.0, -2.051, 0.0],
                                    [0.0, -2.307, 0.0]], d=1)

    cog_ribbon_ctrl_grp = cmds.group(name=cog_ribbon_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.setAttr(cog_ribbon_ctrl + '.sx', general_scale_offset * .55)
    cmds.setAttr(cog_ribbon_ctrl + '.sy', general_scale_offset * .55)
    cmds.setAttr(cog_ribbon_ctrl + '.sz', general_scale_offset * .55)
    cmds.makeIdentity(cog_ribbon_ctrl, apply=True, scale=True, rotate=True)
    cmds.parent(cog_ribbon_ctrl, cog_ribbon_ctrl_grp)
    cmds.delete(cmds.parentConstraint(ribbon_cog_jnt[0], cog_ribbon_ctrl_grp))

    add_orient_offset(cog_ribbon_ctrl, (90, 0, 90), apply=settings.get('uniform_ctrl_orient'))
    if settings.get('uniform_ctrl_orient'):
        cmds.rotate(0, -90, -90, cog_ribbon_ctrl_grp, os=True, relative=True)

    cmds.parentConstraint(cog_ribbon_ctrl, ribbon_cog_jnt[0], mo=True)
    change_viewport_color(cog_ribbon_ctrl, AUTO_CTRL_COLOR)

    # Chest Ribbon Controls Visibility of Cog and Spine Curves
    cmds.addAttr(chest_ribbon_ctrl, ln='showAdjustmentControls', at='bool', k=True)
    cmds.connectAttr(chest_ribbon_ctrl + '.showAdjustmentControls', cog_ribbon_ctrl_grp + '.v', f=True)
    cmds.connectAttr(chest_ribbon_ctrl + '.showAdjustmentControls', spine_ribbon_ctrl_grp + '.v', f=True)
    cmds.connectAttr(chest_ribbon_ctrl + '.showAdjustmentControls', chest_ribbon_adjustment_ctrl_grp + '.v', f=True)

    # ### FK Spine ###

    # Create FK Chain
    fk_cog_jnt = cmds.duplicate(rig_joints.get('cog_jnt'),
                                name=rig_joints.get('cog_jnt').replace(JNT_SUFFIX, 'fk_' + JNT_SUFFIX), po=True)
    fk_spine01_jnt = cmds.duplicate(rig_joints.get('spine01_jnt'),
                                    name=rig_joints.get('spine01_jnt').replace(JNT_SUFFIX, 'fk_' + JNT_SUFFIX), po=True)
    fk_spine02_jnt = cmds.duplicate(rig_joints.get('spine02_jnt'),
                                    name=rig_joints.get('spine02_jnt').replace(JNT_SUFFIX, 'fk_' + JNT_SUFFIX), po=True)
    fk_spine03_jnt = cmds.duplicate(rig_joints.get('spine03_jnt'),
                                    name=rig_joints.get('spine03_jnt').replace(JNT_SUFFIX, 'fk_' + JNT_SUFFIX), po=True)
    fk_spine04_jnt = cmds.duplicate(rig_joints.get('spine04_jnt'),
                                    name=rig_joints.get('spine04_jnt').replace(JNT_SUFFIX, 'fk_' + JNT_SUFFIX), po=True)
    change_viewport_color(fk_cog_jnt[0], fk_jnt_color)
    change_viewport_color(fk_spine01_jnt[0], fk_jnt_color)
    change_viewport_color(fk_spine02_jnt[0], fk_jnt_color)
    change_viewport_color(fk_spine03_jnt[0], fk_jnt_color)
    change_viewport_color(fk_spine04_jnt[0], fk_jnt_color)
    cmds.parent(fk_cog_jnt, world=True)
    cmds.parent(fk_spine01_jnt, fk_cog_jnt)
    cmds.parent(fk_spine02_jnt, fk_spine01_jnt)
    cmds.parent(fk_spine03_jnt, fk_spine02_jnt)
    cmds.parent(fk_spine04_jnt, fk_spine03_jnt)
    cmds.setAttr(fk_cog_jnt[0] + '.radius', (cmds.getAttr(fk_cog_jnt[0] + '.radius') * .4))
    cmds.setAttr(fk_spine01_jnt[0] + '.radius', (cmds.getAttr(fk_spine01_jnt[0] + '.radius') * .4))
    cmds.setAttr(fk_spine02_jnt[0] + '.radius', (cmds.getAttr(fk_spine02_jnt[0] + '.radius') * .4))
    cmds.setAttr(fk_spine03_jnt[0] + '.radius', (cmds.getAttr(fk_spine03_jnt[0] + '.radius') * .4))
    cmds.setAttr(fk_spine04_jnt[0] + '.radius', (cmds.getAttr(fk_spine04_jnt[0] + '.radius') * .4))

    # FK Spine 01
    cmds.addAttr(spine01_ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
    cmds.setAttr(spine01_ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)

    setup_shape_switch(spine01_ctrl, shape_names=['box', 'flat', 'pin'], shape_enum=['Box', 'Flat', 'Pin'])

    cmds.parentConstraint(spine01_ctrl, fk_spine01_jnt, mo=True)  # Automated
    offset_group = cmds.group(name=spine01_ctrl + 'OffsetGrp', empty=True, world=True)
    cmds.delete(cmds.parentConstraint(spine01_ctrl_grp, offset_group))
    cmds.parent(offset_group, spine01_ctrl_grp)
    cmds.parent(spine01_ctrl, offset_group)

    spine01_condition_node = cmds.createNode('condition', name=spine01_ctrl.replace(CTRL_SUFFIX, '') + AUTO_SUFFIX)
    cmds.connectAttr(spine02_ctrl + '.rotate', spine01_condition_node + '.colorIfTrue', f=True)
    cmds.connectAttr(spine01_condition_node + '.outColor', offset_group + '.rotate', f=True)
    cmds.setAttr(spine01_condition_node + '.secondTerm', 1)
    cmds.setAttr(spine01_condition_node + '.colorIfFalseR', 0)
    cmds.setAttr(spine01_condition_node + '.colorIfFalseG', 0)
    cmds.setAttr(spine01_condition_node + '.colorIfFalseB', 0)

    cmds.addAttr(spine02_ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
    cmds.setAttr(spine02_ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)

    setup_shape_switch(spine02_ctrl, shape_names=['box', 'flat', 'pin'], shape_enum=['Box', 'Flat', 'Pin'])

    cmds.addAttr(spine02_ctrl, ln='rotationOrder', at='enum', en=ROTATE_ORDER_ENUM, keyable=True,
                 niceName='Rotate Order')
    cmds.connectAttr(spine02_ctrl + '.rotationOrder', spine02_ctrl + '.rotateOrder', f=True)

    # FK Spine 02
    cmds.parentConstraint(spine02_ctrl, fk_spine02_jnt, mo=True)

    # FK Spine 03
    cmds.parentConstraint(spine03_ctrl, fk_spine03_jnt, mo=True)  # Automated
    offset_group = cmds.group(name=spine03_ctrl + 'OffsetGrp', empty=True, world=True)
    cmds.delete(cmds.parentConstraint(spine03_ctrl_grp, offset_group))
    cmds.parent(offset_group, spine03_ctrl_grp)
    cmds.parent(spine03_ctrl, offset_group)

    cmds.addAttr(spine03_ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
    cmds.setAttr(spine03_ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)

    setup_shape_switch(spine03_ctrl, shape_names=['box', 'flat', 'pin'], shape_enum=['Box', 'Flat', 'Pin'])

    spine03_condition_node = cmds.createNode('condition', name=spine03_ctrl.replace(CTRL_SUFFIX, '') + AUTO_SUFFIX)
    cmds.connectAttr(spine04_ctrl + '.rotate', spine03_condition_node + '.colorIfTrue', f=True)
    cmds.connectAttr(spine03_condition_node + '.outColor', offset_group + '.rotate', f=True)
    cmds.setAttr(spine03_condition_node + '.secondTerm', 1)
    cmds.setAttr(spine03_condition_node + '.colorIfFalseR', 0)
    cmds.setAttr(spine03_condition_node + '.colorIfFalseG', 0)
    cmds.setAttr(spine03_condition_node + '.colorIfFalseB', 0)

    cmds.addAttr(spine04_ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
    cmds.setAttr(spine04_ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)

    setup_shape_switch(spine04_ctrl, shape_names=['box', 'flat', 'pin'], shape_enum=['Box', 'Flat', 'Pin'])

    cmds.addAttr(spine04_ctrl, ln='rotationOrder', at='enum', en=ROTATE_ORDER_ENUM, keyable=True,
                 niceName='Rotate Order')
    cmds.connectAttr(spine04_ctrl + '.rotationOrder', spine04_ctrl + '.rotateOrder', f=True)

    # FK Spine 04
    cmds.parentConstraint(spine04_ctrl, fk_spine04_jnt, mo=True)  # Automated

    # FK Global Chest Ctrl Setup
    change_viewport_color(chest_global_fk_ctrl, AUTO_CTRL_COLOR)
    chest_global_fk_ctrl_grp = cmds.group(name=chest_global_fk_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.delete(cmds.parentConstraint(chest_global_fk_ctrl, chest_global_fk_ctrl_grp))
    cmds.parent(chest_global_fk_ctrl, chest_global_fk_ctrl_grp)
    cmds.parent(chest_global_fk_ctrl_grp, spine04_ctrl)
    chest_offset_groups = []
    chest_offset_tag = 'Chest'
    spine01_ctrl_offset_grp = create_inbetween(spine01_ctrl, offset_suffix=chest_offset_tag)
    spine02_ctrl_offset_grp = create_inbetween(spine02_ctrl, offset_suffix='Offset' + chest_offset_tag)
    spine03_ctrl_offset_grp = create_inbetween(spine03_ctrl, offset_suffix=chest_offset_tag)
    spine04_ctrl_offset_grp = create_inbetween(spine04_ctrl, offset_suffix='Offset' + chest_offset_tag)
    chest_offset_groups.append(spine01_ctrl_offset_grp)
    chest_offset_groups.append(spine02_ctrl_offset_grp)
    chest_offset_groups.append(spine03_ctrl_offset_grp)
    chest_offset_groups.append(spine04_ctrl_offset_grp)
    for grp in chest_offset_groups:
        cmds.connectAttr(chest_global_fk_ctrl + '.rotate', grp + '.rotate')
        cmds.connectAttr(chest_global_fk_ctrl + '.translate', grp + '.translate')
        change_outliner_color(grp, AUTO_CTRL_COLOR)
    setup_shape_switch(chest_global_fk_ctrl, attr='controlShape', shape_names=['box', 'pin'], shape_enum=['Box', 'Pin'])
    lock_hide_default_attr(chest_global_fk_ctrl, rotate=False, translate=False)

    # FK IK Spine Switcher
    cmds.addAttr(cog_ctrl, ln='switchAttributes', at='enum', en='-------------:', keyable=True)
    cmds.setAttr(cog_ctrl + '.switchAttributes', lock=True)
    cmds.addAttr(cog_ctrl, ln='spineInfluenceSwitch', at='double', k=True, maxValue=1, minValue=0)
    cmds.addAttr(cog_ctrl, ln='autoVisibility', at='bool', k=True)
    cmds.addAttr(cog_ctrl, ln='systemVisibility', at='enum', k=True, en="FK:IK:")
    cmds.addAttr(cog_ctrl, ln='baseFKCtrlsVisibility', at='bool', k=True,
                 niceName='Base FK Visibility')
    cmds.addAttr(cog_ctrl, ln='additionalFKCtrlsVisibility', at='bool', k=True,
                 niceName='Additional FK Visibility')
    cmds.addAttr(cog_ctrl, ln='additionalFKCtrlsAutoRotate', at='bool', k=True,
                 niceName='Additional Auto Rotate')
    cmds.addAttr(cog_ctrl, ln='globalFKCtrlVisibility', at='bool', k=True,
                 niceName='Global FK Ctrl Visibility')
    cmds.setAttr(cog_ctrl + '.autoVisibility', 1)
    cmds.setAttr(cog_ctrl + '.systemVisibility', 1)
    cmds.setAttr(cog_ctrl + '.spineInfluenceSwitch', 1)  # Start as IK
    cmds.setAttr(cog_ctrl + '.baseFKCtrlsVisibility', 1)
    # cmds.setAttr(cog_ctrl + '.additionalFKCtrlsVisibility', 1) # Start With Additional Visible
    # cmds.setAttr(cog_ctrl + '.globalFKCtrlVisibility', 1) # Start with Global Visible
    cmds.setAttr(cog_ctrl + '.additionalFKCtrlsAutoRotate', 1)
    cmds.connectAttr(cog_ctrl + '.additionalFKCtrlsAutoRotate', spine01_condition_node + '.firstTerm', f=True)
    cmds.connectAttr(cog_ctrl + '.additionalFKCtrlsAutoRotate', spine03_condition_node + '.firstTerm', f=True)

    # Setup Base Ctrls Visibility
    shapes_spine_02 = cmds.listRelatives(spine02_ctrl, s=True, f=True) or []
    shapes_spine_04 = cmds.listRelatives(spine04_ctrl, s=True, f=True) or []
    shapes = shapes_spine_02 + shapes_spine_04
    for shape in shapes:
        cmds.setAttr(shape + '.overrideEnabled', 1)
        cmds.setAttr(shape + '.overrideRGBColors', 1)
        cmds.setAttr(shape + '.overrideColorRGB', CENTER_CTRL_COLOR[0], CENTER_CTRL_COLOR[1], CENTER_CTRL_COLOR[2])
        cmds.connectAttr(cog_ctrl + '.baseFKCtrlsVisibility', shape + '.overrideVisibility', f=True)
    # Setup In-Between and Global Ctrls Visibility
    shapes_spine_03 = cmds.listRelatives(spine03_ctrl, s=True, f=True) or []
    shapes_spine_01 = cmds.listRelatives(spine01_ctrl, s=True, f=True) or []
    shapes = shapes_spine_03 + shapes_spine_01
    for shape in shapes:
        cmds.setAttr(shape + '.overrideEnabled', 1)
        cmds.setAttr(shape + '.overrideRGBColors', 1)
        cmds.setAttr(shape + '.overrideColorRGB', AUTO_CTRL_COLOR[0], AUTO_CTRL_COLOR[1], AUTO_CTRL_COLOR[2])
        cmds.connectAttr(cog_ctrl + '.additionalFKCtrlsVisibility', shape + '.overrideVisibility', f=True)
    cmds.connectAttr(cog_ctrl + '.globalFKCtrlVisibility', chest_global_fk_ctrl_grp + '.v', f=True)

    spine_switch_condition_node = cmds.createNode('condition', name='spine_switchVisibility_' + AUTO_SUFFIX)
    spine_visibility_condition_node = cmds.createNode('condition', name='spine_autoVisibility_' + AUTO_SUFFIX)

    cmds.connectAttr(cog_ctrl + '.spineInfluenceSwitch', spine_visibility_condition_node + '.firstTerm', f=True)
    cmds.setAttr(spine_visibility_condition_node + '.operation', 3)
    cmds.setAttr(spine_visibility_condition_node + '.secondTerm', .5)
    cmds.setAttr(spine_visibility_condition_node + '.colorIfTrueR', 1)
    cmds.setAttr(spine_visibility_condition_node + '.colorIfTrueG', 1)
    cmds.setAttr(spine_visibility_condition_node + '.colorIfTrueB', 1)
    cmds.setAttr(spine_visibility_condition_node + '.colorIfFalseR', 0)
    cmds.setAttr(spine_visibility_condition_node + '.colorIfFalseG', 0)
    cmds.setAttr(spine_visibility_condition_node + '.colorIfFalseB', 0)
    cmds.connectAttr(cog_ctrl + '.systemVisibility', spine_switch_condition_node + '.colorIfFalseR', f=True)
    cmds.connectAttr(cog_ctrl + '.autoVisibility', spine_switch_condition_node + '.firstTerm', f=True)
    cmds.setAttr(spine_switch_condition_node + '.secondTerm', 1)

    cmds.connectAttr(spine_visibility_condition_node + '.outColor', spine_switch_condition_node + '.colorIfTrue',
                     f=True)

    # IK Reverse
    spine_v_reverse_node = cmds.createNode('reverse', name='spine_autoVisibility_reverse')
    cmds.connectAttr(spine_switch_condition_node + '.outColorR', spine_v_reverse_node + '.inputX', f=True)

    # IK Visibility
    visibility_ik = [cog_ribbon_ctrl, spine_ribbon_ctrl, chest_ribbon_ctrl]

    for obj in visibility_ik:
        cmds.connectAttr(spine_switch_condition_node + '.outColorR', obj + '.v', f=True)

    # Fk Visibility
    visibility_fk = [spine01_ctrl_grp]

    for obj in visibility_fk:
        cmds.connectAttr(spine_v_reverse_node + '.outputX', obj + '.v', f=True)

    # #### FK IK Constraints ####
    cmds.parentConstraint(cog_offset_data_grp, fk_cog_jnt[0], mo=True)
    cog_constraint = cmds.parentConstraint([fk_cog_jnt[0], ik_cog_jnt[0]], rig_joints.get('cog_jnt'))
    spine01_constraint = cmds.parentConstraint([fk_spine01_jnt[0], ik_spine01_jnt[0]], rig_joints.get('spine01_jnt'))
    spine02_constraint = cmds.parentConstraint([fk_spine02_jnt[0], ik_spine02_jnt[0]], rig_joints.get('spine02_jnt'))
    spine03_constraint = cmds.parentConstraint([fk_spine03_jnt[0], ik_spine03_jnt[0]], rig_joints.get('spine03_jnt'))
    spine04_constraint = cmds.parentConstraint([fk_spine04_jnt[0], ik_spine04_jnt[0]], rig_joints.get('spine04_jnt'))

    spine_switch_reverse_node = cmds.createNode('reverse', name='spine_switch_reverse')
    cmds.connectAttr(cog_ctrl + '.spineInfluenceSwitch', spine_switch_reverse_node + '.inputX', f=True)

    # FK
    cmds.connectAttr(spine_switch_reverse_node + '.outputX', cog_constraint[0] + '.w0', f=True)
    cmds.connectAttr(spine_switch_reverse_node + '.outputX', spine01_constraint[0] + '.w0', f=True)
    cmds.connectAttr(spine_switch_reverse_node + '.outputX', spine02_constraint[0] + '.w0', f=True)
    cmds.connectAttr(spine_switch_reverse_node + '.outputX', spine03_constraint[0] + '.w0', f=True)
    cmds.connectAttr(spine_switch_reverse_node + '.outputX', spine04_constraint[0] + '.w0', f=True)

    # IK
    cmds.connectAttr(cog_ctrl + '.spineInfluenceSwitch', cog_constraint[0] + '.w1', f=True)
    cmds.connectAttr(cog_ctrl + '.spineInfluenceSwitch', spine01_constraint[0] + '.w1', f=True)
    cmds.connectAttr(cog_ctrl + '.spineInfluenceSwitch', spine02_constraint[0] + '.w1', f=True)
    cmds.connectAttr(cog_ctrl + '.spineInfluenceSwitch', spine03_constraint[0] + '.w1', f=True)
    cmds.connectAttr(cog_ctrl + '.spineInfluenceSwitch', spine04_constraint[0] + '.w1', f=True)

    # IK FK Spine Mechanics
    cmds.parent(cog_ribbon_ctrl_grp, cog_offset_data_grp)
    cmds.parent(spine_ribbon_ctrl_grp, cog_offset_data_grp)
    cmds.parent(chest_ribbon_ctrl_grp, cog_offset_data_grp)
    spine04_offset_group = cmds.group(name=spine04_ctrl.replace(CTRL_SUFFIX, '') + 'switch_ctrl_grp',
                                      empty=True,
                                      world=True)
    cmds.delete(cmds.parentConstraint(rig_joints.get('spine04_jnt'), spine04_offset_group))
    cmds.parent(right_clavicle_ctrl_grp, spine04_offset_group)
    cmds.parent(left_clavicle_ctrl_grp, spine04_offset_group)

    cmds.parent(spine04_offset_group, main_ctrl)

    neck_base_offset_group = cmds.group(name=neck_base_ctrl.replace(CTRL_SUFFIX, '') + 'switch_ctrl_grp',
                                        empty=True,
                                        world=True)
    cmds.delete(cmds.parentConstraint(rig_joints.get('spine04_jnt'), neck_base_offset_group))
    cmds.parent(neck_base_ctrl_grp, neck_base_offset_group)
    cmds.parent(neck_base_offset_group, main_ctrl)

    # Keep Line of Sight
    head_ik_fk_constraint = cmds.parentConstraint([chest_pivot_data_grp, spine04_ctrl], neck_base_offset_group, mo=True)
    cmds.connectAttr(cog_ctrl + '.spineInfluenceSwitch', head_ik_fk_constraint[0] + '.w0', f=True)
    cmds.connectAttr(spine_switch_reverse_node + '.outputX', head_ik_fk_constraint[0] + '.w1', f=True)
    spine_switcher_constraint = cmds.parentConstraint([rig_joints.get('spine04_jnt'),
                                                       spine04_ctrl],
                                                      spine04_offset_group, mo=True)

    cmds.connectAttr(spine_switch_reverse_node + '.outputX', spine_switcher_constraint[0] + '.w1', f=True)
    cmds.connectAttr(cog_ctrl + '.spineInfluenceSwitch', spine_switcher_constraint[0] + '.w0', f=True)

    inbetween_cog_spine_constraint = cmds.parentConstraint([cog_ribbon_ctrl,
                                                            chest_pivot_data_grp,
                                                            cog_ctrl],
                                                           spine_ribbon_ctrl_grp, mo=True)

    cmds.setAttr(inbetween_cog_spine_constraint[0] + '.interpType', 0)
    cmds.parent(spine_ik_grp, general_automation_grp)

    for jnt in [ik_cog_jnt[0], fk_cog_jnt[0], ribbon_cog_jnt[0], ribbon_spine02_jnt[0], ribbon_spine04_jnt[0]]:
        cmds.setAttr(jnt + '.v', 0)
        cmds.parent(jnt, skeleton_grp)

    # Ribbon Middle Follow Attribute
    cmds.addAttr(spine_ribbon_ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
    cmds.setAttr(spine_ribbon_ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)

    cmds.addAttr(spine_ribbon_ctrl, ln="followChestAndHip", at='double', k=True, maxValue=1, minValue=0)
    cmds.setAttr(spine_ribbon_ctrl + '.followChestAndHip', 1)

    spine_follow_reverse_node = cmds.createNode('reverse', name='spine_follow_reverse')

    cmds.connectAttr(spine_ribbon_ctrl + '.followChestAndHip', spine_follow_reverse_node + '.inputX', f=True)

    cmds.connectAttr(spine_ribbon_ctrl + '.followChestAndHip', inbetween_cog_spine_constraint[0] + '.w0', f=True)
    cmds.connectAttr(spine_ribbon_ctrl + '.followChestAndHip', inbetween_cog_spine_constraint[0] + '.w1', f=True)
    cmds.connectAttr(spine_follow_reverse_node + '.outputX', inbetween_cog_spine_constraint[0] + '.w2', f=True)

    # ############## End Spine Ribbon FK IK Switcher ##############

    # Neck Base
    cmds.parentConstraint(neck_base_ctrl, rig_joints.get('neck_base_jnt'), mo=True)
    base_offset_group = cmds.group(name=neck_base_ctrl + 'OffsetGrp', empty=True, world=True)
    cmds.delete(cmds.parentConstraint(neck_base_ctrl_grp, base_offset_group))
    cmds.parent(base_offset_group, neck_base_ctrl_grp)
    cmds.parent(neck_base_ctrl, base_offset_group)

    # Neck Mid
    cmds.parentConstraint(neck_mid_ctrl, rig_joints.get('neck_mid_jnt'), mo=True)
    mid_offset_group = cmds.group(name=neck_mid_ctrl + 'OffsetGrp', empty=True, world=True)
    cmds.delete(cmds.parentConstraint(neck_mid_ctrl_grp, mid_offset_group))
    cmds.parent(mid_offset_group, neck_mid_ctrl_grp)
    cmds.parent(neck_mid_ctrl, mid_offset_group)

    # Head Ctrl
    cmds.parentConstraint(head_offset_ctrl, rig_joints.get('head_jnt'), mo=True)  # Head drives offset directly
    top_offset_group = cmds.group(name=head_ctrl + 'OffsetGrp', empty=True, world=True)
    cmds.delete(cmds.parentConstraint(head_ctrl_grp, top_offset_group))
    cmds.parent(top_offset_group, head_ctrl_grp)
    cmds.parent(head_ctrl, top_offset_group)

    # ### Neck Head Automation ###
    cmds.addAttr(neck_base_ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
    cmds.setAttr(neck_base_ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)

    cmds.addAttr(neck_base_ctrl, ln='rotationOrder', at='enum', en=ROTATE_ORDER_ENUM, keyable=True,
                 niceName='Rotate Order')
    cmds.connectAttr(neck_base_ctrl + '.rotationOrder', neck_base_ctrl + '.rotateOrder', f=True)

    # Head and Base to Mid
    neck_mid_plus_node = cmds.createNode('plusMinusAverage', name=neck_mid_ctrl.replace(CTRL_SUFFIX, '') + 'sum')
    neck_base_to_mid_multiply_node = cmds.createNode('multiplyDivide',
                                                     name=neck_base_ctrl.replace(CTRL_SUFFIX, 'mid_') + 'influence')
    head_to_mid_multiply_node = cmds.createNode('multiplyDivide',
                                                name=head_ctrl.replace(CTRL_SUFFIX, 'mid_') + 'influence')
    cmds.connectAttr(neck_base_ctrl + '.rotate', neck_base_to_mid_multiply_node + '.input1', f=True)
    cmds.connectAttr(head_ctrl + '.rotate', head_to_mid_multiply_node + '.input1', f=True)
    cmds.connectAttr(neck_base_to_mid_multiply_node + '.output', neck_mid_plus_node + '.input3D[0]', f=True)
    cmds.connectAttr(head_to_mid_multiply_node + '.output', neck_mid_plus_node + '.input3D[1]', f=True)
    cmds.connectAttr(neck_mid_plus_node + '.output3D', mid_offset_group + '.rotate', f=True)

    # Head to NeckMid
    head_to_base_multiply_node = cmds.createNode('multiplyDivide',
                                                 name=head_ctrl.replace(CTRL_SUFFIX, 'base_') + 'influence')
    cmds.connectAttr(head_ctrl + '.rotate', head_to_base_multiply_node + '.input1', f=True)
    cmds.connectAttr(head_to_base_multiply_node + '.output', base_offset_group + '.rotate', f=True)

    # NeckMid to Head
    base_head_to_multiply_node = cmds.createNode('multiplyDivide',
                                                 name=head_ctrl.replace(CTRL_SUFFIX, 'base_') + 'influence')
    cmds.connectAttr(neck_base_ctrl + '.rotate', base_head_to_multiply_node + '.input1', f=True)
    cmds.connectAttr(base_head_to_multiply_node + '.output', top_offset_group + '.rotate', f=True)

    # Neck Mid Visibility
    cmds.addAttr(neck_base_ctrl, ln="neckMidVisibility", at='bool', k=True, niceName='Visibility Neck Mid')

    for shape in cmds.listRelatives(neck_mid_ctrl, s=True, f=True) or []:
        cmds.connectAttr(neck_base_ctrl + '.neckMidVisibility', shape + '.visibility', f=True)

    # Connect Influence Attributes
    cmds.addAttr(head_ctrl, ln='neckBaseInfluence', at='double', k=True, maxValue=1, minValue=0)
    cmds.addAttr(head_ctrl, ln='neckMidInfluence', at='double', k=True, maxValue=1, minValue=0)
    cmds.addAttr(neck_base_ctrl, ln='neckMidInfluence', at='double', k=True, maxValue=1, minValue=0)
    cmds.addAttr(neck_base_ctrl, ln='headInfluence', at='double', k=True, maxValue=1, minValue=0)
    cmds.setAttr(neck_base_ctrl + '.neckMidInfluence', 1)
    # cmds.setAttr(neck_base_ctrl + '.headInfluence', 1)

    for attr in ['X', 'Y', 'Z']:
        cmds.connectAttr(head_ctrl + '.neckBaseInfluence', head_to_base_multiply_node + '.input2' + attr, f=True)
        cmds.connectAttr(head_ctrl + '.neckMidInfluence', head_to_mid_multiply_node + '.input2' + attr, f=True)
        cmds.connectAttr(neck_base_ctrl + '.neckMidInfluence', neck_base_to_mid_multiply_node + '.input2' + attr,
                         f=True)
        cmds.connectAttr(neck_base_ctrl + '.headInfluence', base_head_to_multiply_node + '.input2' + attr, f=True)

    # Jaw Ctrl
    cmds.parentConstraint(jaw_ctrl, rig_joints.get('jaw_jnt'), mo=True)

    # Hip Ctrl
    cmds.parentConstraint(hip_offset_data_grp, rig_joints.get('hip_jnt'), mo=True)

    # ################# Left FK Controls #################
    # Left Leg
    cmds.parentConstraint(left_hip_ctrl, left_hip_fk_jnt, mo=True)
    cmds.parentConstraint(left_knee_ctrl, left_knee_fk_jnt, mo=True)
    cmds.parentConstraint(left_ankle_ctrl, left_ankle_fk_jnt, mo=True)
    cmds.parentConstraint(left_ball_ctrl, left_ball_fk_jnt, mo=True)

    # Left Arm
    cmds.parentConstraint(left_shoulder_ctrl, left_shoulder_fk_jnt, mo=True)
    cmds.parentConstraint(left_elbow_ctrl, left_elbow_fk_jnt, mo=True)
    cmds.parentConstraint(left_wrist_ctrl, left_wrist_fk_jnt, mo=True)

    # Left Fingers
    cmds.parentConstraint(left_thumb01_ctrl_list[0], rig_joints.get('left_thumb01_jnt'))
    cmds.parentConstraint(left_thumb02_ctrl_list[0], rig_joints.get('left_thumb02_jnt'))
    cmds.parentConstraint(left_thumb03_ctrl_list[0], rig_joints.get('left_thumb03_jnt'))

    cmds.parentConstraint(left_index01_ctrl_list[0], rig_joints.get('left_index01_jnt'))
    cmds.parentConstraint(left_index02_ctrl_list[0], rig_joints.get('left_index02_jnt'))
    cmds.parentConstraint(left_index03_ctrl_list[0], rig_joints.get('left_index03_jnt'))

    cmds.parentConstraint(left_middle01_ctrl_list[0], rig_joints.get('left_middle01_jnt'))
    cmds.parentConstraint(left_middle02_ctrl_list[0], rig_joints.get('left_middle02_jnt'))
    cmds.parentConstraint(left_middle03_ctrl_list[0], rig_joints.get('left_middle03_jnt'))

    cmds.parentConstraint(left_ring01_ctrl_list[0], rig_joints.get('left_ring01_jnt'))
    cmds.parentConstraint(left_ring02_ctrl_list[0], rig_joints.get('left_ring02_jnt'))
    cmds.parentConstraint(left_ring03_ctrl_list[0], rig_joints.get('left_ring03_jnt'))

    cmds.parentConstraint(left_pinky01_ctrl_list[0], rig_joints.get('left_pinky01_jnt'))
    cmds.parentConstraint(left_pinky02_ctrl_list[0], rig_joints.get('left_pinky02_jnt'))
    cmds.parentConstraint(left_pinky03_ctrl_list[0], rig_joints.get('left_pinky03_jnt'))

    left_fingers_list = [(left_thumb01_ctrl_list, left_thumb02_ctrl_list, left_thumb03_ctrl_list),
                         (left_index01_ctrl_list, left_index02_ctrl_list, left_index03_ctrl_list),
                         (left_middle01_ctrl_list, left_middle02_ctrl_list, left_middle03_ctrl_list),
                         (left_ring01_ctrl_list, left_ring02_ctrl_list, left_ring03_ctrl_list),
                         (left_pinky01_ctrl_list, left_pinky02_ctrl_list, left_pinky03_ctrl_list)]

    # Add Custom Attributes
    cmds.addAttr(left_fingers_ctrl, ln='fingersAutomation', at='enum', k=True, en='-------------:')
    cmds.addAttr(left_fingers_ctrl, ln='autoRotation', at='bool', k=True)
    cmds.setAttr(left_fingers_ctrl + '.autoRotation', 1)
    cmds.setAttr(left_fingers_ctrl + '.sx', lock=True, k=False, channelBox=False)
    cmds.setAttr(left_fingers_ctrl + '.sy', lock=True, k=False, channelBox=False)
    cmds.setAttr(left_fingers_ctrl + '.fingersAutomation', lock=True)

    # IK Finger Joints
    left_fingers_ik_grp = cmds.group(name='left_ikFingers_grp', world=True, empty=True)
    left_ik_wrist_switch = cmds.duplicate(rig_joints.get('left_wrist_jnt'),
                                          name=rig_joints.get('left_wrist_jnt').replace(JNT_SUFFIX,
                                                                                        'switch_' + JNT_SUFFIX),
                                          po=True)
    cmds.setAttr(left_ik_wrist_switch[0] + '.v', 0)
    change_viewport_color(left_ik_wrist_switch[0], ik_jnt_color)
    cmds.parent(left_ik_wrist_switch, skeleton_grp)
    cmds.parentConstraint(rig_joints.get('left_wrist_jnt'), left_ik_wrist_switch)

    left_ik_finger_chains = []
    for finger in ['thumb', 'index', 'middle', 'ring', 'pinky']:
        left_ik_finger_jnts = []
        finger_name = rig_joints.get('left_' + finger + '01_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX)
        left_ik_finger_jnts.append(cmds.duplicate(rig_joints.get('left_' + finger + '01_jnt'),
                                                  name=finger_name, po=True))
        finger_name = rig_joints.get('left_' + finger + '02_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX)
        left_ik_finger_jnts.append(cmds.duplicate(rig_joints.get('left_' + finger + '02_jnt'),
                                                  name=finger_name, po=True))
        finger_name = rig_joints.get('left_' + finger + '03_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX)
        left_ik_finger_jnts.append(cmds.duplicate(rig_joints.get('left_' + finger + '03_jnt'),
                                                  name=finger_name, po=True))
        finger_name = rig_joints.get('left_' + finger + '04_jnt')
        finger_name = finger_name.replace('end' + JNT_SUFFIX.capitalize(), 'ik_' + 'end' + JNT_SUFFIX.capitalize())
        left_ik_finger_jnts.append(cmds.duplicate(rig_joints.get('left_' + finger + '04_jnt'),
                                                  name=finger_name, po=True))
        left_ik_finger_chains.append(left_ik_finger_jnts)

    ik_finger_handles = []
    for ik_chain in left_ik_finger_chains:
        ik_chain_start = ''
        ik_chain_end = ''
        for index in range(len(ik_chain)):
            change_viewport_color(ik_chain[index][0], ik_jnt_color)
            cmds.setAttr(ik_chain[index][0] + '.radius', (cmds.getAttr(ik_chain[index][0] + '.radius') * .5))
            cmds.setAttr(ik_chain[index][0] + '.preferredAngleZ', -30)
            if index == 0:
                cmds.parent(ik_chain[index][0], left_ik_wrist_switch)
                ik_chain_start = ik_chain[index][0]
            else:
                cmds.parent(ik_chain[index][0], ik_chain[index - 1][0])
            if index == len(ik_chain) - 1:
                ik_chain_end = ik_chain[index][0]

        ik_finger_handles.append(
            cmds.ikHandle(n=ik_chain_start.replace(JNT_SUFFIX, '').replace('01', '') + 'SC_ikHandle', sj=ik_chain_start,
                          ee=ik_chain_end, sol='ikSCsolver'))

    # Constraint IK Skeleton to Base Skeleton and Store Constraints
    finger_switch_constraints = []
    for ik_chain in left_ik_finger_chains:
        for index in range(len(ik_chain)):
            if index != len(ik_chain) - 1:
                finger_name = ik_chain[index][0].replace('left_', '').replace('_ik_', '').replace(JNT_SUFFIX, '')
                finger_switch_constraints.append(
                    cmds.parentConstraint(ik_chain[index][0], rig_joints.get('left_' + finger_name + '_jnt'), mo=True))

    # IK Finger Controls
    ik_finger_ctrls = {}
    left_hand_ik_grp = cmds.group(name='left_ikFingers_switch_ctrl_grp', world=True, empty=True)
    cmds.delete(cmds.parentConstraint(left_hand_grp, left_hand_ik_grp))
    cmds.parent(left_hand_ik_grp, direction_ctrl)
    for ik_handle in ik_finger_handles:
        ik_finger_ctrl = cmds.curve(name=ik_handle[0].replace('SC_ikHandle', 'ctrl'),
                                    p=[[-0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [0.5, 0.5, -0.5], [-0.5, 0.5, -0.5],
                                       [-0.5, 0.5, 0.5], [-0.5, -0.5, 0.5], [-0.5, -0.5, -0.5], [0.5, -0.5, -0.5],
                                       [0.5, -0.5, 0.5], [-0.5, -0.5, 0.5], [0.5, -0.5, 0.5], [0.5, 0.5, 0.5],
                                       [0.5, 0.5, -0.5], [0.5, -0.5, -0.5], [-0.5, -0.5, -0.5], [-0.5, 0.5, -0.5]], d=1)
        cmds.setAttr(ik_finger_ctrl + '.sx', left_arm_scale_offset * .05)
        cmds.setAttr(ik_finger_ctrl + '.sy', left_arm_scale_offset * .05)
        cmds.setAttr(ik_finger_ctrl + '.sz', left_arm_scale_offset * .05)
        cmds.makeIdentity(ik_finger_ctrl, apply=True, scale=True)

        ik_finger_ctrl_grp = cmds.group(name=ik_finger_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
        cmds.parent(ik_finger_ctrl, ik_finger_ctrl_grp)
        cmds.delete(cmds.parentConstraint(ik_handle[0], ik_finger_ctrl_grp))

        # Aim Chain towards middle of the finger (Straight Line)
        ik_start_jnt = cmds.ikHandle(ik_handle[0], q=True, sj=True)
        ik_mid_jnt = cmds.listRelatives(ik_start_jnt, children=True)[0]
        cmds.delete(cmds.aimConstraint(ik_start_jnt, ik_finger_ctrl_grp, aimVector=(-1, 0, 0), worldUpType="object",
                                       worldUpObject=ik_mid_jnt))
        change_viewport_color(ik_finger_ctrl, LEFT_CTRL_COLOR)
        cmds.parentConstraint(ik_finger_ctrl, ik_handle[0], mo=True)
        cmds.parent(ik_finger_ctrl_grp, left_hand_ik_grp)
        cmds.parent(ik_handle[0], left_fingers_ik_grp)
        ik_finger_ctrls[ik_finger_ctrl] = ik_finger_ctrl_grp
        cmds.setAttr(ik_finger_ctrl + '.ry', lock=True, keyable=False)
        cmds.setAttr(ik_finger_ctrl + '.rz', lock=True, keyable=False)
        cmds.setAttr(ik_finger_ctrl + '.sx', lock=True, keyable=False)
        cmds.setAttr(ik_finger_ctrl + '.sy', lock=True, keyable=False)
        cmds.setAttr(ik_finger_ctrl + '.sz', lock=True, keyable=False)
        cmds.setAttr(ik_finger_ctrl + '.v', lock=True, keyable=False)

    cmds.parent(left_fingers_ik_grp, ik_solvers_grp)

    # Left Auto Fist/Splay Offset
    # A list of tuples of tuples 1:[thumb, index...],  2: f_01, f_02, f_03,  3: finger_ctrl, ctrl_grp, ctrl_offset
    for obj in left_fingers_list:
        finger_name = remove_numbers(obj[0][0].replace(CTRL_SUFFIX, ''))

        # Create Nodes
        active_condition_node = cmds.createNode('condition', name=finger_name + AUTO_SUFFIX)
        plus_node = cmds.createNode('plusMinusAverage', name=finger_name + 'addition')
        limit_condition_node = cmds.createNode('condition', name=finger_name + 'limit')
        multiply_node = cmds.createNode('multiplyDivide', name=finger_name + MULTIPLY_SUFFIX)

        attribute_fist_pose_long = finger_name.replace('left_', '').replace('right_', '')
        attribute_fist_pose_long = attribute_fist_pose_long.replace('_', '') + 'FistPoseLimit'
        attribute_fist_pose_nice = finger_name.replace('left_', '').replace('right_', '').replace('_', '').capitalize()
        attribute_fist_pose_nice = 'Fist Pose Limit ' + attribute_fist_pose_nice
        cmds.addAttr(left_fingers_ctrl, ln=attribute_fist_pose_long, at='double', k=True,
                     niceName=attribute_fist_pose_nice)
        cmds.setAttr(left_fingers_ctrl + '.' + attribute_fist_pose_long, -90)

        attribute_long_name = finger_name.replace('left_', '').replace('right_', '').replace('_', '') + 'Multiplier'
        attribute_nice_name = finger_name.replace('left_', '').replace('right_', '').replace('_', '').capitalize()
        attribute_nice_name = 'Rot Multiplier ' + attribute_nice_name
        cmds.addAttr(left_fingers_ctrl, ln=attribute_long_name, at='double', k=True, niceName=attribute_nice_name)

        # Set Default Values
        cmds.setAttr(active_condition_node + '.secondTerm', 1)
        cmds.setAttr(active_condition_node + '.colorIfFalseR', 0)
        cmds.setAttr(active_condition_node + '.colorIfFalseG', 0)
        cmds.setAttr(active_condition_node + '.colorIfFalseB', 0)
        cmds.setAttr(limit_condition_node + '.operation', 3)

        # Offset & Curl
        if 'thumb' in finger_name:
            cmds.setAttr(left_fingers_ctrl + '.' + attribute_long_name, .7)
            cmds.connectAttr(left_curl_thumb_ctrl + '.rz', plus_node + '.input3D[0].input3Dz', f=True)
        elif 'index' in finger_name:
            cmds.setAttr(left_fingers_ctrl + '.' + attribute_long_name, .8)
            cmds.connectAttr(left_curl_index_ctrl + '.rz', plus_node + '.input3D[0].input3Dz', f=True)
        elif 'middle' in finger_name:
            cmds.setAttr(left_fingers_ctrl + '.' + attribute_long_name, .9)
            cmds.connectAttr(left_curl_middle_ctrl + '.rz', plus_node + '.input3D[0].input3Dz', f=True)
        elif 'ring' in finger_name:
            cmds.setAttr(left_fingers_ctrl + '.' + attribute_long_name, 1)
            cmds.connectAttr(left_curl_ring_ctrl + '.rz', plus_node + '.input3D[0].input3Dz', f=True)
        else:
            cmds.setAttr(left_fingers_ctrl + '.' + attribute_long_name, 1)
            cmds.connectAttr(left_curl_pinky_ctrl + '.rz', plus_node + '.input3D[0].input3Dz', f=True)

        # Connect Nodes
        cmds.connectAttr(left_fingers_ctrl + '.autoRotation', active_condition_node + '.firstTerm', f=True)
        cmds.connectAttr(left_fingers_ctrl + '.rotate', multiply_node + '.input1', f=True)
        cmds.connectAttr(left_fingers_ctrl + '.' + attribute_long_name, multiply_node + '.input2X', f=True)
        cmds.connectAttr(left_fingers_ctrl + '.' + attribute_long_name, multiply_node + '.input2Y', f=True)
        cmds.connectAttr(left_fingers_ctrl + '.' + attribute_long_name, multiply_node + '.input2Z', f=True)
        cmds.connectAttr(active_condition_node + '.outColorB', limit_condition_node + '.firstTerm', f=True)
        cmds.connectAttr(multiply_node + '.output', plus_node + '.input3D[1]', f=True)
        cmds.connectAttr(plus_node + '.output3D', active_condition_node + '.colorIfTrue', f=True)
        cmds.connectAttr(active_condition_node + '.outColor', limit_condition_node + '.colorIfTrue', f=True)

        # Set Limits
        cmds.connectAttr(left_fingers_ctrl + '.' + attribute_fist_pose_long, limit_condition_node + '.secondTerm',
                         f=True)
        cmds.connectAttr(left_fingers_ctrl + '.' + attribute_fist_pose_long, limit_condition_node + '.colorIfFalseR',
                         f=True)
        cmds.connectAttr(left_fingers_ctrl + '.' + attribute_fist_pose_long, limit_condition_node + '.colorIfFalseG',
                         f=True)
        cmds.connectAttr(left_fingers_ctrl + '.' + attribute_fist_pose_long, limit_condition_node + '.colorIfFalseB',
                         f=True)

        for finger in obj:
            cmds.connectAttr(active_condition_node + '.outColorR', finger[2] + '.rotateX', f=True)
            cmds.connectAttr(limit_condition_node + '.outColorB', finger[2] + '.rotateZ', f=True)

            # Add Extra Distal Multiply
            if '03' in finger[0]:
                attr_name = 'distalMultiplier'
                attr_name += finger_name.replace('left_', '').replace('right_', '').replace('_', '').capitalize()
                cmds.addAttr(left_fingers_ctrl, ln=attr_name, at='double', k=True)

                end_multiply_node = cmds.createNode('multiplyDivide', name=finger_name + 'endMultiply')
                cmds.connectAttr(limit_condition_node + '.outColorB', end_multiply_node + '.input1Z')
                cmds.connectAttr(end_multiply_node + '.outputZ', finger[2] + '.rotateZ', f=True)
                cmds.connectAttr(left_fingers_ctrl + '.' + attr_name, end_multiply_node + '.input2Z', f=True)
                cmds.setAttr(left_fingers_ctrl + '.' + attr_name, 1)

    # Left Finger Abduction Automation
    left_fingers_minz_scale = 1
    left_fingers_maxz_scale = 5
    left_fingers_min_abduction_rot = -60
    left_fingers_max_abduction_rot = 180

    cmds.setAttr(left_fingers_ctrl + '.sz', 2)
    cmds.addAttr(left_fingers_ctrl, ln='fingersAbduction', at='enum', k=True, en='-------------:')
    cmds.setAttr(left_fingers_ctrl + '.fingersAbduction', lock=True)  # Adduction
    cmds.addAttr(left_fingers_ctrl, ln='arrowVisibility', at='bool', k=True)
    cmds.connectAttr(left_fingers_ctrl + '.arrowVisibility', left_fingers_abduction_ctrl[0] + '.v')
    cmds.setAttr(left_fingers_ctrl + '.arrowVisibility', 1)

    cmds.addAttr(left_fingers_ctrl, ln='abductionInfluence', at='double', k=True, maxValue=1, minValue=0)
    cmds.setAttr(left_fingers_ctrl + '.abductionInfluence', 1)

    left_fingers_decompose_matrix_node = cmds.createNode('decomposeMatrix', name='left_fingers_inverse_matrix')
    cmds.connectAttr(left_fingers_ctrl + '.inverseMatrix', left_fingers_decompose_matrix_node + '.inputMatrix')

    left_fingers_shape_offset_grp = cmds.group(name=left_fingers_ctrl.replace(CTRL_SUFFIX, '') + 'shapeOffsetGrp',
                                               empty=True, world=True)
    cmds.delete(cmds.parentConstraint(left_fingers_ctrl, left_fingers_shape_offset_grp))
    cmds.parent(left_fingers_shape_offset_grp, left_fingers_ctrl_grp)
    cmds.parent(left_fingers_ctrl, left_fingers_shape_offset_grp)

    cmds.connectAttr(left_fingers_decompose_matrix_node + '.outputScale', left_fingers_shape_offset_grp + '.scale')

    left_fingers_inverse_rot_multiply_node = cmds.createNode('multiplyDivide', name='left_fingers_inverseRot_multiply')
    cmds.connectAttr(left_fingers_decompose_matrix_node + '.outputRotate',
                     left_fingers_inverse_rot_multiply_node + '.input1')
    cmds.connectAttr(left_fingers_inverse_rot_multiply_node + '.output', left_fingers_shape_offset_grp + '.rotate')

    cmds.parent(left_fingers_abduction_ctrl[0], left_fingers_ctrl)
    cmds.connectAttr(left_fingers_ctrl + '.scale', left_fingers_abduction_ctrl[1] + '.scale')

    cmds.setAttr(left_fingers_ctrl + '.minScaleZLimit', left_fingers_minz_scale)
    cmds.setAttr(left_fingers_ctrl + '.maxScaleZLimit', left_fingers_maxz_scale)
    cmds.setAttr(left_fingers_ctrl + '.minScaleZLimitEnable', 1)
    cmds.setAttr(left_fingers_ctrl + '.maxScaleZLimitEnable', 1)

    # A list of tuples of tuples 1:[thumb, index...],  2: f_01, f_02, f_03,  3: finger_ctrl, ctrl_grp, ctrl_offset
    for obj in left_fingers_list:
        # Unpack Elements
        finger_name = remove_numbers(obj[0][0].replace(CTRL_SUFFIX, ''))
        ctrl_offset = obj[0][2]

        # ### Abduction/Adduction System ###
        abduction_blend_node = cmds.createNode('blendTwoAttr', name=finger_name + 'abduction_blend')
        abduction_multiply_node = cmds.createNode('multiplyDivide', name=finger_name + 'abduction_multiply')
        abduction_range_node = cmds.createNode('setRange', name=finger_name + 'abduction_range')
        abduction_sum_node = cmds.createNode('plusMinusAverage', name=finger_name + 'abduction_sum')
        cmds.setAttr(abduction_range_node + '.oldMinZ', left_fingers_minz_scale)
        cmds.setAttr(abduction_range_node + '.oldMaxZ', left_fingers_maxz_scale)
        cmds.setAttr(abduction_range_node + '.minZ', left_fingers_min_abduction_rot)
        cmds.setAttr(abduction_range_node + '.maxZ', left_fingers_max_abduction_rot)
        cmds.connectAttr(left_fingers_ctrl + '.sz', abduction_range_node + '.valueZ', f=True)
        cmds.connectAttr(abduction_range_node + '.outValueZ', abduction_multiply_node + '.input1X', f=True)
        cmds.connectAttr(abduction_multiply_node + '.outputX', abduction_blend_node + '.input[1]', f=True)
        cmds.connectAttr(abduction_blend_node + '.output', abduction_sum_node + '.input3D[0].input3Dy')
        cmds.connectAttr(abduction_sum_node + '.output3Dx', ctrl_offset + '.rx', force=True)
        cmds.connectAttr(abduction_sum_node + '.output3Dy', ctrl_offset + '.ry')
        cmds.connectAttr(left_fingers_ctrl + '.abductionInfluence', abduction_blend_node + '.attributesBlender')
        cmds.setAttr(abduction_blend_node + ".input[0]", 0)

        if 'thumb' in finger_name:
            # Abduction/Adduction
            cmds.addAttr(left_fingers_ctrl, ln='rotMultiplierThumb', at='double', k=True)
            cmds.setAttr(left_fingers_ctrl + '.rotMultiplierThumb', -.1)
            cmds.connectAttr(left_fingers_ctrl + '.rotMultiplierThumb', abduction_multiply_node + '.input2X', f=True)
        elif 'index' in finger_name:
            # Abduction/Adduction
            cmds.addAttr(left_fingers_ctrl, ln='rotMultiplierIndex', at='double', k=True)
            cmds.setAttr(left_fingers_ctrl + '.rotMultiplierIndex', -.7)
            cmds.connectAttr(left_fingers_ctrl + '.rotMultiplierIndex', abduction_multiply_node + '.input2X', f=True)
        elif 'middle' in finger_name:
            # Abduction/Adduction
            cmds.addAttr(left_fingers_ctrl, ln='rotMultiplierMiddle', at='double', k=True)
            cmds.setAttr(left_fingers_ctrl + '.rotMultiplierMiddle', -.3)
            cmds.connectAttr(left_fingers_ctrl + '.rotMultiplierMiddle', abduction_multiply_node + '.input2X', f=True)
        elif 'ring' in finger_name:
            # Abduction/Adduction
            cmds.addAttr(left_fingers_ctrl, ln='rotMultiplierRing', at='double', k=True)
            cmds.setAttr(left_fingers_ctrl + '.rotMultiplierRing', .2)
            cmds.connectAttr(left_fingers_ctrl + '.rotMultiplierRing', abduction_multiply_node + '.input2X', f=True)
        elif 'pinky' in finger_name:
            # Abduction/Adduction
            cmds.addAttr(left_fingers_ctrl, ln='rotMultiplierPinky', at='double', k=True)
            cmds.setAttr(left_fingers_ctrl + '.rotMultiplierPinky', .7)
            cmds.connectAttr(left_fingers_ctrl + '.rotMultiplierPinky', abduction_multiply_node + '.input2X', f=True)

    # Left Auto Knuckle Compression System (Translation Z Offset)
    cmds.addAttr(left_fingers_ctrl, ln='knucklesAutomation', at='enum', k=True, en='-------------:')
    cmds.setAttr(left_fingers_ctrl + '.knucklesAutomation', lock=True)
    cmds.addAttr(left_fingers_ctrl, ln='showCompressionCtrls', at='bool', k=True, maxValue=1, minValue=0)
    cmds.addAttr(left_fingers_ctrl, ln='autoCompression', at='double', k=True, maxValue=1, minValue=0)
    cmds.setAttr(left_fingers_ctrl + '.autoCompression', 1)
    cmds.addAttr(left_fingers_ctrl, ln='transCompression', at='double', k=True, minValue=0)
    cmds.setAttr(left_fingers_ctrl + '.transCompression', 1)

    left_knuckle_blend_node = cmds.createNode('blendTwoAttr', name='left_knuckle_compression_blend')
    left_knuckle_reverse_node = cmds.createNode('reverse', name='left_knuckle_compression_reverse')
    cmds.connectAttr(left_fingers_ctrl + '.autoCompression', left_knuckle_blend_node + '.attributesBlender')
    cmds.setAttr(left_knuckle_blend_node + '.input[0]', 0)
    left_compression_range_node = cmds.createNode('setRange', name='left_knuckle_compression_range')
    cmds.connectAttr(left_fingers_ctrl + '.rz', left_knuckle_reverse_node + '.inputZ', f=True)
    cmds.connectAttr(left_knuckle_reverse_node + '.outputZ', left_compression_range_node + '.valueZ', f=True)
    cmds.connectAttr(left_compression_range_node + '.outValueZ', left_knuckle_blend_node + '.input[1]', f=True)
    cmds.setAttr(left_compression_range_node + '.oldMaxZ', 180)
    cmds.connectAttr(left_fingers_ctrl + '.transCompression', left_compression_range_node + '.maxZ', f=True)
    # Rotation System
    cmds.addAttr(left_fingers_ctrl, ln='rotCompression', at='double', k=True, minValue=0)
    cmds.setAttr(left_fingers_ctrl + '.rotCompression', 10)
    left_knuckle_rot_blend_node = cmds.createNode('blendTwoAttr', name='left_knuckle_rotCompression_blend')
    left_knuckle_rot_range_node = cmds.createNode('setRange', name='left_knuckle_rotCompression_range')
    knuckle_rot_multiply_node = cmds.createNode('multiplyDivide', name='left_knuckle_rotCompression_influence')
    cmds.connectAttr(left_fingers_ctrl + '.autoCompression', knuckle_rot_multiply_node + '.input1X')
    cmds.connectAttr(left_fingers_ctrl + '.rotCompression', knuckle_rot_multiply_node + '.input2X')
    cmds.connectAttr(knuckle_rot_multiply_node + '.outputX', left_knuckle_rot_blend_node + '.input[0]')
    cmds.setAttr(left_knuckle_rot_blend_node + '.input[1]', 0)
    cmds.connectAttr(left_fingers_ctrl + '.minimumRotationZ', left_knuckle_rot_range_node + '.oldMinZ')
    cmds.connectAttr(left_fingers_ctrl + '.rz', left_knuckle_rot_range_node + '.valueZ')
    cmds.setAttr(left_knuckle_rot_range_node + '.maxZ', 1)
    cmds.connectAttr(left_knuckle_rot_range_node + '.outValueZ', left_knuckle_rot_blend_node + '.attributesBlender')

    # Left Manual Compression Controls
    left_compression_ctrl_output = []
    left_compression_joints = [rig_joints.get('left_index01_jnt'),
                               rig_joints.get('left_middle01_jnt'),
                               rig_joints.get('left_ring01_jnt'),
                               rig_joints.get('left_pinky01_jnt')]
    for joint in left_compression_joints:
        name = joint.replace(JNT_SUFFIX, '')
        left_compression_ctrl = cmds.curve(name=name + 'compression_ctrl',
                                           p=[[0.0, 0.28, 0.0], [-0.28, 0.001, 0.0], [0.0, 0.0, 0.28],
                                              [0.0, 0.28, 0.0], [0.28, 0.001, 0.0], [0.0, 0.0, 0.28],
                                              [0.28, 0.001, 0.0], [0.0, 0.0, -0.28], [0.0, 0.28, 0.0],
                                              [0.0, 0.0, -0.28], [-0.28, 0.001, 0.0], [0.0, -0.28, 0.0],
                                              [0.0, 0.0, -0.28], [0.28, 0.001, 0.0], [0.0, -0.28, 0.0],
                                              [0.0, 0.0, 0.28]], d=1)
        left_compression_ctrl_grp = cmds.group(name=left_compression_ctrl + GRP_SUFFIX.capitalize(),
                                               empty=True, world=True)
        cmds.parent(left_compression_ctrl, left_compression_ctrl_grp)
        rescale(left_compression_ctrl, left_wrist_scale_offset * .3)
        cmds.delete(cmds.parentConstraint(left_fingers_ctrl, left_compression_ctrl_grp))
        cmds.delete(cmds.pointConstraint(joint, left_compression_ctrl_grp))
        cmds.move(left_wrist_scale_offset * .3, left_compression_ctrl_grp, moveY=True, relative=True, objectSpace=True)
        cmds.move(-left_wrist_scale_offset * .2, left_compression_ctrl_grp, moveX=True, relative=True, objectSpace=True)
        lock_hide_default_attr(left_compression_ctrl, rotate=False)
        cmds.setAttr(left_compression_ctrl + '.rx', lock=True, keyable=False)
        cmds.setAttr(left_compression_ctrl + '.ry', lock=True, keyable=False)
        change_viewport_color(left_compression_ctrl, LEFT_CTRL_COLOR)
        manual_multiply_node = cmds.createNode('multiplyDivide', name=name + 'compressionInfluence')
        cmds.addAttr(left_compression_ctrl, ln='influence', at='double', k=True)
        cmds.setAttr(left_compression_ctrl + '.influence', .1)
        cmds.connectAttr(left_compression_ctrl + '.rz', manual_multiply_node + '.input1Z')
        cmds.connectAttr(left_compression_ctrl + '.influence', manual_multiply_node + '.input2Z')
        cmds.connectAttr(left_fingers_ctrl + '.showCompressionCtrls', left_compression_ctrl_grp + '.v')
        cmds.parent(left_compression_ctrl_grp, left_fingers_ctrl_grp)
        left_compression_ctrl_output.append(manual_multiply_node)

    # Knuckle Compression
    for obj in left_fingers_list:
        # Unpack Elements
        finger_name = remove_numbers(obj[0][0].replace(CTRL_SUFFIX, ''))
        ctrl_offset = obj[0][2]

        # Knuckle Compression System
        knuckle_multiply_node = ''
        knuckle_rot_multiply_node = ''
        knuckle_sum_node = ''
        if 'thumb' not in ctrl_offset:
            knuckle_multiply_node = cmds.createNode('multiplyDivide', name=finger_name + 'compression_multiply')
            knuckle_sum_node = cmds.createNode('plusMinusAverage', name=finger_name + 'compression_sum')
            cmds.connectAttr(left_knuckle_blend_node + '.output', knuckle_multiply_node + '.input1Z')
            cmds.connectAttr(knuckle_multiply_node + '.outputZ', knuckle_sum_node + '.input1D[0]')
            cmds.connectAttr(knuckle_sum_node + '.output1D', ctrl_offset + '.tz')

            # Rot System
            knuckle_rot_multiply_node = cmds.createNode('multiplyDivide', name=finger_name + 'rotCompression_multiply')
            cmds.connectAttr(left_knuckle_rot_blend_node + '.output', knuckle_rot_multiply_node + '.input2Y')
            cmds.connectAttr(left_knuckle_rot_blend_node + '.output', knuckle_rot_multiply_node + '.input2X')
            cmds.connectAttr(knuckle_rot_multiply_node + '.output', finger_name + 'abduction_sum.input3D[1]')

        # Connections
        if 'index' in finger_name:
            # Trans
            cmds.addAttr(left_fingers_ctrl, ln='transMultiplierIndex', at='double', k=True)
            cmds.setAttr(left_fingers_ctrl + '.transMultiplierIndex', -1.5)
            cmds.connectAttr(left_fingers_ctrl + '.transMultiplierIndex', knuckle_multiply_node + '.input2Z')
            cmds.connectAttr(left_compression_ctrl_output[0] + '.outputZ', knuckle_sum_node + '.input1D[1]')
            # Rot
            nice_name_y = 'Rot Y Multiplier Index'
            nice_name_x = 'Rot X Multiplier Index'
            cmds.addAttr(left_fingers_ctrl, ln='rotCompMultiplierIndexY', at='double', k=True, niceName=nice_name_y)
            cmds.setAttr(left_fingers_ctrl + '.rotCompMultiplierIndexY', 0.5)
            cmds.addAttr(left_fingers_ctrl, ln='rotCompMultiplierIndexX', at='double', k=True, niceName=nice_name_x)
            cmds.setAttr(left_fingers_ctrl + '.rotCompMultiplierIndexX', 0)
            cmds.connectAttr(left_fingers_ctrl + '.rotCompMultiplierIndexY', knuckle_rot_multiply_node + '.input1Y')
            cmds.connectAttr(left_fingers_ctrl + '.rotCompMultiplierIndexX', knuckle_rot_multiply_node + '.input1X')
        elif 'middle' in finger_name:
            # Trans
            cmds.addAttr(left_fingers_ctrl, ln='transMultiplierMiddle', at='double', k=True)
            cmds.setAttr(left_fingers_ctrl + '.transMultiplierMiddle', -.5)
            cmds.connectAttr(left_fingers_ctrl + '.transMultiplierMiddle', knuckle_multiply_node + '.input2Z')
            cmds.connectAttr(left_compression_ctrl_output[1] + '.outputZ', knuckle_sum_node + '.input1D[1]')
            # Rot
            nice_name_y = 'Rot Y Multiplier Middle'
            nice_name_x = 'Rot X Multiplier Middle'
            cmds.addAttr(left_fingers_ctrl, ln='rotCompMultiplierMiddleY', at='double', k=True, niceName=nice_name_y)
            cmds.setAttr(left_fingers_ctrl + '.rotCompMultiplierMiddleY', 0.25)
            cmds.addAttr(left_fingers_ctrl, ln='rotCompMultiplierMiddleX', at='double', k=True, niceName=nice_name_x)
            cmds.setAttr(left_fingers_ctrl + '.rotCompMultiplierMiddleX', 0)
            cmds.connectAttr(left_fingers_ctrl + '.rotCompMultiplierMiddleY', knuckle_rot_multiply_node + '.input1Y')
            cmds.connectAttr(left_fingers_ctrl + '.rotCompMultiplierMiddleX', knuckle_rot_multiply_node + '.input1X')
        elif 'ring' in finger_name:
            # Trans
            cmds.addAttr(left_fingers_ctrl, ln='transMultiplierRing', at='double', k=True)
            cmds.setAttr(left_fingers_ctrl + '.transMultiplierRing', .5)
            cmds.connectAttr(left_fingers_ctrl + '.transMultiplierRing', knuckle_multiply_node + '.input2Z')
            cmds.connectAttr(left_compression_ctrl_output[2] + '.outputZ', knuckle_sum_node + '.input1D[1]')
            # Rot
            nice_name_y = 'Rot Y Multiplier Ring'
            nice_name_x = 'Rot X Multiplier Ring'
            cmds.addAttr(left_fingers_ctrl, ln='rotCompMultiplierRingY', at='double', k=True, niceName=nice_name_y)
            cmds.setAttr(left_fingers_ctrl + '.rotCompMultiplierRingY', -0.25)
            cmds.addAttr(left_fingers_ctrl, ln='rotCompMultiplierRingX', at='double', k=True, niceName=nice_name_x)
            cmds.setAttr(left_fingers_ctrl + '.rotCompMultiplierRingX', 0)
            cmds.connectAttr(left_fingers_ctrl + '.rotCompMultiplierRingY', knuckle_rot_multiply_node + '.input1Y')
            cmds.connectAttr(left_fingers_ctrl + '.rotCompMultiplierRingX', knuckle_rot_multiply_node + '.input1X')
        elif 'pinky' in finger_name:
            # Trans
            cmds.addAttr(left_fingers_ctrl, ln='transMultiplierPinky', at='double', k=True)
            cmds.setAttr(left_fingers_ctrl + '.transMultiplierPinky', 1.5)
            cmds.connectAttr(left_fingers_ctrl + '.transMultiplierPinky', knuckle_multiply_node + '.input2Z')
            cmds.connectAttr(left_compression_ctrl_output[3] + '.outputZ', knuckle_sum_node + '.input1D[1]')
            # Rot
            nice_name_y = 'Rot Y Multiplier Pinky'
            nice_name_x = 'Rot X Multiplier Pinky'
            cmds.addAttr(left_fingers_ctrl, ln='rotCompMultiplierPinkyY', at='double', k=True, niceName=nice_name_y)
            cmds.setAttr(left_fingers_ctrl + '.rotCompMultiplierPinkyY', -0.5)
            cmds.addAttr(left_fingers_ctrl, ln='rotCompMultiplierPinkyX', at='double', k=True, niceName=nice_name_x)
            cmds.setAttr(left_fingers_ctrl + '.rotCompMultiplierPinkyX', 0)
            cmds.connectAttr(left_fingers_ctrl + '.rotCompMultiplierPinkyY', knuckle_rot_multiply_node + '.input1Y')
            cmds.connectAttr(left_fingers_ctrl + '.rotCompMultiplierPinkyX', knuckle_rot_multiply_node + '.input1X')

    # Create FK/IK Switch for Fingers
    cmds.addAttr(left_fingers_ctrl, ln='switchAttributes', at='enum', k=True, en='-------------:')
    cmds.setAttr(left_fingers_ctrl + '.switchAttributes', lock=True)
    cmds.addAttr(left_fingers_ctrl, ln='influenceSwitch', at='double', k=True, maxValue=1, minValue=0)
    cmds.setAttr(left_fingers_ctrl + '.influenceSwitch', 1)

    left_fingers_visibility_condition_node = cmds.createNode('condition', name='left_fingers_ikVisibility_condition')

    cmds.connectAttr(left_fingers_ctrl + '.influenceSwitch', left_fingers_visibility_condition_node + '.firstTerm',
                     f=True)
    cmds.setAttr(left_fingers_visibility_condition_node + '.operation', 4)
    cmds.setAttr(left_fingers_visibility_condition_node + '.secondTerm', .5)
    cmds.setAttr(left_fingers_visibility_condition_node + '.colorIfTrueR', 1)
    cmds.setAttr(left_fingers_visibility_condition_node + '.colorIfTrueG', 1)
    cmds.setAttr(left_fingers_visibility_condition_node + '.colorIfTrueB', 1)
    cmds.setAttr(left_fingers_visibility_condition_node + '.colorIfFalseR', 0)
    cmds.setAttr(left_fingers_visibility_condition_node + '.colorIfFalseG', 0)
    cmds.setAttr(left_fingers_visibility_condition_node + '.colorIfFalseB', 0)

    for ctrl in ik_finger_ctrls:
        for shape in cmds.listRelatives(ctrl, s=True, f=True) or []:
            cmds.connectAttr(left_fingers_visibility_condition_node + '.outColorR', shape + '.v', f=True)

    reverse_node = cmds.createNode('reverse', name='left_fingers_ik_reverse')
    cmds.connectAttr(left_fingers_ctrl + '.influenceSwitch', reverse_node + '.inputX', f=True)

    for constraint in finger_switch_constraints:
        cmds.connectAttr(left_fingers_ctrl + '.influenceSwitch', constraint[0] + '.w0', f=True)
        cmds.connectAttr(reverse_node + '.outputX', constraint[0] + '.w1', f=True)

    # Create Parenting Switcher for Fingers
    cmds.addAttr(left_fingers_ctrl, ln='ikParent', at='enum', k=True, en="World:Wrist:", niceName="IK Fingers Parent")
    cmds.setAttr(left_fingers_ctrl + '.ikParent', 1)
    ik_fingers_system_constraint = cmds.parentConstraint([controls_grp, left_hand_grp], left_hand_ik_grp, mo=True)

    left_ik_fingers_world_condition_node = cmds.createNode('condition',
                                                           name='left_ikFingers_parentWorld_' + AUTO_SUFFIX)
    left_ik_fingers_wrist_condition_node = cmds.createNode('condition',
                                                           name='left_ikFingers_parentWrist_' + AUTO_SUFFIX)

    cmds.setAttr(left_ik_fingers_world_condition_node + '.secondTerm', 0)
    cmds.setAttr(left_ik_fingers_wrist_condition_node + '.secondTerm', 1)

    for node in [left_ik_fingers_world_condition_node, left_ik_fingers_wrist_condition_node]:
        cmds.setAttr(node + '.colorIfTrueR', 1)
        cmds.setAttr(node + '.colorIfTrueG', 1)
        cmds.setAttr(node + '.colorIfTrueB', 1)
        cmds.setAttr(node + '.colorIfFalseR', 0)
        cmds.setAttr(node + '.colorIfFalseG', 0)
        cmds.setAttr(node + '.colorIfFalseB', 0)

    cmds.connectAttr(left_fingers_ctrl + '.ikParent', left_ik_fingers_world_condition_node + '.firstTerm', f=True)
    cmds.connectAttr(left_fingers_ctrl + '.ikParent', left_ik_fingers_wrist_condition_node + '.firstTerm', f=True)

    cmds.connectAttr(left_ik_fingers_world_condition_node + '.outColorR', ik_fingers_system_constraint[0] + '.w0',
                     f=True)
    cmds.connectAttr(left_ik_fingers_wrist_condition_node + '.outColorR', ik_fingers_system_constraint[0] + '.w1',
                     f=True)

    # Control Specific Parenting System
    for ctrl in ik_finger_ctrls:
        fk_parent_name = ctrl.replace('_ik_' + CTRL_SUFFIX, '03_' + CTRL_SUFFIX)
        inbetween_transform = cmds.group(name=(ctrl + 'FkOffset'), empty=True)
        parent_override_transform = cmds.group(name=(ctrl + 'ParentOverride'), empty=True)
        cmds.parent(parent_override_transform, inbetween_transform)
        ctrl_parent = cmds.listRelatives(ctrl, parent=True) or []
        cmds.delete(cmds.parentConstraint(ctrl_parent[0], inbetween_transform))
        cmds.parent(inbetween_transform, ctrl_parent[0])
        cmds.parent(ctrl, parent_override_transform)

        cmds.addAttr(ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', k=True, en='-------------:')
        cmds.setAttr(ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)
        cmds.addAttr(ctrl, ln='ikFollowsFk', at='double', k=True, maxValue=1, minValue=0, niceName='IK Follows FK')
        cmds.setAttr(ctrl + '.ikFollowsFk', 1)
        cmds.addAttr(ctrl, ln='forceWorldParenting', at='double', k=True, maxValue=1, minValue=0)

        condition_node = cmds.createNode('condition', name=ctrl.replace('_ik_' + CTRL_SUFFIX, '_condition'))
        parent_constraint = cmds.parentConstraint([left_hand_ik_grp, fk_parent_name], inbetween_transform, mo=True)

        cmds.connectAttr(left_fingers_ctrl + '.ikParent', condition_node + '.firstTerm', f=True)
        cmds.setAttr(condition_node + '.colorIfFalseR', 0)
        cmds.setAttr(condition_node + '.colorIfFalseG', 0)
        cmds.setAttr(condition_node + '.colorIfFalseB', 0)

        cmds.connectAttr(ctrl + '.ikFollowsFk', condition_node + '.colorIfFalseR', f=True)
        cmds.connectAttr(condition_node + '.outColorR', parent_constraint[0] + '.w1', f=True)

        reverse_node = cmds.createNode('reverse', name=ctrl.replace('_ik_' + CTRL_SUFFIX, '_reverse'))
        cmds.connectAttr(condition_node + '.outColorR', reverse_node + '.inputX', f=True)
        cmds.connectAttr(reverse_node + '.outputX', parent_constraint[0] + '.w0', f=True)

        # Force World Parent
        cmds.parentConstraint(inbetween_transform, parent_override_transform)
        parent_override_constraint = cmds.parentConstraint(controls_grp, parent_override_transform, mo=True)

        cmds.connectAttr(ctrl + '.forceWorldParenting', parent_override_constraint[0] + '.w1', f=True)
        override_reverse_node = cmds.createNode('reverse',
                                                name=ctrl.replace('_worldOverride_' + CTRL_SUFFIX, '_reverse'))
        cmds.connectAttr(ctrl + '.forceWorldParenting', override_reverse_node + '.inputX', f=True)
        cmds.connectAttr(override_reverse_node + '.outputX', parent_override_constraint[0] + '.w0', f=True)

    # ################# Right FK Controls #################
    # Right Leg
    cmds.parentConstraint(right_hip_ctrl, right_hip_fk_jnt, mo=True)
    cmds.parentConstraint(right_knee_ctrl, right_knee_fk_jnt, mo=True)
    cmds.parentConstraint(right_ankle_ctrl, right_ankle_fk_jnt, mo=True)
    cmds.parentConstraint(right_ball_ctrl, right_ball_fk_jnt, mo=True)

    # Right Arm
    cmds.parentConstraint(right_shoulder_ctrl, right_shoulder_fk_jnt, mo=True)
    cmds.parentConstraint(right_elbow_ctrl, right_elbow_fk_jnt, mo=True)
    cmds.parentConstraint(right_wrist_ctrl, right_wrist_fk_jnt, mo=True)

    # Right Fingers
    cmds.parentConstraint(right_thumb01_ctrl_list[0], rig_joints.get('right_thumb01_jnt'))
    cmds.parentConstraint(right_thumb02_ctrl_list[0], rig_joints.get('right_thumb02_jnt'))
    cmds.parentConstraint(right_thumb03_ctrl_list[0], rig_joints.get('right_thumb03_jnt'))

    cmds.parentConstraint(right_index01_ctrl_list[0], rig_joints.get('right_index01_jnt'))
    cmds.parentConstraint(right_index02_ctrl_list[0], rig_joints.get('right_index02_jnt'))
    cmds.parentConstraint(right_index03_ctrl_list[0], rig_joints.get('right_index03_jnt'))

    cmds.parentConstraint(right_middle01_ctrl_list[0], rig_joints.get('right_middle01_jnt'))
    cmds.parentConstraint(right_middle02_ctrl_list[0], rig_joints.get('right_middle02_jnt'))
    cmds.parentConstraint(right_middle03_ctrl_list[0], rig_joints.get('right_middle03_jnt'))

    cmds.parentConstraint(right_ring01_ctrl_list[0], rig_joints.get('right_ring01_jnt'))
    cmds.parentConstraint(right_ring02_ctrl_list[0], rig_joints.get('right_ring02_jnt'))
    cmds.parentConstraint(right_ring03_ctrl_list[0], rig_joints.get('right_ring03_jnt'))

    cmds.parentConstraint(right_pinky01_ctrl_list[0], rig_joints.get('right_pinky01_jnt'))
    cmds.parentConstraint(right_pinky02_ctrl_list[0], rig_joints.get('right_pinky02_jnt'))
    cmds.parentConstraint(right_pinky03_ctrl_list[0], rig_joints.get('right_pinky03_jnt'))

    right_fingers_list = [(right_thumb01_ctrl_list, right_thumb02_ctrl_list, right_thumb03_ctrl_list),
                          (right_index01_ctrl_list, right_index02_ctrl_list, right_index03_ctrl_list),
                          (right_middle01_ctrl_list, right_middle02_ctrl_list, right_middle03_ctrl_list),
                          (right_ring01_ctrl_list, right_ring02_ctrl_list, right_ring03_ctrl_list),
                          (right_pinky01_ctrl_list, right_pinky02_ctrl_list, right_pinky03_ctrl_list)]

    # Add Custom Attributes
    cmds.addAttr(right_fingers_ctrl, ln='fingersAutomation', at='enum', k=True, en='-------------:')
    cmds.addAttr(right_fingers_ctrl, ln='autoRotation', at='bool', k=True)
    cmds.setAttr(right_fingers_ctrl + '.autoRotation', 1)

    cmds.setAttr(right_fingers_ctrl + '.sx', lock=True, k=False, channelBox=False)
    cmds.setAttr(right_fingers_ctrl + '.sy', lock=True, k=False, channelBox=False)
    cmds.setAttr(right_fingers_ctrl + '.fingersAutomation', lock=True)

    # IK Finger Joints
    right_fingers_ik_grp = cmds.group(name='right_ikFingers_grp', world=True, empty=True)
    right_ik_wrist_switch = cmds.duplicate(rig_joints.get('right_wrist_jnt'),
                                           name=rig_joints.get('right_wrist_jnt').replace(JNT_SUFFIX,
                                                                                          'switch_' + JNT_SUFFIX),
                                           po=True)
    cmds.setAttr(right_ik_wrist_switch[0] + '.v', 0)
    change_viewport_color(right_ik_wrist_switch[0], ik_jnt_color)
    cmds.parent(right_ik_wrist_switch, skeleton_grp)
    cmds.parentConstraint(rig_joints.get('right_wrist_jnt'), right_ik_wrist_switch)

    right_ik_finger_chains = []
    for finger in ['thumb', 'index', 'middle', 'ring', 'pinky']:
        right_ik_finger_jnts = []
        finger_name = rig_joints.get('right_' + finger + '01_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX)
        right_ik_finger_jnts.append(cmds.duplicate(rig_joints.get('right_' + finger + '01_jnt'),
                                                   name=finger_name, po=True))
        finger_name = rig_joints.get('right_' + finger + '02_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX)
        right_ik_finger_jnts.append(cmds.duplicate(rig_joints.get('right_' + finger + '02_jnt'),
                                                   name=finger_name, po=True))
        finger_name = rig_joints.get('right_' + finger + '03_jnt').replace(JNT_SUFFIX, 'ik_' + JNT_SUFFIX)
        right_ik_finger_jnts.append(cmds.duplicate(rig_joints.get('right_' + finger + '03_jnt'),
                                                   name=finger_name, po=True))
        finger_name = rig_joints.get('right_' + finger + '04_jnt')
        finger_name = finger_name.replace('end' + JNT_SUFFIX.capitalize(), 'ik_' + 'end' + JNT_SUFFIX.capitalize())
        right_ik_finger_jnts.append(cmds.duplicate(rig_joints.get('right_' + finger + '04_jnt'),
                                                   name=finger_name, po=True))
        right_ik_finger_chains.append(right_ik_finger_jnts)

    ik_finger_handles = []
    for ik_chain in right_ik_finger_chains:
        ik_chain_start = ''
        ik_chain_end = ''
        for index in range(len(ik_chain)):
            change_viewport_color(ik_chain[index][0], ik_jnt_color)
            cmds.setAttr(ik_chain[index][0] + '.radius', (cmds.getAttr(ik_chain[index][0] + '.radius') * .5))
            cmds.setAttr(ik_chain[index][0] + '.preferredAngleZ', -30)
            if index == 0:
                cmds.parent(ik_chain[index][0], right_ik_wrist_switch)
                ik_chain_start = ik_chain[index][0]
            else:
                cmds.parent(ik_chain[index][0], ik_chain[index - 1][0])
            if index == len(ik_chain) - 1:
                ik_chain_end = ik_chain[index][0]

        ik_finger_handles.append(
            cmds.ikHandle(n=ik_chain_start.replace(JNT_SUFFIX, '').replace('01', '') + 'SC_ikHandle', sj=ik_chain_start,
                          ee=ik_chain_end, sol='ikSCsolver'))

    # Constraint IK Skeleton to Base Skeleton and Store Constraints
    finger_switch_constraints = []
    for ik_chain in right_ik_finger_chains:
        for index in range(len(ik_chain)):
            if index != len(ik_chain) - 1:
                finger_name = ik_chain[index][0].replace('right_', '').replace('_ik_', '').replace(JNT_SUFFIX, '')
                finger_switch_constraints.append(
                    cmds.parentConstraint(ik_chain[index][0], rig_joints.get('right_' + finger_name + '_jnt'), mo=True))

    # IK Finger Controls
    ik_finger_ctrls = {}
    right_hand_ik_grp = cmds.group(name='right_ikFingers_switch_ctrl_grp', world=True, empty=True)
    cmds.delete(cmds.parentConstraint(right_hand_grp, right_hand_ik_grp))
    cmds.parent(right_hand_ik_grp, direction_ctrl)
    for ik_handle in ik_finger_handles:
        ik_finger_ctrl = cmds.curve(name=ik_handle[0].replace('SC_ikHandle', 'ctrl'),
                                    p=[[-0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [0.5, 0.5, -0.5], [-0.5, 0.5, -0.5],
                                       [-0.5, 0.5, 0.5], [-0.5, -0.5, 0.5], [-0.5, -0.5, -0.5], [0.5, -0.5, -0.5],
                                       [0.5, -0.5, 0.5], [-0.5, -0.5, 0.5], [0.5, -0.5, 0.5], [0.5, 0.5, 0.5],
                                       [0.5, 0.5, -0.5], [0.5, -0.5, -0.5], [-0.5, -0.5, -0.5], [-0.5, 0.5, -0.5]], d=1)
        cmds.setAttr(ik_finger_ctrl + '.sx', right_arm_scale_offset * .05)
        cmds.setAttr(ik_finger_ctrl + '.sy', right_arm_scale_offset * .05)
        cmds.setAttr(ik_finger_ctrl + '.sz', right_arm_scale_offset * .05)
        cmds.makeIdentity(ik_finger_ctrl, apply=True, scale=True)

        ik_finger_ctrl_grp = cmds.group(name=ik_finger_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
        cmds.parent(ik_finger_ctrl, ik_finger_ctrl_grp)
        cmds.delete(cmds.parentConstraint(ik_handle[0], ik_finger_ctrl_grp))

        # Aim Chain towards middle of the finger (Straight Line)
        ik_start_jnt = cmds.ikHandle(ik_handle[0], q=True, sj=True)
        ik_mid_jnt = cmds.listRelatives(ik_start_jnt, children=True)[0]
        cmds.delete(cmds.aimConstraint(ik_start_jnt, ik_finger_ctrl_grp, aimVector=(-1, 0, 0), worldUpType="object",
                                       worldUpObject=ik_mid_jnt))
        change_viewport_color(ik_finger_ctrl, RIGHT_CTRL_COLOR)
        cmds.parentConstraint(ik_finger_ctrl, ik_handle[0], mo=True)
        cmds.parent(ik_finger_ctrl_grp, right_hand_ik_grp)
        cmds.parent(ik_handle[0], right_fingers_ik_grp)
        ik_finger_ctrls[ik_finger_ctrl] = ik_finger_ctrl_grp
        cmds.setAttr(ik_finger_ctrl + '.ry', lock=True, keyable=False)
        cmds.setAttr(ik_finger_ctrl + '.rz', lock=True, keyable=False)
        cmds.setAttr(ik_finger_ctrl + '.sx', lock=True, keyable=False)
        cmds.setAttr(ik_finger_ctrl + '.sy', lock=True, keyable=False)
        cmds.setAttr(ik_finger_ctrl + '.sz', lock=True, keyable=False)
        cmds.setAttr(ik_finger_ctrl + '.v', lock=True, keyable=False)

    cmds.parent(right_fingers_ik_grp, ik_solvers_grp)

    # Right Auto Fist/Splay Offset
    # A list of tuples of tuples 1:[thumb, index...],  2:(f_01, f_02, f_03),  3:(finger_ctrl, ctrl_grp, ctrl_offset)
    for obj in right_fingers_list:
        finger_name = remove_numbers(obj[0][0].replace(CTRL_SUFFIX, ''))

        # Create Nodes
        active_condition_node = cmds.createNode('condition', name=finger_name + AUTO_SUFFIX)
        plus_node = cmds.createNode('plusMinusAverage', name=finger_name + 'addition')
        limit_condition_node = cmds.createNode('condition', name=finger_name + 'limit')
        multiply_node = cmds.createNode('multiplyDivide', name=finger_name + MULTIPLY_SUFFIX)

        attribute_fist_pose_long = finger_name.replace('right_', '').replace('right_', '').replace('_',
                                                                                                   '') + 'FistPoseLimit'
        attribute_fist_pose_nice = finger_name.replace('right_', '').replace('right_', '').replace('_', '').capitalize()
        attribute_fist_pose_nice = 'Fist Pose Limit ' + attribute_fist_pose_nice
        cmds.addAttr(right_fingers_ctrl, ln=attribute_fist_pose_long, at='double', k=True,
                     niceName=attribute_fist_pose_nice)
        cmds.setAttr(right_fingers_ctrl + '.' + attribute_fist_pose_long, -90)

        attribute_long_name = finger_name.replace('right_', '').replace('right_', '').replace('_', '') + 'Multiplier'
        attribute_nice_name = finger_name.replace('right_', '').replace('right_', '').replace('_', '').capitalize()
        attribute_nice_name = 'Rot Multiplier ' + attribute_nice_name
        cmds.addAttr(right_fingers_ctrl, ln=attribute_long_name, at='double', k=True, niceName=attribute_nice_name)

        # Set Default Values
        cmds.setAttr(active_condition_node + '.secondTerm', 1)
        cmds.setAttr(active_condition_node + '.colorIfFalseR', 0)
        cmds.setAttr(active_condition_node + '.colorIfFalseG', 0)
        cmds.setAttr(active_condition_node + '.colorIfFalseB', 0)
        cmds.setAttr(limit_condition_node + '.operation', 3)

        # Offset & Curl
        if 'thumb' in finger_name:
            cmds.setAttr(right_fingers_ctrl + '.' + attribute_long_name, .7)
            cmds.connectAttr(right_curl_thumb_ctrl + '.rz', plus_node + '.input3D[0].input3Dz', f=True)
        elif 'index' in finger_name:
            cmds.setAttr(right_fingers_ctrl + '.' + attribute_long_name, .8)
            cmds.connectAttr(right_curl_index_ctrl + '.rz', plus_node + '.input3D[0].input3Dz', f=True)
        elif 'middle' in finger_name:
            cmds.setAttr(right_fingers_ctrl + '.' + attribute_long_name, .9)
            cmds.connectAttr(right_curl_middle_ctrl + '.rz', plus_node + '.input3D[0].input3Dz', f=True)
        elif 'ring' in finger_name:
            cmds.setAttr(right_fingers_ctrl + '.' + attribute_long_name, 1)
            cmds.connectAttr(right_curl_ring_ctrl + '.rz', plus_node + '.input3D[0].input3Dz', f=True)
        else:
            cmds.setAttr(right_fingers_ctrl + '.' + attribute_long_name, 1)
            cmds.connectAttr(right_curl_pinky_ctrl + '.rz', plus_node + '.input3D[0].input3Dz', f=True)

        # Connect Nodes
        cmds.connectAttr(right_fingers_ctrl + '.autoRotation', active_condition_node + '.firstTerm', f=True)
        cmds.connectAttr(right_fingers_ctrl + '.rotate', multiply_node + '.input1', f=True)
        cmds.connectAttr(right_fingers_ctrl + '.' + attribute_long_name, multiply_node + '.input2X', f=True)
        cmds.connectAttr(right_fingers_ctrl + '.' + attribute_long_name, multiply_node + '.input2Y', f=True)
        cmds.connectAttr(right_fingers_ctrl + '.' + attribute_long_name, multiply_node + '.input2Z', f=True)
        cmds.connectAttr(active_condition_node + '.outColorB', limit_condition_node + '.firstTerm', f=True)
        cmds.connectAttr(multiply_node + '.output', plus_node + '.input3D[1]', f=True)
        cmds.connectAttr(plus_node + '.output3D', active_condition_node + '.colorIfTrue', f=True)
        cmds.connectAttr(active_condition_node + '.outColor', limit_condition_node + '.colorIfTrue', f=True)

        # Set Limits
        cmds.connectAttr(right_fingers_ctrl + '.' + attribute_fist_pose_long, limit_condition_node + '.secondTerm',
                         f=True)
        cmds.connectAttr(right_fingers_ctrl + '.' + attribute_fist_pose_long, limit_condition_node + '.colorIfFalseR',
                         f=True)
        cmds.connectAttr(right_fingers_ctrl + '.' + attribute_fist_pose_long, limit_condition_node + '.colorIfFalseG',
                         f=True)
        cmds.connectAttr(right_fingers_ctrl + '.' + attribute_fist_pose_long, limit_condition_node + '.colorIfFalseB',
                         f=True)

        for finger in obj:
            cmds.connectAttr(active_condition_node + '.outColorR', finger[2] + '.rotateX', f=True)
            # cmds.connectAttr(active_condition_node + '.outColorG', finger[2] + '.rotateY', f=True)
            cmds.connectAttr(limit_condition_node + '.outColorB', finger[2] + '.rotateZ', f=True)

            # Add Extra Distal Multiply
            if '03' in finger[0]:
                attr_name = 'distalMultiplier'
                attr_name += finger_name.replace('right_', '').replace('right_', '').replace('_', '').capitalize()
                cmds.addAttr(right_fingers_ctrl, ln=attr_name, at='double', k=True)

                end_multiply_node = cmds.createNode('multiplyDivide', name=finger_name + 'endMultiply')
                cmds.connectAttr(limit_condition_node + '.outColorB', end_multiply_node + '.input1Z')
                cmds.connectAttr(end_multiply_node + '.outputZ', finger[2] + '.rotateZ', f=True)
                cmds.connectAttr(right_fingers_ctrl + '.' + attr_name, end_multiply_node + '.input2Z', f=True)
                cmds.setAttr(right_fingers_ctrl + '.' + attr_name, 1)

    # Right Finger Abduction Automation
    right_fingers_minz_scale = 1
    right_fingers_maxz_scale = 5
    right_fingers_min_abduction_rot = -60
    right_fingers_max_abduction_rot = 180

    cmds.setAttr(right_fingers_ctrl + '.sz', 2)
    cmds.addAttr(right_fingers_ctrl, ln='fingersAbduction', at='enum', k=True, en='-------------:')
    cmds.setAttr(right_fingers_ctrl + '.fingersAbduction', lock=True)  # Adduction
    cmds.addAttr(right_fingers_ctrl, ln='arrowVisibility', at='bool', k=True)
    cmds.connectAttr(right_fingers_ctrl + '.arrowVisibility', right_fingers_abduction_ctrl[0] + '.v')
    cmds.setAttr(right_fingers_ctrl + '.arrowVisibility', 1)

    cmds.addAttr(right_fingers_ctrl, ln='abductionInfluence', at='double', k=True, maxValue=1, minValue=0)
    cmds.setAttr(right_fingers_ctrl + '.abductionInfluence', 1)

    right_fingers_decompose_matrix_node = cmds.createNode('decomposeMatrix', name='right_fingers_inverse_matrix')
    cmds.connectAttr(right_fingers_ctrl + '.inverseMatrix', right_fingers_decompose_matrix_node + '.inputMatrix')

    right_fingers_shape_offset_grp = cmds.group(name=right_fingers_ctrl.replace(CTRL_SUFFIX, '') + 'shapeOffsetGrp',
                                                empty=True, world=True)
    cmds.delete(cmds.parentConstraint(right_fingers_ctrl, right_fingers_shape_offset_grp))
    cmds.parent(right_fingers_shape_offset_grp, right_fingers_ctrl_grp)
    cmds.parent(right_fingers_ctrl, right_fingers_shape_offset_grp)

    cmds.connectAttr(right_fingers_decompose_matrix_node + '.outputScale', right_fingers_shape_offset_grp + '.scale')

    right_fingers_inverse_rot_multiply_node = cmds.createNode('multiplyDivide',
                                                              name='right_fingers_inverseRot_multiply')
    cmds.connectAttr(right_fingers_decompose_matrix_node + '.outputRotate',
                     right_fingers_inverse_rot_multiply_node + '.input1')
    cmds.connectAttr(right_fingers_inverse_rot_multiply_node + '.output', right_fingers_shape_offset_grp + '.rotate')

    cmds.parent(right_fingers_abduction_ctrl[0], right_fingers_ctrl)
    cmds.connectAttr(right_fingers_ctrl + '.scale', right_fingers_abduction_ctrl[1] + '.scale')

    cmds.setAttr(right_fingers_ctrl + '.minScaleZLimit', right_fingers_minz_scale)
    cmds.setAttr(right_fingers_ctrl + '.maxScaleZLimit', right_fingers_maxz_scale)
    cmds.setAttr(right_fingers_ctrl + '.minScaleZLimitEnable', 1)
    cmds.setAttr(right_fingers_ctrl + '.maxScaleZLimitEnable', 1)

    # A list of tuples of tuples 1:[thumb, index...],  2:(f_01, f_02, f_03),  3:(finger_ctrl, ctrl_grp, ctrl_offset)
    for obj in right_fingers_list:
        finger_name = remove_numbers(obj[0][0].replace(CTRL_SUFFIX, ''))
        ctrl_offset = obj[0][2]

        # ### Abduction/Adduction System ###
        abduction_blend_node = cmds.createNode('blendTwoAttr', name=finger_name + 'abduction_blend')
        abduction_multiply_node = cmds.createNode('multiplyDivide', name=finger_name + 'abduction_multiply')
        abduction_range_node = cmds.createNode('setRange', name=finger_name + 'abduction_range')
        abduction_sum_node = cmds.createNode('plusMinusAverage', name=finger_name + 'abduction_sum')
        cmds.setAttr(abduction_range_node + '.oldMinZ', right_fingers_minz_scale)
        cmds.setAttr(abduction_range_node + '.oldMaxZ', right_fingers_maxz_scale)
        cmds.setAttr(abduction_range_node + '.minZ', right_fingers_min_abduction_rot)
        cmds.setAttr(abduction_range_node + '.maxZ', right_fingers_max_abduction_rot)
        cmds.connectAttr(right_fingers_ctrl + '.sz', abduction_range_node + '.valueZ', f=True)
        cmds.connectAttr(abduction_range_node + '.outValueZ', abduction_multiply_node + '.input1X', f=True)
        cmds.connectAttr(abduction_multiply_node + '.outputX', abduction_blend_node + '.input[1]', f=True)

        # Right Multiply Reverse
        abduction_multiply_reverse_node = cmds.createNode('multiplyDivide',
                                                          name=finger_name + 'abduction_multiplyReverse')
        cmds.setAttr(abduction_multiply_reverse_node + '.input2X', -1)
        cmds.setAttr(abduction_multiply_reverse_node + '.input2Y', -1)
        cmds.setAttr(abduction_multiply_reverse_node + '.input2Z', -1)
        cmds.connectAttr(abduction_blend_node + '.output', abduction_multiply_reverse_node + '.input1Y')
        cmds.connectAttr(abduction_multiply_reverse_node + '.outputY', abduction_sum_node + '.input3D[0].input3Dy')
        cmds.connectAttr(abduction_sum_node + '.output3Dx', ctrl_offset + '.rx', force=True)
        cmds.connectAttr(abduction_sum_node + '.output3Dy', ctrl_offset + '.ry')
        cmds.connectAttr(right_fingers_ctrl + '.abductionInfluence', abduction_blend_node + '.attributesBlender')
        cmds.setAttr(abduction_blend_node + ".input[0]", 0)

        if 'thumb' in finger_name:
            cmds.addAttr(right_fingers_ctrl, ln='rotMultiplierThumb', at='double', k=True)
            cmds.setAttr(right_fingers_ctrl + '.rotMultiplierThumb', -.1)
            cmds.connectAttr(right_fingers_ctrl + '.rotMultiplierThumb', abduction_multiply_node + '.input2X',
                             f=True)
        elif 'index' in finger_name:
            cmds.addAttr(right_fingers_ctrl, ln='rotMultiplierIndex', at='double', k=True)
            cmds.setAttr(right_fingers_ctrl + '.rotMultiplierIndex', -.7)
            cmds.connectAttr(right_fingers_ctrl + '.rotMultiplierIndex', abduction_multiply_node + '.input2X',
                             f=True)
        elif 'middle' in finger_name:
            cmds.addAttr(right_fingers_ctrl, ln='rotMultiplierMiddle', at='double', k=True)
            cmds.setAttr(right_fingers_ctrl + '.rotMultiplierMiddle', -.3)
            cmds.connectAttr(right_fingers_ctrl + '.rotMultiplierMiddle', abduction_multiply_node + '.input2X',
                             f=True)
        elif 'ring' in finger_name:
            cmds.addAttr(right_fingers_ctrl, ln='rotMultiplierRing', at='double', k=True)
            cmds.setAttr(right_fingers_ctrl + '.rotMultiplierRing', .2)
            cmds.connectAttr(right_fingers_ctrl + '.rotMultiplierRing', abduction_multiply_node + '.input2X',
                             f=True)
        elif 'pinky' in finger_name:
            cmds.addAttr(right_fingers_ctrl, ln='rotMultiplierPinky', at='double', k=True)
            cmds.setAttr(right_fingers_ctrl + '.rotMultiplierPinky', .7)
            cmds.connectAttr(right_fingers_ctrl + '.rotMultiplierPinky', abduction_multiply_node + '.input2X',
                             f=True)

    # Right Auto Knuckle Compression System (Translation Z Offset)
    cmds.addAttr(right_fingers_ctrl, ln='knucklesAutomation', at='enum', k=True, en='-------------:')
    cmds.setAttr(right_fingers_ctrl + '.knucklesAutomation', lock=True)
    cmds.addAttr(right_fingers_ctrl, ln='showCompressionCtrls', at='bool', k=True, maxValue=1, minValue=0)
    cmds.addAttr(right_fingers_ctrl, ln='autoCompression', at='double', k=True, maxValue=1, minValue=0)
    cmds.setAttr(right_fingers_ctrl + '.autoCompression', 1)
    cmds.addAttr(right_fingers_ctrl, ln='transCompression', at='double', k=True, minValue=0)
    cmds.setAttr(right_fingers_ctrl + '.transCompression', 1)

    right_knuckle_blend_node = cmds.createNode('blendTwoAttr', name='right_knuckle_compression_blend')
    right_knuckle_reverse_node = cmds.createNode('reverse', name='right_knuckle_compression_reverse')
    cmds.connectAttr(right_fingers_ctrl + '.autoCompression', right_knuckle_blend_node + '.attributesBlender')
    cmds.setAttr(right_knuckle_blend_node + '.input[0]', 0)
    right_compression_range_node = cmds.createNode('setRange', name='right_knuckle_compression_range')
    cmds.connectAttr(right_fingers_ctrl + '.rz', right_knuckle_reverse_node + '.inputZ', f=True)
    cmds.connectAttr(right_knuckle_reverse_node + '.outputZ', right_compression_range_node + '.valueZ', f=True)
    cmds.connectAttr(right_compression_range_node + '.outValueZ', right_knuckle_blend_node + '.input[1]', f=True)
    cmds.setAttr(right_compression_range_node + '.oldMaxZ', 180)
    cmds.connectAttr(right_fingers_ctrl + '.transCompression', right_compression_range_node + '.maxZ', f=True)
    # Rotation System
    cmds.addAttr(right_fingers_ctrl, ln='rotCompression', at='double', k=True, minValue=0)
    cmds.setAttr(right_fingers_ctrl + '.rotCompression', 10)
    right_knuckle_rot_blend_node = cmds.createNode('blendTwoAttr', name='right_knuckle_rotCompression_blend')
    right_knuckle_rot_range_node = cmds.createNode('setRange', name='right_knuckle_rotCompression_range')
    knuckle_rot_multiply_node = cmds.createNode('multiplyDivide', name='right_knuckle_rotCompression_influence')
    cmds.connectAttr(right_fingers_ctrl + '.autoCompression', knuckle_rot_multiply_node + '.input1X')
    cmds.connectAttr(right_fingers_ctrl + '.rotCompression', knuckle_rot_multiply_node + '.input2X')
    cmds.connectAttr(knuckle_rot_multiply_node + '.outputX', right_knuckle_rot_blend_node + '.input[0]')
    cmds.setAttr(right_knuckle_rot_blend_node + '.input[1]', 0)
    cmds.connectAttr(right_fingers_ctrl + '.minimumRotationZ', right_knuckle_rot_range_node + '.oldMinZ')
    cmds.connectAttr(right_fingers_ctrl + '.rz', right_knuckle_rot_range_node + '.valueZ')
    cmds.setAttr(right_knuckle_rot_range_node + '.maxZ', 1)
    cmds.connectAttr(right_knuckle_rot_range_node + '.outValueZ',
                     right_knuckle_rot_blend_node + '.attributesBlender')

    # Right Manual Compression Controls
    right_compression_ctrl_output = []
    right_compression_joints = [rig_joints.get('right_index01_jnt'),
                                rig_joints.get('right_middle01_jnt'),
                                rig_joints.get('right_ring01_jnt'),
                                rig_joints.get('right_pinky01_jnt')]
    for joint in right_compression_joints:
        name = joint.replace(JNT_SUFFIX, '')
        right_compression_ctrl = cmds.curve(name=name + 'compression_ctrl',
                                            p=[[0.0, 0.28, 0.0], [-0.28, 0.001, 0.0], [0.0, 0.0, 0.28],
                                               [0.0, 0.28, 0.0], [0.28, 0.001, 0.0], [0.0, 0.0, 0.28],
                                               [0.28, 0.001, 0.0], [0.0, 0.0, -0.28], [0.0, 0.28, 0.0],
                                               [0.0, 0.0, -0.28], [-0.28, 0.001, 0.0], [0.0, -0.28, 0.0],
                                               [0.0, 0.0, -0.28], [0.28, 0.001, 0.0], [0.0, -0.28, 0.0],
                                               [0.0, 0.0, 0.28]], d=1)
        right_compression_ctrl_grp = cmds.group(name=right_compression_ctrl + GRP_SUFFIX.capitalize(),
                                                empty=True, world=True)
        cmds.parent(right_compression_ctrl, right_compression_ctrl_grp)
        rescale(right_compression_ctrl, right_wrist_scale_offset * .3)
        cmds.delete(cmds.parentConstraint(right_fingers_ctrl, right_compression_ctrl_grp))
        cmds.delete(cmds.pointConstraint(joint, right_compression_ctrl_grp))
        cmds.move(-right_wrist_scale_offset * .3, right_compression_ctrl_grp, moveY=True, relative=True,
                  objectSpace=True)
        cmds.move(right_wrist_scale_offset * .2, right_compression_ctrl_grp, moveX=True, relative=True,
                  objectSpace=True)
        lock_hide_default_attr(right_compression_ctrl, rotate=False)
        cmds.setAttr(right_compression_ctrl + '.rx', lock=True, keyable=False)
        cmds.setAttr(right_compression_ctrl + '.ry', lock=True, keyable=False)
        change_viewport_color(right_compression_ctrl, RIGHT_CTRL_COLOR)
        manual_multiply_node = cmds.createNode('multiplyDivide', name=name + 'compressionInfluence')
        cmds.addAttr(right_compression_ctrl, ln='influence', at='double', k=True)
        cmds.setAttr(right_compression_ctrl + '.influence', -.1)
        cmds.connectAttr(right_compression_ctrl + '.rz', manual_multiply_node + '.input1Z')
        cmds.connectAttr(right_compression_ctrl + '.influence', manual_multiply_node + '.input2Z')
        cmds.connectAttr(right_fingers_ctrl + '.showCompressionCtrls', right_compression_ctrl_grp + '.v')
        cmds.parent(right_compression_ctrl_grp, right_fingers_ctrl_grp)
        right_compression_ctrl_output.append(manual_multiply_node)

    # Knuckle Compression
    for obj in right_fingers_list:
        # Unpack Elements
        finger_name = remove_numbers(obj[0][0].replace(CTRL_SUFFIX, ''))
        ctrl_offset = obj[0][2]

        # Knuckle Compression System
        knuckle_multiply_node = ''
        knuckle_rot_multiply_node = ''
        knuckle_sum_node = ''
        if 'thumb' not in ctrl_offset:
            knuckle_multiply_node = cmds.createNode('multiplyDivide', name=finger_name + 'compression_multiply')
            knuckle_sum_node = cmds.createNode('plusMinusAverage', name=finger_name + 'compression_sum')
            cmds.connectAttr(right_knuckle_blend_node + '.output', knuckle_multiply_node + '.input1Z')
            cmds.connectAttr(knuckle_multiply_node + '.outputZ', knuckle_sum_node + '.input1D[0]')
            cmds.connectAttr(knuckle_sum_node + '.output1D', ctrl_offset + '.tz')

            # Rot System
            knuckle_rot_multiply_node = cmds.createNode('multiplyDivide',
                                                        name=finger_name + 'rotCompression_multiply')
            cmds.connectAttr(right_knuckle_rot_blend_node + '.output', knuckle_rot_multiply_node + '.input2Y')
            cmds.connectAttr(right_knuckle_rot_blend_node + '.output', knuckle_rot_multiply_node + '.input2X')
            cmds.connectAttr(knuckle_rot_multiply_node + '.output', finger_name + 'abduction_sum.input3D[1]')

        # Connections
        if 'index' in finger_name:
            # Trans
            cmds.addAttr(right_fingers_ctrl, ln='transMultiplierIndex', at='double', k=True)
            cmds.setAttr(right_fingers_ctrl + '.transMultiplierIndex', 1.5)
            cmds.connectAttr(right_fingers_ctrl + '.transMultiplierIndex', knuckle_multiply_node + '.input2Z')
            cmds.connectAttr(right_compression_ctrl_output[0] + '.outputZ', knuckle_sum_node + '.input1D[1]')
            # Rot
            nice_name_y = 'Rot Y Multiplier Index'
            nice_name_x = 'Rot X Multiplier Index'
            cmds.addAttr(right_fingers_ctrl, ln='rotCompMultiplierIndexY', at='double', k=True,
                         niceName=nice_name_y)
            cmds.setAttr(right_fingers_ctrl + '.rotCompMultiplierIndexY', -0.5)
            cmds.addAttr(right_fingers_ctrl, ln='rotCompMultiplierIndexX', at='double', k=True,
                         niceName=nice_name_x)
            cmds.setAttr(right_fingers_ctrl + '.rotCompMultiplierIndexX', 0)
            cmds.connectAttr(right_fingers_ctrl + '.rotCompMultiplierIndexY',
                             knuckle_rot_multiply_node + '.input1Y')
            cmds.connectAttr(right_fingers_ctrl + '.rotCompMultiplierIndexX',
                             knuckle_rot_multiply_node + '.input1X')
        elif 'middle' in finger_name:
            # Trans
            cmds.addAttr(right_fingers_ctrl, ln='transMultiplierMiddle', at='double', k=True)
            cmds.setAttr(right_fingers_ctrl + '.transMultiplierMiddle', .5)
            cmds.connectAttr(right_fingers_ctrl + '.transMultiplierMiddle', knuckle_multiply_node + '.input2Z')
            cmds.connectAttr(right_compression_ctrl_output[1] + '.outputZ', knuckle_sum_node + '.input1D[1]')
            # Rot
            nice_name_y = 'Rot Y Multiplier Middle'
            nice_name_x = 'Rot X Multiplier Middle'
            cmds.addAttr(right_fingers_ctrl, ln='rotCompMultiplierMiddleY', at='double', k=True,
                         niceName=nice_name_y)
            cmds.setAttr(right_fingers_ctrl + '.rotCompMultiplierMiddleY', -0.25)
            cmds.addAttr(right_fingers_ctrl, ln='rotCompMultiplierMiddleX', at='double', k=True,
                         niceName=nice_name_x)
            cmds.setAttr(right_fingers_ctrl + '.rotCompMultiplierMiddleX', 0)
            cmds.connectAttr(right_fingers_ctrl + '.rotCompMultiplierMiddleY',
                             knuckle_rot_multiply_node + '.input1Y')
            cmds.connectAttr(right_fingers_ctrl + '.rotCompMultiplierMiddleX',
                             knuckle_rot_multiply_node + '.input1X')
        elif 'ring' in finger_name:
            # Trans
            cmds.addAttr(right_fingers_ctrl, ln='transMultiplierRing', at='double', k=True)
            cmds.setAttr(right_fingers_ctrl + '.transMultiplierRing', -.5)
            cmds.connectAttr(right_fingers_ctrl + '.transMultiplierRing', knuckle_multiply_node + '.input2Z')
            cmds.connectAttr(right_compression_ctrl_output[2] + '.outputZ', knuckle_sum_node + '.input1D[1]')
            # Rot
            nice_name_y = 'Rot Y Multiplier Ring'
            nice_name_x = 'Rot X Multiplier Ring'
            cmds.addAttr(right_fingers_ctrl, ln='rotCompMultiplierRingY', at='double', k=True, niceName=nice_name_y)
            cmds.setAttr(right_fingers_ctrl + '.rotCompMultiplierRingY', 0.25)
            cmds.addAttr(right_fingers_ctrl, ln='rotCompMultiplierRingX', at='double', k=True, niceName=nice_name_x)
            cmds.setAttr(right_fingers_ctrl + '.rotCompMultiplierRingX', 0)
            cmds.connectAttr(right_fingers_ctrl + '.rotCompMultiplierRingY', knuckle_rot_multiply_node + '.input1Y')
            cmds.connectAttr(right_fingers_ctrl + '.rotCompMultiplierRingX', knuckle_rot_multiply_node + '.input1X')
        elif 'pinky' in finger_name:
            # Trans
            cmds.addAttr(right_fingers_ctrl, ln='transMultiplierPinky', at='double', k=True)
            cmds.setAttr(right_fingers_ctrl + '.transMultiplierPinky', -1.5)
            cmds.connectAttr(right_fingers_ctrl + '.transMultiplierPinky', knuckle_multiply_node + '.input2Z')
            cmds.connectAttr(right_compression_ctrl_output[3] + '.outputZ', knuckle_sum_node + '.input1D[1]')
            # Rot
            nice_name_y = 'Rot Y Multiplier Pinky'
            nice_name_x = 'Rot X Multiplier Pinky'
            cmds.addAttr(right_fingers_ctrl, ln='rotCompMultiplierPinkyY', at='double', k=True,
                         niceName=nice_name_y)
            cmds.setAttr(right_fingers_ctrl + '.rotCompMultiplierPinkyY', 0.5)
            cmds.addAttr(right_fingers_ctrl, ln='rotCompMultiplierPinkyX', at='double', k=True,
                         niceName=nice_name_x)
            cmds.setAttr(right_fingers_ctrl + '.rotCompMultiplierPinkyX', 0)
            cmds.connectAttr(right_fingers_ctrl + '.rotCompMultiplierPinkyY',
                             knuckle_rot_multiply_node + '.input1Y')
            cmds.connectAttr(right_fingers_ctrl + '.rotCompMultiplierPinkyX',
                             knuckle_rot_multiply_node + '.input1X')

    # Create FK/IK Switch for Fingers
    cmds.addAttr(right_fingers_ctrl, ln='switchAttributes', at='enum', k=True, en='-------------:')
    cmds.setAttr(right_fingers_ctrl + '.switchAttributes', lock=True)
    cmds.addAttr(right_fingers_ctrl, ln='influenceSwitch', at='double', k=True, maxValue=1, minValue=0)
    cmds.setAttr(right_fingers_ctrl + '.influenceSwitch', 1)

    right_fingers_visibility_condition_node = cmds.createNode('condition', name='right_fingers_ikVisibility_condition')

    cmds.connectAttr(right_fingers_ctrl + '.influenceSwitch', right_fingers_visibility_condition_node + '.firstTerm',
                     f=True)
    cmds.setAttr(right_fingers_visibility_condition_node + '.operation', 4)
    cmds.setAttr(right_fingers_visibility_condition_node + '.secondTerm', .5)
    cmds.setAttr(right_fingers_visibility_condition_node + '.colorIfTrueR', 1)
    cmds.setAttr(right_fingers_visibility_condition_node + '.colorIfTrueG', 1)
    cmds.setAttr(right_fingers_visibility_condition_node + '.colorIfTrueB', 1)
    cmds.setAttr(right_fingers_visibility_condition_node + '.colorIfFalseR', 0)
    cmds.setAttr(right_fingers_visibility_condition_node + '.colorIfFalseG', 0)
    cmds.setAttr(right_fingers_visibility_condition_node + '.colorIfFalseB', 0)

    for ctrl in ik_finger_ctrls:
        for shape in cmds.listRelatives(ctrl, s=True, f=True) or []:
            cmds.connectAttr(right_fingers_visibility_condition_node + '.outColorR', shape + '.v', f=True)

    reverse_node = cmds.createNode('reverse', name='right_fingers_ik_reverse')
    cmds.connectAttr(right_fingers_ctrl + '.influenceSwitch', reverse_node + '.inputX', f=True)

    for constraint in finger_switch_constraints:
        cmds.connectAttr(right_fingers_ctrl + '.influenceSwitch', constraint[0] + '.w0', f=True)
        cmds.connectAttr(reverse_node + '.outputX', constraint[0] + '.w1', f=True)

    # Create Parenting Switcher for Fingers
    cmds.addAttr(right_fingers_ctrl, ln='ikParent', at='enum', k=True, en="World:Wrist:", niceName="IK Fingers Parent")
    cmds.setAttr(right_fingers_ctrl + '.ikParent', 1)
    ik_fingers_system_constraint = cmds.parentConstraint([controls_grp, right_hand_grp], right_hand_ik_grp, mo=True)

    right_ik_fingers_world_condition_node = cmds.createNode('condition',
                                                            name='right_ikFingers_parentWorld_' + AUTO_SUFFIX)
    right_ik_fingers_wrist_condition_node = cmds.createNode('condition',
                                                            name='right_ikFingers_parentWrist_' + AUTO_SUFFIX)

    cmds.setAttr(right_ik_fingers_world_condition_node + '.secondTerm', 0)
    cmds.setAttr(right_ik_fingers_wrist_condition_node + '.secondTerm', 1)

    for node in [right_ik_fingers_world_condition_node, right_ik_fingers_wrist_condition_node]:
        cmds.setAttr(node + '.colorIfTrueR', 1)
        cmds.setAttr(node + '.colorIfTrueG', 1)
        cmds.setAttr(node + '.colorIfTrueB', 1)
        cmds.setAttr(node + '.colorIfFalseR', 0)
        cmds.setAttr(node + '.colorIfFalseG', 0)
        cmds.setAttr(node + '.colorIfFalseB', 0)

    cmds.connectAttr(right_fingers_ctrl + '.ikParent', right_ik_fingers_world_condition_node + '.firstTerm', f=True)
    cmds.connectAttr(right_fingers_ctrl + '.ikParent', right_ik_fingers_wrist_condition_node + '.firstTerm', f=True)

    cmds.connectAttr(right_ik_fingers_world_condition_node + '.outColorR', ik_fingers_system_constraint[0] + '.w0',
                     f=True)
    cmds.connectAttr(right_ik_fingers_wrist_condition_node + '.outColorR', ik_fingers_system_constraint[0] + '.w1',
                     f=True)

    # Control Specific Parenting System
    for ctrl in ik_finger_ctrls:
        fk_parent_name = ctrl.replace('_ik_' + CTRL_SUFFIX, '03_' + CTRL_SUFFIX)
        inbetween_transform = cmds.group(name=(ctrl + 'FkOffset'), empty=True)
        parent_override_transform = cmds.group(name=(ctrl + 'ParentOverride'), empty=True)
        cmds.parent(parent_override_transform, inbetween_transform)
        ctrl_parent = cmds.listRelatives(ctrl, parent=True) or []
        cmds.delete(cmds.parentConstraint(ctrl_parent[0], inbetween_transform))
        cmds.parent(inbetween_transform, ctrl_parent[0])
        cmds.parent(ctrl, parent_override_transform)

        cmds.addAttr(ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', k=True, en='-------------:')
        cmds.setAttr(ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)
        cmds.addAttr(ctrl, ln='ikFollowsFk', at='double', k=True, maxValue=1, minValue=0, niceName='IK Follows FK')
        cmds.setAttr(ctrl + '.ikFollowsFk', 1)
        cmds.addAttr(ctrl, ln='forceWorldParenting', at='double', k=True, maxValue=1, minValue=0)

        condition_node = cmds.createNode('condition', name=ctrl.replace('_ik_' + CTRL_SUFFIX, '_condition'))
        parent_constraint = cmds.parentConstraint([right_hand_ik_grp, fk_parent_name], inbetween_transform, mo=True)

        cmds.connectAttr(right_fingers_ctrl + '.ikParent', condition_node + '.firstTerm', f=True)
        cmds.setAttr(condition_node + '.colorIfFalseR', 0)
        cmds.setAttr(condition_node + '.colorIfFalseG', 0)
        cmds.setAttr(condition_node + '.colorIfFalseB', 0)

        cmds.connectAttr(ctrl + '.ikFollowsFk', condition_node + '.colorIfFalseR', f=True)
        cmds.connectAttr(condition_node + '.outColorR', parent_constraint[0] + '.w1', f=True)

        reverse_node = cmds.createNode('reverse', name=ctrl.replace('_ik_' + CTRL_SUFFIX, '_reverse'))
        cmds.connectAttr(condition_node + '.outColorR', reverse_node + '.inputX', f=True)
        cmds.connectAttr(reverse_node + '.outputX', parent_constraint[0] + '.w0', f=True)

        # Force World Parent
        cmds.parentConstraint(inbetween_transform, parent_override_transform)
        parent_override_constraint = cmds.parentConstraint(controls_grp, parent_override_transform, mo=True)

        cmds.connectAttr(ctrl + '.forceWorldParenting', parent_override_constraint[0] + '.w1', f=True)
        override_reverse_node = cmds.createNode('reverse',
                                                name=ctrl.replace('_worldOverride_' + CTRL_SUFFIX, '_reverse'))
        cmds.connectAttr(ctrl + '.forceWorldParenting', override_reverse_node + '.inputX', f=True)
        cmds.connectAttr(override_reverse_node + '.outputX', parent_override_constraint[0] + '.w0', f=True)

    # ### End Finger Controls ###

    # Create Separators before Custom Attributes
    # Main Eye
    cmds.addAttr(main_eye_ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
    cmds.setAttr(main_eye_ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)
    # Left Knee
    cmds.addAttr(left_knee_ik_ctrl, ln="kneeAutomation", at='enum', en='-------------:', keyable=True)
    cmds.setAttr(left_knee_ik_ctrl + '.kneeAutomation', lock=True)
    # Right Knee
    cmds.addAttr(right_knee_ik_ctrl, ln="kneeAutomation", at='enum', en='-------------:', keyable=True)
    cmds.setAttr(right_knee_ik_ctrl + '.kneeAutomation', lock=True)
    # Left Elbow
    cmds.addAttr(left_elbow_ik_ctrl, ln="elbowAutomation", at='enum', en='-------------:', keyable=True)
    cmds.setAttr(left_elbow_ik_ctrl + '.elbowAutomation', lock=True)
    # Right Elbow
    cmds.addAttr(right_elbow_ik_ctrl, ln="elbowAutomation", at='enum', en='-------------:', keyable=True)
    cmds.setAttr(right_elbow_ik_ctrl + '.elbowAutomation', lock=True)

    # Create Aim Lines
    aim_pairs = [(left_knee_ik_ctrl, rig_joints.get('left_knee_jnt')),
                 (right_knee_ik_ctrl, rig_joints.get('right_knee_jnt')),
                 (left_elbow_ik_ctrl, rig_joints.get('left_elbow_jnt')),
                 (right_elbow_ik_ctrl, rig_joints.get('right_elbow_jnt')),
                 (left_eye_ctrl, rig_joints.get('left_eye_jnt')),
                 (right_eye_ctrl, rig_joints.get('right_eye_jnt')), ]
    aim_line_alternative_control = {left_eye_ctrl: main_eye_ctrl,
                                    right_eye_ctrl: main_eye_ctrl}
    aim_line_grp = cmds.group(name='aimLines_grp', world=True, empty=True)
    for pair in aim_pairs:
        ctrl = pair[0]
        jnt = pair[1]
        generated_line = create_visualization_line(ctrl, jnt)
        cmds.setAttr(generated_line[0] + '.overrideEnabled', 1)
        cmds.setAttr(generated_line[0] + '.overrideDisplayType', 1)
        cmds.setAttr(generated_line[0] + '.inheritsTransform', 0)
        cmds.setAttr(generated_line[0] + '.t', lock=True)
        cmds.setAttr(generated_line[0] + '.r', lock=True)
        cmds.setAttr(generated_line[0] + '.s', lock=True)
        attr_name = 'showAimLine'
        if ctrl not in aim_line_alternative_control:
            cmds.addAttr(ctrl, ln=attr_name, at='bool', keyable=True)
            cmds.setAttr(ctrl + '.' + attr_name, 1)
            cmds.connectAttr(ctrl + '.' + attr_name, generated_line[0] + '.v')
        else:
            if not cmds.attributeQuery(attr_name, node=aim_line_alternative_control.get(ctrl), exists=True):
                cmds.addAttr(aim_line_alternative_control.get(ctrl), ln=attr_name, at='bool', keyable=True)
            cmds.connectAttr(aim_line_alternative_control.get(ctrl) + '.' + attr_name, generated_line[0] + '.v')

        cmds.parent(generated_line[0], ctrl)
        cmds.parent(generated_line[1], aim_line_grp)
        cmds.parent(generated_line[2], aim_line_grp)
        cmds.rename(generated_line[0], generated_line[0] + '_crv')
    cmds.parent(aim_line_grp, general_automation_grp)

    # ################# IK Controls #################
    # ################# Left Leg IK Controls ################

    # - WIP - @@@ # - WIP - ########################################################################
    # Left Leg IK

    # left_leg_rp_ik_handle = cmds.ikHandle(n='left_footAnkle_RP_ikHandle', sj=left_hip_ik_jnt, ee=left_ankle_ik_jnt,
    #                                       sol='ikRPsolver')
    # cmds.poleVectorConstraint(left_knee_ik_ctrl, left_leg_rp_ik_handle[0])
    #
    # # Force IK offset not to pop when FK - TODO Experiment with forced offset
    # # cmds.matchTransform(rig_joints.get('left_hip_jnt'), left_hip_ik_jnt, pos=1, rot=1)
    # # cmds.matchTransform(rig_joints.get('left_knee_jnt'), left_hip_ik_jnt, pos=1, rot=1)
    # cmds.parent(left_ankle_ctrl_grp, world=True)
    # cmds.parent(left_ball_ctrl_grp, world=True)
    # cmds.matchTransform(left_hip_ctrl_grp, left_hip_ik_jnt, pos=1, rot=1)
    # if settings.get('uniform_ctrl_orient'):
    #     cmds.rotate(-90, -90, 0, left_hip_ctrl_grp, os=True, relative=True)
    # cmds.matchTransform(left_knee_ctrl_grp, left_knee_ik_jnt, pos=1, rot=1)
    # if settings.get('uniform_ctrl_orient'):
    #     cmds.rotate(0, -90, -90, left_knee_ctrl_grp, os=True, relative=True)
    # cmds.matchTransform(left_ankle_ctrl_grp, left_ankle_ik_jnt, pos=1, rot=1)
    # if settings.get('uniform_ctrl_orient'):
    #     cmds.rotate(0, -90, -90, left_ankle_ctrl_grp, os=True, relative=True)
    # cmds.parent(left_ankle_ctrl_grp, left_knee_ctrl)
    # cmds.parent(left_ball_ctrl_grp, left_ankle_ctrl)
    #
    # cmds.matchTransform(left_ball_ik_jnt, left_ball_fk_jnt, pos=1, rot=1)
    # cmds.matchTransform(left_toe_ik_jnt, left_toe_fk_jnt, pos=1, rot=1)
    #
    # left_leg_ball_ik_handle = cmds.ikHandle(n='left_footBall_SC_ikHandle', sj=left_ankle_ik_jnt, ee=left_ball_ik_jnt,
    #                                         sol='ikSCsolver')
    # left_leg_toe_ik_handle = cmds.ikHandle(n='left_footToe_SC_ikHandle', sj=left_ball_ik_jnt, ee=left_toe_ik_jnt,
    #                                        sol='ikSCsolver')
    # - WIP - ########################################################################

    # Left Leg IK
    left_leg_rp_ik_handle = cmds.ikHandle(n='left_footAnkle_RP_ikHandle', sj=left_hip_ik_jnt, ee=left_ankle_ik_jnt,
                                          sol='ikRPsolver')
    left_leg_ball_ik_handle = cmds.ikHandle(n='left_footBall_SC_ikHandle', sj=left_ankle_ik_jnt, ee=left_ball_ik_jnt,
                                            sol='ikSCsolver')
    left_leg_toe_ik_handle = cmds.ikHandle(n='left_footToe_SC_ikHandle', sj=left_ball_ik_jnt, ee=left_toe_ik_jnt,
                                           sol='ikSCsolver')
    cmds.poleVectorConstraint(left_knee_ik_ctrl, left_leg_rp_ik_handle[0])

    # Left Foot Automation Setup
    left_foot_pivot_grp = cmds.group(name='left_foot_pivot' + GRP_SUFFIX.capitalize(), empty=True, world=True)
    left_heel_pivot_grp = cmds.group(name='left_heel_pivot' + GRP_SUFFIX.capitalize(), empty=True, world=True)
    left_ball_pivot_grp = cmds.group(name='left_ball_pivot' + GRP_SUFFIX.capitalize(), empty=True, world=True)
    left_toe_pivot_grp = cmds.group(name='left_toe_pivot' + GRP_SUFFIX.capitalize(), empty=True, world=True)
    left_toe_pos_pivot_grp = cmds.group(name='left_toeUpDown_pivot' + GRP_SUFFIX.capitalize(), empty=True, world=True)
    # FK Toe Influence
    left_toe_fk_pivot_grp = cmds.group(name='left_toe_fk_pivot' + GRP_SUFFIX.capitalize(), empty=True, world=True)
    left_toe_fk_pivot_zero_grp = cmds.group(name='left_toe_fk_zero' + GRP_SUFFIX.capitalize(), empty=True, world=True)
    left_toe_pos_zero_grp = cmds.group(name='left_toeUpDown_zero' + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(left_toe_pos_pivot_grp, left_toe_pos_zero_grp)
    cmds.parent(left_toe_pos_zero_grp, left_toe_pivot_grp)
    cmds.delete(cmds.pointConstraint(rig_joints.get('left_ball_jnt'), left_toe_fk_pivot_grp))
    cmds.delete(cmds.pointConstraint(rig_joints.get('left_ball_jnt'), left_toe_fk_pivot_zero_grp))

    cmds.delete(cmds.pointConstraint(rig_joints.get('left_ankle_jnt'), left_foot_pivot_grp))
    cmds.delete(cmds.pointConstraint(elements.get('left_ball_pivot_grp'), left_heel_pivot_grp))
    cmds.delete(cmds.pointConstraint(rig_joints.get('left_ball_jnt'), left_ball_pivot_grp))
    cmds.delete(cmds.pointConstraint(rig_joints.get('left_toe_jnt'), left_toe_pivot_grp))

    desired_rotation = cmds.xform(elements.get('left_ankle_proxy_crv'), q=True, ro=True)
    cmds.setAttr(left_foot_pivot_grp + '.ry', desired_rotation[1])
    cmds.setAttr(left_heel_pivot_grp + '.ry', desired_rotation[1])
    cmds.setAttr(left_ball_pivot_grp + '.ry', desired_rotation[1])
    cmds.setAttr(left_toe_pivot_grp + '.ry', desired_rotation[1])

    if cmds.objExists(elements_default.get('left_heel_proxy_pivot')):
        cmds.delete(cmds.pointConstraint(elements_default.get('left_heel_proxy_pivot'), left_heel_pivot_grp))

    cmds.parent(left_foot_pivot_grp, rig_setup_grp)
    cmds.parent(left_heel_pivot_grp, left_foot_pivot_grp)
    cmds.parent(left_toe_pivot_grp, left_heel_pivot_grp)
    cmds.parent(left_ball_pivot_grp, left_toe_pivot_grp)

    # Toe IK toe ctrl setup
    cmds.parent(left_toe_fk_pivot_grp, left_toe_fk_pivot_zero_grp)
    cmds.parent(left_toe_fk_pivot_zero_grp, left_toe_pivot_grp)
    cmds.parent(left_toe_pos_zero_grp, left_toe_fk_pivot_grp)
    left_toe_full_ctrl = cmds.curve(name='left_toe_ik_' + CTRL_SUFFIX,
                                    p=[[0.0, 0.0, 0.0], [0.0, 0.398, 0.229], [0.0, 0.409, 0.217], [0.0, 0.423, 0.206],
                                       [0.0, 0.439, 0.2], [0.0, 0.456, 0.197], [0.0, 0.473, 0.2], [0.0, 0.488, 0.206],
                                       [0.0, 0.456, 0.264], [0.0, 0.398, 0.229], [0.0, 0.392, 0.246],
                                       [0.0, 0.389, 0.264],
                                       [0.0, 0.392, 0.281], [0.0, 0.398, 0.296], [0.0, 0.409, 0.31],
                                       [0.0, 0.423, 0.319],
                                       [0.0, 0.439, 0.327], [0.0, 0.456, 0.329], [0.0, 0.473, 0.327],
                                       [0.0, 0.488, 0.319],
                                       [0.0, 0.502, 0.31], [0.0, 0.513, 0.296], [0.0, 0.519, 0.281],
                                       [0.0, 0.521, 0.264],
                                       [0.0, 0.519, 0.246], [0.0, 0.513, 0.229], [0.0, 0.502, 0.215],
                                       [0.0, 0.488, 0.206],
                                       [0.0, 0.423, 0.319], [0.0, 0.456, 0.264], [0.0, 0.513, 0.296]], d=1)
    rescale(left_toe_full_ctrl, left_foot_scale_offset, True)
    change_viewport_color(left_toe_full_ctrl, LEFT_CTRL_COLOR)
    lock_hide_default_attr(left_toe_full_ctrl, translate=False, rotate=False)
    left_toe_full_ctrl_grp = cmds.group(name=left_toe_full_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(left_toe_full_ctrl, left_toe_full_ctrl_grp)
    cmds.delete(cmds.parentConstraint(left_toe_fk_pivot_grp, left_toe_full_ctrl_grp))
    cmds.parent(left_toe_full_ctrl_grp, left_foot_offset_data_grp)
    cmds.connectAttr(left_toe_full_ctrl + '.translate', left_toe_fk_pivot_grp + '.translate')
    cmds.connectAttr(left_toe_full_ctrl + '.rotate', left_toe_fk_pivot_grp + '.rotate')

    cmds.parent(left_leg_toe_ik_handle[0], left_toe_pos_pivot_grp)
    cmds.parent(left_leg_ball_ik_handle[0], left_ball_pivot_grp)
    cmds.parent(left_leg_rp_ik_handle[0], left_ball_pivot_grp)
    cmds.parentConstraint(left_foot_offset_data_grp, left_foot_pivot_grp, mo=True)

    cmds.connectAttr(left_ball_roll_ctrl + '.rotate', left_ball_pivot_grp + '.rotate', f=True)
    cmds.connectAttr(left_toe_roll_ctrl + '.rotate', left_toe_pivot_grp + '.rotate', f=True)
    cmds.connectAttr(left_heel_roll_ctrl + '.rotate', left_heel_pivot_grp + '.rotate', f=True)
    cmds.connectAttr(left_toe_up_down_ctrl + '.translate', left_toe_pos_pivot_grp + '.translate', f=True)

    # Left Leg Switch
    cmds.addAttr(left_leg_switch, ln='switchAttributes', at='enum', en='-------------:', keyable=True)
    cmds.addAttr(left_leg_switch, ln='influenceSwitch', at='double', k=True, maxValue=1, minValue=0)
    cmds.addAttr(left_leg_switch, ln='autoVisibility', at='bool', k=True)
    cmds.addAttr(left_leg_switch, ln='systemVisibility', at='enum', k=True, en="FK:IK:")
    cmds.addAttr(left_leg_switch, ln="footAutomation", at='enum', en='-------------:', keyable=True)
    cmds.addAttr(left_leg_switch, ln='generalCtrlVisibility', at='bool', k=True)
    cmds.addAttr(left_leg_switch, ln='fullToeCtrlVisibility', at='bool', k=True)
    cmds.setAttr(left_leg_switch + '.generalCtrlVisibility', 1)
    cmds.setAttr(left_leg_switch + '.footAutomation', lock=True)
    cmds.setAttr(left_leg_switch + '.switchAttributes', lock=True)
    cmds.setAttr(left_leg_switch + '.autoVisibility', 1)
    cmds.setAttr(left_leg_switch + '.systemVisibility', 1)
    cmds.setAttr(left_leg_switch + '.influenceSwitch', 1)

    left_switch_condition_node = cmds.createNode('condition', name='left_leg_switchVisibility_' + AUTO_SUFFIX)
    left_visibility_condition_node = cmds.createNode('condition', name='left_leg_autoVisibility_' + AUTO_SUFFIX)

    cmds.connectAttr(left_leg_switch + '.influenceSwitch', left_visibility_condition_node + '.firstTerm', f=True)
    cmds.setAttr(left_visibility_condition_node + '.operation', 3)
    cmds.setAttr(left_visibility_condition_node + '.secondTerm', .5)
    cmds.setAttr(left_visibility_condition_node + '.colorIfTrueR', 1)
    cmds.setAttr(left_visibility_condition_node + '.colorIfTrueG', 1)
    cmds.setAttr(left_visibility_condition_node + '.colorIfTrueB', 1)
    cmds.setAttr(left_visibility_condition_node + '.colorIfFalseR', 0)
    cmds.setAttr(left_visibility_condition_node + '.colorIfFalseG', 0)
    cmds.setAttr(left_visibility_condition_node + '.colorIfFalseB', 0)

    cmds.connectAttr(left_leg_switch + '.systemVisibility', left_switch_condition_node + '.colorIfFalseR', f=True)
    cmds.connectAttr(left_leg_switch + '.autoVisibility', left_switch_condition_node + '.firstTerm', f=True)
    cmds.setAttr(left_switch_condition_node + '.secondTerm', 1)

    cmds.connectAttr(left_visibility_condition_node + '.outColor', left_switch_condition_node + '.colorIfTrue', f=True)

    # IK Reverse
    left_v_reverse_node = cmds.createNode('reverse', name='left_leg_autoVisibility_reverse')
    cmds.connectAttr(left_switch_condition_node + '.outColorR', left_v_reverse_node + '.inputX', f=True)

    # IK Visibility
    visibility_ik = [left_foot_ik_ctrl_grp, left_knee_ik_ctrl_grp]

    for obj in visibility_ik:
        cmds.connectAttr(left_switch_condition_node + '.outColorR', obj + '.v', f=True)

    for shape in cmds.listRelatives(left_leg_switch, s=True, f=True) or []:
        if 'ik' in shape:
            cmds.connectAttr(left_switch_condition_node + '.outColorR', shape + '.v', f=True)

    # Fk Visibility
    visibility_fk = [left_hip_ctrl_grp, left_knee_ctrl_grp, left_ankle_ctrl_grp, left_ball_ctrl_grp]

    for obj in visibility_fk:
        cmds.connectAttr(left_v_reverse_node + '.outputX', obj + '.v', f=True)

    for shape in cmds.listRelatives(left_leg_switch, s=True, f=True) or []:
        if 'fk' in shape:
            cmds.connectAttr(left_v_reverse_node + '.outputX', shape + '.v', f=True)

    # FK IK Constraints
    left_hip_constraint = cmds.parentConstraint([left_hip_fk_jnt, left_hip_ik_jnt], rig_joints.get('left_hip_jnt'))
    left_knee_constraint = cmds.parentConstraint([left_knee_fk_jnt, left_knee_ik_jnt], rig_joints.get('left_knee_jnt'))
    left_ankle_constraint = cmds.parentConstraint([left_ankle_fk_jnt, left_ankle_ik_jnt],
                                                  rig_joints.get('left_ankle_jnt'))
    left_ball_constraint = cmds.parentConstraint([left_ball_fk_jnt, left_ball_ik_jnt], rig_joints.get('left_ball_jnt'))
    left_switch_constraint = cmds.parentConstraint([left_foot_offset_data_grp, left_ankle_ctrl], left_leg_switch_grp,
                                                   mo=True)

    left_switch_reverse_node = cmds.createNode('reverse', name='left_leg_switch_reverse')
    cmds.connectAttr(left_leg_switch + '.influenceSwitch', left_switch_reverse_node + '.inputX', f=True)

    # FK
    cmds.connectAttr(left_switch_reverse_node + '.outputX', left_hip_constraint[0] + '.w0', f=True)
    cmds.connectAttr(left_switch_reverse_node + '.outputX', left_knee_constraint[0] + '.w0', f=True)
    cmds.connectAttr(left_switch_reverse_node + '.outputX', left_ankle_constraint[0] + '.w0', f=True)
    cmds.connectAttr(left_switch_reverse_node + '.outputX', left_ball_constraint[0] + '.w0', f=True)
    cmds.connectAttr(left_switch_reverse_node + '.outputX', left_switch_constraint[0] + '.w1', f=True)

    # IK
    cmds.connectAttr(left_leg_switch + '.influenceSwitch', left_hip_constraint[0] + '.w1', f=True)
    cmds.connectAttr(left_leg_switch + '.influenceSwitch', left_knee_constraint[0] + '.w1', f=True)
    cmds.connectAttr(left_leg_switch + '.influenceSwitch', left_ankle_constraint[0] + '.w1', f=True)
    cmds.connectAttr(left_leg_switch + '.influenceSwitch', left_ball_constraint[0] + '.w1', f=True)
    cmds.connectAttr(left_leg_switch + '.influenceSwitch', left_switch_constraint[0] + '.w0', f=True)

    # Foot Automation Visibility
    cmds.connectAttr(left_leg_switch + '.generalCtrlVisibility', left_heel_roll_ctrl_grp + '.v', f=True)
    cmds.connectAttr(left_leg_switch + '.generalCtrlVisibility', left_ball_roll_ctrl_grp + '.v', f=True)
    cmds.connectAttr(left_leg_switch + '.generalCtrlVisibility', left_toe_roll_ctrl_grp + '.v', f=True)
    cmds.connectAttr(left_leg_switch + '.generalCtrlVisibility', left_toe_up_down_ctrl_grp + '.v', f=True)
    cmds.connectAttr(left_leg_switch + '.fullToeCtrlVisibility', left_toe_full_ctrl_grp + '.v', f=True)

    # Setup Shape Switch
    setup_shape_switch(left_foot_ik_ctrl, attr='controlShape', shape_names=['box', 'flat', 'pin'],
                       shape_enum=['Box', 'Flat', 'Pin'])

    # Left Foot In-Between
    # Offset ctrl was created earlier when creating the original ctrl
    cmds.setAttr(left_foot_offset_ik_ctrl + '.scaleX', .9)
    cmds.setAttr(left_foot_offset_ik_ctrl + '.scaleY', .9)
    cmds.setAttr(left_foot_offset_ik_ctrl + '.scaleZ', .9)
    cmds.makeIdentity(left_foot_offset_ik_ctrl, apply=True, scale=True)
    change_viewport_color(left_foot_offset_ik_ctrl, (.3, .6, 1))
    lock_hide_default_attr(left_foot_offset_ik_ctrl, translate=False, rotate=False, visibility=False)
    cmds.setAttr(left_foot_offset_ik_ctrl + '.v', k=False, channelBox=False)
    # Recreate Connections
    cmds.addAttr(left_foot_offset_ik_ctrl, ln='rotationOrder', at='enum', en=ROTATE_ORDER_ENUM, keyable=True,
                 niceName='Rotate Order')
    cmds.connectAttr(left_foot_offset_ik_ctrl + '.rotationOrder', left_foot_offset_ik_ctrl + '.rotateOrder', f=True)
    setup_shape_switch(left_foot_offset_ik_ctrl, attr='controlShape', shape_names=['box', 'flat', 'pin'],
                       shape_enum=['Box', 'Flat', 'Pin'])
    cmds.parent(left_foot_offset_ik_ctrl, left_foot_ik_ctrl)

    cmds.connectAttr(left_foot_offset_ik_ctrl + '.rotationOrder', left_foot_offset_data_grp + '.rotateOrder', f=True)
    cmds.parent(left_foot_offset_ik_ctrl, left_foot_offset_ik_ctrl_grp)
    cmds.parent(left_foot_offset_ik_ctrl_grp, left_foot_ik_ctrl)

    # Add Scale Ctrl for later
    cmds.addAttr(left_foot_ik_ctrl, ln='showScaleCtrl', at='bool', keyable=True)

    # Show Offset Ctrl
    cmds.addAttr(left_foot_ik_ctrl, ln='showOffsetCtrl', at='bool', k=True)
    cmds.connectAttr(left_foot_ik_ctrl + '.showOffsetCtrl', left_foot_offset_ik_ctrl + '.v', f=True)
    # #### End Wrist In-Between Offset

    # Left IK Knee Automation
    left_knee_ik_offset_grp = cmds.group(
        name=left_knee_ik_ctrl.replace('_ctrl', '_legOffset') + GRP_SUFFIX.capitalize(), empty=True, world=True)
    left_hip_ik_offset_reference = cmds.group(name=left_knee_ik_ctrl.replace('_ctrl', '_offsetReference'), empty=True,
                                              world=True)
    cmds.delete(cmds.parentConstraint(rig_joints.get('left_hip_jnt'), left_hip_ik_offset_reference))
    cmds.parent(left_hip_ik_offset_reference, hip_offset_data_grp)
    cmds.parent(left_knee_ik_offset_grp, direction_ctrl)
    cmds.pointConstraint([left_hip_ik_offset_reference, left_foot_offset_data_grp], left_knee_ik_offset_grp)

    left_leg_up_dir = cmds.group(name=left_knee_ik_ctrl.replace('_ctrl', '_legOffsetUpDir'), empty=True, world=True)
    cmds.move(general_scale_offset * 50, left_leg_up_dir, moveX=True)
    cmds.parent(left_leg_up_dir, direction_ctrl)
    cmds.aimConstraint(left_foot_offset_data_grp, left_knee_ik_offset_grp, upVector=(0, 1, 0), worldUpType="object",
                       worldUpObject=left_leg_up_dir)

    left_knee_ik_override_grp = cmds.group(
        name=left_knee_ik_ctrl.replace('_ctrl', '_override') + GRP_SUFFIX.capitalize(), empty=True, world=True)
    left_knee_ik_twist_override_grp = cmds.group(
        name=left_knee_ik_ctrl.replace('_ctrl', '_twistOverride') + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.delete(cmds.parentConstraint(left_knee_ik_offset_grp, left_knee_ik_override_grp))
    cmds.delete(cmds.parentConstraint(left_knee_ik_offset_grp, left_knee_ik_twist_override_grp))
    cmds.parent(left_knee_ik_override_grp, left_knee_ik_offset_grp)
    cmds.parent(left_knee_ik_twist_override_grp, left_knee_ik_override_grp)
    cmds.parent(left_knee_ik_ctrl_grp, left_knee_ik_twist_override_grp)

    left_knee_ctrl_constraint = cmds.parentConstraint([left_knee_ik_offset_grp, direction_ctrl],
                                                      left_knee_ik_override_grp, mo=True)
    cmds.addAttr(left_foot_ik_ctrl, ln='pVecFollowsLegPlane', at='float', k=True, maxValue=1, minValue=0,
                 niceName='Knee Follows Leg')
    cmds.setAttr(left_foot_ik_ctrl + '.pVecFollowsLegPlane', 1)
    cmds.connectAttr(left_foot_ik_ctrl + '.pVecFollowsLegPlane', left_knee_ctrl_constraint[0] + '.w0', f=True)
    left_knee_reverse_node = cmds.createNode('reverse', name='left_knee_parent_reverse')
    cmds.connectAttr(left_foot_ik_ctrl + '.pVecFollowsLegPlane', left_knee_reverse_node + '.inputX', f=True)
    cmds.connectAttr(left_knee_reverse_node + '.outputX', left_knee_ctrl_constraint[0] + '.w1', f=True)

    cmds.addAttr(left_foot_ik_ctrl, ln='pVecTwist', at='float', k=True, niceName='Knee Twist')
    cmds.connectAttr(left_foot_ik_ctrl + '.pVecTwist', left_knee_ik_twist_override_grp + '.rx', f=True)

    # Follow Foot Offset
    left_knee_ik_foot_offset_parent_grp = cmds.group(
        name=left_knee_ik_ctrl.replace('_ctrl', '_footOverrideData') + GRP_SUFFIX.capitalize(), empty=True, world=True)
    left_knee_ik_foot_offset_data_grp = cmds.group(name=left_knee_ik_ctrl.replace('_ctrl', '_footOverrideData'),
                                                   empty=True, world=True)
    cmds.parent(left_knee_ik_foot_offset_data_grp, left_knee_ik_foot_offset_parent_grp)
    cmds.delete(cmds.parentConstraint(left_foot_ik_ctrl, left_knee_ik_foot_offset_parent_grp))
    cmds.parentConstraint(left_foot_offset_data_grp, left_knee_ik_foot_offset_data_grp)
    cmds.parent(left_knee_ik_foot_offset_parent_grp, main_ctrl)

    left_knee_ik_foot_offset_grp = cmds.group(name=left_knee_ik_ctrl.replace('_ctrl', '_footOffsetDriver'), empty=True,
                                              world=True)
    left_knee_ik_foot_offset_parent_grp = cmds.group(
        name=left_knee_ik_ctrl.replace('_ctrl', '_footOffset') + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.delete(cmds.parentConstraint(left_foot_ik_ctrl, left_knee_ik_foot_offset_grp))
    cmds.delete(cmds.parentConstraint(left_foot_ik_ctrl, left_knee_ik_foot_offset_parent_grp))
    cmds.parent(left_knee_ik_foot_offset_grp, left_knee_ik_foot_offset_parent_grp)
    cmds.parent(left_knee_ik_foot_offset_parent_grp, left_knee_ik_twist_override_grp)
    cmds.parent(left_knee_ik_ctrl_grp, left_knee_ik_foot_offset_grp)

    cmds.addAttr(left_foot_ik_ctrl, ln='pVecFollowsFoot', at='float', k=True, maxValue=1, minValue=0,
                 niceName='Knee Follows Foot')

    left_foot_trans_multiply_node = cmds.createNode('multiplyDivide', name='left_foot_translate_parentOffset_multiply')
    left_foot_rot_multiply_node = cmds.createNode('multiplyDivide', name='left_foot_rotate_parentOffset_multiply')
    cmds.connectAttr(left_knee_ik_foot_offset_data_grp + '.translate', left_foot_trans_multiply_node + '.input1',
                     f=True)
    cmds.connectAttr(left_knee_ik_foot_offset_data_grp + '.rotate', left_foot_rot_multiply_node + '.input1', f=True)
    cmds.connectAttr(left_foot_trans_multiply_node + '.output', left_knee_ik_foot_offset_grp + '.translate', f=True)
    cmds.connectAttr(left_foot_rot_multiply_node + '.output', left_knee_ik_foot_offset_grp + '.rotate', f=True)

    for multiply_node in [left_foot_trans_multiply_node, left_foot_rot_multiply_node]:
        cmds.connectAttr(left_foot_ik_ctrl + '.pVecFollowsFoot', multiply_node + '.input2X', f=True)
        cmds.connectAttr(left_foot_ik_ctrl + '.pVecFollowsFoot', multiply_node + '.input2Y', f=True)
        cmds.connectAttr(left_foot_ik_ctrl + '.pVecFollowsFoot', multiply_node + '.input2Z', f=True)

    # Left Leg Stretchy System
    cmds.addAttr(left_leg_switch, ln="squashStretch", at='enum', en='-------------:', keyable=True)
    cmds.setAttr(left_leg_switch + '.squashStretch', lock=True)

    left_leg_stretchy_elements = make_stretchy_ik(left_leg_rp_ik_handle[0], 'left_leg', left_leg_switch)

    # Change Stretchy System to be compatible with roll controls
    for child in cmds.listRelatives(left_leg_stretchy_elements[0], children=True) or []:
        if 'Constraint' in child:
            cmds.delete(child)
    cmds.parentConstraint(left_ball_pivot_grp, left_leg_stretchy_elements[0], mo=True)

    # Transfer Data to Base Skeleton
    left_hip_scale_blend = cmds.createNode('blendColors', name='left_hip_switchScale_blend')
    left_knee_scale_blend = cmds.createNode('blendColors', name='left_knee_switchScale_blend')

    cmds.connectAttr(left_hip_ik_jnt + '.scale', left_hip_scale_blend + '.color1', f=True)
    cmds.connectAttr(left_hip_fk_jnt + '.scale', left_hip_scale_blend + '.color2', f=True)
    cmds.connectAttr(left_leg_switch + '.influenceSwitch', left_hip_scale_blend + '.blender', f=True)
    cmds.connectAttr(left_hip_scale_blend + '.output', rig_joints.get('left_hip_jnt') + '.scale', f=True)

    cmds.connectAttr(left_knee_ik_jnt + '.scale', left_knee_scale_blend + '.color1', f=True)
    cmds.connectAttr(left_knee_fk_jnt + '.scale', left_knee_scale_blend + '.color2', f=True)
    cmds.connectAttr(left_leg_switch + '.influenceSwitch', left_knee_scale_blend + '.blender', f=True)
    cmds.connectAttr(left_knee_scale_blend + '.output', rig_joints.get('left_knee_jnt') + '.scale', f=True)

    # Left Foot Control Limits
    # Heel, Ball and Toe
    for ctrl in [left_heel_roll_ctrl, left_ball_roll_ctrl, left_toe_roll_ctrl]:
        cmds.addAttr(ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
        cmds.setAttr(ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)
        cmds.addAttr(ctrl, ln='lockYZ', at='bool', k=True)
        cmds.setAttr(ctrl + '.lockYZ', 1)

        cmds.setAttr(ctrl + '.minRotYLimit', 0)
        cmds.setAttr(ctrl + '.maxRotYLimit', 0)
        cmds.setAttr(ctrl + '.minRotZLimit', 0)
        cmds.setAttr(ctrl + '.maxRotZLimit', 0)

        cmds.connectAttr(ctrl + '.lockYZ', ctrl + '.minRotYLimitEnable', f=True)
        cmds.connectAttr(ctrl + '.lockYZ', ctrl + '.maxRotYLimitEnable', f=True)
        cmds.connectAttr(ctrl + '.lockYZ', ctrl + '.minRotZLimitEnable', f=True)
        cmds.connectAttr(ctrl + '.lockYZ', ctrl + '.maxRotZLimitEnable', f=True)

    # Left Toe Up and Down
    cmds.addAttr(left_toe_up_down_ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
    cmds.setAttr(left_toe_up_down_ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)
    cmds.addAttr(left_toe_up_down_ctrl, ln='lockXZ', at='bool', k=True)
    cmds.setAttr(left_toe_up_down_ctrl + '.lockXZ', 1)

    cmds.setAttr(left_toe_up_down_ctrl + '.minTransXLimit', 0)
    cmds.setAttr(left_toe_up_down_ctrl + '.maxTransXLimit', 0)
    cmds.setAttr(left_toe_up_down_ctrl + '.minTransZLimit', 0)
    cmds.setAttr(left_toe_up_down_ctrl + '.maxTransZLimit', 0)

    cmds.connectAttr(left_toe_up_down_ctrl + '.lockXZ', left_toe_up_down_ctrl + '.minTransXLimitEnable', f=True)
    cmds.connectAttr(left_toe_up_down_ctrl + '.lockXZ', left_toe_up_down_ctrl + '.maxTransXLimitEnable', f=True)
    cmds.connectAttr(left_toe_up_down_ctrl + '.lockXZ', left_toe_up_down_ctrl + '.minTransZLimitEnable', f=True)
    cmds.connectAttr(left_toe_up_down_ctrl + '.lockXZ', left_toe_up_down_ctrl + '.maxTransZLimitEnable', f=True)

    # ################# Right Leg IK Controls #################
    # Right Leg IK
    right_leg_rp_ik_handle = cmds.ikHandle(n='right_footAnkle_RP_ikHandle', sj=right_hip_ik_jnt, ee=right_ankle_ik_jnt,
                                           sol='ikRPsolver')
    right_leg_ball_ik_handle = cmds.ikHandle(n='right_footBall_SC_ikHandle', sj=right_ankle_ik_jnt,
                                             ee=right_ball_ik_jnt, sol='ikSCsolver')
    right_leg_toe_ik_handle = cmds.ikHandle(n='right_footToe_SC_ikHandle', sj=right_ball_ik_jnt, ee=right_toe_ik_jnt,
                                            sol='ikSCsolver')
    cmds.poleVectorConstraint(right_knee_ik_ctrl, right_leg_rp_ik_handle[0])

    # Right Foot Automation Setup
    right_foot_pivot_grp = cmds.group(name='right_foot_pivot' + GRP_SUFFIX.capitalize(), empty=True, world=True)
    right_heel_pivot_grp = cmds.group(name='right_heel_pivot' + GRP_SUFFIX.capitalize(), empty=True, world=True)
    right_ball_pivot_grp = cmds.group(name='right_ball_pivot' + GRP_SUFFIX.capitalize(), empty=True, world=True)
    right_toe_pivot_grp = cmds.group(name='right_toe_pivot' + GRP_SUFFIX.capitalize(), empty=True, world=True)
    right_toe_pos_pivot_grp = cmds.group(name='right_toeUpDown_pivot' + GRP_SUFFIX.capitalize(), empty=True, world=True)
    # cmds.parent(right_toe_pos_pivot_grp, right_toe_pivot_grp)

    # FK Toe Influence
    right_toe_fk_pivot_grp = cmds.group(name='right_toe_fk_pivot' + GRP_SUFFIX.capitalize(), empty=True, world=True)
    right_toe_fk_pivot_zero_grp = cmds.group(name='right_toe_fk_zero' + GRP_SUFFIX.capitalize(), empty=True, world=True)
    right_toe_pos_zero_grp = cmds.group(name='right_toeUpDown_zero' + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(right_toe_pos_pivot_grp, right_toe_pos_zero_grp)
    cmds.parent(right_toe_pos_zero_grp, right_toe_pivot_grp)
    cmds.delete(cmds.pointConstraint(rig_joints.get('right_ball_jnt'), right_toe_fk_pivot_grp))
    cmds.delete(cmds.pointConstraint(rig_joints.get('right_ball_jnt'), right_toe_fk_pivot_zero_grp))

    cmds.delete(cmds.pointConstraint(rig_joints.get('right_ankle_jnt'), right_foot_pivot_grp))
    cmds.delete(cmds.pointConstraint(elements.get('right_ball_pivot_grp'), right_heel_pivot_grp))
    cmds.delete(cmds.pointConstraint(rig_joints.get('right_ball_jnt'), right_ball_pivot_grp))
    cmds.delete(cmds.pointConstraint(rig_joints.get('right_toe_jnt'), right_toe_pivot_grp))

    desired_rotation = cmds.xform(elements.get('right_ankle_proxy_crv'), q=True, ro=True)
    cmds.setAttr(right_foot_pivot_grp + '.ry', desired_rotation[1])
    cmds.setAttr(right_heel_pivot_grp + '.ry', desired_rotation[1])
    cmds.setAttr(right_ball_pivot_grp + '.ry', desired_rotation[1])
    cmds.setAttr(right_toe_pivot_grp + '.ry', desired_rotation[1])

    if cmds.objExists(elements_default.get('right_heel_proxy_pivot')):
        cmds.delete(
            cmds.pointConstraint(elements_default.get('right_heel_proxy_pivot'), right_heel_pivot_grp))

    cmds.parent(right_foot_pivot_grp, rig_setup_grp)
    cmds.parent(right_heel_pivot_grp, right_foot_pivot_grp)
    cmds.parent(right_toe_pivot_grp, right_heel_pivot_grp)
    cmds.parent(right_ball_pivot_grp, right_toe_pivot_grp)

    cmds.parent(right_toe_fk_pivot_grp, right_toe_fk_pivot_zero_grp)
    cmds.parent(right_toe_fk_pivot_zero_grp, right_toe_pivot_grp)
    cmds.parent(right_toe_pos_zero_grp, right_toe_fk_pivot_grp)

    right_toe_full_ctrl = cmds.curve(name='right_toe_ik_' + CTRL_SUFFIX,
                                     p=[[0.0, 0.0, 0.0], [0.0, -0.398, -0.229], [0.0, -0.409, -0.217],
                                        [0.0, -0.423, -0.206], [0.0, -0.439, -0.2], [0.0, -0.456, -0.197],
                                        [0.0, -0.473, -0.2], [0.0, -0.488, -0.206], [0.0, -0.456, -0.264],
                                        [0.0, -0.398, -0.229], [0.0, -0.392, -0.246], [0.0, -0.389, -0.264],
                                        [0.0, -0.392, -0.281], [0.0, -0.398, -0.296], [0.0, -0.409, -0.31],
                                        [0.0, -0.423, -0.319], [0.0, -0.439, -0.327], [0.0, -0.456, -0.329],
                                        [0.0, -0.473, -0.327], [0.0, -0.488, -0.319], [0.0, -0.502, -0.31],
                                        [0.0, -0.513, -0.296], [0.0, -0.519, -0.281], [0.0, -0.521, -0.264],
                                        [0.0, -0.519, -0.246], [0.0, -0.513, -0.229], [0.0, -0.502, -0.215],
                                        [0.0, -0.488, -0.206], [0.0, -0.423, -0.319], [0.0, -0.456, -0.264],
                                        [0.0, -0.513, -0.296]], d=1)
    rescale(right_toe_full_ctrl, right_foot_scale_offset, True)
    change_viewport_color(right_toe_full_ctrl, RIGHT_CTRL_COLOR)
    lock_hide_default_attr(right_toe_full_ctrl, translate=False, rotate=False)
    right_toe_full_ctrl_grp = cmds.group(name=right_toe_full_ctrl + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.parent(right_toe_full_ctrl, right_toe_full_ctrl_grp)
    cmds.delete(cmds.parentConstraint(right_toe_fk_pivot_grp, right_toe_full_ctrl_grp))
    cmds.parent(right_toe_full_ctrl_grp, right_foot_offset_data_grp)
    cmds.connectAttr(right_toe_full_ctrl + '.translate', right_toe_fk_pivot_grp + '.translate')
    cmds.connectAttr(right_toe_full_ctrl + '.rotate', right_toe_fk_pivot_grp + '.rotate')

    cmds.parent(right_leg_toe_ik_handle[0], right_toe_pos_pivot_grp)
    cmds.parent(right_leg_ball_ik_handle[0], right_ball_pivot_grp)
    cmds.parent(right_leg_rp_ik_handle[0], right_ball_pivot_grp)
    cmds.parentConstraint(right_foot_offset_data_grp, right_foot_pivot_grp, mo=True)

    cmds.connectAttr(right_ball_roll_ctrl + '.rotate', right_ball_pivot_grp + '.rotate', f=True)
    cmds.connectAttr(right_toe_roll_ctrl + '.rotate', right_toe_pivot_grp + '.rotate', f=True)
    cmds.connectAttr(right_heel_roll_ctrl + '.rotate', right_heel_pivot_grp + '.rotate', f=True)
    cmds.connectAttr(right_toe_up_down_ctrl + '.translate', right_toe_pos_pivot_grp + '.translate', f=True)

    # Right Leg Switch
    cmds.addAttr(right_leg_switch, ln='switchAttributes', at='enum', en='-------------:', keyable=True)
    cmds.addAttr(right_leg_switch, ln='influenceSwitch', at='double', k=True, maxValue=1, minValue=0)
    cmds.addAttr(right_leg_switch, ln='autoVisibility', at='bool', k=True)
    cmds.addAttr(right_leg_switch, ln='systemVisibility', at='enum', k=True, en="FK:IK:")
    cmds.addAttr(right_leg_switch, ln="footAutomation", at='enum', en='-------------:', keyable=True)
    cmds.addAttr(right_leg_switch, ln='generalCtrlVisibility', at='bool', k=True)
    cmds.addAttr(right_leg_switch, ln='fullToeCtrlVisibility', at='bool', k=True)

    cmds.setAttr(right_leg_switch + '.generalCtrlVisibility', 1)
    cmds.setAttr(right_leg_switch + '.footAutomation', lock=True)
    cmds.setAttr(right_leg_switch + '.switchAttributes', lock=True)
    cmds.setAttr(right_leg_switch + '.autoVisibility', 1)
    cmds.setAttr(right_leg_switch + '.systemVisibility', 1)
    cmds.setAttr(right_leg_switch + '.influenceSwitch', 1)

    right_switch_condition_node = cmds.createNode('condition', name='right_leg_switchVisibility_' + AUTO_SUFFIX)
    right_visibility_condition_node = cmds.createNode('condition', name='right_leg_autoVisibility_' + AUTO_SUFFIX)

    cmds.connectAttr(right_leg_switch + '.influenceSwitch', right_visibility_condition_node + '.firstTerm', f=True)
    cmds.setAttr(right_visibility_condition_node + '.operation', 3)
    cmds.setAttr(right_visibility_condition_node + '.secondTerm', .5)
    cmds.setAttr(right_visibility_condition_node + '.colorIfTrueR', 1)
    cmds.setAttr(right_visibility_condition_node + '.colorIfTrueG', 1)
    cmds.setAttr(right_visibility_condition_node + '.colorIfTrueB', 1)
    cmds.setAttr(right_visibility_condition_node + '.colorIfFalseR', 0)
    cmds.setAttr(right_visibility_condition_node + '.colorIfFalseG', 0)
    cmds.setAttr(right_visibility_condition_node + '.colorIfFalseB', 0)

    cmds.connectAttr(right_leg_switch + '.systemVisibility', right_switch_condition_node + '.colorIfFalseR', f=True)
    cmds.connectAttr(right_leg_switch + '.autoVisibility', right_switch_condition_node + '.firstTerm', f=True)
    cmds.setAttr(right_switch_condition_node + '.secondTerm', 1)

    cmds.connectAttr(right_visibility_condition_node + '.outColor', right_switch_condition_node + '.colorIfTrue',
                     f=True)

    # IK Reverse
    right_v_reverse_node = cmds.createNode('reverse', name='right_leg_autoVisibility_reverse')
    cmds.connectAttr(right_switch_condition_node + '.outColorR', right_v_reverse_node + '.inputX', f=True)

    # IK Visibility
    visibility_ik = [right_foot_ik_ctrl_grp, right_knee_ik_ctrl_grp]

    for obj in visibility_ik:
        cmds.connectAttr(right_switch_condition_node + '.outColorR', obj + '.v', f=True)

    for shape in cmds.listRelatives(right_leg_switch, s=True, f=True) or []:
        if 'ik' in shape:
            cmds.connectAttr(right_switch_condition_node + '.outColorR', shape + '.v', f=True)

    # Fk Visibility
    visibility_fk = [right_hip_ctrl_grp, right_knee_ctrl_grp, right_ankle_ctrl_grp, right_ball_ctrl_grp]

    for obj in visibility_fk:
        cmds.connectAttr(right_v_reverse_node + '.outputX', obj + '.v', f=True)

    for shape in cmds.listRelatives(right_leg_switch, s=True, f=True) or []:
        if 'fk' in shape:
            cmds.connectAttr(right_v_reverse_node + '.outputX', shape + '.v', f=True)

    # FK IK Constraints
    right_hip_constraint = cmds.parentConstraint([right_hip_fk_jnt, right_hip_ik_jnt], rig_joints.get('right_hip_jnt'))
    right_knee_constraint = cmds.parentConstraint([right_knee_fk_jnt, right_knee_ik_jnt],
                                                  rig_joints.get('right_knee_jnt'))
    right_ankle_constraint = cmds.parentConstraint([right_ankle_fk_jnt, right_ankle_ik_jnt],
                                                   rig_joints.get('right_ankle_jnt'))
    right_ball_constraint = cmds.parentConstraint([right_ball_fk_jnt, right_ball_ik_jnt],
                                                  rig_joints.get('right_ball_jnt'))
    right_switch_constraint = cmds.parentConstraint([right_foot_ik_ctrl, right_ankle_ctrl], right_leg_switch_grp,
                                                    mo=True)

    right_switch_reverse_node = cmds.createNode('reverse', name='right_leg_switch_reverse')
    cmds.connectAttr(right_leg_switch + '.influenceSwitch', right_switch_reverse_node + '.inputX', f=True)

    # FK
    cmds.connectAttr(right_switch_reverse_node + '.outputX', right_hip_constraint[0] + '.w0', f=True)
    cmds.connectAttr(right_switch_reverse_node + '.outputX', right_knee_constraint[0] + '.w0', f=True)
    cmds.connectAttr(right_switch_reverse_node + '.outputX', right_ankle_constraint[0] + '.w0', f=True)
    cmds.connectAttr(right_switch_reverse_node + '.outputX', right_ball_constraint[0] + '.w0', f=True)
    cmds.connectAttr(right_switch_reverse_node + '.outputX', right_switch_constraint[0] + '.w1', f=True)

    # IK
    cmds.connectAttr(right_leg_switch + '.influenceSwitch', right_hip_constraint[0] + '.w1', f=True)
    cmds.connectAttr(right_leg_switch + '.influenceSwitch', right_knee_constraint[0] + '.w1', f=True)
    cmds.connectAttr(right_leg_switch + '.influenceSwitch', right_ankle_constraint[0] + '.w1', f=True)
    cmds.connectAttr(right_leg_switch + '.influenceSwitch', right_ball_constraint[0] + '.w1', f=True)
    cmds.connectAttr(right_leg_switch + '.influenceSwitch', right_switch_constraint[0] + '.w0', f=True)

    # Foot Automation Visibility
    cmds.connectAttr(right_leg_switch + '.generalCtrlVisibility', right_heel_roll_ctrl_grp + '.v', f=True)
    cmds.connectAttr(right_leg_switch + '.generalCtrlVisibility', right_ball_roll_ctrl_grp + '.v', f=True)
    cmds.connectAttr(right_leg_switch + '.generalCtrlVisibility', right_toe_roll_ctrl_grp + '.v', f=True)
    cmds.connectAttr(right_leg_switch + '.generalCtrlVisibility', right_toe_up_down_ctrl_grp + '.v', f=True)
    cmds.connectAttr(right_leg_switch + '.fullToeCtrlVisibility', right_toe_full_ctrl_grp + '.v', f=True)

    # Setup Shape Switch
    setup_shape_switch(right_foot_ik_ctrl, attr='controlShape', shape_names=['box', 'flat', 'pin'],
                       shape_enum=['Box', 'Flat', 'Pin'])

    # Right Foot In-Between
    # Offset ctrl was created earlier when creating the original ctrl
    cmds.setAttr(right_foot_offset_ik_ctrl + '.scaleX', .9)
    cmds.setAttr(right_foot_offset_ik_ctrl + '.scaleY', .9)
    cmds.setAttr(right_foot_offset_ik_ctrl + '.scaleZ', .9)
    cmds.makeIdentity(right_foot_offset_ik_ctrl, apply=True, scale=True)
    change_viewport_color(right_foot_offset_ik_ctrl, (1, .3, .3))
    lock_hide_default_attr(right_foot_offset_ik_ctrl, translate=False, rotate=False, visibility=False)
    cmds.setAttr(right_foot_offset_ik_ctrl + '.v', k=False, channelBox=False)
    # Recreate Connections
    cmds.addAttr(right_foot_offset_ik_ctrl, ln='rotationOrder', at='enum', en=ROTATE_ORDER_ENUM, keyable=True,
                 niceName='Rotate Order')
    cmds.connectAttr(right_foot_offset_ik_ctrl + '.rotationOrder', right_foot_offset_ik_ctrl + '.rotateOrder', f=True)
    setup_shape_switch(right_foot_offset_ik_ctrl, attr='controlShape', shape_names=['box', 'flat', 'pin'],
                       shape_enum=['Box', 'Flat', 'Pin'])
    cmds.parent(right_foot_offset_ik_ctrl, right_foot_ik_ctrl)

    cmds.connectAttr(right_foot_offset_ik_ctrl + '.rotationOrder', right_foot_offset_data_grp + '.rotateOrder', f=True)
    cmds.parent(right_foot_offset_ik_ctrl, right_foot_offset_ik_ctrl_grp)
    cmds.parent(right_foot_offset_ik_ctrl_grp, right_foot_ik_ctrl)

    # Add Scale Ctrl for later
    cmds.addAttr(right_foot_ik_ctrl, ln='showScaleCtrl', at='bool', keyable=True)

    # Show Offset Ctrl
    cmds.addAttr(right_foot_ik_ctrl, ln='showOffsetCtrl', at='bool', k=True)
    cmds.connectAttr(right_foot_ik_ctrl + '.showOffsetCtrl', right_foot_offset_ik_ctrl + '.v', f=True)

    # #### End Wrist In-Between Offset

    # Right IK Knee Automation
    right_knee_ik_offset_grp = cmds.group(
        name=right_knee_ik_ctrl.replace('_ctrl', '_legOffset') + GRP_SUFFIX.capitalize(), empty=True, world=True)
    right_hip_ik_offset_reference = cmds.group(name=right_knee_ik_ctrl.replace('_ctrl', '_offsetReference'), empty=True,
                                               world=True)
    cmds.delete(cmds.parentConstraint(rig_joints.get('right_hip_jnt'), right_hip_ik_offset_reference))
    cmds.parent(right_hip_ik_offset_reference, hip_offset_data_grp)
    cmds.parent(right_knee_ik_offset_grp, direction_ctrl)
    cmds.pointConstraint([right_hip_ik_offset_reference, right_foot_offset_data_grp], right_knee_ik_offset_grp)

    right_leg_up_dir = cmds.group(name=right_knee_ik_ctrl.replace('_ctrl', '_legOffsetUpDir'), empty=True, world=True)
    cmds.move(general_scale_offset * -50, right_leg_up_dir, moveX=True)
    cmds.parent(right_leg_up_dir, direction_ctrl)
    cmds.aimConstraint(right_foot_offset_data_grp, right_knee_ik_offset_grp, upVector=(0, 1, 0), worldUpType="object",
                       worldUpObject=right_leg_up_dir)  # No WORKING

    right_knee_ik_override_grp = cmds.group(
        name=right_knee_ik_ctrl.replace('_ctrl', '_override') + GRP_SUFFIX.capitalize(), empty=True, world=True)
    right_knee_ik_twist_override_grp = cmds.group(
        name=right_knee_ik_ctrl.replace('_ctrl', '_twistOverride') + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.delete(cmds.parentConstraint(right_knee_ik_offset_grp, right_knee_ik_override_grp))
    cmds.delete(cmds.parentConstraint(right_knee_ik_offset_grp, right_knee_ik_twist_override_grp))
    cmds.parent(right_knee_ik_override_grp, right_knee_ik_offset_grp)
    cmds.parent(right_knee_ik_twist_override_grp, right_knee_ik_override_grp)
    cmds.parent(right_knee_ik_ctrl_grp, right_knee_ik_twist_override_grp)

    right_knee_ctrl_constraint = cmds.parentConstraint([right_knee_ik_offset_grp, direction_ctrl],
                                                       right_knee_ik_override_grp, mo=True)
    cmds.addAttr(right_foot_ik_ctrl, ln='pVecFollowsLegPlane', at='float', k=True, maxValue=1, minValue=0,
                 niceName='Knee Follows Leg')
    cmds.setAttr(right_foot_ik_ctrl + '.pVecFollowsLegPlane', 1)
    cmds.connectAttr(right_foot_ik_ctrl + '.pVecFollowsLegPlane', right_knee_ctrl_constraint[0] + '.w0', f=True)
    right_knee_reverse_node = cmds.createNode('reverse', name='right_knee_parent_reverse')
    cmds.connectAttr(right_foot_ik_ctrl + '.pVecFollowsLegPlane', right_knee_reverse_node + '.inputX', f=True)
    cmds.connectAttr(right_knee_reverse_node + '.outputX', right_knee_ctrl_constraint[0] + '.w1', f=True)

    cmds.addAttr(right_foot_ik_ctrl, ln='pVecTwist', at='float', k=True, niceName='Knee Twist')
    cmds.connectAttr(right_foot_ik_ctrl + '.pVecTwist', right_knee_ik_twist_override_grp + '.rx', f=True)

    # Follow Foot Offset
    right_knee_ik_foot_offset_parent_grp = cmds.group(
        name=right_knee_ik_ctrl.replace('_ctrl', '_footOverrideData') + GRP_SUFFIX.capitalize(), empty=True, world=True)
    right_knee_ik_foot_offset_data_grp = cmds.group(name=right_knee_ik_ctrl.replace('_ctrl', '_footOverrideData'),
                                                    empty=True, world=True)
    cmds.parent(right_knee_ik_foot_offset_data_grp, right_knee_ik_foot_offset_parent_grp)
    cmds.delete(cmds.parentConstraint(right_foot_ik_ctrl, right_knee_ik_foot_offset_parent_grp))
    cmds.parentConstraint(right_foot_offset_data_grp, right_knee_ik_foot_offset_data_grp)
    cmds.parent(right_knee_ik_foot_offset_parent_grp, main_ctrl)

    right_knee_ik_foot_offset_grp = cmds.group(name=right_knee_ik_ctrl.replace('_ctrl', '_footOffsetDriver'),
                                               empty=True, world=True)
    right_knee_ik_foot_offset_parent_grp = cmds.group(
        name=right_knee_ik_ctrl.replace('_ctrl', '_footOffset') + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.delete(cmds.parentConstraint(right_foot_ik_ctrl, right_knee_ik_foot_offset_grp))
    cmds.delete(cmds.parentConstraint(right_foot_ik_ctrl, right_knee_ik_foot_offset_parent_grp))
    cmds.parent(right_knee_ik_foot_offset_grp, right_knee_ik_foot_offset_parent_grp)
    cmds.parent(right_knee_ik_foot_offset_parent_grp, right_knee_ik_twist_override_grp)
    cmds.parent(right_knee_ik_ctrl_grp, right_knee_ik_foot_offset_grp)

    cmds.addAttr(right_foot_ik_ctrl, ln='pVecFollowsFoot', at='float', k=True, maxValue=1, minValue=0,
                 niceName='Knee Follows Foot')

    right_foot_trans_multiply_node = cmds.createNode('multiplyDivide',
                                                     name='right_foot_translate_parentOffset_multiply')
    right_foot_rot_multiply_node = cmds.createNode('multiplyDivide', name='right_foot_rotate_parentOffset_multiply')
    cmds.connectAttr(right_knee_ik_foot_offset_data_grp + '.translate', right_foot_trans_multiply_node + '.input1',
                     f=True)
    cmds.connectAttr(right_knee_ik_foot_offset_data_grp + '.rotate', right_foot_rot_multiply_node + '.input1', f=True)
    cmds.connectAttr(right_foot_trans_multiply_node + '.output', right_knee_ik_foot_offset_grp + '.translate', f=True)
    cmds.connectAttr(right_foot_rot_multiply_node + '.output', right_knee_ik_foot_offset_grp + '.rotate', f=True)

    for multiply_node in [right_foot_trans_multiply_node, right_foot_rot_multiply_node]:
        cmds.connectAttr(right_foot_ik_ctrl + '.pVecFollowsFoot', multiply_node + '.input2X', f=True)
        cmds.connectAttr(right_foot_ik_ctrl + '.pVecFollowsFoot', multiply_node + '.input2Y', f=True)
        cmds.connectAttr(right_foot_ik_ctrl + '.pVecFollowsFoot', multiply_node + '.input2Z', f=True)

    # Right Leg Stretchy System
    cmds.addAttr(right_leg_switch, ln="squashStretch", at='enum', en='-------------:', keyable=True)
    cmds.setAttr(right_leg_switch + '.squashStretch', lock=True)

    right_leg_stretchy_elements = make_stretchy_ik(right_leg_rp_ik_handle[0], 'right_leg', right_leg_switch)

    # Change Stretchy System to be compatible with roll controls
    for child in cmds.listRelatives(right_leg_stretchy_elements[0], children=True) or []:
        if 'Constraint' in child:
            cmds.delete(child)
    cmds.parentConstraint(right_ball_pivot_grp, right_leg_stretchy_elements[0], mo=True)

    # Transfer Data to Base Skeleton
    right_hip_scale_blend = cmds.createNode('blendColors', name='right_hip_switchScale_blend')
    right_knee_scale_blend = cmds.createNode('blendColors', name='right_knee_switchScale_blend')

    cmds.connectAttr(right_hip_ik_jnt + '.scale', right_hip_scale_blend + '.color1', f=True)
    cmds.connectAttr(right_hip_fk_jnt + '.scale', right_hip_scale_blend + '.color2', f=True)
    cmds.connectAttr(right_leg_switch + '.influenceSwitch', right_hip_scale_blend + '.blender', f=True)
    cmds.connectAttr(right_hip_scale_blend + '.output', rig_joints.get('right_hip_jnt') + '.scale', f=True)

    cmds.connectAttr(right_knee_ik_jnt + '.scale', right_knee_scale_blend + '.color1', f=True)
    cmds.connectAttr(right_knee_fk_jnt + '.scale', right_knee_scale_blend + '.color2', f=True)
    cmds.connectAttr(right_leg_switch + '.influenceSwitch', right_knee_scale_blend + '.blender', f=True)
    cmds.connectAttr(right_knee_scale_blend + '.output', rig_joints.get('right_knee_jnt') + '.scale', f=True)

    # Right Foot Control Limits
    # Heel, Ball and Toe
    for ctrl in [right_heel_roll_ctrl, right_ball_roll_ctrl, right_toe_roll_ctrl]:
        cmds.addAttr(ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
        cmds.setAttr(ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)
        cmds.addAttr(ctrl, ln='lockYZ', at='bool', k=True)
        cmds.setAttr(ctrl + '.lockYZ', 1)

        cmds.setAttr(ctrl + '.minRotYLimit', 0)
        cmds.setAttr(ctrl + '.maxRotYLimit', 0)
        cmds.setAttr(ctrl + '.minRotZLimit', 0)
        cmds.setAttr(ctrl + '.maxRotZLimit', 0)

        cmds.connectAttr(ctrl + '.lockYZ', ctrl + '.minRotYLimitEnable', f=True)
        cmds.connectAttr(ctrl + '.lockYZ', ctrl + '.maxRotYLimitEnable', f=True)
        cmds.connectAttr(ctrl + '.lockYZ', ctrl + '.minRotZLimitEnable', f=True)
        cmds.connectAttr(ctrl + '.lockYZ', ctrl + '.maxRotZLimitEnable', f=True)

    # Right Toe Up and Down
    cmds.addAttr(right_toe_up_down_ctrl, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
    cmds.setAttr(right_toe_up_down_ctrl + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)
    cmds.addAttr(right_toe_up_down_ctrl, ln='lockXZ', at='bool', k=True)
    cmds.setAttr(right_toe_up_down_ctrl + '.lockXZ', 1)

    cmds.setAttr(right_toe_up_down_ctrl + '.minTransXLimit', 0)
    cmds.setAttr(right_toe_up_down_ctrl + '.maxTransXLimit', 0)
    cmds.setAttr(right_toe_up_down_ctrl + '.minTransZLimit', 0)
    cmds.setAttr(right_toe_up_down_ctrl + '.maxTransZLimit', 0)

    cmds.connectAttr(right_toe_up_down_ctrl + '.lockXZ', right_toe_up_down_ctrl + '.minTransXLimitEnable', f=True)
    cmds.connectAttr(right_toe_up_down_ctrl + '.lockXZ', right_toe_up_down_ctrl + '.maxTransXLimitEnable', f=True)
    cmds.connectAttr(right_toe_up_down_ctrl + '.lockXZ', right_toe_up_down_ctrl + '.minTransZLimitEnable', f=True)
    cmds.connectAttr(right_toe_up_down_ctrl + '.lockXZ', right_toe_up_down_ctrl + '.maxTransZLimitEnable', f=True)

    # ################# Left Arm Controls #################
    # Left Arm Handles
    left_arm_rp_ik_handle = cmds.ikHandle(n='left_armWrist_RP_ikHandle', sj=left_shoulder_ik_jnt, ee=left_wrist_ik_jnt,
                                          sol='ikRPsolver')
    cmds.poleVectorConstraint(left_elbow_ik_ctrl, left_arm_rp_ik_handle[0])
    cmds.parent(left_arm_rp_ik_handle[0], ik_solvers_grp)
    cmds.pointConstraint(left_wrist_offset_ik_ctrl, left_arm_rp_ik_handle[0])

    cmds.select(d=True)
    cmds.select(left_wrist_ik_jnt)
    left_wrist_ik_dir_jnt = cmds.duplicate(name=left_wrist_ik_jnt.replace('ik', 'ikDir'))
    cmds.parent(left_wrist_ik_dir_jnt, world=True)

    # Left Arm Switch
    cmds.addAttr(left_arm_switch, ln='switchAttributes', at='enum', en='-------------:', keyable=True)
    cmds.addAttr(left_arm_switch, ln='influenceSwitch', at='double', k=True, maxValue=1, minValue=0)
    cmds.addAttr(left_arm_switch, ln='autoVisibility', at='bool', k=True)
    cmds.addAttr(left_arm_switch, ln='systemVisibility', at='enum', k=True, en="FK:IK:")
    cmds.addAttr(left_arm_switch, ln="fingerAutomation", at='enum', en='-------------:', keyable=True)
    cmds.addAttr(left_arm_switch, ln='ctrlVisibility', at='bool', k=True)
    cmds.setAttr(left_arm_switch + '.ctrlVisibility', 1)
    cmds.setAttr(left_arm_switch + '.fingerAutomation', lock=True)
    cmds.setAttr(left_arm_switch + '.switchAttributes', lock=True)
    cmds.setAttr(left_arm_switch + '.autoVisibility', 1)
    cmds.setAttr(left_arm_switch + '.systemVisibility', 1)
    cmds.setAttr(left_arm_switch + '.influenceSwitch', 1)

    left_switch_condition_node = cmds.createNode('condition', name='left_arm_switchVisibility_' + AUTO_SUFFIX)
    left_visibility_condition_node = cmds.createNode('condition', name='left_arm_autoVisibility_' + AUTO_SUFFIX)

    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_visibility_condition_node + '.firstTerm', f=True)
    cmds.setAttr(left_visibility_condition_node + '.operation', 3)
    cmds.setAttr(left_visibility_condition_node + '.secondTerm', .5)
    cmds.setAttr(left_visibility_condition_node + '.colorIfTrueR', 1)
    cmds.setAttr(left_visibility_condition_node + '.colorIfTrueG', 1)
    cmds.setAttr(left_visibility_condition_node + '.colorIfTrueB', 1)
    cmds.setAttr(left_visibility_condition_node + '.colorIfFalseR', 0)
    cmds.setAttr(left_visibility_condition_node + '.colorIfFalseG', 0)
    cmds.setAttr(left_visibility_condition_node + '.colorIfFalseB', 0)

    cmds.connectAttr(left_arm_switch + '.systemVisibility', left_switch_condition_node + '.colorIfFalseR', f=True)
    cmds.connectAttr(left_arm_switch + '.autoVisibility', left_switch_condition_node + '.firstTerm', f=True)
    cmds.setAttr(left_switch_condition_node + '.secondTerm', 1)

    cmds.connectAttr(left_visibility_condition_node + '.outColor', left_switch_condition_node + '.colorIfTrue', f=True)

    # IK Reverse
    left_v_reverse_node = cmds.createNode('reverse', name='left_arm_autoVisibility_reverse')
    cmds.connectAttr(left_switch_condition_node + '.outColorR', left_v_reverse_node + '.inputX', f=True)

    # IK Visibility
    visibility_ik = [left_wrist_ik_ctrl_grp, left_elbow_ik_ctrl_grp]

    for obj in visibility_ik:
        cmds.connectAttr(left_switch_condition_node + '.outColorR', obj + '.v', f=True)

    for shape in cmds.listRelatives(left_arm_switch, s=True, f=True) or []:
        if 'ik' in shape:
            cmds.connectAttr(left_switch_condition_node + '.outColorR', shape + '.v', f=True)

    # Fk Visibility
    visibility_fk = [left_shoulder_ctrl_grp, left_elbow_ctrl_grp, left_wrist_ctrl_grp]

    for obj in visibility_fk:
        cmds.connectAttr(left_v_reverse_node + '.outputX', obj + '.v', f=True)

    for shape in cmds.listRelatives(left_arm_switch, s=True, f=True) or []:
        if 'fk' in shape:
            cmds.connectAttr(left_v_reverse_node + '.outputX', shape + '.v', f=True)

    # FK IK Constraints
    left_shoulder_constraint = cmds.parentConstraint([left_shoulder_fk_jnt, left_shoulder_ik_jnt],
                                                     rig_joints.get('left_shoulder_jnt'), mo=True)
    left_elbow_constraint = cmds.parentConstraint([left_elbow_fk_jnt, left_elbow_ik_jnt],
                                                  rig_joints.get('left_elbow_jnt'), mo=True)
    left_wrist_constraint = cmds.pointConstraint([left_wrist_fk_jnt, left_wrist_ik_jnt],
                                                 rig_joints.get('left_wrist_jnt'), mo=True)
    left_switch_constraint = cmds.parentConstraint([left_wrist_offset_ik_ctrl, left_wrist_ctrl], left_arm_switch_grp,
                                                   mo=True)

    left_switch_reverse_node = cmds.createNode('reverse', name='left_arm_switch_reverse')
    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_switch_reverse_node + '.inputX', f=True)

    # FK
    cmds.connectAttr(left_switch_reverse_node + '.outputX', left_shoulder_constraint[0] + '.w0', f=True)
    cmds.connectAttr(left_switch_reverse_node + '.outputX', left_elbow_constraint[0] + '.w0', f=True)
    cmds.connectAttr(left_switch_reverse_node + '.outputX', left_wrist_constraint[0] + '.w0', f=True)
    cmds.connectAttr(left_switch_reverse_node + '.outputX', left_switch_constraint[0] + '.w1', f=True)

    # IK
    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_shoulder_constraint[0] + '.w1', f=True)
    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_elbow_constraint[0] + '.w1', f=True)
    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_wrist_constraint[0] + '.w1', f=True)
    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_switch_constraint[0] + '.w0', f=True)

    # Left Transfer Raw Rotate
    left_wrist_rotate_blend = cmds.createNode('blendColors', name='left_wrist_rotate_blend')
    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_wrist_rotate_blend + '.blender', f=True)
    cmds.connectAttr(left_wrist_fk_jnt + '.rotate', left_wrist_rotate_blend + '.color2', f=True)
    cmds.connectAttr(left_wrist_ik_jnt + '.rotate', left_wrist_rotate_blend + '.color1', f=True)
    cmds.connectAttr(left_wrist_rotate_blend + '.output', rig_joints.get('left_wrist_jnt') + '.rotate', f=True)

    # Arm Automation Visibility
    cmds.connectAttr(left_arm_switch + '.ctrlVisibility', left_fingers_ctrl_grp + '.v', f=True)

    # Left IK Wrist Automation
    left_elbow_ik_offset_grp = cmds.group(
        name=left_elbow_ik_ctrl.replace('_ctrl', '_armOffset') + GRP_SUFFIX.capitalize(), empty=True, world=True)
    left_shoulder_ik_offset_reference = cmds.group(name=left_elbow_ik_ctrl.replace('_ctrl', '_offsetReference'),
                                                   empty=True, world=True)
    cmds.delete(cmds.parentConstraint(rig_joints.get('left_shoulder_jnt'), left_shoulder_ik_offset_reference))
    cmds.parent(left_shoulder_ik_offset_reference, left_clavicle_ctrl)
    cmds.parent(left_elbow_ik_offset_grp, direction_ctrl)
    cmds.pointConstraint([left_shoulder_ik_offset_reference, left_wrist_offset_ik_ctrl], left_elbow_ik_offset_grp)

    left_arm_up_dir = cmds.group(name=left_elbow_ik_ctrl.replace('_ctrl', '_armOffsetUpDir'), empty=True, world=True)
    cmds.parent(left_arm_up_dir, main_ctrl)
    cmds.parentConstraint(rig_joints.get('spine04_jnt'), left_arm_up_dir, mo=True)
    cmds.aimConstraint(left_wrist_offset_ik_ctrl, left_elbow_ik_offset_grp, upVector=(0, 1, 0), worldUpType="object",
                       worldUpObject=left_arm_up_dir)

    left_elbow_ik_override_grp = cmds.group(
        name=left_elbow_ik_ctrl.replace('_ctrl', '_override') + GRP_SUFFIX.capitalize(), empty=True, world=True)
    left_elbow_ik_twist_override_grp = cmds.group(
        name=left_elbow_ik_ctrl.replace('_ctrl', '_twistOverride') + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.delete(cmds.parentConstraint(left_elbow_ik_offset_grp, left_elbow_ik_override_grp))
    cmds.delete(cmds.parentConstraint(left_elbow_ik_offset_grp, left_elbow_ik_twist_override_grp))
    cmds.parent(left_elbow_ik_override_grp, left_elbow_ik_offset_grp)
    cmds.parent(left_elbow_ik_twist_override_grp, left_elbow_ik_override_grp)
    cmds.parent(left_elbow_ik_ctrl_grp, left_elbow_ik_twist_override_grp)

    left_wrist_ctrl_constraint = cmds.parentConstraint([left_elbow_ik_offset_grp, direction_ctrl],
                                                       left_elbow_ik_override_grp, mo=True)
    cmds.addAttr(left_wrist_ik_ctrl, ln='pVecFollowsArmPlane', at='float', k=True, maxValue=1, minValue=0,
                 niceName='Elbow Follows Arm')
    cmds.setAttr(left_wrist_ik_ctrl + '.pVecFollowsArmPlane', 1)
    cmds.connectAttr(left_wrist_ik_ctrl + '.pVecFollowsArmPlane', left_wrist_ctrl_constraint[0] + '.w0', f=True)
    left_wrist_reverse_node = cmds.createNode('reverse', name='left_wrist_parent_reverse')
    cmds.connectAttr(left_wrist_ik_ctrl + '.pVecFollowsArmPlane', left_wrist_reverse_node + '.inputX', f=True)
    cmds.connectAttr(left_wrist_reverse_node + '.outputX', left_wrist_ctrl_constraint[0] + '.w1', f=True)

    cmds.addAttr(left_wrist_ik_ctrl, ln='pVecTwist', at='float', k=True, niceName='Elbow Twist')
    cmds.connectAttr(left_wrist_ik_ctrl + '.pVecTwist', left_elbow_ik_twist_override_grp + '.rx', f=True)

    # Follow Wrist Offset
    left_elbow_ik_wrist_offset_parent_grp = cmds.group(
        name=left_elbow_ik_ctrl.replace('_ctrl', '_wristOverrideData') + GRP_SUFFIX.capitalize(), empty=True,
        world=True)
    left_elbow_ik_wrist_offset_data_grp = cmds.group(name=left_elbow_ik_ctrl.replace('_ctrl', '_wristOverrideData'),
                                                     empty=True, world=True)
    cmds.parent(left_elbow_ik_wrist_offset_data_grp, left_elbow_ik_wrist_offset_parent_grp)
    cmds.delete(cmds.parentConstraint(left_wrist_ik_ctrl, left_elbow_ik_wrist_offset_parent_grp))
    cmds.parentConstraint(left_wrist_offset_ik_ctrl, left_elbow_ik_wrist_offset_data_grp)
    cmds.parent(left_elbow_ik_wrist_offset_parent_grp, main_ctrl)

    left_elbow_ik_wrist_offset_grp = cmds.group(name=left_elbow_ik_ctrl.replace('_ctrl', '_wristOffsetDriver'),
                                                empty=True, world=True)
    left_elbow_ik_wrist_offset_parent_grp = cmds.group(
        name=left_elbow_ik_ctrl.replace('_ctrl', '_wristOffset') + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.delete(cmds.parentConstraint(left_wrist_ik_ctrl, left_elbow_ik_wrist_offset_grp))
    cmds.delete(cmds.parentConstraint(left_wrist_ik_ctrl, left_elbow_ik_wrist_offset_parent_grp))
    cmds.parent(left_elbow_ik_wrist_offset_grp, left_elbow_ik_wrist_offset_parent_grp)
    cmds.parent(left_elbow_ik_wrist_offset_parent_grp, left_elbow_ik_twist_override_grp)
    cmds.parent(left_elbow_ik_ctrl_grp, left_elbow_ik_wrist_offset_grp)

    cmds.addAttr(left_wrist_ik_ctrl, ln='pVecFollowsWrist', at='float', k=True, maxValue=1, minValue=0,
                 niceName='Elbow Follows Wrist')

    left_wrist_trans_multiply_node = cmds.createNode('multiplyDivide',
                                                     name='left_wrist_translate_parentOffset_multiply')
    left_wrist_rot_multiply_node = cmds.createNode('multiplyDivide', name='left_wrist_rotate_parentOffset_multiply')
    cmds.connectAttr(left_elbow_ik_wrist_offset_data_grp + '.translate', left_wrist_trans_multiply_node + '.input1',
                     f=True)
    cmds.connectAttr(left_elbow_ik_wrist_offset_data_grp + '.rotate', left_wrist_rot_multiply_node + '.input1', f=True)
    cmds.connectAttr(left_wrist_trans_multiply_node + '.output', left_elbow_ik_wrist_offset_grp + '.translate', f=True)
    cmds.connectAttr(left_wrist_rot_multiply_node + '.output', left_elbow_ik_wrist_offset_grp + '.rotate', f=True)

    for multiply_node in [left_wrist_trans_multiply_node, left_wrist_rot_multiply_node]:
        cmds.connectAttr(left_wrist_ik_ctrl + '.pVecFollowsWrist', multiply_node + '.input2X', f=True)
        cmds.connectAttr(left_wrist_ik_ctrl + '.pVecFollowsWrist', multiply_node + '.input2Y', f=True)
        cmds.connectAttr(left_wrist_ik_ctrl + '.pVecFollowsWrist', multiply_node + '.input2Z', f=True)

    # Left Leg Stretchy System
    cmds.addAttr(left_arm_switch, ln="squashStretch", at='enum', en='-------------:', keyable=True)
    cmds.setAttr(left_arm_switch + '.squashStretch', lock=True)
    left_arm_stretchy_elements = make_stretchy_ik(left_arm_rp_ik_handle[0], 'left_arm', left_arm_switch)

    # Transfer Data to Base Skeleton
    left_shoulder_scale_blend = cmds.createNode('blendColors', name='left_shoulder_switchScale_blend')
    left_elbow_scale_blend = cmds.createNode('blendColors', name='left_elbow_switchScale_blend')

    cmds.connectAttr(left_shoulder_ik_jnt + '.scale', left_shoulder_scale_blend + '.color1', f=True)
    cmds.connectAttr(left_shoulder_fk_jnt + '.scale', left_shoulder_scale_blend + '.color2', f=True)
    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_shoulder_scale_blend + '.blender', f=True)
    cmds.connectAttr(left_shoulder_scale_blend + '.output', rig_joints.get('left_shoulder_jnt') + '.scale', f=True)

    cmds.connectAttr(left_elbow_ik_jnt + '.scale', left_elbow_scale_blend + '.color1', f=True)
    cmds.connectAttr(left_elbow_fk_jnt + '.scale', left_elbow_scale_blend + '.color2', f=True)
    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_elbow_scale_blend + '.blender', f=True)
    cmds.connectAttr(left_elbow_scale_blend + '.output', rig_joints.get('left_elbow_jnt') + '.scale', f=True)

    # Left Arm Separator
    cmds.addAttr(left_arm_switch, ln="armControls", at='enum', en='-------------:', keyable=True)
    cmds.setAttr(left_arm_switch + '.armControls', lock=True)

    # Left Fingers Limits (Connections)
    cmds.connectAttr(left_fingers_ctrl + '.maximumRotationZ', left_fingers_ctrl + '.maxRotZLimit', f=True)
    cmds.connectAttr(left_fingers_ctrl + '.minimumRotationZ', left_fingers_ctrl + '.minRotZLimit', f=True)

    left_rot_reverse_node = cmds.createNode('reverse', name='left_fingers_rotateShape_reverse')
    cmds.connectAttr(left_fingers_ctrl + '.rotateShape', left_rot_reverse_node + '.inputX')
    cmds.connectAttr(left_rot_reverse_node + '.outputX', left_fingers_inverse_rot_multiply_node + '.input2X')
    cmds.connectAttr(left_rot_reverse_node + '.outputX', left_fingers_inverse_rot_multiply_node + '.input2Y')
    cmds.connectAttr(left_rot_reverse_node + '.outputX', left_fingers_inverse_rot_multiply_node + '.input2Z')

    # Left Finger Curls Visibility (Connections)
    for curl_ctrl in left_curl_controls:
        for shape in cmds.listRelatives(curl_ctrl, s=True, f=True) or []:
            cmds.connectAttr(left_fingers_ctrl + '.showCurlControls', shape + '.v', f=True)

    # Left Finger Ctrl Visibility (Connections)
    for finger_parent in [left_thumb01_ctrl_list[1], left_index01_ctrl_list[1], left_middle01_ctrl_list[1],
                          left_ring01_ctrl_list[1], left_pinky01_ctrl_list[1]]:
        cmds.connectAttr(left_fingers_ctrl + '.showFkFingerCtrls', finger_parent + '.v', f=True)

    # Left Forearm Rotation & Scale
    left_forearm_grp = cmds.group(name=left_forearm_jnt + GRP_SUFFIX.capitalize(), empty=True, world=True)
    left_forearm_loc = cmds.spaceLocator(name=left_forearm_jnt.replace(JNT_SUFFIX, 'posLoc'))[0]
    cmds.setAttr(left_forearm_loc + '.v', 0)
    change_viewport_color(left_forearm_loc, LEFT_CTRL_COLOR)
    cmds.parent(left_forearm_loc, left_forearm_grp)

    cmds.delete(cmds.parentConstraint(rig_joints.get('left_elbow_jnt'), left_forearm_grp))

    cmds.parent(left_forearm_grp, skeleton_grp)
    cmds.pointConstraint([rig_joints.get('left_elbow_jnt'), rig_joints.get('left_wrist_jnt')], left_forearm_grp)
    cmds.setAttr(left_forearm_jnt + '.tx', 0)
    cmds.setAttr(left_forearm_jnt + '.ty', 0)
    cmds.setAttr(left_forearm_jnt + '.tz', 0)

    cmds.addAttr(left_arm_switch, ln='forearmRotation', at='double', k=True, maxValue=1, minValue=0)
    cmds.setAttr(left_arm_switch + '.forearmRotation', .5)

    cmds.addAttr(left_arm_switch, ln='forearmScale', at='double', k=True, minValue=0.01)
    cmds.setAttr(left_arm_switch + '.forearmScale', 1)
    cmds.connectAttr(left_arm_switch + '.forearmScale', left_forearm_jnt + '.sx', f=True)
    cmds.connectAttr(left_arm_switch + '.forearmScale', left_forearm_jnt + '.sy', f=True)
    cmds.connectAttr(left_arm_switch + '.forearmScale', left_forearm_jnt + '.sz', f=True)

    left_forearm_multiply_node = cmds.createNode('multiplyDivide', name="left_arm_forearmRotation_" + MULTIPLY_SUFFIX)
    left_forearm_blend_node = cmds.createNode('blendTwoAttr', name='left_arm_forearmRotation_blend')

    cmds.connectAttr('%s.rx' % left_wrist_ik_ctrl, '%s.input[0]' % left_forearm_blend_node)
    cmds.connectAttr('%s.rx' % left_wrist_ctrl, '%s.input[1]' % left_forearm_blend_node)

    cmds.connectAttr(left_arm_switch + '.forearmRotation', left_forearm_multiply_node + '.input2X', f=True)
    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_forearm_blend_node + '.attributesBlender', f=True)

    # cmds.connectAttr(rig_joints.get('left_wrist_jnt') + '.rotateX', left_forearm_multiply_node + '.input1X', f=True)
    cmds.connectAttr(left_forearm_multiply_node + '.outputX', left_forearm_jnt + '.rotateX', f=True)

    cmds.pointConstraint(left_forearm_loc, left_forearm_jnt)  # Receive Position from Mechanics

    # Clean Twist System (Aim) ############### ###############
    left_elbow_twist_sample_jnt = rig_joints.get('left_elbow_jnt')
    left_elbow_twist_sample_jnt = left_elbow_twist_sample_jnt.replace(JNT_SUFFIX, 'aim' + JNT_SUFFIX.capitalize())
    left_elbow_twist_sample_jnt = cmds.duplicate(rig_joints.get('left_elbow_jnt'),
                                                 name=left_elbow_twist_sample_jnt,
                                                 parentOnly=True)[0]
    change_viewport_color(left_elbow_twist_sample_jnt, (1, 0, 1))

    left_wrist_twist_sample_jnt = rig_joints.get('left_wrist_jnt')
    left_wrist_twist_sample_jnt = left_wrist_twist_sample_jnt.replace(JNT_SUFFIX, 'aim' + JNT_SUFFIX.capitalize())
    left_wrist_twist_sample_jnt = cmds.duplicate(left_elbow_twist_sample_jnt,
                                                 name=left_wrist_twist_sample_jnt,
                                                 parentOnly=True)[0]

    cmds.setAttr(left_wrist_twist_sample_jnt + '.rotateOrder', 1)
    cmds.parent(left_wrist_twist_sample_jnt, left_elbow_twist_sample_jnt)
    cmds.pointConstraint(rig_joints.get('left_wrist_jnt'), left_wrist_twist_sample_jnt)
    cmds.parent(left_elbow_twist_sample_jnt, skeleton_grp)
    cmds.parentConstraint(rig_joints.get('left_elbow_jnt'), left_elbow_twist_sample_jnt)
    left_wrist_aim_loc = cmds.spaceLocator(name=rig_joints.get('left_wrist_jnt').replace(JNT_SUFFIX, 'twistLoc'))[0]
    cmds.delete(cmds.parentConstraint(left_wrist_twist_sample_jnt, left_wrist_aim_loc))
    cmds.move(general_scale_offset * .4, left_wrist_aim_loc, moveY=True, relative=True, objectSpace=True)
    change_viewport_color(left_wrist_aim_loc, (1, 0, 1))
    cmds.parentConstraint(rig_joints.get('left_wrist_jnt'), left_wrist_aim_loc, mo=True)
    cmds.aimConstraint(left_elbow_twist_sample_jnt, left_wrist_twist_sample_jnt,
                       aimVector=(-1, 0, 0),
                       upVector=(0, 1, 0),
                       worldUpType="object",
                       worldUpObject=left_wrist_aim_loc)
    cmds.connectAttr(left_wrist_twist_sample_jnt + '.rotateX', left_forearm_multiply_node + '.input1X', f=True)
    cmds.parent(left_wrist_aim_loc, arms_automation_grp)
    cmds.setAttr(left_elbow_twist_sample_jnt + '.v', 0)
    new_radius = cmds.getAttr(left_elbow_twist_sample_jnt + '.radius') * 0.5
    cmds.setAttr(left_elbow_twist_sample_jnt + '.radius', new_radius)
    cmds.setAttr(left_wrist_twist_sample_jnt + '.radius', new_radius)

    # ############## ############## ############## #############

    # Left IK Switcher Parent System
    left_clavicle_wrist_constraint = cmds.parentConstraint(
        [controls_grp, left_clavicle_ctrl, rig_joints.get('spine04_jnt')], left_wrist_ik_ctrl_grp, mo=True)
    cmds.addAttr(left_arm_switch, ln='parent', at='enum', k=True, en="World:Clavicle:Chest:")
    cmds.setAttr(left_arm_switch + '.parent', 2)

    left_switch_world_condition_node = cmds.createNode('condition', name='left_arm_parentWorld_' + AUTO_SUFFIX)
    left_switch_clavicle_condition_node = cmds.createNode('condition', name='left_arm_parentClavicle_' + AUTO_SUFFIX)
    left_switch_chest_condition_node = cmds.createNode('condition', name='left_arm_parentChest_' + AUTO_SUFFIX)

    cmds.setAttr(left_switch_world_condition_node + '.secondTerm', 0)
    cmds.setAttr(left_switch_clavicle_condition_node + '.secondTerm', 1)
    cmds.setAttr(left_switch_chest_condition_node + '.secondTerm', 2)

    for node in [left_switch_world_condition_node, left_switch_clavicle_condition_node,
                 left_switch_chest_condition_node]:
        cmds.setAttr(node + '.colorIfTrueR', 1)
        cmds.setAttr(node + '.colorIfTrueG', 1)
        cmds.setAttr(node + '.colorIfTrueB', 1)
        cmds.setAttr(node + '.colorIfFalseR', 0)
        cmds.setAttr(node + '.colorIfFalseG', 0)
        cmds.setAttr(node + '.colorIfFalseB', 0)

    cmds.connectAttr(left_arm_switch + '.parent', left_switch_world_condition_node + '.firstTerm', f=True)
    cmds.connectAttr(left_arm_switch + '.parent', left_switch_clavicle_condition_node + '.firstTerm', f=True)
    cmds.connectAttr(left_arm_switch + '.parent', left_switch_chest_condition_node + '.firstTerm', f=True)

    cmds.connectAttr(left_switch_world_condition_node + '.outColorR', left_clavicle_wrist_constraint[0] + '.w0', f=True)
    cmds.connectAttr(left_switch_clavicle_condition_node + '.outColorR', left_clavicle_wrist_constraint[0] + '.w1',
                     f=True)
    cmds.connectAttr(left_switch_chest_condition_node + '.outColorR', left_clavicle_wrist_constraint[0] + '.w2', f=True)

    # ################# Right Arm Controls #################
    # Right Arm Handles
    right_arm_rp_ik_handle = cmds.ikHandle(n='right_armWrist_RP_ikHandle', sj=right_shoulder_ik_jnt,
                                           ee=right_wrist_ik_jnt, sol='ikRPsolver')
    cmds.poleVectorConstraint(right_elbow_ik_ctrl, right_arm_rp_ik_handle[0])
    cmds.parent(right_arm_rp_ik_handle[0], ik_solvers_grp)
    cmds.pointConstraint(right_wrist_offset_ik_ctrl, right_arm_rp_ik_handle[0])

    cmds.select(d=True)
    cmds.select(right_wrist_ik_jnt)
    right_wrist_ik_dir_jnt = cmds.duplicate(name=right_wrist_ik_jnt.replace('ik', 'ikDir'))
    cmds.parent(right_wrist_ik_dir_jnt, world=True)

    # Right Arm Switch
    cmds.addAttr(right_arm_switch, ln='switchAttributes', at='enum', en='-------------:', keyable=True)
    cmds.addAttr(right_arm_switch, ln='influenceSwitch', at='double', k=True, maxValue=1, minValue=0)
    cmds.addAttr(right_arm_switch, ln='autoVisibility', at='bool', k=True)
    cmds.addAttr(right_arm_switch, ln='systemVisibility', at='enum', k=True, en="FK:IK:")
    cmds.addAttr(right_arm_switch, ln="fingerAutomation", at='enum', en='-------------:', keyable=True)
    cmds.addAttr(right_arm_switch, ln='ctrlVisibility', at='bool', k=True)
    cmds.setAttr(right_arm_switch + '.ctrlVisibility', 1)
    cmds.setAttr(right_arm_switch + '.fingerAutomation', lock=True)
    cmds.setAttr(right_arm_switch + '.switchAttributes', lock=True)
    cmds.setAttr(right_arm_switch + '.autoVisibility', 1)
    cmds.setAttr(right_arm_switch + '.systemVisibility', 1)
    cmds.setAttr(right_arm_switch + '.influenceSwitch', 1)

    right_switch_condition_node = cmds.createNode('condition', name='right_arm_switchVisibility_' + AUTO_SUFFIX)
    right_visibility_condition_node = cmds.createNode('condition', name='right_arm_autoVisibility_' + AUTO_SUFFIX)

    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_visibility_condition_node + '.firstTerm', f=True)
    cmds.setAttr(right_visibility_condition_node + '.operation', 3)
    cmds.setAttr(right_visibility_condition_node + '.secondTerm', .5)
    cmds.setAttr(right_visibility_condition_node + '.colorIfTrueR', 1)
    cmds.setAttr(right_visibility_condition_node + '.colorIfTrueG', 1)
    cmds.setAttr(right_visibility_condition_node + '.colorIfTrueB', 1)
    cmds.setAttr(right_visibility_condition_node + '.colorIfFalseR', 0)
    cmds.setAttr(right_visibility_condition_node + '.colorIfFalseG', 0)
    cmds.setAttr(right_visibility_condition_node + '.colorIfFalseB', 0)

    cmds.connectAttr(right_arm_switch + '.systemVisibility', right_switch_condition_node + '.colorIfFalseR', f=True)
    cmds.connectAttr(right_arm_switch + '.autoVisibility', right_switch_condition_node + '.firstTerm', f=True)
    cmds.setAttr(right_switch_condition_node + '.secondTerm', 1)

    cmds.connectAttr(right_visibility_condition_node + '.outColor', right_switch_condition_node + '.colorIfTrue',
                     f=True)

    # IK Reverse
    right_v_reverse_node = cmds.createNode('reverse', name='right_arm_autoVisibility_reverse')
    cmds.connectAttr(right_switch_condition_node + '.outColorR', right_v_reverse_node + '.inputX', f=True)

    # IK Visibility
    visibility_ik = [right_wrist_ik_ctrl_grp, right_elbow_ik_ctrl_grp]

    for obj in visibility_ik:
        cmds.connectAttr(right_switch_condition_node + '.outColorR', obj + '.v', f=True)

    for shape in cmds.listRelatives(right_arm_switch, s=True, f=True) or []:
        if 'ik' in shape:
            cmds.connectAttr(right_switch_condition_node + '.outColorR', shape + '.v', f=True)

    # Fk Visibility
    visibility_fk = [right_shoulder_ctrl_grp, right_elbow_ctrl_grp, right_wrist_ctrl_grp]

    for obj in visibility_fk:
        cmds.connectAttr(right_v_reverse_node + '.outputX', obj + '.v', f=True)

    for shape in cmds.listRelatives(right_arm_switch, s=True, f=True) or []:
        if 'fk' in shape:
            cmds.connectAttr(right_v_reverse_node + '.outputX', shape + '.v', f=True)

    # FK IK Constraints
    right_shoulder_constraint = cmds.parentConstraint([right_shoulder_fk_jnt, right_shoulder_ik_jnt],
                                                      rig_joints.get('right_shoulder_jnt'), mo=True)
    right_elbow_constraint = cmds.parentConstraint([right_elbow_fk_jnt, right_elbow_ik_jnt],
                                                   rig_joints.get('right_elbow_jnt'), mo=True)
    right_wrist_constraint = cmds.pointConstraint([right_wrist_fk_jnt, right_wrist_ik_jnt],
                                                  rig_joints.get('right_wrist_jnt'), mo=True)
    right_switch_constraint = cmds.parentConstraint([right_wrist_offset_ik_ctrl, right_wrist_ctrl],
                                                    right_arm_switch_grp, mo=True)

    right_switch_reverse_node = cmds.createNode('reverse', name='right_arm_switch_reverse')
    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_switch_reverse_node + '.inputX', f=True)

    # FK
    cmds.connectAttr(right_switch_reverse_node + '.outputX', right_shoulder_constraint[0] + '.w0', f=True)
    cmds.connectAttr(right_switch_reverse_node + '.outputX', right_elbow_constraint[0] + '.w0', f=True)
    cmds.connectAttr(right_switch_reverse_node + '.outputX', right_wrist_constraint[0] + '.w0', f=True)
    cmds.connectAttr(right_switch_reverse_node + '.outputX', right_switch_constraint[0] + '.w1', f=True)

    # IK
    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_shoulder_constraint[0] + '.w1', f=True)
    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_elbow_constraint[0] + '.w1', f=True)
    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_wrist_constraint[0] + '.w1', f=True)
    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_switch_constraint[0] + '.w0', f=True)

    # Right Transfer Raw Rotate
    right_wrist_rotate_blend = cmds.createNode('blendColors', name='right_wrist_rotate_blend')
    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_wrist_rotate_blend + '.blender', f=True)
    cmds.connectAttr(right_wrist_fk_jnt + '.rotate', right_wrist_rotate_blend + '.color2', f=True)
    cmds.connectAttr(right_wrist_ik_jnt + '.rotate', right_wrist_rotate_blend + '.color1', f=True)
    cmds.connectAttr(right_wrist_rotate_blend + '.output', rig_joints.get('right_wrist_jnt') + '.rotate', f=True)

    # Arm Automation Visibility
    cmds.connectAttr(right_arm_switch + '.ctrlVisibility', right_fingers_ctrl_grp + '.v', f=True)

    # Right IK Wrist Automation
    right_elbow_ik_offset_grp = cmds.group(
        name=right_elbow_ik_ctrl.replace('_ctrl', '_offset') + GRP_SUFFIX.capitalize(), empty=True, world=True)
    right_shoulder_ik_offset_reference = cmds.group(name=right_elbow_ik_ctrl.replace('_ctrl', '_offsetReference'),
                                                    empty=True, world=True)
    cmds.delete(cmds.parentConstraint(rig_joints.get('right_shoulder_jnt'), right_shoulder_ik_offset_reference))
    cmds.parent(right_shoulder_ik_offset_reference, right_clavicle_ctrl)
    cmds.parent(right_elbow_ik_offset_grp, direction_ctrl)
    cmds.pointConstraint([right_shoulder_ik_offset_reference, right_wrist_offset_ik_ctrl], right_elbow_ik_offset_grp)

    right_arm_up_dir = cmds.group(name=right_elbow_ik_ctrl.replace('_ctrl', '_armOffsetUpDir'), empty=True, world=True)
    cmds.parent(right_arm_up_dir, main_ctrl)
    cmds.parentConstraint(rig_joints.get('spine04_jnt'), right_arm_up_dir, mo=True)
    cmds.aimConstraint(right_wrist_offset_ik_ctrl, right_elbow_ik_offset_grp, upVector=(0, 1, 0), worldUpType="object",
                       worldUpObject=right_arm_up_dir)

    right_elbow_ik_override_grp = cmds.group(
        name=right_elbow_ik_ctrl.replace('_ctrl', '_override') + GRP_SUFFIX.capitalize(), empty=True, world=True)
    right_elbow_ik_twist_override_grp = cmds.group(
        name=right_elbow_ik_ctrl.replace('_ctrl', '_twistOverride') + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.delete(cmds.parentConstraint(right_elbow_ik_offset_grp, right_elbow_ik_override_grp))
    cmds.delete(cmds.parentConstraint(right_elbow_ik_offset_grp, right_elbow_ik_twist_override_grp))
    cmds.parent(right_elbow_ik_override_grp, right_elbow_ik_offset_grp)
    cmds.parent(right_elbow_ik_twist_override_grp, right_elbow_ik_override_grp)
    cmds.parent(right_elbow_ik_ctrl_grp, right_elbow_ik_twist_override_grp)

    right_wrist_ctrl_constraint = cmds.parentConstraint([right_elbow_ik_offset_grp, direction_ctrl],
                                                        right_elbow_ik_override_grp, mo=True)
    cmds.addAttr(right_wrist_ik_ctrl, ln='pVecFollowsArmPlane', at='float', k=True, maxValue=1, minValue=0,
                 niceName='Elbow Follows Arm')
    cmds.setAttr(right_wrist_ik_ctrl + '.pVecFollowsArmPlane', 1)
    cmds.connectAttr(right_wrist_ik_ctrl + '.pVecFollowsArmPlane', right_wrist_ctrl_constraint[0] + '.w0', f=True)
    right_wrist_reverse_node = cmds.createNode('reverse', name='right_wrist_parent_reverse')
    cmds.connectAttr(right_wrist_ik_ctrl + '.pVecFollowsArmPlane', right_wrist_reverse_node + '.inputX', f=True)
    cmds.connectAttr(right_wrist_reverse_node + '.outputX', right_wrist_ctrl_constraint[0] + '.w1', f=True)

    cmds.addAttr(right_wrist_ik_ctrl, ln='pVecTwist', at='float', k=True, niceName='Elbow Twist')

    # Multiply Negative (Invert Right Side)
    right_upvec_twist_multiply_reverse_node = cmds.createNode('multiplyDivide', name='right_pVecTwist_multiply')
    cmds.setAttr(right_upvec_twist_multiply_reverse_node + '.input2X', -1)
    cmds.setAttr(right_upvec_twist_multiply_reverse_node + '.input2Y', -1)
    cmds.setAttr(right_upvec_twist_multiply_reverse_node + '.input2Z', -1)
    cmds.connectAttr(right_wrist_ik_ctrl + '.pVecTwist', right_upvec_twist_multiply_reverse_node + '.input1X', f=True)
    cmds.connectAttr(right_upvec_twist_multiply_reverse_node + '.outputX', right_elbow_ik_twist_override_grp + '.rx',
                     f=True)

    # Follow Wrist Offset
    right_elbow_ik_wrist_offset_parent_grp = cmds.group(
        name=right_elbow_ik_ctrl.replace('_ctrl', '_wristOverrideData') + GRP_SUFFIX.capitalize(), empty=True,
        world=True)
    right_elbow_ik_wrist_offset_data_grp = cmds.group(name=right_elbow_ik_ctrl.replace('_ctrl', '_wristOverrideData'),
                                                      empty=True, world=True)
    cmds.parent(right_elbow_ik_wrist_offset_data_grp, right_elbow_ik_wrist_offset_parent_grp)
    cmds.delete(cmds.parentConstraint(right_wrist_ik_ctrl, right_elbow_ik_wrist_offset_parent_grp))
    cmds.parentConstraint(right_wrist_offset_ik_ctrl, right_elbow_ik_wrist_offset_data_grp)
    cmds.parent(right_elbow_ik_wrist_offset_parent_grp, main_ctrl)

    right_elbow_ik_wrist_offset_grp = cmds.group(name=right_elbow_ik_ctrl.replace('_ctrl', '_wristOffsetDriver'),
                                                 empty=True, world=True)
    right_elbow_ik_wrist_offset_parent_grp = cmds.group(
        name=right_elbow_ik_ctrl.replace('_ctrl', '_wristOffset') + GRP_SUFFIX.capitalize(), empty=True, world=True)
    cmds.delete(cmds.parentConstraint(right_wrist_ik_ctrl, right_elbow_ik_wrist_offset_grp))
    cmds.delete(cmds.parentConstraint(right_wrist_ik_ctrl, right_elbow_ik_wrist_offset_parent_grp))
    cmds.parent(right_elbow_ik_wrist_offset_grp, right_elbow_ik_wrist_offset_parent_grp)
    cmds.parent(right_elbow_ik_wrist_offset_parent_grp, right_elbow_ik_twist_override_grp)
    cmds.parent(right_elbow_ik_ctrl_grp, right_elbow_ik_wrist_offset_grp)

    cmds.addAttr(right_wrist_ik_ctrl, ln='pVecFollowsWrist', at='float', k=True, maxValue=1, minValue=0,
                 niceName='Elbow Follows Wrist')

    right_wrist_trans_multiply_node = cmds.createNode('multiplyDivide',
                                                      name='right_wrist_translate_parentOffset_multiply')
    right_wrist_rot_multiply_node = cmds.createNode('multiplyDivide', name='right_wrist_rotate_parentOffset_multiply')
    cmds.connectAttr(right_elbow_ik_wrist_offset_data_grp + '.translate', right_wrist_trans_multiply_node + '.input1',
                     f=True)
    cmds.connectAttr(right_elbow_ik_wrist_offset_data_grp + '.rotate', right_wrist_rot_multiply_node + '.input1',
                     f=True)
    cmds.connectAttr(right_wrist_trans_multiply_node + '.output', right_elbow_ik_wrist_offset_grp + '.translate',
                     f=True)
    cmds.connectAttr(right_wrist_rot_multiply_node + '.output', right_elbow_ik_wrist_offset_grp + '.rotate', f=True)

    for multiply_node in [right_wrist_trans_multiply_node, right_wrist_rot_multiply_node]:
        cmds.connectAttr(right_wrist_ik_ctrl + '.pVecFollowsWrist', multiply_node + '.input2X', f=True)
        cmds.connectAttr(right_wrist_ik_ctrl + '.pVecFollowsWrist', multiply_node + '.input2Y', f=True)
        cmds.connectAttr(right_wrist_ik_ctrl + '.pVecFollowsWrist', multiply_node + '.input2Z', f=True)

    # Right Leg Stretchy System
    cmds.addAttr(right_arm_switch, ln="squashStretch", at='enum', en='-------------:', keyable=True)
    cmds.setAttr(right_arm_switch + '.squashStretch', lock=True)
    right_arm_stretchy_elements = make_stretchy_ik(right_arm_rp_ik_handle[0], 'right_arm', right_arm_switch)

    # Transfer Data to Base Skeleton
    right_shoulder_scale_blend = cmds.createNode('blendColors', name='right_shoulder_switchScale_blend')
    right_elbow_scale_blend = cmds.createNode('blendColors', name='right_elbow_switchScale_blend')

    cmds.connectAttr(right_shoulder_ik_jnt + '.scale', right_shoulder_scale_blend + '.color1', f=True)
    cmds.connectAttr(right_shoulder_fk_jnt + '.scale', right_shoulder_scale_blend + '.color2', f=True)
    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_shoulder_scale_blend + '.blender', f=True)
    cmds.connectAttr(right_shoulder_scale_blend + '.output', rig_joints.get('right_shoulder_jnt') + '.scale', f=True)

    cmds.connectAttr(right_elbow_ik_jnt + '.scale', right_elbow_scale_blend + '.color1', f=True)
    cmds.connectAttr(right_elbow_fk_jnt + '.scale', right_elbow_scale_blend + '.color2', f=True)
    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_elbow_scale_blend + '.blender', f=True)
    cmds.connectAttr(right_elbow_scale_blend + '.output', rig_joints.get('right_elbow_jnt') + '.scale', f=True)

    # Right Arm Separator
    cmds.addAttr(right_arm_switch, ln="armControls", at='enum', en='-------------:', keyable=True)
    cmds.setAttr(right_arm_switch + '.armControls', lock=True)

    # Right Fingers Limits (Connections)
    cmds.connectAttr(right_fingers_ctrl + '.maximumRotationZ', right_fingers_ctrl + '.maxRotZLimit', f=True)
    cmds.connectAttr(right_fingers_ctrl + '.minimumRotationZ', right_fingers_ctrl + '.minRotZLimit', f=True)

    right_rot_reverse_node = cmds.createNode('reverse', name='right_fingers_rotateShape_reverse')
    cmds.connectAttr(right_fingers_ctrl + '.rotateShape', right_rot_reverse_node + '.inputX')
    cmds.connectAttr(right_rot_reverse_node + '.outputX', right_fingers_inverse_rot_multiply_node + '.input2X')
    cmds.connectAttr(right_rot_reverse_node + '.outputX', right_fingers_inverse_rot_multiply_node + '.input2Y')
    cmds.connectAttr(right_rot_reverse_node + '.outputX', right_fingers_inverse_rot_multiply_node + '.input2Z')

    # Right Finger Curls Visibility (Connections)
    for curl_ctrl in right_curl_controls:
        for shape in cmds.listRelatives(curl_ctrl, s=True, f=True) or []:
            cmds.connectAttr(right_fingers_ctrl + '.showCurlControls', shape + '.v', f=True)

    # Right Finger Ctrl Visibility (Connections)
    for finger_parent in [right_thumb01_ctrl_list[1], right_index01_ctrl_list[1], right_middle01_ctrl_list[1],
                          right_ring01_ctrl_list[1], right_pinky01_ctrl_list[1]]:
        cmds.connectAttr(right_fingers_ctrl + '.showFkFingerCtrls', finger_parent + '.v', f=True)

    # Right Forearm Rotation & Scale
    right_forearm_grp = cmds.group(name=right_forearm_jnt + GRP_SUFFIX.capitalize(), empty=True, world=True)
    right_forearm_loc = cmds.spaceLocator(name=right_forearm_jnt.replace(JNT_SUFFIX, 'posLoc'))[0]
    cmds.setAttr(right_forearm_loc + '.v', 0)
    change_viewport_color(right_forearm_loc, RIGHT_CTRL_COLOR)
    cmds.parent(right_forearm_loc, right_forearm_grp)

    cmds.delete(cmds.parentConstraint(rig_joints.get('right_elbow_jnt'), right_forearm_grp))

    cmds.parent(right_forearm_grp, skeleton_grp)
    cmds.pointConstraint([rig_joints.get('right_elbow_jnt'), rig_joints.get('right_wrist_jnt')], right_forearm_grp)
    cmds.orientConstraint(rig_joints.get('right_elbow_jnt'), right_forearm_grp)
    cmds.setAttr(right_forearm_jnt + '.tx', 0)
    cmds.setAttr(right_forearm_jnt + '.ty', 0)
    cmds.setAttr(right_forearm_jnt + '.tz', 0)

    cmds.addAttr(right_arm_switch, ln='forearmRotation', at='double', k=True, maxValue=1, minValue=0)
    cmds.setAttr(right_arm_switch + '.forearmRotation', .5)

    cmds.addAttr(right_arm_switch, ln='forearmScale', at='double', k=True, minValue=0.01)
    cmds.setAttr(right_arm_switch + '.forearmScale', 1)
    cmds.connectAttr(right_arm_switch + '.forearmScale', right_forearm_jnt + '.sx', f=True)
    cmds.connectAttr(right_arm_switch + '.forearmScale', right_forearm_jnt + '.sy', f=True)
    cmds.connectAttr(right_arm_switch + '.forearmScale', right_forearm_jnt + '.sz', f=True)

    right_forearm_multiply_node = cmds.createNode('multiplyDivide', name="right_arm_forearmRotation_" + MULTIPLY_SUFFIX)
    right_forearm_blend_node = cmds.createNode('blendTwoAttr', name='right_arm_forearmRotation_blend')

    cmds.connectAttr('%s.rx' % right_wrist_ik_ctrl, '%s.input[0]' % right_forearm_blend_node)
    cmds.connectAttr('%s.rx' % right_wrist_ctrl, '%s.input[1]' % right_forearm_blend_node)

    cmds.connectAttr(right_arm_switch + '.forearmRotation', right_forearm_multiply_node + '.input2X', f=True)
    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_forearm_blend_node + '.attributesBlender', f=True)

    # cmds.connectAttr(rig_joints.get('right_wrist_jnt') + '.rotateX', right_forearm_multiply_node + '.input1X', f=True)

    # right_forearm_reverse_node = cmds.createNode('reverse', name='right_forearm_reverse')
    # cmds.connectAttr(right_forearm_multiply_node + '.outputX', right_forearm_reverse_node + '.inputX', f=True)
    # cmds.connectAttr(right_forearm_reverse_node + '.outputX', right_forearm_jnt + '.rx')
    cmds.connectAttr(right_forearm_multiply_node + '.outputX', right_forearm_jnt + '.rx', f=True)

    cmds.pointConstraint(right_forearm_loc, right_forearm_jnt)  # Receive Position from Mechanics

    # Clean Twist System (Aim) ############### ###############
    right_elbow_twist_sample_jnt = rig_joints.get('right_elbow_jnt')
    right_elbow_twist_sample_jnt = right_elbow_twist_sample_jnt.replace(JNT_SUFFIX, 'aim' + JNT_SUFFIX.capitalize())
    right_elbow_twist_sample_jnt = cmds.duplicate(rig_joints.get('right_elbow_jnt'),
                                                  name=right_elbow_twist_sample_jnt,
                                                  parentOnly=True)[0]
    change_viewport_color(right_elbow_twist_sample_jnt, (1, 0, 1))

    right_wrist_twist_sample_jnt = rig_joints.get('right_wrist_jnt')
    right_wrist_twist_sample_jnt = right_wrist_twist_sample_jnt.replace(JNT_SUFFIX, 'aim' + JNT_SUFFIX.capitalize())
    right_wrist_twist_sample_jnt = cmds.duplicate(right_elbow_twist_sample_jnt,
                                                  name=right_wrist_twist_sample_jnt,
                                                  parentOnly=True)[0]

    cmds.setAttr(right_wrist_twist_sample_jnt + '.rotateOrder', 1)
    cmds.parent(right_wrist_twist_sample_jnt, right_elbow_twist_sample_jnt)
    cmds.pointConstraint(rig_joints.get('right_wrist_jnt'), right_wrist_twist_sample_jnt)
    cmds.parent(right_elbow_twist_sample_jnt, skeleton_grp)
    cmds.parentConstraint(rig_joints.get('right_elbow_jnt'), right_elbow_twist_sample_jnt)
    right_wrist_aim_loc = cmds.spaceLocator(name=rig_joints.get('right_wrist_jnt').replace(JNT_SUFFIX, 'twistLoc'))[0]
    cmds.delete(cmds.parentConstraint(right_wrist_twist_sample_jnt, right_wrist_aim_loc))
    cmds.move(-general_scale_offset * .4, right_wrist_aim_loc, moveY=True, relative=True, objectSpace=True)
    change_viewport_color(right_wrist_aim_loc, (1, 0, 1))
    cmds.parentConstraint(rig_joints.get('right_wrist_jnt'), right_wrist_aim_loc, mo=True)
    cmds.aimConstraint(right_elbow_twist_sample_jnt, right_wrist_twist_sample_jnt,
                       aimVector=(1, 0, 0),
                       upVector=(0, -1, 0),
                       worldUpType="object",
                       worldUpObject=right_wrist_aim_loc)
    cmds.connectAttr(right_wrist_twist_sample_jnt + '.rotateX', right_forearm_multiply_node + '.input1X', f=True)
    cmds.parent(right_wrist_aim_loc, arms_automation_grp)
    cmds.setAttr(right_elbow_twist_sample_jnt + '.v', 0)
    new_radius = cmds.getAttr(right_elbow_twist_sample_jnt + '.radius') * 0.5
    cmds.setAttr(right_elbow_twist_sample_jnt + '.radius', new_radius)
    cmds.setAttr(right_wrist_twist_sample_jnt + '.radius', new_radius)

    # Right IK Switcher Parent System
    right_clavicle_wrist_constraint = cmds.parentConstraint(
        [controls_grp, right_clavicle_ctrl, rig_joints.get('spine04_jnt')], right_wrist_ik_ctrl_grp, mo=True)
    cmds.addAttr(right_arm_switch, ln='parent', at='enum', k=True, en="World:Clavicle:Chest:")
    cmds.setAttr(right_arm_switch + '.parent', 2)

    right_switch_world_condition_node = cmds.createNode('condition', name='right_arm_parentWorld_' + AUTO_SUFFIX)
    right_switch_clavicle_condition_node = cmds.createNode('condition', name='right_arm_parentClavicle_' + AUTO_SUFFIX)
    right_switch_chest_condition_node = cmds.createNode('condition', name='right_arm_parentChest_' + AUTO_SUFFIX)

    cmds.setAttr(right_switch_world_condition_node + '.secondTerm', 0)
    cmds.setAttr(right_switch_clavicle_condition_node + '.secondTerm', 1)
    cmds.setAttr(right_switch_chest_condition_node + '.secondTerm', 2)

    for node in [right_switch_world_condition_node, right_switch_clavicle_condition_node,
                 right_switch_chest_condition_node]:
        cmds.setAttr(node + '.colorIfTrueR', 1)
        cmds.setAttr(node + '.colorIfTrueG', 1)
        cmds.setAttr(node + '.colorIfTrueB', 1)
        cmds.setAttr(node + '.colorIfFalseR', 0)
        cmds.setAttr(node + '.colorIfFalseG', 0)
        cmds.setAttr(node + '.colorIfFalseB', 0)

    cmds.connectAttr(right_arm_switch + '.parent', right_switch_world_condition_node + '.firstTerm', f=True)
    cmds.connectAttr(right_arm_switch + '.parent', right_switch_clavicle_condition_node + '.firstTerm', f=True)
    cmds.connectAttr(right_arm_switch + '.parent', right_switch_chest_condition_node + '.firstTerm', f=True)

    cmds.connectAttr(right_switch_world_condition_node + '.outColorR', right_clavicle_wrist_constraint[0] + '.w0',
                     f=True)
    cmds.connectAttr(right_switch_clavicle_condition_node + '.outColorR', right_clavicle_wrist_constraint[0] + '.w1',
                     f=True)
    cmds.connectAttr(right_switch_chest_condition_node + '.outColorR', right_clavicle_wrist_constraint[0] + '.w2',
                     f=True)

    # ################# Lock Parameters for FK Controls #################

    lock_attr = 'lockXY'
    primary_rotation_channel = 'Z'
    alternative_prim_rot_list = []

    if settings.get('uniform_ctrl_orient'):
        lock_attr = 'lockYZ'
        primary_rotation_channel = 'X'

    for obj in [left_elbow_ctrl, right_elbow_ctrl, left_knee_ctrl, right_knee_ctrl]:
        cmds.addAttr(obj, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
        cmds.setAttr(obj + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)
        cmds.addAttr(obj, ln='rotationOrder', at='enum', en=ROTATE_ORDER_ENUM, keyable=True, niceName='Rotate Order')
        cmds.connectAttr(obj + '.rotationOrder', obj + '.rotateOrder', f=True)

        if obj not in alternative_prim_rot_list:
            create_limit_lock_attributes(obj, lock_attr, primary_rotation_channel)
        else:
            create_limit_lock_attributes(obj, lock_attr='lockYZ', primary_rotation_channel='X')

    for obj in [left_hip_ctrl, left_ankle_ctrl, left_ball_ctrl, left_clavicle_ctrl, left_shoulder_ctrl, left_wrist_ctrl,
                right_hip_ctrl, right_ankle_ctrl, right_ball_ctrl, right_clavicle_ctrl, right_shoulder_ctrl,
                right_wrist_ctrl, spine01_ctrl, spine02_ctrl, spine03_ctrl, spine04_ctrl, neck_base_ctrl,
                neck_mid_ctrl, hip_ctrl, jaw_ctrl, head_ctrl, chest_global_fk_ctrl]:

        if not obj.startswith('spine02') and not obj.startswith('spine04') and not obj.startswith('neckBase'):
            if not cmds.attributeQuery(CUSTOM_ATTR_SEPARATOR, node=obj, exists=True):
                cmds.addAttr(obj, ln=CUSTOM_ATTR_SEPARATOR, at='enum', en='-------------:', keyable=True)
                cmds.setAttr(obj + '.' + CUSTOM_ATTR_SEPARATOR, lock=True)
            # Expose Custom Rotate Order
            if not cmds.attributeQuery(CUSTOM_ATTR_SEPARATOR, node=obj, exists=True):
                cmds.addAttr(obj, ln='rotationOrder', at='enum', en=ROTATE_ORDER_ENUM, keyable=True,
                             niceName='Rotate Order')
                cmds.connectAttr(obj + '.rotationOrder', obj + '.rotateOrder', f=True)

        create_limit_lock_attributes(obj, ignore_rot=True)

    # Eyes
    cmds.parent(main_eye_ctrl_grp, direction_ctrl)
    main_eye_constraint = cmds.parentConstraint([head_offset_ctrl, direction_ctrl], main_eye_ctrl_grp, mo=True)
    cmds.addAttr(main_eye_ctrl, ln='followHead', at='double', k=True, minValue=0, maxValue=1)
    cmds.addAttr(main_eye_ctrl, ln='inheritHeadRoll', at='double', k=True, minValue=0, maxValue=1)
    cmds.addAttr(main_eye_ctrl, ln='converge', at='double', k=True)
    cmds.setAttr(main_eye_ctrl + '.followHead', 1)

    eye_follow_head_reverse_node = cmds.createNode('reverse', name='eyes_followHead_reverse')
    cmds.connectAttr(main_eye_ctrl + '.followHead', main_eye_constraint[0] + '.w0', f=True)
    cmds.connectAttr(main_eye_ctrl + '.followHead', eye_follow_head_reverse_node + '.inputX', f=True)
    cmds.connectAttr(eye_follow_head_reverse_node + '.outputX', main_eye_constraint[0] + '.w1', f=True)

    # Left Eye
    left_eye_up_vec = cmds.spaceLocator(name='left_eye_upVec')[0]
    cmds.delete(cmds.parentConstraint(rig_joints.get('left_eye_jnt'), left_eye_up_vec))
    cmds.move(general_scale_offset, left_eye_up_vec, y=True, relative=True, objectSpace=True)
    cmds.setAttr(left_eye_up_vec + '.lsx', general_scale_offset * .1)
    cmds.setAttr(left_eye_up_vec + '.lsy', general_scale_offset * .1)
    cmds.setAttr(left_eye_up_vec + '.lsz', general_scale_offset * .1)
    cmds.setAttr(left_eye_up_vec + '.v', 0)
    cmds.parent(left_eye_up_vec, head_offset_ctrl)
    change_viewport_color(left_eye_up_vec, (0, .3, 1))

    cmds.aimConstraint(left_eye_ctrl, rig_joints.get('left_eye_jnt'), mo=True, upVector=(0, 1, 0), worldUpType="object",
                       worldUpObject=left_eye_up_vec)

    # Right Eye
    right_eye_up_vec = cmds.spaceLocator(name='right_eye_upVec')[0]
    cmds.delete(cmds.parentConstraint(rig_joints.get('right_eye_jnt'), right_eye_up_vec))
    cmds.move(general_scale_offset, right_eye_up_vec, y=True, relative=True, objectSpace=True)
    cmds.setAttr(right_eye_up_vec + '.lsx', general_scale_offset * .1)
    cmds.setAttr(right_eye_up_vec + '.lsy', general_scale_offset * .1)
    cmds.setAttr(right_eye_up_vec + '.lsz', general_scale_offset * .1)
    cmds.setAttr(right_eye_up_vec + '.v', 0)
    cmds.parent(right_eye_up_vec, head_offset_ctrl)
    change_viewport_color(right_eye_up_vec, (1, 0, 0))

    cmds.aimConstraint(right_eye_ctrl, rig_joints.get('right_eye_jnt'), mo=True, upVector=(0, 1, 0),
                       worldUpType="object", worldUpObject=right_eye_up_vec)

    # Extra Eye Automation - Inherit Head Roll and Converge
    # Inherit Head Roll
    head_up_vec_loc = cmds.duplicate(left_eye_up_vec, name="head_upVec")[0]
    change_viewport_color(head_up_vec_loc, (0, 1, 0))
    cmds.delete(cmds.pointConstraint([left_eye_up_vec, right_eye_up_vec], head_up_vec_loc))
    main_eye_data_offset_loc = cmds.spaceLocator(name=main_eye_ctrl_offset_grp + 'Loc')[0]
    cmds.delete(cmds.parentConstraint(main_eye_ctrl_offset_grp, main_eye_data_offset_loc))
    cmds.parent(main_eye_data_offset_loc, main_eye_ctrl)
    cmds.setAttr(main_eye_data_offset_loc + '.v', 0)
    for dimension in ['X', 'Y', 'Z']:
        cmds.setAttr(main_eye_data_offset_loc + '.localScale' + dimension, general_scale_offset * .5)

    cmds.aimConstraint(head_offset_ctrl, main_eye_data_offset_loc, aimVector=(0, 0, -1), upVector=(0, 1, 0),
                       worldUpType='object', worldUpObject=head_up_vec_loc, mo=True)

    head_roll_multiply = cmds.createNode('multiplyDivide', name=head_ctrl + "_" + MULTIPLY_SUFFIX)
    cmds.connectAttr(main_eye_ctrl + '.inheritHeadRoll', head_roll_multiply + '.input2X')
    cmds.connectAttr(main_eye_ctrl + '.inheritHeadRoll', head_roll_multiply + '.input2Y')
    cmds.connectAttr(main_eye_ctrl + '.inheritHeadRoll', head_roll_multiply + '.input2Z')
    cmds.connectAttr(head_roll_multiply + '.output', main_eye_ctrl_offset_grp + '.rotate')
    cmds.connectAttr(main_eye_data_offset_loc + '.rotate', head_roll_multiply + '.input1')
    # Converge
    eye_converge_reverse_multiply = cmds.createNode('multiplyDivide', name='temp' + "_" + MULTIPLY_SUFFIX)
    cmds.connectAttr(main_eye_ctrl + '.converge', right_eye_ctrl_offset_grp + '.tx')
    cmds.connectAttr(main_eye_ctrl + '.converge', eye_converge_reverse_multiply + '.input1X')
    cmds.setAttr(eye_converge_reverse_multiply + '.input2X', -1)
    cmds.connectAttr(eye_converge_reverse_multiply + '.outputX', left_eye_ctrl_offset_grp + '.tx')

    # ################ Organize Stretchy System Elements #################
    stretchy_system_grp = cmds.group(name='stretchyAutomation_' + GRP_SUFFIX, empty=True, world=True)
    foot_automation_grp = cmds.group(name='footAutomation_' + GRP_SUFFIX, empty=True, world=True)
    change_outliner_color(stretchy_system_grp, (1, .65, .45))
    change_outliner_color(foot_automation_grp, (1, .65, .45))
    cmds.parent(left_leg_stretchy_elements[1], stretchy_system_grp)
    cmds.parent(right_leg_stretchy_elements[1], stretchy_system_grp)
    cmds.parent(left_foot_pivot_grp, foot_automation_grp)
    cmds.parent(right_foot_pivot_grp, foot_automation_grp)
    cmds.parent(right_arm_stretchy_elements[1], stretchy_system_grp)
    cmds.parent(left_arm_stretchy_elements[1], stretchy_system_grp)
    stretchy_system_grp_children = cmds.listRelatives(stretchy_system_grp, children=True)  # TODO Send to make stretchy
    for obj in stretchy_system_grp_children:
        grp_children = cmds.listRelatives(obj, children=True)
        for child in grp_children:
            child_shape = cmds.listRelatives(child, shapes=True) or []
            for shape in child_shape:
                if cmds.objectType(shape) == 'distanceDimShape':
                    cmds.setAttr(child + '.overrideEnabled', 1)
                    cmds.setAttr(child + '.overrideDisplayType', 1)

    # Finger Automation System Hierarchy
    finger_automation_grp = cmds.group(name='fingersAutomation_' + GRP_SUFFIX, empty=True, world=True)
    cmds.parent(left_fingers_abduction_ctrl[2], finger_automation_grp)
    cmds.parent(right_fingers_abduction_ctrl[2], finger_automation_grp)
    change_outliner_color(finger_automation_grp, (1, .65, .45))
    cmds.setAttr(finger_automation_grp + '.inheritsTransform', 0)

    # Spine Automation System Hierarchy
    change_outliner_color(spine_automation_grp, (1, .65, .45))

    # Arms Automation System Hierarchy
    cmds.parent(left_forearm_grp, arms_automation_grp)
    cmds.parent(right_forearm_grp, arms_automation_grp)

    # ###### Main Hierarchy for Top Parent Groups ######
    if cmds.objExists('geometry_grp'):
        geometry_grp = 'geometry_grp'
    else:
        geometry_grp = cmds.group(name='geometry_grp', empty=True, world=True)
    change_outliner_color(geometry_grp, (.3, 1, .8))
    rig_grp = cmds.group(name='rig_grp', empty=True, world=True)
    change_outliner_color(rig_grp, (1, .45, .7))
    cmds.parent(general_automation_grp, rig_setup_grp)
    cmds.parent(stretchy_system_grp, rig_setup_grp)
    cmds.parent(arms_automation_grp, rig_setup_grp)
    cmds.parent(finger_automation_grp, rig_setup_grp)
    cmds.parent(spine_automation_grp, rig_setup_grp)
    cmds.parent(foot_automation_grp, rig_setup_grp)

    # Scale Constraints
    main_skeleton_constraint = cmds.scaleConstraint(main_ctrl, skeleton_grp)
    cmds.setAttr(main_skeleton_constraint[0] + '.v', 0)
    cmds.scaleConstraint(main_ctrl, rig_setup_grp)

    # Hierarchy Adjustments and Color
    cmds.setAttr(rig_setup_grp + '.v', 0)
    cmds.setAttr(left_clavicle_switch_jnt + '.v', 0)
    cmds.setAttr(right_clavicle_switch_jnt + '.v', 0)
    cmds.setAttr(hip_switch_jnt + '.v', 0)

    cmds.parent(geometry_grp, rig_grp)
    cmds.parent(skeleton_grp, rig_grp)
    cmds.parent(controls_grp, rig_grp)
    cmds.parent(rig_setup_grp, rig_grp)

    cmds.setAttr(main_ctrl + '.sx', k=False)
    cmds.setAttr(main_ctrl + '.sz', k=False)
    cmds.addAttr(main_ctrl, ln="rigOptions", at='enum', en='-------------:', keyable=True)
    cmds.setAttr(main_ctrl + '.rigOptions', lock=True)
    cmds.addAttr(main_ctrl, ln="geometryDisplayMode", at='enum', en="Normal:Template:Reference:", keyable=True)
    cmds.addAttr(main_ctrl, ln="controlsVisibility", at="bool", keyable=True)
    cmds.setAttr(main_ctrl + '.controlsVisibility', 1)

    cmds.addAttr(main_ctrl, ln='jointCtrlsScaleInfluence', at='double', k=True, minValue=0, maxValue=1)
    cmds.setAttr(main_ctrl + ".jointCtrlsScaleInfluence", 1)

    cmds.setAttr(geometry_grp + '.overrideEnabled', 1)
    cmds.connectAttr(main_ctrl + '.geometryDisplayMode', geometry_grp + '.overrideDisplayType', f=True)
    cmds.connectAttr(main_ctrl + '.controlsVisibility', direction_ctrl_grp + '.v', f=True)
    cmds.connectAttr(main_ctrl + '.controlsVisibility', left_arm_switch_grp + '.v', f=True)
    cmds.connectAttr(main_ctrl + '.controlsVisibility', right_arm_switch_grp + '.v', f=True)
    cmds.connectAttr(main_ctrl + '.controlsVisibility', left_leg_switch_grp + '.v', f=True)
    cmds.connectAttr(main_ctrl + '.controlsVisibility', right_leg_switch_grp + '.v', f=True)

    # Moved the parenting of these systems after IK creation to solve pose issues
    cmds.parent(right_shoulder_ik_jnt, right_clavicle_switch_jnt)
    cmds.parent(left_shoulder_ik_jnt, left_clavicle_switch_jnt)

    # ################# Joint Inflation System #################

    # Elements to Inflate/Deflate - Ctrl, CtrlGrp, Joint, CreateOffset?
    create_offset = True
    inflation_system_groups = [
        [cog_ctrl, cog_ctrl_grp, rig_joints.get('cog_jnt')],
        [hip_ctrl, hip_ctrl_grp, rig_joints.get('hip_jnt')],
        [spine01_ctrl, spine01_ctrl_grp, rig_joints.get('spine01_jnt'), create_offset],
        [spine02_ctrl, spine02_ctrl_grp, rig_joints.get('spine02_jnt'), create_offset],
        [spine03_ctrl, spine03_ctrl_grp, rig_joints.get('spine03_jnt'), create_offset],
        [spine04_ctrl, spine04_ctrl_grp, rig_joints.get('spine04_jnt'), create_offset],

        [neck_base_ctrl, neck_base_ctrl_grp, rig_joints.get('neck_base_jnt')],
        [neck_mid_ctrl, neck_mid_ctrl_grp, rig_joints.get('neck_mid_jnt')],
        # [head_ctrl, head_ctrl_grp, rig_joints.get('head_jnt')],# Issues with eyes
        # [jaw_ctrl, jaw_ctrl_grp, rig_joints.get('jaw_jnt')], Really necessary?
        # Left Arm
        [left_clavicle_ctrl, left_clavicle_ctrl_grp, rig_joints.get('left_clavicle_jnt')],
        [left_shoulder_ctrl, left_shoulder_ctrl_grp, left_shoulder_fk_jnt],
        [left_elbow_ctrl, left_elbow_ctrl_grp, left_elbow_fk_jnt],
        [left_wrist_ctrl, left_wrist_ctrl_grp, left_wrist_fk_jnt],
        [left_wrist_ik_ctrl, left_wrist_ik_ctrl_grp, left_wrist_ik_jnt],

        # Left Leg
        [left_hip_ctrl, left_hip_ctrl_grp, left_hip_fk_jnt],
        [left_knee_ctrl, left_knee_ctrl_grp, left_knee_fk_jnt],
        [left_ankle_ctrl, left_ankle_ctrl_grp, left_ankle_fk_jnt],
        [left_foot_ik_ctrl, left_foot_ik_ctrl_grp, left_ankle_ik_jnt],
        [left_ball_ctrl, left_ball_ctrl_grp, rig_joints.get('left_ball_jnt')],

        # Left Fingers
        [left_thumb01_ctrl_list[0], left_thumb01_ctrl_list[1], rig_joints.get('left_thumb01_jnt')],
        [left_thumb02_ctrl_list[0], left_thumb02_ctrl_list[1], rig_joints.get('left_thumb02_jnt')],
        [left_thumb03_ctrl_list[0], left_thumb03_ctrl_list[1], rig_joints.get('left_thumb03_jnt')],

        [left_index01_ctrl_list[0], left_index01_ctrl_list[1], rig_joints.get('left_index01_jnt')],
        [left_index02_ctrl_list[0], left_index02_ctrl_list[1], rig_joints.get('left_index02_jnt')],
        [left_index03_ctrl_list[0], left_index03_ctrl_list[1], rig_joints.get('left_index03_jnt')],

        [left_middle01_ctrl_list[0], left_middle01_ctrl_list[1], rig_joints.get('left_middle01_jnt')],
        [left_middle02_ctrl_list[0], left_middle02_ctrl_list[1], rig_joints.get('left_middle02_jnt')],
        [left_middle03_ctrl_list[0], left_middle03_ctrl_list[1], rig_joints.get('left_middle03_jnt')],

        [left_ring01_ctrl_list[0], left_ring01_ctrl_list[1], rig_joints.get('left_ring01_jnt')],
        [left_ring02_ctrl_list[0], left_ring02_ctrl_list[1], rig_joints.get('left_ring02_jnt')],
        [left_ring03_ctrl_list[0], left_ring03_ctrl_list[1], rig_joints.get('left_ring03_jnt')],

        [left_pinky01_ctrl_list[0], left_pinky01_ctrl_list[1], rig_joints.get('left_pinky01_jnt')],
        [left_pinky02_ctrl_list[0], left_pinky02_ctrl_list[1], rig_joints.get('left_pinky02_jnt')],
        [left_pinky03_ctrl_list[0], left_pinky03_ctrl_list[1], rig_joints.get('left_pinky03_jnt')],

        # Right Arm
        [right_clavicle_ctrl, right_clavicle_ctrl_grp, rig_joints.get('right_clavicle_jnt')],
        [right_shoulder_ctrl, right_shoulder_ctrl_grp, right_shoulder_fk_jnt],
        [right_elbow_ctrl, right_elbow_ctrl_grp, right_elbow_fk_jnt],
        [right_wrist_ctrl, right_wrist_ctrl_grp, right_wrist_fk_jnt],
        [right_wrist_ik_ctrl, right_wrist_ik_ctrl_grp, right_wrist_ik_jnt],

        # Right Leg
        [right_hip_ctrl, right_hip_ctrl_grp, right_hip_fk_jnt],
        [right_knee_ctrl, right_knee_ctrl_grp, right_knee_fk_jnt],
        [right_ankle_ctrl, right_ankle_ctrl_grp, right_ankle_fk_jnt],
        [right_foot_ik_ctrl, right_foot_ik_ctrl_grp, right_ankle_ik_jnt],
        [right_ball_ctrl, right_ball_ctrl_grp, rig_joints.get('right_ball_jnt')],

        # Right Fingers
        [right_thumb01_ctrl_list[0], right_thumb01_ctrl_list[1], rig_joints.get('right_thumb01_jnt')],
        [right_thumb02_ctrl_list[0], right_thumb02_ctrl_list[1], rig_joints.get('right_thumb02_jnt')],
        [right_thumb03_ctrl_list[0], right_thumb03_ctrl_list[1], rig_joints.get('right_thumb03_jnt')],

        [right_index01_ctrl_list[0], right_index01_ctrl_list[1], rig_joints.get('right_index01_jnt')],
        [right_index02_ctrl_list[0], right_index02_ctrl_list[1], rig_joints.get('right_index02_jnt')],
        [right_index03_ctrl_list[0], right_index03_ctrl_list[1], rig_joints.get('right_index03_jnt')],

        [right_middle01_ctrl_list[0], right_middle01_ctrl_list[1], rig_joints.get('right_middle01_jnt')],
        [right_middle02_ctrl_list[0], right_middle02_ctrl_list[1], rig_joints.get('right_middle02_jnt')],
        [right_middle03_ctrl_list[0], right_middle03_ctrl_list[1], rig_joints.get('right_middle03_jnt')],

        [right_ring01_ctrl_list[0], right_ring01_ctrl_list[1], rig_joints.get('right_ring01_jnt')],
        [right_ring02_ctrl_list[0], right_ring02_ctrl_list[1], rig_joints.get('right_ring02_jnt')],
        [right_ring03_ctrl_list[0], right_ring03_ctrl_list[1], rig_joints.get('right_ring03_jnt')],

        [right_pinky01_ctrl_list[0], right_pinky01_ctrl_list[1], rig_joints.get('right_pinky01_jnt')],
        [right_pinky02_ctrl_list[0], right_pinky02_ctrl_list[1], rig_joints.get('right_pinky02_jnt')],
        [right_pinky03_ctrl_list[0], right_pinky03_ctrl_list[1], rig_joints.get('right_pinky03_jnt')],
    ]

    # Joint Inflation Basic Setup
    jnt_scale_ctrl_scale = general_scale_offset * 0.05
    for ctrl_grps in inflation_system_groups:  # Ctrl, CtrlGrp, Joint, CreateOffset?
        # Unpack Values
        ctrl = ctrl_grps[0]
        joint = ctrl_grps[2]

        blend_node = cmds.createNode('blendColors', name=ctrl.replace(CTRL_SUFFIX, '') + 'inflation_blend')

        cmds.setAttr(blend_node + '.color2R', 1)
        cmds.setAttr(blend_node + '.color2G', 1)
        cmds.setAttr(blend_node + '.color2B', 1)

        cmds.connectAttr(main_ctrl + '.jointCtrlsScaleInfluence', blend_node + '.blender')  # Main Control's Slave

        jnt_scale_ctrl = create_loc_joint_curve(ctrl.replace(CTRL_SUFFIX, 'scaleCtrl'), jnt_scale_ctrl_scale)
        cmds.delete(cmds.parentConstraint(ctrl, jnt_scale_ctrl))
        cmds.parent(jnt_scale_ctrl, ctrl)
        cmds.connectAttr(jnt_scale_ctrl + '.scale', blend_node + '.color1')
        cmds.connectAttr(blend_node + '.output', joint + '.scale')
        lock_hide_default_attr(jnt_scale_ctrl, scale=False, visibility=False)
        cmds.setAttr(jnt_scale_ctrl + '.v', keyable=False)

        if not cmds.attributeQuery('showScaleCtrl', node=ctrl_grps[0], exists=True):
            cmds.addAttr(ctrl, ln='showScaleCtrl', at='bool', keyable=True)
        cmds.connectAttr(ctrl + '.showScaleCtrl', jnt_scale_ctrl + '.visibility')
        cmds.setAttr(ctrl + '.showScaleCtrl', 0)

        cmds.setAttr(jnt_scale_ctrl + '.minScaleXLimit', 0.01)
        cmds.setAttr(jnt_scale_ctrl + '.minScaleYLimit', 0.01)
        cmds.setAttr(jnt_scale_ctrl + '.minScaleZLimit', 0.01)
        cmds.setAttr(jnt_scale_ctrl + '.minScaleXLimitEnable', 1)
        cmds.setAttr(jnt_scale_ctrl + '.minScaleYLimitEnable', 1)
        cmds.setAttr(jnt_scale_ctrl + '.minScaleZLimitEnable', 1)

        if len(ctrl_grps) > 3:  # Create Offset Input
            if ctrl_grps[3]:
                offset_node = cmds.createNode('plusMinusAverage',
                                              name=ctrl.replace(CTRL_SUFFIX, '') + 'offset_sum')

                cmds.addAttr(ctrl, ln='scaleOffset', at='double3', k=False)
                cmds.addAttr(ctrl, ln='scaleOffsetX', at='double', k=False, minValue=0, parent='scaleOffset')
                cmds.addAttr(ctrl, ln='scaleOffsetY', at='double', k=False, minValue=0, parent='scaleOffset')
                cmds.addAttr(ctrl, ln='scaleOffsetZ', at='double', k=False, minValue=0, parent='scaleOffset')

                cmds.connectAttr(blend_node + '.output', offset_node + '.input3D[0]', force=True)
                cmds.connectAttr(ctrl + '.scaleOffset', offset_node + '.input3D[1]', force=True)
                cmds.connectAttr(offset_node + '.output3D', joint + '.scale', force=True)

    # Joint Inflation/Deflation Mechanics & Special Cases
    left_wrist_scale_blend = cmds.createNode('blendColors', name='left_wrist_switchScale_blend')
    cmds.connectAttr(left_wrist_ik_ctrl.replace(CTRL_SUFFIX, 'scaleCtrl') + '.scale',
                     left_wrist_scale_blend + '.color1')
    cmds.connectAttr(left_wrist_ctrl.replace(CTRL_SUFFIX, 'scaleCtrl') + '.scale', left_wrist_scale_blend + '.color2')
    cmds.connectAttr(left_wrist_scale_blend + '.output', rig_joints.get('left_wrist_jnt') + '.scale')
    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_wrist_scale_blend + '.blender')

    cmds.setAttr(right_wrist_ik_ctrl.replace(CTRL_SUFFIX, 'scaleCtrl') + '.sz', 1)  # Account for inverted scale
    right_wrist_scale_blend = cmds.createNode('blendColors', name='right_wrist_switchScale_blend')
    cmds.connectAttr(right_wrist_ik_ctrl.replace(CTRL_SUFFIX, 'scaleCtrl') + '.scale',
                     right_wrist_scale_blend + '.color1')
    cmds.connectAttr(right_wrist_ctrl.replace(CTRL_SUFFIX, 'scaleCtrl') + '.scale', right_wrist_scale_blend + '.color2')
    cmds.connectAttr(right_wrist_scale_blend + '.output', rig_joints.get('right_wrist_jnt') + '.scale')
    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_wrist_scale_blend + '.blender')

    left_ankle_scale_blend = cmds.createNode('blendColors', name='left_ankle_switchScale_blend')
    cmds.connectAttr(left_foot_ik_ctrl.replace(CTRL_SUFFIX, 'scaleCtrl') + '.scale', left_ankle_scale_blend + '.color1')
    cmds.connectAttr(left_ankle_ctrl.replace(CTRL_SUFFIX, 'scaleCtrl') + '.scale', left_ankle_scale_blend + '.color2')
    cmds.connectAttr(left_ankle_scale_blend + '.output', rig_joints.get('left_ankle_jnt') + '.scale')
    cmds.connectAttr(left_leg_switch + '.influenceSwitch', left_ankle_scale_blend + '.blender')

    right_ankle_scale_blend = cmds.createNode('blendColors', name='right_ankle_switchScale_blend')
    cmds.connectAttr(right_foot_ik_ctrl.replace(CTRL_SUFFIX, 'scaleCtrl') + '.scale',
                     right_ankle_scale_blend + '.color1')
    cmds.connectAttr(right_ankle_ctrl.replace(CTRL_SUFFIX, 'scaleCtrl') + '.scale', right_ankle_scale_blend + '.color2')
    cmds.connectAttr(right_ankle_scale_blend + '.output', rig_joints.get('right_ankle_jnt') + '.scale')
    cmds.connectAttr(right_leg_switch + '.influenceSwitch', right_ankle_scale_blend + '.blender')

    left_ball_connection_list = cmds.listConnections(rig_joints.get('left_ball_jnt') + '.scale', source=True) or []
    left_ball_inflation_node = ''
    for obj in left_ball_connection_list:
        if 'inflation_blend' in obj:
            left_ball_inflation_node = obj

    left_ball_scale_blend = cmds.createNode('blendColors', name='left_ball_switchScale_blend')
    cmds.setAttr(left_ball_scale_blend + '.color1R', 1)
    cmds.setAttr(left_ball_scale_blend + '.color1G', 1)
    cmds.setAttr(left_ball_scale_blend + '.color1B', 1)
    cmds.connectAttr(left_ball_inflation_node + '.output', left_ball_scale_blend + '.color2', f=True)
    cmds.connectAttr(left_ball_scale_blend + '.output', rig_joints.get('left_ball_jnt') + '.scale', f=True)
    cmds.connectAttr(left_leg_switch + '.influenceSwitch', left_ball_scale_blend + '.blender')

    right_ball_connection_list = cmds.listConnections(rig_joints.get('right_ball_jnt') + '.scale', source=True) or []
    right_ball_inflation_node = ''
    for obj in right_ball_connection_list:
        if 'inflation_blend' in obj:
            right_ball_inflation_node = obj

    right_ball_scale_blend = cmds.createNode('blendColors', name='right_ball_switchScale_blend')
    cmds.setAttr(right_ball_scale_blend + '.color1R', 1)
    cmds.setAttr(right_ball_scale_blend + '.color1G', 1)
    cmds.setAttr(right_ball_scale_blend + '.color1B', 1)
    cmds.connectAttr(right_ball_inflation_node + '.output', right_ball_scale_blend + '.color2', f=True)
    cmds.connectAttr(right_ball_scale_blend + '.output', rig_joints.get('right_ball_jnt') + '.scale', f=True)
    cmds.connectAttr(right_leg_switch + '.influenceSwitch', right_ball_scale_blend + '.blender')

    # Auto Breathing System
    cmds.addAttr(main_ctrl, ln='autoBreathingSystem', at='enum', en='-------------:', keyable=True)
    cmds.setAttr(main_ctrl + '.autoBreathingSystem', e=True, lock=True)
    cmds.addAttr(main_ctrl, ln='breathingInfluence', at="double", keyable=True)
    sine_output = add_sine_attributes(main_ctrl, sine_prefix='breathing', hide_unkeyable=True,
                                      add_absolute_output=False, nice_name_prefix=True)

    breathing_sine_min = -1
    breathing_sine_max = 1
    breathing_new_min = 0
    limit_scale_prefix = 'maxScale'

    for ctrl in [spine01_ctrl, spine02_ctrl, spine03_ctrl, spine04_ctrl]:
        ctrl_name = ctrl.replace(CTRL_SUFFIX, '').replace('_', '')
        breathing_range_node = cmds.createNode('setRange', name=ctrl_name + '_breathing_range')
        cmds.addAttr(main_ctrl, ln=limit_scale_prefix + ctrl_name.capitalize(), at='double', keyable=True)

        for attr in ['x', 'y', 'z']:
            cmds.setAttr(breathing_range_node + '.oldMin' + attr.capitalize(), breathing_sine_min)
            cmds.setAttr(breathing_range_node + '.oldMax' + attr.capitalize(), breathing_sine_max)
            cmds.setAttr(breathing_range_node + '.min' + attr.capitalize(), breathing_new_min)
            cmds.connectAttr(main_ctrl + '.' + limit_scale_prefix + ctrl_name.capitalize(),
                             breathing_range_node + '.max' + attr.capitalize())

        cmds.connectAttr(sine_output[0], breathing_range_node + '.valueX')
        cmds.connectAttr(sine_output[0], breathing_range_node + '.valueY')
        cmds.connectAttr(sine_output[0], breathing_range_node + '.valueZ')

        influence_multiply_node = cmds.createNode('multiplyDivide',
                                                  name=ctrl_name + "_breathingInfluence_" + MULTIPLY_SUFFIX)

        cmds.connectAttr(breathing_range_node + '.outValueX', influence_multiply_node + '.input1X')
        cmds.connectAttr(breathing_range_node + '.outValueY', influence_multiply_node + '.input1Y')
        cmds.connectAttr(breathing_range_node + '.outValueZ', influence_multiply_node + '.input1Z')

        cmds.connectAttr(main_ctrl + '.breathingInfluence', influence_multiply_node + '.input2X')
        cmds.connectAttr(main_ctrl + '.breathingInfluence', influence_multiply_node + '.input2Y')
        cmds.connectAttr(main_ctrl + '.breathingInfluence', influence_multiply_node + '.input2Z')

        cmds.connectAttr(influence_multiply_node + '.outputX', ctrl + '.scaleOffsetX')
        cmds.connectAttr(influence_multiply_node + '.outputY', ctrl + '.scaleOffsetY')
        cmds.connectAttr(influence_multiply_node + '.outputZ', ctrl + '.scaleOffsetZ')

    # Clean time1 input from main_ctrl
    cmds.addAttr(main_ctrl_grp, ln='inputTime', at='double', keyable=True)
    cmds.connectAttr('time1.outTime', main_ctrl_grp + '.inputTime', force=True)
    breathing_multiply = cmds.listConnections(main_ctrl + '.breathingTime') or []
    cmds.connectAttr(main_ctrl_grp + '.inputTime', breathing_multiply[0] + '.input1X', force=True)

    # Other Breathing Adjustments
    cmds.setAttr(main_ctrl + '.' + limit_scale_prefix + 'Spine01', .05)
    cmds.setAttr(main_ctrl + '.' + limit_scale_prefix + 'Spine02', .1)
    cmds.setAttr(main_ctrl + '.' + limit_scale_prefix + 'Spine03', .15)
    cmds.setAttr(main_ctrl + '.' + limit_scale_prefix + 'Chest', .2)
    cmds.setAttr(main_ctrl + '.breathingTime', 1)
    cmds.setAttr(main_ctrl + '.breathingFrequency', 6)

    # Create Alternative Setup for Clavicles
    left_clavicle_pos_loc = cmds.spaceLocator(name=left_clavicle_ctrl.replace(CTRL_SUFFIX, 'posLoc'))[0]
    right_clavicle_pos_loc = cmds.spaceLocator(name=right_clavicle_ctrl.replace(CTRL_SUFFIX, 'posLoc'))[0]

    left_clavicle_pos_loc_grp = cmds.group(name=left_clavicle_pos_loc + 'Grp', world=True, empty=True)
    right_clavicle_pos_loc_grp = cmds.group(name=right_clavicle_pos_loc + 'Grp', world=True, empty=True)

    cmds.parent(left_clavicle_pos_loc, left_clavicle_pos_loc_grp)
    cmds.parent(right_clavicle_pos_loc, right_clavicle_pos_loc_grp)

    cmds.pointConstraint(left_clavicle_ctrl, left_clavicle_pos_loc_grp)
    cmds.pointConstraint(right_clavicle_ctrl, right_clavicle_pos_loc_grp)

    cmds.pointConstraint(left_clavicle_pos_loc, rig_joints.get('left_clavicle_jnt'))
    cmds.pointConstraint(right_clavicle_pos_loc, rig_joints.get('right_clavicle_jnt'))

    # Left Auto Clavicle
    left_clavicle_auto_jnt = cmds.duplicate(rig_joints.get('left_clavicle_jnt'),
                                            name=rig_joints.get('left_clavicle_jnt').replace(JNT_SUFFIX, 'driver' +
                                                                                             JNT_SUFFIX.capitalize()),
                                            parentOnly=True)[0]
    left_shoulder_auto_jnt = cmds.duplicate(rig_joints.get('left_shoulder_jnt'),
                                            name=rig_joints.get('left_shoulder_jnt').replace(JNT_SUFFIX, 'driverEnd' +
                                                                                             JNT_SUFFIX.capitalize()),
                                            parentOnly=True)[0]
    cmds.parent(left_clavicle_auto_jnt, world=True)
    cmds.parent(left_shoulder_auto_jnt, left_clavicle_auto_jnt)

    left_auto_clavicle_sc_ik_handle = cmds.ikHandle(n='left_auto_clavicle_SC_ikHandle', sj=left_clavicle_auto_jnt,
                                                    ee=left_shoulder_auto_jnt, sol='ikSCsolver')
    left_auto_clavicle_sc_ik_handle_grp = cmds.group(name=left_auto_clavicle_sc_ik_handle[0] + GRP_SUFFIX.capitalize(),
                                                     empty=True, world=True)
    left_auto_clavicle_sc_ik_handle_offset_grp = cmds.group(name=left_auto_clavicle_sc_ik_handle[0] + 'Offset',
                                                            empty=True, world=True)
    cmds.parent(left_auto_clavicle_sc_ik_handle_offset_grp, left_auto_clavicle_sc_ik_handle_grp)
    cmds.delete(cmds.pointConstraint(left_auto_clavicle_sc_ik_handle[0], left_auto_clavicle_sc_ik_handle_grp))
    cmds.parent(left_auto_clavicle_sc_ik_handle[0], left_auto_clavicle_sc_ik_handle_offset_grp)

    cmds.addAttr(left_wrist_ik_ctrl, ln='autoClavicleSystem', at='enum', en='-------------:', keyable=True)
    cmds.setAttr(left_wrist_ik_ctrl + '.autoClavicleSystem', lock=True)
    cmds.addAttr(left_wrist_ik_ctrl, ln='clavicleInfluence', at='double', k=True, minValue=0, maxValue=1)
    cmds.setAttr(left_wrist_ik_ctrl + ".clavicleInfluence", .1)
    cmds.addAttr(left_wrist_ik_ctrl, ln='clavicleLimitZ', at='double', k=True, minValue=0)
    cmds.setAttr(left_wrist_ik_ctrl + ".clavicleLimitZ", 3)
    cmds.addAttr(left_wrist_ik_ctrl, ln='clavicleRampUpStartEnd', at='bool', k=True, niceName="Show Ramp-up Locs")
    cmds.addAttr(left_wrist_ik_ctrl, ln='clavicleSlowMultiplier', at='double', k=True, minValue=0)
    cmds.setAttr(left_wrist_ik_ctrl + ".clavicleSlowMultiplier", .5)

    cmds.setAttr(left_auto_clavicle_sc_ik_handle_offset_grp + '.maxTransZLimitEnable', 1)
    cmds.setAttr(left_auto_clavicle_sc_ik_handle_offset_grp + '.minTransZLimitEnable', 1)
    cmds.connectAttr(left_wrist_ik_ctrl + '.clavicleLimitZ',
                     left_auto_clavicle_sc_ik_handle_offset_grp + '.maxTransZLimit')

    left_invert_z_limit_node = cmds.createNode('multiplyDivide', name=ctrl_name + "_autoClavicleZLimit_" + AUTO_SUFFIX)
    cmds.setAttr(left_invert_z_limit_node + '.input2Z', -1)

    cmds.connectAttr(left_wrist_ik_ctrl + '.clavicleLimitZ', left_invert_z_limit_node + '.input1Z')
    cmds.connectAttr(left_invert_z_limit_node + '.outputZ',
                     left_auto_clavicle_sc_ik_handle_offset_grp + '.minTransZLimit')

    left_switch_influence_node = ctrl_name + "_autoClavicleRotate_" + AUTO_SUFFIX
    left_switch_influence_node = cmds.createNode('multiplyDivide', name=left_switch_influence_node)

    offset_influence_multiply_node = ctrl_name + "_clavicleInfluence_" + MULTIPLY_SUFFIX
    offset_influence_multiply_node = cmds.createNode('multiplyDivide', name=offset_influence_multiply_node)

    # Gather Ramp-Up Information & Create Auxiliary Nodes
    ramp_up_influence_multiply_node = ctrl_name + "_autoClavicleRampUp_" + MULTIPLY_SUFFIX
    ramp_up_influence_multiply_node = cmds.createNode('multiplyDivide', name=ramp_up_influence_multiply_node)
    ramp_up_influence_remap_node = ctrl_name + "_autoClavicleRampUp_remap"
    ramp_up_influence_remap_node = cmds.createNode('remapValue', name=ramp_up_influence_remap_node)

    cmds.connectAttr(left_wrist_ik_ctrl + '.clavicleInfluence', left_switch_influence_node + '.input1X')
    cmds.connectAttr(left_wrist_ik_ctrl + '.clavicleInfluence', left_switch_influence_node + '.input1Y')
    cmds.connectAttr(left_wrist_ik_ctrl + '.clavicleInfluence', left_switch_influence_node + '.input1Z')

    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_switch_influence_node + '.input2X')
    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_switch_influence_node + '.input2Y')
    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_switch_influence_node + '.input2Z')
    cmds.connectAttr(left_switch_influence_node + '.outputX', ramp_up_influence_multiply_node + '.input2X')
    cmds.connectAttr(left_switch_influence_node + '.outputY', ramp_up_influence_multiply_node + '.input2Y')
    cmds.connectAttr(left_switch_influence_node + '.outputZ', ramp_up_influence_multiply_node + '.input2Z')
    cmds.connectAttr(ramp_up_influence_multiply_node + '.output', offset_influence_multiply_node + '.input2')

    cmds.connectAttr(ramp_up_influence_remap_node + '.outValue', ramp_up_influence_multiply_node + '.input1Y')
    cmds.setAttr(ramp_up_influence_multiply_node + '.input1X', 1)
    cmds.setAttr(ramp_up_influence_multiply_node + '.input1Z', 1)

    # Account for Offset Control
    left_auto_clavicle_rot = cmds.group(name='left_auto_clavicle_posSampler', empty=True, world=True)
    left_auto_clavicle_rot_grp = 'left_auto_clavicle_rot' + GRP_SUFFIX.capitalize()
    left_auto_clavicle_rot_grp = cmds.group(name=left_auto_clavicle_rot_grp, empty=True, world=True)

    # Limit to Translation Above Shoulder
    left_auto_clavicle_ramp_up = cmds.spaceLocator(name='left_auto_clavicle_rot_ramp_up_start')[0]
    left_auto_clavicle_ramp_up_end = cmds.spaceLocator(name='left_auto_clavicle_rot_ramp_up_end')[0]
    left_auto_clavicle_ramp_up_grp = 'left_auto_clavicle_ramp_up' + GRP_SUFFIX.capitalize()
    left_auto_clavicle_ramp_up_grp = cmds.group(name=left_auto_clavicle_ramp_up_grp, empty=True, world=True)

    cmds.parent(left_auto_clavicle_rot, left_auto_clavicle_rot_grp)
    cmds.parent(left_auto_clavicle_ramp_up, left_auto_clavicle_ramp_up_grp)
    cmds.parent(left_auto_clavicle_ramp_up_end, left_auto_clavicle_ramp_up_grp)
    cmds.delete(cmds.pointConstraint(rig_joints.get('left_wrist_jnt'), left_auto_clavicle_rot_grp))
    cmds.delete(cmds.pointConstraint(rig_joints.get('left_wrist_jnt'), left_auto_clavicle_ramp_up_grp))
    cmds.delete(cmds.pointConstraint(rig_joints.get('left_shoulder_jnt'),
                                     left_auto_clavicle_ramp_up_grp, skip=('x', 'z')))

    cmds.delete(cmds.pointConstraint(rig_joints.get('head_jnt'), left_auto_clavicle_ramp_up_end, skip=('x', 'z')))
    cmds.connectAttr(left_auto_clavicle_ramp_up_end + '.ty', ramp_up_influence_remap_node + '.inputMax')
    cmds.connectAttr(left_wrist_ik_ctrl + ".clavicleSlowMultiplier", ramp_up_influence_remap_node + '.outputMin')

    cmds.pointConstraint(left_wrist_offset_ik_ctrl, left_auto_clavicle_rot)
    cmds.pointConstraint(left_wrist_offset_ik_ctrl, left_auto_clavicle_ramp_up)

    # Limit Ramp Up
    cmds.setAttr(left_auto_clavicle_ramp_up + '.minTransYLimitEnable', 1)
    cmds.setAttr(left_auto_clavicle_ramp_up + '.minTransYLimit', 0)
    cmds.parent(left_auto_clavicle_rot_grp, left_wrist_ik_ctrl_grp)
    cmds.parent(left_auto_clavicle_ramp_up_grp, left_wrist_ik_ctrl_grp)

    cmds.connectAttr(left_auto_clavicle_rot + '.translate', offset_influence_multiply_node + '.input1')
    cmds.connectAttr(offset_influence_multiply_node + '.output',
                     left_auto_clavicle_sc_ik_handle_offset_grp + '.translate')

    change_viewport_color(left_clavicle_auto_jnt, automation_jnt_color)
    change_viewport_color(left_shoulder_auto_jnt, automation_jnt_color)
    cmds.setAttr(left_clavicle_auto_jnt + ".radius", 1)
    cmds.setAttr(left_shoulder_auto_jnt + ".radius", .5)

    # Setup Ramp-Up Locators
    cmds.connectAttr(left_wrist_ik_ctrl + '.clavicleRampUpStartEnd', left_auto_clavicle_ramp_up + '.v')
    cmds.connectAttr(left_wrist_ik_ctrl + '.clavicleRampUpStartEnd', left_auto_clavicle_ramp_up_end + '.v')
    change_viewport_color(left_auto_clavicle_ramp_up, automation_jnt_color)
    change_viewport_color(left_auto_clavicle_ramp_up_end, automation_jnt_color)
    lock_hide_default_attr(left_auto_clavicle_ramp_up)
    lock_hide_default_attr(left_auto_clavicle_ramp_up_end, translate=False)
    cmds.setAttr(left_auto_clavicle_ramp_up_end + '.tx', lock=True, k=False, channelBox=False)
    cmds.setAttr(left_auto_clavicle_ramp_up_end + '.tz', lock=True, k=False, channelBox=False)
    cmds.addAttr(left_auto_clavicle_ramp_up, ln='minimumTranslateY', at='double', k=True)
    cmds.connectAttr(left_auto_clavicle_ramp_up + '.minimumTranslateY', left_auto_clavicle_ramp_up + '.minTransYLimit')

    # Create Ramp Up Connection
    cmds.connectAttr(left_auto_clavicle_ramp_up + '.ty', ramp_up_influence_remap_node + '.inputValue')

    left_clavicle_offset_plus_node = cmds.createNode('plusMinusAverage',
                                                     name=ctrl_name + "_autoClavicleRotate_" + AUTO_SUFFIX)

    if settings.get('uniform_ctrl_orient'):
        rot_offset_node = cmds.createNode('multiplyDivide', name='left_clavicle_rotOffset')
        cmds.setAttr(rot_offset_node + '.input2Z', -1)
        cmds.connectAttr(left_clavicle_ctrl + '.rz', rot_offset_node + '.input1Z', f=True)
        cmds.connectAttr(rot_offset_node + '.outputZ', left_clavicle_offset_plus_node + '.input3D[0].input3Dy')
        cmds.connectAttr(left_clavicle_ctrl + '.rx', left_clavicle_offset_plus_node + '.input3D[0].input3Dx')
        cmds.connectAttr(left_clavicle_ctrl + '.ry', left_clavicle_offset_plus_node + '.input3D[0].input3Dz')
    else:
        cmds.connectAttr(left_clavicle_ctrl + '.rotate', left_clavicle_offset_plus_node + '.input3D[0]')
    cmds.connectAttr(left_clavicle_auto_jnt + '.rotate', left_clavicle_offset_plus_node + '.input3D[1]')
    cmds.connectAttr(left_clavicle_offset_plus_node + '.output3D', rig_joints.get('left_clavicle_jnt') + '.rotate',
                     force=True)

    # Right Auto Clavicle
    right_clavicle_auto_jnt = cmds.duplicate(rig_joints.get('right_clavicle_jnt'),
                                             name=rig_joints.get('right_clavicle_jnt').replace(JNT_SUFFIX, 'driver' +
                                                                                               JNT_SUFFIX.capitalize()),
                                             parentOnly=True)[0]
    right_shoulder_auto_jnt = cmds.duplicate(rig_joints.get('right_shoulder_jnt'),
                                             name=rig_joints.get('right_shoulder_jnt').replace(JNT_SUFFIX, 'driverEnd' +
                                                                                               JNT_SUFFIX.capitalize()),
                                             parentOnly=True)[0]
    cmds.parent(right_clavicle_auto_jnt, world=True)
    cmds.parent(right_shoulder_auto_jnt, right_clavicle_auto_jnt)

    right_auto_clavicle_sc_ik_handle = cmds.ikHandle(n='right_auto_clavicle_SC_ikHandle', sj=right_clavicle_auto_jnt,
                                                     ee=right_shoulder_auto_jnt, sol='ikSCsolver')
    right_auto_clavicle_sc_ik_handle_grp = cmds.group(
        name=right_auto_clavicle_sc_ik_handle[0] + GRP_SUFFIX.capitalize(), empty=True, world=True)
    right_auto_clavicle_sc_ik_handle_offset_grp = cmds.group(name=right_auto_clavicle_sc_ik_handle[0] + 'Offset',
                                                             empty=True, world=True)
    cmds.parent(right_auto_clavicle_sc_ik_handle_offset_grp, right_auto_clavicle_sc_ik_handle_grp)
    cmds.delete(cmds.pointConstraint(right_auto_clavicle_sc_ik_handle[0], right_auto_clavicle_sc_ik_handle_grp))
    cmds.parent(right_auto_clavicle_sc_ik_handle[0], right_auto_clavicle_sc_ik_handle_offset_grp)

    cmds.addAttr(right_wrist_ik_ctrl, ln='autoClavicleSystem', at='enum', en='-------------:', keyable=True)
    cmds.setAttr(right_wrist_ik_ctrl + '.autoClavicleSystem', lock=True)
    cmds.addAttr(right_wrist_ik_ctrl, ln='clavicleInfluence', at='double', k=True, minValue=0, maxValue=1)
    cmds.setAttr(right_wrist_ik_ctrl + ".clavicleInfluence", .1)
    cmds.addAttr(right_wrist_ik_ctrl, ln='clavicleLimitZ', at='double', k=True, minValue=0)
    cmds.setAttr(right_wrist_ik_ctrl + ".clavicleLimitZ", 3)
    cmds.addAttr(right_wrist_ik_ctrl, ln='clavicleRampUpStartEnd', at='bool', k=True, niceName="Show Ramp-up Locs")
    cmds.addAttr(right_wrist_ik_ctrl, ln='clavicleSlowMultiplier', at='double', k=True, minValue=0)
    cmds.setAttr(right_wrist_ik_ctrl + ".clavicleSlowMultiplier", .5)

    cmds.setAttr(right_auto_clavicle_sc_ik_handle_offset_grp + '.maxTransZLimitEnable', 1)
    cmds.setAttr(right_auto_clavicle_sc_ik_handle_offset_grp + '.minTransZLimitEnable', 1)
    cmds.connectAttr(right_wrist_ik_ctrl + '.clavicleLimitZ',
                     right_auto_clavicle_sc_ik_handle_offset_grp + '.maxTransZLimit')

    right_invert_z_limit_node = cmds.createNode('multiplyDivide', name=ctrl_name + "_autoClavicleZLimit_" + AUTO_SUFFIX)
    cmds.setAttr(right_invert_z_limit_node + '.input2Z', -1)

    cmds.connectAttr(right_wrist_ik_ctrl + '.clavicleLimitZ', right_invert_z_limit_node + '.input1Z')
    cmds.connectAttr(right_invert_z_limit_node + '.outputZ',
                     right_auto_clavicle_sc_ik_handle_offset_grp + '.minTransZLimit')

    right_switch_influence_node = ctrl_name + "_autoClavicleRotate_" + AUTO_SUFFIX
    right_switch_influence_node = cmds.createNode('multiplyDivide', name=right_switch_influence_node)

    offset_influence_multiply_node = ctrl_name + "_clavicleInfluence_" + MULTIPLY_SUFFIX
    offset_influence_multiply_node = cmds.createNode('multiplyDivide', name=offset_influence_multiply_node)

    # Gather Ramp-Up Information & Create Auxiliary Nodes
    ramp_up_influence_multiply_node = ctrl_name + "_autoClavicleRampUp_" + MULTIPLY_SUFFIX
    ramp_up_influence_multiply_node = cmds.createNode('multiplyDivide', name=ramp_up_influence_multiply_node)
    ramp_up_influence_remap_node = ctrl_name + "_autoClavicleRampUp_remap"
    ramp_up_influence_remap_node = cmds.createNode('remapValue', name=ramp_up_influence_remap_node)

    cmds.connectAttr(right_wrist_ik_ctrl + '.clavicleInfluence', right_switch_influence_node + '.input1X')
    cmds.connectAttr(right_wrist_ik_ctrl + '.clavicleInfluence', right_switch_influence_node + '.input1Y')
    cmds.connectAttr(right_wrist_ik_ctrl + '.clavicleInfluence', right_switch_influence_node + '.input1Z')

    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_switch_influence_node + '.input2X')
    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_switch_influence_node + '.input2Y')
    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_switch_influence_node + '.input2Z')
    cmds.connectAttr(right_switch_influence_node + '.outputX', ramp_up_influence_multiply_node + '.input2X')
    cmds.connectAttr(right_switch_influence_node + '.outputY', ramp_up_influence_multiply_node + '.input2Y')
    cmds.connectAttr(right_switch_influence_node + '.outputZ', ramp_up_influence_multiply_node + '.input2Z')
    cmds.connectAttr(ramp_up_influence_multiply_node + '.output', offset_influence_multiply_node + '.input2')

    cmds.connectAttr(ramp_up_influence_remap_node + '.outValue', ramp_up_influence_multiply_node + '.input1Y')
    cmds.setAttr(ramp_up_influence_multiply_node + '.input1X', 1)
    cmds.setAttr(ramp_up_influence_multiply_node + '.input1Z', 1)

    # Account for Offset Control
    right_auto_clavicle_rot = cmds.group(name='right_auto_clavicle_posSampler', empty=True, world=True)
    right_auto_clavicle_rot_grp = 'right_auto_clavicle_rot' + GRP_SUFFIX.capitalize()
    right_auto_clavicle_rot_grp = cmds.group(name=right_auto_clavicle_rot_grp, empty=True, world=True)

    # Limit to Translation Above Shoulder
    right_auto_clavicle_ramp_up = cmds.spaceLocator(name='right_auto_clavicle_rot_ramp_up_start')[0]
    right_auto_clavicle_ramp_up_end = cmds.spaceLocator(name='right_auto_clavicle_rot_ramp_up_end')[0]
    right_auto_clavicle_ramp_up_grp = 'right_auto_clavicle_ramp_up' + GRP_SUFFIX.capitalize()
    right_auto_clavicle_ramp_up_grp = cmds.group(name=right_auto_clavicle_ramp_up_grp, empty=True, world=True)

    cmds.parent(right_auto_clavicle_rot, right_auto_clavicle_rot_grp)
    cmds.parent(right_auto_clavicle_ramp_up, right_auto_clavicle_ramp_up_grp)
    cmds.parent(right_auto_clavicle_ramp_up_end, right_auto_clavicle_ramp_up_grp)
    cmds.delete(cmds.pointConstraint(rig_joints.get('right_wrist_jnt'), right_auto_clavicle_rot_grp))
    cmds.delete(cmds.pointConstraint(rig_joints.get('right_wrist_jnt'), right_auto_clavicle_ramp_up_grp))
    cmds.delete(cmds.pointConstraint(rig_joints.get('right_shoulder_jnt'),
                                     right_auto_clavicle_ramp_up_grp, skip=('x', 'z')))

    cmds.delete(cmds.pointConstraint(rig_joints.get('head_jnt'), right_auto_clavicle_ramp_up_end, skip=('x', 'z')))
    cmds.connectAttr(right_auto_clavicle_ramp_up_end + '.ty', ramp_up_influence_remap_node + '.inputMax')
    cmds.connectAttr(right_wrist_ik_ctrl + ".clavicleSlowMultiplier", ramp_up_influence_remap_node + '.outputMin')

    cmds.pointConstraint(right_wrist_offset_ik_ctrl, right_auto_clavicle_rot)
    cmds.pointConstraint(right_wrist_offset_ik_ctrl, right_auto_clavicle_ramp_up)

    # Limit Ramp Up
    cmds.setAttr(right_auto_clavicle_ramp_up + '.minTransYLimitEnable', 1)
    cmds.setAttr(right_auto_clavicle_ramp_up + '.minTransYLimit', 0)
    cmds.parent(right_auto_clavicle_rot_grp, right_wrist_ik_ctrl_grp)
    cmds.parent(right_auto_clavicle_ramp_up_grp, right_wrist_ik_ctrl_grp)

    cmds.connectAttr(right_auto_clavicle_rot + '.translate', offset_influence_multiply_node + '.input1')
    cmds.connectAttr(offset_influence_multiply_node + '.output',
                     right_auto_clavicle_sc_ik_handle_offset_grp + '.translate')

    change_viewport_color(right_clavicle_auto_jnt, automation_jnt_color)
    change_viewport_color(right_shoulder_auto_jnt, automation_jnt_color)
    cmds.setAttr(right_clavicle_auto_jnt + ".radius", 1)
    cmds.setAttr(right_shoulder_auto_jnt + ".radius", .5)

    # Setup Ramp-Up Locators
    cmds.connectAttr(right_wrist_ik_ctrl + '.clavicleRampUpStartEnd', right_auto_clavicle_ramp_up + '.v')
    cmds.connectAttr(right_wrist_ik_ctrl + '.clavicleRampUpStartEnd', right_auto_clavicle_ramp_up_end + '.v')
    change_viewport_color(right_auto_clavicle_ramp_up, automation_jnt_color)
    change_viewport_color(right_auto_clavicle_ramp_up_end, automation_jnt_color)
    lock_hide_default_attr(right_auto_clavicle_ramp_up)
    lock_hide_default_attr(right_auto_clavicle_ramp_up_end, translate=False)
    cmds.setAttr(right_auto_clavicle_ramp_up_end + '.tx', lock=True, k=False, channelBox=False)
    cmds.setAttr(right_auto_clavicle_ramp_up_end + '.tz', lock=True, k=False, channelBox=False)
    cmds.addAttr(right_auto_clavicle_ramp_up, ln='minimumTranslateY', at='double', k=True)
    cmds.connectAttr(right_auto_clavicle_ramp_up + '.minimumTranslateY',
                     right_auto_clavicle_ramp_up + '.minTransYLimit')

    # Create Ramp Up Connection
    cmds.connectAttr(right_auto_clavicle_ramp_up + '.ty', ramp_up_influence_remap_node + '.inputValue')

    right_clavicle_offset_plus_node = cmds.createNode('plusMinusAverage',
                                                      name=ctrl_name + "_autoClavicleRotate_" + AUTO_SUFFIX)

    if settings.get('uniform_ctrl_orient'):
        rot_offset_node = cmds.createNode('multiplyDivide', name='right_clavicle_rotOffset')
        cmds.setAttr(rot_offset_node + '.input2Z', -1)
        cmds.connectAttr(right_clavicle_ctrl + '.rz', rot_offset_node + '.input1Z', f=True)
        cmds.connectAttr(rot_offset_node + '.outputZ', right_clavicle_offset_plus_node + '.input3D[0].input3Dy')
        cmds.connectAttr(right_clavicle_ctrl + '.rx', right_clavicle_offset_plus_node + '.input3D[0].input3Dx')
        cmds.connectAttr(right_clavicle_ctrl + '.ry', right_clavicle_offset_plus_node + '.input3D[0].input3Dz')
    else:
        cmds.connectAttr(right_clavicle_ctrl + '.rotate', right_clavicle_offset_plus_node + '.input3D[0]')
    cmds.connectAttr(right_clavicle_auto_jnt + '.rotate', right_clavicle_offset_plus_node + '.input3D[1]')
    cmds.connectAttr(right_clavicle_offset_plus_node + '.output3D', rig_joints.get('right_clavicle_jnt') + '.rotate',
                     force=True)

    # Organize Auto Clavicle System
    cmds.setAttr(left_clavicle_auto_jnt + ".v", 0)
    cmds.setAttr(right_clavicle_auto_jnt + ".v", 0)
    cmds.parent(left_clavicle_auto_jnt, skeleton_grp)
    cmds.parent(right_clavicle_auto_jnt, skeleton_grp)

    auto_clavicle_grp = cmds.group(name='autoClavicle_grp', empty=True, world=True)
    cmds.parent(left_auto_clavicle_sc_ik_handle_grp, auto_clavicle_grp)
    cmds.parent(right_auto_clavicle_sc_ik_handle_grp, auto_clavicle_grp)
    cmds.parent(left_clavicle_pos_loc_grp, auto_clavicle_grp)
    cmds.parent(right_clavicle_pos_loc_grp, auto_clavicle_grp)
    cmds.parent(auto_clavicle_grp, general_automation_grp)  # Group created above with the other top parent groups

    # Clavicle Breathing Mechanics
    for ctrl_pair in [(left_clavicle_ctrl, left_clavicle_pos_loc), (right_clavicle_ctrl, right_clavicle_pos_loc)]:
        ctrl_name = ctrl_pair[0].replace('_' + CTRL_SUFFIX, '')
        if 'left_' in ctrl_name:
            attr_name = 'L' + ctrl_name.replace('left_', '').capitalize()
            attr_nice_name = 'Max Trans L ' + ctrl_name.replace('left_', '').capitalize()
        else:
            attr_name = 'R' + ctrl_name.replace('right_', '').capitalize()
            attr_nice_name = 'Max Trans R ' + ctrl_name.replace('right_', '').capitalize()

        breathing_range_node = cmds.createNode('setRange', name=ctrl_name + '_breathing_range')

        breathing_sine_min = -1
        breathing_sine_max = 1
        breathing_new_min = 0
        limit_translate_prefix = 'maxTranslate'

        cmds.addAttr(main_ctrl, ln=limit_translate_prefix + attr_name, at='double', keyable=True, nn=attr_nice_name)

        for attr in ['x', 'y', 'z']:
            cmds.setAttr(breathing_range_node + '.oldMin' + attr.capitalize(), breathing_sine_min)
            cmds.setAttr(breathing_range_node + '.oldMax' + attr.capitalize(), breathing_sine_max)
            cmds.setAttr(breathing_range_node + '.min' + attr.capitalize(), breathing_new_min)
            cmds.connectAttr(main_ctrl + '.' + limit_translate_prefix + attr_name,
                             breathing_range_node + '.max' + attr.capitalize())

        cmds.connectAttr(sine_output[0], breathing_range_node + '.valueX')
        cmds.connectAttr(sine_output[0], breathing_range_node + '.valueY')
        cmds.connectAttr(sine_output[0], breathing_range_node + '.valueZ')

        influence_multiply_node = cmds.createNode('multiplyDivide',
                                                  name=ctrl_name + "breathingInfluence_" + MULTIPLY_SUFFIX)

        cmds.connectAttr(breathing_range_node + '.outValueY', influence_multiply_node + '.input1Y')
        cmds.connectAttr(main_ctrl + '.breathingInfluence', influence_multiply_node + '.input2Y')
        cmds.connectAttr(influence_multiply_node + '.outputY', ctrl_pair[1] + '.ty')

        cmds.setAttr(main_ctrl + '.' + limit_translate_prefix + attr_name, 1)

    # Eye Visibility Attr
    cmds.addAttr(head_ctrl, ln='eyeCtrlVisibility', at='bool', keyable=True)
    cmds.setAttr(head_ctrl + '.eyeCtrlVisibility', 1)
    cmds.connectAttr(head_ctrl + '.eyeCtrlVisibility', main_eye_ctrl_grp + '.v')

    # Fix Fingers/Hand Stretch
    # Left Side
    left_hand_constraint = cmds.parentConstraint(
        [left_wrist_offset_ik_ctrl, left_wrist_ctrl, left_wrist_ik_jnt, left_wrist_fk_jnt], left_hand_grp, mo=True)

    left_switch_hand_blend_a = cmds.createNode('blendColors', name='left_hand_stretchy_blend')
    left_switch_hand_blend_b = cmds.createNode('blendColors', name='left_hand_nonStretchy_blend')

    cmds.connectAttr(left_arm_switch + '.stretch', left_switch_hand_blend_a + '.blender', f=True)
    cmds.connectAttr(left_arm_switch + '.stretch', left_switch_hand_blend_b + '.blender', f=True)

    cmds.setAttr(left_switch_hand_blend_a + '.color2R', 0)
    cmds.setAttr(left_switch_hand_blend_a + '.color2G', 0)
    cmds.setAttr(left_switch_hand_blend_b + '.color1R', 0)
    cmds.setAttr(left_switch_hand_blend_b + '.color1G', 0)

    cmds.connectAttr(left_switch_reverse_node + '.outputX', left_switch_hand_blend_a + '.color1R', f=True)
    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_switch_hand_blend_a + '.color1G', f=True)

    cmds.connectAttr(left_switch_reverse_node + '.outputX', left_switch_hand_blend_b + '.color2R', f=True)
    cmds.connectAttr(left_arm_switch + '.influenceSwitch', left_switch_hand_blend_b + '.color2G', f=True)

    cmds.connectAttr(left_switch_hand_blend_a + '.outputG', left_hand_constraint[0] + '.w0', f=True)
    cmds.connectAttr(left_switch_hand_blend_a + '.outputR', left_hand_constraint[0] + '.w1', f=True)

    cmds.connectAttr(left_switch_hand_blend_b + '.outputG', left_hand_constraint[0] + '.w2', f=True)
    cmds.connectAttr(left_switch_hand_blend_b + '.outputR', left_hand_constraint[0] + '.w3', f=True)

    # Right Side
    right_hand_constraint = cmds.parentConstraint(
        [right_wrist_offset_ik_ctrl, right_wrist_ctrl, right_wrist_ik_jnt, right_wrist_fk_jnt], right_hand_grp, mo=True)

    right_switch_hand_blend_a = cmds.createNode('blendColors', name='right_hand_stretchy_blend')
    right_switch_hand_blend_b = cmds.createNode('blendColors', name='right_hand_nonStretchy_blend')

    cmds.connectAttr(right_arm_switch + '.stretch', right_switch_hand_blend_a + '.blender', f=True)
    cmds.connectAttr(right_arm_switch + '.stretch', right_switch_hand_blend_b + '.blender', f=True)

    cmds.setAttr(right_switch_hand_blend_a + '.color2R', 0)
    cmds.setAttr(right_switch_hand_blend_a + '.color2G', 0)
    cmds.setAttr(right_switch_hand_blend_b + '.color1R', 0)
    cmds.setAttr(right_switch_hand_blend_b + '.color1G', 0)

    cmds.connectAttr(right_switch_reverse_node + '.outputX', right_switch_hand_blend_a + '.color1R', f=True)
    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_switch_hand_blend_a + '.color1G', f=True)

    cmds.connectAttr(right_switch_reverse_node + '.outputX', right_switch_hand_blend_b + '.color2R', f=True)
    cmds.connectAttr(right_arm_switch + '.influenceSwitch', right_switch_hand_blend_b + '.color2G', f=True)

    cmds.connectAttr(right_switch_hand_blend_a + '.outputG', right_hand_constraint[0] + '.w0', f=True)
    cmds.connectAttr(right_switch_hand_blend_a + '.outputR', right_hand_constraint[0] + '.w1', f=True)

    cmds.connectAttr(right_switch_hand_blend_b + '.outputG', right_hand_constraint[0] + '.w2', f=True)
    cmds.connectAttr(right_switch_hand_blend_b + '.outputR', right_hand_constraint[0] + '.w3', f=True)

    # No Flip Setup for Wrists
    cmds.parent(left_wrist_ik_dir_jnt, left_wrist_ik_jnt)
    cmds.move(left_wrist_scale_offset, left_wrist_ik_dir_jnt, x=True, relative=True, objectSpace=True)
    left_hand_sc_ik_handle = cmds.ikHandle(n='left_hand_SC_ikHandle', sj=left_wrist_ik_jnt, ee=left_wrist_ik_dir_jnt[0],
                                           sol='ikSCsolver')
    cmds.parent(left_hand_sc_ik_handle[0], left_wrist_offset_ik_ctrl)
    cmds.setAttr(left_hand_sc_ik_handle[0] + '.v', 0)
    cmds.parent(right_wrist_ik_dir_jnt, right_wrist_ik_jnt)
    cmds.move(right_wrist_scale_offset * -1, right_wrist_ik_dir_jnt, x=True, relative=True, objectSpace=True)

    right_hand_sc_ik_handle = cmds.ikHandle(n='right_hand_SC_ikHandle', sj=right_wrist_ik_jnt,
                                            ee=right_wrist_ik_dir_jnt[0], sol='ikSCsolver')
    # cmds.parent(right_hand_sc_ik_handle[0], right_wrist_offset_ik_ctrl)
    cmds.parent(right_hand_sc_ik_handle[0], right_wrist_offset_ik_ctrl_data)
    cmds.setAttr(right_hand_sc_ik_handle[0] + '.v', 0)

    # ################# Bulletproof Controls #################
    lock_hide_default_attr(cog_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(spine01_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(spine02_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(spine03_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(spine04_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(neck_base_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(neck_mid_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(head_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(jaw_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(hip_ctrl, translate=False, rotate=False)

    # Legs and Arms FK
    lock_hide_default_attr(left_hip_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(left_knee_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(left_ankle_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(left_ball_ctrl, translate=False, rotate=False)

    lock_hide_default_attr(right_hip_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(right_knee_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(right_ankle_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(right_ball_ctrl, translate=False, rotate=False)

    # Arms IK
    lock_hide_default_attr(left_clavicle_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(left_shoulder_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(left_elbow_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(left_wrist_ctrl, translate=False, rotate=False)

    lock_hide_default_attr(right_clavicle_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(right_shoulder_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(right_elbow_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(right_wrist_ctrl, translate=False, rotate=False)

    lock_hide_default_attr(left_wrist_ik_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(left_elbow_ik_ctrl, translate=False)
    lock_hide_default_attr(right_wrist_ik_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(right_elbow_ik_ctrl, translate=False)

    # Fingers Automation
    lock_hide_default_attr(left_fingers_ctrl, rotate=False, scale=False)
    lock_hide_default_attr(right_fingers_ctrl, rotate=False, scale=False)
    cmds.setAttr(left_fingers_ctrl + '.rx', lock=True, k=False, channelBox=False)
    cmds.setAttr(left_fingers_ctrl + '.ry', lock=True, k=False, channelBox=False)
    cmds.setAttr(right_fingers_ctrl + '.rx', lock=True, k=False, channelBox=False)
    cmds.setAttr(right_fingers_ctrl + '.ry', lock=True, k=False, channelBox=False)

    # Fingers
    lock_fingers = [  # Left
        left_thumb01_ctrl_list[0], left_thumb02_ctrl_list[0], left_thumb03_ctrl_list[0],
        left_index01_ctrl_list[0], left_index02_ctrl_list[0], left_index03_ctrl_list[0],
        left_middle01_ctrl_list[0], left_middle02_ctrl_list[0], left_middle03_ctrl_list[0],
        left_ring01_ctrl_list[0], left_ring02_ctrl_list[0], left_ring03_ctrl_list[0],
        left_pinky01_ctrl_list[0], left_pinky02_ctrl_list[0], left_pinky03_ctrl_list[0],
        # Right
        right_thumb01_ctrl_list[0], right_thumb02_ctrl_list[0], right_thumb03_ctrl_list[0],
        right_index01_ctrl_list[0], right_index02_ctrl_list[0], right_index03_ctrl_list[0],
        right_middle01_ctrl_list[0], right_middle02_ctrl_list[0], right_middle03_ctrl_list[0],
        right_ring01_ctrl_list[0], right_ring02_ctrl_list[0], right_ring03_ctrl_list[0],
        right_pinky01_ctrl_list[0], right_pinky02_ctrl_list[0], right_pinky03_ctrl_list[0]
    ]

    for finger in lock_fingers:
        lock_hide_default_attr(finger, translate=False, rotate=False)

    # Foot Automation
    lock_hide_default_attr(left_foot_ik_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(left_heel_roll_ctrl, rotate=False)
    lock_hide_default_attr(left_ball_roll_ctrl, rotate=False)
    lock_hide_default_attr(left_toe_roll_ctrl, rotate=False)
    lock_hide_default_attr(left_toe_up_down_ctrl, translate=False)
    lock_hide_default_attr(left_knee_ik_ctrl, translate=False)

    lock_hide_default_attr(right_foot_ik_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(right_heel_roll_ctrl, rotate=False)
    lock_hide_default_attr(right_ball_roll_ctrl, rotate=False)
    lock_hide_default_attr(right_toe_roll_ctrl, rotate=False)
    lock_hide_default_attr(right_toe_up_down_ctrl, translate=False)
    lock_hide_default_attr(right_knee_ik_ctrl, translate=False)

    # Switch Controls
    lock_hide_default_attr(left_arm_switch)
    lock_hide_default_attr(right_arm_switch)
    lock_hide_default_attr(left_leg_switch)
    lock_hide_default_attr(right_leg_switch)

    # Eye Controls
    lock_hide_default_attr(main_eye_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(left_eye_ctrl, translate=False)
    lock_hide_default_attr(right_eye_ctrl, translate=False)

    # Lock Groups
    lock_hide_default_attr(controls_grp, visibility=False)
    lock_hide_default_attr(skeleton_grp, visibility=False)
    lock_hide_default_attr(direction_ctrl, translate=False, rotate=False, visibility=False)
    lock_hide_default_attr(rig_setup_grp, visibility=False)
    lock_hide_default_attr(geometry_grp, visibility=False)
    lock_hide_default_attr(rig_grp, visibility=False)
    lock_hide_default_attr(foot_automation_grp, visibility=False)
    lock_hide_default_attr(stretchy_system_grp, visibility=False)
    lock_hide_default_attr(ik_solvers_grp, visibility=False)

    # Spine Ribbon
    lock_hide_default_attr(cog_ribbon_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(spine_ribbon_ctrl, translate=False, rotate=False)
    lock_hide_default_attr(chest_ribbon_ctrl, translate=False, rotate=False)

    # Create Seamless FK/IK Switch References
    left_ankle_ref_loc = cmds.spaceLocator(name=elements_default.get('left_ankle_ik_reference'))[0]
    cmds.delete(cmds.parentConstraint(left_foot_ik_ctrl, left_ankle_ref_loc))
    cmds.parent(left_ankle_ref_loc, left_ankle_fk_jnt)
    cmds.setAttr(left_ankle_ref_loc + '.v', 0)

    left_knee_ref_loc = cmds.spaceLocator(name=elements_default.get('left_knee_ik_reference'))[0]
    cmds.delete(cmds.pointConstraint(left_knee_ik_ctrl, left_knee_ref_loc))
    cmds.parent(left_knee_ref_loc, left_knee_fk_jnt)
    cmds.setAttr(left_knee_ref_loc + '.v', 0)

    left_elbow_ref_loc = cmds.spaceLocator(name=elements_default.get('left_elbow_ik_reference'))[0]
    cmds.delete(cmds.pointConstraint(left_elbow_ik_ctrl, left_elbow_ref_loc))
    cmds.parent(left_elbow_ref_loc, left_elbow_fk_jnt)
    cmds.setAttr(left_elbow_ref_loc + '.v', 0)

    right_ankle_ref_loc = cmds.spaceLocator(name=elements_default.get('right_ankle_ik_reference'))[0]
    cmds.delete(cmds.parentConstraint(right_foot_ik_ctrl, right_ankle_ref_loc))
    cmds.parent(right_ankle_ref_loc, right_ankle_fk_jnt)
    cmds.setAttr(right_ankle_ref_loc + '.v', 0)

    right_knee_ref_loc = cmds.spaceLocator(name=elements_default.get('right_knee_ik_reference'))[0]
    cmds.delete(cmds.pointConstraint(right_knee_ik_ctrl, right_knee_ref_loc))
    cmds.parent(right_knee_ref_loc, right_knee_fk_jnt)
    cmds.setAttr(right_knee_ref_loc + '.v', 0)

    right_elbow_ref_loc = cmds.spaceLocator(name=elements_default.get('right_elbow_ik_reference'))[0]
    cmds.delete(cmds.pointConstraint(right_elbow_ik_ctrl, right_elbow_ref_loc))
    cmds.parent(right_elbow_ref_loc, right_elbow_fk_jnt)
    cmds.setAttr(right_elbow_ref_loc + '.v', 0)

    # Wrist Reference
    right_wrist_ref_loc = cmds.spaceLocator(name=elements_default.get('right_wrist_ik_reference'))[0]
    cmds.delete(cmds.parentConstraint(right_wrist_ik_ctrl, right_wrist_ref_loc))
    cmds.parent(right_wrist_ref_loc, right_wrist_fk_jnt)
    cmds.setAttr(right_wrist_ref_loc + '.v', 0)

    left_wrist_ref_loc = cmds.spaceLocator(name=elements_default.get('left_wrist_ik_reference'))[0]
    cmds.delete(cmds.parentConstraint(left_wrist_ik_ctrl, left_wrist_ref_loc))
    cmds.parent(left_wrist_ref_loc, left_wrist_fk_jnt)
    cmds.setAttr(left_wrist_ref_loc + '.v', 0)

    # Uniform FK Offset Reference
    switch_ref_locators = []
    # Left Arm
    left_shoulder_fk_ref_loc = cmds.spaceLocator(name='left_fkShoulderOffsetRef_loc')[0]  # TODO
    cmds.delete(cmds.parentConstraint(left_shoulder_ik_jnt, left_shoulder_fk_ref_loc))
    cmds.parent(left_shoulder_fk_ref_loc, left_shoulder_ik_jnt)
    cmds.setAttr(left_shoulder_fk_ref_loc + '.v', 0)
    switch_ref_locators.append(left_shoulder_fk_ref_loc)

    left_elbow_fk_ref_loc = cmds.spaceLocator(name='left_fkElbowOffsetRef_loc')[0]
    cmds.delete(cmds.parentConstraint(left_elbow_ik_jnt, left_elbow_fk_ref_loc))
    cmds.parent(left_elbow_fk_ref_loc, left_elbow_ik_jnt)
    cmds.setAttr(left_elbow_fk_ref_loc + '.v', 0)
    switch_ref_locators.append(left_elbow_fk_ref_loc)

    left_wrist_fk_ref_loc = cmds.spaceLocator(name='left_fkWristOffsetRef_loc')[0]
    cmds.delete(cmds.parentConstraint(left_wrist_ik_jnt, left_wrist_fk_ref_loc))
    cmds.parent(left_wrist_fk_ref_loc, left_wrist_ik_jnt)
    cmds.setAttr(left_wrist_fk_ref_loc + '.v', 0)
    switch_ref_locators.append(left_wrist_fk_ref_loc)

    # Right Arm
    right_shoulder_fk_ref_loc = cmds.spaceLocator(name='right_fkShoulderOffsetRef_loc')[0]  # TODO
    cmds.delete(cmds.parentConstraint(right_shoulder_ik_jnt, right_shoulder_fk_ref_loc))
    cmds.parent(right_shoulder_fk_ref_loc, right_shoulder_ik_jnt)
    cmds.setAttr(right_shoulder_fk_ref_loc + '.v', 0)
    switch_ref_locators.append(right_shoulder_fk_ref_loc)

    right_elbow_fk_ref_loc = cmds.spaceLocator(name='right_fkElbowOffsetRef_loc')[0]
    cmds.delete(cmds.parentConstraint(right_elbow_ik_jnt, right_elbow_fk_ref_loc))
    cmds.parent(right_elbow_fk_ref_loc, right_elbow_ik_jnt)
    cmds.setAttr(right_elbow_fk_ref_loc + '.v', 0)
    switch_ref_locators.append(right_elbow_fk_ref_loc)

    right_wrist_fk_ref_loc = cmds.spaceLocator(name='right_fkWristOffsetRef_loc')[0]
    cmds.delete(cmds.parentConstraint(right_wrist_ik_jnt, right_wrist_fk_ref_loc))
    cmds.parent(right_wrist_fk_ref_loc, right_wrist_ik_jnt)
    cmds.setAttr(right_wrist_fk_ref_loc + '.v', 0)
    switch_ref_locators.append(right_wrist_fk_ref_loc)

    # Left Leg
    left_hip_fk_ref_loc = cmds.spaceLocator(name='left_fkHipOffsetRef_loc')[0]
    cmds.delete(cmds.parentConstraint(left_hip_ik_jnt, left_hip_fk_ref_loc))
    cmds.parent(left_hip_fk_ref_loc, left_hip_ik_jnt)
    cmds.setAttr(left_hip_fk_ref_loc + '.v', 0)
    switch_ref_locators.append(left_hip_fk_ref_loc)

    left_knee_fk_ref_loc = cmds.spaceLocator(name='left_fkKneeOffsetRef_loc')[0]
    cmds.delete(cmds.parentConstraint(left_knee_ik_jnt, left_knee_fk_ref_loc))
    cmds.parent(left_knee_fk_ref_loc, left_knee_ik_jnt)
    cmds.setAttr(left_knee_fk_ref_loc + '.v', 0)
    switch_ref_locators.append(left_knee_fk_ref_loc)

    left_ankle_fk_ref_loc = cmds.spaceLocator(name='left_fkAnkleOffsetRef_loc')[0]
    cmds.delete(cmds.parentConstraint(left_ankle_ik_jnt, left_ankle_fk_ref_loc))
    cmds.parent(left_ankle_fk_ref_loc, left_ankle_ik_jnt)
    cmds.setAttr(left_ankle_fk_ref_loc + '.v', 0)
    switch_ref_locators.append(left_ankle_fk_ref_loc)

    # Right Leg
    right_hip_fk_ref_loc = cmds.spaceLocator(name='right_fkHipOffsetRef_loc')[0]
    cmds.delete(cmds.parentConstraint(right_hip_ik_jnt, right_hip_fk_ref_loc))
    cmds.parent(right_hip_fk_ref_loc, right_hip_ik_jnt)
    cmds.setAttr(right_hip_fk_ref_loc + '.v', 0)
    switch_ref_locators.append(right_hip_fk_ref_loc)

    right_knee_fk_ref_loc = cmds.spaceLocator(name='right_fkKneeOffsetRef_loc')[0]
    cmds.delete(cmds.parentConstraint(right_knee_ik_jnt, right_knee_fk_ref_loc))
    cmds.parent(right_knee_fk_ref_loc, right_knee_ik_jnt)
    cmds.setAttr(right_knee_fk_ref_loc + '.v', 0)
    switch_ref_locators.append(right_knee_fk_ref_loc)

    right_ankle_fk_ref_loc = cmds.spaceLocator(name='right_fkAnkleOffsetRef_loc')[0]
    cmds.delete(cmds.parentConstraint(right_ankle_ik_jnt, right_ankle_fk_ref_loc))
    cmds.parent(right_ankle_fk_ref_loc, right_ankle_ik_jnt)
    cmds.setAttr(right_ankle_fk_ref_loc + '.v', 0)
    switch_ref_locators.append(right_ankle_fk_ref_loc)

    if settings.get('uniform_ctrl_orient'):
        for loc in switch_ref_locators:
            cmds.rotate(0, -90, -90, loc, os=True, relative=True)

    # Simplify Spine (Reduce number of joints from 5 to 3)
    if settings.get('simplify_spine'):
        for jnt in ['spine01_jnt', 'spine02_jnt', 'spine03_jnt']:
            cmds.setAttr(rig_joints.get(jnt) + '.v', 0)

        new_spine_name = re.sub(r'[0-9]+', '', rig_joints.get('spine02_jnt'))  # Remove Numbers
        new_spine_02_jnt = cmds.duplicate(rig_joints.get('spine02_jnt'), name=new_spine_name, po=True)[0]
        cmds.setAttr(new_spine_02_jnt + '.v', 1)
        cmds.parent(new_spine_02_jnt, world=True)

        cmds.delete(cmds.parentConstraint([rig_joints.get('spine01_jnt'),
                                           rig_joints.get('spine02_jnt'),
                                           rig_joints.get('spine03_jnt'),
                                           ], new_spine_02_jnt))

        cmds.parent(rig_joints.get('spine01_jnt'), skeleton_grp)
        cmds.parent(rig_joints.get('spine02_jnt'), skeleton_grp)
        cmds.parent(rig_joints.get('spine03_jnt'), skeleton_grp)
        cmds.parent(new_spine_02_jnt, rig_joints.get('cog_jnt'))
        cmds.parent(rig_joints.get('spine04_jnt'), new_spine_02_jnt)
        cmds.parentConstraint(rig_joints.get('spine02_jnt'), new_spine_02_jnt, mo=True)
        rig_joints['spine02_jnt'] = new_spine_02_jnt

    # Enforce footToe ikHandle position
    cmds.matchTransform(right_leg_toe_ik_handle[0], right_toe_fk_jnt, pos=1, rot=1)
    cmds.matchTransform(left_leg_toe_ik_handle[0], left_toe_fk_jnt, pos=1, rot=1)

    # Move Pelvis under Root
    cmds.parent(rig_joints.get('hip_jnt'), rig_joints.get('main_jnt'))
    cmds.parent(rig_joints.get('cog_jnt'), rig_joints.get('hip_jnt'))

    # Store Proxy as String Attribute
    store_proxy_as_string(main_ctrl, 'biped_proxy_pose', data_biped)

    # Delete Proxy
    cmds.delete(elements.get('main_proxy_grp'))

    # Add Notes - Controls
    note = 'This rig was created using ' + str(data_biped.script_name) + '. (v' + str(
        data_biped.script_version) + ')\n\nIssues, questions or suggestions? Go to:\ngithub.com/TrevisanGMW/gt-tools'
    add_node_note(main_ctrl, note)
    add_node_note(main_ctrl_grp, note)
    add_node_note(controls_grp, note)
    add_node_note(rig_grp, note)

    note = 'Finger automation system. Rotating this control will cause fingers to rotate in the same direction. ' \
           'Convenient for when quickly creating a fist or splay pose.\nAttributes:\n-Activate System: ' \
           'Whether or not the system is active.\n\n-Fist Pose Limit: What rotation should be considered a ' \
           '"fist" pose for the fingers.\n\n-Rot Multiplier: How much of the rotation will be transferred to the ' \
           'selected finger. (Used to create a less robotic movement between the fingers)\n\n-Show Attributes: ' \
           'These attributes control the visibility of other finger related controls. '
    add_node_note(left_fingers_ctrl, note)
    add_node_note(right_fingers_ctrl, note)

    # ################# Control Manip Default #################
    cmds.setAttr(main_ctrl + '.showManipDefault', 1)  # Translate
    cmds.setAttr(direction_ctrl + '.showManipDefault', 6)  # Smart
    cmds.setAttr(cog_ctrl + '.showManipDefault', 6)  # Smart
    cmds.setAttr(hip_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(spine01_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(spine02_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(spine03_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(spine04_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(neck_base_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(neck_mid_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(head_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(jaw_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(main_eye_ctrl + '.showManipDefault', 1)  # Translate
    cmds.setAttr(left_eye_ctrl + '.showManipDefault', 1)  # Translate
    cmds.setAttr(right_eye_ctrl + '.showManipDefault', 1)  # Translate

    # ### Left Controls
    cmds.setAttr(left_hip_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(left_knee_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(left_ankle_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(left_ball_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(left_foot_ik_ctrl + '.showManipDefault', 6)  # Smart
    cmds.setAttr(left_knee_ik_ctrl + '.showManipDefault', 1)  # Translate
    cmds.setAttr(left_clavicle_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(left_shoulder_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(left_elbow_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(left_wrist_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(left_wrist_ik_ctrl + '.showManipDefault', 6)  # Smart
    cmds.setAttr(left_elbow_ik_ctrl + '.showManipDefault', 1)  # Translate
    cmds.setAttr(left_fingers_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(left_toe_roll_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(left_ball_roll_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(left_heel_roll_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(left_toe_up_down_ctrl + '.showManipDefault', 1)  # Translate
    for finger in left_fingers_list:
        for ctrl_tuple in finger:
            for ctrl in ctrl_tuple:
                cmds.setAttr(ctrl + '.showManipDefault', 2)  # Rotate

    # ### Right Controls
    cmds.setAttr(right_hip_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(right_knee_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(right_ankle_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(right_ball_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(right_foot_ik_ctrl + '.showManipDefault', 6)  # Smart
    cmds.setAttr(right_knee_ik_ctrl + '.showManipDefault', 1)  # Translate
    cmds.setAttr(right_clavicle_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(right_shoulder_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(right_elbow_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(right_wrist_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(right_wrist_ik_ctrl + '.showManipDefault', 6)  # Smart
    cmds.setAttr(right_elbow_ik_ctrl + '.showManipDefault', 1)  # Translate
    cmds.setAttr(right_fingers_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(right_toe_roll_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(right_ball_roll_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(right_heel_roll_ctrl + '.showManipDefault', 2)  # Rotate
    cmds.setAttr(right_toe_up_down_ctrl + '.showManipDefault', 1)  # Translate
    for finger in right_fingers_list:
        for ctrl_tuple in finger:
            for ctrl in ctrl_tuple:
                cmds.setAttr(ctrl + '.showManipDefault', 2)  # Rotate

    """
    # ################# Joint Labelling #################
    # Joint Side
    for obj in rig_joints:
        if 'left_' in obj:
            cmds.setAttr(rig_joints.get(obj) + '.side', 1)  # 1 Left
        elif 'right_' in obj:
            cmds.setAttr(rig_joints.get(obj) + '.side', 2)  # 2 Right
        else:
            cmds.setAttr(rig_joints.get(obj) + '.side', 0)  # 0 Center
    
    # Joint Label
    cmds.setAttr(rig_joints.get('main_jnt') + '.type', 18)  # Other
    cmds.setAttr(rig_joints.get('main_jnt') + '.otherType', 'Origin', type='string')  # Other
    cmds.setAttr(rig_joints.get('cog_jnt') + '.type', 1)  # Root
    cmds.setAttr(rig_joints.get('spine01_jnt') + '.type', 6)  # Spine
    cmds.setAttr(rig_joints.get('spine02_jnt') + '.type', 6)  # Spine
    cmds.setAttr(rig_joints.get('spine03_jnt') + '.type', 6)  # Spine
    cmds.setAttr(rig_joints.get('spine04_jnt') + '.type', 6)  # Spine
    # cmds.setAttr(rig_joints.get('neck_base_jnt') + '.type', 7)  # Neck - Causing ngSkinTools to fail mirror operation
    # cmds.setAttr(rig_joints.get('neck_mid_jnt') + '.type', 7)  # Neck
    cmds.setAttr(rig_joints.get('head_jnt') + '.type', 8)  # Head
    cmds.setAttr(rig_joints.get('jaw_jnt') + '.type', 18)  # Other
    cmds.setAttr(rig_joints.get('jaw_jnt') + '.otherType', 'Jaw', type='string')  # Other
    cmds.setAttr(rig_joints.get('left_eye_jnt') + '.type', 18)  # Other
    cmds.setAttr(rig_joints.get('right_eye_jnt') + '.type', 18)  # Other
    cmds.setAttr(rig_joints.get('left_eye_jnt') + '.otherType', 'Eye', type='string')  # Other
    cmds.setAttr(rig_joints.get('right_eye_jnt') + '.otherType', 'Eye', type='string')  # Other
    cmds.setAttr(rig_joints.get('hip_jnt') + '.type', 2)  # Hip
    cmds.setAttr(rig_joints.get('left_hip_jnt') + '.type', 2)  # Hip
    cmds.setAttr(rig_joints.get('right_hip_jnt') + '.type', 2)  # Hip
    cmds.setAttr(rig_joints.get('left_knee_jnt') + '.type', 3)  # Knee
    cmds.setAttr(rig_joints.get('right_knee_jnt') + '.type', 3)  # Knee
    cmds.setAttr(rig_joints.get('left_ankle_jnt') + '.type', 4)  # Foot
    cmds.setAttr(rig_joints.get('right_ankle_jnt') + '.type', 4)  # Foot
    cmds.setAttr(rig_joints.get('left_ball_jnt') + '.type', 5)  # Toe
    cmds.setAttr(rig_joints.get('right_ball_jnt') + '.type', 5)  # Toe
    cmds.setAttr(rig_joints.get('left_clavicle_jnt') + '.type', 9)  # Collar
    cmds.setAttr(rig_joints.get('right_clavicle_jnt') + '.type', 9)  # Collar
    cmds.setAttr(rig_joints.get('left_shoulder_jnt') + '.type', 10)  # Shoulder
    cmds.setAttr(rig_joints.get('right_shoulder_jnt') + '.type', 10)  # Shoulder
    cmds.setAttr(rig_joints.get('left_elbow_jnt') + '.type', 11)  # Elbow
    cmds.setAttr(rig_joints.get('right_elbow_jnt') + '.type', 11)  # Elbow
    cmds.setAttr(rig_joints.get('left_wrist_jnt') + '.type', 12)  # Elbow
    cmds.setAttr(rig_joints.get('right_wrist_jnt') + '.type', 12)  # Elbow
    cmds.setAttr(left_forearm_jnt + '.type', 18)  # Other
    cmds.setAttr(right_forearm_jnt + '.type', 18)  # Other
    cmds.setAttr(left_forearm_jnt + '.otherType', 'Forearm', type='string')  # Other
    cmds.setAttr(right_forearm_jnt + '.otherType', 'Forearm', type='string')  # Other
    # Left Fingers
    cmds.setAttr(rig_joints.get('left_thumb01_jnt') + '.type', 14)  # Thumb
    cmds.setAttr(rig_joints.get('left_thumb02_jnt') + '.type', 14)  # Thumb
    cmds.setAttr(rig_joints.get('left_thumb03_jnt') + '.type', 14)  # Thumb
    cmds.setAttr(rig_joints.get('left_index01_jnt') + '.type', 19)  # Index Finger
    cmds.setAttr(rig_joints.get('left_index02_jnt') + '.type', 19)  # Index Finger
    cmds.setAttr(rig_joints.get('left_index03_jnt') + '.type', 19)  # Index Finger
    cmds.setAttr(rig_joints.get('left_middle01_jnt') + '.type', 20)  # Middle Finger
    cmds.setAttr(rig_joints.get('left_middle02_jnt') + '.type', 20)  # Middle Finger
    cmds.setAttr(rig_joints.get('left_middle03_jnt') + '.type', 20)  # Middle Finger
    cmds.setAttr(rig_joints.get('left_ring01_jnt') + '.type', 21)  # Ring Finger
    cmds.setAttr(rig_joints.get('left_ring02_jnt') + '.type', 21)  # Ring Finger
    cmds.setAttr(rig_joints.get('left_ring03_jnt') + '.type', 21)  # Ring Finger
    cmds.setAttr(rig_joints.get('left_pinky01_jnt') + '.type', 22)  # Pinky Finger
    cmds.setAttr(rig_joints.get('left_pinky02_jnt') + '.type', 22)  # Pinky Finger
    cmds.setAttr(rig_joints.get('left_pinky03_jnt') + '.type', 22)  # Pinky Finger
    # Right Fingers
    cmds.setAttr(rig_joints.get('right_thumb01_jnt') + '.type', 14)  # Thumb
    cmds.setAttr(rig_joints.get('right_thumb02_jnt') + '.type', 14)  # Thumb
    cmds.setAttr(rig_joints.get('right_thumb03_jnt') + '.type', 14)  # Thumb
    cmds.setAttr(rig_joints.get('right_index01_jnt') + '.type', 19)  # Index Finger
    cmds.setAttr(rig_joints.get('right_index02_jnt') + '.type', 19)  # Index Finger
    cmds.setAttr(rig_joints.get('right_index03_jnt') + '.type', 19)  # Index Finger
    cmds.setAttr(rig_joints.get('right_middle01_jnt') + '.type', 20)  # Middle Finger
    cmds.setAttr(rig_joints.get('right_middle02_jnt') + '.type', 20)  # Middle Finger
    cmds.setAttr(rig_joints.get('right_middle03_jnt') + '.type', 20)  # Middle Finger
    cmds.setAttr(rig_joints.get('right_ring01_jnt') + '.type', 21)  # Ring Finger
    cmds.setAttr(rig_joints.get('right_ring02_jnt') + '.type', 21)  # Ring Finger
    cmds.setAttr(rig_joints.get('right_ring03_jnt') + '.type', 21)  # Ring Finger
    cmds.setAttr(rig_joints.get('right_pinky01_jnt') + '.type', 22)  # Pinky Finger
    cmds.setAttr(rig_joints.get('right_pinky02_jnt') + '.type', 22)  # Pinky Finger
    cmds.setAttr(rig_joints.get('right_pinky03_jnt') + '.type', 22)  # Pinky Finger
    """

    # Creates game skeleton (No Segment Scale Compensate)
    if settings.get('using_no_ssc_skeleton'):
        new_skeleton_suffix = 'game'
        duplicated_joints, game_root_jnt = generate_no_ssc_skeleton(new_skeleton_suffix, jnt_suffix='jnt',
                                                                    skeleton_root=rig_joints_default.get('main_jnt'))

        attach_no_ssc_skeleton(game_root_jnt,
                               rig_joints_default.get('main_jnt'),
                               main_ctrl, new_skeleton_suffix)

    # ################ Store Created Joints #################
    rig_joints_default['left_forearm_jnt'] = left_forearm_jnt
    rig_joints_default['right_forearm_jnt'] = right_forearm_jnt

    for obj in rig_joints:
        rig_joints_default[obj] = rig_joints.get(obj)

    # ################ Attach Metadata to Main Control #################
    cmds.addAttr(main_ctrl, ln='metadata', dataType='string')
    metadata_dict = {'worldspace_ik_orient': settings.get('worldspace_ik_orient'),
                     'uniform_ctrl_orient': settings.get('uniform_ctrl_orient'),
                     'using_no_ssc_skeleton': settings.get('using_no_ssc_skeleton'),
                     'skeleton_root': str(rig_joints_default.get('main_jnt')),
                     }
    cmds.setAttr(main_ctrl + '.metadata', json.dumps(metadata_dict, indent=4), typ='string')

    # ################# Clean Selection & Print Feedback #################
    cmds.select(d=True)
    unique_message = '<' + str(random.random()) + '>'
    cmds.inViewMessage(
        amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">Control Rig'
                             '</span><span style=\"color:#FFFFFF;\"> has been generated. Enjoy!</span>',
        pos='botLeft', fade=True, alpha=.9)

    # ################# Start of Extra Debugging Commands #################
    if data_biped.debugging and data_biped.debugging_post_code:
        # Case Specific Debugging Options
        debugging_auto_breathing = False  # Auto activates breathing Time
        debugging_display_lra = False
        debugging_ikfk_jnts_visible = False
        debugging_offset_ctrls_visible = False
        debugging_annotate = False
        debugging_show_fk_fingers = False
        debugging_show_fk_controls = False
        debugging_show_fk_spine = False

        if debugging_show_fk_spine:
            cmds.setAttr(cog_ctrl + '.spineInfluenceSwitch', 0)

        if debugging_ikfk_jnts_visible:
            make_visible_obj = [hip_switch_jnt,  # Makes Hip IK/FK joints visible
                                left_clavicle_switch_jnt,
                                right_clavicle_switch_jnt]
            for obj in make_visible_obj:
                cmds.setAttr(obj + '.v', 1)

            cmds.setAttr(left_clavicle_switch_jnt + '.v', 1)
            cmds.setAttr(right_clavicle_switch_jnt + '.v', 1)

        if debugging_offset_ctrls_visible:
            cmds.setAttr(left_wrist_ik_ctrl + '.showOffsetCtrl', 1)
            cmds.setAttr(right_wrist_ik_ctrl + '.showOffsetCtrl', 1)
            cmds.setAttr(left_foot_ik_ctrl + '.showOffsetCtrl', 1)
            cmds.setAttr(right_foot_ik_ctrl + '.showOffsetCtrl', 1)
            cmds.setAttr(chest_ribbon_ctrl + '.showOffsetCtrl', 1)
            cmds.setAttr(chest_ribbon_ctrl + '.showAdjustmentControls', 1)
            cmds.setAttr(cog_ctrl + '.showOffsetCtrl', 1)
            cmds.setAttr(hip_ctrl + '.showOffsetCtrl', 1)
            cmds.setAttr(head_ctrl + '.showOffsetCtrl', 1)

        # Annotate Debugging Elements:
        if debugging_annotate:
            annotate_objs = [right_elbow_ik_ctrl,
                             left_elbow_ik_ctrl,
                             rig_joints.get('right_elbow_jnt'),
                             rig_joints.get('left_elbow_jnt'),
                             ]

            # Original WS_POS
            for obj in annotate_objs:
                obj_pos = cmds.xform(obj, q=True, ws=True, t=True)
                ws_x_pos_text = 'WS-X: {:.2f}'.format(round(obj_pos[0], 2))
                ws_y_pos_text = 'WS-Y: {:.2f}'.format(round(obj_pos[1], 2))
                ws_z_pos_text = 'WS-Z: {:.2f}'.format(round(obj_pos[2], 2))

                ann_holder = cmds.spaceLocator(name=obj + '_ann_loc')
                cmds.xform(ann_holder[0], ws=True, t=obj_pos)
                annotate = cmds.annotate(ann_holder, tx=obj, p=(obj_pos[0], obj_pos[1] + 5, obj_pos[2]))
                annotate_x = cmds.annotate(ann_holder, tx=ws_x_pos_text, p=(obj_pos[0], obj_pos[1] + 4, obj_pos[2]))
                annotate_y = cmds.annotate(ann_holder, tx=ws_y_pos_text, p=(obj_pos[0], obj_pos[1] + 3, obj_pos[2]))
                annotate_z = cmds.annotate(ann_holder, tx=ws_z_pos_text, p=(obj_pos[0], obj_pos[1] + 2, obj_pos[2]))
                cmds.setAttr(annotate + '.displayArrow', 0)
                cmds.setAttr(annotate_x + '.displayArrow', 0)
                cmds.setAttr(annotate_y + '.displayArrow', 0)
                change_viewport_color(annotate, (1, 0, 1))
                change_viewport_color(annotate_x, (1, 0, 0))
                change_viewport_color(annotate_y, (0, 1, 0))
                change_viewport_color(annotate_z, (0, 0, 1))
                annotation_transforms = [cmds.listRelatives(annotate, parent=True),
                                         cmds.listRelatives(annotate_x, parent=True),
                                         cmds.listRelatives(annotate_y, parent=True),
                                         cmds.listRelatives(annotate_z, parent=True)]
                cmds.parent(ann_holder, obj)
                cmds.parent(annotate, ann_holder, s=True)
                cmds.parent(annotate_x, ann_holder, s=True)
                cmds.parent(annotate_y, ann_holder, s=True)
                cmds.parent(annotate_z, ann_holder, s=True)
                for empty_trans in annotation_transforms:
                    cmds.delete(empty_trans)

            # Original OS Rot
            annotate_objs = [rig_joints.get('left_shoulder_jnt'),
                             rig_joints.get('right_shoulder_jnt')]

            for obj in annotate_objs:
                obj_rot = cmds.xform(obj, q=True, os=True, ro=True)
                obj_pos = cmds.xform(obj, q=True, ws=True, t=True)
                ws_x_rot_text = 'OS-R-X: {:.2f}'.format(round(obj_rot[0], 2))
                ws_y_rot_text = 'OS-R-Y: {:.2f}'.format(round(obj_rot[1], 2))
                ws_z_rot_text = 'OS-R-Z: {:.2f}'.format(round(obj_rot[2], 2))

                ann_holder = cmds.spaceLocator(name=obj + '_ann_loc')
                cmds.xform(ann_holder[0], ws=True, t=obj_pos)
                annotate = cmds.annotate(ann_holder, tx=obj, p=(obj_pos[0], obj_pos[1] + 5, obj_pos[2]))
                annotate_x = cmds.annotate(ann_holder, tx=ws_x_rot_text, p=(obj_pos[0], obj_pos[1] + 4, obj_pos[2]))
                annotate_y = cmds.annotate(ann_holder, tx=ws_y_rot_text, p=(obj_pos[0], obj_pos[1] + 3, obj_pos[2]))
                annotate_z = cmds.annotate(ann_holder, tx=ws_z_rot_text, p=(obj_pos[0], obj_pos[1] + 2, obj_pos[2]))
                cmds.setAttr(annotate + '.displayArrow', 0)
                cmds.setAttr(annotate_x + '.displayArrow', 0)
                cmds.setAttr(annotate_y + '.displayArrow', 0)
                change_viewport_color(annotate, (1, 0, 1))
                change_viewport_color(annotate_x, (1, 0, 0))
                change_viewport_color(annotate_y, (0, 1, 0))
                change_viewport_color(annotate_z, (0, 0, 1))
                annotation_transforms = [cmds.listRelatives(annotate, parent=True),
                                         cmds.listRelatives(annotate_x, parent=True),
                                         cmds.listRelatives(annotate_y, parent=True),
                                         cmds.listRelatives(annotate_z, parent=True)]
                cmds.parent(ann_holder, obj)
                cmds.parent(annotate, ann_holder, s=True)
                cmds.parent(annotate_x, ann_holder, s=True)
                cmds.parent(annotate_y, ann_holder, s=True)
                cmds.parent(annotate_z, ann_holder, s=True)
                for empty_trans in annotation_transforms:
                    cmds.delete(empty_trans)
                logger.debug(str(ann_holder))

        if debugging_auto_breathing:
            cmds.setAttr(main_ctrl + '.breathingInfluence', 1)

        if debugging_display_lra:
            try:
                all_jnts = cmds.ls(type='joint')
                for jnt in all_jnts:
                    cmds.setAttr(jnt + ".displayLocalAxis", 1)
            except Exception as e:
                logger.debug(str(e))

        if debugging_show_fk_fingers:
            cmds.setAttr(left_fingers_ctrl + '.showFkFingerCtrls', 1)
            cmds.setAttr(right_fingers_ctrl + '.showFkFingerCtrls', 1)

        if debugging_show_fk_controls:
            cmds.setAttr(left_leg_switch + '.influenceSwitch', 0)
            cmds.setAttr(right_leg_switch + '.influenceSwitch', 0)
            cmds.setAttr(left_arm_switch + '.influenceSwitch', 0)
            cmds.setAttr(right_arm_switch + '.influenceSwitch', 0)

    # ################# End of Extra Debugging Commands #################

    # End of Create Base Rig Controls


def build_biped_rig(create_rig_ctrls=True, debugging=True):
    """
    Creates a rig without the GUI. Helpful for when debugging or changing the rig.
    Args:
        create_rig_ctrls: Whether it should generate the controls after creating the proxy
        debugging (bool): Whether debugging mode should be activated

    """
    # Settings
    biped_obj = GTBipedRiggerData()
    biped_obj.debugging = debugging
    biped_obj.debugging_force_new_scene = True
    biped_obj.settings['using_no_ssc_skeleton'] = True
    biped_obj.settings['proxy_limits'] = True
    biped_obj.settings['uniform_ctrl_orient'] = True
    biped_obj.settings['worldspace_ik_orient'] = False
    biped_obj.settings['simplify_spine'] = True

    # Get/Set Camera Pos/Rot
    if biped_obj.debugging and biped_obj.debugging_force_new_scene:
        persp_pos = cmds.getAttr('persp.translate')[0]
        persp_rot = cmds.getAttr('persp.rotate')[0]
        cmds.file(new=True, force=True)
        if biped_obj.debugging_keep_cam_transforms:
            cmds.viewFit(all=True)
            cmds.setAttr('persp.tx', persp_pos[0])
            cmds.setAttr('persp.ty', persp_pos[1])
            cmds.setAttr('persp.tz', persp_pos[2])
            cmds.setAttr('persp.rx', persp_rot[0])
            cmds.setAttr('persp.ry', persp_rot[1])
            cmds.setAttr('persp.rz', persp_rot[2])

    # Create Proxy
    create_proxy(biped_obj)

    # Use Proxy Template
    biped_obj.debugging_import_proxy = True
    import gt_rigger_biped_gui
    if biped_obj.debugging_import_proxy:
        gt_rigger_biped_gui.import_biped_proxy_pose(debugging=biped_obj.debugging_import_proxy,
                                                    debugging_path=biped_obj.debugging_import_path)

    # Create Controls
    if create_rig_ctrls:
        create_controls(biped_obj)


# Test it
if __name__ == '__main__':
    build_biped_rig(create_rig_ctrls=True, debugging=True)
