"""
 GT Renamer - Script for Quickly Renaming Multiple Objects
 github.com/TrevisanGMW/gt-tools - 2020-06-25
 
 1.1 - 2020-08-03
 Fixed little issue when auto adding suffix to objects with multiple shapes.
 Added persistent settings.
 Fixed "all" option, so functions handles errors when trying to rename readOnly nodes.
 Added list of nodes to ignore.
 Fixed issue where auto prefix would sometimes raise an error when getting position using xform.
 
 1.2 - 2020-10-17
 Fixed an issue where the manual input for prefixes and suffixes wouldn't work.
 
 1.3 - 2020-10-23
 Added feedback to how many objects were renamed. (in view messages)
 Added persistent settings for selection type
 Added a check to ignore renaming when a new name is identical to current
 
 1.4 - 2020-11-15
 Changed the color and text for a few UI elements
 Removed a few unnecessary lines
 
 1.5 - 2021-05-08
 Made script compatible with Python 3 (Maya 2022+)
 
 Todo:
    Add persistent settings for the selection type (Selected, Hierarchy, All)
    Consider adding more types to auto suffix.
    Add more direction planes to the auto prefix option.
    Add alphabetize option (already started; function at the bottom) .
    Test with more complex scenes using the "all" option.
    Update help menu.
    Auto rename shaders and file nodes.
 
"""
import maya.cmds as cmds
import traceback
import random
import copy
import sys
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
script_version = "1.5.0"

# Python Version
python_version = sys.version_info.major

# Auto Suffix/Prefix Strings and other settings:
gt_renamer_settings = {'transform_suffix': '_grp',
                       'mesh_suffix': '_geo',
                       'nurbs_curv_suffix': '_crv',
                       'joint_suffix': '_jnt',
                       'locator_suffix': '_loc',
                       'surface_suffix': '_sur',
                       'left_prefix': 'left_',
                       'right_prefix': 'right_',
                       'center_prefix': 'center_',
                       'def_starting_number': '1',
                       'def_padding_number': '2',
                       'selection_type': '0',
                       'error_message': 'Some objects were not renamed. Open the script editor to see why.',
                       'nodes_to_ignore': ['defaultRenderLayer', 'renderLayerManager', 'defaultLayer', 'layerManager',
                                           'poseInterpolatorManager', 'shapeEditorManager', 'side', 'front', 'top',
                                           'persp', 'lightLinker1', 'strokeGlobals', 'globalCacheControl',
                                           'hyperGraphLayout', 'hyperGraphInfo', 'ikSystem',
                                           'defaultHardwareRenderGlobals', 'characterPartition',
                                           'hardwareRenderGlobals', 'defaultColorMgtGlobals',
                                           'defaultViewColorManager', 'defaultObjectSet', 'defaultLightSet',
                                           'defaultResolution', 'defaultRenderQuality', 'defaultRenderGlobals',
                                           'dof1', 'shaderGlow1', 'initialMaterialInfo', 'initialParticleSE',
                                           'initialShadingGroup', 'particleCloud1', 'standardSurface1', 'lambert1',
                                           'defaultTextureList1', 'lightList1', 'defaultRenderingList1',
                                           'defaultRenderUtilityList1', 'postProcessList1', 'defaultShaderList1',
                                           'defaultLightList1', 'renderGlobalsList1', 'renderPartition',
                                           'hardwareRenderingGlobals', 'sequenceManager1', 'time1'],
                       'node_types_to_ignore': ['objectRenderFilter', 'objectTypeFilter', 'dynController',
                                                'objectMultiFilter', 'selectionListOperator']
                       }

# Store Default Values for Resetting
gt_renamer_settings_default_values = copy.deepcopy(gt_renamer_settings)


def get_persistent_settings_renamer():
    """ 
    Checks if persistent settings for GT Renamer exists and transfer them to the settings variables.
    It assumes that persistent settings were stored using the cmds.optionVar function.
    """

    stored_transform_suffix_exists = cmds.optionVar(exists="gt_renamer_transform_suffix")
    stored_mesh_suffix_exists = cmds.optionVar(exists="gt_renamer_mesh_suffix")
    stored_nurbs_curv_suffix_exists = cmds.optionVar(exists="gt_renamer_nurbs_curve_suffix")
    stored_joint_suffix_exists = cmds.optionVar(exists="gt_renamer_joint_suffix")
    stored_locator_suffix_exists = cmds.optionVar(exists="gt_renamer_locator_suffix")
    stored_surface_suffix_exists = cmds.optionVar(exists="gt_renamer_surface_suffix")
    stored_left_prefix_exists = cmds.optionVar(exists="gt_renamer_left_prefix")
    stored_right_prefix_exists = cmds.optionVar(exists="gt_renamer_right_prefix")
    stored_center_prefix_exists = cmds.optionVar(exists="gt_renamer_center_prefix")
    stored_def_starting_number_exists = cmds.optionVar(exists="gt_renamer_def_starting_number")
    stored_def_padding_number_exists = cmds.optionVar(exists="gt_renamer_def_padding_number")
    stored_selection_type_exists = cmds.optionVar(exists="gt_renamer_selection_type")
    
    if stored_transform_suffix_exists:
        gt_renamer_settings['transform_suffix'] = str(cmds.optionVar(q="gt_renamer_transform_suffix"))
    
    if stored_mesh_suffix_exists:
        gt_renamer_settings['mesh_suffix'] = str(cmds.optionVar(q="gt_renamer_mesh_suffix"))
        
    if stored_nurbs_curv_suffix_exists:
        gt_renamer_settings['nurbs_curv_suffix'] = str(cmds.optionVar(q="gt_renamer_nurbs_curve_suffix"))
        
    if stored_joint_suffix_exists:
        gt_renamer_settings['joint_suffix'] = str(cmds.optionVar(q="gt_renamer_joint_suffix"))
        
    if stored_locator_suffix_exists:
        gt_renamer_settings['locator_suffix'] = str(cmds.optionVar(q="gt_renamer_locator_suffix"))
        
    if stored_surface_suffix_exists:
        gt_renamer_settings['surface_suffix'] = str(cmds.optionVar(q="gt_renamer_surface_suffix"))
        
    if stored_left_prefix_exists:
        gt_renamer_settings['left_prefix'] = str(cmds.optionVar(q="gt_renamer_left_prefix"))
        
    if stored_right_prefix_exists:
        gt_renamer_settings['right_prefix'] = str(cmds.optionVar(q="gt_renamer_right_prefix"))
        
    if stored_center_prefix_exists:
        gt_renamer_settings['center_prefix'] = str(cmds.optionVar(q="gt_renamer_center_prefix"))
        
    if stored_def_starting_number_exists:
        gt_renamer_settings['def_starting_number'] = str(cmds.optionVar(q="gt_renamer_def_starting_number"))
        
    if stored_def_padding_number_exists:
        gt_renamer_settings['def_padding_number'] = str(cmds.optionVar(q="gt_renamer_def_padding_number"))
      
    if stored_selection_type_exists:
        gt_renamer_settings['selection_type'] = str(cmds.optionVar(q="gt_renamer_selection_type"))
    

def set_persistent_settings_renamer(option_var_name, option_var_string):
    """ 
    Stores persistent settings for GT Renamer.
    It assumes that persistent settings were stored using the cmds.optionVar function.
    
        Parameters:
                option_var_name (string): name of the optionVar string. Must start with script name + name of the variable
                option_var_string (string): string to be stored under the option_var_name
                    
    """
    
    if option_var_string != '' and option_var_name != '':
        cmds.optionVar( sv=(str(option_var_name), str(option_var_string)))
    

def reset_persistent_settings_renamer():
    """ Resets persistent settings for GT Renamer """
    cmds.optionVar(remove='gt_renamer_transform_suffix')
    cmds.optionVar(remove='gt_renamer_mesh_suffix')
    cmds.optionVar(remove='gt_renamer_nurbs_curve_suffix')
    cmds.optionVar(remove='gt_renamer_joint_suffix')
    cmds.optionVar(remove='gt_renamer_locator_suffix')
    cmds.optionVar(remove='gt_renamer_surface_suffix')
    cmds.optionVar(remove='gt_renamer_left_prefix')
    cmds.optionVar(remove='gt_renamer_right_prefix')
    cmds.optionVar(remove='gt_renamer_center_prefix')
    cmds.optionVar(remove='gt_renamer_def_starting_number')
    cmds.optionVar(remove='gt_renamer_def_padding_number')
    cmds.optionVar(remove='gt_renamer_selection_type')
    
    for def_value in gt_renamer_settings_default_values:
        for value in gt_renamer_settings:
            if def_value == value:
                gt_renamer_settings[value] = gt_renamer_settings_default_values[def_value]

    get_persistent_settings_renamer()
    build_gui_renamer()
    cmds.warning('Persistent settings for ' + script_name + ' were cleared.')
    

# Renamer UI ============================================================================
def build_gui_renamer():
    """ Builds the UI for GT Renamer """
    window_name = "build_gui_renamer"
    if cmds.window(window_name, exists =True):
        cmds.deleteUI(window_name)    

    # ===================================================================================
    
    build_gui_renamer = cmds.window(window_name, title=script_name + '  (v' + script_version+ ')',
                                    titleBar=True, mnb=False, mxb=False, sizeable =True)
    
    cmds.window(window_name, e=True, s=True, wh=[1,1])
    
    content_main = cmds.columnLayout()

    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 10)], p=content_main)  # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 200), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)], p=content_main)
    cmds.text(" ", bgc=title_bgc_color)  # Tiny Empty Green Space
    cmds.text(script_name, bgc=title_bgc_color,  fn="boldLabelFont", align="left")
    cmds.button( l ="Help", bgc=title_bgc_color, c=lambda x:build_gui_help_renamer())
    cmds.separator(h=10, style='none', p=content_main)  # Empty Space

    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,10)], p=content_main)
    cmds.rowColumnLayout(nc=3, cw=[(1, 90),(2, 95),(3, 95)], cs=[(1,15)])
    selection_type_rc = cmds.radioCollection()
    selection_type_selected = cmds.radioButton( label='Selected', select=True, cc=lambda x:store_selection_type_persistent_settings())
    selection_type_hierarchy = cmds.radioButton( label='Hierarchy', cc=lambda x:store_selection_type_persistent_settings())
    selection_type_all = cmds.radioButton( label='All', cc=lambda x:store_selection_type_persistent_settings())
    
    def store_selection_type_persistent_settings():
        """ Stores current state of seletion type as persistent settings """
        set_persistent_settings_renamer('gt_renamer_selection_type', cmds.radioButton(cmds.radioCollection(selection_type_rc, q=True, select=True), q=True, label=True))
        
    # Set Persistent Settings for Selection Type
    if gt_renamer_settings.get('selection_type') == 'Hierarchy':
        cmds.radioCollection(selection_type_rc, e=True, select=selection_type_hierarchy)
    elif gt_renamer_settings.get('selection_type') == 'All':
        cmds.radioCollection(selection_type_rc, e=True, select=selection_type_all)
    else:
        cmds.radioCollection(selection_type_rc, e=True, select=selection_type_selected)
    
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
    rename_number_textfield = cmds.textField(placeholderText = 'new_name', enterCommand=lambda x: start_renaming('rename_and_number'))
    
    cmds.separator(h=7, style='none') # Empty Space
    
    cmds.rowColumnLayout( nc=4, cw=[(1, 50),(2, 40),(3, 60),(4, 40)], cs=[(1, 20),(2, 0),(3, 10),(4, 0)], p=body_column)
    cmds.text('Start #:')
    start_number_textfield = cmds.textField(text = gt_renamer_settings.get('def_starting_number'),
                                            enterCommand=lambda x:start_renaming('rename_and_number'),
                                            cc=lambda x: set_persistent_settings_renamer('gt_renamer_def_starting_number', cmds.textField(start_number_textfield, q=True, text=True)))
    cmds.text('Padding:')
    padding_number_textfield = cmds.textField(text = gt_renamer_settings.get('def_padding_number'), \
                                              enterCommand=lambda x:start_renaming('rename_and_number'), \
                                              cc=lambda x: set_persistent_settings_renamer('gt_renamer_def_padding_number', cmds.textField(padding_number_textfield, q=True, text=True)))
        
    cmds.rowColumnLayout( nc=1, cw=[(1, 240)], cs=[(1, 10)], p=body_column)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.button(l ="Rename and Number", bgc=(.6, .6, .6), c=lambda x: start_renaming('rename_and_number'))
    cmds.separator(h=10, style='none')  # Empty Space

    # Prefix and Suffix ================
    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 0)], p=body_column)
    cmds.separator(h=10)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('Prefix and Suffix')
    cmds.separator(h=7, style='none')  # Empty Space
    
    cmds.rowColumnLayout( nc=4, cw=[(1, 50),(2, 50),(3, 50),(4, 85)], cs=[(1, 0),(2, 0),(3, 0),(4, 10)], p=body_column)
    cmds.text('Prefix:')
    cmds.radioCollection()
    add_prefix_auto = cmds.radioButton( label='Auto', select=True, cc=lambda x:update_prefix_suffix_options())
    cmds.radioButton( label='Input', cc=lambda x:update_prefix_suffix_options())
    prefix_textfield = cmds.textField(placeholderText='prefix_',
                                      enterCommand=lambda x: start_renaming('add_prefix'), en=False)
    
    cmds.text('Suffix:')
    cmds.radioCollection()
    add_suffix_auto = cmds.radioButton( label='Auto', select=True, cc=lambda x:update_prefix_suffix_options())
    cmds.radioButton( label='Input', cc=lambda x:update_prefix_suffix_options())
    suffix_textfield = cmds.textField(placeholderText='_suffix',
                                      enterCommand=lambda x: start_renaming('add_suffix'), en=False)
    
    cmds.separator(h=10, style='none')  # Empty Space
    
    cmds.rowColumnLayout( nc=6, cw=[(1, 40), (2, 40),(3, 40),(4, 40),(5, 40), (6, 40)],
                          cs=[(1, 5),(2, 0),(3, 0),(4, 0),(5, 0),(6, 0)], p=body_column)
    cmds.text('Group', font='smallObliqueLabelFont')
    cmds.text('Mesh', font='smallObliqueLabelFont')
    cmds.text('Nurbs', font='smallObliqueLabelFont')
    cmds.text('Joint', font='smallObliqueLabelFont')
    cmds.text('Locator', font='smallObliqueLabelFont')
    cmds.text('Surface', font='smallObliqueLabelFont')
    transform_suffix_textfield = cmds.textField(text = gt_renamer_settings.get('transform_suffix'),
                                                enterCommand=lambda x:start_renaming('add_suffix'),
                                                cc=lambda x:set_persistent_settings_renamer('gt_renamer_transform_suffix', cmds.textField(transform_suffix_textfield, q=True, text=True)))
    mesh_suffix_textfield = cmds.textField(text = gt_renamer_settings.get('mesh_suffix'),
                                            enterCommand=lambda x:start_renaming('add_suffix'),
                                            cc=lambda x:set_persistent_settings_renamer('gt_renamer_mesh_suffix', cmds.textField(mesh_suffix_textfield, q=True, text=True)))
    nurbs_curve_suffix_textfield = cmds.textField(text = gt_renamer_settings.get('nurbs_curv_suffix'),
                                                enterCommand=lambda x:start_renaming('add_suffix'),
                                                cc=lambda x:set_persistent_settings_renamer('gt_renamer_nurbs_curve_suffix', cmds.textField(nurbs_curve_suffix_textfield, q=True, text=True)))
    joint_suffix_textfield = cmds.textField(text = gt_renamer_settings.get('joint_suffix'),
                                            enterCommand=lambda x:start_renaming('add_suffix'),
                                            cc=lambda x:set_persistent_settings_renamer('gt_renamer_joint_suffix', cmds.textField(joint_suffix_textfield, q=True, text=True)))
    locator_suffix_textfield = cmds.textField(text = gt_renamer_settings.get('locator_suffix'),
                                              enterCommand=lambda x:start_renaming('add_suffix'),
                                              cc=lambda x:set_persistent_settings_renamer('gt_renamer_locator_suffix', cmds.textField(locator_suffix_textfield, q=True, text=True)))
    surface_suffix_textfield = cmds.textField(text = gt_renamer_settings.get('surface_suffix'),
                                              enterCommand=lambda x:start_renaming('add_suffix'),
                                              cc=lambda x:set_persistent_settings_renamer('gt_renamer_surface_suffix', cmds.textField(surface_suffix_textfield, q=True, text=True)))
    
    cmds.separator(h=5, style='none') # Empty Space
    
    cmds.rowColumnLayout( nc=3, cw=[(1, 80),(2, 80),(3, 80)], cs=[(1, 5),(2, 0),(3, 0)], p=body_column)
    cmds.text('Left', font='smallObliqueLabelFont')
    cmds.text('Center', font='smallObliqueLabelFont')
    cmds.text('Right', font='smallObliqueLabelFont')
    left_prefix_textfield = cmds.textField(text = gt_renamer_settings.get('left_prefix') , \
                                           enterCommand=lambda x:start_renaming('add_suffix'), \
                                           cc=lambda x:set_persistent_settings_renamer('gt_renamer_left_prefix', cmds.textField(left_prefix_textfield, q=True, text=True)))
    center_prefix_textfield = cmds.textField(text = gt_renamer_settings.get('center_prefix'), \
                                             enterCommand=lambda x:start_renaming('add_suffix'), \
                                             cc=lambda x:set_persistent_settings_renamer('gt_renamer_center_prefix', cmds.textField(center_prefix_textfield, q=True, text=True)))
    right_prefix_textfield = cmds.textField(text = gt_renamer_settings.get('right_prefix'), \
                                            enterCommand=lambda x:start_renaming('add_suffix'), \
                                            cc=lambda x:set_persistent_settings_renamer('gt_renamer_right_prefix', cmds.textField(right_prefix_textfield, q=True, text=True)))
    
    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 120),(2, 120)], cs=[(1, 5),(2, 5)], p=body_column)
    cmds.button(l ="Add Prefix", bgc=(.6, .6, .6), c=lambda x:start_renaming('add_prefix'))
    cmds.button(l ="Add Suffix", bgc=(.6, .6, .6), c=lambda x:start_renaming('add_suffix'))
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
    cmds.button(l ="Search and Replace", bgc=(.6, .6, .6), c=lambda x:start_renaming('search_and_replace'))
    cmds.separator(h=15, style='none') # Empty Space
       
       
    def update_prefix_suffix_options():
        """ Updates variables and UI when there is an user input (For the prefix and suffix options) """
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
        cmds.textField(nurbs_curve_suffix_textfield, e=True, en=suffix_auto_textfields)
        cmds.textField(joint_suffix_textfield, e=True, en=suffix_auto_textfields)
        cmds.textField(locator_suffix_textfield, e=True, en=suffix_auto_textfields)
        cmds.textField(surface_suffix_textfield, e=True, en=suffix_auto_textfields)
        
        cmds.textField(left_prefix_textfield, e=True, en=prefix_auto_textfields)
        cmds.textField(center_prefix_textfield, e=True, en=prefix_auto_textfields)
        cmds.textField(right_prefix_textfield, e=True, en=prefix_auto_textfields)
        
        cmds.textField(suffix_textfield, e=True, en=suffix_input_textfields)
        cmds.textField(prefix_textfield, e=True, en=prefix_input_textfields)
       
       
    def start_renaming(operation):
        """ 
        Main function to rename elements, it uses a string to determine what operation to run.
        
                Parameters:
                    operation (string): name of the operation to execute. (e.g. search_and_replace)
        """
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
            for node in gt_renamer_settings.get('nodes_to_ignore'):
                if cmds.objExists(node):
                    selection.remove(node)  
            for node_type in gt_renamer_settings.get('node_types_to_ignore'):
                undesired_types = cmds.ls(type=node_type)
                for undesired_node in undesired_types:
                    if cmds.objExists(undesired_node):
                        if undesired_node in selection:
                            selection.remove(undesired_node)
                      
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
                nurbsCurv_suffix_input = cmds.textField(nurbs_curve_suffix_textfield, q=True, text=True)
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
                print(traceback.format_exc())
                cmds.error("## Error, see script editor: %s" % e)
            finally:
                cmds.undoInfo(closeChunk=True, chunkName=script_name)
           
    
    # Show and Lock Window
    cmds.showWindow(build_gui_renamer)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    if python_version == 3:
        widget = wrapInstance(int(qw), QWidget)
    else:
        widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/renamePreset.png')
    widget.setWindowIcon(icon)
    


def build_gui_help_renamer():
    """ Creates the Help GUI for GT Renamer """
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
    cmds.text(script_name + " Help", bgc=[.4,.4,.4],  fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p=main_column) # Empty Space

    # Body ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column)
    cmds.text(l='Script for renaming multiple objects.', align="center")
    cmds.separator(h=15, style='none') # Empty Space
    
    cmds.text(l='Modes:', align="center", fn="tinyBoldLabelFont")
    cmds.text(l='- Selected: uses selected objects when renaming.', align="left", font='smallPlainLabelFont')
    cmds.text(l='- Hierarchy: uses hierarchy when renaming.', align="left", font='smallPlainLabelFont')
    cmds.text(l='- All: uses everything in the scene (even hidden nodes)', align="left", font='smallPlainLabelFont')
    
    cmds.separator(h=10, style='none') # Empty Space
    
    cmds.text(l='Other Tools:', align="center", fn="tinyBoldLabelFont")
    cmds.text(l='- Remove First Letter: removes the first letter of a name.', align="left", font='smallPlainLabelFont')
    cmds.text(l='If the next character is a number, it will be deleted.', align="left", font='smallPlainLabelFont')
    cmds.text(l='- Remove Last Letter: removes the last letter of a name.', align="left", font='smallPlainLabelFont')
    cmds.text(l='- U-Case: makes all letters uppercase.', align="left", font='smallPlainLabelFont')
    cmds.text(l='- Capitalize: makes the 1st letter of every word uppercase.', align="left", font='smallPlainLabelFont')
    cmds.text(l='- L-Case: makes all letters lowercase.', align="left", font='smallPlainLabelFont')
    
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
    cmds.button(l='Reset Persistent Settings', h=30, c=lambda args: reset_persistent_settings_renamer())
    cmds.separator(h=5, style='none')
    cmds.button(l='OK', h=30, c=lambda args: close_help_gui())
    cmds.separator(h=8, style='none')
    
    # Show and Lock Window
    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    if python_version == 3:
        widget = wrapInstance(int(qw), QWidget)
    else:
        widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/question.png')
    widget.setWindowIcon(icon)
    
    def close_help_gui():
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)
   


def string_replace(string, search, replace):
    """
    Search and Replace Function for a String
            
            Parameters:
                    string (string): string to be processed
                    search (string): what to search for
                    replace (string): what to replace it with
    """
    if string == '':
        return ''
    replace_string = string.replace(search, replace)    
    return replace_string



def get_short_name(obj):
    """
    Get the name of the objects without its path (Maya returns full path if name is not unique)

            Parameters:
                    obj (string) - object to extract short name
    """
    if obj == '':
        return ''
    split_path = obj.split('|')
    if len(split_path) >= 1:
        short_name = split_path[len(split_path)-1]
    return short_name


def rename_uppercase(obj_list):
    """
    Rename objects to be uppercase
    
            Parameters:
                    obj_list (list) - a list of objects (strings) to be renamed
    """
    to_rename = []
    errors = ''
    
    for obj in obj_list:
        object_short_name = get_short_name(obj)
        new_name = object_short_name.upper()
        if cmds.objExists(obj) and 'shape' not in cmds.nodeType(obj, inherited=True) and obj != new_name:
            to_rename.append([obj,new_name])
            
    for pair in reversed(to_rename):
        if cmds.objExists(pair[0]):
            try:
                cmds.rename(pair[0], pair[1])
            except Exception as exception:
                errors = errors + '"' + str(pair[0]) + '" : "' + exception[0].rstrip("\n") + '".\n'
    if errors != '':
            print('#' * 80 + '\n')
            print(errors)
            print('#' * 80)
            cmds.warning(gt_renamer_settings.get('error_message'))
            
    renaming_inview_feedback(len(to_rename))

def rename_lowercase(obj_list):
    """
    Rename objects to be lowercase
    
            Parameters:
                    obj_list (list) - a list of objects (strings) to be renamed
    """
    to_rename = []
    errors = ''
    
    for obj in obj_list:
        object_short_name = get_short_name(obj)
        new_name = object_short_name.lower()
        if cmds.objExists(obj) and 'shape' not in cmds.nodeType(obj, inherited=True) and obj != new_name:
            to_rename.append([obj,new_name])
            
    for pair in reversed(to_rename):
        if cmds.objExists(pair[0]):
            try:
                cmds.rename(pair[0], pair[1])
            except Exception as exception:
                errors = errors + '"' + str(pair[0]) + '" : "' + exception[0].rstrip("\n") + '".\n'
    if errors != '':
            print('#' * 80 + '\n')
            print(errors)
            print('#' * 80)
            cmds.warning(gt_renamer_settings.get('error_message'))
            
    renaming_inview_feedback(len(to_rename))


def rename_capitalize(obj_list):
    """
    Rename objects to be capitalized

            Parameters:
                    obj_list (list) - a list of objects (strings) to be renamed
    """
    to_rename = []
    errors = ''
    
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
        
        if cmds.objExists(obj) and 'shape' not in cmds.nodeType(obj, inherited=True) and obj != new_name:
            to_rename.append([obj,new_name])
            
    for pair in reversed(to_rename):
        if cmds.objExists(pair[0]):
            try:
                cmds.rename(pair[0], pair[1])
            except Exception as exception:
                errors = errors + '"' + str(pair[0]) + '" : "' + exception[0].rstrip("\n") + '".\n'
    if errors != '':
            print('#' * 80 + '\n')
            print(errors)
            print('#' * 80)
            cmds.warning(gt_renamer_settings.get('error_message'))
            
    renaming_inview_feedback(len(to_rename))


def remove_first_letter(obj_list):
    """
    Rename objects removing the first letter

            Parameters:
                    obj_list (list) - a list of objects (strings) to be renamed
    """
    to_rename = []
    errors = ''
    
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
            try:
                cmds.rename(pair[0], pair[1])
            except Exception as exception:
                errors = errors + '"' + str(pair[0]) + '" : "' + exception[0].rstrip("\n") + '".\n'
    if errors != '':
            print('#' * 80 + '\n')
            print(errors)
            print('#' * 80)
            cmds.warning(gt_renamer_settings.get('error_message'))
    
    renaming_inview_feedback(len(to_rename))


def remove_last_letter(obj_list):
    """
    Rename objects removing the last letter

            Parameters:
                    obj_list (list) - a list of objects (strings) to be renamed
    """
    to_rename = []
    errors = ''
    
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
            try:
                cmds.rename(pair[0], pair[1])
            except Exception as exception:
                errors = errors + '"' + str(pair[0]) + '" : "' + exception[0].rstrip("\n") + '".\n'
    if errors != '':
            print('#' * 80 + '\n')
            print(errors)
            print('#' * 80)
            cmds.warning(gt_renamer_settings.get('error_message'))
            
    renaming_inview_feedback(len(to_rename))


def rename_search_replace(obj_list, search, replace):
    """
    Rename Using Search and Replace

            Parameters:
                    obj_list (list): a list of objects (strings) to be renamed
                    search (string): what to search for
                    replace (string): what to replace it with
    """
    if search == '':
        cmds.warning('The search string must not be empty.')
    else: 
        to_rename = []
        
        for obj in obj_list:
            object_short_name = get_short_name(obj)
            new_name = string_replace(str(object_short_name), search, replace)
            if cmds.objExists(obj) and 'shape' not in cmds.nodeType(obj, inherited=True) and obj != new_name:
                to_rename.append([obj,new_name])
                
        for pair in reversed(to_rename):
            if cmds.objExists(pair[0]):
                cmds.rename(pair[0], pair[1])
    
        renaming_inview_feedback(len(to_rename))
        

def rename_and_number(obj_list, new_name, start_number, padding_number):
    """
    Rename Objects and Add Number (With Padding)

            Parameters:
                    obj_list (list): a list of objects (strings) to be renamed
                    new_name (string): a new name to rename the objects
                    start_number (int): what number to start counting from
                    padding_number (int): how many zeroes it will add before numbers
    """
    if new_name == '':
        cmds.warning('The provided string must not be empty.')
    else: 
        to_rename = []
        count = start_number
        errors = ''
        
        for obj in obj_list:
            object_short_name = get_short_name(obj)
            new_name_and_number = new_name + str(count).zfill(padding_number)
            if cmds.objExists(obj) and 'shape' not in cmds.nodeType(obj, inherited=True):
                to_rename.append([obj,new_name_and_number])
                count += 1
            
        for pair in reversed(to_rename):
            if cmds.objExists(pair[0]):
                try:
                    cmds.rename(pair[0], pair[1])
                except Exception as exception:
                    errors = errors + '"' + str(pair[0]) + '" : "' + exception[0].rstrip("\n") + '".\n'
        
        if errors != '':
            print('#' * 80 + '\n')
            print(errors)
            print('#' * 80)
            cmds.warning(gt_renamer_settings.get('error_message'))
            
        renaming_inview_feedback(len(to_rename))


def rename_add_prefix(obj_list, new_prefix_list):
    """
    Add Prefix

            Parameters:
                    obj_list (list): a list of objects (strings) to be renamed
                    new_prefix_list (list) - a list of prefix strings, if just one it assumes that it's a manual input, if more (3) it automates (usually left, center, right)
    """
    
    auto_prefix = True
    if len(new_prefix_list) == 1:
        auto_prefix = False
        new_prefix = new_prefix_list[0]
    
    if auto_prefix == False and new_prefix == '':
        cmds.warning('Prefix Input must not be empty.')
    else: 
        to_rename = []
        errors = ''
        for obj in obj_list:
            if auto_prefix and 'shape' not in cmds.nodeType(obj, inherited=True):
                try:
                    obj_x_pos = cmds.xform(obj, piv=True , q=True , ws=True)[0]
                except:
                    obj_x_pos = 'Unknown'
                if obj_x_pos == 'Unknown':
                    new_prefix = ''
                elif obj_x_pos > 0.0001:
                    new_prefix= new_prefix_list[0]
                elif obj_x_pos < -0.0001:
                    new_prefix = new_prefix_list[2]
                else:
                    new_prefix = new_prefix_list[1]
            else:
                new_prefix = ''
                if not auto_prefix:
                    new_prefix = new_prefix_list[0]
    
            object_short_name = get_short_name(obj)
            
            if object_short_name.startswith(new_prefix):
                new_name_and_prefix = object_short_name
            else:
                new_name_and_prefix = new_prefix + object_short_name
            
            if cmds.objExists(obj) and 'shape' not in cmds.nodeType(obj, inherited=True) and obj != new_name_and_prefix:
                to_rename.append([obj,new_name_and_prefix])
            
        for pair in reversed(to_rename):
            if cmds.objExists(pair[0]):
                try:
                    cmds.rename(pair[0], pair[1])
                except Exception as exception:
                    errors = errors + '"' + str(pair[0]) + '" : "' + exception[0].rstrip("\n") + '".\n'
                
                    
        if errors != '':
            print('#' * 80 + '\n')
            print(errors)
            print('#' * 80)
            cmds.warning(gt_renamer_settings.get('error_message'))
        
        renaming_inview_feedback(len(to_rename))
            

def rename_add_suffix(obj_list, new_suffix_list):
    """
    Add Suffix

            Parameters:
                    obj_list (list): a list of objects (strings) to be renamed
                    new_suffix_list (list): - a list of suffix strings, if just one it assumes that it's a manual input, if more (6) it automates (usually _geo,_jnt, etc...)
    """
    auto_suffix = True
    
    if len(new_suffix_list) == 1:
        auto_suffix = False
        new_suffix = new_suffix_list[0]
    
    if auto_suffix == False and new_suffix == '':
        cmds.warning('Suffix Input must not be empty.')
    else: 
        to_rename = []
        errors = ''
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
            else:
                new_suffix = ''
                if not auto_suffix:
                    new_suffix = new_suffix_list[0]
                        
            object_short_name = get_short_name(obj)
            
            if object_short_name.endswith(new_suffix):
                new_name_and_suffix = object_short_name
            else:
                new_name_and_suffix = object_short_name + new_suffix
            
            if cmds.objExists(obj) and 'shape' not in cmds.nodeType(obj, inherited=True) and obj != new_name_and_suffix:
                to_rename.append([obj,new_name_and_suffix])
            
        for pair in reversed(to_rename):
            if cmds.objExists(pair[0]):
                try:
                    cmds.rename(pair[0], pair[1])
                except Exception as exception:
                    errors = errors + '"' + str(pair[0]) + '" : "' + exception[0].rstrip("\n") + '".\n'
                    
        if errors != '':
            print('#' * 80 + '\n')
            print(errors)
            print('#' * 80)
            cmds.warning(gt_renamer_settings.get('error_message'))
        
        renaming_inview_feedback(len(to_rename))
    
        
def rename_and_alphabetize(obj_list, new_name):
    """
    WIP - Rename Objects and Add Letter (Alphabetical Order) - Work in Progress

            Parameters:
                    obj_list (list): a list of objects (strings) to be renamed
                    new_name - WIP
    """
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


def renaming_inview_feedback(number_of_renames):
    """
    Prints an inViewMessage to give feedback to the user about how many objects were renamed.
    Uses the module "random" to force identical messages to appear at the same time.

            Parameters:
                    number_of_renames (int): how many objects were renamed.
    """
    if number_of_renames != 0:
            message = '<' + str(random.random()) + '><span style=\"color:#FF0000;text-decoration:underline;\">' + str(number_of_renames)
            
            if number_of_renames == 1:
                message += '</span><span style=\"color:#FFFFFF;\"> object was renamed.</span>'
            else: 
                message += '</span><span style=\"color:#FFFFFF;\"> objects were renamed.</span>'
            cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)

# Run Script
get_persistent_settings_renamer()
if __name__ == '__main__':
    build_gui_renamer()