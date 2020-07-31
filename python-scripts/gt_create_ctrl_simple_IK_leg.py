"""

 Simple Biped IK Leg Generator
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-01-06
 1.1 - 2020-03-11
 Added stretchy leg option.
 
 1.2 - 2020-06-07
 Updated naming convention to make it clearer. (PEP8)
 Fixed random window widthHeight issue.
 
 1.3 - 2020-06-17
 Changed UI
 Updated help menu
 Added icon
 
 TO DO:
 Add rolls
 Use replace instead of substring to rename elements.

"""
import maya.cmds as cmds
import maya.mel as mel
from decimal import *
from maya import OpenMayaUI as omui

try:
    from shiboken2 import wrapInstance
except ImportError:
    from shiboken import wrapInstance

try:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QWidget
except ImportError:
    from PySide.QtGui import QIcon, QWidget


# Script Name
script_name = "GT - IK Leg Generator"

# Version:
script_version = "1.3"


stored_joints = { 'hip_jnt': '', 
             'ankle_jnt': '',
             'ball_jnt': ''
            }

settings = { 'using_custom_ik_ctrl': False, 
             'custom_ik_ctrl_name': '',
             'using_custom_pvector_ctrl': False,
             'custom_pvector_ctrl' : '',
             'using_custom_ikfk_switch' : False,
             'custom_ikfk_switch_name' : '',
             'using_colorize_ctrls' : True,
             'def_use_ball_jnt' : True,
             'def_colorize_ctrl' : True,
             'def_use_ik_ctrl' : False,
             'def_use_ik_switch' : False,
             'def_use_pvector' : False,
             'make_stretchy' : True,
             'ctrl_grp_tag' : 'CtrlGrp',
             'jnt_tag' : 'Jnt'
            }


# Main Form ============================================================================
def build_gui_simple_ik_leg():
    window_name = "build_gui_simple_ik_leg"
    if cmds.window(window_name, exists =True):
        cmds.deleteUI(window_name)    

    # Main GUI Start Here =================================================================================

    build_gui_simple_ik_leg = cmds.window(window_name, title=script_name + "  v" + script_version,\
                          titleBar=True, mnb=False, mxb=False, sizeable =True)
                          
    cmds.window(window_name, e=True, s=True, wh=[1,1])

    column_main = cmds.columnLayout() 

    form = cmds.formLayout(p=column_main)

    content_main = cmds.columnLayout(adj = True)


    # Title Text
    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 10)], p=content_main) # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 200), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)], p=content_main) # Title Column
    cmds.text(" ", bgc=[0,.5,0]) # Tiny Empty Green Space
    cmds.text(script_name + " v" + script_version, bgc=[0,.5,0],  fn="boldLabelFont", align="left")
    cmds.button( l ="Help", bgc=(0, .5, 0), c=lambda x:build_help_gui_ik_leg_generator())
    cmds.separator(h=10, style='none', p=content_main) # Empty Space

    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,10)], p=content_main)
    
    cmds.rowColumnLayout(nc=2, cw=[(1, 130),(2, 130)], cs=[(1,0),(2, 0)], p=body_column)
    cmds.text("Joint Tag (Suffix)")
    cmds.text("Ctrl Group Tag (Suffix)")
    jnt_tag_text_field = cmds.textField(text=settings.get("jnt_tag"), \
                                           enterCommand=lambda x:update_settings(), textChangedCommand=lambda x:update_settings())
    ctrl_grp_text_field = cmds.textField(text=settings.get("ctrl_grp_tag"), \
                                           enterCommand=lambda x:update_settings(), textChangedCommand=lambda x:update_settings())
    
    
    cmds.separator(h=15, p=body_column)
    
    # CheckboxGrp One
    interactive_container_misc = cmds.rowColumnLayout(p=body_column, numberOfRows=1, h= 25)

    check_box_grp_one = cmds.checkBoxGrp(p=interactive_container_misc, columnWidth2=[140, 1], numberOfCheckBoxes=2, \
                                label1 = 'Custom PVector Ctrl', label2 = "Custom IK Ctrl", v1 = settings.get("def_use_pvector"), v2 = settings.get("def_use_ik_ctrl"), \
                                on2=lambda x:is_custom_ik_ctrl_enabled(True),  of2=lambda x:is_custom_ik_ctrl_enabled(False), \
                                on1 =lambda x:is_custom_pvector_enabled(True), of1=lambda x:is_custom_pvector_enabled(False) ) 
    # CheckboxGrp Two
    interactive_container_misc = cmds.rowColumnLayout(p=body_column, numberOfRows=1, h= 25)

    check_box_grp_two = cmds.checkBoxGrp(p=interactive_container_misc, columnWidth2=[140, 1], numberOfCheckBoxes=2, \
                                label1 = 'Colorize Controls ', label2 = "Custom IK Switch", v1 = settings.get("def_colorize_ctrl"), v2 = settings.get("def_use_ik_switch"), \
                                on2=lambda x:is_custom_ik_switch_enabled(True),  of2=lambda x:is_custom_ik_switch_enabled(False) ) 
    cmds.separator(h=10, p=body_column)
    
    #pVector Ctrl Loader
    pvector_container = cmds.rowColumnLayout( p=body_column, numberOfRows=1)
    pvector_btn = cmds.button(p=pvector_container, l ="Load PVector Ctrl", c=lambda x:update_load_btn_ctrls("pVector"), w=130)
    pvector_status = cmds.button(p=pvector_container, l ="Not loaded yet", bgc=(0, 0, 0), w=130, \
                            c="cmds.headsUpMessage( 'Select your pole vector control and click on \"Load PVector Ctrl Joint\"', verticalOffset=150 , time=5.0)")
    
    #Custom IK Ctrl Loader
    ik_ctrl_container = cmds.rowColumnLayout( p=body_column, numberOfRows=1)
    ik_ctrl_btn = cmds.button(p=ik_ctrl_container, l ="Load IK Ctrl", c=lambda x:update_load_btn_ctrls("ikCtrl"), w=130)
    ik_ctrl_status = cmds.button(p=ik_ctrl_container, l ="Not loaded yet", bgc=(0, 0, 0), w=130, \
                            c="cmds.headsUpMessage( 'Select your IK Switch control and click on \"Load IK Switch Ctrl Joint\"', verticalOffset=150 , time=5.0)")
    
    #IK Switch Ctrl Loader
    ik_switch_container = cmds.rowColumnLayout( p=body_column, numberOfRows=1)
    ik_switch_btn = cmds.button(p=ik_switch_container, l ="Load IK Switch Ctrl", c=lambda x:update_load_btn_ctrls("ikSwitch"), w=130)
    ik_switch_status = cmds.button(p=ik_switch_container, l ="Not loaded yet", bgc=(0, 0, 0), w=130,  \
                            c="cmds.headsUpMessage( 'Select your Custom IK Control and click on \"Load IK Ctrl Joint\"', verticalOffset=150 , time=5.0)")
                            
    
    cmds.separator(h=15, p=body_column)
    # CheckboxGrp Three
    interactive_container_jnt = cmds.rowColumnLayout(p=body_column, numberOfRows=1, h= 25)
    cmds.text("    ") # Increase this to move checkboxes to the right
    check_box_grp_three = cmds.checkBoxGrp(p=interactive_container_jnt, columnWidth2=[130, 1], numberOfCheckBoxes=2, \
                                label1 = 'Make Stretchy Legs ', label2 = "Use Ball Joint", v1 = settings.get("make_stretchy"), v2 = settings.get("def_use_ball_jnt"), \
                                on2=lambda x:is_ball_enabled(True),  of2=lambda x:is_ball_enabled(False)\
                               ,on1=lambda x:update_settings(),  of1=lambda x:update_settings())
                            
    cmds.separator(h=10, p=body_column)
    #Hip Joint Loader
    hip_container = cmds.rowColumnLayout( p=body_column, numberOfRows=1)
    cmds.button(p=hip_container, l ="Load Hip Joint", c=lambda x:update_load_btn_jnt("hip"), w=130)
    hip_status = cmds.button(p=hip_container, l ="Not loaded yet", bgc=(0, 0, 0), w=130, \
                            c="cmds.headsUpMessage( 'Select your hip joint and click on \"Load Hip Joint\"', verticalOffset=150 , time=5.0)")
                            
    #Ankle Joint Loader
    ankle_container = cmds.rowColumnLayout( p=body_column, numberOfRows=1)
    cmds.button(p=ankle_container, l ="Load Ankle Joint", c=lambda x:update_load_btn_jnt("ankle"), w=130)
    ankle_status = cmds.button(p=ankle_container, l ="Not loaded yet", bgc=(0, 0, 0), w=130, \
                            c="cmds.headsUpMessage( 'Select your ankle joint and click on \"Load Ankle Joint\"', verticalOffset=150 , time=5.0)")
                            
    #Ball Joint Loader
    ball_container = cmds.rowColumnLayout( p=body_column, numberOfRows=1)
    ball_load_btn = cmds.button(p=ball_container, l ="Load Ball Joint", c=lambda x:update_load_btn_jnt("ball"), w=130)
    ball_status = cmds.button(p=ball_container, l ="Not loaded yet", bgc=(0, 0, 0), w=130, \
                            c="cmds.headsUpMessage( 'Select your ball joint and click on \"Load Ball Joint\"', verticalOffset=150 , time=5.0)")
      
    cmds.separator(h=10, p=body_column)
    cmds.separator(h=10, style="none", p=body_column)
    cmds.button(p=body_column, l ="Generate",bgc=(.6, .8, .6), c=lambda x:check_before_running(cmds.checkBoxGrp(check_box_grp_three, q=True, value2=True)))
    cmds.separator(h=10, style="none", p=body_column)
    
    def update_settings():
        settings["make_stretchy"] = cmds.checkBoxGrp(check_box_grp_three, q=True, value1=True)
        
        jnt_tag = parse_text_field(cmds.textField(jnt_tag_text_field,q=True,text=True))
        if jnt_tag != [] and len(jnt_tag) > 0:
            settings["jnt_tag"] = jnt_tag[0]
        
        ctrl_grp_tag = parse_text_field(cmds.textField(ctrl_grp_text_field,q=True,text=True))
        if ctrl_grp_tag != [] and len(ctrl_grp_tag) > 0:
            settings["ctrl_grp_tag"] = ctrl_grp_tag[0]

        
    def is_ball_enabled(state):
        if state:
            cmds.button(ball_load_btn, e=True, en=True)
            cmds.button(ball_status, l ="Not loaded yet", e=True, en=True, bgc=(0, 0, 0))
            stored_joints["ball_jnt"] = ''
        else:
            cmds.button(ball_load_btn, e=True, en=False)
            cmds.button(ball_status, l ="Not necessary", e=True, en=False, bgc=(.25, .25, .25))
            
    def is_custom_ik_ctrl_enabled(state):
        if state:
            cmds.button(ik_ctrl_btn, e=True, en=True)
            cmds.button(ik_ctrl_status, l ="Not loaded yet", e=True, en=True, bgc=(0, 0, 0))
            settings["custom_ik_ctrl_name"] = ''
            settings["using_custom_ik_ctrl"] = True
        else:
            cmds.button(ik_ctrl_btn, e=True, en=False)
            cmds.button(ik_ctrl_status, l ="Not necessary", e=True, en=False, bgc=(.25, .25, .25))
            settings["using_custom_ik_ctrl"] = False
            
    def is_custom_ik_switch_enabled(state):
        if state:
            cmds.button(ik_switch_btn, e=True, en=True)
            cmds.button(ik_switch_status, l ="Not loaded yet", e=True, en=True, bgc=(0, 0, 0))
            settings["custom_ikfk_switch_name"] = ''
            settings["using_custom_ikfk_switch"] = True
        else:
            cmds.button(ik_switch_btn, e=True, en=False)
            cmds.button(ik_switch_status, l ="Not necessary", e=True, en=False, bgc=(.25, .25, .25))
            settings["using_custom_ikfk_switch"] = False
            
    def is_custom_pvector_enabled(state):
        if state:
            cmds.button(pvector_btn, e=True, en=True)
            cmds.button(pvector_status, l ="Not loaded yet", e=True, en=True, bgc=(0, 0, 0))
            settings["custom_pvector_ctrl"] = ''
            settings["using_custom_pvector_ctrl"] = True
        else:
            cmds.button(pvector_btn, e=True, en=False)
            cmds.button(pvector_status, l ="Not necessary", e=True, en=False, bgc=(.25, .25, .25))
            settings["using_custom_pvector_ctrl"] = False
    
    # Curves Loader @@@@@@@@@@@@
    def update_load_btn_ctrls(button_name):
        
        # Check If Selection is Valid
        received_valid_ctrl = False
        selected_ctrls = cmds.ls(selection=True,tr=1, type='nurbsCurve')
        
        if len(selected_ctrls) == 0:
            cmds.warning("First element in your selection wasn't a control (nurbsCurve)")
        elif len(selected_ctrls) > 1:
            cmds.warning("You selected more than one curve! Please select only one")
        elif cmds.objectType(cmds.listRelatives(selected_ctrls[0], children=True)[0]) == "nurbsCurve":
            received_ctrl = selected_ctrls[0]
            received_valid_ctrl = True
        else:
            cmds.warning("Something went wrong, make sure you selected just one curve")
        
        # If pVector
        if button_name is "pVector" and received_valid_ctrl == True:
            settings["custom_pvector_ctrl"] = received_ctrl
            cmds.button(pvector_status, l=received_ctrl,e=True, bgc=(.6, .8, .6), w=130, c=lambda x:if_exists_select(settings.get("custom_pvector_ctrl")))
        elif button_name is "pVector":
            cmds.button(pvector_status, l ="Failed to Load",e=True, bgc=(1, .4, .4), w=130,c="cmds.headsUpMessage( 'Make sure you select only one curve and try again', verticalOffset=150 , time=5.0)")
        # If ikCtrl
        if button_name is "ikCtrl" and received_valid_ctrl == True:
            settings["custom_ik_ctrl_name"] = received_ctrl
            cmds.button(ik_ctrl_status, l=received_ctrl,e=True, bgc=(.6, .8, .6), w=130, c=lambda x:if_exists_select(settings.get("custom_ik_ctrl_name")))
        elif button_name is "ikCtrl":
            cmds.button(ik_ctrl_status, l ="Failed to Load",e=True, bgc=(1, .4, .4), w=130,c="cmds.headsUpMessage( 'Make sure you select only one curve and try again', verticalOffset=150 , time=5.0)")
        # If ikSwitch
        if button_name is "ikSwitch" and received_valid_ctrl == True:
            settings["custom_ikfk_switch_name"] = received_ctrl
            cmds.button(ik_switch_status, l=received_ctrl,e=True, bgc=(.6, .8, .6), w=130, c=lambda x:if_exists_select(settings.get("custom_ikfk_switch_name")))
        elif button_name is "ikSwitch":
            cmds.button(ik_switch_status, l ="Failed to Load",e=True, bgc=(1, .4, .4), w=130,c="cmds.headsUpMessage( 'Make sure you select only one curve and try again', verticalOffset=150 , time=5.0)")

    # Joints Loader @@@@@@@@@@@@
    def update_load_btn_jnt(button_name):
        
        # Check If Selection is Valid
        received_valid_jnt = False
        selected_joints = cmds.ls(selection=True, type='joint')
        if len(selected_joints) == 0:
            cmds.warning("First element in your selection wasn't a joint")
        elif len(selected_joints) > 1:
            cmds.warning("You selected more than one joint! Please select only one")
        elif cmds.objectType(selected_joints[0]) == "joint":
            joint = selected_joints[0]
            received_valid_jnt = True
        else:
            cmds.warning("Something went wrong, make sure you selected just one joint")
            
        # If Hip
        if button_name is "hip" and received_valid_jnt == True:
            stored_joints["hip_jnt"] = joint
            cmds.button(hip_status, l =joint,e=True, bgc=(.6, .8, .6), w=130, c=lambda x:if_exists_select(stored_joints.get("hip_jnt")))
        elif button_name is "hip":
            cmds.button(hip_status, l ="Failed to Load",e=True, bgc=(1, .4, .4), w=130,c="cmds.headsUpMessage( 'Make sure you select only one joint and try again', verticalOffset=150 , time=5.0)")
        
        # If Ankle
        if button_name is "ankle" and received_valid_jnt == True:
            stored_joints["ankle_jnt"] = joint
            cmds.button(ankle_status, l =joint,e=True, bgc=(.6, .8, .6), w=130, c=lambda x:if_exists_select(stored_joints.get("ankle_jnt")))
        elif button_name is "ankle":
            cmds.button(ankle_status, l ="Failed to Load",e=True, bgc=(1, .4, .4), w=130,c="cmds.headsUpMessage( 'Make sure you select only one joint and try again', verticalOffset=150 , time=5.0)")
        
        # If Ball
        if button_name is "ball" and received_valid_jnt == True:
            stored_joints["ball_jnt"] = joint
            cmds.button(ball_status, l =joint,e=True, bgc=(.6, .8, .6), w=130, c=lambda x:if_exists_select(stored_joints.get("ball_jnt")))
        elif button_name is "ball":
            cmds.button(ball_status, l ="Failed to Load",e=True, bgc=(1, .4, .4), w=130,c="cmds.headsUpMessage( 'Make sure you select only one joint and try again', verticalOffset=150 , time=5.0)")


    # Show and Lock Window
    cmds.showWindow(build_gui_simple_ik_leg)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/kinHandle.png')
    widget.setWindowIcon(icon)
    
    
    # Update Everything
    is_ball_enabled(settings.get("def_use_ball_jnt"))
    is_custom_ik_ctrl_enabled(settings.get("def_use_ik_ctrl"))
    is_custom_ik_switch_enabled(settings.get("def_use_ik_switch"))
    is_custom_pvector_enabled(settings.get("def_use_pvector"))
    # Main GUI Ends Here =================================================================================
    

#Checks if loaded elements are still valid before running script (in case the user changed it after loading)
def check_before_running(is_using_ball):
    is_valid = True
    error_message = '    Please reload missing elements.    Missing: '

    if cmds.objExists(stored_joints.get("hip_jnt")) == False: # Hip
        is_valid = False
        error_message = error_message + 'hip joint, '
    if cmds.objExists(stored_joints.get("ankle_jnt")) == False: # Ankle
        is_valid = False
        error_message = error_message + 'ankle joint, '

        
    if cmds.objExists(stored_joints.get("hip_jnt")) and len(cmds.listRelatives(stored_joints.get("hip_jnt"), type='joint') or []) > 0: # Check knee exists
        if cmds.objExists(stored_joints.get("ankle_jnt")):
            if cmds.listRelatives(stored_joints.get("hip_jnt"), type='joint')[0] == stored_joints.get("ankle_jnt"):
                is_valid = False
                error_message = error_message + 'knee joint, '

    if is_using_ball:
        if cmds.objExists(stored_joints.get("ball_jnt")) == False: # Ball
            is_valid = False
            error_message = error_message + 'ball joint, '
        if cmds.objExists(stored_joints.get("ball_jnt")) == True and len(cmds.listRelatives(stored_joints.get("ball_jnt"), type='joint') or []) == 0: # Check if ball has children
            is_valid = False
            error_message = error_message + 'toe joint, '  
    
    #Check curves here
    if settings.get("using_custom_pvector_ctrl"):
        if cmds.objExists(settings.get("custom_pvector_ctrl")) == False:
            is_valid = False
            error_message = error_message + 'pole vector ctrl, '
            
    if settings.get("using_custom_ik_ctrl"):
        if cmds.objExists(settings.get("custom_ik_ctrl_name")) == False:
            is_valid = False
            error_message = error_message + 'custom IK ctrl, '
            
    if settings.get("using_custom_ikfk_switch"):
        if cmds.objExists(settings.get("custom_ikfk_switch_name")) == False:
            is_valid = False
            error_message = error_message + 'custom IK switch ctrl, '
            
    if settings.get("using_custom_ikfk_switch"):
        if cmds.objExists(settings.get("custom_ikfk_switch_name")) == False:
            is_valid = False
            error_message = error_message + 'custom IK switch ctrl, '
            
        
    if is_valid:
        generate_simple_ik_leg(is_using_ball)
    else:
        cmds.warning(error_message[:-2] + ".")



# Main Function - Generates Legs
def generate_simple_ik_leg(is_using_ball):
    ik_jnts = [] # For changing its color later
    jnt_tag_length = len(settings.get('jnt_tag'))
    # ============================= Start of Main Function =============================
    hip_jnt_start_rp_fk = stored_joints.get("hip_jnt") # Hip
    if len(cmds.listRelatives(hip_jnt_start_rp_fk, type='joint') or []) > 0: # Check if hip has children
        knee_jnt_middle_rp_fk = cmds.listRelatives(hip_jnt_start_rp_fk, type='joint')[0] # Knee
    ankle_jnt_end_rp_fk = stored_joints.get("ankle_jnt") # Ankle
    
    if is_using_ball: 
        ball_jnt_end_sc1_fk = stored_joints.get("ball_jnt") # Ball
        if len(cmds.listRelatives(ball_jnt_end_sc1_fk, type='joint') or []) > 0: # Check if ball has children
            toe_jnt_end_sc2_fk = cmds.listRelatives(ball_jnt_end_sc1_fk, type='joint')[0] # Toe

    # Creates IK Skeleton
    start_joint_rp_ik = cmds.duplicate(hip_jnt_start_rp_fk, po=True, name = hip_jnt_start_rp_fk[:-jnt_tag_length] + "_IK_Jnt") # Create IK Hip
    middle_joint_rp_ik = cmds.duplicate(knee_jnt_middle_rp_fk, po=True, name = knee_jnt_middle_rp_fk[:-jnt_tag_length] + "_IK_Jnt") # Create IK Knee
    end_joint_rp_ik = cmds.duplicate(ankle_jnt_end_rp_fk, po=True, name = ankle_jnt_end_rp_fk[:-jnt_tag_length] + "_IK_Jnt") # Create IK Ankle
    ik_jnts.append(start_joint_rp_ik)
    ik_jnts.append(middle_joint_rp_ik)
    ik_jnts.append(end_joint_rp_ik)
    
    if is_using_ball: 
        end_joint_sc1_ik = cmds.duplicate(ball_jnt_end_sc1_fk, po=True, name = ball_jnt_end_sc1_fk[:-jnt_tag_length] + "_IK_Jnt") # Create IK Ball
        end_joint_sc2_ik = cmds.duplicate(toe_jnt_end_sc2_fk, po=True, name = ball_jnt_end_sc1_fk[:-jnt_tag_length] + "_IK_Jnt") # Create IK Toe
        ik_jnts.append(end_joint_sc1_ik)
        ik_jnts.append(end_joint_sc2_ik)

    # Recreate Hierarchy (IK Skeleton)
    if len(cmds.listRelatives(start_joint_rp_ik, parent=True) or []) != 0:  # Check if parent is already world
        cmds.parent( start_joint_rp_ik, world=True)
    cmds.parent( middle_joint_rp_ik, start_joint_rp_ik )
    cmds.parent( end_joint_rp_ik, middle_joint_rp_ik )
    
    if is_using_ball: 
        cmds.parent( end_joint_sc1_ik, end_joint_rp_ik )
        cmds.parent( end_joint_sc2_ik, end_joint_sc1_ik )

    # Parent Constraints
    start_joint_rp_ik_pConstraint = cmds.parentConstraint( start_joint_rp_ik, hip_jnt_start_rp_fk )
    middle_joint_rp_ik_pConstraint = cmds.parentConstraint( middle_joint_rp_ik, knee_jnt_middle_rp_fk )
    end_joint_rp_ik_pConstraint = cmds.parentConstraint( end_joint_rp_ik, ankle_jnt_end_rp_fk )
    if is_using_ball: 
        end_joint_sc1_ik_pConstraint = cmds.parentConstraint( end_joint_sc1_ik, ball_jnt_end_sc1_fk )

    # Create Main Rotate-Plane IK Solver
    ikHandle_name = start_joint_rp_ik[0][:-jnt_tag_length] + 'RP_ikHandle'
    ikHandle_rp = cmds.ikHandle( n=ikHandle_name, sj=start_joint_rp_ik[0], ee=end_joint_rp_ik[0], sol='ikRPsolver')

    # Create Ankle to Ball Single-Chain IK Solver
    if is_using_ball: 
        ikHandle_name = end_joint_rp_ik[0][:-jnt_tag_length] + 'SC_ikHandle'
        ikHandle_sc_ball = cmds.ikHandle( n=ikHandle_name, sj=end_joint_rp_ik[0], ee=end_joint_sc1_ik[0], sol='ikSCsolver')
        ikHandle_name = end_joint_sc2_ik[0][:-4] + 'SC_ikHandle'
        ikHandle_sc_toe = cmds.ikHandle( n=ikHandle_name, sj=end_joint_sc1_ik[0], ee=end_joint_sc2_ik[0], sol='ikSCsolver')
        

    if settings.get("using_custom_ik_ctrl"):
        ik_control = settings.get("custom_ik_ctrl_name")
    else:
        ik_control = cmds.curve(name = start_joint_rp_ik[0][:-jnt_tag_length] + 'Ctrl', p=[[-0.569, 0.569, -0.569], [-0.569, 0.569, 0.569], \
                    [0.569, 0.569, 0.569], [0.569, 0.569, -0.569], [-0.569, 0.569, -0.569], [-0.569, -0.569, -0.569], \
                    [0.569, -0.569, -0.569], [0.569, 0.569, -0.569], [0.569, 0.569, 0.569], [0.569, -0.569, 0.569], \
                    [0.569, -0.569, -0.569], [-0.569, -0.569, -0.569], [-0.569, -0.569, 0.569], [0.569, -0.569, 0.569], \
                    [0.569, 0.569, 0.569], [-0.569, 0.569, 0.569], [-0.569, -0.569, 0.569]],d=1) # Creates Cube
                    
        ik_ctrl_grp = cmds.group(name=(ik_control+'Grp'))
        placement_constraint = cmds.pointConstraint(end_joint_rp_ik,ik_ctrl_grp)
        cmds.delete(placement_constraint)

    # Constraint IK Handles to IK Control
    cmds.parentConstraint(ik_control, ikHandle_rp[0], maintainOffset=True)
    if is_using_ball: 
        cmds.parentConstraint(ik_control, ikHandle_sc_ball[0], maintainOffset=True)
        cmds.parentConstraint(ik_control, ikHandle_sc_toe[0], maintainOffset=True)

    if settings.get("using_custom_pvector_ctrl"):
        pvector_ctrl = settings.get("custom_pvector_ctrl")
    else:
        pvector_ctrl = cmds.curve(name= ik_control[:-4] + 'pvector_ctrlCtrl', p=[[0.268, 0.268, 0.0], [0.535, 0.268, 0.0], [0.535, -0.268, -0.0], [0.268, -0.268, -0.0], [0.268, -0.535, -0.0], [-0.268, -0.535, -0.0], [-0.268, -0.268, -0.0], [-0.535, -0.268, -0.0], [-0.535, 0.268, 0.0], [-0.268, 0.268, 0.0], [-0.268, 0.535, 0.0], [0.268, 0.535, 0.0], [0.268, 0.268, 0.0]],d=1)
        pvector_ctrl_ctrl_grp = cmds.group(name=(pvector_ctrl +'Grp'))
        
        placement_constraint = cmds.pointConstraint(middle_joint_rp_ik,pvector_ctrl_ctrl_grp)
        cmds.delete(placement_constraint)
        
        
    cmds.poleVectorConstraint( pvector_ctrl, ikHandle_rp[0] ) 

    #Check if exists (use checker before running)
    if settings.get("using_custom_ikfk_switch"):
        ik_switch_ctrl = settings.get("custom_ikfk_switch_name")
    else:
        ik_switch_ctrl_before_naming = create_fkik_switch()
        ik_switch_ctrl = cmds.rename(ik_switch_ctrl_before_naming, ik_control.replace("_IK_Ctrl", "_") + "switch_ikfkCtrl")
        cmds.setAttr(ik_switch_ctrl + ".overrideEnabled", 1)
        cmds.setAttr(ik_switch_ctrl + ".overrideColor", 17) #Yellow 
                         
    cmds.addAttr(ik_switch_ctrl, niceName='IK FK Switch', longName='ikSwitch', attributeType='bool', defaultValue = 1, keyable = True )
    cmds.addAttr(ik_switch_ctrl, niceName='IK FK Influence', longName='ikInfluence', attributeType='double', defaultValue = 1, keyable = True )
    lock_hide_attr(ik_switch_ctrl, ['tx','ty','tz','rx','ry','rz', 'sx','sy','sz','v'],True,False)
    ik_switch_ctrlGrp = cmds.group(name=(ik_switch_ctrl+'Grp'))

    reverse_node = cmds.createNode('reverse')
    cmds.connectAttr('%s.ikSwitch' % ik_switch_ctrl, '%s.inputX' % reverse_node)

    ctrl_name = hip_jnt_start_rp_fk[:-jnt_tag_length] + settings.get("ctrl_grp_tag")
    if cmds.objExists(ctrl_name):
        cmds.connectAttr('%s.outputX' % reverse_node, '%s.v' % ctrl_name)
        
    ctrl_name = knee_jnt_middle_rp_fk[:-jnt_tag_length] + settings.get("ctrl_grp_tag")
    if cmds.objExists(ctrl_name):
        cmds.connectAttr('%s.outputX' % reverse_node, '%s.v' % ctrl_name)
      
    ctrl_name = ankle_jnt_end_rp_fk[:-jnt_tag_length] + settings.get("ctrl_grp_tag")
    if cmds.objExists(ctrl_name):
        cmds.connectAttr('%s.outputX' % reverse_node, '%s.v' % ctrl_name)  
    
    if is_using_ball: 
        ctrl_name = ball_jnt_end_sc1_fk[:-jnt_tag_length] + settings.get("ctrl_grp_tag")
        if cmds.objExists(ctrl_name):
            cmds.connectAttr('%s.outputX' % reverse_node, '%s.v' % ctrl_name)
        
    cmds.connectAttr('%s.ikSwitch' % ik_switch_ctrl, '%s.v' % ik_control)
    cmds.connectAttr('%s.ikSwitch' % ik_switch_ctrl, '%s.v' % pvector_ctrl)
    
    # Main Ctrl IK Influence
    # Creates Condition (IK Switch is one) > 
    # Reverse goes to FK weight, true data is passed to IK Weight

    condition_node = cmds.createNode('condition')
    cmds.setAttr(condition_node + '.secondTerm', 1)
    cmds.setAttr(condition_node + '.colorIfFalseR', 0)
    cmds.setAttr(condition_node + '.colorIfFalseG', 0)
    cmds.setAttr(condition_node + '.colorIfFalseB', 0)
    cmds.connectAttr('%s.ikSwitch' % ik_switch_ctrl, '%s.firstTerm' % condition_node)
    cmds.connectAttr('%s.ikInfluence' % ik_switch_ctrl, '%s.colorIfTrueR' % condition_node)

    start_joint_rp_ik_pConstraint_lwn = get_last_weight_number(start_joint_rp_ik_pConstraint[0])
    middle_joint_rp_ik_pConstraint_lwn = get_last_weight_number(middle_joint_rp_ik_pConstraint[0])
    end_joint_rp_ik_pConstraint_lwn = get_last_weight_number(end_joint_rp_ik_pConstraint[0])
    if is_using_ball: 
        end_joint_sc1_ik_pConstraint_lwn = get_last_weight_number(end_joint_sc1_ik_pConstraint[0])

    cmds.connectAttr('%s.outColorR' % condition_node, start_joint_rp_ik_pConstraint[0] + '.' + start_joint_rp_ik[0] + "W" + start_joint_rp_ik_pConstraint_lwn)
    cmds.connectAttr('%s.outColorR' % condition_node, middle_joint_rp_ik_pConstraint[0] + '.' + middle_joint_rp_ik[0] + "W" + middle_joint_rp_ik_pConstraint_lwn)
    cmds.connectAttr('%s.outColorR' % condition_node, end_joint_rp_ik_pConstraint[0] + '.' + end_joint_rp_ik[0] + "W" + end_joint_rp_ik_pConstraint_lwn)
    if is_using_ball: 
        cmds.connectAttr('%s.outColorR' % condition_node, end_joint_sc1_ik_pConstraint[0] + '.' + end_joint_sc1_ik[0] + "W" + end_joint_sc1_ik_pConstraint_lwn)

    reverse_condition_node = cmds.createNode('reverse')
    cmds.connectAttr('%s.outColorR' % condition_node, '%s.inputX' % reverse_condition_node)
    
    #Connects constraint weights to reverse node
    def connect_non_ik_weights(constraintName, nonIKWeightList):
        for obj in nonIKWeightList:
            cmds.connectAttr('%s.outputX' % reverse_condition_node, constraintName + '.' + obj)
            
    connect_non_ik_weights(start_joint_rp_ik_pConstraint[0],get_all_weights_but_not_last(start_joint_rp_ik_pConstraint[0]))
    connect_non_ik_weights(middle_joint_rp_ik_pConstraint[0],get_all_weights_but_not_last(middle_joint_rp_ik_pConstraint[0]))
    connect_non_ik_weights(end_joint_rp_ik_pConstraint[0],get_all_weights_but_not_last(end_joint_rp_ik_pConstraint[0]))
    if is_using_ball: 
        connect_non_ik_weights(end_joint_sc1_ik_pConstraint[0],get_all_weights_but_not_last(end_joint_sc1_ik_pConstraint[0]))

    # Colorize Control Start ------------------
    if settings.get("using_colorize_ctrls"):
        controls = [ik_control, pvector_ctrl]
        for ctrl in controls:
            if True == True:
                        cmds.setAttr(ctrl + ".overrideEnabled", 1)
                        if 'right_' in ctrl:
                            cmds.setAttr(ctrl + ".overrideColor", 13) #Red
                        elif 'left_' in ctrl:
                            cmds.setAttr(ctrl + ".overrideColor", 6) #Blue
                        else:
                            cmds.setAttr(ctrl + ".overrideColor", 17) #Yellow                                
                            
    # Create setup grp
    main_ik_grp_name = hip_jnt_start_rp_fk.replace("Jnt","")
    main_ik_grp = cmds.group(name=main_ik_grp_name + "_IK_Setup_grp",em=True)
    cmds.parent(start_joint_rp_ik, main_ik_grp) # Parent to Setup Grp (IK Skeleton)
    solvers_ik_grp = cmds.group(name=main_ik_grp_name + "_solvers_grp",em=True)
    # Parent to Setup Grp (Solvers)
    if is_using_ball: 
        cmds.parent(ikHandle_sc_ball[0], solvers_ik_grp)
        cmds.parent(ikHandle_sc_toe[0], solvers_ik_grp)
        
    cmds.parent(ikHandle_rp[0], solvers_ik_grp) # Parent to Setup Grp (Solvers)
    cmds.parent(solvers_ik_grp, main_ik_grp) # Parent to Setup Grp (Solvers)
    
    cmds.setAttr(solvers_ik_grp + ".v", 0) #Make solvers grp invisible
    cmds.setAttr(start_joint_rp_ik[0] + ".v", 0) #Make ik skeleton invisible
    
    
    ctrls_ik_grp = cmds.group(name=main_ik_grp_name + "_controls_grp",em=True)
    generated_ctrls = [ik_switch_ctrlGrp,pvector_ctrl_ctrl_grp,ik_ctrl_grp]
    for ctrl in generated_ctrls:
        if cmds.objExists(ctrl):
            cmds.parent(ctrl, ctrls_ik_grp)
    cmds.parent(ctrls_ik_grp, main_ik_grp)
    
    ctrls_children = cmds.listRelatives(ctrls_ik_grp, c=True) 
    if ctrls_children == None:
        cmds.delete(ctrls_ik_grp)
    
    # Add some color to the new outliner elements
    change_outliner_color(main_ik_grp,[0.240,1,0.062])
    change_outliner_color(solvers_ik_grp,[1,1,0.126])
    change_outliner_color(ctrls_ik_grp,[1,0.479,0.172])
    for jnt in ik_jnts:
        change_outliner_color(jnt[0],[0.763,0.332,0.892])

    # If not using Ball, make IK control rotate ankle
    if is_using_ball == False: 
        cmds.orientConstraint(ik_control,end_joint_rp_ik)
        
    # Make leg stretchy
    if settings.get('make_stretchy'):
        cmds.select(ikHandle_rp)
        ikHandle = cmds.ls(selection=True, type="ikHandle")
        stretchy_grp = make_stretchy_legs(ikHandle)
        cmds.parent(stretchy_grp, main_ik_grp)
        change_outliner_color(stretchy_grp,[1,0,0])
        cmds.setAttr(stretchy_grp + ".v", 0) #Make it invisible
        
    cmds.select(ik_control)

    # ============================= End of Main Function =============================


# Creates Help GUI
def build_help_gui_ik_leg_generator():
    window_name = "build_help_gui_ik_leg_generator"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title= script_name + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1,1])

    cmds.columnLayout("main_column", p= window_name)
   
    # Title Text
    cmds.separator(h=12, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p="main_column") # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column") # Title Column
    cmds.text(script_name + " Help", bgc=[0,.5,0],  fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p="main_column") # Empty Space


    # Body ====================   
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p="main_column")
    cmds.text(l='This script assumes that you are using a simple leg', align="left")
    cmds.text(l='composed of a hip joint, a knee joint an ankle joint', align="left")
    cmds.text(l='and maybe ball and toe joints.', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='In case your setup is different, I suggest you try', align="left")
    cmds.text(l='a different solution.', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Joint Tag (Suffix) and Ctrl Group Tag (Suffix):', align="left", fn="boldLabelFont")
    cmds.text(l='These two textfields allow you to define what suffix you', align="left")
    cmds.text(l='used for you base skeleton joints and your control groups.', align="left") 
    cmds.text(l='(used when creating new names or looking for controls)', align="left")
    cmds.separator(h=10, style='none') # Empty Space
    cmds.text(l='The Ctrl Group Tag is used to define the visibility of the', align="left")
    cmds.text(l='FK system.', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Custom PVector Ctrl, IK Ctrl and IK Switch:', align="left", fn="boldLabelFont")
    cmds.text(l='These options allow you to load an already existing', align="left")
    cmds.text(l='control.', align="left")
    cmds.text(l='In case you already created curve you could simply load', align="left")
    cmds.text(l='them and the script will use yours instead of creating a', align="left")
    cmds.text(l='new one', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Colorize Controls: ', align="left", fn="boldLabelFont")
    cmds.text(l='This option looks for "right_" and "left_" tags', align="left")
    cmds.text(l='and assign colors based on the found tag', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Make Stretchy Legs: ', align="left", fn="boldLabelFont")
    cmds.text(l='This option creates measure tools to define how to', align="left")
    cmds.text(l='strechy the leg when it goes beyong its current size.', align="left")
    cmds.text(l='- Term = What is being compared', align="left")
    cmds.text(l='- Condition = Default Size (used for scalling the rig)', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Use Ball Joint:', align="left", fn="boldLabelFont")
    cmds.text(l='This option allows you to define whether or not to use', align="left")
    cmds.text(l='a ball joint.', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Load \"Content\" Buttons:', align="left", fn="boldLabelFont")
    cmds.text(l='These buttons allow you to load the necessary', align="left")
    cmds.text(l='objects before running the script.', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 140),(2, 140)], cs=[(1,10),(2, 0)], p="main_column")
    cmds.text('Guilherme Trevisan  ')
    cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1,1,1])
    cmds.rowColumnLayout(nc=2, cw=[(1, 140),(2, 140)], cs=[(1,10),(2, 0)], p="main_column")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1,1,1])
    cmds.separator(h=7, style='none') # Empty Space
    
    # Close Button 
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p="main_column")
    cmds.separator(h=10, style='none')
    cmds.button(l='OK', h=30, c=lambda args: close_help_gui())
    cmds.separator(h=8, style='none')
    
    # Show and Lock Window
    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/question.png')
    widget.setWindowIcon(icon)
    
    def close_help_gui():
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)
    # Help Dialog Ends Here =================================================================================


# Locks an hides attributes
def lock_hide_attr(obj,attrArray,lock,hide):
        for a in attrArray:
            cmds.setAttr(obj + '.' + a, k=hide,l=lock)

# Returns a list of weights with the exception of the last weight
def get_all_weights_but_not_last(parentConstraint):
    if cmds.objExists(parentConstraint) and cmds.objectType(parentConstraint) in 'parentConstraint':
        constraint_weights = cmds.parentConstraint(parentConstraint,q=True, wal=True)
        weights_except_last = []
        for obj in constraint_weights:
            if constraint_weights[-1] not in obj:
                weights_except_last.append(obj)
        return weights_except_last
        

# Returns the last weight in a parentConstraint
def get_last_weight_number(parentConstraint):
    if cmds.objExists(parentConstraint) and cmds.objectType(parentConstraint) in 'parentConstraint':
        last_weight = cmds.parentConstraint(parentConstraint,q=True, wal=True)[-1]
        return last_weight.split("W")[-1] # last_weightNumber


# If object exists, select it
def if_exists_select(obj):
    if cmds.objExists(obj):
        cmds.select(obj)
        cmds.headsUpMessage(obj + " selected", verticalOffset=150 )
    else:
        cmds.warning("Object doesn't exist! Did you delete or rename it after loading?")
        
# To quickly create nurbs texts    
def create_text(text):
    cmds.textCurves(ch=0, t=text)
    print(text)
    cmds.ungroup()
    cmds.ungroup()
    curves = cmds.ls(sl=True)
    cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)
    shapes = curves[1:]
    cmds.select(shapes, r=True)
    cmds.pickWalk(d='Down')
    cmds.select(curves[0], tgl=True)
    cmds.parent(r=True, s=True)
    cmds.pickWalk(d='up')
    cmds.delete(shapes)
    cmds.xform(cp=True)
    return cmds.ls(sl=True)[0]

# Quickly create FK IK Switch
def create_fkik_switch():    
    fkik_curves = create_text("FK/IK")
    switch_curves = create_text("SWITCH")
    cmds.scale(0.679,0.679,0.679, switch_curves)
    cmds.move(-0.6,-0.9,0, switch_curves)
    cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)
    switch_shapes = cmds.listRelatives(ad=True)
    for shape in switch_shapes:
        cmds.parent(shape,fkik_curves, r=True, s=True)
    cmds.delete(switch_curves)
    cmds.pickWalk(d='up')
    cmds.xform(os=True, t=[-1.2,0,0],ro=[-90,0,0], ztp=True)
    cmds.xform(cp=1)
    cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)
    return cmds.ls(sl=True)
    
# Changes outliner color if obj exists
def change_outliner_color(obj,colorRGB):    
    if cmds.objExists(obj):
        cmds.setAttr ( obj + ".useOutlinerColor" , True)
        cmds.setAttr ( obj  + ".outlinerColor" , colorRGB[0],colorRGB[1], colorRGB[2])

# Change the outliner color of a list
def change_list_outliner_color(objList, colorRGB):
    for obj in objList:
        if cmds.objExists(obj):
            cmds.setAttr ( obj + ".useOutlinerColor" , True)
            cmds.setAttr ( obj + ".outlinerColor" , colorRGB[0],colorRGB[1],colorRGB[2])

# Make Stretchy Legs
def make_stretchy_legs(ikHandle):
    ikHandle_manipulated_joints = cmds.ikHandle(ikHandle, q=True, jointList=True)

    top_joint_position = cmds.getAttr(ikHandle_manipulated_joints[0] + '.translate')
    ikHandle_position = cmds.getAttr(ikHandle[0] + '.translate')

    distance_one = cmds.distanceDimension(sp=top_joint_position[0], ep=ikHandle_position[0] )
    distance_one_transform = cmds.listRelatives(distance_one, parent=True)[0]
    distance_one_locators = cmds.listConnections(distance_one)

    #Rename Distance One Nodes
    name_top_locator = (ikHandle_manipulated_joints[0].replace("_IK_", "")).replace("Jnt","") 
    name_bottom_locator = ((ikHandle[0].replace("_IK_","")).replace("_ikHandle","")).replace("RP","")
    name_distance_node = name_bottom_locator
    distance_node_one = cmds.rename(distance_one_transform, name_distance_node + "_strechyTerm_01")
    top_locator_one = cmds.rename(distance_one_locators[0], name_top_locator + "_ST_01")
    bottom_locator_one = cmds.rename(distance_one_locators[1], name_bottom_locator + "_ST_02")

    distance_two = cmds.distanceDimension(sp=(0,0,0), ep=(1,1,1) )

    distance_two_transform = cmds.listRelatives(distance_two, parent=True)[0]
    distance_two_locators = cmds.listConnections(distance_two)
    cmds.xform(distance_two_locators[0], t=top_joint_position[0] )
    cmds.xform(distance_two_locators[1], t=ikHandle_position[0] )

    #Rename Distance Two Nodes
    distance_node_two = cmds.rename(distance_two_transform, name_distance_node + "_strechyCondition_01")
    top_locator_two = cmds.rename(distance_two_locators[0], name_top_locator + "_SC_01")
    bottom_locator_two = cmds.rename(distance_two_locators[1], name_bottom_locator + "_SC_02")

    stretchy_grp = cmds.group(name=name_top_locator + "_stretchySystem_grp", empty=True, world=True)
    cmds.parent( distance_node_one, stretchy_grp )
    cmds.parent( top_locator_one, stretchy_grp )
    cmds.parent( bottom_locator_one, stretchy_grp )
    cmds.parent( distance_node_two, stretchy_grp )
    cmds.parent( top_locator_two, stretchy_grp )
    cmds.parent( bottom_locator_two, stretchy_grp )

    change_list_outliner_color([distance_node_one,top_locator_one,bottom_locator_one],[0,1,0]) 
    change_list_outliner_color([distance_node_two,top_locator_two,bottom_locator_two],[1,0,0])

    mel.eval('AEdagNodeCommonRefreshOutliners();') #Make sure outliner colors update

    # Start connecting everything ----------------------------------------

    stretch_normalization_node = cmds.createNode('multiplyDivide', name=name_distance_node + "_distNormalization_divide")
    cmds.connectAttr('%s.distance' % distance_node_one, '%s.input1X' % stretch_normalization_node)
    cmds.connectAttr('%s.distance' % distance_node_two, '%s.input2X' % stretch_normalization_node) # Check if necessary

    cmds.setAttr( stretch_normalization_node + ".operation", 2)

    stretch_condition_node = cmds.createNode('condition', name=name_distance_node + "_strechyCondition_condition")
    cmds.setAttr( stretch_condition_node + ".operation", 3)
    cmds.connectAttr('%s.distance' % distance_node_one, '%s.firstTerm' % stretch_condition_node)
    cmds.connectAttr('%s.distance' % distance_node_two, '%s.secondTerm' % stretch_condition_node)
    cmds.connectAttr('%s.outputX' % stretch_normalization_node, '%s.colorIfTrueR' % stretch_condition_node)

    cmds.connectAttr('%s.outColorR' % stretch_condition_node, '%s.scaleX' % ikHandle_manipulated_joints[0])
    cmds.connectAttr('%s.outColorR' % stretch_condition_node, '%s.scaleX' % ikHandle_manipulated_joints[1])


    cmds.pointConstraint (ikHandle_manipulated_joints[0], top_locator_one)
    cmds.pointConstraint (ikHandle_manipulated_joints[0], top_locator_two)

    try:
        ikHandle_parent_constraint = cmds.listRelatives(ikHandle, children=True,type='parentConstraint' )[0]
        ikHandle_ctrl = cmds.parentConstraint(ikHandle_parent_constraint, q=True, targetList=True)
        cmds.parentConstraint (ikHandle_ctrl, bottom_locator_one)
    except:
        pass
    
    return stretchy_grp

def parse_text_field(text_field_data):
    text_field_data_no_spaces = text_field_data.replace(" ", "")
    if len(text_field_data_no_spaces) <= 0:
        return []
    else:
        return_list = text_field_data_no_spaces.split(",")
        empty_objects = []
        for obj in return_list:
            if '' == obj:
                empty_objects.append(obj)
        for obj in empty_objects:
            return_list.remove(obj)
        return return_list


# Build UI
if __name__ == '__main__':
    build_gui_simple_ik_leg()