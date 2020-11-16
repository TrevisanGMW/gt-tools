"""

 GT Transfer Transforms - Script for quickly transfering Translate, Rotate, and Scale between objects.
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-06-07
 
 1.1 - 2020-06-09
 Added Copy/Paste TRS options.
 
 1.2 - 2020-06-18
 Changed GUI
 Added icons
 Added help menu
 
 1.3 - 2020-11-15
 Updated a few UI elements and colors
 Removed a few unnecessary lines
 
 To Do:
 Use a dictionary instead of list for attributes.
 Add checks before getting, setting.
 Make get and set use previous settings
 Extract short name when comparing left/right for nonunique setups

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
script_name = "GT - Transfer Transforms"

# Version:
script_version = "1.2"


# Main Form ============================================================================
def build_gui_transfer_transforms():
    window_name = "build_gui_transfer_transforms"
    if cmds.window(window_name, exists =True):
        cmds.deleteUI(window_name)    

    # Main GUI Start Here =================================================================================

    build_gui_transfer_transforms = cmds.window(window_name, title=script_name + '  (v' + script_version + ')',\
                          titleBar=True, mnb=False, mxb=False, sizeable =True)
                          
    cmds.window(window_name, e=True, s=True, wh=[1,1])
    
    content_main = cmds.columnLayout(adj = True)

    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 240)], cs=[(1, 10)], p=content_main) # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 170), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)], p=content_main) # Title Column
    cmds.text(" ", bgc=title_bgc_color) # Tiny Empty Green Space
    cmds.text(script_name, bgc=title_bgc_color,  fn="boldLabelFont", align="left")
    cmds.button( l ="Help", bgc=title_bgc_color, c=lambda x:build_gui_help_transfer_transforms())
    cmds.separator(h=10, style='none') # Empty Space
    
    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 230)], cs=[(1,10)], p=content_main)
    
    cmds.rowColumnLayout(nc=1, cw=[(1, 230)], cs=[(1,20)])
    transform_column_width = [100, 1]
    
    # Translate
    translate_x_checkbox = cmds.checkBoxGrp(columnWidth2=transform_column_width, numberOfCheckBoxes=2, \
                                label1 = '  Translate X', label2 = "Invert Value", v1 = True, v2 = False) 
                                
    translate_y_checkbox = cmds.checkBoxGrp(columnWidth2=transform_column_width, numberOfCheckBoxes=2, \
                                label1 = '  Translate Y', label2 = "Invert Value", v1 = True, v2 = False) 

    translate_z_checkbox = cmds.checkBoxGrp(columnWidth2=transform_column_width, numberOfCheckBoxes=2, \
                                label1 = '  Translate Z', label2 = "Invert Value", v1 = True, v2 = False) 
        
    cmds.separator(h=10, p=body_column)
    
    # Rotate
    cmds.rowColumnLayout(nc=1, cw=[(1, 230)], cs=[(1,20)], p=body_column)              
    rotate_x_checkbox = cmds.checkBoxGrp(columnWidth2=transform_column_width, numberOfCheckBoxes=2, \
                                label1 = '  Rotate X', label2 = "Invert Value", v1 = True, v2 = False) 
                                
    rotate_y_checkbox = cmds.checkBoxGrp(columnWidth2=transform_column_width, numberOfCheckBoxes=2, \
                                label1 = '  Rotate Y', label2 = "Invert Value", v1 = True, v2 = False) 
                                
    rotate_z_checkbox = cmds.checkBoxGrp(columnWidth2=transform_column_width, numberOfCheckBoxes=2, \
                                label1 = '  Rotate Z', label2 = "Invert Value", v1 = True, v2 = False) 
         
    cmds.separator(h=10, p=body_column)
    
    # Scale  
    cmds.rowColumnLayout(nc=1, cw=[(1, 230)], cs=[(1,20)], p=body_column)                        
    scale_x_checkbox = cmds.checkBoxGrp(columnWidth2=transform_column_width, numberOfCheckBoxes=2, \
                                label1 = '  Scale X', label2 = "Invert Value", v1 = True, v2 = False) 
    
    scale_y_checkbox = cmds.checkBoxGrp(columnWidth2=transform_column_width, numberOfCheckBoxes=2, \
                                label1 = '  Scale Y', label2 = "Invert Value", v1 = True, v2 = False) 
    
    scale_z_checkbox = cmds.checkBoxGrp(columnWidth2=transform_column_width, numberOfCheckBoxes=2, \
                                label1 = '  Scale Z', label2 = "Invert Value", v1 = True, v2 = False) 

    cmds.separator(h=10, p=body_column)
    
    # Left Side Tag text fields
    
    #side_text_container = cmds.rowColumnLayout( p=content_main, numberOfRows=1, adj=True)
    cmds.rowColumnLayout(nc=2, cw=[(1, 100),(2, 100)], cs=[(1,15),(2,0)], p=body_column)  
    cmds.text("Left Side Tag:")
    cmds.text("Right Side Tag:")  
    
    cmds.separator(h=7, style='none', p=body_column) # Empty Space 
    
    cmds.rowColumnLayout(nc=2, cw=[(1, 100),(2, 100)], cs=[(1,15),(2,0)], p=body_column)  
    left_tag_text_field = cmds.textField(text="left_", enterCommand=lambda x:update_stored_values_and_run())
    right_tag_text_field = cmds.textField(text="right_", enterCommand=lambda x:update_stored_values_and_run())
    
    cmds.separator(h=7, style='none', p=body_column) # Empty Space 

    cmds.rowColumnLayout(nc=1, cw=[(1, 210)], cs=[(1,10)], p=body_column)     
    cmds.button(l ="From Right to Left", c=lambda x:transfer_transforms_side_to_side("right"))
    cmds.button(l ="From Left to Right", c=lambda x:transfer_transforms_side_to_side("left"))
    cmds.separator(h=7, style='none', p=body_column) # Empty Space 
    cmds.separator(h=10, p=body_column)
    
    cmds.separator(h=7, style='none', p=body_column) # Empty Space 
    cmds.button(p=body_column, l ="Transfer (Source/Targets)", bgc=(.6, .6, .6), c=lambda x:transfer_transforms())
    cmds.separator(h=7, style='none', p=body_column) # Empty Space 
    
    cmds.separator(h=10, p=content_main)
    
    # Copy and Paste Transforms
    copy_text_container = cmds.rowColumnLayout(p=content_main, numberOfRows=1, adj=True)
    cmds.text("Copy and Paste Transforms", p=copy_text_container)
    cmds.separator(h=7, style='none', p=content_main) # Empty Space
    
    cmds.rowColumnLayout(nc=4, cw=[(1, 20),(2, 65),(3, 65),(4, 65)], cs=[(1,15),(2,0)], p=content_main)

    cmds.text(" ")
    cmds.text("X", bgc=[.5,0,0])
    cmds.text("Y", bgc=[0,.5,0])
    cmds.text("Z", bgc=[0,0,.5])

    cmds.text("T")
    tx_copy_text_field = cmds.textField(text="0.0", ann="tx")
    ty_copy_text_field = cmds.textField(text="0.0", ann="ty")
    tz_copy_text_field = cmds.textField(text="0.0", ann="tz")
    
    cmds.text("R")
    rx_copy_text_field = cmds.textField(text="0.0", ann="rx")
    ry_copy_text_field = cmds.textField(text="0.0", ann="ry")
    rz_copy_text_field = cmds.textField(text="0.0", ann="rz")
    
    cmds.text("S")
    sx_copy_text_field = cmds.textField(text="1.0", ann="sx")
    sy_copy_text_field = cmds.textField(text="1.0", ann="sy")
    sz_copy_text_field = cmds.textField(text="1.0", ann="sz")
    
    cmds.separator(h=7, style='none', p=content_main) # Empty Space
    
    cmds.rowColumnLayout(nc=2, cw=[(1, 115),(2, 115)], cs=[(1,10),(2,0)], p=content_main)
    
    cmds.button(l ="Get TRS", c=lambda x:transfer_transforms_copy_paste("get"))
    cmds.button(l ="Set TRS", c=lambda x:transfer_transforms_copy_paste("set"))
    
    cmds.separator(h=7, style='none', p=content_main) # Empty Space
    
    def extract_checkbox_transform_value(checkbox_grp, attribute_name):
        is_used = cmds.checkBoxGrp(checkbox_grp, q=True, value1=True)
        is_inverted = cmds.checkBoxGrp(checkbox_grp, q=True, value2=True)
        attribute_name = attribute_name
        return [is_used, is_inverted, attribute_name]
        
    def get_desired_transforms():
        transforms = []
        tx = extract_checkbox_transform_value(translate_x_checkbox,"tx")
        ty = extract_checkbox_transform_value(translate_y_checkbox,"ty")
        tz = extract_checkbox_transform_value(translate_z_checkbox,"tz")
        
        rx = extract_checkbox_transform_value(rotate_x_checkbox,"rx")
        ry = extract_checkbox_transform_value(rotate_y_checkbox,"ry")
        rz = extract_checkbox_transform_value(rotate_z_checkbox,"rz")
        
        sx = extract_checkbox_transform_value(scale_x_checkbox,"sx")
        sy = extract_checkbox_transform_value(scale_y_checkbox,"sy")
        sz = extract_checkbox_transform_value(scale_z_checkbox,"sz")
        
        transforms.append(tx)
        transforms.append(ty)
        transforms.append(tz)
        
        transforms.append(rx)
        transforms.append(ry)
        transforms.append(rz)
        
        transforms.append(sx)
        transforms.append(sy)
        transforms.append(sz)
        return transforms
    
    # Main Function Starts --------------------------------------------
    def transfer_transforms():
        
        if len(cmds.ls(selection=True)) != 0:
            source = cmds.ls(selection=True)[0]
            targets = cmds.ls(selection=True)
            targets.remove(source)
            
            # Settings
            transforms = get_desired_transforms()
            
            # Transfer 
            for transform in transforms:

                if transform[0]: # Using Transform?
                    if transform[1]: #Inverted?
                        source_transform = (cmds.getAttr(source + "." + transform[2]) * -1)
                    else:
                        source_transform = cmds.getAttr(source + "." + transform[2])
                    
                    for target in targets:
                        cmds.setAttr(target + "." + transform[2], source_transform)
        else:
            cmds.warning("Select source 1st, then targets 2nd, 3rd...")
                        
    # Main Function Ends --------------------------------------------
    
    def transfer_transforms_side_to_side(source_side):
        
        if len(cmds.ls(selection=True)) != 0:
        
            #Settings
            left_side_tag = parse_text_field(cmds.textField(left_tag_text_field, q=True, text=True))[0]
            right_side_tag = parse_text_field(cmds.textField(right_tag_text_field, q=True, text=True))[0]
            transforms = get_desired_transforms()
            
            selection = cmds.ls(selection=True)
            
            right_side_objects = []
            left_side_objects = []

            for obj in selection:  
                if right_side_tag in obj:
                    right_side_objects.append(obj)
                    
            for obj in selection:  
                if left_side_tag in obj:
                    left_side_objects.append(obj)

             
            for left_obj in left_side_objects:
                for right_obj in right_side_objects:
                    remove_side_tag_left = left_obj.replace(left_side_tag,"")
                    remove_side_tag_right = right_obj.replace(right_side_tag,"")
                    if remove_side_tag_left == remove_side_tag_right:
                        print(right_obj + " was paired with " + left_obj)
                        
                        # Transfer Right to Left
                        if source_side is "right":
                            for transform in transforms:
                                if transform[0]: # Using Transform?
                                    if transform[1]: # Inverted?
                                        source_transform = (cmds.getAttr(right_obj + "." + transform[2]) * -1)
                                    else:
                                        source_transform = cmds.getAttr(right_obj + "." + transform[2])
                                    
                                    cmds.setAttr(left_obj + "." + transform[2], source_transform)
                                    
                        # Transfer Left to Right
                        if source_side is "left":
                            for transform in transforms:
                                if transform[0]: # Using Transform?
                                    if transform[1]: # Inverted?
                                        source_transform = (cmds.getAttr(left_obj + "." + transform[2]) * -1)
                                    else:
                                        source_transform = cmds.getAttr(left_obj + "." + transform[2])
                                    
                                    cmds.setAttr(right_obj + "." + transform[2], source_transform)
        else:
            cmds.warning("Select all elements you want to match before running the script")                 
    # Side to Side Function Ends --------------------------------------------

    # Copy Paste Function Starts --------------------------------------------
    def transfer_transforms_copy_paste(operation):
        copy_text_fields = [tx_copy_text_field, ty_copy_text_field, tz_copy_text_field,\
                            rx_copy_text_field, ry_copy_text_field, rz_copy_text_field,\
                            sx_copy_text_field, sy_copy_text_field, sz_copy_text_field]

        if operation == "get":
            if len(cmds.ls(selection=True)) != 0:
                #Object to Get
                source = cmds.ls(selection=True)[0]

                # Settings
                transforms = get_desired_transforms()
                
                # Transfer 
                for transform in transforms:

                    if transform[0]: # Using Transform?
                        if transform[1]: #Inverted?
                            source_transform = (cmds.getAttr(source + "." + transform[2]) * -1)
                        else:
                            source_transform = cmds.getAttr(source + "." + transform[2])
                        
                        for text_field in copy_text_fields:
                            if cmds.textField(text_field, q=True, ann=True) == transform[2]:
                                cmds.textField(text_field, e=True, en=True)
                                cmds.textField(text_field, e=True, text=source_transform)
            else: 
                cmds.warning("Select an object to get its transforms")
            
        if operation == "set":
            if len(cmds.ls(selection=True)) != 0:
                #Objects to Set
                targets = cmds.ls(selection=True)

                # Settings
                transforms = get_desired_transforms()
                
                # Transfer 
                for text_field in copy_text_fields:
                    for target in targets:
                        cmds.setAttr(target + "." + cmds.textField(text_field, q=True, ann=True), float(cmds.textField(text_field, q=True, text=True)))
            else: 
                cmds.warning("Select objects to set their transforms")
    # Copy Paste Function Ends --------------------------------------------
    
    # Show and Lock Window
    cmds.showWindow(build_gui_transfer_transforms)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/transform.svg')
    widget.setWindowIcon(icon)
    
    # Main GUI Ends Here =================================================================================

# Creates Help GUI
def build_gui_help_transfer_transforms():
    window_name = "build_gui_help_transfer_transforms"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title= script_name + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1,1])

    cmds.columnLayout("main_column", p= window_name)
   
    # Title Text
    cmds.separator(h=12, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p="main_column") # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column") # Title Column
    cmds.text(script_name + " Help", bgc=[.4,.4,.4],  fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p="main_column") # Empty Space
        
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p="main_column")
    cmds.text(l='This script quickly transfer', align="center")
    cmds.text(l='Translate, Rotate, and Scale', align="center")
    cmds.text(l='between objects.', align="center")
    
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Transfer (Source/Targets):', align="left", fn="boldLabelFont")
    cmds.text(l='1. Select Source 1st', align="left")
    cmds.text(l='2. Select Targets 2nd,3rd...', align="left")
    cmds.text(l='3. Select which transforms to transfer (or maybe invert)', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Transfer from one side to the other:', align="left", fn="boldLabelFont")
    cmds.text(l='"From Right to Left" and From Left To Right" functions.', align="left")
    cmds.text(l='1. Select all elements', align="left")
    cmds.text(l='2. Select which transforms to transfer (or maybe invert)', align="left")
    cmds.text(l='3. Select one of the "From > To" options:', align="left")
    cmds.text(l='e.g. "From Right to Left" : Copy transforms from objects', align="left")
    cmds.text(l='with the provided prefix "Right Side Tag" to objects ', align="left")
    cmds.text(l='with the provided prefix "Left Side Tag".', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Copy and Paste Transforms:', align="left", fn="boldLabelFont")
    cmds.text(l='This function doesn\'t take in consideration the', align="left")
    cmds.text(l='previous settings. It works on its own.', align="left")
    cmds.text(l='As the name suggests, it copy transforms, which', align="left")
    cmds.text(l='populates the text fields, or it pastes transforms', align="left")
    cmds.text(l='from selected fields back to selected objects.', align="left")
    cmds.text(l='', align="left")
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
    

# Build UI
if __name__ == '__main__':
    build_gui_transfer_transforms()