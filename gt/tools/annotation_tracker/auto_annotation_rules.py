"""Calibration profile rules and temporal locomotion filtering."""

import math
from itertools import groupby


LOCOMOTION_STATES = ("walk", "jog", "run", "sprint")
RANGE_NAME_FIELD = "range_name"
TRANSITION_MODES = {
    "activity": "Enter on arrival, exit on departure",
    "locomotion": "Enter on movement start, exit on stop",
    "off": "Do not label transitions",
}
RULES = {
    "minimum_range_frames": (12, 1, 10000),
    "gap_frames": (8, 0, 10000),
    "transition_buffer_frames": (6, 0, 10000),
    "minimum_travel": (0.42, 0.0, 10.0),
    "start_speed_multiplier": (1.25, 1.0, 4.0),
    "transition_mode": ("activity", None, None),
    "allow_initial_departure": (False, None, None),
    "require_paired_transitions": (False, None, None),
    "pose_threshold": (0.65, 0.0, 4.0),
    "pose_minimum_frames": (9, 1, 10000),
    "pose_margin": (0.12, 0.0, 4.0),
}
DEFAULT_RULES = {key: spec[0] for key, spec in RULES.items()}


def normalize_rules(values):
    """Validates profile-specific rule overrides.

    Args:
        values (dict): Sparse settings saved in a calibration profile.

    Returns:
        dict: Validated known rule overrides.
    """
    if not isinstance(values, dict):
        raise ValueError("Calibration detection rules must be an object.")
    overrides = {}
    for key in values.keys() & RULES.keys():
        value = values[key]
        default, minimum, maximum = RULES[key]
        if type(default) is float:
            valid = type(value) in (int, float) and math.isfinite(value) and minimum <= value <= maximum
        elif type(default) is int:
            valid = type(value) is int and minimum <= value <= maximum
        elif type(default) is bool:
            valid = type(value) is bool
        else:
            valid = isinstance(value, str) and value in TRANSITION_MODES
        if not valid:
            raise ValueError(f"Invalid value for calibration rule '{key}'.")
        overrides[key] = value
    return overrides


def spans(labels):
    """Groups consecutive labels and returns inclusive indexes.

    Args:
        labels (iterable): Frame labels in timeline order.

    Yields:
        tuple: Label, first index, last index.
    """
    start = 0
    for label, group in groupby(labels):
        length = sum(1 for _ in group)
        yield label, start, start + length - 1
        start += length


def movement_mask(speeds, root_ground, gait, idle_speed, rules):
    """Finds sustained travel or repeated in-place gait through stationary motion.

    Args:
        speeds (list): Normalized speed per frame.
        root_ground (list or None): Normalized horizontal pelvis positions.
        gait (list or None): Repeated gait speeds independent of root motion.
        idle_speed (float): Maximum speed at rest.
        rules (dict): Resolved calibration profile rules.

    Returns:
        list: Boolean mask of frames which belong to qualifying locomotion.
    """
    moving = []
    active = False
    for speed in speeds:
        threshold = idle_speed if active else idle_speed * rules["start_speed_multiplier"]
        active = speed > threshold
        moving.append(active)

    groups = list(spans(moving))
    for active, first, last in groups[1:-1]:
        if not active and last - first + 1 <= rules["gap_frames"]:
            moving[first:last + 1] = [True] * (last - first + 1)

    for active, first, last in list(spans(moving)):
        if not active:
            continue
        length = last - first + 1
        gait_frames = sum(value > idle_speed for value in gait[first:last + 1]) if gait else 0
        sustained_gait = gait_frames >= max(1, math.ceil(length * 0.60))
        required = min(rules["minimum_range_frames"], len(speeds))
        if root_ground:
            origin = root_ground[max(0, first - 1)]
            travel = max(math.dist(origin, point) for point in root_ground[first:last + 1])
        else:
            travel = rules["minimum_travel"]
        if length < required or (travel < rules["minimum_travel"] and not sustained_gait):
            moving[first:last + 1] = [False] * length

    groups = list(spans(moving))
    if len(groups) > 1:
        for active, first, last in (groups[0], groups[-1]):
            length = last - first + 1
            if not active and length <= rules["gap_frames"]:
                moving[first:last + 1] = [True] * length
    return moving


def transition_markers(moving, rules, allowed, writable):
    """Places arrival and departure buffers around stable motion bouts.

    Args:
        moving (list): Boolean mask of confirmed travel.
        rules (dict): Resolved calibration rules.
        allowed (set): Transition labels supported by the active schema.
        writable (list): Boolean mask of frames Auto Annotate may fill.

    Returns:
        list: Label, first index, and last index for each emitted transition.
    """
    mode = rules["transition_mode"]
    buffer = rules["transition_buffer_frames"]
    if mode == "off" or not buffer or not allowed:
        return []
    arrival, departure = ("enter", "exit") if mode == "activity" else ("exit", "enter")
    markers = []
    arrived = False
    for active, first, last in spans(moving):
        if not active or first == 0 and last == len(moving) - 1:
            continue
        if first == last and 0 < first < len(moving) - 1:
            continue
        width = min(buffer, max(1, (last - first + 1) // 3))
        allow_departure = mode != "activity" or arrived or rules["allow_initial_departure"]
        if first > 0 and departure in allowed and allow_departure and all(writable[first:first + width]):
            markers.append((departure, first, first + width - 1))
        if last + 1 < len(moving) and arrival in allowed and all(writable[last - width + 1:last + 1]):
            markers.append((arrival, last - width + 1, last))
        arrived = arrived or last + 1 < len(moving)
    if not rules["require_paired_transitions"]:
        return markers
    paired = []
    pending = None
    for marker in markers:
        if marker[0] == "enter":
            pending = marker
        elif pending is not None:
            paired.extend((pending, marker))
            pending = None
    return paired
