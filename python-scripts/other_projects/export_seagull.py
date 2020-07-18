import maya.cmds as cmds
import maya.mel as mel

# Simple Script used to export the Blue Heron Rig
scriptVersion = "1.0"

def seagullDialog():
    if cmds.window("seagullDialog", exists =True):
        cmds.deleteUI("seagullDialog")    

    # mainDialog Start Here =================================================================================

    seagullDialog = cmds.window("seagullDialog", title="BH - " + scriptVersion,\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =True)
    columnMain = cmds.columnLayout() 
    form = cmds.formLayout(p=columnMain)
    contentMain = cmds.columnLayout(adj = True)
    
    cmds.text(" Seagull Exporter - v" + scriptVersion, bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.text(" Made for Seagull_Rig.003.ma",  fn="boldLabelFont")
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
 
    cmds.showWindow(seagullDialog)
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
    
    if usingProxy:
        cmds.parent( 'seagull_lo', world=True )
    else:
        cmds.parent( 'seagull_mid', world=True )
        #cmds.parent( 'feathers_mid', world=True )
        cmds.parent( 'wing_feathers_mid', world=True )
        cmds.parent( 'tail_feathers_mid', world=True )
        
        
    
    cmds.delete('Seagull')


def bakeSimulation():
    mel.eval("BakeSimulationOptions;")
    
    
def selectRootJnt():
    allJnts = cmds.ls(type="joint")
    
    for jnt in allJnts:
        if "rootJnt" in jnt:
            cmds.select("rootJnt", hierarchy=True)


#Start current "Main"
seagullDialog()