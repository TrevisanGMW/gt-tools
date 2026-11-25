# Frames a camera on every node of one type, e.g. all meshes or all joints.
# The camera transform is saved with the scene, so this works in batch (mayapy) runs too.
# Common NODE_TYPE values: "mesh", "joint", "nurbsCurve", "locator", "transform".
import sys
import maya.cmds as cmds

NODE_TYPE = "mesh"
CAMERA = "persp"
FIT_FACTOR = 0.9  # Lower values leave more space around the framed nodes.
INCLUDE_HIDDEN = False


def get_frame_targets(node_type, include_hidden):
    """Gets transforms to frame for a node type.

    Args:
        node_type (str): Maya node type.
        include_hidden (bool): Include hidden nodes.

    Returns:
        list: Transforms (or DAG nodes) to frame.
    """
    query_kwargs = {"type": node_type, "long": True}
    if not include_hidden:
        query_kwargs["visible"] = True
    nodes = cmds.ls(**query_kwargs) or []
    inherited_types = cmds.nodeType(node_type, isTypeName=True, inherited=True) or []
    if nodes and "shape" in inherited_types:
        nodes = cmds.listRelatives(nodes, parent=True, fullPath=True) or []
    return sorted(set(nodes))


frame_targets = get_frame_targets(NODE_TYPE, INCLUDE_HIDDEN)
if not frame_targets:
    sys.stdout.write(f'No "{NODE_TYPE}" nodes found; the camera was not moved.\n')
elif not cmds.objExists(CAMERA):
    sys.stdout.write(f'Camera "{CAMERA}" does not exist; the camera was not moved.\n')
else:
    previous_selection = cmds.ls(selection=True) or []
    try:
        cmds.select(frame_targets, replace=True)
        cmds.viewFit(CAMERA, fitFactor=FIT_FACTOR)
    finally:
        if previous_selection:
            cmds.select(previous_selection, replace=True)
        else:
            cmds.select(clear=True)
    sys.stdout.write(f'Framed {len(frame_targets)} "{NODE_TYPE}" node(s) with camera "{CAMERA}".\n')
