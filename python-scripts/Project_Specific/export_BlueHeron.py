import maya.cmds as cmds
import maya.mel as mel

# Simple Script used to export the Blue Heron Rig
scriptVersion = "1.0"

def blueHeronDialog():
    if cmds.window("blueHeronDialog", exists =True):
        cmds.deleteUI("blueHeronDialog")    

    # mainDialog Start Here =================================================================================

    blueHeronDialog = cmds.window("blueHeronDialog", title="BH - " + scriptVersion,\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =True)
    columnMain = cmds.columnLayout() 
    form = cmds.formLayout(p=columnMain)
    contentMain = cmds.columnLayout(adj = True)
    
    cmds.text("Step: 1")
    cmds.button(p=contentMain, l ="Import References", c=lambda x:importReferences())
    cmds.separator(h=10, p=contentMain)
    cmds.text("Step: 2")
    cmds.button(p=contentMain, l ="Select rootJnt (Hierarchy)", c=lambda x:selectRootJnt())
    cmds.separator(h=10, p=contentMain)
    cmds.text("Step: 3")
    cmds.button(p=contentMain, l ="Bake Simulation", c=lambda x:bakeSimulation())
    cmds.separator(h=10, p=contentMain)
    cmds.text("Step: 4")
    cmds.button(p=contentMain, l ="Prepare Scene for Export", bgc=(.6, .8, .6), c=lambda x:prepareScene())
    cmds.separator(h=10, p=contentMain)
    cmds.text("Step: 5")
    container = cmds.rowColumnLayout( p=contentMain, numberOfRows=1)
    cmds.button(p=container, l ="Export All", c=lambda x:mel.eval("Export;"), w=100)
    cmds.button(p=container, l ="Export Selection", c=lambda x:mel.eval("ExportSelection;"))
 
    cmds.showWindow(blueHeronDialog)
    # mainDialog Ends Here =================================================================================

def importReferences():
    try:
        refs = cmds.ls(rf=True)
        for i in refs:
            rFile = cmds.referenceQuery(i, f=True)
            cmds.file(rFile, importReference=True)
    except:
        cmds.warning("Something went wrong. Maybe you don't have any references to import?")

def prepareScene():

    allGroups = cmds.ls(type="transform")
    allJnts = cmds.ls(type="joint")
    
    for jnt in allJnts:
        if "rootJnt" in jnt:
            if len(cmds.listRelatives(jnt, parent=True) or []) != 0:
                cmds.parent( jnt, world=True )
    
    usingProxy = cmds.getAttr('mainCtrl.useProxy')
    
    if usingProxy:
        for obj in allGroups:
            if "blue_heron_mid" == obj or "BlueHeronBody_lo" == obj:
                if len(cmds.listRelatives(obj, parent=True) or []) != 0:
                    cmds.parent( obj, world=True )
    else:
        for obj in allGroups:
                if "blue_heron_mid" == obj:
                    if len(cmds.listRelatives(obj, parent=True) or []) != 0:
                        cmds.parent( obj, world=True )
    
    for obj in allGroups:
        if "Blue_Heron" in obj :
            cmds.delete(obj)

    if usingProxy:
        for obj in allGroups:
            if "blue_heron_mid" == obj:
                cmds.rename(obj, obj.replace("mid","lo"))
            if "blueHeronBody_mid" == obj:
                cmds.delete(obj)

def bakeSimulation():
    mel.eval("BakeSimulationOptions;")
    
    
def selectRootJnt():
    allJnts = cmds.ls(type="joint")
    
    for jnt in allJnts:
        if "rootJnt" in jnt:
            cmds.select("rootJnt", hierarchy=True)


#Start current "Main"
blueHeronDialog()