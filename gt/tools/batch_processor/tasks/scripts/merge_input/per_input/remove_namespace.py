# Removes the namespace of the input that was just merged.
# Same as the task's "Remove" namespace option, shown here as a starting point for custom rules.
# Maya renames nodes whose names clash with existing root-namespace nodes.
# Referenced inputs keep their namespace.
import sys
import maya.cmds as cmds

if load_mode == "Reference":
    sys.stdout.write(f"Skipped namespace removal for referenced input: {input_path}\n")
elif namespace and cmds.namespace(exists=f":{namespace}"):
    cmds.namespace(removeNamespace=f":{namespace}", mergeNamespaceWithRoot=True)
    sys.stdout.write(f"Removed namespace: {namespace}\n")
else:
    sys.stdout.write(f"No namespace to remove for: {input_path}\n")
