"""
 Inbetween Generator -> Simple script used to create Inbetween Transforms
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-02-04
 1.1 - 2020-02-18
 Added Color Picker

 1.2 - 2020-06-07
 Updated naming convention to make it clearer. (PEP8)
 Changed Script Name. (Previously rigLayer Generator)
 Fixed random window widthHeight issue.
 
 To do: 
 Add option to use a different methods of position matching (use getAttr values)
 Add option to use joint's orientation instead of rotation
 
"""
import maya.cmds as cmds

# Version
script_version = "v1.2";

settings = { 'outliner_color': [0,1,0] }

# Main Form ============================================================================
def build_gui_generate_inbetween():
    if cmds.window("build_gui_generate_inbetween", exists =True):
        cmds.deleteUI("build_gui_generate_inbetween")    

    # Main GUI Start Here =================================================================================
    
    # Build UI
    build_gui_generate_inbetween = cmds.window("build_gui_generate_inbetween", title="gt_inbetween " + script_version,\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =False,widthHeight=[323, 217])
    column_main = cmds.columnLayout() 
    
    form = cmds.formLayout(p=column_main)

    content_main = cmds.columnLayout(adj = True)

    cmds.text("")
    cmds.text("GT - In-between Generator - " + script_version, bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.text("  ")
    cmds.text("      This script creates a inbetween_transform (transform)       ")
    cmds.text('      for selected elements  ')

    cmds.separator(h=15, p=content_main)
    
    mid_container = cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 25)
    transform_type = cmds.optionMenu(p=mid_container, label='  Layer Type')
    cmds.menuItem( label='Group' )
    cmds.menuItem( label='Joint' )
    cmds.menuItem( label='Locator' )
    
    transform_parent_type = cmds.optionMenu(p=mid_container, label='  Parent Type')
    cmds.menuItem( label='Selection' )
    cmds.menuItem( label='Parent' )
    cmds.text("  ",p=mid_container)
    
    empty_container_spacer = cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 10)
    color_container = cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 25)
    color_slider = cmds.colorSliderGrp(label='Outliner Color  ', rgb=(settings.get("outliner_color")[0], \
                                                                settings.get("outliner_color")[1], settings.get("outliner_color")[2]),\
                                                                columnWidth=((1,85),(3,130)), cc=lambda x:update_stored_values())
    
    cmds.separator(h=15, p=content_main)
    bottom_container = cmds.rowColumnLayout(p=content_main,adj=True)
    cmds.text('New Transform Tag:',p=bottom_container)
    desired_tag = cmds.textField(p = bottom_container, text="_rigLayer", enterCommand=lambda x:create_inbetween(parse_text_field(cmds.textField(desired_tag, q=True, text=True))[0],\
                                                                        cmds.optionMenu(transform_parent_type, q=True, value=True),\
                                                                        cmds.optionMenu(transform_type, q=True, value=True)))
    cmds.button(p=bottom_container, l ="Generate", bgc=(.6, .8, .6), c=lambda x:create_inbetween(parse_text_field(cmds.textField(desired_tag, q=True, text=True))[0],\
                                                                        cmds.optionMenu(transform_parent_type, q=True, value=True),\
                                                                        cmds.optionMenu(transform_type, q=True, value=True)))
                                                                                                                              
    # Updates Stored Values
    def update_stored_values():
        settings["outliner_color"] = cmds.colorSliderGrp(color_slider, q=True, rgb=True)
        #print(settings.get("outliner_color")) Debugging
        
    cmds.showWindow(build_gui_generate_inbetween)

    # Main GUI Ends Here =================================================================================


# Main Function
# layer_tag = string to use as tag
# parent_type = parent, or selection (determines the pivot)
# layer_type = joint, locator or group(also nothing) : inbetween type
def create_inbetween(layer_tag,parent_type,layer_type):
    selection = cmds.ls(selection=True)

    for obj in selection:
        cmds.select( clear=True )
        if layer_type == "Joint":
            inbetween_transform = cmds.joint(name=(obj + layer_tag))
        if layer_type == "Locator":
            inbetween_transform = cmds.spaceLocator(name=(obj + layer_tag))[0]
        if layer_type == "Group":
            inbetween_transform = cmds.group(name=(obj + layer_tag),empty=True)
             
        cmds.setAttr ( inbetween_transform + ".useOutlinerColor" , True)
        cmds.setAttr ( inbetween_transform  + ".outlinerColor" , settings.get("outliner_color")[0],settings.get("outliner_color")[1], settings.get("outliner_color")[2])
        selection_parent = cmds.listRelatives(obj, parent=True) or []
        
        if len(selection_parent) != 0 and parent_type == "Parent" : 
            constraint = cmds.parentConstraint(selection_parent[0],inbetween_transform)
            cmds.delete(constraint)
            cmds.parent( inbetween_transform, selection_parent[0])
            cmds.parent( obj, inbetween_transform) 
        elif len(selection_parent) == 0 and parent_type == "Parent" :
            cmds.parent( obj, inbetween_transform)
            
        if len(selection_parent) != 0 and parent_type == "Selection" : 
            constraint = cmds.parentConstraint(obj,inbetween_transform)
            cmds.delete(constraint)
            cmds.parent( inbetween_transform, selection_parent[0])
            cmds.parent( obj, inbetween_transform)
        elif len(selection_parent) == 0 and parent_type == "Selection" :
            constraint = cmds.parentConstraint(obj,inbetween_transform)
            cmds.delete(constraint)
            cmds.parent( obj, inbetween_transform)

# Function to Parse textField data 
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

#Run Script
build_gui_generate_inbetween()