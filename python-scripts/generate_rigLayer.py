import maya.cmds as cmds

# rigLayer Generator -> Simple script used to create rigLayers.
# @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-02-04
# Last update - 2020-02-04

scriptVersion = "1.0";


# Main Form ============================================================================
def createRigLayerDialog():
    if cmds.window("createRigLayerDialog", exists =True):
        cmds.deleteUI("createRigLayerDialog")    

    # mainDialog Start Here =================================================================================

    createRigLayerDialog = cmds.window("createRigLayerDialog", title="rigLayer v" + scriptVersion,\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =False)

    columnMain = cmds.columnLayout() 

    form = cmds.formLayout(p=columnMain)

    contentMain = cmds.columnLayout(adj = True)

    cmds.text("")
    cmds.text("rigLayer Generator - v" + scriptVersion, bgc=[0,.5,0],  fn="boldLabelFont")
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
    
    
    bottomContainer = cmds.rowColumnLayout(p=contentMain,adj=True)
    cmds.text('Layer Tag:',p=bottomContainer)
    desiredTag = cmds.textField(p = bottomContainer, text="_rigLayer", enterCommand=lambda x:createRigLayer(parseTextField(cmds.textField(desiredTag, q=True, text=True))[0],\
                                                                        cmds.optionMenu(rigLayerParentType, q=True, value=True),\
                                                                        cmds.optionMenu(rigLayerType, q=True, value=True)))
    cmds.button(p=bottomContainer, l ="Generate", bgc=(.6, .8, .6), c=lambda x:createRigLayer(parseTextField(cmds.textField(desiredTag, q=True, text=True))[0],\
                                                                        cmds.optionMenu(rigLayerParentType, q=True, value=True),\
                                                                        cmds.optionMenu(rigLayerType, q=True, value=True)))

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
        cmds.setAttr ( rigLayer  + ".outlinerColor" , 0,1,0)
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
            

#Run Script
createRigLayerDialog()