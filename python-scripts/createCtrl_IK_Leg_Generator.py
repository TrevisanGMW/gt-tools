import maya.cmds as cmds
from decimal import *

# IK Leg Generator 
# @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-01-06
# Last update - 2020-01-14
# To do:
# Update auto generated curves
# Add "Make Stretchy Legs" function
# Test it further


# Version:
scriptVersion = "v0.8a"


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
             'makeStretchy' : False,
             'ctrlGrpTag' : 'CtrlGrp',
             'ctrlTag' : 'Ctrl', # Not yet used # Add text boxes for these
             'jntTag' : 'Jnt' #not yet used, grab legth or replace?
            }


# Main Form ============================================================================
def ikLegMainDialog():
    if cmds.window("ikLegMainDialog", exists =True):
        cmds.deleteUI("ikLegMainDialog")    

    # mainDialog Start Here =================================================================================

    ikLegMainDialog = cmds.window("ikLegMainDialog", title="IK Leg - " + scriptVersion,\
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
    checkBoxGrpThree = cmds.checkBoxGrp(en1=False,p=interactiveContainerJnt, columnWidth2=[130, 1], numberOfCheckBoxes=2, \
                                label1 = 'Make Stretchy Legs ', label2 = "Use Ball Joint", v1 = settings.get("makeStretchy"), v2 = settings.get("useBallJntDef"), \
                                on2=lambda x:isBallEnabled(True),  of2=lambda x:isBallEnabled(False) )   
                            
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
    #isBallEnabled(settings.get("useBallJntDef"))  # Uncomment after done
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
        if len(cmds.listRelatives(storedJoints.get("ballJnt"), type='joint') or []) == 0: # Check if ball has children
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
    # ============================= Start of Main Function =============================
    hipJnt_startRP_FK = storedJoints.get("hipJnt") # Hip
    if len(cmds.listRelatives(hipJnt_startRP_FK, type='joint') or []) > 0: # Check if hip has children
        kneeJnt_middleRP_FK = cmds.listRelatives(hipJnt_startRP_FK, type='joint')[0] # Knee
    ankleJnt_endRP_FK = storedJoints.get("ankleJnt") # Ankle
    
    if isUsingBall: ############# Find a better solution for this
        ballJnt_endSC1_FK = storedJoints.get("ballJnt") # Ball
        if len(cmds.listRelatives(ballJnt_endSC1_FK, type='joint') or []) > 0: # Check if ball has children
            toeJnt_endSC2_FK = cmds.listRelatives(ballJnt_endSC1_FK, type='joint')[0] # Toe

    # Creates IK Skeleton
    startJoint_RP_IK = cmds.duplicate(hipJnt_startRP_FK, po=True, name = hipJnt_startRP_FK[:-3] + "_IK_Jnt") # Create IK Hip
    middleJoint_RP_IK = cmds.duplicate(kneeJnt_middleRP_FK, po=True, name = kneeJnt_middleRP_FK[:-3] + "_IK_Jnt") # Create IK Knee
    endJoint_RP_IK = cmds.duplicate(ankleJnt_endRP_FK, po=True, name = ankleJnt_endRP_FK[:-3] + "_IK_Jnt") # Create IK Ankle
    
    if isUsingBall: ############# Find a better solution for this
        endJoint_SC1_IK = cmds.duplicate(ballJnt_endSC1_FK, po=True, name = ballJnt_endSC1_FK[:-3] + "_IK_Jnt") # Create IK Ball
        endJoint_SC2_IK = cmds.duplicate(toeJnt_endSC2_FK, po=True, name = ballJnt_endSC1_FK[:-3] + "_IK_Jnt") # Create IK Toe

    # Recreate Hierarchy
    if len(cmds.listRelatives(startJoint_RP_IK, parent=True) or []) != 0:  # Check if parent is already world
        cmds.parent( startJoint_RP_IK, world=True)
    cmds.parent( middleJoint_RP_IK, startJoint_RP_IK )
    cmds.parent( endJoint_RP_IK, middleJoint_RP_IK )
    
    if isUsingBall: ############# Find a better solution for this
        cmds.parent( endJoint_SC1_IK, endJoint_RP_IK )
        cmds.parent( endJoint_SC2_IK, endJoint_SC1_IK )

    startJoint_RP_IK_pConstraint = cmds.parentConstraint( startJoint_RP_IK, hipJnt_startRP_FK )
    middleJoint_RP_IK_pConstraint = cmds.parentConstraint( middleJoint_RP_IK, kneeJnt_middleRP_FK )
    endJoint_RP_IK_pConstraint = cmds.parentConstraint( endJoint_RP_IK, ankleJnt_endRP_FK )
    if isUsingBall: ############# Find a better solution for this
        endJoint_SC1_IK_pConstraint = cmds.parentConstraint( endJoint_SC1_IK, ballJnt_endSC1_FK )

    # Create Main Rotate-Plane IK Solver
    ikHandleName = startJoint_RP_IK[0][:-3] + 'RP_ikHandle'
    ikHandle_RP = cmds.ikHandle( n=ikHandleName, sj=startJoint_RP_IK[0], ee=endJoint_RP_IK[0], sol='ikRPsolver')

    # Create Ankle to Ball Single-Chain IK Solver
    if isUsingBall: ############# Find a better solution for this
        ikHandleName = endJoint_RP_IK[0][:-3] + 'SC_ikHandle'
        ikHandle_SC_ball = cmds.ikHandle( n=ikHandleName, sj=endJoint_RP_IK[0], ee=endJoint_SC1_IK[0], sol='ikSCsolver')
        ikHandle_SC_toe = cmds.ikHandle( n=ikHandleName, sj=endJoint_SC1_IK[0], ee=endJoint_SC2_IK[0], sol='ikSCsolver')
        
    #Make so it doesn't go inside of a group - right now it goes inside the L_F_Leg_FK_IK_Switch_doeGrp


    if settings.get("usingCustomIKCtrl"):
        ikControl = settings.get("customIKCtrlName")
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
    cmds.parentConstraint(ikControl, ikHandle_RP[0], maintainOffset=True)
    if isUsingBall: ############# Find a better solution for this
        cmds.parentConstraint(ikControl, ikHandle_SC_ball[0], maintainOffset=True)
        cmds.parentConstraint(ikControl, ikHandle_SC_toe[0], maintainOffset=True)

    if settings.get("usingCustomPoleVectorCtrl"):
        poleVector = settings.get("customPoleVectorCtrl")
    else:
        poleVector = cmds.curve(name= ikControl[:-4] + 'poleVectorCtrl', p=[[0.268, 0.268, 0.0], [0.535, 0.268, 0.0], [0.535, -0.268, -0.0], [0.268, -0.268, -0.0], [0.268, -0.535, -0.0], [-0.268, -0.535, -0.0], [-0.268, -0.268, -0.0], [-0.535, -0.268, -0.0], [-0.535, 0.268, 0.0], [-0.268, 0.268, 0.0], [-0.268, 0.535, 0.0], [0.268, 0.535, 0.0], [0.268, 0.268, 0.0]],d=1)
        poleVectorCtrlGrp = cmds.group(name=(poleVector +'Grp'))
        
        placementConstraint = cmds.pointConstraint(middleJoint_RP_IK,poleVectorCtrlGrp)
        cmds.delete(placementConstraint)
        
        hipOrientation = cmds.getAttr((hipJnt_startRP_FK + '.jointOrient')) # Check orientation to determine direction group should be positioned
        totalOrient = (abs(hipOrientation[0][0]) + abs(hipOrientation[0][1]) + abs(hipOrientation[0][2]))
        if totalOrient > 150: # Back
            print("First")#poleVectorCtrlGrp
        elif totalOrient < 150: # Front
            print("Second")
        
    cmds.poleVectorConstraint( poleVector, ikHandle_RP[0] ) # Investigate here why weird grouping is happening

    #Check if exists (use checker before running)
    if settings.get("usingCustomIKFKSwitch"):
        ikSwitchCtrl = settings.get("customIKFKSwitchName")
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

    ctrlName = hipJnt_startRP_FK[:-3] + settings.get("ctrlGrpTag")
    if cmds.objExists(ctrlName):
        cmds.connectAttr('%s.outputX' % reverseNode, '%s.v' % ctrlName)
        
    ctrlName = kneeJnt_middleRP_FK[:-3] + settings.get("ctrlGrpTag")
    if cmds.objExists(ctrlName):
        cmds.connectAttr('%s.outputX' % reverseNode, '%s.v' % ctrlName)
      
    ctrlName = ankleJnt_endRP_FK[:-3] + settings.get("ctrlGrpTag")
    if cmds.objExists(ctrlName):
        cmds.connectAttr('%s.outputX' % reverseNode, '%s.v' % ctrlName)  
    
    if isUsingBall: ############# Find a better solution for this
        ctrlName = ballJnt_endSC1_FK[:-3] + settings.get("ctrlGrpTag")
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
    if isUsingBall: ############# Find a better solution for this
        endJoint_SC1_IK_pConstraint_LWN = getLastWeightNumber(endJoint_SC1_IK_pConstraint[0])

    cmds.connectAttr('%s.outColorR' % conditionNode, startJoint_RP_IK_pConstraint[0] + '.' + startJoint_RP_IK[0] + "W" + startJoint_RP_IK_pConstraint_LWN)
    cmds.connectAttr('%s.outColorR' % conditionNode, middleJoint_RP_IK_pConstraint[0] + '.' + middleJoint_RP_IK[0] + "W" + middleJoint_RP_IK_pConstraint_LWN)
    cmds.connectAttr('%s.outColorR' % conditionNode, endJoint_RP_IK_pConstraint[0] + '.' + endJoint_RP_IK[0] + "W" + endJoint_RP_IK_pConstraint_LWN)
    if isUsingBall: ############# Find a better solution for this
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
    if isUsingBall: ############# Find a better solution for this
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

    # Colorize Control End ---------------------


    # ============================= End of Main Function =============================

# Locks an hides attributes
def lockHideAttr(obj,attrArray,lock,hide):
        for a in attrArray:
            maya.cmds.setAttr(obj + '.' + a, k=hide,l=lock)

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

# Start current "Main"
ikLegMainDialog()
