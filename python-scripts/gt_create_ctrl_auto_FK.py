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

"""
import maya.cmds as cmds

# Version:
script_version = "v1.3"

# Default Settings
mimic_hierarchy = True
constraint_joint = True
auto_color_ctrls = True
default_select_hierarchy = True
default_curve = "cmds.circle(name=joint_name + 'Ctrl', normal=[1,0,0], radius=1.5, ch=False)"
default_ctrl_tag = "_Ctrl"
default_ctrl_grp_tag = "_CtrlGrp"
default_joint_tag = "_Jnt"

# Custom Curve Dictionary
settings = { 'using_custom_curve': False, 
             'custom_curve': default_curve,
             'failed_to_build_curve': False,
            }


# Main Form ============================================================================
def build_gui_auto_FK():
    if cmds.window("build_gui_auto_FK", exists =True):
        cmds.deleteUI("build_gui_auto_FK")    

    # Main GUI Start Here =================================================================================

    build_gui_auto_FK = cmds.window("build_gui_auto_FK", title="gt_autoFK - " + script_version,\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable = False, widthHeight=[269, 392])
    
    column_main = cmds.columnLayout() 

    form = cmds.formLayout(p=column_main)

    content_main = cmds.columnLayout(adj = True)

    cmds.text("")
    cmds.text("GT - Auto FK with Hierarchy - " + script_version, bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.text("  ")
    cmds.text("      This script generates FK controls while       ")
    cmds.text("      storing their transforms in groups.     ")
    cmds.text("      Select desired joints and run script.     ")
    cmds.text("   ")
    cmds.text("Steps:")
    cmds.text('1. Select Joints   ')
    cmds.text('2. Generate Controls')
    cmds.text("   ")
    cmds.separator(h=10, p=content_main)
    check_boxes_one_container = cmds.rowColumnLayout( numberOfRows=1, h= 25)
    cmds.text("      ")
    check_boxes_one = cmds.checkBoxGrp(p=check_boxes_one_container, columnWidth2=[120, 1], numberOfCheckBoxes=2, \
                                label1 = 'Mimic Hierarchy', label2 = "Constraint Joint    ", v1 = mimic_hierarchy, v2 = constraint_joint) 
    check_boxes_two_container = cmds.rowColumnLayout( numberOfRows=1, h= 25,p=content_main)
    cmds.text("      ")
    
    check_boxes_two = cmds.checkBoxGrp(p=check_boxes_two_container, columnWidth2=[120, 1], numberOfCheckBoxes=2, \
                                label1 = 'Colorize Controls', label2 = "Select Hierarchy  ", v1 = auto_color_ctrls, v2 = default_select_hierarchy)
    cmds.button(p=content_main, l ="(Advanced) Custom Curve", c=lambda x:define_custom_curve())

    cmds.rowColumnLayout(p=content_main,numberOfRows=1, h= 7) #Empty Space
    
    # Text Fields
    joint_tag_text_field_container = cmds.rowColumnLayout(p=content_main, numberOfRows=1)
    cmds.text("Joint Tag:", width=130, p=joint_tag_text_field_container)
    joint_tag_text_field = cmds.textField(p = joint_tag_text_field_container ,text = default_joint_tag, width=130, enterCommand=lambda x:generate_FK_controls())
    
    ctrl_tag_text_field_container = cmds.rowColumnLayout(p=content_main, numberOfRows=1)
    cmds.text("Control Tag:", width=130, p=ctrl_tag_text_field_container)
    ctrl_tag_text_field = cmds.textField(p = ctrl_tag_text_field_container ,text = default_ctrl_tag,width=130, enterCommand=lambda x:generate_FK_controls())
    
    ctrl_grp_tag_text_field_container = cmds.rowColumnLayout(p=content_main, numberOfRows=1)
    cmds.text("Control Group Tag:", width=130, p=ctrl_grp_tag_text_field_container)
    ctrl_grp_tag_text_field = cmds.textField(p = ctrl_grp_tag_text_field_container ,text = default_ctrl_grp_tag,width=130, enterCommand=lambda x:generate_FK_controls())
                                

    cmds.rowColumnLayout(numberOfRows=1, h= 7) #Empty Space
    
    cmds.separator(h=10, p=content_main)
    cmds.text(p=content_main, label='Ignore Joints Containing These Strings:' )
    #cmds.separator(h=5, p=content_main)
    undesired_strings_text_field = cmds.textField(p = content_main, text="End, eye", enterCommand=lambda x:generate_FK_controls())
    cmds.text(p=content_main, label='(Use Commas to Separate Strings)' )
    cmds.separator(h=10, p=content_main)
    cmds.button(p=content_main, l ="Generate", bgc=(.6, .8, .6), c=lambda x:generate_FK_controls())
    
    # Generate FK Main Function Starts --------------------------------------------
    def generate_FK_controls():
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
                print(joint_tag)
                joint_name = jnt.replace(joint_tag,"")
            else:
                joint_name = jnt
            ctrlName = joint_name + ctrl_tag
            ctrlGrpName = joint_name + ctrl_grp_tag


            if settings.get("using_custom_curve"):
                ctrl = create_custom_curve(settings.get("custom_curve"))
                print(ctrl)
                ctrl = cmds.rename(ctrl, ctrlName)
                if settings.get("failed_to_build_curve"):
                    ctrl = cmds.circle(name=ctrlName, normal=[1,0,0], radius=1.5, ch=False)
            else:
                ctrl = cmds.circle(name=ctrlName, normal=[1,0,0], radius=1.5, ch=False)
                
            
            grp = cmds.group(name=ctrlGrpName)
            constraint = cmds.parentConstraint(jnt,grp)
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
      
    cmds.showWindow(build_gui_auto_FK)
    # Main GUI Ends Here =================================================================================


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

# Define Custom Curve by updating a dictonary
def define_custom_curve():
    result = cmds.promptDialog(
                    title='Py Curve',
                    message='Paste Python Curve Below:',
                    button=['OK', 'Use Default'],
                    defaultButton='OK',
                    cancelButton='Use Default',
                    dismissString='Use Default')

    if result == 'OK':
        settings["custom_curve"] = cmds.promptDialog(query=True, text=True)
        settings["using_custom_curve"] = True
        settings["failed_to_build_curve"] = False
    else:
        settings["using_custom_curve"] = False

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