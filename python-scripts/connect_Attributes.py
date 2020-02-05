import maya.cmds as cmds
from decimal import *

# Connect Attributes Script
# @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-02-04
# Last update - 2020-02-05
# To do: Finish main function

# Version:
scriptVersion = "v0.1"
 

settings = { 'targetList': [], 
             'sourceObj': [],
             'defReverseNode': False,
             'defDisconnect' : False,
             'defSingleST' : False,
             'reverseNode' : False,
             'disconnect' : False,
             'singleSourceTarget' : False
            }


# Main Form ============================================================================
def connectAttributesMainDialog():
    if cmds.window("connectAttributesMainDialog", exists =True):
        cmds.deleteUI("connectAttributesMainDialog")    

    # mainDialog Start Here =================================================================================

    connectAttributesMainDialog = cmds.window("connectAttributesMainDialog", title="connectAttr - " + scriptVersion,\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =True)

    columnMain = cmds.columnLayout() 

    form = cmds.formLayout(p=columnMain)

    contentMain = cmds.columnLayout(adj = True)

    cmds.text("")
    cmds.text("Connect Custom Attributes - " + scriptVersion, bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.text("  ")
    cmds.text("      This script creates a direct connection       ")
    cmds.text("      between source and target elements     ")
    cmds.text("   ")
    cmds.text('The Single Source/Target  ')
    cmds.text('option expects user to select  ')
    cmds.text('Source (1st) then Target (2nd)  ')
    cmds.text("   ")
    cmds.separator(h=15, p=contentMain)
    
    
    # Checkbox One
    interactiveContainerMisc = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 25)
    cmds.text("    ")
    singleSourceTarget = cmds.checkBox(p=interactiveContainerMisc, label='  Use Single Source/Target   (Selection) ', value=settings.get("defSingleST"),\
                         cc=lambda x:isUsingSingleTarget(cmds.checkBox(singleSourceTarget, query=True, value=True)) )

    cmds.separator(h=15, p=contentMain)
    # CheckboxGrp Two
    interactiveContainerJnt = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 25)
    cmds.text("    ") # Increase this to move checkboxes to the right
    checkBoxGrpThree = cmds.checkBoxGrp(p=interactiveContainerJnt, columnWidth2=[135, 1], numberOfCheckBoxes=2, \
                                label1 = '  Add Reverse Node', label2 = "Disconnect", v1 = settings.get("defReverseNode"), v2 = settings.get("defDisconnect"), \
                                on1=lambda x:isBallEnabled(True),  of1=lambda x:isBallEnabled(False),
                                on2=lambda x:isBallEnabled(True),  of2=lambda x:isBallEnabled(False) )   
                                                   
    cmds.separator(h=10, p=contentMain)
    #Source List Loader
    sourceContainer = cmds.rowColumnLayout( p=contentMain, numberOfRows=1)
    sourceBtn = cmds.button(p=sourceContainer, l ="Load Source Object", c=lambda x:updateLoadButtonJnt("source"), w=130)
    sourceStatus = cmds.button(p=sourceContainer, l ="Not loaded yet", bgc=(0, 0, 0), w=130, \
                            c="cmds.headsUpMessage( 'Select your source element and click on \"Load Source Object\"', verticalOffset=150 , time=5.0)")
                            
    #Target List Loader
    targetContainer = cmds.rowColumnLayout( p=contentMain, numberOfRows=1)
    targetBtn = cmds.button(p=targetContainer, l ="Load Target Objects", c=lambda x:updateLoadButtonJnt("target"), w=130)
    targetStatus = cmds.button(p=targetContainer, l ="Not loaded yet", bgc=(0, 0, 0), w=130, \
                            c="cmds.headsUpMessage( 'Select your target elements and click on \"Load Target Objects\"', verticalOffset=150 , time=5.0)")
                            
    bottomContainer = cmds.rowColumnLayout(p=contentMain,adj=True)
    cmds.text('Attributes:',p=bottomContainer)
    attributesInput = cmds.textField(p = bottomContainer, text="translate, rotate, scale", enterCommand=lambda x:connectAttributes())
    cmds.button(p=bottomContainer, l ="Connect Attributes", bgc=(.6, .8, .6), c=lambda x:connectAttributes())

    def isUsingSingleTarget(state): 
        if state:
            print("true")
            cmds.button(sourceBtn, e=True, en=False)
            cmds.button(sourceStatus, l ="Not necessary", e=True, en=False, bgc=(.25, .25, .25))
            cmds.button(targetBtn, e=True, en=False)
            cmds.button(targetStatus, l ="Not necessary", e=True, en=False, bgc=(.25, .25, .25))
            settings["targetList"] = []
            settings["sourceObj"] = []
        else:
            print("false")
            cmds.button(sourceBtn, e=True, en=True)
            cmds.button(sourceStatus, l ="Not loaded yet", e=True, en=True, bgc=(0, 0, 0),\
                        c="cmds.headsUpMessage( 'Select your source element and click on \"Load Source Object\"', verticalOffset=150 , time=5.0)")
            cmds.button(targetBtn, e=True, en=True)
            cmds.button(targetStatus, l ="Not loaded yet", e=True, en=True, bgc=(0, 0, 0), \
                        c="cmds.headsUpMessage( 'Select your target elements and click on \"Load Target Objects\"', verticalOffset=150 , time=5.0)")
            

    # Objects Loader
    def updateLoadButtonJnt(buttonName):
        
        # Check If Selection is Valid
        receivedValidSourceSelection = False
        receivedValidTargetSelection = False
        selectedElements = cmds.ls(selection=True)
        
        if buttonName == "source":
            if len(selectedElements) == 0:
                cmds.warning("Please make sure you select at least one object before loading")
            elif len(selectedElements) == 1:
                receivedValidSourceSelection = True
            elif len(selectedElements) > 1:
                 cmds.warning("You can only have one source object")
            else:
                cmds.warning("Something went wrong, make sure you selected all necessary elements")
                
        if buttonName == "target":
            if len(selectedElements) == 0:
                cmds.warning("Please make sure you select at least one object before loading")
            elif len(selectedElements) > 0:
                 receivedValidTargetSelection = True
            else:
                cmds.warning("Something went wrong, make sure you selected all necessary elements")
            
        # If Source
        if buttonName is "source" and receivedValidSourceSelection == True:
            settings["sourceObj"] = selectedElements[0]
            cmds.button(sourceStatus, l=selectedElements[0],e=True, bgc=(.6, .8, .6), w=130, c=lambda x:ifExistsSelect(settings.get("sourceObj")))
        elif buttonName is "source":
            cmds.button(sourceStatus, l ="Failed to Load",e=True, bgc=(1, .4, .4), w=130,\
                        c="cmds.headsUpMessage( 'Make sure you select only one source element', verticalOffset=150 , time=5.0)")
        
        # If Target
        if buttonName is "target" and receivedValidTargetSelection == True:
            settings["targetList"] = selectedElements
            
            loadedText = str(len(selectedElements)) + " objects loaded"
            if len(selectedElements) == 1:
                loadedText = selectedElements[0]

            cmds.button(targetStatus, l =loadedText,e=True, bgc=(.6, .8, .6), w=130, c=lambda x:printIfExistsInList(settings.get("targetList")))
        elif buttonName is "target":
            cmds.button(targetStatus, l ="Failed to Load",e=True, bgc=(1, .4, .4), w=130,\
                        c="cmds.headsUpMessage( 'Make sure you select at least one target element', verticalOffset=150 , time=5.0)")


    cmds.showWindow(connectAttributesMainDialog)
    # mainDialog Ends Here =================================================================================


# Main Function - Generates Legs
def connectAttributes():
    #if settings.get("targetList") == [] or settings.get("sourceObj") == 
    
    print("running")
    # cmds.connectAttr('%s.curveSystemRotation' % selection[0], '%s.input2X' % selection[1]) 
    # cmds.connectAttr('%s.curveSystemRotation' % selection[0], '%s.input2Y' % selection[1]) 
    # cmds.connectAttr('%s.curveSystemRotation' % selection[0], '%s.input2Z' % selection[1]) 

    # ============================= End of Main Function =============================

# If object exists, select it
def ifExistsSelect(obj):
    if cmds.objExists(obj):
        cmds.select(obj)
        cmds.headsUpMessage(obj + " selected", verticalOffset=150 )
    else:
        cmds.warning("Object doesn't exist! Did you delete or rename it after loading?")
        
def printIfExistsInList(list):
    missingElements = False
    print("#" * 32 + " Target Objects " + "#" * 32)
    for obj in list:
        if cmds.objExists(obj):
            print(obj)
        else:
            print(obj + " no longer exists!")
            missingElements = True
    print("#" * 80)
    if missingElements:
        cmds.headsUpMessage( 'It looks like you are missing some target elements! Open script editor for more information', verticalOffset=150 , time=5.0)
    else:
        cmds.headsUpMessage( 'Open script editor to see a list of your loaded elements', verticalOffset=150 , time=5.0)

# Start current "Main"
connectAttributesMainDialog()