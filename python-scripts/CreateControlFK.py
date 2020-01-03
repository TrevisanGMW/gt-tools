'''
Super simple script used to introduce students to the use of python in Maya
It automatically creates an FK control and stores its transforms in a separated group before parent constraining the joint to it.
'''

# 1. Import Maya Commands.
import maya.cmds as cmds

# 2. Get my joint.
my_joint = cmds.ls(selection=True)

# 3. Get my joint name and remove "Jnt" from it.
joint_name = my_joint[0][:-3]

# 4. Create Control.
# Normal determines the orientation of the control.
# Radius determines its size.
# Ch determines if construction history is kept.
ctrl = cmds.circle(name=joint_name + 'Ctrl', normal=[1,0,0], radius =1, ch=False)

# 5. Create Group
grp = cmds.group(name=(ctrl[0]+'Grp'))

# 6. Move group. Use parent constraint to match joint's transforms.
constraint = cmds.parentConstraint(my_joint[0],grp)

# 7. Delete constraint. (As it's no longer necessary after we matched transforms)
cmds.delete(constraint)

# 8. Constraint joint.
cmds.parentConstraint(ctrl[0], my_joint[0])

# 9. Select control.
cmds.select(ctrl[0])