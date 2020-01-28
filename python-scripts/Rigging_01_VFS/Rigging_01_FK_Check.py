#FK Assignment Checker v1.1
import maya.cmds as cmds
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

checkPos = {'headEndJnt' : [0.0,149.233143069,0.668539302549], \
'headJnt' : [0.0,120.015257626,-0.639659610777], \
'jawEndJnt' : [0.0,116.236452934,13.6109303846], \
'jawJnt' : [0.0,126.167495596,0.348183087647], \
'left_ankleJnt' : [7.0123406744,4.86555330952,-2.79820729391], \
'left_ballJnt' : [7.0123406744,1.02850939838,4.53731783033], \
'left_clavicleJnt' : [1.99819553729,106.182093768,4.33649659673], \
'left_elbowJnt' : [22.4758134645,89.4607372056,-3.50156067348], \
'left_eyeJnt' : [6.43210369349,129.206703186,8.14929789305], \
'left_forearmJnt' : [29.0251,79.0077,-1.57048], \
'left_hipJnt' : [7.0123406744,67.9592303246,-1.51017675398], \
'left_index1Jnt' : [36.9358118715,65.9390942712,2.79654683133], \
'left_index2Jnt' : [38.2771633644,63.2194228843,3.71898456919], \
'left_index3Jnt' : [38.661564528,61.5304646092,4.12551802376], \
'left_indexEndJnt' : [38.7522360987,60.0286719031,4.47728607869], \
'left_kneeJnt' : [7.0123406744,36.8033011581,0.0795756394473], \
'left_middle1Jnt' : [37.9307463496,65.8299701415,1.54959082013], \
'left_middle2Jnt' : [38.7690353438,62.681506381,2.27610790846], \
'left_middle3Jnt' : [39.0054656954,60.6694057821,2.68708099936], \
'left_middleEndJnt' : [38.9414521895,59.1075947384,2.95970994586], \
'left_pinky1Jnt' : [37.3551393862,65.5599821692,-1.25996026201], \
'left_pinky2Jnt' : [37.9827198168,62.814317734,-1.00771080677], \
'left_pinky3Jnt' : [37.9362171314,61.4300044519,-0.889283355574], \
'left_pinkyEndJnt' : [37.8184834472,60.3680630906,-0.802542448691], \
'left_ring1Jnt' : [37.6885763314,65.68324954,0.0229446386359], \
'left_ring2Jnt' : [38.4179729513,62.4753505534,0.589287495165], \
'left_ring3Jnt' : [38.5253316541,60.632464935,0.873300648774], \
'left_ringEndJnt' : [38.4986920063,59.1844513526,1.07851490242], \
'left_shoulderJnt' : [11.0031830733,105.341662531,0.477419333912], \
'left_thumb1Jnt' : [33.9591622097,68.9890666496,1.61462823792], \
'left_thumb2Jnt' : [34.0388565884,67.3726171241,2.89815868748], \
'left_thumb3Jnt' : [34.1500088529,65.4871552069,4.38099207377], \
'left_thumbEndJnt' : [33.8280998265,64.247060114,6.548938852], \
'left_toeEndJnt' : [7.0123406744,0.577092467654,9.954320999], \
'left_wristJnt' : [34.6260131345,70.0683962704,0.0809636915612], \
'neck1Jnt' : [0.0,110.16000818,0.492043674797], \
'neck2Jnt' : [0.0,115.006130224,0.297299471595], \
'right_ankleJnt' : [-7.01234,4.86555,-2.79821], \
'right_ballJnt' : [-7.01234,1.02851,4.53732], \
'right_clavicleJnt' : [-1.9982,106.182,4.3365], \
'right_elbowJnt' : [-22.4758,89.4607,-3.50156], \
'right_eyeJnt' : [-6.4321,129.207,8.1493], \
'right_forearmJnt' : [-29.0251,79.0077,-1.57048], \
'right_hipJnt' : [-7.01234,67.9592,-1.51018], \
'right_index1Jnt' : [-36.9358,65.9391,2.79655], \
'right_index2Jnt' : [-38.2772,63.2194,3.71898], \
'right_index3Jnt' : [-38.6616,61.5305,4.12552], \
'right_indexEndJnt' : [-38.7522,60.0287,4.47729], \
'right_kneeJnt' : [-7.01234,36.8033,0.0795756], \
'right_middle1Jnt' : [-37.9307,65.83,1.54959], \
'right_middle2Jnt' : [-38.769,62.6815,2.27611], \
'right_middle3Jnt' : [-39.0055,60.6694,2.68708], \
'right_middleEndJnt' : [-38.9415,59.1076,2.95971], \
'right_pinky1Jnt' : [-37.3551,65.56,-1.25996], \
'right_pinky2Jnt' : [-37.9827,62.8143,-1.00771], \
'right_pinky3Jnt' : [-37.9362,61.43,-0.889283], \
'right_pinkyEndJnt' : [-37.8185,60.3681,-0.802542], \
'right_ring1Jnt' : [-37.6886,65.6832,0.0229446], \
'right_ring2Jnt' : [-38.418,62.4754,0.589287], \
'right_ring3Jnt' : [-38.5253,60.6325,0.873301], \
'right_ringEndJnt' : [-38.4987,59.1845,1.07851], \
'right_shoulderJnt' : [-11.0032,105.342,0.477419], \
'right_thumb1Jnt' : [-33.9592,68.9891,1.61463], \
'right_thumb2Jnt' : [-34.0389,67.3726,2.89816], \
'right_thumb3Jnt' : [-34.15,65.4872,4.38099], \
'right_thumbEndJnt' : [-33.8281,64.2471,6.54894], \
'right_toeEndJnt' : [-7.01234,0.577092,9.95432], \
'right_wristJnt' : [-34.626,70.0684,0.0809637], \
'rootJnt' : [0.0,69.5529866698,-0.765198021547], \
'spine1Jnt' : [0.0,77.2626710745,2.34698601378], \
'spine2Jnt' : [0.0,85.6171219688,4.20944831972], \
'spine3Jnt' : [0.0,94.7258648069,4.39788862078], \
'spine4Jnt' : [0.0,101.530770628,2.80260454951]}

joint_names = ['rootJnt', 'spine1Jnt', 'spine2Jnt', 'spine3Jnt', 'spine4Jnt', \
'neck1Jnt', 'neck2Jnt', 'headJnt', 'headEndJnt', 'jawJnt', 'jawEndJnt', \
'left_eyeJnt', 'right_eyeJnt', 'left_clavicleJnt', 'left_shoulderJnt', \
'left_elbowJnt', 'left_wristJnt', 'left_thumb1Jnt', \
'left_thumb2Jnt', 'left_thumb3Jnt', 'left_thumbEndJnt', 'left_index1Jnt', \
'left_index2Jnt', 'left_index3Jnt', 'left_indexEndJnt', 'left_middle1Jnt', \
'left_middle2Jnt', 'left_middle3Jnt', 'left_middleEndJnt', 'left_ring1Jnt', \
'left_ring2Jnt', 'left_ring3Jnt', 'left_ringEndJnt', 'left_pinky1Jnt', \
'left_pinky2Jnt', 'left_pinky3Jnt', 'left_pinkyEndJnt', 'right_clavicleJnt', \
'right_shoulderJnt', 'right_elbowJnt', 'right_wristJnt', \
'right_thumb1Jnt', 'right_thumb2Jnt', 'right_thumb3Jnt', 'right_thumbEndJnt', \
'right_index1Jnt', 'right_index2Jnt', 'right_index3Jnt', 'right_indexEndJnt', \
'right_middle1Jnt', 'right_middle2Jnt', 'right_middle3Jnt', 'right_middleEndJnt', \
'right_ring1Jnt', 'right_ring2Jnt', 'right_ring3Jnt', 'right_ringEndJnt', \
'right_pinky1Jnt', 'right_pinky2Jnt', 'right_pinky3Jnt', 'right_pinkyEndJnt']

leg_joint_names = ['left_hipJnt', 'left_kneeJnt', 'left_ankleJnt', 'left_ballJnt', 'left_toeEndJnt', \
'right_hipJnt', 'right_kneeJnt', 'right_ankleJnt', 'right_ballJnt', 'right_toeEndJnt']

#check control names
#neck1Jnt ===> neck1Ctrl
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
print 'vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv'
print 'vvvvvvvvvvvvvvvvvvvvvvvvvvvvv FK Rig Issues vvvvvvvvvvvvvvvvvvvvvvvvvvvvvv'
print 'vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv\n'

#check file type
fileType = cmds.file(query = True, type=1)
if fileType[0] == 'mayaAscii':
    scene_mark += 5
else:
    cmds.warning('Your file must be saved as a ".ma"')


for j in joint_names:
    if not cmds.objExists(j):
        cmds.error('Your skeleton is missing "' + j + '". You must fix your skeleton before continuing.')
        deductions -= 3
    else:
        base = j[:-3]
        ctrl = (base + 'Ctrl')
        control_node_names.append(ctrl)
        if cmds.objExists(ctrl):
            ctrls_mark += 1
            trn = cmds.getAttr(ctrl + '.translate')
            rot = cmds.getAttr(ctrl + '.rotate')
            scl = cmds.getAttr(ctrl + '.scale')
            if cmds.getAttr(ctrl + '.translate') != [(0,0,0)] and cmds.getAttr(ctrl + '.rotate') != [(0,0,0)] and  cmds.getAttr(ctrl + '.scale') != [(1,1,1)]:
                cmds.warning('"' + ctrl + ' does not have zeroed default transform values.')
            else:
                ctrl_transforms_mark += 1
            
            #check for group
            if cmds.listRelatives(ctrl, parent = True, type = 'transform'):
                parent = cmds.listRelatives(ctrl, parent = True, type = 'transform')
                if parent[0] == (ctrl + "Grp"):
                    control_node_names.append(ctrl + "Grp")
                    ctrl_grps_mark += 1
                    
                    # check that group is parented to the right control
                    # get name of parent joint
                    if cmds.listRelatives(j, parent = True, type = 'joint'):
                        parentJnt = cmds.listRelatives(j, parent = True, type = 'joint')
                        parentCtrlName = parentJnt[0][:-3] + 'Ctrl'
                        
                        #check group is parented to the higher control
                        if cmds.listRelatives((ctrl + "Grp"), parent = True, type = 'transform'):
                            ctrl_grps_mark += 0.5
                            parentNode = cmds.listRelatives((ctrl + "Grp"), parent = True, type = 'transform')
                            if parentNode[0] == parentCtrlName:
                                ctrl_grps_mark += 0.5
                            else:
                                cmds.warning('The parent of "' + ctrl + 'Grp" should be ' + parentCtrlName + '", not "' + parentNode[0] + '".')
                        else:
                            cmds.warning('"' + ctrl + 'Grp" should be parented to "' + parentCtrlName + '".')
                    elif j != 'rootJnt':
                        cmds.warning('"' + j + '" should be a part of your main skeleton hierarchy')

                    #check to make sure group matches posotion and orientation of joint
                    jointTrn = cmds.xform(j, q = True, ws = True, t = True)
                    jointRot = cmds.xform(j, q = True, ws = True, ro = True)
                    ctrlGrpTrn = cmds.xform((ctrl + "Grp"), q = True, ws = True, t = True)
                    ctrlGrpRot = cmds.xform((ctrl + "Grp"), q = True, ws = True, ro = True)
                    if round(jointTrn[0],3) == round(ctrlGrpTrn[0],3) and round(jointTrn[1],3) == round(ctrlGrpTrn[1],3) and round(jointTrn[2],3) == round(ctrlGrpTrn[2],3):
                        ctrl_grps_placement_mark += 1
                    else:
                        #print ctrlGrpTrn, jointTrn
                        cmds.warning('"' + ctrl + 'Grp" does not match the position of "' + j + '".')
                        
                            
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
                            cmds.warning('"' + ctrl + 'Grp" does not match the orientation of "' + j + '".')
                else:
                    cmds.warning('The parent of "' + ctrl + '" should be "' + ctrl + 'Grp", not "' + parent[0] + '".')
            else:
                cmds.warning('"' + ctrl + '" should be parented to "' + ctrl + 'Grp".')
                #deductions -= 3
        elif cmds.listRelatives(j, children = True, type = 'joint'):
            cmds.warning('"' + ctrl + '" does not exist.')
            #deductions -= 5
            

        #check constraints
        
        #skip end joints
        if cmds.listRelatives(j, c= True, type = 'joint'):
            transforms = ['.tx', '.ty', '.tz', '.rx', '.ry', '.rz', '.sx', '.sy', '.sz']
            connections = []
            for x in transforms:
                connection = cmds.listConnections((j + x),s = True, d = False)
                if connection and connection not in connections:
                    connections = connections + connection
            
            #check connection type and len
            connections = list(set(connections))
            if len(connections) == 0:
                cmds.warning('"' + j +'" is not constrained.')
            elif len(connections) > 1:
                cmds.warning('"' + j +'" should only have one constraint affecting the channels.')
            elif 'Constraint' in connections[0]:
                #check that there is only one weight, and that it is correct
                targets = cmds.listConnections(connections[0] + '.target', s = 1, d = 0)
                for tgt in targets:
                    if tgt == connections[0]:
                        targets.remove(tgt)
                        targets = list(set(targets))
                
                if len(targets) == 1:
                    if targets[0] == ctrl:
                        constraints_mark += 1
                    else:
                        cmds.warning('"' + j + '" should be constrained to "' + ctrl + '".')
                else:
                    cmds.warning('"' + j + '" should only be constrained to "' + ctrl + '". You need to delete the constraint and make a new one.')
        

#check that there are no extra transforms in the scene
all_nodes = geo_names + joint_names + leg_joint_names + control_node_names + extra_geo_names


transforms = cmds.ls(type = 'transform')
for t in transforms:
    if t not in all_nodes:
        if "Constraint" not in t:
            if cmds.listRelatives(t, c = True):
                children = cmds.listRelatives(t, c = True)
                if cmds.nodeType(children[0]) != 'camera':
                    cmds.warning('"' + t + '" is either improperly named or should not be in the scene.')
                    deductions -= 2                    
            else:
                cmds.warning('"' + t + '" is either improperly named or should not be in the scene.')
                deductions -= 2


ctrls_mark = round(((ctrls_mark/47)*20), 2)
ctrl_transforms_mark = round(((ctrl_transforms_mark/47)*15), 2)
ctrl_grps_mark = round(((ctrl_grps_mark/93)*20), 2)
ctrl_grps_placement_mark = round(((ctrl_grps_placement_mark/94)*15), 2)
constraints_mark = round(((constraints_mark/47)*25), 2)
deductions = deductions

print 'scene_mark =', scene_mark, '/5'
print 'ctrls_mark =', ctrls_mark , '/20'
print 'ctrl_transforms_mark =', ctrl_transforms_mark, '/15'
print 'ctrl_grps_mark =', ctrl_grps_mark, '/20'
print 'ctrl_grps_placement_mark =', ctrl_grps_placement_mark, '/15'
print 'constraints_mark =', constraints_mark, '/25'
print 'deductions:',deductions

final_mark = round((scene_mark + ctrls_mark + ctrl_transforms_mark + ctrl_grps_mark + ctrl_grps_placement_mark + constraints_mark + deductions), 2)
if final_mark < 0:
    final_mark = 0
if final_mark == 100:
    print '                          >     No Issues     <'
    cmds.confirmDialog(title = 'Great! 100%', icon = 'information', message = 'Congratulations! Your rig is looking good so far!\n\nNote: This is not necessarily a final grade.')
else:
    print '\n^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^'
    print '^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ FK Rig Issues ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^'
    print '^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^'
    cmds.warning('Your score so far is ' + str(final_mark) + '%. See script editor for a list of issues.')
    cmds.confirmDialog(title = ('Score: ' + str(final_mark)), icon = 'warning', message = ('Your score so far is ' + str(final_mark) + '%. See script editor for a list of issues.\n\nNote: This is not necessarily a final grade.'))
