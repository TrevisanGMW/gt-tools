import maya.cmds as cmds

# rigLayer Generator -> Simple script used to create rigLayers
# @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-02-04
# Last update - 2020-02-18 - Added Color Picker
#
# To do: 
# Add option to use a different method of position matching (use channelbox values)
# Add option to use joint's orientation instead of rotation

scriptVersion = "v1.1";

settings = { 'outlinerColor': [0,1,0] }

# Main Form ============================================================================
def createRigLayerDialog():
    if cmds.window("createRigLayerDialog", exists =True):
        cmds.deleteUI("createRigLayerDialog")    

    # mainDialog Start Here =================================================================================
    
    # Build UI
    createRigLayerDialog = cmds.window("createRigLayerDialog", title="gt_rigLayer " + scriptVersion,\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =False)
    columnMain = cmds.columnLayout() 

    form = cmds.formLayout(p=columnMain)

    contentMain = cmds.columnLayout(adj = True)

    cmds.text("")
    cmds.text("GT - Rig Layer Generator - " + scriptVersion, bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.text("  ")
    cmds.text("      This script creates a rigLayer (transform)       ")
    cmds.text('      for selected elements  ')

    cmds.separator(h=15, p=contentMain)
    
    midContainer = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 25)
    rigLayerType = cmds.optionMenu(p=midContainer, label='  Layer Type')
    cmds.menuItem( label='Group' )
    cmds.menuItem( label='Joint' )
    cmds.menuItem( label='Locator' )
    
    rigLayerParentType = cmds.optionMenu(p=midContainer, label='  Parent Type')
    cmds.menuItem( label='Selection' )
    cmds.menuItem( label='Parent' )
    cmds.text("  ",p=midContainer)
    
    #cmds.separator(h=15, p=contentMain)
    colorContainer1 = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 10)
    colorContainer = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 25)
    #cmds.colorSliderGrp( p=colorContainer, label='Blue', rgb=(0, 0, 1) )
    colorSlider = cmds.colorSliderGrp(label='Outliner Color  ', rgb=(settings.get("outlinerColor")[0], \
                                                                settings.get("outlinerColor")[1], settings.get("outlinerColor")[2]),\
                                                                columnWidth=((1,85),(3,130)), cc=lambda x:updateStoredValues())
    #colorSlider = cmds.colorSliderGrp( label='', adj=2, columnWidth=((1,1),(3,1)))
    cmds.separator(h=15, p=contentMain)
    bottomContainer = cmds.rowColumnLayout(p=contentMain,adj=True)
    cmds.text('Layer Tag:',p=bottomContainer)
    desiredTag = cmds.textField(p = bottomContainer, text="_rigLayer", enterCommand=lambda x:createRigLayer(parseTextField(cmds.textField(desiredTag, q=True, text=True))[0],\
                                                                        cmds.optionMenu(rigLayerParentType, q=True, value=True),\
                                                                        cmds.optionMenu(rigLayerType, q=True, value=True)))
    cmds.button(p=bottomContainer, l ="Generate", bgc=(.6, .8, .6), c=lambda x:createRigLayer(parseTextField(cmds.textField(desiredTag, q=True, text=True))[0],\
                                                                        cmds.optionMenu(rigLayerParentType, q=True, value=True),\
                                                                        cmds.optionMenu(rigLayerType, q=True, value=True)))
                                                                                                                              
    # Updates Stored Values
    def updateStoredValues():
        settings["outlinerColor"] = cmds.colorSliderGrp(colorSlider, q=True, rgb=True)
        #print(settings.get("outlinerColor")) Debugging
        
    cmds.showWindow(createRigLayerDialog)

    # mainDialog Ends Here =================================================================================


# Main Function
# layerTag = string to use as tag
# parentType = parent, or selection (determines the pivot)
# layerType = joint, locator or group(also nothing) : what the rig layer is
def createRigLayer(layerTag,parentType,layerType):
    selection = cmds.ls(selection=True)

    for obj in selection:
        cmds.select( clear=True )
        if layerType == "Joint":
            rigLayer = cmds.joint(name=(obj + layerTag))
        if layerType == "Locator":
            rigLayer = cmds.spaceLocator(name=(obj + layerTag))[0]
        if layerType == "Group":
            rigLayer = cmds.group(name=(obj + layerTag),empty=True)
             
        cmds.setAttr ( rigLayer + ".useOutlinerColor" , True)
        cmds.setAttr ( rigLayer  + ".outlinerColor" , settings.get("outlinerColor")[0],settings.get("outlinerColor")[1], settings.get("outlinerColor")[2])
        selectionParent = cmds.listRelatives(obj, parent=True) or []
        
        if len(selectionParent) != 0 and parentType == "Parent" : 
            constraint = cmds.parentConstraint(selectionParent[0],rigLayer)
            cmds.delete(constraint)
            cmds.parent( rigLayer, selectionParent[0])
            cmds.parent( obj, rigLayer) 
        elif len(selectionParent) == 0 and parentType == "Parent" :
            cmds.parent( obj, rigLayer)
            
        if len(selectionParent) != 0 and parentType == "Selection" : 
            constraint = cmds.parentConstraint(obj,rigLayer)
            cmds.delete(constraint)
            cmds.parent( rigLayer, selectionParent[0])
            cmds.parent( obj, rigLayer)
        elif len(selectionParent) == 0 and parentType == "Selection" :
            constraint = cmds.parentConstraint(obj,rigLayer)
            cmds.delete(constraint)
            cmds.parent( obj, rigLayer)

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

#Run Script
createRigLayerDialog()