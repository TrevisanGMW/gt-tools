import maya.cmds as cmds
from decimal import *

# IK Leg Generator 
# @Guilherme Trevisan - TrevisanGMW@gmail.com - 2019-01-06
# Last update - 2019-01-06
#

# Version:
scriptVersion = "v1.0"

# Default Settings
useBallJnt = True
addImport = False

ctrlGrpTag = 'CtrlGrp'
ctrlTag = 'Ctrl'
jntTag = 'Jnt' #not yet used, grab legth! later

usingCustomCtrl = False
customCtrlName = 'left_back_paw_IK_fawnCtrl'
usingCustomPoleVectorCtrl = False
customPoleVectorCtrl = 'left_back_leg1_PoleVector_fawnCtrl'
usingCustomIKFKSwitch = False
customIKFKSwitchName = 'L_B_Leg_FK_IK_Switch_fawn'


storedJoints = { 'hipJnt': '', 
             'ankleJnt': '',
             'ballJnt': ''
            }
            


# Function for the "Run Code" button
def runOutput(out):
    try:
        exec(out)
    except:
        cmds.warning("Something is wrong with your code!")


# Main Form ============================================================================
def ikLegMainDialog():
    if cmds.window("ikLegMainDialog", exists =True):
        cmds.deleteUI("ikLegMainDialog")    

    # mainDialog Start Here =================================================================================

    ikLegMainDialog = cmds.window("ikLegMainDialog", title="IK Leg - " + scriptVersion, widthHeight=(480,250),\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =True)

    columnMain = cmds.columnLayout() 

    form = cmds.formLayout(p=columnMain)

    contentMain = cmds.columnLayout(adj = True)

    cmds.text("")
    cmds.text("IK Leg Generator - " + scriptVersion, bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.text("  ")
    cmds.text("      This script assumes that you already have       ")
    cmds.text("      joints for the leg. (hip, knee, ankle, ball, toe)     ")
    cmds.text("   ")
    cmds.text('1. Load your joints  ')
    cmds.text('(Select Jnt and Click Load)  ')
    cmds.text('2. Click on \"Generate\"  ')
    cmds.text("   ")
    cmds.separator(h=10, p=contentMain)
    interactiveContainer = cmds.rowColumnLayout( numberOfRows=1, h= 25)
    cmds.text("   ")
    settings = cmds.checkBoxGrp(p=interactiveContainer, columnWidth2=[150, 1], numberOfCheckBoxes=2, \
                                label1 = 'Add import \"maya.cmds\" ', label2 = "Use Ball Joint", v1 = addImport, v2 = useBallJnt, \
                                on2=lambda x:isBallEnabled(True),  of2=lambda x:isBallEnabled(False) )   
    
    #Hip Joint Loader
    hipContainer = cmds.rowColumnLayout( p=contentMain, numberOfRows=1)
    cmds.button(p=hipContainer, l ="Load Hip Joint", c=lambda x:updateLoadButton("hip"), w=130)
    hipStatus = cmds.button(p=hipContainer, l ="Not loaded yet", bgc=(0, 0, 0), w=130, \
                            c="cmds.headsUpMessage( 'Select your hip joint and click on \"Load Hip Joint\"', verticalOffset=150 , time=5.0)")
                            
    #Ankle Joint Loader
    ankleContainer = cmds.rowColumnLayout( p=contentMain, numberOfRows=1)
    cmds.button(p=ankleContainer, l ="Load Ankle Joint", c=lambda x:updateLoadButton("ankle"), w=130)
    ankleStatus = cmds.button(p=ankleContainer, l ="Not loaded yet", bgc=(0, 0, 0), w=130, \
                            c="cmds.headsUpMessage( 'Select your ankle joint and click on \"Load Ankle Joint\"', verticalOffset=150 , time=5.0)")
                            
    #Ball Joint Loader
    ballContainer = cmds.rowColumnLayout( p=contentMain, numberOfRows=1)
    ballLoadButton = cmds.button(p=ballContainer, l ="Load Ball Joint", c=lambda x:updateLoadButton("ball"), w=130)
    ballStatus = cmds.button(p=ballContainer, l ="Not loaded yet", bgc=(0, 0, 0), w=130, \
                            c="cmds.headsUpMessage( 'Select your ball joint and click on \"Load Ball Joint\"', verticalOffset=150 , time=5.0)")
      

    cmds.separator(h=10, p=contentMain)
    cmds.text(p=contentMain, label='Click Here After Loading Joints' )
    #outputPython = cmds.scrollField(p =contentMain, editable=True, wordWrap=True)
    cmds.button(p=contentMain, l ="Generate",bgc=(.2, .2, .25), c=lambda x:generateIkLeg())
    
    def isBallEnabled(state):
        if state:
            print("True")
            cmds.button(ballLoadButton, e=True, en=True)
            cmds.button(ballStatus, l ="Not loaded yet", e=True, en=True, bgc=(0, 0, 0))
            storedJoints["ballJnt"] = ''
        else:
            print("False")
            cmds.button(ballLoadButton, e=True, en=False)
            cmds.button(ballStatus, e=True, en=False, bgc=(.25, .25, .25))
    
    def updateLoadButton(buttonName):
        
        # Check If Selection is Valid
        receiveValidJnt = False
        selectedJoints = cmds.ls(selection=True, type='joint')
        if len(selectedJoints) == 0:
            cmds.warning("First element in your selection wasn't a joint")
        elif len(selectedJoints) > 1:
            cmds.warning("You selected more than one joint! Please select only one")
        elif cmds.objectType(selectedJoints[0]) == "joint":
            joint = selectedJoints[0]
            receiveValidJnt = True
        else:
            cmds.warning("Something went wrong, make sure you selected just one joint")
            
        # If Hip
        if buttonName is "hip" and receiveValidJnt == True:
            storedJoints["hipJnt"] = joint
            cmds.button(hipStatus, l =joint,e=True, bgc=(.6, .8, .6), w=130, c=lambda x:ifExistsSelect(storedJoints.get("hipJnt")))
        elif buttonName is "hip":
            cmds.button(hipStatus, l ="Fail to Load",e=True, bgc=(1, .4, .4), w=130,c="cmds.headsUpMessage( 'Make sure you select only one joint and try again', verticalOffset=150 , time=5.0)")
        
        # If Ankle
        if buttonName is "ankle" and receiveValidJnt == True:
            storedJoints["ankleJnt"] = joint
            cmds.button(ankleStatus, l =joint,e=True, bgc=(.6, .8, .6), w=130, c=lambda x:ifExistsSelect(storedJoints.get("ankleJnt")))
        elif buttonName is "ankle":
            cmds.button(ankleStatus, l ="Fail to Load",e=True, bgc=(1, .4, .4), w=130,c="cmds.headsUpMessage( 'Make sure you select only one joint and try again', verticalOffset=150 , time=5.0)")
        
        # If Ball
        if buttonName is "ball" and receiveValidJnt == True:
            storedJoints["ballJnt"] = joint
            cmds.button(ballStatus, l =joint,e=True, bgc=(.6, .8, .6), w=130, c=lambda x:ifExistsSelect(storedJoints.get("ballJnt")))
        elif buttonName is "ball":
            cmds.button(ballStatus, l ="Fail to Load",e=True, bgc=(1, .4, .4), w=130,c="cmds.headsUpMessage( 'Make sure you select only one joint and try again', verticalOffset=150 , time=5.0)")


    cmds.showWindow(ikLegMainDialog)
    # mainDialog Ends Here =================================================================================


# Main Function, it generates the ik legs
def generateIkLeg():
    # ============================= End of Main Function =============================
    #Add if exists?
    startJoint_RP_FK = storedJoints.get("hipJnt") # Hip
    middleJoint_RP_FK = cmds.listRelatives(startJoint_RP_FK, type='joint')[0] # Knee
    endJoint_RP_FK = storedJoints.get("ankleJnt") # Ankle
    endJoint_SC_FK = storedJoints.get("ballJnt") # Ball
    #endJoint_SC_IK = selectedJoints[3] # Toe End?

    # Creates IK Skeleton
    startJoint_RP_IK = cmds.duplicate(startJoint_RP_FK, po=True, name = startJoint_RP_FK[:-3] + "_IK_Jnt")
    middleJoint_RP_IK = cmds.duplicate(middleJoint_RP_FK, po=True, name = middleJoint_RP_FK[:-3] + "_IK_Jnt") # list
    endJoint_RP_IK = cmds.duplicate(endJoint_RP_FK, po=True, name = endJoint_RP_FK[:-3] + "_IK_Jnt")
    endJoint_SC_IK = cmds.duplicate(endJoint_SC_FK, po=True, name = endJoint_SC_FK[:-3] + "_IK_Jnt")

    # Recreate Hierarchy
    cmds.parent( startJoint_RP_IK, world=True) # Check if it's not already under world before doing this
    cmds.parent( middleJoint_RP_IK, startJoint_RP_IK )
    cmds.parent( endJoint_RP_IK, middleJoint_RP_IK )
    cmds.parent( endJoint_SC_IK, endJoint_RP_IK )

    startJoint_RP_IK_pConstraint = cmds.parentConstraint( startJoint_RP_IK, startJoint_RP_FK )
    middleJoint_RP_IK_pConstraint = cmds.parentConstraint( middleJoint_RP_IK, middleJoint_RP_FK )
    endJoint_RP_IK_pConstraint = cmds.parentConstraint( endJoint_RP_IK, endJoint_RP_FK )
    # check if it has a constraint before doing it? it might not even be necessary
    #endJoint_SC_IK_pConstraint = cmds.parentConstraint( endJoint_SC_IK, endJoint_SC_FK )

    # Create Main Rotate-Plane IK Solver
    ikHandleName = startJoint_RP_IK[0][:-3] + 'RP_ikHandle'
    ikHandle_RP = cmds.ikHandle( n=ikHandleName, sj=startJoint_RP_IK[0], ee=endJoint_RP_IK[0], sol='ikRPsolver')

    # Create Ankle to Ball Single-Chain IK Solver
    ikHandleName = endJoint_RP_IK[0][:-3] + 'SC_ikHandle'
    ikHandle_SC = cmds.ikHandle( n=ikHandleName, sj=endJoint_RP_IK[0], ee=endJoint_SC_IK[0], sol='ikSCsolver')
    #Make so it doesn't go inside of a group - right now it goes inside the L_F_Leg_FK_IK_Switch_doeGrp

    #check if right or left and color it (add checkbox for turning this on or off)

    if usingCustomCtrl:
        ikControl = customCtrlName
    else:
        ikControl = cmds.curve(name = startJoint_RP_IK[0][:-3] + 'Ctrl', p=[[-0.569, 0.569, -0.569], [-0.569, 0.569, 0.569], \
                    [0.569, 0.569, 0.569], [0.569, 0.569, -0.569], [-0.569, 0.569, -0.569], [-0.569, -0.569, -0.569], \
                    [0.569, -0.569, -0.569], [0.569, 0.569, -0.569], [0.569, 0.569, 0.569], [0.569, -0.569, 0.569], \
                    [0.569, -0.569, -0.569], [-0.569, -0.569, -0.569], [-0.569, -0.569, 0.569], [0.569, -0.569, 0.569], \
                    [0.569, 0.569, 0.569], [-0.569, 0.569, 0.569], [-0.569, -0.569, 0.569]],d=1) # Creates Cube
                    
        ikCtrlGrp = cmds.group(name=(ikControl+'Grp'))
        placementConstraint = cmds.pointConstraint(endJoint_RP_IK,ikCtrlGrp)
        cmds.delete(placementConstraint)

    # Constraint IK Handles to IK Control
    cmds.parentConstraint(ikControl, ikHandle_SC[0], maintainOffset=True)
    cmds.parentConstraint(ikControl, ikHandle_RP[0], maintainOffset=True)


    if usingCustomPoleVectorCtrl:
        poleVector = customPoleVectorCtrl
    else:
        #CHECK ORIENTATION  - if orientation, then move forward or backwards
        poleVector = cmds.curve(name= ikControl[:-4] + 'poleVectorCtrl', p=[[0.268, 0.268, 0.0], [0.535, 0.268, 0.0], [0.535, -0.268, -0.0], [0.268, -0.268, -0.0], [0.268, -0.535, -0.0], [-0.268, -0.535, -0.0], [-0.268, -0.268, -0.0], [-0.535, -0.268, -0.0], [-0.535, 0.268, 0.0], [-0.268, 0.268, 0.0], [-0.268, 0.535, 0.0], [0.268, 0.535, 0.0], [0.268, 0.268, 0.0]],d=1)
        poleVectorCtrlGrp = cmds.group(name=(poleVector +'Grp'))
        #move group here (forward or backwards?)
        placementConstraint = cmds.pointConstraint(middleJoint_RP_IK,poleVectorCtrlGrp)
        cmds.delete(placementConstraint)
        
    cmds.poleVectorConstraint( poleVector, ikHandle_RP[0] ) # Investigate here

    if usingCustomIKFKSwitch:
        ikSwitchCtrl = customIKFKSwitchName
    else:
        ikSwitchCtrl =  cmds.curve(name = ikControl[:-4] + '_SwitchCtrl', degree = 1,\
                knot = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],\
                point = [(5.8520521406535408e-007, 0, -1.0398099422454834),\
                         (1.2360682487487793, 0, -3.8042259216308594),\
                         (3.2360701560974121, 0, -2.351142406463623),\
                         (0.69169783592224121, 0, -0.53726297616958618),\
                         (3.9999988079071045, 0, 2.2737367544323206e-013),\
                         (3.2360680103302002, 0, 2.3511412143707275),\
                         (0.42749345302581787, 0, 0.27587676048278809),\
                         (1.2360677719116211, 0, 3.8042242527008057),\
                         (-1.2360682487487793, 0, 3.8042266368865967),\
                         (-0.42749285697937012, 0, 0.27587652206420898),\
                         (-3.236067533493042, 0, 2.3511402606964111),\
                         (-4.0000009536743164, 0, 0),\
                         (-0.6916964054107666, 0, -0.53726291656494141),\
                         (-3.2360677719116211, 0, -2.3511404991149902),\
                         (-1.2360686063766479, 0, -3.8042278289794922),\
                         (5.8520521406535408e-007, 0, -1.0398099422454834)]) # Creates Fancy Shape, update this to FKIK Switch Curves
                         
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
    # ============================= End of Main Function =============================

#Locks an hides attributes
def lockHideAttr(obj,attrArray,lock,hide):
        for a in attrArray:
            maya.cmds.setAttr(obj + '.' + a, k=hide,l=lock)


#If object exists, select it
def ifExistsSelect(obj):
    if cmds.objExists(obj):
        cmds.select(obj)
        cmds.headsUpMessage(obj + " selected", verticalOffset=150 )
    else:
        cmds.warning("Object doesn't exist! Did you delete or rename it after loading?")

#Start current "Main"
ikLegMainDialog()