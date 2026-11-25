"""
Motion Evaluation General Checks - Checks that work on any animated transforms.

Distances are ratios of the reference length (see MotionData.get_reference_length)
and speeds are reference lengths per second, so the defaults work at any scale
and frame rate.
"""

from .checks_base import CheckDefinition, CheckResult, ParameterSpec, MODE_GENERAL
from .checks_base import CHART_BELOW, worst_per_frame
from . import math_utils


def check_jitter(data, parameters):
    """Flags high-frequency noise that deviates from a smooth local trajectory.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): half_window, residual_ratio, min_run.

    Returns:
        CheckResult: Findings.
    """
    result = CheckResult()
    reference = data.get_reference_length()
    limit = parameters["residual_ratio"] * reference
    ratios = []
    for node_path in data.node_paths:
        residuals = math_utils.jitter_residuals(data.get_positions(node_path), parameters["half_window"])
        flagged = [index for index, residual in enumerate(residuals) if residual > limit]
        result.flag_many(math_utils.filter_minimum_run(flagged, parameters["min_run"]), data.get_label(node_path))
        ratios.append([residual / reference for residual in residuals])
    result.add_series("worst node", worst_per_frame(data.frame_count, ratios))
    result.set_chart("ratio of reference length", parameters["residual_ratio"], "Noise Limit")
    return result


def find_pops(samples, measure, limit, jump_factor):
    """Finds isolated pops in a sampled series.

    Two pop shapes are detected:
        - Step: one jump that is much larger than the steps before and after (teleport and stay).
        - Spike: a frame far from both neighbors while the neighbors agree (out and back).

    Args:
        samples (list): Values per frame (positions or matrices).
        measure (callable): ``measure(sample_a, sample_b)`` returning a non-negative distance.
        limit (float): Minimum per-frame change counted as a pop.
        jump_factor (float): How much larger the pop must be than the surrounding change.

    Returns:
        set: Frame indexes containing pops.
    """
    count = len(samples)
    if count < 2:
        return set()
    steps = [0.0] + [measure(samples[index - 1], samples[index]) for index in range(1, count)]
    pops = set()
    for index in range(1, count):
        step = steps[index]
        if step <= limit:
            continue
        neighbors = []
        if index - 1 >= 1:
            neighbors.append(steps[index - 1])
        if index + 1 < count:
            neighbors.append(steps[index + 1])
        if not neighbors or step > jump_factor * max(neighbors):
            pops.add(index)
    for index in range(1, count - 1):
        step_in = steps[index]
        step_out = steps[index + 1]
        if step_in <= limit or step_out <= limit:
            continue
        across = measure(samples[index - 1], samples[index + 1])
        if min(step_in, step_out) > jump_factor * across:
            pops.add(index)
    return pops


def get_step_rates(samples, measure, fps):
    """Measures the change between consecutive samples as a per-second rate.

    Args:
        samples (list): Values per frame (positions or matrices).
        measure (callable): ``measure(sample_a, sample_b)`` returning a non-negative distance.
        fps (float): Frames per second.

    Returns:
        list: Rate per frame (0.0 on the first frame).
    """
    return [0.0] + [measure(samples[index - 1], samples[index]) * fps for index in range(1, len(samples))]


def check_position_pops(data, parameters):
    """Flags single-frame teleports and spikes that are much larger than the surrounding motion.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): pop_speed, jump_factor.

    Returns:
        CheckResult: Findings.
    """
    result = CheckResult()
    reference = data.get_reference_length()
    limit = parameters["pop_speed"] * reference / data.fps
    rates = []
    for node_path in data.node_paths:
        positions = data.get_positions(node_path)
        pops = find_pops(positions, math_utils.distance, limit, parameters["jump_factor"])
        result.flag_many(pops, data.get_label(node_path))
        rates.append([rate / reference for rate in get_step_rates(positions, math_utils.distance, data.fps)])
    result.add_series("fastest node", worst_per_frame(data.frame_count, rates))
    result.set_chart("reference lengths per second", parameters["pop_speed"], "Pop Speed")
    return result


def check_rotation_pops(data, parameters):
    """Flags orientation flips and snaps that are much larger than the surrounding rotation.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): max_angular_speed, jump_factor.

    Returns:
        CheckResult: Findings.
    """
    result = CheckResult()
    limit = parameters["max_angular_speed"] / data.fps
    rates = []
    for node_path in data.node_paths:
        matrices = data.get_matrices(node_path)
        pops = find_pops(matrices, math_utils.rotation_angle_between, limit, parameters["jump_factor"])
        result.flag_many(pops, data.get_label(node_path))
        rates.append(get_step_rates(matrices, math_utils.rotation_angle_between, data.fps))
    result.add_series("fastest node", worst_per_frame(data.frame_count, rates))
    result.set_chart("degrees per second", parameters["max_angular_speed"], "Angular Speed")
    return result


def check_excessive_speed(data, parameters):
    """Flags character travel speeds beyond a plausible sprint.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): max_speed, min_run.

    Returns:
        CheckResult: Findings.
    """
    result = CheckResult()
    reference = data.get_reference_length()
    limit = parameters["max_speed"] * reference
    for node_path in data.get_speed_nodes():
        speeds = math_utils.speeds(data.get_positions(node_path), data.fps)
        flagged = [index for index, speed in enumerate(speeds) if speed > limit]
        result.flag_many(math_utils.filter_minimum_run(flagged, parameters["min_run"]), data.get_label(node_path))
        result.add_series(data.get_label(node_path), [speed / reference for speed in speeds])
    result.set_chart("reference lengths per second", parameters["max_speed"], "Max Speed")
    return result


def check_frozen_motion(data, parameters):
    """Flags long stretches where every sampled node is perfectly still.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): min_seconds, position_tolerance_ratio, angle_tolerance.

    Returns:
        CheckResult: Findings.
    """
    result = CheckResult()
    if data.frame_count < 2 or not data.nodes:
        return result
    position_limit = parameters["position_tolerance_ratio"] * data.get_reference_length()
    still_flags = [False] * data.frame_count
    for index in range(1, data.frame_count):
        is_still = True
        for node_path in data.node_paths:
            positions = data.get_positions(node_path)
            matrices = data.get_matrices(node_path)
            if math_utils.distance(positions[index], positions[index - 1]) > position_limit:
                is_still = False
                break
            if math_utils.rotation_angle_between(matrices[index - 1], matrices[index]) > parameters["angle_tolerance"]:
                is_still = False
                break
        still_flags[index] = is_still
    reference = data.get_reference_length()
    movement = [0.0] * data.frame_count
    for node_path in data.node_paths:
        positions = data.get_positions(node_path)
        for index in range(1, data.frame_count):
            movement[index] = max(movement[index], math_utils.distance(positions[index], positions[index - 1]))
    result.add_series("most moving node", [None] + [value / reference for value in movement[1:]])
    result.set_chart("ratio of reference length per frame", parameters["position_tolerance_ratio"],
                     "Move Tolerance", direction=CHART_BELOW)
    minimum_frames = max(2, int(round(parameters["min_seconds"] * data.fps)))
    for start, end in math_utils.find_runs(still_flags):
        if end - start + 1 >= minimum_frames:
            result.flag_many(range(max(0, start - 1), end + 1))
    if result.flagged:
        result.details.append("Every sampled node is motionless for longer than the allowed time.")
    return result


def check_scale_changes(data, parameters):
    """Flags world scale that drifts from the first frame.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): tolerance.

    Returns:
        CheckResult: Findings.
    """
    result = CheckResult()
    changes = []
    for node_path in data.node_paths:
        matrices = data.get_matrices(node_path)
        if not matrices:
            continue
        base_scale = math_utils.matrix_scale(matrices[0])
        node_changes = []
        for index, matrix in enumerate(matrices):
            current_scale = math_utils.matrix_scale(matrix)
            change = max(
                abs(current_scale[axis_index] - base_scale[axis_index]) / max(abs(base_scale[axis_index]), 1e-6)
                for axis_index in range(3)
            )
            node_changes.append(change)
            if change > parameters["tolerance"]:
                result.flag(index, data.get_label(node_path))
        changes.append(node_changes)
    result.add_series("worst node", worst_per_frame(data.frame_count, changes))
    result.set_chart("relative scale change", parameters["tolerance"], "Tolerance")
    return result


def check_invalid_values(data, parameters):
    """Flags frames whose transforms contain NaN or infinite values.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): Unused.

    Returns:
        CheckResult: Findings.
    """
    result = CheckResult()
    invalid_counts = [0] * data.frame_count
    for node_path in data.node_paths:
        for index, matrix in enumerate(data.get_matrices(node_path)):
            if not math_utils.is_finite_sequence(matrix):
                result.flag(index, data.get_label(node_path))
                invalid_counts[index] += 1
    result.add_series("invalid nodes", invalid_counts)
    result.set_chart("nodes with NaN or infinite values", 0.5, "Any invalid node")
    return result


def check_below_ground(data, parameters):
    """Flags nodes that drop below a fixed ground height.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): ground_height, tolerance_ratio.

    Returns:
        CheckResult: Findings.
    """
    result = CheckResult()
    limit = parameters["ground_height"] - parameters["tolerance_ratio"] * data.get_reference_length()
    heights = []
    for node_path in data.node_paths:
        node_heights = []
        for index, position in enumerate(data.get_positions(node_path)):
            node_heights.append(position[1])
            if position[1] < limit:
                result.flag(index, data.get_label(node_path))
        heights.append(node_heights)
    result.add_series("lowest node", worst_per_frame(data.frame_count, heights, use_minimum=True))
    result.set_chart("height (scene units)", limit, "Ground - Tolerance", direction=CHART_BELOW)
    return result


def check_bone_length_changes(data, parameters):
    """Flags parent-child distances that stretch or shrink, ignoring top-level offsets.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): tolerance, min_offset_ratio.

    Returns:
        CheckResult: Findings.
    """
    result = CheckResult()
    minimum_offset = parameters["min_offset_ratio"] * data.get_reference_length()
    root_nodes = set(data.get_root_nodes())
    changes = []
    for node_path in data.node_paths:
        parent_path = data.get_parent(node_path)
        if not parent_path or parent_path in root_nodes:
            continue
        child_positions = data.get_positions(node_path)
        parent_positions = data.get_positions(parent_path)
        lengths = [
            math_utils.distance(child_positions[index], parent_positions[index]) for index in range(data.frame_count)
        ]
        rest_length = math_utils.median(lengths)
        if rest_length <= minimum_offset:
            continue
        label = f"{data.get_label(parent_path)} > {data.get_label(node_path)}"
        bone_changes = [abs(bone_length - rest_length) / rest_length for bone_length in lengths]
        for index, change in enumerate(bone_changes):
            if change > parameters["tolerance"]:
                result.flag(index, label)
        changes.append(bone_changes)
    result.add_series("worst bone", worst_per_frame(data.frame_count, changes))
    result.set_chart("relative length change", parameters["tolerance"], "Tolerance")
    return result


GENERAL_CHECKS = [
    CheckDefinition(
        key="jitter",
        label="Jitter",
        mode=MODE_GENERAL,
        description="High-frequency noise on any sampled node, measured against a smooth local fit.",
        function=check_jitter,
        parameters=[
            ParameterSpec("residual_ratio", "Noise Limit", 0.012, 0.0005, 1.0,
                          "Allowed deviation from the smooth trajectory, as a ratio of the reference length."),
            ParameterSpec("half_window", "Half Window", 2, 1, 10,
                          "Frames on each side used for the smooth fit. Larger values tolerate slower wobble less."),
            ParameterSpec("min_run", "Min Run", 3, 1, 60,
                          "Consecutive noisy frames needed. Filters single-frame impacts and direction changes."),
        ],
        weight=1.0, warn_below=85, fail_below=50, event_penalty=0.0, frame_penalty=2.0,
    ),
    CheckDefinition(
        key="position_pops",
        label="Position Pops",
        mode=MODE_GENERAL,
        description="Single-frame teleports that are much larger than the motion around them.",
        function=check_position_pops,
        parameters=[
            ParameterSpec("pop_speed", "Pop Speed", 7.5, 0.1, 1000.0,
                          "Minimum speed of the popping frame, in reference lengths per second."),
            ParameterSpec("jump_factor", "Jump Factor", 3.0, 1.0, 100.0,
                          "How many times larger than both neighboring frames the step must be."),
        ],
        weight=1.0, warn_below=90, fail_below=50, event_penalty=20.0, frame_penalty=0.0,
    ),
    CheckDefinition(
        key="rotation_pops",
        label="Rotation Pops",
        mode=MODE_GENERAL,
        description="Orientation flips or snaps that are much larger than the rotation around them.",
        function=check_rotation_pops,
        parameters=[
            ParameterSpec("max_angular_speed", "Angular Speed", 1440.0, 10.0, 100000.0,
                          "Minimum rotation speed of the popping frame, in degrees per second.", decimals=1),
            ParameterSpec("jump_factor", "Jump Factor", 3.0, 1.0, 100.0,
                          "How many times larger than both neighboring frames the rotation step must be."),
        ],
        weight=1.0, warn_below=90, fail_below=50, event_penalty=15.0, frame_penalty=0.0,
    ),
    CheckDefinition(
        key="excessive_speed",
        label="Excessive Speed",
        mode=MODE_GENERAL,
        description="Character travel faster than a plausible sprint (hips in biped mode, top nodes otherwise).",
        function=check_excessive_speed,
        parameters=[
            ParameterSpec("max_speed", "Max Speed", 12.0, 0.1, 1000.0,
                          "Highest allowed travel speed, in reference lengths per second."),
            ParameterSpec("min_run", "Min Run", 2, 1, 60, "Consecutive fast frames needed."),
        ],
        weight=1.0, warn_below=90, fail_below=50, event_penalty=10.0, frame_penalty=1.0,
    ),
    CheckDefinition(
        key="frozen_motion",
        label="Frozen Motion",
        mode=MODE_GENERAL,
        description="Stretches where every sampled node is perfectly still, often caused by missing data.",
        function=check_frozen_motion,
        parameters=[
            ParameterSpec("min_seconds", "Min Seconds", 1.0, 0.05, 600.0, "Shortest still stretch reported."),
            ParameterSpec("position_tolerance_ratio", "Move Tolerance", 0.00001, 0.0, 0.1,
                          "Movement per frame treated as still, as a ratio of the reference length.", decimals=6),
            ParameterSpec("angle_tolerance", "Angle Tolerance", 0.01, 0.0, 10.0,
                          "Rotation per frame treated as still, in degrees.", decimals=4),
        ],
        weight=0.5, warn_below=90, fail_below=0, event_penalty=0.0, frame_penalty=1.0,
    ),
    CheckDefinition(
        key="scale_changes",
        label="Scale Changes",
        mode=MODE_GENERAL,
        description="World scale that drifts away from the first frame.",
        function=check_scale_changes,
        parameters=[
            ParameterSpec("tolerance", "Tolerance", 0.01, 0.0, 10.0, "Allowed relative scale change (0.01 = 1%)."),
        ],
        weight=0.5, warn_below=90, fail_below=0, event_penalty=0.0, frame_penalty=2.0,
    ),
    CheckDefinition(
        key="invalid_values",
        label="Invalid Values",
        mode=MODE_GENERAL,
        description="NaN or infinite transform values.",
        function=check_invalid_values,
        weight=1.0, warn_below=100, fail_below=100, event_penalty=100.0, frame_penalty=0.0,
    ),
    CheckDefinition(
        key="bone_length_changes",
        label="Bone Stretch",
        mode=MODE_GENERAL,
        description="Parent-child distances that stretch or shrink over time (top-level offsets are ignored).",
        function=check_bone_length_changes,
        parameters=[
            ParameterSpec("tolerance", "Tolerance", 0.02, 0.0, 10.0, "Allowed relative length change (0.02 = 2%)."),
            ParameterSpec("min_offset_ratio", "Min Bone", 0.02, 0.0, 10.0,
                          "Ignore bones shorter than this ratio of the reference length."),
        ],
        weight=0.5, warn_below=90, fail_below=0, event_penalty=0.0, frame_penalty=2.0,
    ),
    CheckDefinition(
        key="below_ground",
        label="Below Ground",
        mode=MODE_GENERAL,
        description="Any sampled node below a fixed ground height. Off by default because props can go below zero.",
        function=check_below_ground,
        parameters=[
            ParameterSpec("ground_height", "Ground Height", 0.0, -1000000.0, 1000000.0,
                          "Ground height in scene units along the up axis."),
            ParameterSpec("tolerance_ratio", "Tolerance", 0.05, 0.0, 10.0,
                          "Allowed depth below the ground, as a ratio of the reference length."),
        ],
        enabled=False, weight=1.0, warn_below=90, fail_below=50, event_penalty=0.0, frame_penalty=2.0,
    ),
]
