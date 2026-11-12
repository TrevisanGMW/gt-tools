"""
Helpers shared by the repair fixes: results, channels, node resolution, and local-space sampling.
"""

from .. import math_utils
from . import transform_math

CHANNELS = {"rotate": ("rotate",), "translate": ("translate",), "both": ("rotate", "translate")}
FLOOR_PERCENTILE = 0.1


def get_channels(params):
    """Gets the channel tuple from the "channels" parameter.

    Args:
        params (dict): Fix parameters.

    Returns:
        tuple: Channel names.

    Raises:
        ValueError: When the value is unknown.
    """
    value = str(params.get("channels") or "rotate").lower()
    if value not in CHANNELS:
        raise ValueError(f'channels must be one of {", ".join(CHANNELS)}, not "{value}".')
    return CHANNELS[value]


def build_result(frames, nodes):
    """Builds an empty fix result.

    Args:
        frames (tuple): Repaired span.
        nodes (list): Node paths.

    Returns:
        dict: Result dictionary.
    """
    return {"keys": 0, "nodes": list(nodes), "frames": [int(frames[0]), int(frames[1])], "warnings": []}


def add_key_result(result, key_result):
    """Adds a host keying (or sub-fix) result to a fix result.

    Args:
        result (dict): Fix result, changed in place.
        key_result (dict): Result with "keys" and "warnings".
    """
    result["keys"] += int(key_result.get("keys") or 0)
    result["warnings"].extend(key_result.get("warnings") or [])


def get_parent_matrices(matrices, parent_path, frame_count):
    """Gets a parent's sampled matrices, or None entries for a top node.

    Args:
        matrices (dict): Sampled matrices by path.
        parent_path (str): Parent path or None.
        frame_count (int): Frames in the window.

    Returns:
        list: Matrices or None values.
    """
    return matrices[parent_path] if parent_path else [None] * frame_count


def require_nodes(scene, nodes, fix_key):
    """Resolves the nodes a fix works on.

    Args:
        scene (RepairScene): Scene access.
        nodes (list): Names, labels, or role keys.
        fix_key (str): Fix name for the error message.

    Returns:
        list: Node paths.

    Raises:
        ValueError: When no node was given.
    """
    if not nodes:
        raise ValueError(f'The "{fix_key}" fix needs "nodes" (node names, report offender labels, or role keys).')
    return [scene.resolve_node(node) for node in nodes]


def sample_local_series(scene, node_paths, window_start, window_end):
    """Samples nodes and returns their local rotations and translations per frame.

    Args:
        scene (RepairScene): Scene access.
        node_paths (list): Node paths.
        window_start (int): First frame.
        window_end (int): Last frame.

    Returns:
        dict: Node path to {"matrices": local matrices, "quaternions": list, "positions": list}.
    """
    matrices, parents = scene.sample(node_paths, window_start, window_end)
    frame_count = window_end - window_start + 1
    series = {}
    for node_path in node_paths:
        parent_matrices = get_parent_matrices(matrices, parents.get(node_path), frame_count)
        local_matrices = [transform_math.local_from_world(world, parent)
                          for world, parent in zip(matrices[node_path], parent_matrices)]
        series[node_path] = {
            "matrices": local_matrices,
            "quaternions": [transform_math.matrix_to_quaternion(matrix) for matrix in local_matrices],
            "positions": [math_utils.matrix_position(matrix) for matrix in local_matrices],
        }
    return series


def key_local_series(scene, node_path, window_start, indexes, local_matrices, quaternions, positions, channels):
    """Keys new local rotations and/or translations on chosen window indexes.

    Args:
        scene (RepairScene): Scene access.
        node_path (str): Node path.
        window_start (int): Frame of index 0.
        indexes (list): Window indexes to key.
        local_matrices (list): Original local matrices (scale is kept).
        quaternions (list): New local rotations per window index.
        positions (list): New local translations per window index.
        channels (tuple): "rotate" and/or "translate".

    Returns:
        dict: Host keying result.
    """
    new_matrices = []
    for index in indexes:
        matrix = local_matrices[index]
        if "rotate" in channels:
            matrix = transform_math.replace_rotation(matrix, quaternions[index])
        if "translate" in channels:
            matrix = transform_math.replace_position(matrix, positions[index])
        new_matrices.append(matrix)
    frames = [window_start + index for index in indexes]
    return scene.host.key_local_transforms(node_path, frames, new_matrices, channels)
