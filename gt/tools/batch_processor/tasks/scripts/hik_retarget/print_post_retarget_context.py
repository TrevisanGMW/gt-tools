# Prints the Batch Processor HumanIK post-retarget script context.
# Available values:
#   context / batch_context: Full runtime dictionary.
#   arguments / args: input, output, project, project_dir, task, task_id, etc.
#   environment_variables / env: Project environment variables.
#   project, task, work_item, output_path, source_character, target_character,
#   imported_source_nodes, imported_target_nodes.
import pprint
import sys
import maya.cmds as cmds

sys.stdout.write("HumanIK post script\n")
sys.stdout.write("Input: {0}\n".format(args.get("input") or context.get("source_path")))
sys.stdout.write("Output: {0}\n".format(args.get("output") or output_path))
sys.stdout.write("Arguments:\n")
pprint.pprint(arguments)
sys.stdout.write("Environment Variables:\n")
pprint.pprint(environment_variables)
