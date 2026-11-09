"""
Motion Evaluation Pose Checks - Calibration poses (T-pose or A-pose) left in a clip.

Position based, so it works on any skeleton with mapped arm roles. A frame
matches when both arms point sideways at the target height with straight
elbows, the trunk is upright, and the knees are straight. A match only counts
while the arms and head hold still for a minimum time, so motion that briefly
passes through a similar pose is not flagged.
"""

from .checks_base import CheckDefinition, CheckResult, ParameterSpec, MODE_BIPED, CHART_BELOW
from . import math_utils
import math

SIDES = ("left", "right")
POSE_TYPE_T = "t"
POSE_TYPE_A = "a"
POSE_TYPE_BOTH = "both"
POSE_TYPES = [POSE_TYPE_T, POSE_TYPE_A, POSE_TYPE_BOTH]
SEARCH_EDGES = "edges"
SEARCH_ANYWHERE = "anywhere"
SEARCH_MODES = [SEARCH_EDGES, SEARCH_ANYWHERE]
# Arm elevation (degrees above horizontal) of each pose type.
POSE_ELEVATIONS = {POSE_TYPE_T: [0.0], POSE_TYPE_A: [-45.0], POSE_TYPE_BOTH: [0.0, -45.0]}
ELBOW_TOLERANCE = 30.0
TRUNK_TOLERANCE = 25.0
KNEE_TOLERANCE = 30.0
UP_VECTOR = (0.0, 1.0, 0.0)
ARM_ROLES = [f"{side}_{part}" for side in SIDES for part in ("arm", "forearm", "hand")]
LEG_ROLES = [f"{side}_{part}" for side in SIDES for part in ("up_leg", "leg", "foot")]
STILL_ROLES = ["head"] + [f"{side}_{part}" for side in SIDES for part in ("forearm", "hand")]


def get_target_directions(lateral, side_sign, elevations):
    """Gets the arm directions of the calibration pose for one side.

    Args:
        lateral (tuple): Horizontal unit vector pointing to the character's left.
        side_sign (float): 1.0 for the left arm, -1.0 for the right arm.
        elevations (list): Arm elevations in degrees above horizontal.

    Returns:
        list: Unit target directions (shoulder to wrist).
    """
    directions = []
    for elevation in elevations:
        radians = math.radians(elevation)
        side_vector = math_utils.scale(lateral, side_sign * math.cos(radians))
        directions.append(math_utils.add(side_vector, (0.0, math.sin(radians), 0.0)))
    return directions


def get_bend(start, middle, end):
    """Measures the bend of a three-joint chain (0 = straight).

    Args:
        start (tuple): Upper joint position.
        middle (tuple): Middle joint position.
        end (tuple): Lower joint position.

    Returns:
        float: Bend in degrees.
    """
    return math_utils.angle_between(math_utils.subtract(middle, start), math_utils.subtract(end, middle))


def measure_pose_mismatch(data, index, elevations, arm_tolerance):
    """Measures how far one frame is from the calibration pose.

    Args:
        data (MotionData): Sampled motion.
        index (int): Frame index.
        elevations (list): Accepted arm elevations in degrees.
        arm_tolerance (float): Allowed arm direction error in degrees.

    Returns:
        float or None: Worst ratio of error to tolerance (1.0 or less matches), or None when unmeasurable.
    """

    def position(role_key):
        """Gets a role position on this frame.

        Args:
            role_key (str): Role key.

        Returns:
            tuple: Y-up position.
        """
        return data.get_role_positions(role_key)[index]

    lateral = math_utils.subtract(position("left_arm"), position("right_arm"))
    lateral = math_utils.normalize((lateral[0], 0.0, lateral[2]))
    if lateral is None:
        return None
    ratios = [
        math_utils.angle_between(math_utils.subtract(position("head"), position("hips")), UP_VECTOR) / TRUNK_TOLERANCE
    ]
    for side, side_sign in (("left", 1.0), ("right", -1.0)):
        shoulder, elbow, wrist = [position(f"{side}_{part}") for part in ("arm", "forearm", "hand")]
        arm_direction = math_utils.subtract(wrist, shoulder)
        targets = get_target_directions(lateral, side_sign, elevations)
        arm_error = min(math_utils.angle_between(arm_direction, target) for target in targets)
        ratios.append(arm_error / max(arm_tolerance, 1e-6))
        ratios.append(get_bend(shoulder, elbow, wrist) / ELBOW_TOLERANCE)
        knee_bend = get_bend(position(f"{side}_up_leg"), position(f"{side}_leg"), position(f"{side}_foot"))
        ratios.append(knee_bend / KNEE_TOLERANCE)
    return max(ratios)


def get_hold_speeds(data):
    """Gets the fastest movement of the arms and head relative to the hips.

    Args:
        data (MotionData): Sampled motion.

    Returns:
        list: Leg lengths per second, one per frame.
    """
    hips = data.get_role_positions("hips")
    reference = data.get_reference_length()
    speed_lists = []
    for role_key in STILL_ROLES:
        positions = data.get_role_positions(role_key)
        if not positions:
            continue
        relative = [math_utils.subtract(position, hip) for position, hip in zip(positions, hips)]
        speed_lists.append([speed / reference for speed in math_utils.speeds(relative, data.fps)])
    speeds = [max(values) for values in zip(*speed_lists)] if speed_lists else [0.0] * data.frame_count
    return math_utils.moving_average(speeds, max(3, int(round(data.fps * 0.2))))


def is_at_edge(span, frame_count, edge_frames):
    """Checks whether a frame span touches the start or end window of the clip.

    Args:
        span (list): Inclusive [start, end] indexes.
        frame_count (int): Number of frames.
        edge_frames (int): Frames in each edge window.

    Returns:
        bool: True when the span starts in the first window or ends in the last one.
    """
    return span[0] < edge_frames or span[1] >= frame_count - edge_frames


def describe_span(span, data):
    """Builds a readable line for a held pose span.

    Args:
        span (list): Inclusive [start, end] indexes.
        data (MotionData): Sampled motion.

    Returns:
        str: Description such as "Pose held 1.4 s at the start (frames 1-42).".
    """
    seconds = (span[1] - span[0] + 1) / max(data.fps, 1e-6)
    if span[0] == 0:
        location = " at the start"
    elif span[1] == data.frame_count - 1:
        location = " at the end"
    else:
        location = ""
    first_frame = span[0] + data.start_frame
    last_frame = span[1] + data.start_frame
    return f"Calibration pose held {seconds:.1f} s{location} (frames {first_frame}-{last_frame})."


def check_t_pose(data, parameters):
    """Flags calibration poses held at the clip edges (or anywhere).

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): pose_type, search, edge_seconds, min_hold_seconds, arm_tolerance, hold_speed.

    Returns:
        CheckResult: Findings.
    """
    result = CheckResult()
    elevations = POSE_ELEVATIONS.get(parameters["pose_type"], POSE_ELEVATIONS[POSE_TYPE_T])
    mismatches = [
        measure_pose_mismatch(data, index, elevations, parameters["arm_tolerance"])
        for index in range(data.frame_count)
    ]
    hold_speeds = get_hold_speeds(data)
    held = [
        mismatch is not None and mismatch <= 1.0 and speed <= parameters["hold_speed"]
        for mismatch, speed in zip(mismatches, hold_speeds)
    ]
    min_hold_frames = max(1, int(round(parameters["min_hold_seconds"] * data.fps)))
    edge_frames = max(1, int(round(parameters["edge_seconds"] * data.fps)))
    for span in math_utils.find_runs(held):
        if span[1] - span[0] + 1 < min_hold_frames:
            continue
        if parameters["search"] == SEARCH_EDGES and not is_at_edge(span, data.frame_count, edge_frames):
            continue
        result.flag_many(range(span[0], span[1] + 1), "pose")
        result.details.append(describe_span(span, data))
    result.add_series("pose difference", mismatches)
    result.set_chart("ratio of tolerance (1 or less = pose matches)", 1.0, "Match", direction=CHART_BELOW)
    return result


POSE_CHECKS = [
    CheckDefinition(
        key="t_pose",
        label="T-Pose",
        mode=MODE_BIPED,
        description=("Calibration T-pose (or A-pose) held at the start or end of the clip. "
                     "Off by default. Needs the arm roles."),
        function=check_t_pose,
        parameters=[
            ParameterSpec("pose_type", "Pose Type", POSE_TYPE_T,
                          tooltip=("Calibration pose to detect:\n"
                                   "t: arms out horizontally.\n"
                                   "a: arms out about 45 degrees down.\n"
                                   "both: either pose."),
                          choices=POSE_TYPES),
            ParameterSpec("search", "Search", SEARCH_EDGES,
                          tooltip=("Where a held pose counts:\n"
                                   "edges: only when it touches the first or last Edge Seconds of the clip.\n"
                                   "anywhere: any held pose in the clip."),
                          choices=SEARCH_MODES),
            ParameterSpec("edge_seconds", "Edge Seconds", 10.0, 0.0, 600.0,
                          "Length of the start and end windows used when Search is edges.", decimals=2),
            ParameterSpec("min_hold_seconds", "Min Hold", 0.5, 0.0, 60.0,
                          "Shortest time the pose must be held, in seconds. Ignores poses passed through quickly.",
                          decimals=2),
            ParameterSpec("arm_tolerance", "Arm Tolerance", 25.0, 1.0, 90.0,
                          "Allowed difference (degrees) between each arm and the calibration pose direction.",
                          decimals=1),
            ParameterSpec("hold_speed", "Hold Speed", 0.3, 0.0, 100.0,
                          "Arms and head moving slower than this (leg lengths per second, relative to the hips)\n"
                          "count as holding the pose."),
        ],
        required_roles=["hips", "head"] + LEG_ROLES + ARM_ROLES,
        enabled=False, weight=1.0, warn_below=90, fail_below=50, event_penalty=60.0, frame_penalty=0.0,
    ),
]
