'''
Simple script used to help students understand how to automate the process of creating follicles for rigging
It automatically creates follicles according to the UVs selected on a Nurbs object
For a more complete version of this script check GT Tools
'''

# 1. Import Maya Commands.
import maya.cmds as cmds

# 2. Create the necessary variables
nurbsUVs = cmds.ls(selection=True) # Store selection in a variable called "nurbsUVs". 
nurbsObject = nurbsUVs[0].split(".")[0] # Extract the name of the nurbs object. The same could be done with "listRelatives"
folliclesList = [] # Create an empty list that we can populate with the follicles we are going to create

# 3. Create an empty group to later store our newly create follicles
follicleGrp = cmds.group(name="follicles_grp", empty=True)

# 4. Start a "for loop" to go through every object in the list "nurbsUVs"
for uv in nurbsUVs:
    uvCoordinate = cmds.nurbsEditUV(uv, query=True) #Extract UV position using the command nurbsEditUV (Using polygons? Use cmds.polyEditUV)
    follicle = cmds.createNode("follicle") # Create a follicle (no default connection on this one)
    cmds.setAttr(follicle + ".parameterU",uvCoordinate[0]) # Give the extracted coordinate to U of the follicle
    cmds.setAttr(follicle + ".parameterV",uvCoordinate[1]/2) # Give half of the extracted coordinate V to the follicle (so it's in the middle)
    follicleTransform = cmds.listRelatives(follicle,allParents=True)[0] # Extract the follicle's transform (parent)

    cmds.connectAttr (nurbsObject + ".local", follicle + ".inputSurface")  # Connect the nurbs object on the follicle (so it knows what to use)
    cmds.connectAttr (nurbsObject + ".worldMatrix", follicle + ".inputWorldMatrix",force=True) # Connect transforms to follicle (so it knows where it is)
    cmds.connectAttr (follicle + ".outTranslate", follicleTransform + ".translate",force=True) # Connects follicleShape position to its transform (default behaviour)
    cmds.connectAttr (follicle + ".outRotate", follicleTransform + ".rotate",force=True) # Connects follicleShape rotate to its transform (default behaviour)

    cmds.parent(follicleTransform, follicleGrp) # Parents the follicle to the previously created follicle group

