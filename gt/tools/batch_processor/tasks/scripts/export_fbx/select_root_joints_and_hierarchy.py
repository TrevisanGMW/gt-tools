# Selects every root joint and its joint hierarchy for an FBX export.
# Enable Export Selection in the FBX Export task to export this selection only.
# Available values:
#   context / batch_context, arguments / args, environment_variables / env,
#   project, task, work_item, output_path, export_mode.
import sys
import maya.cmds as cmds


root_joints = []
for joint_name in cmds.ls(type="joint", long=True) or []:
    parent_joints = cmds.listRelatives(joint_name, parent=True, type="joint", fullPath=True) or []
    if not parent_joints:
        root_joints.append(joint_name)

cmds.select(clear=True)
if root_joints:
    cmds.select(sorted(root_joints), replace=True, hierarchy=True)
sys.stdout.write(f"Pre-export: selected {len(root_joints)} root joint hierarchy(s).\n")
