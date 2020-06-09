"""

 GT Transfer Transforms - Script for quickly transfering Translate, Rotate, and Scale between objects.
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-06-07
 
 1.1 - 2020-06-09
 Added Copy/Paste TRS options.
 
 To Do:
 Use a dictionary instead of list for attributes.
 Add checks before getting, setting.

"""
import maya.cmds as cmds

# Version:
script_version = "v1.1"


# Main Form ============================================================================
def build_gui_transfer_transforms():
    if cmds.window("build_gui_transfer_transforms", exists =True):
        cmds.deleteUI("build_gui_transfer_transforms")    

    # Main GUI Start Here =================================================================================

    build_gui_transfer_transforms = cmds.window("build_gui_transfer_transforms", title=script_version,\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable = True)#, widthHeight=[269, 392])
    
    column_main = cmds.columnLayout() 

    form = cmds.formLayout(p=column_main)

    content_main = cmds.columnLayout(adj = True)

    cmds.text("")
    cmds.text("GT - Transfer Transforms - " + script_version, bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.text("  ")
    cmds.text("      Script for quickly transfering       ")
    cmds.text("      Translate, Rotate, and Scale      ")
    cmds.text("      between objects.     ")
    cmds.text("   ")
    cmds.text("Steps (Source/Targets):")
    cmds.text('1. Select Source 1st   ')
    cmds.text('2. Select Targets 2nd,3rd...')
    cmds.text('3. Run Script')
    cmds.text("   ")
    cmds.text("Steps (One side to the other):")
    cmds.text('1. Select All Elements   ')
    cmds.text('2. Run Script')
    cmds.text("   ")
    cmds.separator(h=10, p=content_main)
    
    
    # Translate
    translate_x_container = cmds.rowColumnLayout( numberOfRows=1, h= 25, p=content_main)
    cmds.text("   ")
    translate_x_checkbox = cmds.checkBoxGrp(p=translate_x_container, columnWidth2=[90, 1], numberOfCheckBoxes=2, \
                                label1 = '  Translate X', label2 = "Invert Value", v1 = True, v2 = False) 
                                
    translate_y_container = cmds.rowColumnLayout( numberOfRows=1, h= 25, p=content_main)
    cmds.text("   ")
    translate_y_checkbox = cmds.checkBoxGrp(p=translate_y_container, columnWidth2=[90, 1], numberOfCheckBoxes=2, \
                                label1 = '  Translate Y', label2 = "Invert Value", v1 = True, v2 = False) 
                                
    translate_z_container = cmds.rowColumnLayout( numberOfRows=1, h= 25, p=content_main)
    cmds.text("   ")
    translate_z_checkbox = cmds.checkBoxGrp(p=translate_z_container, columnWidth2=[90, 1], numberOfCheckBoxes=2, \
                                label1 = '  Translate Z', label2 = "Invert Value", v1 = True, v2 = False) 
         
    cmds.separator(h=10, p=content_main)
    
    # Rotate                    
    rotate_x_container = cmds.rowColumnLayout( numberOfRows=1, h= 25, p=content_main)
    cmds.text("   ")
    rotate_x_checkbox = cmds.checkBoxGrp(p=rotate_x_container, columnWidth2=[90, 1], numberOfCheckBoxes=2, \
                                label1 = '  Rotate X', label2 = "Invert Value", v1 = True, v2 = False) 

    rotate_y_container = cmds.rowColumnLayout( numberOfRows=1, h= 25, p=content_main)
    cmds.text("   ")
    rotate_y_checkbox = cmds.checkBoxGrp(p=rotate_y_container, columnWidth2=[90, 1], numberOfCheckBoxes=2, \
                                label1 = '  Rotate Y', label2 = "Invert Value", v1 = True, v2 = False) 
                                
    rotate_z_container = cmds.rowColumnLayout( numberOfRows=1, h= 25, p=content_main)
    cmds.text("   ")
    rotate_z_checkbox = cmds.checkBoxGrp(p=rotate_z_container, columnWidth2=[90, 1], numberOfCheckBoxes=2, \
                                label1 = '  Rotate Z', label2 = "Invert Value", v1 = True, v2 = False) 
         
    cmds.separator(h=10, p=content_main) 
    
    # Scale                        
    scale_x_container = cmds.rowColumnLayout( numberOfRows=1, h= 25, p=content_main)
    cmds.text("   ")
    scale_x_checkbox = cmds.checkBoxGrp(p=scale_x_container, columnWidth2=[90, 1], numberOfCheckBoxes=2, \
                                label1 = '  Scale X', label2 = "Invert Value", v1 = True, v2 = False) 
    
    scale_y_container = cmds.rowColumnLayout( numberOfRows=1, h= 25, p=content_main)
    cmds.text("   ")
    scale_y_checkbox = cmds.checkBoxGrp(p=scale_y_container, columnWidth2=[90, 1], numberOfCheckBoxes=2, \
                                label1 = '  Scale Y', label2 = "Invert Value", v1 = True, v2 = False) 
    
    scale_z_container = cmds.rowColumnLayout( numberOfRows=1, h= 25, p=content_main)
    cmds.text("   ")
    scale_z_checkbox = cmds.checkBoxGrp(p=scale_z_container, columnWidth2=[90, 1], numberOfCheckBoxes=2, \
                                label1 = '  Scale Z', label2 = "Invert Value", v1 = True, v2 = False) 

    #cmds.rowColumnLayout(p=content_main,numberOfRows=1, h= 5) #Empty Space
    cmds.separator(h=10, p=content_main)
    
    # Left Side Tag textFields
    
    side_text_container = cmds.rowColumnLayout( p=content_main, numberOfRows=1, adj=True)
    cmds.text("Left Side Tag:   ", p=side_text_container)
    cmds.text("Right Side Tag:   ", p=side_text_container)
    
    side_textfield_container = cmds.rowColumnLayout( p=content_main, numberOfRows=1)
    
    left_tag_text_field = cmds.textField(p = side_textfield_container, width=96, text="left_", \
                                           enterCommand=lambda x:update_stored_values_and_run())
    right_tag_text_field = cmds.textField(p = side_textfield_container,width=96, text="right_", \
                                           enterCommand=lambda x:update_stored_values_and_run())
    cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 5) #Empty Space
    
    
    cmds.button(p=content_main, l ="From Right to Left", c=lambda x:transfer_transforms_side_to_side("right"))
    cmds.button(p=content_main, l ="From Left to Right", c=lambda x:transfer_transforms_side_to_side("left"))
    cmds.separator(h=10, p=content_main) 
    cmds.button(p=content_main, l ="Transfer (Source/Targets)", bgc=(.6, .8, .6), c=lambda x:transfer_transforms())
    
    # Copy and Paste Transforms
    cmds.separator(h=10, p=content_main)
    
    copy_text_container = cmds.rowColumnLayout( p=content_main, numberOfRows=1, adj=True)
    cmds.text("       Copy and Paste Transforms", p=copy_text_container)
    cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 5) #Empty Space
    translate_copy_textfield_container = cmds.rowColumnLayout( p=content_main, numberOfRows=1)
    
    cmds.text("   T    ", p=translate_copy_textfield_container)
    tx_copy_text_field = cmds.textField(p = translate_copy_textfield_container, width=55, text="0.0", ann="tx")
    ty_copy_text_field = cmds.textField(p = translate_copy_textfield_container, width=55, text="0.0", ann="ty")
    tz_copy_text_field = cmds.textField(p = translate_copy_textfield_container, width=55, text="0.0", ann="tz")
    cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 5) #Empty Space
     
    rotate_copy_textfield_container = cmds.rowColumnLayout( p=content_main, numberOfRows=1)
    
    cmds.text("   R    ", p=rotate_copy_textfield_container)
    rx_copy_text_field = cmds.textField(p = rotate_copy_textfield_container, width=55, text="0.0", ann="rx")
    ry_copy_text_field = cmds.textField(p = rotate_copy_textfield_container, width=55, text="0.0", ann="ry")
    rz_copy_text_field = cmds.textField(p = rotate_copy_textfield_container, width=55, text="0.0", ann="rz")
    cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 5) #Empty Space
    
    scale_copy_textfield_container = cmds.rowColumnLayout( p=content_main, numberOfRows=1)
    
    cmds.text("   S    ", p=scale_copy_textfield_container)
    sx_copy_text_field = cmds.textField(p = scale_copy_textfield_container, width=55, text="1.0", ann="sx")
    sy_copy_text_field = cmds.textField(p = scale_copy_textfield_container, width=55, text="1.0", ann="sy")
    sz_copy_text_field = cmds.textField(p = scale_copy_textfield_container, width=55, text="1.0", ann="sz")
    cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 5) #Empty Space
    
    container = cmds.rowColumnLayout( p=content_main, numberOfRows=1)
    cmds.button(p=container, l ="Get TRS", c=lambda x:transfer_transforms_copy_paste("get"), w=97)
    cmds.button(p=container, l ="Set TRS", c=lambda x:transfer_transforms_copy_paste("set"), w=97)
    
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
    
    cmds.showWindow(build_gui_transfer_transforms)
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
    

#Start current "Main"
build_gui_transfer_transforms()