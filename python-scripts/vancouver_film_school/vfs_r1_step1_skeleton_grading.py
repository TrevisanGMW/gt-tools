"""

 Rigging 1 - Betty Skeleton Check - v1.2
 This script checks for issues in the skeleton (joints) for the character "Betty" in Rigging 1 - VFS
 Part of the code used for this script was repourposed from a previous script found in the course material folder (2019)
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-03-01 - github.com/TrevisanGMW

 1.1 
 Changed part fo the previously created code to match new version of Betty.
 Removed duplicated joint for wrist (to simplify it)
 
 1.2
 Created GUI
 Added output textbox (so students don't need to use script editor at this point)
 Changed the names of all joints to match a new pattern - "side_description_jnt" (all lowercase)
 
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


# Checklist Name
character_name = 'Betty'
script_name = 'Rigging 1 - Skeleton Checker'

# Version
script_version = '1.2'


def build_gui_gt_r1_skeleton_check():
    
    window_name = "build_gui_gt_r1_skeleton_check"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title= script_name + ' - v' + script_version, mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1,1])

    cmds.columnLayout("main_column", p= window_name)
   
    # Title Text
    cmds.separator(h=12, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 410)], cs=[(1, 10)], p="main_column") # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 400)], cs=[(1, 10)], p="main_column") # Title Column
    cmds.text(script_name, bgc=[0,.5,0],  fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p="main_column") # Empty Space

    # Body ====================
    checklist_spacing = 4
    cmds.rowColumnLayout(nc=1, cw=[(1, 400)], cs=[(1,10)], p="main_column")
    cmds.text(l='This script performs a series of checks to detect common issues that are often\naccidently ignored when creating a skeleton for the first time. (Assignment 1)', align="left")
    cmds.text(l='', align="left")
    cmds.text(l='Make sure you run this script before submitting your skeleton.', align="center")
    cmds.text(l='\nCurrent Character: "' + character_name + '"    -   Assignment: "Rigging 1.1"', align="center")
    #cmds.text(l='', align="left")  

    
    cmds.separator(h=15, style='none') # Empty Space

    # Checklist Items =============
    cmds.rowColumnLayout(nc=1, cw=[(1, 400)], cs=[(1, 10)], p="main_column")
    cmds.text(l='Output:', align="center", fn="boldLabelFont") 
    cmds.text(l='Use the refresh button below to check for issues:', align="center", fn="smallPlainLabelFont") 
    cmds.separator(h=checklist_spacing, style='none') # Empty Space
   
   
    output_scroll_field = cmds.scrollField(editable=False, wordWrap=True, fn="obliqueLabelFont")
    
    cmds.separator(h=10, style='none') # Empty Space

    # Refresh Button
    cmds.rowColumnLayout(nc=1, cw=[(1, 400)], cs=[(1,10)], p="main_column")
    cmds.separator(h=10, style='none')
    cmds.button(l='Refresh', h=30, c=lambda args: reroute_errors())
    cmds.separator(h=8, style='none')
    
    # Show and Lock Window
    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/kinJoint.png')
    widget.setWindowIcon(icon)
    
    
    def reroute_errors():
        try:
            check_skeleton()
        except Exception as exception:
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=str(exception) + '\n')
    
    
    def check_skeleton():
        
        cmds.scrollField(output_scroll_field, e=True, clear=True)
        
        mark = 0
        root = []

        name_mark = 0
        parenting_mark = 0
        orients_mark = 0
        transforms_mark = 0
        placement_mark = 0
        scene_mark = 0
        deductions = 0
        
        placement_mark_division = 0.353
        orients_mark_division = 0.355
        transforms_mark_division = 0.071
        parenting_mark_division = 0.141
        name_mark_division = 0.3522
        
        check_position = {'head_end_jnt': [0.0, 149.627, 0.668539302549], \
                    'head_jnt': [0.0, 120.015257626, -0.639659610777], \
                    'jaw_end_jnt': [0.0, 116.236452934, 13.6109303846], \
                    'jaw_jnt': [0.0, 126.167495596, 0.348183087647], \
                    'left_ankle_jnt': [7.0123406744, 4.86555330952, -2.79820729391], \
                    'left_ball_jnt': [6.958, 0.056, 3.4], \
                    'left_clavicle_jnt': [1.99819553729, 106.182093768, 4.33649659673], \
                    'left_elbow_jnt': [22.068, 89.436, -4.228], \
                    'left_eye_jnt': [6.43210369349, 129.206703186, 8.14929789305], \
                    'left_hip_jnt': [7.0123406744, 67.9592303246, -1.51017675398], \
                    'left_index1_jnt': [36.9358118715, 65.9390942712, 2.79654683133], \
                    'left_index2_jnt': [38.2771633644, 63.2194228843, 3.71898456919], \
                    'left_index3_jnt': [38.661564528, 61.5304646092, 4.12551802376], \
                    'left_index_end_jnt': [38.7522360987, 60.0286719031, 4.47728607869], \
                    'left_knee_jnt': [7.0123406744, 36.8033011581, 0.0795756394473], \
                    'left_middle1_jnt': [37.9307463496, 65.8299701415, 1.54959082013], \
                    'left_middle2_jnt': [38.7690353438, 62.681506381, 2.27610790846], \
                    'left_middle3_jnt': [39.0054656954, 60.6694057821, 2.68708099936], \
                    'left_middle_end_jnt': [38.9414521895, 59.1075947384, 2.95970994586], \
                    'left_pinky1_jnt': [37.3551393862, 65.5599821692, -1.25996026201], \
                    'left_pinky2_jnt': [37.9827198168, 62.814317734, -1.00771080677], \
                    'left_pinky3_jnt': [37.9362171314, 61.4300044519, -0.889283355574], \
                    'left_pinky_end_jnt': [37.8184834472, 60.3680630906, -0.802542448691], \
                    'left_ring1_jnt': [37.6885763314, 65.68324954, 0.0229446386359], \
                    'left_ring2_jnt': [38.4179729513, 62.4753505534, 0.589287495165], \
                    'left_ring3_jnt': [38.5253316541, 60.632464935, 0.873300648774], \
                    'left_ring_end_jnt': [38.4986920063, 59.1844513526, 1.07851490242], \
                    'left_shoulder_jnt': [11.0031830733, 105.341662531, 0.477419333912], \
                    'left_thumb1_jnt': [33.9591622097, 68.9890666496, 1.61462823792], \
                    'left_thumb2_jnt': [34.0388565884, 67.3726171241, 2.89815868748], \
                    'left_thumb3_jnt': [34.1500088529, 65.4871552069, 4.38099207377], \
                    'left_thumb_end_jnt': [33.8280998265, 64.247060114, 6.548938852], \
                    'left_toe_end_jnt': [7.0123406744, 0.577092467654, 9.954320999], \
                    'left_wrist_jnt': [34.495, 70.633, -0.164], \
                    'neck1_jnt': [0.0, 111.421, 1.214], \
                    'neck2_jnt': [0.0, 115.006130224, 0.297299471595], \
                    'right_ankle_jnt': [-7.01234, 4.86555, -2.79821], \
                    'right_ball_jnt': [-7.01234, 1.02851, 4.53732], \
                    'right_clavicle_jnt': [-1.9982, 106.182, 4.3365], \
                    'right_elbow_jnt': [-22.4758, 89.4607, -3.50156], \
                    'right_eye_jnt': [-6.4321, 129.207, 8.1493], \
                    'right_hip_jnt': [-7.01234, 67.9592, -1.51018], \
                    'right_index1_jnt': [-36.9358, 65.9391, 2.79655], \
                    'right_index2_jnt': [-38.2772, 63.2194, 3.71898], \
                    'right_index3_jnt': [-38.6616, 61.5305, 4.12552], \
                    'right_index_end_jnt': [-38.7522, 60.0287, 4.47729], \
                    'right_knee_jnt': [-7.01234, 36.8033, 0.0795756], \
                    'right_middle1_jnt': [-37.9307, 65.83, 1.54959], \
                    'right_middle2_jnt': [-38.769, 62.6815, 2.27611], \
                    'right_middle3_jnt': [-39.0055, 60.6694, 2.68708], \
                    'right_middle_end_jnt': [-38.9415, 59.1076, 2.95971], \
                    'right_pinky1_jnt': [-37.3551, 65.56, -1.25996], \
                    'right_pinky2_jnt': [-37.9827, 62.8143, -1.00771], \
                    'right_pinky3_jnt': [-37.9362, 61.43, -0.889283], \
                    'right_pinky_end_jnt': [-37.8185, 60.3681, -0.802542], \
                    'right_ring1_jnt': [-37.6886, 65.6832, 0.0229446], \
                    'right_ring2_jnt': [-38.418, 62.4754, 0.589287], \
                    'right_ring3_jnt': [-38.5253, 60.6325, 0.873301], \
                    'right_ring_end_jnt': [-38.4987, 59.1845, 1.07851], \
                    'right_shoulder_jnt': [-11.0032, 105.342, 0.477419], \
                    'right_thumb1_jnt': [-33.9592, 68.9891, 1.61463], \
                    'right_thumb2_jnt': [-34.0389, 67.3726, 2.89816], \
                    'right_thumb3_jnt': [-34.15, 65.4872, 4.38099], \
                    'right_thumb_end_jnt': [-33.8281, 64.2471, 6.54894], \
                    'right_toe_end_jnt': [-7.01234, 0.577092, 9.95432], \
                    'right_wrist_jnt': [-34.626, 70.0684, 0.0809637], \
                    'root_jnt': [0.0, 69.5529866698, -0.765198021547], \
                    'spine1_jnt': [0.0, 77.2626710745, 2.34698601378], \
                    'spine2_jnt': [0.0, 85.6171219688, 4.20944831972], \
                    'spine3_jnt': [0.0, 89.744, 6.318], \
                    'spine4_jnt': [0.0, 95.128, 5.423]}

        joint_names = ['root_jnt', 'spine1_jnt', 'spine2_jnt', 'spine3_jnt', 'spine4_jnt', \
                       'neck1_jnt', 'neck2_jnt', 'head_jnt', 'head_end_jnt', 'jaw_jnt', 'jaw_end_jnt', \
                       'left_eye_jnt', 'right_eye_jnt', 'left_clavicle_jnt', 'left_shoulder_jnt', \
                       'left_elbow_jnt', 'left_wrist_jnt', 'left_thumb1_jnt', \
                       'left_thumb2_jnt', 'left_thumb3_jnt', 'left_thumb_end_jnt', 'left_index1_jnt', \
                       'left_index2_jnt', 'left_index3_jnt', 'left_index_end_jnt', 'left_middle1_jnt', \
                       'left_middle2_jnt', 'left_middle3_jnt', 'left_middle_end_jnt', 'left_ring1_jnt', \
                       'left_ring2_jnt', 'left_ring3_jnt', 'left_ring_end_jnt', 'left_pinky1_jnt', \
                       'left_pinky2_jnt', 'left_pinky3_jnt', 'left_pinky_end_jnt', 'right_clavicle_jnt', \
                       'right_shoulder_jnt', 'right_elbow_jnt', 'right_wrist_jnt', \
                       'right_thumb1_jnt', 'right_thumb2_jnt', 'right_thumb3_jnt', 'right_thumb_end_jnt', \
                       'right_index1_jnt', 'right_index2_jnt', 'right_index3_jnt', 'right_index_end_jnt', \
                       'right_middle1_jnt', 'right_middle2_jnt', 'right_middle3_jnt', 'right_middle_end_jnt', \
                       'right_ring1_jnt', 'right_ring2_jnt', 'right_ring3_jnt', 'right_ring_end_jnt', \
                       'right_pinky1_jnt', 'right_pinky2_jnt', 'right_pinky3_jnt', 'right_pinky_end_jnt', \
                       'left_hip_jnt', 'left_knee_jnt', 'left_ankle_jnt', 'left_ball_jnt', 'left_toe_end_jnt', \
                       'right_hip_jnt', 'right_knee_jnt', 'right_ankle_jnt', 'right_ball_jnt', 'right_toe_end_jnt']

        joints = cmds.ls(type='joint')

        # check file type
        file_type = cmds.file(query=True, type=1)
        if file_type[0] != 'mayaAscii':
            cmds.scrollField(output_scroll_field, e=True, ip=0, it='Your file must be saved as a ".ma".\n')
        else:
            scene_mark += 1

        # check number of joints
        if len(joints) != 71:
            cmds.scrollField(output_scroll_field, e=True, ip=0, it='Your skeleton has ' + str(len(joints)) + '. It should have 71 joints.\n')
            if len(joints) > 71:
                deductions = (abs(len(joints) - 71) * 5)

        # check to see what joints are missing
        for jnt in joint_names:
            if not cmds.objExists(jnt):
                cmds.scrollField(output_scroll_field, e=True, ip=0, it='Your skeleton does not have a joint named "' + jnt + '".\n')

        for jnt in joints:
            # check names
            if jnt not in joint_names:
                # check name
                cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + jnt + '" is not a proper name.\n')
            else:
                name_mark += name_mark_division

                parents = []
                orient_deduction = []
                if cmds.listRelatives(jnt, c=True, type='joint') or 'wrist' in jnt:
                    # check to make sure joints are oriented with a value that is consistent witht their parent
                    orient_check_jnts = ['spine', 'neck', 'head_jnt', 'jaw_jnt', 'shoulder', 'elbow', \
                                       'wrist', 'thumb', 'index', 'middle', 'ring', 'pinky', 'knee', 'ankle',
                                       'ball']
                    if any(j in jnt for j in orient_check_jnts) and 'thumb1' not in jnt:
                        if cmds.listRelatives(jnt, children=True) or 'wrist' in jnt:
                            joint_orients = cmds.getAttr((jnt + '.jointOrient'))
                            total_orient = (abs(joint_orients[0][0]) + abs(joint_orients[0][1]) + abs(joint_orients[0][2]))
                            if (total_orient) > 150:
                                cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + jnt + '" or its parent has incorrect joint orients.\n')
                                parent_node = cmds.listRelatives(jnt, parent=True)
                                if parent_node:
                                    parents.append(parent_node[0])
                                orient_deduction.append(jnt)
                            elif (total_orient) > 110 and 'jaw_jnt' not in jnt:
                                cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + jnt + '" or its parent has incorrect joint orients.\n')
                                orient_deduction.append(jnt)
                                if cmds.listRelatives(jnt, parent=True):
                                    parents.append(cmds.listRelatives(jnt, parent=True))

                            elif (total_orient) > 90 and 'jaw_jnt' not in jnt and 'shoulder_jnt' not in jnt and 'index' not in jnt and 'middle' not in jnt and 'ring' not in jnt and 'pinky' not in jnt:
                                cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + jnt + '" or its parent has incorrect joint orients.\n')
                                orient_deduction.append(jnt)
                                if cmds.listRelatives(jnt, parent=True):
                                    parents.append(cmds.listRelatives(jnt, parent=True))
                            elif (total_orient) > 60 and 'ankle' not in jnt and 'jaw_jnt' not in jnt and 'shoulder_jnt' not in jnt and 'index' not in jnt and 'middle' not in jnt and 'ring' not in jnt and 'pinky' not in jnt:
                                cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + jnt + '" or its parent has incorrect joint orients.\n')
                                orient_deduction.append(jnt)
                                if cmds.listRelatives(jnt, parent=True):
                                    parents.append(cmds.listRelatives(jnt, parent=True))
                            elif (total_orient) > 20 and 'wrist' in jnt:
                                cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + jnt + '" or its parent has incorrect joint orients.\n')
                                orient_deduction.append(jnt)
                                if cmds.listRelatives(jnt, parent=True):
                                    parents.append(cmds.listRelatives(jnt, parent=True))
                            else:
                                orients_mark += orients_mark_division
                    # check to make sure joints have not been moved since their parent has oriented to them
                    orient_check_two_jnts = ['index2', 'index3', 'index_end_jnt', 'middle2', 'middle3', \
                                        'middleEnd', 'ring2', 'ring3', 'ringEnd', 'pinky2', 'pinky3', 'pinkyEnd', \
                                        'thumb2', 'thumb3', 'thumbEnd', 'elbow', 'shoulder', \
                                        'jawEnd', 'head_jnt', 'headEnd', 'neck', 'ball', 'toe', 'ankle', 'knee', 'spine']
                    if any(j in jnt for j in orient_check_two_jnts):
                        parent_joint = cmds.listRelatives(jnt, parent=True)
                        if parent_joint and parent_joint[0] not in parents:
                            if abs(cmds.getAttr(jnt + '.translateY')) > 0.05 or abs(
                                    cmds.getAttr(jnt + '.translateZ')) > 0.05:
                                cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + jnt + '" position is wrong or its parent has incorrect joint orients.\n')
                            elif jnt not in orient_deduction:
                                orients_mark += orients_mark_division

                    orients_mark = orients_mark - (len(orient_deduction) * 2.5)
                    if orients_mark < 0:
                        orients_mark = 0

                # check frozen transforms
                rot = cmds.getAttr((jnt + '.rotate'))
                scl = cmds.getAttr((jnt + '.scale'))
                if (0.001 < rot[0][0] > 0.001) or (0.001 < rot[0][1] > 0.001) or (0.001 < rot[0][2] > 0.001):
                    cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + jnt + '" has non-frozen rotations.\n')
                elif (scl[0][0] != 1) or (scl[0][1] != 1) or (scl[0][2] != 1):
                    cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + jnt + '" has non-frozen scales.\n')
                else:
                    transforms_mark += transforms_mark_division

                # check positions
                target_position = (check_position.get(jnt))
                current_position = cmds.xform(jnt, q=True, rp=True, ws=True)
                val = [a - b for a, b in zip(target_position, current_position)]
                val_total = abs(val[0]) + abs(val[1]) + abs(val[2])

                small_position_check = ['thumb', 'index', 'middle', 'ring', 'pinky', 'eye']
                mid_position_check = ['neck', 'head_jnt', 'shoulder', 'elbow', 'wrist', 'knee', 'ankle', 'ball', 'toe']
                large_position_check = ['root', 'spine', 'clavicle']
                if any(j in jnt for j in small_position_check) and not any(j in "1" for j in small_position_check):
                    if val_total > 3: ## Tolerance for small checks
                        cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + jnt + '" is not in the accurate position. Look at reference and adjust it.\n')
                    else:
                        placement_mark += placement_mark_division
                elif any(j in jnt for j in small_position_check) or any(j in jnt for j in mid_position_check):
                    if val_total > 4: ## Tolerance for mid check
                        cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + jnt + '" is not in the accurate position. Look at reference and adjust it.\n')
                    else:
                        placement_mark += placement_mark_division
                elif any(j in jnt for j in large_position_check):
                    if val_total > 7: ## Tolerance for large check
                        cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + jnt + '" is not in the accurate position. Look at reference and adjust it.\n')
                    else:
                        placement_mark += placement_mark_division
                elif val_total > 7: ## Tolerance for any other checks
                    cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + jnt + '" is not in the accurate position. Look at reference and adjust it.\n')
                else:
                    placement_mark += placement_mark_division

            # check to make sure there is only one hierarchy
            if not cmds.listRelatives(jnt, parent=True, type='joint'):
                root.append(jnt)
            # check parenting
            if jnt == 'root_jnt':
                if cmds.listRelatives(jnt, children=True) and len(cmds.listRelatives(jnt, children=True)) != 3:
                    cmds.scrollField(output_scroll_field, e=True, ip=0, it='root_jnt should have three child joints: spine1_jnt, left_hip_jnt, right_hip_jnt.\n')
                else:
                    parenting_mark += parenting_mark_division
            elif jnt == 'spine4_jnt':
                if cmds.listRelatives(jnt, children=True) and len(cmds.listRelatives(jnt, children=True)) != 3:
                    cmds.scrollField(output_scroll_field, e=True, ip=0, it='spine4_jnt should have three child joints: neck1_jnt, left_clavicle_jnt, right_clavicle_jnt.\n')
                else:
                    parenting_mark += parenting_mark_division
            elif jnt == 'head_jnt':
                if cmds.listRelatives(jnt, children=True) and len(cmds.listRelatives(jnt, children=True)) != 4:
                    cmds.scrollField(output_scroll_field, e=True, ip=0, it='head_jnt should have four child joints: jaw_jnt, head_end_jnt, left_eye_jnt, right_eye_jnt.\n')
                else:
                    parenting_mark += parenting_mark_division
            elif jnt == 'left_elbow_jnt':
                if cmds.listRelatives(jnt, children=True) and len(cmds.listRelatives(jnt, children=True)) != 1:
                    cmds.scrollField(output_scroll_field, e=True, ip=0, it='left_elbow_jnt should have a child joint: left_wrist_jnt.\n')
                else:
                    parenting_mark += parenting_mark_division
            elif jnt == 'right_elbow_jnt':
                if cmds.listRelatives(jnt, children=True) and len(cmds.listRelatives(jnt, children=True)) != 1:
                    cmds.scrollField(output_scroll_field, e=True, ip=0, it='right_elbow_jnt should have a child joint: right_wrist_jnt.\n')
                else:
                    parenting_mark += parenting_mark_division
            elif jnt == 'left_wrist_jnt':
                if cmds.listRelatives(jnt, children=True) and len(cmds.listRelatives(jnt, children=True)) != 5:
                    cmds.scrollField(output_scroll_field, e=True, ip=0, it='left_wrist_jnt should have five child joints: left_thumb1_jnt, left_index1_jnt, left_middle1_jnt, left_ring1_jnt, left_pinky1_jnt.\n')
                else:
                    parenting_mark += parenting_mark_division
            elif jnt == 'right_wrist_jnt':
                if cmds.listRelatives(jnt, children=True) and len(cmds.listRelatives(jnt, children=True)) != 5:
                    cmds.scrollField(output_scroll_field, e=True, ip=0, it='right_wrist_jnt should have five child joints: right_thumb1_jnt, right_index1_jnt, right_middle1_jnt, right_ring1_jnt, right_pinky1_jnt.\n')
                else:
                    parenting_mark += parenting_mark_division
            elif "_end_jnt" in jnt or "eye_jnt" in jnt:
                if cmds.listRelatives(jnt, children=True):
                    cmds.scrollField(output_scroll_field, e=True, ip=0, it=jnt + ' should not have any children.\n')
                else:
                    parenting_mark += parenting_mark_division
            elif cmds.listRelatives(jnt, children=True) and len(cmds.listRelatives(jnt, children=True)) != 1:
                cmds.scrollField(output_scroll_field, e=True, ip=0, it=jnt + ' should have only one children.\n')
            else:
                parenting_mark += parenting_mark_division

        # make sure joints are all under one hierarchy
        if len(root) > 1:
            cmds.scrollField(output_scroll_field, e=True, ip=0, it='Your joints are not under one hierarchy.\n')
        else:
            scene_mark += 2

        # make sure root joint isn't parented to anything
        for j in root:
            if cmds.listRelatives(j, p=True):
                cmds.scrollField(output_scroll_field, e=True, ip=0, it='Joints should not be parented to anything other than joints.\n')
            else:
                scene_mark += 2

        # make sure mark is not above max
        if name_mark >= 25:
            name_mark = 25
        if parenting_mark >= 10:
            parenting_mark = 10
        if orients_mark >= 30:
            orients_mark = 30
        if transforms_mark >= 5:
            transforms_mark = 5
        if placement_mark >= 25:
            placement_mark = 25
        if scene_mark >= 5:
            scene_mark = 5
            
        final_mark = name_mark + parenting_mark + orients_mark + transforms_mark + placement_mark + scene_mark - deductions
       
        if final_mark >= 100:
            cmds.scrollField(output_scroll_field, e=True, ip=0, it='Suggested Grade:\n')
        else:
            cmds.scrollField(output_scroll_field, e=True, ip=0, it='\n\nSuggested Grade:\n')
        cmds.scrollField(output_scroll_field, e=True, ip=0, it='  Naming:  ' + str(int(name_mark)) + '/25\n')
        cmds.scrollField(output_scroll_field, e=True, ip=0, it='  Parenting:  ' + str(int(parenting_mark)) + '/10\n')
        cmds.scrollField(output_scroll_field, e=True, ip=0, it='  Orients:  ' + str(int(orients_mark)) + '/30\n')
        cmds.scrollField(output_scroll_field, e=True, ip=0, it='  Transforms:  ' + str(int(transforms_mark)) + '/5\n')
        cmds.scrollField(output_scroll_field, e=True, ip=0, it='  Placement:  ' + str(int(placement_mark)) + '/25\n')
        cmds.scrollField(output_scroll_field, e=True, ip=0, it='  Scene:  ' + str(int(scene_mark)) + '/5\n')
        cmds.scrollField(output_scroll_field, e=True, ip=0, it='  Deductions:  ' + str(int(deductions)) + '\n')

        if final_mark >= 100:
            cmds.scrollField(output_scroll_field, e=True, ip=0, it='\n          Total: 100%\n\nCongratulations!\nYour skeleton is looking good so far!\nNote: This is not necessarily your final grade.')
        else:
            cmds.scrollField(output_scroll_field, e=True, ip=0, it='\n          Total:  ' + str(round(final_mark,2)) + '%\n\nSee the list above for issues. \nNote: This is not necessarily your final grade.')

        cmds.scrollField(output_scroll_field, e=True, ip=1, it='') # Bring Back to the Top


#Build GUI
if __name__ == '__main__':
    build_gui_gt_r1_skeleton_check()