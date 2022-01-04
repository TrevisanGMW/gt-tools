'''
GT Rigger Data - Settings and naming conventions for auto rigger scripts
github.com/TrevisanGMW - 2021-12-10
'''
import maya.cmds as cmds
import copy

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
ROTATE_ORDER_ENUM = 'xyz:yzx:zxy:xzy:yxz:zyx'
CUSTOM_ATTR_SEPARATOR = 'controlBehaviour'


class GTBipedRiggerData:
    # Script Name
    script_name = 'GT Auto Biped Rigger'

    # Version:
    script_version = '1.8.14'

    # Permanent Settings
    option_var = 'gt_auto_biped_rigger_setup'
    ignore_keys = ['is_settings_visible', 'body_column_height']

    # Loaded Elements Dictionary
    elements = {  # General Settings
        'main_proxy_grp': 'auto_biped_proxy' + '_' + GRP_SUFFIX,
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
        # Right Side Elements are auto populated, script copies from Left to Right
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
        self.settings = {'is_settings_visible': False,
                         'body_column_height': 0,  # determined during settings GUI creation
                         'using_no_ssc_skeleton': False,
                         'proxy_limits': False,
                         'offer_heel_roll_positioning': True,
                         'uniform_ctrl_orient': False,
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


class GTFacialRiggerData:
    pass
    # TODO

# Manage Persistent Settings
def get_persistent_settings(data_object):
    """
    Checks if persistent settings for exists and transfer them to the settings dictionary.
    It assumes that persistent settings were stored using the cmds.optionVar function.

        Parameters:
            data_object (GT*RiggerData): A GT*RiggerData object that is used to expo.

        Returns:
            True or False (bool): Whether or not it was successfully updated
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
            print('Couldn\'t load persistent settings. Resetting it might fix the issue.')
            return False
        return True


def set_persistent_settings(data_object):
    """
    Stores persistant settings for GT Auto Rigger Data objects.
    It converts the dictionary into a list for easy storage. (The get function converts it back to a dictionary)
    It assumes that persistent settings were stored using the cmds.optionVar function.

        Parameters:
            data_object (GT*RiggerData): A GT*RiggerData object that is used to expo.

        Returns:
            True or False (bool): Whether or not it was successfully set
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
    """ Resets persistant settings for GT Auto Biped Rigger

        Parameters:
            data_object (GT*RiggerData): A GT*RiggerData object that is used to expo.

        Returns:
            True or False (bool): Whether or not it was successfully updated
    """
    # Basic Validation
    # if not data_object:
    #     return False
    # try:
    #     data_object.option_var
    #     data_object.settings
    #     data_object.script_name
    #     data_object.gui_module
    #     data_object.entry_function
    # except:
    #     return False
    print('Before Reset:')
    print(data_object.settings)
    cmds.optionVar(remove=data_object.option_var)
    # data_object.settings = data_object.settings_default

    cmds.warning('Persistent settings for ' + data_object.script_name + ' were cleared.')
    print('After Reset:')
    print(data_object.settings)

    print("Was in the default:")
    print(data_object.settings_default)

    # try:
    #     cmds.evalDeferred('import ' + data_object.gui_module)
    #     cmds.evalDeferred(data_object.gui_module + '.' + data_object.entry_function)
    # except:
    #     try:
    #         cmds.evalDeferred(data_object.entry_function)
    #     except:
    #         pass
    # return True
