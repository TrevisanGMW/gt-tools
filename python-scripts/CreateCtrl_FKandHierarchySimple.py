'''
Simple version of Auto FK Control with Hierarchy Script used to help students understand the basics of Python.
It creates FK controls for every selected joint storing their transform in groups, then it mimics the hierarchy of the joints to properly parent controls.
'''

# Import Maya cmds
import maya.cmds as cmds

# Grab all joints from selection
selectedJoints = cmds.ls(selection=True, type='joint')

# For every joint that doesn't contain "End" or "eye", do something
for jnt in selectedJoints:
    if 'End' in jnt or 'eye' in jnt:
        pass
    else:
        #Create Ctrl in the same way we did before
        joint_name = jnt[:-3]
        ctrl = cmds.circle(name=joint_name + 'Ctrl', normal=[1,0,0], radius=1.5, ch=False)
        grp = cmds.group(name=(ctrl[0]+'Grp'))
        constraint = cmds.parentConstraint(jnt,grp)
        cmds.delete(constraint)
        cmds.parentConstraint(ctrl[0],jnt)

        #Auto parents new controls
        # "or []" Accounts for root joint that doesn't have a parent, it forces it to be a list instead of "NoneType"
        jntParent = cmds.listRelatives(jnt, allParents=True) or []
        if len(jntParent) == 0:
            pass
        else:
            parentCtrl = (jntParent[0][:-3] + 'Ctrl')
            print(parentCtrl)
        
            if cmds.objExists(parentCtrl):
                cmds.parent(grp, parentCtrl)