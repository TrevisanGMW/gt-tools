import maya.cmds as cmds
import maya.mel as mel

# Simple Script used to export the Blue Heron Rig
scriptVersion = "3.0"
rigVersion = "Made for \"Raven_Rig.008\""

def ravenDialog():
    if cmds.window("ravenDialog", exists =True):
        cmds.deleteUI("ravenDialog")    

    # mainDialog Start Here =================================================================================

    ravenDialog = cmds.window("ravenDialog", title="BH - " + scriptVersion,\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =True)
    columnMain = cmds.columnLayout() 
    form = cmds.formLayout(p=columnMain)
    contentMain = cmds.columnLayout(adj = True)
    
    cmds.text(" Raven Exporter - v" + scriptVersion, bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.text(rigVersion,  fn="boldLabelFont")
    cmds.separator(h=10, p=contentMain)
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
 
    cmds.showWindow(ravenDialog)
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


    usingProxy = cmds.getAttr('mainCtrl.useProxy')
    
    cmds.parent( 'rootJnt', world=True )
    cmds.parent( 'tail_feathers_primary_mid_grp', world=True )
    cmds.parent( 'wing_feathers_primary_mid_grp', world=True )
    cmds.delete('wing_feathers_primary_lo_grp')
    cmds.delete('tail_feathers_primary_lo_grp')
    
    if usingProxy:
        cmds.parent( 'raven_lo', world=True )
        cmds.delete('tail_feathers_primary_mid_grp')
        cmds.delete('wing_feathers_primary_mid_grp')
    else:
        cmds.parent( 'raven_mid', world=True )
    
    cmds.delete('Raven')


def bakeSimulation():
    mel.eval("BakeSimulationOptions;")
    
    
def selectRootJnt():
    allJnts = cmds.ls(type="joint")
    
    for jnt in allJnts:
        if "rootJnt" in jnt:
            cmds.select("rootJnt", hierarchy=True)


#Start current "Main"
ravenDialog()