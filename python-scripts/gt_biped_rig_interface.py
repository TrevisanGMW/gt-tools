"""
 Custom Rig Interface for GT Auto Biped Rigger.
 github.com/TrevisanGMW/gt-tools - 2021-01-05
 
 1.0 - 2021-01-05
 Initial Release

 1.1 - 2021-05-11
 Made script compatible with Python 3.0 (Maya 2022)

 1.2 - 2021-10-28
 Added mirror IK functions
 Added reset pose function
 Changed it to accept namespaces with or without ":"
  
 1.3 - 2021-10-29
 Changed the name from "Seamless IK/FK Switch" to "Custom Rig Interface"
 Added functions to mirror and reset FK controls
 Added center controls to reset pose function
 Added custom rig name (if not empty, it will display a message describing unique rig target)
 Added system to get and set persistent settings to store the namespace input
 Added warning message reminding user to check their namespace in case elements are not found
 
 1.3.1 - 2021-11-01
 Changed versioning system to semantic to account for patches
 Fixed some typos in the "locked" message for when trying to mirror
 Added scale mirroring functions (fixes finger abduction pose)
 Included curl controls in the mirroring list
 
 1.3.2 - 2021-11-03
 Added IK fingers to mirroring functions
 
 1.3.3 - 2021-11-04
 Added animation import/export functions. (".anim" with ".json" data)
 Changed the pose file extension to ".pose" instead of ".json" to avoid confusion
 Added animation mirroring functions
 
 1.3.4 - 2021-11-08
 Add settings menu
 Made UI aware of FK/IK state
 Recreated part of the UI to use Tabs
 Improved switch functions with a mechanism to auto create keyframes (sparse or bake)
 Added inView feedback explaining switch information
 Fixed issue where the arm pole vector wouldn't mirror properly
 Added option to reset persistent settings
 
 1.3.5 - 2021-11-10
 Added animation and pose reset
 Updates animation functions to account for tangents and other key properties
 
 1.3.6 - 2021-11-12
 Allowed for multiple instances (in case animating multiple characters)
 Changed icons and assigned an alternative one for extra instances
 Added a missing import for "sys"
 
 1.3.7 - 2021-11-23
 Updated switcher to be compatible with new offset controls
 Added inView message for when auto clavicle is active so the user doesn't think the control is popping
 
 1.3.8 - 2021-11-23
 Included a few missing controls to the pose and animation management control lists
  
 1.3.9 - 2021-11-30
 Updated the script so it works with the new offset controls
 Accounted for new wrist reference control
 
 1.3.10 - 2021-12-01
 Added option to define whether or not to transfer data to offset control or control
 
 TODO:
    Include function to extract character's metadata
    Created flip pose function
    Convert GUI to QT
    Add Flip options
    Overwrite keys for animation functions
    Add Namespace picker (button to the right of the namespace textfield)
    Option to save pose thumbnail when exporting it 
    Add option to open multiple instances
    
"""
try:
    from shiboken2 import wrapInstance
except ImportError:
    from shiboken import wrapInstance
    
try:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QWidget
except ImportError:
    from PySide.QtGui import QIcon, QWidget

from maya import OpenMayaUI as omui
import maya.cmds as cmds
import random
import json
import copy
import sys
import os


# Script Name
script_name = 'GT Custom Rig Interface'
unique_rig = '' # If provided, it will be used in the window title

# Version:
script_version = "1.3.10"

# Python Version
python_version = sys.version_info.major

# FK/IK Swticher Elements                    
left_arm_seamless_dict = { 'switch_ctrl' : 'left_arm_switch_ctrl', # Switch Ctrl
                           'end_ik_ctrl' : 'left_wrist_ik_offsetCtrl', # IK Elements
                           'pvec_ik_ctrl' : 'left_elbow_ik_ctrl',
                           'base_ik_jnt' :  'left_shoulder_ik_jnt',
                           'mid_ik_jnt' : 'left_elbow_ik_jnt',
                           'end_ik_jnt' : 'left_wrist_ik_jnt',
                           'base_fk_ctrl' : 'left_shoulder_ctrl', # FK Elements
                           'mid_fk_ctrl' : 'left_elbow_ctrl',
                           'end_fk_ctrl' : 'left_wrist_ctrl' ,
                           'base_fk_jnt' :  'left_shoulder_fk_jnt',
                           'mid_fk_jnt' : 'left_elbow_fk_jnt',
                           'end_fk_jnt' : 'left_wrist_fk_jnt',
                           'mid_ik_reference' : 'left_elbowSwitch_loc',
                           'end_ik_reference' : 'left_wristSwitch_loc',
                           'incompatible_attr_holder' : 'left_wrist_ik_ctrl', # Auto Clavicle
                         }

right_arm_seamless_dict = { 'switch_ctrl' : 'right_arm_switch_ctrl', # Switch Ctrl
                            'end_ik_ctrl' : 'right_wrist_ik_offsetCtrl', # IK Elements
                            'pvec_ik_ctrl' : 'right_elbow_ik_ctrl',
                            'base_ik_jnt' :  'right_shoulder_ik_jnt',
                            'mid_ik_jnt' : 'right_elbow_ik_jnt',
                            'end_ik_jnt' : 'right_wrist_ik_jnt',
                            'base_fk_ctrl' : 'right_shoulder_ctrl', # FK Elements
                            'mid_fk_ctrl' : 'right_elbow_ctrl',
                            'end_fk_ctrl' : 'right_wrist_ctrl' ,
                            'base_fk_jnt' :  'right_shoulder_fk_jnt',
                            'mid_fk_jnt' : 'right_elbow_fk_jnt',
                            'end_fk_jnt' : 'right_wrist_fk_jnt',
                            'mid_ik_reference' : 'right_elbowSwitch_loc',
                            'end_ik_reference' : 'right_wristSwitch_loc',
                            'incompatible_attr_holder' : 'right_wrist_ik_ctrl', # Auto Clavicle
                           }
                            
left_leg_seamless_dict = { 'switch_ctrl' : 'left_leg_switch_ctrl', # Switch Ctrl
                           'end_ik_ctrl' : 'left_foot_ik_offsetCtrl', # IK Elements
                           'pvec_ik_ctrl' : 'left_knee_ik_ctrl',
                           'base_ik_jnt' :  'left_hip_ik_jnt',
                           'mid_ik_jnt' : 'left_knee_ik_jnt',
                           'end_ik_jnt' : 'left_ankle_ik_jnt',
                           'base_fk_ctrl' : 'left_hip_ctrl', # FK Elements
                           'mid_fk_ctrl' : 'left_knee_ctrl',
                           'end_fk_ctrl' : 'left_ankle_ctrl' , 
                           'base_fk_jnt' :  'left_hip_fk_jnt',
                           'mid_fk_jnt' : 'left_knee_fk_jnt',
                           'end_fk_jnt' : 'left_ankle_fk_jnt',
                           'mid_ik_reference' : 'left_kneeSwitch_loc',
                           'end_ik_reference' : 'left_ankleSwitch_loc', #left_ankleSwitch_loc
                           'incompatible_attr_holder' : '',
                          }
                           
right_leg_seamless_dict = { 'switch_ctrl' : 'right_leg_switch_ctrl', # Switch Ctrl
                            'end_ik_ctrl' : 'right_foot_ik_offsetCtrl', # IK Elements
                            'pvec_ik_ctrl' : 'right_knee_ik_ctrl',
                            'base_ik_jnt' :  'right_hip_ik_jnt',
                            'mid_ik_jnt' : 'right_knee_ik_jnt',
                            'end_ik_jnt' : 'right_ankle_ik_jnt',
                            'base_fk_ctrl' : 'right_hip_ctrl', # FK Elements
                            'mid_fk_ctrl' : 'right_knee_ctrl',
                            'end_fk_ctrl' : 'right_ankle_ctrl' ,
                            'base_fk_jnt' :  'right_hip_fk_jnt',
                            'mid_fk_jnt' : 'right_knee_fk_jnt',
                            'end_fk_jnt' : 'right_ankle_fk_jnt',
                            'mid_ik_reference' : 'right_kneeSwitch_loc',
                            'end_ik_reference' : 'right_ankleSwitch_loc',
                            'incompatible_attr_holder' : '',
                          }
                          
seamless_elements_dictionaries = [right_arm_seamless_dict, left_arm_seamless_dict, left_leg_seamless_dict, right_leg_seamless_dict]

# Mirror Elements
namespace_separator = ':'
left_prefix = 'left'
right_prefix = 'right'
not_inverted = (False, False, False)
invert_x = (True, False, False)
invert_y = (False, True, False)
invert_z = (False, False, True)
invert_yz = (False, True, True)
invert_all = (True, True, True)


# Dictionary Pattern:
# Key: Control name (if not in the center, remove prefix)
# Value: A list with two tuples. [(Is Translate XYZ inverted?), (Is Rotate XYZ inverted?), Is mirroring scale?]
# Value Example: '_fingers_ctrl': [not_inverted, not_inverted, True] = Not inverting Translate XYZ. Not inverting Rotate XYZ. Yes, mirroring scale.
gt_ab_general_ctrls = {# Fingers Automation
                   '_fingers_ctrl': [not_inverted, not_inverted, True],
                   '_thumbCurl_ctrl': [not_inverted, not_inverted],
                   '_indexCurl_ctrl': [not_inverted, not_inverted],
                   '_middleCurl_ctrl': [not_inverted, not_inverted],
                   '_ringCurl_ctrl': [not_inverted, not_inverted],
                   '_pinkyCurl_ctrl': [not_inverted, not_inverted],
                   
                   # Fingers FK
                   '_thumb03_ctrl': [not_inverted, not_inverted],
                   '_thumb02_ctrl': [not_inverted, not_inverted],
                   '_thumb01_ctrl': [not_inverted, not_inverted],
                   '_index01_ctrl': [not_inverted, not_inverted],
                   '_middle02_ctrl': [not_inverted, not_inverted],
                   '_middle01_ctrl': [not_inverted, not_inverted],
                   '_index03_ctrl': [not_inverted, not_inverted],
                   '_index02_ctrl': [not_inverted, not_inverted],
                   '_ring03_ctrl': [not_inverted, not_inverted],
                   '_ring02_ctrl': [not_inverted, not_inverted],
                   '_ring01_ctrl': [not_inverted, not_inverted],
                   '_middle03_ctrl': [not_inverted, not_inverted],
                   '_pinky03_ctrl': [not_inverted, not_inverted],
                   '_pinky02_ctrl': [not_inverted, not_inverted],
                   '_pinky01_ctrl': [not_inverted, not_inverted],
                   
                   # Finger IK
                   '_thumb_ik_ctrl': [invert_z, invert_x],
                   '_index_ik_ctrl': [invert_z, invert_x],
                   '_middle_ik_ctrl': [invert_z, invert_x],
                   '_ring_ik_ctrl': [invert_z, invert_x],
                   '_pinky_ik_ctrl': [invert_z, invert_x],
                   # Clavicle
                   '_clavicle_ctrl': [not_inverted, not_inverted],
                   # Eyes
                   '_eye_ctrl': [invert_x, not_inverted],
                 }   

gt_ab_ik_ctrls = { # Arm
                   '_elbow_ik_ctrl': [invert_x, not_inverted], 
                   '_wrist_ik_ctrl': [invert_all, not_inverted],
                   '_wrist_ik_offsetCtrl': [invert_all, not_inverted],
                   # Leg
                   '_heelRoll_ctrl': [invert_x, not_inverted],
                   '_ballRoll_ctrl': [invert_x, not_inverted],
                   '_toeRoll_ctrl': [invert_x, not_inverted],
                   '_toe_upDown_ctrl': [invert_x, not_inverted],
                   '_foot_ik_ctrl': [invert_x, invert_yz],
                   '_foot_ik_offsetCtrl': [invert_x, invert_yz],
                   '_knee_ik_ctrl': [invert_x, not_inverted],
                 }
                   
gt_ab_fk_ctrls = {# Arm
                   '_shoulder_ctrl': [invert_all, not_inverted],
                   '_elbow_ctrl': [invert_all, not_inverted],
                   '_wrist_ctrl': [invert_all, not_inverted],
                  # Leg
                   '_hip_ctrl': [invert_x, invert_yz],
                   '_knee_ctrl': [invert_all, not_inverted],
                   '_ankle_ctrl': [invert_all, not_inverted],
                   '_ball_ctrl': [invert_all, not_inverted],
                 }
                       
gt_ab_center_ctrls = ['cog_ctrl', 
                      'cog_offsetCtrl', 
                      'hip_ctrl', 
                      'hip_offsetCtrl', 
                      'spine01_ctrl', 
                      'spine02_ctrl', 
                      'spine03_ctrl', 
                      'spine04_ctrl', 
                      'cog_ribbon_ctrl', 
                      'chest_ribbon_offsetCtrl', 
                      'spine_ribbon_ctrl', 
                      'chest_ribbon_ctrl',
                      'neckBase_ctrl',
                      'neckMid_ctrl',
                      'head_ctrl',
                      'jaw_ctrl',
                      'main_eye_ctrl',
                      'left_eye_ctrl',
                      'right_eye_ctrl',
                      ]            

gt_custom_rig_interface_settings = {
                                    'namespace' : '',
                                    'auto_key_switch' : True,
                                    'auto_key_method_bake' : True,
                                    'auto_key_start_frame' : 1,
                                    'auto_key_end_frame' : 10,
                                    'pose_export_thumbnail' : False,
                                    'allow_multiple_instances' : False,
                                    'offset_target' : True,
                                   }
                   
gt_custom_rig_interface_settings_default = copy.deepcopy(gt_custom_rig_interface_settings)


# Manage Persistent Settings
def get_persistent_settings_rig_interface():
    ''' 
    Checks if persistant settings for GT Auto Biped Rig Interface exists and loads it if this is the case.
    It assumes that persistent settings were stored using the cmds.optionVar function.
    '''
    # Check if there is anything stored
    stored_setup_exists = cmds.optionVar(exists=("gt_auto_biped_rig_interface_setup"))
  
    if stored_setup_exists:
        stored_settings = {}
        try:
            stored_settings = eval(str(cmds.optionVar(q=("gt_auto_biped_rig_interface_setup"))))
            for stored_item in stored_settings:
                for item in gt_custom_rig_interface_settings:
                    if stored_item == item:
                        gt_custom_rig_interface_settings[item] = stored_settings.get(stored_item)
        except:
            print('Couldn\'t load persistent settings, try resetting it in the help menu.')


def set_persistent_settings_rig_interface():
    ''' 
    Stores persistant settings for GT Auto Biped Rig Interface.
    It converts the dictionary into a list for easy storage. (The get function converts it back to a dictionary)
    It assumes that persistent settings were stored using the cmds.optionVar function.
    '''
    cmds.optionVar( sv=('gt_auto_biped_rig_interface_setup', str(gt_custom_rig_interface_settings)))


def reset_persistent_settings_rig_interface():
    ''' Resets persistant settings for GT Auto Biped Rig Interface '''
    cmds.optionVar( remove='gt_auto_biped_rig_interface_setup' )
    gt_custom_rig_interface_settings =  gt_custom_rig_interface_settings_default
    cmds.optionVar( sv=('gt_auto_biped_rig_interface_setup', str(gt_custom_rig_interface_settings_default)))
    cmds.warning('Persistent settings for ' + script_name + ' were cleared.')
    try:
        cmds.evalDeferred('build_gui_custom_rig_interface()')
    except:
        try:
            build_gui_custom_rig_interface()
        except:
            try:
                cmds.evalDeferred('gt_biped_rig_interface.build_gui_custom_rig_interface()')
            except:
                pass

             
# Main Window ============================================================================
def build_gui_custom_rig_interface():
    
    # Retrieve Persistent Settings
    get_persistent_settings_rig_interface()
    
    rig_interface_window_name = 'build_gui_custom_rig_interface'
    is_secondary_instance = False
    if cmds.window(rig_interface_window_name, exists=True) and not gt_custom_rig_interface_settings.get('allow_multiple_instances'):
        cmds.deleteUI(rig_interface_window_name)  
    # In case it's a secondary instance 
    if gt_custom_rig_interface_settings.get('allow_multiple_instances'):
        if cmds.window(rig_interface_window_name, exists=True):
            rig_interface_window_name = rig_interface_window_name + '_' + str(random.random()).replace('.','')
            is_secondary_instance = True
            
            gt_custom_rig_interface_settings_instanced = copy.deepcopy(gt_custom_rig_interface_settings)
   


    # Main GUI Start Here =================================================================================
    def update_fk_ik_buttons():
        '''
        Updates the background color of the FK/IK buttons according to the value of the current influenceSwitch attribute.
        This attempts to make the UI "aware" of the current state of the controls.
        '''
        active_color = (.6,.6,.6)
        inactive_color = (.36,.36,.36)
        ctrl_btn_lists = [
                          [right_arm_seamless_dict, right_arm_fk_btn, right_arm_ik_btn],
                          [left_arm_seamless_dict, left_arm_fk_btn, left_arm_ik_btn],
                          [right_leg_seamless_dict, right_leg_fk_btn, right_leg_ik_btn],
                          [left_leg_seamless_dict, left_leg_fk_btn, left_leg_ik_btn]
                         ]
        for ctrl_btns in ctrl_btn_lists:
            if cmds.objExists(gt_custom_rig_interface_settings.get('namespace') + namespace_separator + ctrl_btns[0].get('switch_ctrl')):
                try:
                    current_system = cmds.getAttr(gt_custom_rig_interface_settings.get('namespace') + namespace_separator + ctrl_btns[0].get('switch_ctrl') + '.influenceSwitch')
                    if current_system < 0.5:
                        cmds.button(ctrl_btns[1], e=True, bgc=active_color) # FK Button
                        cmds.button(ctrl_btns[2], e=True, bgc=inactive_color) # IK Button
                    else:
                        cmds.button(ctrl_btns[2], e=True, bgc=active_color) # FK Button
                        cmds.button(ctrl_btns[1], e=True, bgc=inactive_color) # IK Button
                except:
                    pass
            else:
                cmds.button(ctrl_btns[2], e=True, bgc=inactive_color) # FK Button
                cmds.button(ctrl_btns[1], e=True, bgc=inactive_color) # IK Button
    

    def update_stored_settings(is_instance=False):
        '''
        Extracts the namespace used and stores it as a persistent variable
        This function also calls "update_fk_ik_buttons()" so it updates the UI
        
                    Parameters:
                        is_instance (optional, bool): Allow a bool argument to determine if the settings are supposed to be stored or not
                                                      This is used for secondary instances (multiple windows)
                                              
        '''
        gt_custom_rig_interface_settings['namespace'] = cmds.textField(namespace_txt, q=True, text=True)
        gt_custom_rig_interface_settings['auto_key_switch'] = cmds.checkBox(auto_key_switch_chk, q=True, value=True)
        gt_custom_rig_interface_settings['auto_key_switch'] = cmds.checkBox(auto_key_switch_chk, q=True, value=True)
        gt_custom_rig_interface_settings['auto_key_method_bake'] = cmds.radioButton(auto_key_method_rb1, query=True, select=True)
        gt_custom_rig_interface_settings['auto_key_start_frame'] = cmds.intField(auto_key_start_int_field, q=True, value=0)
        gt_custom_rig_interface_settings['auto_key_end_frame'] = cmds.intField(auto_key_end_int_field, q=True, value=0)
        
        if not gt_custom_rig_interface_settings.get('offset_target'):
            for data in seamless_elements_dictionaries:
                data['end_ik_ctrl'] = data.get('end_ik_ctrl').replace('offsetCtrl','ctrl')
        else:
            for data in seamless_elements_dictionaries:
                data['end_ik_ctrl'] = data.get('end_ik_ctrl').replace('ctrl','offsetCtrl')

        if gt_custom_rig_interface_settings.get('auto_key_switch'):
            cmds.radioButton(auto_key_method_rb1, e=True, en=True)
            cmds.radioButton(auto_key_method_rb2, e=True, en=True)
            cmds.rowColumnLayout(switch_range_column, e=True, en=True)
        else:
            cmds.radioButton(auto_key_method_rb1, e=True, en=False)
            cmds.radioButton(auto_key_method_rb2, e=True, en=False)
            cmds.rowColumnLayout(switch_range_column, e=True, en=False)
        
        if not is_instance: # Doesn't update persistent settings for secondary instances
            set_persistent_settings_rig_interface()
        update_fk_ik_buttons()


    def update_switch(ik_fk_dict, direction='ik_to_fk', is_auto_switch=False):
        '''
        Runs the switch function using the parameters provided in the UI
        Also updates the UI to keep track of the FK/IK state.
        
                Parameters:
                     ik_fk_dict (dict): A dicitionary containg the elements that are part of the system you want to switch
                     direction (optinal, string): Either "fk_to_ik" or "ik_to_fk". It determines what is the source and what is the target.
        '''
        method = 'bake' if gt_custom_rig_interface_settings.get('auto_key_method_bake') else 'sparse' 
        
        if is_auto_switch:
            gt_rig_fk_ik_switch_auto(ik_fk_dict, 
                                             namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator,
                                             keyframe=gt_custom_rig_interface_settings.get('auto_key_switch'),
                                             start_time=int(gt_custom_rig_interface_settings.get('auto_key_start_frame')), 
                                             end_time=int(gt_custom_rig_interface_settings.get('auto_key_end_frame')), 
                                             method=method
                                             )

        else:
            gt_rig_fk_ik_switch(ik_fk_dict, 
                                        direction, 
                                        namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator,
                                        keyframe=gt_custom_rig_interface_settings.get('auto_key_switch'),
                                        start_time=int(gt_custom_rig_interface_settings.get('auto_key_start_frame')), 
                                        end_time=int(gt_custom_rig_interface_settings.get('auto_key_end_frame')), 
                                        method=method
                                        )

        update_fk_ik_buttons()

    def invert_stored_setting(key_string):
        '''
        Used for boolean values, it inverts the value, so if True it becomes False and vice-versa.
        It also stores the new values after they are changed so future instances remember it.
        
                Parameters:
                    key_string (string) : Key name, used to determine what bool value to flip
        '''
        gt_custom_rig_interface_settings[key_string] = not gt_custom_rig_interface_settings.get(key_string)
        set_persistent_settings_rig_interface()
        update_stored_settings()
                       
    def get_auto_key_current_frame(target_integer_field='start', is_instance=False):
        '''
        Gets the current frame and auto fills an integer field.
        
                Parameters:
                    target_integer_field (optional, string) : Gets the current timeline frame and feeds it into the start or end integer field.
                                                              Can only be "start" or "end". Anything else will be understood as "end".
                    is_instance (optional, bool): Allow a bool argument to determine if the settings are supposed to be stored or not
                                                      This is used for secondary instances (multiple windows)
        
        '''
        current_time = cmds.currentTime(q=True)
        if target_integer_field == 'start':
            cmds.intField(auto_key_start_int_field, e=True, value=current_time)
        else:
            cmds.intField(auto_key_end_int_field, e=True, value=current_time)

        update_stored_settings(is_instance)
    
    
    def mirror_fk_ik_pose(source_side='right'):
        '''
        Runs a full pose mirror function.
        
                Parameters:
                     source_side (optinal, string): Either "right" or "left". It determines what is the source and what is the target of the mirror.
        '''
        
        gt_rig_pose_mirror([gt_ab_general_ctrls, gt_ab_ik_ctrls, gt_ab_fk_ctrls], source_side, namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator)
        
        
    def reset_animation_and_pose():
        '''
        Deletes Keyframes and Resets pose back to default
        '''
        gt_rig_anim_reset(namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator)
        gt_rig_pose_reset(gt_ab_ik_ctrls, gt_ab_fk_ctrls, gt_ab_center_ctrls, namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator)
    

    def build_custom_help_window(input_text, help_title=''):
        ''' 
        Creates a help window to display the provided text

                Parameters:
                    input_text (string): Text used as help, this is displayed in a scroll fields.
                    help_title (optinal, string)
        '''
        window_name = help_title.replace(" ","_").replace("-","_").lower().strip() + "_help_window"
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)

        cmds.window(window_name, title= help_title + " Help", mnb=False, mxb=False, s=True)
        cmds.window(window_name, e=True, s=True, wh=[1,1])

        main_column = cmds.columnLayout(p= window_name)
       
        # Title Text
        cmds.separator(h=12, style='none') # Empty Space
        cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p=main_column) # Window Size Adjustment
        cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column) # Title Column
        cmds.text(help_title + ' Help', bgc=(.4, .4, .4),  fn='boldLabelFont', align='center')
        cmds.separator(h=10, style='none', p=main_column) # Empty Space

        # Body ====================       
        cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column)
        
        help_scroll_field = cmds.scrollField(editable=False, wordWrap=True, fn='smallPlainLabelFont')
     
        cmds.scrollField(help_scroll_field, e=True, ip=0, it=input_text)
        cmds.scrollField(help_scroll_field, e=True, ip=1, it='') # Bring Back to the Top
        
        # Close Button 
        cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column)
        cmds.separator(h=10, style='none')
        cmds.button(l='OK', h=30, c=lambda args: close_help_gui())
        cmds.separator(h=8, style='none')
        
        # Show and Lock Window
        cmds.showWindow(window_name)
        cmds.window(window_name, e=True, s=False)
        
        # Set Window Icon
        qw = omui.MQtUtil.findWindow(window_name)
        if python_version == 3:
            widget = wrapInstance(int(qw), QWidget)
        else:
            widget = wrapInstance(long(qw), QWidget)
        icon = QIcon(':/question.png')
        widget.setWindowIcon(icon)
        
        def close_help_gui():
            ''' Closes help windows '''
            if cmds.window(window_name, exists=True):
                cmds.deleteUI(window_name, window=True)
        # Custom Help Dialog Ends Here =================================================================================
        
    # Build UI.
    script_title = script_name
    if unique_rig != '':
        script_title = 'GT - Rig Interface for ' + unique_rig
      
    if is_secondary_instance:
      script_version_title = '  (Extra Instance)'
    else:
      script_version_title = '  (v' + script_version + ')'
      
    build_gui_custom_rig_interface = cmds.window(rig_interface_window_name, title=script_title + script_version_title,\
                          titleBar=True, mnb=False, mxb=False, sizeable =True)

    cmds.window(rig_interface_window_name, e=True, s=True, wh=[1,1])

    content_main = cmds.columnLayout(adj = True)

    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 10)], p=content_main) # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 200), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)], p=content_main) # Title Column
    cmds.text(" ", bgc=title_bgc_color) # Tiny Empty Green Space
    cmds.text(script_title, bgc=title_bgc_color,  fn="boldLabelFont", align="left")
    cmds.button( l ="Help", bgc=title_bgc_color, c=lambda x:open_gt_tools_documentation())
    cmds.separator(h=5, style='none') # Empty Space
        
    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,10)], p=content_main)
    
    cmds.text('Namespace:')
    namespace_txt = cmds.textField(text=gt_custom_rig_interface_settings.get('namespace'), pht='Namespace:: (Optional)', cc=lambda x:update_stored_settings(is_secondary_instance))
    
    cmds.separator(h=10, style='none') # Empty Space
    
    form = cmds.formLayout()
    tabs = cmds.tabLayout(innerMarginWidth=5, innerMarginHeight=5)
    cmds.formLayout(form, edit=True, attachForm=((tabs, 'top', 0), (tabs, 'left', 0), (tabs, 'bottom', 0), (tabs, 'right', 0)) )

    ############# FK/IK Switch Tab #############
    btn_margin = 5
    fk_ik_switch_tab = cmds.rowColumnLayout(nc=1, cw=[(1, 246)], cs=[(1,0)], p=tabs)

    fk_ik_btn_width = 59
    cw_fk_ik_states = [(1, fk_ik_btn_width),(2, fk_ik_btn_width),(3, fk_ik_btn_width),(4, fk_ik_btn_width)]
    cs_fk_ik_states = [(1,2), (2,2), (3,3), (4,2)]
    
    switch_btn_width = 120
    cw_fk_ik_switches = [(1, switch_btn_width),(2, switch_btn_width)]
    cs_fk_ik_switches = [(1,2), (2,3)]
    
    arms_text = cmds.rowColumnLayout(nc=2, cw=cw_fk_ik_switches, cs=cs_fk_ik_switches, p=fk_ik_switch_tab)
    cmds.separator(h=2, style='none') # Empty Space
    cmds.separator(h=2, style='none') # Empty Space
    cmds.text('Right Arm:', p=arms_text) #R
    cmds.text('Left Arm:', p=arms_text) #L
    
    arms_switch_state_column = cmds.rowColumnLayout(nc=4, cw=cw_fk_ik_states, cs=cs_fk_ik_states, p=fk_ik_switch_tab)
    right_arm_fk_btn = cmds.button(l ="FK", c=lambda x:update_switch(right_arm_seamless_dict, 'ik_to_fk'), p=arms_switch_state_column) #R
    right_arm_ik_btn = cmds.button(l ="IK", c=lambda x:update_switch(right_arm_seamless_dict, 'fk_to_ik'), p=arms_switch_state_column) #L
    left_arm_fk_btn = cmds.button(l ="FK", c=lambda x:update_switch(left_arm_seamless_dict, 'ik_to_fk'), p=arms_switch_state_column) #R
    left_arm_ik_btn = cmds.button(l ="IK", c=lambda x:update_switch(left_arm_seamless_dict, 'fk_to_ik'), p=arms_switch_state_column) #L
    
    arms_switch_column = cmds.rowColumnLayout(nc=2, cw=cw_fk_ik_switches, cs=cs_fk_ik_switches, p=fk_ik_switch_tab)
    cmds.button(l ="Switch", c=lambda x:update_switch(right_arm_seamless_dict, is_auto_switch=True), p=arms_switch_column) #R
    cmds.button(l ="Switch", c=lambda x:update_switch(left_arm_seamless_dict, is_auto_switch=True), p=arms_switch_column) #L
    
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.text('Right Leg:', p=arms_switch_column) #R
    cmds.text('Left Leg:', p=arms_switch_column) #L

    legs_switch_state_column = cmds.rowColumnLayout(nc=4, cw=cw_fk_ik_states, cs=cs_fk_ik_states, p=fk_ik_switch_tab)
    right_leg_fk_btn = cmds.button(l ="FK", c=lambda x:update_switch(right_leg_seamless_dict, 'ik_to_fk'), p=legs_switch_state_column) #R
    right_leg_ik_btn = cmds.button(l ="IK", c=lambda x:update_switch(right_leg_seamless_dict, 'fk_to_ik'), p=legs_switch_state_column) #L
    left_leg_fk_btn = cmds.button(l ="FK", c=lambda x:update_switch(left_arm_seamless_dict, 'ik_to_fk'), p=legs_switch_state_column) #R
    left_leg_ik_btn = cmds.button(l ="IK", c=lambda x:update_switch(left_arm_seamless_dict, 'fk_to_ik'), p=legs_switch_state_column) #L
    
    legs_switch_column = cmds.rowColumnLayout(nc=2, cw=cw_fk_ik_switches, cs=cs_fk_ik_switches, p=fk_ik_switch_tab)
    cmds.button(l ="Switch", c=lambda x:update_switch(right_leg_seamless_dict, is_auto_switch=True), p=legs_switch_column) #R
    cmds.button(l ="Switch", c=lambda x:update_switch(left_leg_seamless_dict, is_auto_switch=True), p=legs_switch_column) #L
    
    # Auto Key Settings (Switch Settings)
    switch_settings_column = cmds.rowColumnLayout(nc=1, cw=[(1, 245)], cs=[(1, 6)], p=fk_ik_switch_tab)
    cmds.separator(h=15) # Empty Space
    switch_auto_key_column = cmds.rowColumnLayout(nc=3, cw=[(1, 80),(2, 130),(3, 60)], cs=[(1, 25)], p=fk_ik_switch_tab)
    auto_key_switch_chk = cmds.checkBox( label='Auto Key',  value=gt_custom_rig_interface_settings.get('auto_key_switch'), cc=lambda x:update_stored_settings(is_secondary_instance))
    
    method_container = cmds.rowColumnLayout( p=switch_auto_key_column, numberOfRows=1)
    auto_key_method_rc = cmds.radioCollection()
    auto_key_method_rb1 = cmds.radioButton( p=method_container, label=' Bake  ', sl=gt_custom_rig_interface_settings.get('auto_key_method_bake'), cc=lambda x:update_stored_settings(is_secondary_instance))
    auto_key_method_rb2 = cmds.radioButton( p=method_container,  label=' Sparse ', sl=(not gt_custom_rig_interface_settings.get('auto_key_method_bake')), cc=lambda x:update_stored_settings(is_secondary_instance))
    cmds.separator(h=5, style='none', p=fk_ik_switch_tab) # Empty Space
    
    switch_range_column = cmds.rowColumnLayout(nc=6, cw=[(1, 40),(2, 40),(3, 30),(4, 30),(5, 40),(6, 30)], cs=[(1, 10), (4, 10)], p=fk_ik_switch_tab)
    cmds.text('Start:', p=switch_range_column)
    auto_key_start_int_field = cmds.intField(value=int(gt_custom_rig_interface_settings.get('auto_key_start_frame')), p=switch_range_column, cc=lambda x:update_stored_settings(is_secondary_instance))
    cmds.button(l ="Get", c=lambda x:get_auto_key_current_frame(), p=switch_range_column, h=5) #L
    cmds.text('End:', p=switch_range_column)
    auto_key_end_int_field = cmds.intField(value=int(gt_custom_rig_interface_settings.get('auto_key_end_frame')),p=switch_range_column, cc=lambda x:update_stored_settings(is_secondary_instance))
    cmds.button(l ="Get", c=lambda x:get_auto_key_current_frame('end'), p=switch_range_column, h=5) #L
    cmds.separator(h=10, style='none', p=fk_ik_switch_tab) # Empty Space
    

    ############# Pose Management Tab #############
    pose_management_tab = cmds.rowColumnLayout(nc=1, cw=[(1, 246)], cs=[(1,0)], p=tabs)

    btn_margin = 2
    
    cmds.separator(h=5, style='none') # Empty Space
    pose_title_column = cmds.rowColumnLayout(nc=1, cw=[(1, 245)], cs=cs_fk_ik_switches, p=pose_management_tab)
    cmds.text('Mirror Pose:', p=pose_title_column)
    cmds.separator(h=5, style='none', p=pose_title_column) # Empty Space
    
    
    mirror_pose_column = cmds.rowColumnLayout(nc=2, cw=cw_fk_ik_switches, cs=cs_fk_ik_switches, p=pose_management_tab)
    
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.separator(h=btn_margin, style='none') # Empty Space
    
    cmds.text('Right to Left:', p=mirror_pose_column) #R
    cmds.text('Left to Right:', p=mirror_pose_column) #L
    
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.separator(h=btn_margin, style='none') # Empty Space
    
    cmds.button(l ="Mirror ->", c=lambda x:mirror_fk_ik_pose('right'), p=mirror_pose_column) #R
    cmds.button(l ="<- Mirror", c=lambda x:mirror_fk_ik_pose('left'), p=mirror_pose_column) #L
    
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.separator(h=btn_margin, style='none') # Empty Space
    
    pose_mirror_ik_fk_column = cmds.rowColumnLayout(nc=4, cw=cw_fk_ik_states, cs=cs_fk_ik_states, p=pose_management_tab)
    
    # IK Pose Mirror
    cmds.button(l ="IK Only >", c=lambda x:gt_rig_pose_mirror([gt_ab_general_ctrls, gt_ab_ik_ctrls], 'right', namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), p=pose_mirror_ik_fk_column) #R
    cmds.button(l ="FK Only >", c=lambda x:gt_rig_pose_mirror([gt_ab_general_ctrls, gt_ab_fk_ctrls], 'right', namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), p=pose_mirror_ik_fk_column) #R
    
    
    # FK Pose Mirror
    cmds.button(l ="< IK Only", c=lambda x:gt_rig_pose_mirror([gt_ab_general_ctrls, gt_ab_ik_ctrls], 'left', namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), p=pose_mirror_ik_fk_column) #L
    cmds.button(l ="< FK Only", c=lambda x:gt_rig_pose_mirror([gt_ab_general_ctrls, gt_ab_fk_ctrls], 'left', namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), p=pose_mirror_ik_fk_column) #L
    

    # Reset Pose
    pose_management_column = cmds.rowColumnLayout(nc=1, cw=[(1, 245)], cs=cs_fk_ik_switches, p=pose_management_tab)
    cmds.separator(h=15, style='none', p=pose_management_column) # Empty Space
    cmds.text('Reset Pose:', p=pose_management_column) #R
    cmds.separator(h=btn_margin, style='none', p=pose_management_column) # Empty Space
    cmds.button(l ="Reset Back to Default Pose", c=lambda x:gt_rig_pose_reset(gt_ab_ik_ctrls, gt_ab_fk_ctrls, gt_ab_center_ctrls, namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), p=pose_management_column)

    # Export Import Pose
    cmds.separator(h=btn_margin, style='none', p=pose_management_column) # Empty Space
    cmds.separator(h=15, style='none', p=pose_management_column) # Empty Space
    cmds.text('Import/Export Poses:', p=pose_management_column) 
    
    import_export_pose_column = cmds.rowColumnLayout(nc=2, cw=cw_fk_ik_switches, cs=cs_fk_ik_switches, p=pose_management_tab)
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.button(l ="Import Current Pose", c=lambda x:gt_rig_pose_import(namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), p=import_export_pose_column)
    cmds.button(l ="Export Current Pose", c=lambda x:gt_rig_pose_export(namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), p=import_export_pose_column) 


    ############# Animation Management Tab #############
    
    anim_management_tab = cmds.rowColumnLayout(nc=1, cw=[(1, 246)], cs=[(1,0)], p=tabs)
    
    cmds.separator(h=5, style='none') # Empty Space
    anim_title_column = cmds.rowColumnLayout(nc=1, cw=[(1, 245)], cs=cs_fk_ik_switches, p=anim_management_tab)
    cmds.text('Mirror Animation:', p=anim_title_column)
    cmds.separator(h=5, style='none', p=anim_title_column) # Empty Space
    
    mirror_anim_column = cmds.rowColumnLayout(nc=2, cw=cw_fk_ik_switches, cs=cs_fk_ik_switches, p=anim_management_tab)
    
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.separator(h=btn_margin, style='none') # Empty Space
    
    cmds.text('Right to Left:', p=mirror_anim_column) #R
    cmds.text('Left to Right:', p=mirror_anim_column) #L
    
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.separator(h=btn_margin, style='none') # Empty Space
    
    cmds.button(l ="Mirror ->", c=lambda x:gt_rig_anim_mirror([gt_ab_general_ctrls, gt_ab_ik_ctrls, gt_ab_fk_ctrls], 'right', namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), p=mirror_anim_column) #R
    cmds.button(l ="<- Mirror", c=lambda x:gt_rig_anim_mirror([gt_ab_general_ctrls, gt_ab_ik_ctrls, gt_ab_fk_ctrls], 'left', namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), p=mirror_anim_column) #L
    
    # Reset Animation
    anim_management_column = cmds.rowColumnLayout(nc=1, cw=[(1, 245)], cs=cs_fk_ik_switches, p=anim_management_tab)
    cmds.separator(h=15, style='none', p=anim_management_column) # Empty Space
    cmds.text('Reset Animation:', p=anim_management_column) #R
    cmds.separator(h=btn_margin, style='none', p=anim_management_column) # Empty Space
    cmds.button(l ="Reset Animation (Delete Keyframes)", c=lambda x:gt_rig_anim_reset(namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), p=anim_management_column)
    cmds.separator(h=btn_margin, style='none', p=anim_management_column) # Empty Space
    cmds.button(l ="Reset Animation and Pose", c=lambda x:reset_animation_and_pose(), p=anim_management_column)
    
    # Export Import Pose
    cmds.separator(h=17, style='none', p=anim_management_column) # Empty Space
    cmds.text('Import/Export Animation:', p=anim_management_column) 

    import_export_pose_column = cmds.rowColumnLayout(nc=2, cw=cw_fk_ik_switches, cs=cs_fk_ik_switches, p=anim_management_tab)
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.button(l ="Import Animation", c=lambda x:gt_rig_anim_import(namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), p=import_export_pose_column)
    cmds.button(l ="Export Animation", c=lambda x:gt_rig_anim_export(namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), p=import_export_pose_column) 
    
    ############# Settings Tab #############
    settings_tab = cmds.rowColumnLayout(nc=1, cw=[(1, 240)], cs=[(1,0)], p=tabs)
    
    if not is_secondary_instance:
        # General Settings
        enabled_bgc_color = (.4, .4, .4)
        disabled_bgc_color = (.3,.3,.3)
        cmds.separator(h=5, style='none') # Empty Space
        cmds.text('General Settings:', font='boldLabelFont')
        cmds.separator(h=5, style='none') # Empty Space
        cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 200), (3, 20)], cs=[(1,10)]) 
        
        # Allow Multiple Instances
        is_option_enabled = True
        cmds.text(' ', bgc=(enabled_bgc_color if is_option_enabled else disabled_bgc_color), h=20) # Tiny Empty Spac
        cmds.checkBox( label='  Allow Multiple Instances', value=gt_custom_rig_interface_settings.get('allow_multiple_instances'), ebg=True, cc=lambda x:invert_stored_setting('allow_multiple_instances'), en=is_option_enabled) 

        multiple_instances_help_message = 'This option will allow you to open multiple instances of this script. (multiple windows)\nThis can be helpful in case you are animating more than one character at the same time.\n\nThe extra instance will not be allowed to change settings or to set persistent options, so make sure to change these in your main (primary) instance of the script.'
        multiple_instances_help_title = 'Allow Multiple Instances'
        cmds.button(l ='?', bgc=enabled_bgc_color, c=lambda x:build_custom_help_window(multiple_instances_help_message, multiple_instances_help_title))
        
        # Transfer Data to Offset Control
        is_option_enabled = True
        cmds.text(' ', bgc=(enabled_bgc_color if is_option_enabled else disabled_bgc_color), h=20) # Tiny Empty Spac
        cmds.checkBox( label='  Transfer Data to Offset Control', value=gt_custom_rig_interface_settings.get('offset_target'), ebg=True, cc=lambda x:invert_stored_setting('offset_target'), en=is_option_enabled) 
        ''' TODO, create better description '''
        offset_target_thumbnail_help_message = 'Use this option to transfer the data to the IK offset control instead of transfering it directly to the IK control.'
        offset_target_thumbnail_help_title = 'Transfer Data to Offset Control'
        cmds.button(l ='?', bgc=enabled_bgc_color, c=lambda x:build_custom_help_window(offset_target_thumbnail_help_message, offset_target_thumbnail_help_title))
        
        # Export Thumbnail With Pose
        is_option_enabled = False
        cmds.text(' ', bgc=(enabled_bgc_color if is_option_enabled else disabled_bgc_color), h=20) # Tiny Empty Spac
        cmds.checkBox( label='  Export Thumbnail with Pose', value=gt_custom_rig_interface_settings.get('pose_export_thumbnail'), ebg=True, cc=lambda x:invert_stored_setting('pose_export_thumbnail'), en=is_option_enabled) 

        export_pose_thumbnail_help_message = 'This option will be included in future versions, thank you for your patience.\n\nExports a thumbnail ".jpg" file together with your ".pose" file.\nThis extra thumbnail file can be used to quickly undestand what you pose looks like before importing it.\n\nThe thumbnail is a screenshot of you active viewport at the moment of exporting the pose. If necessary, export it again to generate another thumbnail.'
        export_pose_thumbnail_help_title = 'Export Thumbnail with Pose'
        cmds.button(l ='?', bgc=enabled_bgc_color, c=lambda x:build_custom_help_window(export_pose_thumbnail_help_message, export_pose_thumbnail_help_title))
       
        # Reset Persistent Settings
        cmds.separator(h=btn_margin, style='none', p=settings_tab) # Empty Space
        settings_buttons_column = cmds.rowColumnLayout(nc=1, cw=[(1, 240)], cs=[(1,10)], p=settings_tab) 
        cmds.button(l ="Reset Persistent Settings", c=lambda x:reset_persistent_settings_rig_interface(), p=settings_buttons_column)
    else:
        # Secondary Instance Can't change settings
        cmds.rowColumnLayout(settings_tab, e=True, cw=[(1, 250)], cs=[(1,0)])
        cmds.separator(h=100, style='none') # Empty Space
        cmds.text('Use main instance for settings', font='boldLabelFont', en=False)

  
    ################# END TABS #################
    cmds.tabLayout( tabs, edit=True, tabLabel=((fk_ik_switch_tab, ' FK/IK '), (pose_management_tab, ' Pose '), (anim_management_tab, 'Animation'), (settings_tab, ' Settings ')))

    # Outside Margin
    cmds.separator(h=10, style='none', p=content_main) # Empty Space
 
    # Show and Lock Window
    cmds.showWindow(build_gui_custom_rig_interface)
    cmds.window(rig_interface_window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(rig_interface_window_name)
    if python_version == 3:
        widget = wrapInstance(int(qw), QWidget)
    else:
        widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/out_timeEditorAnimSource.png')
    if is_secondary_instance:
        icon = QIcon(':/animateSnapshot.png')
    widget.setWindowIcon(icon)

    # Update FK/IK States and Settings for the first run time
    update_fk_ik_buttons()
    update_stored_settings(is_secondary_instance)

    # Remove the focus from the textfield and give it to the window
    cmds.setFocus(rig_interface_window_name)

    # Main GUI Ends Here =================================================================================
    

def open_gt_tools_documentation():
    ''' Opens a web browser with the the auto rigger docs  '''
    cmds.showHelp ('https://github.com/TrevisanGMW/gt-tools/tree/release/docs#-gt-auto-biped-rigger-', absolute=True) 

def gt_rig_fk_ik_switch(ik_fk_dict, direction='fk_to_ik', namespace='', keyframe=False, start_time=0, end_time=0, method='sparse'):
    '''
    Transfer the position of the FK to IK or IK to FK systems in a seamless way, so the animator can easily switch between one and the other
    
            Parameters:
                ik_fk_dict (dict): A dicitionary containg the elements that are part of the system you want to switch
                direction (optinal, string): Either "fk_to_ik" or "ik_to_fk". It determines what is the source and what is the target.
                namespace (optinal, string): In case the rig has a namespace, it will be used to properly select the controls.
                
                
                keyframe (optinal, bool): If active it will created a keyframe at the current frame, move to the
                start_time (optinal, int): Where to create the first keyframe
                end_time (optinal, int): Where to create the last keyframe
                method (optinal, string): Method used for creating the keyframes. Either 'sparse' or 'bake'.
    '''
    def switch(match_only=False):
        '''
        Performs the switch operation.
        Commands were wrapped into a function to be used during the bake operation.
        
                Parameters:
                    match_only (optional, bool) If active (True) it will only match the pose, but not switch
        
                Returns:
                    attr_value (float): Value which the influence attribute was set to. Either 1 (fk_to_ik) or 0 (ik_to_fk).
                                        This value is returned only if "match_only" is False. Otherwise, expect None.
        '''
        try:
            ik_fk_ns_dict = {}
            for obj in ik_fk_dict:
                ik_fk_ns_dict[obj] = namespace + ik_fk_dict.get(obj)
            
            fk_pairs = [[ik_fk_ns_dict.get('base_ik_jnt'), ik_fk_ns_dict.get('base_fk_ctrl')],
                        [ik_fk_ns_dict.get('mid_ik_jnt'), ik_fk_ns_dict.get('mid_fk_ctrl')],
                        [ik_fk_ns_dict.get('end_ik_jnt'), ik_fk_ns_dict.get('end_fk_ctrl')]]            
                                    
            if direction == 'fk_to_ik':
                if ik_fk_dict.get('end_ik_reference') != '':
                    cmds.matchTransform(ik_fk_ns_dict.get('end_ik_ctrl'), ik_fk_ns_dict.get('end_ik_reference'), pos=1, rot=1)
                else:
                    cmds.matchTransform(ik_fk_ns_dict.get('end_ik_ctrl'), ik_fk_ns_dict.get('end_fk_jnt'), pos=1, rot=1)
                cmds.matchTransform(ik_fk_ns_dict.get('pvec_ik_ctrl'), ik_fk_ns_dict.get('mid_ik_reference'), pos=1, rot=1)

                if not match_only:
                    cmds.setAttr(ik_fk_ns_dict.get('switch_ctrl') + '.influenceSwitch', 1)
                return 1
            if direction == 'ik_to_fk':
                for pair in fk_pairs:
                    cmds.matchTransform(pair[1], pair[0], pos=1, rot=1)
                    pass
                if not match_only:
                    cmds.setAttr(ik_fk_ns_dict.get('switch_ctrl') + '.influenceSwitch', 0)
                return 0
        except Exception as e:
            cmds.warning('An error occurred. Please check if a namespace is necessary or if a control was deleted.     Error: ' + str(e))
    
    
    def print_inview_feedback():
        '''
        Prints feedback using inView messages so the user knows what operation was executed.
        '''
                
        is_valid_message = True
        message_target = 'IK' if direction == 'fk_to_ik' else 'FK'
        
        # Try to figure it out system:
        message_direction = ''
        pvec_ik_ctrl = ik_fk_dict.get(next(iter(ik_fk_dict)))
        if pvec_ik_ctrl.startswith('right_'):
            message_direction = 'right'
        elif pvec_ik_ctrl.startswith('left_'):
            message_direction = 'left'
        else:
            is_valid_message = False
        
        message_limb = ''
        if 'knee' in pvec_ik_ctrl:
            message_limb = 'leg'
        elif 'elbow' in pvec_ik_ctrl:
            message_limb = 'arm'
        else:
            is_valid_message = False
        
        message_range = ''
        if keyframe:
            message_range = '(Start: <span style=\"color:#FFFFFF;\">' + str(start_time) + '</span> End: <span style=\"color:#FFFFFF;\">' + str(end_time) + '</span> Method: <span style=\"color:#FFFFFF;\">' + method.capitalize() + '</span> )'
        

        if is_valid_message:
            # Print Feedback
            unique_message = '<' + str(random.random()) + '>'
            cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FFFFFF;\">Switched ' + message_direction + ' ' + message_limb + ' to </span><span style=\"color:#FF0000;text-decoration:underline;\">' + message_target +'</span>  ' + message_range, pos='botLeft', fade=True, alpha=.9)
    


    # Find Available Controls
    available_ctrls = []

    for key in ik_fk_dict:
        if cmds.objExists(namespace + ik_fk_dict.get(key)):
            available_ctrls.append(ik_fk_dict.get(key))
        if cmds.objExists(namespace + key):
            available_ctrls.append(key)
    
    # No Controls were found
    if len(available_ctrls) == 0:
        is_valid=False
        cmds.warning('No controls were found. Make sure you are using the correct namespace.')

    else:
        if ik_fk_dict.get('incompatible_attr_holder'):
            auto_clavicle_value = cmds.getAttr(ik_fk_dict.get('incompatible_attr_holder') + '.autoClavicleInfluence')
            cmds.setAttr(ik_fk_dict.get('incompatible_attr_holder') + '.autoClavicleInfluence', 0)

        if keyframe:
            if method.lower() == 'sparse': # Only Influence Switch
                original_time = cmds.currentTime(q=True)
                cmds.currentTime(start_time)
                cmds.setKeyframe(namespace + ik_fk_dict.get('switch_ctrl'), time=start_time, attribute='influenceSwitch')
                cmds.currentTime(end_time)
                switch()
                cmds.setKeyframe(namespace + ik_fk_dict.get('switch_ctrl'), time=end_time, attribute='influenceSwitch')
                cmds.currentTime(original_time)
                print_inview_feedback()
            elif method.lower() == 'bake':
                if start_time >= end_time:
                    cmds.warning('Invalid range. Please review the stard and end frame and try again.')
                else:
                    original_time = cmds.currentTime(q=True)
                    cmds.currentTime(start_time)
                    current_time = cmds.currentTime(q=True)
                    cmds.setKeyframe(namespace + ik_fk_dict.get('switch_ctrl'), time=current_time, attribute='influenceSwitch') # Start Switch
                    for index in range(end_time - start_time):
                        cmds.currentTime(current_time)
                        switch(match_only=True)
                        if direction == 'fk_to_ik':
                            for channel in ['t','r']:
                                for dimension in ['x', 'y', 'z']:
                                    cmds.setKeyframe(namespace + ik_fk_dict.get('end_ik_ctrl'), time=current_time, attribute=channel+dimension) # Wrist IK Ctrl
                                    cmds.setKeyframe(namespace + ik_fk_dict.get('pvec_ik_ctrl'), time=current_time, attribute=channel+dimension) # PVec Elbow IK Ctrl

                        if direction == 'ik_to_fk':
                            for channel in ['t','r']:
                                for dimension in ['x', 'y', 'z']:
                                    cmds.setKeyframe(namespace + ik_fk_dict.get('base_fk_ctrl'), time=current_time, attribute=channel+dimension) # Shoulder FK Ctrl
                                    cmds.setKeyframe(namespace + ik_fk_dict.get('end_fk_ctrl'), time=current_time, attribute=channel+dimension) # Wrist FK Ctrl
                                    cmds.setKeyframe(namespace + ik_fk_dict.get('mid_fk_ctrl'), time=current_time, attribute=channel+dimension) # Elbow FK Ctrl
                        current_time += 1
                    switch()
                    cmds.setKeyframe(namespace + ik_fk_dict.get('switch_ctrl'), time=current_time, attribute='influenceSwitch') # End Switch
                    cmds.currentTime(original_time)
                    print_inview_feedback()
            else:
                cmds.warning('Invalid method was provided. Must be either "sparse" or "bake", but got ' + method)
        else:
            switch()
            print_inview_feedback()
            
        if ik_fk_dict.get('incompatible_attr_holder'):
            cmds.setAttr(ik_fk_dict.get('incompatible_attr_holder') + '.autoClavicleInfluence', auto_clavicle_value)
            if auto_clavicle_value != 0:
                # Print Feedback
                cmds.inViewMessage(amg='</span><span style=\"color:#FF0000;text-decoration:underline;\">Warning:</span><span style=\"color:#FFFFFF;\"> Auto clavicle was activated, any unexpected pose offset is likely coming from this automation.', pos='botLeft', fade=True, alpha=.9, fadeStayTime=2000)
    
            

def gt_rig_fk_ik_switch_auto(ik_fk_dict, namespace='', keyframe=False, start_time=0, end_time=0, method='sparse'):
    ''' 
    Calls gt_rig_fk_ik_switch, but switches (toggles) between FK and IK based on the current influence number. 
    It automatically checks the influenceSwitch value attribute and determines what direction to take it. "0-0.5":IK and "0.5-1":FK
    
            Parameters:
                ik_fk_dict (dictionary): A dicitionary containg the elements that are part of the system you want to switch
                namespace (string): In case the rig has a namespace, it will be used to properly select the controls.
                
                keyframe (optinal, bool): If active it will created a keyframe at the current frame, move to the
                start_time (optinal, int): Where to create the first keyframe
                end_time (optinal, int): Where to create the last keyframe
                method (optinal, string): Method used for creating the keyframes. Either 'sparse' or 'bake'.    
    '''
    try:
        if cmds.objExists(namespace + ik_fk_dict.get('switch_ctrl')):
            current_system = cmds.getAttr(namespace + ik_fk_dict.get('switch_ctrl') + '.influenceSwitch')
            if current_system < 0.5:
                gt_rig_fk_ik_switch(ik_fk_dict, direction='fk_to_ik', namespace=namespace, keyframe=keyframe, start_time=start_time, end_time=end_time, method=method)
            else:
                gt_rig_fk_ik_switch(ik_fk_dict, direction='ik_to_fk', namespace=namespace, keyframe=keyframe, start_time=start_time, end_time=end_time, method=method)
        else:
            cmds.warning('Switch control was not found. Please check if a namespace is necessary.')
    except Exception as e:
        cmds.warning('An error occurred. Please check if a namespace is necessary.     Error: ' + str(e))




def gt_rig_pose_reset(gt_ab_ik_ctrls, gt_ab_fk_ctrls, gt_ab_center_ctrls, namespace=''):
    '''
    Reset transforms list of controls back to 0 Transalte and Rotate values. 

        Parameters:
                gt_ab_ik_ctrls (dict, list) : A list or dictionary of IK controls without their side prefix (e.g. "_wrist_ctrl")
                gt_ab_fk_ctrls (dict, list) : A list or dictionary of FK controls without their side prefix (e.g. "_wrist_ctrl")
                gt_ab_center_ctrls (dict, list) : A list or dictionary of center controls (full names) (e.g. "spine01_ctrl")
                namespace (string): In case the rig has a namespace, it will be used to properly select the controls.
    
    '''
    available_ctrls = []
    for obj in gt_ab_ik_ctrls:
        if cmds.objExists(namespace + left_prefix + obj):
            available_ctrls.append(left_prefix + obj)
        if cmds.objExists(namespace + right_prefix + obj):
            available_ctrls.append(right_prefix + obj)
            
    for obj in gt_ab_fk_ctrls:
        if cmds.objExists(namespace + left_prefix + obj):
            available_ctrls.append(left_prefix + obj)
        if cmds.objExists(namespace + right_prefix + obj):
            available_ctrls.append(right_prefix + obj)
            
    for obj in gt_ab_general_ctrls:
        if cmds.objExists(namespace + left_prefix + obj):
            available_ctrls.append(left_prefix + obj)
        if cmds.objExists(namespace + right_prefix + obj):
            available_ctrls.append(right_prefix + obj)
            
    for obj in gt_ab_center_ctrls:
        if cmds.objExists(namespace + obj):
            available_ctrls.append(obj)
    
    if len(available_ctrls) == 0:
        cmds.warning('No controls were found. Please check if a namespace is necessary.')
    else:
        unique_message = '<' + str(random.random()) + '>'
        cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FFFFFF;\">Pose </span><span style=\"color:#FF0000;text-decoration:underline;\"> Reset!</span>', pos='botLeft', fade=True, alpha=.9)
    
    for ctrl in available_ctrls:
        dimensions = ['x','y','z']
        transforms = ['t', 'r', 's']
        for transform in transforms:
            for dimension in dimensions:
                try:
                    if cmds.getAttr(namespace + ctrl + '.' + transform + dimension, lock=True) is False:
                        cmds.setAttr(namespace + ctrl + '.' + transform + dimension, 0)
                except:
                    pass
    
    # Special Cases
    special_case_ctrls = ['left_fingers_ctrl', 'right_fingers_ctrl']
    for ctrl in special_case_ctrls:
        if cmds.objExists(namespace + ctrl):
            if cmds.getAttr(namespace + ctrl + '.' + 'sz', lock=True) is False:
                    cmds.setAttr(namespace + ctrl + '.' + 'sz', 2)
                    
def gt_rig_pose_mirror(gt_ab_ctrls, source_side, namespace=''):
    '''
    Mirrors the character pose from one side to the other

        Parameters:
                gt_ab_ctrls (dict) : A list of dictionaries of controls without their side prefix (e.g. "_wrist_ctrl")
                namespace (string): In case the rig has a namespace, it will be used to properly select the controls.
    
    '''
    # Merge Dictionaries
    gt_ab_ctrls_dict = {}
    for ctrl_dict in gt_ab_ctrls:
        gt_ab_ctrls_dict.update(ctrl_dict)
   
    # Find available Ctrls
    available_ctrls = []
    for obj in gt_ab_ctrls_dict:
        if cmds.objExists(namespace + left_prefix + obj):
            available_ctrls.append(left_prefix + obj)
        if cmds.objExists(namespace + right_prefix + obj):
            available_ctrls.append(right_prefix + obj)
            
    # Start Mirroring
    if len(available_ctrls) != 0:
     
        errors = []
            
        right_side_objects = []
        left_side_objects = []

        for obj in available_ctrls:  
            if right_prefix in obj:
                right_side_objects.append(obj)
                
        for obj in available_ctrls:  
            if left_prefix in obj:
                left_side_objects.append(obj)
                
        for left_obj in left_side_objects:
            for right_obj in right_side_objects:
                remove_side_tag_left = left_obj.replace(left_prefix,'')
                remove_side_tag_right = right_obj.replace(right_prefix,'')
                if remove_side_tag_left == remove_side_tag_right:
                    # print(right_obj + ' was paired with ' + left_obj)
                    
                    key = gt_ab_ctrls_dict.get(remove_side_tag_right) # TR = [(ivnerted?,ivnerted?,ivnerted?),(ivnerted?,ivnerted?,ivnerted?)]
                    transforms = []

                    # Mirroring Transform?, Inverting it? (X,Y,Z), Transform name.
                    transforms.append([True, key[0][0], 'tx']) 
                    transforms.append([True, key[0][1], 'ty'])
                    transforms.append([True, key[0][2], 'tz'])
                    transforms.append([True, key[1][0], 'rx'])
                    transforms.append([True, key[1][1], 'ry'])
                    transforms.append([True, key[1][2], 'rz'])
                    
                    if len(key) > 2: # Mirroring Scale?
                        transforms.append([True, False, 'sx'])
                        transforms.append([True, False, 'sy'])
                        transforms.append([True, False, 'sz'])
                    
                    # Transfer Right to Left
                    if source_side is 'right':
                        for transform in transforms:
                            if transform[0]: # Using Transform?
                                if transform[1]: # Inverted?
                                    source_transform = (cmds.getAttr(namespace + right_obj + '.' + transform[2]) * -1)
                                else:
                                    source_transform = cmds.getAttr(namespace + right_obj + '.' + transform[2])

                                if not cmds.getAttr(namespace + left_obj + '.' + transform[2], lock=True):
                                    cmds.setAttr(namespace + left_obj + '.' + transform[2], source_transform)
                                else:
                                    errors.append(namespace + left_obj + ' "' + transform[2]+'" is locked.' )
                                
                    # Transfer Left to Right
                    if source_side is 'left':
                        for transform in transforms:
                            if transform[0]: # Using Transform?
                                if transform[1]: # Inverted?
                                    source_transform = (cmds.getAttr(namespace + left_obj + '.' + transform[2]) * -1)
                                else:
                                    source_transform = cmds.getAttr(namespace + left_obj + '.' + transform[2])
                                
                                if not cmds.getAttr(namespace + right_obj + '.' + transform[2], lock=True):
                                    cmds.setAttr(namespace + right_obj + '.' + transform[2], source_transform)
                                else:
                                    errors.append(namespace + right_obj + ' "' + transform[2]+'" is locked.' )
                    
        # Print Feedback
        unique_message = '<' + str(random.random()) + '>'
        source_message = '(Left to Right)'
        if source_side == 'right':
            source_message = '(Right to Left)'
        cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FFFFFF;\">Pose </span><span style=\"color:#FF0000;text-decoration:underline;\"> mirrored!</span> ' + source_message, pos='botLeft', fade=True, alpha=.9)
                        
        if len(errors) != 0:
            unique_message = '<' + str(random.random()) + '>'
            if len(errors) == 1:
                is_plural = 'attribute was'
            else:
                is_plural = 'attributes were'
            for error in errors:
                print(str(error))
            sys.stdout.write(str(len(errors)) + ' locked '+ is_plural + ' ignored. (Open Script Editor to see a list)\n')
    else:
        cmds.warning('No controls were found. Please check if a namespace is necessary.')
    cmds.setFocus("MayaWindow")
    
    
def gt_rig_pose_export(namespace =''):
    ''' 
    Exports a Pose (JSON) file containing the translate, rotate and scale data from the rig controls (used to export a pose)
    Added a variable called "gt_auto_biped_export_method" after v1.3, so the extraction method can be stored.
    
        Parameters:
            namespace (string): In case the rig has a namespace, it will be used to properly select the controls.
    
    ''' 
    # Validate Operation and Write file
    is_valid = True
    successfully_created_file = False

    # Find Available Controls
    available_ctrls = []
    for obj in gt_ab_ik_ctrls:
        if cmds.objExists(namespace + left_prefix + obj):
            available_ctrls.append(left_prefix + obj)
        if cmds.objExists(namespace + right_prefix + obj):
            available_ctrls.append(right_prefix + obj)
            
    for obj in gt_ab_fk_ctrls:
        if cmds.objExists(namespace + left_prefix + obj):
            available_ctrls.append(left_prefix + obj)
        if cmds.objExists(namespace + right_prefix + obj):
            available_ctrls.append(right_prefix + obj)
            
    for obj in gt_ab_general_ctrls:
        if cmds.objExists(namespace + left_prefix + obj):
            available_ctrls.append(left_prefix + obj)
        if cmds.objExists(namespace + right_prefix + obj):
            available_ctrls.append(right_prefix + obj)
            
    for obj in gt_ab_center_ctrls:
        if cmds.objExists(namespace + obj):
            available_ctrls.append(obj)
    
    # No Controls were found
    if len(available_ctrls) == 0:
        is_valid=False
        cmds.warning('No controls were found. Make sure you are using the correct namespace.')


    if is_valid:
        file_name = cmds.fileDialog2(fileFilter=script_name + " - POSE File (*.pose)", dialogStyle=2, okCaption= 'Export', caption= 'Exporting Rig Pose for "' + script_name + '"') or []
        if len(file_name) > 0:
            pose_file = file_name[0]
            successfully_created_file = True
            

    if successfully_created_file and is_valid:
        export_dict = {'gt_interface_version' : script_version, 'gt_export_method' : 'object-space'}
        for obj in available_ctrls:
            translate = cmds.getAttr(obj + '.translate')[0]
            rotate = cmds.getAttr(obj + '.rotate')[0]
            scale = cmds.getAttr(obj + '.scale')[0]
            to_save = [obj, translate, rotate, scale]
            export_dict[obj] = to_save
    
        try: 
            with open(pose_file, 'w') as outfile:
                json.dump(export_dict, outfile, indent=4)

            unique_message = '<' + str(random.random()) + '>'
            cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FFFFFF;\">Current Pose exported to </span><span style=\"color:#FF0000;text-decoration:underline;\">' + os.path.basename(file_name[0]) +'</span><span style=\"color:#FFFFFF;\">.</span>', pos='botLeft', fade=True, alpha=.9)
            sys.stdout.write('Pose exported to the file "' + pose_file + '".')
        except Exception as e:
            print (e)
            successfully_created_file = False
            cmds.warning('Couldn\'t write to file. Please make sure the exporting directory is accessible.')




def gt_rig_pose_import(debugging=False, debugging_path='', namespace=''):
    ''' 
    Imports a POSE (JSON) file containing the translate, rotate and scale data for the rig controls (exported using the "gt_rig_pose_export" function)
    Uses the imported data to set the translate, rotate and scale position of every control curve
    
            Parameters:
                debugging (bool): If debugging, the function will attempt to auto load the file provided in the "debugging_path" parameter
                debugging_path (string): Debugging path for the import function
                namespace (string): In case the rig has a namespace, it will be used to properly select the controls.
    
    TODO
        Check import method to use the proper method when setting attributes.
        Exporting using the export button uses "setAttr", extract functions will use "xform" instead.
    
    ''' 
    def set_unlocked_os_attr(target, attr, value):
        ''' 
        Sets an attribute to the provided value in case it's not locked (Uses "cmds.setAttr" function so object space)
        
                Parameters:
                    target (string): Name of the target object (object that will receive transforms)
                    attr (string): Name of the attribute to apply (no need to add ".", e.g. "rx" would be enough)
                    value (float): Value used to set attribute. e.g. 1.5, 2, 5...
        
        '''
        try:
            if not cmds.getAttr(target + '.' + attr, lock=True):
                cmds.setAttr(target + '.' + attr, value)
        except:
            pass
            
    def set_unlocked_ws_attr(target, attr, value_tuple):
        ''' 
        Sets an attribute to the provided value in case it's not locked (Uses "cmds.xform" function with world space)
        
                Parameters:
                    target (string): Name of the target object (object that will receive transforms)
                    attr (string): Name of the attribute to apply (no need to add ".", e.g. "rx" would be enough)
                    value_tuple (tuple): A tuple with three (3) floats used to set attributes. e.g. (1.5, 2, 5)
        
        '''
        try:
            if attr == 'translate':
                cmds.xform(target, ws=True, t=value_tuple)
            if attr == 'rotate':
                cmds.xform(target, ws=True, ro=value_tuple)
            if attr == 'scale':
                cmds.xform(target, ws=True, s=value_tuple)
        except:
            pass
     
     
    # Find Available Controls
    available_ctrls = []
    for obj in gt_ab_ik_ctrls:
        if cmds.objExists(namespace + left_prefix + obj):
            available_ctrls.append(left_prefix + obj)
        if cmds.objExists(namespace + right_prefix + obj):
            available_ctrls.append(right_prefix + obj)
            
    for obj in gt_ab_fk_ctrls:
        if cmds.objExists(namespace + left_prefix + obj):
            available_ctrls.append(left_prefix + obj)
        if cmds.objExists(namespace + right_prefix + obj):
            available_ctrls.append(right_prefix + obj)
            
    for obj in gt_ab_general_ctrls:
        if cmds.objExists(namespace + left_prefix + obj):
            available_ctrls.append(left_prefix + obj)
        if cmds.objExists(namespace + right_prefix + obj):
            available_ctrls.append(right_prefix + obj)
            
    for obj in gt_ab_center_ctrls:
        if cmds.objExists(namespace + obj):
            available_ctrls.append(obj)
    
    # Track Current State
    import_version = 0.0
    import_method = 'object-space'
    
    if not debugging:
        file_name = cmds.fileDialog2(fileFilter=script_name + " - POSE File (*.pose)", dialogStyle=2, fileMode= 1, okCaption= 'Import', caption= 'Importing Proxy Pose for "' + script_name + '"') or []
    else:
        file_name = [debugging_path]
    
    if len(file_name) > 0:
        pose_file = file_name[0]
        file_exists = True
    else:
        file_exists = False
    
    if file_exists:
        try: 
            with open(pose_file) as json_file:
                data = json.load(json_file)
                try:
                    is_valid_file = True
                    is_operation_valid = True

                    if not data.get('gt_interface_version'):
                        is_valid_file = False
                        cmds.warning('Imported file doesn\'t seem to be compatible or is missing data.')
                    else:                       
                        import_version = float(re.sub("[^0-9]", "", str(data.get('gt_interface_version'))))
                
                    if data.get('gt_export_method'):
                      import_method = data.get('gt_export_method')
                
                    if len(available_ctrls) == 0:
                        cmds.warning('No controls were found. Please check if a namespace is necessary.')
                        is_operation_valid = False
                        
                    if is_operation_valid:
                        # Object-Space
                        for ctrl in data:
                            if ctrl != 'gt_interface_version' and ctrl != 'gt_export_method':
                                curent_object = data.get(ctrl) # Name, T, R, S
                                if cmds.objExists(namespace + curent_object[0]):
                                    set_unlocked_os_attr(namespace + curent_object[0], 'tx', curent_object[1][0])
                                    set_unlocked_os_attr(namespace + curent_object[0], 'ty', curent_object[1][1])
                                    set_unlocked_os_attr(namespace + curent_object[0], 'tz', curent_object[1][2])
                                    set_unlocked_os_attr(namespace + curent_object[0], 'rx', curent_object[2][0])
                                    set_unlocked_os_attr(namespace + curent_object[0], 'ry', curent_object[2][1])
                                    set_unlocked_os_attr(namespace + curent_object[0], 'rz', curent_object[2][2])
                                    set_unlocked_os_attr(namespace + curent_object[0], 'sx', curent_object[3][0])
                                    set_unlocked_os_attr(namespace + curent_object[0], 'sy', curent_object[3][1])
                                    set_unlocked_os_attr(namespace + curent_object[0], 'sz', curent_object[3][2])
                        
                        unique_message = '<' + str(random.random()) + '>'
                        cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FFFFFF;\">Pose imported from </span><span style=\"color:#FF0000;text-decoration:underline;\">' + os.path.basename(pose_file) +'</span><span style=\"color:#FFFFFF;\">.</span>', pos='botLeft', fade=True, alpha=.9)
                        sys.stdout.write('Pose imported from the file "' + pose_file + '".')
                    
                except Exception as e:
                    print(e)
                    cmds.warning('An error occured when importing the pose. Make sure you imported a valid POSE file.')
        except:
            file_exists = False
            cmds.warning('Couldn\'t read the file. Please make sure the selected file is accessible.')



def gt_rig_pose_flip(namespace =''):
    ''' 
    Flips the current pose (Essentially like a mirror in both sides at te same time)
    Creates a Pose dictionary containing the translate, rotate and scale data from the rig controls (used to store a pose)
    
        Parameters:
            namespace (string): In case the rig has a namespace, it will be used to properly select the controls.
    
    ''' 
    # Validate Operation and Write file
    is_valid = True

    # Find Available Controls
    available_ctrls = []
    for obj in gt_ab_ik_ctrls:
        if cmds.objExists(namespace + left_prefix + obj):
            available_ctrls.append(left_prefix + obj)
        if cmds.objExists(namespace + right_prefix + obj):
            available_ctrls.append(right_prefix + obj)
            
    for obj in gt_ab_fk_ctrls:
        if cmds.objExists(namespace + left_prefix + obj):
            available_ctrls.append(left_prefix + obj)
        if cmds.objExists(namespace + right_prefix + obj):
            available_ctrls.append(right_prefix + obj)
            
    for obj in gt_ab_general_ctrls:
        if cmds.objExists(namespace + left_prefix + obj):
            available_ctrls.append(left_prefix + obj)
        if cmds.objExists(namespace + right_prefix + obj):
            available_ctrls.append(right_prefix + obj)
            
    for obj in gt_ab_center_ctrls:
        if cmds.objExists(namespace + obj):
            available_ctrls.append(obj)
    
    # No Controls were found
    if len(available_ctrls) == 0:
        is_valid=False
        cmds.warning('No controls were found. Make sure you are using the correct namespace.')


    if is_valid:
        pose_dict = {}
        for obj in available_ctrls:
            # Get Pose
            translate = cmds.getAttr(obj + '.translate')[0]
            rotate = cmds.getAttr(obj + '.rotate')[0]
            scale = cmds.getAttr(obj + '.scale')[0]
            to_save = [obj, translate, rotate, scale]
            pose_dict[obj] = to_save
            
            # Reset Current Pose ?
            # gt_rig_pose_reset(gt_ab_ik_ctrls, gt_ab_fk_ctrls, gt_ab_center_ctrls, namespace=namespace)
        
            
            # TODO
            # Set Pose
            # for ctrl in pose_dict:
            #     curent_object = pose_dict.get(ctrl) # Name, T, R, S
            #     if cmds.objExists(namespace + curent_object[0]):
            #         set_unlocked_os_attr(namespace + curent_object[0], 'tx', curent_object[1][0])
            #         set_unlocked_os_attr(namespace + curent_object[0], 'ty', curent_object[1][1])
            #         set_unlocked_os_attr(namespace + curent_object[0], 'tz', curent_object[1][2])
            #         set_unlocked_os_attr(namespace + curent_object[0], 'rx', curent_object[2][0])
            #         set_unlocked_os_attr(namespace + curent_object[0], 'ry', curent_object[2][1])
            #         set_unlocked_os_attr(namespace + curent_object[0], 'rz', curent_object[2][2])
            #         set_unlocked_os_attr(namespace + curent_object[0], 'sx', curent_object[3][0])
            #         set_unlocked_os_attr(namespace + curent_object[0], 'sy', curent_object[3][1])
            #         set_unlocked_os_attr(namespace + curent_object[0], 'sz', curent_object[3][2])
            


def gt_rig_anim_reset(namespace=''):
    '''
    Deletes all keyframes and resets pose (Doesn't include Set Driven Keys)
    
            Parameters:
                namespace (string): In case the rig has a namespace, it will be used to properly select the controls.    
    '''   
    function_name = 'GT Reset Rig Animation'
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    try:
        keys_ta = cmds.ls(type='animCurveTA')
        keys_tl = cmds.ls(type='animCurveTL')
        keys_tt = cmds.ls(type='animCurveTT')
        keys_tu = cmds.ls(type='animCurveTU')
        deleted_counter = 0
        all_keyframes = keys_ta + keys_tl + keys_tt + keys_tu
        for key in all_keyframes:
            try:
                key_target_namespace = cmds.listConnections(key, destination=True)[0].split(':')[0]
                if key_target_namespace == namespace.replace(':', '') or len(cmds.listConnections(key, destination=True)[0].split(':')) == 1:
                    cmds.delete(key)
                    deleted_counter += 1
            except:
                pass   
        message = '<span style=\"color:#FF0000;text-decoration:underline;\">' +  str(deleted_counter) + ' </span>'
        is_plural = 'keyframe nodes were'
        if deleted_counter == 1:
            is_plural = 'keyframe node was'
        message += is_plural + ' deleted.'
        
        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)
        
        # gt_rig_pose_reset(gt_ab_ik_ctrls, gt_ab_fk_ctrls, gt_ab_center_ctrls, namespace) # Add as an option?
        
    except Exception as e:
        cmds.warning(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
        
        
def gt_rig_anim_mirror(gt_ab_ctrls, source_side, namespace=''):
    '''
    Mirrors the character animation from one side to the other

        Parameters:
                gt_ab_ctrls (dict) : A list of dictionaries of controls without their side prefix (e.g. "_wrist_ctrl")
                namespace (string): In case the rig has a namespace, it will be used to properly select the controls.
    
    '''
    
    def invert_float_list_values(float_list):
        '''
        Returns a list where all the float values are inverted. For example, if the value is 5, it will then become -5.

            Parameters:
                    float_list (list) : A list of floats.
                    
            Returns:
                    inverted_float_list (list): A list of floats with their values inverted
    
        '''

        inverted_values = []
        for val in float_list:
            inverted_values.append(val* -1)
        return inverted_values

    
    # Merge Dictionaries
    gt_ab_ctrls_dict = {}
    for ctrl_dict in gt_ab_ctrls:
        gt_ab_ctrls_dict.update(ctrl_dict)
   
    # Find available Ctrls
    available_ctrls = []
    for obj in gt_ab_ctrls_dict:
        if cmds.objExists(namespace + left_prefix + obj):
            available_ctrls.append(left_prefix + obj)
        if cmds.objExists(namespace + right_prefix + obj):
            available_ctrls.append(right_prefix + obj)
            
    # Start Mirroring
    if len(available_ctrls) != 0:
     
        errors = []
            
        right_side_objects = []
        left_side_objects = []

        for obj in available_ctrls:  
            if right_prefix in obj:
                right_side_objects.append(obj)
                
        for obj in available_ctrls:  
            if left_prefix in obj:
                left_side_objects.append(obj)
                
        for left_obj in left_side_objects:
            for right_obj in right_side_objects:
                remove_side_tag_left = left_obj.replace(left_prefix,'')
                remove_side_tag_right = right_obj.replace(right_prefix,'')
                if remove_side_tag_left == remove_side_tag_right:
                    # print(right_obj + ' was paired with ' + left_obj)
                    
                    key = gt_ab_ctrls_dict.get(remove_side_tag_right) # TR = [(ivnerted?,ivnerted?,ivnerted?),(ivnerted?,ivnerted?,ivnerted?)]
                    transforms = []

                    # Mirroring Transform?, Inverting it? (X,Y,Z), Transform name.
                    transforms.append([True, key[0][0], 'tx']) 
                    transforms.append([True, key[0][1], 'ty'])
                    transforms.append([True, key[0][2], 'tz'])
                    transforms.append([True, key[1][0], 'rx'])
                    transforms.append([True, key[1][1], 'ry'])
                    transforms.append([True, key[1][2], 'rz'])
                    
                    if len(key) > 2: # Mirroring Scale?
                        transforms.append([True, False, 'sx'])
                        transforms.append([True, False, 'sy'])
                        transforms.append([True, False, 'sz'])
                    
                    # Transfer Right to Left 
                    if source_side is 'right':
                        for transform in transforms:
                            if transform[0]: # Using Transform? Inverted? Name of the Attr
                                try:
                                    attr = transform[2]
                                    
                                    # Get Values
                                    frames = cmds.keyframe(namespace + right_obj, q=1, at=attr)
                                    values = cmds.keyframe(namespace + right_obj, q=1, at=attr, valueChange=True)
                                    
                                    in_angle_tangent = cmds.keyTangent(namespace + right_obj, at=attr, inAngle=True, query=True)
                                    out_angle_tanget = cmds.keyTangent(namespace + right_obj, at=attr, outAngle=True, query=True)
                                    is_locked = cmds.keyTangent(namespace + right_obj, at=attr, weightLock=True, query=True)
                                    in_weight = cmds.keyTangent(namespace + right_obj, at=attr, inWeight=True, query=True)
                                    out_weight = cmds.keyTangent(namespace + right_obj, at=attr, outWeight=True, query=True)
                                    in_tangent_type = cmds.keyTangent(namespace + right_obj, at=attr, inTangentType=True, query=True)
                                    out_tangent_type = cmds.keyTangent(namespace + right_obj, at=attr, outTangentType=True, query=True)
                                    
                                    if transform[1]: # Inverted?
                                        values = invert_float_list_values(values)
                                        in_angle_tangent = invert_float_list_values(in_angle_tangent)
                                        out_angle_tanget = invert_float_list_values(out_angle_tanget)
                                        in_weight = invert_float_list_values(in_weight)
                                        out_weight = invert_float_list_values(out_weight)


                                    # Set Keys/Values
                                    for index in range(len(values)):
                                        time = frames[index]
                                        cmds.setKeyframe(namespace + left_obj, time=time, attribute=attr, value=values[index])
                                        # Set Tangents
                                        cmds.keyTangent(namespace + left_obj, at=attr, time=(time,time), lock=is_locked[index], e=True)
                                        cmds.keyTangent(namespace + left_obj, at=attr, time=(time,time), inAngle=in_angle_tangent[index], e=True)
                                        cmds.keyTangent(namespace + left_obj, at=attr, time=(time,time), outAngle=out_angle_tanget[index], e=True)
                                        cmds.keyTangent(namespace + left_obj, at=attr, time=(time,time), inWeight=in_weight[index], e=True)
                                        cmds.keyTangent(namespace + left_obj, at=attr, time=(time,time), outWeight=out_weight[index], e=True)
                                        cmds.keyTangent(namespace + left_obj, at=attr, time=(time,time), inTangentType=in_tangent_type[index], e=True)
                                        cmds.keyTangent(namespace + left_obj, at=attr, time=(time,time), outTangentType=out_tangent_type[index], e=True)
                                except:
                                    pass # 0 keyframes

                        # Other Attributes
                        attributes = cmds.listAnimatable(namespace + right_obj)
                        default_channels = ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ']
                        for attr in attributes:
                            try:
                                short_attr = attr.split('.')[-1]
                                if short_attr not in default_channels:
                                     # Get Keys/Values
                                    frames = cmds.keyframe(namespace + right_obj, q=1, at=short_attr)
                                    values = cmds.keyframe(namespace + right_obj, q=1, at=short_attr, valueChange=True)

                                    # Set Keys/Values
                                    for index in range(len(values)):
                                        cmds.setKeyframe(namespace + left_obj, time=frames[index], attribute=short_attr, value=values[index])
                            except:
                                pass # 0 keyframes
                    
                    # Transfer Left to Right
                    if source_side is 'left':
                        for transform in transforms:
                            if transform[0]: # Using Transform? Inverted? Name of the Attr
                                try:
                                    attr = transform[2]
                                    
                                    # Get Values
                                    frames = cmds.keyframe(namespace + left_obj, q=1, at=attr)
                                    values = cmds.keyframe(namespace + left_obj, q=1, at=attr, valueChange=True)
                                    
                                    in_angle_tangent = cmds.keyTangent(namespace + left_obj, at=attr, inAngle=True, query=True)
                                    out_angle_tanget = cmds.keyTangent(namespace + left_obj, at=attr, outAngle=True, query=True)
                                    is_locked = cmds.keyTangent(namespace + left_obj, at=attr, weightLock=True, query=True)
                                    in_weight = cmds.keyTangent(namespace + left_obj, at=attr, inWeight=True, query=True)
                                    out_weight = cmds.keyTangent(namespace + left_obj, at=attr, outWeight=True, query=True)
                                    in_tangent_type = cmds.keyTangent(namespace + left_obj, at=attr, inTangentType=True, query=True)
                                    out_tangent_type = cmds.keyTangent(namespace + left_obj, at=attr, outTangentType=True, query=True)
                                    
                                    if transform[1]: # Inverted?
                                        values = invert_float_list_values(values)
                                        in_angle_tangent = invert_float_list_values(in_angle_tangent)
                                        out_angle_tanget = invert_float_list_values(out_angle_tanget)
                                        in_weight = invert_float_list_values(in_weight)
                                        out_weight = invert_float_list_values(out_weight)


                                    # Set Keys/Values
                                    for index in range(len(values)):
                                        time = frames[index]
                                        cmds.setKeyframe(namespace + right_obj, time=time, attribute=attr, value=values[index])
                                        # Set Tangents
                                        cmds.keyTangent(namespace + right_obj, at=attr, time=(time,time), lock=is_locked[index], e=True)
                                        cmds.keyTangent(namespace + right_obj, at=attr, time=(time,time), inAngle=in_angle_tangent[index], e=True)
                                        cmds.keyTangent(namespace + right_obj, at=attr, time=(time,time), outAngle=out_angle_tanget[index], e=True)
                                        cmds.keyTangent(namespace + right_obj, at=attr, time=(time,time), inWeight=in_weight[index], e=True)
                                        cmds.keyTangent(namespace + right_obj, at=attr, time=(time,time), outWeight=out_weight[index], e=True)
                                        cmds.keyTangent(namespace + right_obj, at=attr, time=(time,time), inTangentType=in_tangent_type[index], e=True)
                                        cmds.keyTangent(namespace + right_obj, at=attr, time=(time,time), outTangentType=out_tangent_type[index], e=True)
                                except:
                                    pass # 0 keyframes

                        # Other Attributes
                        attributes = cmds.listAnimatable(namespace + left_obj)
                        default_channels = ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ']
                        for attr in attributes:
                            try:
                                short_attr = attr.split('.')[-1]
                                if short_attr not in default_channels:
                                     # Get Keys/Values
                                    frames = cmds.keyframe(namespace + left_obj, q=1, at=short_attr)
                                    values = cmds.keyframe(namespace + left_obj, q=1, at=short_attr, valueChange=True)

                                    # Set Keys/Values
                                    for index in range(len(values)):
                                        cmds.setKeyframe(namespace + right_obj, time=frames[index], attribute=short_attr, value=values[index])
                            except:
                                pass # 0 keyframes

        # Print Feedback
        unique_message = '<' + str(random.random()) + '>'
        source_message = '(Left to Right)'
        if source_side == 'right':
            source_message = '(Right to Left)'
        cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FFFFFF;\">Animation </span><span style=\"color:#FF0000;text-decoration:underline;\"> mirrored!</span> ' + source_message, pos='botLeft', fade=True, alpha=.9)
                           
        if len(errors) != 0:
            unique_message = '<' + str(random.random()) + '>'
            if len(errors) == 1:
                is_plural = ' error '
            else:
                is_plural = ' errors '
            for error in errors:
                print(str(error))
            sys.stdout.write(str(len(errors)) + is_plural + 'occurred. (Open Script Editor to see a list)\n')
    else:
        cmds.warning('No controls were found. Please check if a namespace is necessary.')
    cmds.setFocus("MayaWindow")



def gt_rig_anim_export(namespace =''):
    ''' 
    Exports an ANIM (JSON) file containing the translate, rotate and scale keyframe (animation) data from the rig controls.

        Parameters:
            namespace (string): In case the rig has a namespace, it will be used to properly select the controls.
    
    ''' 
    # Validate Operation and Write file
    is_valid = True
    successfully_created_file = False

    # Find Available Controls
    available_ctrls = []
    for obj in gt_ab_ik_ctrls:
        if cmds.objExists(namespace + left_prefix + obj):
            available_ctrls.append(left_prefix + obj)
        if cmds.objExists(namespace + right_prefix + obj):
            available_ctrls.append(right_prefix + obj)
            
    for obj in gt_ab_fk_ctrls:
        if cmds.objExists(namespace + left_prefix + obj):
            available_ctrls.append(left_prefix + obj)
        if cmds.objExists(namespace + right_prefix + obj):
            available_ctrls.append(right_prefix + obj)
            
    for obj in gt_ab_general_ctrls:
        if cmds.objExists(namespace + left_prefix + obj):
            available_ctrls.append(left_prefix + obj)
        if cmds.objExists(namespace + right_prefix + obj):
            available_ctrls.append(right_prefix + obj)
            
    for obj in gt_ab_center_ctrls:
        if cmds.objExists(namespace + obj):
            available_ctrls.append(obj)
    
    # No Controls were found
    if len(available_ctrls) == 0:
        is_valid=False
        cmds.warning('No controls were found. Make sure you are using the correct namespace.')


    if is_valid:
        file_name = cmds.fileDialog2(fileFilter=script_name + " - ANIM File (*.anim)", dialogStyle=2, okCaption= 'Export', caption= 'Exporting Rig Animation for "' + script_name + '"') or []
        if len(file_name) > 0:
            pose_file = file_name[0]
            successfully_created_file = True
            

    if successfully_created_file and is_valid:
        export_dict = {'gt_interface_version' : script_version, 'gt_export_method' : 'object-space'}
                
        # Extract Keyframes:
        for obj in available_ctrls:
            attributes = cmds.listAnimatable(namespace + obj)
            for attr in attributes:
                try:
                    short_attr = attr.split('.')[-1]
                    frames = cmds.keyframe(namespace + obj, q=1, at=short_attr)
                    values = cmds.keyframe(namespace + obj, q=1, at=short_attr, valueChange=True)
                    in_angle_tangent = cmds.keyTangent(namespace + obj, at=short_attr, inAngle=True, query=True)
                    out_angle_tanget = cmds.keyTangent(namespace + obj, at=short_attr, outAngle=True, query=True)
                    is_locked = cmds.keyTangent(namespace + obj, at=short_attr, weightLock=True, query=True)
                    in_weight = cmds.keyTangent(namespace + obj, at=short_attr, inWeight=True, query=True)
                    out_weight = cmds.keyTangent(namespace + obj, at=short_attr, outWeight=True, query=True)
                    in_tangent_type = cmds.keyTangent(namespace + obj, at=short_attr, inTangentType=True, query=True)
                    out_tangent_type = cmds.keyTangent(namespace + obj, at=short_attr, outTangentType=True, query=True)
                    export_dict['{}.{}'.format(obj, short_attr)] = zip(frames, values, in_angle_tangent, out_angle_tanget, is_locked, in_weight, out_weight, in_tangent_type, out_tangent_type)
                except:
                    pass # 0 keyframes


        try: 
            with open(pose_file, 'w') as outfile:
                json.dump(export_dict, outfile, indent=4)
      
            unique_message = '<' + str(random.random()) + '>'
            cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FFFFFF;\">Current Animation exported to </span><span style=\"color:#FF0000;text-decoration:underline;\">' + os.path.basename(file_name[0]) +'</span><span style=\"color:#FFFFFF;\">.</span>', pos='botLeft', fade=True, alpha=.9)
            sys.stdout.write('Animation exported to the file "' + pose_file + '".')
        except Exception as e:
            print (e)
            successfully_created_file = False
            cmds.warning('Couldn\'t write to file. Please make sure the exporting directory is accessible.')


def gt_rig_anim_import(debugging=False, debugging_path='', namespace=''):
    ''' 
    Imports an ANIM (JSON) file containing the translate, rotate and scale keyframe data for the rig controls (exported using the "gt_rig_anim_export" function)
    Uses the imported data to set the translate, rotate and scale position of every control curve
    
            Parameters:
                debugging (bool): If debugging, the function will attempt to auto load the file provided in the "debugging_path" parameter
                debugging_path (string): Debugging path for the import function
                namespace (string): In case the rig has a namespace, it will be used to properly select the controls.    
    ''' 
    # Find Available Controls
    available_ctrls = []
    for obj in gt_ab_ik_ctrls:
        if cmds.objExists(namespace + left_prefix + obj):
            available_ctrls.append(left_prefix + obj)
        if cmds.objExists(namespace + right_prefix + obj):
            available_ctrls.append(right_prefix + obj)
            
    for obj in gt_ab_fk_ctrls:
        if cmds.objExists(namespace + left_prefix + obj):
            available_ctrls.append(left_prefix + obj)
        if cmds.objExists(namespace + right_prefix + obj):
            available_ctrls.append(right_prefix + obj)
            
    for obj in gt_ab_general_ctrls:
        if cmds.objExists(namespace + left_prefix + obj):
            available_ctrls.append(left_prefix + obj)
        if cmds.objExists(namespace + right_prefix + obj):
            available_ctrls.append(right_prefix + obj)
            
    for obj in gt_ab_center_ctrls:
        if cmds.objExists(namespace + obj):
            available_ctrls.append(obj)
    
    # Track Current State
    import_version = 0.0
    import_method = 'object-space'
    
    if not debugging:
        file_name = cmds.fileDialog2(fileFilter=script_name + " - ANIM File (*.anim)", dialogStyle=2, fileMode= 1, okCaption= 'Import', caption= 'Importing Proxy Pose for "' + script_name + '"') or []
    else:
        file_name = [debugging_path]
    
    if len(file_name) > 0:
        anim_file = file_name[0]
        file_exists = True
    else:
        file_exists = False
    
    if file_exists:
        try: 
            with open(anim_file) as json_file:
                data = json.load(json_file)
                try:
                    is_valid_file = True
                    is_operation_valid = True

                    if not data.get('gt_interface_version'):
                        is_valid_file = False
                        cmds.warning('Imported file doesn\'t seem to be compatible or is missing data.')
                    else:                       
                        import_version = float(re.sub("[^0-9]", "", str(data.get('gt_interface_version'))))
                
                    if data.get('gt_export_method'):
                      import_method = data.get('gt_export_method')
                
                    if len(available_ctrls) == 0:
                        cmds.warning('No controls were found. Please check if a namespace is necessary.')
                        is_operation_valid = False
                        
                    if is_operation_valid:
                        # Object-Space
                        for key, dict_value in data.iteritems():
                            if key != 'gt_interface_version' and key != 'gt_export_method':
                                for key_data in dict_value:
                                    # Unpack Data
                                    time = key_data[0]
                                    value = key_data[1]
                                    in_angle_tangent = key_data[2]
                                    out_angle_tanget = key_data[3] 
                                    is_locked = key_data[4]
                                    in_weight = key_data[5]
                                    out_weight = key_data[6] 
                                    in_tangent_type = key_data[7] 
                                    out_tangent_type = key_data[8] 
                                    
                                    try:
                                        obj, attr = key.split('.')
                                        cmds.setKeyframe(namespace + obj, time=time, attribute=attr, value=value)
                                        cmds.keyTangent(namespace + obj, at=attr, time=(time,time), lock=is_locked, e=True)
                                        cmds.keyTangent(namespace + obj, at=attr, time=(time,time), inAngle=in_angle_tangent, e=True)
                                        cmds.keyTangent(namespace + obj, at=attr, time=(time,time), outAngle=out_angle_tanget, e=True)
                                        cmds.keyTangent(namespace + obj, at=attr, time=(time,time), inWeight=in_weight, e=True)
                                        cmds.keyTangent(namespace + obj, at=attr, time=(time,time), outWeight=out_weight, e=True)
                                        cmds.keyTangent(namespace + obj, at=attr, time=(time,time), inTangentType=in_tangent_type, e=True)
                                        cmds.keyTangent(namespace + obj, at=attr, time=(time,time), outTangentType=out_tangent_type, e=True)
                                    except:
                                        pass

                        unique_message = '<' + str(random.random()) + '>'
                        cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FFFFFF;\">Animation imported from </span><span style=\"color:#FF0000;text-decoration:underline;\">' + os.path.basename(anim_file) +'</span><span style=\"color:#FFFFFF;\">.</span>', pos='botLeft', fade=True, alpha=.9)
                        sys.stdout.write('Animation imported from the file "' + anim_file + '".')
                            
                except Exception as e:
                    print(e)
                    cmds.warning('An error occured when importing the pose. Make sure you imported a valid ANIM file.')
        except:
            file_exists = False
            cmds.warning('Couldn\'t read the file. Please make sure the selected file is accessible.')



#Build UI
if __name__ == '__main__':
    build_gui_custom_rig_interface()