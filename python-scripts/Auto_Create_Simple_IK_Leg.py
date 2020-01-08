import maya.cmds as cmds

'''
Current How to:
Select Start of IK joint
End of IK Joint
End of Foot Joint

This script is a work in progress.
To do:
1. Add Stretchy legs
2. Make UI (load custom objects to be checked)
3. Make sure it's not dependent on previous system
4. Use toe or not (checkbox)
5. Better way to manage tags (use length)
6. Better way to grab weight name (look for attribute)
7. Make first joint parent to FK control after creating system
'''

# Auto Create Simple IK Legs Generator
# @Guilherme Trevisan - TrevisanGMW@gmail.com - 2019-01-06
# Last update - 2019-01-06
#

# Version:
scriptVersion = "v0.1a"

ctrlGrpTag = 'CtrlGrp'
ctrlTag = 'Ctrl'
jntTag = 'Jnt' #not yet used, grab legth! later

usingCustomCtrl = True
customCtrlName = 'left_back_paw_IK_fawnCtrl'
usingCustomPoleVectorCtrl = True
customPoleVectorCtrl = 'left_back_leg1_PoleVector_fawnCtrl'
usingCustomIKFKSwitch = True
customIKFKSwitchName = 'L_B_Leg_FK_IK_Switch_fawn'


selectedJoints = cmds.ls(selection=True, type='joint')
#Add if exists?
startJoint_RP_FK = selectedJoints[0] # Hip
middleJoint_RP_FK = cmds.listRelatives(startJoint_RP_FK, type='joint')[0] # Knee
#grab knee here
endJoint_RP_FK = selectedJoints[1] # Foot
endJoint_SC_FK = selectedJoints[2] # Toe
#endJoint_SC_IK = selectedJoints[3] # Toe End?


startJoint_RP_IK = cmds.duplicate(startJoint_RP_FK, po=True, name = startJoint_RP_FK[:-3] + "_IK_Jnt")
middleJoint_RP_IK = cmds.duplicate(middleJoint_RP_FK, po=True, name = middleJoint_RP_FK[:-3] + "_IK_Jnt") # list
endJoint_RP_IK = cmds.duplicate(endJoint_RP_FK, po=True, name = endJoint_RP_FK[:-3] + "_IK_Jnt")
endJoint_SC_IK = cmds.duplicate(endJoint_SC_FK, po=True, name = endJoint_SC_FK[:-3] + "_IK_Jnt")

#Check if it's not already under world before doing this
cmds.parent(startJoint_RP_IK, world=True)
cmds.parent( middleJoint_RP_IK, startJoint_RP_IK )
cmds.parent( endJoint_RP_IK, middleJoint_RP_IK )
cmds.parent( endJoint_SC_IK, endJoint_RP_IK )

startJoint_RP_IK_pConstraint = cmds.parentConstraint( startJoint_RP_IK, startJoint_RP_FK )
middleJoint_RP_IK_pConstraint = cmds.parentConstraint( middleJoint_RP_IK, middleJoint_RP_FK )
endJoint_RP_IK_pConstraint = cmds.parentConstraint( endJoint_RP_IK, endJoint_RP_FK )
# check if it has a constraint before doing it? it might not even be necessary
#endJoint_SC_IK_pConstraint = cmds.parentConstraint( endJoint_SC_IK, endJoint_SC_FK )


# main IK
ikHandleName = startJoint_RP_IK[0][:-3] + 'RP_ikHandle'
ikHandle_RP = cmds.ikHandle( n=ikHandleName, sj=startJoint_RP_IK[0], ee=endJoint_RP_IK[0], sol='ikRPsolver')

# foot IK
ikHandleName = endJoint_RP_IK[0][:-3] + 'SC_ikHandle'
ikHandle_SC = cmds.ikHandle( n=ikHandleName, sj=endJoint_RP_IK[0], ee=endJoint_SC_IK[0], sol='ikSCsolver')
#Make so it doesn't go inside of a group - right now it goes inside the L_F_Leg_FK_IK_Switch_doeGrp

#check if right or left and color it
#ikControlName = 
if usingCustomCtrl:
    ikControl = customCtrlName
else:
    ikControl = cmds.curve(name = startJoint_RP_IK[0][:-3] + 'Ctrl', p=[[-0.569, 0.569, -0.569], [-0.569, 0.569, 0.569], [0.569, 0.569, 0.569], [0.569, 0.569, -0.569], [-0.569, 0.569, -0.569], [-0.569, -0.569, -0.569], [0.569, -0.569, -0.569], [0.569, 0.569, -0.569], [0.569, 0.569, 0.569], [0.569, -0.569, 0.569], [0.569, -0.569, -0.569], [-0.569, -0.569, -0.569], [-0.569, -0.569, 0.569], [0.569, -0.569, 0.569], [0.569, 0.569, 0.569], [-0.569, 0.569, 0.569], [-0.569, -0.569, 0.569]],d=1)
    ikCtrlGrp = cmds.group(name=(ikControl+'Grp'))
    placementConstraint = cmds.pointConstraint(endJoint_RP_IK,ikCtrlGrp)
    cmds.delete(placementConstraint)

#cmds.rename(ikControl, ikControlName)


cmds.parentConstraint(ikControl, ikHandle_SC[0], maintainOffset=True)
cmds.parentConstraint(ikControl, ikHandle_RP[0], maintainOffset=True)


if usingCustomPoleVectorCtrl:
    poleVector = customPoleVectorCtrl
else:
    #if orientation, then move forward of backwards
    poleVector = cmds.curve(name= ikControl[:-4] + 'poleVectorCtrl', p=[[0.268, 0.268, 0.0], [0.535, 0.268, 0.0], [0.535, -0.268, -0.0], [0.268, -0.268, -0.0], [0.268, -0.535, -0.0], [-0.268, -0.535, -0.0], [-0.268, -0.268, -0.0], [-0.535, -0.268, -0.0], [-0.535, 0.268, 0.0], [-0.268, 0.268, 0.0], [-0.268, 0.535, 0.0], [0.268, 0.535, 0.0], [0.268, 0.268, 0.0]],d=1)
    poleVectorCtrlGrp = cmds.group(name=(poleVector +'Grp'))
    #move group here (forward or backwards?)
    placementConstraint = cmds.pointConstraint(middleJoint_RP_IK,poleVectorCtrlGrp)
    cmds.delete(placementConstraint)
    
cmds.poleVectorConstraint( poleVector, ikHandle_RP[0] ) # Investigate here


def lockHideAttr(obj,attrArray,lock,hide):
    for a in attrArray:
        maya.cmds.setAttr(obj + '.' + a, k=hide,l=lock)

if usingCustomIKFKSwitch:
    ikSwitchCtrl = customIKFKSwitchName
else:
    ikSwitchCtrl = cmds.curve(name = ikControl[:-4] + '_SwitchCtrl',p=[[0.784, 0.0, -11.123], [0.0, 0.0, -11.448], [-0.784, 0.0, -11.123], [-1.108, 0.0, -10.339], [-0.784, -0.0, -9.556], [-0.0, -0.0, -9.231], [0.784, -0.0, -9.556], [1.108, -0.0, -10.339]],d=3)

cmds.addAttr(ikSwitchCtrl, niceName='IK FK Switch', longName='ikSwitch', attributeType='bool', defaultValue = 1, keyable = True )
cmds.addAttr(ikSwitchCtrl, niceName='IK FK Influence', longName='ikInfluence', attributeType='double', defaultValue = 1, keyable = True )
lockHideAttr(ikSwitchCtrl, ['tx','ty','tz','rx','ry','rz', 'sx','sy','sz','v'],True,False)
ikSwitchCtrlGrp = cmds.group(name=(ikSwitchCtrl+'Grp'))

reverseNode = cmds.createNode('reverse')
cmds.connectAttr('%s.ikSwitch' % ikSwitchCtrl, '%s.inputX' % reverseNode)


ctrlName = startJoint_RP_FK[:-3] + ctrlGrpTag
if cmds.objExists(ctrlName):
    cmds.connectAttr('%s.outputX' % reverseNode, '%s.v' % ctrlName)
    
ctrlName = middleJoint_RP_FK[:-3] + ctrlGrpTag
if cmds.objExists(ctrlName):
    cmds.connectAttr('%s.outputX' % reverseNode, '%s.v' % ctrlName)
  
ctrlName = endJoint_RP_FK[:-3] + ctrlGrpTag
if cmds.objExists(ctrlName):
    cmds.connectAttr('%s.outputX' % reverseNode, '%s.v' % ctrlName)  

ctrlName = endJoint_SC_FK[:-3] + ctrlGrpTag
if cmds.objExists(ctrlName):
    cmds.connectAttr('%s.outputX' % reverseNode, '%s.v' % ctrlName)
    

cmds.connectAttr('%s.ikSwitch' % ikSwitchCtrl, '%s.v' % ikControl)
cmds.connectAttr('%s.ikSwitch' % ikSwitchCtrl, '%s.v' % poleVector)

#Main ctrl IK Influence > Condition (if one (IK) pass data) > Reverse = FK    Normal = IK

conditionNode = cmds.createNode('condition')
cmds.setAttr(conditionNode + '.secondTerm', 1)
cmds.setAttr(conditionNode + '.colorIfFalseR', 0)
cmds.setAttr(conditionNode + '.colorIfFalseG', 0)
cmds.setAttr(conditionNode + '.colorIfFalseB', 0)
cmds.connectAttr('%s.ikSwitch' % ikSwitchCtrl, '%s.firstTerm' % conditionNode)
cmds.connectAttr('%s.ikInfluence' % ikSwitchCtrl, '%s.colorIfTrueR' % conditionNode)


cmds.connectAttr('%s.outColorR' % conditionNode, startJoint_RP_IK_pConstraint[0] + '.' + startJoint_RP_IK[0] + "W1")
cmds.connectAttr('%s.outColorR' % conditionNode, middleJoint_RP_IK_pConstraint[0] + '.' + middleJoint_RP_IK[0] + "W1")
cmds.connectAttr('%s.outColorR' % conditionNode, endJoint_RP_IK_pConstraint[0] + '.' + endJoint_RP_IK[0] + "W1")

reverseConditionNode = cmds.createNode('reverse')
cmds.connectAttr('%s.outColorR' % conditionNode, '%s.inputX' % reverseConditionNode)

cmds.connectAttr('%s.outputX' % reverseConditionNode, startJoint_RP_IK_pConstraint[0] + '.' + startJoint_RP_FK[:-3] + ctrlTag + "W0")
cmds.connectAttr('%s.outputX' % reverseConditionNode, middleJoint_RP_IK_pConstraint[0] + '.' + middleJoint_RP_FK[:-3] + ctrlTag + "W0")
cmds.connectAttr('%s.outputX' % reverseConditionNode, endJoint_RP_IK_pConstraint[0] + '.' + endJoint_RP_FK[:-3] + ctrlTag + "W0")




#type='parentConstraint' 
#cmds.ls(nt=True)
