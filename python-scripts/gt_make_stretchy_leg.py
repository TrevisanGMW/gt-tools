"""
 Create Stretchy Legs (With condition for scaling)
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-03-13

 1.1 - 2020-06-07
 Fixed random window widthHeight issue.
 Updated naming convention to make it clearer. (PEP8)
 
 1.2 - 2020-06-17
 Added window icon
 Added help menu
 Changed GUI
 
 TO DO:
 Add textfields for suffixes
 Ignore systems without controls?
 
"""
import maya.cmds as cmds
import maya.mel as mel
from maya import OpenMayaUI as omui

try:
    from shiboken2 import wrapInstance
except ImportError:
    from shiboken import wrapInstance

try:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QWidget
except ImportError:
    from PySide.QtGui import QIcon, QWidget

# Script Name
script_name = "GT - Make Stretchy Legs"

# Version:
script_version = "1.2";

settings = { 'outlinerColor': [0,1,0] }

# Main Form ============================================================================
def build_gui_make_stretchy_legs():
    window_name = "build_gui_make_stretchy_legs"
    if cmds.window(window_name, exists =True):
        cmds.deleteUI(window_name)    

    # Main GUI Start Here =================================================================================
    
    # Build UI
    build_gui_make_stretchy_legs = cmds.window(window_name, title=script_name + "  v" + script_version,\
                          titleBar=True, mnb=False, mxb=False, sizeable =True)

    cmds.window(window_name, e=True, s=True, wh=[1,1])
    
    column_main = cmds.columnLayout() 

    form = cmds.formLayout(p=column_main)

    content_main = cmds.columnLayout(adj = True)

    # Title Text
    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 10)], p=content_main) # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 200), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)], p=content_main) # Title Column
    cmds.text(" ", bgc=[0,.5,0]) # Tiny Empty Green Space
    cmds.text(script_name + " v" + script_version, bgc=[0,.5,0],  fn="boldLabelFont", align="left")
    cmds.button( l ="Help", bgc=(0, .5, 0), c=lambda x:build_gui_help_make_stretchy_legs())
    cmds.separator(h=5, style='none') # Empty Space
    
    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1,10)], p=content_main)
    
    cmds.text(l='This script creates a simple stretchy leg setup.', align="center")
    cmds.text(l='Select your ikHandle and click on "Make Stretchy', align="center")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Important:', align="center", fn="boldLabelFont")
    cmds.text(l='It assumes that you have a curve driving your', align="center")
    cmds.text(l='ikHandle as a control.', align="center")
    
    cmds.separator(h=7, style='none') # Empty Space
    
    cmds.separator(h=5)
    cmds.separator(h=7, style='none') # Empty Space
    
    cmds.button(l ="Make Stretchy", bgc=(.6, .8, .6), c=lambda x:make_stretchy_legs())                                                                                                 
    cmds.separator(h=10, style='none') # Empty Space
    
    # Show and Lock Window
    cmds.showWindow(build_gui_make_stretchy_legs)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/ikSCsolver.svg')
    widget.setWindowIcon(icon)

    # Main GUI Ends Here =================================================================================

# Creates Help GUI
def build_gui_help_make_stretchy_legs():
    window_name = "build_gui_help_make_stretchy_legs"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)


    cmds.window(window_name, title= script_name + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1,1])

    cmds.columnLayout("main_column", p= window_name)
   
    # Title Text
    cmds.separator(h=12, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p="main_column") # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column") # Title Column
    cmds.text(script_name + " Help", bgc=[0,.5,0],  fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p="main_column") # Empty Space

    
    # Body ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p="main_column")
    cmds.text(l='This script creates a simple stretchy leg setup.', align="center")
    cmds.text(l='Select your ikHandle and click on "Make Stretchy', align="center")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Important:', align="center", fn="boldLabelFont")
    cmds.text(l='It assumes that you have a curve driving your', align="center")
    cmds.text(l='ikHandle as a control.', align="center")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 140),(2, 140)], cs=[(1,10),(2, 0)], p="main_column")
    cmds.text('Guilherme Trevisan  ')
    cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1,1,1])
    cmds.rowColumnLayout(nc=2, cw=[(1, 140),(2, 140)], cs=[(1,10),(2, 0)], p="main_column")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1,1,1])
    cmds.separator(h=7, style='none') # Empty Space
    
    # Close Button 
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p="main_column")
    cmds.separator(h=10, style='none')
    cmds.button(l='OK', h=30, c=lambda args: close_help_gui())
    cmds.separator(h=8, style='none')
    
    # Show and Lock Window
    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/question.png')
    widget.setWindowIcon(icon)
    
    def close_help_gui():
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)


def change_outliner_color(objList, colorRGB):
    for obj in objList:
        if cmds.objExists(obj):
            cmds.setAttr ( obj + ".useOutlinerColor" , True)
            cmds.setAttr ( obj + ".outlinerColor" , colorRGB[0],colorRGB[1],colorRGB[2])


def make_stretchy_legs():
    
    ikHandle = cmds.ls(selection=True, type="ikHandle")
    
    ikHandle_manipulated_joints = cmds.ikHandle(ikHandle, q=True, jointList=True)

    top_joint_position = cmds.getAttr(ikHandle_manipulated_joints[0] + '.translate')
    ikHandle_position = cmds.getAttr(ikHandle[0] + '.translate')

    distance_one = cmds.distanceDimension(sp=top_joint_position[0], ep=ikHandle_position[0] )
    distance_one_transform = cmds.listRelatives(distance_one, parent=True)[0]
    distance_one_locators = cmds.listConnections(distance_one)

    # Rename Distance One Nodes
    name_top_locator = (ikHandle_manipulated_joints[0].replace("_IK_", "")).replace("Jnt","") # Change this, use a textbox to query user
    name_bottom_locator = ((ikHandle[0].replace("_IK_","")).replace("_ikHandle","")).replace("RP","")
    name_distance_node = name_bottom_locator
    distance_node_one = cmds.rename(distance_one_transform, name_distance_node + "_strechyTerm_01")
    top_locator_one = cmds.rename(distance_one_locators[0], name_top_locator + "_ST_01")
    bottom_locator_one = cmds.rename(distance_one_locators[1], name_bottom_locator + "_ST_02")

    distance_two = cmds.distanceDimension(sp=(0,0,0), ep=(1,1,1) )
    distance_two_transform = cmds.listRelatives(distance_two, parent=True)[0]
    distance_two_locators = cmds.listConnections(distance_two)
    cmds.xform(distance_two_locators[0], t=top_joint_position[0] )
    cmds.xform(distance_two_locators[1], t=ikHandle_position[0] )

    #Rename Distance Two Nodes
    distance_node_two = cmds.rename(distance_two_transform, name_distance_node + "_strechyCondition_01")
    top_locator_two = cmds.rename(distance_two_locators[0], name_top_locator + "_SC_01")
    bottom_locator_two = cmds.rename(distance_two_locators[1], name_bottom_locator + "_SC_02")

    stretchy_grp = cmds.group(name=name_top_locator + "_stretchySystem_grp", empty=True, world=True)
    cmds.parent( distance_node_one, stretchy_grp )
    cmds.parent( top_locator_one, stretchy_grp )
    cmds.parent( bottom_locator_one, stretchy_grp )
    cmds.parent( distance_node_two, stretchy_grp )
    cmds.parent( top_locator_two, stretchy_grp )
    cmds.parent( bottom_locator_two, stretchy_grp )

    change_outliner_color([distance_node_one,top_locator_one,bottom_locator_one],[0,1,0]) 
    change_outliner_color([distance_node_two,top_locator_two,bottom_locator_two],[1,0,0])

    mel.eval('AEdagNodeCommonRefreshOutliners();') #Make sure outliner colors update

    # Start connecting everything ----------------------------------------

    stretch_normalization_node = cmds.createNode('multiplyDivide', name=name_distance_node + "_distNormalization_divide")
    cmds.connectAttr('%s.distance' % distance_node_one, '%s.input1X' % stretch_normalization_node)
    cmds.connectAttr('%s.distance' % distance_node_two, '%s.input2X' % stretch_normalization_node) # Check if necessary

    cmds.setAttr( stretch_normalization_node + ".operation", 2)

    stretch_condition_node = cmds.createNode('condition', name=name_distance_node + "_strechyCondition_condition")
    cmds.setAttr( stretch_condition_node + ".operation", 3)
    cmds.connectAttr('%s.distance' % distance_node_one, '%s.firstTerm' % stretch_condition_node)
    cmds.connectAttr('%s.distance' % distance_node_two, '%s.secondTerm' % stretch_condition_node)
    cmds.connectAttr('%s.outputX' % stretch_normalization_node, '%s.colorIfTrueR' % stretch_condition_node)

    cmds.connectAttr('%s.outColorR' % stretch_condition_node, '%s.scaleX' % ikHandle_manipulated_joints[0])
    cmds.connectAttr('%s.outColorR' % stretch_condition_node, '%s.scaleX' % ikHandle_manipulated_joints[1])


    cmds.pointConstraint (ikHandle_manipulated_joints[0], top_locator_one)
    cmds.pointConstraint (ikHandle_manipulated_joints[0], top_locator_two)

    #Check if already has control before doing this
    try: 
        ikHandle_parent_constraint = cmds.listRelatives(ikHandle, children=True,type='parentConstraint' )[0]
        ikHandle_ctrl = cmds.parentConstraint(ikHandle_parent_constraint, q=True, targetList=True)
        cmds.parentConstraint (ikHandle_ctrl, bottom_locator_one)
    except:
        pass


#Run Script
build_gui_make_stretchy_legs()