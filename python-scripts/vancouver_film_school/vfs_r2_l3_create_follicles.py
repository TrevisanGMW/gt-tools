import maya.cmds as cmds

# 2. Create the necessary variables
nurbs_uvs = cmds.ls(selection=True) # Store selection in a variable called "nurbs_uvs". 
nurbs_object = nurbs_uvs[0].split(".")[0] # Extract the name of the nurbs object. The same could be done with "listRelatives"
follicles_list = [] # Create an empty list that we can populate with the follicles we are going to create

# 3. Create an empty group to later store our newly create follicles
follicle_grp = cmds.group(name="follicles_grp", empty=True)

# 4. Start a "for loop" to go through every object in the list "nurbs_uvs"
for uv in nurbs_uvs:
    uv_coordinates = cmds.nurbsEditUV(uv, query=True) #Extract UV position using the command nurbsEditUV (Using polygons? Use cmds.polyEditUV)
    follicle = cmds.createNode("follicle") # Create a follicle (no default connection on this one)
    cmds.setAttr(follicle + ".parameterU",uv_coordinates[0]) # Give the extracted coordinate to U of the follicle
    cmds.setAttr(follicle + ".parameterV",uv_coordinates[1]/2) # Give half of the extracted coordinate V to the follicle (so it's in the middle)
    follicle_transform = cmds.listRelatives(follicle,allParents=True)[0] # Extract the follicle's transform (parent)

    cmds.connectAttr (nurbs_object + ".local", follicle + ".inputSurface")  # Connect the nurbs object on the follicle (so it knows what to use)
    cmds.connectAttr (nurbs_object + ".worldMatrix", follicle + ".inputWorldMatrix",force=True) # Connect transforms to follicle (so it knows where it is)
    cmds.connectAttr (follicle + ".outTranslate", follicle_transform + ".translate",force=True) # Connects follicleShape position to its transform (default behaviour)
    cmds.connectAttr (follicle + ".outRotate", follicle_transform + ".rotate",force=True) # Connects follicleShape rotate to its transform (default behaviour)

    follicles_list.append(follicle_transform) # Adds new follicles to our previously created list

# 5. Organize and Clean up
for foll in follicles_list:
    cmds.parent(foll, follicle_grp)