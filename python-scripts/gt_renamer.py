"""
 GT Renamer - Script for Quickly Renaming Multiple Objects
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-06-25
 
 1.1 - 2020-07-10
 Fixed little issue when auto adding suffix to objects with multiple shapes
 
"""
import maya.cmds as cmds
import traceback
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


# Script Name:
script_name = "GT Renamer"

# Version:
script_version = "1.0";

# Auto Suffix/Prefix Strings:
transform_suffix= '_grp'
mesh_suffix= '_geo'
nurbsCurv_suffixe= '_crv'
joint_suffix= '_jnt'
locator_suffix= '_loc'
surface_suffix= '_sur'
left_prefix= 'left_'
right_prefix= 'right_'
center_prefix= 'center_'


# Main Form ============================================================================
def build_gui_renamer():
    window_name = "build_gui_renamer"
    if cmds.window(window_name, exists =True):
        cmds.deleteUI(window_name)    

    # Main GUI Start Here =================================================================================
    
    build_gui_renamer = cmds.window(window_name, title=script_name + "  v" + script_version,\
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
    cmds.button( l ="Help", bgc=(0, .5, 0), c=lambda x:build_gui_help_renamer())
    cmds.separator(h=10, style='none', p=content_main) # Empty Space

    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,10)], p=content_main)
    cmds.rowColumnLayout(nc=3, cw=[(1, 90),(2, 95),(3, 95)], cs=[(1,15)])
    cmds.radioCollection()
    selection_type_selected = cmds.radioButton( label='Selected', select=True )
    selection_type_hierarchy = cmds.radioButton( label='Hierarchy' )
    cmds.radioButton( label='All' )
    
    cmds.rowColumnLayout( nc=1, cw=[(1, 260)], cs=[(1, 0)], p=body_column)
    cmds.separator(h=5, style='none') # Empty Space
    
    # Other Tools ================
    cmds.separator(h=10)
    cmds.separator(h=5, style='none') # Empty Space
    cmds.text('Other Tools')
    cmds.separator(h=7, style='none') # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 120),(2, 120)], cs=[(1, 5),(2, 5)], p=body_column)
    cmds.button(l ="Remove First Letter", c=lambda x:start_renaming('remove_first_letter'))
    cmds.button(l ="Remove Last Letter", c=lambda x:start_renaming('remove_last_letter'))
    cmds.separator(h=7, style='none') # Empty Space
    cmds.separator(h=7, style='none') # Empty Space
    cmds.rowColumnLayout(nc=3, cw=[(1, 78),(2, 79),(3, 78)], cs=[(1, 5),(2, 5), (3, 5)], p=body_column)
    cmds.button(l ="U-Case", c=lambda x:start_renaming('uppercase_names'))
    cmds.button(l ="Capitalize", c=lambda x:start_renaming('capitalize_names'))
    cmds.button(l ="L-Case", c=lambda x:start_renaming('lowercase_names'))
    cmds.separator(h=7, style='none') # Empty Space
    cmds.rowColumnLayout( nc=1, cw=[(1, 260)], cs=[(1, 0)], p=body_column)
    
    # Rename and Number ================
    cmds.separator(h=10)
    cmds.separator(h=5, style='none') # Empty Space
    cmds.text('Rename and Number')
    cmds.separator(h=7, style='none') # Empty Space
    
    cmds.rowColumnLayout( nc=2, cw=[(1, 80),(2, 150)], cs=[(1, 5),(2, 0)], p=body_column)
    cmds.text('Rename:')
    rename_number_textfield = cmds.textField(placeholderText = 'new_name', enterCommand=lambda x:start_renaming('rename_and_number'))
    
    cmds.separator(h=7, style='none') # Empty Space
    
    cmds.rowColumnLayout( nc=4, cw=[(1, 50),(2, 40),(3, 60),(4, 40)], cs=[(1, 20),(2, 0),(3, 10),(4, 0)], p=body_column)
    cmds.text('Start #:')
    start_number_textfield = cmds.textField(text = '1', enterCommand=lambda x:start_renaming('rename_and_number'))
    cmds.text('Padding:')
    padding_number_textfield = cmds.textField(text = '2', enterCommand=lambda x:start_renaming('rename_and_number'))
        
    cmds.rowColumnLayout( nc=1, cw=[(1, 240)], cs=[(1, 10)], p=body_column)
    cmds.separator(h=10, style='none') # Empty Space
    cmds.button(l ="Rename and Number", bgc=(.6, .8, .6), c=lambda x:start_renaming('rename_and_number'))
    cmds.separator(h=10, style='none') # Empty Space
    
    
    # Prefix and Suffix ================
    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 0)], p=body_column)
    cmds.separator(h=10)
    cmds.separator(h=5, style='none') # Empty Space
    cmds.text('Prefix and Suffix')
    cmds.separator(h=7, style='none') # Empty Space
    
    cmds.rowColumnLayout( nc=4, cw=[(1, 50),(2, 50),(3, 50),(4, 85)], cs=[(1, 0),(2, 0),(3, 0),(4, 10)], p=body_column)
    cmds.text('Prefix:')
    cmds.radioCollection()
    add_prefix_auto = cmds.radioButton( label='Auto', select=True, cc=lambda x:update_prefix_suffix_options() ) 
    cmds.radioButton( label='Input', cc=lambda x:update_prefix_suffix_options() ) 
    prefix_textfield = cmds.textField(placeholderText = 'prefix_', enterCommand=lambda x:start_renaming('add_prefix'), en=False)
    
    cmds.text('Suffix:')
    cmds.radioCollection()
    add_suffix_auto = cmds.radioButton( label='Auto', select=True, cc=lambda x:update_prefix_suffix_options() ) 
    cmds.radioButton( label='Input', cc=lambda x:update_prefix_suffix_options() ) 
    suffix_textfield = cmds.textField(placeholderText = '_suffix', enterCommand=lambda x:start_renaming('add_suffix'), en=False)
    
    cmds.separator(h=10, style='none') # Empty Space
    
    cmds.rowColumnLayout( nc=6, cw=[(1, 40),(2, 40),(3, 40),(4, 40),(5, 40),(6, 40)], cs=[(1, 5),(2, 0),(3, 0),(4, 0),(5, 0),(6, 0)], p=body_column)
    cmds.text('Group', font='smallObliqueLabelFont')
    cmds.text('Mesh', font='smallObliqueLabelFont')
    cmds.text('Nurbs', font='smallObliqueLabelFont')
    cmds.text('Joint', font='smallObliqueLabelFont')
    cmds.text('Locator', font='smallObliqueLabelFont')
    cmds.text('Surface', font='smallObliqueLabelFont')
    transform_suffix_textfield = cmds.textField(text = transform_suffix , enterCommand=lambda x:start_renaming('add_suffix'))
    mesh_suffix_textfield = cmds.textField(text = mesh_suffix, enterCommand=lambda x:start_renaming('add_suffix'))
    nurbsCurv_suffix_textfield = cmds.textField(text = nurbsCurv_suffixe, enterCommand=lambda x:start_renaming('add_suffix'))
    joint_suffix_textfield = cmds.textField(text = joint_suffix, enterCommand=lambda x:start_renaming('add_suffix'))
    locator_suffix_textfield = cmds.textField(text = locator_suffix, enterCommand=lambda x:start_renaming('add_suffix'))
    surface_suffix_textfield = cmds.textField(text = surface_suffix, enterCommand=lambda x:start_renaming('add_suffix'))
    
    cmds.separator(h=5, style='none') # Empty Space
    
    cmds.rowColumnLayout( nc=3, cw=[(1, 80),(2, 80),(3, 80)], cs=[(1, 5),(2, 0),(3, 0)], p=body_column)
    cmds.text('Left', font='smallObliqueLabelFont')
    cmds.text('Center', font='smallObliqueLabelFont')
    cmds.text('Right', font='smallObliqueLabelFont')
    left_prefix_textfield = cmds.textField(text = left_prefix , enterCommand=lambda x:start_renaming('add_suffix'))
    center_prefix_textfield = cmds.textField(text = center_prefix, enterCommand=lambda x:start_renaming('add_suffix'))
    right_prefix_textfield = cmds.textField(text = right_prefix, enterCommand=lambda x:start_renaming('add_suffix'))
    
    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 120),(2, 120)], cs=[(1, 5),(2, 5)], p=body_column)
    cmds.button(l ="Add Prefix", bgc=(.6, .8, .6), c=lambda x:start_renaming('add_prefix'))
    cmds.button(l ="Add Suffix", bgc=(.6, .8, .6), c=lambda x:start_renaming('add_suffix'))
    cmds.separator(h=10, style='none') # Empty Space
    
    
    # Search and Replace ==================
    cmds.rowColumnLayout( nc=1, cw=[(1, 260)], cs=[(1, 0)], p=body_column)
    cmds.separator(h=10)
    cmds.separator(h=5, style='none') # Empty Space
    cmds.text('Search and Replace')
    cmds.separator(h=7, style='none') # Empty Space
    
    cmds.rowColumnLayout( nc=2, cw=[(1, 70),(2, 150)], cs=[(1, 10),(2, 0)], p=body_column)
    cmds.text('Search:')
    search_textfield = cmds.textField(placeholderText = 'search_text', enterCommand=lambda x:start_renaming('search_and_replace'))
    
    cmds.text('Replace:')
    replace_textfield = cmds.textField(placeholderText = 'replace_text', enterCommand=lambda x:start_renaming('search_and_replace'))

    cmds.rowColumnLayout( nc=1, cw=[(1, 240)], cs=[(1, 10)], p=body_column)
    cmds.separator(h=15, style='none') # Empty Space
    cmds.button(l ="Search and Replace", bgc=(.6, .8, .6), c=lambda x:start_renaming('search_and_replace'))
    cmds.separator(h=15, style='none') # Empty Space
       
       
    def update_prefix_suffix_options():
        if cmds.radioButton(add_prefix_auto, q=True, select=True):
            prefix_auto_textfields = True
            prefix_input_textfields = False
        else:
            prefix_auto_textfields = False
            prefix_input_textfields = True
            
        if cmds.radioButton(add_suffix_auto, q=True, select=True):
            suffix_auto_textfields = True
            suffix_input_textfields = False
        else:
            suffix_auto_textfields = False
            suffix_input_textfields = True
    
        cmds.textField(transform_suffix_textfield, e=True, en=suffix_auto_textfields)
        cmds.textField(mesh_suffix_textfield, e=True, en=suffix_auto_textfields)
        cmds.textField(nurbsCurv_suffix_textfield, e=True, en=suffix_auto_textfields)
        cmds.textField(joint_suffix_textfield, e=True, en=suffix_auto_textfields)
        cmds.textField(locator_suffix_textfield, e=True, en=suffix_auto_textfields)
        cmds.textField(surface_suffix_textfield, e=True, en=suffix_auto_textfields)
        
        cmds.textField(left_prefix_textfield, e=True, en=prefix_auto_textfields)
        cmds.textField(center_prefix_textfield, e=True, en=prefix_auto_textfields)
        cmds.textField(right_prefix_textfield, e=True, en=prefix_auto_textfields)
        
        cmds.textField(suffix_textfield, e=True, en=suffix_input_textfields)
        cmds.textField(prefix_textfield, e=True, en=prefix_input_textfields)
       
       
    def start_renaming(operation):
        
        current_selection = cmds.ls(selection=True)
        is_operation_valid = True
        
        # Manage type of selection
        if cmds.radioButton(selection_type_selected, q=True, select=True):
            selection = cmds.ls(selection=True)
        elif cmds.radioButton(selection_type_hierarchy, q=True, select=True):
            cmds.select(hierarchy=True)
            selection = cmds.ls(selection=True)
            cmds.select(current_selection)
        else:
            selection = cmds.ls()
            
        
        # Check if something is selected
        if len(selection) == 0:
            cmds.warning('Nothing is selected!')
            is_operation_valid = False

        # Start Renaming Operation
        if operation == 'search_and_replace':
                    search_string = cmds.textField(search_textfield, q=True, text=True)
                    replace_string = cmds.textField(replace_textfield, q=True, text=True)
                    rename_search_replace(selection, search_string, replace_string)
        elif operation == 'rename_and_number':
            new_name = cmds.textField(rename_number_textfield, q=True, text=True)
            
            if cmds.textField(start_number_textfield, q=True, text=True).isdigit() and cmds.textField(padding_number_textfield, q=True, text=True).isdigit():
                start_number = int(cmds.textField(start_number_textfield, q=True, text=True))
                padding_number = int(cmds.textField(padding_number_textfield, q=True, text=True))
                rename_and_number(selection, new_name, start_number, padding_number)
            else:
                cmds.warning('Start Number and Padding Number must be digits (numbers)')
        elif operation == 'add_prefix':          
            prefix_list = []
            if cmds.radioButton(add_prefix_auto, q=True, select=True):
                left_prefix_input = cmds.textField(left_prefix_textfield, q=True, text=True)
                center_prefix_input = cmds.textField(center_prefix_textfield, q=True, text=True)
                right_prefix_input = cmds.textField(right_prefix_textfield, q=True, text=True)
                prefix_list.append(left_prefix_input)
                prefix_list.append(center_prefix_input)
                prefix_list.append(right_prefix_input)
            else:
                new_prefix = cmds.textField(prefix_textfield, q=True, text=True)
                prefix_list.append(new_prefix)
                
            rename_add_prefix(selection, prefix_list)
            
        elif operation == 'add_suffix':
            
            suffix_list = []
            if cmds.radioButton(add_suffix_auto, q=True, select=True):
                transform_suffix_input = cmds.textField(transform_suffix_textfield, q=True, text=True)
                mesh_suffix_input = cmds.textField(mesh_suffix_textfield, q=True, text=True)
                nurbsCurv_suffix_input = cmds.textField(nurbsCurv_suffix_textfield, q=True, text=True)
                joint_suffix_input = cmds.textField(joint_suffix_textfield, q=True, text=True)
                locator_suffix_input = cmds.textField(locator_suffix_textfield, q=True, text=True)
                surface_suffix_input = cmds.textField(surface_suffix_textfield, q=True, text=True)
                suffix_list.append(transform_suffix_input)
                suffix_list.append(mesh_suffix_input)
                suffix_list.append(nurbsCurv_suffix_input)
                suffix_list.append(joint_suffix_input)
                suffix_list.append(locator_suffix_input)
                suffix_list.append(surface_suffix_input)
            else:
                new_suffix = cmds.textField(suffix_textfield, q=True, text=True)
                suffix_list.append(new_suffix)
                
            rename_add_suffix(selection, suffix_list)
        elif operation == 'remove_first_letter':
            remove_first_letter(selection)
        elif operation == 'remove_last_letter':
            remove_last_letter(selection)
        elif operation == 'uppercase_names':
            rename_uppercase(selection)
        elif operation == 'capitalize_names':
            rename_capitalize(selection)
        elif operation == 'lowercase_names':
            rename_lowercase(selection)
    
        # Undo function
        if is_operation_valid:
            cmds.undoInfo(openChunk=True, chunkName=script_name) 
            try:
                pass
            except Exception as e:
                print traceback.format_exc()
                cmds.error("## Error, see script editor: %s" % e)
            finally:
                cmds.undoInfo(closeChunk=True, chunkName=script_name)
           
    
    # Show and Lock Window
    cmds.showWindow(build_gui_renamer)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/renamePreset.png')
    widget.setWindowIcon(icon)
    

'''
Create Help GUI

'''
def build_gui_help_renamer():
    window_name = "build_gui_help_renamer"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title= script_name + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1,1])

    main_column = cmds.columnLayout(p= window_name)
   
    # Title Text
    cmds.separator(h=12, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p=main_column) # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column) # Title Column
    cmds.text(script_name + " Help", bgc=[0,.5,0],  fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p=main_column) # Empty Space

    # Body ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column)
    cmds.text(l='Script for renaming multiple objects.', align="center")
    cmds.separator(h=15, style='none') # Empty Space
    
    cmds.text(l='Modes:', align="center", fn="tinyBoldLabelFont")
    cmds.text(l='- Selected: uses selected objects when renaming.', align="left", font='smallPlainLabelFont')
    cmds.text(l='- Hierarchy: uses hierarchy when renaming.,', align="left", font='smallPlainLabelFont')
    cmds.text(l='- All: uses everything in the scene (even hidden nodes)', align="left", font='smallPlainLabelFont')
    
    cmds.separator(h=10, style='none') # Empty Space
    
    cmds.text(l='Other Tools:', align="center", fn="tinyBoldLabelFont")
    cmds.text(l='- Remove First Letter: removes the first letter of a name.', align="left", font='smallPlainLabelFont')
    cmds.text(l='If the next character is a number, it will be deleted.', align="left", font='smallPlainLabelFont')
    cmds.text(l='- Remove Last Letter: removes the last letter of a name,', align="left", font='smallPlainLabelFont')
    cmds.text(l='- U-Case: makes all letters uppercase', align="left", font='smallPlainLabelFont')
    cmds.text(l='- Capitalize: makes the 1st letter of every word uppercase.', align="left", font='smallPlainLabelFont')
    cmds.text(l='- L-Case: makes all letters lowercase', align="left", font='smallPlainLabelFont')
    
    cmds.separator(h=10, style='none') # Empty Space
    
    cmds.text(l='Rename and Number:', align="center", fn="tinyBoldLabelFont")
    cmds.text(l='Renames selected objects and number them.', align="left", font='smallPlainLabelFont')
    cmds.text(l='- Start # : first number when countaing the new names.', align="left", font='smallPlainLabelFont')
    cmds.text(l='- Padding : how many zeros before the number. e.g. "001"', align="left", font='smallPlainLabelFont')
    cmds.separator(h=10, style='none') # Empty Space
    
    cmds.text(l='Prefix and Suffix:', align="center", fn="tinyBoldLabelFont")
    cmds.text(l='Prefix: adds a string in front of a name.', align="left", font='smallPlainLabelFont')
    cmds.text(l='Suffix: adds a string at the end of a name.', align="left", font='smallPlainLabelFont')
    cmds.separator(h=5, style='none') # Empty Space
    cmds.text(l=' - Auto: Uses the provided strings to automatically name', align="left", font='smallPlainLabelFont')
    cmds.text(l='objects according to their type or position.', align="left", font='smallPlainLabelFont')
    cmds.text(l='1st example: a mesh would automatically receive "_geo"', align="left", font='smallPlainLabelFont')
    cmds.text(l='2nd example: an object in positive side of X, would', align="left", font='smallPlainLabelFont')
    cmds.text(l='automatically receive "left_"', align="left", font='smallPlainLabelFont')
    cmds.separator(h=5, style='none') # Empty Space
    cmds.text(l=' - Input: uses the provided text as a prefix or suffix.', align="left", font='smallPlainLabelFont')
    cmds.separator(h=10, style='none') # Empty Space
    
    cmds.text(l='Search and Replace:', align="center", fn="tinyBoldLabelFont")
    cmds.text(l='Uses the well-known method of search and replace', align="left", font='smallPlainLabelFont')
    cmds.text(l='to rename objects.', align="left", font='smallPlainLabelFont')
    cmds.separator(h=10, style='none') # Empty Space
    
    cmds.rowColumnLayout(nc=2, cw=[(1, 140),(2, 140)], cs=[(1,10),(2, 0)], p=main_column)
    cmds.text('Guilherme Trevisan  ')
    cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1,1,1])
    cmds.rowColumnLayout(nc=2, cw=[(1, 140),(2, 140)], cs=[(1,10),(2, 0)], p=main_column)
    cmds.separator(h=10, style='none') # Empty Space
    cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1,1,1])
    cmds.separator(h=7, style='none') # Empty Space
    
    # Close Button 
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column)
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
   

'''
Search and Replace Function for String

@param obj - object to extract short name
@param search - what to search for
@param replace - what to replace it with
'''
def string_replace(string, search, replace):
    if string == '':
        return ''
    replace_string = string.replace(search, replace)    
    return replace_string


'''
Get the name of the objects without its path (Maya returns full path if name is not unique)

@param obj - object to extract short name
'''
def get_short_name(obj):
    if obj == '':
        return ''
    split_path = obj.split('|')
    if len(split_path) >= 1:
        short_name = split_path[len(split_path)-1]
    return short_name


'''
Rename Uppercase

@param obj_list - a list of objects to be renamed
'''
def rename_uppercase(obj_list):
    to_rename = []
    
    for obj in obj_list:
        object_short_name = get_short_name(obj)
        new_name = object_short_name.upper()
        if cmds.objExists(obj) and 'shape' not in cmds.nodeType(obj, inherited=True):
            to_rename.append([obj,new_name])
            
    for pair in reversed(to_rename):
        if cmds.objExists(pair[0]):
            cmds.rename(pair[0], pair[1])

'''
Rename Lowercase

@param obj_list - a list of objects to be renamed
'''
def rename_lowercase(obj_list):
    to_rename = []
    
    for obj in obj_list:
        object_short_name = get_short_name(obj)
        new_name = object_short_name.lower()
        if cmds.objExists(obj) and 'shape' not in cmds.nodeType(obj, inherited=True):
            to_rename.append([obj,new_name])
            
    for pair in reversed(to_rename):
        if cmds.objExists(pair[0]):
            cmds.rename(pair[0], pair[1])

'''
Rename Capitalize

@param obj_list - a list of objects to be renamed
'''
def rename_capitalize(obj_list):
    to_rename = []
    
    for obj in obj_list:
        object_short_name = get_short_name(obj)
        object_short_name_split = object_short_name.split('_')
        
        if len(object_short_name_split) > 1:
            new_name = ''
            for name in object_short_name_split:
                new_name = new_name + name.capitalize() + '_'
            new_name = new_name[:-1]
        else:
            new_name = object_short_name.capitalize() 
        
        if cmds.objExists(obj) and 'shape' not in cmds.nodeType(obj, inherited=True):
            to_rename.append([obj,new_name])
            
    for pair in reversed(to_rename):
        if cmds.objExists(pair[0]):
            cmds.rename(pair[0], pair[1])


'''
Remove First Letter

@param obj_list - a list of objects to be renamed
'''
def remove_first_letter(obj_list):
    to_rename = []
    
    for obj in obj_list:
        object_short_name = get_short_name(obj)
        is_char = False
        
        if len(object_short_name) > 1:
            new_name = object_short_name[1:]
        else:
            is_char = True
            new_name = object_short_name
            cmds.warning('"' + object_short_name + '" is just one letter. You can\'t remove it.')
        
        if cmds.objExists(obj) and 'shape' not in cmds.nodeType(obj, inherited=True) and is_char == False:
            to_rename.append([obj,new_name])
            
    for pair in reversed(to_rename):
        if cmds.objExists(pair[0]):
            cmds.rename(pair[0], pair[1])

'''
Remove Last Letter

@param obj_list - a list of objects to be renamed
'''
def remove_last_letter(obj_list):
    to_rename = []
    
    for obj in obj_list:
        object_short_name = get_short_name(obj)
        is_char = False
        
        if len(object_short_name) > 1:
            new_name = object_short_name[:-1]
        else:
            is_char = True
            new_name = object_short_name
            cmds.warning('"' + object_short_name + '" is just one letter. You can\'t remove it.')
        
        if cmds.objExists(obj) and 'shape' not in cmds.nodeType(obj, inherited=True) and is_char == False:
            to_rename.append([obj,new_name])
            
    for pair in reversed(to_rename):
        if cmds.objExists(pair[0]):
            cmds.rename(pair[0], pair[1])

'''
Rename Using Search and Replace

@param obj_list - a list of objects to be renamed
@param search - what to search for
@param replace - what to replace it with
'''
def rename_search_replace(obj_list, search, replace):
    if search == '':
        cmds.warning('The search string must not be empty.')
    else: 
        to_rename = []
        
        for obj in obj_list:
            object_short_name = get_short_name(obj)
            new_name = string_replace(str(object_short_name), search, replace)
            if cmds.objExists(obj) and 'shape' not in cmds.nodeType(obj, inherited=True):
                to_rename.append([obj,new_name])
                
        for pair in reversed(to_rename):
            if cmds.objExists(pair[0]):
                cmds.rename(pair[0], pair[1])
        
'''
Rename Objects and Add Number (With Padding)

@param obj_list - a list of objects to be renamed
@param new_name - a new name to rename the objects
@param start_number - what number to start counting from
@param padding_number - how many zeroes it will add before numbers
'''
def rename_and_number(obj_list, new_name, start_number, padding_number):
    if new_name == '':
        cmds.warning('The provided string must not be empty.')
    else: 
        to_rename = []
        count = start_number
        
        for obj in obj_list:
            object_short_name = get_short_name(obj)
            new_name_and_number = new_name + str(count).zfill(padding_number)
            if cmds.objExists(obj) and 'shape' not in cmds.nodeType(obj, inherited=True):
                to_rename.append([obj,new_name_and_number])
                count += 1
            
        print(to_rename)
        for pair in reversed(to_rename):
            if cmds.objExists(pair[0]):
                cmds.rename(pair[0], pair[1])


'''
Add Prefix

@param obj_list - a list of objects to be renamed with a new prefix
@param new_prefix_list - a list of Prefix strings, if just one it assumes that it's a manual input, if more it automates.
'''
def rename_add_prefix(obj_list, new_prefix_list):
    
    auto_prefix = True
    if len(new_prefix_list) == 1:
        auto_prefix = False
        new_prefix = new_prefix_list[0]
    
    if auto_prefix == False and new_prefix == '':
        cmds.warning('Prefix Input must not be empty.')
    else: 
        to_rename = []
        for obj in obj_list:
            if auto_prefix and 'shape' not in cmds.nodeType(obj, inherited=True):
                obj_x_pos = cmds.xform(obj, piv=True , q=True , ws=True)[0]
                if obj_x_pos > 0.0001:
                    new_prefix= new_prefix_list[0]
                elif obj_x_pos < -0.0001:
                    new_prefix = new_prefix_list[2]
                else:
                    new_prefix = new_prefix_list[1]
                    
            object_short_name = get_short_name(obj)
            
            if object_short_name.startswith(new_prefix):
                new_name_and_prefix = object_short_name
            else:
                new_name_and_prefix = new_prefix + object_short_name
            
            print(cmds.nodeType(obj, inherited=True))
            if cmds.objExists(obj) and 'shape' not in cmds.nodeType(obj, inherited=True) :
                to_rename.append([obj,new_name_and_prefix])
            
        print(to_rename)
        for pair in reversed(to_rename):
            if cmds.objExists(pair[0]):
                cmds.rename(pair[0], pair[1])
                
'''
Add Suffix

@param obj_list - a list of objects to be renamed with a new suffix
@param new_suffix_list - a list of suffix strings, if just one it assumes that it's a manual input, if more it automates.
'''
def rename_add_suffix(obj_list, new_suffix_list):
    auto_suffix = True
    
    if len(new_suffix_list) == 1:
        auto_suffix = False
        new_suffix = new_suffix_list[0]
    
    if auto_suffix == False and new_suffix == '':
        cmds.warning('Suffix Input must not be empty.')
    else: 
        to_rename = []
        for obj in obj_list:
            if auto_suffix and 'shape' not in cmds.nodeType(obj, inherited=True):
                object_type = ''
                object_shape = cmds.listRelatives(obj, shapes=True, fullPath=True) or []

                if len(object_shape) > 0:
                    object_type = cmds.objectType(object_shape[0])
                else:
                    object_type = cmds.objectType(obj)
                    
                if object_type == 'transform':
                    new_suffix = new_suffix_list[0]
                elif object_type == 'mesh':
                    new_suffix = new_suffix_list[1]
                elif object_type == 'nurbsCurve':
                    new_suffix = new_suffix_list[2]
                elif object_type == 'joint':
                    new_suffix = new_suffix_list[3]
                elif object_type == 'locator':
                    new_suffix = new_suffix_list[4]
                elif object_type == 'nurbsSurface':
                    new_suffix = new_suffix_list[5]
                else:
                    new_suffix =''
                        
            object_short_name = get_short_name(obj)
            
            if object_short_name.endswith(new_suffix):
                new_name_and_suffix = object_short_name
            else:
                new_name_and_suffix = object_short_name + new_suffix
            
            if cmds.objExists(obj) and 'shape' not in cmds.nodeType(obj, inherited=True) :
                to_rename.append([obj,new_name_and_suffix])
            
        for pair in reversed(to_rename):
            if cmds.objExists(pair[0]):
                cmds.rename(pair[0], pair[1])

        

'''
Rename Objects and Add Letter (Alphabetical Order) - Work in Progress

@param obj_list - a list of objects to be renamed with a new suffix
@param new_name - .
'''
def rename_and_alphabetize(obj_list, new_name):
    alphabet_array = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]
    print([len(alphabet_array)])
    current_letter_index = 0
    multiple_letter_patch = ''
    multiple_letter_index = 0
    for obj in obj_list:
        object_short_name = get_short_name(obj)
        new_name_and_letter = new_name + multiple_letter_patch + alphabet_array[current_letter_index]
        current_letter_index += 1
        if current_letter_index == 25:
            multiple_letter_patch = current_letter_index[multiple_letter_index]
        cmds.rename(obj, new_name_and_letter)
               


# Build UI
build_gui_renamer()