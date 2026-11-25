"""
Span fixes that work on any joint: bridge, smooth, spike clamp, and hinge limit clamp.

Every fix has the signature ``fix(scene, frames, nodes, params)`` (see fixes.py).
"""

from .. import checks_limits
from .. import math_utils
from . import solvers
from . import transform_math
from .fixes_common import add_key_result
from .fixes_common import build_result
from .fixes_common import get_channels
from .fixes_common import key_local_series
from .fixes_common import require_nodes
from .fixes_common import sample_local_series

SPIKE_CONTEXT_FRAMES = 10
HINGE_PARTS = {"knee": ("up_leg", "leg", "foot"), "elbow": ("arm", "forearm", "hand")}
DEFAULT_LIMITS = {"backward": 0.0, "side": 30.0}


def span_bridge(scene, frames, nodes, params):
    """Replaces the span with a smooth transition between the poses just before and after it.

    Rotations are slerped in local space; translations follow a Hermite curve. ``strength`` below 1
    only pulls the motion part of the way. ``ease`` > 0 fades the bridge in and out over that many
    frames inside the span instead of replacing it at full strength from the first frame.

    Args:
        scene (RepairScene): Scene access.
        frames (tuple): (start, end) frames.
        nodes (list): Nodes to repair.
        params (dict): channels, strength, ease.

    Returns:
        dict: Fix result.
    """
    start_frame, end_frame = int(frames[0]), int(frames[1])
    node_paths = require_nodes(scene, nodes, "span_bridge")
    channels = get_channels(params)
    strength = min(1.0, max(0.0, float(params.get("strength", 1.0))))
    ease = max(0, int(params.get("ease", 0)))
    margin = 2
    window_start = start_frame - margin
    series = sample_local_series(scene, node_paths, window_start, end_frame + margin)
    span_start, span_end = start_frame - window_start, end_frame - window_start
    weights = build_ease_weights(span_start, span_end, ease, strength)
    result = build_result(frames, node_paths)
    for node_path in node_paths:
        data = series[node_path]
        bridged_quaternions = solvers.bridge_quaternions(data["quaternions"], span_start, span_end)
        bridged_positions = solvers.bridge_vectors(data["positions"], span_start, span_end)
        quaternions = list(data["quaternions"])
        positions = list(data["positions"])
        for index, weight in weights.items():
            quaternions[index] = transform_math.slerp(data["quaternions"][index], bridged_quaternions[index], weight)
            positions[index] = math_utils.lerp(data["positions"][index], bridged_positions[index], weight)
        add_key_result(result, key_local_series(scene, node_path, window_start, sorted(weights), data["matrices"],
                                                quaternions, positions, channels))
    return result


def build_ease_weights(span_start, span_end, ease, strength):
    """Builds per-index weights inside a span, fading in and out over ``ease`` frames.

    Args:
        span_start (int): First index.
        span_end (int): Last index.
        ease (int): Fade length in frames (0 = full strength everywhere).
        strength (float): Peak weight.

    Returns:
        dict: Index to weight.
    """
    weights = {}
    for index in range(span_start, span_end + 1):
        weight = 1.0
        if ease:
            distance = min(index - span_start, span_end - index) + 1
            weight = math_utils.smoothstep(min(1.0, distance / float(ease + 1)))
        weights[index] = weight * strength
    return weights


def span_smooth(scene, frames, nodes, params):
    """Smooths the span with a Gaussian filter, blending in and out over ``blend`` frames.

    With ``adaptive`` on, fast frames are smoothed less than slow ones, so accents survive while
    jitter during slow motion is removed.

    Args:
        scene (RepairScene): Scene access.
        frames (tuple): (start, end) frames.
        nodes (list): Nodes to repair.
        params (dict): radius, blend, channels, strength, adaptive.

    Returns:
        dict: Fix result.
    """
    start_frame, end_frame = int(frames[0]), int(frames[1])
    node_paths = require_nodes(scene, nodes, "span_smooth")
    channels = get_channels(params)
    radius = max(1, int(params.get("radius", 2)))
    blend = max(0, int(params.get("blend", 3)))
    strength = min(1.0, max(0.0, float(params.get("strength", 1.0))))
    margin = blend + radius
    window_start = start_frame - margin
    window_end = end_frame + margin
    series = sample_local_series(scene, node_paths, window_start, window_end)
    frame_count = window_end - window_start + 1
    weights = solvers.build_blend_weights(frame_count, start_frame - window_start, end_frame - window_start, blend)
    result = build_result(frames, node_paths)
    for node_path in node_paths:
        data = series[node_path]
        smooth_quaternions = solvers.smooth_quaternions(data["quaternions"], radius)
        smooth_positions = solvers.smooth_vectors(data["positions"], radius)
        node_weights = list(weights)
        if params.get("adaptive"):
            node_weights = apply_speed_weights(node_weights, smooth_quaternions)
        quaternions = list(data["quaternions"])
        positions = list(data["positions"])
        indexes = [index for index, weight in enumerate(node_weights) if weight > 0.0]
        for index in indexes:
            amount = node_weights[index] * strength
            quaternions[index] = transform_math.slerp(data["quaternions"][index], smooth_quaternions[index], amount)
            positions[index] = math_utils.lerp(data["positions"][index], smooth_positions[index], amount)
        add_key_result(result, key_local_series(scene, node_path, window_start, indexes, data["matrices"],
                                                quaternions, positions, channels))
    return result


def apply_speed_weights(weights, quaternions):
    """Scales smoothing weights down where the (smoothed) rotation moves fast.

    Args:
        weights (list): Blend weights per index.
        quaternions (list): Smoothed rotations per index.

    Returns:
        list: Scaled weights (1 at rest, 0 at the fastest frame of the window).
    """
    last = len(quaternions) - 1
    speeds = [solvers.quaternion_angle(quaternions[max(0, index - 1)], quaternions[min(last, index + 1)])
              for index in range(len(quaternions))]
    fastest = max(speeds) or 1.0
    return [weight * (1.0 - speed / fastest) for weight, speed in zip(weights, speeds)]


def spike_clamp(scene, frames, nodes, params):
    """Caps how fast the nodes may move inside the span, relative to the motion around it.

    The largest allowed step is ``factor`` times the median step in the frames around the span,
    so a pop is flattened while the overall motion through the span is kept.

    Args:
        scene (RepairScene): Scene access.
        frames (tuple): (start, end) frames.
        nodes (list): Nodes to repair.
        params (dict): channels, factor.

    Returns:
        dict: Fix result.
    """
    start_frame, end_frame = int(frames[0]), int(frames[1])
    node_paths = require_nodes(scene, nodes, "spike_clamp")
    channels = get_channels(params)
    factor = max(0.1, float(params.get("factor", 1.5)))
    window_start = start_frame - SPIKE_CONTEXT_FRAMES
    window_end = end_frame + SPIKE_CONTEXT_FRAMES
    series = sample_local_series(scene, node_paths, window_start, window_end)
    span_start, span_end = start_frame - window_start, end_frame - window_start
    result = build_result(frames, node_paths)
    for node_path in node_paths:
        data = series[node_path]
        angle_step = solvers.median_step(data["quaternions"], span_start, span_end, solvers.quaternion_angle)
        move_step = solvers.median_step(data["positions"], span_start, span_end, math_utils.distance)
        quaternions = solvers.clamp_step_quaternions(data["quaternions"], span_start, span_end,
                                                     max(1e-4, angle_step * factor))
        positions = solvers.clamp_step_vectors(data["positions"], span_start, span_end,
                                               max(1e-6, move_step * factor))
        add_key_result(result, key_local_series(scene, node_path, window_start, list(range(span_start, span_end + 1)),
                                                data["matrices"], quaternions, positions, channels))
    return result


def resolve_hinge_nodes(scene, nodes, params):
    """Resolves the upper, hinge, and lower joints of a knee or elbow.

    Accepts explicit [upper, hinge, lower] nodes, a report label such as "left knee", or the
    "side" and "joint" parameters.

    Args:
        scene (RepairScene): Scene access.
        nodes (list): Optional nodes or one report label.
        params (dict): side, joint.

    Returns:
        list: Three node paths.

    Raises:
        ValueError: When the joint cannot be resolved.
    """
    if nodes and len(nodes) == 3:
        return [scene.resolve_node(node) for node in nodes]
    side, joint = str(params.get("side") or "").lower(), str(params.get("joint") or "").lower()
    if nodes and len(nodes) == 1:
        words = str(nodes[0]).lower().split()
        if len(words) == 2:
            side, joint = words
    if side not in ("left", "right") or joint not in HINGE_PARTS:
        raise ValueError('limit_clamp needs "nodes" [upper, hinge, lower], a label like "left knee", or '
                         '"side" (left/right) and "joint" (knee/elbow).')
    return [scene.resolve_node(f"{side}_{part}") for part in HINGE_PARTS[joint]]


def learn_hinge(scene, chain):
    """Learns a chain's hinge axis (in the upper joint's space) from the whole clip.

    Args:
        scene (RepairScene): Scene access.
        chain (list): [upper, hinge, lower] node paths.

    Returns:
        tuple: Local hinge axis.

    Raises:
        ValueError: When the joint never bends enough to learn the axis.
    """
    clip_start, clip_end = scene.host.get_time_range("playback")
    clip = scene.host.sample_world_matrices(chain, int(clip_start), int(clip_end))
    upper, hinge, lower = chain
    rotations = [math_utils.matrix_rotation(matrix) for matrix in clip[upper]]
    positions = [[math_utils.matrix_position(matrix) for matrix in clip[node]] for node in chain]
    upper_directions = checks_limits.get_directions(positions[0], positions[1])
    lower_directions = checks_limits.get_directions(positions[1], positions[2])
    axis = checks_limits.learn_hinge_axis(rotations, upper_directions, lower_directions)
    if axis is None:
        raise ValueError(f"{hinge.split('|')[-1]} never bends enough in this clip to learn its hinge axis.")
    return axis


def limit_clamp(scene, frames, nodes, params):
    """Rotates a knee or elbow back inside its limit where it bends too far, blending in and out.

    The hinge axis is learned from the clip (like the joint-limit checks). Only the hinge joint
    rotates; its children follow, so a planted foot may move (add a foot_lock step after it).

    Args:
        scene (RepairScene): Scene access.
        frames (tuple): (start, end) frames.
        nodes (list): [upper, hinge, lower], or a label such as "left knee".
        params (dict): side, joint, measure, limit, margin, blend.

    Returns:
        dict: Fix result.
    """
    start_frame, end_frame = int(frames[0]), int(frames[1])
    chain = resolve_hinge_nodes(scene, nodes, params)
    measure = str(params.get("measure") or "backward").lower()
    if measure not in DEFAULT_LIMITS:
        raise ValueError('limit_clamp "measure" must be "backward" or "side".')
    limit = params.get("limit")
    limit = DEFAULT_LIMITS[measure] if limit in (None, "") else float(limit)
    target_limit = limit - max(0.0, float(params.get("margin", 2.0)))
    blend = max(0, int(params.get("blend", 3)))
    hinge_local = learn_hinge(scene, chain)
    upper, hinge_joint, lower = chain
    window_start, window_end = start_frame - blend, end_frame + blend
    matrices, parents = scene.sample(chain, window_start, window_end)
    hinge_parent = parents.get(hinge_joint)
    frame_count = window_end - window_start + 1
    weights = solvers.build_blend_weights(frame_count, blend, blend + end_frame - start_frame, blend)
    keyed_frames, new_worlds, parent_worlds = [], [], []
    for index, weight in enumerate(weights):
        if weight <= 0.0:
            continue
        positions = [math_utils.matrix_position(matrices[node][index]) for node in chain]
        upper_direction = math_utils.normalize(math_utils.subtract(positions[1], positions[0]))
        lower_direction = math_utils.normalize(math_utils.subtract(positions[2], positions[1]))
        world_matrix = matrices[hinge_joint][index]
        if upper_direction is not None and lower_direction is not None:
            hinge_world = math_utils.to_world(math_utils.matrix_rotation(matrices[upper][index]), hinge_local)
            target = solvers.limit_hinge_direction(upper_direction, lower_direction, hinge_world, measure,
                                                   target_limit)
            if target is not None:
                turn = transform_math.slerp(transform_math.IDENTITY_QUATERNION,
                                            transform_math.quaternion_from_to(lower_direction, target), weight)
                rows, scale_values, position = transform_math.split_matrix(world_matrix)
                world_matrix = transform_math.join_matrix(
                    transform_math.multiply_rows(rows, transform_math.quaternion_to_rows(turn)), scale_values,
                    position)
        keyed_frames.append(window_start + index)
        new_worlds.append(world_matrix)
        parent_worlds.append(matrices[hinge_parent][index] if hinge_parent else None)
    result = build_result(frames, [hinge_joint])
    result["limit"] = limit
    add_key_result(result, scene.key_world_matrices(hinge_joint, keyed_frames, new_worlds, parent_worlds,
                                                    ("rotate",)))
    return result

