import maya.cmds as cmds

# DEPRECATED
# GT API - A list of functions that could be useful for other scripts
# @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-03-03
# Last update - 2020-03-03

 
# Prints selection attributes
def printSelectionAttributes(type):
    selection = cmds.ls(selection=True)
    if type == "keyable" and len(selection) > 0:
        attrList = cmds.listAttr (selection[0], k=True) or []
    elif len(selection) > 0:
        attrList = cmds.listAttr (selection[0]) or []
    
    
    if len(selection) > 0 and attrList != []:
        print("#" * 80)
        print(" " * 30 + selection[0] + " attributes:")
        for attr in attrList:
            print(attr)
        print("#" * 80)
        cmds.headsUpMessage( 'Open Script Editor to see the list of attributes', verticalOffset=150 , time=5.0)
    else:
        cmds.warning("Nothing selected (or no attributes to be displayed)")
                

# If object exists, select it
def ifExistsSelect(obj):
    if cmds.objExists(obj):
        cmds.select(obj)
        cmds.headsUpMessage(obj + " selected", verticalOffset=150 )
    else:
        cmds.warning("Object doesn't exist! Did you delete or rename it?")


# Disconnect attributes
def disconnectAttribute(node, attrName, source=True, destination=False):
    connectionPairs = []
    if source:
        connectionsList = cmds.listConnections(node, plugs=True, connections=True, destination=False)
        if connectionsList:
            connectionPairs.extend(zip(connectionsList[1::2], connectionsList[::2]))
    
    if destination:
        connectionsList = cmds.listConnections(node, plugs=True, connections=True, source=False)
        if connectionsList:
            connectionPairs.extend(zip(connectionsList[::2], connectionsList[1::2]))
    
    for srcAttr, destAttr in connectionPairs:
        if attrName in destAttr:
            cmds.disconnectAttr(srcAttr, destAttr)

        
# Parses textField data 
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

# Try to run code that came from a string (for the "Run Code" button)
def runOutput(out):
    try:
        exec(out)
    except:
        cmds.warning("Something is wrong with your code!")
        

# Locks an hides attributes
def lockHideAttr(obj,attrArray,lock,hide):  # TO DO : Add a check to first see if the attribute exists here
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
        
# Prints selection attributes
def printSelectionAttributes(type):
    selection = cmds.ls(selection=True)
    if type == "keyable" and len(selection) > 0:
        attrList = cmds.listAttr (selection[0], k=True) or []
    elif len(selection) > 0:
        attrList = cmds.listAttr (selection[0]) or []
    
    
    if len(selection) > 0 and attrList != []:
        print("#" * 80)
        print(" " * 30 + selection[0] + " attributes:")
        for attr in attrList:
            print(attr)
        print("#" * 80)
        cmds.headsUpMessage( 'Open Script Editor to see the list of attributes', verticalOffset=150 , time=5.0)
    else:
        cmds.warning("Nothing selected (or no attributes to be displayed)")
        
        
# targetListManager
def targetListManager(list):
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
        cmds.headsUpMessage( 'Target elements selected (Open script editor to see a list of your loaded elements)', verticalOffset=150 , time=5.0)
    if settings.get("targetList") != [] and missingElements == False:
        cmds.select(settings.get("targetList"))
   
# Gets color from selected element (First)
# Returns RGB color stored as the object's outliner color
def getOutlinerColorFromSelection(colorSlider): 
        selection = cmds.ls(selection=True)
        if len(selection) > 0:
            objAttrList = cmds.listAttr(selection[0]) or []
            if len(objAttrList) > 0 and "outlinerColor" in objAttrList and "useOutlinerColor" in objAttrList:
                extractedColor = cmds.getAttr(selection[0] + ".outlinerColor")
                if cmds.getAttr(selection[0] + ".useOutlinerColor"):
                    return extractedColor[0]
                    #cmds.colorSliderGrp(colorSlider, e=True, rgb=extractedColor[0])
                else:
                    return extractedColor[0]
                    cmds.colorSliderGrp(colorSlider, e=True, rgb=extractedColor[0])
                    cmds.warning("Color extracted, but it looks like the object selected is not using a custom outliner color")
            else:
                cmds.warning("Something went wrong. Try selecting another object.")
        else:
            cmds.warning("Nothing Selected. Please select an object containing the outliner color you want to extract and try again.")
            
# Exports a list of object to TXT file (Created to be used with selection)  
def exportToTxt(list):
    tempDir = cmds.internalVar(userTmpDir=True)
    txtFile = tempDir+'tmp_sel.txt';
    
    f = open(txtFile,'w')
    
    stringForPy = "', '".join(list)
    stringForMel = " ".join(list)
    stringForList = "\n# ".join(list)

    selectCommand = "# Python command to select it:\n\nimport maya.cmds as cmds\nselectedObjects = ['" + stringForPy + \
    "'] \ncmds.select(selectedObjects)\n\n\n\'\'\'\n// Mel command to select it\nselect -r " + stringForMel + "\n\n\'\'\'\n\n\n# List of Objects:\n# " + stringForList

    f.write(selectCommand)
    f.close()

    notepadCommand = 'exec("notepad ' + txtFile + '");'
    mel.eval(notepadCommand)
    
# Returns if object is a shape or not
def isObjectShape(object):
    nodeInheritance =  cmds.nodeType(object, inherited=True)
    isShape = False
    for inheritance in nodeInheritance:
        if "shape" in inheritance:
            isShape = True
    return isShape
    
# Checks if obj exists before selecting it
def ifObjectsInListExistsSelect(list):
    for obj in list:
        if cmds.objExists(obj):
            cmds.select(obj)
            cmds.headsUpMessage(obj + " selected", verticalOffset=150 )
        else:
            cmds.warning("Object doesn't exist! Did you delete or rename it after loading?")
            
