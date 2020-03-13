# Assignment 1 - Rig Skeleton Check - v01.1
import maya.cmds as cmds


def main():
    mark = 0
    root = []
    # name_mark = 25
    # parenting_mark = 10
    # orients_mark = 30
    # transforms_mark = 5
    # placement_mark = 25
    # scene_mark = 5

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
    
    checkPos = {'headEndJnt': [0.0, 149.627, 0.668539302549], \
                'headJnt': [0.0, 120.015257626, -0.639659610777], \
                'jawEndJnt': [0.0, 116.236452934, 13.6109303846], \
                'jawJnt': [0.0, 126.167495596, 0.348183087647], \
                'left_ankleJnt': [7.0123406744, 4.86555330952, -2.79820729391], \
                'left_ballJnt': [6.958, 0.056, 3.4], \
                'left_clavicleJnt': [1.99819553729, 106.182093768, 4.33649659673], \
                'left_elbowJnt': [22.068, 89.436, -4.228], \
                'left_eyeJnt': [6.43210369349, 129.206703186, 8.14929789305], \
                'left_hipJnt': [7.0123406744, 67.9592303246, -1.51017675398], \
                'left_index1Jnt': [36.9358118715, 65.9390942712, 2.79654683133], \
                'left_index2Jnt': [38.2771633644, 63.2194228843, 3.71898456919], \
                'left_index3Jnt': [38.661564528, 61.5304646092, 4.12551802376], \
                'left_indexEndJnt': [38.7522360987, 60.0286719031, 4.47728607869], \
                'left_kneeJnt': [7.0123406744, 36.8033011581, 0.0795756394473], \
                'left_middle1Jnt': [37.9307463496, 65.8299701415, 1.54959082013], \
                'left_middle2Jnt': [38.7690353438, 62.681506381, 2.27610790846], \
                'left_middle3Jnt': [39.0054656954, 60.6694057821, 2.68708099936], \
                'left_middleEndJnt': [38.9414521895, 59.1075947384, 2.95970994586], \
                'left_pinky1Jnt': [37.3551393862, 65.5599821692, -1.25996026201], \
                'left_pinky2Jnt': [37.9827198168, 62.814317734, -1.00771080677], \
                'left_pinky3Jnt': [37.9362171314, 61.4300044519, -0.889283355574], \
                'left_pinkyEndJnt': [37.8184834472, 60.3680630906, -0.802542448691], \
                'left_ring1Jnt': [37.6885763314, 65.68324954, 0.0229446386359], \
                'left_ring2Jnt': [38.4179729513, 62.4753505534, 0.589287495165], \
                'left_ring3Jnt': [38.5253316541, 60.632464935, 0.873300648774], \
                'left_ringEndJnt': [38.4986920063, 59.1844513526, 1.07851490242], \
                'left_shoulderJnt': [11.0031830733, 105.341662531, 0.477419333912], \
                'left_thumb1Jnt': [33.9591622097, 68.9890666496, 1.61462823792], \
                'left_thumb2Jnt': [34.0388565884, 67.3726171241, 2.89815868748], \
                'left_thumb3Jnt': [34.1500088529, 65.4871552069, 4.38099207377], \
                'left_thumbEndJnt': [33.8280998265, 64.247060114, 6.548938852], \
                'left_toeEndJnt': [7.0123406744, 0.577092467654, 9.954320999], \
                'left_wristJnt': [34.495, 70.633, -0.164], \
                'neck1Jnt': [0.0, 111.421, 1.214], \
                'neck2Jnt': [0.0, 115.006130224, 0.297299471595], \
                'right_ankleJnt': [-7.01234, 4.86555, -2.79821], \
                'right_ballJnt': [-7.01234, 1.02851, 4.53732], \
                'right_clavicleJnt': [-1.9982, 106.182, 4.3365], \
                'right_elbowJnt': [-22.4758, 89.4607, -3.50156], \
                'right_eyeJnt': [-6.4321, 129.207, 8.1493], \
                'right_hipJnt': [-7.01234, 67.9592, -1.51018], \
                'right_index1Jnt': [-36.9358, 65.9391, 2.79655], \
                'right_index2Jnt': [-38.2772, 63.2194, 3.71898], \
                'right_index3Jnt': [-38.6616, 61.5305, 4.12552], \
                'right_indexEndJnt': [-38.7522, 60.0287, 4.47729], \
                'right_kneeJnt': [-7.01234, 36.8033, 0.0795756], \
                'right_middle1Jnt': [-37.9307, 65.83, 1.54959], \
                'right_middle2Jnt': [-38.769, 62.6815, 2.27611], \
                'right_middle3Jnt': [-39.0055, 60.6694, 2.68708], \
                'right_middleEndJnt': [-38.9415, 59.1076, 2.95971], \
                'right_pinky1Jnt': [-37.3551, 65.56, -1.25996], \
                'right_pinky2Jnt': [-37.9827, 62.8143, -1.00771], \
                'right_pinky3Jnt': [-37.9362, 61.43, -0.889283], \
                'right_pinkyEndJnt': [-37.8185, 60.3681, -0.802542], \
                'right_ring1Jnt': [-37.6886, 65.6832, 0.0229446], \
                'right_ring2Jnt': [-38.418, 62.4754, 0.589287], \
                'right_ring3Jnt': [-38.5253, 60.6325, 0.873301], \
                'right_ringEndJnt': [-38.4987, 59.1845, 1.07851], \
                'right_shoulderJnt': [-11.0032, 105.342, 0.477419], \
                'right_thumb1Jnt': [-33.9592, 68.9891, 1.61463], \
                'right_thumb2Jnt': [-34.0389, 67.3726, 2.89816], \
                'right_thumb3Jnt': [-34.15, 65.4872, 4.38099], \
                'right_thumbEndJnt': [-33.8281, 64.2471, 6.54894], \
                'right_toeEndJnt': [-7.01234, 0.577092, 9.95432], \
                'right_wristJnt': [-34.626, 70.0684, 0.0809637], \
                'rootJnt': [0.0, 69.5529866698, -0.765198021547], \
                'spine1Jnt': [0.0, 77.2626710745, 2.34698601378], \
                'spine2Jnt': [0.0, 85.6171219688, 4.20944831972], \
                'spine3Jnt': [0.0, 89.744, 6.318], \
                'spine4Jnt': [0.0, 95.128, 5.423]}

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
                   'right_pinky1Jnt', 'right_pinky2Jnt', 'right_pinky3Jnt', 'right_pinkyEndJnt', \
                   'left_hipJnt', 'left_kneeJnt', 'left_ankleJnt', 'left_ballJnt', 'left_toeEndJnt', \
                   'right_hipJnt', 'right_kneeJnt', 'right_ankleJnt', 'right_ballJnt', 'right_toeEndJnt']

    joints = cmds.ls(type='joint')
    print 'vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv'
    print 'vvvvvvvvvvvvvvvvvvvvvvvvvvvv Skeleton Issues vvvvvvvvvvvvvvvvvvvvvvvvvvvvv'
    print 'vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv\n'

    # check file type
    fileType = cmds.file(query=True, type=1)
    if fileType[0] != 'mayaAscii':
        cmds.warning('Your file must be saved as a ".ma"')
    else:
        scene_mark += 1

    # check number of joints
    if len(joints) != 71:
        cmds.warning('Your skeleton has ' + str(len(joints)) + '. It should have 71 joints.')
        if len(joints) > 71:
            deductions = (abs(len(joints) - 71) * 5)

    # check to see what joints are missing
    for jnt in joint_names:
        if not cmds.objExists(jnt):
            cmds.warning('Your skeleton does not have a joint named "' + jnt + '".')
            # mark -= (5)

    for jnt in joints:
        # check names
        # name_mark = 25
        if jnt not in joint_names:
            # check name
            cmds.warning('"' + jnt + '" is not a proper name.')
            # name_mark -= 1
        else:
            name_mark += name_mark_division

            # check orientations
            # orients_mark = 30
            parents = []
            orient_deduction = []
            if cmds.listRelatives(jnt, c=True, type='joint') or 'wrist' in jnt:
                # print jnt
                # check to make sure joints are oriented with a value that is consistent witht their parent
                orientCheckJnts = ['spine', 'neck', 'headJnt', 'jawJnt', 'shoulder', 'elbow', \
                                   'wrist', 'thumb', 'index', 'middle', 'ring', 'pinky', 'knee', 'ankle',
                                   'ball']
                if any(j in jnt for j in orientCheckJnts) and 'thumb1' not in jnt:
                    if cmds.listRelatives(jnt, children=True) or 'wrist' in jnt:
                        jointOrients = cmds.getAttr((jnt + '.jointOrient'))
                        # print jnt, jointOrients
                        totalOrient = (abs(jointOrients[0][0]) + abs(jointOrients[0][1]) + abs(jointOrients[0][2]))
                        if (totalOrient) > 150:
                            cmds.warning('"' + jnt + '" or its parent has incorrect joint orients')
                            parent_node = cmds.listRelatives(jnt, parent=True)
                            if parent_node:
                                parents.append(parent_node[0])
                            orient_deduction.append(jnt)
                        elif (totalOrient) > 110 and 'jawJnt' not in jnt:
                            cmds.warning('"' + jnt + '" or its parent has incorrect joint orients')
                            orient_deduction.append(jnt)
                            if cmds.listRelatives(jnt, parent=True):
                                parents.append(cmds.listRelatives(jnt, parent=True))

                        elif (totalOrient) > 90 and 'jawJnt' not in jnt and 'shoulderJnt' not in jnt and 'index' not in jnt and 'middle' not in jnt and 'ring' not in jnt and 'pinky' not in jnt:
                            cmds.warning('"' + jnt + '" or its parent has incorrect joint orients')
                            orient_deduction.append(jnt)
                            if cmds.listRelatives(jnt, parent=True):
                                parents.append(cmds.listRelatives(jnt, parent=True))
                        elif (
                        totalOrient) > 60 and 'ankle' not in jnt and 'jawJnt' not in jnt and 'shoulderJnt' not in jnt and 'index' not in jnt and 'middle' not in jnt and 'ring' not in jnt and 'pinky' not in jnt:
                            cmds.warning('"' + jnt + '" or its parent has incorrect joint orients')
                            orient_deduction.append(jnt)
                            if cmds.listRelatives(jnt, parent=True):
                                parents.append(cmds.listRelatives(jnt, parent=True))
                        elif (totalOrient) > 20 and 'wrist' in jnt:
                            cmds.warning('"' + jnt + '" or its parent has incorrect joint orients')
                            orient_deduction.append(jnt)
                            if cmds.listRelatives(jnt, parent=True):
                                parents.append(cmds.listRelatives(jnt, parent=True))
                        else:
                            orients_mark += orients_mark_division
                # check to make sure joints have not been moved since their parent has oriented to them
                orientCheck2Jnts = ['index2', 'index3', 'indexEndJnt', 'middle2', 'middle3', \
                                    'middleEnd', 'ring2', 'ring3', 'ringEnd', 'pinky2', 'pinky3', 'pinkyEnd', \
                                    'thumb2', 'thumb3', 'thumbEnd', 'elbow', 'shoulder', \
                                    'jawEnd', 'headJnt', 'headEnd', 'neck', 'ball', 'toe', 'ankle', 'knee', 'spine']
                if any(j in jnt for j in orientCheck2Jnts):
                    parentJoint = cmds.listRelatives(jnt, parent=True)
                    if parentJoint and parentJoint[0] not in parents:
                        # print 'check2', jnt
                        if abs(cmds.getAttr(jnt + '.translateY')) > 0.05 or abs(
                                cmds.getAttr(jnt + '.translateZ')) > 0.05:
                            cmds.warning('"' + jnt + '" position is wrong or its parent has incorrect joint orients')
                            # orients_mark -= 5
                        elif jnt not in orient_deduction:
                            orients_mark += orients_mark_division

                orients_mark = orients_mark - (len(orient_deduction) * 2.5)
                if orients_mark < 0:
                    orients_mark = 0

            # check frozen transforms
            # transforms_mark = 5
            rot = cmds.getAttr((jnt + '.rotate'))
            scl = cmds.getAttr((jnt + '.scale'))
            if (0.001 < rot[0][0] > 0.001) or (0.001 < rot[0][1] > 0.001) or (0.001 < rot[0][2] > 0.001):
                cmds.warning('"' + jnt + '" has non-frozen rotations.')
                # transforms_mark -= 2
            elif (scl[0][0] != 1) or (scl[0][1] != 1) or (scl[0][2] != 1):
                cmds.warning('"' + jnt + '" has non-frozen scales.')
                # transforms_mark -= 2
            else:
                transforms_mark += transforms_mark_division

            # check positions
            # placement_mark = 25
            targetPos = (checkPos.get(jnt))
            pos = cmds.xform(jnt, q=True, rp=True, ws=True)
            val = [a - b for a, b in zip(targetPos, pos)]
            valTotal = abs(val[0]) + abs(val[1]) + abs(val[2])

            smallPosCheck = ['thumb', 'index', 'middle', 'ring', 'pinky', 'eye']
            midPosCheck = ['neck', 'headJnt', 'shoulder', 'elbow', 'wrist', 'knee', 'ankle', 'ball', 'toe']
            # lrgPosCheck = ['root', 'spine', 'clavicle']
            if any(j in jnt for j in smallPosCheck) and not any(j in "1" for j in smallPosCheck):
                if valTotal > 4: ## Tolerance for above joints
                    cmds.warning('"' + jnt + '" is not in the accurate position. Look at reference and adjust.')
                    # placement_mark -= 2
                else:
                    placement_mark += placement_mark_division
            elif any(j in jnt for j in smallPosCheck) or any(j in jnt for j in midPosCheck):
                if valTotal > 4: ## Tolerance for above joints
                    cmds.warning('"' + jnt + '" is not in the accurate position. Look at reference and adjust.')
                    # placement_mark -= 2
                else:
                    placement_mark += placement_mark_division
            elif valTotal > 4: ## Tolerance for above joints
                cmds.warning('"' + jnt + '" is not in the accurate position. Look at reference and adjust.')
                # placement_mark -= 2
            else:
                placement_mark += placement_mark_division

        # check to make sure there is only one hierarchy
        if not cmds.listRelatives(jnt, parent=True, type='joint'):
            root.append(jnt)
        # check parenting
        # parenting_mark = 10
        if jnt == 'rootJnt':
            if cmds.listRelatives(jnt, children=True) and len(cmds.listRelatives(jnt, children=True)) != 3:
                cmds.warning('rootJnt should have three child joints: spine1Jnt, left_HipJnt, right_HipJnt')
            else:
                parenting_mark += parenting_mark_division
        elif jnt == 'spine4Jnt':
            if cmds.listRelatives(jnt, children=True) and len(cmds.listRelatives(jnt, children=True)) != 3:
                cmds.warning('spine4Jnt should have three child joints: neck1Jnt, left_clavicleJnt, right_clavicleJnt')
            else:
                parenting_mark += parenting_mark_division
        elif jnt == 'headJnt':
            if cmds.listRelatives(jnt, children=True) and len(cmds.listRelatives(jnt, children=True)) != 4:
                cmds.warning('headJnt should have four child joints: jawJnt, headEndJnt, left_eyeJnt, right_eyeJnt')
            else:
                parenting_mark += parenting_mark_division
        elif jnt == 'left_elbowJnt':
            if cmds.listRelatives(jnt, children=True) and len(cmds.listRelatives(jnt, children=True)) != 1:
                cmds.warning('left_elbowJnt should have a child joint: left_wristJnt')
            else:
                parenting_mark += parenting_mark_division
        elif jnt == 'right_elbowJnt':
            if cmds.listRelatives(jnt, children=True) and len(cmds.listRelatives(jnt, children=True)) != 1:
                cmds.warning('right_elbowJnt should have a child joint: right_wristJnt')
            else:
                parenting_mark += parenting_mark_division
        elif jnt == 'left_wristJnt':
            if cmds.listRelatives(jnt, children=True) and len(cmds.listRelatives(jnt, children=True)) != 5:
                cmds.warning(
                    'left_wristJnt should have five child joints: left_thumb1Jnt, left_index1Jnt, left_middle1Jnt, left_ring1Jnt, left_pinky1Jnt')
            else:
                parenting_mark += parenting_mark_division
        elif jnt == 'right_wristJnt':
            if cmds.listRelatives(jnt, children=True) and len(cmds.listRelatives(jnt, children=True)) != 5:
                cmds.warning(
                    'right_wristJnt should have five child joints: right_thumb1Jnt, right_index1Jnt, right_middle1Jnt, right_ring1Jnt, right_pinky1Jnt')
            else:
                parenting_mark += parenting_mark_division
        elif "EndJnt" in jnt or "eyeJnt" in jnt:
            if cmds.listRelatives(jnt, children=True):
                cmds.warning(jnt + ' should not have any children')
            else:
                parenting_mark += parenting_mark_division
        elif cmds.listRelatives(jnt, children=True) and len(cmds.listRelatives(jnt, children=True)) != 1:
            cmds.warning(jnt + ' should have only one children')
        else:
            parenting_mark += parenting_mark_division

    # make sure joints are all under one hierarchy
    # scene_mark = 5
    if len(root) > 1:
        cmds.warning('Your joints are not under one hierarchy.')
        # scene_mark -= (len(root) * 5)
    else:
        scene_mark += 2

    # make sure root joint isn't parented to anything
    for j in root:
        if cmds.listRelatives(j, p=True):
            cmds.warning('Joints should not be parented to anything other than joints.')
            # scene_mark -= (len(root) * 5)
        else:
            scene_mark += 2
    '''
    print 'name_mark:', name_mark,'/25'
    print 'parenting_mark:', parenting_mark,'/10'
    print 'orients_mark:', orients_mark,'/30'
    print 'transforms_mark:', transforms_mark,'/5'
    print 'placement_mark:', placement_mark,'/25'
    print 'scene_mark:', scene_mark,'/5'
    print 'deductions:', deductions
    '''

    # make sure mark is above max
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

    print 'name_mark:', name_mark, '/25'
    print 'parenting_mark:', parenting_mark, '/10'
    print 'orients_mark:', orients_mark, '/30'
    print 'transforms_mark:', transforms_mark, '/5'
    print 'placement_mark:', placement_mark, '/25'
    print 'scene_mark:', scene_mark, '/5'
    print 'deductions:', deductions

    final_mark = name_mark + parenting_mark + orients_mark + transforms_mark + placement_mark + scene_mark - deductions
    if final_mark >= 100:
        print '                          >     No Issues     <'
        cmds.confirmDialog(title='Great! 100%', icon='information',
                           message='Congratulations! Your rig is looking good so far!\n\nNote: This is not necessarily a final grade.')
    else:
        print '\n^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^'
        print '^^^^^^^^^^^^^^^^^^^^^^^^^^^^ Skeleton Issues ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^'
        print '^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^'
        cmds.warning('Your score so far is ' + str(final_mark) + '%. See script editor for a list of issues.')
        cmds.confirmDialog(title=('Score: ' + str(final_mark)), icon='warning', message=('Your score so far is ' + str(
            final_mark) + '%. See script editor for a list of issues.\n\nNote: This is not necessarily a final grade.'))


main()