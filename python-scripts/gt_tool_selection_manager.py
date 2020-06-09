"""
 GT Selection Manager Script
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-02-19
 
 1.0 - 2020-03-05 
 Included Help Button

 1.1 - 2020-06-07
 Updated naming convention to make it clearer. (PEP8)
 Fixed random window widthHeight issue.
 
 To Do:
 Add Selection base on Shader name, Texture, TRS
 Add Apply function to outliner color
 Add choice between transform and shape for outliner color
 
"""
import maya.cmds as cmds
import maya.mel as mel

# Version:
script_version = "v1.1"
 

settings = { 'use_contains_string' : False,             # Active Functions
             'use_contains_no_string' : False,
             'use_contains_type' : False,
             'use_contains_no_type' : False,
             'use_visibility_state' : False,
             'use_outliner_color' : False,
             'use_no_outliner_color' : False,
             'stored_outliner_color' : [1,1,1],              # StoredValues
             'stored_no_outliner_color' : [1,1,1],
             'stored_selection_one' : [],
             'stored_selection_two' : [],
             'stored_contains_string' : '',
             'stored_contains_no_string' : '',
             'stored_contains_type' : '',
             'stored_contains_no_type' : '',
             'stored_shape_node_type' : 'Select Shapes as Objects',
             'stored_visibility_state' : False,
             'stored_save_as_quick_selection' : True,
             'stored_new_selection' : False
            }


# Main Form ============================================================================
def build_gui_selection_manager():
    if cmds.window("build_gui_selection_manager", exists =True):
        cmds.deleteUI("build_gui_selection_manager")    

    # Main GUI Start Here =================================================================================

    build_gui_selection_manager = cmds.window("build_gui_selection_manager", title="gt_selection_manager - " + script_version,\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =False, widthHeight = [267, 531])

    column_main = cmds.columnLayout() 

    form = cmds.formLayout(p=column_main)

    content_main = cmds.columnLayout(adj = True)
    
    # Description
    cmds.text("")
    row_one = cmds.rowColumnLayout(p=content_main, numberOfRows=1) #Empty Space
    cmds.text( "         GT Selection Manager - " + script_version + "          ",p=row_one, bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.button( l ="Help", bgc=(0, .5, 0), c=lambda x:build_gui_help_selection_manager())
    cmds.text("        ", bgc=[0,.5,0])
    cmds.rowColumnLayout(p=content_main, adj = True)
    cmds.text("  ")
    cmds.text("      This script allows you to update selections       ")
    cmds.text("      to contain (or not) only filtered elements     ")
    cmds.text("   ")
    cmds.separator(h=15, p=content_main)
    
    
    # Element Name
    cmds.text("Element Name", p=content_main)
    cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 5) #Empty Space
    name_container = cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 25)
    cmds.text("    ") # Increase this to move checkboxes to the right
    contains_string_or_not_checkbox = cmds.checkBoxGrp(p=name_container, columnWidth2=[120, 1], numberOfCheckBoxes=2, \
                                label1 = ' Does Contain ', label2 = "  Doesn't Contain", v1 = settings.get("use_contains_string"), v2 = settings.get("use_contains_no_string"), \
                                cc1=lambda x:update_active_items(), cc2= lambda x:update_active_items())  
    
    # Element Name Textbox
    name_textbox_container = cmds.rowColumnLayout( p=content_main, numberOfRows=1)
    
    contains_name_text_field = cmds.textField(p = name_textbox_container, width=130, text="Jnt", en=False, \
                                           enterCommand=lambda x:update_stored_values_and_run())
    contains_no_name_text_field = cmds.textField(p = name_textbox_container,width=130, text="End, eye", en=False, \
                                           enterCommand=lambda x:update_stored_values_and_run())
    cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 3) #Empty Space
    cmds.separator(h=10, p=content_main)
    
    # Element Type
    cmds.text("Element Type",p=content_main)
    cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 5) #Empty Space
    type_container = cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 25)
    cmds.text("    ") # Increase this to move checkboxes to the right
    contains_type_or_not_checkbox = cmds.checkBoxGrp(p=type_container, columnWidth2=[120, 1], numberOfCheckBoxes=2, \
                                label1 = ' Does Contain ', label2 = "  Doesn't Contain", v1 = settings.get("use_contains_type"), v2 = settings.get("use_contains_no_type"), \
                                cc1=lambda x:update_active_items(), cc2= lambda x:update_active_items())  
    
    # Element Type Textbox
    name_textbox_container = cmds.rowColumnLayout( p=content_main, numberOfRows=1)
    
    contains_type_text_field = cmds.textField(p = name_textbox_container, width=130, text="joint", en=False, \
                                           enterCommand=lambda x:update_stored_values_and_run()) 
    contains_no_type_text_field = cmds.textField(p = name_textbox_container,width=130, text="mesh", en=False, \
                                           enterCommand=lambda x:update_stored_values_and_run())
    cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 3) #Empty Space
    
        
    # Element Type Shape Node Behaviour
    shape_node_behavior_container = cmds.rowColumnLayout(p=content_main,numberOfRows=1, adj = True)
    shape_node_behavior_menu = cmds.optionMenu(en=False, p=shape_node_behavior_container, label=' Behavior', cc=lambda x:update_active_items()) #######
    cmds.menuItem( label='Select Both Parent and Shape')
    cmds.menuItem( label='Select Shapes as Objects')
    cmds.menuItem( label='Select Parent Instead')
    cmds.menuItem( label='Ignore Shape Nodes')
    

    # Print Types Buttons
    cmds.rowColumnLayout(p=content_main,adj=True,h=5)
    show_attributes_container = cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 25)
    cmds.button(p=show_attributes_container, l ="Print Selection Types", w=130,\
                                    c=lambda x:print_selection_types("selection"))                                                                    
    cmds.button(p=show_attributes_container, l ="Print All Scene Types", w=130,\
                                    c=lambda x:print_selection_types("all")) 
    
    cmds.separator(h=10, p=content_main)
    
    # Visibility
    visibility_container = cmds.rowColumnLayout( p=content_main, numberOfRows=1)
    cmds.text("    ")
    use_visibility_state = cmds.checkBox(p=visibility_container, label=' Visibility State  --->  ', value=settings.get("use_visibility_state"),\
                         cc=lambda x:update_active_items())
    cmds.radioCollection()
    visibility_rb1 = cmds.radioButton( p=visibility_container, label=' On  ' , en=False)
    visibility_rb2 = cmds.radioButton( p=visibility_container,  label=' Off ', en=False, sl=True)
    cmds.separator(h=10, p=content_main)
    
    # Outline Color
    outline_color_container = cmds.rowColumnLayout( p=content_main, numberOfRows=1)
    cmds.text("    ")
    use_outline_color = cmds.checkBox(p=outline_color_container, label='', value=settings.get("use_outliner_color"),\
                         cc=lambda x:update_active_items())
                         
    has_outliner_color_slider_one = cmds.colorSliderGrp(en=False, label='Uses Outliner Color  --->  ', rgb=(settings.get("stored_outliner_color")[0], \
                                                                settings.get("stored_outliner_color")[1], settings.get("stored_outliner_color")[2]),\
                                                                columnWidth=((1,145),(2,30),(3,0)), cc=lambda x:update_active_items())
    cmds.button(l ="Get", bgc=(.1, .1, .1), w=30, c=lambda x:get_color_from_selection(has_outliner_color_slider_one), height=10, width=40)
    
    
    outline_no_color_container = cmds.rowColumnLayout( p=content_main, numberOfRows=1) 
    cmds.text("    ")                                              
    use_no_outline_color = cmds.checkBox(p=outline_no_color_container, label='', value=settings.get("use_no_outliner_color"),\
                         cc=lambda x:update_active_items())
                         
    has_no_outliner_color_slider_one = cmds.colorSliderGrp(en=False, label=' But Not Using This  --->   ', rgb=(settings.get("stored_no_outliner_color")[0], \
                                                                settings.get("stored_no_outliner_color")[1], settings.get("stored_no_outliner_color")[2]),\
                                                                columnWidth=((1,145),(2,30),(3,0)), cc=lambda x:update_active_items())
    cmds.button(l ="Get", bgc=(.1, .1, .1), w=30, c=lambda x:get_color_from_selection(has_no_outliner_color_slider_one), height=10, width=40)
                                                   
    cmds.separator(h=10, p=content_main)
 
                        
    # Store Selection One
    target_container = cmds.rowColumnLayout( p=content_main, numberOfRows=1)
    remove_from_sel_btn_one = cmds.button(p=target_container, l ="-", bgc=(.5, .1, .1), w=30, \
                            c=lambda x:selection_storage_manager('remove',1 ))
    store_sel_btn_one = cmds.button(p=target_container, l ="Store Selection", bgc=(0, 0, 0), w=91, \
                            c=lambda x:selection_storage_manager('store',1))
    add_to_sel_btn_one = cmds.button(p=target_container, l ="+", bgc=(.1, .5, .1), w=30, \
                            c=lambda x:selection_storage_manager('add',1))
    reset_sel_btn_one = cmds.button(p=target_container, l ="Reset", w=55, \
                            c=lambda x:selection_storage_manager('reset',1))
    savesel_btn_one = cmds.button(p=target_container, l ="Save", w=55, \
                            c=lambda x:selection_storage_manager('save',1))
    
    # Store Selection Two
    target_container = cmds.rowColumnLayout( p=content_main, numberOfRows=1)
    remove_from_sel_btn_two = cmds.button(p=target_container, l ="-", bgc=(.5, .1, .1), w=30, \
                            c=lambda x:selection_storage_manager('remove',2))
    store_sel_btn_two = cmds.button(p=target_container, l ="Store Selection", bgc=(0, 0, 0), w=91, \
                            c=lambda x:selection_storage_manager('store',2))
    add_to_sel_btn_two = cmds.button(p=target_container, l ="+", bgc=(.1, .5, .1), w=30, \
                            c=lambda x:selection_storage_manager('add',2))
    reset_sel_btn_two = cmds.button(p=target_container, l ="Reset", w=55, \
                            c=lambda x:selection_storage_manager('reset',2))
    save_sel_btn_two = cmds.button(p=target_container, l ="Save", w=55, \
                            c=lambda x:selection_storage_manager('save',2))


    cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 3) #Empty Space
    save_as_container = cmds.rowColumnLayout( p=content_main, numberOfRows=1)                  
    cmds.radioCollection()
    save_as_quick_selection_rb1 = cmds.radioButton( p=save_as_container, sl=True, label=' Save as Quick Selection  ', cc=lambda x:update_active_items())
    cmds.radioButton( p=save_as_container,label=' Save as Text File ', cc=lambda x:update_active_items())

    cmds.separator(h=10, p=content_main)
    
    # Create New Selection (Main Function)
    cmds.button(p=content_main, l ="Create New Selection", c=lambda x:update_stored_values_and_run(True))
    
    cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 5) #Empty Space
    
    # Update Selection (Main Function)
    cmds.button(p=content_main, l ="Update Current Selection", bgc=(.6, .8, .6), c=lambda x:update_stored_values_and_run(False))
    
    # End of Dialog Constructor =========================================================================================================
    
    # Prints selection types or all types
    
    def selection_storage_manager(command,desired_container):
        selection = cmds.ls(selection=True)
        error_detected = False
        
        if desired_container == 1:
            container = 'stored_selection_one'
            button = store_sel_btn_one
        else:
            container = 'stored_selection_two'
            button = store_sel_btn_two
        
        if len(selection) > 0:
            pass
        else:
            if command != "save" and command != "load" and command != "add" and command != "reset":
                cmds.warning('Nothing Selected')
            error_detected = True

            
        if command == "remove" and error_detected == False:
            for obj in selection:
                if obj in settings.get(container):
                    try: 
                        settings.get(container).remove(obj)
                    except:
                        pass
        
        to_store_list = []
        if command == "store" and error_detected == False:
            for obj in selection:
                to_store_list.append(obj)
            settings[container] = to_store_list
            
        to_add_list = []
        if command == "add" and error_detected == False:
            for obj in selection:
                if obj not in settings.get(container):
                    to_add_list.append(obj)
                    
            for obj_add in to_add_list:
                settings.get(container).append(obj_add)
                     
        if command == "reset":
            settings[container] = []
                
        if command == "save":
            if settings.get('stored_save_as_quick_selection') != True:
                export_to_txt(settings.get(container)) ########
            else:
                new_set = cmds.sets(name="Set_StoredSelection_0" + str(desired_container))
                for obj in settings.get(container):
                    cmds.sets(obj, add=new_set)
                        
        if command == "load":
            stored_list_manager(settings.get(container))
            

        
        # Updates Button
        if len(settings.get(container)) == 0:
            cmds.button(button, l ="Store Selection", e=True, bgc=(0, 0, 0), c=lambda x:selection_storage_manager('store', desired_container))
        else:
            loaded_text = str(len(settings.get(container))) + " objects"
            if len(settings.get(container)) == 1:
                loaded_text = settings.get(container)[0]
            cmds.button(button, l =loaded_text,e=True, bgc=(.6, .8, .6), c=lambda x:selection_storage_manager('load',desired_container))
            
    
    def print_selection_types(type):
        selection = cmds.ls(selection=True)
        type_list = []
        if type == "selection" and len(selection) > 0:
            for obj in selection:
                if cmds.objectType(obj) not in type_list:
                    type_list.append(cmds.objectType(obj))
                try: # Too handle elements without shapes
                    shape_node = cmds.listRelatives(obj, shapes=True) or []
                except:
                    pass
                if shape_node != [] and cmds.objectType(shape_node[0]) not in type_list:
                    type_list.append(cmds.objectType(shape_node[0])+ " (Shape Node)") 

        if type == "all":
            #type_list = cmds.ls(nodeTypes=True) # Too see every type available
            everything_in_scene = cmds.ls()
            for obj in everything_in_scene:
                if cmds.objectType(obj) not in type_list:
                    type_list.append(cmds.objectType(obj))
                try: # Too handle elements without shapes
                    shape_node = cmds.listRelatives(obj, shapes=True) or []
                except:
                    pass
                if shape_node != [] and cmds.objectType(shape_node[0]) not in type_list:
                    type_list.append(cmds.objectType(shape_node[0]) + " (Shape Node)")

        if type_list != []:
            print("#" * 80)
            print(" " * 30 + " Types:")
            for type in type_list:
                print(type)
            print("#" * 80)
            cmds.headsUpMessage( 'Open Script Editor to see the list of types', verticalOffset=150 , time=5.0)
        else:
            cmds.warning("Nothing selected (or no types to be displayed)")

    # Updates many of the stored GUI values (Used by multiple elements)
    def get_color_from_selection(color_slider): 
        selection = cmds.ls(selection=True)
        if len(selection) > 0:
            obj_attr_list = cmds.listAttr(selection[0]) or []
            if len(obj_attr_list) > 0 and "outlinerColor" in obj_attr_list and "useOutlinerColor" in obj_attr_list:
                extracted_color = cmds.getAttr(selection[0] + ".outlinerColor")
                if cmds.getAttr(selection[0] + ".useOutlinerColor"):
                    cmds.colorSliderGrp(color_slider, e=True, rgb=extracted_color[0])
                else:
                    cmds.colorSliderGrp(color_slider, e=True, rgb=extracted_color[0])
                    cmds.warning("Color extracted, but it looks like the object selected is not using a custom outliner color")
            else:
                cmds.warning("Something went wrong. Try selecting another object.")
        else:
            cmds.warning("Nothing Selected. Please select an object containing the outliner color you want to extract and try again.")
        

    # Updates many of the stored GUI values (Used by multiple elements)
    def update_active_items(): 
        # Updates Visibility and Use Settings
        settings["use_contains_string"] = cmds.checkBoxGrp(contains_string_or_not_checkbox, q=True, value1=True)
        settings["use_contains_no_string"] = cmds.checkBoxGrp(contains_string_or_not_checkbox, q=True, value2=True)
        settings["use_contains_type"] = cmds.checkBoxGrp(contains_type_or_not_checkbox, q=True, value1=True)
        settings["use_contains_no_type"] = cmds.checkBoxGrp(contains_type_or_not_checkbox, q=True, value2=True)
        settings["use_visibility_state"] = cmds.checkBox(use_visibility_state, q=True, value=True)
        settings["use_outliner_color"] = cmds.checkBox(use_outline_color, q=True, value=True)
        settings["use_no_outliner_color"] = cmds.checkBox(use_no_outline_color, q=True, value=True)
        
        
        # Updates Visibility
        if settings.get("use_contains_string"):
            cmds.textField(contains_name_text_field, e=True, en=True)
        else:
            cmds.textField(contains_name_text_field, e=True, en=False)
            
        if settings.get("use_contains_no_string"):
            cmds.textField(contains_no_name_text_field, e=True, en=True)
        else:
            cmds.textField(contains_no_name_text_field, e=True, en=False)
            
        if settings.get("use_contains_type"):
            cmds.textField(contains_type_text_field, e=True, en=True)
        else:
            cmds.textField(contains_type_text_field, e=True, en=False)
        
        if settings.get("use_contains_no_type"):
            cmds.textField(contains_no_type_text_field, e=True, en=True)
        else:
            cmds.textField(contains_no_type_text_field, e=True, en=False)
        
        if settings.get("use_visibility_state"):
            cmds.radioButton( visibility_rb1, e=True, en=True)
            cmds.radioButton( visibility_rb2, e=True, en=True)
        else:
            cmds.radioButton( visibility_rb1, e=True, en=False)
            cmds.radioButton( visibility_rb2, e=True, en=False)
        
        if settings.get("use_outliner_color"):
            cmds.colorSliderGrp(has_outliner_color_slider_one, e=True, en=True)
        else:
            cmds.colorSliderGrp(has_outliner_color_slider_one, e=True, en=False)
        
        if settings.get("use_no_outliner_color"):
            cmds.colorSliderGrp(has_no_outliner_color_slider_one, e=True, en=True)
        else:
            cmds.colorSliderGrp(has_no_outliner_color_slider_one, e=True, en=False)
        
        
        # Stores Values
        settings["stored_contains_string"] = parse_text_field(cmds.textField(contains_name_text_field, q=True, text=True))
        settings["stored_contains_no_string"] = parse_text_field(cmds.textField(contains_no_name_text_field, q=True, text=True))
        settings["stored_contains_type"] = parse_text_field(cmds.textField(contains_type_text_field, q=True, text=True))
        settings["stored_contains_no_type"] = parse_text_field(cmds.textField(contains_no_type_text_field, q=True, text=True))
        
        
        if settings.get('use_contains_type') or settings.get('use_contains_no_type'):
            cmds.optionMenu(shape_node_behavior_menu, e=True, en=True)
        else:
            cmds.optionMenu(shape_node_behavior_menu, e=True, en=False)
  
        settings["stored_shape_node_type"] = cmds.optionMenu(shape_node_behavior_menu, q=True, value=True)
     
        settings["stored_visibility_state"]  = cmds.radioButton(visibility_rb1, q=True, select=True )
        settings["stored_save_as_quick_selection"]  = cmds.radioButton(save_as_quick_selection_rb1, q=True, select=True )

        settings["stored_outliner_color"] = cmds.colorSliderGrp(has_outliner_color_slider_one, q=True, rgb=True)
        
        settings["stored_no_outliner_color"] = cmds.colorSliderGrp(has_no_outliner_color_slider_one, q=True, rgb=True)

        
    # Updates elements to reflect the use disconnect function
    def update_stored_values_and_run(is_new_selection): 
        update_active_items() # Updates Stored Values
        settings["stored_new_selection"] = is_new_selection # New selection or existing one?
        manage_selection() # Runs main function


    cmds.showWindow(build_gui_selection_manager)
    # Main GUI Ends Here =================================================================================


# Main Function 
def manage_selection():
    
    managed_selection_list = []
    to_remove_list = []
    to_add_list = []
    
    
    # New Selection or Existing One
    if settings.get("stored_new_selection"):
        selection = cmds.ls()
    else:
        selection = cmds.ls(selection=True)

    # Starts Processing ################################################
    for obj in selection:
        
        #String Manager
        if settings.get('use_contains_string'):
            for string in settings.get('stored_contains_string'):
                if string in obj:
                    to_add_list.append(obj)
                    
        if settings.get('use_contains_no_string'):
            for string in settings.get('stored_contains_no_string'):
                if string in obj:
                    to_remove_list.append(obj)
        
        # Type Manager (Define Vars First)
        if settings.get('use_contains_type') or settings.get('use_contains_no_type'):
            obj_type = cmds.objectType(obj)
            obj_shape_type = []
            if settings.get('stored_shape_node_type') != 'Ignore Shape Nodes':
                obj_shape_type_extract = cmds.listRelatives(obj, shapes=True) or []
                if len(obj_shape_type_extract) > 0:
                    obj_shape_type = cmds.objectType(obj_shape_type_extract[0])
        
        # Type Contains
        if settings.get('use_contains_type'):
            for string in settings.get('stored_contains_type'):
                if settings.get('stored_shape_node_type') == "Select Shapes as Objects" and string in obj_type:
                    to_add_list.append(obj)
                    
                if settings.get('stored_shape_node_type') == "Select Parent Instead":
                    if string in obj_shape_type or string in obj_type:
                        if is_object_shape(obj) == False:
                            to_add_list.append(obj)
                        else:
                            to_remove_list.append(obj)
                        
                if settings.get('stored_shape_node_type') == "Ignore Shape Nodes" and string in obj_type:
                    if is_object_shape(obj) == False:
                        to_add_list.append(obj)
                    else:
                        to_remove_list.append(obj)
                    
                if settings.get('stored_shape_node_type') == "Select Both Parent and Shape" and string in obj_shape_type or string in obj_type:
                    to_add_list.append(obj)
       
        # Type Doesn't Contain          
        if settings.get('use_contains_no_type'):
            for string in settings.get('stored_contains_no_type'):
                if settings.get('stored_shape_node_type') == "Select Shapes as Objects" and string in obj_type:
                    to_remove_list.append(obj)
                    
                if settings.get('stored_shape_node_type') == "Select Parent Instead":
                    if string in obj_shape_type or string in obj_type:
                        if is_object_shape(obj) == False:
                            to_remove_list.append(obj)
                        else:
                            pass
                        
                if settings.get('stored_shape_node_type') == "Ignore Shape Nodes" and string in obj_type:
                    if is_object_shape(obj) == False:
                        to_remove_list.append(obj)
                    else:
                        pass
                    
                if settings.get('stored_shape_node_type') == "Select Both Parent and Shape" and string in obj_shape_type or string in obj_type:
                    to_remove_list.append(obj)
        
        # Create Variables for Visibility and Outliner Color
        if settings.get('use_visibility_state') == True or settings.get('use_outliner_color') == True or settings.get('use_no_outliner_color') == True:
            obj_attr_list = cmds.listAttr(obj) or []
        
        # Check Visibility State
        if settings.get('use_visibility_state') == True and settings.get('stored_visibility_state') == True:
            if len(obj_attr_list) > 0 and "visibility" in obj_attr_list:
                if cmds.getAttr(obj + ".visibility"):
                    to_add_list.append(obj)
        
        if settings.get('use_visibility_state') == True and settings.get('stored_visibility_state') == False:
            if len(obj_attr_list) > 0 and "visibility" in obj_attr_list:
                if cmds.getAttr(obj + ".visibility"):
                    to_remove_list.append(obj)
                    
        # Check outliner color      
        if settings.get('use_outliner_color'):
            if len(obj_attr_list) > 0 and "outlinerColor" in obj_attr_list and "useOutlinerColor" in obj_attr_list:
                outliner_color = cmds.getAttr(obj + ".outlinerColor")[0]
                stored_outliner_color = settings.get('stored_outliner_color')
                if outliner_color[0] == stored_outliner_color[0] and outliner_color[1] == stored_outliner_color[1] and outliner_color[2] == stored_outliner_color[2]:
                    to_add_list.append(obj)
                        
        if settings.get('use_no_outliner_color'):
            if len(obj_attr_list) > 0 and "outlinerColor" in obj_attr_list and "useOutlinerColor" in obj_attr_list:
                outliner_color = cmds.getAttr(obj + ".outlinerColor")[0]
                stored_no_outliner_color = settings.get('stored_no_outliner_color')
                if outliner_color[0] == stored_no_outliner_color[0] and outliner_color[1] == stored_no_outliner_color[1] and outliner_color[2] == stored_no_outliner_color[2]:
                    to_remove_list.append(obj)

    # Finishes Processing ################################################
    
    # Check what was done to determine actions
    add_operations = [ 'use_contains_string', 'use_contains_type', 'use_outliner_color',  ]
    remove_operations = [ 'use_contains_no_string', 'use_contains_no_type', 'use_no_outliner_color' ]

    add_operation_happened = False
    remove_operation_happened = False
    for op in add_operations:
        if settings.get(op) == True:
            add_operation_happened = True
            
    for op in remove_operations:
        if settings.get(op) == True:
            remove_operation_happened = True
    
    if settings.get('use_visibility_state') == True and settings.get('stored_visibility_state') == True:
        add_operation_happened = True
        
    if settings.get('use_visibility_state') == True and settings.get('stored_visibility_state') == False:
        remove_operation_happened = True

    
    # Manage Selection
    if add_operation_happened == False and remove_operation_happened == False:
        managed_selection_list = selection
        cmds.warning("No option was active, everything was selected.")
        
    if add_operation_happened == False and remove_operation_happened == True:
        managed_selection_list = selection
    
    for obj_add in to_add_list:
        if obj_add not in to_remove_list:
            managed_selection_list.append(obj_add)
        
    managed_selection_list_copy = managed_selection_list
    for obj_remove in to_remove_list:
        for obj_copy in managed_selection_list_copy:
            if obj_remove in obj_copy and obj_remove in managed_selection_list:
                    managed_selection_list.remove(obj_remove)
    
    cmds.select(managed_selection_list, ne=True)
 

    # ============================= End of Main Function =============================

def export_to_txt(list):
    temp_dir = cmds.internalVar(userTmpDir=True)
    txt_file = temp_dir+'tmp_sel.txt';
    
    f = open(txt_file,'w')
    
    string_for_python = "', '".join(list)
    string_for_mel = " ".join(list)
    string_for_list = "\n# ".join(list)

    select_command = "# Python command to select it:\n\nimport maya.cmds as cmds\nselectedObjects = ['" + string_for_python + \
    "'] \ncmds.select(selectedObjects)\n\n\n\'\'\'\n// Mel command to select it\nselect -r " + string_for_mel + "\n\n\'\'\'\n\n\n# List of Objects:\n# " + string_for_list

    f.write(select_command)
    f.close()

    notepad_command = 'exec("notepad ' + txt_file + '");'
    mel.eval(notepad_command)

    
# Returns if object is a shape or not
def is_object_shape(object):
    node_inheritance =  cmds.nodeType(object, inherited=True)
    is_shape = False
    for inheritance in node_inheritance:
        if "shape" in inheritance:
            is_shape = True
    return is_shape

# If object exists, select it
def if_objects_in_list_exists_select(list): ################################# EDITING
    for obj in list:
        if cmds.objExists(obj):
            cmds.select(obj)
            cmds.headsUpMessage(obj + " selected", verticalOffset=150 )
        else:
            cmds.warning("Object doesn't exist! Did you delete or rename it after loading?")

# If object exists, select it
def if_exists_select(obj):
    if cmds.objExists(obj):
        cmds.select(obj)
        cmds.headsUpMessage(obj + " selected", verticalOffset=150 )
    else:
        cmds.warning("Object doesn't exist! Did you delete or rename it after loading?")

# stored_list_manager
def stored_list_manager(list):
    missing_elements = False
    found_elements = []
    print("#" * 32 + " Objects List " + "#" * 32)
    for obj in list:
        if cmds.objExists(obj):
            print(obj)
            found_elements.append(obj)
        else:
            print(obj + " no longer exists!")
            missing_elements = True
    print("#" * 80)
    if missing_elements:
        cmds.headsUpMessage( 'It looks like you are missing some elements! Open script editor for more information', verticalOffset=150 , time=5.0)
    else:
        cmds.headsUpMessage( 'Stored elements selected (Open script editor to see a list)', verticalOffset=150 , time=5.0)
    if list != []:
        cmds.select(found_elements)

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


def build_gui_help_selection_manager():
    if cmds.window("build_gui_help_selection_manager", exists =True):
        cmds.deleteUI("build_gui_help_selection_manager")    

    # Help Dialog Start Here =================================================================================
    
    # Build About UI
    build_gui_help_selection_manager = cmds.window("build_gui_help_selection_manager", title="GT Selection Manager - Help",\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =False, widthHeight = [330, 781])
    column_main = cmds.columnLayout() 

    form = cmds.formLayout(p=column_main)

    content_main = cmds.columnLayout(adj = True)

    cmds.text("")
    cmds.text("Help for GT Selection Manager ", bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.text("  ")
    cmds.text(" Version Installed: " + script_version)
    cmds.text("  ")
    cmds.text("      This script allows you to create or update your       ")
    cmds.text('      selections based on some filters (parameters)  ')
    cmds.text('      You can also save and load previous selections.  ')
    cmds.text(' ')
    cmds.text('      Element Name:   ')
    cmds.text('      This option allows you to check  if the string used   ')
    cmds.text('      for the object name contains or doesn\'t contain the     ')
    cmds.text('      the provided parameter.    ')
    cmds.text(' ')
    cmds.text('      Element Type:    ')
    cmds.text('      This filter will check the type of the element to       ')
    cmds.text('      determine if it should be part of the selection or not.    ')
    cmds.text(' ')
    cmds.text('      Element Type > Behavior (Dropdown Menu):   ')
    cmds.text('      Since most elements are transforms, you can use the   ')
    cmds.text('      dropdown menu "Behavior" to determine how to filter    ')
    cmds.text('      the shape element (usually hidden inside the transform)   ')
    cmds.text('      (You can consider transform, shape, both or ignore it)    ')
    cmds.text(' ')
    cmds.text("      Visibility State:   ")
    cmds.text('      Selection based on the current state of the node\'s    ')
    cmds.text('      visibility attribute.    ')
    cmds.text(' ')
    cmds.text("      Outliner Color (Transform):   ")
    cmds.text('      Filters the option under Node > Display > Outliner Color    ')
    cmds.text('      In case you\'re unsure about the exact color, you can use    ')
    cmds.text('      the "Get" button to automatically copy a color.    ')
    cmds.text(' ')
    cmds.text("      Outliner Color:   ")
    cmds.text('      Filters the option under Node > Display > Outliner Color    ')
    cmds.text('      In case you\'re unsure about the exact color, you can use    ')
    cmds.text('      the "Get" button to automatically copy a color.    ')
    cmds.text(' ')
    cmds.text('      Store Selection Options:    ')
    cmds.text('      Select objects and click on "Store Selection"    ')
    cmds.text('      to store them for later.    ')
    cmds.text('      Use the "-" and "+" buttons to add or remove elements.   ')
    cmds.text('      Use the "Reset" button to clean your selection   ')
    cmds.text(' ')
    cmds.text('      You can save your selection in two ways:   ')
    cmds.text('      As a set (creates a set containing selection   ')
    cmds.text('      As text (creates a txt file containing  the code   ')
    cmds.text('      necessary to recreate selection (as well as a list)   ')
    cmds.text(' ')
    cmds.text('      Create New Selection : Uses all objects as initial selection  ')
    cmds.text('      Update Current Selection : Considers only selected objects  ')
    cmds.text(' ')

    email_container = cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 25)
    
    cmds.text('             Guilherme Trevisan : ')
    cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1,1,1], p=email_container)
    website_container = cmds.rowColumnLayout(p=content_main, numberOfRows=1, h= 25)
    cmds.text('                      Visit my ')
    cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1,1,1], p=website_container)
    cmds.text(' for updated versions')
    cmds.text(' ', p= content_main)
    cmds.separator(h=15, p=content_main)
    
    cmds.button(l ="Ok", p= content_main, c=lambda x:close_about_window())
                                                                                                                              
    def close_about_window():
        if cmds.window("build_gui_help_selection_manager", exists =True):
            cmds.deleteUI("build_gui_help_selection_manager")  
        
    cmds.showWindow(build_gui_help_selection_manager)
    
    # Help Dialog Ends Here =================================================================================



# Start current "Main"
build_gui_selection_manager()