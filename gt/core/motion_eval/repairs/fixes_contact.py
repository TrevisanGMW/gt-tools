"""
Contact fix: contact_settle removes contact flicker by making each foot read clearly as down or up.

It measures contact the same way the checks do (checks_biped.compute_contacts on the sampled
clip), picks one clean state per frame for the flagged span (with at most one change, so a real
landing or lift-off survives), and moves only that leg with two-bone IK: down frames are lowered
onto the floor and held in place, up frames are lifted clear of the contact height.

Every fix has the signature ``fix(scene, frames, nodes, params)`` (see fixes.py).
"""

from .. import checks_base
from .. import checks_biped
from .. import math_utils
from . import solvers
from .fixes_common import add_key_result
from .fixes_common import build_result
from .fixes_feet import resolve_legs
from .fixes_feet import solve_leg_window

CONTACT_WEIGHT = 0.5
HOLD_DRIFT_RATIO = 0.06
SIDES = ("left", "right")


def build_motion_data(scene, settings=None):
    """Samples the whole clip of the resolved roles into a MotionData, like an evaluation does.

    Args:
        scene (RepairScene): Scene access (its template roles are sampled).
        settings (dict, optional): Preset settings that change contact detection.

    Returns:
        MotionData: Sampled biped motion.

    Raises:
        ValueError: When the scene has no resolved roles.
    """
    roles = dict(scene.roles)
    if not roles:
        raise ValueError("contact_settle needs a skeleton template so it can measure contact like the checks.")
    clip_start, clip_end = scene.host.get_time_range("playback")
    start_frame, end_frame = int(round(clip_start)), int(round(clip_end))
    node_paths = list(dict.fromkeys(roles.values()))
    matrices = scene.host.sample_world_matrices(node_paths, start_frame, end_frame)
    parents = scene.host.get_parents(node_paths)
    sample = {
        "fps": scene.host.get_fps(), "start_frame": start_frame, "frame_count": end_frame - start_frame + 1,
        "up_axis": scene.get_up_axis(), "meters_per_unit": scene.host.get_meters_per_unit(),
        "nodes": dict((path, {"matrices": matrices[path], "parent": parents.get(path)}) for path in node_paths),
        "roles": roles,
    }
    return checks_base.MotionData(sample, mode=checks_base.MODE_BIPED, settings=settings or {})


def count_crossings(weights):
    """Counts how often contact weights cross 0.5 (the check's on/off line).

    Args:
        weights (list): Contact weights.

    Returns:
        int: Crossings.
    """
    return sum(1 for index in range(1, len(weights))
               if (weights[index] >= CONTACT_WEIGHT) != (weights[index - 1] >= CONTACT_WEIGHT))


def get_lowest_heights(data, contact):
    """Gets, per frame, the lowest foot/toe/heel height above that joint's own floor.

    Args:
        data (MotionData): Sampled motion.
        contact (dict): One side of checks_biped.compute_contacts.

    Returns:
        list: Heights per frame (Y-up, scene units).
    """
    lowest = [None] * data.frame_count
    for path in contact["joints"]:
        heights = [position[1] for position in data.get_positions(path)]
        floor = math_utils.percentile(heights, checks_biped.FLOOR_PERCENTILE)
        for index, height in enumerate(heights):
            value = height - floor
            lowest[index] = value if lowest[index] is None else min(lowest[index], value)
    return [value or 0.0 for value in lowest]


def pick_flickering_sides(contacts, span_start, span_end, sides):
    """Keeps the sides whose contact toggles inside the span (all of them when none toggles).

    Args:
        contacts (dict): Result of checks_biped.compute_contacts.
        span_start (int): First clip index.
        span_end (int): Last clip index.
        sides (list): Candidate sides.

    Returns:
        list: Sides to settle.
    """
    window_start = max(0, span_start - 1)
    scored = [(count_crossings(contacts[side]["weights"][window_start:span_end + 2]), side) for side in sides]
    flickering = [side for crossings, side in scored if crossings >= 2]
    return flickering or [side for crossings, side in scored if crossings >= 1] or list(sides)


def get_leg_side(scene, leg):
    """Finds whether a leg is the left or right one from the template roles.

    Args:
        scene (RepairScene): Scene access.
        leg (list): [thigh, knee, foot].

    Returns:
        str: "left" or "right".

    Raises:
        ValueError: When the foot is not a foot role.
    """
    for side in SIDES:
        if scene.roles.get(f"{side}_foot") == leg[2]:
            return side
    raise ValueError(f"{leg[2].split('|')[-1]} is not the left_foot or right_foot role of the skeleton template.")


def extend_down_edges(weights, positions, span_start, span_end, states, max_extend, max_drift):
    """Grows the span over the rest of a contact that continues past a down edge.

    Without this, a held foot would be released while it is still on the floor, which reads as
    sliding at the span edges.

    Args:
        weights (list): Contact weights over the whole clip.
        positions (list): Y-up ankle positions over the whole clip.
        span_start (int): First clip index of the span.
        span_end (int): Last clip index of the span.
        states (list): True (down) per span frame.
        max_extend (int): Most frames added on each side.
        max_drift (float): Largest ground-plane distance from the edge frame.

    Returns:
        tuple: (start, end, states) for the grown span.
    """
    def is_held(index, edge):
        """Checks whether a frame continues the contact of an edge frame.

        Args:
            index (int): Clip index.
            edge (int): Edge clip index.

        Returns:
            bool: True when grounded and close to the edge position.
        """
        drift = math_utils.planar_distance(positions[index], positions[edge])
        return weights[index] >= CONTACT_WEIGHT and drift <= max_drift

    start, end = span_start, span_end
    if states and states[0]:
        while start > 0 and span_start - start < max_extend and is_held(start - 1, span_start):
            start -= 1
    if states and states[-1]:
        while end < len(weights) - 1 and end - span_end < max_extend and is_held(end + 1, span_end):
            end += 1
    return start, end, [True] * (span_start - start) + list(states) + [True] * (end - span_end)


def build_run_pins(foot_positions, states, offset, up_index):
    """Gets, per down frame, the ground-plane position its run of down frames is held at.

    Args:
        foot_positions (list): Ankle positions per window index.
        states (list): True (down) per span index.
        offset (int): Window index of span index 0.
        up_index (int): Up axis index.

    Returns:
        dict: Span index to pin position (down frames only).
    """
    pins = {}
    index = 0
    while index < len(states):
        if not states[index]:
            index += 1
            continue
        run_end = index
        while run_end + 1 < len(states) and states[run_end + 1]:
            run_end += 1
        pin = solvers.get_pin_position(foot_positions, offset + index, offset + run_end)
        for run_index in range(index, run_end + 1):
            pins[run_index] = pin
        index = run_end + 1
    return pins


def settle_leg(scene, leg, frames, states, offsets, params):
    """Moves one leg so its foot follows the settled plan.

    Args:
        scene (RepairScene): Scene access.
        leg (list): [thigh, knee, foot].
        frames (tuple): (start, end) span.
        states (list): True (down) per span frame.
        offsets (list): Up-axis offsets per span frame.
        params (dict): blend, hold.

    Returns:
        dict: Fix result for this leg.
    """
    blend = max(0, int(params.get("blend", 6)))
    up_index = solvers.get_axis_index(scene.get_up_axis())
    hold = bool(params.get("hold", True))

    def build_targets(foot_positions, span_start, span_end):
        """Builds the settled ankle targets for the window.

        Args:
            foot_positions (list): Ankle positions per window index.
            span_start (int): Window index of the first span frame.
            span_end (int): Window index of the last span frame.

        Returns:
            list: Targets per window index.
        """
        pins = build_run_pins(foot_positions, states, span_start, up_index) if hold else {}
        targets = []
        for index, position in enumerate(foot_positions):
            span_index = min(span_end, max(span_start, index)) - span_start
            target = list(position)
            if span_index in pins:
                for axis in range(3):
                    if axis != up_index:
                        target[axis] = pins[span_index][axis]
            target[up_index] += offsets[span_index]
            targets.append(tuple(target))
        return targets

    return solve_leg_window(scene, leg, frames, blend, build_targets)


def contact_settle(scene, frames, nodes, params):
    """Removes contact flicker: each foot reads clearly as down or up over the span.

    Args:
        scene (RepairScene): Scene access (needs a skeleton template).
        frames (tuple): (start, end) flagged frames.
        nodes (list): Optional [thigh, knee, foot].
        params (dict): side, mode, blend, hold, extend_max, down_ratio, up_ratio, height_ratio,
            min_base_speed.

    Returns:
        dict: Fix result with a "plans" entry per settled side.
    """
    data = build_motion_data(scene, {"contact_height_ratio": float(params.get("height_ratio", 0.06)),
                                     "contact_min_base_speed": float(params.get("min_base_speed", 0.5))})
    contacts = checks_biped.compute_contacts(data)
    height_end = float(params.get("height_ratio", 0.06)) * data.get_reference_length()
    height_start = height_end / 6.0
    span_start = min(data.frame_count - 1, max(0, int(frames[0]) - data.start_frame))
    span_end = min(data.frame_count - 1, max(span_start, int(frames[1]) - data.start_frame))
    legs = resolve_legs(scene, nodes, params, "contact_settle")
    sides = [get_leg_side(scene, leg) for leg in legs]
    if not nodes and str(params.get("side") or "auto").lower() == "auto":
        chosen = pick_flickering_sides(contacts, span_start, span_end, sides)
        legs = [leg for leg, side in zip(legs, sides) if side in chosen]
        sides = [side for side in sides if side in chosen]
    mode = str(params.get("mode") or "auto").lower()
    result = build_result(frames, [])
    result["plans"] = {}
    for leg, side in zip(legs, sides):
        weights = contacts[side]["weights"]
        states = solvers.choose_contact_states(weights[span_start:span_end + 1], mode)
        side_start, side_end = span_start, span_end
        if params.get("hold", True):
            side_start, side_end, states = extend_down_edges(
                weights, data.get_role_positions(f"{side}_foot"), span_start, span_end, states,
                max(0, int(params.get("extend_max", 20))), HOLD_DRIFT_RATIO * data.get_reference_length())
        lowest = get_lowest_heights(data, contacts[side])[side_start:side_end + 1]
        offsets = solvers.build_settle_offsets(lowest, states, height_start * float(params.get("down_ratio", 0.5)),
                                               height_end * float(params.get("up_ratio", 1.25)))
        if len(offsets) > 2:
            offsets = [vector[0] for vector in solvers.smooth_vectors([(value, 0.0, 0.0) for value in offsets], 1)]
        result["plans"][side] = "".join("d" if down else "u" for down in states)
        span_frames = (data.start_frame + side_start, data.start_frame + side_end)
        leg_result = settle_leg(scene, leg, span_frames, states, offsets, params)
        result["nodes"].extend(leg_result["nodes"])
        add_key_result(result, leg_result)
    return result
