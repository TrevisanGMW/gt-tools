"""
Foot and ground fixes: foot_lock, foot_floor_clamp, hips_follow, and ground_snap.

Every fix has the signature ``fix(scene, frames, nodes, params)`` (see fixes.py).
"""

from .. import math_utils
from . import solvers
from . import transform_math
from .fixes_common import FLOOR_PERCENTILE
from .fixes_common import add_key_result
from .fixes_common import build_result
from .fixes_common import get_parent_matrices

LEG_ROLES = ("{side}_up_leg", "{side}_leg", "{side}_foot")
DEFAULT_CONTACT_ROLES = ("left_foot", "right_foot", "left_toe", "right_toe")
PLANTED_HEIGHT_RATIO = 0.08
CONTACT_DRIFT_RATIO = 0.06


# ------------------------------------------------ Legs ------------------------------------------------
def resolve_legs(scene, nodes, params, fix_key="foot_lock"):
    """Resolves the legs a fix works on: explicit nodes, one side, or both sides for "auto".

    Args:
        scene (RepairScene): Scene access.
        nodes (list): Optional explicit [thigh, knee, foot].
        params (dict): "side": "left", "right", or "auto".
        fix_key (str): Fix name for messages.

    Returns:
        list: Legs as [thigh, knee, foot] node paths.

    Raises:
        ValueError: When a leg cannot be resolved or is not a direct chain.
    """
    if nodes:
        if len(nodes) != 3:
            raise ValueError(f'{fix_key} "nodes" must list exactly [thigh, knee, foot].')
        legs = [[scene.resolve_node(node) for node in nodes]]
    else:
        side = str(params.get("side") or "auto").lower()
        if side not in ("left", "right", "auto"):
            raise ValueError(f'{fix_key} "side" must be "left", "right", or "auto".')
        legs = []
        for name in (["left", "right"] if side == "auto" else [side]):
            try:
                legs.append([scene.resolve_node(role.format(side=name)) for role in LEG_ROLES])
            except ValueError:
                if side != "auto":
                    raise
        if not legs:
            raise ValueError(f"{fix_key} found no leg roles; give a skeleton template or \"nodes\".")
    for thigh, knee, foot in legs:
        if scene.get_parent(knee) != thigh or scene.get_parent(foot) != knee:
            raise ValueError(f"{fix_key} needs thigh -> knee -> foot as direct parent/child joints "
                             f"({knee.split('|')[-1]} or {foot.split('|')[-1]} has another parent).")
    return legs


def is_auto_side(nodes, params):
    """Checks whether a fix should pick its legs by itself.

    Args:
        nodes (list): Explicit nodes.
        params (dict): Fix parameters.

    Returns:
        bool: True for side "auto" without explicit nodes.
    """
    return not nodes and str(params.get("side") or "auto").lower() == "auto"


def measure_leg(scene, leg):
    """Measures a leg over the whole clip: foot heights above its floor and leg length.

    Args:
        scene (RepairScene): Scene access.
        leg (list): [thigh, knee, foot].

    Returns:
        dict: {"start", "lift" (height above floor per frame), "floor", "leg_length"}.
    """
    up_index = solvers.get_axis_index(scene.get_up_axis())
    clip_start, clip_end = scene.host.get_time_range("playback")
    clip = scene.host.sample_world_matrices(list(leg), int(clip_start), int(clip_end))
    thigh, knee, foot = leg
    heights = [matrix[12 + up_index] for matrix in clip[foot]]
    floor = math_utils.percentile(heights, FLOOR_PERCENTILE)
    positions = [math_utils.matrix_position(clip[node][0]) for node in leg]
    leg_length = math_utils.distance(positions[0], positions[1]) + math_utils.distance(positions[1], positions[2])
    return {"start": int(clip_start), "lift": [height - floor for height in heights], "floor": floor,
            "leg_length": leg_length, "positions": [math_utils.matrix_position(matrix) for matrix in clip[foot]]}


def get_span_indexes(measurement, frames):
    """Converts a frame span into clip indexes of a leg measurement.

    Args:
        measurement (dict): Result of measure_leg.
        frames (tuple): (start, end) frames.

    Returns:
        tuple: (start, end) indexes, clamped to the clip.
    """
    last = len(measurement["lift"]) - 1
    start = min(last, max(0, int(frames[0]) - measurement["start"]))
    end = min(last, max(start, int(frames[1]) - measurement["start"]))
    return start, end


def pick_planted_legs(scene, legs, frames, up_axis=None):
    """Keeps the legs whose foot is planted during the span (for side "auto").

    A foot counts as planted when its highest point in the span stays within
    PLANTED_HEIGHT_RATIO of the leg length above its own floor (low percentile over the clip).
    When no foot qualifies, the lowest foot is used.

    Args:
        scene (RepairScene): Scene access.
        legs (list): Candidate legs.
        frames (tuple): (start, end) span.
        up_axis (str, optional): Unused; kept for callers that pass it.

    Returns:
        list: Legs to lock.
    """
    planted, lowest = [], None
    for leg in legs:
        measurement = measure_leg(scene, leg)
        start, end = get_span_indexes(measurement, frames)
        lift = max(measurement["lift"][start:end + 1])
        if lift <= PLANTED_HEIGHT_RATIO * measurement["leg_length"]:
            planted.append(leg)
        if lowest is None or lift < lowest[0]:
            lowest = (lift, leg)
    return planted or [lowest[1]]


def get_contact_span(scene, leg, frames, max_extend):
    """Grows a span to the whole contact of a foot (neighbor frames where it stays planted and close).

    Args:
        scene (RepairScene): Scene access.
        leg (list): [thigh, knee, foot].
        frames (tuple): Reported (start, end) frames.
        max_extend (int): Most frames added on each side.

    Returns:
        tuple: (start, end) frames.
    """
    measurement = measure_leg(scene, leg)
    start, end = get_span_indexes(measurement, frames)
    start, end = solvers.extend_contact_span(
        measurement["lift"], start, end, PLANTED_HEIGHT_RATIO * measurement["leg_length"], max_extend,
        positions=measurement["positions"], max_drift=CONTACT_DRIFT_RATIO * measurement["leg_length"],
        up_axis=scene.get_up_axis())
    return start + measurement["start"], end + measurement["start"]


def solve_leg_window(scene, leg, frames, blend, build_targets):
    """Re-poses a leg with two-bone IK over a span (plus blend frames) and keys it.

    Args:
        scene (RepairScene): Scene access.
        leg (list): [thigh, knee, foot] node paths.
        frames (tuple): (start, end) span.
        blend (int): Blend frames before and after.
        build_targets (callable): ``build_targets(foot_positions, span_start, span_end)`` returning
            the target foot position per window index.

    Returns:
        dict: Fix result for this leg.
    """
    thigh, knee, foot = leg
    start_frame, end_frame = int(frames[0]), int(frames[1])
    window_start, window_end = start_frame - blend, end_frame + blend
    matrices, parents = scene.sample([thigh, knee, foot], window_start, window_end)
    frame_count = window_end - window_start + 1
    span_start, span_end = blend, blend + end_frame - start_frame
    weights = solvers.build_blend_weights(frame_count, span_start, span_end, blend)
    foot_positions = scene.get_positions(matrices[foot])
    targets = build_targets(foot_positions, span_start, span_end)
    thigh_parents = get_parent_matrices(matrices, parents.get(thigh), frame_count)
    keyed_frames = []
    new_matrices = {thigh: [], knee: [], foot: []}
    parent_matrices = {thigh: [], knee: [], foot: []}
    bend = None
    for index, weight in enumerate(weights):
        if weight <= 0.0:
            continue
        target = math_utils.lerp(foot_positions[index], targets[index], weight)
        new_thigh, new_knee, new_foot, bend = solvers.solve_leg_matrices(
            matrices[thigh][index], matrices[knee][index], matrices[foot][index], target, bend)
        keyed_frames.append(window_start + index)
        new_matrices[thigh].append(new_thigh)
        new_matrices[knee].append(new_knee)
        new_matrices[foot].append(new_foot)
        parent_matrices[thigh].append(thigh_parents[index])
        parent_matrices[knee].append(new_thigh)
        parent_matrices[foot].append(new_knee)
    result = build_result(frames, [thigh, knee, foot])
    for node_path in (thigh, knee, foot):
        add_key_result(result, scene.key_world_matrices(node_path, keyed_frames, new_matrices[node_path],
                                                        parent_matrices[node_path], ("rotate",)))
    return result


# ------------------------------------------------ Fixes ------------------------------------------------
def foot_lock(scene, frames, nodes, params):
    """Pins planted feet in place over a contact span with two-bone IK, blending in and out.

    The thigh and knee rotate so the ankle reaches the pinned position; the foot keeps its world
    rotation. Bone lengths never change. With side "auto" (the default) every foot that is
    planted during the span is locked, because report spans do not say which foot slid.
    ``pin_at`` picks where the foot is pinned; ``extend_contact`` grows the span to the whole
    contact so the blend does not lift the foot inside the contact (less contact flicker).

    Args:
        scene (RepairScene): Scene access.
        frames (tuple): (start, end) contact frames.
        nodes (list): Optional [thigh, knee, foot].
        params (dict): side, blend, pin_height, min_height, pin_at, extend_contact, extend_max.

    Returns:
        dict: Fix result.
    """
    legs = resolve_legs(scene, nodes, params, "foot_lock")
    if is_auto_side(nodes, params):
        legs = pick_planted_legs(scene, legs, frames)
    up_axis = scene.get_up_axis()
    min_height = params.get("min_height")
    min_height = None if min_height in (None, "") else float(min_height)
    anchor = str(params.get("pin_at") or "average").lower()
    blend = max(0, int(params.get("blend", 4)))

    def build_targets(foot_positions, span_start, span_end):
        """Builds pinned targets for one leg.

        Args:
            foot_positions (list): Foot positions per window index.
            span_start (int): First pinned index.
            span_end (int): Last pinned index.

        Returns:
            list: Targets per window index.
        """
        return solvers.build_pin_targets(foot_positions, span_start, span_end, up_axis,
                                         bool(params.get("pin_height")), min_height, anchor)

    result = build_result(frames, [])
    for leg in legs:
        leg_frames = frames
        if params.get("extend_contact"):
            leg_frames = get_contact_span(scene, leg, frames, max(0, int(params.get("extend_max", 30))))
        leg_result = solve_leg_window(scene, leg, leg_frames, blend, build_targets)
        result["nodes"].extend(leg_result["nodes"])
        add_key_result(result, leg_result)
    return result


def foot_floor_clamp(scene, frames, nodes, params):
    """Lifts only the sinking foot (two-bone IK) so it never goes below the floor in the span.

    Unlike ground_snap the body stays where it is, so the other foot is not moved.

    Args:
        scene (RepairScene): Scene access.
        frames (tuple): (start, end) frames.
        nodes (list): Optional [thigh, knee, foot].
        params (dict): side, floor, margin, blend.

    Returns:
        dict: Fix result.
    """
    legs = resolve_legs(scene, nodes, params, "foot_floor_clamp")
    up_axis = scene.get_up_axis()
    up_index = solvers.get_axis_index(up_axis)
    floor = params.get("floor")
    if floor in (None, ""):
        measurements = [measure_leg(scene, leg) for leg in legs]
        floor = min(measurement["floor"] for measurement in measurements)
    floor = float(floor) + float(params.get("margin", 0.0))
    blend = max(0, int(params.get("blend", 3)))

    def build_targets(foot_positions, span_start, span_end):
        """Clamps the foot height at the floor.

        Args:
            foot_positions (list): Foot positions per window index.
            span_start (int): First index of the span.
            span_end (int): Last index of the span.

        Returns:
            list: Targets per window index.
        """
        targets = []
        for position in foot_positions:
            target = list(position)
            target[up_index] = max(floor, target[up_index])
            targets.append(tuple(target))
        return targets

    result = build_result(frames, [])
    result["floor"] = floor
    for leg in legs:
        matrices = scene.host.sample_world_matrices([leg[2]], int(frames[0]), int(frames[1]))[leg[2]]
        if is_auto_side(nodes, params) and min(matrix[12 + up_index] for matrix in matrices) >= floor:
            continue
        leg_result = solve_leg_window(scene, leg, frames, blend, build_targets)
        result["nodes"].extend(leg_result["nodes"])
        add_key_result(result, leg_result)
    return result


def hips_follow(scene, frames, nodes, params):
    """Moves the body along the ground so the planted foot stays put, without bending the legs.

    Use it when the whole body drifts during a contact (the leg pose is fine but the root
    slides). The offset fades out over ``blend`` frames after the span.

    Args:
        scene (RepairScene): Scene access.
        frames (tuple): (start, end) contact frames.
        nodes (list): Optional [body node]. Defaults to the "hips" role.
        params (dict): side, pin_at, blend.

    Returns:
        dict: Fix result.
    """
    start_frame, end_frame = int(frames[0]), int(frames[1])
    body = scene.resolve_node(nodes[0] if nodes else "hips")
    legs = resolve_legs(scene, [], params, "hips_follow")
    if is_auto_side([], params):
        legs = pick_planted_legs(scene, legs, frames)
    up_axis = scene.get_up_axis()
    up_index = solvers.get_axis_index(up_axis)
    anchor = str(params.get("pin_at") or "average").lower()
    blend = max(0, int(params.get("blend", 8)))
    window_start, window_end = start_frame - blend, end_frame + blend
    feet = [leg[2] for leg in legs]
    matrices, parents = scene.sample([body] + feet, window_start, window_end)
    frame_count = window_end - window_start + 1
    span_start, span_end = blend, blend + end_frame - start_frame
    weights = solvers.build_blend_weights(frame_count, span_start, span_end, blend)
    drifts = []
    for foot in feet:
        positions = scene.get_positions(matrices[foot])
        pin = solvers.get_pin_position(positions, span_start, span_end, anchor, up_axis)
        drifts.append([tuple(0.0 if axis == up_index else positions[index][axis] - pin[axis] for axis in range(3))
                       for index in range(frame_count)])
    body_parents = get_parent_matrices(matrices, parents.get(body), frame_count)
    keyed_frames, new_worlds, parent_worlds = [], [], []
    for index, weight in enumerate(weights):
        if weight <= 0.0:
            continue
        span_index = min(span_end, max(span_start, index))
        drift = [sum(foot_drift[span_index][axis] for foot_drift in drifts) / len(drifts) for axis in range(3)]
        position = math_utils.subtract(math_utils.matrix_position(matrices[body][index]),
                                       math_utils.scale(drift, weight))
        keyed_frames.append(window_start + index)
        new_worlds.append(transform_math.replace_position(matrices[body][index], position))
        parent_worlds.append(body_parents[index])
    result = build_result(frames, [body])
    add_key_result(result, scene.key_world_matrices(body, keyed_frames, new_worlds, parent_worlds, ("translate",)))
    return result


def ground_snap(scene, frames, nodes, params):
    """Moves the body up or down so its lowest contact point sits on the floor during the span.

    Args:
        scene (RepairScene): Scene access.
        frames (tuple): (start, end) frames.
        nodes (list): Optional [body node] to move. Defaults to the "hips" role.
        params (dict): mode, floor, contacts, blend, smooth.

    Returns:
        dict: Fix result.
    """
    start_frame, end_frame = int(frames[0]), int(frames[1])
    body = scene.resolve_node(nodes[0] if nodes else "hips")
    contact_names = params.get("contacts") or [role for role in DEFAULT_CONTACT_ROLES if role in scene.roles]
    if not contact_names:
        raise ValueError('ground_snap needs "contacts" (foot/toe nodes) or a skeleton template with foot roles.')
    contacts = [scene.resolve_node(name) for name in contact_names]
    up_index = solvers.get_axis_index(scene.get_up_axis())
    blend = max(0, int(params.get("blend", 4)))
    window_start, window_end = start_frame - blend, end_frame + blend
    floor = params.get("floor")
    if floor in (None, ""):
        clip_start, clip_end = scene.host.get_time_range("playback")
        clip_matrices = scene.host.sample_world_matrices(contacts, int(clip_start), int(clip_end))
        lowest = [min(clip_matrices[path][index][12 + up_index] for path in contacts)
                  for index in range(len(clip_matrices[contacts[0]]))]
        floor = math_utils.percentile(lowest, FLOOR_PERCENTILE)
    matrices, parents = scene.sample([body] + [path for path in contacts if path != body], window_start, window_end)
    frame_count = window_end - window_start + 1
    lowest = [min(matrices[path][index][12 + up_index] for path in contacts) for index in range(frame_count)]
    offsets = solvers.build_ground_offsets(lowest, float(floor), str(params.get("mode") or "both"),
                                           int(params.get("smooth", 2)))
    weights = solvers.build_blend_weights(frame_count, blend, blend + end_frame - start_frame, blend)
    body_parents = get_parent_matrices(matrices, parents.get(body), frame_count)
    keyed_frames, new_worlds, parent_worlds = [], [], []
    for index, weight in enumerate(weights):
        if weight <= 0.0:
            continue
        position = list(math_utils.matrix_position(matrices[body][index]))
        position[up_index] += offsets[index] * weight
        keyed_frames.append(window_start + index)
        new_worlds.append(transform_math.replace_position(matrices[body][index], position))
        parent_worlds.append(body_parents[index])
    result = build_result(frames, [body])
    result["floor"] = float(floor)
    add_key_result(result, scene.key_world_matrices(body, keyed_frames, new_worlds, parent_worlds, ("translate",)))
    return result
