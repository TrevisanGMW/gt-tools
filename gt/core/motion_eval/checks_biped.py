"""
Motion Evaluation Biped Checks - Contact, ground, balance, and body-proxy checks for bipeds.

Roles come from the skeleton template, so no skeleton names live here. Distances
are ratios of the measured leg length and speeds are leg lengths per second.
"""

from .checks_base import (
    CheckDefinition,
    CheckResult,
    ParameterSpec,
    MODE_BIPED,
    GRAVITY_METERS_PER_SECOND_SQUARED,
    CHART_BELOW,
    worst_per_frame,
)
from . import math_utils
import math

SIDES = ("left", "right")
LEG_ROLES = [f"{side}_{part}" for side in SIDES for part in ("up_leg", "leg", "foot")]
FIRM_CONTACT_NEIGHBORHOOD = 2
PLANTED_SWING_SPEED = 1.2
# Low height percentile used as each contact joint's floor. High enough that a brief sink
# below the ground does not become the floor itself, low enough for clips with long air time.
FLOOR_PERCENTILE = 0.1


# ------------------------------------------------ Contacts ------------------------------------------------
def get_contact_joint_paths(data, side):
    """Gets the joints used to detect ground contact for one foot.

    Args:
        data (MotionData): Sampled motion.
        side (str): "left" or "right".

    Returns:
        list: Available foot, toe, and heel node paths.
    """
    paths = []
    for part in ("foot", "toe", "heel"):
        path = data.get_role_path(f"{side}_{part}")
        if path:
            paths.append(path)
    return paths


def compute_contacts(data):
    """Estimates per-foot ground contact from the foot, toe, and heel joints.

    Grounding is height based: a joint close to its floor height (its low
    percentile height) is grounded regardless of speed, so sliding feet stay
    grounded and can be measured. The combined weight additionally fades out
    joints that move much faster than the character, which suits gait timing.

    Args:
        data (MotionData): Sampled motion.

    Returns:
        dict: Per side {
            "grounded": list (height-only weight of the lowest joint),
            "weights": list (height and speed weight),
            "best_joint": list (lowest joint path per frame),
            "joint_grounded": dict (path to height-only weights),
            "joints": list,
            "planted_heights": dict (path to typical grounded height),
        }
    """
    if "contacts" in data.cache:
        return data.cache["contacts"]
    reference = data.get_reference_length()
    height_end = float(data.settings.get("contact_height_ratio", 0.06)) * reference
    height_start = height_end / 6.0
    minimum_base_speed = float(data.settings.get("contact_min_base_speed", 0.5)) * reference
    character_speeds = data.get_character_speeds()
    contacts = {}
    for side in SIDES:
        joint_paths = get_contact_joint_paths(data, side)
        joint_positions = {path: data.get_positions(path) for path in joint_paths}
        floors = {
            path: math_utils.percentile([position[1] for position in positions], FLOOR_PERCENTILE)
            for path, positions in joint_positions.items()
        }
        joint_speeds = {path: math_utils.speeds(positions, data.fps) for path, positions in joint_positions.items()}
        joint_grounded = {path: [] for path in joint_paths}
        grounded, weights, best_joint = [], [], []
        for index in range(data.frame_count):
            base_speed = max(character_speeds[index], minimum_base_speed)
            speed_start = 0.25 * base_speed
            speed_end = 2.50 * base_speed
            best_grounded, best_weight = 0.0, 0.0
            best_path = joint_paths[0] if joint_paths else None
            for path in joint_paths:
                height = joint_positions[path][index][1] - floors[path]
                height_weight = 1.0 - math_utils.smoothstep(
                    (height - height_start) / max(1e-9, height_end - height_start)
                )
                speed_air = math_utils.smoothstep(
                    (joint_speeds[path][index] - speed_start) / max(1e-9, speed_end - speed_start)
                )
                joint_grounded[path].append(height_weight)
                if height_weight > best_grounded:
                    best_grounded, best_path = height_weight, path
                best_weight = max(best_weight, min(height_weight, 1.0 - speed_air))
            grounded.append(best_grounded)
            weights.append(best_weight)
            best_joint.append(best_path)
        planted_heights = {}
        for path in joint_paths:
            planted = [
                joint_positions[path][index][1]
                for index in range(data.frame_count)
                if joint_grounded[path][index] >= 0.5
            ]
            planted_heights[path] = math_utils.median(planted) if planted else floors[path]
        contacts[side] = {
            "grounded": grounded,
            "weights": weights,
            "best_joint": best_joint,
            "joint_grounded": joint_grounded,
            "joints": joint_paths,
            "planted_heights": planted_heights,
        }
    data.cache["contacts"] = contacts
    return contacts


def is_firmly_planted(weights, index, plant_weight):
    """Checks firm contact around a frame, excluding heel-strike and toe-off corners.

    Args:
        weights (list): Contact weights.
        index (int): Frame index.
        plant_weight (float): Minimum weight for firm contact.

    Returns:
        bool: True when every frame in the neighborhood is firmly planted.
    """
    for neighbor in range(index - FIRM_CONTACT_NEIGHBORHOOD, index + FIRM_CONTACT_NEIGHBORHOOD + 1):
        if neighbor < 0 or neighbor >= len(weights) or weights[neighbor] < plant_weight:
            return False
    return True


def get_airborne_flags(data, contact_limit=0.5):
    """Flags frames where neither foot touches the ground (height based).

    Args:
        data (MotionData): Sampled motion.
        contact_limit (float): Grounded weight treated as touching.

    Returns:
        list: True for airborne frames.
    """
    contacts = compute_contacts(data)
    return [
        all(contacts[side]["grounded"][index] < contact_limit for side in SIDES)
        for index in range(data.frame_count)
    ]


# ------------------------------------------------ Checks ------------------------------------------------
def get_planted_flags(data, side, plant_weight, swing_speed):
    """Flags frames where a foot is firmly planted.

    A planted frame has its lowest contact joint grounded across the
    neighborhood and moving slower than the swing speed, so swinging feet that
    pass close to the floor are excluded while slow slides stay measurable.

    Args:
        data (MotionData): Sampled motion.
        side (str): "left" or "right".
        plant_weight (float): Grounded weight required.
        swing_speed (float): Planar speed (leg lengths per second) above which the foot is swinging.

    Returns:
        list: True for planted frames.
    """
    contacts = compute_contacts(data)[side]
    swing_limit = swing_speed * data.get_reference_length()
    planar_speeds = {
        path: math_utils.speeds(data.get_positions(path), data.fps, planar=True) for path in contacts["joints"]
    }
    flags = []
    for index in range(data.frame_count):
        if not is_firmly_planted(contacts["grounded"], index, plant_weight):
            flags.append(False)
            continue
        path = contacts["best_joint"][index]
        window = range(index - FIRM_CONTACT_NEIGHBORHOOD, index + FIRM_CONTACT_NEIGHBORHOOD + 1)
        flags.append(all(planar_speeds[path][neighbor] <= swing_limit for neighbor in window))
    return flags


def check_foot_slide(data, parameters):
    """Flags planted feet that slide along the ground.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): slide_speed, swing_speed, plant_weight, min_run.

    Returns:
        CheckResult: Findings.
    """
    result = CheckResult()
    contacts = compute_contacts(data)
    reference = data.get_reference_length()
    limit = parameters["slide_speed"] * reference / data.fps
    for side in SIDES:
        planted = get_planted_flags(data, side, parameters["plant_weight"], parameters["swing_speed"])
        candidates = []
        slide_speeds = [None] * data.frame_count
        for index in range(1, data.frame_count):
            if not planted[index]:
                continue
            positions = data.get_positions(contacts[side]["best_joint"][index])
            step = math_utils.planar_distance(positions[index], positions[index - 1])
            slide_speeds[index] = step * data.fps / reference
            if step > limit:
                candidates.append(index)
        result.flag_many(math_utils.filter_minimum_run(candidates, parameters["min_run"]), f"{side} foot")
        result.add_series(f"{side} foot (planted)", slide_speeds)
    result.set_chart("leg lengths per second", parameters["slide_speed"], "Slide Speed")
    return result


def check_planted_foot_jitter(data, parameters):
    """Flags noise on feet while they are firmly planted.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): residual_ratio, half_window, plant_weight, min_run.

    Returns:
        CheckResult: Findings.
    """
    result = CheckResult()
    contacts = compute_contacts(data)
    reference = data.get_reference_length()
    limit = parameters["residual_ratio"] * reference
    for side in SIDES:
        side_contacts = contacts[side]
        planted = get_planted_flags(data, side, parameters["plant_weight"], PLANTED_SWING_SPEED)
        residuals_by_joint = {
            path: math_utils.jitter_residuals(data.get_positions(path), parameters["half_window"])
            for path in side_contacts["joints"]
        }
        planted_residuals = [
            residuals_by_joint[side_contacts["best_joint"][index]][index] if planted[index] else None
            for index in range(data.frame_count)
        ]
        flagged = [
            index for index, residual in enumerate(planted_residuals) if residual is not None and residual > limit
        ]
        result.flag_many(math_utils.filter_minimum_run(flagged, parameters["min_run"]), f"{side} foot")
        result.add_series(
            f"{side} foot (planted)",
            [None if residual is None else residual / reference for residual in planted_residuals],
        )
    result.set_chart("ratio of leg length", parameters["residual_ratio"], "Noise Limit")
    return result


def check_ground_penetration(data, parameters):
    """Flags feet sinking below the ground.

    Auto ground compares every contact joint to its typical planted height.
    Fixed ground compares the lowest contact joint to the configured ground height.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): tolerance_ratio.

    Returns:
        CheckResult: Findings.
    """
    result = CheckResult()
    contacts = compute_contacts(data)
    reference = data.get_reference_length()
    tolerance = parameters["tolerance_ratio"] * reference
    fixed_ground = str(data.settings.get("ground_mode", "auto")).lower() == "fixed"
    ground_height = float(data.settings.get("ground_height", 0.0))
    for side in SIDES:
        depths = []
        for path in contacts[side]["joints"]:
            base = ground_height if fixed_ground else contacts[side]["planted_heights"][path]
            limit = base - tolerance
            positions = data.get_positions(path)
            for index, position in enumerate(positions):
                if position[1] < limit:
                    result.flag(index, data.get_label(path))
            depths.append([(position[1] - base) / reference for position in positions])
        result.add_series(f"{side} foot", worst_per_frame(data.frame_count, depths, use_minimum=True))
    result.set_chart("height above ground, ratio of leg length", -parameters["tolerance_ratio"],
                     "- Tolerance", direction=CHART_BELOW)
    return result


def check_floating(data, parameters):
    """Flags airborne stretches longer than a plausible jump.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): max_air_seconds.

    Returns:
        CheckResult: Findings.
    """
    result = CheckResult()
    maximum_frames = max(1, int(round(parameters["max_air_seconds"] * data.fps)))
    for start, end in math_utils.find_runs(get_airborne_flags(data)):
        if end - start + 1 > maximum_frames:
            result.flag_many(range(start, end + 1), "both feet")
            result.details.append(f"Airborne for {(end - start + 1) / data.fps:.2f}s.")
    add_contact_series(result, data, "grounded")
    return result


def add_contact_series(result, data, weight_key):
    """Records both feet contact weights on a result.

    Args:
        result (CheckResult): Result receiving the series.
        data (MotionData): Sampled motion.
        weight_key (str): "grounded" (height only) or "weights" (height and speed).
    """
    contacts = compute_contacts(data)
    for side in SIDES:
        result.add_series(f"{side} foot contact", contacts[side][weight_key])
    result.set_chart("contact weight (1 = on the ground)", 0.5, "Contact", direction=CHART_BELOW)


def find_flicker_frames(weights, window_frames, minimum_crossings):
    """Finds frames where a contact toggles on and off too often.

    Args:
        weights (list): Contact weights.
        window_frames (int): Sliding window length.
        minimum_crossings (int): Crossings inside the window that count as flicker.

    Returns:
        set: Flagged frame indexes.
    """
    crossings = [
        index for index in range(1, len(weights)) if (weights[index] >= 0.5) != (weights[index - 1] >= 0.5)
    ]
    flagged = set()
    for position, crossing in enumerate(crossings):
        inside = [other for other in crossings[position:] if other <= crossing + window_frames]
        if len(inside) >= minimum_crossings:
            flagged.update(range(inside[0], inside[-1] + 1))
    return flagged


def check_contact_flicker(data, parameters):
    """Flags foot contacts that toggle rapidly, usually a hovering or noisy foot.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): window_seconds, crossings.

    Returns:
        CheckResult: Findings.
    """
    result = CheckResult()
    contacts = compute_contacts(data)
    window_frames = max(2, int(round(parameters["window_seconds"] * data.fps)))
    for side in SIDES:
        flagged = find_flicker_frames(contacts[side]["weights"], window_frames, parameters["crossings"])
        result.flag_many(flagged, f"{side} foot")
    add_contact_series(result, data, "weights")
    return result


def get_character_forward_axes(data):
    """Gets a planar forward axis per frame from the hip width, oriented by the feet.

    The axis is perpendicular to the line between the thighs, so it does not
    depend on foot pitch. Its sign is chosen so it agrees with the toes (or,
    without toes, with the usual forward knee bend) across the clip.

    Args:
        data (MotionData): Sampled motion.

    Returns:
        list: Unit (x, 0, z) forward vectors, one per frame.
    """
    if "forward_axes" in data.cache:
        return data.cache["forward_axes"]
    left_hips = data.get_role_positions("left_up_leg")
    right_hips = data.get_role_positions("right_up_leg")
    axes = []
    for index in range(data.frame_count):
        lateral = math_utils.subtract(right_hips[index], left_hips[index])
        forward = (lateral[2], 0.0, -lateral[0])
        forward_length = math_utils.length(forward)
        axes.append(math_utils.scale(forward, 1.0 / forward_length) if forward_length > 1e-9 else (0.0, 0.0, 1.0))
    vote = 0.0
    for side in SIDES:
        ankles = data.get_role_positions(f"{side}_foot")
        toes = data.get_role_positions(f"{side}_toe")
        knees = data.get_role_positions(f"{side}_leg")
        for index in range(data.frame_count):
            if toes:
                foot = math_utils.subtract(toes[index], ankles[index])
                vote += math_utils.dot((foot[0], 0.0, foot[2]), axes[index])
            else:
                knee = math_utils.subtract(knees[index], ankles[index])
                vote += math_utils.dot((knee[0], 0.0, knee[2]), axes[index])
    if vote < 0.0:
        axes = [math_utils.scale(axis, -1.0) for axis in axes]
    data.cache["forward_axes"] = axes
    return axes


def check_knee_hyperextension(data, parameters):
    """Flags knees bending backwards relative to the character's forward direction.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): angle_threshold.

    Returns:
        CheckResult: Findings.
    """
    result = CheckResult()
    forward_axes = get_character_forward_axes(data)
    for side in SIDES:
        hips = data.get_role_positions(f"{side}_up_leg")
        knees = data.get_role_positions(f"{side}_leg")
        ankles = data.get_role_positions(f"{side}_foot")
        backward_bends = [None] * data.frame_count
        for index in range(data.frame_count):
            thigh = math_utils.subtract(hips[index], knees[index])
            shin = math_utils.subtract(ankles[index], knees[index])
            thigh_length = math_utils.length(thigh)
            shin_length = math_utils.length(shin)
            if thigh_length <= 1e-9 or shin_length <= 1e-9:
                continue
            cosine = max(-1.0, min(1.0, math_utils.dot(thigh, shin) / (thigh_length * shin_length)))
            bend = 180.0 - math.degrees(math.acos(cosine))
            hip_to_ankle = math_utils.subtract(ankles[index], hips[index])
            line_length_squared = max(math_utils.dot(hip_to_ankle, hip_to_ankle), 1e-12)
            projection = math_utils.dot(math_utils.subtract(knees[index], hips[index]), hip_to_ankle)
            closest = math_utils.add(hips[index], math_utils.scale(hip_to_ankle, projection / line_length_squared))
            knee_offset = math_utils.subtract(knees[index], closest)
            is_backward = math_utils.dot(knee_offset, forward_axes[index]) < 0.0
            backward_bends[index] = bend if is_backward else -bend
            if is_backward and bend >= parameters["angle_threshold"]:
                result.flag(index, f"{side} knee")
        result.add_series(f"{side} knee", backward_bends)
    result.set_chart("backward bend in degrees (negative = normal forward bend)",
                     parameters["angle_threshold"], "Min Bend")
    return result


def get_torso_segment(data, index):
    """Gets the torso proxy segment for a frame.

    Args:
        data (MotionData): Sampled motion.
        index (int): Frame index.

    Returns:
        tuple: (bottom, top) points.
    """
    top_role = "neck" if data.has_role("neck") else "chest" if data.has_role("chest") else "spine"
    return data.get_role_positions("hips")[index], data.get_role_positions(top_role)[index]


def build_limb_segments(data):
    """Builds the capsule segments available for intersection tests.

    Args:
        data (MotionData): Sampled motion.

    Returns:
        dict: Segment name to (start_role, end_role) for available roles.
    """
    segments = {}
    for side in SIDES:
        candidates = {
            f"{side} thigh": (f"{side}_up_leg", f"{side}_leg"),
            f"{side} shin": (f"{side}_leg", f"{side}_foot"),
            f"{side} foot": (f"{side}_foot", f"{side}_toe"),
            f"{side} forearm": (f"{side}_forearm", f"{side}_hand"),
            f"{side} upper arm": (f"{side}_arm", f"{side}_forearm"),
        }
        for name, roles in candidates.items():
            if data.has_role(roles[0]) and data.has_role(roles[1]):
                segments[name] = roles
    return segments


def check_limb_intersection(data, parameters):
    """Flags limbs passing through each other or through the torso using capsule proxies.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): torso_radius_ratio, leg_radius_ratio, arm_radius_ratio, depth_ratio, min_run.

    Returns:
        CheckResult: Findings.
    """
    result = CheckResult()
    reference = data.get_reference_length()
    segments = build_limb_segments(data)
    radius_by_type = {
        "thigh": parameters["leg_radius_ratio"] * reference,
        "shin": parameters["leg_radius_ratio"] * reference * 0.8,
        "foot": parameters["leg_radius_ratio"] * reference * 0.6,
        "forearm": parameters["arm_radius_ratio"] * reference,
        "upper arm": parameters["arm_radius_ratio"] * reference,
    }
    torso_radius = parameters["torso_radius_ratio"] * reference
    pairs = []
    for limb in ("thigh", "shin", "foot"):
        for other in ("thigh", "shin", "foot"):
            pair = (f"left {limb}", f"right {other}")
            if pair[0] in segments and pair[1] in segments:
                pairs.append(pair)
    for side in SIDES:
        for limb in ("forearm",):
            if f"{side} {limb}" in segments:
                pairs.append((f"{side} {limb}", "torso"))
    if not pairs:
        return CheckResult.skipped("Needs leg or arm roles on both sides.")
    gap_ratios = []
    for first, second in pairs:
        flagged = []
        first_radius = radius_by_type[first.split(" ", 1)[1]]
        second_radius = torso_radius if second == "torso" else radius_by_type[second.split(" ", 1)[1]]
        limit = (first_radius + second_radius) * (1.0 - parameters["depth_ratio"])
        first_start = data.get_role_positions(segments[first][0])
        first_end = data.get_role_positions(segments[first][1])
        if second != "torso":
            second_start = data.get_role_positions(segments[second][0])
            second_end = data.get_role_positions(segments[second][1])
        pair_ratios = []
        for index in range(data.frame_count):
            if second == "torso":
                bottom, top = get_torso_segment(data, index)
            else:
                bottom, top = second_start[index], second_end[index]
            gap = math_utils.segment_segment_distance(first_start[index], first_end[index], bottom, top)
            pair_ratios.append(gap / max(limit, 1e-9))
            if gap < limit:
                flagged.append(index)
        result.flag_many(math_utils.filter_minimum_run(flagged, parameters["min_run"]), f"{first} / {second}")
        gap_ratios.append(pair_ratios)
    result.add_series("closest limb pair", worst_per_frame(data.frame_count, gap_ratios, use_minimum=True))
    result.set_chart("gap / allowed gap (below 1 = intersecting)", 1.0, "Allowed Gap", direction=CHART_BELOW)
    return result


def convex_hull(points):
    """Computes the 2D convex hull of points with the monotone chain algorithm.

    Args:
        points (list): (x, z) points.

    Returns:
        list: Hull points in counter-clockwise order.
    """
    points = sorted(set(points))
    if len(points) <= 2:
        return points

    def cross(origin, point_a, point_b):
        """Computes the 2D cross product of OA and OB.

        Args:
            origin (tuple): Origin point.
            point_a (tuple): First point.
            point_b (tuple): Second point.

        Returns:
            float: Cross product.
        """
        return (point_a[0] - origin[0]) * (point_b[1] - origin[1]) - (point_a[1] - origin[1]) * (point_b[0] - origin[0])

    lower = []
    for point in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper = []
    for point in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]


def distance_to_support(point, support_points):
    """Measures how far a 2D point lies outside the support polygon.

    Args:
        point (tuple): (x, z) point.
        support_points (list): (x, z) support points.

    Returns:
        float: Distance outside the polygon, 0.0 when inside.
    """
    hull = convex_hull(support_points)
    point_3d = (point[0], 0.0, point[1])
    if len(hull) == 1:
        return math_utils.distance(point_3d, (hull[0][0], 0.0, hull[0][1]))
    edges = [(hull[index], hull[(index + 1) % len(hull)]) for index in range(len(hull))]
    if len(hull) >= 3:
        inside = all(
            (end[0] - start[0]) * (point[1] - start[1]) - (end[1] - start[1]) * (point[0] - start[0]) >= 0
            for start, end in edges
        )
        if inside:
            return 0.0
    return min(
        math_utils.point_segment_distance(point_3d, (start[0], 0.0, start[1]), (end[0], 0.0, end[1]))
        for start, end in edges
    )


def get_center_of_mass(data, index):
    """Approximates the center of mass from the hips, upper body, and head.

    Args:
        data (MotionData): Sampled motion.
        index (int): Frame index.

    Returns:
        tuple: Approximate center of mass.
    """
    weighted_roles = [("hips", 0.5), ("chest", 0.2), ("spine", 0.15), ("head", 0.15)]
    total_weight = 0.0
    center = (0.0, 0.0, 0.0)
    for role_key, weight in weighted_roles:
        positions = data.get_role_positions(role_key)
        if positions:
            center = math_utils.add(center, math_utils.scale(positions[index], weight))
            total_weight += weight
    return math_utils.scale(center, 1.0 / max(total_weight, 1e-9))


def check_balance(data, parameters):
    """Flags slow, grounded poses whose center of mass stays outside the feet support.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): margin_ratio, min_seconds, max_character_speed.

    Returns:
        CheckResult: Findings.
    """
    result = CheckResult()
    contacts = compute_contacts(data)
    reference = data.get_reference_length()
    margin = parameters["margin_ratio"] * reference
    speed_limit = parameters["max_character_speed"] * reference
    character_speeds = data.get_character_speeds()
    unbalanced = [False] * data.frame_count
    outside_ratios = [None] * data.frame_count
    for index in range(data.frame_count):
        if character_speeds[index] > speed_limit:
            continue
        support = []
        for side in SIDES:
            for path in contacts[side]["joints"]:
                if contacts[side]["joint_grounded"][path][index] < 0.5:
                    continue
                position = data.get_positions(path)[index]
                support.append((position[0], position[2]))
        if not support:
            continue
        center = get_center_of_mass(data, index)
        outside = distance_to_support((center[0], center[2]), support)
        outside_ratios[index] = outside / reference
        unbalanced[index] = outside > margin
    minimum_frames = max(1, int(round(parameters["min_seconds"] * data.fps)))
    for start, end in math_utils.find_runs(unbalanced):
        if end - start + 1 >= minimum_frames:
            result.flag_many(range(start, end + 1), "center of mass")
    result.add_series("center of mass outside support", outside_ratios)
    result.set_chart("distance outside the feet, ratio of leg length", parameters["margin_ratio"], "Margin")
    return result


def check_airborne_gravity(data, parameters):
    """Flags jumps whose vertical hips motion does not follow gravity.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): min_air_frames, tolerance.

    Returns:
        CheckResult: Findings.
    """
    result = CheckResult()
    hips = data.get_role_positions("hips")
    gravity = data.get_meters_to_units(GRAVITY_METERS_PER_SECOND_SQUARED)
    airborne = get_airborne_flags(data, contact_limit=0.2)
    for start, end in math_utils.find_runs(airborne):
        if end - start + 1 < parameters["min_air_frames"]:
            continue
        heights = [hips[index][1] for index in range(start, end + 1)]
        acceleration = math_utils.fit_parabola(heights, 1.0 / data.fps)
        if acceleration is None:
            continue
        if abs(acceleration + gravity) > parameters["tolerance"] * gravity:
            result.flag_many(range(start, end + 1), "hips")
            result.details.append(
                f"Jump at frames {start + data.start_frame}-{end + data.start_frame}: vertical acceleration "
                f"{acceleration * data.meters_per_unit:.2f} m/s2 (gravity is -9.81)."
            )
    reference = data.get_reference_length()
    floor = min(position[1] for position in hips) if hips else 0.0
    result.add_series("hips height", [(position[1] - floor) / reference for position in hips])
    result.add_series("airborne", [1.0 if flag else 0.0 for flag in airborne])
    result.set_chart("hips height above its lowest point, ratio of leg length (airborne = 1)")
    return result


def check_gait_asymmetry(data, parameters):
    """Flags locomotion where one foot stays planted much longer than the other.

    Args:
        data (MotionData): Sampled motion.
        parameters (dict): min_speed, asymmetry_ratio.

    Returns:
        CheckResult: Findings.
    """
    result = CheckResult()
    contacts = compute_contacts(data)
    speed_limit = parameters["min_speed"] * data.get_reference_length()
    moving = [speed > speed_limit for speed in data.get_character_speeds()]
    minimum_frames = max(2, int(round(data.fps)))
    for start, end in math_utils.find_runs(moving):
        if end - start + 1 < minimum_frames:
            continue
        durations = {}
        for side in SIDES:
            flags = [contacts[side]["weights"][index] >= 0.5 for index in range(start, end + 1)]
            runs = math_utils.find_runs(flags)
            durations[side] = [run_end - run_start + 1 for run_start, run_end in runs]
        if not durations["left"] or not durations["right"]:
            continue
        left_mean = sum(durations["left"]) / len(durations["left"])
        right_mean = sum(durations["right"]) / len(durations["right"])
        asymmetry = abs(left_mean - right_mean) / max(left_mean, right_mean)
        if asymmetry > parameters["asymmetry_ratio"]:
            result.flag_many(range(start, end + 1), "gait")
            result.details.append(f"Stance time differs by {asymmetry * 100:.0f}% between feet.")
    add_contact_series(result, data, "weights")
    return result


BIPED_CHECKS = [
    CheckDefinition(
        key="foot_slide",
        label="Foot Sliding",
        mode=MODE_BIPED,
        description="Planted feet sliding along the ground (foot skating).",
        function=check_foot_slide,
        parameters=[
            ParameterSpec("slide_speed", "Slide Speed", 0.3, 0.01, 100.0,
                          "Ground speed of a planted foot treated as sliding, in leg lengths per second."),
            ParameterSpec("swing_speed", "Swing Speed", 1.2, 0.05, 100.0,
                          "Feet faster than this (leg lengths per second) are swinging, not sliding."),
            ParameterSpec("plant_weight", "Plant Weight", 0.9, 0.1, 1.0,
                          "Height-based grounded weight (0-1) required around a frame to count as planted."),
            ParameterSpec("min_run", "Min Run", 3, 1, 60, "Consecutive sliding frames needed."),
        ],
        required_roles=LEG_ROLES,
        weight=1.0, warn_below=85, fail_below=50, event_penalty=0.0, frame_penalty=2.0,
    ),
    CheckDefinition(
        key="planted_foot_jitter",
        label="Planted Foot Jitter",
        mode=MODE_BIPED,
        description="Noise on feet while they are firmly planted, where any movement is visible.",
        function=check_planted_foot_jitter,
        parameters=[
            ParameterSpec("residual_ratio", "Noise Limit", 0.006, 0.0005, 1.0,
                          "Allowed deviation from the smooth trajectory, as a ratio of the leg length."),
            ParameterSpec("half_window", "Half Window", 2, 1, 10, "Frames on each side used for the smooth fit."),
            ParameterSpec("plant_weight", "Plant Weight", 0.9, 0.1, 1.0, "Contact weight treated as planted."),
            ParameterSpec("min_run", "Min Run", 3, 1, 60, "Consecutive noisy frames needed."),
        ],
        required_roles=LEG_ROLES,
        weight=0.5, warn_below=85, fail_below=0, event_penalty=0.0, frame_penalty=2.0,
    ),
    CheckDefinition(
        key="ground_penetration",
        label="Ground Penetration",
        mode=MODE_BIPED,
        description="Feet sinking below the ground (auto-detected or fixed, see Global settings).",
        function=check_ground_penetration,
        parameters=[
            ParameterSpec("tolerance_ratio", "Tolerance", 0.05, 0.0, 10.0,
                          "Allowed depth below the ground, as a ratio of the leg length."),
        ],
        required_roles=LEG_ROLES,
        weight=1.0, warn_below=85, fail_below=50, event_penalty=0.0, frame_penalty=2.0,
    ),
    CheckDefinition(
        key="floating",
        label="Floating",
        mode=MODE_BIPED,
        description="Both feet off the ground for longer than a plausible jump.",
        function=check_floating,
        parameters=[
            ParameterSpec("max_air_seconds", "Max Air Time", 0.9, 0.05, 60.0,
                          "Longest allowed airborne stretch, in seconds."),
        ],
        required_roles=LEG_ROLES,
        weight=1.0, warn_below=90, fail_below=50, event_penalty=10.0, frame_penalty=1.0,
    ),
    CheckDefinition(
        key="contact_flicker",
        label="Contact Flicker",
        mode=MODE_BIPED,
        description="Foot contact toggling on and off quickly, usually a hovering or noisy foot.",
        function=check_contact_flicker,
        parameters=[
            ParameterSpec("window_seconds", "Window", 0.4, 0.05, 10.0, "Sliding window length, in seconds."),
            ParameterSpec("crossings", "Crossings", 3, 2, 50,
                          "Contact changes inside the window that count as flicker."),
        ],
        required_roles=LEG_ROLES,
        weight=0.5, warn_below=90, fail_below=0, event_penalty=5.0, frame_penalty=0.5,
    ),
    CheckDefinition(
        key="knee_hyperextension",
        label="Knee Hyperextension",
        mode=MODE_BIPED,
        description="Knees bending backwards relative to the character's forward direction.",
        function=check_knee_hyperextension,
        parameters=[
            ParameterSpec("angle_threshold", "Min Bend", 5.0, 0.0, 90.0,
                          "Backward bend (degrees) required before a knee is flagged.", decimals=1),
        ],
        required_roles=LEG_ROLES,
        weight=0.5, warn_below=90, fail_below=50, event_penalty=0.0, frame_penalty=2.0,
    ),
    CheckDefinition(
        key="limb_intersection",
        label="Limb Intersection",
        mode=MODE_BIPED,
        description="Legs passing through each other and forearms passing through the torso (capsule proxies).",
        function=check_limb_intersection,
        parameters=[
            ParameterSpec("torso_radius_ratio", "Torso Radius", 0.14, 0.0, 2.0,
                          "Torso capsule radius, as a ratio of the leg length."),
            ParameterSpec("leg_radius_ratio", "Leg Radius", 0.07, 0.0, 2.0,
                          "Thigh capsule radius (shin and foot are slightly thinner)."),
            ParameterSpec("arm_radius_ratio", "Arm Radius", 0.045, 0.0, 2.0, "Arm capsule radius."),
            ParameterSpec("depth_ratio", "Depth", 0.5, 0.0, 0.99,
                          "Overlap fraction of the combined radii needed. Higher values allow more contact."),
            ParameterSpec("min_run", "Min Run", 2, 1, 60, "Consecutive intersecting frames needed."),
        ],
        required_roles=["hips", "spine"],
        weight=1.0, warn_below=85, fail_below=50, event_penalty=5.0, frame_penalty=1.5,
    ),
    CheckDefinition(
        key="balance",
        label="Balance",
        mode=MODE_BIPED,
        description=("Slow, grounded poses whose center of mass stays outside the feet support. "
                     "Off by default: sitting or leaning on props is support the skeleton cannot see."),
        function=check_balance,
        parameters=[
            ParameterSpec("margin_ratio", "Margin", 0.2, 0.0, 10.0,
                          "Allowed distance outside the support area, as a ratio of the leg length."),
            ParameterSpec("min_seconds", "Min Seconds", 0.5, 0.0, 60.0, "Shortest unbalanced stretch reported."),
            ParameterSpec("max_character_speed", "Max Speed", 0.5, 0.0, 100.0,
                          "Only check while the character moves slower than this (leg lengths per second)."),
        ],
        required_roles=LEG_ROLES + ["hips"],
        enabled=False, weight=0.5, warn_below=90, fail_below=0, event_penalty=0.0, frame_penalty=1.0,
    ),
    CheckDefinition(
        key="airborne_gravity",
        label="Airborne Gravity",
        mode=MODE_BIPED,
        description="Jumps whose vertical hips motion does not follow gravity (needs correct scene units).",
        function=check_airborne_gravity,
        parameters=[
            ParameterSpec("min_air_frames", "Min Air Frames", 5, 3, 600, "Shortest airborne stretch evaluated."),
            ParameterSpec("tolerance", "Tolerance", 0.4, 0.0, 10.0,
                          "Allowed difference from gravity, as a fraction of gravity."),
        ],
        required_roles=LEG_ROLES + ["hips"],
        weight=0.5, warn_below=90, fail_below=0, event_penalty=10.0, frame_penalty=0.0,
    ),
    CheckDefinition(
        key="gait_asymmetry",
        label="Gait Asymmetry",
        mode=MODE_BIPED,
        description="Locomotion where one foot stays planted much longer than the other. Off by default.",
        function=check_gait_asymmetry,
        parameters=[
            ParameterSpec("min_speed", "Min Speed", 0.6, 0.0, 100.0,
                          "Character speed that counts as locomotion (leg lengths per second)."),
            ParameterSpec("asymmetry_ratio", "Asymmetry", 0.35, 0.0, 1.0,
                          "Allowed relative stance-time difference between the feet."),
        ],
        required_roles=LEG_ROLES + ["hips"],
        enabled=False, weight=0.25, warn_below=90, fail_below=0, event_penalty=0.0, frame_penalty=0.5,
    ),
]
