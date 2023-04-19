"""
 GT Selection Manager Script
 github.com/TrevisanGMW/gt-tools -  2020-02-19
 
 1.0 - 2020-03-05 
 Included Help Button

 1.1 - 2020-06-07
 Updated naming convention to make it clearer. (PEP8)
 Fixed random window widthHeight issue.
 
 1.2 - 2020-06-18
 Updated GUI
 Added window icon
 
 1.2.1 - 2020-06-25
 Fixed minor issue with non-unique names when listing shapes
 
 1.3 - 20202-10-25
 Added more documentation
 Replaced "headsUpMessage" with "inViewMessage"
 Made a few minor changes
 
 1.4 - 20202-11-15
 Updated a few UI elements (color and text)
 
 1.5 - 2021-05-12
 Made script compatible with Python 3 (Maya 2022+)
 
 1.6 - 2021-08-18
 Added a select hierarchy button for convenience

 1.7.0 - 2022-07-04
 Added patch to the script version
 Added logger
 Added debug message to broad exceptions
 Refactored big portion of the script
 Fixed issue with the selection of outliner colors

 1.7.1 - 2022-10-26
 Updated selection variable name from "selectedObjects" to "selected_objects"

 To Do:
 Add Selection base on Shader name, Texture, TRS
 Add choice between transform and shape for outliner color
 
"""
import maya.cmds as cmds
import maya.mel as mel
import logging
import random
from maya import OpenMayaUI

try:
    from shiboken2 import wrapInstance
except ImportError:
    from shiboken import wrapInstance

try:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QWidget
except ImportError:
    from PySide.QtGui import QIcon, QWidget

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_rigger_biped_gui")
logger.setLevel(logging.INFO)

# Script Name
script_name = "GT Selection Manager"

# Version:
script_version = "1.7.1"

gt_sel_manager = {'use_contains_string': False,  # Active Functions
                  'use_contains_no_string': False,
                  'use_contains_type': False,
                  'use_contains_no_type': False,
                  'use_visibility_state': False,
                  'use_outliner_color': False,
                  'use_no_outliner_color': False,
                  'stored_outliner_color': [1, 1, 1],  # StoredValues
                  'stored_no_outliner_color': [1, 1, 1],
                  'stored_selection_one': [],
                  'stored_selection_two': [],
                  'stored_contains_string': '',
                  'stored_contains_no_string': '',
                  'stored_contains_type': '',
                  'stored_contains_no_type': '',
                  'stored_shape_node_type': 'Select Shapes as Objects',
                  'stored_visibility_state': False,
                  'stored_save_as_quick_selection': True,
                  'stored_new_selection': False
                  }


# Main Form ============================================================================
def build_gui_selection_manager():
    """ Builds the main window for GT Selection Manager """
    window_name = "build_gui_selection_manager"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)

        # Main GUI Start Here =================================================================================

    window_gui_selection_manager = cmds.window(window_name, title=script_name + '  (v' + script_version + ')',
                                               titleBar=True, mnb=False, mxb=False, sizeable=True)

    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    content_main = cmds.columnLayout(adj=True)

    # Title
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 10)], p=content_main)  # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 200), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)], p=content_main)
    cmds.text(" ", bgc=title_bgc_color)  # Tiny Empty Green Space
    cmds.text(script_name, bgc=title_bgc_color, fn="boldLabelFont", align="left")
    cmds.button(l="Help", bgc=title_bgc_color, c=lambda x: build_gui_help_selection_manager())
    cmds.separator(h=10, style='none', p=content_main)  # Empty Space

    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)

    cmds.separator(h=10)
    cmds.separator(h=5, style='none')  # Empty Space

    # Element Name
    cmds.text("Element Name")
    cmds.separator(h=10, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)])
    contains_string_or_not_checkbox = cmds.checkBoxGrp(columnWidth2=[120, 1], numberOfCheckBoxes=2,
                                                       label1=' Does Contain ', label2="  Doesn't Contain",
                                                       v1=gt_sel_manager.get("use_contains_string"),
                                                       v2=gt_sel_manager.get("use_contains_no_string"),
                                                       cc1=lambda x: update_active_items(),
                                                       cc2=lambda x: update_active_items())

    # Element Name Textbox
    cmds.rowColumnLayout(nc=3, cw=[(1, 110), (2, 10), (3, 110)], cs=[(1, 0), (2, 0), (2, 0)])
    contains_name_text_field = cmds.textField(text="_jnt", en=False,
                                              enterCommand=lambda x: update_stored_values_and_run(False))

    cmds.separator(h=10, style='none')  # Empty Space

    contains_no_name_text_field = cmds.textField(text="endJnt, eye", en=False,
                                                 enterCommand=lambda x: update_stored_values_and_run(False))

    cmds.separator(h=10, style='none')  # Empty Space

    cmds.separator(h=10, p=body_column)

    # Element Type
    cmds.separator(h=5, style='none', p=body_column)  # Empty Space
    cmds.text("Element Type", p=body_column)
    cmds.separator(h=5, style='none', p=body_column)  # Empty Space

    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=body_column)
    contains_type_or_not_checkbox = cmds.checkBoxGrp(columnWidth2=[120, 1], numberOfCheckBoxes=2,
                                                     label1=' Does Contain ', label2="  Doesn't Contain",
                                                     v1=gt_sel_manager.get("use_contains_type"),
                                                     v2=gt_sel_manager.get("use_contains_no_type"),
                                                     cc1=lambda x: update_active_items(),
                                                     cc2=lambda x: update_active_items())

    # Element Type Textbox
    cmds.rowColumnLayout(nc=3, cw=[(1, 110), (2, 10), (3, 110)], cs=[(1, 0), (2, 0), (2, 0)])

    contains_type_text_field = cmds.textField(text="joint", en=False,
                                              enterCommand=lambda x: update_stored_values_and_run(False))
    cmds.separator(h=10, style='none')  # Empty Space
    contains_no_type_text_field = cmds.textField(text="mesh", en=False,
                                                 enterCommand=lambda x: update_stored_values_and_run(False))

    # Element Type Shape Node Behaviour
    cmds.rowColumnLayout(nc=1, cw=[(1, 240)], cs=[(1, 0)], p=body_column)
    cmds.separator(h=5, style='none')  # Empty Space
    shape_node_behavior_menu = cmds.optionMenu(en=False, label=' Behavior', cc=lambda x: update_active_items())
    cmds.menuItem(label='Select Both Parent and Shape')
    cmds.menuItem(label='Select Shapes as Objects')
    cmds.menuItem(label='Select Parent Instead')
    cmds.menuItem(label='Ignore Shape Nodes')

    # Print Types Buttons
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 130), (2, 130)], cs=[(1, 0), (2, 0)], p=body_column)

    cmds.button(l="Print Selection Types", c=lambda x: print_selection_types("selection"))
    cmds.button(l="Print All Scene Types", c=lambda x: print_selection_types("all"))

    cmds.separator(h=5, style='none')  # Empty Space
    cmds.separator(h=10, p=body_column)

    # Visibility
    visibility_container = cmds.rowColumnLayout(p=body_column, numberOfRows=1)
    cmds.text("    ")
    use_visibility_state = cmds.checkBox(p=visibility_container, label=' Visibility State  --->  ',
                                         value=gt_sel_manager.get("use_visibility_state"),
                                         cc=lambda x: update_active_items())
    cmds.radioCollection()
    visibility_rb1 = cmds.radioButton(p=visibility_container, label=' On  ', en=False)
    visibility_rb2 = cmds.radioButton(p=visibility_container, label=' Off ', en=False, sl=True)
    cmds.separator(h=10, p=body_column)

    # Outline Color
    outline_color_container = cmds.rowColumnLayout(p=body_column, numberOfRows=1)
    cmds.text("    ")
    use_outline_color = cmds.checkBox(p=outline_color_container, label='',
                                      value=gt_sel_manager.get("use_outliner_color"),
                                      cc=lambda x: update_active_items())

    has_outliner_color_slider_one = cmds.colorSliderGrp(en=False, label='Using Outliner Color  --->  ',
                                                        rgb=(gt_sel_manager.get("stored_outliner_color")[0],
                                                             gt_sel_manager.get("stored_outliner_color")[1],
                                                             gt_sel_manager.get("stored_outliner_color")[2]),
                                                        columnWidth=((1, 145), (2, 30), (3, 0)),
                                                        cc=lambda x: update_active_items())
    cmds.button(l="Get", bgc=(.2, .2, .2), w=30, c=lambda x: get_color_from_selection(has_outliner_color_slider_one),
                height=10, width=40)

    outline_no_color_container = cmds.rowColumnLayout(p=body_column, numberOfRows=1)
    cmds.text("    ")
    use_no_outline_color = cmds.checkBox(p=outline_no_color_container, label='',
                                         value=gt_sel_manager.get("use_no_outliner_color"),
                                         cc=lambda x: update_active_items())

    has_no_outliner_color_slider_one = cmds.colorSliderGrp(en=False, label=' But Not Using Color  --->   ',
                                                           rgb=(gt_sel_manager.get("stored_no_outliner_color")[0],
                                                                gt_sel_manager.get("stored_no_outliner_color")[1],
                                                                gt_sel_manager.get("stored_no_outliner_color")[2]),
                                                           columnWidth=((1, 145), (2, 30), (3, 0)),
                                                           cc=lambda x: update_active_items())
    cmds.button(l="Get", bgc=(.2, .2, .2), w=30, c=lambda x: get_color_from_selection(has_no_outliner_color_slider_one),
                height=10, width=40)

    cmds.separator(h=10, p=body_column)
    cmds.separator(h=5, style='none', p=body_column)  # Empty Space

    # Store Selection One
    target_container = cmds.rowColumnLayout(p=body_column, numberOfRows=1)
    cmds.button(p=target_container, l="-", bgc=(.5, .3, .3), w=30, c=lambda x: selection_storage_manager('remove', 1))
    store_sel_btn_one = cmds.button(p=target_container, l="Store Selection", bgc=(.2, .2, .2), w=91,
                                    c=lambda x: selection_storage_manager('store', 1))
    cmds.button(p=target_container, l="+", bgc=(.3, .5, .3), w=30, c=lambda x: selection_storage_manager('add', 1))
    cmds.button(p=target_container, l="Reset", w=55, c=lambda x: selection_storage_manager('reset', 1))
    cmds.button(p=target_container, l="Save", w=55, c=lambda x: selection_storage_manager('save', 1))

    # Store Selection Two
    target_container = cmds.rowColumnLayout(p=body_column, numberOfRows=1)
    cmds.button(p=target_container, l="-", bgc=(.5, .3, .3), w=30, c=lambda x: selection_storage_manager('remove', 2))
    store_sel_btn_two = cmds.button(p=target_container, l="Store Selection", bgc=(.2, .2, .2), w=91,
                                    c=lambda x: selection_storage_manager('store', 2))
    cmds.button(p=target_container, l="+", bgc=(.3, .5, .3), w=30, c=lambda x: selection_storage_manager('add', 2))
    cmds.button(p=target_container, l="Reset", w=55, c=lambda x: selection_storage_manager('reset', 2))
    cmds.button(p=target_container, l="Save", w=55, c=lambda x: selection_storage_manager('save', 2))
    cmds.separator(h=5, style='none', p=body_column)  # Empty Space

    save_as_container = cmds.rowColumnLayout(p=body_column, numberOfRows=1)
    cmds.radioCollection()

    save_as_quick_selection_rb1 = cmds.radioButton(p=save_as_container, sl=True, label=' Save as Quick Selection  ',
                                                   cc=lambda x: update_active_items())
    cmds.radioButton(p=save_as_container, label=' Save as Text File ', cc=lambda x: update_active_items())

    cmds.separator(h=10, p=body_column)

    cmds.separator(h=10, style='none', p=body_column)  # Empty Space

    # Select Hierarchy
    cmds.button(p=body_column, l="Select Hierarchy", c=lambda x: select_hierarchy())

    cmds.separator(h=5, style='none', p=body_column)  # Empty Space
    # Create New Selection (Main Function)
    cmds.button(p=body_column, l="Create New Selection", c=lambda x: update_stored_values_and_run(True))

    cmds.separator(h=5, style='none', p=body_column)  # Empty Space
    # Update Selection (Main Function)
    cmds.button(p=body_column, l="Update Current Selection", c=lambda x: update_stored_values_and_run(False))
    cmds.separator(h=10, style='none', p=body_column)  # Empty Space

    # End of Main Dialog ==============================================================================================
    def selection_storage_manager(operation, desired_container):
        """
        Updates the storage section of the script
        
        Args:
                operation (string): Which operation to execute. Save, load, store, reset, add, or remove.
                desired_container (int): Which containing the update, 1 or 2.
        """
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
            if operation != "save" and operation != "load" and operation != "add" and operation != "reset":
                cmds.warning('Nothing Selected')
            error_detected = True

        if operation == "remove" and error_detected is False:
            for obj in selection:
                if obj in gt_sel_manager.get(container):
                    try:
                        gt_sel_manager.get(container).remove(obj)
                    except Exception as e:
                        logger.debug(str(e))

        to_store_list = []
        if operation == "store" and error_detected is False:
            for obj in selection:
                to_store_list.append(obj)
            gt_sel_manager[container] = to_store_list

        to_add_list = []
        if operation == "add" and error_detected is False:
            for obj in selection:
                if obj not in gt_sel_manager.get(container):
                    to_add_list.append(obj)

            for obj_add in to_add_list:
                gt_sel_manager.get(container).append(obj_add)

        if operation == "reset":
            gt_sel_manager[container] = []

        if operation == "save":
            if gt_sel_manager.get('stored_save_as_quick_selection') is not True:
                export_to_txt(gt_sel_manager.get(container))
            else:
                new_set = cmds.sets(name="Set_StoredSelection_0" + str(desired_container))
                for obj in gt_sel_manager.get(container):
                    cmds.sets(obj, add=new_set)

        if operation == "load":
            stored_list_manager(gt_sel_manager.get(container))

        # Updates Button
        if len(gt_sel_manager.get(container)) == 0:
            cmds.button(button, l="Store Selection", e=True, bgc=(.2, .2, .2),
                        c=lambda x: selection_storage_manager('store', desired_container))
        else:
            loaded_text = str(len(gt_sel_manager.get(container))) + " objects"
            if len(gt_sel_manager.get(container)) == 1:
                loaded_text = gt_sel_manager.get(container)[0]
            cmds.button(button, l=loaded_text, e=True, bgc=(.6, .8, .6),
                        c=lambda x: selection_storage_manager('load', desired_container))

    def print_selection_types(selection_type):
        """
        Prints the type of the selected objects.
                
        Args:
                selection_type (string): Type of selection used when querying types. Selection = only selected objects.
                All = everything.
        """
        selection = cmds.ls(selection=True)
        type_list = []
        if selection_type == "selection" and len(selection) > 0:
            for obj in selection:
                if cmds.objectType(obj) not in type_list:
                    type_list.append(cmds.objectType(obj))
                shape_node = []
                try:  # To handle elements without shapes
                    shape_node = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
                except Exception as e:
                    logger.debug(str(e))
                if shape_node != [] and cmds.objectType(shape_node[0]) not in type_list:
                    type_list.append(cmds.objectType(shape_node[0]) + " (Shape Node)")

        if selection_type == "all":
            # type_list = cmds.ls(nodeTypes=True) # Too see every type available
            everything_in_scene = cmds.ls()
            for obj in everything_in_scene:
                shape_node = []
                if cmds.objectType(obj) not in type_list:
                    type_list.append(cmds.objectType(obj))
                try:  # To handle elements without shapes
                    shape_node = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
                except Exception as e:
                    logger.debug(str(e))
                if shape_node != [] and cmds.objectType(shape_node[0]) not in type_list:
                    type_list.append(cmds.objectType(shape_node[0]) + " (Shape Node)")

        if type_list:
            print("#" * 80)
            print(" " * 30 + " Types:")
            for obj_type in type_list:
                print(obj_type)
            print("#" * 80)
            # cmds.headsUpMessage( 'Open the Script Editor to see the list of types', verticalOffset=150 , time=5.0)
            message = '<' + str(random.random())
            message += '>Open the <span style=\"color:#FF0000;\">Script Editor</span> to see the list of types.'
            cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)
        else:
            cmds.warning("Nothing selected (or no types to be displayed)")

    def get_color_from_selection(color_slider):
        """
        Updates many of the stored gui values (Used by multiple elements) 
        
        Args:
            color_slider (colorSliderGrp): a color slider object to be updated.
        """
        selection = cmds.ls(selection=True)
        if len(selection) > 0:
            obj_attr_list = cmds.listAttr(selection[0]) or []
            if len(obj_attr_list) > 0 and "outlinerColor" in obj_attr_list and "useOutlinerColor" in obj_attr_list:
                extracted_color = cmds.getAttr(selection[0] + ".outlinerColor")
                logger.debug('Outliner Color (Sampled): ' + str(extracted_color))
                if cmds.getAttr(selection[0] + ".useOutlinerColor"):
                    cmds.colorSliderGrp(color_slider, e=True, rgb=extracted_color[0])
                else:
                    cmds.colorSliderGrp(color_slider, e=True, rgb=extracted_color[0])
                    cmds.warning("Color extracted, but it looks like the object "
                                 "selected is not using a custom outliner color")
            else:
                cmds.warning("Something went wrong. Try selecting another object.")
        else:
            cmds.warning("Nothing Selected. Please select an object containing the "
                         "outliner color you want to extract and try again.")

    def update_active_items():
        """ Updates many of the stored gui values (Used by multiple elements) """
        # Updates Visibility and Use gt_sel_manager
        gt_sel_manager["use_contains_string"] = cmds.checkBoxGrp(contains_string_or_not_checkbox, q=True, value1=True)
        gt_sel_manager["use_contains_no_string"] = cmds.checkBoxGrp(contains_string_or_not_checkbox, q=True,
                                                                    value2=True)
        gt_sel_manager["use_contains_type"] = cmds.checkBoxGrp(contains_type_or_not_checkbox, q=True, value1=True)
        gt_sel_manager["use_contains_no_type"] = cmds.checkBoxGrp(contains_type_or_not_checkbox, q=True, value2=True)
        gt_sel_manager["use_visibility_state"] = cmds.checkBox(use_visibility_state, q=True, value=True)
        gt_sel_manager["use_outliner_color"] = cmds.checkBox(use_outline_color, q=True, value=True)
        gt_sel_manager["use_no_outliner_color"] = cmds.checkBox(use_no_outline_color, q=True, value=True)

        # Updates Visibility
        if gt_sel_manager.get("use_contains_string"):
            cmds.textField(contains_name_text_field, e=True, en=True)
        else:
            cmds.textField(contains_name_text_field, e=True, en=False)

        if gt_sel_manager.get("use_contains_no_string"):
            cmds.textField(contains_no_name_text_field, e=True, en=True)
        else:
            cmds.textField(contains_no_name_text_field, e=True, en=False)

        if gt_sel_manager.get("use_contains_type"):
            cmds.textField(contains_type_text_field, e=True, en=True)
        else:
            cmds.textField(contains_type_text_field, e=True, en=False)

        if gt_sel_manager.get("use_contains_no_type"):
            cmds.textField(contains_no_type_text_field, e=True, en=True)
        else:
            cmds.textField(contains_no_type_text_field, e=True, en=False)

        if gt_sel_manager.get("use_visibility_state"):
            cmds.radioButton(visibility_rb1, e=True, en=True)
            cmds.radioButton(visibility_rb2, e=True, en=True)
        else:
            cmds.radioButton(visibility_rb1, e=True, en=False)
            cmds.radioButton(visibility_rb2, e=True, en=False)

        if gt_sel_manager.get("use_outliner_color"):
            cmds.colorSliderGrp(has_outliner_color_slider_one, e=True, en=True)
        else:
            cmds.colorSliderGrp(has_outliner_color_slider_one, e=True, en=False)

        if gt_sel_manager.get("use_no_outliner_color"):
            cmds.colorSliderGrp(has_no_outliner_color_slider_one, e=True, en=True)
        else:
            cmds.colorSliderGrp(has_no_outliner_color_slider_one, e=True, en=False)

        # Stores Values
        gt_sel_manager["stored_contains_string"] = parse_text_field(
            cmds.textField(contains_name_text_field, q=True, text=True))
        gt_sel_manager["stored_contains_no_string"] = parse_text_field(
            cmds.textField(contains_no_name_text_field, q=True, text=True))
        gt_sel_manager["stored_contains_type"] = parse_text_field(
            cmds.textField(contains_type_text_field, q=True, text=True))
        gt_sel_manager["stored_contains_no_type"] = parse_text_field(
            cmds.textField(contains_no_type_text_field, q=True, text=True))

        if gt_sel_manager.get('use_contains_type') or gt_sel_manager.get('use_contains_no_type'):
            cmds.optionMenu(shape_node_behavior_menu, e=True, en=True)
        else:
            cmds.optionMenu(shape_node_behavior_menu, e=True, en=False)

        gt_sel_manager["stored_shape_node_type"] = cmds.optionMenu(shape_node_behavior_menu, q=True, value=True)

        gt_sel_manager["stored_visibility_state"] = cmds.radioButton(visibility_rb1, q=True, select=True)
        gt_sel_manager["stored_save_as_quick_selection"] = cmds.radioButton(save_as_quick_selection_rb1, q=True,
                                                                            select=True)

        gt_sel_manager["stored_outliner_color"] = cmds.colorSliderGrp(has_outliner_color_slider_one, q=True, rgb=True)

        gt_sel_manager["stored_no_outliner_color"] = cmds.colorSliderGrp(has_no_outliner_color_slider_one, q=True,
                                                                         rgb=True)

    def update_stored_values_and_run(is_new_selection):
        """
        Updates elements to reflect the use of the disconnect function. 
        Stored selection type.
        Then it runs the main function.
        
        Args:
            is_new_selection (bool) : Is a new selection or existing one?
        
        """
        logger.debug('"update_stored_values_and_run" has been called.')
        update_active_items()  # Updates Stored Values
        gt_sel_manager["stored_new_selection"] = is_new_selection
        manage_selection()  # Runs main function

    # Show and Lock Window
    cmds.showWindow(window_gui_selection_manager)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/selectByHierarchy.png')
    widget.setWindowIcon(icon)

    # Main GUI Ends Here =================================================================================


# Main Function 
def manage_selection():
    """
    Manage Selection (The main function for this script)
    It queries the many options provided in the selection manager gui to update/create a new selection
    
    """
    managed_selection_list = []
    to_remove_list = []
    to_add_list = []

    # New Selection or Existing One
    if gt_sel_manager.get("stored_new_selection"):
        selection = cmds.ls()
    else:
        selection = cmds.ls(selection=True)

    # Starts Processing ################################################
    for obj in selection:

        # String Manager
        if gt_sel_manager.get('use_contains_string'):
            for string in gt_sel_manager.get('stored_contains_string'):
                if string in obj:
                    to_add_list.append(obj)

        if gt_sel_manager.get('use_contains_no_string'):
            for string in gt_sel_manager.get('stored_contains_no_string'):
                if string in obj:
                    to_remove_list.append(obj)

        # Type Manager (Define Vars First)
        obj_type = []
        obj_shape_type = []
        if gt_sel_manager.get('use_contains_type') or gt_sel_manager.get('use_contains_no_type'):
            obj_type = cmds.objectType(obj)
            if gt_sel_manager.get('stored_shape_node_type') != 'Ignore Shape Nodes':
                obj_shape_type_extract = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
                if len(obj_shape_type_extract) > 0:
                    obj_shape_type = cmds.objectType(obj_shape_type_extract[0])

        # Type Contains
        if gt_sel_manager.get('use_contains_type'):
            for string in gt_sel_manager.get('stored_contains_type'):
                if gt_sel_manager.get('stored_shape_node_type') == "Select Shapes as Objects" and string in obj_type:
                    to_add_list.append(obj)

                if gt_sel_manager.get('stored_shape_node_type') == "Select Parent Instead":
                    if string in obj_shape_type or string in obj_type:
                        if is_object_shape(obj) is False:
                            to_add_list.append(obj)
                        else:
                            to_remove_list.append(obj)

                if gt_sel_manager.get('stored_shape_node_type') == "Ignore Shape Nodes" and string in obj_type:
                    if is_object_shape(obj) is False:
                        to_add_list.append(obj)
                    else:
                        to_remove_list.append(obj)

                if gt_sel_manager.get('stored_shape_node_type') == "Select Both Parent and Shape" and \
                   string in obj_shape_type or string in obj_type:
                    to_add_list.append(obj)

        # Type Doesn't Contain          
        if gt_sel_manager.get('use_contains_no_type'):
            for string in gt_sel_manager.get('stored_contains_no_type'):
                if gt_sel_manager.get('stored_shape_node_type') == "Select Shapes as Objects" and string in obj_type:
                    to_remove_list.append(obj)

                if gt_sel_manager.get('stored_shape_node_type') == "Select Parent Instead":
                    if string in obj_shape_type or string in obj_type:
                        if is_object_shape(obj) is False:
                            to_remove_list.append(obj)
                        else:
                            pass

                if gt_sel_manager.get('stored_shape_node_type') == "Ignore Shape Nodes" and string in obj_type:
                    if is_object_shape(obj) is False:
                        to_remove_list.append(obj)
                    else:
                        pass

                if gt_sel_manager.get('stored_shape_node_type') == "Select Both Parent and Shape" and \
                   string in obj_shape_type or string in obj_type:
                    to_remove_list.append(obj)

        # Create Variables for Visibility and Outliner Color
        obj_attr_list = []
        if gt_sel_manager.get('use_visibility_state') is True or \
           gt_sel_manager.get('use_outliner_color') is True or \
           gt_sel_manager.get('use_no_outliner_color') is True:
            obj_attr_list = cmds.listAttr(obj) or []

        # Check Visibility State
        if gt_sel_manager.get('use_visibility_state') is True and gt_sel_manager.get('stored_visibility_state') is True:
            if len(obj_attr_list) > 0 and "visibility" in obj_attr_list:
                if cmds.getAttr(obj + ".visibility"):
                    to_add_list.append(obj)

        if gt_sel_manager.get('use_visibility_state') is True and gt_sel_manager.get(
                'stored_visibility_state') is False:
            if len(obj_attr_list) > 0 and "visibility" in obj_attr_list:
                if cmds.getAttr(obj + ".visibility"):
                    to_remove_list.append(obj)

        # Check outliner color      
        if gt_sel_manager.get('use_outliner_color'):
            if len(obj_attr_list) > 0 and "outlinerColor" in obj_attr_list and "useOutlinerColor" in obj_attr_list:
                outliner_color = cmds.getAttr(obj + ".outlinerColor")[0]
                stored_outliner_color = gt_sel_manager.get('stored_outliner_color')
                logger.debug('Outliner Color (Object): ' + str(outliner_color))
                logger.debug('Outliner Color (Stored): ' + str(stored_outliner_color))

                outliner_color_r = float('%.6f' % (outliner_color[0]))
                outliner_color_g = float('%.6f' % (outliner_color[1]))
                outliner_color_b = float('%.6f' % (outliner_color[2]))
                stored_outliner_color_r = float('%.6f' % (stored_outliner_color[0]))
                stored_outliner_color_g = float('%.6f' % (stored_outliner_color[1]))
                stored_outliner_color_b = float('%.6f' % (stored_outliner_color[2]))
                debug_message = 'Outliner Color (Object-Truncated): ('
                debug_message += str(outliner_color_r) + ', '
                debug_message += str(outliner_color_g) + ', '
                debug_message += str(outliner_color_b) + ')'
                logger.debug(debug_message)
                debug_message = 'Outliner Color (Stored-Truncated): ('
                debug_message += str(stored_outliner_color_r) + ', '
                debug_message += str(stored_outliner_color_g) + ', '
                debug_message += str(stored_outliner_color_b) + ')'
                logger.debug(debug_message)

                if outliner_color_r == stored_outliner_color_r and \
                   outliner_color_g == stored_outliner_color_g and \
                   outliner_color_b == stored_outliner_color_b:
                    to_add_list.append(obj)

        if gt_sel_manager.get('use_no_outliner_color'):
            if len(obj_attr_list) > 0 and "outlinerColor" in obj_attr_list and "useOutlinerColor" in obj_attr_list:
                outliner_color = cmds.getAttr(obj + ".outlinerColor")[0]
                stored_no_outliner_color = gt_sel_manager.get('stored_no_outliner_color')

                outliner_color_r = float('%.6f' % (outliner_color[0]))
                outliner_color_g = float('%.6f' % (outliner_color[1]))
                outliner_color_b = float('%.6f' % (outliner_color[2]))
                stored_no_outliner_color_r = float('%.6f' % (stored_no_outliner_color[0]))
                stored_no_outliner_color_g = float('%.6f' % (stored_no_outliner_color[1]))
                stored_no_outliner_color_b = float('%.6f' % (stored_no_outliner_color[2]))

                if outliner_color_r == stored_no_outliner_color_r and \
                   outliner_color_g == stored_no_outliner_color_g and \
                   outliner_color_b == stored_no_outliner_color_b:
                    to_remove_list.append(obj)

    # Finishes Processing ################################################

    # Check what was done to determine actions
    add_operations = ['use_contains_string', 'use_contains_type', 'use_outliner_color', ]
    remove_operations = ['use_contains_no_string', 'use_contains_no_type', 'use_no_outliner_color']

    add_operation_happened = False
    remove_operation_happened = False
    for op in add_operations:
        if gt_sel_manager.get(op) is True:
            add_operation_happened = True

    for op in remove_operations:
        if gt_sel_manager.get(op) is True:
            remove_operation_happened = True

    if gt_sel_manager.get('use_visibility_state') is True and gt_sel_manager.get('stored_visibility_state') is True:
        add_operation_happened = True

    if gt_sel_manager.get('use_visibility_state') is True and gt_sel_manager.get('stored_visibility_state') is False:
        remove_operation_happened = True

    # Manage Selection
    if add_operation_happened is False and remove_operation_happened is False:
        managed_selection_list = selection
        cmds.warning("No option was active, everything was selected.")

    if add_operation_happened is False and remove_operation_happened is True:
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
    selection_feedback(len(managed_selection_list))

    # ============================= End of Main Function =============================


def export_to_txt(export_list):
    """
    Creates a txt file and writes a list of objects to it (with necessary code used to select it, in Mel and Python)
    
    Args:
        export_list (list): A list of string to be exported to a txt file
    
    """
    temp_dir = cmds.internalVar(userTmpDir=True)
    txt_file = temp_dir + 'tmp_sel.txt'

    f = open(txt_file, 'w')

    string_for_python = "', '".join(export_list)
    string_for_mel = " ".join(export_list)
    string_for_list = "\n# ".join(export_list)

    select_command = "# Python command to select it:\n\n" \
                     "import maya.cmds as cmds\nselected_objects = ['" + string_for_python + \
                     "'] \ncmds.select(selected_objects)\n\n\n\'\'\'\n" \
                     "// Mel command to select it\nselect -r " + string_for_mel + \
                     "\n\n\'\'\'\n\n\n# List of Objects:\n# " + string_for_list

    f.write(select_command)
    f.close()

    notepad_command = 'exec("notepad ' + txt_file + '");'
    mel.eval(notepad_command)


def select_hierarchy():
    """
    Adds the hierarchy of the selected object to the selection              
    """
    cmds.select(hierarchy=True)


def is_object_shape(obj):
    """
    Returns if object is a shape or not 
    
            Returns:
                is_shape (bool): Returns true if object is a shape
    """
    node_inheritance = cmds.nodeType(obj, inherited=True)
    is_shape = False
    for inheritance in node_inheritance:
        if "shape" in inheritance:
            is_shape = True
    return is_shape


def stored_list_manager(stored_list):
    """
    Loads stored list 

    Args:
        stored_list (list): list of objects (strings) to be selected
    """
    missing_elements = False
    found_elements = []
    print("#" * 32 + " Objects List " + "#" * 32)
    for obj in stored_list:
        if cmds.objExists(obj):
            print(obj)
            found_elements.append(obj)
        else:
            print(obj + " no longer exists!")
            missing_elements = True
    print("#" * 80)
    if missing_elements:
        message = 'Some elements are <span style=\"color:#FF0000;\">missing!</span>'
        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)
        message = 'Open script editor for more information.'
        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)
    else:
        cmds.inViewMessage(amg='Stored elements have been selected.', pos='botLeft', fade=True, alpha=.9)
    if stored_list:
        cmds.select(found_elements)


def parse_text_field(text_field_data):
    """
    Parses textField data 
    
    Args:
            text_field_data (string): The text provided in the textfield

    Returns:
            return_list (list): A list of strings with every work from the text field
    
    """
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


def selection_feedback(number_objects):
    """
    Prints an inViewMessage to give feedback to the user about how many objects are now selected.
    Uses the module "random" to force identical messages to appear at the same time.

    Args:
        number_objects (int): how many objects were selected.
    """
    if number_objects != 0:
        message = '<' + str(random.random()) + '><span style=\"color:#FF0000;text-decoration:underline;\">' + str(
            number_objects)

        if number_objects == 1:
            message += '</span><span style=\"color:#FFFFFF;\"> object was selected.</span>'
        else:
            message += '</span><span style=\"color:#FFFFFF;\"> objects were selected.</span>'
        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)
    else:
        cmds.inViewMessage(amg='No objects were selected.', pos='botLeft', fade=True, alpha=.9)


def build_gui_help_selection_manager():
    """ Creates Help Window """
    window_name = "build_gui_help_selection_manager"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title=script_name + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    cmds.columnLayout("main_column", p=window_name)

    # Title Text
    cmds.separator(h=12, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p="main_column")  # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")  # Title Column
    cmds.text(script_name + " Help", bgc=[.4, .4, .4], fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p="main_column")  # Empty Space

    # Body ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")
    cmds.text(l='This script allows you to update selections', align="left")
    cmds.text(l='to contain (or not) filtered elements.', align="left")
    cmds.text(l='You can also save and load previous selections.', align="left")
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.text(l='Element Name:', align="left", fn="boldLabelFont")
    cmds.text(l='This option allows you to check if the string used', align="left")
    cmds.text(l="for the object name contains or doesn't contain the", align="left")
    cmds.text(l='the provided strings (parameters).', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Element Type:', align="left", fn="boldLabelFont")
    cmds.text(l='This filter will check the type of the element to', align="left")
    cmds.text(l='determine if it should be part of the selection or not.', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Element Type > Behavior (Dropdown Menu):', align="left", fn="boldLabelFont")
    cmds.text(l='Since most elements are transforms, you can use the', align="left")
    cmds.text(l='dropdown menu "Behavior" to determine how to filter', align="left")
    cmds.text(l='the shape element (usually hidden inside the transform)', align="left")
    cmds.text(l='(You can consider transform, shape, both or ignore it) ', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Visibility State:', align="left", fn="boldLabelFont")
    cmds.text(l='Selection based on the current state of the node\'s ', align="left")
    cmds.text(l='visibility attribute.', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Outliner Color (Transform):', align="left", fn="boldLabelFont")
    cmds.text(l='Filters the option under Node > Display > Outliner Color ', align="left")
    cmds.text(l='In case you\'re unsure about the exact color, you can use ', align="left")
    cmds.text(l='the "Get" button to automatically copy a color.', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Store Selection Options: ', align="left", fn="boldLabelFont")
    cmds.text(l='Select objects and click on "Store Selection" to store', align="left")
    cmds.text(l='them for later.', align="left")
    cmds.text(l='Use the "-" and "+" buttons to add or remove elements.', align="left")
    cmds.text(l='Use the "Reset" button to clear your selection', align="left")
    cmds.separator(h=7, style='none')  # Empty Space
    cmds.text(l='You can save your selection in two ways:', align="left")
    cmds.text(l='As a set (creates a set containing selection', align="left")
    cmds.text(l='As text (creates a txt file containing  the code', align="left")
    cmds.text(l='necessary to recreate selection (as well as a list)', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Create New Selection : Uses all objects as initial selection', align="left")
    cmds.text(l='Update Current Selection : Considers only selected objects', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 140), (2, 140)], cs=[(1, 10), (2, 0)], p="main_column")
    cmds.text('Guilherme Trevisan  ')
    cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1, 1, 1])
    cmds.rowColumnLayout(nc=2, cw=[(1, 140), (2, 140)], cs=[(1, 10), (2, 0)], p="main_column")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1, 1, 1])
    cmds.separator(h=7, style='none')  # Empty Space

    # Close Button 
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")
    cmds.separator(h=10, style='none')
    cmds.button(l='OK', h=30, c=lambda args: close_help_gui())
    cmds.separator(h=8, style='none')

    # Show and Lock Window
    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/question.png')
    widget.setWindowIcon(icon)

    def close_help_gui():
        """ Function for the close button ("OK" button) """
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)

    # Help Dialog Ends Here =================================================================================


# Build UI
if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)  # Debug
    build_gui_selection_manager()
