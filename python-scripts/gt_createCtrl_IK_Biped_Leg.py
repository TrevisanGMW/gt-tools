import maya.cmds as cmds
from decimal import *

# IK Leg Generator (This script is still a work in progress)
# @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-01-06
# Last update - 2020-03-11


# Version:
scriptVersion = "v1.0"


storedJoints = { 'hipJnt': '', 
             'ankleJnt': '',
             'ballJnt': ''
            }

settings = { 'usingCustomIKCtrl': False, 
             'customIKCtrlName': '',
             'usingCustomPoleVectorCtrl': False,
             'customPoleVectorCtrl' : '',
             'usingCustomIKFKSwitch' : False,
             'customIKFKSwitchName' : '',
             'usingColorizeCtrls' : True,
             'useBallJntDef' : True,
             'colorizeCtrlDef' : True,
             'useIKCtrlDef' : False,
             'useIKSwitchDef' : False,
             'usePVectorDef' : False,
             'makeStretchy' : True,
             'ctrlGrpTag' : 'CtrlGrp',
             'jntTag' : 'Jnt'
            }


# Main Form ============================================================================
def ikLegMainDialog():
    if cmds.window("ikLegMainDialog", exists =True):
        cmds.deleteUI("ikLegMainDialog")    

    # mainDialog Start Here =================================================================================

    ikLegMainDialog = cmds.window("ikLegMainDialog", title="gt_ik_leg - " + scriptVersion,\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable = False)

    columnMain = cmds.columnLayout() 

    form = cmds.formLayout(p=columnMain)

    contentMain = cmds.columnLayout(adj = True)


    cmds.text("", h=7)
    row1 = cmds.rowColumnLayout(p=contentMain, numberOfRows=1 ) #Empty Space
    cmds.text( "         GT - IK Leg Generator - " + scriptVersion + "           ",p=row1, bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.button( l ="Help", bgc=(0, .5, 0), c=lambda x:ikLegGeneratorHelpMenuDialog())
    cmds.text("        ", bgc=[0,.5,0])
    cmds.rowColumnLayout(p=contentMain, adj = True)

    cmds.text("  ")
    cmds.text("      This script assumes that you already have       ")
    cmds.text("      joints for the leg. (hip, knee, ankle, ball, toe)     ")
    cmds.text("   ")
    cmds.text('1. Load your joints  ')
    cmds.text('(Select Jnt and Click Load)  ')
    cmds.text('2. Click on \"Generate\"  ')
    cmds.text("   ")
    cmds.separator(h=15, p=contentMain)
    
    textContainer = cmds.rowColumnLayout( p=contentMain , numberOfRows=1)
    cmds.text("        Joint Tag (Suffix)", p = textContainer)
    cmds.text("          Ctrl Group Tag (Suffix)", p = textContainer)
    cmds.rowColumnLayout( p=contentMain, h=3) # Empty Space
    tagStringContainer = cmds.rowColumnLayout( p=contentMain, numberOfRows=1)
    
    jntTagTxtfield = cmds.textField(p = tagStringContainer, width=130, text=settings.get("jntTag"), \
                                           enterCommand=lambda x:updateSettings(), textChangedCommand=lambda x:updateSettings())
    ctrlGrpTxtfield = cmds.textField(p = tagStringContainer,width=130, text=settings.get("ctrlGrpTag"), \
                                           enterCommand=lambda x:updateSettings(), textChangedCommand=lambda x:updateSettings())
    
    
    cmds.separator(h=15, p=contentMain)
    
    # CheckboxGrp One
    interactiveContainerMisc = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 25)
    cmds.text("    ")
    checkBoxGrpOne = cmds.checkBoxGrp(p=interactiveContainerMisc, columnWidth2=[130, 1], numberOfCheckBoxes=2, \
                                label1 = 'Custom PVector Ctrl', label2 = "Custom IK Ctrl", v1 = settings.get("usePVectorDef"), v2 = settings.get("useIKCtrlDef"), \
                                on2=lambda x:isCustomIKCtrlEnabled(True),  of2=lambda x:isCustomIKCtrlEnabled(False), \
                                on1 =lambda x:isCustomPVectorEnabled(True), of1=lambda x:isCustomPVectorEnabled(False) ) 
    # CheckboxGrp Two
    interactiveContainerMisc = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 25)
    cmds.text("    ")
    checkBoxGrpTwo = cmds.checkBoxGrp(p=interactiveContainerMisc, columnWidth2=[130, 1], numberOfCheckBoxes=2, \
                                label1 = 'Colorize Controls ', label2 = "Custom IK Switch", v1 = settings.get("colorizeCtrlDef"), v2 = settings.get("useIKSwitchDef"), \
                                on2=lambda x:isCustomIKSwitchEnabled(True),  of2=lambda x:isCustomIKSwitchEnabled(False) ) 
    cmds.separator(h=10, p=contentMain)
    
    #pVector Ctrl Loader
    pVectorContainer = cmds.rowColumnLayout( p=contentMain, numberOfRows=1)
    pVectorBtn = cmds.button(p=pVectorContainer, l ="Load PVector Ctrl", c=lambda x:updateLoadButtonCtrls("pVector"), w=130)
    pVectorStatus = cmds.button(p=pVectorContainer, l ="Not loaded yet", bgc=(0, 0, 0), w=130, \
                            c="cmds.headsUpMessage( 'Select your pole vector control and click on \"Load PVector Ctrl Joint\"', verticalOffset=150 , time=5.0)")
    
    #Custom IK Ctrl Loader
    ikCtrlContainer = cmds.rowColumnLayout( p=contentMain, numberOfRows=1)
    ikCtrlBtn = cmds.button(p=ikCtrlContainer, l ="Load IK Ctrl", c=lambda x:updateLoadButtonCtrls("ikCtrl"), w=130)
    ikCtrlStatus = cmds.button(p=ikCtrlContainer, l ="Not loaded yet", bgc=(0, 0, 0), w=130, \
                            c="cmds.headsUpMessage( 'Select your IK Switch control and click on \"Load IK Switch Ctrl Joint\"', verticalOffset=150 , time=5.0)")
    
    #IK Switch Ctrl Loader
    ikSwitchContainer = cmds.rowColumnLayout( p=contentMain, numberOfRows=1)
    ikSwitchBtn = cmds.button(p=ikSwitchContainer, l ="Load IK Switch Ctrl", c=lambda x:updateLoadButtonCtrls("ikSwitch"), w=130)
    ikSwitchStatus = cmds.button(p=ikSwitchContainer, l ="Not loaded yet", bgc=(0, 0, 0), w=130,  \
                            c="cmds.headsUpMessage( 'Select your Custom IK Control and click on \"Load IK Ctrl Joint\"', verticalOffset=150 , time=5.0)")
                            
    
    cmds.separator(h=15, p=contentMain)
    # CheckboxGrp Three
    interactiveContainerJnt = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 25)
    cmds.text("    ") # Increase this to move checkboxes to the right
    checkBoxGrpThree = cmds.checkBoxGrp(p=interactiveContainerJnt, columnWidth2=[130, 1], numberOfCheckBoxes=2, \
                                label1 = 'Make Stretchy Legs ', label2 = "Use Ball Joint", v1 = settings.get("makeStretchy"), v2 = settings.get("useBallJntDef"), \
                                on2=lambda x:isBallEnabled(True),  of2=lambda x:isBallEnabled(False)\
                               ,on1=lambda x:updateSettings(),  of1=lambda x:updateSettings())
                            
    cmds.separator(h=10, p=contentMain)
    #Hip Joint Loader
    hipContainer = cmds.rowColumnLayout( p=contentMain, numberOfRows=1)
    cmds.button(p=hipContainer, l ="Load Hip Joint", c=lambda x:updateLoadButtonJnt("hip"), w=130)
    hipStatus = cmds.button(p=hipContainer, l ="Not loaded yet", bgc=(0, 0, 0), w=130, \
                            c="cmds.headsUpMessage( 'Select your hip joint and click on \"Load Hip Joint\"', verticalOffset=150 , time=5.0)")
                            
    #Ankle Joint Loader
    ankleContainer = cmds.rowColumnLayout( p=contentMain, numberOfRows=1)
    cmds.button(p=ankleContainer, l ="Load Ankle Joint", c=lambda x:updateLoadButtonJnt("ankle"), w=130)
    ankleStatus = cmds.button(p=ankleContainer, l ="Not loaded yet", bgc=(0, 0, 0), w=130, \
                            c="cmds.headsUpMessage( 'Select your ankle joint and click on \"Load Ankle Joint\"', verticalOffset=150 , time=5.0)")
                            
    #Ball Joint Loader
    ballContainer = cmds.rowColumnLayout( p=contentMain, numberOfRows=1)
    ballLoadButton = cmds.button(p=ballContainer, l ="Load Ball Joint", c=lambda x:updateLoadButtonJnt("ball"), w=130)
    ballStatus = cmds.button(p=ballContainer, l ="Not loaded yet", bgc=(0, 0, 0), w=130, \
                            c="cmds.headsUpMessage( 'Select your ball joint and click on \"Load Ball Joint\"', verticalOffset=150 , time=5.0)")
      
    cmds.separator(h=10, p=contentMain)
    cmds.text(p=contentMain, label='Click Here After Loading Joints' )
    cmds.button(p=contentMain, l ="Generate",bgc=(.2, .2, .25), c=lambda x:checkBeforeRunning(cmds.checkBoxGrp(checkBoxGrpThree, q=True, value2=True)))
    
    def updateSettings():
        settings["makeStretchy"] = cmds.checkBoxGrp(checkBoxGrpThree, q=True, value1=True)
        
        jntTag = parseTextField(cmds.textField(jntTagTxtfield,q=True,text=True))
        if jntTag != [] and len(jntTag) > 0:
            settings["jntTag"] = jntTag[0]
        
        ctrlGrpTag = parseTextField(cmds.textField(ctrlGrpTxtfield,q=True,text=True))
        if ctrlGrpTag != [] and len(ctrlGrpTag) > 0:
            settings["ctrlGrpTag"] = ctrlGrpTag[0]

        
    def isBallEnabled(state):
        if state:
            cmds.button(ballLoadButton, e=True, en=True)
            cmds.button(ballStatus, l ="Not loaded yet", e=True, en=True, bgc=(0, 0, 0))
            storedJoints["ballJnt"] = ''
        else:
            cmds.button(ballLoadButton, e=True, en=False)
            cmds.button(ballStatus, l ="Not necessary", e=True, en=False, bgc=(.25, .25, .25))
            
    def isCustomIKCtrlEnabled(state):
        if state:
            cmds.button(ikCtrlBtn, e=True, en=True)
            cmds.button(ikCtrlStatus, l ="Not loaded yet", e=True, en=True, bgc=(0, 0, 0))
            settings["customIKCtrlName"] = ''
            settings["usingCustomIKCtrl"] = True
        else:
            cmds.button(ikCtrlBtn, e=True, en=False)
            cmds.button(ikCtrlStatus, l ="Not necessary", e=True, en=False, bgc=(.25, .25, .25))
            settings["usingCustomIKCtrl"] = False
            
    def isCustomIKSwitchEnabled(state):
        if state:
            cmds.button(ikSwitchBtn, e=True, en=True)
            cmds.button(ikSwitchStatus, l ="Not loaded yet", e=True, en=True, bgc=(0, 0, 0))
            settings["customIKFKSwitchName"] = ''
            settings["usingCustomIKFKSwitch"] = True
        else:
            cmds.button(ikSwitchBtn, e=True, en=False)
            cmds.button(ikSwitchStatus, l ="Not necessary", e=True, en=False, bgc=(.25, .25, .25))
            settings["usingCustomIKFKSwitch"] = False
            
    def isCustomPVectorEnabled(state):
        if state:
            cmds.button(pVectorBtn, e=True, en=True)
            cmds.button(pVectorStatus, l ="Not loaded yet", e=True, en=True, bgc=(0, 0, 0))
            settings["customPoleVectorCtrl"] = ''
            settings["usingCustomPoleVectorCtrl"] = True
        else:
            cmds.button(pVectorBtn, e=True, en=False)
            cmds.button(pVectorStatus, l ="Not necessary", e=True, en=False, bgc=(.25, .25, .25))
            settings["usingCustomPoleVectorCtrl"] = False
    
    # Curves Loader @@@@@@@@@@@@
    def updateLoadButtonCtrls(buttonName):
        
        # Check If Selection is Valid
        receivedValidCtrl = False
        selectedCtrls = cmds.ls(selection=True,tr=1, type='nurbsCurve')
        
        if len(selectedCtrls) == 0:
            cmds.warning("First element in your selection wasn't a control (nurbsCurve)")
        elif len(selectedCtrls) > 1:
            cmds.warning("You selected more than one curve! Please select only one")
        elif cmds.objectType(cmds.listRelatives(selectedCtrls[0], children=True)[0]) == "nurbsCurve":
            receivedCtrl = selectedCtrls[0]
            receivedValidCtrl = True
        else:
            cmds.warning("Something went wrong, make sure you selected just one curve")
        
        # If pVector
        if buttonName is "pVector" and receivedValidCtrl == True:
            settings["customPoleVectorCtrl"] = receivedCtrl
            cmds.button(pVectorStatus, l=receivedCtrl,e=True, bgc=(.6, .8, .6), w=130, c=lambda x:ifExistsSelect(settings.get("customPoleVectorCtrl")))
        elif buttonName is "pVector":
            cmds.button(pVectorStatus, l ="Failed to Load",e=True, bgc=(1, .4, .4), w=130,c="cmds.headsUpMessage( 'Make sure you select only one curve and try again', verticalOffset=150 , time=5.0)")
        # If ikCtrl
        if buttonName is "ikCtrl" and receivedValidCtrl == True:
            settings["customIKCtrlName"] = receivedCtrl
            cmds.button(ikCtrlStatus, l=receivedCtrl,e=True, bgc=(.6, .8, .6), w=130, c=lambda x:ifExistsSelect(settings.get("customIKCtrlName")))
        elif buttonName is "ikCtrl":
            cmds.button(ikCtrlStatus, l ="Failed to Load",e=True, bgc=(1, .4, .4), w=130,c="cmds.headsUpMessage( 'Make sure you select only one curve and try again', verticalOffset=150 , time=5.0)")
        # If ikSwitch
        if buttonName is "ikSwitch" and receivedValidCtrl == True:
            settings["customIKFKSwitchName"] = receivedCtrl
            cmds.button(ikSwitchStatus, l=receivedCtrl,e=True, bgc=(.6, .8, .6), w=130, c=lambda x:ifExistsSelect(settings.get("customIKFKSwitchName")))
        elif buttonName is "ikSwitch":
            cmds.button(ikSwitchStatus, l ="Failed to Load",e=True, bgc=(1, .4, .4), w=130,c="cmds.headsUpMessage( 'Make sure you select only one curve and try again', verticalOffset=150 , time=5.0)")

    # Joints Loader @@@@@@@@@@@@
    def updateLoadButtonJnt(buttonName):
        
        # Check If Selection is Valid
        receivedValidJnt = False
        selectedJoints = cmds.ls(selection=True, type='joint')
        if len(selectedJoints) == 0:
            cmds.warning("First element in your selection wasn't a joint")
        elif len(selectedJoints) > 1:
            cmds.warning("You selected more than one joint! Please select only one")
        elif cmds.objectType(selectedJoints[0]) == "joint":
            joint = selectedJoints[0]
            receivedValidJnt = True
        else:
            cmds.warning("Something went wrong, make sure you selected just one joint")
            
        # If Hip
        if buttonName is "hip" and receivedValidJnt == True:
            storedJoints["hipJnt"] = joint
            cmds.button(hipStatus, l =joint,e=True, bgc=(.6, .8, .6), w=130, c=lambda x:ifExistsSelect(storedJoints.get("hipJnt")))
        elif buttonName is "hip":
            cmds.button(hipStatus, l ="Failed to Load",e=True, bgc=(1, .4, .4), w=130,c="cmds.headsUpMessage( 'Make sure you select only one joint and try again', verticalOffset=150 , time=5.0)")
        
        # If Ankle
        if buttonName is "ankle" and receivedValidJnt == True:
            storedJoints["ankleJnt"] = joint
            cmds.button(ankleStatus, l =joint,e=True, bgc=(.6, .8, .6), w=130, c=lambda x:ifExistsSelect(storedJoints.get("ankleJnt")))
        elif buttonName is "ankle":
            cmds.button(ankleStatus, l ="Failed to Load",e=True, bgc=(1, .4, .4), w=130,c="cmds.headsUpMessage( 'Make sure you select only one joint and try again', verticalOffset=150 , time=5.0)")
        
        # If Ball
        if buttonName is "ball" and receivedValidJnt == True:
            storedJoints["ballJnt"] = joint
            cmds.button(ballStatus, l =joint,e=True, bgc=(.6, .8, .6), w=130, c=lambda x:ifExistsSelect(storedJoints.get("ballJnt")))
        elif buttonName is "ball":
            cmds.button(ballStatus, l ="Failed to Load",e=True, bgc=(1, .4, .4), w=130,c="cmds.headsUpMessage( 'Make sure you select only one joint and try again', verticalOffset=150 , time=5.0)")


    cmds.showWindow(ikLegMainDialog)
    # Update Everything
    isBallEnabled(settings.get("useBallJntDef"))
    isCustomIKCtrlEnabled(settings.get("useIKCtrlDef"))
    isCustomIKSwitchEnabled(settings.get("useIKSwitchDef"))
    isCustomPVectorEnabled(settings.get("usePVectorDef"))
    # mainDialog Ends Here =================================================================================


#Checks if loaded elements are still valid before running script (in case the user changed it after loading)
def checkBeforeRunning(isUsingBall):
    isValid = True
    errorMessage = '    Please reload missing elements.    Missing: '

    if cmds.objExists(storedJoints.get("hipJnt")) == False: # Hip
        isValid = False
        errorMessage = errorMessage + 'hip joint, '
    if cmds.objExists(storedJoints.get("ankleJnt")) == False: # Ankle
        isValid = False
        errorMessage = errorMessage + 'ankle joint, '

        
    if cmds.objExists(storedJoints.get("hipJnt")) and len(cmds.listRelatives(storedJoints.get("hipJnt"), type='joint') or []) > 0: # Check knee exists
        if cmds.objExists(storedJoints.get("ankleJnt")):
            if cmds.listRelatives(storedJoints.get("hipJnt"), type='joint')[0] == storedJoints.get("ankleJnt"):
                isValid = False
                errorMessage = errorMessage + 'knee joint, '

    if isUsingBall:
        if cmds.objExists(storedJoints.get("ballJnt")) == False: # Ball
            isValid = False
            errorMessage = errorMessage + 'ball joint, '
        if cmds.objExists(storedJoints.get("ballJnt")) == True and len(cmds.listRelatives(storedJoints.get("ballJnt"), type='joint') or []) == 0: # Check if ball has children
            isValid = False
            errorMessage = errorMessage + 'toe joint, '  
    
    #Check curves here
    if settings.get("usingCustomPoleVectorCtrl"):
        if cmds.objExists(settings.get("customPoleVectorCtrl")) == False:
            isValid = False
            errorMessage = errorMessage + 'pole vector ctrl, '
            
    if settings.get("usingCustomIKCtrl"):
        if cmds.objExists(settings.get("customIKCtrlName")) == False:
            isValid = False
            errorMessage = errorMessage + 'custom IK ctrl, '
            
    if settings.get("usingCustomIKFKSwitch"):
        if cmds.objExists(settings.get("customIKFKSwitchName")) == False:
            isValid = False
            errorMessage = errorMessage + 'custom IK switch ctrl, '
            
    if settings.get("usingCustomIKFKSwitch"):
        if cmds.objExists(settings.get("customIKFKSwitchName")) == False:
            isValid = False
            errorMessage = errorMessage + 'custom IK switch ctrl, '
            
        
    if isValid:
        generateIkLeg(isUsingBall)
    else:
        cmds.warning(errorMessage[:-2] + ".")



# Main Function - Generates Legs
def generateIkLeg(isUsingBall):
    ikJnts = [] # For changing its color later
    jntTagLength = len(settings.get('jntTag'))
    # ============================= Start of Main Function =============================
    hipJnt_startRP_FK = storedJoints.get("hipJnt") # Hip
    if len(cmds.listRelatives(hipJnt_startRP_FK, type='joint') or []) > 0: # Check if hip has children
        kneeJnt_middleRP_FK = cmds.listRelatives(hipJnt_startRP_FK, type='joint')[0] # Knee
    ankleJnt_endRP_FK = storedJoints.get("ankleJnt") # Ankle
    
    if isUsingBall: 
        ballJnt_endSC1_FK = storedJoints.get("ballJnt") # Ball
        if len(cmds.listRelatives(ballJnt_endSC1_FK, type='joint') or []) > 0: # Check if ball has children
            toeJnt_endSC2_FK = cmds.listRelatives(ballJnt_endSC1_FK, type='joint')[0] # Toe

    # Creates IK Skeleton
    startJoint_RP_IK = cmds.duplicate(hipJnt_startRP_FK, po=True, name = hipJnt_startRP_FK[:-jntTagLength] + "_IK_Jnt") # Create IK Hip
    middleJoint_RP_IK = cmds.duplicate(kneeJnt_middleRP_FK, po=True, name = kneeJnt_middleRP_FK[:-jntTagLength] + "_IK_Jnt") # Create IK Knee
    endJoint_RP_IK = cmds.duplicate(ankleJnt_endRP_FK, po=True, name = ankleJnt_endRP_FK[:-jntTagLength] + "_IK_Jnt") # Create IK Ankle
    ikJnts.append(startJoint_RP_IK)
    ikJnts.append(middleJoint_RP_IK)
    ikJnts.append(endJoint_RP_IK)
    
    if isUsingBall: 
        endJoint_SC1_IK = cmds.duplicate(ballJnt_endSC1_FK, po=True, name = ballJnt_endSC1_FK[:-jntTagLength] + "_IK_Jnt") # Create IK Ball
        endJoint_SC2_IK = cmds.duplicate(toeJnt_endSC2_FK, po=True, name = ballJnt_endSC1_FK[:-jntTagLength] + "_IK_Jnt") # Create IK Toe
        ikJnts.append(endJoint_SC1_IK)
        ikJnts.append(endJoint_SC2_IK)

    # Recreate Hierarchy (IK Skeleton)
    if len(cmds.listRelatives(startJoint_RP_IK, parent=True) or []) != 0:  # Check if parent is already world
        cmds.parent( startJoint_RP_IK, world=True)
    cmds.parent( middleJoint_RP_IK, startJoint_RP_IK )
    cmds.parent( endJoint_RP_IK, middleJoint_RP_IK )
    
    if isUsingBall: 
        cmds.parent( endJoint_SC1_IK, endJoint_RP_IK )
        cmds.parent( endJoint_SC2_IK, endJoint_SC1_IK )

    # Parent Constraints
    startJoint_RP_IK_pConstraint = cmds.parentConstraint( startJoint_RP_IK, hipJnt_startRP_FK )
    middleJoint_RP_IK_pConstraint = cmds.parentConstraint( middleJoint_RP_IK, kneeJnt_middleRP_FK )
    endJoint_RP_IK_pConstraint = cmds.parentConstraint( endJoint_RP_IK, ankleJnt_endRP_FK )
    if isUsingBall: 
        endJoint_SC1_IK_pConstraint = cmds.parentConstraint( endJoint_SC1_IK, ballJnt_endSC1_FK )

    # Create Main Rotate-Plane IK Solver
    ikHandleName = startJoint_RP_IK[0][:-jntTagLength] + 'RP_ikHandle'
    ikHandle_RP = cmds.ikHandle( n=ikHandleName, sj=startJoint_RP_IK[0], ee=endJoint_RP_IK[0], sol='ikRPsolver')

    # Create Ankle to Ball Single-Chain IK Solver
    if isUsingBall: 
        ikHandleName = endJoint_RP_IK[0][:-jntTagLength] + 'SC_ikHandle'
        ikHandle_SC_ball = cmds.ikHandle( n=ikHandleName, sj=endJoint_RP_IK[0], ee=endJoint_SC1_IK[0], sol='ikSCsolver')
        ikHandleName = endJoint_SC2_IK[0][:-4] + 'SC_ikHandle'
        ikHandle_SC_toe = cmds.ikHandle( n=ikHandleName, sj=endJoint_SC1_IK[0], ee=endJoint_SC2_IK[0], sol='ikSCsolver')
        

    if settings.get("usingCustomIKCtrl"):
        ikControl = settings.get("customIKCtrlName")
    else:
        ikControl = cmds.curve(name = startJoint_RP_IK[0][:-jntTagLength] + 'Ctrl', p=[[-0.569, 0.569, -0.569], [-0.569, 0.569, 0.569], \
                    [0.569, 0.569, 0.569], [0.569, 0.569, -0.569], [-0.569, 0.569, -0.569], [-0.569, -0.569, -0.569], \
                    [0.569, -0.569, -0.569], [0.569, 0.569, -0.569], [0.569, 0.569, 0.569], [0.569, -0.569, 0.569], \
                    [0.569, -0.569, -0.569], [-0.569, -0.569, -0.569], [-0.569, -0.569, 0.569], [0.569, -0.569, 0.569], \
                    [0.569, 0.569, 0.569], [-0.569, 0.569, 0.569], [-0.569, -0.569, 0.569]],d=1) # Creates Cube
                    
        ikCtrlGrp = cmds.group(name=(ikControl+'Grp'))
        placementConstraint = cmds.pointConstraint(endJoint_RP_IK,ikCtrlGrp)
        cmds.delete(placementConstraint)

    # Constraint IK Handles to IK Control
    cmds.parentConstraint(ikControl, ikHandle_RP[0], maintainOffset=True)
    if isUsingBall: 
        cmds.parentConstraint(ikControl, ikHandle_SC_ball[0], maintainOffset=True)
        cmds.parentConstraint(ikControl, ikHandle_SC_toe[0], maintainOffset=True)

    if settings.get("usingCustomPoleVectorCtrl"):
        poleVector = settings.get("customPoleVectorCtrl")
    else:
        poleVector = cmds.curve(name= ikControl[:-4] + 'poleVectorCtrl', p=[[0.268, 0.268, 0.0], [0.535, 0.268, 0.0], [0.535, -0.268, -0.0], [0.268, -0.268, -0.0], [0.268, -0.535, -0.0], [-0.268, -0.535, -0.0], [-0.268, -0.268, -0.0], [-0.535, -0.268, -0.0], [-0.535, 0.268, 0.0], [-0.268, 0.268, 0.0], [-0.268, 0.535, 0.0], [0.268, 0.535, 0.0], [0.268, 0.268, 0.0]],d=1)
        poleVectorCtrlGrp = cmds.group(name=(poleVector +'Grp'))
        
        placementConstraint = cmds.pointConstraint(middleJoint_RP_IK,poleVectorCtrlGrp)
        cmds.delete(placementConstraint)
        
        # hipOrientation = cmds.getAttr((hipJnt_startRP_FK + '.jointOrient')) # Check orientation to determine direction group should be positioned
        # totalOrient = (abs(hipOrientation[0][0]) + abs(hipOrientation[0][1]) + abs(hipOrientation[0][2]))
        # if totalOrient > 150: # Back
        #     print("First")#poleVectorCtrlGrp
        # elif totalOrient < 150: # Front
        #     print("Second")
        
    cmds.poleVectorConstraint( poleVector, ikHandle_RP[0] ) # Investigate here why weird grouping is happening

    #Check if exists (use checker before running)
    if settings.get("usingCustomIKFKSwitch"):
        ikSwitchCtrl = settings.get("customIKFKSwitchName")
    else:
        ikSwitchCtrlBeforeNaming = create_fkikSwitch()
        ikSwitchCtrl = cmds.rename(ikSwitchCtrlBeforeNaming,"switch_ikfkCtrl")
        cmds.setAttr(ikSwitchCtrl + ".overrideEnabled", 1)
        cmds.setAttr(ikSwitchCtrl + ".overrideColor", 17) #Yellow 
                         
    cmds.addAttr(ikSwitchCtrl, niceName='IK FK Switch', longName='ikSwitch', attributeType='bool', defaultValue = 1, keyable = True )
    cmds.addAttr(ikSwitchCtrl, niceName='IK FK Influence', longName='ikInfluence', attributeType='double', defaultValue = 1, keyable = True )
    lockHideAttr(ikSwitchCtrl, ['tx','ty','tz','rx','ry','rz', 'sx','sy','sz','v'],True,False)
    ikSwitchCtrlGrp = cmds.group(name=(ikSwitchCtrl+'Grp'))

    reverseNode = cmds.createNode('reverse')
    cmds.connectAttr('%s.ikSwitch' % ikSwitchCtrl, '%s.inputX' % reverseNode)

    ctrlName = hipJnt_startRP_FK[:-jntTagLength] + settings.get("ctrlGrpTag")
    if cmds.objExists(ctrlName):
        cmds.connectAttr('%s.outputX' % reverseNode, '%s.v' % ctrlName)
        
    ctrlName = kneeJnt_middleRP_FK[:-jntTagLength] + settings.get("ctrlGrpTag")
    if cmds.objExists(ctrlName):
        cmds.connectAttr('%s.outputX' % reverseNode, '%s.v' % ctrlName)
      
    ctrlName = ankleJnt_endRP_FK[:-jntTagLength] + settings.get("ctrlGrpTag")
    if cmds.objExists(ctrlName):
        cmds.connectAttr('%s.outputX' % reverseNode, '%s.v' % ctrlName)  
    
    if isUsingBall: 
        ctrlName = ballJnt_endSC1_FK[:-jntTagLength] + settings.get("ctrlGrpTag")
        if cmds.objExists(ctrlName):
            cmds.connectAttr('%s.outputX' % reverseNode, '%s.v' % ctrlName)
        
    cmds.connectAttr('%s.ikSwitch' % ikSwitchCtrl, '%s.v' % ikControl)
    cmds.connectAttr('%s.ikSwitch' % ikSwitchCtrl, '%s.v' % poleVector)
    
    # Main Ctrl IK Influence
    # Creates Condition (IK Switch is one) > 
    # Reverse goes to FK weight, true data is passed to IK Weight

    conditionNode = cmds.createNode('condition')
    cmds.setAttr(conditionNode + '.secondTerm', 1)
    cmds.setAttr(conditionNode + '.colorIfFalseR', 0)
    cmds.setAttr(conditionNode + '.colorIfFalseG', 0)
    cmds.setAttr(conditionNode + '.colorIfFalseB', 0)
    cmds.connectAttr('%s.ikSwitch' % ikSwitchCtrl, '%s.firstTerm' % conditionNode)
    cmds.connectAttr('%s.ikInfluence' % ikSwitchCtrl, '%s.colorIfTrueR' % conditionNode)

    startJoint_RP_IK_pConstraint_LWN = getLastWeightNumber(startJoint_RP_IK_pConstraint[0])
    middleJoint_RP_IK_pConstraint_LWN = getLastWeightNumber(middleJoint_RP_IK_pConstraint[0])
    endJoint_RP_IK_pConstraint_LWN = getLastWeightNumber(endJoint_RP_IK_pConstraint[0])
    if isUsingBall: 
        endJoint_SC1_IK_pConstraint_LWN = getLastWeightNumber(endJoint_SC1_IK_pConstraint[0])

    cmds.connectAttr('%s.outColorR' % conditionNode, startJoint_RP_IK_pConstraint[0] + '.' + startJoint_RP_IK[0] + "W" + startJoint_RP_IK_pConstraint_LWN)
    cmds.connectAttr('%s.outColorR' % conditionNode, middleJoint_RP_IK_pConstraint[0] + '.' + middleJoint_RP_IK[0] + "W" + middleJoint_RP_IK_pConstraint_LWN)
    cmds.connectAttr('%s.outColorR' % conditionNode, endJoint_RP_IK_pConstraint[0] + '.' + endJoint_RP_IK[0] + "W" + endJoint_RP_IK_pConstraint_LWN)
    if isUsingBall: 
        cmds.connectAttr('%s.outColorR' % conditionNode, endJoint_SC1_IK_pConstraint[0] + '.' + endJoint_SC1_IK[0] + "W" + endJoint_SC1_IK_pConstraint_LWN)

    reverseConditionNode = cmds.createNode('reverse')
    cmds.connectAttr('%s.outColorR' % conditionNode, '%s.inputX' % reverseConditionNode)
    
    #Connects constraint weights to reverse node
    def connectNonIKWeights(constraintName, nonIKWeightList):
        for obj in nonIKWeightList:
            cmds.connectAttr('%s.outputX' % reverseConditionNode, constraintName + '.' + obj)
            
    connectNonIKWeights(startJoint_RP_IK_pConstraint[0],getAllWeightsButNotLast(startJoint_RP_IK_pConstraint[0]))
    connectNonIKWeights(middleJoint_RP_IK_pConstraint[0],getAllWeightsButNotLast(middleJoint_RP_IK_pConstraint[0]))
    connectNonIKWeights(endJoint_RP_IK_pConstraint[0],getAllWeightsButNotLast(endJoint_RP_IK_pConstraint[0]))
    if isUsingBall: 
        connectNonIKWeights(endJoint_SC1_IK_pConstraint[0],getAllWeightsButNotLast(endJoint_SC1_IK_pConstraint[0]))

    # Colorize Control Start ------------------
    if settings.get("usingColorizeCtrls"):
        controls = [ikControl, poleVector]
        for ctrl in controls:
            if True == True:
                        cmds.setAttr(ctrl + ".overrideEnabled", 1)
                        if 'right_' in ctrl:
                            cmds.setAttr(ctrl + ".overrideColor", 13) #Red
                        elif 'left_' in ctrl:
                            cmds.setAttr(ctrl + ".overrideColor", 6) #Blue
                        else:
                            cmds.setAttr(ctrl + ".overrideColor", 17) #Yellow                                
                            
    # Create setup grp
    mainIKGrpName = hipJnt_startRP_FK.replace("Jnt","")
    mainIKGrp = cmds.group(name=mainIKGrpName + "_IK_Setup_grp",em=True)
    cmds.parent(startJoint_RP_IK, mainIKGrp) # Parent to Setup Grp (IK Skeleton)
    solversIKGrp = cmds.group(name="solvers_grp",em=True)
    # Parent to Setup Grp (Solvers)
    if isUsingBall: 
        cmds.parent(ikHandle_SC_ball[0], solversIKGrp)
        cmds.parent(ikHandle_SC_toe[0], solversIKGrp)
        
    cmds.parent(ikHandle_RP[0], solversIKGrp) # Parent to Setup Grp (Solvers)
    cmds.parent(solversIKGrp, mainIKGrp) # Parent to Setup Grp (Solvers)
    
    ctrlsIKGrp = cmds.group(name="controls_grp",em=True)
    generatedCtrls = [ikSwitchCtrlGrp,poleVectorCtrlGrp,ikCtrlGrp]
    for ctrl in generatedCtrls:
        if cmds.objExists(ctrl):
            cmds.parent(ctrl, ctrlsIKGrp)
    cmds.parent(ctrlsIKGrp, mainIKGrp)
    
    ctrlsChildren = cmds.listRelatives(ctrlsIKGrp, c=True) 
    if ctrlsChildren == None:
        cmds.delete(ctrlsIKGrp)
    
    # Add some color to the new outliner elements
    changeOutlinerColor(mainIKGrp,[0.240,1,0.062])
    changeOutlinerColor(solversIKGrp,[1,1,0.126])
    changeOutlinerColor(ctrlsIKGrp,[1,0.479,0.172])
    for jnt in ikJnts:
        changeOutlinerColor(jnt[0],[0.763,0.332,0.892])

    # If not using Ball, make IK control rotate ankle
    if isUsingBall == False: 
        cmds.orientConstraint(ikControl,endJoint_RP_IK)
        
    # Make leg stretchy
    if settings.get('makeStretchy'):
        cmds.select(ikHandle_RP)
        ikHandle = cmds.ls(selection=True, type="ikHandle")
        stretchyGrp = makeStretchyLegs(ikHandle)
        cmds.parent(stretchyGrp, mainIKGrp)
        changeOutlinerColor(stretchyGrp,[1,0,0])
        cmds.setAttr(stretchyGrp + ".v", 0) #Make it invisible
        
    cmds.select(ikControl)

    # ============================= End of Main Function =============================


def ikLegGeneratorHelpMenuDialog():
    if cmds.window("helpMenuDialog", exists =True):
        cmds.deleteUI("helpMenuDialog")    

    # Help Dialog Start Here =================================================================================
    
    # Build About UI
    helpMenuDialog = cmds.window("helpMenuDialog", title="GT - IK Leg Generator - Help",\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =True)
    columnMain = cmds.columnLayout() 

    form = cmds.formLayout(p=columnMain)

    contentMain = cmds.columnLayout(adj = True)

    cmds.text("")
    cmds.text("Help for GT IK Leg Generator", bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.text("  ")
    cmds.text(" Version Installed: " + scriptVersion)
    cmds.text("  ")
    cmds.text("     This script allows you to generate a simple       ")
    cmds.text('     IK leg by automating by automating the many steps  ')
    cmds.text('     involved in creating it  ')
    cmds.text(' ')
    cmds.text('     This script assumes that you are using a simple leg  ')
    cmds.text('     composed of a hip joint, a knee joint an ankle joint  ')
    cmds.text('     and maybe ball and toe joints.     ')
    cmds.text('     In case your setup is different, I suggest you try    ')
    cmds.text('     a different solution.    ')
    cmds.text(' ')
    cmds.text('     Joint Tag (Suffix) and Ctrl Group Tag (Suffix):    ')
    cmds.text('     These two textfields allow you to define what tag you ')
    cmds.text('     used for you base skeleton joints and your control groups.')
    cmds.text(' ', h=2)
    cmds.text('     It will use the length of your joint tag to define how many')
    cmds.text('     letters to remove from the end (suffix) of the joint name.')
    cmds.text('     (used when creating new names or looking for controls)')
    cmds.text(' ', h=2)
    cmds.text('     The Ctrl Group Tag is used to define the visibility of the')
    cmds.text('     FK system.')
    cmds.text(' ')
    cmds.text('     Custom PVector Ctrl, IK Ctrl and IK Switch:')
    cmds.text('     These options allow you to load an already existing control.')
    cmds.text('     In case you already created fancy curve')
    cmds.text('     you could simple load it')
    cmds.text('     and the script will use yours instead of creating a new one')
    cmds.text(' ')
    cmds.text('     Colorize Controls:   ')
    cmds.text('     This option looks for "right_" and "left_" tags')
    cmds.text('     and assign colors based on the found tag')
    cmds.text(' ')
    cmds.text("     Make Stretchy Legs:   ")
    cmds.text('     This option creates measure tools to define how to')
    cmds.text('     strechy the leg when it goes beyong its current size.')
    cmds.text('     Term = What is being compared    ')
    cmds.text('     Condition = Default Size (used for scalling the rig)')
    cmds.text(' ')
    cmds.text("     Use Ball Joint:   ")
    cmds.text('     This option allows you to define whether or not to use')
    cmds.text('     a ball joint')
    cmds.text(' ')
    cmds.text("     Load \"Content\" Buttons:  ")
    cmds.text('     These buttons allow you to load the necessary')
    cmds.text('      objects before running the script.')
    cmds.text(' ')
    cmds.text('     Generate Button:    ')
    cmds.text('     Runs the script. Generate an IK leg using loaded objects')
    cmds.text(' ', w=400)

    emailContainer = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 25)
    
    cmds.text('                            Guilherme Trevisan : ')
    cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1,1,1], p=emailContainer)
    websiteContainer = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 25)
    cmds.text('                                    Visit my ')
    cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1,1,1], p=websiteContainer)
    cmds.text(' for updated versions')
    cmds.text(' ', p= contentMain)
    cmds.separator(h=15, p=contentMain)
    
    cmds.button(l ="Ok", p= contentMain, c=lambda x:closeAboutWindow())
                                                                                                                              
    def closeAboutWindow():
        if cmds.window("helpMenuDialog", exists =True):
            cmds.deleteUI("helpMenuDialog")  
        
    cmds.showWindow(helpMenuDialog)
    
    # Help Dialog Ends Here =================================================================================


# Locks an hides attributes
def lockHideAttr(obj,attrArray,lock,hide):
        for a in attrArray:
            cmds.setAttr(obj + '.' + a, k=hide,l=lock)

# Returns a list of weights with the exception of the last weight
def getAllWeightsButNotLast(parentConstraint):
    if cmds.objExists(parentConstraint) and cmds.objectType(parentConstraint) in 'parentConstraint':
        constraintWeights = cmds.parentConstraint(parentConstraint,q=True, wal=True)
        weightsExceptLast = []
        for obj in constraintWeights:
            if constraintWeights[-1] not in obj:
                weightsExceptLast.append(obj)
        return weightsExceptLast
        

# Returns the last weight in a parentConstraint
def getLastWeightNumber(parentConstraint):
    if cmds.objExists(parentConstraint) and cmds.objectType(parentConstraint) in 'parentConstraint':
        lastWeight = cmds.parentConstraint(parentConstraint,q=True, wal=True)[-1]
        return lastWeight.split("W")[-1] # lastWeightNumber


# If object exists, select it
def ifExistsSelect(obj):
    if cmds.objExists(obj):
        cmds.select(obj)
        cmds.headsUpMessage(obj + " selected", verticalOffset=150 )
    else:
        cmds.warning("Object doesn't exist! Did you delete or rename it after loading?")
        
# To quickly create nurbs texts    
def create_text(text):
    cmds.textCurves(ch=0, t=text)
    print(text)
    cmds.ungroup()
    cmds.ungroup()
    curves = cmds.ls(sl=True)
    cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)
    shapes = curves[1:]
    cmds.select(shapes, r=True)
    cmds.pickWalk(d='Down')
    cmds.select(curves[0], tgl=True)
    cmds.parent(r=True, s=True)
    cmds.pickWalk(d='up')
    cmds.delete(shapes)
    cmds.xform(cp=True)
    return cmds.ls(sl=True)[0]

# Quickly create FK IK Switch
def create_fkikSwitch():    
    fkikCurves = create_text("FK/IK")
    switchCurves = create_text("SWITCH")
    cmds.scale(0.679,0.679,0.679, switchCurves)
    cmds.move(-0.6,-0.9,0, switchCurves)
    cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)
    switchShapes = cmds.listRelatives(ad=True)
    for shape in switchShapes:
        cmds.parent(shape,fkikCurves, r=True, s=True)
    cmds.delete(switchCurves)
    cmds.pickWalk(d='up')
    cmds.xform(os=True, t=[-1.2,0,0],ro=[-90,0,0], ztp=True)
    cmds.xform(cp=1)
    cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0)
    return cmds.ls(sl=True)
    
# Changes outliner color if obj exists
def changeOutlinerColor(obj,colorRGB):    
    if cmds.objExists(obj):
        cmds.setAttr ( obj + ".useOutlinerColor" , True)
        cmds.setAttr ( obj  + ".outlinerColor" , colorRGB[0],colorRGB[1], colorRGB[2])

# Change the outliner color of a list
def changeListOutlinerColor(objList, colorRGB):
    for obj in objList:
        if cmds.objExists(obj):
            cmds.setAttr ( obj + ".useOutlinerColor" , True)
            cmds.setAttr ( obj + ".outlinerColor" , colorRGB[0],colorRGB[1],colorRGB[2])

# Make Stretchy Legs
def makeStretchyLegs(ikHandle):
    ikHandleManipulatedJoints = cmds.ikHandle(ikHandle, q=True, jointList=True)

    topJointPosition = cmds.getAttr(ikHandleManipulatedJoints[0] + '.translate')
    ikHandlePosition = cmds.getAttr(ikHandle[0] + '.translate')

    distanceOne = cmds.distanceDimension(sp=topJointPosition[0], ep=ikHandlePosition[0] )
    distanceOneTransform = cmds.listRelatives(distanceOne, parent=True)[0]
    distanceOneLocators = cmds.listConnections(distanceOne)

    #Rename Distance One Nodes
    nameTopLocator = (ikHandleManipulatedJoints[0].replace("_IK_", "")).replace("Jnt","") # Change this, use a textbox to query user
    nameBottomLocator = ((ikHandle[0].replace("_IK_","")).replace("_ikHandle","")).replace("RP","")
    nameDistanceNode = nameBottomLocator
    distanceNodeOne = cmds.rename(distanceOneTransform, nameDistanceNode + "_strechyTerm_01")
    topLocatorOne = cmds.rename(distanceOneLocators[0], nameTopLocator + "_ST_01")
    bottomLocatorOne = cmds.rename(distanceOneLocators[1], nameBottomLocator + "_ST_02")

    distanceTwo = cmds.distanceDimension(sp=(0,0,0), ep=(1,1,1) )

    distanceTwoTransform = cmds.listRelatives(distanceTwo, parent=True)[0]
    distanceTwoLocators = cmds.listConnections(distanceTwo)
    cmds.xform(distanceTwoLocators[0], t=topJointPosition[0] )
    cmds.xform(distanceTwoLocators[1], t=ikHandlePosition[0] )

    #Rename Distance Two Nodes
    distanceNodeTwo = cmds.rename(distanceTwoTransform, nameDistanceNode + "_strechyCondition_01")
    topLocatorTwo = cmds.rename(distanceTwoLocators[0], nameTopLocator + "_SC_01")
    bottomLocatorTwo = cmds.rename(distanceTwoLocators[1], nameBottomLocator + "_SC_02")

    stretchyGrp = cmds.group(name="stretchySystem_grp", empty=True, world=True)
    cmds.parent( distanceNodeOne, stretchyGrp )
    cmds.parent( topLocatorOne, stretchyGrp )
    cmds.parent( bottomLocatorOne, stretchyGrp )
    cmds.parent( distanceNodeTwo, stretchyGrp )
    cmds.parent( topLocatorTwo, stretchyGrp )
    cmds.parent( bottomLocatorTwo, stretchyGrp )

    changeListOutlinerColor([distanceNodeOne,topLocatorOne,bottomLocatorOne],[0,1,0]) 
    changeListOutlinerColor([distanceNodeTwo,topLocatorTwo,bottomLocatorTwo],[1,0,0])

    mel.eval('AEdagNodeCommonRefreshOutliners();') #Make sure outliner colors update

    # Start connecting everything ----------------------------------------

    stretchNormalizationNode = cmds.createNode('multiplyDivide', name=nameDistanceNode + "_distNormalization_divide")
    cmds.connectAttr('%s.distance' % distanceNodeOne, '%s.input1X' % stretchNormalizationNode)
    cmds.connectAttr('%s.distance' % distanceNodeTwo, '%s.input2X' % stretchNormalizationNode) # Check if necessary

    cmds.setAttr( stretchNormalizationNode + ".operation", 2)

    stretchConditionNode = cmds.createNode('condition', name=nameDistanceNode + "_strechyCondition_condition")
    cmds.setAttr( stretchConditionNode + ".operation", 3)
    cmds.connectAttr('%s.distance' % distanceNodeOne, '%s.firstTerm' % stretchConditionNode)
    cmds.connectAttr('%s.distance' % distanceNodeTwo, '%s.secondTerm' % stretchConditionNode)
    cmds.connectAttr('%s.outputX' % stretchNormalizationNode, '%s.colorIfTrueR' % stretchConditionNode)

    cmds.connectAttr('%s.outColorR' % stretchConditionNode, '%s.scaleX' % ikHandleManipulatedJoints[0])
    cmds.connectAttr('%s.outColorR' % stretchConditionNode, '%s.scaleX' % ikHandleManipulatedJoints[1])


    cmds.pointConstraint (ikHandleManipulatedJoints[0], topLocatorOne)
    cmds.pointConstraint (ikHandleManipulatedJoints[0], topLocatorTwo)

    try:
        ikHandleParentConstraint = cmds.listRelatives(ikHandle, children=True,type='parentConstraint' )[0]
        ikHandleCtrl = cmds.parentConstraint(ikHandleParentConstraint, q=True, targetList=True)
        cmds.parentConstraint (ikHandleCtrl, bottomLocatorOne)
    except:
        pass
    
    return stretchyGrp

def parseTextField(textFieldData):
    textFieldDataNoSpaces = textFieldData.replace(" ", "")
    if len(textFieldDataNoSpaces) <= 0:
        return []
    else:
        returnList = textFieldDataNoSpaces.split(",")
        emptyObjects = []
        for obj in returnList:
            if '' == obj:
                emptyObjects.append(obj)
        for obj in emptyObjects:
            returnList.remove(obj)
        return returnList


# Start current "Main"
ikLegMainDialog()