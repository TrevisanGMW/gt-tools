"""

 GT Grading Script  - Script for automatically testing and grading assignments
 Configured for: Rigging 2 - Facial Rig
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-08-13 - github.com/TrevisanGMW
 
 To Do:
    Update nonunique elements function
    Update name of the side ui controls
    Fix left_innerBrow_Ctrl and lip corner direction issue

"""
import maya.cmds as cmds
from datetime import datetime
from maya import OpenMayaUI as omui
import maya.OpenMaya as om
import os.path, time, re
import maya.mel as mel


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
assignment_name = 'Rigging 2 - Facial Rig'
script_name = 'GT - Grading Script'

# Regex pattern
re_file_name = re.compile(r'(^\dD\d{3}\_\w+\_)(FacialRig|FacialRigging|Facial_Rig|FaceRig)(_|.)')

# Version
script_version = '1.0'

# Grading Components
gt_grading_components = { 0 : ['Organization & Functionality', 20],
                          1 : ['Joint Placement & Skinning', 30],
                          2 : ['Controls & Side UI Connection', 30],
                          3 : ['Blend Shapes & Deformers', 20]
                        }

# Common Notes
gt_grading_notes = { 0 : ['Scale Issue', 'Rig is not scalable. (Many things can cause this issue. Common causes are incorrect hierarchy or missing constraints)'],
                     1 : ['Geo not skinned', 'Some geometries were not skinned (bound) to any joints.'],
                     2 : ['Needs Polishing', 'Skin weights need some polishing.'],
                     3 : ['Joint Placement', 'Not all new joints seem to be positioned correctly.'],
                     4 : ['Missing Joint', 'Missing one or more expected joint.'],
                     5 : ['Incorrect Hierarchy', 'The current hierarchy is making the rig not fully functional.'],
                     6 : ['Missing Connections', 'Some joints on the character\'s face don\'t seem to be properly connected to any controls or to the side UI.'],
                     7 : ['Weak Set Driven Keys', 'Set driven keys are not moving the facial joints enough to properly change the facial expression.'],
                     8 : ['Missing Control', 'Missing a control or expected rigging element.'],
                     9 : ['Broken Control', 'Not all controls are fully functional. (Testing could have helped prevent that.)'],
                    10 : ['Missing BS Target', 'Missing one or more expected blend shape target.'],
                    11 : ['Broken Deformer', 'Not all deformers are fully functional.'],
                    12 : ['Organization', 'Scene is not properly organized. (Possible issues: naming, junk objects, keyframes left behind, incorrect scene name, etc..)'],
                    13 : ['Symmetry Issues', 'Deformation is not symmetrical'],
                    14 : ['Random Influences', 'Some random vertices seem to be assigned incorrectly (Use ngSkinTools to avoid this)']
                   }
                   
gt_grading_settings = { 'keyframes_interval' : 5
                      }


# Toggle Visibility List
toggle_jnt_visibility = ['head', 'jaw', 'neckmid', 'neckmid']

# Dict { joint_name : [position, rotation, radius, ignore_string_list] - Radius can be replaced with a XYZ tuple for custom scale. Add a list at the end of ignoring objects.
# To quickly create a list use : extract_brute_force_dict(is_joint=False, include_vec_scale=False)
brute_force_joint_naming_dict = {'neckBase_jnt' : [ [-0.000, 86.248, -3.785], [90.000, -16.310, 90.000], 1.8],
                                 'neckMid_jnt' : [ [-0.000, 89.732, -2.946], [90.000, -25.099, 90.000], 1.8],
                                 'head_jnt' : [ [-0.000, 92.828, -1.571], [90.000, -3.162, 90.000], 1.47, ['jaw', 'tongue']],
                                 'head_end_jnt' : [ [0.000, 103.658, -0.757], [90.000, -3.162, 90.000], 2.5],
                                 'jawPivot_jnt' : [ [0.000, 94.628, 1.059], [-90.000, -42.261, -90.000], 1.6, ['head']],
                                 'jawPivot_end_jnt' : [ [0.000, 89.713, 4.353], [-90.000, -42.261, -90.000], 0.8],
                                 'right_eye_jnt' : [ [-1.950, 97.160, 4.413], [-114.720, 85.248, 65.355], 0.8],
                                 'right_eye_end_jnt' : [ [-1.990, 97.074, 5.551], [-114.720, 85.248, 65.355], 0.3],
                                 'left_eye_jnt' : [ [1.950, 97.160, 4.413], [65.280, -85.248, -65.355], 0.8],
                                 'left_eye_end_jnt' : [ [1.990, 97.074, 5.551], [65.280, -85.248, -65.355], 0.3],
                                 'left_innerBrow_jnt' : [ [0.925, 98.158, 6.383], [-0.000, 0.000, 0.000], 0.55],
                                 'left_midBrow_jnt' : [ [2.038, 98.469, 6.298], [-0.000, 0.000, 0.000], 0.55],
                                 'left_outerBrow_jnt' : [ [3.206, 98.300, 5.873], [-0.000, 0.000, 0.000], 0.55],
                                 'right_innerBrow_jnt' : [ [-0.925, 98.158, 6.383], [180.000, 0.000, 0.000], 0.55],
                                 'right_midBrow_jnt' : [ [-2.038, 98.469, 6.298], [180.000, 0.000, 0.000], 0.55],
                                 'right_outerBrow_jnt' : [ [-3.206, 98.300, 5.873], [180.000, 0.000, 0.000], 0.55],
                                 'left_lipCorner_jnt' : [ [1.872, 92.292, 5.013], [-0.000, 0.000, 0.000], 1, ['teeth', 'tongue']],
                                 'right_lipCorner_jnt' : [ [-1.872, 92.292, 5.013], [180.000, 0.000, 0.000], 1, ['teeth', 'tongue']],
                                 'left_outerCheek_jnt' : [ [2.940, 94.904, 5.501], [-0.000, 0.000, 0.000], 1],
                                 'left_innerCheek_jnt' : [ [1.105, 95.808, 5.906], [-0.000, 0.000, 0.000], 1],
                                 'right_innerCheek_jnt' : [ [-1.105, 95.808, 5.906], [180.000, 0.000, 0.000], 1],
                                 'right_outerCheek_jnt' : [ [-2.940, 94.904, 5.501], [180.000, 0.000, 0.000], 1],
                                 'left_upperOutLip_jnt' : [ [1.019, 92.455, 5.636], [0.000, 19.839, 0.000], (0.750, 0.218, 0.336), ['ignore_name']], 
                                 'left_upperOutLip_jnt' : [ [1.019, 92.455, 5.636], [0.000, 19.839, 0.000], (0.750, 0.218, 0.336)], 
                                 'left_lowerOutLip_jnt' : [ [0.986, 92.066, 5.579], [0.000, 27.748, 0.000], (0.649, 0.203, 0.336)], 
                                 'mid_lowerLip_jnt' : [ [0.000, 92.128, 5.824], [0.000, 0.000, -0.000], (0.676, 0.126, 0.336)], 
                                 'mid_upperLip_jnt' : [ [0.000, 92.387, 5.820], [-0.000, 0.000, 0.000], (0.646, 0.157, 0.398)], 
                                 'right_upperOutLip_jnt' : [ [-1.019, 92.455, 5.636], [0.000, 160.161, 0.000], (0.750, 0.218, 0.336)], 
                                 'right_lowerOutLip_jnt' : [ [-0.986, 92.066, 5.579], [0.000, 152.252, 0.000], (0.649, 0.203, 0.336)] 
                                }  
                                                       
brute_force_ctrl_naming_dict = {'main_eye_ctrl' : [ [0.000, 97.160, 18.800], [0.000, 0.000, 0.000], (1.000, 1.000, 10.000)],
                                'left_eye_ctrl' : [ [1.950, 97.160, 18.800], [0.000, 0.000, 0.000], (1.000, 1.000, 10.000)],
                                'right_eye_ctrl' : [ [-1.950, 97.160, 18.800], [0.000, 0.000, 0.000], (1.000, 1.000, 10.000)],
                                'head_squashStretch_ctrl' : [ [0.000, 106.859, 1.500], [0.000, 0.000, 0.000], 3.660],
                                'head_ctrl' : [ [-0.000, 92.828, -1.571], [90.000, -3.162, 90.000], 1.47, ['tongue']],
                                'neckMid_ctrl' : [ [-0.000, 89.732, -2.946], [90.000, -25.099, 90.000], 1.8, ['neckBase', 'neckbase']],
                                }




# Delete this after 3D145 is done and source file is patched
temp_ignore_non_uniques = ['effector6', 'left_Hand_IK_Gimbal_CtrlGrp', 'right_foot_Jnt']



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
            item_id = items.get(item)[0].lower().replace(" & ","_").replace(" ","_").replace("-","_").replace(",","").replace(":","")
            create_check_button("check_btn_" + item_id, item_id)
            
            if len(override_fonts) > 0 and item in override_fonts[0]:
                cmds.text(items.get(item)[0] + ': ', fn=override_fonts[1], align='left')
            else:
                cmds.text(items.get(item)[0] + ': ', align='left')
                
            max_value = items.get(item)[1]
            cmds.intSliderGrp('grade_' + item_id, cw=[(1,0),(2,40),(3,10)], cal=[(1,'left')], field=True, label='',\
                              minValue=0, maxValue=max_value, fieldMinValue=0, fieldMaxValue=max_value, value=max_value, cc=lambda args: update_grade_output())

    create_gt_grading_components(gt_grading_components, ([0,1,2, 3],'smallPlainLabelFont'))
    
    # Late Submission
    cmds.separator(h=5, style='none') # Empty Space
    cmds.separator(h=5, style='none') # Empty Space
    check_items_column = cmds.rowColumnLayout(nc=3, cw=[(1, 50), (2, 150),(3, 180)], cs=[(1, 15), (2, 10)], p=main_column)

    cmds.button('check_btn_late_submission', l='Check', h=14, bgc=[.5,.7,.5], c=lambda args: run_check_operation('late_submission_check'))
    cmds.text('Late Submission Penalty (Days): ', fn='smallPlainLabelFont', align='left')
    cmds.intSliderGrp('late_submission_multiplier' , cw=[(1,0),(2,40),(3,10)], cal=[(1,'left')], field=True, label='' + ': ',\
                       minValue=0, maxValue=10, fieldMinValue=0, fieldMaxValue=100, value=0, fieldStep=10, cc=lambda args: update_grade_output())

    def update_grade_output():
        ''' Updates "Output Window" UI elements to show current grade. '''
        cmds.scrollField(output_scroll_field, e=True, clear=True)
        grade_total = 0
        for grade in gt_grading_components:
            item_name = gt_grading_components.get(int(grade))[0]
            item_id = gt_grading_components.get(grade)[0].lower().replace(" & ","_").replace(" ","_").replace("-","_").replace(",","").replace(":","")
            grade_total += cmds.intSliderGrp('grade_' + item_id, q=True, value=True)
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=str(cmds.intSliderGrp('grade_' + item_id, q=True, value=True)) + '/' + str(gt_grading_components.get(int(grade))[1]) + ' - ' + item_name + '\n')
        
        penalty = 1.0 - (0.1*float(cmds.intSliderGrp('late_submission_multiplier', q=True, value=True)))
        if penalty != 1.0:
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=str(int(cmds.intSliderGrp('late_submission_multiplier', q=True, value=True)*10)) + '% - Late Submission Penalty\n')
            
        grade_total = grade_total * penalty
        
        cmds.scrollField(output_scroll_field, e=True, ip=0, it='\n      Total: ' +  str(grade_total) + '\n\n')
        
        
        for note in gt_grading_notes:
            item_id = gt_grading_notes.get(note)[0].lower().replace(" & ","_").replace(" ","_").replace("-","_").replace(",","").replace(":","")

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
            item_id = items.get(item)[0].lower().replace(" & ","_").replace(" ","_").replace("-","_").replace(",","").replace(":","")
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
    
    cmds.button(l='Reset Viewport', h=30, bgc=footer_buttons_color, c=lambda args: reset_viewport())
    cmds.button(l='Patch Joints', h=30, bgc=footer_buttons_color, c=lambda args: patch_joints())
    cmds.button(l='Reset Transforms', h=30, bgc=footer_buttons_color, c=lambda args: reset_transforms())
    
    cmds.separator(h=5, style='none')
    cmds.separator(h=5, style='none')
    cmds.separator(h=5, style='none')
    
    
    toggle_joints_visibility_btn = cmds.button(l='Toggle Big Joints', h=30, bgc=footer_buttons_color, c=lambda args: toggle_big_joints_visibility(toggle_jnt_visibility))
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
    
    def run_check_operation(operation_name):
        ''' 
        Tries to run an operation based on the provided string
        
                    Parameters:
                        operation_name (string) : name of the operation/function to run
        
        '''
        try:
            if operation_name == 'late_submission_check':
                late_submission_check()
            elif operation_name == 'joint_placement_skinning':
                joint_placement_skinning()
            elif operation_name == 'controls_side_ui_connection':
                controls_side_ui_connection()
            elif operation_name == 'blend_shapes_deformers':
                blend_shapes_deformers()
            elif operation_name == 'organization_functionality':
                organization_functionality()
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
            item_id = gt_grading_notes.get(note)[0].lower().replace(" & ","_").replace(" ","_").replace("-","_").replace(",","").replace(":","")
            button_name = "note_btn_" + item_id
            cmds.button(button_name, e=True, bgc=[.3,.3,.3], ann='0')
            
        for item in gt_grading_components:
            item_id = gt_grading_components.get(item)[0].lower().replace(" & ","_").replace(" ","_").replace("-","_").replace(",","").replace(":","")
            max_value = gt_grading_components.get(item)[1]
            cmds.intSliderGrp('grade_' + item_id, e=True,  value=max_value)
        
        cmds.intSliderGrp('late_submission_multiplier', e=True, value=0)
        update_grade_output()



    def patch_joints():
        ''' Change joints to be easily visible when grading it (color, radius, size, etc... It alsop changes the global multiplier (jointDisplayScale) back to one '''
        try:
            general_desired_size = .5
            all_joints = cmds.ls(type='joint')
            for obj in all_joints:
                if cmds.objExists(obj):
                    if cmds.getAttr(obj + ".radius" ,lock=True) is False:
                        cmds.setAttr(obj + '.radius', general_desired_size)
                        cmds.select(d=True)
                        if 'teeth' in obj:
                            if cmds.getAttr(obj + ".radius" ,lock=True) is False:
                                cmds.setAttr(obj + '.radius', general_desired_size/4)
                                change_obj_color(obj, rgb_color=(1,0,0))
                        if 'lip' in obj.lower():
                            if cmds.getAttr(obj + ".radius" ,lock=True) is False:
                                cmds.setAttr(obj + '.radius', general_desired_size/3)
                                change_obj_color(obj, rgb_color=(0,0,1))
                        if 'neckbase' in obj.lower():
                            change_obj_color(obj, rgb_color=(1,1,0))
                        if 'cheek' in obj.lower():
                            if cmds.getAttr(obj + ".radius" ,lock=True) is False:
                                cmds.setAttr(obj + '.radius', general_desired_size/4)
                                change_obj_color(obj, rgb_color=(0,1,0))
                        if 'eye' in obj.lower() and 'end' not in obj.lower() and 'brow' not in obj.lower():
                            if cmds.getAttr(obj + ".radius" ,lock=True) is False:
                                cmds.setAttr(obj + '.radius', general_desired_size*1.5)
                                change_obj_color(obj, rgb_color=(1,0,0))
                        if 'eye' in obj.lower() and 'end' in obj.lower() and 'brow' not in obj.lower():
                            if cmds.getAttr(obj + ".radius" ,lock=True) is False:
                                cmds.setAttr(obj + '.radius', general_desired_size/2)
                                change_obj_color(obj, rgb_color=(0,1,1))
                        if 'tongue' in obj.lower():
                            if cmds.getAttr(obj + ".radius" ,lock=True) is False:
                                cmds.setAttr(obj + '.radius', general_desired_size/6)
                                change_obj_color(obj, rgb_color=(1,.5,1))
                        if 'brow' in obj.lower():
                            if cmds.getAttr(obj + ".radius" ,lock=True) is False:
                                cmds.setAttr(obj + '.radius', general_desired_size/3)
                                change_obj_color(obj, rgb_color=(0,1,.72))
                        if 'jaw' in obj.lower() and 'end' not in obj.lower():
                            if cmds.getAttr(obj + ".radius" ,lock=True) is False:
                                cmds.setAttr(obj + '.radius', general_desired_size/3)
                                change_obj_color(obj, rgb_color=(1,1,1))
            cmds.jointDisplayScale(1) 
            
            # Try to make visible
            all_transforms = cmds.ls(type='transform')
            all_joints = cmds.ls(type='transform')
            
            for jnt in all_joints: 
                if 'root' in jnt:
                    if cmds.getAttr(jnt + ".v" , lock=True):
                        cmds.setAttr(jnt + ".v", lock=False)
                    cmds.setAttr(jnt + ".v", 1)
                    
            for obj in all_transforms: 
                if 'skeleton' in obj or 'bones' in obj:
                    if cmds.getAttr(obj + ".v" , lock=True):
                        cmds.setAttr(obj + ".v", lock=False)
                    cmds.setAttr(obj + ".v", 1)

        except Exception as exception:
            cmds.scrollField(output_scroll_field, e=True, clear=True)
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=str(exception) + '\n')
            
        
            
    def organization_functionality():
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
        
        # TEMP CODE =======================================================================
        print()
        try:
            for string in temp_ignore_non_uniques:
                if string in non_unique_transforms:
                    non_unique_transforms.remove(string)
        except:
            pass
        # TEMP CODE =======================================================================
        
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
            
      
        # Look for expected objects        
        not_found = []
        found_without_name = []
        # Joints
        all_joints = cmds.ls(type='joint', long=True)
        for obj in brute_force_joint_naming_dict:
            obj_exists = False
            if cmds.objExists(obj):
                obj_exists = True
            else:
                if type(brute_force_joint_naming_dict.get(obj)[2]) is tuple:
                    new_scale = brute_force_joint_naming_dict.get(obj)[2]
                    ray_tracing_obj = cmds.polySphere(name=('ray_tracing_obj_' + obj), r=1, sx=8, sy=8, ch=False, cuv=False)
                    if cmds.objExists(ray_tracing_obj[0]):
                        cmds.setAttr(ray_tracing_obj[0] + '.scaleX', new_scale[0])
                        cmds.setAttr(ray_tracing_obj[0] + '.scaleY', new_scale[1])
                        cmds.setAttr(ray_tracing_obj[0] + '.scaleZ', new_scale[2])
                else:
                    ray_tracing_obj = cmds.polySphere(name=('ray_tracing_obj_' + obj), r=brute_force_joint_naming_dict.get(obj)[2], sx=8, sy=8, ch=False, cuv=False)
                    cmds.xform(ray_tracing_obj, ws=True, ro=(0,0,90) )
                    cmds.makeIdentity(ray_tracing_obj, apply=True, rotate=True)
                cmds.xform(ray_tracing_obj, a=True, ro=brute_force_joint_naming_dict.get(obj)[1] )
                cmds.xform(ray_tracing_obj, a=True, t=brute_force_joint_naming_dict.get(obj)[0] )
                
                
                for jnt in all_joints:
                    jnt_pos = cmds.xform(jnt, piv=True , q=True , ws=True)
                    is_joint_inside = is_point_inside_mesh(ray_tracing_obj[0], point=(jnt_pos[0],jnt_pos[1],jnt_pos[2]))
                    
                    ignore_joint = False
                    if len(brute_force_joint_naming_dict.get(obj)) == 4:
                        for string in brute_force_joint_naming_dict.get(obj)[3]:
                            if  string in jnt:
                                ignore_joint = True
                    
                    if is_joint_inside and get_short_name(jnt) != obj and ignore_joint is False:
                        found_without_name.append([jnt, obj])
                        obj_exists = True
                cmds.delete(ray_tracing_obj)
            if not obj_exists:
                not_found.append(obj)

        
        # Ctrls (nurbsCurve)
        all_nurbs_curves = cmds.ls(type='nurbsCurve', long=True)
        for obj in brute_force_ctrl_naming_dict:
            obj_exists = False
            if cmds.objExists(obj):
                obj_exists = True
            else:
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
                    crv_transform = cmds.listRelatives(crv, allParents=True) or []
                    if len(crv_transform) > 0:
                        crv_pos = cmds.xform(crv_transform[0], piv=True , q=True , ws=True)
                        is_crv_inside = is_point_inside_mesh(ray_tracing_obj[0], point=(crv_pos[0],crv_pos[1],crv_pos[2]))
                        
                        ignore_crv = False
                        if len(brute_force_ctrl_naming_dict.get(obj)) == 4:
                            for string in brute_force_ctrl_naming_dict.get(obj)[3]:
                                if string in jnt:
                                    ignore_crv = True
                        
                        if is_crv_inside and get_short_name(crv_transform[0]) != obj and ignore_crv is False:
                            found_without_name.append([crv_transform[0], obj])
                            obj_exists = True
                cmds.delete(ray_tracing_obj)
            if not obj_exists:
                not_found.append(obj)

        # Write issues to the output string
        if len(not_found) > 0:
            issues += 'The following expected objects were not found:\n'
        for obj in not_found:
            issues += '"' + str(obj) + '"\n'
        issues += '\n'
            
        if len(found_without_name) > 0:
            issues += 'The following objects were found, but had a different name:\n'
        for obj in found_without_name:
            issues += '"' + str(get_short_name(obj[0])) + '" =>  Expected: "'+ str(obj[1]) + '".\n'

 

        #--------------------------------
              
              
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
		message='Please, provide a due date to calculate how many days it has passed.\n(The script uses the last modified date on the file as the submission date.)\n\nFormat: "MM/DD" for example "05/15"',
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
                cmds.modelEditor(each_panel, e=1, joints=1)
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
        '''
        # Pairs to be sorted and renamed
        to_rename = []

        # Joints
        all_joints = cmds.ls(type='joint', long=True)
        for obj in brute_force_joint_naming_dict:
            
            if type(brute_force_joint_naming_dict.get(obj)[2]) is tuple:
                new_scale = brute_force_joint_naming_dict.get(obj)[2]
                ray_tracing_obj = cmds.polySphere(name=('ray_tracing_obj_' + obj), r=1, sx=8, sy=8, ch=False, cuv=False)
                if cmds.objExists(ray_tracing_obj[0]):
                    cmds.setAttr(ray_tracing_obj[0] + '.scaleX', new_scale[0])
                    cmds.setAttr(ray_tracing_obj[0] + '.scaleY', new_scale[1])
                    cmds.setAttr(ray_tracing_obj[0] + '.scaleZ', new_scale[2])
            else:
                ray_tracing_obj = cmds.polySphere(name=('ray_tracing_obj_' + obj), r=brute_force_joint_naming_dict.get(obj)[2], sx=8, sy=8, ch=False, cuv=False)
                cmds.xform(ray_tracing_obj, ws=True, ro=(0,0,90) )
                cmds.makeIdentity(ray_tracing_obj, apply=True, rotate=True)
            cmds.xform(ray_tracing_obj, a=True, ro=brute_force_joint_naming_dict.get(obj)[1] )
            cmds.xform(ray_tracing_obj, a=True, t=brute_force_joint_naming_dict.get(obj)[0] )
            
            for jnt in all_joints:
                jnt_pos = cmds.xform(jnt, piv=True , q=True , ws=True)
                is_joint_inside = is_point_inside_mesh(ray_tracing_obj[0], point=(jnt_pos[0],jnt_pos[1],jnt_pos[2]))
                
                ignore_joint = False
                if len(brute_force_joint_naming_dict.get(obj)) == 4:
                    for string in brute_force_joint_naming_dict.get(obj)[3]:
                        if string in jnt:
                            ignore_joint = True
                
                if is_joint_inside and get_short_name(jnt) != obj and ignore_joint is False:
                    to_rename.append([jnt, obj])

            cmds.delete(ray_tracing_obj)
        
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
                crv_transform = cmds.listRelatives(crv, allParents=True) or []
                if len(crv_transform) > 0:
                    crv_pos = cmds.xform(crv_transform[0], piv=True , q=True , ws=True)
                    is_crv_inside = is_point_inside_mesh(ray_tracing_obj[0], point=(crv_pos[0],crv_pos[1],crv_pos[2]))
                    
                    ignore_crv = False
                    if len(brute_force_ctrl_naming_dict.get(obj)) == 4:
                        for string in brute_force_ctrl_naming_dict.get(obj)[3]:
                            if string in jnt:
                                ignore_crv = True
                    
                    if is_crv_inside and get_short_name(crv_transform[0]) != obj  and ignore_crv is False:
                        to_rename.append([crv_transform[0], obj])
            cmds.delete(ray_tracing_obj)
               
        # Sort it based on how many parents it has
        pipe_pairs_to_rename = []
        for obj in to_rename:
            pipe_pairs_to_rename.append([len(obj[0].split('|')), obj])
            
        sorted_pairs_to_rename = sorted(pipe_pairs_to_rename, key=lambda x: x[0], reverse=True)

        # Rename sorted pairs
        errors = ''    
        for pair in sorted_pairs_to_rename:
            if cmds.objExists(pair[1][0]):
                try:
                    cmds.rename(pair[1][0], pair[1][1])
                except Exception as exception:
                    errors = errors + '"' + str(pair[1][1]) + '" : "' + exception[0].rstrip("\n") + '".\n'
        if errors != '':
                cmds.scrollField(output_scroll_field, e=True, clear=True)
                cmds.scrollField(output_scroll_field, e=True, ip=0, it=str(exception) + '\n')
                
    def toggle_big_joints_visibility(jnt_contains_list):
        '''
        Hide joints that might get on the way when checking location of the joints
        
                Parameters:
                        jnt_contains_list (list): A list of strings. If any joints contains one of these strings, it is considered a big joint.
     
        '''
        all_joints = cmds.ls(type='joint')
        hidden_joints = []
        visible_joints = []
        
        try:
            for jnt in all_joints:
                for jnt_string in jnt_contains_list:
                    if jnt_string in jnt and cmds.getAttr(jnt + ".drawStyle") == 2:
                        hidden_joints.append(jnt)
                    elif jnt_string in jnt and cmds.getAttr(jnt + ".drawStyle") == 0:
                        visible_joints.append(jnt)
        except:
            visible_joints.append('__place_holder__')

      
        if visible_joints < hidden_joints:
            is_hidding = True
        else:
            is_hidding = False

        try:
            for obj in all_joints:
                is_big_joint = False
                for big_jnt in jnt_contains_list:
                    if big_jnt in obj.lower():
                        is_big_joint = True
                if cmds.objExists(obj) and is_big_joint == True:
                    if not is_hidding:
                        if cmds.getAttr(obj + ".drawStyle" ,lock=True) is False:
                            cmds.setAttr(obj + '.drawStyle', 2)
                    else:
                         if cmds.getAttr(obj + ".drawStyle" ,lock=True) is False:
                            cmds.setAttr(obj + '.drawStyle', 0)
                        
                                    
        except Exception as exception:
            cmds.scrollField(output_scroll_field, e=True, clear=True)
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=str(exception) + '\n')
    

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


def key_spine(spine_list, keyframes_interval):
    '''Key Spine Joints (Used for upper body and symmetry steps)'''
    for spine in spine_list:
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
                cmds.setKeyframe(my_obj, v=value, at=attribute, t=at_frame, itt='linear')
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

    
def joint_placement_skinning():
    '''Checks Joint Placement and Skinning'''
    
    # Reset other buttons
    for item in gt_grading_components:
        item_id = gt_grading_components.get(item)[0].lower().replace(" & ","_").replace(" ","_").replace("-","_").replace(",","").replace(":","")
        if 'joint_placement_skinning' not in item_id:
            cmds.button('check_btn_' + item_id, e=True, l='Check', bgc=[.5,.7,.5], ann='0')
    delete_all_keyframes()
    reset_transforms()
        
    # Unsubdivide Meshes
    unsubdivide_geometries()
                
    # Reset Time
    cmds.currentTime(0)
    
    # Adjust Size of the timeline
    keyframes_interval = gt_grading_settings.get('keyframes_interval')
    cmds.playbackOptions(minTime=0, max = (keyframes_interval * 14))
    
    # Focus On Head Area
    frame_object('neckBase_Jnt')
    frame_object('neckBase_jnt')
    frame_object('neckbase_jnt')
    
    # Try to make joints visible
    all_transforms = cmds.ls(type='transform')
    all_joints = cmds.ls(type='transform')
    
    for jnt in all_joints: 
        if 'root' in jnt:
            if cmds.getAttr(jnt + ".v" , lock=True):
                cmds.setAttr(jnt + ".v", lock=False)
            cmds.setAttr(jnt + ".v", 1)
            
    for obj in all_transforms: 
        if 'skeleton' in obj or 'bones' in obj:
            if cmds.getAttr(obj + ".v" , lock=True):
                cmds.setAttr(obj + ".v", lock=False)
            cmds.setAttr(obj + ".v", 1)
            
    
    try:
        panel_list = cmds.getPanel(type="modelPanel")
    
        for each_panel in panel_list:
            cmds.modelEditor(each_panel, e=1, polymeshes=1)
            cmds.modelEditor(each_panel, e=1, joints=1)
            cmds.modelEditor(each_panel, e=1, wireframeOnShaded=1)
            
    except:
        pass
    
    
    # Clean Selection
    cmds.select(clear=True)
        
    delete_all_keyframes()
    reset_transforms()
    cmds.play(state=False)
    cmds.currentTime(0)
    
    try:
        from ngSkinTools.ui.mainwindow import MainWindow
        MainWindow.open()
    except:
        pass
    
        

def controls_side_ui_connection():
    '''Checks Upper body and fingers'''
    
    # Reset other buttons
    for item in gt_grading_components:
        item_id = gt_grading_components.get(item)[0].lower().replace(" & ","_").replace(" ","_").replace("-","_").replace(",","").replace(":","")
        if 'controls_side_ui_connection' not in item_id:
            cmds.button('check_btn_' + item_id, e=True, l='Check', bgc=[.5,.7,.5], ann='0')
    delete_all_keyframes()
    reset_transforms()
    
    # Check Button Status
    button_status = int(cmds.button('check_btn_controls_side_ui_connection', q=True, ann=True))
    if not button_status:
        # Change button to stop and update its status
        cmds.button('check_btn_controls_side_ui_connection', e=True, l='Stop', bgc=[.5,.2,.2], ann='1')
        
        # Unsubdivide Meshes
        unsubdivide_geometries()
        
        
        # Reset Time
        cmds.currentTime(0)
        
        # Adjust Size of the timeline
        keyframes_interval = gt_grading_settings.get('keyframes_interval')
        cmds.playbackOptions(minTime=0, max = (keyframes_interval * 34))
                    
        # Focus On Head Area
        frame_object('head_Jnt')
        frame_object('head_jnt')
        frame_object('head_jnt')
         
        
        # Right Eyebrows
        to_key = ['right_outerBrow_Ctrl', 'right_outerBrow_ctrl', 'right_outerBrowCtrl']
        # TY
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 2))
        keyframe_list(to_key, 5, 'translateY', (keyframes_interval * 3))
        keyframe_list(to_key, -5, 'translateY', (keyframes_interval * 4))
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 5))
        
        to_key = ['right_midBrow_Ctrl', 'right_midBrow_ctrl', 'right_midBrowCtrl']
        # TY
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 6))
        keyframe_list(to_key, 5, 'translateY', (keyframes_interval * 7))
        keyframe_list(to_key, -5, 'translateY', (keyframes_interval * 8))
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 9))
        
        to_key = ['right_innerBrow_Ctrl', 'right_innerBrow_ctrl', 'right_innerBrowCtrl']
        # TY
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 10))
        keyframe_list(to_key, 5, 'translateY', (keyframes_interval * 11))
        keyframe_list(to_key, -5, 'translateY', (keyframes_interval * 12))
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 13))
        # TX
        keyframe_list(to_key, 0, 'translateX', (keyframes_interval * 14))
        keyframe_list(to_key, 5, 'translateX', (keyframes_interval * 15))
        keyframe_list(to_key, 5, 'translateX', (keyframes_interval * 16))
        keyframe_list(to_key, 0, 'translateX', (keyframes_interval * 17))
        
        # Left Eyebrows
        to_key = ['left_outerBrow_Ctrl', 'left_outerBrow_ctrl', 'left_outerBrowCtrl']
        # TY
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 2))
        keyframe_list(to_key, 5, 'translateY', (keyframes_interval * 3))
        keyframe_list(to_key, -5, 'translateY', (keyframes_interval * 4))
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 5))
        
        to_key = ['left_midBrow_Ctrl', 'left_midBrow_ctrl', 'left_midBrowCtrl'] 
        # TY
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 6))
        keyframe_list(to_key, 5, 'translateY', (keyframes_interval * 7))
        keyframe_list(to_key, -5, 'translateY', (keyframes_interval * 8))
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 9))
        
        to_key = ['left_innerBrow_Ctrl', 'left_innerBrow_ctrl', 'left_innerBrowCtrl']
        # TY
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 10))
        keyframe_list(to_key, 5, 'translateY', (keyframes_interval * 11))
        keyframe_list(to_key, -5, 'translateY', (keyframes_interval * 12))
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 13))
        # TX
        keyframe_list(to_key, 0, 'translateX', (keyframes_interval * 14))
        keyframe_list(to_key, -5, 'translateX', (keyframes_interval * 15))
        keyframe_list(to_key, -5, 'translateX', (keyframes_interval * 16))
        keyframe_list(to_key, 0, 'translateX', (keyframes_interval * 17))
        
        
        to_key = ['right_outerBrow_Ctrl', 'right_outerBrow_ctrl', 'right_outerBrowCtrl', 'right_midBrow_Ctrl', 'right_midBrow_ctrl', 'right_midBrowCtrl',\
                  'right_innerBrow_Ctrl', 'right_innerBrow_ctrl', 'right_innerBrowCtrl', 'left_outerBrow_Ctrl', 'left_outerBrow_ctrl', 'left_outerBrowCtrl',\
                  'left_midBrow_Ctrl', 'left_midBrow_ctrl', 'left_midBrowCtrl', 'left_innerBrow_Ctrl', 'left_innerBrow_ctrl', 'left_innerBrowCtrl']
        # TY
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 16))
        keyframe_list(to_key, 5, 'translateY', (keyframes_interval * 18))
        keyframe_list(to_key, -5, 'translateY', (keyframes_interval * 20))
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 22))
        
        
        # Eyes
        to_key = ['right_eyelid_close_Ctrl', 'right_eyelid_close_ctrl', 'right_eyelid_closeCtrl','left_eyelid_close_Ctrl', 'left_eyelid_close_ctrl', 'left_eyelid_closeCtrl']
        # TY
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 10))
        keyframe_list(to_key, -10, 'translateY', (keyframes_interval * 12))
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 15))
        
        # Cheeks
        to_key = ['left_outerCheek_Ctrl', 'left_outerCheek_ctrl', 'left_outerCheekCtrl','right_outerCheek_Ctrl', 'right_outerCheek_ctrl', 'right_outerCheekCtrl',\
                  'left_innerCheek_Ctrl', 'left_innerCheek_ctrl', 'left_innerCheekCtrl', 'right_innerCheek_Ctrl', 'right_innerCheek_ctrl', 'right_innerCheekCtrl',\
                  'left_puffCheek_Ctrl', 'left_puffCheek_ctrl', 'left_puffCheekCtrl', 'right_puffCheek_Ctrl', 'right_puffCheek_ctrl', 'right_puffCheekCtrl']
        # TY
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 2))
        keyframe_list(to_key, 10, 'translateY', (keyframes_interval * 4))
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 6))

        # Mouth Corners
        to_key = ['right_lipCorner_Ctrl', 'right_lipCorner_ctrl', 'right_lipCornerCtrl','left_lipCorner_Ctrl', 'left_lipCorner_ctrl', 'left_lipCornerCtrl']
        # TY
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 6))
        keyframe_list(to_key, 5, 'translateY', (keyframes_interval * 8))
        keyframe_list(to_key, -5, 'translateY', (keyframes_interval * 10))
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 12))
        
        # TX
        to_key = ['right_lipCorner_Ctrl', 'right_lipCorner_ctrl', 'right_lipCornerCtrl']
        keyframe_list(to_key, 0, 'translateX', (keyframes_interval * 18))
        keyframe_list(to_key, 5, 'translateX', (keyframes_interval * 20))
        keyframe_list(to_key, -5, 'translateX', (keyframes_interval * 22))
        keyframe_list(to_key, 0, 'translateX', (keyframes_interval * 24))
        to_key = ['left_lipCorner_Ctrl', 'left_lipCorner_ctrl', 'left_lipCornerCtrl']
        keyframe_list(to_key, 0, 'translateX', (keyframes_interval * 18))
        keyframe_list(to_key, -5, 'translateX', (keyframes_interval * 20))
        keyframe_list(to_key, 5, 'translateX', (keyframes_interval * 22))
        keyframe_list(to_key, 0, 'translateX', (keyframes_interval * 24))
        
        # Mouth Inside
        to_key = ['right_upperOutLip_ctrl', 'right_upperOutLipCtrl','left_upperOutLip_Ctrl', 'left_upperOutLip_ctrl',\
                  'left_upperOutLipCtrl', 'right_lowerOutLip_Ctrl', 'right_lowerOutLip_ctrl', 'right_lowerOutLipCtrl',\
                  'left_lowerOutLip_Ctrl', 'left_lowerOutLip_ctrl', 'left_lowerOutLipCtrl','right_upperOutLip_Ctrl']
        # TY
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 12))
        keyframe_list(to_key, 5, 'translateY', (keyframes_interval * 14))
        keyframe_list(to_key, -5, 'translateY', (keyframes_interval * 16))
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 18))
        
        # Mouth Mid
        to_key = ['mid_lip_Ctrl', 'mid_lip_ctrl', 'mid_lipCtrl']
        # TY
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 1))
        keyframe_list(to_key, 5, 'translateY', (keyframes_interval * 3))
        keyframe_list(to_key, -5, 'translateY', (keyframes_interval * 5))
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 7))
        
        # Jaw 
        to_key = ['jaw_Ctrl', 'jaw_ctrl', 'jawCtrl']
        # TY
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 20))
        keyframe_list(to_key, 5, 'translateY', (keyframes_interval * 22))
        keyframe_list(to_key, -5, 'translateY', (keyframes_interval * 24))
        keyframe_list(to_key, -5, 'translateY', (keyframes_interval * 32))
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 34))
        
        # Tongue In Out
        to_key = ['tongue_in_out_Ctrl', 'tongue_in_out_ctrl', 'tongue_in_outCtrl']
        # TY
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 24))
        keyframe_list(to_key, 10, 'translateY', (keyframes_interval * 26))
        keyframe_list(to_key, 10, 'translateY', (keyframes_interval * 32))
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 33))
        
        # Tongue ROT
        to_key = ['tongue_Ctrl', 'tongue_ctrl', 'tongueCtrl']
        # TY
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 26))
        keyframe_list(to_key, 5, 'translateY', (keyframes_interval * 27))
        keyframe_list(to_key, -5, 'translateY', (keyframes_interval * 28))
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 29))
        # TX
        keyframe_list(to_key, 0, 'translateX', (keyframes_interval * 29))
        keyframe_list(to_key, 5, 'translateX', (keyframes_interval * 30))
        keyframe_list(to_key, -5, 'translateX', (keyframes_interval * 31))
        keyframe_list(to_key, 0, 'translateX', (keyframes_interval * 32))

        # Eyes Aim
        to_key = ['main_eye_Ctrl', 'main_eye_ctrl', 'main_eyeCtrl']
        # TY
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 16))
        keyframe_list(to_key, 5, 'translateY', (keyframes_interval * 18))
        keyframe_list(to_key, -5, 'translateY', (keyframes_interval * 20))
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 22))
        # TX
        keyframe_list(to_key, 0, 'translateX', (keyframes_interval * 22))
        keyframe_list(to_key, 5, 'translateX', (keyframes_interval * 24))
        keyframe_list(to_key, -5, 'translateX', (keyframes_interval * 26))
        keyframe_list(to_key, 0, 'translateX', (keyframes_interval * 28))
        
        to_key = ['left_eye_Ctrl', 'left_eye_ctrl', 'left_eyeCtrl', 'right_eye_Ctrl', 'right_eye_ctrl', 'right_eyeCtrl']
        # TY
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 2))
        keyframe_list(to_key, 5, 'translateY', (keyframes_interval * 4))
        keyframe_list(to_key, -5, 'translateY', (keyframes_interval * 6))
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 8))
        # TX
        keyframe_list(to_key, 0, 'translateX', (keyframes_interval * 8))
        keyframe_list(to_key, 5, 'translateX', (keyframes_interval * 10))
        keyframe_list(to_key, -5, 'translateX', (keyframes_interval * 12))
        keyframe_list(to_key, 0, 'translateX', (keyframes_interval * 14))

        # No Selection
        cmds.select(clear=True)
        
        # Play Animation
        cmds.PlaybackForward()
 
    else:
        # Kill Keys
        delete_all_keyframes()
        reset_transforms()
        
        cmds.button('check_btn_controls_side_ui_connection', e=True, l='Check', bgc=[.5,.7,.5], ann='0')
        cmds.play(state=False)
        cmds.currentTime(0)
        # No Selection
        cmds.select(clear=True)
    
def blend_shapes_deformers():
    '''Checks Lower body, legs and feet'''
    
    # Reset other buttons
    for item in gt_grading_components:
        item_id = gt_grading_components.get(item)[0].lower().replace(" & ","_").replace(" ","_").replace("-","_").replace(",","").replace(":","")
        if 'blend_shapes_deformers' not in item_id:
            cmds.button('check_btn_' + item_id, e=True, l='Check', bgc=[.5,.7,.5], ann='0')
    delete_all_keyframes()
    reset_transforms()
    
    # Check Button Status
    button_status = int(cmds.button('check_btn_blend_shapes_deformers', q=True, ann=True))
    if not button_status:
        
        # Change button to stop and update its status
        cmds.button('check_btn_blend_shapes_deformers', e=True, l='Stop', bgc=[.5,.2,.2], ann='1')
        
        # Unsubdivide Meshes
        unsubdivide_geometries()
        
        
        # Reset Time
        cmds.currentTime(0)
        
        # Adjust Size of the timeline
        keyframes_interval = gt_grading_settings.get('keyframes_interval')
        cmds.playbackOptions(minTime=0, max = (keyframes_interval * 34))
                    
        # Focus On Head Area
        frame_object('head_Jnt')
        frame_object('head_jnt')
        frame_object('head_jnt')
        
        # Try to hide eye controls
        to_key = ['main_eye_Ctrl', 'main_eye_ctrl', 'main_eyeCtrl']
        for obj in to_key:
            if cmds.objExists(obj):
                try:
                    cmds.setAttr(obj + '.v', 0)
                except:
                    pass
        
        # Eyes
        to_key = ['right_eyelid_close_Ctrl', 'right_eyelid_close_ctrl', 'right_eyelid_closeCtrl','left_eyelid_close_Ctrl', 'left_eyelid_close_ctrl', 'left_eyelid_closeCtrl']
        # TY
        keyframe_list(to_key, 0, 'translateY', 0)
        keyframe_list(to_key, -10, 'translateY', (keyframes_interval * 2))
        keyframe_list(to_key, -10, 'translateY', (keyframes_interval * 6))
        keyframe_list(to_key, 0, 'translateY', (keyframes_interval * 8))
        

        # TX
        to_key = ['right_lipCorner_Ctrl', 'right_lipCorner_ctrl', 'right_lipCornerCtrl']
        keyframe_list(to_key, 0, 'translateX', 0)
        keyframe_list(to_key, 5, 'translateX', (keyframes_interval * 2))
        keyframe_list(to_key, 5, 'translateX', (keyframes_interval * 6))
        keyframe_list(to_key, 0, 'translateX', (keyframes_interval * 8))
        to_key = ['left_lipCorner_Ctrl', 'left_lipCorner_ctrl', 'left_lipCornerCtrl']
        keyframe_list(to_key, 0, 'translateX', 0)
        keyframe_list(to_key, -5, 'translateX', (keyframes_interval * 2))
        keyframe_list(to_key, -5, 'translateX', (keyframes_interval * 6))
        keyframe_list(to_key, 0, 'translateX', (keyframes_interval * 8))
        
     
        # Head
        to_key = ['head_Ctrl', 'head_ctrl', 'headCtrl']
        # RX
        keyframe_list(to_key, 0, 'rx', (keyframes_interval * 6))
        keyframe_list(to_key, -90, 'rx', (keyframes_interval * 8))
        keyframe_list(to_key, 90, 'rx', (keyframes_interval * 10))
        keyframe_list(to_key, 0, 'rx', (keyframes_interval * 12))
        
        # Extra for squash stretch
        keyframe_list(to_key, 0, 'rx', (keyframes_interval * 23))
        keyframe_list(to_key, 30, 'rx', (keyframes_interval * 25))
        keyframe_list(to_key, 30, 'rx', (keyframes_interval * 30))
        keyframe_list(to_key, 0, 'rx', (keyframes_interval * 32))
        
        # RY
        keyframe_list(to_key, 0, 'ry', (keyframes_interval * 12))
        keyframe_list(to_key, -45, 'ry', (keyframes_interval * 14))
        keyframe_list(to_key, 45, 'ry', (keyframes_interval * 16))
        keyframe_list(to_key, 0, 'ry', (keyframes_interval * 18))
        
        # Squash Stretch
        to_key = ['head_squashStretch_Ctrl', 'head_squashStretch_ctrl', 'head_squashStretchCtrl']
        # TY
        keyframe_list(to_key, 0, 'ty', (keyframes_interval * 17))
        keyframe_list(to_key, 5, 'ty', (keyframes_interval * 19))
        keyframe_list(to_key, -5, 'ty', (keyframes_interval * 21))
        keyframe_list(to_key, 0, 'ty', (keyframes_interval * 23))
        
        # TX
        keyframe_list(to_key, 0, 'tx', (keyframes_interval * 17))
        keyframe_list(to_key, -5, 'tx', (keyframes_interval * 19))
        keyframe_list(to_key, 5, 'tx', (keyframes_interval * 21))
        keyframe_list(to_key, 0, 'tx', (keyframes_interval * 23))
        
        # TY
        keyframe_list(to_key, 0, 'ty', (keyframes_interval * 24))
        keyframe_list(to_key, 5, 'ty', (keyframes_interval * 26))
        keyframe_list(to_key, -5, 'ty', (keyframes_interval * 28))
        keyframe_list(to_key, 0, 'ty', (keyframes_interval * 30))
        
        # TX
        keyframe_list(to_key, 0, 'tx', (keyframes_interval * 24))
        keyframe_list(to_key, -5, 'tx', (keyframes_interval * 26))
        keyframe_list(to_key, 5, 'tx', (keyframes_interval * 28))
        keyframe_list(to_key, 0, 'tx', (keyframes_interval * 30))
     
        # Open Shape Editor
        mel.eval('ShapeEditor')

        # No Selection
        cmds.select(clear=True)
        
        # Play Animation
        cmds.PlaybackForward()
 
    else:
        # Try to unhide eye controls
        to_key = ['main_eye_Ctrl', 'main_eye_ctrl', 'main_eyeCtrl']
        for obj in to_key:
            if cmds.objExists(obj):
                try:
                    cmds.setAttr(obj + '.v', 1)
                except:
                    pass
        # Kill Keys
        delete_all_keyframes()
        reset_transforms()
        # Reset Button
        cmds.button('check_btn_blend_shapes_deformers', e=True, l='Check', bgc=[.5,.7,.5], ann='0')
        cmds.play(state=False)
        cmds.currentTime(0)
        # No Selection
        cmds.select(clear=True)
    

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



#Build GUI
if __name__ == '__main__':
    build_gui_gt_grader_script()