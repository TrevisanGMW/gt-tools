import maya.cmds as cmds

# Auto FK Control with Hierarchy
# @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-01-03
# Last update - 2020-01-03

# Version:
scriptVersion = "v1.0"

# Default Settings
mimicHierarchy = True
constraintJoint = True
autoColorCtrls = True
defaultRemoveTag = True
defaultCurve = "cmds.circle(name=joint_name + 'Ctrl', normal=[1,0,0], radius=1.5, ch=False)"
jointTagLengthDefault = 3

# Custom Curve Dictionary
settings = { 'usingCustomCurve': False, 
             'customCurve': defaultCurve,
             'failedToBuildCurve': False,
             'jointTagLength' : jointTagLengthDefault,
            }


# Main Form ============================================================================
def autoFKMainDialog():
    if cmds.window("autoFKMainDialog", exists =True):
        cmds.deleteUI("autoFKMainDialog")    

    # mainDialog Start Here =================================================================================

    autoFKMainDialog = cmds.window("autoFKMainDialog", title="Auto FK - " + scriptVersion,\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =False)

    columnMain = cmds.columnLayout() 

    form = cmds.formLayout(p=columnMain)

    contentMain = cmds.columnLayout(adj = True)

    cmds.text("")
    cmds.text("Auto FK with Hierarchy - " + scriptVersion, bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.text("  ")
    cmds.text("      This script generates FK controls while       ")
    cmds.text("      storing their transforms in groups.     ")
    cmds.text("      Select desired joints and run script.     ")
    cmds.text("   ")
    cmds.text('1. Select Root Joint   ')
    cmds.text('2. Select Hierarchy    ')
    cmds.text("3. Generate Controls")
    cmds.text("   ")
    cmds.separator(h=10, p=contentMain)
    checkBoxesOneContainer = cmds.rowColumnLayout( numberOfRows=1, h= 25)
    cmds.text("      ")
    checkBoxesOne = cmds.checkBoxGrp(p=checkBoxesOneContainer, columnWidth2=[120, 1], numberOfCheckBoxes=2, \
                                label1 = 'Mimic Hierarchy', label2 = "Constraint Joint    ", v1 = mimicHierarchy, v2 = constraintJoint) 
    checkBoxesTwoContainer = cmds.rowColumnLayout( numberOfRows=1, h= 25,p=contentMain)
    cmds.text("      ")
    checkBoxesTwo = cmds.checkBoxGrp(p=checkBoxesTwoContainer, columnWidth2=[120, 1], numberOfCheckBoxes=2, \
                                label1 = 'Colorize Controls', label2 = "Remove Jnt Tag  ", v1 = autoColorCtrls, v2 = defaultRemoveTag)
    cmds.button(p=contentMain, l ="(Advanced) Custom Curve", c=lambda x:defineCustomCurve())
    cmds.button(p=contentMain, l ="(Advanced) Change Joint Tag Length", c=lambda x:changeJntTagLength())
    cmds.separator(h=10, p=contentMain)
    cmds.text(p=contentMain, label='Ignore Joints Containing These Strings:' )
    cmds.separator(h=5, p=contentMain)
    undesiredStringsTextField = cmds.textField(p = contentMain, text="End, eye", enterCommand=lambda x:generateFKControls())
    cmds.text(p=contentMain, label='(Use Commas to Separate Strings)' )
    cmds.separator(h=10, p=contentMain)
    cmds.button(p=contentMain, l ="Generate", bgc=(.6, .8, .6), c=lambda x:generateFKControls())
    
    # Generate FK Main Function Starts --------------------------------------------
    def generateFKControls():
        selectedJoints = cmds.ls(selection=True, type='joint')
        undesiredJntStrings = parseTextField(cmds.textField(undesiredStringsTextField, q=True, text=True))
        undesiredJoints = []

        # Find undesired joints and make a list of them
        for jnt in selectedJoints:
            for name in undesiredJntStrings:
                if name in jnt:
                    undesiredJoints.append(jnt)
                else:
                    pass
        
        # Remove undesired joints from selection list
        for jnt in undesiredJoints:
            selectedJoints.remove(jnt)

        
        for jnt in selectedJoints:
            if cmds.checkBoxGrp(checkBoxesTwo, q=True, value2=True) and settings.get("jointTagLength") != 0:
                joint_name = jnt[:-settings.get("jointTagLength")]
                print("1")
            else:
                joint_name = jnt
                print("2")
            ctrlName = joint_name + 'Ctrl'


            if settings.get("usingCustomCurve"):
                ctrl = createCustomCurve(settings.get("customCurve"))
                print(ctrl)
                ctrl = cmds.rename(ctrl, ctrlName)
                if settings.get("failedToBuildCurve"):
                    ctrl = cmds.circle(name=ctrlName, normal=[1,0,0], radius=1.5, ch=False)
            else:
                ctrl = cmds.circle(name=ctrlName, normal=[1,0,0], radius=1.5, ch=False)
                
            
            grp = cmds.group(name=(ctrlName +'Grp'))
            constraint = cmds.parentConstraint(jnt,grp)
            cmds.delete(constraint)
            
            
            # Colorize Control Start ------------------

            if cmds.checkBoxGrp(checkBoxesTwo, q=True, value1=True):
                cmds.setAttr(ctrl[0] + ".overrideEnabled", 1)
                if 'right_' in ctrl[0]:
                    cmds.setAttr(ctrl[0] + ".overrideColor", 13) #Red
                elif 'left_' in ctrl[0]:
                    cmds.setAttr(ctrl[0] + ".overrideColor", 6) #Blue
                else:
                    cmds.setAttr(ctrl[0] + ".overrideColor", 17) #Yellow
            else:
                pass
            
            # Colorize Control End ---------------------
            
            
            if cmds.checkBoxGrp(checkBoxesOne, q=True, value2=True):
                cmds.parentConstraint(ctrlName,jnt)
            
            if cmds.checkBoxGrp(checkBoxesOne, q=True, value1=True):
                #Auto parents new controls
                # "or []" Accounts for root joint that doesn't have a parent, it forces it to be a list
                jntParent = cmds.listRelatives(jnt, allParents=True) or []
                if len(jntParent) == 0:
                    pass
                else:
                    parentCtrl = (jntParent[0][:-3] + 'Ctrl')
                    
                    if cmds.objExists(parentCtrl):
                        cmds.parent(grp, parentCtrl)
    # Generate FK Main Function Ends --------------------------------------------
      
    cmds.showWindow(autoFKMainDialog)
    # mainDialog Ends Here =================================================================================


# Function to Parse textField data 
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

# Define Custom Curve by updating a dictonary
def defineCustomCurve():
    result = cmds.promptDialog(
                    title='Py Curve',
                    message='Paste Python Curve Below:',
                    button=['OK', 'Use Default'],
                    defaultButton='OK',
                    cancelButton='Use Default',
                    dismissString='Use Default')

    if result == 'OK':
        settings["customCurve"] = cmds.promptDialog(query=True, text=True)
        settings["usingCustomCurve"] = True
        settings["failedToBuildCurve"] = False
    else:
        settings["usingCustomCurve"] = False

# Force Run Nested Exec
def createCustomCurve(input):
    try:
        exec(input)
        return cmds.ls(selection=True)
    except:
        cmds.error("Something is wrong with your python curve!")
        settings["failedToBuildCurve"] = True
        
# Define Custom Curve by updating a dictonary
def changeJntTagLength():
    result = cmds.promptDialog(
                    title='Py Curve',
                    message='New Jnt Tag Legth:',
                    button=['Change','Use Default (3)'],
                    defaultButton='OK',
                    cancelButton='Use Default',
                    dismissString='Use Default')

    if result == 'Change':
        try:
            settings["jointTagLength"] = int(cmds.promptDialog(query=True, text=True))
        except:
            cmds.warning("You entered an invalid option. Using Default (3)")
    else:
        settings["jointTagLength"] = jointTagLengthDefault


#Start current "Main"
autoFKMainDialog()
