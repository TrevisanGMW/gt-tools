import maya.cmds as cmds

# GT Connect Attributes Script
# @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-02-04
# Last update - 2020-02-12

# Version:
scriptVersion = "v1.0"
 

settings = { 'targetList': [], 
             'sourceObj': [],
             'defReverseNode': False,
             'defDisconnect' : False,
             'defSingleST' : False,
             'defUseCustomNode' : False,
             'statusSingleST' : False,
             'statusUseCustomNode' : False,
             'statusUseReverseNode' : False,
             'statusDisconnect' : False,
             'statusAddInput' : False,
             'inputNodeType' : 'condition',
             'customNode' : 'plusMinusAverage'
            }


# Main Form ============================================================================
def connectAttributesMainDialog():
    if cmds.window("connectAttributesMainDialog", exists =True):
        cmds.deleteUI("connectAttributesMainDialog")    

    # mainDialog Start Here =================================================================================

    connectAttributesMainDialog = cmds.window("connectAttributesMainDialog", title="connectAttr - " + scriptVersion,\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =False)

    columnMain = cmds.columnLayout() 

    form = cmds.formLayout(p=columnMain)

    contentMain = cmds.columnLayout(adj = True)
    
    # Description
    cmds.text("")
    cmds.text("GT Connect Attributes - " + scriptVersion, bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.text("  ")
    cmds.text("      This script creates a node connection       ")
    cmds.text("      between source and target elements     ")
    cmds.text("   ")
    cmds.text('The Selection Source/Target  ')
    cmds.text('option expects the user to select  ')
    cmds.text('Source (1st) then Targets (2nd ,3rd...)  ')
    cmds.text("   ")
    cmds.separator(h=15, p=contentMain)
    
    # Checkbox - Selection as Source and Target
    interactiveContainerMisc = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 25)
    cmds.text("    ")
    singleSourceTarget = cmds.checkBox(p=interactiveContainerMisc, label='  Use Selection as Source and Target (s)', value=settings.get("defSingleST"),\
                         cc=lambda x:isUsingSingleTarget(cmds.checkBox(singleSourceTarget, query=True, value=True)) )

    # CheckboxGrp Reverse and Disconnect
    interactiveContainerJnt = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 25)
    cmds.text("    ") # Increase this to move checkboxes to the right
    revDiscCheckBoxGrp = cmds.checkBoxGrp(p=interactiveContainerJnt, columnWidth2=[135, 1], numberOfCheckBoxes=2, \
                                label1 = '  Add Reverse Node', label2 = "Disconnect", v1 = settings.get("defReverseNode"), v2 = settings.get("defDisconnect"), \
                                cc1=lambda x:updateStoredValues(), cc2= lambda x:isDisconnecting(cmds.checkBoxGrp(revDiscCheckBoxGrp,q=True,v2=True)))   

    cmds.separator(h=15, p=contentMain)

    # Checkbox Use Custom Node Between Connection
    interactiveContainerMisc = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 25)
    cmds.text("    ")
    addCustomNode = cmds.checkBox(p=interactiveContainerMisc, label='  Add Custom Node Between Connection', value=settings.get("defUseCustomNode"),\
                          cc=lambda x:isUsingCustomNode(cmds.checkBox(addCustomNode, query=True, value=True)) ) # UPDATE THIS
    
    # Dropdown Menu (Custom Node)
    customNodeMenuContainer = cmds.rowColumnLayout(p=contentMain,numberOfRows=1, adj = True)
    customNodeMenu = cmds.optionMenu(en=False, p=customNodeMenuContainer, label='   Custom Node', cc=lambda x:updateStoredValues()) #######
    cmds.menuItem( label='plusMinusAverage' )
    cmds.menuItem( label='multiplyDivide' )
    cmds.menuItem( label='condition' )

    customNodeEmptySpace = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 7)
    
    # Checkbox and Dropdown Menu for Input node and its type
    nodeBehaviourContainerOne = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 25)
    cmds.text("    ")
    addCtrlNode = cmds.checkBox(p=nodeBehaviourContainerOne, en=False, label='  Add Input Node  ', value=settings.get("defUseCustomNode"),\
                          cc=lambda x:updateStoredValues())
    
    ctrlNodeOutput = cmds.optionMenu(en=False, p=nodeBehaviourContainerOne, label='', w=120,cc=lambda x:updateStoredValues()) #######
    cmds.menuItem( label='condition' )
    cmds.menuItem( label='plusMinusAverage' )
    cmds.menuItem( label='multiplyDivide' )     
    cmds.text("   ",p=customNodeMenuContainer)
                                                   
    cmds.separator(h=10, p=contentMain)
    
    # Source List Loader (Buttons)
    sourceContainer = cmds.rowColumnLayout( p=contentMain, numberOfRows=1)
    sourceBtn = cmds.button(p=sourceContainer, l ="Load Source Object", c=lambda x:updateLoadButtonJnt("source"), w=130)
    sourceStatus = cmds.button(p=sourceContainer, l ="Not loaded yet", bgc=(0, 0, 0), w=130, \
                            c="cmds.headsUpMessage( 'Select your source element and click on \"Load Source Object\"', verticalOffset=150 , time=5.0)")
                            
    # Target List Loader (Buttons)
    targetContainer = cmds.rowColumnLayout( p=contentMain, numberOfRows=1)
    targetBtn = cmds.button(p=targetContainer, l ="Load Target Objects", c=lambda x:updateLoadButtonJnt("target"), w=130)
    targetStatus = cmds.button(p=targetContainer, l ="Not loaded yet", bgc=(0, 0, 0), w=130, \
                            c="cmds.headsUpMessage( 'Select your target elements and click on \"Load Target Objects\"', verticalOffset=150 , time=5.0)")
    cmds.separator(h=10, p=contentMain)
    
    # Source/Target Attributes
    bottomContainer = cmds.rowColumnLayout(p=contentMain,adj=True)
    cmds.text('Source Attribute (Only One):',p=bottomContainer)
    sourceAttributesInput = cmds.textField(p = bottomContainer, text="translate", \
                                    enterCommand=lambda x:connectAttributes(cmds.textField(sourceAttributesInput, q=True, text=True),\
                                                                            cmds.textField(targetAttributesInput, q=True, text=True)))
    cmds.text('Target Attributes:',p=bottomContainer)
    targetAttributesInput = cmds.textField(p = bottomContainer, text="translate, rotate, scale", \
                                    enterCommand=lambda x:connectAttributes(cmds.textField(sourceAttributesInput, q=True, text=True),\
                                                                            cmds.textField(targetAttributesInput, q=True, text=True)))
    
    # Print Attributes Buttons
    cmds.rowColumnLayout(p=contentMain,adj=True,h=5)
    showAttributesContainer = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 25)
    cmds.button(p=showAttributesContainer, l ="List All Attributes", w=130,\
                                    c=lambda x:printSelectionAttributes("all"))                                                                    
    cmds.button(p=showAttributesContainer, l ="List Keyable Attributes", w=130,\
                                    c=lambda x:printSelectionAttributes("keyable")) 
    
    cmds.separator(h=10, p=contentMain)
    
    # Connect Button (Main Function)
    cmds.button(p=contentMain, l ="Connect Attributes", bgc=(.6, .8, .6), \
                                    c=lambda x:connectAttributes(cmds.textField(sourceAttributesInput, q=True, text=True),\
                                                                            cmds.textField(targetAttributesInput, q=True, text=True)))

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
                
    # Updates elements to reflect the use of selection (instead of loaders)
    def isUsingSingleTarget(state): 
        if state:
            settings["statusSingleST"] = cmds.checkBox(singleSourceTarget, q=True, value=True)
            cmds.button(sourceBtn, e=True, en=False)
            cmds.button(sourceStatus, l ="Not necessary", e=True, en=False, bgc=(.25, .25, .25))
            cmds.button(targetBtn, e=True, en=False)
            cmds.button(targetStatus, l ="Not necessary", e=True, en=False, bgc=(.25, .25, .25))
            settings["targetList"] = []
            settings["sourceObj"] = []
        else:
            settings["statusSingleST"] = cmds.checkBox(singleSourceTarget, q=True, value=True)
            cmds.button(sourceBtn, e=True, en=True)
            cmds.button(sourceStatus, l ="Not loaded yet", e=True, en=True, bgc=(0, 0, 0),\
                        c="cmds.headsUpMessage( 'Select your source element and click on \"Load Source Object\"', verticalOffset=150 , time=5.0)")
            cmds.button(targetBtn, e=True, en=True)
            cmds.button(targetStatus, l ="Not loaded yet", e=True, en=True, bgc=(0, 0, 0), \
                        c="cmds.headsUpMessage( 'Select your target elements and click on \"Load Target Objects\"', verticalOffset=150 , time=5.0)")
            
    # Updates elements to reflect the use of in between custom node
    def isUsingCustomNode(state): 
        if state:
            cmds.optionMenu(customNodeMenu, e=True, en=True)
            settings["statusUseCustomNode"] = cmds.checkBox(addCustomNode, q=True, value=True)
            cmds.checkBox(addCtrlNode,e=True, en=True)
            cmds.optionMenu(ctrlNodeOutput,e=True, en=True)
        else:
            cmds.optionMenu(customNodeMenu, e=True, en=False)
            settings["statusUseCustomNode"] = cmds.checkBox(addCustomNode, q=True, value=True)
            cmds.checkBox(addCtrlNode,e=True, en=False)
            cmds.optionMenu(ctrlNodeOutput,e=True, en=False)

    # Updates many of the stored GUI values (Used by multiple elements)
    def updateStoredValues(): 
        settings["customNode"] = cmds.optionMenu(customNodeMenu, q=True, value=True)
        settings["statusUseReverseNode"] = cmds.checkBoxGrp(revDiscCheckBoxGrp, q=True, value1=True)
        settings["statusDisconnect"] = cmds.checkBoxGrp(revDiscCheckBoxGrp, q=True, value2=True)
        settings["inputNodeType"] = cmds.optionMenu(ctrlNodeOutput, q=True, value=True)
        settings["statusAddInput"] = cmds.checkBox(addCtrlNode, q=True, value=True)
        #print(settings.get("customNode")) # Debugging
        
    # Updates elements to reflect the use disconnect function
    def isDisconnecting(state): 
        
        if state:
            cmds.checkBox(addCustomNode, e=True, en=False)
            isUsingCustomNode(False)
            cmds.checkBoxGrp(revDiscCheckBoxGrp, e=True, en1=False)
            
        else:
            cmds.checkBox(addCustomNode, e=True, en=True)
            isUsingCustomNode(cmds.checkBox(addCustomNode, q=True, value=True))
            cmds.checkBoxGrp(revDiscCheckBoxGrp, e=True, en1=True)
    
    
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
        
            cmds.button(targetStatus, l =loadedText,e=True, bgc=(.6, .8, .6), w=130, c=lambda x:targetListManager(settings.get("targetList")))
        elif buttonName is "target":
            cmds.button(targetStatus, l ="Failed to Load",e=True, bgc=(1, .4, .4), w=130,\
                        c="cmds.headsUpMessage( 'Make sure you select at least one target element', verticalOffset=150 , time=5.0)")


    cmds.showWindow(connectAttributesMainDialog)
    # mainDialog Ends Here =================================================================================


# Main Function 
def connectAttributes(sourceTextFieldAttribute,tagetTextFieldAttributes):

    # Final Check before running
    isReadyToConnect = True

    if settings.get("statusSingleST") == False:
        if settings.get("targetList") == [] or settings.get("sourceObj") == []:
            cmds.warning("One of your lists is empty")
            isReadyToConnect = False
        else:
            targetList = settings.get("targetList")
            sourceObj = settings.get("sourceObj")
    else:
        selection = cmds.ls(selection=True) or []
        if len(selection) < 2:
            cmds.warning("You need at least two elements selected to create connections")
            isReadyToConnect = False
        else:
            targetList = selection
            sourceObj = selection[0]
            targetList.remove(sourceObj)
    
    doDisconnect = settings.get('statusDisconnect')
    customNode = settings.get('customNode')
    inputNodeType = settings.get('inputNodeType')
    usingReverseNode = settings.get('statusUseReverseNode')
    targetAttributesList = parseTextField(tagetTextFieldAttributes)
    
    # Start Connecting
    if isReadyToConnect and doDisconnect == False:
        
        # Creates Necessary Nodes
        if settings.get('statusAddInput'):
                inputNode = cmds.createNode(inputNodeType)
 
        for targetObj in targetList: 
         for attr in targetAttributesList:

            if settings.get('statusUseCustomNode'): # Is using custom node?
            
                if usingReverseNode:
                    reverseNode = cmds.createNode("reverse")
            
                #Source to inBetween node
                nodeInBetween = cmds.createNode(customNode)
                if customNode == "plusMinusAverage":
                    if "3" in cmds.getAttr(sourceObj + "." + sourceTextFieldAttribute,type=True):
                        cmds.connectAttr(sourceObj + "." + sourceTextFieldAttribute, nodeInBetween + "." + "input3D[0]") 
                    else:
                        cmds.connectAttr(sourceObj + "." + sourceTextFieldAttribute, nodeInBetween + "." + "input3D[0].input3Dx") 
                
                elif customNode == "multiplyDivide":
                    if "3" in cmds.getAttr(sourceObj + "." + sourceTextFieldAttribute,type=True):
                        cmds.connectAttr(sourceObj + "." + sourceTextFieldAttribute, nodeInBetween + "." + "input1") 
                    else:
                        cmds.connectAttr(sourceObj + "." + sourceTextFieldAttribute, nodeInBetween + "." + "input1X") 
                        
                elif customNode == "condition":
                    if "3" in cmds.getAttr(sourceObj + "." + sourceTextFieldAttribute,type=True):
                        cmds.connectAttr(sourceObj + "." + sourceTextFieldAttribute, nodeInBetween + "." + "colorIfTrue") 
                    else:
                        cmds.connectAttr(sourceObj + "." + sourceTextFieldAttribute, nodeInBetween + "." + "colorIfTrueR")
                     
                # inBetween node to Target node
                if usingReverseNode:
                    # Connect Custom node to Reverse Node
                    if customNode == "plusMinusAverage":
                        if "3" in cmds.getAttr(targetObj + "." + attr,type=True):
                            cmds.connectAttr(nodeInBetween + "." + "output3D", reverseNode + "." + 'input') 
                        else:
                            cmds.connectAttr(nodeInBetween + "." + "output3Dx", reverseNode + "." + 'inputX')  
                    elif customNode == "multiplyDivide":
                        if "3" in cmds.getAttr(targetObj + "." + attr,type=True):
                            cmds.connectAttr(nodeInBetween + "." + "output", reverseNode + "." + 'input') 
                        else:
                            cmds.connectAttr(nodeInBetween + "." + "outputX", reverseNode + "." + 'inputX') 
                            
                    elif customNode == "condition":
                        if "3" in cmds.getAttr(targetObj + "." + attr,type=True):
                            cmds.connectAttr(nodeInBetween + "." + "outColor", reverseNode + "." + 'input') 
                        else:
                            cmds.connectAttr(nodeInBetween + "." + "outColorR", reverseNode + "." + 'inputX')
                    # Reverse Output to Target Node
                    if "3" in cmds.getAttr(targetObj + "." + attr,type=True):
                        cmds.connectAttr(reverseNode + "." + "output", targetObj + "." + attr) 
                    else:
                        cmds.connectAttr(reverseNode + "." + "outputX", targetObj + "." + attr)  
                else:
                    # Custom Node to Target Node
                    if customNode == "plusMinusAverage":
                        if "3" in cmds.getAttr(targetObj + "." + attr,type=True):
                            cmds.connectAttr(nodeInBetween + "." + "output3D", targetObj + "." + attr) 
                        else:
                            cmds.connectAttr(nodeInBetween + "." + "output3Dx", targetObj + "." + attr)  
                    
                    elif customNode == "multiplyDivide":
                        if "3" in cmds.getAttr(targetObj + "." + attr,type=True):
                            cmds.connectAttr(nodeInBetween + "." + "output", targetObj + "." + attr) 
                        else:
                            cmds.connectAttr(nodeInBetween + "." + "outputX", targetObj + "." + attr) 
                            
                    elif customNode == "condition":
                        if "3" in cmds.getAttr(targetObj + "." + attr,type=True):
                            cmds.connectAttr(nodeInBetween + "." + "outColor", targetObj + "." + attr) 
                        else:
                            cmds.connectAttr(nodeInBetween + "." + "outColorR", targetObj + "." + attr) 
                
                
                # input node to custom nodes
                if settings.get('statusAddInput'):
                    if inputNodeType == "plusMinusAverage":
                        outOfInput = "output3D"
                    elif inputNodeType == "multiplyDivide":
                        outOfInput = "output"
                    elif inputNodeType == "condition":
                        outOfInput = "outColor"
                        
                    if customNode == "plusMinusAverage":
                        cmds.connectAttr(inputNode + "." + outOfInput, nodeInBetween + "." + "input3D[1]") 
                    elif customNode == "multiplyDivide":
                        cmds.connectAttr(inputNode + "." + outOfInput, nodeInBetween + "." + "input2") 
                    elif customNode == "condition":
                        cmds.connectAttr(inputNode + "." + outOfInput, nodeInBetween + "." + "colorIfFalse") 
                
            else: # Not using custom node (Do simple connection)
                if usingReverseNode:
                    reverseNode = cmds.createNode("reverse")
                    #Reverse Input
                    if "3" in cmds.getAttr(sourceObj + "." + sourceTextFieldAttribute,type=True):
                        cmds.connectAttr(sourceObj + "." + sourceTextFieldAttribute, reverseNode + "." + "input") 
                    else:
                        cmds.connectAttr(sourceObj + "." + sourceTextFieldAttribute, reverseNode + "." + "inputX")
                    #Reverse Output
                    if "3" in cmds.getAttr(targetObj + "." + attr,type=True):
                        cmds.connectAttr(reverseNode + "." + "output", targetObj + "." + attr) 
                    else:
                        cmds.connectAttr(reverseNode + "." + "outputX", targetObj + "." + attr)  
                else:
                    cmds.connectAttr(sourceObj + "." + sourceTextFieldAttribute, targetObj + "." + attr) #Simple Connection
            
            
    elif isReadyToConnect and doDisconnect == True: # Disconnect Instead
        for targetObj in targetList: 
            for attr in targetAttributesList:
                #cmds.connectAttr(sourceObj + "." + sourceTextFieldAttribute, targetObj + "." + attr) #Simple Connection
                cmds.disconnectAttr(sourceObj + "." + sourceTextFieldAttribute, targetObj + "." + attr)

        

    # ============================= End of Main Function =============================

# If object exists, select it
def ifExistsSelect(obj):
    if cmds.objExists(obj):
        cmds.select(obj)
        cmds.headsUpMessage(obj + " selected", verticalOffset=150 )
    else:
        cmds.warning("Object doesn't exist! Did you delete or rename it after loading?")

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

# Start current "Main"
connectAttributesMainDialog()