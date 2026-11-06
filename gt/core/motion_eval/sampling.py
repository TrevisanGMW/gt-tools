"""
Motion Evaluation Sampling - Samples world transforms from the open scene of the active host.

Host-agnostic: every scene call goes through hosts.get_host() (Maya inside Maya or mayapy,
Blender inside Blender, motion sample files in plain Python), so this module imports
anywhere and works the same in every host. The sample it builds is what the checks read
(see checks_base.MotionData).
"""

from .checks_base import MODE_BIPED, MODE_GENERAL
from . import hosts
from . import templates
from .hosts.maya_host import METERS_PER_LINEAR_UNIT  # noqa: F401 (kept for older imports)
import logging
import os

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

MAX_SAMPLED_NODES = 2000


def get_host():
    """Gets the active scene host.

    Returns:
        SceneHost: Host (see hosts.get_host).
    """
    return hosts.get_host()


def get_scene_name():
    """Gets the open scene file name without its folder and extension.

    Returns:
        str: Scene name, or "untitled" for unsaved scenes.
    """
    scene_path = get_host().get_scene_path() or ""
    return os.path.splitext(os.path.basename(scene_path))[0] or "untitled"


def get_scene_fps():
    """Gets the scene frame rate.

    Returns:
        float: Frames per second.
    """
    return float(get_host().get_fps())


def get_meters_per_unit():
    """Gets the size of one scene linear unit in meters.

    Returns:
        float: Meters per scene unit.
    """
    return float(get_host().get_meters_per_unit())


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
    return str(get_host().get_up_axis() or "y").lower()


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
    host = get_host()
    if range_mode == RANGE_CUSTOM and custom_start is not None and custom_end is not None:
        start, end = float(custom_start), float(custom_end)
    elif range_mode == RANGE_ANIMATION:
        start, end = host.get_time_range("animation")
    elif range_mode == RANGE_KEYED and node_paths:
        key_range = host.get_key_range(list(node_paths))
        start, end = key_range if key_range else host.get_time_range("playback")
    else:
        start, end = host.get_time_range("playback")
    start, end = int(round(start)), int(round(end))
    return min(start, end), max(start, end)


# ------------------------------------------------ Node Collection ------------------------------------------------
def list_template_candidates():
    """Lists scene nodes that templates may resolve, joints first.

    Returns:
        list: Node paths (joints, then other transforms).
    """
    host = get_host()
    return host.list_joints() + host.list_transforms()


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
    """Lists transforms (joints included) driven directly by animation curves.

    Returns:
        list: Node paths.
    """
    return get_host().list_animated_nodes()


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
    host = get_host()
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
            matches = host.find_nodes(name)
            if not matches:
                warnings.append(f'Node "{name}" was not found.')
            node_paths.extend(matches)
    elif scope == SCOPE_SELECTION:
        node_paths = host.get_selected_nodes()
    else:
        node_paths = host.list_joints()
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
    return get_host().get_parents(node_paths)


# ------------------------------------------------ Sampling ------------------------------------------------
def sample_world_matrices(node_paths, start_frame, end_frame):
    """Samples world matrices for every node at every frame (the host restores its current frame).

    Args:
        node_paths (list): Long node paths.
        start_frame (int): First frame.
        end_frame (int): Last frame.

    Returns:
        dict: Node path to a list of flat 16-value matrices.
    """
    return get_host().sample_world_matrices(node_paths, start_frame, end_frame)


def sample_scene(mode=MODE_GENERAL, template=None, frame_range=None, general_scope=None, node_names=None,
                 extra_data=None):
    """Samples the open scene for evaluation.

    Args:
        mode (str): MODE_GENERAL or MODE_BIPED.
        template (dict, optional): Skeleton template. Required in biped mode.
        frame_range (tuple, optional): (start, end) frames. Defaults to the playback range.
        general_scope (str, optional): Node scope for general mode.
        node_names (list, optional): Names for the node list scope.
        extra_data (list, optional): Extra data keys to collect (see SceneHost.get_extra_data); keys the
            host cannot provide are left out, so the checks needing them are skipped.

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
        "extra": collect_extra_data(extra_data, node_paths, start_frame, end_frame),
    }


def collect_extra_data(data_keys, node_paths, start_frame, end_frame):
    """Asks the host for extra scene data needed by checks.

    Args:
        data_keys (list or None): Extra data keys.
        node_paths (list): Sampled node paths.
        start_frame (int): First frame.
        end_frame (int): Last frame.

    Returns:
        dict: Key to data, only for keys the host provided.
    """
    host = get_host()
    extra = {}
    for data_key in data_keys or []:
        value = host.get_extra_data(data_key, node_paths, start_frame, end_frame)
        if value is not None:
            extra[data_key] = value
    return extra


def describe_scene():
    """Describes the open scene for tool windows (node lists, ranges, frame rate).

    Returns:
        dict: "host", "nodes" (joints first, then transforms), "joint_count", "joint_label"
            ("joint" or "bone"), "playback" and "animation" ranges, "fps", and "up_axis".
    """
    host = get_host()
    joints = host.list_joints()
    return {
        "host": host.name,
        "nodes": joints + host.list_transforms(),
        "joint_count": len(joints),
        "joint_label": host.joint_label,
        "playback": list(host.get_time_range("playback")),
        "animation": list(host.get_time_range("animation")),
        "fps": float(host.get_fps()),
        "up_axis": str(host.get_up_axis()),
    }
