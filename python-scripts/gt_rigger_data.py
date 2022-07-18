"""
GT Rigger Data - Settings and naming conventions for auto rigger scripts
github.com/TrevisanGMW - 2021-12-10

2022-06-28
Added facial and corrective classes

"""
import maya.cmds as cmds
import logging
import copy

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_rigger_data")
logger.setLevel(logging.INFO)

SCRIPT_VERSION_BASE = '1.9.13'
SCRIPT_VERSION_FACIAL = '0.0.18'
SCRIPT_VERSION_CORRECTIVE = '0.0.12'

# General Vars
GRP_SUFFIX = 'grp'
CRV_SUFFIX = 'crv'
JNT_SUFFIX = 'jnt'
PROXY_SUFFIX = 'proxy'
CTRL_SUFFIX = 'ctrl'
AUTO_SUFFIX = 'automation'
MULTIPLY_SUFFIX = 'multiply'
FIRST_SHAPE_SUFFIX = '1st'
SECOND_SHAPE_SUFFIX = '2nd'
LEFT_CTRL_COLOR = (0, .3, 1)  # Soft Blue
RIGHT_CTRL_COLOR = (1, 0, 0)  # Red
CENTER_CTRL_COLOR = (1, 1, 0)  # Yellow
AUTO_CTRL_COLOR = (.6, .2, 1)  # Purple
LEFT_JNT_COLOR = (.2, .6, 1)
RIGHT_JNT_COLOR = (1, .4, .4)
CENTER_JNT_COLOR = (.8, .8, .8)
LEFT_PROXY_COLOR = (.2, .6, 1)
RIGHT_PROXY_COLOR = (1, .4, .4)
CENTER_PROXY_COLOR = (.8, .8, .8)
ALT_PROXY_COLOR = (1, 0, 1)
PROXY_DRIVEN_COLOR = (1, .5, 1)
ROTATE_ORDER_ENUM = 'xyz:yzx:zxy:xzy:yxz:zyx'
CUSTOM_ATTR_SEPARATOR = 'controlBehaviour'


class GTBipedRiggerData:
    # Script Name
    script_name = 'GT Biped Rigger'

    # Version:
    script_version = SCRIPT_VERSION_BASE

    # Permanent Settings
    option_var = 'gt_biped_rigger_base_setup'
    ignore_keys = ['']  # Not to be stored

    # Loaded Elements Dictionary
    elements = {  # General Settings
        'main_proxy_grp': 'rigger_biped_proxy' + '_' + GRP_SUFFIX,
        # Center Elements
        'main_crv': 'root' + '_' + PROXY_SUFFIX,
        'cog_proxy_crv': 'waist' + '_' + PROXY_SUFFIX,
        'spine01_proxy_crv': 'spine01' + '_' + PROXY_SUFFIX,
        'spine02_proxy_crv': 'spine02' + '_' + PROXY_SUFFIX,
        'spine03_proxy_crv': 'spine03' + '_' + PROXY_SUFFIX,
        # 'spine04_proxy_crv': 'spine04' + '_' + PROXY_SUFFIX,
        'spine04_proxy_crv': 'chest' + '_' + PROXY_SUFFIX,
        'neck_base_proxy_crv': 'neckBase' + '_' + PROXY_SUFFIX,
        'neck_mid_proxy_crv': 'neckMid' + '_' + PROXY_SUFFIX,
        'head_proxy_crv': 'head' + '_' + PROXY_SUFFIX,
        'head_end_proxy_crv': 'head' + '_end' + PROXY_SUFFIX.capitalize(),
        'jaw_proxy_crv': 'jaw' + '_' + PROXY_SUFFIX,
        'jaw_end_proxy_crv': 'jaw' + '_end' + PROXY_SUFFIX.capitalize(),
        'hip_proxy_crv': 'pelvis' + '_' + PROXY_SUFFIX,
        # Left Side Elements (No need for prefix, these are automatically added)
        # Right Side Elements are automatically populated, script copies from Left to Right
        'left_eye_proxy_crv': 'eye' + '_' + PROXY_SUFFIX,
        'left_clavicle_proxy_crv': 'clavicle' + '_' + PROXY_SUFFIX,
        'left_shoulder_proxy_crv': 'shoulder' + '_' + PROXY_SUFFIX,
        'left_elbow_proxy_crv': 'elbow' + '_' + PROXY_SUFFIX,
        'left_wrist_proxy_crv': 'wrist' + '_' + PROXY_SUFFIX,
        'left_thumb01_proxy_crv': 'thumb01' + '_' + PROXY_SUFFIX,
        'left_thumb02_proxy_crv': 'thumb02' + '_' + PROXY_SUFFIX,
        'left_thumb03_proxy_crv': 'thumb03' + '_' + PROXY_SUFFIX,
        'left_thumb04_proxy_crv': 'thumb04' + '_end' + PROXY_SUFFIX.capitalize(),
        'left_index01_proxy_crv': 'index01' + '_' + PROXY_SUFFIX,
        'left_index02_proxy_crv': 'index02' + '_' + PROXY_SUFFIX,
        'left_index03_proxy_crv': 'index03' + '_' + PROXY_SUFFIX,
        'left_index04_proxy_crv': 'index04' + '_end' + PROXY_SUFFIX.capitalize(),
        'left_middle01_proxy_crv': 'middle01' + '_' + PROXY_SUFFIX,
        'left_middle02_proxy_crv': 'middle02' + '_' + PROXY_SUFFIX,
        'left_middle03_proxy_crv': 'middle03' + '_' + PROXY_SUFFIX,
        'left_middle04_proxy_crv': 'middle04' + '_end' + PROXY_SUFFIX.capitalize(),
        'left_ring01_proxy_crv': 'ring01' + '_' + PROXY_SUFFIX,
        'left_ring02_proxy_crv': 'ring02' + '_' + PROXY_SUFFIX,
        'left_ring03_proxy_crv': 'ring03' + '_' + PROXY_SUFFIX,
        'left_ring04_proxy_crv': 'ring04' + '_end' + PROXY_SUFFIX.capitalize(),
        'left_pinky01_proxy_crv': 'pinky01' + '_' + PROXY_SUFFIX,
        'left_pinky02_proxy_crv': 'pinky02' + '_' + PROXY_SUFFIX,
        'left_pinky03_proxy_crv': 'pinky03' + '_' + PROXY_SUFFIX,
        'left_pinky04_proxy_crv': 'pinky04' + '_end' + PROXY_SUFFIX.capitalize(),
        'left_hip_proxy_crv': 'hip' + '_' + PROXY_SUFFIX,
        'left_knee_proxy_crv': 'knee' + '_' + PROXY_SUFFIX,
        'left_ankle_proxy_crv': 'ankle' + '_' + PROXY_SUFFIX,
        'left_ball_proxy_crv': 'ball' + '_' + PROXY_SUFFIX,
        'left_toe_proxy_crv': 'toe' + '_' + PROXY_SUFFIX,
        'left_heel_proxy_pivot': 'heel_pivot' + '_' + PROXY_SUFFIX,
        'left_elbow_pv_dir': 'elbow_proxy_poleVecDir',
        'left_elbow_dir_loc': 'elbow_proxy_dirParent',
        'left_elbow_aim_loc': 'elbow_proxy_dirAim',
        'left_elbow_upvec_loc': 'elbow_proxy_dirParentUp',
        'left_elbow_divide_node': 'elbowUp_divide',
        'left_knee_pv_dir': 'knee_proxy_poleVecDir',
        'left_knee_dir_loc': 'knee_proxy_dirParent',
        'left_knee_aim_loc': 'knee_proxy_dirAim',
        'left_knee_upvec_loc': 'knee_proxy_dirParentUp',
        'left_knee_divide_node': 'knee_divide',
        'left_ball_pivot_grp': 'ball_proxy_pivot' + GRP_SUFFIX.capitalize(),
        'left_ankle_ik_reference': 'ankleSwitch_loc',
        'left_knee_ik_reference': 'kneeSwitch_loc',
        'left_elbow_ik_reference': 'elbowSwitch_loc',
        'left_wrist_ik_reference': 'wristSwitch_loc',
        'left_shoulder_ik_reference': 'shoulderSwitch_loc',
    }

    # Auto Populate Control Names (Copy from Left to Right) + Add prefixes
    elements_list = list(elements)
    for item in elements_list:
        if item.startswith('left_'):
            elements[item] = 'left_' + elements.get(item)  # Add "left_" prefix
            elements[item.replace('left_', 'right_')] = elements.get(item).replace('left_', 'right_')  # Add right copy

    # Store Default Values
    def __init__(self):
        self.settings = {'using_no_ssc_skeleton': False,
                         'proxy_limits': False,
                         'offer_heel_roll_positioning': True,
                         'uniform_ctrl_orient': True,
                         'worldspace_ik_orient': False,
                         'simplify_spine': True,
                         }

        self.elements_default = copy.deepcopy(self.elements)
        self.settings_default = copy.deepcopy(self.settings)

    # Create Joints List
    joints_default = {}
    for obj in elements:
        if obj.endswith('_crv'):
            name = elements.get(obj).replace(PROXY_SUFFIX, JNT_SUFFIX).replace('end' + PROXY_SUFFIX.capitalize(),
                                                                               'end' + JNT_SUFFIX.capitalize())
            joints_default[obj.replace('_crv', '_' + JNT_SUFFIX).replace('_proxy', '')] = name
    joints_default['left_forearm_jnt'] = 'left_forearm_jnt'
    joints_default['right_forearm_jnt'] = 'right_forearm_jnt'

    # Reset Persistent Settings Variables
    gui_module = 'gt_rigger_biped_gui'
    entry_function = 'build_gui_auto_biped_rig()'

    # Used to export/import proxy
    proxy_storage_variables = {'file_extension': 'ppose_base',
                               'script_source': 'gt_rigger_biped_version',
                               'export_method': 'gt_rigger_biped_export_method',
                               'attr_name': 'biped_proxy_pose'}

    # Debugging Vars
    debugging = False  # Activates Debugging Mode
    debugging_auto_recreate = True  # Auto deletes proxy/rig before creating
    debugging_force_new_scene = True  # Forces new instance every time
    debugging_keep_cam_transforms = True  # Keeps camera position
    debugging_import_proxy = True  # Auto Imports Proxy
    debugging_import_path = 'C:\\template.ppose'  # Path to auto import
    debugging_bind_rig = False  # Auto Binds Rig
    debugging_bind_geo = 'body_geo'  # Name of the geo to bind
    debugging_bind_heatmap = False  # If not using heatmap, then closest distance
    debugging_post_code = True  # Runs code found at the end of the create controls command


class GTBipedRiggerFacialData:
    # Script Name
    script_name = 'GT Facial Rigger'

    # Version:
    script_version = SCRIPT_VERSION_FACIAL

    # Permanent Settings
    option_var = 'gt_biped_rigger_facial_setup'
    ignore_keys = ['']  # Not to be stored

    # Loaded Elements Dictionary
    elements = {  # Pre Existing Elements
        'main_proxy_grp': 'rigger_facial_proxy' + '_' + GRP_SUFFIX,
        'main_root': 'rigger_facial' + '_' + PROXY_SUFFIX,

        # Center Elements
        'head_crv': 'headRoot' + '_' + PROXY_SUFFIX,
        'jaw_crv': 'jawRoot' + '_' + PROXY_SUFFIX,
        'left_eye_crv': 'eyeRoot_' + PROXY_SUFFIX,

        # Eyelids
        'left_upper_eyelid_crv': 'upperEyelid_' + PROXY_SUFFIX,
        'left_lower_eyelid_crv': 'lowerEyelid_' + PROXY_SUFFIX,

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

        # Tongue
        'base_tongue_crv': 'baseTongue_' + PROXY_SUFFIX,
        'mid_tongue_crv': 'midTongue_' + PROXY_SUFFIX,
        'tip_tongue_crv': 'tipTongue_' + PROXY_SUFFIX,

        # Cheek
        'left_cheek_crv': 'cheek_' + PROXY_SUFFIX,

        # # Nose
        'left_nose_crv': 'nose_' + PROXY_SUFFIX,
    }

    # Auto Populate Control Names (Copy from Left to Right) + Add prefixes
    elements_list = list(elements)
    for item in elements_list:
        if item.startswith('left_'):
            elements[item] = 'left_' + elements.get(item)  # Add "left_" prefix
            elements[item.replace('left_', 'right_')] = elements.get(item).replace('left_', 'right_')  # Add right copy

    # Expected elements for when merging with existing rig
    preexisting_dict = {'neck_base_jnt': 'neckBase_jnt',
                        'head_jnt': 'head_jnt',
                        'jaw_jnt': 'jaw_jnt',
                        'left_eye_jnt': 'left_eye_jnt',
                        'right_eye_jnt': 'right_eye_jnt',
                        'head_ctrl': 'head_ctrl',
                        'jaw_ctrl': 'jaw_ctrl',
                        }

    # Store Default Values
    def __init__(self):
        self.settings = {'find_pre_existing_elements': True,
                         'setup_nose_cheek': False}

        self.elements_default = copy.deepcopy(self.elements)
        self.settings_default = copy.deepcopy(self.settings)

    # Create Joints List
    joints_default = {}
    for obj in elements:
        if obj.endswith('_crv'):
            name = elements.get(obj).replace(PROXY_SUFFIX, JNT_SUFFIX).replace('end' + PROXY_SUFFIX.capitalize(),
                                                                               'end' + JNT_SUFFIX.capitalize())
            joints_default[obj.replace('_crv', '_' + JNT_SUFFIX).replace('_proxy', '')] = name

    # Reset Persistent Settings Variables
    gui_module = 'gt_rigger_facial_gui'
    entry_function = 'build_gui_auto_biped_rig()'

    # Used to export/import proxy
    proxy_storage_variables = {'file_extension': 'ppose_facial',
                               'script_source': 'gt_rigger_facial_version',
                               'export_method': 'gt_rigger_facial_export_method',
                               'attr_name': 'facial_proxy_pose'}

    # Debugging Vars
    debugging = False  # Activates Debugging Mode


class GTBipedRiggerCorrectiveData:
    # Script Name
    script_name = 'GT Corrective Rigger'

    # Version:
    script_version = SCRIPT_VERSION_CORRECTIVE

    # Permanent Settings
    option_var = 'gt_biped_rigger_corrective_setup'
    ignore_keys = ['']  # Not to be stored

    # Loaded Elements Dictionary
    elements = {  # Pre Existing Elements
                'main_proxy_grp': 'rigger_corrective_proxy' + '_' + GRP_SUFFIX,
                'main_root': 'rigger_corrective_proxy' + '_' + PROXY_SUFFIX,

                # Wrists
                'left_main_wrist_crv': 'mainWrist_' + PROXY_SUFFIX,
                'left_upper_wrist_crv': 'upperWrist_' + PROXY_SUFFIX,
                'left_lower_wrist_crv': 'lowerWrist_' + PROXY_SUFFIX,

                # Knees
                'left_main_knee_crv': 'mainKnee_' + PROXY_SUFFIX,
                'left_back_knee_crv': 'backKnee_' + PROXY_SUFFIX,
                'left_front_knee_crv': 'frontKnee_' + PROXY_SUFFIX,

                # Hips
                'left_main_hip_crv': 'mainHip_' + PROXY_SUFFIX,
                'left_back_hip_crv': 'backHip_' + PROXY_SUFFIX,
                'left_front_hip_crv': 'frontHip_' + PROXY_SUFFIX,
                'left_outer_hip_crv': 'outerHip_' + PROXY_SUFFIX,
                # 'left_inner_hip_crv': 'innerHip_' + PROXY_SUFFIX,

                # Elbows
                'left_main_elbow_crv': 'mainElbow_' + PROXY_SUFFIX,
                'left_front_elbow_crv': 'frontElbow_' + PROXY_SUFFIX,

                # Shoulders
                'left_main_shoulder_crv': 'mainShoulder_' + PROXY_SUFFIX,
                'left_back_shoulder_crv': 'backShoulder_' + PROXY_SUFFIX,
                'left_front_shoulder_crv': 'frontShoulder_' + PROXY_SUFFIX,
                'left_upper_shoulder_crv': 'upperShoulder_' + PROXY_SUFFIX,
                # 'left_lower_shoulder_crv': 'lowerShoulder_' + PROXY_SUFFIX,
                }

    # Auto Populate Control Names (Copy from Left to Right) + Add prefixes
    elements_list = list(elements)
    for item in elements_list:
        if item.startswith('left_'):
            elements[item] = 'left_' + elements.get(item)  # Add "left_" prefix
            elements[item.replace('left_', 'right_')] = elements.get(item).replace('left_', 'right_')  # Add right copy

    preexisting_dict = {'left_wrist_jnt': 'left_wrist_jnt',
                        'right_wrist_jnt': 'right_wrist_jnt',
                        'left_knee_jnt': 'left_knee_jnt',
                        'right_knee_jnt': 'right_knee_jnt',
                        'left_forearm_jnt': 'left_forearm_jnt',
                        'right_forearm_jnt': 'right_forearm_jnt',
                        'left_wrist_aimJnt': 'left_wrist_aimJnt',
                        'right_wrist_aimJnt': 'right_wrist_aimJnt',
                        'left_hip_jnt': 'left_hip_jnt',
                        'right_hip_jnt': 'right_hip_jnt',
                        'left_elbow_jnt': 'left_elbow_jnt',
                        'right_elbow_jnt': 'right_elbow_jnt',
                        'left_shoulder_jnt': 'left_shoulder_jnt',
                        'right_shoulder_jnt': 'right_shoulder_jnt',
                        }

    # Store Default Values
    def __init__(self):
        self.settings = {'setup_wrists': True,
                         'setup_elbows': True,
                         'setup_shoulders': True,
                         'setup_knees': True,
                         'setup_hips': True,
                         }

        self.elements_default = copy.deepcopy(self.elements)
        self.settings_default = copy.deepcopy(self.settings)

    # Create Joints List
    joints_default = {}
    for obj in elements:
        if obj.endswith('_crv'):
            name = elements.get(obj).replace(PROXY_SUFFIX, JNT_SUFFIX).replace('end' + PROXY_SUFFIX.capitalize(),
                                                                               'end' + JNT_SUFFIX.capitalize())
            joints_default[obj.replace('_crv', '_' + JNT_SUFFIX).replace('_proxy', '')] = name
    joints_default['left_forearm_jnt'] = 'left_forearm_jnt'
    joints_default['right_forearm_jnt'] = 'right_forearm_jnt'

    # Reset Persistent Settings Variables
    gui_module = 'gt_rigger_biped_gui'
    entry_function = 'build_gui_auto_biped_rig()'

    # Used to export/import proxy
    proxy_storage_variables = {'file_extension': 'ppose_corrective',
                               'script_source': 'gt_rigger_corrective_version',
                               'export_method': 'gt_rigger_corrective_export_method',
                               'attr_name': 'corrective_proxy_pose'}

    # Debugging Vars
    debugging = False  # Activates Debugging Mode
    debugging_auto_recreate = True  # Auto deletes proxy/rig before creating
    debugging_force_new_scene = True  # Forces new instance every time
    debugging_keep_cam_transforms = True  # Keeps camera position
    debugging_import_proxy = True  # Auto Imports Proxy
    debugging_import_path = 'C:\\template.ppose'  # Path to auto import
    debugging_bind_rig = False  # Auto Binds Rig
    debugging_bind_geo = 'body_geo'  # Name of the geo to bind
    debugging_bind_heatmap = False  # If not using heatmap, then closest distance
    debugging_post_code = True  # Runs code found at the end of the create controls command


# Manage Persistent Settings
def get_persistent_settings(data_object):
    """
    Checks if persistent settings for exists and transfer them to the settings dictionary.
    It assumes that persistent settings were stored using the cmds.optionVar function.

        Parameters:
            data_object (GT*RiggerData): A GT*RiggerData object that is used to expo.

        Returns:
            True or False (bool): Whether operation was successful
    """
    # Basic Validation
    if not data_object:
        return False
    try:
        data_object.option_var
        data_object.ignore_keys  # The values in these keys will not get imported (No persistent behaviour)
    except:
        return False

    # Check if there is anything stored
    stored_setup_exists = cmds.optionVar(exists=(data_object.option_var))

    # The values in these keys will not get imported (No persistent behaviour)

    if stored_setup_exists:
        stored_settings = {}
        try:
            stored_settings = eval(str(cmds.optionVar(q=(data_object.option_var))))
            for stored_item in stored_settings:
                for item in data_object.settings:
                    if stored_item == item and item not in data_object.ignore_keys:
                        data_object.settings[item] = stored_settings.get(stored_item)
        except:
            print("Couldn't load persistent settings. Resetting it might fix the issue.")
            return False
        return True


def set_persistent_settings(data_object):
    """
    Stores persistent settings for GT Auto Rigger Data objects.
    It converts the dictionary into a list for easy storage. (The get function converts it back to a dictionary)
    It assumes that persistent settings were stored using the cmds.optionVar function.

    Args:
        data_object (GT*RiggerData): A GT*RiggerData object that is used to expo.

    Returns:
        True or False (bool): Whether the operation was successful
    """
    # Basic Validation
    if not data_object:
        return False
    try:
        data_object.option_var
        data_object.settings
    except:
        return False

    cmds.optionVar(sv=(data_object.option_var, str(data_object.settings)))
    if str(cmds.optionVar(q=(data_object.option_var)) == str(data_object.settings)):
        return True
    else:
        return False


def reset_persistent_settings(data_object):
    """
    Resets persistent settings for GT Auto Biped Rigger

    Args:
        data_object (GT*RiggerData): A GT*RiggerData object that is used to expo.

    Returns:
        True or False (bool): Whether the reset was successful
    """
    # Basic Validation
    if not data_object:
        return False
    try:
        data_object.option_var
        data_object.settings
        data_object.script_name
        data_object.gui_module
        data_object.entry_function
    except Exception as e:
        logger.debug(str(e))
        return False

    cmds.optionVar(remove=data_object.option_var)
    data_object.settings = data_object.settings_default
    cmds.warning('Persistent settings for ' + data_object.script_name + ' were cleared.')
    return True
