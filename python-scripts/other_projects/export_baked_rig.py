import maya.cmds as cmds
import maya.mel as mel

# Simple Script used to export rig into game engines
scriptVersion = "1.0"

def exportBakedRigDialog():
    if cmds.window("exportBakedRigDialog", exists =True):
        cmds.deleteUI("exportBakedRigDialog")    

    # mainDialog Start Here =================================================================================

    exportBakedRigDialog = cmds.window("exportBakedRigDialog", title="BR - " + scriptVersion,\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =True)
    columnMain = cmds.columnLayout() 
    form = cmds.formLayout(p=columnMain)
    contentMain = cmds.columnLayout(adj = True)
    
    cmds.text("Step: 1")
    cmds.button(p=contentMain, l ="Import References", c=lambda x:importReferences())
    cmds.separator(h=10, p=contentMain)
    cmds.text("Step: 2")
    cmds.button(p=contentMain, l ="Bake Simulation", c=lambda x:bakeSimulation())
    cmds.separator(h=10, p=contentMain)
    cmds.text("Step: 3")
    container = cmds.rowColumnLayout( p=contentMain, numberOfRows=1)
    cmds.button(p=container, l ="Export All", c=lambda x:mel.eval("Export;"), w=100)
    ankleStatus = cmds.button(p=container, l ="Export Selection", c=lambda x:mel.eval("ExportSelection;"))
 
    cmds.showWindow(exportBakedRigDialog)
    # mainDialog Ends Here =================================================================================

def importReferences():
    try:
        refs = cmds.ls(rf=True)
        for i in refs:
            rFile = cmds.referenceQuery(i, f=True)
            cmds.file(rFile, importReference=True)
    except:
        cmds.warning("Something went wrong. Maybe you don't have any references to import?")


def bakeSimulation():
    cmds.select(cmds.ls(type="joint"))
    mel.eval("BakeSimulationOptions;")


#Start current "Main"
exportBakedRigDialog()