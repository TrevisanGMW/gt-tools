import maya.cmds as cmds
import maya.mel as mel


# Create Stretchy Legs (With condition for scaling)
# @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-03-13
#

scriptVersion = "v1.0";

settings = { 'outlinerColor': [0,1,0] }

# Main Form ============================================================================
def makeStretchyLegsDialog():
    if cmds.window("makeStretchyLegsDialog", exists =True):
        cmds.deleteUI("makeStretchyLegsDialog")    

    # mainDialog Start Here =================================================================================
    
    # Build UI
    makeStretchyLegsDialog = cmds.window("makeStretchyLegsDialog", title="gt_stretchyLeg " + scriptVersion,\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =True)
    columnMain = cmds.columnLayout() 

    form = cmds.formLayout(p=columnMain)

    contentMain = cmds.columnLayout(adj = True)

    cmds.text("")
    cmds.text("GT - Make Stretchy Legs - " + scriptVersion, bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.text("  ")
    cmds.text("      This script creates a simple stretchy leg setup.     ")
    cmds.text('        ')
    cmds.text('      Select your ikHandle and click on "Make Stretchy"  ')
    cmds.text('        ')
    cmds.text('      It assumes that you have a curve driving your  ')
    cmds.text('      ikHandle as a control.  ')

    cmds.separator(h=15)
    
    cmds.button(l ="Make Stretchy", bgc=(.6, .8, .6), c=lambda x:makeStretchyLegs())                                                                                                 

    cmds.showWindow(makeStretchyLegsDialog)

    # mainDialog Ends Here =================================================================================




def changeOutlinerColor(objList, colorRGB):
    for obj in objList:
        if cmds.objExists(obj):
            cmds.setAttr ( obj + ".useOutlinerColor" , True)
            cmds.setAttr ( obj + ".outlinerColor" , colorRGB[0],colorRGB[1],colorRGB[2])


def makeStretchyLegs():
    
    ikHandle = cmds.ls(selection=True, type="ikHandle")
    
    ikHandleManipulatedJoints = cmds.ikHandle(ikHandle, q=True, jointList=True)

    topJointPosition = cmds.getAttr(ikHandleManipulatedJoints[0] + '.translate')
    ikHandlePosition = cmds.getAttr(ikHandle[0] + '.translate')

    distanceOne = cmds.distanceDimension(sp=topJointPosition[0], ep=ikHandlePosition[0] )
    distanceOneTransform = cmds.listRelatives(distanceOne, parent=True)[0]
    distanceOneLocators = cmds.listConnections(distanceOne)

    #Rename Distance One Nodes
    nameTopLocator = (ikHandleManipulatedJoints[0].replace("_IK_", "")).replace("Jnt","") # Change this, use a textbox to query user
    nameBottomLocator = ((ikHandle[0].replace("_IK_","")).replace("_ikHandle","")).replace("RP","")
    nameDistanceNode = nameBottomLocator
    distanceNodeOne = cmds.rename(distanceOneTransform, nameDistanceNode + "_strechyTerm_01")
    topLocatorOne = cmds.rename(distanceOneLocators[0], nameTopLocator + "_ST_01")
    bottomLocatorOne = cmds.rename(distanceOneLocators[1], nameBottomLocator + "_ST_02")

    distanceTwo = cmds.distanceDimension(sp=(0,0,0), ep=(1,1,1) )

    distanceTwoTransform = cmds.listRelatives(distanceTwo, parent=True)[0]
    distanceTwoLocators = cmds.listConnections(distanceTwo)
    cmds.xform(distanceTwoLocators[0], t=topJointPosition[0] )
    cmds.xform(distanceTwoLocators[1], t=ikHandlePosition[0] )

    #Rename Distance Two Nodes
    distanceNodeTwo = cmds.rename(distanceTwoTransform, nameDistanceNode + "_strechyCondition_01")
    topLocatorTwo = cmds.rename(distanceTwoLocators[0], nameTopLocator + "_SC_01")
    bottomLocatorTwo = cmds.rename(distanceTwoLocators[1], nameBottomLocator + "_SC_02")

    stretchyGrp = cmds.group(name=nameDistanceNode + "_StretchySystem", empty=True, world=True)
    cmds.parent( distanceNodeOne, stretchyGrp )
    cmds.parent( topLocatorOne, stretchyGrp )
    cmds.parent( bottomLocatorOne, stretchyGrp )
    cmds.parent( distanceNodeTwo, stretchyGrp )
    cmds.parent( topLocatorTwo, stretchyGrp )
    cmds.parent( bottomLocatorTwo, stretchyGrp )

    changeOutlinerColor([distanceNodeOne,topLocatorOne,bottomLocatorOne],[0,1,0]) 
    changeOutlinerColor([distanceNodeTwo,topLocatorTwo,bottomLocatorTwo],[1,0,0])

    mel.eval('AEdagNodeCommonRefreshOutliners();') #Make sure outliner colors update

    # Start connecting everything ----------------------------------------

    stretchNormalizationNode = cmds.createNode('multiplyDivide', name=nameDistanceNode + "_distNormalization_divide")
    cmds.connectAttr('%s.distance' % distanceNodeOne, '%s.input1X' % stretchNormalizationNode)
    cmds.connectAttr('%s.distance' % distanceNodeTwo, '%s.input2X' % stretchNormalizationNode) # Check if necessary

    cmds.setAttr( stretchNormalizationNode + ".operation", 2)

    stretchConditionNode = cmds.createNode('condition', name=nameDistanceNode + "_strechyCondition_condition")
    cmds.setAttr( stretchConditionNode + ".operation", 3)
    cmds.connectAttr('%s.distance' % distanceNodeOne, '%s.firstTerm' % stretchConditionNode)
    cmds.connectAttr('%s.distance' % distanceNodeTwo, '%s.secondTerm' % stretchConditionNode)
    cmds.connectAttr('%s.outputX' % stretchNormalizationNode, '%s.colorIfTrueR' % stretchConditionNode)

    cmds.connectAttr('%s.outColorR' % stretchConditionNode, '%s.scaleX' % ikHandleManipulatedJoints[0])
    cmds.connectAttr('%s.outColorR' % stretchConditionNode, '%s.scaleX' % ikHandleManipulatedJoints[1])


    cmds.pointConstraint (ikHandleManipulatedJoints[0], topLocatorOne)
    cmds.pointConstraint (ikHandleManipulatedJoints[0], topLocatorTwo)

    #Check if already has control before doing this
    try: 
        ikHandleParentConstraint = cmds.listRelatives(ikHandle, children=True,type='parentConstraint' )[0]
        ikHandleCtrl = cmds.parentConstraint(ikHandleParentConstraint, q=True, targetList=True)
        cmds.parentConstraint (ikHandleCtrl, bottomLocatorOne)
    except:
        pass



#Run Script
makeStretchyLegsDialog()