"""
Motion Evaluation Joint Limit Checks - Biomechanically impossible elbow, knee, wrist, forearm, and head poses.

Joint axis conventions differ between skeletons, so no check reads rotation
values or assumes which local axis is a hinge. Instead each joint learns its
neutral pose from the clip itself, in the parent joint's own space:

- Hinges (elbows, knees) learn their bend axis from the frames where they are
  clearly bent, then measure backward bending and bending out of that plane.
- Wrists and twists measure how far the joint moves away from its median pose
  in the clip.

A joint that never bends enough to learn its hinge is reported and not measured.
"""

from .checks_base import CheckDefinition, CheckResult, ParameterSpec, MODE_BIPED
from . import math_utils
import math

SIDES = ("left", "right")
ARM_PARTS = ("arm", "forearm", "hand")
LEG_PARTS = ("up_leg", "leg", "foot")
LEG_ROLES = [f"{side}_{part}" for side in SIDES for part in LEG_PARTS]
# A hinge is learned from frames bent at least this much (degrees), where the bend plane is reliable.
HINGE_LEARN_MIN_BEND = 25.0
HINGE_LEARN_MIN_FRAMES = 5
# Mean length of the learned bend normals (1 = all identical). Lower means no consistent hinge axis.
HINGE_MIN_CONSISTENCY = 0.5
# Sideways bending is only measured past this bend (degrees). Near-straight limbs show the carrying
# angle and solver offsets as apparent side bend, and a straight joint has no reliable bend plane.
SIDE_BEND_MIN_BEND = 30.0


# ------------------------------------------------ Helpers ------------------------------------------------
def get_part_paths(data, side, parts):
    """Gets the node paths of a chain of side roles.

    Args:
        data (MotionData): Sampled motion.
        side (str): "left" or "right".
        parts (tuple): Role suffixes, for example ("arm", "forearm", "hand").

    Returns:
        list or None: Node paths in chain order, or None when a role is unavailable.
    """
    paths = [data.get_role_path(f"{side}_{part}") for part in parts]
    return None if None in paths else paths


def get_directions(start_positions, end_positions):
    """Gets unit directions between two position series.

    Args:
        start_positions (list): Start positions, one per frame.
        end_positions (list): End positions, one per frame.

    Returns:
        list: Unit vectors, or None on frames where the points overlap.
    """
    return [math_utils.normalize(math_utils.subtract(end, start)) for start, end in zip(start_positions, end_positions)]


def to_local_series(rotations, directions):
    """Expresses world directions in the space of a joint, frame by frame.

    Args:
        rotations (list): Joint rotation axes per frame (see MotionData.get_rotations).
        directions (list): World unit vectors per frame (None entries are kept).

    Returns:
        list: Local unit vectors, or None where the direction is missing.
    """
    return [
        math_utils.to_local(rotation, direction) if direction is not None else None
        for rotation, direction in zip(rotations, directions)
    ]


def flag_limit(result, values, threshold, min_run, offender):
    """Flags frames whose value reaches a limit and records the series.

    Args:
        result (CheckResult): Result to update.
        values (list): Measured value per frame (None = not measured).
        threshold (float): Limit; values at or above it are flagged.
        min_run (int): Consecutive frames needed.
        offender (str): Joint label, for example "left elbow".
    """
    flagged = [index for index, value in enumerate(values) if value is not None and value >= threshold]
    result.flag_many(math_utils.filter_minimum_run(flagged, min_run), offender)
    result.add_series(offender, values)


def get_missing_side_roles(data, parts):
    """Lists unavailable side roles of a chain.

    Args:
        data (MotionData): Sampled motion.
        parts (tuple): Role suffixes.

    Returns:
        list: Missing role keys for both sides.
    """
    return data.missing_roles([f"{side}_{part}" for side in SIDES for part in parts])


# ------------------------------------------------ Hinges ------------------------------------------------
def learn_hinge_axis(rotations, upper_directions, lower_directions):
    """Learns a hinge axis in the upper joint's space from clearly bent frames.

    Args:
        rotations (list): Upper joint rotation axes per frame.
        upper_directions (list): Upper bone unit directions per frame.
        lower_directions (list): Lower bone unit directions per frame.

    Returns:
        tuple or None: Local unit axis pointing along the normal bend (upper x lower),
            or None when the clip has too few consistent bent frames.
    """
    normals = []
    for rotation, upper, lower in zip(rotations, upper_directions, lower_directions):
        if upper is None or lower is None or math_utils.angle_between(upper, lower) < HINGE_LEARN_MIN_BEND:
            continue
        normal = math_utils.normalize(math_utils.cross(upper, lower))
        if normal is not None:
            normals.append(math_utils.to_local(rotation, normal))
    if len(normals) < HINGE_LEARN_MIN_FRAMES:
        return None
    total = (sum(normal[0] for normal in normals), sum(normal[1] for normal in normals),
             sum(normal[2] for normal in normals))
    if math_utils.length(total) / len(normals) < HINGE_MIN_CONSISTENCY:
        return None
    return math_utils.median_direction(normals)


def measure_hinge(data, side, parts):
    """Measures backward and sideways bending of a hinge joint (elbow or knee).

    Args:
        data (MotionData): Sampled motion.
        side (str): "left" or "right".
        parts (tuple): Upper, middle, and lower role suffixes.

    Returns:
        dict or None: {"learned": bool, "backward": list, "side": list} with degrees per frame
            (None where not measured; "side" only where the joint bends at least SIDE_BEND_MIN_BEND),
            or None when a role is unavailable.
    """
    cache_key = f"hinge_{side}_{parts[1]}"
    if cache_key in data.cache:
        return data.cache[cache_key]
    paths = get_part_paths(data, side, parts)
    measurement = None
    if paths:
        upper_positions, middle_positions, lower_positions = [data.get_positions(path) for path in paths]
        rotations = data.get_rotations(paths[0])
        upper_directions = get_directions(upper_positions, middle_positions)
        lower_directions = get_directions(middle_positions, lower_positions)
        hinge_local = learn_hinge_axis(rotations, upper_directions, lower_directions)
        backward = [None] * data.frame_count
        sideways = [None] * data.frame_count
        for index in range(min(data.frame_count, len(rotations)) if hinge_local else 0):
            upper = upper_directions[index]
            lower = lower_directions[index]
            if upper is None or lower is None:
                continue
            hinge = math_utils.to_world(rotations[index], hinge_local)
            along_upper = math_utils.scale(upper, math_utils.dot(hinge, upper))
            hinge = math_utils.normalize(math_utils.subtract(hinge, along_upper))
            if hinge is None:
                continue
            backward[index] = -math_utils.signed_angle(upper, lower, hinge)
            if math_utils.angle_between(upper, lower) >= SIDE_BEND_MIN_BEND:
                sideways[index] = abs(math.degrees(math.asin(max(-1.0, min(1.0, math_utils.dot(lower, hinge))))))
        measurement = {"learned": hinge_local is not None, "backward": backward, "side": sideways}
    data.cache[cache_key] = measurement
    return measurement


def run_hinge_check(data, parameters, parts, joint_name, measure_key):
    """Runs a hinge limit on both sides.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): angle_threshold, min_run.
        parts (tuple): Upper, middle, and lower role suffixes.
        joint_name (str): Readable joint name, for example "elbow".
        measure_key (str): "backward" or "side" (see measure_hinge).

    Returns:
        CheckResult: Findings, or a skipped result when neither side is mapped.
    """
    result = CheckResult()
    measured_sides = 0
    for side in SIDES:
        measurement = measure_hinge(data, side, parts)
        if measurement is None:
            continue
        measured_sides += 1
        offender = f"{side} {joint_name}"
        if not measurement["learned"]:
            result.details.append(f"{offender.capitalize()} never bends enough to learn its hinge axis (not measured).")
        flag_limit(result, measurement[measure_key], parameters["angle_threshold"], parameters["min_run"], offender)
    if not measured_sides:
        return CheckResult.skipped(f"Missing roles: {', '.join(get_missing_side_roles(data, parts))}")
    return result


def check_elbow_hyperextension(data, parameters):
    """Flags elbows bending backwards past their straight pose.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): angle_threshold, min_run.

    Returns:
        CheckResult: Findings.
    """
    result = run_hinge_check(data, parameters, ARM_PARTS, "elbow", "backward")
    result.set_chart("backward bend in degrees (negative = normal bend)", parameters["angle_threshold"], "Min Bend")
    return result


def check_elbow_side_bend(data, parameters):
    """Flags elbows bending sideways out of their hinge plane.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): angle_threshold, min_run.

    Returns:
        CheckResult: Findings.
    """
    result = run_hinge_check(data, parameters, ARM_PARTS, "elbow", "side")
    result.set_chart("degrees out of the bend plane", parameters["angle_threshold"], "Max Angle")
    return result


def check_knee_side_bend(data, parameters):
    """Flags knees bending sideways out of their hinge plane.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): angle_threshold, min_run.

    Returns:
        CheckResult: Findings.
    """
    result = run_hinge_check(data, parameters, LEG_PARTS, "knee", "side")
    result.set_chart("degrees out of the bend plane", parameters["angle_threshold"], "Max Angle")
    return result


# ------------------------------------------------ Swing and twist ------------------------------------------------
def measure_wrist_bend(data, side):
    """Measures how far a hand bends away from its median pose relative to the forearm.

    The forearm direction is expressed in the hand's space. Rolling the hand
    around the forearm does not change it, so only bending is measured.

    Args:
        data (MotionData): Sampled motion.
        side (str): "left" or "right".

    Returns:
        list or None: Degrees per frame, or None when a role is unavailable.
    """
    paths = get_part_paths(data, side, ("forearm", "hand"))
    if not paths:
        return None
    directions = get_directions(data.get_positions(paths[0]), data.get_positions(paths[1]))
    local_directions = to_local_series(data.get_rotations(paths[1]), directions)
    neutral = math_utils.median_direction(local_directions)
    values = [None] * data.frame_count
    if neutral is None:
        return values
    for index, direction in enumerate(local_directions[:data.frame_count]):
        if direction is not None:
            values[index] = math_utils.angle_between(direction, neutral)
    return values


def measure_twist(data, parent_path, parent_axis_paths, child_path, child_axis_paths):
    """Measures how far a child joint rolls around its bone relative to a parent, from the median roll.

    Each joint gets a reference vector perpendicular to its bone. The parent's
    reference is carried onto the child bone with the smallest rotation, so
    bending is ignored and only the roll between both references remains.

    Args:
        data (MotionData): Sampled motion.
        parent_path (str): Parent joint node path (for example the upper arm).
        parent_axis_paths (tuple): Start and end node paths of the parent bone.
        child_path (str): Child joint node path (for example the hand).
        child_axis_paths (tuple): Start and end node paths of the twist axis (child bone).

    Returns:
        list: Absolute twist away from the median roll, in degrees per frame (None = not measured).
    """
    parent_rotations = data.get_rotations(parent_path)
    child_rotations = data.get_rotations(child_path)
    parent_directions = get_directions(*[data.get_positions(path) for path in parent_axis_paths])
    child_directions = get_directions(*[data.get_positions(path) for path in child_axis_paths])
    parent_local = to_local_series(parent_rotations, parent_directions)
    child_local = to_local_series(child_rotations, child_directions)
    parent_neutral = math_utils.median_direction(parent_local)
    child_neutral = math_utils.median_direction(child_local)
    angles = [None] * data.frame_count
    if parent_neutral is None or child_neutral is None:
        return angles
    parent_reference = math_utils.perpendicular_vector(parent_neutral)
    child_reference = math_utils.perpendicular_vector(child_neutral)
    frame_count = min(data.frame_count, len(parent_rotations), len(child_rotations))
    for index in range(frame_count):
        if parent_local[index] is None or child_local[index] is None:
            continue
        parent_world = math_utils.to_world(
            parent_rotations[index], math_utils.rotate_from_to(parent_reference, parent_neutral, parent_local[index]))
        parent_world = math_utils.rotate_from_to(parent_world, parent_directions[index], child_directions[index])
        child_world = math_utils.to_world(
            child_rotations[index], math_utils.rotate_from_to(child_reference, child_neutral, child_local[index]))
        angles[index] = math_utils.signed_angle(parent_world, child_world, child_directions[index])
    center = math_utils.circular_median_degrees(angles)
    return [abs(math_utils.wrap_degrees(angle - center)) if angle is not None else None for angle in angles]


def check_wrist_bend(data, parameters):
    """Flags hands bending too far away from the forearm.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): angle_threshold, min_run.

    Returns:
        CheckResult: Findings.
    """
    result = CheckResult()
    for side in SIDES:
        values = measure_wrist_bend(data, side)
        if values is not None:
            flag_limit(result, values, parameters["angle_threshold"], parameters["min_run"], f"{side} wrist")
    if not result.series:
        return CheckResult.skipped(f"Missing roles: {', '.join(get_missing_side_roles(data, ('forearm', 'hand')))}")
    result.set_chart("degrees from the median wrist pose", parameters["angle_threshold"], "Max Angle")
    return result


def check_forearm_twist(data, parameters):
    """Flags hands rolled too far around the forearm relative to the upper arm.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): angle_threshold, min_run.

    Returns:
        CheckResult: Findings.
    """
    result = CheckResult()
    for side in SIDES:
        paths = get_part_paths(data, side, ARM_PARTS)
        if not paths:
            continue
        arm_path, forearm_path, hand_path = paths
        values = measure_twist(data, arm_path, (arm_path, forearm_path), hand_path, (forearm_path, hand_path))
        flag_limit(result, values, parameters["angle_threshold"], parameters["min_run"], f"{side} forearm")
    if not result.series:
        return CheckResult.skipped(f"Missing roles: {', '.join(get_missing_side_roles(data, ARM_PARTS))}")
    result.set_chart("degrees of roll from the median pose", parameters["angle_threshold"], "Max Angle")
    return result


def check_head_turn(data, parameters):
    """Flags heads turned too far relative to the chest.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): angle_threshold, min_run.

    Returns:
        CheckResult: Findings.
    """
    result = CheckResult()
    torso_path = data.get_role_path("chest") or data.get_role_path("spine")
    head_path = data.get_role_path("head")
    neck_path = data.get_role_path("neck")
    if neck_path:
        values = measure_twist(data, torso_path, (torso_path, neck_path), head_path, (neck_path, head_path))
    else:
        values = measure_twist(data, torso_path, (torso_path, head_path), head_path, (torso_path, head_path))
    if not data.has_role("chest"):
        result.details.append("No chest role: measured against the lowest spine joint, which includes spine twist.")
    flag_limit(result, values, parameters["angle_threshold"], parameters["min_run"], "head")
    result.set_chart("degrees of turn from the median pose", parameters["angle_threshold"], "Max Angle")
    return result


# ------------------------------------------------ Definitions ------------------------------------------------
def build_min_run_parameter():
    """Builds the shared Min Run parameter.

    Returns:
        ParameterSpec: Consecutive frames needed before a limit is flagged.
    """
    return ParameterSpec("min_run", "Min Run", 2, 1, 60, "Consecutive frames past the limit needed.")


LIMIT_CHECKS = [
    CheckDefinition(
        key="elbow_hyperextension",
        label="Elbow Hyperextension",
        mode=MODE_BIPED,
        description=("Elbows bending backwards. The bend direction is learned from the clip's bent frames, "
                     "so arms that never bend are not measured."),
        function=check_elbow_hyperextension,
        parameters=[
            ParameterSpec("angle_threshold", "Min Bend", 35.0, 0.0, 90.0,
                          "Backward bend (degrees) required before an elbow is flagged.", decimals=1),
            build_min_run_parameter(),
        ],
        weight=0.5, warn_below=90, fail_below=50, event_penalty=0.0, frame_penalty=2.0,
    ),
    CheckDefinition(
        key="elbow_side_bend",
        label="Elbow Side Bend",
        mode=MODE_BIPED,
        description=("Bent elbows leaving their hinge plane sideways (learned from the clip's bent frames). "
                     "Only measured while the elbow bends at least 30 degrees. Off by default: forearm roll "
                     "and the carrying angle reach 40-60 degrees in normal poses such as hands on hips."),
        function=check_elbow_side_bend,
        parameters=[
            ParameterSpec("angle_threshold", "Max Angle", 60.0, 0.0, 90.0,
                          "Angle (degrees) the forearm may leave the elbow's bend plane.", decimals=1),
            build_min_run_parameter(),
        ],
        enabled=False, weight=0.5, warn_below=90, fail_below=50, event_penalty=0.0, frame_penalty=2.0,
    ),
    CheckDefinition(
        key="knee_side_bend",
        label="Knee Side Bend",
        mode=MODE_BIPED,
        description=("Bent knees leaving their hinge plane sideways (learned from the clip's bent frames). "
                     "Only measured while the knee bends at least 30 degrees."),
        function=check_knee_side_bend,
        parameters=[
            ParameterSpec("angle_threshold", "Max Angle", 45.0, 0.0, 90.0,
                          "Angle (degrees) the shin may leave the knee's bend plane.\n"
                          "Seated knees reach about 35 degrees through shin rotation.", decimals=1),
            build_min_run_parameter(),
        ],
        required_roles=LEG_ROLES,
        weight=0.5, warn_below=90, fail_below=50, event_penalty=0.0, frame_penalty=2.0,
    ),
    CheckDefinition(
        key="wrist_bend",
        label="Wrist Bend",
        mode=MODE_BIPED,
        description="Hands bending too far from the forearm, measured from the clip's median wrist pose.",
        function=check_wrist_bend,
        parameters=[
            ParameterSpec("angle_threshold", "Max Angle", 110.0, 0.0, 180.0,
                          "Bend (degrees) away from the median wrist pose before a wrist is flagged.", decimals=1),
            build_min_run_parameter(),
        ],
        weight=0.5, warn_below=90, fail_below=50, event_penalty=0.0, frame_penalty=2.0,
    ),
    CheckDefinition(
        key="forearm_twist",
        label="Forearm Twist",
        mode=MODE_BIPED,
        description="Hands rolled too far around the forearm relative to the upper arm, from the median roll.",
        function=check_forearm_twist,
        parameters=[
            ParameterSpec("angle_threshold", "Max Angle", 140.0, 0.0, 180.0,
                          "Roll (degrees) away from the median forearm roll before it is flagged.", decimals=1),
            build_min_run_parameter(),
        ],
        weight=0.5, warn_below=90, fail_below=50, event_penalty=0.0, frame_penalty=2.0,
    ),
    CheckDefinition(
        key="head_turn",
        label="Head Turn",
        mode=MODE_BIPED,
        description="Heads turned too far relative to the chest, from the median head turn.",
        function=check_head_turn,
        parameters=[
            ParameterSpec("angle_threshold", "Max Angle", 100.0, 0.0, 180.0,
                          "Turn (degrees) away from the median head turn before it is flagged.", decimals=1),
            build_min_run_parameter(),
        ],
        required_roles=["spine", "head"],
        weight=0.5, warn_below=90, fail_below=50, event_penalty=0.0, frame_penalty=2.0,
    ),
]
