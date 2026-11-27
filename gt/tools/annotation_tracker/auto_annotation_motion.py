"""Deterministic analysis of normalized humanoid motion and pose cues."""

import math
import statistics
from bisect import bisect_left
from collections import defaultdict
from itertools import groupby

from gt.tools.annotation_tracker.auto_annotation_model import (
    DEFAULT_IDLE_SPEED,
    DEFAULT_STANDING_CUES,
    DEFAULT_WALK_SPEED,
    FEATURE_SCALES,
    get_schema_fields,
    summarize_example,
    supports_value,
)
from gt.tools.annotation_tracker.auto_annotation_rules import (
    DEFAULT_RULES,
    LOCOMOTION_STATES,
    RANGE_NAME_FIELD,
    movement_mask,
    spans,
    transition_markers,
)


SIDES = ("left", "right")
PRIMARY_POSE_CUES = {"pelvis_height", "knee_flexion", "thigh_ratio", "torso_pitch", "torso_roll"}


def _difference(point, origin):
    """Subtracts one 3D position from another.

    Args:
        point (tuple): Position to express relative to the origin.
        origin (tuple): Origin position.

    Returns:
        tuple: Relative position.
    """
    return tuple(value - center for value, center in zip(point, origin))


def _planar_length(vector):
    """Measures a vector in the canonical Y-up ground plane.

    Args:
        vector (tuple): Canonical XYZ vector.

    Returns:
        float: Ground-plane magnitude.
    """
    return math.hypot(vector[0], vector[2])


def _quantile(values, fraction):
    """Gets a robust percentile from a sequence of measurements.

    Args:
        values (list): Nonempty measurements.
        fraction (float): Desired fraction between zero and one.

    Returns:
        float: Nearest-rank sample value.
    """
    ordered = sorted(values)
    return ordered[round((len(ordered) - 1) * fraction)]


def _leg_length(positions):
    """Estimates anatomical scale from the sampled skeleton.

    Args:
        positions (list): Per-frame role positions.

    Returns:
        float: Median leg-chain length, or a supported fallback estimate.
    """
    lengths = []
    for sample in positions[:24]:
        for side in SIDES:
            hip = sample.get(f"{side}_upper_leg")
            knee = sample.get(f"{side}_knee")
            if hip and knee:
                foot = sample[f"{side}_foot"]
                lengths.append(math.dist(hip, knee) + math.dist(knee, foot))
    if lengths:
        return statistics.median(lengths)
    return _quantile(
        [math.dist(sample["pelvis"], sample[f"{side}_foot"]) for sample in positions for side in SIDES], 0.95
    )


def _flexion(hip, knee, foot):
    """Measures flexion away from a straight leg.

    Args:
        hip (tuple): Hip position.
        knee (tuple): Knee position.
        foot (tuple): Ankle position.

    Returns:
        float: Flexion angle in degrees.
    """
    thigh = _difference(knee, hip)
    shin = _difference(foot, knee)
    magnitude = math.hypot(*thigh) * math.hypot(*shin)
    if not magnitude:
        return 0.0
    dot = sum(left * right for left, right in zip(thigh, shin)) / magnitude
    return math.degrees(math.acos(max(-1.0, min(1.0, dot))))


def _describe_pose(sample, floor, scale):
    """Measures anatomical pose cues independent of rig height and headings.

    Args:
        sample (dict): Current anatomical role positions.
        floor (float): Estimated support plane.
        scale (float): Reference leg length.

    Returns:
        dict: Available normalized height, distance, and angle measurements.
    """
    pelvis = sample["pelvis"]
    feet = [sample[f"{side}_foot"] for side in SIDES]
    descriptor = {
        "pelvis_height": (pelvis[1] - floor) / scale,
        "left_foot_height": (sample.get("left_toe", feet[0])[1] - floor) / scale,
        "right_foot_height": (sample.get("right_toe", feet[1])[1] - floor) / scale,
        "foot_separation": _planar_length(_difference(*feet)) / scale,
    }
    flexions = []
    thigh_ratios = []
    knee_heights = []
    for side in SIDES:
        hip = sample.get(f"{side}_upper_leg")
        knee = sample.get(f"{side}_knee")
        if hip and knee:
            thigh_length = math.dist(hip, knee)
            if thigh_length:
                flexions.append(_flexion(hip, knee, sample[f"{side}_foot"]))
                thigh_ratios.append(abs(hip[1] - knee[1]) / thigh_length)
                knee_heights.append((knee[1] - floor) / scale)
    if flexions:
        descriptor.update(
            knee_flexion=max(flexions), thigh_ratio=min(thigh_ratios), knee_height=min(knee_heights)
        )

    left = sample.get("left_upper_leg")
    right = sample.get("right_upper_leg")
    lateral = _difference(right, left) if left and right else (0, 0, 0)
    span = _planar_length(lateral)
    if span:
        lateral_x, lateral_z = lateral[0] / span, lateral[2] / span
        forward_x, forward_z = lateral_z, -lateral_x
        toe_offsets = [
            _difference(sample[f"{side}_toe"], sample[f"{side}_foot"])
            for side in SIDES if f"{side}_toe" in sample
        ]
        if sum(point[0] * forward_x + point[2] * forward_z for point in toe_offsets) < 0:
            forward_x, forward_z = -forward_x, -forward_z
        foot_offsets = [_difference(foot, pelvis) for foot in feet]
        descriptor["foot_forward"] = sum(
            point[0] * forward_x + point[2] * forward_z for point in foot_offsets
        ) / (2 * scale)
        chest = sample.get("chest") or sample.get("spine")
        if chest:
            torso = _difference(chest, pelvis)
            descriptor["torso_pitch"] = math.degrees(
                math.atan2(torso[0] * forward_x + torso[2] * forward_z, torso[1])
            )
            descriptor["torso_roll"] = math.degrees(
                math.atan2(torso[0] * lateral_x + torso[2] * lateral_z, torso[1])
            )
    chest = sample.get("chest") or sample.get("spine")
    for side in SIDES:
        hand = sample.get(f"{side}_hand")
        if chest and hand:
            descriptor[f"{side}_hand_reach"] = math.dist(hand, chest) / scale
    if "left_hand" in sample and "right_hand" in sample:
        descriptor["hand_separation"] = math.dist(sample["left_hand"], sample["right_hand"]) / scale
    return descriptor


def _smooth(values, radius):
    """Averages a centered window using cumulative sums.

    Args:
        values (list): Time series.
        radius (int): Frames on either side to include.

    Returns:
        list: Smoothed time series.
    """
    sums = [0.0]
    for value in values:
        sums.append(sums[-1] + value)
    output = []
    for index in range(len(values)):
        start = max(0, index - radius)
        end = min(len(values), index + radius + 1)
        output.append((sums[end] - sums[start]) / (end - start))
    return output


def _in_place_speeds(positions, descriptors, factor, fps):
    """Estimates gait speed when a cycle is authored in place.

    Args:
        positions (list): Per-frame joint positions.
        descriptors (list): Per-frame normalized pose cues.
        factor (float): Scene units per frame to leg lengths per second.
        fps (float): Scene frame rate.

    Returns:
        list: Gait speed where both feet show alternating swing and support.
    """
    side_speeds = {}
    side_lifted = {}
    for side in SIDES:
        local = [_difference(sample[f"{side}_foot"], sample["pelvis"]) for sample in positions]
        side_speeds[side] = [0.0] + [
            _planar_length(_difference(current, previous)) * factor
            for previous, current in zip(local, local[1:])
        ]
        baseline = _quantile([sample[f"{side}_foot_height"] for sample in descriptors], 0.10)
        side_lifted[side] = [
            sample[f"{side}_foot_height"] - baseline > 0.045 for sample in descriptors
        ]
    radius = max(1, round(fps * 0.32))
    lift_ratios = {side: _smooth(side_lifted[side], radius) for side in SIDES}
    left_only = _smooth([
        left and not right for left, right in zip(side_lifted["left"], side_lifted["right"])
    ], radius)
    right_only = _smooth([
        right and not left for left, right in zip(side_lifted["left"], side_lifted["right"])
    ], radius)
    combined = _smooth([
        (left + right) * 0.5 for left, right in zip(side_speeds["left"], side_speeds["right"])
    ], radius)
    swaps = []
    previous = 0
    for index, (left, right) in enumerate(zip(side_lifted["left"], side_lifted["right"])):
        side = int(left) - int(right)
        if side and side != previous:
            if previous:
                swaps.append(index)
            previous = side
    cadence_window = max(1, round(fps * 0.62))
    return [
        speed if left > 0.08 and right > 0.08 and all(
            0.10 < lift_ratios[side][index] < 0.85 for side in SIDES
        ) and bisect_left(swaps, index + cadence_window + 1) - bisect_left(swaps, index - cadence_window) >= 2 else 0.0
        for index, (left, right, speed) in enumerate(zip(left_only, right_only, combined))
    ]


def analyze_motion(samples, floor_height=None):
    """Computes normalized descriptors and locomotion telemetry once per scene.

    Args:
        samples (dict): Sampled scene joints and timing.
        floor_height (float, optional): Known floor in scene units along the up axis.

    Returns:
        dict: Motion data ready for segmentation, calibration, and quality checks.
    """
    positions = samples["positions"]
    fps = samples["fps"]
    scale = _leg_length(positions)
    if not math.isfinite(scale) or scale <= 1e-8:
        raise ValueError("Could not measure a nonzero leg length for motion normalization.")
    floor = floor_height if floor_height is not None else _quantile(
        [sample.get(f"{side}_toe", sample[f"{side}_foot"])[1] for sample in positions for side in SIDES], 0.04
    )
    descriptors = [_describe_pose(sample, floor, scale) for sample in positions]
    factor = fps / scale
    deltas = [
        _difference(current["pelvis"], previous["pelvis"])
        for previous, current in zip(positions, positions[1:])
    ]
    root_speed = [_planar_length(delta) * factor for delta in deltas]
    root_speed.insert(0, root_speed[0] if root_speed else 0.0)
    smoothed = _smooth(root_speed, max(1, round(fps * 0.07)))
    in_place = _in_place_speeds(positions, descriptors, factor, fps)
    for descriptor, speed, local_speed in zip(descriptors, smoothed, in_place):
        descriptor["speed"] = max(speed, local_speed)
    return {
        "start": samples["start"],
        "fps": fps,
        "descriptors": descriptors,
        "root_ground": [
            (sample["pelvis"][0] / scale, sample["pelvis"][2] / scale) for sample in positions
        ],
        "gait": in_place,
        "positions": positions,
        "leg_length": scale,
        "floor": floor,
    }


def _pose_distance(descriptor, example, cues):
    """Measures how well one pose falls in a calibrated feature distribution.

    Args:
        descriptor (dict): Current frame measurements.
        example (dict): Stored measured pose example.
        cues (set or None): Enabled pose cues, or None for the built-in cue selection.

    Returns:
        float: Normalized distance, or infinity with insufficient shared features.
    """
    features = example["features"]
    if cues is not None:
        features = {name: values for name, values in features.items() if name in cues}
    overlap = descriptor.keys() & features.keys()
    minimum = 4 if cues is None else min(4, len(cues))
    if not overlap or len(overlap) < max(minimum, math.ceil(len(features) * 0.6)):
        return math.inf
    errors = {}
    for name in sorted(overlap):
        lower, middle, upper = features[name]
        value = descriptor[name]
        unit = FEATURE_SCALES[name]
        spread = min(unit, max(middle - lower, upper - middle))
        outside = max(lower - value, value - upper, 0.0)
        error = 0.20 * abs(value - middle) / (unit + spread) + 0.80 * outside / unit
        errors[name] = min(error, 4.0)
    distinctive_error = max((errors[name] for name in overlap & PRIMARY_POSE_CUES), default=0.0)
    average_error = math.sqrt(statistics.mean(error ** 2 for error in errors.values()))
    # Agreement on many ordinary measurements should not hide a key pose difference.
    return max(average_error, 0.75 * distinctive_error)


def match_pose(descriptor, poses, cues=None):
    """Chooses a calibrated label when one example is sufficiently distinct.

    Args:
        descriptor (dict): Per-frame pose cues.
        poses (dict): Validated labels with calibrated examples.
        cues (set, optional): Explicit pose cues selected for this calibration.

    Returns:
        str: Matching pose label or an empty string.
    """
    if cues is not None and not cues:
        return ""
    candidates = {}
    for label, examples in poses.items():
        for example in examples:
            distance = _pose_distance(descriptor, example, cues)
            if distance <= example.get("threshold", DEFAULT_RULES["pose_threshold"]):
                current = candidates.get(label, (math.inf, "", ""))
                candidates[label] = min(current, (distance, "", ""))
    return _best_pose(candidates, DEFAULT_RULES["pose_margin"])[0]


def _best_pose(candidates, margin):
    """Resolves one match from the competing labels at a frame.

    Args:
        candidates (dict): Best distance, suffix and state per matching label.
        margin (float): Required separation from the second-best label.

    Returns:
        tuple: Chosen label, suffix and state, or empty strings.
    """
    ranked = sorted((distance, label, suffix, state) for label, (distance, suffix, state) in candidates.items())
    if not ranked or (len(ranked) > 1 and ranked[1][0] - ranked[0][0] < margin):
        return "", "", ""
    return ranked[0][1:]


def _pose_matches(descriptors, poses, cues, rules, use_names, moving, allow_activity):
    """Finds matching pose spans with sufficient consecutive evidence per example.

    Args:
        descriptors (list): Per-frame measured features.
        poses (dict): Calibrated labels and their examples.
        cues (set or None): Enabled pose measurements.
        rules (dict): Resolved calibration rules.
        use_names (bool): Uses each label as its default range-name suffix.
        moving (list): Frames with confirmed locomotion.
        allow_activity (bool): Whether the schema supports the activity state.

    Returns:
        list: Matched label, suffix and assigned state per frame.
    """
    if not poses or cues is not None and not cues:
        return [("", "", "")] * len(descriptors)
    matches = [{} for _ in descriptors]
    for label, examples in poses.items():
        for example in examples:
            threshold = example.get("threshold", rules["pose_threshold"])
            minimum = example.get("minimum_frames", rules["pose_minimum_frames"])
            suffix = example.get("suffix", label if use_names else "")
            state = example.get("state", "") if allow_activity else ""
            distances = [
                math.inf if state == "activity" and active else _pose_distance(descriptor, example, cues)
                for descriptor, active in zip(descriptors, moving)
            ]
            for accepted, first, last in spans(distance <= threshold for distance in distances):
                if accepted and last - first + 1 >= minimum:
                    for index in range(first, last + 1):
                        candidate = distances[index], suffix, state
                        if label not in matches[index] or candidate[0] < matches[index][label][0]:
                            matches[index][label] = candidate
    return [_best_pose(candidates, rules["pose_margin"]) for candidates in matches]


def _state_for_speed(speed, locomotion, idle_max, walk_max, run_max, allow_idle):
    """Selects the closest available locomotion state for a measured speed.

    Args:
        speed (float): Normalized root or gait speed.
        locomotion (list): Permitted locomotion labels ordered by speed.
        idle_max (float): Maximum idle speed.
        walk_max (float): Maximum walk speed.
        run_max (float): Calibrated upper running speed or infinity.
        allow_idle (bool): Whether the schema accepts idle.

    Returns:
        str: Valid measured state or an empty string.
    """
    if speed <= idle_max:
        return "idle" if allow_idle else ""
    upper_speeds = {"walk": walk_max, "jog": min(walk_max * 1.25, run_max), "run": run_max}
    for state in locomotion:
        if speed <= upper_speeds.get(state, math.inf):
            return state
    return locomotion[-1] if locomotion else ""


def _stands(descriptor):
    """Identifies a clearly upright stance from available geometric cues.

    Args:
        descriptor (dict): Current measured pose.

    Returns:
        bool: Whether measurements support an upright stance.
    """
    return descriptor["pelvis_height"] >= DEFAULT_STANDING_CUES["pelvis_height"] and all(
        abs(descriptor.get(cue, 0.0)) <= DEFAULT_STANDING_CUES[cue]
        for cue in ("knee_flexion", "torso_pitch", "torso_roll")
    )


def _stable_labels(labels, minimum, fallback):
    """Suppresses short runs of labels while keeping the complete timeline.

    Args:
        labels (list): Label at each frame.
        minimum (int): Minimum stable run length.
        fallback (str): Value used for unsupported short runs.

    Returns:
        list: Stabilized labels.
    """
    runs = [(label, len(list(group))) for label, group in groupby(labels)]
    result = []
    for index, (label, length) in enumerate(runs):
        if length < minimum and len(runs) > 1:
            previous = runs[index - 1] if index else (fallback, 0)
            following = runs[index + 1] if index + 1 < len(runs) else (fallback, 0)
            label, support = max((previous, following), key=lambda run: run[1])
            if support < minimum:
                label = fallback
        result.extend([label] * length)
    return result


def _classify_motion(analysis, locomotion, idle_speed, walk_speed, run_speed, idle_label, rules):
    """Classifies stable motion bouts before allowing any transition markers.

    Args:
        analysis (dict): Frame descriptors, root travel, and repeated gait evidence.
        locomotion (list): Locomotion labels supported by the schema.
        idle_speed (float): Idle threshold in normalized units.
        walk_speed (float): Maximum walking speed.
        run_speed (float): Maximum running speed before sprint.
        idle_label (str): Idle label when the schema supports it.
        rules (dict): Resolved calibration rules.

    Returns:
        tuple: Motion labels and a mask of confirmed travel frames.
    """
    speeds = [sample["speed"] for sample in analysis["descriptors"]]
    moving = movement_mask(speeds, analysis.get("root_ground"), analysis.get("gait"), idle_speed, rules)
    states = [idle_label] * len(speeds)
    for active, first, last in spans(moving):
        if active and locomotion:
            labels = [
                _state_for_speed(speed, locomotion, idle_speed, walk_speed, run_speed, False)
                if speed > idle_speed else locomotion[0]
                for speed in speeds[first:last + 1]
            ]
            states[first:last + 1] = _stable_labels(labels, rules["minimum_range_frames"], locomotion[0])
    return states, moving


def generate_ranges(analysis, gaps, schema, profile, pose_field):
    """Builds schema-compatible annotation ranges for uncovered spans.

    Args:
        analysis (dict): Motion descriptors and frame rate.
        gaps (list): Inclusive frame pairs safe to annotate.
        schema (dict): Active annotation schema.
        profile (dict): Optional portable profile.
        pose_field (str): Schema field used for calibrated labels.

    Returns:
        list: New tracker ranges with state and available stance metadata.
    """
    fields = get_schema_fields(schema, "frame_range")
    state_field = fields.get("state")
    profile = profile or {}
    rules = dict(DEFAULT_RULES, **profile.get("rules", {}))
    thresholds = profile.get("locomotion", {})
    idle_speed = thresholds.get("idle_max_speed", DEFAULT_IDLE_SPEED)
    walk_speed = thresholds.get("walk_max_speed", DEFAULT_WALK_SPEED)
    run_speed = thresholds.get("run_max_speed", math.inf)
    locomotion = [state for state in ("walk", "run") if supports_value(state_field, state)]
    if not locomotion:
        locomotion = [state for state in LOCOMOTION_STATES if state != "sprint" and supports_value(state_field, state)]
    if math.isfinite(run_speed) and supports_value(state_field, "sprint"):
        locomotion.append("sprint")
    can_idle = supports_value(state_field, "idle")
    can_stand = supports_value(fields.get("stance"), "stand")
    allow_activity = supports_value(state_field, "activity")
    use_names = pose_field == RANGE_NAME_FIELD
    pose_field_definition = fields.get(pose_field)
    poses = {
        name: examples if use_names or supports_value(pose_field_definition, name) else [
            example for example in examples if allow_activity and example.get("state") == "activity"
        ]
        for name, examples in profile.get("poses", {}).items()
    }
    cues = set(profile["pose_cues"]) if "pose_cues" in profile else None
    descriptors = analysis["descriptors"]
    states, moving = _classify_motion(
        analysis, locomotion, idle_speed, walk_speed, run_speed, "idle" if can_idle else "", rules
    )
    calibrated = _pose_matches(descriptors, poses, cues, rules, use_names, moving, allow_activity)
    stances = _stable_labels(
        ["stand" if can_stand and _stands(sample) else "" for sample in descriptors], rules["minimum_range_frames"], ""
    )
    if pose_field == "stance":
        stances = [
            match[0] if supports_value(pose_field_definition, match[0]) else stance
            for match, stance in zip(calibrated, stances)
        ]

    start = analysis["start"]
    writable = [False] * len(descriptors)
    for first, last in gaps:
        writable[first - start:last - start + 1] = [True] * (last - first + 1)
    allowed = {label for label in ("enter", "exit") if supports_value(state_field, label)}
    for label, first, last in transition_markers(moving, rules, allowed, writable):
        width = last - first + 1
        stance = "stand" if stances[first:last + 1].count("stand") * 2 >= width else ""
        states[first:last + 1] = [label] * width
        stances[first:last + 1] = [stance] * width
        calibrated[first:last + 1] = [("", "", "")] * width

    ranges = []
    for first, last in gaps:
        group_start = first
        labels = zip(states[first - start:last - start + 1], stances[first - start:last - start + 1],
                     calibrated[first - start:last - start + 1])
        for (state, stance, (pose, suffix, trained_state)), group in groupby(labels):
            length = sum(1 for _ in group)
            data = {}
            state = trained_state or state
            if state:
                data["state"] = state
            if stance:
                data["stance"] = stance
            if pose and not use_names and supports_value(pose_field_definition, pose):
                data[pose_field] = pose
            if data or pose:
                name = (state or stance or pose) if use_names or suffix or trained_state else (pose or state or stance)
                suffix = suffix.strip("_ ")
                if suffix.casefold() == name.casefold():
                    suffix = ""
                ranges.append({
                    "name": f"{name}_{suffix}" if suffix else name,
                    "start": group_start,
                    "end": group_start + length - 1,
                    "custom_data": data,
                })
            group_start += length
    return ranges


def collect_examples(analysis, labeled_ranges, feature_names=None):
    """Builds portable examples from user-selected annotated ranges.

    Args:
        analysis (dict): Scene motion descriptors.
        labeled_ranges (list): Inclusive start, end, label and optional learned State tuples.
        feature_names (tuple, optional): Features to include in each example.

    Returns:
        dict: Available examples keyed by pose label.
    """
    examples = defaultdict(list)
    first = analysis["start"]
    for start, end, label, *state in labeled_ranges:
        samples = analysis["descriptors"][max(0, start - first):max(0, end - first + 1)]
        if samples:
            example = summarize_example(samples, feature_names)
            if state and state[0]:
                example["state"] = state[0]
            examples[label].append(example)
    return dict(examples)
