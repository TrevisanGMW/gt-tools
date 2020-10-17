"""

 GT Grading Script  - Script for automatically testing and grading assignments
 Configured for: Rigging 1 - Control Rig (Assignment 1.3 - Final)
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-08-13 - github.com/TrevisanGMW

 1.1 - 2020/10/10
 Eyes no longer move when testing bulleproof

"""
import maya.cmds as cmds
from datetime import datetime
from maya import OpenMayaUI as omui
import maya.OpenMaya as om
import os.path
import time
import re

try:
    from shiboken2 import wrapInstance
except ImportError:
    from shiboken import wrapInstance

try:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QWidget
except ImportError:
    from PySide.QtGui import QIcon, QWidget


# Script and Assignment Name
assignment_name = 'Rigging 1 - Control Rig'
script_name = 'GT - Grading Script'

# Regex pattern
re_file_name = re.compile(r'(^\dD\d{3}\_\w+\_)(ControlRig|Control|Rig|Control)(_|.)')

# Version
script_version = '1.1'

# Grading Components
gt_grading_components = { 0 : ['Organization & File Name', 10],
                          1 : ['FK System (Upper Body)', 25],
                          2 : ['IK System (Lower Body)', 25],
                          3 : ['Main & Eye Controls', 20],
                          4 : ['Bulletproofing, Targets & Others', 15],
                          5 : ['Scalable Control Rig', 5],
                        }

# Common Notes
gt_grading_notes = { 0 : ['Organization', 'Scene is not properly organized. (Possible issues: naming, junk objects, keyframes left behind, incorrect scene name, etc..)'],
                     1 : ['Geo not skinned', 'Some geometries were not skinned (bound) to any joints.'],
                     2 : ['Missing Control', 'Missing one or more expected controls.'],
                     3 : ['Malfunctioning FK', 'Not all controls are fully functional on your FK system.'],
                     4 : ['Incorrect Hierarchy', 'The current hierarchy is making the rig not fully functional.'], 
                     5 : ['Junk Data', 'Junk data was left behind. All controls should have been zeroed.'],
                     6 : ['Malfunctioning IK', 'Not all controls are fully functional on your IK system.'],
                     7 : ['Missing Attribute', 'Not all custom attributes exist or are fully functional.'],
                     8 : ['Missing Pole Vector', 'A pole vector control for the knee is not present or malfunctioning.'],
                     9 : ['Broken Skin Weights', 'Skin weights were not transfered to this file or are malfunctioning.'],
                    10 : ['Missing Bulletproofing', 'Rig is not bulletproof.'],
                    11 : ['Broken Eye Controls', 'Eye controls are missing or malfunctioning.'],
                    12 : ['Broken Main Controls', 'Main controls are missing or malfunctioning.'],
                    13 : ['Missing BS Target', 'Missing one or more expected blend shape target.'],
                    14 : ['Not Scalable', 'Rig breaks when the scale is changed.']
                   }
                   
gt_grading_settings = { 'keyframes_interval' : 5,
                        'joints_visibility_state' : True
                      }

# Elements Lists                     
thumb_fingers_ctrls = ['left_thumb1_ctrl', 'left_thumb2_ctrl', 'left_thumb3_ctrl', \
                'right_thumb1_ctrl', 'right_thumb2_ctrl', 'right_thumb3_ctrl']
                    
index_fingers_ctrls = ['left_index1_ctrl', 'left_index2_ctrl', 'left_index3_ctrl', \
                'right_index1_ctrl', 'right_index2_ctrl', 'right_index3_ctrl']
                    
middle_fingers_ctrls = ['left_middle1_ctrl', 'left_middle2_ctrl', 'left_middle3_ctrl', \
                'right_middle1_ctrl', 'right_middle2_ctrl', 'right_middle3_ctrl']
                    
ring_fingers_ctrls = ['left_ring1_ctrl', 'left_ring2_ctrl', 'left_ring3_ctrl', \
                'right_ring1_ctrl', 'right_ring2_ctrl', 'right_ring3_ctrl']
                    
pinky_fingers_ctrls = ['left_pinky1_ctrl', 'left_pinky2_ctrl', 'left_pinky3_ctrl', \
                'right_pinky1_ctrl', 'right_pinky2_ctrl', 'right_pinky3_ctrl']
                
spine_ctrls = ['spine1_ctrl', 'spine2_ctrl', 'spine3_ctrl']

knee_ctrls = ['left_knee_ctrl','right_knee_ctrl']

foot_ctrls = ['left_foot_ctrl', 'right_foot_ctrl']

eye_ctrls = ['left_eye_ctrl','right_eye_ctrl', 'main_eye_ctrl']

wrist_ctrls = ['left_wrist_ctrl', 'right_wrist_ctrl']


# Dict { joint_name : [position, rotation, radius, ignore_string_list] - Radius can be replaced with a XYZ tuple for custom scale. Add a list at the end of ignoring objects.
# To quickly create a list use : extract_brute_force_dict(is_joint=False, include_vec_scale=True)
small_radius = 1.2
brute_force_ctrl_naming_dict = {'root_ctrl' : [ [-0.000, 68.213, -0.000], [90.000, -29.914, 90.000], 5, ['hip']],
                                'spine1_ctrl' : [ [-0.000, 74.642, 3.699], [90.000, -13.143, 90.000], 4.5, ['spine2', 'spine3', 'spine4']],
                                'spine2_ctrl' : [ [0.000, 82.788, 5.753], [90.000, -4.753, 90.000], 4.45, ['spine1', 'spine3', 'spine4']],
                                'spine3_ctrl' : [ [0.000, 89.744, 6.318], [90.000, 9.432, 90.000], 3.5, ['spine2', 'spine1', 'spine4']],
                                'spine4_ctrl' : [ [0.000, 97.788, 4.736], [90.000, 14.487, 90.000], 5.5, ['spine2', 'spine3', 'spine1']],
                                'neck1_ctrl' : [ [-0.000, 109.851, 0.917], [90.000, -10.685, 90.000], 2.7],
                                'neck2_ctrl' : [ [-0.000, 114.569, 1.294], [90.000, 24.717, 90.000], 2.3],
                                'head_ctrl' : [ [0.000, 119.812, -0.847], [90.000, -9.801, 90.000], 3.4, ['jaw']],
                                'jaw_ctrl' : [ [-0.000, 127.082, -1.245], [-90.000, -55.636, -90.000], 4, ['head']],
                                'right_clavicle_ctrl' : [ [-3.923, 106.337, 4.045], [88.064, -26.863, 4.278], 4],
                                'right_shoulder_ctrl' : [ [-10.783, 106.827, 0.561], [90.873, -13.006, 57.019], 4],
                                'right_elbow_ctrl' : [ [-22.068, 89.436, -4.228], [90.929, 10.179, 61.621], 8],
                                'right_wrist_ctrl' : [ [-33.983, 71.527, -0.253], [95.569, 4.904, 60.188], 1.7],
                                'right_thumb1_ctrl' : [ [-34.790, 68.980, 0.959], [-21.795, 51.020, 121.460], small_radius],
                                'right_thumb2_ctrl' : [ [-33.915, 67.550, 3.031], [-48.819, 38.623, 91.987], small_radius],
                                'right_thumb3_ctrl' : [ [-33.857, 65.857, 4.385], [-54.746, 58.638, 92.780], small_radius],
                                'right_pinky1_ctrl' : [ [-37.726, 65.625, -1.365], [179.617, 6.299, 80.969], small_radius],
                                'right_pinky2_ctrl' : [ [-38.166, 62.857, -1.055], [-175.501, 6.461, 89.944], small_radius],
                                'right_pinky3_ctrl' : [ [-38.167, 61.505, -0.902], [-177.809, 5.631, 100.538], small_radius],
                                'right_ring1_ctrl' : [ [-38.012, 65.683, -0.033], [-179.774, 10.010, 77.555], small_radius],
                                'right_ring2_ctrl' : [ [-38.687, 62.625, 0.520], [-174.803, 8.830, 90.955], small_radius],
                                'right_ring3_ctrl' : [ [-38.656, 60.737, 0.813], [179.695, 9.448, 96.247], small_radius],
                                'right_middle1_ctrl' : [ [-37.562, 65.887, 1.311], [-175.674, 14.035, 66.650], small_radius],
                                'right_middle2_ctrl' : [ [-38.933, 62.712, 2.176], [-174.291, 13.113, 83.605], small_radius],
                                'right_middle3_ctrl' : [ [-39.163, 60.658, 2.657], [-176.819, 14.100, 93.782], small_radius],
                                'right_index1_ctrl' : [ [-37.144, 66.220, 2.815], [-172.814, 14.588, 68.191], small_radius],
                                'right_index2_ctrl' : [ [-38.367, 63.161, 3.673], [-169.935, 13.883, 80.486], small_radius],
                                'right_index3_ctrl' : [ [-38.626, 61.619, 4.059], [-175.316, 13.913, 88.718], small_radius],
                                'left_clavicle_ctrl' : [ [3.923, 106.337, 4.045], [-91.936, 26.863, -4.278], 4],
                                'left_shoulder_ctrl' : [ [10.783, 106.827, 0.561], [-89.127, 13.006, -57.019], 4],
                                'left_elbow_ctrl' : [ [22.068, 89.436, -4.228], [-89.071, -10.179, -61.621], 8],
                                'left_wrist_ctrl' : [ [33.983, 71.527, -0.253], [-84.431, -4.904, -60.188], 1.7],
                                'left_thumb1_ctrl' : [ [34.790, 68.980, 0.959], [158.205, -51.020, -121.460], small_radius],
                                'left_thumb2_ctrl' : [ [33.915, 67.550, 3.031], [131.181, -38.623, -91.987], small_radius],
                                'left_thumb3_ctrl' : [ [33.857, 65.857, 4.385], [125.254, -58.638, -92.780], small_radius],
                                'left_ring1_ctrl' : [ [38.012, 65.683, -0.033], [0.226, -10.010, -77.555], small_radius],
                                'left_ring2_ctrl' : [ [38.687, 62.625, 0.520], [5.197, -8.830, -90.955], small_radius],
                                'left_ring3_ctrl' : [ [38.656, 60.737, 0.813], [-0.305, -9.448, -96.247], small_radius],
                                'left_middle1_ctrl' : [ [37.562, 65.887, 1.311], [4.326, -14.035, -66.650], small_radius],
                                'left_middle2_ctrl' : [ [38.933, 62.712, 2.176], [5.709, -13.113, -83.605], small_radius],
                                'left_middle3_ctrl' : [ [39.163, 60.658, 2.657], [3.181, -14.100, -93.782], small_radius],
                                'left_index1_ctrl' : [ [37.143, 66.220, 2.815], [7.186, -14.588, -68.191], small_radius],
                                'left_index2_ctrl' : [ [38.367, 63.161, 3.673], [10.065, -13.883, -80.486], small_radius],
                                'left_index3_ctrl' : [ [38.626, 61.619, 4.059], [4.684, -13.913, -88.718], small_radius],
                                'left_pinky1_ctrl' : [ [37.726, 65.625, -1.365], [-0.383, -6.299, -80.969], small_radius],
                                'left_pinky2_ctrl' : [ [38.166, 62.857, -1.055], [4.499, -6.461, -89.944], small_radius],
                                'left_pinky3_ctrl' : [ [38.167, 61.505, -0.902], [2.191, -5.631, -100.538], small_radius],
                                'left_eye_ctrl' : [ [6.432, 129.207, 61.954], [0, 0, 0], (2.8, 2.8, 45)],
                                'main_eye_ctrl' : [ [0.000, 129.207, 61.954], [0, 0, 0], (2.8, 2.8, 45), ['left_', 'right_', 'r_', 'l_']],
                                'right_eye_ctrl' : [ [-6.432, 129.207, 61.954], [0, 0, 0],(2.8, 2.8, 45)],
                                'right_foot_ctrl' : [ [-6.958, 5.028, -3.074], [90.000, 52.476, 90.000], 3.5],
                                'left_foot_ctrl' : [ [6.958, 5.028, -3.074], [0, 0, 0], 3.5],
                                'right_knee_ctrl' : [ [-6.958, 35.466, 30.755], [0, 0, 0], (3.5, 3.5, 25)],
                                'left_knee_ctrl' : [ [6.958, 35.466, 30.755], [0, 0, 0], (3.5, 3.5, 25)],
                                'direction_ctrl' : [ [0, 0, 0], [0, 0, 0], 3, ['main', 'root', 'master', 'top'], ['main', 'root', 'master', 'top', 'controls']],
                                'main_ctrl' : [ [0, 0, 0], [0, 0, 0], 3, ['direction', 'left', 'right', 'eye', 'wire', 'base', 'upper', 'lower', 'brow', 'cog'],\
                                                                         ['direction', 'left', 'right', 'eye', 'wire', 'base', 'upper', 'lower', 'brow', 'cog'] ],
                                }


def build_gui_gt_grader_script():
    ''' Build UI'''
    window_name = "build_gui_gt_grader_script"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title= script_name + ' - '+  assignment_name + ' - v' + script_version, mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1,1])

    main_column = cmds.columnLayout(p= window_name)
   
    # Title Text
    cmds.separator(h=12, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 410)], cs=[(1, 10)], p=main_column) # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 400)], cs=[(1, 10)], p=main_column) # Title Column
    cmds.text(assignment_name, bgc=[0,.5,0],  fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p=main_column) # Empty Space

    # Body ====================
    checklist_spacing = 4
    cmds.rowColumnLayout(nc=1, cw=[(1, 400)], cs=[(1,10)], p=main_column)
    cmds.text(l='This script was created for grading.\nIf used incorrectly it may irreversibly change your scene.', align="center")
    cmds.separator(h=5, style='none') # Empty Space
    cmds.rowColumnLayout(nc=3, cw=[(1, 65),(2, 270),(3, 65)], cs=[(1,10)], p=main_column)
    cmds.separator(h=10, style='none') # Empty Space
    cmds.text(l='Please, save it first in case you want to proceed.', bgc=[1,.3,.3],align="center")
    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 400)], cs=[(1,10)], p=main_column)
    cmds.separator(h=10, style='none') # Empty Space
    cmds.separator(h=12) 
    cmds.separator(h=10, style='none') # Empty Space
    
    # Build Checklist 
    cmds.rowColumnLayout(nc=3, cw=[(1, 50), (2, 165)], cs=[(1, 15), (2, 0)], p=main_column)
    cmds.text(l='Checks:')
    cmds.text(l='Component:')
    cmds.text(l='Grade:', align='left')
    cmds.separator(h=10, style='none') # Empty Space
    
    check_items_column = cmds.rowColumnLayout(nc=3, cw=[(1, 50), (2, 150),(3, 180)], cs=[(1, 15), (2, 10)], p=main_column)

    def create_check_button(btn_id, item_id):
        ''' 
        Simple Create button function used to reroute scope
        
                    Parameters:
                        btn_id (string) : String used as an id for the button
                        item_id (string) : String used as the id of the elements
        
        '''
        cmds.button(btn_id, l='Check', h=14, bgc=[.5,.7,.5], ann='0', c=lambda args: run_check_operation(item_id))

    def create_gt_grading_components(items, override_fonts= ([],'smallPlainLabelFont') ):
        ''' 
        Creates the UI for the assignment components
        
                    Parameters:
                        item (dict) : Dictionary of assingment components. 
                                      Pattern: "{int_id : ['string_component_name', int_max_grade]}" 
                                      Example: {0 : ['Organization & File Name', 10]}
                        override_fonts (tuple) : A tuple used to override the font used for the component. It should carry two elements:
                                      buttons_to_override (list): a list of integers to find the buttons you want to change
                                      font (string): what font to use (instead of the default one)
        
        '''
        for item in items:
            item_id = strip_string_as_id(items.get(item)[0])
            create_check_button("check_btn_" + item_id, item_id)
            
            if len(override_fonts) > 0 and item in override_fonts[0]:
                cmds.text(items.get(item)[0] + ': ', fn=override_fonts[1], align='left')
            else:
                cmds.text(items.get(item)[0] + ': ', align='left')
                
            max_value = items.get(item)[1]
            cmds.intSliderGrp('grade_' + item_id, cw=[(1,0),(2,40),(3,10)], cal=[(1,'left')], field=True, label='',\
                              minValue=0, maxValue=max_value, fieldMinValue=0, fieldMaxValue=max_value, value=max_value, cc=lambda args: update_grade_output())

    create_gt_grading_components(gt_grading_components, ([0, 1,2,3,4,5],'smallPlainLabelFont'))
    
    # Late Submission
    cmds.separator(h=5, style='none') # Empty Space
    cmds.separator(h=5, style='none') # Empty Space
    check_items_column = cmds.rowColumnLayout(nc=3, cw=[(1, 50), (2, 150),(3, 180)], cs=[(1, 15), (2, 10)], p=main_column)

    cmds.button('check_btn_late_submission', l='Check', h=14, bgc=[.5,.7,.5], c=lambda args: run_check_operation('late_submission_check'))
    cmds.text('Late Submission Penalty (Days): ', fn='smallPlainLabelFont', align='left')
    cmds.intSliderGrp('late_submission_multiplier' , cw=[(1,0),(2,40),(3,10)], cal=[(1,'left')], field=True, label='',\
                       minValue=0, maxValue=10, fieldMinValue=0, fieldMaxValue=100, value=0, fieldStep=10, cc=lambda args: update_grade_output())

    def update_grade_output():
        ''' Updates "Output Window" UI elements to show current grade. '''
        cmds.scrollField(output_scroll_field, e=True, clear=True)
        grade_total = 0
        for grade in gt_grading_components:
            item_name = gt_grading_components.get(int(grade))[0]
            item_id = strip_string_as_id(gt_grading_components.get(grade)[0])
            grade_total += cmds.intSliderGrp('grade_' + item_id, q=True, value=True)
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=str(cmds.intSliderGrp('grade_' + item_id, q=True, value=True)) + '/' + str(gt_grading_components.get(int(grade))[1]) + ' - ' + item_name + '\n')
        
        penalty = 1.0 - (0.1*float(cmds.intSliderGrp('late_submission_multiplier', q=True, value=True)))
        if penalty != 1.0:
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=str(int(cmds.intSliderGrp('late_submission_multiplier', q=True, value=True)*10)) + '% - Late Submission Penalty\n')
            
        grade_total = grade_total * penalty
        
        cmds.scrollField(output_scroll_field, e=True, ip=0, it='\n      Total: ' +  str(grade_total) + '\n\n')
        
        
        for note in gt_grading_notes:
            item_id = strip_string_as_id(gt_grading_notes.get(note)[0])

            button_name = "note_btn_" + item_id
            button_state = int(cmds.button(button_name, q=True, ann=True))
            
            if button_state:
                cmds.scrollField(output_scroll_field, e=True, ip=0, it=' - ' + str(gt_grading_notes.get(int(note))[1]) + '\n')
        
        
        cmds.scrollField(output_scroll_field, e=True, ip=1, it='') # Bring Back to the Top
        

    cmds.separator(h=15, style='none') # Empty Space
    
    # Output Window =============
    cmds.rowColumnLayout(nc=1, cw=[(1, 400)], cs=[(1, 10)], p=main_column)
    cmds.text(l='Output Window:', align="center", fn="smallPlainLabelFont")  
    cmds.separator(h=checklist_spacing, style='none') # Empty Space
   
    output_scroll_field = cmds.scrollField(editable=False, wordWrap=True, fn="obliqueLabelFont")
    
    cmds.separator(h=10, style='none') # Empty Space
    cmds.text(l='Add Common Notes:', align="center", fn="smallPlainLabelFont")  
    cmds.separator(h=5, style='none') # Empty Space

    buttons_size = 130
    buttons_per_row = 3
    cmds.rowColumnLayout(nc=buttons_per_row, cw=[(1, buttons_size), (2, buttons_size), (3, buttons_size), (4, buttons_size)], cs=[(1, 10), (2, 5),(3, 5),(4, 5)], p=main_column)
    
    
    def create_note_button(btn_id, btn_label):
        ''' 
        Simple Create button function used to reroute scope
        
                    Parameters:
                        btn_id (string) : String used as an id for the button
                        btn_label (string) : String used as the label for the button
        
        '''
        cmds.button(btn_id, l=btn_label, bgc=[.3,.3,.3], ann='0', c=lambda args: update_note_btn(btn_id))
    
    def create_gt_grading_note_buttons(items):
        ''' 
        Adds buttons for quickly adding common notes
        
                    Parameters:
                        item (dict) : Dictionary of assingment components. 
                                      Pattern: "{int_id : ['string_button_label', 'string_issue_note']}" 
                                      Example: { 0 : ['Volume issues', 'Some areas of the model are clearly losing volume when deforming.'] }
        '''
        count = 0
        for item in items:
            item_name = items.get(int(item))[0]
            item_id = strip_string_as_id(items.get(item)[0])
            create_note_button("note_btn_" + item_id, item_name)
            count += 1
            if count == buttons_per_row:
                count = 0
                cmds.separator(h=5, style='none') # Empty Space
                cmds.separator(h=5, style='none') # Empty Space
                cmds.separator(h=5, style='none') # Empty Space

    create_gt_grading_note_buttons(gt_grading_notes)
    
    def update_note_btn(btn_name):
        ''' 
        Updates the note buttons to be active or inactive
        
                    Parameters:
                        btn_name (string) : button name/id
        
        '''
        button_state = int(cmds.button(btn_name, q=True, ann=True))
        if button_state:
            cmds.button(btn_name, e=True, bgc=[.3,.3,.3], ann='0')
        else:
            cmds.button(btn_name, e=True, bgc=[.5,.3,.3], ann='1')
        update_grade_output() # Update Text
    
    cmds.rowColumnLayout(nc=1, cw=[(1, 400)], cs=[(1,10)], p=main_column)
    cmds.separator(h=12) 
    cmds.separator(h=5, style='none')
    
    cmds.text(l='Quick Patches:', align="center", fn="smallPlainLabelFont")  
    cmds.separator(h=5, style='none') # Empty Space
        
    buttons_size = 130
    buttons_per_row = 3
    cmds.rowColumnLayout(nc=buttons_per_row, cw=[(1, buttons_size), (2, buttons_size), (3, buttons_size), (4, buttons_size)], cs=[(1, 10), (2, 5),(3, 5),(4, 5)], p=main_column)
    
    
    footer_buttons_color = [.51,.51,.51]
    
    cmds.button(l='All Common Patches', h=30, bgc=footer_buttons_color, c=lambda args: apply_all_common())
    cmds.button(l='Delete Display Layers', h=30, bgc=footer_buttons_color, c=lambda args: delete_all_display_layers())
    cmds.button(l='Delete Namespaces', h=30, bgc=footer_buttons_color, c=lambda args: delete_all_namespaces())
    
    cmds.separator(h=5, style='none')
    cmds.separator(h=5, style='none')
    cmds.separator(h=5, style='none')
    
    
    cmds.button(l='Reset Viewport', h=30, bgc=footer_buttons_color, c=lambda args: reset_viewport())
    cmds.button(l='Toggle Joints', h=30, bgc=footer_buttons_color, c=lambda args: toggle_joints())
    cmds.button(l='Reset Transforms', h=30, bgc=footer_buttons_color, c=lambda args: reset_transforms())
    
    cmds.separator(h=5, style='none')
    cmds.separator(h=5, style='none')
    cmds.separator(h=5, style='none')
    
    
    cmds.button(l='Improve Ctrls Visibility', h=30, bgc=footer_buttons_color, c=lambda args: improve_ctrls_visibility())
    cmds.button(l='Delete All Keyframes', h=30, bgc=footer_buttons_color, c=lambda args: delete_all_keyframes())
    cmds.button(l='Reload File', h=30, bgc=footer_buttons_color, c=lambda args: reload_file())
    
    cmds.separator(h=5, style='none')
    cmds.separator(h=5, style='none')
    cmds.separator(h=5, style='none')
    
    cmds.button(l='Brute Force Naming', h=30, bgc=footer_buttons_color, c=lambda args: brute_force_naming())
    cmds.button(l='Reset Grades', h=30, bgc=footer_buttons_color, c=lambda args: reset_grades())
    cmds.button(l='Open File', h=30, bgc=footer_buttons_color, c=lambda args: open_file())
    
    cmds.separator(h=8, style='none')
    
    # Show and Lock Window
    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/plusMinusAverage.svg')
    widget.setWindowIcon(icon)
    update_grade_output()
    
    
    def apply_all_common():
        ''' Run All Common Patches'''
        
        cmds.scrollField(output_scroll_field, e=True, clear=True) # Clean output window
        output = ''
        errors = ''
        
        try:
            delete_all_namespaces()
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=' - All namespaces were deleted.\n')
        except Exception as e:
            errors = str(e) + '\n'
            
        try:
            delete_all_keyframes()
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=' - All keyframes were deleted.\n')
        except Exception as e:
            errors = str(e) + '\n'
        
        try:
            delete_all_display_layers()
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=' - All display layers were deleted.\n')
        except Exception as e:
            errors = str(e) + '\n'
        
        
        try:
            unsubdivide_geometries()
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=' - All meshes were unsubdivided.\n')
        except Exception as e:
            errors = str(e) + '\n'
        
        try:
            improve_ctrls_visibility()
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=' - Controls visibility was improved.\n')
        except Exception as e:
            errors = str(e) + '\n'
        
        
        try:
            if cmds.objExists('left_pupil_geo') and cmds.objExists('right_pupil_geo'):
                apply_simple_checker_shader(["left_pupil_geo", "right_pupil_geo"])
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=' - Eye shader was applied.\n')
        except Exception as e:
            errors = str(e) + '\n'
            
        try:
            cmds.currentTime(0)
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=' - Timeline was reset back to zero.\n')
        except Exception as e:
            errors = str(e) + '\n'
            
        
        try:
            reset_viewport()
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=' - Viewport and "persp" camera were reset.\n')
        except Exception as e:
            errors = str(e) + '\n'
            
        try:
            reset_transforms()
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=' - Transforms were reset.\n')
        except Exception as e:
            errors = str(e) + '\n'
                
            
        if errors != '':
            cmds.scrollField(output_scroll_field, e=True, ip=0, it='\nSome errors were raised:\n' + errors)
            cmds.scrollField(output_scroll_field, e=True, ip=1, it='') # Bring Back to the Top
            
        # Focus On Head Area
        frame_object('spine2_jnt')
        frame_object('spine2_Jnt')
        frame_object('spine2Jnt')
    
    
    
    def run_check_operation(operation_name):
        ''' 
        Tries to run an operation based on the provided string
        
                    Parameters:
                        operation_name (string) : name of the operation/function to run
        
        '''
        try:
            if operation_name == 'late_submission_check':
                late_submission_check()
            elif operation_name == 'fk_system_upper_body':
                fk_system_upper_body()
            elif operation_name == 'ik_system_lower_body':
                ik_system_lower_body()
            elif operation_name == 'main_eye_controls':
                main_eye_controls()
            elif operation_name == 'bulletproofing_targets_others':
                bulletproofing_targets_others()
            elif operation_name == 'scalable_control_rig':
                scalable_control_rig()
            elif operation_name == 'organization_file_name':
                organization_file_name()
            else:
                pass
        except Exception as exception:
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=str(exception) + '\n')
    
      
    def open_file():
        ''' Invoke open file dialog for quickly loading other files '''
        multiple_filters = "Maya Files (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb);;All Files (*.*)"
        file_path = cmds.fileDialog2(fileFilter=multiple_filters, dialogStyle=2, fm=1)
        if file_path is not None:
            cmds.file(file_path, open=True, force=True)
            reset_grades()
    
           
    def reload_file():
        ''' Reopens the opened file (to revert back any changes done to the file '''        
        if cmds.file(query=True, exists=True): # Check to see if it was ever saved
                    file_path = cmds.file(query=True, expandName=True)
                    if file_path is not None:
                        cmds.file(file_path, open=True, force=True)
        else:
            cmds.warning('File was never saved.')
    
      
    def reset_grades():
        ''' Resets all changes done to the script (for when switching between submissions) '''
        for note in gt_grading_notes:
            item_id = strip_string_as_id(gt_grading_notes.get(note)[0])
            button_name = "note_btn_" + item_id
            cmds.button(button_name, e=True, bgc=[.3,.3,.3], ann='0')
            
        for item in gt_grading_components:
            item_id = strip_string_as_id(gt_grading_components.get(item)[0])
            max_value = gt_grading_components.get(item)[1]
            cmds.intSliderGrp('grade_' + item_id, e=True,  value=max_value)
        
        cmds.intSliderGrp('late_submission_multiplier', e=True, value=0)

        update_grade_output()

    def toggle_joints():
        ''' Toggle the visibility of the joints (Hard coded)'''
              
        try:
            # Make Joints Visible
            all_transforms = cmds.ls(type='transform')
            for obj in all_transforms:
                if 'skeleton' in obj or 'joints' in obj:
                    if cmds.objExists(obj) and cmds.getAttr(obj + ".v" ,lock=True) is False:
                        cmds.setAttr(obj + '.v', 1)       

            all_joints = cmds.ls(type='joint')
            for obj in all_joints:
                if cmds.objExists(obj):
                    if cmds.getAttr(obj + ".radius" ,lock=True) is False:
                        cmds.setAttr(obj + '.radius', 1)
                        change_obj_color(obj ,rgb_color=(.4,0,.4))
                        if 'thumb' in obj or 'index' in obj or 'middle' in obj or 'ring' in obj or 'pinky' in obj or 'wrist' in obj or 'neck' in obj:
                            cmds.setAttr(obj + '.radius', .3)
                            
                        if 'root' in obj:
                            cmds.setAttr(obj + '.radius', 3)
                            
                        if 'head_jnt' in obj:
                            cmds.setAttr(obj + '.radius', .1)
                        
                        if 'eye' in obj:
                            cmds.setAttr(obj + '.radius', 5)
                        
                        if 'index' in obj or 'ring' in obj:
                            change_obj_color(obj ,rgb_color=(1,0,0))
                        elif 'middle' in obj or 'pinky' in obj or 'thumb' in obj or 'clavicle' in obj or 'jaw' in obj or 'ankle' in obj:
                            change_obj_color(obj ,rgb_color=(0,1,0))
                        elif 'eye' in obj:
                            change_obj_color(obj ,rgb_color=(1,1,1))
                        
                        if 'endJnt' in obj:
                            change_obj_color(obj ,rgb_color=(1,0,0))

                        
                    if cmds.getAttr(obj + ".v" ,lock=True) is False:
                        cmds.setAttr(obj + '.v', 1)   
            cmds.jointDisplayScale(1)
            
            # Use viewport as visibility toggle
            if gt_grading_settings.get('joints_visibility_state'):
            
                panel_list = cmds.getPanel(type="modelPanel")
            
                for each_panel in panel_list:
                    cmds.modelEditor(each_panel, e=1, joints=1, jointXray=1)
                    
                    
                gt_grading_settings['joints_visibility_state'] = False
            else:
                
                panel_list = cmds.getPanel(type="modelPanel")
            
                for each_panel in panel_list:
                    cmds.modelEditor(each_panel, e=1, joints=0, jointXray=0)
                
                
                gt_grading_settings['joints_visibility_state'] = True
                
        except Exception as exception:
            cmds.scrollField(output_scroll_field, e=True, clear=True)
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=str(exception) + '\n')
            
            
    def organization_file_name():
        ''' Performs many check to find obvious organization issues '''
        issues = ''

        # Check File Naming
        if cmds.file(query=True, exists=True): # Check to see if it was ever saved
                    file_path = cmds.file(query=True, expandName=True)
                    file_name = file_path.split('/')[-1]                    
                    extracted_name = re_file_name.findall(file_name) or []
                    if not len(extracted_name) >= 1:
                        issues += 'File name doesn\'t seem to follow the correct naming convention:\nFile name: "' + file_name + '".\n\n'
                    else:
                        issues = ''
        else:
            issues += 'The scene was never saved.\n\n'
        
                
        # Check File Type
        file_type = cmds.file(query=True, type=1)
        if file_type[0] != 'mayaAscii':
            issues += 'Your file must be saved as a ".ma".\n\n'
            
            
        # Check For non-unique objects
        all_transforms = cmds.ls(type = 'transform')
        already_checked = []
        non_unique_transforms = []
        for obj in all_transforms:
            short_name = get_short_name(obj)
            if short_name in already_checked:
                non_unique_transforms.append(short_name)
            already_checked.append(short_name)
            
        if len(non_unique_transforms) > 0:
            if len(non_unique_transforms) == 1:
                issues += str(len(non_unique_transforms)) + ' non-unique object found in the scene:\n'
            else:
                issues += str(len(non_unique_transforms)) + ' non-unique objects found in the scene:\n'
                 
            for obj in non_unique_transforms:
                issues += 'Multiple "' + obj + '" were found.\n'
            issues += '\n'
            
        # Check if keyframes were left behind
        all_keyframes = cmds.ls(type='animCurveTA')
        if len(all_keyframes) > 0:
            if len(all_keyframes) == 1:
                issues += str(len(all_keyframes)) + ' keyframe found in the scene:\n'
            else:
                issues += str(len(all_keyframes)) + ' keyframes found in the scene:\n'
                
            for keyframe in all_keyframes:
                issues += '"' + keyframe + '"\n'
            issues += '\n'
                          
              
        # Write issues to the output window
        if issues != '':
            cmds.scrollField(output_scroll_field, e=True, clear=True)
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=issues)
            cmds.scrollField(output_scroll_field, e=True, ip=1, it='') # Bring Back to the Top
        else:
            update_grade_output()
            cmds.scrollField(output_scroll_field, e=True, ip=0, it='No obvious organization issues were found.\n')
            
                
    def late_submission_check():
        '''Calculates late submissions'''
        
        result = cmds.promptDialog(
		title='Due Date',
		message='Please, provide a due date to calculate the difference.\n(The script uses the last modified date on the file as the submission date.)\n\nFormat: "MM/DD" for example "05/15"',
		button=['OK', 'Cancel'],
		defaultButton='OK',
		cancelButton='Cancel',
		dismissString='Cancel',
        text=str(datetime.now().month) + '/' + str(datetime.now().day))
        
        output = ''

        if result == 'OK':
            try:
                is_valid_due_date = True
                try:
                    input_date = cmds.promptDialog(query=True, text=True).split('/')     
                    due_date = datetime(datetime.now().year, int(input_date[0]), int(input_date[1]))
                except:
                    is_valid_due_date = False
                    due_date = datetime(datetime.now().year, datetime.now().month, datetime.now().day)
                
                
                if cmds.file(query=True, exists=True): # Check to see if it was ever saved
                    file_path = cmds.file(query=True, expandName=True)
                    file_name = file_path.split('/')[-1]
                    last_modified = datetime.strptime(time.ctime(os.path.getmtime(file_path)), "%a %b %d %H:%M:%S %Y")
                    submission_date = last_modified
                    output += 'File: ' + file_name + ("\n\nLast Modified:  %s" % str(last_modified.year) + ' / ' + str(last_modified.month).zfill(2) + ' / ' + str(last_modified.day).zfill(2) + ' - (' + last_modified.ctime() + ')')
                    if not is_valid_due_date:
                        output += '\nDue Date:        Failed to parse provided date.'
                    else:
                        output += '\nDue Date:        %s' % str(due_date.year) + ' / ' + str(due_date.month).zfill(2) + ' / ' + str(due_date.day).zfill(2) + ' - (' + due_date.ctime() + ')'
                    
                else:
                    output += 'File: untitled - (never saved)'
                    submission_date = datetime(datetime.now().year, datetime.now().month, datetime.now().day) 
                    
                    output += "\n\nLast Modified:  Failed to get last modified date (file was never modified)"
                    
                    if not is_valid_due_date:
                        output += '\nDue Date:        Failed to parse provided date.'
                    else:
                        output += '\nDue Date:        %s' % str(due_date.year) + ' / ' + str(due_date.month).zfill(2) + ' / ' + str(due_date.day).zfill(2) + ' - (' + due_date.ctime() + ')'
                
                today_date = datetime(datetime.now().year, datetime.now().month, datetime.now().day) 
                output += '\nToday\'s Date:   %s' % str(today_date.year) + ' / ' + str(today_date.month).zfill(2) + ' / ' + str(today_date.day).zfill(2) + ' - (' + today_date.ctime() + ')'

                delta = submission_date - due_date
                days_late = delta.days
                days_late_raw = days_late
                
                delta_today_vs_due = today_date - due_date
                
                if days_late > 10:
                    days_late = 10
                elif days_late < 0:
                    days_late = 0
                
                
                if not is_valid_due_date:
                    days_late = 0
                else:
                    output += '\n\nDifference between "Due Date" and "Today\'s Date" :  ' + str(delta_today_vs_due.days) 
                    output += '\nDifference between "Due Date" and "Last Modified" :  ' + str(days_late_raw) 
                    output += '\nLate Submission Penalty changed to :  ' + str(days_late) + '  (' + str(10*days_late) + '% penalty)'
                    
                cmds.intSliderGrp('late_submission_multiplier', e=True, value=days_late)
                #update_grade_output()
                
            except Exception as e:
                cmds.warning('Script failed to calculate dates. Check the window output for more information')
                output += '\n' + str(e)
       
        if output != '':
            cmds.scrollField(output_scroll_field, e=True, clear=True)
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=output)
            cmds.scrollField(output_scroll_field, e=True, ip=1, it='') # Bring Back to the Top


    def reset_viewport():
        ''' Changes the settings of the viewport to match what is necessary for this assignment '''
        try:
            panel_list = cmds.getPanel(type="modelPanel")
        
            for each_panel in panel_list:
                cmds.modelEditor(each_panel, e=1, allObjects=0)
                cmds.modelEditor(each_panel, e=1, polymeshes=1)
                cmds.modelEditor(each_panel, e=1, joints=0)
                cmds.modelEditor(each_panel, e=1, jx=1)
                cmds.modelEditor(each_panel, e=1, nurbsCurves=1)
                cmds.modelEditor(each_panel, e=1, ikHandles=1)
                cmds.modelEditor(each_panel, e=1, locators=1)
                cmds.modelEditor(each_panel, e=1, grid=1)
                cmds.modelEditor(each_panel, e=1, displayLights='default')
                cmds.modelEditor(each_panel, e=1, udm=False)
                cmds.modelEditor(each_panel, e=1, wireframeOnShaded=0)
                cmds.modelEditor(each_panel, e=1, displayTextures=1)
                cmds.DisplayShadedAndTextured()
                set_display_layers_visibility(True)
                set_display_layers_type(0)
                reset_persp_shape_attributes()
        except Exception as exception:
            cmds.scrollField(output_scroll_field, e=True, clear=True)
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=str(exception) + '\n')


    def brute_force_naming():
        '''
        Goes through the dictionary "brute_force_joint_naming_dict" and automatically renames objects that are within the provided radius of a point.
        This function uses another function called "is_point_inside_mesh", which can be found below
        
        Uses the function "search_delete_temp_meshes(starts_with)" to delete meshes during exceptions.
        
        '''
        to_rename = []
        errors = '' 
        
        
        # Ctrls
        all_nurbs_curves = cmds.ls(type='nurbsCurve', long=True)
        for obj in brute_force_ctrl_naming_dict:
            if type(brute_force_ctrl_naming_dict.get(obj)[2]) is tuple:
                new_scale = brute_force_ctrl_naming_dict.get(obj)[2]
                ray_tracing_obj = cmds.polySphere(name=('ray_tracing_obj_' + obj), r=1, sx=8, sy=8, ch=False, cuv=False)
                if cmds.objExists(ray_tracing_obj[0]):
                    cmds.setAttr(ray_tracing_obj[0] + '.scaleX', new_scale[0])
                    cmds.setAttr(ray_tracing_obj[0] + '.scaleY', new_scale[1])
                    cmds.setAttr(ray_tracing_obj[0] + '.scaleZ', new_scale[2])
            else:
                ray_tracing_obj = cmds.polySphere(name=('ray_tracing_obj_' + obj), r=brute_force_ctrl_naming_dict.get(obj)[2], sx=8, sy=8, ch=False, cuv=False)
                cmds.xform(ray_tracing_obj, ws=True, ro=(0,0,90) )
                cmds.makeIdentity(ray_tracing_obj, apply=True, rotate=True)
            cmds.xform(ray_tracing_obj, a=True, ro=brute_force_ctrl_naming_dict.get(obj)[1] )
            cmds.xform(ray_tracing_obj, a=True, t=brute_force_ctrl_naming_dict.get(obj)[0] )
            
            for crv in all_nurbs_curves:
                try:
                    crv_transform = cmds.listRelatives(crv, allParents=True, f=True) or []
                    if len(crv_transform) > 0:
                        crv_pos = cmds.xform(crv_transform[0], piv=True , q=True , ws=True)
                        is_crv_inside = is_point_inside_mesh(ray_tracing_obj[0], point=(crv_pos[0],crv_pos[1],crv_pos[2]))
                                                
                        ignore_crv = False
                        if len(brute_force_ctrl_naming_dict.get(obj)) == 4: # Undesired Strings
                            for string in brute_force_ctrl_naming_dict.get(obj)[3]:
                                if string in get_short_name(crv_transform[0]):
                                    ignore_crv = True
                        
                        if len(brute_force_ctrl_naming_dict.get(obj)) == 5: # Undesired Parent
                            crv_transform_parent = cmds.listRelatives(crv_transform[0], allParents=True, f=True) or []
                            if len(crv_transform_parent) > 0:
                                for string in brute_force_ctrl_naming_dict.get(obj)[4]:
                                    if string in get_short_name(crv_transform_parent[0]):
                                        ignore_crv = True
                                    
                        if is_crv_inside and get_short_name(crv_transform[0]) != obj and ignore_crv is False:
                            to_rename.append([crv_transform[0], obj])
                except Exception as e:
                    errors += str(e) + '\n'
            cmds.delete(ray_tracing_obj)

        # Sort it based on how many parents it has
        pipe_pairs_to_rename = []
        for obj in to_rename:
            pipe_pairs_to_rename.append([len(obj[0].split('|')), obj])
            
        sorted_pairs_to_rename = sorted(pipe_pairs_to_rename, key=lambda x: x[0], reverse=True)

        # Rename sorted pairs   
        for pair in sorted_pairs_to_rename:
            if cmds.objExists(pair[1][0]):
                try:
                    cmds.rename(pair[1][0], pair[1][1])
                except Exception as exception:
                    errors = errors + '"' + str(pair[1][1]) + '" : "' + exception[0].rstrip("\n") + '".\n'
        if errors != '':
                search_delete_temp_meshes('ray_tracing_obj_')
                cmds.scrollField(output_scroll_field, e=True, clear=True)
                cmds.scrollField(output_scroll_field, e=True, ip=0, it='Some errors were raised:\n' + errors)
                cmds.scrollField(output_scroll_field, e=True, ip=1, it='') # Bring Back to the Top
    

def reset_persp_shape_attributes():
    '''
    If persp shape exists (default camera), reset its attributes
    '''
    if cmds.objExists('perspShape'):
        try:
            cmds.setAttr('perspShape' + ".focalLength", 35)
            cmds.setAttr('perspShape' + ".verticalFilmAperture", 0.945)
            cmds.setAttr('perspShape' + ".horizontalFilmAperture", 1.417)
            cmds.setAttr('perspShape' + ".lensSqueezeRatio", 1)
            cmds.setAttr('perspShape' + ".fStop", 5.6)
            cmds.setAttr('perspShape' + ".focusDistance", 5)
            cmds.setAttr('perspShape' + ".shutterAngle", 144)
            cmds.setAttr('perspShape' + ".locatorScale", 1)
            cmds.setAttr('perspShape' + ".nearClipPlane", 0.100)
            cmds.setAttr('perspShape' + ".farClipPlane", 10000.000)
            cmds.setAttr('perspShape' + ".cameraScale", 1)
            cmds.setAttr('perspShape' + ".preScale", 1)
            cmds.setAttr('perspShape' + ".postScale", 1)
            cmds.setAttr('perspShape' + ".depthOfField", 0)
        except:
            pass

def delete_control_rig():
    '''
    Delete the control rig out of the betty rig 
    
    '''
    
    # Check for wire system
    wire_system_status = False
    for wire_obj in wire_system_elements:
        if cmds.objExists(wire_obj):
            cmds.delete(wire_obj)
            wire_system_status = True
            
    if cmds.objExists('eye_elements_mainWireGrp') and cmds.objExists('head_jnt'):
        cmds.delete('eye_elements_mainWireGrp')
        wire_system_status = True
    
    if wire_system_status is True:
        for eye_geo in eye_mesh_elements:
                if cmds.objExists(eye_geo) and cmds.objExists('head_jnt'):
                    cmds.parent(eye_geo,"headJnt")
                    
    # Parent certain objects to the world
    if len(unparent_list) > 0: 
        for obj in unparent_list:
            if cmds.objExists(obj):
                cmds.select(obj)
                try:
                    cmds.parent(world = True)
                except:
                    pass
    
    # Delete undesired objects
    for obj in delete_list:
        if cmds.objExists(obj):
            cmds.select(obj)
            deletion_container = cmds.ls(selection=True)[0]
            cmds.delete(deletion_container)
    
    cmds.select(d=True)
            
    print(' ')
    

def delete_all_keyframes():
    '''Deletes all nodes of the type "animCurveTA" (keyframes)'''
    keys_ta = cmds.ls(type='animCurveTA')
    keys_tl = cmds.ls(type='animCurveTL')
    keys_tt = cmds.ls(type='animCurveTT')
    keys_tu = cmds.ls(type='animCurveTU')
    #keys_ul = cmds.ls(type='animCurveUL')
    #keys_ua = cmds.ls(type='animCurveUA')
    #keys_ut = cmds.ls(type='animCurveUT')
    #keys_uu = cmds.ls(type='animCurveUU')
    all_keyframes = keys_ta + keys_tl + keys_tt + keys_tu
    for obj in all_keyframes:
        try:
            cmds.delete(obj)
        except:
            pass
                    
def reset_transforms():
    '''Modified version of the reset transforms. It checks for incomming connections, then set the attribute to 0 if there are none'''
    all_joints = cmds.ls(type='joint')
    all_meshes = cmds.ls(type='mesh')
    all_transforms = cmds.ls(type='transform')
    
    for obj in all_meshes:
        try:
            mesh_transform = ''
            mesh_transform_extraction = cmds.listRelatives(obj, allParents=True) or []
            if len(mesh_transform_extraction) > 0:
                mesh_transform = mesh_transform_extraction[0]
            
            if len(mesh_transform_extraction) > 0 and cmds.objExists(mesh_transform) and 'shape' not in cmds.nodeType(mesh_transform, inherited=True):
                mesh_connection_rx = cmds.listConnections( mesh_transform + '.rotateX', d=False, s=True ) or []
                if not len(mesh_connection_rx) > 0:
                    if cmds.getAttr(mesh_transform + '.rotateX', lock=True) is False:
                        cmds.setAttr(mesh_transform + '.rotateX', 0)
                mesh_connection_ry = cmds.listConnections( mesh_transform + '.rotateY', d=False, s=True ) or []
                if not len(mesh_connection_ry) > 0:
                    if cmds.getAttr(mesh_transform + '.rotateY', lock=True) is False:
                        cmds.setAttr(mesh_transform + '.rotateY', 0)
                mesh_connection_rz = cmds.listConnections( mesh_transform + '.rotateZ', d=False, s=True ) or []
                if not len(mesh_connection_rz) > 0:
                    if cmds.getAttr(mesh_transform + '.rotateZ', lock=True) is False:
                        cmds.setAttr(mesh_transform + '.rotateZ', 0)

                mesh_connection_sx = cmds.listConnections( mesh_transform + '.scaleX', d=False, s=True ) or []
                if not len(mesh_connection_sx) > 0:
                    if cmds.getAttr(mesh_transform + '.scaleX', lock=True) is False:
                        cmds.setAttr(mesh_transform + '.scaleX', 1)
                mesh_connection_sy = cmds.listConnections( mesh_transform + '.scaleY', d=False, s=True ) or []
                if not len(mesh_connection_sy) > 0:
                    if cmds.getAttr(mesh_transform + '.scaleY', lock=True) is False:
                        cmds.setAttr(mesh_transform + '.scaleY', 1)
                mesh_connection_sz = cmds.listConnections( mesh_transform + '.scaleZ', d=False, s=True ) or []
                if not len(mesh_connection_sz) > 0:
                    if cmds.getAttr(mesh_transform + '.scaleZ', lock=True) is False:
                        cmds.setAttr(mesh_transform + '.scaleZ', 1)
        except Exception as e:
            raise e
            
    for jnt in all_joints:
        try:
            joint_connection_rx = cmds.listConnections( jnt + '.rotateX', d=False, s=True ) or []
            if not len(joint_connection_rx) > 0:
                if cmds.getAttr(jnt + '.rotateX', lock=True) is False:
                    cmds.setAttr(jnt + '.rotateX', 0)
            joint_connection_ry = cmds.listConnections( jnt + '.rotateY', d=False, s=True ) or []
            if not len(joint_connection_ry) > 0:
                if cmds.getAttr(jnt + '.rotateY', lock=True) is False:
                    cmds.setAttr(jnt + '.rotateY', 0)
            joint_connection_rz = cmds.listConnections( jnt + '.rotateZ', d=False, s=True ) or []
            if not len(joint_connection_rz) > 0:
                if cmds.getAttr(jnt + '.rotateZ', lock=True) is False:
                    cmds.setAttr(jnt + '.rotateZ', 0)

            joint_connection_sx = cmds.listConnections( jnt + '.scaleX', d=False, s=True ) or []
            if not len(joint_connection_sx) > 0:
                if cmds.getAttr(jnt + '.scaleX', lock=True) is False:
                    cmds.setAttr(jnt + '.scaleX', 1)
            joint_connection_sy = cmds.listConnections( jnt + '.scaleY', d=False, s=True ) or []
            if not len(joint_connection_sy) > 0:
                if cmds.getAttr(jnt + '.scaleY', lock=True) is False:
                    cmds.setAttr(jnt + '.scaleY', 1)
            joint_connection_sz = cmds.listConnections( jnt + '.scaleZ', d=False, s=True ) or []
            if not len(joint_connection_sz) > 0:
                if cmds.getAttr(jnt + '.scaleZ', lock=True) is False:
                    cmds.setAttr(jnt + '.scaleZ', 1)
        except Exception as e:
            raise e

    for obj in all_transforms:
        try:
            if 'ctrl' in obj.lower() and 'ctrlgrp' not in obj.lower():
                
                obj_connection_tx = cmds.listConnections( obj + '.tx', d=False, s=True ) or []
                if not len(obj_connection_tx) > 0:
                    if cmds.getAttr(obj + '.tx', lock=True) is False:
                        cmds.setAttr(obj + '.tx', 0)
                obj_connection_ty = cmds.listConnections( obj + '.ty', d=False, s=True ) or []
                if not len(obj_connection_ty) > 0:
                    if cmds.getAttr(obj + '.ty', lock=True) is False:
                        cmds.setAttr(obj + '.ty', 0)
                obj_connection_tz = cmds.listConnections( obj + '.tz', d=False, s=True ) or []
                if not len(obj_connection_tz) > 0:
                    if cmds.getAttr(obj + '.tz', lock=True) is False:
                        cmds.setAttr(obj + '.tz', 0)
                
                obj_connection_rx = cmds.listConnections( obj + '.rotateX', d=False, s=True ) or []
                if not len(obj_connection_rx) > 0:
                    if cmds.getAttr(obj + '.rotateX', lock=True) is False:
                        cmds.setAttr(obj + '.rotateX', 0)
                obj_connection_ry = cmds.listConnections( obj + '.rotateY', d=False, s=True ) or []
                if not len(obj_connection_ry) > 0:
                    if cmds.getAttr(obj + '.rotateY', lock=True) is False:
                        cmds.setAttr(obj + '.rotateY', 0)
                obj_connection_rz = cmds.listConnections( obj + '.rotateZ', d=False, s=True ) or []
                if not len(obj_connection_rz) > 0:
                    if cmds.getAttr(obj + '.rotateZ', lock=True) is False:
                        cmds.setAttr(obj + '.rotateZ', 0)

                obj_connection_sx = cmds.listConnections( obj + '.scaleX', d=False, s=True ) or []
                if not len(obj_connection_sx) > 0:
                    if cmds.getAttr(obj + '.scaleX', lock=True) is False:
                        cmds.setAttr(obj + '.scaleX', 1)
                obj_connection_sy = cmds.listConnections( obj + '.scaleY', d=False, s=True ) or []
                if not len(obj_connection_sy) > 0:
                    if cmds.getAttr(obj + '.scaleY', lock=True) is False:
                        cmds.setAttr(obj + '.scaleY', 1)
                obj_connection_sz = cmds.listConnections( obj + '.scaleZ', d=False, s=True ) or []
                if not len(obj_connection_sz) > 0:
                    if cmds.getAttr(obj + '.scaleZ', lock=True) is False:
                        cmds.setAttr(obj + '.scaleZ', 1)
                        
                # Only for this assignment:
                attributes_to_reset = ['heelRoll', 'HeelRoll', 'heelroll', 'toeRoll', 'ToeRoll', 'toeroll', 'ballRoll', 'BallRoll', 'ballroll']
                for attr in attributes_to_reset:
                    if cmds.attributeQuery(attr, node=obj, exists=True):
                        if cmds.getAttr(obj + '.' + attr, lock=True) is False:
                            cmds.setAttr(obj + '.' + attr, 0)
        except Exception as e:
            raise e



def set_display_layers_visibility(visibility_state):
    '''
    Sets display layer visibility
    
            Parameters:
                visibility_state (bool): New state for the visibility of all display layers
    '''
    layers = cmds.ls(long=True, type='displayLayer')
    for l in layers[0:]:	
		if l.find("defaultLayer") == -1:													
			cmds.setAttr( '%s.visibility' % l, visibility_state)


def set_display_layers_type(display_layer_type):
    '''
    Sets display layer type (template, reference, etc...)
    
            Parameters:
                display_layer_type (int): New state for the type of every display layer
    '''
    layers = cmds.ls(long=True, type='displayLayer')
    for l in layers[0:]:	
		if l.find("defaultLayer") == -1:
                    cmds.setAttr(l + '.displayType', display_layer_type)


def apply_simple_checker_shader(obj_list):
    '''
    Applies a new lambert with a checker to objects in the list
    
            Parameters:
                obj_list (list): A list of objects (strings) that will receive the new shader
    '''
    for node in obj_list:
        if cmds.objExists(node):
            shd = cmds.shadingNode('lambert', name="%s_lambert" % node, asShader=True)
            shdSG = cmds.sets(name='%sSG' % shd, empty=True, renderable=True, noSurfaceShader=True)
            cmds.connectAttr('%s.outColor' % shd, '%s.surfaceShader' % shdSG)
            cmds.sets(node, e=True, forceElement=shdSG)
            checkerNode = cmds.shadingNode("checker", asTexture=True, n = "Checker_%s" % node)
            checkerUVNode = cmds.shadingNode("place2dTexture", asTexture=True, n = "text_%s" % node)
            cmds.connectAttr('%s.outColor' %checkerNode,'%s.color' %shd)
            cmds.connectAttr('%s.outUV' %checkerUVNode,'%s.uvCoord' %checkerNode)
            cmds.connectAttr('%s.outUvFilterSize' %checkerUVNode,'%s.uvFilterSize' %checkerNode)
            cmds.setAttr(checkerUVNode + ".repeatU", 4)
            cmds.setAttr(checkerUVNode + ".repeatV", 4)         
 
def key_arms(shoulder_name, elbow_name, keyframes_interval):
    '''Keys Arm Joints (Used for upper body and symmetry steps)'''
    if cmds.objExists(elbow_name):
        try:
            cmds.select(elbow_name)
            elbow_selection = cmds.ls(selection=True)[0]
            cmds.setKeyframe(elbow_selection, v=0, at='rotateZ', t=(keyframes_interval * 4))
            cmds.setKeyframe(elbow_selection, v=-90, at='rotateZ', t=(keyframes_interval * 5 ))
            cmds.setKeyframe(elbow_selection, v=0, at='rotateZ', t=(keyframes_interval * 6))
            if cmds.objExists(shoulder_name):
                cmds.select(shoulder_name)
                shoulder_selection = cmds.ls(selection=True)[0]
                cmds.setKeyframe(shoulder_selection, v=0, at='rotateY', t=(keyframes_interval * 6))
                cmds.setKeyframe(shoulder_selection, v=-50, at='rotateY', t=(keyframes_interval * 7 ))
                cmds.setKeyframe(shoulder_selection, v=0, at='rotateY', t=(keyframes_interval * 8 ))
                cmds.setKeyframe(shoulder_selection, v=0, at='rotateZ', t=(keyframes_interval * 8 ))
                cmds.setKeyframe(shoulder_selection, v=-50, at='rotateZ', t=(keyframes_interval * 9 ))
                cmds.setKeyframe(shoulder_selection, v=0, at='rotateZ', t=(keyframes_interval * 10 ))
        except:
            pass


def key_spine(spine_ctrls, keyframes_interval):
    '''Key Spine Joints (Used for upper body and symmetry steps)'''
    for spine in spine_ctrls:
        if cmds.objExists(spine):
            try:
                cmds.select(spine)
                spine = cmds.ls(selection=True)[0]
                cmds.setKeyframe(spine, v=0, at='rotateZ', t=(keyframes_interval * 10))
                cmds.setKeyframe(spine, v=30, at='rotateZ', t=(keyframes_interval * 11 ))
                cmds.setKeyframe(spine, v=-30, at='rotateZ', t=(keyframes_interval * 13 ))
                cmds.setKeyframe(spine, v=0, at='rotateZ', t=(keyframes_interval * 14))
            except:
                pass
                
                            
def frame_object(obj):
    '''
    Focus the currently active camera on an object
    
            Parameters:
                obj (string): Name of the object to focus
    '''
    
    if cmds.objExists(obj):
        cmds.select(obj)
        cmds.FrameSelectedWithoutChildren()
        cmds.select(d=True) 
 
 
def clean_rotation(obj_list):
    '''
    Cleans rotation by deleting keyframes and reseting it back to zero
    
            Parameters:
                obj_list (list): A list of objects (strings) that will receive the new shader
    '''
    for obj in obj_list:
        if cmds.objExists(obj):
            cmds.select(obj)
            my_obj = cmds.ls(selection=True)[0]
            cmds.cutKey(my_obj, time = (-5000, 5000), clear = True)
            cmds.setAttr(my_obj + ".rotate", 0,0,0)

      
def keyframe_list(obj_list, value, attribute, at_frame):
    '''
    Keys rotation for an entire list 
    
            Parameters:
                obj_list (list): A list of objects (strings) that will receive the new shader
                value (float, int): keyframe value (e.g. 1 or 2...)
                attribute (string): name of the attribute "e.g. rotation"
                at_frame (int): What frame (time) the keyframe should be
    '''
    for obj in obj_list:
        if cmds.objExists(obj):
            try:
                cmds.select(obj)
                my_obj = cmds.ls(selection=True)[0]
                cmds.setKeyframe(my_obj, v=value, at=attribute, t=at_frame )
            except:
                pass


            
def unsubdivide_geometries():
    ''' 
    Unsubdivides all geometry by changing their display smoothness to zero
    This function ignores errors! (In case something is locked)
    '''
    all_geo = cmds.ls(type='mesh')
    for obj in all_geo:
        try:
            if cmds.objExists(obj):
                cmds.displaySmoothness(obj, polygonObject=1)
        except:
            pass

            
def fk_system_upper_body():
    '''Checks FK System (Upper Body)'''
    
    # Reset other buttons
    for item in gt_grading_components:
        item_id = strip_string_as_id(gt_grading_components.get(item)[0])
        if 'fk_system_upper_body' not in item_id:
            cmds.button('check_btn_' + item_id, e=True, l='Check', bgc=[.5,.7,.5], ann='0')
    delete_all_keyframes()
    reset_transforms()
    
    # Check Button Status
    button_status = int(cmds.button('check_btn_fk_system_upper_body', q=True, ann=True))
    if not button_status:
        # Change button to stop and update its status
        cmds.button('check_btn_fk_system_upper_body', e=True, l='Stop', bgc=[.5,.2,.2], ann='1')
        
        # Unsubdivide Meshes
        unsubdivide_geometries()
        
        # Give eyes a Checker Material
        if cmds.objExists('left_pupil_geo') and cmds.objExists('right_pupil_geo'):
            apply_simple_checker_shader(["left_pupil_geo", "right_pupil_geo"])
            
        # Reset Time
        cmds.currentTime(0)
        
        # Adjust Size of the timeline
        keyframes_interval = gt_grading_settings.get('keyframes_interval') + 5
        cmds.playbackOptions(minTime=0, max = (keyframes_interval * 14))
        
        # Focus On Desired Area
        frame_object('body')
        frame_object('body_geo')
        
   
        # Start Animating
        middle_fingers_ctrls_ctrl_offset = 3
        ring_fingers_ctrls_ctrl_offset = middle_fingers_ctrls_ctrl_offset + middle_fingers_ctrls_ctrl_offset
        pinky_fingers_ctrls_ctrl_offset = ring_fingers_ctrls_ctrl_offset + middle_fingers_ctrls_ctrl_offset
        wait_before_arm_offset = 2
           
        #Key Thumb Fingers
        unlock_attribute(thumb_fingers_ctrls, 'rotateZ')
        keyframe_list(thumb_fingers_ctrls, 15, 'rotateZ', (keyframes_interval * 2))
        keyframe_list(thumb_fingers_ctrls, -25, 'rotateZ', (keyframes_interval * 3))
        keyframe_list(thumb_fingers_ctrls, 0, 'rotateZ', (keyframes_interval * 4))
            
        #Key Index Fingers
        unlock_attribute(index_fingers_ctrls, 'rotateZ')
        keyframe_list(index_fingers_ctrls, 0, 'rotateZ', 0)
        keyframe_list(index_fingers_ctrls, -70, 'rotateZ', keyframes_interval)
        current_frame_time = keyframes_interval + keyframes_interval;
        keyframe_list(index_fingers_ctrls, 0, 'rotateZ', current_frame_time)
        
        #Key Middle Fingers
        unlock_attribute(middle_fingers_ctrls, 'rotateZ')
        keyframe_list(middle_fingers_ctrls, 0, 'rotateZ', (0 + middle_fingers_ctrls_ctrl_offset))
        keyframe_list(middle_fingers_ctrls, -70, 'rotateZ', (keyframes_interval + middle_fingers_ctrls_ctrl_offset))
        current_frame_time = keyframes_interval + keyframes_interval;
        keyframe_list(middle_fingers_ctrls, 0, 'rotateZ', (current_frame_time + middle_fingers_ctrls_ctrl_offset))
        
        #Key Ring Fingers
        unlock_attribute(ring_fingers_ctrls, 'rotateZ')
        keyframe_list(ring_fingers_ctrls, 0, 'rotateZ', (0 + ring_fingers_ctrls_ctrl_offset))
        keyframe_list(ring_fingers_ctrls, -70, 'rotateZ', (keyframes_interval + ring_fingers_ctrls_ctrl_offset))
        current_frame_time = keyframes_interval + keyframes_interval;
        keyframe_list(ring_fingers_ctrls, 0, 'rotateZ', (current_frame_time + ring_fingers_ctrls_ctrl_offset))
        
        #Key Pinky Fingers
        unlock_attribute(pinky_fingers_ctrls, 'rotateZ')
        keyframe_list(pinky_fingers_ctrls, 0, 'rotateZ', (0 + pinky_fingers_ctrls_ctrl_offset))
        keyframe_list(pinky_fingers_ctrls, -70, 'rotateZ', (keyframes_interval + pinky_fingers_ctrls_ctrl_offset))
        current_frame_time = keyframes_interval + keyframes_interval;
        keyframe_list(pinky_fingers_ctrls, 0, 'rotateZ', (current_frame_time + pinky_fingers_ctrls_ctrl_offset))
        
        #Key Shoulder and Elbow Joints
        unlock_attribute(['left_shoulder_ctrl','left_elbow_ctrl', 'right_shoulder_ctrl','right_elbow_ctrl'], 'rotateZ')
        key_arms('left_shoulder_ctrl','left_elbow_ctrl', keyframes_interval)
        key_arms('right_shoulder_ctrl','right_elbow_ctrl', keyframes_interval)

        key_spine(spine_ctrls, keyframes_interval)
        
        #Head Ctrls
        # If head exists, add animation to it
        if cmds.objExists('head_ctrl'):
            cmds.select('head_ctrl')
            head_ctrl = cmds.ls(selection=True)[0]
            # Move Front and Back
            unlock_attribute(head_ctrl, 'rotateZ')
            cmds.setKeyframe( head_ctrl, v=0, at='rotateZ', t=current_frame_time )
            current_frame_time += keyframes_interval
            cmds.setKeyframe( head_ctrl, v=30, at='rotateZ', t=current_frame_time )
            current_frame_time += keyframes_interval
            cmds.setKeyframe( head_ctrl, v=0, at='rotateZ', t=current_frame_time )
            current_frame_time += keyframes_interval
            cmds.setKeyframe( head_ctrl, v=-30, at='rotateZ', t=current_frame_time )
            current_frame_time += keyframes_interval
            cmds.setKeyframe( head_ctrl, v=0, at='rotateZ', t=current_frame_time )
            # Move to Left and Right
            unlock_attribute(head_ctrl, 'rotateY')
            cmds.setKeyframe( head_ctrl, v=0, at='rotateY', t=current_frame_time )
            current_frame_time += keyframes_interval
            cmds.setKeyframe( head_ctrl, v=30, at='rotateY', t=current_frame_time )
            current_frame_time += keyframes_interval
            cmds.setKeyframe( head_ctrl, v=0, at='rotateY', t=current_frame_time )
            current_frame_time += keyframes_interval
            cmds.setKeyframe( head_ctrl, v=-30, at='rotateY', t=current_frame_time )
            current_frame_time += keyframes_interval
            cmds.setKeyframe( head_ctrl, v=0, at='rotateY', t=current_frame_time )
            # Move to Left and Right
            unlock_attribute(head_ctrl, 'rotateX')
            cmds.setKeyframe( head_ctrl, v=0, at='rotateX', t=current_frame_time )
            current_frame_time += keyframes_interval
            cmds.setKeyframe( head_ctrl, v=30, at='rotateX', t=current_frame_time )
            current_frame_time += keyframes_interval
            cmds.setKeyframe( head_ctrl, v=0, at='rotateX', t=current_frame_time )
            current_frame_time += keyframes_interval
            cmds.setKeyframe( head_ctrl, v=-30, at='rotateX', t=current_frame_time )
            current_frame_time += keyframes_interval
            cmds.setKeyframe( head_ctrl, v=0, at='rotateX', t=current_frame_time )
        else:
            print("Missing head_ctrl!")
        
        # if Jaw exists add animation to it
        if cmds.objExists('jaw_ctrl'):
            cmds.select('jaw_ctrl')
            jaw_ctrl = cmds.ls(selection=True)[0]
            # Move Front and Back
            unlock_attribute( jaw_ctrl, 'rotateZ')
            cmds.setKeyframe( jaw_ctrl, v=0, at='rotateZ', t=0 )
            cmds.setKeyframe( jaw_ctrl, v=30, at='rotateZ', t=(keyframes_interval* 1.5) )
            cmds.setKeyframe( jaw_ctrl, v=0, at='rotateZ', t=(keyframes_interval* 3) )
        else:
            print("Missing jaw_ctrl!")
           
        if cmds.objExists('main_eye_ctrl'):
            unlock_attribute( ['main_eye_ctrl'], 'visibility')
            cmds.setAttr("main_eye_ctrl.visibility", 0)
            
        if cmds.objExists('main_eyes_ctrl'):
            unlock_attribute( ['main_eyes_ctrl'], 'visibility')
            cmds.setAttr("main_eyes_ctrl.visibility", 0)
                    
        # Clean Selection
        cmds.select(clear=True)
        
        # Play Animation
        cmds.PlaybackForward()
        
    else:
        #Remove Key frames from previous step)
        delete_all_keyframes()
        reset_transforms()
        cmds.button('check_btn_fk_system_upper_body', e=True, l='Check', bgc=[.5,.7,.5], ann='0')
        cmds.play(state=False)
        cmds.currentTime(0)


def ik_system_lower_body():
    '''Checks IK System (Lower Body)'''
    
    # Reset other buttons
    for item in gt_grading_components:
        item_id = strip_string_as_id(gt_grading_components.get(item)[0])
        if 'ik_system_lower_body' not in item_id:
            cmds.button('check_btn_' + item_id, e=True, l='Check', bgc=[.5,.7,.5], ann='0')
    delete_all_keyframes()
    reset_transforms()
    
    # Check Button Status
    button_status = int(cmds.button('check_btn_ik_system_lower_body', q=True, ann=True))
    if not button_status:
        # Change button to stop and update its status
        cmds.button('check_btn_ik_system_lower_body', e=True, l='Stop', bgc=[.5,.2,.2], ann='1')
        
        # Unsubdivide Meshes
        unsubdivide_geometries()
        
        # Give eyes a Checker Material
        if cmds.objExists('left_pupil_geo') and cmds.objExists('right_pupil_geo'):
            apply_simple_checker_shader(["left_pupil_geo", "right_pupil_geo"])
            
        # Reset Time
        cmds.currentTime(0)
        
        # Adjust Size of the timeline
        keyframes_interval = gt_grading_settings.get('keyframes_interval') + 3
        cmds.playbackOptions(minTime=0, max = (keyframes_interval * 18))
        
        # Focus On Desired Area
        frame_object('body')
        frame_object('body_geo')
        
        # Start Animating
        # First Step IK
        unlock_attribute(foot_ctrls, 'translateY')
        unlock_attribute(foot_ctrls, 'translateZ')
        unlock_attribute(foot_ctrls, 'rotateX')
        
        keyframe_list(foot_ctrls, 0, 'translateY', 0)
        keyframe_list(foot_ctrls, 30, 'translateY', keyframes_interval + (keyframes_interval/2))
        keyframe_list(foot_ctrls, 0, 'translateY', (keyframes_interval* 3))
        
        keyframe_list(foot_ctrls, 0, 'translateZ', 0)
        keyframe_list(foot_ctrls, 15, 'translateZ', keyframes_interval + (keyframes_interval/2))
        keyframe_list(foot_ctrls, 0, 'translateZ', (keyframes_interval* 3))
        
        keyframe_list(foot_ctrls, 0, 'rotateX', 0)
        keyframe_list(foot_ctrls, 30, 'rotateX', keyframes_interval + (keyframes_interval/2))
        keyframe_list(foot_ctrls, 0, 'rotateX', (keyframes_interval* 3))

        # Second Step IK
        keyframe_list(foot_ctrls, 0, 'translateY', (keyframes_interval* 3))
        keyframe_list(foot_ctrls, 15, 'translateY', (keyframes_interval* 4))
        keyframe_list(foot_ctrls, 0, 'translateY', (keyframes_interval* 5))
        
        keyframe_list(foot_ctrls, 0, 'translateX', (keyframes_interval* 3))
        keyframe_list(foot_ctrls, 40, 'translateX', (keyframes_interval* 4))
        keyframe_list(foot_ctrls, 0, 'translateX', (keyframes_interval* 5))
                
        # Third Step IK
        keyframe_list(foot_ctrls, 0, 'heelRoll', (keyframes_interval* 5))
        keyframe_list(foot_ctrls, 10, 'heelRoll', (keyframes_interval* 6))
        keyframe_list(foot_ctrls, 0, 'heelRoll', (keyframes_interval* 7))
        
        keyframe_list(foot_ctrls, 0, 'ballRoll', (keyframes_interval* 7))
        keyframe_list(foot_ctrls, 10, 'ballRoll', (keyframes_interval* 8))
        keyframe_list(foot_ctrls, 0, 'ballRoll', (keyframes_interval* 9))
        
        keyframe_list(foot_ctrls, 0, 'toeRoll', (keyframes_interval* 9))
        keyframe_list(foot_ctrls, 10, 'toeRoll', (keyframes_interval* 10))
        keyframe_list(foot_ctrls, 0, 'toeRoll', (keyframes_interval* 11))
        
        # Change if HeelRoll, BallRoll or ToeRoll
        keyframe_list(foot_ctrls, 0, 'HeelRoll', (keyframes_interval* 5))
        keyframe_list(foot_ctrls, 10, 'HeelRoll', (keyframes_interval* 6))
        keyframe_list(foot_ctrls, 0, 'HeelRoll', (keyframes_interval* 7))
        
        keyframe_list(foot_ctrls, 0, 'BallRoll', (keyframes_interval* 7))
        keyframe_list(foot_ctrls, 10, 'BallRoll', (keyframes_interval* 8))
        keyframe_list(foot_ctrls, 0, 'BallRoll', (keyframes_interval* 9))
        
        keyframe_list(foot_ctrls, 0, 'ToeRoll', (keyframes_interval* 9))
        keyframe_list(foot_ctrls, 10, 'ToeRoll', (keyframes_interval* 10))
        keyframe_list(foot_ctrls, 0, 'ToeRoll', (keyframes_interval* 11))

        # Fourth Step IK
        keyframe_list(foot_ctrls, 0, 'translateY', (keyframes_interval* 11))
        keyframe_list(foot_ctrls, 10, 'translateY', (keyframes_interval* 12))
        keyframe_list(foot_ctrls, 10, 'translateY', (keyframes_interval* 13))
        keyframe_list(foot_ctrls, 0, 'translateY', (keyframes_interval* 14))
        
        keyframe_list(knee_ctrls, 0, 'translateX', (keyframes_interval* 11))
        keyframe_list(knee_ctrls, 40, 'translateX', (keyframes_interval* 12))
        keyframe_list(knee_ctrls, 0, 'translateX', (keyframes_interval* 13))
        
        keyframe_list(knee_ctrls, 0, 'translateX', (keyframes_interval* 13))
        keyframe_list(knee_ctrls, -40, 'translateX', (keyframes_interval* 14))
        keyframe_list(knee_ctrls, 0, 'translateX', (keyframes_interval* 15))
        
      
        # Move Hip (Root) Down
        if cmds.objExists('root_ctrl'):
            try:
                unlock_attribute(['root_ctrl'], 'translateX')
                unlock_attribute(['root_ctrl'], 'translateY')
                unlock_attribute(['root_ctrl'], 'translateZ')
                cmds.setKeyframe('root_ctrl', at='ty', t=(keyframes_interval* 15) )
                cmds.setKeyframe('root_ctrl', at='tx', t=(keyframes_interval* 15) )
                cmds.setKeyframe('root_ctrl', at='tz', t=(keyframes_interval* 15) )
                
                cmds.xform('root_ctrl', ws=True, t=(0, 35, 0) )
                cmds.setKeyframe('root_ctrl', at='ty', t=(keyframes_interval* 16.5) )
                cmds.setKeyframe('root_ctrl', at='tx', t=(keyframes_interval* 16.5) )
                cmds.setKeyframe('root_ctrl', at='tz', t=(keyframes_interval* 16.5) )
                
                if cmds.getAttr('root_ctrl' + '.ty', lock=True) is False:
                        cmds.setAttr('root_ctrl' + '.ty', 0)
                if cmds.getAttr('root_ctrl' + '.tx', lock=True) is False:
                        cmds.setAttr('root_ctrl' + '.tx', 0)
                if cmds.getAttr('root_ctrl' + '.tz', lock=True) is False:
                        cmds.setAttr('root_ctrl' + '.tz', 0)
                        
                cmds.setKeyframe('root_ctrl', at='ty', t=(keyframes_interval* 18) )
                cmds.setKeyframe('root_ctrl', at='tx', t=(keyframes_interval* 18) )
                cmds.setKeyframe('root_ctrl', at='tz', t=(keyframes_interval* 18) )
            except:
                pass  
                    
        # Clean Selection
        cmds.select(clear=True)
        
        # Play Animation
        cmds.PlaybackForward()
        
    else:
        #Remove Key frames from previous step)
        delete_all_keyframes()
        reset_transforms()
        cmds.button('check_btn_ik_system_lower_body', e=True, l='Check', bgc=[.5,.7,.5], ann='0')
        cmds.play(state=False)
        cmds.currentTime(0)


def main_eye_controls():
    '''Checks Main and Eye Controls'''
    
    # Reset other buttons
    for item in gt_grading_components:
        item_id = strip_string_as_id(gt_grading_components.get(item)[0])
        if 'main_eye_controls' not in item_id:
            cmds.button('check_btn_' + item_id, e=True, l='Check', bgc=[.5,.7,.5], ann='0')
    delete_all_keyframes()
    reset_transforms()
    
    # Check Button Status
    button_status = int(cmds.button('check_btn_main_eye_controls', q=True, ann=True))
    if not button_status:
        # Change button to stop and update its status
        cmds.button('check_btn_main_eye_controls', e=True, l='Stop', bgc=[.5,.2,.2], ann='1')
        
        # Unsubdivide Meshes
        unsubdivide_geometries()
        
        # Give eyes a Checker Material
        if cmds.objExists('left_pupil_geo') and cmds.objExists('right_pupil_geo'):
            apply_simple_checker_shader(["left_pupil_geo", "right_pupil_geo"])
            
        # Reset Time
        cmds.currentTime(0)
        
        # Adjust Size of the timeline
        keyframes_interval = gt_grading_settings.get('keyframes_interval') + 1
        cmds.playbackOptions(minTime=0, max = (keyframes_interval * 20))
        
        # Focus On Desired Area
        frame_object('body')
        frame_object('body_geo')
        
        
        if cmds.objExists('main_eye_ctrl'):
            unlock_attribute( ['main_eye_ctrl'], 'visibility')
            cmds.setAttr("main_eye_ctrl.visibility", 1)
            
        if cmds.objExists('main_eyes_ctrl'):
            unlock_attribute( ['main_eyes_ctrl'], 'visibility')
            cmds.setAttr("main_eyes_ctrl.visibility", 1)
        
        # Start Animating
        unlock_attribute(['main_ctrl'], 'translateX')
        keyframe_list(["main_ctrl"], 0, 'translateX', 0)
        keyframe_list(["main_ctrl"], 65, 'translateX', (keyframes_interval * 1))
        keyframe_list(["main_ctrl"], -65, 'translateX', (keyframes_interval * 3))
        keyframe_list(["main_ctrl"], 0, 'translateX', (keyframes_interval * 4))
        
        unlock_attribute(['direction_ctrl', 'directional_ctrl'], 'translateX')
        keyframe_list(['direction_ctrl', 'directional_ctrl'], 0, 'translateX', (keyframes_interval * 4))
        keyframe_list(['direction_ctrl', 'directional_ctrl'], 65, 'translateX', (keyframes_interval * 5))
        keyframe_list(['direction_ctrl', 'directional_ctrl'], -65, 'translateX', (keyframes_interval * 7))
        keyframe_list(['direction_ctrl', 'directional_ctrl'], 0, 'translateX', (keyframes_interval * 8))
        
        unlock_attribute(['main_eye_ctrl', 'main_eyes_ctrl'], 'translateX')
        unlock_attribute(['main_eye_ctrl', 'main_eyes_ctrl'], 'translateY')
        unlock_attribute(['main_eye_ctrl', 'main_eyes_ctrl'], 'translateZ')
        
        keyframe_list(['main_eye_ctrl', 'main_eyes_ctrl'], 0, 'translateX', (keyframes_interval * 8))
        keyframe_list(['main_eye_ctrl', 'main_eyes_ctrl'], 0, 'translateY', (keyframes_interval * 8))
        keyframe_list(['main_eye_ctrl', 'main_eyes_ctrl'], 0, 'translateZ', (keyframes_interval * 8))
        
        key_translate_world_pos(['main_eye_ctrl', 'main_eyes_ctrl'], (35,129.207,72.255), (keyframes_interval * 9))
        key_translate_world_pos(['main_eye_ctrl', 'main_eyes_ctrl'], (-35,129.207,72.255), (keyframes_interval * 11))
        
        keyframe_list(['main_eye_ctrl', 'main_eyes_ctrl'], 0, 'translateX', (keyframes_interval * 12))
        keyframe_list(['main_eye_ctrl', 'main_eyes_ctrl'], 0, 'translateY', (keyframes_interval * 12))
        keyframe_list(['main_eye_ctrl', 'main_eyes_ctrl'], 0, 'translateZ', (keyframes_interval * 12))
        
        key_translate_world_pos(['main_eye_ctrl', 'main_eyes_ctrl'], (0,160,72.255), (keyframes_interval * 13))
        key_translate_world_pos(['main_eye_ctrl', 'main_eyes_ctrl'], (0,110,72.255), (keyframes_interval * 15))
        
        keyframe_list(['main_eye_ctrl', 'main_eyes_ctrl'], 0, 'translateX', (keyframes_interval * 16))
        keyframe_list(['main_eye_ctrl', 'main_eyes_ctrl'], 0, 'translateY', (keyframes_interval * 16))
        keyframe_list(['main_eye_ctrl', 'main_eyes_ctrl'], 0, 'translateZ', (keyframes_interval * 16))
        
        
        eye_ctrls_no_main = ['left_eye_ctrl','right_eye_ctrl']
        
        unlock_attribute(eye_ctrls_no_main, 'translateX')
        unlock_attribute(eye_ctrls_no_main, 'translateY')
        unlock_attribute(eye_ctrls_no_main, 'translateZ')
        
        keyframe_list(eye_ctrls_no_main, 0, 'translateX', (keyframes_interval * 16))
        keyframe_list(eye_ctrls_no_main, 0, 'translateY', (keyframes_interval * 16))
        keyframe_list(eye_ctrls_no_main, 0, 'translateZ', (keyframes_interval * 16))
        
        key_translate_world_pos(['left_eye_ctrl'], (35,129.207,72.255), (keyframes_interval * 17))
        key_translate_world_pos(['left_eye_ctrl'], (-35,129.207,72.255), (keyframes_interval * 19))
        key_translate_world_pos(['right_eye_ctrl'], (-35,129.207,72.255), (keyframes_interval * 17))
        key_translate_world_pos(['right_eye_ctrl'], (35,129.207,72.255), (keyframes_interval * 19))
        
        keyframe_list(eye_ctrls_no_main, 0, 'translateX', (keyframes_interval * 20))
        keyframe_list(eye_ctrls_no_main, 0, 'translateY', (keyframes_interval * 20))
        keyframe_list(eye_ctrls_no_main, 0, 'translateZ', (keyframes_interval * 20))
                    
        # Clean Selection
        cmds.select(clear=True)
        
        # Play Animation
        cmds.PlaybackForward()
        
    else:
        #Remove Key frames from previous step)
        delete_all_keyframes()
        reset_transforms()
        cmds.button('check_btn_main_eye_controls', e=True, l='Check', bgc=[.5,.7,.5], ann='0')
        cmds.play(state=False)
        cmds.currentTime(0)

def bulletproofing_targets_others():
    '''Checks Bulletproofing Targets and Others'''
    
    # Reset other buttons
    for item in gt_grading_components:
        item_id = strip_string_as_id(gt_grading_components.get(item)[0])
        if 'bulletproofing_targets_others' not in item_id:
            cmds.button('check_btn_' + item_id, e=True, l='Check', bgc=[.5,.7,.5], ann='0')
    delete_all_keyframes()
    reset_transforms()
    
    # Check Button Status
    button_status = int(cmds.button('check_btn_bulletproofing_targets_others', q=True, ann=True))
    if not button_status:
        # Change button to stop and update its status
        cmds.button('check_btn_bulletproofing_targets_others', e=True, l='Stop', bgc=[.5,.2,.2], ann='1')
        
        # Unsubdivide Meshes
        unsubdivide_geometries()
        
        # Give eyes a Checker Material
        if cmds.objExists('left_pupil_geo') and cmds.objExists('right_pupil_geo'):
            apply_simple_checker_shader(["left_pupil_geo", "right_pupil_geo"])
            
        # Reset Time
        cmds.currentTime(0)
        
        # Adjust Size of the timeline
        keyframes_interval = gt_grading_settings.get('keyframes_interval') + 2
        cmds.playbackOptions(minTime=0, max = (keyframes_interval * 6))
        
        # Focus On Desired Area
        frame_object('body')
        frame_object('body_geo')
        
        
        if cmds.objExists('main_eye_ctrl'):
            unlock_attribute( ['main_eye_ctrl'], 'visibility')
            cmds.setAttr("main_eye_ctrl.visibility", 1)
            
        if cmds.objExists('main_eyes_ctrl'):
            unlock_attribute( ['main_eyes_ctrl'], 'visibility')
            cmds.setAttr("main_eyes_ctrl.visibility", 1)
                
        # Start Animating

        #Check if bulletproof by scaling it
        should_be_bulletproof = ['spine1_ctrl','spine3_ctrl','left_elbow_ctrl','right_elbow_ctrl','direction_ctrl']
        keyframe_list(should_be_bulletproof, 1, 'scaleX', 0)
        keyframe_list(should_be_bulletproof, 1.5, 'scaleX', keyframes_interval)
        keyframe_list(should_be_bulletproof, 1, 'scaleX', (keyframes_interval * 2))

        keyframe_list(should_be_bulletproof, 1, 'scaleX', 0)
        keyframe_list(should_be_bulletproof, 1.5, 'scaleX', keyframes_interval)
        keyframe_list(should_be_bulletproof, 1, 'scaleX', (keyframes_interval * 2))
        
        #keyframe_list(eye_ctrls, 0, 'translateZ', 0)
        #keyframe_list(eye_ctrls, 120, 'translateZ', keyframes_interval)
        #keyframe_list(eye_ctrls, 0, 'translateZ', (keyframes_interval * 2))

        #Define possible naming variations
        fist_variations = ['fist','Fist','FIST']
        smile_variations = ['smile','Smile','SMILE']
        splay_variations = ['splay','Splay','SPLAY']
        sad_variations = ['sad', 'Sad', 'SAD']
        
        
        for each in fist_variations:
            keyframe_list(wrist_ctrls, 0, each, (keyframes_interval* 2))
            keyframe_list(wrist_ctrls, 10, each, (keyframes_interval* 3))
            keyframe_list(wrist_ctrls, 0, each, (keyframes_interval* 4))
        
        for each in splay_variations:
            keyframe_list(wrist_ctrls, 0, each, (keyframes_interval* 4))
            keyframe_list(wrist_ctrls, 10, each, (keyframes_interval* 5))
            keyframe_list(wrist_ctrls, 0, each, (keyframes_interval* 6))
        
        for each in sad_variations:
            keyframe_list(['head_ctrl'], 0, each, (keyframes_interval* 2))
            keyframe_list(['head_ctrl'], 10, each, (keyframes_interval* 3))
            keyframe_list(['head_ctrl'], 0, each, (keyframes_interval* 4))


        for each in smile_variations:
            keyframe_list(['head_ctrl'], 0, each, (keyframes_interval* 4))
            keyframe_list(['head_ctrl'], 10, each, (keyframes_interval* 5))
            keyframe_list(['head_ctrl'], 0, each, (keyframes_interval* 6))
                    
        # Clean Selection
        cmds.select(clear=True)
        
        # Play Animation
        cmds.PlaybackForward()
        
    else:
        #Remove Key frames from previous step)
        delete_all_keyframes()
        reset_transforms()
        cmds.button('check_btn_bulletproofing_targets_others', e=True, l='Check', bgc=[.5,.7,.5], ann='0')
        cmds.play(state=False)
        cmds.currentTime(0)


def scalable_control_rig():
    '''Checks if rig is scalable'''
    
    # Reset other buttons
    for item in gt_grading_components:
        item_id = strip_string_as_id(gt_grading_components.get(item)[0])
        if 'scalable_control_rig' not in item_id:
            cmds.button('check_btn_' + item_id, e=True, l='Check', bgc=[.5,.7,.5], ann='0')
    delete_all_keyframes()
    reset_transforms()
    
    # Check Button Status
    button_status = int(cmds.button('check_btn_scalable_control_rig', q=True, ann=True))
    if not button_status:
        # Change button to stop and update its status
        cmds.button('check_btn_scalable_control_rig', e=True, l='Stop', bgc=[.5,.2,.2], ann='1')
        
        # Unsubdivide Meshes
        unsubdivide_geometries()
        
        # Give eyes a Checker Material
        if cmds.objExists('left_pupil_geo') and cmds.objExists('right_pupil_geo'):
            apply_simple_checker_shader(["left_pupil_geo", "right_pupil_geo"])
            
        # Reset Time
        cmds.currentTime(0)
        
        # Adjust Size of the timeline
        keyframes_interval = gt_grading_settings.get('keyframes_interval') + 4
        cmds.playbackOptions(minTime=0, max = (keyframes_interval * 6))
        
        # Focus On Desired Area
        frame_object('body')
        frame_object('body_geo')
        
        # Make eyes invisible
        if cmds.objExists('main_eye_ctrl'):
            unlock_attribute( ['main_eye_ctrl'], 'visibility')
            cmds.setAttr("main_eye_ctrl.visibility", 0)
            
        if cmds.objExists('main_eyes_ctrl'):
            unlock_attribute( ['main_eyes_ctrl'], 'visibility')
            cmds.setAttr("main_eyes_ctrl.visibility", 0)
                
        # Start Animating
        # Scale main_ctrl
        unlock_attribute(['root_ctrl'], 'scaleX')
        unlock_attribute(['root_ctrl'], 'scaleY')
        unlock_attribute(['root_ctrl'], 'scaleZ')
        keyframe_list(['main_ctrl'], 1, 'scaleX', 0)
        keyframe_list(['main_ctrl'], 0.2, 'scaleX', (keyframes_interval * 2))
        keyframe_list(['main_ctrl'], 2, 'scaleX', (keyframes_interval * 4))
        keyframe_list(['main_ctrl'], 1, 'scaleX', (keyframes_interval * 6))
        
        keyframe_list(['main_ctrl'], 1, 'scaleY', 0)
        keyframe_list(['main_ctrl'], 0.2, 'scaleY', (keyframes_interval * 2))
        keyframe_list(['main_ctrl'], 2, 'scaleY', (keyframes_interval * 4))
        keyframe_list(['main_ctrl'], 1, 'scaleY', (keyframes_interval * 6))
        
        keyframe_list(['main_ctrl'], 1, 'scaleZ', 0)
        keyframe_list(['main_ctrl'], 0.2, 'scaleZ', (keyframes_interval * 2))
        keyframe_list(['main_ctrl'], 2, 'scaleZ', (keyframes_interval * 4))
        keyframe_list(['main_ctrl'], 1, 'scaleZ', (keyframes_interval * 6))
                    
        # Clean Selection
        cmds.select(clear=True)
        
        # Play Animation
        cmds.PlaybackForward()
        
    else:
        #Remove Key frames from previous step)
        delete_all_keyframes()
        reset_transforms()
        cmds.button('check_btn_scalable_control_rig', e=True, l='Check', bgc=[.5,.7,.5], ann='0')
        cmds.play(state=False)
        cmds.currentTime(0)


def is_point_inside_mesh(mesh, point=(0.0, 0.0, 0.0), ray_dir=(0.0, 0.0, 1.0)):
    '''
    Uses ray tracing to determine if a point is inside of a mesh.
    
                Parameters:
                    mesh (string) : Name of the mesh object
                    point (float vector) : Point position (Could be updated to auto extract...)
                    ray_dir (float vector) : Direction of the ray
                    
                Returns:
                    is_inside (bool) : True or False according to where the point is
    
    '''
    sel = om.MSelectionList()
    dag = om.MDagPath()

    sel.add(mesh)
    sel.getDagPath(0,dag)

    mesh = om.MFnMesh(dag)

    point = om.MFloatPoint(*point)
    ray_dir = om.MFloatVector(*ray_dir)
    float_array = om.MFloatPointArray()

    mesh.allIntersections(
            point, ray_dir,
            None, None,
            False, om.MSpace.kWorld,
            10000, False,
            None, # replace none with a mesh look up accelerator if needed
            False,
            float_array,
            None, None,
            None, None,
            None
        ) 
    return float_array.length()%2 == 1   

def get_short_name(obj):
    '''
    Get the name of the objects without its path (Maya returns full path if name is not unique)

            Parameters:
                    obj (string) - object to extract short name
                    
            Returns:
                    short_name (string) - the short version of the name of an object (no pipes)
    '''
    if obj == '':
        return ''
    split_path = obj.split('|')
    if len(split_path) >= 1:
        short_name = split_path[len(split_path)-1]
    return short_name
    

def extract_brute_force_dict(is_joint=True, include_vec_scale=False):
    '''
    Internal Function used to generate a dictionary that is later used to automatically change the name of objects.
    To use, select the objects you want to have in your dictionary, then run it. (Output goes to the script editor.)
    '''
    sel = cmds.ls(selection=True)

    for obj in sel:
        extraction_string = "'" + obj + "' : [ "
        position = cmds.getAttr(obj + '.translate')

        extraction_string += "[{:.{}f}".format( position[0][0], 3 )
        extraction_string += ", {:.{}f}".format( position[0][1], 3 )
        extraction_string += ", {:.{}f}], ".format( position[0][2], 3 )
        
        if is_joint:
            orientation = cmds.getAttr(obj + '.jointOrient')
        else: 
            orientation = cmds.getAttr(obj + '.rotate')
        
        extraction_string += "[{:.{}f}".format( orientation[0][0], 3 )
        extraction_string += ", {:.{}f}".format( orientation[0][1], 3 )
        extraction_string += ", {:.{}f}], ".format( orientation[0][2], 3 )
        
        scale = cmds.getAttr(obj + '.scale')
        if include_vec_scale:
            extraction_string += '1, ('
            extraction_string += "{:.{}f}".format( scale[0][0], 3 )
            extraction_string += ", {:.{}f}".format( scale[0][1], 3 )
            extraction_string += ", {:.{}f})],".format( scale[0][2], 3 )
        else:
            extraction_string += " {:.{}f}".format( scale[0][0], 3 ) + '],'
        
        print(extraction_string.replace('ray_tracing_obj_', ''))


def search_delete_temp_meshes(starts_with):
    '''
    Deletes any mesh that starts with the provided string
            
            Parameters:
                    starts_with (string): String the temp mesh starts with
                        
    '''
    all_meshes = cmds.ls(type='mesh')

    for obj in all_meshes:
        mesh_transform = ''
        mesh_transform_extraction = cmds.listRelatives(obj, allParents=True) or []
        if len(mesh_transform_extraction) > 0:
            mesh_transform = mesh_transform_extraction[0]
            
        try:
            if mesh_transform.startswith(starts_with) and cmds.objExists(mesh_transform):
                cmds.delete(mesh_transform)
        except:
            pass
            
            
def delete_all_namespaces():
    '''Deletes all namespaces in the scene'''
    cmds.undoInfo(openChunk=True, chunkName='Delete all namespaces')
    try:
        default_namespaces = ['UI', 'shared']

        def num_children(namespace):
            '''Used as a sort key, this will sort namespaces by how many children they have.'''
            return namespace.count(':')

        namespaces = [namespace for namespace in cmds.namespaceInfo(lon=True, r=True) if namespace not in default_namespaces]
        
        # Reverse List
        namespaces.sort(key=num_children, reverse=True) # So it does the children first

        print(namespaces)

        for namespace in namespaces:
            if namespace not in default_namespaces:
                mel.eval('namespace -mergeNamespaceWithRoot -removeNamespace "' + namespace + '";')
    except Exception as e:
        cmds.warning(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName='Delete all namespaces')
        

def change_obj_color(obj, rgb_color=(1,1,1)):
    '''
    Changes the color of an object by changing the drawing override settings
            
            Parameters:
                    obj (string): Name of the object to change color
                    rgb_color (tuple): RGB color 
                        
    '''
    try:
        if cmds.objExists(obj) and cmds.getAttr(obj + '.overrideEnabled', lock=True) is False:
            cmds.setAttr(obj + ".overrideEnabled", 1)
            cmds.setAttr(obj + ".overrideRGBColors", 1) 
            cmds.setAttr(obj + ".overrideColorRGB", rgb_color[0], rgb_color[1], rgb_color[2]) 
    except Exception as e:
        raise e
        
        
def delete_all_display_layers():
    ''' Deletes all display layers '''
    try:
        display_layers = cmds.ls(type = 'displayLayer')
        for layer in display_layers:
            if layer != 'defaultLayer':
                cmds.delete(layer)
    except:
        pass

def strip_string_as_id(string):
    ''' 
    Removes undesired symbols from a string 
                
                Parameters:
                        string (string): A string to process
                        
                Returns:
                        clean_string (string): A string without undesired symbols
    
    '''
    clean_string = string.lower().replace(" & ","_").replace("(","").replace(")","").replace(" ","_").replace("-","_").replace(",","").replace(":","")
    return clean_string
    
def improve_ctrls_visibility():
    ''' Improves the visibility of the nurbs curves in a rig'''

    all_curves = cmds.ls(type='nurbsCurve')
    
    for crv in all_curves:
        curve_transform = cmds.listRelatives(crv, allParents=True) or []
        
        if len(curve_transform) > 0:
            curve_transform = curve_transform[0]
            
        if cmds.getAttr(curve_transform + ".overrideEnabled" ,lock=True) is False:
            cmds.setAttr(curve_transform + ".overrideEnabled", 1)
            
            if curve_transform.lower().startswith('right_') or curve_transform.lower().startswith('r_'):
                change_obj_color(curve_transform, rgb_color=(1,0,0))
            elif curve_transform.lower().startswith('left_') or curve_transform.lower().startswith('l_'):
                change_obj_color(curve_transform, rgb_color=(0,0,1))
            elif curve_transform.lower().startswith('main_ctrl'):
                change_obj_color(curve_transform, rgb_color=(1,0,.5))
            else:
                change_obj_color(curve_transform, rgb_color=(1,1,0))
        
        if cmds.getAttr(crv + ".ls" ,lock=True) is False:
            cmds.setAttr(curve_transform + ".ls", 3)
            fingers = ['thumb', 'index', 'middle', 'finger', 'pinky', 'ring']
            for string in fingers:
                if string in crv:
                    cmds.setAttr(curve_transform + ".ls", 2)
   
            if 'direction' in curve_transform and cmds.getAttr(crv + ".ls" ,lock=True) is False:
                cmds.setAttr(crv + ".ls", 1)

def unlock_attribute(obj_list, attribute_name):
    ''' 
    Unlocks attribute from a list of objects
    
            Parameters:
                obj_list (list): List of objects (strings)
                attribute_name (string): Name of the attribute to unlock
    '''
    for obj in obj_list:
        if cmds.objExists(obj):
            if cmds.attributeQuery(attribute_name, node=obj, exists=True):
                if cmds.getAttr(obj + "." + attribute_name ,lock=True) is True:
                    cmds.setAttr(obj + "." + attribute_name, lock=0)

def key_translate_world_pos(obj_list, world_pos, time):
    ''' 
    Keys an object using world position instead of values in the translate attributes
    
            Parameters:
                obj_list (list): List of objects (strings)
                world_pos (tuple): A tuple of float values to be used as the world positon translate (X, Y, Z)
                time (int): time in the time line to create the key
    '''
    for obj in obj_list:
        if cmds.objExists(obj):          
            cmds.xform(obj, ws=True, t=world_pos)
            cmds.setKeyframe(obj, at='tx', t=time )
            cmds.setKeyframe(obj, at='ty', t=time )
            cmds.setKeyframe(obj, at='tz', t=time )
            

#Build GUI
if __name__ == '__main__':
    build_gui_gt_grader_script()