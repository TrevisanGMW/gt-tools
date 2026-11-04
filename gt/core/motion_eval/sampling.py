"""
Motion Evaluation Sampling - Samples world transforms from the open Maya scene.

Maya runtime module. Maya is imported lazily so the package stays importable
outside Maya, but these functions require a Maya session.
"""

from .checks_base import MODE_BIPED, MODE_GENERAL
from . import templates
import logging

logger = logging.getLogger(__name__)

SCOPE_ALL_JOINTS = "All Joints"
SCOPE_ANIMATED_TRANSFORMS = "Animated Transforms"
SCOPE_TEMPLATE_JOINTS = "Template Joints"
SCOPE_NODE_LIST = "Node List"
SCOPE_SELECTION = "Selection"
GENERAL_SCOPES = [SCOPE_ALL_JOINTS, SCOPE_ANIMATED_TRANSFORMS, SCOPE_TEMPLATE_JOINTS, SCOPE_NODE_LIST, SCOPE_SELECTION]

RANGE_PLAYBACK = "Playback Range"
RANGE_ANIMATION = "Animation Range"
RANGE_KEYED = "Keyed Range"
RANGE_CUSTOM = "Custom"
RANGE_MODES = [RANGE_PLAYBACK, RANGE_ANIMATION, RANGE_KEYED, RANGE_CUSTOM]
RANGE_TOOLTIPS = {
    RANGE_PLAYBACK: "The inner time slider range (playback start/end),\nthe frames between the two inner fields.",
    RANGE_ANIMATION: "The outer time slider range (animation start/end),\nusually the full length of the shot or clip.",
    RANGE_KEYED: "From the first to the last keyframe on the evaluated nodes\n"
                 "(skeleton joints in Biped mode, the node scope in General mode).",
    RANGE_CUSTOM: "Use the Start and End frames typed next to this option.",
}
SCOPE_TOOLTIPS = {
    SCOPE_ALL_JOINTS: "Every joint in the scene.",
    SCOPE_ANIMATED_TRANSFORMS: "Every transform or joint driven by animation curves.",
    SCOPE_TEMPLATE_JOINTS: "Only the joints mapped by the skeleton\n(the Skeleton row becomes active).",
    SCOPE_NODE_LIST: "Only the nodes typed in the field next to this option.\nComma separated, wildcards allowed.",
    SCOPE_SELECTION: "Only the nodes selected in Maya when Evaluate is pressed.",
}

METERS_PER_LINEAR_UNIT = {
    "mm": 0.001,
    "millimeter": 0.001,
    "cm": 0.01,
    "centimeter": 0.01,
    "m": 1.0,
    "meter": 1.0,
    "km": 1000.0,
    "kilometer": 1000.0,
    "in": 0.0254,
    "inch": 0.0254,
    "ft": 0.3048,
    "foot": 0.3048,
    "yd": 0.9144,
    "yard": 0.9144,
    "mi": 1609.344,
    "mile": 1609.344,
}
MAX_SAMPLED_NODES = 2000


def get_maya_cmds():
    """Imports maya.cmds lazily.

    Returns:
        module: maya.cmds.
    """
    import maya.cmds as cmds

    return cmds


# ------------------------------------------------ Scene Info ------------------------------------------------
def get_scene_name():
    """Gets the open scene file name without its folder and extension.

    Returns:
        str: Scene name, or "untitled" for unsaved scenes.
    """
    import os

    scene_path = get_maya_cmds().file(query=True, sceneName=True) or ""
    return os.path.splitext(os.path.basename(scene_path))[0] or "untitled"


def get_scene_fps():
    """Gets the scene frame rate.

    Returns:
        float: Frames per second.
    """
    import maya.api.OpenMaya as om2

    return float(om2.MTime(1.0, om2.MTime.kSeconds).asUnits(om2.MTime.uiUnit()))


def get_meters_per_unit():
    """Gets the size of one scene linear unit in meters.

    Returns:
        float: Meters per scene unit.
    """
    cmds = get_maya_cmds()
    unit = str(cmds.currentUnit(query=True, linear=True) or "cm").lower()
    return METERS_PER_LINEAR_UNIT.get(unit, 0.01)


def get_up_axis(template=None):
    """Gets the up axis used for evaluation.

    Args:
        template (dict, optional): Template whose "up_axis" can override the scene.

    Returns:
        str: "y" or "z".
    """
    template_axis = str((template or {}).get("up_axis") or "scene").lower()
    if template_axis in ("y", "z"):
        return template_axis
    cmds = get_maya_cmds()
    return str(cmds.upAxis(query=True, axis=True) or "y").lower()


def resolve_frame_range(range_mode=RANGE_PLAYBACK, custom_start=None, custom_end=None, node_paths=None):
    """Resolves the frame range to evaluate.

    Args:
        range_mode (str): One of RANGE_MODES.
        custom_start (float, optional): Start frame for the custom mode.
        custom_end (float, optional): End frame for the custom mode.
        node_paths (list, optional): Nodes used by the keyed mode.

    Returns:
        tuple: (start, end) integer frames.
    """
    cmds = get_maya_cmds()
    if range_mode == RANGE_CUSTOM and custom_start is not None and custom_end is not None:
        start, end = float(custom_start), float(custom_end)
    elif range_mode == RANGE_ANIMATION:
        start = cmds.playbackOptions(query=True, animationStartTime=True)
        end = cmds.playbackOptions(query=True, animationEndTime=True)
    elif range_mode == RANGE_KEYED and node_paths:
        key_times = cmds.keyframe(list(node_paths), query=True, timeChange=True) or []
        if key_times:
            start, end = min(key_times), max(key_times)
        else:
            start = cmds.playbackOptions(query=True, minTime=True)
            end = cmds.playbackOptions(query=True, maxTime=True)
    else:
        start = cmds.playbackOptions(query=True, minTime=True)
        end = cmds.playbackOptions(query=True, maxTime=True)
    start, end = int(round(start)), int(round(end))
    return min(start, end), max(start, end)


# ------------------------------------------------ Node Collection ------------------------------------------------
def list_template_candidates():
    """Lists scene nodes that templates may resolve, joints first.

    Returns:
        list: Long node paths (joints, then other transforms).
    """
    cmds = get_maya_cmds()
    joints = cmds.ls(type="joint", long=True) or []
    joint_set = set(joints)
    transforms = [path for path in (cmds.ls(type="transform", long=True) or []) if path not in joint_set]
    return joints + transforms


def resolve_template_in_scene(template, require_biped=False):
    """Resolves template roles against the open scene.

    Args:
        template (dict): Skeleton template.
        require_biped (bool): Report missing biped roles as required.

    Returns:
        dict: Resolution from templates.resolve_template_roles.
    """
    required = templates.REQUIRED_BIPED_ROLES if require_biped else []
    return templates.resolve_template_roles(template, list_template_candidates(), required_roles=required)


def list_animated_transforms():
    """Lists transforms driven directly by animation curves.

    Returns:
        list: Long transform paths.
    """
    cmds = get_maya_cmds()
    curves = cmds.ls(type=["animCurveTL", "animCurveTA", "animCurveTU"]) or []
    if not curves:
        return []
    connected = cmds.listConnections(curves, source=False, destination=True, type="transform") or []
    return sorted(set(cmds.ls(connected, long=True) or []))


def get_keyed_range_nodes(mode, template=None, general_scope=None, node_names=None):
    """Gets the nodes whose keys define the Keyed Range.

    Args:
        mode (str): MODE_GENERAL or MODE_BIPED.
        template (dict, optional): Skeleton template (used in biped mode and by the template scope).
        general_scope (str, optional): Node scope used in general mode.
        node_names (list, optional): Names for the node list scope.

    Returns:
        list or None: Node paths, or None when nothing could be resolved (falls back to the playback range).
    """
    try:
        if mode == MODE_BIPED:
            if not template:
                return None
            return list(resolve_template_in_scene(template)["roles"].values()) or None
        node_paths, _roles, _warnings = collect_general_nodes(general_scope or SCOPE_ALL_JOINTS, template, node_names)
        return node_paths or None
    except ValueError:
        return None


def collect_general_nodes(general_scope, template=None, node_names=None):
    """Collects nodes for general mode.

    Args:
        general_scope (str): One of GENERAL_SCOPES.
        template (dict, optional): Template used by the template scope.
        node_names (list, optional): Names used by the node list scope.

    Returns:
        tuple: (node_paths, roles, warnings).

    Raises:
        ValueError: If the scope produces no nodes.
    """
    cmds = get_maya_cmds()
    warnings = []
    roles = {}
    scope = general_scope or SCOPE_ALL_JOINTS
    if scope == SCOPE_TEMPLATE_JOINTS:
        if not template:
            raise ValueError('The "Template Joints" scope needs a skeleton template.')
        resolution = resolve_template_in_scene(template)
        roles = resolution["roles"]
        warnings.extend(resolution["warnings"])
        node_paths = list(dict.fromkeys(roles.values()))
    elif scope == SCOPE_ANIMATED_TRANSFORMS:
        node_paths = list_animated_transforms()
    elif scope == SCOPE_NODE_LIST:
        node_paths = []
        for name in node_names or []:
            matches = cmds.ls(str(name).strip(), long=True, type="transform") or []
            if not matches:
                warnings.append(f'Node "{name}" was not found.')
            node_paths.extend(matches)
    elif scope == SCOPE_SELECTION:
        node_paths = cmds.ls(selection=True, long=True, type="transform") or []
    else:
        node_paths = cmds.ls(type="joint", long=True) or []
    node_paths = list(dict.fromkeys(node_paths))
    if not node_paths:
        raise ValueError(f'No nodes found for the "{scope}" scope.')
    if len(node_paths) > MAX_SAMPLED_NODES:
        warnings.append(f"Only the first {MAX_SAMPLED_NODES} of {len(node_paths)} nodes were sampled.")
        node_paths = node_paths[:MAX_SAMPLED_NODES]
    return node_paths, roles, warnings


def get_parent_paths(node_paths):
    """Gets the DAG parent of each node.

    Args:
        node_paths (list): Long node paths.

    Returns:
        dict: Node path to parent path (or None).
    """
    cmds = get_maya_cmds()
    parents = {}
    for node_path in node_paths:
        parent = cmds.listRelatives(node_path, parent=True, fullPath=True) or []
        parents[node_path] = parent[0] if parent else None
    return parents


# ------------------------------------------------ Sampling ------------------------------------------------
def get_dag_paths(node_paths):
    """Converts node paths into OpenMaya DAG paths.

    Args:
        node_paths (list): Long node paths.

    Returns:
        list: MDagPath objects in the same order.
    """
    import maya.api.OpenMaya as om2

    selection = om2.MSelectionList()
    for node_path in node_paths:
        selection.add(node_path)
    return [selection.getDagPath(index) for index in range(selection.length())]


def sample_world_matrices(node_paths, start_frame, end_frame):
    """Samples world matrices for every node at every frame.

    The current time is restored afterwards and viewport refresh is suspended
    while sampling.

    Args:
        node_paths (list): Long node paths.
        start_frame (int): First frame.
        end_frame (int): Last frame.

    Returns:
        dict: Node path to a list of flat 16-value matrices.
    """
    cmds = get_maya_cmds()
    dag_paths = get_dag_paths(node_paths)
    matrices = {node_path: [] for node_path in node_paths}
    original_time = cmds.currentTime(query=True)
    is_batch = cmds.about(batch=True)
    if not is_batch:
        cmds.refresh(suspend=True)
    try:
        for frame in range(int(start_frame), int(end_frame) + 1):
            cmds.currentTime(frame, update=True)
            for node_path, dag_path in zip(node_paths, dag_paths):
                matrix = dag_path.inclusiveMatrix()
                matrices[node_path].append([matrix[index] for index in range(16)])
    finally:
        cmds.currentTime(original_time, update=True)
        if not is_batch:
            cmds.refresh(suspend=False)
    return matrices


def sample_scene(mode=MODE_GENERAL, template=None, frame_range=None, general_scope=None, node_names=None):
    """Samples the open scene for evaluation.

    Args:
        mode (str): MODE_GENERAL or MODE_BIPED.
        template (dict, optional): Skeleton template. Required in biped mode.
        frame_range (tuple, optional): (start, end) frames. Defaults to the playback range.
        general_scope (str, optional): Node scope for general mode.
        node_names (list, optional): Names for the node list scope.

    Returns:
        dict: Sample dictionary consumed by evaluation.evaluate_sample.

    Raises:
        ValueError: If required roles or nodes are missing.
    """
    warnings = []
    if mode == MODE_BIPED:
        resolution = resolve_template_in_scene(template, require_biped=True)
        if resolution["missing_required"]:
            labels = [templates.ROLE_LABELS.get(role, role) for role in resolution["missing_required"]]
            raise ValueError(
                f'Skeleton template "{(template or {}).get("name", "")}" is missing required roles in this scene: '
                f"{', '.join(labels)}"
            )
        warnings.extend(resolution["warnings"])
        roles = resolution["roles"]
        node_paths = list(dict.fromkeys(roles.values()))
    else:
        node_paths, roles, scope_warnings = collect_general_nodes(general_scope, template, node_names)
        warnings.extend(scope_warnings)
    if frame_range is None:
        frame_range = resolve_frame_range(RANGE_PLAYBACK)
    start_frame, end_frame = int(frame_range[0]), int(frame_range[1])
    if end_frame <= start_frame:
        raise ValueError(f"Frame range {start_frame}-{end_frame} needs at least two frames.")
    parents = get_parent_paths(node_paths)
    matrices = sample_world_matrices(node_paths, start_frame, end_frame)
    nodes = {node_path: {"matrices": matrices[node_path], "parent": parents.get(node_path)} for node_path in node_paths}
    return {
        "fps": get_scene_fps(),
        "start_frame": start_frame,
        "frame_count": end_frame - start_frame + 1,
        "up_axis": get_up_axis(template),
        "meters_per_unit": get_meters_per_unit(),
        "nodes": nodes,
        "roles": roles,
        "warnings": warnings,
    }
