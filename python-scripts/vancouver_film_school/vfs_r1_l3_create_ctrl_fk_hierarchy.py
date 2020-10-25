'''
Simple version of Auto FK Control with Hierarchy Script used to help students understand the basics of Python.
It creates FK controls for every selected joint storing their transform in groups, then it mimics the hierarchy of the joints to properly parent controls.
If you're looking for a more complete solution, refer to the script called "gt_create_ctrl_auto_FK"
'''

# Import Maya cmds
import maya.cmds as cmds

# Grab all joints from selection
selected_joints = cmds.ls(selection=True, type='joint')

# For every joint that doesn't contain "end" or "eye", do something
for jnt in selected_joints:
    if 'end' in jnt or 'eye' in jnt:
        pass
    else:
        #Create Ctrl in the same way we did before
        joint_name = jnt[:-3]
        ctrl = cmds.circle(name=joint_name + 'ctrl', normal=[1,0,0], radius=1.5, ch=False)
        grp = cmds.group(name=(ctrl[0]+'grp'))
        constraint = cmds.parentConstraint(jnt,grp)
        cmds.delete(constraint)
        cmds.parentConstraint(ctrl[0],jnt)

        #Auto parents new controls
        # "or []" Accounts for root joint that doesn't have a parent, it forces it to be a list instead of "NoneType"
        jnt_parent = cmds.listRelatives(jnt, allParents=True) or []
        if len(jnt_parent) == 0:
            pass
        else:
            parent_ctrl = (jnt_parent[0][:-3] + 'ctrl')
            print(parent_ctrl)
        
            if cmds.objExists(parent_ctrl):
                cmds.parent(grp, parent_ctrl)