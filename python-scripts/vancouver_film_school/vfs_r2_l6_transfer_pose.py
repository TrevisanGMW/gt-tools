'''
Simple script used to help students understand how to transfer attributes
Select source object 1st, target object 2nd, then run script.
For more complete version of this script check GT Tools
'''

# 1. Import Maya Commands.
import maya.cmds as cmds

# 2. Grabs Selection
selection = cmds.ls(selection=True)

# 3. Extracts Transforms From Source Object. 
# "[0]" grabs the first result from the returned list.
source_translate = cmds.getAttr(selection[0] + ".translate")[0]
source_rotate = cmds.getAttr(selection[0] + ".rotate")[0]
source_scale = cmds.getAttr(selection[0] + ".scale")[0]

# 4. Applies Transforms To The Target Object.
# XYZ = [0][1][2]   thus   [0] = X   [1] = Y   [2] = Z
cmds.setAttr(selection[1] + ".translateX", source_translate[0])
cmds.setAttr(selection[1] + ".translateY", source_translate[1])
cmds.setAttr(selection[1] + ".translateZ", source_translate[2]*-1) # "*-1" inverts the value

cmds.setAttr(selection[1] + ".rotateX", source_rotate[0])
cmds.setAttr(selection[1] + ".rotateY", source_rotate[1])
cmds.setAttr(selection[1] + ".rotateZ", source_rotate[2])

cmds.setAttr(selection[1] + ".scaleX", source_scale[0])
cmds.setAttr(selection[1] + ".scaleY", source_scale[1])
cmds.setAttr(selection[1] + ".scaleZ", source_scale[2])