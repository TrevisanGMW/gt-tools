# Builds the selection used by the "Selection" validation scope.
# Selects every mesh transform found under a top group, so the validators that
# follow only inspect that part of the scene.
# Available values:
#   context / batch_context, arguments / args, environment_variables / env,
#   project, task, work_item, output_path, validation_scope, node_type,
#   validator_names.
import sys
import maya.cmds as cmds

GROUP_NAME = "geometry_grp"

cmds.select(clear=True)
if not cmds.objExists(GROUP_NAME):
    sys.stdout.write("Pre-validation: group '{0}' was not found, nothing selected.\n".format(GROUP_NAME))
else:
    shapes = cmds.listRelatives(GROUP_NAME, allDescendents=True, type="mesh", fullPath=True) or []
    transforms = cmds.listRelatives(shapes, parent=True, fullPath=True) or []
    transforms = sorted(set(transforms))
    if transforms:
        cmds.select(transforms, replace=True)
    sys.stdout.write("Pre-validation: selected {0} mesh transform(s).\n".format(len(transforms)))
