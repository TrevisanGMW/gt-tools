import maya.cmds as cmds # 1. Import Maya Commands

selection = cmds.ls(selection=True) # 2. Store selection in a variable
uv_coordinates = cmds.nurbsEditUV(selection[0], query=True) # 3. Query UV coordinates from object zero in selection list
print(uv_coordinates) # 4. Print UV coordinates

