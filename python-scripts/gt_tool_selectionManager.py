import maya.cmds as cmds
import maya.mel as mel

# GT Selection Manager Script
# @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-02-19
# Last update - 2020-02-25

# Version:
scriptVersion = "v1.0"
 

# Ideas:
# Shader name, Texture, TRS


settings = { 'useContainsString' : False,             # Active Functions
             'useContainsNoString' : False,
             'useContainsType' : False,
             'useContainsNoType' : False,
             'useVisibilityState' : False,
             'useOutlinerColor' : False,
             'useNoOutlinerColor' : False,
             'storedOutlinerColor' : [1,1,1],              # StoredValues
             'storedNoOutlinerColor' : [1,1,1],
             'storedSelectionOne' : [],
             'storedSelectionTwo' : [],
             'storedContainsString' : '',
             'storedContainsNoString' : '',
             'storedContainsType' : '',
             'storedContainsNoType' : '',
             'storedshapeNodeType' : 'Select Shapes as Objects',
             'storedVisibilityState' : False,
             'storedSaveAsQuickSelection' : True,
             'storedNewSelection' : False
            }


# Main Form ============================================================================
def selectionManagerMainDialog():
    if cmds.window("selectionManagerMainDialog", exists =True):
        cmds.deleteUI("selectionManagerMainDialog")    

    # mainDialog Start Here =================================================================================

    selectionManagerMainDialog = cmds.window("selectionManagerMainDialog", title="gt_selection_manager - " + scriptVersion,\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =True)

    columnMain = cmds.columnLayout() 

    form = cmds.formLayout(p=columnMain)

    contentMain = cmds.columnLayout(adj = True)
    
    # Description
    cmds.text("")
    cmds.text("GT Selection Manager - " + scriptVersion, bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.text("  ")
    cmds.text("      This script allows you to update selections       ")
    cmds.text("      to contain (or not) only filtered elements     ")
    cmds.text("   ")
    cmds.separator(h=15, p=contentMain)
    
    
    # Element Name
    cmds.text("Element Name")
    cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 5) #Empty Space
    nameContainer = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 25)
    cmds.text("    ") # Increase this to move checkboxes to the right
    containsStringOrNotCheckbox = cmds.checkBoxGrp(p=nameContainer, columnWidth2=[120, 1], numberOfCheckBoxes=2, \
                                label1 = ' Does Contain ', label2 = "  Doesn't Contain", v1 = settings.get("useContainsString"), v2 = settings.get("useContainsNoString"), \
                                cc1=lambda x:updateActiveItems(), cc2= lambda x:updateActiveItems())  
    
    # Element Name Textbox
    nameTextboxContainer = cmds.rowColumnLayout( p=contentMain, numberOfRows=1)
    
    containsNameTxtfield = cmds.textField(p = nameTextboxContainer, width=130, text="Jnt", en=False, \
                                           enterCommand=lambda x:updateStoredValuesAndRun())
    containsNoNameTxtfield = cmds.textField(p = nameTextboxContainer,width=130, text="End, eye", en=False, \
                                           enterCommand=lambda x:updateStoredValuesAndRun())
    cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 3) #Empty Space
    cmds.separator(h=10, p=contentMain)
    
    # Element Type
    cmds.text("Element Type",p=contentMain)
    cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 5) #Empty Space
    typeContainer = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 25)
    cmds.text("    ") # Increase this to move checkboxes to the right
    containsTypeOrNotCheckbox = cmds.checkBoxGrp(p=typeContainer, columnWidth2=[120, 1], numberOfCheckBoxes=2, \
                                label1 = ' Does Contain ', label2 = "  Doesn't Contain", v1 = settings.get("useContainsType"), v2 = settings.get("useContainsNoType"), \
                                cc1=lambda x:updateActiveItems(), cc2= lambda x:updateActiveItems())  
    
    # Element Type Textbox
    nameTextboxContainer = cmds.rowColumnLayout( p=contentMain, numberOfRows=1)
    
    containsTypeTxtfield = cmds.textField(p = nameTextboxContainer, width=130, text="joint", en=False, \
                                           enterCommand=lambda x:updateStoredValuesAndRun()) 
    containsNoTypeTxtfield = cmds.textField(p = nameTextboxContainer,width=130, text="mesh", en=False, \
                                           enterCommand=lambda x:updateStoredValuesAndRun())
    cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 3) #Empty Space
    
        
    # Element Type Shape Node Behaviour
    shapeNodeBehaviorContainer = cmds.rowColumnLayout(p=contentMain,numberOfRows=1, adj = True)
    shapeNodeBehaviorMenu = cmds.optionMenu(en=False, p=shapeNodeBehaviorContainer, label=' Behavior', cc=lambda x:updateActiveItems()) #######
    cmds.menuItem( label='Select Both Parent and Shape')
    cmds.menuItem( label='Select Shapes as Objects')
    cmds.menuItem( label='Select Parent Instead')
    cmds.menuItem( label='Ignore Shape Nodes')
    

    # Print Types Buttons
    cmds.rowColumnLayout(p=contentMain,adj=True,h=5)
    showAttributesContainer = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 25)
    cmds.button(p=showAttributesContainer, l ="Print Selection Types", w=130,\
                                    c=lambda x:printSelectionTypes("selection"))                                                                    
    cmds.button(p=showAttributesContainer, l ="Print All Scene Types", w=130,\
                                    c=lambda x:printSelectionTypes("all")) 
    
    cmds.separator(h=10, p=contentMain)
    
    # Visibility
    visibilityContainer = cmds.rowColumnLayout( p=contentMain, numberOfRows=1)
    cmds.text("    ")
    useVisibilityState = cmds.checkBox(p=visibilityContainer, label=' Visibility State  --->  ', value=settings.get("useVisibilityState"),\
                         cc=lambda x:updateActiveItems())
    cmds.radioCollection()
    visibilityRb1 = cmds.radioButton( p=visibilityContainer, label=' On  ' , en=False)
    visibilityRb2 = cmds.radioButton( p=visibilityContainer,  label=' Off ', en=False, sl=True)
    cmds.separator(h=10, p=contentMain)
    
    # Outline Color
    outlineColorContainer = cmds.rowColumnLayout( p=contentMain, numberOfRows=1)
    cmds.text("    ")
    useOutlineColor = cmds.checkBox(p=outlineColorContainer, label='', value=settings.get("useOutlinerColor"),\
                         cc=lambda x:updateActiveItems())
                         
    hasOutlinerColorSliderOne = cmds.colorSliderGrp(en=False, label='Uses Outliner Colors  --->  ', rgb=(settings.get("storedOutlinerColor")[0], \
                                                                settings.get("storedOutlinerColor")[1], settings.get("storedOutlinerColor")[2]),\
                                                                columnWidth=((1,145),(2,30),(3,0)), cc=lambda x:updateActiveItems())
    cmds.button(l ="Get", bgc=(.1, .1, .1), w=30, c=lambda x:getColorFromSelection(hasOutlinerColorSliderOne), height=10, width=40)
    
    
    outlineNoColorContainer = cmds.rowColumnLayout( p=contentMain, numberOfRows=1) 
    cmds.text("    ")                                              
    useNoOutlineColor = cmds.checkBox(p=outlineNoColorContainer, label='', value=settings.get("useNoOutlinerColor"),\
                         cc=lambda x:updateActiveItems())
                         
    hasNoOutlinerColorSliderOne = cmds.colorSliderGrp(en=False, label=' But Not Using These  --->  ', rgb=(settings.get("storedNoOutlinerColor")[0], \
                                                                settings.get("storedNoOutlinerColor")[1], settings.get("storedNoOutlinerColor")[2]),\
                                                                columnWidth=((1,145),(2,30),(3,0)), cc=lambda x:updateActiveItems())
    cmds.button(l ="Get", bgc=(.1, .1, .1), w=30, c=lambda x:getColorFromSelection(hasNoOutlinerColorSliderOne), height=10, width=40)
                                                   
    cmds.separator(h=10, p=contentMain)
 
                        
    # Store Selection One
    targetContainer = cmds.rowColumnLayout( p=contentMain, numberOfRows=1)
    removeFromSelBtnOne = cmds.button(p=targetContainer, l ="-", bgc=(.5, .1, .1), w=30, \
                            c=lambda x:selectionStorageManager('remove',1 ))
    storeSelBtnOne = cmds.button(p=targetContainer, l ="Store Selection", bgc=(0, 0, 0), w=91, \
                            c=lambda x:selectionStorageManager('store',1))
    addToSelBtnOne = cmds.button(p=targetContainer, l ="+", bgc=(.1, .5, .1), w=30, \
                            c=lambda x:selectionStorageManager('add',1))
    resetSelBtnOne = cmds.button(p=targetContainer, l ="Reset", w=55, \
                            c=lambda x:selectionStorageManager('reset',1))
    saveSelBtnOne = cmds.button(p=targetContainer, l ="Save", w=55, \
                            c=lambda x:selectionStorageManager('save',1))
    
    # Store Selection Two
    targetContainer = cmds.rowColumnLayout( p=contentMain, numberOfRows=1)
    removeFromSelBtnTwo = cmds.button(p=targetContainer, l ="-", bgc=(.5, .1, .1), w=30, \
                            c=lambda x:selectionStorageManager('remove',2))
    storeSelBtnTwo = cmds.button(p=targetContainer, l ="Store Selection", bgc=(0, 0, 0), w=91, \
                            c=lambda x:selectionStorageManager('store',2))
    addToSelBtnTwo = cmds.button(p=targetContainer, l ="+", bgc=(.1, .5, .1), w=30, \
                            c=lambda x:selectionStorageManager('add',2))
    resetSelBtnTwo = cmds.button(p=targetContainer, l ="Reset", w=55, \
                            c=lambda x:selectionStorageManager('reset',2))
    saveSelBtnTwo = cmds.button(p=targetContainer, l ="Save", w=55, \
                            c=lambda x:selectionStorageManager('save',2))


    cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 3) #Empty Space
    saveAsContainer = cmds.rowColumnLayout( p=contentMain, numberOfRows=1)                  
    cmds.radioCollection()
    saveAsQuickSelectionRb1 = cmds.radioButton( p=saveAsContainer, sl=True, label=' Save as Quick Selection  ', cc=lambda x:updateActiveItems())
    cmds.radioButton( p=saveAsContainer,label=' Save as Text File ', cc=lambda x:updateActiveItems())

    cmds.separator(h=10, p=contentMain)
    
    # Create New Selection (Main Function)
    cmds.button(p=contentMain, l ="Create New Selection", c=lambda x:updateStoredValuesAndRun(True))
    
    cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 5) #Empty Space
    
    # Update Selection (Main Function)
    cmds.button(p=contentMain, l ="Update Current Selection", bgc=(.6, .8, .6), c=lambda x:updateStoredValuesAndRun(False))
    
    # End of Dialog Constructor =========================================================================================================
    
    # Prints selection types or all types
    
    def selectionStorageManager(command,desiredContainer):
        selection = cmds.ls(selection=True)
        errorDetected = False
        
        if desiredContainer == 1:
            container = 'storedSelectionOne'
            button = storeSelBtnOne
        else:
            container = 'storedSelectionTwo'
            button = storeSelBtnTwo
        
        if len(selection) > 0:
            pass
        else:
            if command != "save" and command != "load" and command != "add" and command != "reset":
                cmds.warning('Nothing Selected')
            errorDetected = True

            
        if command == "remove" and errorDetected == False:
            for obj in selection:
                if obj in settings.get(container):
                    try: 
                        settings.get(container).remove(obj)
                    except:
                        pass
        
        toStoreList = []
        if command == "store" and errorDetected == False:
            for obj in selection:
                toStoreList.append(obj)
            settings[container] = toStoreList
            
        toAddList = []
        if command == "add" and errorDetected == False:
            for obj in selection:
                if obj not in settings.get(container):
                    toAddList.append(obj)
                    
            for objAdd in toAddList:
                settings.get(container).append(objAdd)
                     
        if command == "reset":
            settings[container] = []
                
        if command == "save":
            if settings.get('storedSaveAsQuickSelection') != True:
                exportToTxt(settings.get(container)) ########
            else:
                newSet = cmds.sets(name="Set_StoredSelection_0" + str(desiredContainer))
                for obj in settings.get(container):
                    cmds.sets(obj, add=newSet)
                        
        if command == "load":
            storedListManager(settings.get(container))
            

        
        # Updates Button
        if len(settings.get(container)) == 0:
            cmds.button(button, l ="Store Selection", e=True, bgc=(0, 0, 0), c=lambda x:selectionStorageManager('store', desiredContainer))
        else:
            loadedText = str(len(settings.get(container))) + " objects"
            if len(settings.get(container)) == 1:
                loadedText = settings.get(container)[0]
            cmds.button(button, l =loadedText,e=True, bgc=(.6, .8, .6), c=lambda x:selectionStorageManager('load',desiredContainer))
            
    
    def printSelectionTypes (type):
        selection = cmds.ls(selection=True)
        typeList = []
        if type == "selection" and len(selection) > 0:
            for obj in selection:
                if cmds.objectType(obj) not in typeList:
                    typeList.append(cmds.objectType(obj))
                try: # Too handle elements without shapes
                    shapeNode = cmds.listRelatives(obj, shapes=True) or []
                except:
                    pass
                if shapeNode != [] and cmds.objectType(shapeNode[0]) not in typeList:
                    typeList.append(cmds.objectType(shapeNode[0])+ " (Shape Node)") 

        if type == "all":
            #typeList = cmds.ls(nodeTypes=True) # Too see every type available
            everythingInScene = cmds.ls()
            for obj in everythingInScene:
                if cmds.objectType(obj) not in typeList:
                    typeList.append(cmds.objectType(obj))
                try: # Too handle elements without shapes
                    shapeNode = cmds.listRelatives(obj, shapes=True) or []
                except:
                    pass
                if shapeNode != [] and cmds.objectType(shapeNode[0]) not in typeList:
                    typeList.append(cmds.objectType(shapeNode[0]) + " (Shape Node)")

        if typeList != []:
            print("#" * 80)
            print(" " * 30 + " Types:")
            for type in typeList:
                print(type)
            print("#" * 80)
            cmds.headsUpMessage( 'Open Script Editor to see the list of types', verticalOffset=150 , time=5.0)
        else:
            cmds.warning("Nothing selected (or no types to be displayed)")

    # Updates many of the stored GUI values (Used by multiple elements)
    def getColorFromSelection(colorSlider): 
        selection = cmds.ls(selection=True)
        if len(selection) > 0:
            objAttrList = cmds.listAttr(selection[0]) or []
            if len(objAttrList) > 0 and "outlinerColor" in objAttrList and "useOutlinerColor" in objAttrList:
                extractedColor = cmds.getAttr(selection[0] + ".outlinerColor")
                if cmds.getAttr(selection[0] + ".useOutlinerColor"):
                    cmds.colorSliderGrp(colorSlider, e=True, rgb=extractedColor[0])
                else:
                    cmds.colorSliderGrp(colorSlider, e=True, rgb=extractedColor[0])
                    cmds.warning("Color extracted, but it looks like the object selected is not using a custom outliner color")
            else:
                cmds.warning("Something went wrong. Try selecting another object.")
        else:
            cmds.warning("Nothing Selected. Please select an object containing the outliner color you want to extract and try again.")
        

    # Updates many of the stored GUI values (Used by multiple elements)
    def updateActiveItems(): 
        # Updates Visibility and Use Settings
        settings["useContainsString"] = cmds.checkBoxGrp(containsStringOrNotCheckbox, q=True, value1=True)
        settings["useContainsNoString"] = cmds.checkBoxGrp(containsStringOrNotCheckbox, q=True, value2=True)
        settings["useContainsType"] = cmds.checkBoxGrp(containsTypeOrNotCheckbox, q=True, value1=True)
        settings["useContainsNoType"] = cmds.checkBoxGrp(containsTypeOrNotCheckbox, q=True, value2=True)
        settings["useVisibilityState"] = cmds.checkBox(useVisibilityState, q=True, value=True)
        settings["useOutlinerColor"] = cmds.checkBox(useOutlineColor, q=True, value=True)
        settings["useNoOutlinerColor"] = cmds.checkBox(useNoOutlineColor, q=True, value=True)
        
        
        # Updates Visibility
        if settings.get("useContainsString"):
            cmds.textField(containsNameTxtfield, e=True, en=True)
        else:
            cmds.textField(containsNameTxtfield, e=True, en=False)
            
        if settings.get("useContainsNoString"):
            cmds.textField(containsNoNameTxtfield, e=True, en=True)
        else:
            cmds.textField(containsNoNameTxtfield, e=True, en=False)
            
        if settings.get("useContainsType"):
            cmds.textField(containsTypeTxtfield, e=True, en=True)
        else:
            cmds.textField(containsTypeTxtfield, e=True, en=False)
        
        if settings.get("useContainsNoType"):
            cmds.textField(containsNoTypeTxtfield, e=True, en=True)
        else:
            cmds.textField(containsNoTypeTxtfield, e=True, en=False)
        
        if settings.get("useVisibilityState"):
            cmds.radioButton( visibilityRb1, e=True, en=True)
            cmds.radioButton( visibilityRb2, e=True, en=True)
        else:
            cmds.radioButton( visibilityRb1, e=True, en=False)
            cmds.radioButton( visibilityRb2, e=True, en=False)
        
        if settings.get("useOutlinerColor"):
            cmds.colorSliderGrp(hasOutlinerColorSliderOne, e=True, en=True)
        else:
            cmds.colorSliderGrp(hasOutlinerColorSliderOne, e=True, en=False)
        
        if settings.get("useNoOutlinerColor"):
            cmds.colorSliderGrp(hasNoOutlinerColorSliderOne, e=True, en=True)
        else:
            cmds.colorSliderGrp(hasNoOutlinerColorSliderOne, e=True, en=False)
        
        
        # Stores Values
        settings["storedContainsString"] = parseTextField(cmds.textField(containsNameTxtfield, q=True, text=True))
        settings["storedContainsNoString"] = parseTextField(cmds.textField(containsNoNameTxtfield, q=True, text=True))
        settings["storedContainsType"] = parseTextField(cmds.textField(containsTypeTxtfield, q=True, text=True))
        settings["storedContainsNoType"] = parseTextField(cmds.textField(containsNoTypeTxtfield, q=True, text=True))
        
        
        if settings.get('useContainsType') or settings.get('useContainsNoType'):
            cmds.optionMenu(shapeNodeBehaviorMenu, e=True, en=True)
        else:
            cmds.optionMenu(shapeNodeBehaviorMenu, e=True, en=False)
  
        settings["storedshapeNodeType"] = cmds.optionMenu(shapeNodeBehaviorMenu, q=True, value=True)
     
        settings["storedVisibilityState"]  = cmds.radioButton(visibilityRb1, q=True, select=True )
        settings["storedSaveAsQuickSelection"]  = cmds.radioButton(saveAsQuickSelectionRb1, q=True, select=True )

        settings["storedOutlinerColor"] = cmds.colorSliderGrp(hasOutlinerColorSliderOne, q=True, rgb=True)
        
        settings["storedNoOutlinerColor"] = cmds.colorSliderGrp(hasNoOutlinerColorSliderOne, q=True, rgb=True)

        
    # Updates elements to reflect the use disconnect function
    def updateStoredValuesAndRun(isNewSelection): 
        updateActiveItems() # Updates Stored Values
        settings["storedNewSelection"] = isNewSelection # New selection or existing one?
        manageSelection() # Runs main function


    cmds.showWindow(selectionManagerMainDialog)
    # mainDialog Ends Here =================================================================================

# Main Function 
def manageSelection():
    
    managedSelectionList = []
    toRemoveList = []
    toAddList = []
    
    
    # New Selection or Existing One
    if settings.get("storedNewSelection"):
        selection = cmds.ls()
    else:
        selection = cmds.ls(selection=True)

    # Starts Processing ################################################
    for obj in selection:
        
        #String Manager
        if settings.get('useContainsString'):
            for string in settings.get('storedContainsString'):
                if string in obj:
                    toAddList.append(obj)
                    
        if settings.get('useContainsNoString'):
            for string in settings.get('storedContainsNoString'):
                if string in obj:
                    toRemoveList.append(obj)
        
        # Type Manager (Define Vars First)
        if settings.get('useContainsType') or settings.get('useContainsNoType'):
            objType = cmds.objectType(obj)
            objShapeType = []
            if settings.get('storedshapeNodeType') != 'Ignore Shape Nodes':
                objShapeTypeExtract = cmds.listRelatives(obj, shapes=True) or []
                if len(objShapeTypeExtract) > 0:
                    objShapeType = cmds.objectType(objShapeTypeExtract[0])
        
        # Type Contains
        if settings.get('useContainsType'):
            for string in settings.get('storedContainsType'):
                if settings.get('storedshapeNodeType') == "Select Shapes as Objects" and string in objType:
                    toAddList.append(obj)
                    
                if settings.get('storedshapeNodeType') == "Select Parent Instead":
                    if string in objShapeType or string in objType:
                        if isObjectShape(obj) == False:
                            toAddList.append(obj)
                        else:
                            toRemoveList.append(obj)
                        
                if settings.get('storedshapeNodeType') == "Ignore Shape Nodes" and string in objType:
                    if isObjectShape(obj) == False:
                        toAddList.append(obj)
                    else:
                        toRemoveList.append(obj)
                    
                if settings.get('storedshapeNodeType') == "Select Both Parent and Shape" and string in objShapeType or string in objType:
                    toAddList.append(obj)
       
        # Type Doesn't Contain          
        if settings.get('useContainsNoType'):
            for string in settings.get('storedContainsNoType'):
                if settings.get('storedshapeNodeType') == "Select Shapes as Objects" and string in objType:
                    toRemoveList.append(obj)
                    
                if settings.get('storedshapeNodeType') == "Select Parent Instead":
                    if string in objShapeType or string in objType:
                        if isObjectShape(obj) == False:
                            toRemoveList.append(obj)
                        else:
                            pass
                        
                if settings.get('storedshapeNodeType') == "Ignore Shape Nodes" and string in objType:
                    if isObjectShape(obj) == False:
                        toRemoveList.append(obj)
                    else:
                        pass
                    
                if settings.get('storedshapeNodeType') == "Select Both Parent and Shape" and string in objShapeType or string in objType:
                    toRemoveList.append(obj)
        
        # Create Variables for Visibility and Outliner Color
        if settings.get('useVisibilityState') == True or settings.get('useOutlinerColor') == True or settings.get('useNoOutlinerColor') == True:
            objAttrList = cmds.listAttr(obj) or []
        
        # Check Visibility State
        if settings.get('useVisibilityState') == True and settings.get('storedVisibilityState') == True:
            if len(objAttrList) > 0 and "visibility" in objAttrList:
                if cmds.getAttr(obj + ".visibility"):
                    toAddList.append(obj)
        
        if settings.get('useVisibilityState') == True and settings.get('storedVisibilityState') == False:
            if len(objAttrList) > 0 and "visibility" in objAttrList:
                if cmds.getAttr(obj + ".visibility"):
                    toRemoveList.append(obj)
                    
        # Check outliner color      
        if settings.get('useOutlinerColor'):
            if len(objAttrList) > 0 and "outlinerColor" in objAttrList and "useOutlinerColor" in objAttrList:
                outlinerColor = cmds.getAttr(obj + ".outlinerColor")[0]
                storedOutlinerColor = settings.get('storedOutlinerColor')
                if outlinerColor[0] == storedOutlinerColor[0] and outlinerColor[1] == storedOutlinerColor[1] and outlinerColor[2] == storedOutlinerColor[2]:
                    toAddList.append(obj)
                        
        if settings.get('useNoOutlinerColor'):
            if len(objAttrList) > 0 and "outlinerColor" in objAttrList and "useOutlinerColor" in objAttrList:
                outlinerColor = cmds.getAttr(obj + ".outlinerColor")[0]
                storedNoOutlinerColor = settings.get('storedNoOutlinerColor')
                if outlinerColor[0] == storedNoOutlinerColor[0] and outlinerColor[1] == storedNoOutlinerColor[1] and outlinerColor[2] == storedNoOutlinerColor[2]:
                    toRemoveList.append(obj)

    # Finishes Processing ################################################
    
    
    # Check what was done to determine actions
    addOperations = [ 'useContainsString', 'useContainsType', 'useOutlinerColor',  ]
    removeOperations = [ 'useContainsNoString', 'useContainsNoType', 'useNoOutlinerColor' ]

    addOperationHappened = False
    removeOperationHappened = False
    for op in addOperations:
        if settings.get(op) == True:
            addOperationHappened = True
            
    for op in removeOperations:
        if settings.get(op) == True:
            removeOperationHappened = True
    
    if settings.get('useVisibilityState') == True and settings.get('storedVisibilityState') == True:
        addOperationHappened = True
        
    if settings.get('useVisibilityState') == True and settings.get('storedVisibilityState') == False:
        removeOperationHappened = True

    
    # Manage Selection
    if addOperationHappened == False and removeOperationHappened == False:
        managedSelectionList = selection
        cmds.warning("No option was active, everything was selected.")
        
    if addOperationHappened == False and removeOperationHappened == True:
        managedSelectionList = selection
    
    for objAdd in toAddList:
        if objAdd not in toRemoveList:
            managedSelectionList.append(objAdd)
        
    managedSelectionListCopy = managedSelectionList
    for objRemove in toRemoveList:
        for objCopy in managedSelectionListCopy:
            if objRemove in objCopy and objRemove in managedSelectionList:
                    managedSelectionList.remove(objRemove)
    
    cmds.select(managedSelectionList, ne=True)
 

    # ============================= End of Main Function =============================

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

# If object exists, select it
def ifObjectsInListExistsSelect(list): ################################# EDITING
    for obj in list:
        if cmds.objExists(obj):
            cmds.select(obj)
            cmds.headsUpMessage(obj + " selected", verticalOffset=150 )
        else:
            cmds.warning("Object doesn't exist! Did you delete or rename it after loading?")

# If object exists, select it
def ifExistsSelect(obj):
    if cmds.objExists(obj):
        cmds.select(obj)
        cmds.headsUpMessage(obj + " selected", verticalOffset=150 )
    else:
        cmds.warning("Object doesn't exist! Did you delete or rename it after loading?")

# storedListManager
def storedListManager(list):
    missingElements = False
    foundElements = []
    print("#" * 32 + " Objects List " + "#" * 32)
    for obj in list:
        if cmds.objExists(obj):
            print(obj)
            foundElements.append(obj)
        else:
            print(obj + " no longer exists!")
            missingElements = True
    print("#" * 80)
    if missingElements:
        cmds.headsUpMessage( 'It looks like you are missing some elements! Open script editor for more information', verticalOffset=150 , time=5.0)
    else:
        cmds.headsUpMessage( 'Stored elements selected (Open script editor to see a list)', verticalOffset=150 , time=5.0)
    if list != []:
        cmds.select(foundElements)

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

# Start current "Main"
selectionManagerMainDialog()