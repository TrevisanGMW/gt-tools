"""
Batch Python example.

Values exposed by the batch processor when Pass Task Args is enabled:
    arguments["input"]: Current input file for this task.
        Example: C:/project/01_input/walk.fbx
    arguments["output"]: Expected output file for this task.
        Example: C:/project/02_tasks/01_python/walk.ma
    arguments["project_path"]: Batch project file.
        Example: C:/project/Batch_process_project.batch
    arguments["project_dir"]: Folder containing the batch project.
        Example: C:/project
    arguments["task"]: Task display name.
        Example: Python
    arguments["task_id"]: Stable task id from the .batch file.
        Example: 2f35ec56-8e64-4df7-9a30-612af8d4f2db

Project environment variables are available through environment_variables.
Short aliases are also available: args and env.
"""

import pprint
import maya.cmds as cmds

print("Batch Python arguments:")
pprint.pprint(arguments)

print("Batch environment variables:")
pprint.pprint(environment_variables)


def run(context):
    """Runs after the inline script is loaded by the batch processor."""
    print("Processing: {0}".format(args.get("input") or context.get("source_path")))
    print("Output: {0}".format(args.get("output") or context.get("output_path")))
