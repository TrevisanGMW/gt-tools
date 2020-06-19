"""
 GT Connect Attributes Script
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-02-04
 1.2 - 2020-02-18 
 Added force connection and some checks.
 
 1.3 - 2020-06-07 
 Updated naming convention to make it clearer. (PEP8)
 Fixed random window widthHeight issue.
 
 1.4 - 2020-06-17
 Added window icon
 Added help menu
 Changed GUI
 Attribute Listing now exported to txt file instead of script editor
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
script_name = "GT Connect Attributes"

# Version:
script_version = "1.4"
 

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
    window_name = "build_gui_connect_attributes"
    if cmds.window(window_name, exists =True):
        cmds.deleteUI(window_name)    

    # Main GUI Start Here =================================================================================

    build_gui_connect_attributes = cmds.window(window_name, title=script_name + "  v" + script_version,\
                          titleBar=True, mnb=False, mxb=False, sizeable =True)

    cmds.window(window_name, e=True, s=True, wh=[1,1])

    column_main = cmds.columnLayout() 

    form = cmds.formLayout(p=column_main)

    content_main = cmds.columnLayout()
    
    # Title Text
    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 10)], p=content_main) # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 200), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)], p=content_main) # Title Column
    cmds.text(" ", bgc=[0,.5,0]) # Tiny Empty Green Space
    cmds.text(script_name + " v" + script_version, bgc=[0,.5,0],  fn="boldLabelFont", align="left")
    cmds.button( l ="Help", bgc=(0, .5, 0), c=lambda x:build_gui_help_connect_attributes())
    cmds.separator(h=10, style='none', p=content_main) # Empty Space
    
    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,10)], p=content_main)
    #cmds.separator(h=5)
    
    # Checkbox - Selection as Source and Target
    interactive_container_misc = cmds.rowColumnLayout(p=body_column, nc=1, cs=[(1,12)], h= 25)
    single_source_target = cmds.checkBox(p=interactive_container_misc, label='  Use Selection for Source and Target (s)', value=settings.get("def_single_source_target"),\
                         cc=lambda x:is_using_single_target(cmds.checkBox(single_source_target, query=True, value=True)) )

    # CheckboxGrp Reverse and Disconnect
    interactive_container_jnt = cmds.rowColumnLayout(p=body_column, nc=1, cs=[(1,11)], h= 25)
    rev_disc_check_box_grp = cmds.checkBoxGrp(p=interactive_container_jnt, columnWidth2=[137, 0], numberOfCheckBoxes=2, \
                                label1 = '  Add Reverse Node', label2 = " Disconnect", v1 = settings.get("def_reverse_node"), v2 = settings.get("def_disconnect"), \
                                cc1=lambda x:update_stored_values(), cc2= lambda x:is_disconnecting(cmds.checkBoxGrp(rev_disc_check_box_grp,q=True,v2=True)))   

    # Checkbox - Override Existing (Force Connection)
    override_existing_container = cmds.rowColumnLayout(p=body_column, nc=1, cs=[(1,12)], h= 25)
    forcing_connection_checkbox = cmds.checkBox(p=override_existing_container, label='  Force Connection  (Overrides Existing)', value=settings.get("def_force_connection"),\
                         cc=lambda x:update_stored_values())

    cmds.separator(h=15, p=body_column)

    # Checkbox Use Custom Node Between Connection
    interactive_container_misc = cmds.rowColumnLayout(p=body_column, nc=1, cs=[(1,12)], h= 25)
    add_custom_node = cmds.checkBox(p=interactive_container_misc, label='  Add Custom Node Between Connection', value=settings.get("def_use_custom_node"),\
                          cc=lambda x:is_using_custom_node(cmds.checkBox(add_custom_node, query=True, value=True)) ) # UPDATE THIS
    
    # Dropdown Menu (Custom Node)
    custom_node_menu_container = cmds.rowColumnLayout(p=body_column, nc=1, cw=[(1,247)], cs=[(1,3)], h= 25)
    custom_node_menu = cmds.optionMenu(en=False, p=custom_node_menu_container, label='   Custom Node : ', cc=lambda x:update_stored_values()) #######
    cmds.menuItem( label='plusMinusAverage' )
    cmds.menuItem( label='multiplyDivide' )
    cmds.menuItem( label='condition' )

    #custom_node_empty_space = cmds.rowColumnLayout(p=body_column, numberOfRows=1, h= 7) #??????????
    cmds.separator(h=5, style='none', p=body_column) # Empty Space
    
    # Checkbox and Dropdown Menu for Input node and its type
    node_behaviour_container_one = cmds.rowColumnLayout(p=body_column, numberOfRows=1, h= 25)
    cmds.text("    ")
    add_ctrl_node = cmds.checkBox(p=node_behaviour_container_one, en=False, label='  Add Input Node  ', value=settings.get("def_use_custom_node"),\
                          cc=lambda x:update_stored_values())
    
    ctrl_node_output = cmds.optionMenu(en=False, p=node_behaviour_container_one, label='', w=120,cc=lambda x:update_stored_values()) #######
    cmds.menuItem( label='condition' )
    cmds.menuItem( label='plusMinusAverage' )
    cmds.menuItem( label='multiplyDivide' )     
    cmds.text("   ",p=custom_node_menu_container)
                                                   
    cmds.separator(h=10, p=body_column)
    cmds.separator(h=3, style='none', p=body_column) # Empty Space
    
    # Source List Loader (Buttons)
    source_container = cmds.rowColumnLayout( p=body_column, numberOfRows=1)
    source_btn = cmds.button(p=source_container, l ="Load Source Object", c=lambda x:update_load_btn_jnt("source"), w=130)
    source_status = cmds.button(p=source_container, l ="Not loaded yet", bgc=(0, 0, 0), w=130, \
                            c="cmds.headsUpMessage( 'Select your source element and click on \"Load Source Object\"', verticalOffset=150 , time=5.0)")
                            
    # Target List Loader (Buttons)
    target_container = cmds.rowColumnLayout( p=body_column, numberOfRows=1)
    target_btn = cmds.button(p=target_container, l ="Load Target Objects", c=lambda x:update_load_btn_jnt("target"), w=130)
    target_status = cmds.button(p=target_container, l ="Not loaded yet", bgc=(0, 0, 0), w=130, \
                            c="cmds.headsUpMessage( 'Select your target elements and click on \"Load Target Objects\"', verticalOffset=150 , time=5.0)")
    cmds.separator(h=3, style='none', p=body_column) # Empty Space
    cmds.separator(h=10, p=body_column)
    
    # Source/Target Attributes
    bottom_container = cmds.rowColumnLayout(p=body_column, adj=True)
    cmds.text('Source Attribute (Only One):',p=bottom_container)
    source_attributes_input = cmds.textField(p = bottom_container, text="translate", \
                                    enterCommand=lambda x:connect_attributes(cmds.textField(source_attributes_input, q=True, text=True),\
                                                                            cmds.textField(target_attributes_input, q=True, text=True)))
    cmds.text('Target Attributes:',p=bottom_container)
    target_attributes_input = cmds.textField(p = bottom_container, text="translate, rotate, scale", \
                                    enterCommand=lambda x:connect_attributes(cmds.textField(source_attributes_input, q=True, text=True),\
                                                                            cmds.textField(target_attributes_input, q=True, text=True)))
    
    cmds.separator(h=3, style='none', p=body_column) # Empty Space
    cmds.separator(h=10, p=body_column)
    
    # Print Attributes Buttons
    cmds.rowColumnLayout(p=body_column, adj=True, h=5)
    show_attributes_container = cmds.rowColumnLayout(p=body_column, numberOfRows=1, h= 25)
    cmds.button(p=show_attributes_container, l ="List All Attributes", w=130,\
                                    c=lambda x:print_selection_attributes("all"))                                                                    
    cmds.button(p=show_attributes_container, l ="List Keyable Attributes", w=130,\
                                    c=lambda x:print_selection_attributes("keyable")) 
    
    cmds.separator(h=10, style='none', p=body_column) # Empty Space
    
    # Connect Button (Main Function)
    cmds.button(p=body_column, l ="Connect Attributes", bgc=(.6, .8, .6), \
                                    c=lambda x:connect_attributes(cmds.textField(source_attributes_input, q=True, text=True),\
                                                                            cmds.textField(target_attributes_input, q=True, text=True)))
    cmds.separator(h=10, style='none', p=body_column) # Empty Space

    # Prints selection attributes
    def print_selection_attributes(type):
        selection = cmds.ls(selection=True)
        header = ""
        if type == "keyable" and len(selection) > 0:
            attrList = cmds.listAttr (selection[0], k=True) or []
            header = '"' + selection[0] + '" keyable attributes: '
        elif len(selection) > 0:
            attrList = cmds.listAttr (selection[0]) or []
            header = '"' + selection[0] + '" attributes: '
        
        
        if len(selection) > 0 and attrList != []:
            export_to_txt(header, attrList)
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

    
    # Show and Lock Window
    cmds.showWindow(build_gui_connect_attributes)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/hsRearrange.png')
    widget.setWindowIcon(icon)
    
    
    # Main GUI Ends Here =================================================================================


# Creates Help GUI
def build_gui_help_connect_attributes():
    window_name = "build_gui_help_connect_attributes"
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
    cmds.text(l='This script automates the creation of connections', align="left")
    cmds.text(l='between attributes from source (output) and target', align="left")
    cmds.text(l='(input).', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Use Selection for Source and Target (s):', align="left", fn="boldLabelFont")
    cmds.text(l='When this option is activated, you no longer need to', align="left")
    cmds.text(l='load sources/target (s).', align="left")
    cmds.text(l='You can simply select: 1st: source, 2nd, 3rd... : target(s)', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Add Reverse Node:', align="left", fn="boldLabelFont")
    cmds.text(l='Adds a reverse node between connections.', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Disconnect:', align="left", fn="boldLabelFont")
    cmds.text(l='Break connections between selected nodes.', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Force Connection (Overrides Existing)', align="left", fn="boldLabelFont")
    cmds.text(l='Connects nodes even if they already have a connection.', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Add Custom Node Between Connection: ', align="left", fn="boldLabelFont")
    cmds.text(l='Allows user to create a node between connections.', align="left")
    cmds.text(l='Excellent for controlling dataflow.', align="left")
    cmds.text(l='-Custom Node: Which node to create', align="left")
    cmds.text(l='-Add Input Node: Creates one master control to update', align="left")
    cmds.text(l='all in betweens.', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Load Source/Target Objects:', align="left", fn="boldLabelFont")
    cmds.text(l='Use these buttons to load the objects you want to use', align="left")
    cmds.text(l='as source and target (s).', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Source Attribute and Target Attributes:', align="left", fn="boldLabelFont")
    cmds.text(l='Name of the attribute you want to connect.', align="left")
    cmds.text(l='Requirement: Use long or short name (no nice names)', align="left")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='List All Attributes & List Keyable Attributes:', align="left", fn="boldLabelFont")
    cmds.text(l='Returns a list of attributes that can be used to populate', align="left")
    cmds.text(l='the Source and Target Attributes fields.', align="left")
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

# Opens Notepad with header and list of objects
def export_to_txt(header_string, list):
    tempDir = cmds.internalVar(userTmpDir=True)
    txtFile = tempDir+'tmp_state.txt';
    
    file_handle = open(txtFile,'w')
    
    text_to_export = header_string + "\n\n"
    for obj in list:
        text_to_export = text_to_export + str(obj) + "\n"

    file_handle.write(text_to_export)
    file_handle.close()

    notepadCommand = 'exec("notepad ' + txtFile + '");'
    mel.eval(notepadCommand)
  

# Start current "Main"
build_gui_connect_attributes()
