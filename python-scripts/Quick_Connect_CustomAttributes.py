import maya.cmds as cmds

#To do:
# Build a UI
# Load OBJ option
# Add Reverse Node Option

selection = cmds.ls(selection=True)

cmds.connectAttr('%s.curveSystemRotation' % selection[0], '%s.input2X' % selection[1]) 
cmds.connectAttr('%s.curveSystemRotation' % selection[0], '%s.input2Y' % selection[1]) 
cmds.connectAttr('%s.curveSystemRotation' % selection[0], '%s.input2Z' % selection[1]) 


'''


#Translate Only
cmds.connectAttr('%s.rotate' % selection[0], '%s.input1' % selection[1]) 
cmds.connectAttr('%s.output' % selection[1], '%s.rotate' % selection[2])

# Every attribute
cmds.connectAttr('%s.rx' % selection[0], '%s.input1X' % selection[1]) 
cmds.connectAttr('%s.ry' % selection[0], '%s.input1Y' % selection[1])
cmds.connectAttr('%s.rz' % selection[0], '%s.input1Z' % selection[1])

cmds.connectAttr('%s.outputX' % selection[1], '%s.rx' % selection[2])
cmds.connectAttr('%s.outputY' % selection[1], '%s.ry' % selection[2])
cmds.connectAttr('%s.outputZ' % selection[1], '%s.rz' % selection[2])
'''