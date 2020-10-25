import maya.cmds as cmds

selection = cmds.ls(selection=True)
uv_coordinates = cmds.nurbsEditUV(selection[0], query=True)
print(uv_coordinates)

