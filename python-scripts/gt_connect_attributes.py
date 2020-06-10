"""
 GT Connect Attributes Script
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-02-04
 1.2 - 2020-02-18 
 Added force connection and some checks.
 
 1.3 - 2020-06-07 
 Updated naming convention to make it clearer. (PEP8)
 Fixed random window widthHeight issue.
 
"""

import maya.cmds as cmds

# Version:
script_version = "v1.3"
 

settings = { 'target_list': [], 
             'source_obj': [],
             'def_reverse_node': False,
             'def_disconnect' : False,
             'def_single_source_target' : False,
             'def_use_custom_node' : False,
             'def_force_connection' : False,
             'status_single_source_target' : False,
             'status_use_custom_node' : False,
             'status_use_reverse_node' : False,
             'status_disconnect' : False,
             'status_add_input' : False,
             'status_force_connection' : False,
             'input_node_type' : 'condition',
             'custom_node' : 'plusMinusAverage'
            }


# Main Form ============================================================================
def build_gui_connect_attributes():
    if cmds.window("build_gui_connect_attributes", exists =True):
        cmds.deleteUI("build_gui_connect_attributes")    

    # Main GUI Start Here =================================================================================

    build_gui_connect_attributes = cmds.window("build_gui_connect_attributes", title="connectAttr - " + script_version,\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =False, widthHeight=[266, 519])

    column_main = cmds.columnLayout() 

    form = cmds.formLayout(p=column_main)

    content_main = cmds.columnLayout(adj = True)
    
    # Description
    cmds.text("")
    cmds.text("GT Connect Attributes - " + script_version, bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.text("  ")
    cmds.text("      This script creates a node connection       ")
    cmds.text("      between source and target elements     ")
    cmds.text("   ")
    cmds.text('The Selection Source/Target  ')
    cmds.text('option expects the user to select  ')
    cmds.text('Source (1st) then Targets (2nd ,3rd...)  ')
    cmds.text("   ")
    cmds.separator(h=15, p=content_main)
    
    # Checkbox - Selection as Source and Target
    interactive_container_misc = cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 25)
    cmds.text("    ")
    single_source_target = cmds.checkBox(p=interactive_container_misc, label='  Use Selection as Source and Target (s)', value=settings.get("def_single_source_target"),\
                         cc=lambda x:is_using_single_target(cmds.checkBox(single_source_target, query=True, value=True)) )

    # CheckboxGrp Reverse and Disconnect
    interactive_container_jnt = cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 25)
    cmds.text("    ") # Increase this to move checkboxes to the right
    rev_disc_check_box_grp = cmds.checkBoxGrp(p=interactive_container_jnt, columnWidth2=[135, 1], numberOfCheckBoxes=2, \
                                label1 = '  Add Reverse Node', label2 = "Disconnect", v1 = settings.get("def_reverse_node"), v2 = settings.get("def_disconnect"), \
                                cc1=lambda x:update_stored_values(), cc2= lambda x:is_disconnecting(cmds.checkBoxGrp(rev_disc_check_box_grp,q=True,v2=True)))   

    # Checkbox - Override Existing
    override_existing_container = cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 25)
    cmds.text("    ")
    forcing_connection_checkbox = cmds.checkBox(p=override_existing_container, label='  Force Connection  (Overrides Existing)', value=settings.get("def_force_connection"),\
                         cc=lambda x:update_stored_values())

    cmds.separator(h=15, p=content_main)

    # Checkbox Use Custom Node Between Connection
    interactive_container_misc = cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 25)
    cmds.text("    ")
    add_custom_node = cmds.checkBox(p=interactive_container_misc, label='  Add Custom Node Between Connection', value=settings.get("def_use_custom_node"),\
                          cc=lambda x:is_using_custom_node(cmds.checkBox(add_custom_node, query=True, value=True)) ) # UPDATE THIS
    
    # Dropdown Menu (Custom Node)
    custom_node_menu_container = cmds.rowColumnLayout(p=content_main,numberOfRows=1, adj = True)
    custom_node_menu = cmds.optionMenu(en=False, p=custom_node_menu_container, label='   Custom Node', cc=lambda x:update_stored_values()) #######
    cmds.menuItem( label='plusMinusAverage' )
    cmds.menuItem( label='multiplyDivide' )
    cmds.menuItem( label='condition' )

    custom_node_empty_space = cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 7)
    
    # Checkbox and Dropdown Menu for Input node and its type
    node_behaviour_container_one = cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 25)
    cmds.text("    ")
    add_ctrl_node = cmds.checkBox(p=node_behaviour_container_one, en=False, label='  Add Input Node  ', value=settings.get("def_use_custom_node"),\
                          cc=lambda x:update_stored_values())
    
    ctrl_node_output = cmds.optionMenu(en=False, p=node_behaviour_container_one, label='', w=120,cc=lambda x:update_stored_values()) #######
    cmds.menuItem( label='condition' )
    cmds.menuItem( label='plusMinusAverage' )
    cmds.menuItem( label='multiplyDivide' )     
    cmds.text("   ",p=custom_node_menu_container)
                                                   
    cmds.separator(h=10, p=content_main)
    
    # Source List Loader (Buttons)
    source_container = cmds.rowColumnLayout( p=content_main, numberOfRows=1)
    source_btn = cmds.button(p=source_container, l ="Load Source Object", c=lambda x:update_load_btn_jnt("source"), w=130)
    source_status = cmds.button(p=source_container, l ="Not loaded yet", bgc=(0, 0, 0), w=130, \
                            c="cmds.headsUpMessage( 'Select your source element and click on \"Load Source Object\"', verticalOffset=150 , time=5.0)")
                            
    # Target List Loader (Buttons)
    target_container = cmds.rowColumnLayout( p=content_main, numberOfRows=1)
    target_btn = cmds.button(p=target_container, l ="Load Target Objects", c=lambda x:update_load_btn_jnt("target"), w=130)
    target_status = cmds.button(p=target_container, l ="Not loaded yet", bgc=(0, 0, 0), w=130, \
                            c="cmds.headsUpMessage( 'Select your target elements and click on \"Load Target Objects\"', verticalOffset=150 , time=5.0)")
    cmds.separator(h=10, p=content_main)
    
    # Source/Target Attributes
    bottom_container = cmds.rowColumnLayout(p=content_main,adj=True)
    cmds.text('Source Attribute (Only One):',p=bottom_container)
    source_attributes_input = cmds.textField(p = bottom_container, text="translate", \
                                    enterCommand=lambda x:connect_attributes(cmds.textField(source_attributes_input, q=True, text=True),\
                                                                            cmds.textField(target_attributes_input, q=True, text=True)))
    cmds.text('Target Attributes:',p=bottom_container)
    target_attributes_input = cmds.textField(p = bottom_container, text="translate, rotate, scale", \
                                    enterCommand=lambda x:connect_attributes(cmds.textField(source_attributes_input, q=True, text=True),\
                                                                            cmds.textField(target_attributes_input, q=True, text=True)))
    
    # Print Attributes Buttons
    cmds.rowColumnLayout(p=content_main,adj=True,h=5)
    show_attributes_container = cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 25)
    cmds.button(p=show_attributes_container, l ="List All Attributes", w=130,\
                                    c=lambda x:print_selection_attributes("all"))                                                                    
    cmds.button(p=show_attributes_container, l ="List Keyable Attributes", w=130,\
                                    c=lambda x:print_selection_attributes("keyable")) 
    
    cmds.separator(h=10, p=content_main)
    
    # Connect Button (Main Function)
    cmds.button(p=content_main, l ="Connect Attributes", bgc=(.6, .8, .6), \
                                    c=lambda x:connect_attributes(cmds.textField(source_attributes_input, q=True, text=True),\
                                                                            cmds.textField(target_attributes_input, q=True, text=True)))

    # Prints selection attributes
    def print_selection_attributes(type):
        selection = cmds.ls(selection=True)
        if type == "keyable" and len(selection) > 0:
            attrList = cmds.listAttr (selection[0], k=True) or []
        elif len(selection) > 0:
            attrList = cmds.listAttr (selection[0]) or []
        
        
        if len(selection) > 0 and attrList != []:
            print("#" * 80)
            print(" " * 30 + selection[0] + " attributes:")
            for attr in attrList:
                print(attr)
            print("#" * 80)
            cmds.headsUpMessage( 'Open Script Editor to see the list of attributes', verticalOffset=150 , time=5.0)
        else:
            cmds.warning("Nothing selected (or no attributes to be displayed)")
                
    # Updates elements to reflect the use of selection (instead of loaders)
    def is_using_single_target(state): 
        if state:
            settings["status_single_source_target"] = cmds.checkBox(single_source_target, q=True, value=True)
            cmds.button(source_btn, e=True, en=False)
            cmds.button(source_status, l ="Not necessary", e=True, en=False, bgc=(.25, .25, .25))
            cmds.button(target_btn, e=True, en=False)
            cmds.button(target_status, l ="Not necessary", e=True, en=False, bgc=(.25, .25, .25))
            settings["target_list"] = []
            settings["source_obj"] = []
        else:
            settings["status_single_source_target"] = cmds.checkBox(single_source_target, q=True, value=True)
            cmds.button(source_btn, e=True, en=True)
            cmds.button(source_status, l ="Not loaded yet", e=True, en=True, bgc=(0, 0, 0),\
                        c="cmds.headsUpMessage( 'Select your source element and click on \"Load Source Object\"', verticalOffset=150 , time=5.0)")
            cmds.button(target_btn, e=True, en=True)
            cmds.button(target_status, l ="Not loaded yet", e=True, en=True, bgc=(0, 0, 0), \
                        c="cmds.headsUpMessage( 'Select your target elements and click on \"Load Target Objects\"', verticalOffset=150 , time=5.0)")
            
    # Updates elements to reflect the use of in between custom node
    def is_using_custom_node(state): 
        if state:
            cmds.optionMenu(custom_node_menu, e=True, en=True)
            settings["status_use_custom_node"] = cmds.checkBox(add_custom_node, q=True, value=True)
            cmds.checkBox(add_ctrl_node,e=True, en=True)
            cmds.optionMenu(ctrl_node_output,e=True, en=True)
        else:
            cmds.optionMenu(custom_node_menu, e=True, en=False)
            settings["status_use_custom_node"] = cmds.checkBox(add_custom_node, q=True, value=True)
            cmds.checkBox(add_ctrl_node,e=True, en=False)
            cmds.optionMenu(ctrl_node_output,e=True, en=False)

    # Updates many of the stored GUI values (Used by multiple elements)
    def update_stored_values(): 
        settings["custom_node"] = cmds.optionMenu(custom_node_menu, q=True, value=True)
        settings["status_use_reverse_node"] = cmds.checkBoxGrp(rev_disc_check_box_grp, q=True, value1=True)
        settings["status_disconnect"] = cmds.checkBoxGrp(rev_disc_check_box_grp, q=True, value2=True)
        settings["input_node_type"] = cmds.optionMenu(ctrl_node_output, q=True, value=True)
        settings["status_add_input"] = cmds.checkBox(add_ctrl_node, q=True, value=True)
        settings["status_force_connection"] = cmds.checkBox(forcing_connection_checkbox, q=True, value=True)
        #print(settings.get("status_force_connections")) # Debugging
        
    # Updates elements to reflect the use disconnect function
    def is_disconnecting(state): 
        
        if state:
            cmds.checkBox(add_custom_node, e=True, en=False)
            is_using_custom_node(False)
            cmds.checkBoxGrp(rev_disc_check_box_grp, e=True, en1=False)
            update_stored_values()
            
        else:
            cmds.checkBox(add_custom_node, e=True, en=True)
            is_using_custom_node(cmds.checkBox(add_custom_node, q=True, value=True))
            cmds.checkBoxGrp(rev_disc_check_box_grp, e=True, en1=True)
            update_stored_values()
    
    # Objects Loader
    def update_load_btn_jnt(button_name):
        
        # Check If Selection is Valid
        received_valid_source_selection = False
        received_valid_target_selection = False
        selected_elements = cmds.ls(selection=True)
        
        if button_name == "source":
            if len(selected_elements) == 0:
                cmds.warning("Please make sure you select at least one object before loading")
            elif len(selected_elements) == 1:
                received_valid_source_selection = True
            elif len(selected_elements) > 1:
                 cmds.warning("You can only have one source object")
            else:
                cmds.warning("Something went wrong, make sure you selected all necessary elements")
                
        if button_name == "target":
            if len(selected_elements) == 0:
                cmds.warning("Please make sure you select at least one object before loading")
            elif len(selected_elements) > 0:
                 received_valid_target_selection = True
            else:
                cmds.warning("Something went wrong, make sure you selected all necessary elements")
            
        # If Source
        if button_name is "source" and received_valid_source_selection == True:
            settings["source_obj"] = selected_elements[0]
            cmds.button(source_status, l=selected_elements[0],e=True, bgc=(.6, .8, .6), w=130, c=lambda x:if_exists_select(settings.get("source_obj")))
        elif button_name is "source":
            cmds.button(source_status, l ="Failed to Load",e=True, bgc=(1, .4, .4), w=130,\
                        c="cmds.headsUpMessage( 'Make sure you select only one source element', verticalOffset=150 , time=5.0)")
        
        # If Target
        if button_name is "target" and received_valid_target_selection == True:
            settings["target_list"] = selected_elements
            
            loaded_text = str(len(selected_elements)) + " objects loaded"
            if len(selected_elements) == 1:
                loaded_text = selected_elements[0]
        
            cmds.button(target_status, l =loaded_text,e=True, bgc=(.6, .8, .6), w=130, c=lambda x:target_listManager(settings.get("target_list")))
        elif button_name is "target":
            cmds.button(target_status, l ="Failed to Load",e=True, bgc=(1, .4, .4), w=130,\
                        c="cmds.headsUpMessage( 'Make sure you select at least one target element', verticalOffset=150 , time=5.0)")


    cmds.showWindow(build_gui_connect_attributes)
    # Main GUI Ends Here =================================================================================


# Main Function 
def connect_attributes(source_text_attribute,taget_text_attributes):

    # Final Check before running
    is_ready_to_connect = True

    if settings.get("status_single_source_target") == False:
        if settings.get("target_list") == [] or settings.get("source_obj") == []:
            cmds.warning("One of your lists is empty")
            is_ready_to_connect = False
        else:
            target_list = settings.get("target_list")
            source_obj = settings.get("source_obj")
    else:
        selection = cmds.ls(selection=True) or []
        if len(selection) < 2:
            cmds.warning("You need at least two elements selected to create connections")
            is_ready_to_connect = False
        else:
            target_list = selection
            source_obj = selection[0]
            target_list.remove(source_obj)
    
    do_disconnect = settings.get('status_disconnect')
    custom_node = settings.get('custom_node')
    input_node_type = settings.get('input_node_type')
    using_reverse_node = settings.get('status_use_reverse_node')
    target_attributes_list = parse_text_field(taget_text_attributes)
    error_list = []
    
    # Start Connecting
    if is_ready_to_connect and do_disconnect == False:
        
        # Creates Necessary Nodes
        if settings.get('status_add_input'):
                inputNode = cmds.createNode(input_node_type)
 
        is_source_attr_checked = False
        
        for target_obj in target_list: 
         for attr in target_attributes_list:
            error_occured = False
            target_attr_list = []
            
            # Checks if source object exists
            if cmds.objExists(source_obj):
                source_attr_list = cmds.listAttr(source_obj) or []
            else:
                error_occured = True
                error_list.append("The source object " + source_obj + " doesn't seem exist")
                
            # Checks if target object exists
            if error_occured == False and cmds.objExists(target_obj):
                target_attr_list = cmds.listAttr(target_obj) or []
            else:
                error_occured = True
                error_list.append("The target object " + target_obj + " doesn't seem exist")
            
            # Checks if source attribute exists on source
            if error_occured == False and str(source_text_attribute) in source_attr_list:
                pass
            else:
                error_occured = True
                if is_source_attr_checked == False:
                    error_list.append(source_obj + " (Source Object) doesn't seem to have an attribute called " + source_text_attribute)
                is_source_attr_checked = True
            
            # Checks if target attribute exists on target
            if len(target_attr_list) > 0 and attr in target_attr_list:
                pass
            else:
                error_occured = True
                error_list.append(target_obj + " doesn't seem to have an attribute called " + attr)
            
            # Checks if incoming connection already exists
            if error_occured == False and cmds.connectionInfo( target_obj + "." + attr, isDestination=True) == False:
                pass
            else:
                if settings.get("status_force_connection") == False:
                    error_occured = True
                    error_list.append(target_obj + " already has an incoming connection on the attribute: " + attr)
                else:
                    disconnect_attribute(target_obj, attr)

            
            # Allow it to continue if no errors happened
            if error_occured == False:
                if settings.get('status_use_custom_node'): # Is using custom node?
                    
                    if using_reverse_node:
                        reverse_node = cmds.createNode("reverse")
                
                    #Source to inBetween node
                    node_in_between = cmds.createNode(custom_node)
                    if custom_node == "plusMinusAverage":
                        if "3" in cmds.getAttr(source_obj + "." + source_text_attribute,type=True):
                            cmds.connectAttr(source_obj + "." + source_text_attribute, node_in_between + "." + "input3D[0]") 
                        else:
                            cmds.connectAttr(source_obj + "." + source_text_attribute, node_in_between + "." + "input3D[0].input3Dx") 
                    
                    elif custom_node == "multiplyDivide":
                        if "3" in cmds.getAttr(source_obj + "." + source_text_attribute,type=True):
                            cmds.connectAttr(source_obj + "." + source_text_attribute, node_in_between + "." + "input1") 
                        else:
                            cmds.connectAttr(source_obj + "." + source_text_attribute, node_in_between + "." + "input1X") 
                            
                    elif custom_node == "condition":
                        if "3" in cmds.getAttr(source_obj + "." + source_text_attribute,type=True):
                            cmds.connectAttr(source_obj + "." + source_text_attribute, node_in_between + "." + "colorIfTrue") 
                        else:
                            cmds.connectAttr(source_obj + "." + source_text_attribute, node_in_between + "." + "colorIfTrueR")
                         
                    # inBetween node to Target node
                    if using_reverse_node:
                        # Connect Custom node to Reverse Node
                        if custom_node == "plusMinusAverage":
                            if "3" in cmds.getAttr(target_obj + "." + attr,type=True):
                                cmds.connectAttr(node_in_between + "." + "output3D", reverse_node + "." + 'input') 
                            else:
                                cmds.connectAttr(node_in_between + "." + "output3Dx", reverse_node + "." + 'inputX')  
                        elif custom_node == "multiplyDivide":
                            if "3" in cmds.getAttr(target_obj + "." + attr,type=True):
                                cmds.connectAttr(node_in_between + "." + "output", reverse_node + "." + 'input') 
                            else:
                                cmds.connectAttr(node_in_between + "." + "outputX", reverse_node + "." + 'inputX') 
                                
                        elif custom_node == "condition":
                            if "3" in cmds.getAttr(target_obj + "." + attr,type=True):
                                cmds.connectAttr(node_in_between + "." + "outColor", reverse_node + "." + 'input') 
                            else:
                                cmds.connectAttr(node_in_between + "." + "outColorR", reverse_node + "." + 'inputX')
                        # Reverse Output to Target Node
                        if "3" in cmds.getAttr(target_obj + "." + attr,type=True):
                            cmds.connectAttr(reverse_node + "." + "output", target_obj + "." + attr) 
                        else:
                            cmds.connectAttr(reverse_node + "." + "outputX", target_obj + "." + attr)  
                    else:
                        # Custom Node to Target Node
                        if custom_node == "plusMinusAverage":
                            if "3" in cmds.getAttr(target_obj + "." + attr,type=True):
                                cmds.connectAttr(node_in_between + "." + "output3D", target_obj + "." + attr) 
                            else:
                                cmds.connectAttr(node_in_between + "." + "output3Dx", target_obj + "." + attr)  
                        
                        elif custom_node == "multiplyDivide":
                            if "3" in cmds.getAttr(target_obj + "." + attr,type=True):
                                cmds.connectAttr(node_in_between + "." + "output", target_obj + "." + attr) 
                            else:
                                cmds.connectAttr(node_in_between + "." + "outputX", target_obj + "." + attr) 
                                
                        elif custom_node == "condition":
                            if "3" in cmds.getAttr(target_obj + "." + attr,type=True):
                                cmds.connectAttr(node_in_between + "." + "outColor", target_obj + "." + attr) 
                            else:
                                cmds.connectAttr(node_in_between + "." + "outColorR", target_obj + "." + attr) 
                    
                    
                    # Input node to custom nodes
                    if settings.get('status_add_input'):
                        if input_node_type == "plusMinusAverage":
                            out_of_input = "output3D"
                        elif input_node_type == "multiplyDivide":
                            out_of_input = "output"
                        elif input_node_type == "condition":
                            out_of_input = "outColor"
                            
                        if custom_node == "plusMinusAverage":
                            cmds.connectAttr(inputNode + "." + out_of_input, node_in_between + "." + "input3D[1]") 
                        elif custom_node == "multiplyDivide":
                            cmds.connectAttr(inputNode + "." + out_of_input, node_in_between + "." + "input2") 
                        elif custom_node == "condition":
                            cmds.connectAttr(inputNode + "." + out_of_input, node_in_between + "." + "colorIfFalse") 
                    
                else: # Not using custom node (Do simple connection)
                    if using_reverse_node:
                        reverse_node = cmds.createNode("reverse")
                        #Reverse Input
                        if "3" in cmds.getAttr(source_obj + "." + source_text_attribute,type=True):
                            cmds.connectAttr(source_obj + "." + source_text_attribute, reverse_node + "." + "input") 
                        else:
                            cmds.connectAttr(source_obj + "." + source_text_attribute, reverse_node + "." + "inputX")
                        #Reverse Output
                        if "3" in cmds.getAttr(target_obj + "." + attr,type=True):
                            cmds.connectAttr(reverse_node + "." + "output", target_obj + "." + attr) 
                        else:
                            cmds.connectAttr(reverse_node + "." + "outputX", target_obj + "." + attr)  
                    else:
                        cmds.connectAttr(source_obj + "." + source_text_attribute, target_obj + "." + attr) #Simple Connection
            
    # Disconnect Instead          
    elif is_ready_to_connect and do_disconnect == True:
        for target_obj in target_list: 
            for attr in target_attributes_list:
                
                disconnect_error_occured = False
                
                # Checks if target object exists
                if cmds.objExists(target_obj):
                    target_attr_list = cmds.listAttr(target_obj) or []
                else:
                    disconnect_error_occured = True
                    error_list.append("The target object " + target_obj + " doesn't seem exist")
                    
                # Checks if target attribute exists on target
                if len(target_attr_list) > 0 and attr in target_attr_list:
                    pass
                else:
                    disconnect_error_occured = True
                    error_list.append(target_obj + " doesn't seem to have an attribute called " + attr)
                
                if disconnect_error_occured == False:
                        disconnect_attribute(target_obj, attr)
    
    #Print errors if necessary
    if len(error_list) > 0:
        print("#" * 80)
        print(" " * 35 + "Errors:")
        for error in error_list:
            print(error)
        print("#" * 80)
        cmds.warning( 'An error happened when creating your connections, open the script editor for more details')

        

    # ============================= End of Main Function =============================

# If object exists, select it
def if_exists_select(obj):
    if cmds.objExists(obj):
        cmds.select(obj)
        cmds.headsUpMessage(obj + " selected", verticalOffset=150 )
    else:
        cmds.warning("Object doesn't exist! Did you delete or rename it after loading?")

# target_listManager
def target_listManager(list):
    missing_elements = False
    print("#" * 32 + " Target Objects " + "#" * 32)
    for obj in list:
        if cmds.objExists(obj):
            print(obj)
        else:
            print(obj + " no longer exists!")
            missing_elements = True
    print("#" * 80)
    if missing_elements:
        cmds.headsUpMessage( 'It looks like you are missing some target elements! Open script editor for more information', verticalOffset=150 , time=5.0)
    else:
        cmds.headsUpMessage( 'Target elements selected (Open script editor to see a list of your loaded elements)', verticalOffset=150 , time=5.0)
    if settings.get("target_list") != [] and missing_elements == False:
        cmds.select(settings.get("target_list"))


# Disconnect attributes
def disconnect_attribute(node, attrName, source=True, destination=False):
    connection_pairs = []
    if source:
        connectionsList = cmds.listConnections(node, plugs=True, connections=True, destination=False)
        if connectionsList:
            connection_pairs.extend(zip(connectionsList[1::2], connectionsList[::2]))
    
    if destination:
        connectionsList = cmds.listConnections(node, plugs=True, connections=True, source=False)
        if connectionsList:
            connection_pairs.extend(zip(connectionsList[::2], connectionsList[1::2]))
    
    for src_attr, dest_attr in connection_pairs:
        if attrName in dest_attr:
            cmds.disconnectAttr(src_attr, dest_attr)
            

# Parses textField data 
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

# Start current "Main"
build_gui_connect_attributes()
