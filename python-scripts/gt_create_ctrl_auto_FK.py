"""

 Auto FK Control with Hierarchy
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-01-03
 
 1.2 - 2020-05-10 
 Fixed an issue where not using a tag wouldn't build the hierarchy.
 
 1.3 - 2020-06-06 
 Added CtrlGrp, Ctrl, Jnt Tag text fields. 
 Removed joint length button.
 Fixed random window widthHeight issue.
 Updated naming convention to make it clearer. (PEP8)
 
 1.4 - 2020-06-17
 Added help button
 Changed GUI
 Added radius option
 Added icon
 Fixed offset bug on custom python curve
 
"""
import maya.cmds as cmds
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
script_name = "GT - Auto FK"

# Version:
script_version = "1.4"

# Default Settings
mimic_hierarchy = True
constraint_joint = True
auto_color_ctrls = True
default_select_hierarchy = True
default_curve = "cmds.circle(name=joint_name + 'ctrl', normal=[1,0,0], radius=1.5, ch=False)"
default_ctrl_tag = "_ctrl"
default_ctrl_grp_tag = "_ctrlGrp"
default_joint_tag = "_jnt"

# Custom Curve Dictionary
settings = { 'using_custom_curve': False, 
             'custom_curve': default_curve,
             'failed_to_build_curve': False,
            }


# Main Form ============================================================================
def build_gui_auto_FK():
    window_name = "build_gui_auto_FK"
    if cmds.window(window_name, exists =True):
        cmds.deleteUI(window_name)    

    # Main GUI Start Here =================================================================================
    
    build_gui_auto_FK = cmds.window(window_name, title=script_name + "  v" + script_version,\
                          titleBar=True, mnb=False, mxb=False, sizeable =True)
    
    cmds.window(window_name, e=True, s=True, wh=[1,1])
    
    content_main = cmds.columnLayout()

    # Title Text
    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 10)], p=content_main) # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 200), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)], p=content_main) # Title Column
    cmds.text(" ", bgc=[0,.5,0]) # Tiny Empty Green Space
    cmds.text(script_name + " v" + script_version, bgc=[0,.5,0],  fn="boldLabelFont", align="left")
    cmds.button( l ="Help", bgc=(0, .5, 0), c=lambda x:build_gui_help_auto_FK())
    cmds.separator(h=10, style='none', p=content_main) # Empty Space

    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,10)], p=content_main)
    
    cmds.rowColumnLayout( nc=1, cw=[(1, 270)], cs=[(1, 13)], p=body_column)
    check_boxes_one = cmds.checkBoxGrp(columnWidth2=[120, 1], numberOfCheckBoxes=2, \
                                label1 = 'Mimic Hierarchy', label2 = "Constraint Joint    ", v1 = mimic_hierarchy, v2 = constraint_joint) 
    
    cmds.rowColumnLayout( nc=1, cw=[(1, 270)], cs=[(1, 13)], p=body_column)
    
    check_boxes_two = cmds.checkBoxGrp(columnWidth2=[120, 1], numberOfCheckBoxes=2, \
                                label1 = 'Colorize Controls', label2 = "Select Hierarchy  ", v1 = auto_color_ctrls, v2 = default_select_hierarchy)
            
    cmds.rowColumnLayout( nc=1, cw=[(1, 270)], cs=[(1, 0)], p=body_column)
    cmds.separator(h=10)
    cmds.separator(h=5, style='none') # Empty Space
    
    # Customize Control
    cmds.rowColumnLayout( nc=1, cw=[(1, 230)], cs=[(1, 0)], p=body_column)
    ctrl_curve_radius_slider_grp = cmds.floatSliderGrp( cw=[(1, 100),(2, 50),(3, 10)], label='Curve Radius: ', field=True, value=1.0 )  
    cmds.separator(h=7, style='none') # Empty Space                   
    cmds.rowColumnLayout( nc=1, cw=[(1, 230)], cs=[(1, 13)], p=body_column)
    cmds.button(l ="(Advanced) Custom Curve", c=lambda x:define_custom_curve())
    
    cmds.rowColumnLayout( nc=1, cw=[(1, 270)], cs=[(1, 0)], p=body_column)
    cmds.separator(h=5, style='none') # Empty Space
    cmds.separator(h=10)
    
    # Text Fields   
    cmds.rowColumnLayout(nc=3, cw=[(1, 70),(2, 75),(3, 100)], cs=[(1,5),(2, 0)], p=body_column)
    cmds.text("Joint Tag:")
    cmds.text("Control Tag:")
    cmds.text("Control Grp Tag:")
    joint_tag_text_field = cmds.textField(text = default_joint_tag, enterCommand=lambda x:generate_FK_controls())
    ctrl_tag_text_field = cmds.textField(text = default_ctrl_tag, enterCommand=lambda x:generate_FK_controls())
    ctrl_grp_tag_text_field = cmds.textField(text = default_ctrl_grp_tag, enterCommand=lambda x:generate_FK_controls())
       

    cmds.rowColumnLayout( nc=1, cw=[(1, 260)], cs=[(1, 0)], p=body_column)
    
    cmds.separator(h=10)
    cmds.separator(h=5, style='none') # Empty Space
    cmds.text(label='Ignore Joints Containing These Strings:' )
    cmds.rowColumnLayout( nc=1, cw=[(1, 245)], cs=[(1, 5)], p=body_column)
    undesired_strings_text_field = cmds.textField(text="end, eye", enterCommand=lambda x:generate_FK_controls())
    cmds.rowColumnLayout( nc=1, cw=[(1, 260)], cs=[(1, 0)], p=body_column)
    cmds.text(label='(Use Commas to Separate Strings)' )
    cmds.separator(h=5, style='none') # Empty Space
    cmds.separator(h=10)
    cmds.separator(h=10, style='none') # Empty Space
    cmds.button(l ="Generate", bgc=(.6, .8, .6), c=lambda x:generate_FK_controls())
    cmds.separator(h=10, style='none') # Empty Space
    
    # Generate FK Main Function Starts --------------------------------------------
    def generate_FK_controls():
        ctrl_curve_radius = cmds.floatSliderGrp(ctrl_curve_radius_slider_grp, q=True, value=True)
        selected_joints = cmds.ls(selection=True, type='joint')
        if cmds.checkBoxGrp(check_boxes_two, q=True, value2=True):
            cmds.select(hierarchy=True)
            selected_joints = cmds.ls(selection=True, type='joint')
        ctrl_tag =parse_text_field(cmds.textField(ctrl_tag_text_field, q=True, text=True))[0]
        ctrl_grp_tag = parse_text_field(cmds.textField(ctrl_grp_tag_text_field, q=True, text=True))[0]
        joint_tag = parse_text_field(cmds.textField(joint_tag_text_field, q=True, text=True))[0]
        undesired_jnt_strings = parse_text_field(cmds.textField(undesired_strings_text_field, q=True, text=True))
        undesired_joints = []
        
        # Find undesired joints and make a list of them
        for jnt in selected_joints:
            for string in undesired_jnt_strings:
                if string in jnt:
                    undesired_joints.append(jnt)
                else:
                    pass
        
        # Remove undesired joints from selection list
        for jnt in undesired_joints:
            selected_joints.remove(jnt)

        
        for jnt in selected_joints:
            if len(joint_tag) != 0:
                joint_name = jnt.replace(joint_tag,"")
            else:
                joint_name = jnt
            ctrlName = joint_name + ctrl_tag
            ctrlGrpName = joint_name + ctrl_grp_tag


            if settings.get("using_custom_curve"):
                ctrl = create_custom_curve(settings.get("custom_curve"))
                
                ctrl = [cmds.rename(ctrl, ctrlName)]
                
                if settings.get("failed_to_build_curve"):
                    ctrl = cmds.circle(name=ctrlName, normal=[1,0,0], radius=ctrl_curve_radius, ch=False)
            else:
                ctrl = cmds.circle(name=ctrlName, normal=[1,0,0], radius=ctrl_curve_radius, ch=False)
                
            grp = cmds.group(name=ctrlGrpName, empty=True)
            cmds.parent(ctrl, grp)
            constraint = cmds.parentConstraint(jnt, grp)
            cmds.delete(constraint)
            

            # Colorize Control Start ------------------

            if cmds.checkBoxGrp(check_boxes_two, q=True, value1=True):
                cmds.setAttr(ctrl[0] + ".overrideEnabled", 1)
                if 'right_' in ctrl[0]:
                    cmds.setAttr(ctrl[0] + ".overrideColor", 13) #Red
                elif 'left_' in ctrl[0]:
                    cmds.setAttr(ctrl[0] + ".overrideColor", 6) #Blue
                else:
                    cmds.setAttr(ctrl[0] + ".overrideColor", 17) #Yellow
            else:
                pass
            
            # Colorize Control End ---------------------
            
            
            if cmds.checkBoxGrp(check_boxes_one, q=True, value2=True):
                cmds.parentConstraint(ctrlName,jnt)
            
            if cmds.checkBoxGrp(check_boxes_one, q=True, value1=True):
                #Auto parents new controls
                # "or []" Accounts for root joint that doesn't have a parent, it forces it to be a list
                jnt_parent = cmds.listRelatives(jnt, allParents=True) or []
                if len(jnt_parent) == 0:
                    pass
                else:
                    
                    if len(joint_tag) != 0:
                        parent_ctrl = (jnt_parent[0].replace(joint_tag,"") + ctrl_tag)
                    else:
                        parent_ctrl = (jnt_parent[0] + ctrl_tag)
                    
                    if cmds.objExists(parent_ctrl):
                        cmds.parent(grp, parent_ctrl)
    # Generate FK Main Function Ends --------------------------------------------
    
    # Define Custom Curve
    def define_custom_curve():
        result = cmds.promptDialog(
                        title='Py Curve',
                        message='Paste Python Curve Below: \n(Use \"GT Generate Python Curve \" to extract it from an existing curve)',
                        button=['OK', 'Use Default'],
                        defaultButton='OK',
                        cancelButton='Use Default',
                        dismissString='Use Default')

        if result == 'OK':
            settings["custom_curve"] = cmds.promptDialog(query=True, text=True)
            settings["using_custom_curve"] = True
            cmds.floatSliderGrp(ctrl_curve_radius_slider_grp, e=True, en=False)
            settings["failed_to_build_curve"] = False
        else:
            settings["using_custom_curve"] = False
            cmds.floatSliderGrp(ctrl_curve_radius_slider_grp, e=True, en=True)
  
    # Show and Lock Window
    cmds.showWindow(build_gui_auto_FK)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/kinInsert.png')
    widget.setWindowIcon(icon)
    
    # Main GUI Ends Here =================================================================================

# Creates Help GUI
def build_gui_help_auto_FK():
    window_name = "build_gui_help_auto_FK"
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
    cmds.text(l='This script generates FK controls for joints while storing', align="left")
    cmds.text(l='their transforms in groups.', align="left")
    cmds.text(l='Select desired joints and run script.', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Colorize Controls:', align="left", fn="boldLabelFont")
    cmds.text(l='Automatically colorize controls according to their', align="left")
    cmds.text(l='names. ', align="left")
    cmds.text(l='No Prefix = Yellow', align="left")
    cmds.text(l='"left_" = Blue', align="left")
    cmds.text(l='"right_" = Red', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Select Hierarchy: ', align="left", fn="boldLabelFont")
    cmds.text(l='Automatically selects the rest of the hierarchy of the', align="left")
    cmds.text(l='selected object, thus allowing you to only select the', align="left")
    cmds.text(l='root joint before creating controls.', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='(Advanced) Custom Curve:', align="left", fn="boldLabelFont")
    cmds.text(l='You can change the curve used for the creation of the', align="left")
    cmds.text(l='controls. Use the script "GT Generate Python Curve"', align="left")
    cmds.text(l='to generate the code you need to enter here.', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Joint, Control, and Control Group Tag:', align="left", fn="boldLabelFont")
    cmds.text(l='Used to determine the suffix of the elements.', align="left")
    cmds.text(l='Joint Tag is removed from the joint name for the control.', align="left")
    cmds.text(l='Control Tag is added to the generated control.', align="left")
    cmds.text(l='Control Group Tag is added to the control group.', align="left")
    cmds.text(l='(This is the transform carrying the transforms of the joint).', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Ignore Joints Containing These Strings: ', align="left", fn="boldLabelFont")
    cmds.text(l='The script will ignore joints containing these strings.', align="left")
    cmds.text(l='To add multiple strings use commas - ",".', align="left")
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



# Function to Parse textField data 
def parse_text_field(textFieldData):
    text_field_data_no_spaces = textFieldData.replace(" ", "")
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


# Force Run Nested Exec
def create_custom_curve(input):
    try:
        exec(input)
        return cmds.ls(selection=True)
    except:
        cmds.error("Something is wrong with your python curve!")
        settings["failed_to_build_curve"] = True
        

#Start current "Main"
build_gui_auto_FK()