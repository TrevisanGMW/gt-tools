"""

 Rigging 1 - Betty FK Check - v1.1
 This script checks for issues in the FK setp (Ctrls - Lesson 3) for the character "Betty" in Rigging 1 - VFS
 Part of the code used for this script was repourposed from a previous script found in the course material folder (2019)
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-03-01 - github.com/TrevisanGMW

 1.1 
 Changed part fo the previously created code to match new version of Betty.
 Removed duplicated joint for wrist (to simplify it)
 Created GUI
 Added output textbox (so students don't need to use script editor at this point)
 Changed the names of all joints to match a new pattern - "side_description_jnt" (lowercase jnt)
 
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
script_name = 'Rigging 1 - FK Checker'

# Version
script_version = '1.1'


def build_gui_gt_r1_fk_check():
    
    window_name = "build_gui_gt_r1_fk_check"
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
    cmds.text(l='This script performs a series of checks to detect common issues that are often\naccidently ignored when creating FK ctrls for the first time. (Part of Assign. 3)', align="left")
    cmds.text(l='', align="left")
    cmds.text(l='Make sure you run this script before starting Lesson 4.', align="center")
    cmds.text(l='\nCurrent Character: "' + character_name + '"    -   Assignment: "Rigging 1.3"', align="center")
 
    
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
            check_fk_ctrls()
        except Exception as exception:
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=str(exception) + '\n')
    
    
    def check_fk_ctrls():
        
        # Clean Output Window
        cmds.scrollField(output_scroll_field, e=True, clear=True)
        
        mark = 100
        deductions = 0
        scene_mark = 0.0
        ctrls_mark = 0.0
        ctrl_transforms_mark = 0.0
        ctrl_grps_mark = 0.0
        ctrl_grps_placement_mark = 0.0
        constraints_mark = 0.0
        root = []
        marks = {'name_mark' : 25,'parenting_mark' : 10,'orients_mark' : 30, \
                 'transforms_mark' : 5,'placement_mark' : 25,'scene_mark' : 5}


        joint_names = ['root_jnt', 'spine1_jnt', 'spine2_jnt', 'spine3_jnt', 'spine4_jnt', \
                       'neck1_jnt', 'neck2_jnt', 'head_jnt', 'head_endJnt', 'jaw_jnt', 'jaw_endJnt', \
                       'left_eye_jnt', 'right_eye_jnt', 'left_clavicle_jnt', 'left_shoulder_jnt', \
                       'left_elbow_jnt', 'left_wrist_jnt', 'left_thumb1_jnt', \
                       'left_thumb2_jnt', 'left_thumb3_jnt', 'left_thumb_endJnt', 'left_index1_jnt', \
                       'left_index2_jnt', 'left_index3_jnt', 'left_index_endJnt', 'left_middle1_jnt', \
                       'left_middle2_jnt', 'left_middle3_jnt', 'left_middle_endJnt', 'left_ring1_jnt', \
                       'left_ring2_jnt', 'left_ring3_jnt', 'left_ring_endJnt', 'left_pinky1_jnt', \
                       'left_pinky2_jnt', 'left_pinky3_jnt', 'left_pinky_endJnt', 'right_clavicle_jnt', \
                       'right_shoulder_jnt', 'right_elbow_jnt', 'right_wrist_jnt', \
                       'right_thumb1_jnt', 'right_thumb2_jnt', 'right_thumb3_jnt', 'right_thumb_endJnt', \
                       'right_index1_jnt', 'right_index2_jnt', 'right_index3_jnt', 'right_index_endJnt', \
                       'right_middle1_jnt', 'right_middle2_jnt', 'right_middle3_jnt', 'right_middle_endJnt', \
                       'right_ring1_jnt', 'right_ring2_jnt', 'right_ring3_jnt', 'right_ring_endJnt', \
                       'right_pinky1_jnt', 'right_pinky2_jnt', 'right_pinky3_jnt', 'right_pinky_endJnt']

        leg_joint_names = ['left_hip_jnt', 'left_knee_jnt', 'left_ankle_jnt', 'left_ball_jnt', 'left_toe_endJnt', \
                           'right_hip_jnt', 'right_knee_jnt', 'right_ankle_jnt', 'right_ball_jnt', 'right_toe_endJnt']

        # Check control names
        # neck1_jnt ===> neck1_ctrl
        geo_names = ['body_geo', 'hair_geo', 'left_outerEyeTissue_geo', 'left_innerEyeTissue_geo', \
                     'left_eye_geo', 'left_pupil_geo', 'left_brow_geo', 'left_upperLash_geo', \
                     'left_lowerLash_geo', 'right_outerEyeTissue_geo', 'right_innerEyeTissue_geo', \
                     'right_eye_geo', 'right_pupil_geo', 'right_brow_geo', 'right_upperLash_geo', \
                     'right_lowerLash_geo', 'upperTeeth_geo', 'lowerTeeth_geo', 'tongue_geo']

        extra_geo_names = ['rootProxy_geo', 'spine1Proxy_geo', 'spine2Proxy_geo', 'spine3Proxy_geo', 'spine4Proxy_geo', 'neck1Proxy_geo', \
                           'neck2Proxy_geo', 'headProxy_geo', 'jawProxy_geo', 'left_clavicleProxy_geo', 'left_shoulderProxy_geo', 'left_elbowProxy_geo', 'left_wristProxy_geo', \
                           'left_thumb1Proxy_geo', 'left_thumb2Proxy_geo', 'left_thumb3Proxy_geo', 'left_index1Proxy_geo', 'left_index2Proxy_geo', 'left_index3Proxy_geo', \
                           'left_middle1Proxy_geo', 'left_middle2Proxy_geo', 'left_middle3Proxy_geo', 'left_ring1Proxy_geo', 'left_ring2Proxy_geo', 'left_ring3Proxy_geo', \
                           'left_pinky1Proxy_geo', 'left_pinky2Proxy_geo', 'left_pinky3Proxy_geo', 'left_hipProxy_geo', 'left_kneeProxy_geo', 'left_ankleProxy_geo', \
                           'left_ballProxy_geo', 'right_ballProxy_geo', 'right_ankleProxy_geo', 'right_kneeProxy_geo', 'right_hipProxy_geo', 'right_pinky3Proxy_geo', \
                           'right_pinky2Proxy_geo', 'right_pinky1Proxy_geo', 'right_ring3Proxy_geo', 'right_ring2Proxy_geo', 'right_ring1Proxy_geo', 'right_middle3Proxy_geo', \
                           'right_middle2Proxy_geo', 'right_middle1Proxy_geo', 'right_index3Proxy_geo', 'right_index2Proxy_geo', 'right_index1Proxy_geo', 'right_thumb3Proxy_geo', \
                           'right_thumb2Proxy_geo', 'right_thumb1Proxy_geo', 'right_wristProxy_geo', 'right_elbowProxy_geo', 'right_shoulderProxy_geo', 'right_clavicleProxy_geo', \
                           'left_eyeProxy_geo', 'right_eyeProxy_geo', 'proxy_geo_grp', 'Betty', 'geo_grp', 'skeleton', 'skeleton_grp', 'controls_grp', 'controls']

        control_node_names = []
        issues = ''


        # Check file type
        fileType = cmds.file(query = True, type=1)
        if fileType[0] == 'mayaAscii':
            scene_mark += 5
        else:
            issues +='Your file must be saved as a ".ma"\n'

        
        missing_basic_elements = False
        for j in joint_names:
            if not cmds.objExists(j):
                cmds.scrollField(output_scroll_field, e=True, ip=0, it='Your skeleton is missing "' + j + '".\n')
                missing_basic_elements = True
                deductions -= 3
            else:
                base = j[:-3]
                ctrl = (base + 'ctrl')
                control_node_names.append(ctrl)
                if cmds.objExists(ctrl):
                    ctrls_mark += 1
                    trn = cmds.getAttr(ctrl + '.translate')
                    rot = cmds.getAttr(ctrl + '.rotate')
                    scl = cmds.getAttr(ctrl + '.scale')
                    if cmds.getAttr(ctrl + '.translate') != [(0,0,0)] and cmds.getAttr(ctrl + '.rotate') != [(0,0,0)] and  cmds.getAttr(ctrl + '.scale') != [(1,1,1)]:
                        cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + ctrl + ' does not have zeroed default transform values.\n')
                    else:
                        ctrl_transforms_mark += 1
                    
                    # Check for group
                    if cmds.listRelatives(ctrl, parent = True, type = 'transform'):
                        parent = cmds.listRelatives(ctrl, parent = True, type = 'transform')
                        if parent[0] == (ctrl + "Grp"):
                            control_node_names.append(ctrl + "Grp")
                            ctrl_grps_mark += 1
                            
                            # Check that group is parented to the right control
                            # Get name of parent joint
                            if cmds.listRelatives(j, parent = True, type = 'joint'):
                                parentJnt = cmds.listRelatives(j, parent = True, type = 'joint')
                                parentCtrlName = parentJnt[0][:-3] + 'ctrl'
                                
                                # Check group is parented to the higher control
                                if cmds.listRelatives((ctrl + "Grp"), parent = True, type = 'transform'):
                                    ctrl_grps_mark += 0.5
                                    parentNode = cmds.listRelatives((ctrl + "Grp"), parent = True, type = 'transform')
                                    if parentNode[0] == parentCtrlName:
                                        ctrl_grps_mark += 0.5
                                    else:
                                        cmds.scrollField(output_scroll_field, e=True, ip=0, it='The parent of "' + ctrl + 'Grp" should be ' + parentCtrlName + '", not "' + parentNode[0] + '".\n')
                                        
                                else:
                                    cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + ctrl + 'Grp" should be parented to "' + parentCtrlName + '".\n')
                            elif j != 'root_jnt':
                                cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + j + '" should be a part of your main skeleton hierarchy.\n')

                            # Check to make sure group matches position and orientation of joint
                            jointTrn = cmds.xform(j, q = True, ws = True, t = True)
                            jointRot = cmds.xform(j, q = True, ws = True, ro = True)
                            ctrlGrpTrn = cmds.xform((ctrl + "Grp"), q = True, ws = True, t = True)
                            ctrlGrpRot = cmds.xform((ctrl + "Grp"), q = True, ws = True, ro = True)
                            if round(jointTrn[0],3) == round(ctrlGrpTrn[0],3) and round(jointTrn[1],3) == round(ctrlGrpTrn[1],3) and round(jointTrn[2],3) == round(ctrlGrpTrn[2],3):
                                ctrl_grps_placement_mark += 1
                            else:
                                cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + ctrl + 'Grp" does not match the position of "' + j + '".\n')
                                
                                    
                            if round(jointRot[0],3) == round(ctrlGrpRot[0],3) and round(jointRot[1],3) == round(ctrlGrpRot[1],3) and round(jointRot[2],3) == round(ctrlGrpRot[2],3):
                                ctrl_grps_placement_mark += 1
                            else:
                                locator = cmds.spaceLocator(name = (ctrl + "GrpLctr"))
                                cmds.delete(cmds.parentConstraint(j, locator[0]))
                                if cmds.listRelatives((ctrl + "Grp"), parent = True, type = 'transform'):
                                    parentNode2 = cmds.listRelatives((ctrl + "Grp"), parent = True, type = 'transform')
                                    cmds.parent(locator[0], parentNode2[0])
                                
                                newRot = cmds.xform(locator, q = True, ws = True, ro = True)
                                cmds.delete(locator)
                                    
                                if round(newRot[0],3) == round(ctrlGrpRot[0],3) and round(newRot[1],3) == round(ctrlGrpRot[1],3) and round(newRot[2],3) == round(ctrlGrpRot[2],3):
                                    ctrl_grps_placement_mark += 1
                                        
                                else:
                                    cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + ctrl + 'Grp" does not match the orientation of "' + j + '".\n')
                        else:
                            cmds.scrollField(output_scroll_field, e=True, ip=0, it='The parent of "' + ctrl + '" should be "' + ctrl + 'Grp", not "' + parent[0] + '".\n')
                    else:
                        cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + ctrl + '" should be parented to "' + ctrl + 'Grp".\n')
                elif cmds.listRelatives(j, children = True, type = 'joint'):
                    cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + ctrl + '" does not exist.\n')
                    

                # Check constraints
                
                # Skip end joints
                if cmds.listRelatives(j, c= True, type = 'joint'):
                    transforms = ['.tx', '.ty', '.tz', '.rx', '.ry', '.rz', '.sx', '.sy', '.sz']
                    connections = []
                    for x in transforms:
                        connection = cmds.listConnections((j + x),s = True, d = False)
                        if connection and connection not in connections:
                            connections = connections + connection
                    
                    # Check connection type and len
                    connections = list(set(connections))
                    if len(connections) == 0:
                        cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + j +'" is not constrained.\n')
                    elif len(connections) > 1:
                        cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + j +'" should only have one constraint affecting the channels.\n')
                    elif 'Constraint' in connections[0]:
                        # Check that there is only one weight, and that it is correct
                        targets = cmds.listConnections(connections[0] + '.target', s = 1, d = 0)
                        for tgt in targets:
                            if tgt == connections[0]:
                                targets.remove(tgt)
                                targets = list(set(targets))
                        
                        if len(targets) == 1:
                            if targets[0] == ctrl:
                                constraints_mark += 1
                            else:
                                cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + j + '" should be constrained to "' + ctrl + '".\n')
                        else:
                            cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + j + '" should only be constrained to "' + ctrl + '". You need to delete the constraint and make a new one.\n')
                
        if missing_basic_elements:
            cmds.scrollField(output_scroll_field, e=True, ip=0, it='You must fix your skeleton before continuing.\n\n')
        if issues != '':
            cmds.scrollField(output_scroll_field, e=True, ip=0, it=issues)
            
            
        # Check that there are no extra transforms in the scene
        all_nodes = geo_names + joint_names + leg_joint_names + control_node_names + extra_geo_names


        transforms = cmds.ls(type = 'transform')
        for t in transforms:
            if t not in all_nodes:
                if "Constraint" not in t:
                    if cmds.listRelatives(t, c = True):
                        children = cmds.listRelatives(t, c = True)
                        if cmds.nodeType(children[0]) != 'camera':
                            cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + t + '" is either improperly named or should not be in the scene.\n')
                            deductions -= 2                    
                    else:
                        cmds.scrollField(output_scroll_field, e=True, ip=0, it='"' + t + '" is either improperly named or should not be in the scene.\n')
                        deductions -= 2


        ctrls_mark = round(((ctrls_mark/47)*20), 2)
        ctrl_transforms_mark = round(((ctrl_transforms_mark/47)*15), 2)
        ctrl_grps_mark = round(((ctrl_grps_mark/93)*20), 2)
        ctrl_grps_placement_mark = round(((ctrl_grps_placement_mark/94)*15), 2)
        constraints_mark = round(((constraints_mark/47)*25), 2)
        deductions = deductions
        
        final_mark = round((scene_mark + ctrls_mark + ctrl_transforms_mark + ctrl_grps_mark + ctrl_grps_placement_mark + constraints_mark + deductions), 2)
        
        if ctrls_mark >= 20:
            ctrls_mark = 20
        if ctrl_transforms_mark >= 15:
            ctrl_transforms_mark = 15
        if ctrl_grps_mark >= 20:
            ctrl_grps_mark = 20
        if ctrl_grps_placement_mark >= 15:
            ctrl_grps_placement_mark = 15
        if constraints_mark >= 25:
            constraints_mark = 25
        if scene_mark >= 5:
            scene_mark = 5
            
        if final_mark >= 100:
            cmds.scrollField(output_scroll_field, e=True, ip=0, it='Suggested Grade:\n')
        else:
            cmds.scrollField(output_scroll_field, e=True, ip=0, it='\n\nSuggested Grade:\n')
            cmds.scrollField(output_scroll_field, e=True, ip=0, it='  Ctrls:  ' + str(int(ctrls_mark)) + '/20\n')
            cmds.scrollField(output_scroll_field, e=True, ip=0, it='  Ctrl Transforms:  ' + str(int(ctrl_transforms_mark)) + '/15\n')
            cmds.scrollField(output_scroll_field, e=True, ip=0, it='  Ctrl Grps:  ' + str(int(ctrl_grps_mark)) + '/20\n')
            cmds.scrollField(output_scroll_field, e=True, ip=0, it='  Ctrl Grps Placement:  ' + str(int(ctrl_grps_placement_mark)) + '/15\n')
            cmds.scrollField(output_scroll_field, e=True, ip=0, it='  Constraints:  ' + str(int(constraints_mark)) + '/25\n')
            cmds.scrollField(output_scroll_field, e=True, ip=0, it='  Scene:  ' + str(int(scene_mark)) + '/5\n')
            cmds.scrollField(output_scroll_field, e=True, ip=0, it='  Deductions:  ' + str(int(deductions)) + '\n')

      
        
        if final_mark >= 100:
            cmds.scrollField(output_scroll_field, e=True, ip=0, it='\n          Total: 100%\n\nCongratulations!\nYour FK rig is looking good so far!\nNote: This is not necessarily your final grade.')
        else:
            cmds.scrollField(output_scroll_field, e=True, ip=0, it='\n          Total:  ' + str(round(final_mark,2)) + '%\n\nSee the list above for issues. \nNote: This is not necessarily your final grade.')

        cmds.scrollField(output_scroll_field, e=True, ip=1, it='') # Bring Back to the Top
        
    # First Refresh
    reroute_errors()


#Build GUI
if __name__ == '__main__':
    build_gui_gt_r1_fk_check()