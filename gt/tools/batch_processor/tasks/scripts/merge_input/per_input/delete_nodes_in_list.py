# Deletes nodes from the input that was just merged when their short name matches a list.
# Names are matched without namespaces, so "persp_review_cam" matches "walk_01:persp_review_cam".
# Referenced nodes cannot be deleted; they are reported and skipped.
import sys
import maya.cmds as cmds

NAMES_TO_DELETE = [
    "unused_cam",
    "lights_grp",
    "reference_plane",
]


def get_short_name(node_name):
    """Gets a node name without its DAG path or namespace.

    Args:
        node_name (str): Node name.

    Returns:
        str: Short name.
    """
    return node_name.split("|")[-1].split(":")[-1]


targets = set(name.lower() for name in NAMES_TO_DELETE)
nodes_to_delete = [
    node for node in merged_nodes if cmds.objExists(node) and get_short_name(node).lower() in targets
]
deleted_count = 0
for node in nodes_to_delete:
    if not cmds.objExists(node):
        continue
    if cmds.referenceQuery(node, isNodeReferenced=True):
        sys.stdout.write(f"  Skipped referenced node: {node}\n")
        continue
    cmds.delete(node)
    deleted_count += 1
sys.stdout.write(f"Merge Input [{input_index}/{total_inputs}]: deleted {deleted_count} node(s).\n")
