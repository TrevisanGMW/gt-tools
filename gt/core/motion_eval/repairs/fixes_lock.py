"""Foot-lock corrections confined to their reported issue intervals."""

from .. import math_utils
from . import lock_timing
from . import solvers
from .fixes_common import add_key_result
from .fixes_common import build_result
from .fixes_common import get_parent_matrices


def limit_target(hip, knee, ankle, target, max_extension):
    """Limits a correction without straightening a leg past its allowed reach.

    Existing source extension is preserved when it already exceeds the margin.

    Args:
        hip (tuple): Hip world position.
        knee (tuple): Knee world position.
        ankle (tuple): Original ankle world position.
        target (tuple): Proposed ankle world position.
        max_extension (float): Maximum fraction of combined bone length.

    Returns:
        tuple: Reach-safe target and whether the correction was limited.
    """
    length = math_utils.distance(hip, knee) + math_utils.distance(knee, ankle)
    maximum = max(math_utils.distance(hip, ankle), length * max_extension)
    if math_utils.distance(hip, target) <= maximum:
        return target, False
    lower, upper = 0.0, 1.0
    for unused_iteration in range(24):
        fraction = (lower + upper) * 0.5
        candidate = math_utils.lerp(ankle, target, fraction)
        if math_utils.distance(hip, candidate) <= maximum:
            lower = fraction
        else:
            upper = fraction
    return math_utils.lerp(ankle, target, lower), True


def motion_metrics(positions):
    """Measures total travel and the largest per-frame displacement.

    Args:
        positions (list): Sampled world positions.

    Returns:
        tuple: Total path length and largest step.
    """
    steps = [math_utils.distance(previous, current)
             for previous, current in zip(positions, positions[1:])]
    return sum(steps), max(steps or [0.0])


def leading_leg(scene, legs, matrices, up_index, side):
    """Selects a requested leading side or the foot initially moving least.

    Args:
        scene (RepairScene): Scene access.
        legs (list): Resolved leg chains.
        matrices (dict): Sampled world matrices.
        up_index (int): Vertical position index.
        side (str): auto, left or right.

    Returns:
        int: Leading leg index.

    Raises:
        ValueError: When the leading side is invalid.
    """
    if side not in ("auto", "left", "right"):
        raise ValueError('lead_side must be "auto", "left", or "right".')
    scores = []
    for leg in legs:
        positions = scene.get_positions(matrices[leg[2]])[:4]
        speed = sum(sum((current[axis] - previous[axis]) ** 2
                        for axis in range(3) if axis != up_index) ** 0.5
                    for previous, current in zip(positions, positions[1:]))
        name = leg[2].split("|")[-1].split(":")[-1].lower()
        preferred = (scene.roles.get(f"{side}_foot") == leg[2]
                     or side in name or name.endswith("_" + side[0]))
        scores.append((0 if side != "auto" and preferred else 1, speed))
    return min(range(len(legs)), key=scores.__getitem__)


def apply_foot_lock(scene, legs, frames, params):
    """Applies conservative corrections wholly inside a reported issue span.

    Edge samples stay unchanged. Proposed corrections are skipped if they increase
    total ankle travel or peak ankle displacement by more than five percent.
    Contact-extension settings are retained in serialized recipes but cannot
    enlarge the edit interval.

    Args:
        scene (RepairScene): Scene access.
        legs (list): Resolved thigh, knee and foot chains.
        frames (tuple): Inclusive issue interval.
        params (dict): Blend, stagger, side, anchor and reach settings.

    Returns:
        dict: Keying result with per-leg status and reasons for skipped repairs.

    Raises:
        ValueError: When the issue interval or reach setting is invalid.
    """
    clip_start, clip_end = scene.host.get_time_range("playback")
    first = max(int(clip_start), int(frames[0]))
    last = min(int(clip_end), int(frames[1]))
    if last < first:
        raise ValueError("The requested lock does not overlap the playback range.")
    result = build_result(frames, [])
    result["locks"] = []
    entry, release, stagger = lock_timing.resolve_timing(params, scene.host.get_fps())
    extension = float(params.get("max_extension", 0.98))
    if not 0.0 < extension <= 1.0:
        raise ValueError("max_extension must be greater than zero and at most one.")
    count = last - first + 1
    if count < 7:
        result["warnings"].append(f"Foot lock skipped: issue {first}-{last} is too short for bounded easing.")
        result["locks"] = [{"foot": leg[2], "issue_frames": [first, last], "status": "skipped",
                            "reason": "insufficient transition frames"} for leg in legs]
        return result
    nodes = list(dict.fromkeys(node for leg in legs for node in leg))
    matrices, parents = scene.sample(nodes, first, last)
    up_index = solvers.get_axis_index(scene.get_up_axis())
    leader = leading_leg(scene, legs, matrices, up_index, str(params.get("lead_side") or "auto").lower())
    for leg_index, leg in enumerate(legs):
        thigh, knee, foot = leg
        offset = 0 if len(legs) == 1 else (-(stagger // 2) if leg_index == leader else (stagger + 1) // 2)
        weights = lock_timing.bounded_weights(count, entry, release, offset)
        positions = scene.get_positions(matrices[foot])
        targets = solvers.build_pin_targets(
            positions, 0, count - 1, scene.get_up_axis(), bool(params.get("pin_height")),
            params.get("min_height"), str(params.get("pin_at") or "average").lower())
        changed = {node: [] for node in leg}
        parent_world = {node: [] for node in leg}
        thigh_parents = get_parent_matrices(matrices, parents.get(thigh), count)
        proposed = list(positions)
        keyed = []
        bend = None
        limited = 0
        for index, weight in enumerate(weights):
            if weight <= 0.0:
                continue
            target = math_utils.lerp(positions[index], targets[index], weight)
            target, was_limited = limit_target(
                math_utils.matrix_position(matrices[thigh][index]),
                math_utils.matrix_position(matrices[knee][index]), positions[index], target, extension)
            limited += int(was_limited)
            new_thigh, new_knee, new_foot, bend = solvers.solve_leg_matrices(
                matrices[thigh][index], matrices[knee][index], matrices[foot][index], target, bend)
            proposed[index] = math_utils.matrix_position(new_foot)
            keyed.append(first + index)
            for node, matrix, parent in zip(
                    leg, (new_thigh, new_knee, new_foot), (thigh_parents[index], new_thigh, new_knee)):
                changed[node].append(matrix)
                parent_world[node].append(parent)
        original_metrics = motion_metrics(positions)
        proposed_metrics = motion_metrics(proposed)
        peaks = [index for index, weight in enumerate(weights) if weight >= 1.0]
        record = {"foot": foot, "issue_frames": [first, last], "limited_frames": limited,
                  "frames": [first + min(peaks), first + max(peaks)],
                  "blend_in": min(peaks) - 1, "blend_out": count - 2 - max(peaks),
                  "original_travel": original_metrics[0], "proposed_travel": proposed_metrics[0],
                  "original_peak_step": original_metrics[1], "proposed_peak_step": proposed_metrics[1]}
        result["locks"].append(record)
        if max(math_utils.distance(original, corrected)
               for original, corrected in zip(positions, proposed)) <= 1e-6:
            record.update(status="skipped", reason="no reach-safe correction")
            continue
        if any(proposed_value > original_value * 1.05 + 1e-6
               for proposed_value, original_value in zip(proposed_metrics, original_metrics)):
            record.update(status="skipped", reason="would increase foot travel or peak displacement")
            result["warnings"].append(f"Foot lock skipped for {foot}: {record['reason']}.")
            continue
        record.update(status="applied", keyed_frames=[min(keyed), max(keyed)])
        result["nodes"].extend(leg)
        scene.host.prepare_bounded_keying(leg, first, last)
        for node in leg:
            add_key_result(result, scene.key_world_matrices(
                node, keyed, changed[node], parent_world[node], ("rotate",)))
    return result
