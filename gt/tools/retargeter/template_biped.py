"""
Template for Human Biped
"""

import gt.tools.retargeter.retargeter_constants as tools_rt_const
import gt.tools.retargeter.retargeter_framework as tools_rt_frm
import maya.cmds as cmds
import pathlib
import logging
import os


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_biped_definition(
    add_fingers=True, add_fk_arms=True, add_ik_arms=False, add_fk_legs=False, add_ik_legs=True, add_visibility=False
):
    """
    Creates a biped definition based on a biped character created using "tools.auto_rigger"
    Args:
        add_fingers (bool, optional): If True, finger links will be included in the definition.
        add_fk_arms (bool, optional): If True, FK arm links will be included in the definition.
        add_ik_arms (bool, optional): If True, IK arm links will be included in the definition.
        add_fk_legs (bool, optional): If True, FK leg links will be included in the definition.
        add_ik_legs (bool, optional): If True, IK leg links will be included in the definition.
        add_visibility (bool, optional): If True, a visibility links will be included in the definition.
                                         Not as a driven element, but as skip to store set attributes.

    Returns:
        RetargeterDefinition: A definition preconfigured with biped links and properties.
    """
    biped_definition = tools_rt_frm.RetargeterDefinition()

    initial_links = {
        "C_cog_CTRL": tools_rt_frm.TargetingMethods.position_rotation,
        "C_head_CTRL": tools_rt_frm.TargetingMethods.rotation,
        # Center
        "C_spine01_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "C_spine02_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "C_spine03_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "C_neck01_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "C_neck02_CTRL": tools_rt_frm.TargetingMethods.rotation,
    }
    fingers = {
        # Left Fingers
        "L_fingers_CTRL": tools_rt_frm.TargetingMethods.skip,
        "L_thumb01_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "L_thumb02_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "L_thumb03_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "L_index01_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "L_index02_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "L_index03_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "L_middle01_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "L_middle02_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "L_middle03_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "L_ring01_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "L_ring02_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "L_ring03_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "L_pinky01_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "L_pinky02_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "L_pinky03_CTRL": tools_rt_frm.TargetingMethods.rotation,
        # Right Fingers
        "R_fingers_CTRL": tools_rt_frm.TargetingMethods.skip,
        "R_thumb01_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "R_thumb02_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "R_thumb03_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "R_index01_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "R_index02_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "R_index03_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "R_middle01_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "R_middle02_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "R_middle03_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "R_ring01_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "R_ring02_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "R_ring03_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "R_pinky01_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "R_pinky02_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "R_pinky03_CTRL": tools_rt_frm.TargetingMethods.rotation,
    }
    arms_fk = {
        # Left Arm
        "L_arm_CTRL": tools_rt_frm.TargetingMethods.skip,
        "L_clavicle_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "L_upperArm_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "L_lowerArm_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "L_hand_CTRL": tools_rt_frm.TargetingMethods.rotation,
        # Right Arm
        "R_arm_CTRL": tools_rt_frm.TargetingMethods.skip,
        "R_clavicle_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "R_upperArm_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "R_lowerArm_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "R_hand_CTRL": tools_rt_frm.TargetingMethods.rotation,
    }
    arms_ik = {
        # Left Arm
        "L_arm_CTRL": tools_rt_frm.TargetingMethods.skip,
        "L_lowerArm_IK_CTRL": tools_rt_frm.TargetingMethods.offset,
        "L_hand_IK_CTRL": tools_rt_frm.TargetingMethods.position_rotation,
        # Right Arm
        "R_arm_CTRL": tools_rt_frm.TargetingMethods.skip,
        "R_lowerArm_IK_CTRL": tools_rt_frm.TargetingMethods.offset,
        "R_hand_IK_CTRL": tools_rt_frm.TargetingMethods.position_rotation,
    }
    legs_fk = {
        # Left Leg FK
        "L_leg_CTRL": tools_rt_frm.TargetingMethods.skip,
        "L_upperLeg_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "L_lowerLeg_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "L_foot_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "L_ball_CTRL": tools_rt_frm.TargetingMethods.rotation,
        # Right Leg FL
        "R_leg_CTRL": tools_rt_frm.TargetingMethods.skip,
        "R_upperLeg_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "R_lowerLeg_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "R_foot_CTRL": tools_rt_frm.TargetingMethods.rotation,
        "R_ball_CTRL": tools_rt_frm.TargetingMethods.rotation,
    }
    legs_ik = {
        # Left Leg IK
        "L_leg_CTRL": tools_rt_frm.TargetingMethods.skip,
        "L_lowerLeg_IK_CTRL": tools_rt_frm.TargetingMethods.offset,
        "L_foot_IK_CTRL": tools_rt_frm.TargetingMethods.position_rotation,
        "L_toe_IK_CTRL": tools_rt_frm.TargetingMethods.rotation,
        # Right Leg IK
        "R_leg_CTRL": tools_rt_frm.TargetingMethods.skip,
        "R_lowerLeg_IK_CTRL": tools_rt_frm.TargetingMethods.offset,
        "R_foot_IK_CTRL": tools_rt_frm.TargetingMethods.position_rotation,
        "R_toe_IK_CTRL": tools_rt_frm.TargetingMethods.rotation,
    }
    visibility = {
        "C_visibility_CTRL": tools_rt_frm.TargetingMethods.skip,
    }

    if add_fk_arms:
        initial_links.update(arms_fk)
    if add_ik_arms:
        initial_links.update(arms_ik)
    if add_fingers:
        initial_links.update(fingers)
    if add_fk_legs:
        initial_links.update(legs_fk)
    if add_ik_legs:
        initial_links.update(legs_ik)
    if add_visibility:
        initial_links.update(visibility)

    # Add Links
    for target, method in initial_links.items():
        new_link = tools_rt_frm.TargetingLink(target=target, method=method)
        biped_definition.add_link(new_link)
        # Adjust Legs Starting Values
        if target.endswith("_leg_CTRL"):
            new_link.set_target_data({"influenceSwitch": 1})
        # Adjust Finger Visibility Starting Values
        if add_fingers and target.endswith("_fingers_CTRL"):
            new_link.set_target_data({"showFkFingerCtrls": 1})

    return biped_definition


def create_biped_definition_with_self_as_source(
    target_path, add_fingers=True, add_fk_arms=True, add_ik_arms=False, add_fk_legs=False, add_ik_legs=True
):
    """
    Creates a biped definition and sets the sources of the links to match the generic ROM elements.
    Args:
        target_path (str): A path to the target rig.
        add_fingers (bool, optional): If True, finger links will be included in the definition.
        add_fk_arms (bool, optional): If True, FK arm links will be included in the definition.
        add_ik_arms (bool, optional): If True, IK arm links will be included in the definition.
        add_fk_legs (bool, optional): If True, FK leg links will be included in the definition.
        add_ik_legs (bool, optional): If True, IK leg links will be included in the definition.

    Returns:
        RetargeterDefinition: A definition preconfigured with biped links and properties.
    """
    biped_definition = create_biped_definition(
        add_fingers=add_fingers,
        add_fk_arms=add_fk_arms,
        add_ik_arms=add_ik_arms,
        add_fk_legs=add_fk_legs,
        add_ik_legs=add_ik_legs,
    )
    # Define Source File
    source_file = os.path.join(tools_rt_const.RetargeterConstants.DEFAULT_REFERENCES_FOLDER, "male_to_itself.fbx")
    biped_definition.set_source_path(source_file)
    # Define Target File
    biped_definition.set_target_path(target_path)

    # Define Definition Links
    links_target_source = {
        "C_cog_CTRL": "C_hips_JNT",
        "C_head_CTRL": "C_head_JNT",
        # Center
        "C_spine01_CTRL": "C_spine01_JNT",
        "C_spine02_CTRL": "C_spine02_JNT",
        "C_spine03_CTRL": "C_spine03_JNT",
        "C_neck01_CTRL": "C_neck01_JNT",
        "C_neck02_CTRL": "C_neck02_JNT",
    }
    arms_fk = {
        # Left Arm
        "L_arm_CTRL": "",
        "L_clavicle_CTRL": "L_clavicle_JNT",
        "L_upperArm_CTRL": "L_upperArm_JNT",
        "L_lowerArm_CTRL": "L_lowerArm_JNT",
        "L_hand_CTRL": "L_hand_JNT",
        # Right Arm
        "R_arm_CTRL": "",
        "R_clavicle_CTRL": "R_clavicle_JNT",
        "R_upperArm_CTRL": "R_upperArm_JNT",
        "R_lowerArm_CTRL": "R_lowerArm_JNT",
        "R_hand_CTRL": "R_hand_JNT",
    }
    arms_ik = {
        # Left Arm
        "L_arm_CTRL": "",
        "L_lowerArm_IK_CTRL": "L_upperArm_JNT",
        "L_hand_IK_CTRL": "L_hand_JNT",
        # Right Arm
        "R_arm_CTRL": "",
        "R_lowerArm_IK_CTRL": "R_upperArm_JNT",
        "R_hand_IK_CTRL": "R_hand_JNT",
    }
    fingers = {
        # Left Fingers
        "L_thumb01_CTRL": "L_index01_JNT",
        "L_thumb02_CTRL": "L_thumb02_JNT",
        "L_thumb03_CTRL": "L_thumb03_JNT",
        "L_index01_CTRL": "L_index01_JNT",
        "L_index02_CTRL": "L_index02_JNT",
        "L_index03_CTRL": "L_index03_JNT",
        "L_middle01_CTRL": "L_middle01_JNT",
        "L_middle02_CTRL": "L_middle02_JNT",
        "L_middle03_CTRL": "L_middle03_JNT",
        "L_ring01_CTRL": "L_ring01_JNT",
        "L_ring02_CTRL": "L_ring02_JNT",
        "L_ring03_CTRL": "L_ring03_JNT",
        "L_pinky01_CTRL": "L_pinky01_JNT",
        "L_pinky02_CTRL": "L_pinky02_JNT",
        "L_pinky03_CTRL": "L_pinky03_JNT",
        # Right Fingers
        "R_thumb01_CTRL": "R_index01_JNT",
        "R_thumb02_CTRL": "R_thumb02_JNT",
        "R_thumb03_CTRL": "R_thumb03_JNT",
        "R_index01_CTRL": "R_index01_JNT",
        "R_index02_CTRL": "R_index02_JNT",
        "R_index03_CTRL": "R_index03_JNT",
        "R_middle01_CTRL": "R_middle01_JNT",
        "R_middle02_CTRL": "R_middle02_JNT",
        "R_middle03_CTRL": "R_middle03_JNT",
        "R_ring01_CTRL": "R_ring01_JNT",
        "R_ring02_CTRL": "R_ring02_JNT",
        "R_ring03_CTRL": "R_ring03_JNT",
        "R_pinky01_CTRL": "R_pinky01_JNT",
        "R_pinky02_CTRL": "R_pinky02_JNT",
        "R_pinky03_CTRL": "R_pinky03_JNT",
    }

    legs_fk = {
        # Left Leg IK
        "L_leg_CTRL": "",
        "L_upperLeg_CTRL": "L_upperLeg_JNT",
        "L_lowerLeg_CTRL": "L_lowerLeg_JNT",
        "L_foot_CTRL": "L_foot_JNT",
        "L_ball_CTRL": "L_ball_JNT",
        # Right Leg IK
        "R_leg_CTRL": "",
        "R_upperLeg_CTRL": "R_upperLeg_JNT",
        "R_lowerLeg_CTRL": "R_lowerLeg_JNT",
        "R_foot_CTRL": "R_foot_JNT",
        "R_ball_CTRL": "R_ball_JNT",
    }
    legs_ik = {
        # Left Leg IK
        "L_leg_CTRL": "",
        "L_lowerLeg_IK_CTRL": "L_upperLeg_JNT",
        "L_foot_IK_CTRL": "L_foot_JNT",
        "L_toe_IK_CTRL": "L_ball_JNT",
        # Right Leg IK
        "R_leg_CTRL": "",
        "R_lowerLeg_IK_CTRL": "R_upperLeg_JNT",
        "R_foot_IK_CTRL": "R_foot_JNT",
        "R_toe_IK_CTRL": "R_ball_JNT",
    }

    if add_fk_arms:
        links_target_source.update(arms_fk)
    if add_ik_arms:
        links_target_source.update(arms_ik)
    if add_fingers:
        links_target_source.update(fingers)
    if add_fk_legs:
        links_target_source.update(legs_fk)
    if add_ik_legs:
        links_target_source.update(legs_ik)

    for a_target, a_source in links_target_source.items():
        link = biped_definition.get_links_from_target(target=a_target)[0]
        if not a_source:
            continue
        link.set_source(source=a_source)

    # Setup Starting Transforms
    source_setup = biped_definition.get_addon_source_setup()
    comparison_loc_dict = {"tx": -125.0, "tz": 75.0}  # A & B Comparison
    source_setup.set_comparison_loc_data(comparison_loc_dict)

    return biped_definition


def load_retargeter_definitions_from_directory(directory_path):
    """
    Loads and sets up RetargeterDefinition objects from matched FBX/definition file pairs in the given directory.
    It's expected that they both have the same name. e.g. "male_poses_01.fbx" and "male_poses_01.rtg"
    The definition file is used as data for the retarget definition and the FBX becomes its source.

    Args:
        directory_path (str or Path): Directory containing .rtg or legacy .json files and matching .fbx files.

    Returns:
        dict[str, RetargeterDefinition]: Dictionary mapping base filenames (without extension)
                                         to fully set up RetargeterDefinition instances.
    """
    directory_path = pathlib.Path(directory_path)
    retargeter_definitions = {}

    # Find all definition and fbx files
    definition_files = {f.stem: f for f in directory_path.glob("*.json")}
    definition_files.update({f.stem: f for f in directory_path.glob("*.rtg")})
    fbx_files = {f.stem: f for f in directory_path.glob("*.fbx")}

    # Intersect keys to find valid pairs
    valid_keys = set(definition_files) & set(fbx_files)

    for key in valid_keys:
        definition_path = definition_files[key]
        fbx_path = fbx_files[key]

        _definition_dict = core_io.read_json_dict(path=str(definition_path))

        definition = tools_rt_frm.RetargeterDefinition()
        definition.read_data_from_dict(_definition_dict)
        definition.set_source_path(str(fbx_path))

        retargeter_definitions[key] = definition

    return retargeter_definitions


# ROM Long Skin Tester --------------------------------------------------------
def rom_create_biped_definition_with_long_skin_tester(target_path, add_fingers=True):
    """
    Creates a biped definition and sets the sources of the links to match the generic ROM elements.
    Args:
        target_path (str): A path to the target rig.
        add_fingers (bool): If True, finger links will be included in the definition.

    Returns:

    """
    biped_definition = create_biped_definition(add_fingers=add_fingers)
    # Define Source File
    source_file = r"Z:\maya\external\assets\retargeter_references\rom_skin_tester_01.fbx"
    biped_definition.set_source_path(source_file)
    # Define Target File
    biped_definition.set_target_path(target_path)

    # Define Definition Links
    links_target_source = {
        "C_cog_CTRL": "GM_Hips",
        "C_head_CTRL": "GM_Head",
        # Center
        "C_spine01_CTRL": "GM_Spine",
        "C_spine02_CTRL": "GM_Spine1",
        "C_spine03_CTRL": "GM_Spine2",
        "C_neck01_CTRL": "GM_Neck",
        "C_neck02_CTRL": "GM_Neck",  # As Neck1, so it's ignored.
        # Left Limbs
        "L_clavicle_CTRL": "GM_LeftShoulder",
        "L_upperArm_CTRL": "GM_LeftArm",
        "L_lowerArm_CTRL": "GM_LeftForeArm",
        "L_hand_CTRL": "GM_LeftHand",
        # Left Leg IK
        "L_leg_CTRL": "",
        "L_lowerLeg_IK_CTRL": "GM_LeftLeg",
        "L_foot_IK_CTRL": "GM_LeftFoot",
        "L_toe_IK_CTRL": "GM_LeftToeBase",
        # Right Arm
        "R_clavicle_CTRL": "GM_RightShoulder",
        "R_upperArm_CTRL": "GM_RightArm",
        "R_lowerArm_CTRL": "GM_RightForeArm",
        "R_hand_CTRL": "GM_RightHand",
        # Right Leg IK
        "R_leg_CTRL": "",
        "R_lowerLeg_IK_CTRL": "GM_RightLeg",
        "R_foot_IK_CTRL": "GM_RightFoot",
        "R_toe_IK_CTRL": "GM_RightToeBase",
        # Left Fingers
        "L_thumb01_CTRL": "GM_LeftHandThumb1",
        "L_thumb02_CTRL": "GM_LeftHandThumb2",
        "L_thumb03_CTRL": "GM_LeftHandThumb3",
        "L_index01_CTRL": "GM_LeftHandIndex1",
        "L_index02_CTRL": "GM_LeftHandIndex2",
        "L_index03_CTRL": "GM_LeftHandIndex3",
        "L_middle01_CTRL": "GM_LeftHandMiddle1",
        "L_middle02_CTRL": "GM_LeftHandMiddle2",
        "L_middle03_CTRL": "GM_LeftHandMiddle3",
        "L_ring01_CTRL": "GM_LeftHandRing1",
        "L_ring02_CTRL": "GM_LeftHandRing2",
        "L_ring03_CTRL": "GM_LeftHandRing3",
        "L_pinky01_CTRL": "GM_LeftHandPinky1",
        "L_pinky02_CTRL": "GM_LeftHandPinky2",
        "L_pinky03_CTRL": "GM_LeftHandPinky3",
        # Right Fingers
        "R_thumb01_CTRL": "GM_RightHandThumb1",
        "R_thumb02_CTRL": "GM_RightHandThumb2",
        "R_thumb03_CTRL": "GM_RightHandThumb3",
        "R_index01_CTRL": "GM_RightHandIndex1",
        "R_index02_CTRL": "GM_RightHandIndex2",
        "R_index03_CTRL": "GM_RightHandIndex3",
        "R_middle01_CTRL": "GM_RightHandMiddle1",
        "R_middle02_CTRL": "GM_RightHandMiddle2",
        "R_middle03_CTRL": "GM_RightHandMiddle3",
        "R_ring01_CTRL": "GM_RightHandRing1",
        "R_ring02_CTRL": "GM_RightHandRing2",
        "R_ring03_CTRL": "GM_RightHandRing3",
        "R_pinky01_CTRL": "GM_RightHandPinky1",
        "R_pinky02_CTRL": "GM_RightHandPinky2",
        "R_pinky03_CTRL": "GM_RightHandPinky3",
    }

    for a_target, a_source in links_target_source.items():
        link = biped_definition.get_links_from_target(target=a_target)[0]
        if not a_source:
            continue
        link.set_source(source=a_source)

        # Extra Pose Data ---------------------------------------------------
        if a_target == "C_cog_CTRL":
            pose = {"tz": 3.1, "rx": 2.45}
            link.set_target_data(pose)
        if a_target == "C_neck01_CTRL":
            pose = {"rz": -1.8}
            link.set_target_data(pose)
        if a_target.endswith("_clavicle_CTRL"):
            pose = {"rz": -0.6}
            link.set_target_data(pose)
        if a_target.endswith("_upperArm_CTRL"):
            pose = {"ry": 0.65}
            link.set_target_data(pose)
        if a_target.endswith("_lowerArm_CTRL"):
            pose = {"rz": -4}
            link.set_target_data(pose)
        if a_target.endswith("_hand_CTRL"):
            pose = {"ry": 4.8, "rz": -3}
            link.set_target_data(pose)
        if a_target.endswith("_thumb01_CTRL"):
            pose = {"ry": 8.4, "rz": 6.2}
            link.set_target_data(pose)

    # Setup Starting Transforms
    source_setup = biped_definition.get_addon_source_setup()
    offset_transform_dict = {"tz": -1.765, "sx": 101.365, "sy": 101.365, "sz": 101.365}  # Scale and move to pose
    comparison_loc_dict = {"tx": -125.0, "tz": 75.0}  # A & B Comparison

    source_setup.set_transform_data(offset_transform_dict)
    source_setup.set_comparison_loc_data(comparison_loc_dict)

    return biped_definition


def rom_add_long_skin_tester_biped_pose_data_to_definition(biped_definition):
    """
    Adds the data necessary to align the male biped rig to the skin tester ROM file.
    Args:
        biped_definition (RetargeterDefinition): Add male pose data to a biped definition.
    """
    links = biped_definition.get_links()
    for link in links:
        a_target = link.get_target()

        # Extra Pose Data ---------------------------------------------------
        if a_target == "C_cog_CTRL":
            pose = {"tz": 3.1, "rx": 2.45}
            link.set_target_data(pose)
        if a_target == "C_neck01_CTRL":
            pose = {"rz": -1.8}
            link.set_target_data(pose)
        if a_target.endswith("_clavicle_CTRL"):
            pose = {"rz": -0.6}
            link.set_target_data(pose)
        if a_target.endswith("_upperArm_CTRL"):
            pose = {"ry": 0.65}
            link.set_target_data(pose)
        if a_target.endswith("_lowerArm_CTRL"):
            pose = {"rz": -4}
            link.set_target_data(pose)
        if a_target.endswith("_hand_CTRL"):
            pose = {"ry": 4.8, "rz": -3}
            link.set_target_data(pose)
        if a_target.endswith("_thumb01_CTRL"):
            pose = {"ry": 8.4, "rz": 6.2}
            link.set_target_data(pose)

    # Setup Starting Transforms
    source_setup = biped_definition.get_addon_source_setup()
    offset_transform_dict = {"tz": -1.765, "sx": 101.365, "sy": 101.365, "sz": 101.365}  # Scale and move to pose
    comparison_loc_dict = {"tx": -125.0, "tz": 75.0}  # A & B Comparison

    source_setup.set_transform_data(offset_transform_dict)
    source_setup.set_comparison_loc_data(comparison_loc_dict)


def show_dialog_retarget_long_skin_tester_biped_pose():
    """
    Shows a dialog asking for a biped rig file.
    If one is provided, it's retargeted using a reference ROM file
    """
    import gt.ui.file_dialog as ui_file_dialog

    # File Path
    file_path = ui_file_dialog.file_dialog(
        write_mode=False,
        file_filter=tools_rt_const.RetargeterConstants.RETARGET_FILTER,
        ok_caption="Source Rig File",
        cancel_caption="Cancel",
    )
    if not file_path:
        return  # Cancel operation

    biped_rom = os.path.join(tools_rt_const.RetargeterConstants.DEFAULT_REFERENCES_FOLDER, "rom_skin_tester_01.fbx")

    _biped_definition = rom_create_biped_definition_with_long_skin_tester(target_path=file_path, add_fingers=True)
    _biped_definition.set_source_path(biped_rom)
    rom_add_long_skin_tester_biped_pose_data_to_definition(_biped_definition)

    _biped_definition.retarget()
    if cmds.objExists("source:offset"):
        cmds.setAttr("source:offset.bWeight", 1)
    logging.info(f'File retargeted to ROM: "{file_path}".')


if __name__ == "__main__":
    import gt.tests.test_retargeter as test_retargeter
    import gt.core.io as core_io
    import inspect

    # --------------------------------- Get Test File Paths --------------------------------
    cmds.file(new=True, force=True)
    desktop_path = os.path.join(os.path.expanduser(os.getenv("USERPROFILE")), "Desktop")
    module_path = inspect.getfile(test_retargeter)
    module_dir = os.path.dirname(module_path)
    test_data_dir = os.path.join(module_dir, "data")
    rom_a_file = os.path.join(test_data_dir, "rom_a.fbx")
    rom_b_file = os.path.join(test_data_dir, "rom_b.fbx")
    rig_file = os.path.join(test_data_dir, "male_rig.ma")

    from pprint import pprint

    pprint(load_retargeter_definitions_from_directory(r"R:\DccTools\maya\external\assets\auto_rigger_rom_data"))

    # # ------------------------------- Create ROM Definition --------------------------------
    # # Create Definition
    # # a_biped_definition = create_biped_definition(add_fingers=True)
    # a_biped_definition = rom_create_biped_definition_with_long_skin_tester(target_path=rig_file, add_fingers=True)
    #
    # # Set Source/Target
    # a_biped_definition.set_source_path(rom_a_file)  # Comment this out to use full test file
    # # a_biped_definition.set_target_path(rig_file)  # Already set by the definition function (see above)
    #
    # # ------------------------------- Edit Definition Source -------------------------------
    # a_biped_definition.retarget_edit_mode()
    # a_biped_definition.convert_link_fallbacks_to_long()
    # # Se pose manually to simulate user creating a definition.
    # # Not required if using "rom_add_long_skin_tester_biped_pose_data_to_definition".
    # manually_set_pose = True
    # if manually_set_pose:
    #     cmds.currentTime(0)
    #     # Apply Offset Transform Data
    #     cmds.setAttr(f"source:offset.tz", -1.765)
    #     cmds.setAttr(f"source:offset.sx", 101.365)
    #     cmds.setAttr(f"source:offset.sy", 101.365)
    #     cmds.setAttr(f"source:offset.sz", 101.365)
    #     # Apply Comparison Transform Data
    #     cmds.setAttr(f"source:comparison_matrix_B_LOC.tx", -125)
    #     cmds.setAttr(f"source:comparison_matrix_B_LOC.tz", 75)
    #     # Apply Control Transform Data
    #     cmds.setAttr(f"target:C_cog_CTRL.tz", 3.1)
    #     cmds.setAttr(f"target:C_cog_CTRL.rx", 2.45)
    #     cmds.setAttr(f"target:L_clavicle_CTRL.rz", -0.6)
    #     cmds.setAttr(f"target:R_clavicle_CTRL.rz", -0.6)
    #     cmds.setAttr(f"target:L_upperArm_CTRL.ry", 0.65)
    #     cmds.setAttr(f"target:R_upperArm_CTRL.ry", 0.65)
    #     cmds.setAttr(f"target:L_lowerArm_CTRL.rz", -4)
    #     cmds.setAttr(f"target:R_lowerArm_CTRL.rz", -4)
    #     cmds.setAttr(f"target:L_hand_CTRL.ry", 4.8)
    #     cmds.setAttr(f"target:L_hand_CTRL.rz", -3)
    #     cmds.setAttr(f"target:R_hand_CTRL.ry", 4.8)
    #     cmds.setAttr(f"target:R_hand_CTRL.rz", -3)
    #     cmds.setAttr(f"target:L_thumb01_CTRL.ry", 8.5)
    #     cmds.setAttr(f"target:L_thumb01_CTRL.rz", 6.2)
    #     cmds.setAttr(f"target:R_thumb01_CTRL.ry", 8.5)
    #     cmds.setAttr(f"target:R_thumb01_CTRL.rz", 6.2)
    #     cmds.setAttr(f"target:C_neck01_CTRL.rz", -1.8)
    #
    #     # ------------------------------------ Read Functions -----------------------------------
    #     # source_setup = a_biped_definition.get_addon_source_setup()
    #     # source_setup.read_transform_offset_data()  # Reads Main Parent Transform
    #     # source_setup.read_source_skeleton_pose()  # Reads source skeleton TRS
    #     # source_setup.read_comparison_loc_data()  # Reads B comparison position
    #     # a_biped_definition.read_links_target_data()  # Save controls pose
    #     a_biped_definition.read_addons_and_links_scene_data()  # Reads controls pose and addons scene data
    # else:
    #     rom_add_long_skin_tester_biped_pose_data_to_definition(a_biped_definition)
    #
    # # ------------------------------------ Retarget Test ------------------------------------
    # a_biped_definition.retarget_edit_mode(linked_mode=True)
    # # a_biped_definition.set_delete_source_status(True)  # Delete Source After Baking
    # # a_biped_definition.set_source_path(rom_b_file)  # Change to non-t pose file
    # # a_biped_definition.retarget()
    #
    # # ----------------------------------- JSON Output Test ----------------------------------
    # test_json_path = os.path.join(desktop_path, r"retarget_definition.json")
    # definition_as_dict = a_biped_definition.get_definition_as_dict()
    # core_io.write_json(path=test_json_path, data=definition_as_dict)
    #
    # # # Try to re-crete it from JSON file
    # # cmds.file(new=True, force=True)
    # # definition_dict = core_io.read_json_dict(path=test_json_path)
    # # a_clean_definition = tools_rt_frm.RetargeterDefinition()
    # # a_clean_definition.read_data_from_dict(definition_dict)
    # # a_clean_definition.retarget()
