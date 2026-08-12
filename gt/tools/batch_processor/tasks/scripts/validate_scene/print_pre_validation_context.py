# Prints the Batch Processor Validate Scene pre-validation script context.
# Available values:
#   context / batch_context: Full runtime dictionary.
#   arguments / args: input, output, project, project_dir, task, task_id, etc.
#   environment_variables / env: Project environment variables.
#   project, task, work_item, output_path, validation_scope, node_type,
#   validator_names.
import pprint
import sys
import maya.cmds as cmds

sys.stdout.write("Validate Scene pre-validation script\n")
sys.stdout.write("Input: {0}\n".format(args.get("input") or context.get("source_path")))
sys.stdout.write("Scope: {0}\n".format(validation_scope))
sys.stdout.write("Node Type: {0}\n".format(node_type or "None"))
sys.stdout.write("Validators: {0}\n".format(", ".join(validator_names) or "None"))
sys.stdout.write("Current Selection: {0}\n".format(cmds.ls(selection=True, long=True) or []))
sys.stdout.write("Arguments:\n")
pprint.pprint(arguments)
sys.stdout.write("Environment Variables:\n")
pprint.pprint(environment_variables)
