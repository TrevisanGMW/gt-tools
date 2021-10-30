"""
 Custom Rig Interface (Formerly known as "Seamless IK/FK Switcher") for GT Auto Biped Rigger.
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2021-01-05
 github.com/TrevisanGMW/gt-tools

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
import os


# Script Name
script_name = 'GT - Custom Rig Interface'
unique_rig = '' # If provided, it will be used in the window title

# Version:
script_version = "1.3"

# Python Version
python_version = sys.version_info.major

# FK/IK Swticher Elements
left_arm_seamless_dict = { 'switch_ctrl' : 'left_arm_switch_ctrl', # Switch Ctrl
                           'end_ik_ctrl' : 'left_wrist_ik_ctrl', # IK Elements
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
                           'end_ik_reference' : ''
                         }

right_arm_seamless_dict = { 'switch_ctrl' : 'right_arm_switch_ctrl', # Switch Ctrl
                            'end_ik_ctrl' : 'right_wrist_ik_ctrl', # IK Elements
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
                            'end_ik_reference' : ''
                           }
                            
left_leg_seamless_dict = { 'switch_ctrl' : 'left_leg_switch_ctrl', # Switch Ctrl
                           'end_ik_ctrl' : 'left_foot_ik_ctrl', # IK Elements
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
                           'end_ik_reference' : 'left_ankleSwitch_loc'
                          }
                           
right_leg_seamless_dict = { 'switch_ctrl' : 'right_leg_switch_ctrl', # Switch Ctrl
                            'end_ik_ctrl' : 'right_foot_ik_ctrl', # IK Elements
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
                            'end_ik_reference' : 'right_ankleSwitch_loc'
                          }
                          
# Mirror Elements
namespace_separator = ':'
left_prefix = 'left'
right_prefix = 'right'
not_inverted = (False, False, False)
invert_x = (True, False, False)
invert_y = (False, True, False)
invert_yz = (False, True, True)
invert_all = (True, True, True)

# Dictionary Pattern:
# Key: Control name (if not in the center, remove prefix)
# Value: A list with two tuples. [(Is Translate XYZ inverted?), (Is Rotate XYZ inverted?)]
gt_ab_general_ctrls = {# Fingers
                   '_fingers_ctrl': [not_inverted, not_inverted],
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
                   # Clavicle
                   '_clavicle_ctrl': [not_inverted, not_inverted],
                   # Eyes
                   '_eye_ctrl': [invert_x, not_inverted],
                 }   

gt_ab_ik_ctrls = { # Arm
                   '_elbow_ik_ctrl': [not_inverted, not_inverted], 
                   '_wrist_ik_ctrl': [invert_all, not_inverted],
                   # Leg
                   '_heelRoll_ctrl': [invert_x, not_inverted],
                   '_ballRoll_ctrl': [invert_x, not_inverted],
                   '_toeRoll_ctrl': [invert_x, not_inverted],
                   '_toe_upDown_ctrl': [invert_x, not_inverted],
                   '_foot_ik_ctrl': [invert_x, invert_yz],
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
                      'hip_ctrl', 
                      'spine01_ctrl', 
                      'spine02_ctrl', 
                      'spine03_ctrl', 
                      'spine04_ctrl', 
                      'cog_ribbon_ctrl', 
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

gt_ab_interface_settings = {
                            'namespace' : ''
                           }


# Manage Persistent Settings
def get_persistent_settings_auto_biped_rig_interface():
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
                #print(stored_item)
                for item in gt_ab_interface_settings:
                    if stored_item == item:
                        gt_ab_interface_settings[item] = stored_settings.get(stored_item)
        except:
            print('Couldn\'t load persistent settings, try resetting it in the help menu.')


def set_persistent_settings_auto_biped_rig_interface():
    ''' 
    Stores persistant settings for GT Auto Biped Rig Interface.
    It converts the dictionary into a list for easy storage. (The get function converts it back to a dictionary)
    It assumes that persistent settings were stored using the cmds.optionVar function.
    '''
    cmds.optionVar( sv=('gt_auto_biped_rig_interface_setup', str(gt_ab_interface_settings)))


def reset_persistent_settings_auto_biped_rig_interface():
    ''' Resets persistant settings for GT Auto Biped Rig Interface '''
    cmds.optionVar( remove='gt_auto_biped_rig_interface_setup' )
    gt_ab_interface_settings['namespace'] = ''
    cmds.warning('Persistent settings for ' + script_name + ' were cleared.')
  
    
             
# Main Window ============================================================================
def build_gui_custom_rig_interface():
    rig_interface_window_name = 'build_gui_custom_rig_interface'
    if cmds.window(rig_interface_window_name, exists =True):
        cmds.deleteUI(rig_interface_window_name)    

    # Main GUI Start Here =================================================================================
    
    # Build UI
    script_title = script_name
    if unique_rig != '':
        script_title = 'GT - Rig Interface for ' + unique_rig
    
      
    build_gui_custom_rig_interface = cmds.window(rig_interface_window_name, title=script_title + '  (v' + script_version + ')',\
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
    namespace_txt = cmds.textField(text='', pht='Namespace:: (Optional)', cc=lambda x:update_stored_settings())
    
    cmds.separator(h=10, style='none') # Empty Space
    
    btn_margin = 5
    cmds.rowColumnLayout(nc=2, cw=[(1, 129),(2, 130)], cs=[(1,0), (2,5)], p=body_column)
    cmds.text('Right Arm:') #R
    cmds.text('Left Arm:') #L
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.button(l ="Toggle", c=lambda x:gt_ab_seamless_fk_ik_toggle(right_arm_seamless_dict, namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), w=130) #R
    cmds.button(l ="Toggle", c=lambda x:gt_ab_seamless_fk_ik_toggle(left_arm_seamless_dict, namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), w=130) #L
    cmds.button(l ="FK to IK", c=lambda x:gt_ab_seamless_fk_ik_switch(right_arm_seamless_dict, 'fk_to_ik', namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), w=130) #R
    cmds.button(l ="FK to IK", c=lambda x:gt_ab_seamless_fk_ik_switch(left_arm_seamless_dict, 'fk_to_ik', namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), w=130) #L
    cmds.button(l ="IK to FK", c=lambda x:gt_ab_seamless_fk_ik_switch(right_arm_seamless_dict, 'ik_to_fk', namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), w=130) #R
    cmds.button(l ="IK to FK", c=lambda x:gt_ab_seamless_fk_ik_switch(left_arm_seamless_dict, 'ik_to_fk', namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), w=130) #L
    cmds.separator(h=btn_margin, style='none') # Empty Space
    
    cmds.rowColumnLayout(nc=2, cw=[(1, 129),(2, 130)], cs=[(1,0), (2,5)], p=body_column)
    cmds.text('Right Leg:') #R
    cmds.text('Left Leg:') #L
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.button(l ="Toggle", c=lambda x:gt_ab_seamless_fk_ik_toggle(right_leg_seamless_dict, namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), w=130) #R
    cmds.button(l ="Toggle", c=lambda x:gt_ab_seamless_fk_ik_toggle(left_leg_seamless_dict, namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), w=130) #L
    cmds.button(l ="FK to IK", c=lambda x:gt_ab_seamless_fk_ik_switch(right_leg_seamless_dict, 'fk_to_ik', namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), w=130) #R
    cmds.button(l ="FK to IK", c=lambda x:gt_ab_seamless_fk_ik_switch(left_leg_seamless_dict, 'fk_to_ik', namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), w=130) #L
    cmds.button(l ="IK to FK", c=lambda x:gt_ab_seamless_fk_ik_switch(right_leg_seamless_dict, 'ik_to_fk', namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), w=130) #R
    cmds.button(l ="IK to FK", c=lambda x:gt_ab_seamless_fk_ik_switch(left_leg_seamless_dict, 'ik_to_fk', namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), w=130) #L
    
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,10)], p=body_column)
    
    # Pose Management
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.text('Pose Management:') 
    cmds.rowColumnLayout(nc=2, cw=[(1, 129),(2, 130)], cs=[(1,0), (2,5)], p=body_column)
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.button(l ="IK Mirror Right to Left", c=lambda x:gt_ab_mirror_pose([gt_ab_general_ctrls, gt_ab_ik_ctrls], 'right', namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), w=130) #R
    cmds.button(l ="IK Mirror Left to Right", c=lambda x:gt_ab_mirror_pose([gt_ab_general_ctrls, gt_ab_ik_ctrls], 'left', namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), w=130) #L
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.button(l ="FK Mirror Right to Left", c=lambda x:gt_ab_mirror_pose([gt_ab_general_ctrls, gt_ab_fk_ctrls], 'right', namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), w=130) #R
    cmds.button(l ="FK Mirror Left to Right", c=lambda x:gt_ab_mirror_pose([gt_ab_general_ctrls, gt_ab_fk_ctrls], 'left', namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), w=130) #L

    cmds.separator(h=2, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,0)], p=body_column)
    cmds.button(l ="Reset Back to Default Pose", c=lambda x:gt_ab_reset_pose(gt_ab_ik_ctrls, gt_ab_fk_ctrls, gt_ab_center_ctrls, namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), w=130)
    
    # Export Import
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.text('Import/Export Poses:') 
    cmds.rowColumnLayout(nc=2, cw=[(1, 129),(2, 130)], cs=[(1,0), (2,5)], p=body_column)
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.separator(h=btn_margin, style='none') # Empty Space
    cmds.button(l ="Import Current Pose", c=lambda x:import_current_pose(namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), w=130)
    cmds.button(l ="Export Current Pose", c=lambda x:export_current_pose(namespace=cmds.textField(namespace_txt, q=True, text=True)+namespace_separator), w=130) 

    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,10)], p=content_main)
                                                                                               
    cmds.separator(h=10, style='none') # Empty Space
    
    # Show and Lock Window
    cmds.showWindow(build_gui_custom_rig_interface)
    cmds.window(rig_interface_window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(rig_interface_window_name)
    if python_version == 3:
        widget = wrapInstance(int(qw), QWidget)
    else:
        widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/ikSCsolver.svg')
    widget.setWindowIcon(icon)


    # Retrieve Namespace (If used before)
    get_persistent_settings_auto_biped_rig_interface()
    if gt_ab_interface_settings.get('namespace') != '':
        cmds.textField(namespace_txt, e=True, text=gt_ab_interface_settings.get('namespace'))

    # Remove the focus from the textfield and give it to the window
    cmds.setFocus(rig_interface_window_name)

    # Main GUI Ends Here =================================================================================
    def update_stored_settings():
        '''
        Extracts the namespace used and stores it as a persistent variable
        '''
        gt_ab_interface_settings['namespace'] = cmds.textField(namespace_txt, q=True, text=True)
        set_persistent_settings_auto_biped_rig_interface()


def gt_ab_seamless_fk_ik_switch(ik_fk_dict, direction='fk_to_ik', namespace=''):
    '''
    Transfer the position of the FK to IK or IK to FK systems in a seamless way, so the animator can easily switch between one and the other
    
            Parameters:
                ik_fk_ns_dict (dict): A dicitionary containg the elements that are part of the system you want to switch
                direction (string): Either "fk_to_ik" or "ik_to_fk". It determines what is the source and what is the target.
                namespace (string): In case the rig has a namespace, it will be used to properly select the controls.
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
            cmds.setAttr(ik_fk_ns_dict.get('switch_ctrl') + '.influenceSwitch', 1)
        if direction == 'ik_to_fk':
            for pair in fk_pairs:
                cmds.matchTransform(pair[1], pair[0], pos=1, rot=1)
            cmds.setAttr(ik_fk_ns_dict.get('switch_ctrl') + '.influenceSwitch', 0)
    except Exception as e:
        cmds.warning('No controls were found. Please check if a namespace is necessary.     Error: ' + str(e))

def open_gt_tools_documentation():
    ''' Opens a web browser with the latest release '''
    cmds.showHelp ('https://github.com/TrevisanGMW/gt-tools/tree/release/docs#-gt-auto-biped-rigger-', absolute=True) 
    
def gt_ab_seamless_fk_ik_toggle(ik_fk_dict, namespace=''):
    ''' 
    Calls gt_ab_seamless_fk_ik_switch, but toggles between fk and ik 
    
            Parameters:
                ik_fk_dict (dictionary): A dicitionary containg the elements that are part of the system you want to switch
                namespace (string): In case the rig has a namespace, it will be used to properly select the controls.
                
    
    '''
    try:
        current_system = cmds.getAttr(namespace + ik_fk_dict.get('switch_ctrl') + '.influenceSwitch')
        if current_system < 0.5:
            gt_ab_seamless_fk_ik_switch(ik_fk_dict, direction='fk_to_ik', namespace=namespace)
        else:
            gt_ab_seamless_fk_ik_switch(ik_fk_dict, direction='ik_to_fk', namespace=namespace)
    except Exception as e:
        cmds.warning('No controls were found. Please check if a namespace is necessary.     Error: ' + str(e))


def gt_ab_mirror_pose(gt_ab_ctrls, source_side, namespace=''):
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

                    transforms.append([True, key[0][0], 'tx'])
                    transforms.append([True, key[0][1], 'ty'])
                    transforms.append([True, key[0][2], 'tz'])
                    transforms.append([True, key[1][0], 'rx'])
                    transforms.append([True, key[1][1], 'ry'])
                    transforms.append([True, key[1][2], 'rz'])
                    
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
                is_plural = ' attribute was '
            else:
                is_plural = ' attributes were '
            for error in errors:
                print(str(error))
            sys.stdout.write(str(len(errors)) + ' locked '+ is_plural + 'ignored. (Open Script Editor to see a list)\n')
    else:
        cmds.warning('No controls were found. Please check if a namespace is necessary.')
    cmds.setFocus("MayaWindow")
    
def gt_ab_reset_pose(gt_ab_ik_ctrls, gt_ab_fk_ctrls, gt_ab_center_ctrls, namespace=''):
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


def export_current_pose(namespace =''):
    ''' 
    Exports a JSON file containing the translate, rotate and scale data from the rig controls (used to export a pose)
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
        file_name = cmds.fileDialog2(fileFilter=script_name + " - JSON File (*.json)", dialogStyle=2, okCaption= 'Export', caption= 'Exporting Rig Pose for "' + script_name + '"') or []
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


def import_current_pose(debugging=False, debugging_path='', namespace=''):
    ''' 
    Imports a JSON file containing the translate, rotate and scale data for the rig controls (exported using the "export_current_pose" function)
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
        file_name = cmds.fileDialog2(fileFilter=script_name + " - JSON File (*.json)", dialogStyle=2, fileMode= 1, okCaption= 'Import', caption= 'Importing Proxy Pose for "' + script_name + '"') or []
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
                        sys.stdout.write('Pose exported to the file "' + pose_file + '".')
                    
                except Exception as e:
                    print(e)
                    cmds.warning('An error occured when importing the pose. Make sure you imported the correct JSON file.')
        except:
            file_exists = False
            cmds.warning('Couldn\'t read the file. Please make sure the selected file is accessible.')


            
#Build UI
if __name__ == '__main__':
    build_gui_custom_rig_interface()