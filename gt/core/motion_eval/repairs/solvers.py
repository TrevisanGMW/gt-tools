"""
Pure solvers used by the repair fixes. They work on per-frame lists (index 0 = first sampled
frame) and never talk to a host, so they can be tested in plain Python.
"""

import math

from .. import math_utils
from . import transform_math


def build_blend_weights(frame_count, span_start, span_end, blend_frames):
    """Builds per-frame weights: 1 inside a span, smooth ramps before and after it, 0 elsewhere.

    Args:
        frame_count (int): Number of frames in the window.
        span_start (int): First index of the span (inclusive).
        span_end (int): Last index of the span (inclusive).
        blend_frames (int): Ramp length on each side.

    Returns:
        list: Weights between 0 and 1.
    """
    weights = []
    blend_frames = max(0, int(blend_frames))
    for index in range(frame_count):
        if span_start <= index <= span_end:
            weights.append(1.0)
        elif blend_frames and span_start - blend_frames <= index < span_start:
            weights.append(math_utils.smoothstep((index - (span_start - blend_frames - 1)) / float(blend_frames + 1)))
        elif blend_frames and span_end < index <= span_end + blend_frames:
            weights.append(math_utils.smoothstep((span_end + blend_frames + 1 - index) / float(blend_frames + 1)))
        else:
            weights.append(0.0)
    return weights


def hermite(value_start, value_end, tangent_start, tangent_end, blend):
    """Evaluates a cubic Hermite curve.

    Args:
        value_start (float): Value at blend 0.
        value_end (float): Value at blend 1.
        tangent_start (float): Tangent at blend 0 (per unit blend).
        tangent_end (float): Tangent at blend 1 (per unit blend).
        blend (float): Position between 0 and 1.

    Returns:
        float: Curve value.
    """
    squared = blend * blend
    cubed = squared * blend
    return ((2.0 * cubed - 3.0 * squared + 1.0) * value_start + (cubed - 2.0 * squared + blend) * tangent_start
            + (-2.0 * cubed + 3.0 * squared) * value_end + (cubed - squared) * tangent_end)


def bridge_vectors(vectors, span_start, span_end):
    """Replaces a span of vectors with a smooth curve between the frames around it.

    The anchors are the frames just before and after the span; their velocities shape the curve.

    Args:
        vectors (list): Per-frame vectors (tuples).
        span_start (int): First replaced index.
        span_end (int): Last replaced index.

    Returns:
        list: New vectors (same length). Unchanged when the span touches both window ends.
    """
    result = [tuple(vector) for vector in vectors]
    before = span_start - 1
    after = span_end + 1
    if before < 0 and after >= len(vectors):
        return result
    if before < 0:
        return [result[after] if span_start <= index <= span_end else vector for index, vector in enumerate(result)]
    if after >= len(vectors):
        return [result[before] if span_start <= index <= span_end else vector for index, vector in enumerate(result)]
    gap = float(after - before)
    velocity_start = math_utils.subtract(result[before], result[before - 1]) if before >= 1 else (0.0, 0.0, 0.0)
    velocity_end = math_utils.subtract(result[after + 1], result[after]) if after + 1 < len(result) else (0.0, 0.0, 0.0)
    for index in range(span_start, span_end + 1):
        blend = (index - before) / gap
        result[index] = tuple(
            hermite(result[before][axis], result[after][axis], velocity_start[axis] * gap, velocity_end[axis] * gap,
                    blend)
            for axis in range(3)
        )
    return result


def bridge_quaternions(quaternions, span_start, span_end):
    """Replaces a span of rotations with a slerp between the rotations around it.

    Args:
        quaternions (list): Per-frame quaternions.
        span_start (int): First replaced index.
        span_end (int): Last replaced index.

    Returns:
        list: New quaternions (same length).
    """
    result = [tuple(quaternion) for quaternion in quaternions]
    before = span_start - 1
    after = span_end + 1
    if before < 0 and after >= len(result):
        return result
    if before < 0:
        anchor = result[after]
        return [anchor if span_start <= index <= span_end else value for index, value in enumerate(result)]
    if after >= len(result):
        anchor = result[before]
        return [anchor if span_start <= index <= span_end else value for index, value in enumerate(result)]
    gap = float(after - before)
    for index in range(span_start, span_end + 1):
        blend = math_utils.smoothstep((index - before) / gap)
        result[index] = transform_math.slerp(result[before], result[after], blend)
    return result


def gaussian_kernel(radius, sigma=None):
    """Builds normalized Gaussian weights.

    Args:
        radius (int): Half width in frames.
        sigma (float, optional): Standard deviation. Defaults to half the radius.

    Returns:
        list: ``2 * radius + 1`` weights that sum to 1.
    """
    radius = max(1, int(radius))
    sigma = float(sigma or max(0.5, radius / 2.0))
    weights = [math.exp(-(offset * offset) / (2.0 * sigma * sigma)) for offset in range(-radius, radius + 1)]
    total = sum(weights)
    return [weight / total for weight in weights]


def smooth_vectors(vectors, radius):
    """Gaussian-smooths vectors, clamping at the window ends.

    Args:
        vectors (list): Per-frame vectors.
        radius (int): Kernel half width in frames.

    Returns:
        list: Smoothed vectors.
    """
    kernel = gaussian_kernel(radius)
    half = len(kernel) // 2
    last = len(vectors) - 1
    smoothed = []
    for index in range(len(vectors)):
        total = [0.0, 0.0, 0.0]
        for offset, weight in enumerate(kernel):
            sample = vectors[min(last, max(0, index + offset - half))]
            for axis in range(3):
                total[axis] += sample[axis] * weight
        smoothed.append(tuple(total))
    return smoothed


def smooth_quaternions(quaternions, radius):
    """Smooths rotations with a Gaussian average of hemisphere-aligned quaternions.

    Args:
        quaternions (list): Per-frame quaternions.
        radius (int): Kernel half width in frames.

    Returns:
        list: Smoothed unit quaternions.
    """
    aligned = []
    for quaternion in quaternions:
        aligned.append(transform_math.align_quaternion(quaternion, aligned[-1]) if aligned else tuple(quaternion))
    kernel = gaussian_kernel(radius)
    half = len(kernel) // 2
    last = len(aligned) - 1
    smoothed = []
    for index in range(len(aligned)):
        total = [0.0, 0.0, 0.0, 0.0]
        for offset, weight in enumerate(kernel):
            sample = aligned[min(last, max(0, index + offset - half))]
            for axis in range(4):
                total[axis] += sample[axis] * weight
        smoothed.append(transform_math.normalize_quaternion(total))
    return smoothed


def blend_vectors(original, target, weights):
    """Blends two vector lists per frame.

    Args:
        original (list): Original vectors.
        target (list): Target vectors.
        weights (list): Per-frame weights (0 = original, 1 = target).

    Returns:
        list: Blended vectors.
    """
    return [math_utils.lerp(value_a, value_b, weight) for value_a, value_b, weight in zip(original, target, weights)]


def blend_quaternions(original, target, weights):
    """Blends two quaternion lists per frame with slerp.

    Args:
        original (list): Original quaternions.
        target (list): Target quaternions.
        weights (list): Per-frame weights (0 = original, 1 = target).

    Returns:
        list: Blended quaternions.
    """
    return [transform_math.slerp(value_a, value_b, weight)
            for value_a, value_b, weight in zip(original, target, weights)]


def solve_two_bone(hip_position, knee_position, ankle_position, target_position, previous_bend=None):
    """Finds the knee position that puts the ankle on a target while keeping bone lengths.

    The knee stays in the plane it already bends in, so the leg does not flip.

    Args:
        hip_position (tuple): Upper joint position.
        knee_position (tuple): Middle joint position.
        ankle_position (tuple): End joint position.
        target_position (tuple): Desired end joint position.
        previous_bend (tuple, optional): Bend direction of the previous frame, used when the leg
            is straight.

    Returns:
        tuple: (new_knee_position, reached_target_position, bend_direction).
    """
    upper_length = math_utils.distance(hip_position, knee_position)
    lower_length = math_utils.distance(knee_position, ankle_position)
    to_target = math_utils.subtract(target_position, hip_position)
    target_distance = math_utils.length(to_target)
    reach_axis = math_utils.normalize(to_target) or math_utils.normalize(
        math_utils.subtract(ankle_position, hip_position)) or (0.0, -1.0, 0.0)
    minimum = abs(upper_length - lower_length) + 1e-4
    maximum = max(minimum, upper_length + lower_length - 1e-4)
    clamped_distance = min(max(target_distance, minimum), maximum)
    reached = math_utils.add(hip_position, math_utils.scale(reach_axis, clamped_distance))
    leg_axis = math_utils.normalize(math_utils.subtract(ankle_position, hip_position)) or reach_axis
    knee_offset = math_utils.subtract(knee_position, hip_position)
    bend = math_utils.subtract(knee_offset, math_utils.scale(leg_axis, math_utils.dot(knee_offset, leg_axis)))
    bend = math_utils.normalize(bend) or previous_bend or math_utils.perpendicular_vector(reach_axis)
    bend = math_utils.subtract(bend, math_utils.scale(reach_axis, math_utils.dot(bend, reach_axis)))
    bend = math_utils.normalize(bend) or math_utils.perpendicular_vector(reach_axis)
    along = (upper_length * upper_length - lower_length * lower_length + clamped_distance * clamped_distance) / (
        2.0 * clamped_distance)
    height = math.sqrt(max(0.0, upper_length * upper_length - along * along))
    new_knee = math_utils.add(math_utils.add(hip_position, math_utils.scale(reach_axis, along)),
                              math_utils.scale(bend, height))
    return new_knee, reached, bend


def solve_leg_matrices(hip_matrix, knee_matrix, ankle_matrix, target_position, previous_bend=None):
    """Re-poses a three-joint chain so its end reaches a target, keeping the end's world rotation.

    Args:
        hip_matrix (list): Upper joint world matrix.
        knee_matrix (list): Middle joint world matrix.
        ankle_matrix (list): End joint world matrix.
        target_position (tuple): Desired end position.
        previous_bend (tuple, optional): Bend direction from the previous frame.

    Returns:
        tuple: (hip_matrix, knee_matrix, ankle_matrix, bend_direction) as new world matrices.
    """
    hip_position = math_utils.matrix_position(hip_matrix)
    knee_position = math_utils.matrix_position(knee_matrix)
    ankle_position = math_utils.matrix_position(ankle_matrix)
    new_knee, reached, bend = solve_two_bone(hip_position, knee_position, ankle_position, target_position,
                                             previous_bend)
    upper_turn = transform_math.quaternion_to_rows(transform_math.quaternion_from_to(
        math_utils.subtract(knee_position, hip_position), math_utils.subtract(new_knee, hip_position)))
    hip_rows, hip_scale, _hip_position = transform_math.split_matrix(hip_matrix)
    new_hip = transform_math.join_matrix(transform_math.multiply_rows(hip_rows, upper_turn), hip_scale, hip_position)
    knee_rows, knee_scale, _knee_position = transform_math.split_matrix(knee_matrix)
    turned_knee_rows = transform_math.multiply_rows(knee_rows, upper_turn)
    turned_lower = transform_math.rotate_row_vector(math_utils.subtract(ankle_position, knee_position), upper_turn)
    lower_turn = transform_math.quaternion_to_rows(transform_math.quaternion_from_to(
        turned_lower, math_utils.subtract(reached, new_knee)))
    new_knee_matrix = transform_math.join_matrix(transform_math.multiply_rows(turned_knee_rows, lower_turn),
                                                 knee_scale, new_knee)
    new_ankle = transform_math.replace_position(ankle_matrix, reached)
    return new_hip, new_knee_matrix, new_ankle, bend


def get_axis_index(up_axis):
    """Gets the vector index of an up axis.

    Args:
        up_axis (str): "y" or "z".

    Returns:
        int: 1 for Y, 2 for Z.
    """
    return 2 if str(up_axis).lower() == "z" else 1


PIN_ANCHORS = ("average", "start", "end", "still")


def find_still_index(positions, span_start, span_end, up_axis="y"):
    """Finds the frame of a span where a point moves least along the ground plane.

    Args:
        positions (list): Per-frame positions.
        span_start (int): First index.
        span_end (int): Last index.
        up_axis (str): "y" or "z".

    Returns:
        int: Index inside the span.
    """
    axis_index = get_axis_index(up_axis)
    best_index, best_speed = span_start, None
    for index in range(span_start, span_end + 1):
        previous = positions[max(0, index - 1)]
        following = positions[min(len(positions) - 1, index + 1)]
        speed = math.sqrt(sum((following[axis] - previous[axis]) ** 2 for axis in range(3) if axis != axis_index))
        if best_speed is None or speed < best_speed:
            best_index, best_speed = index, speed
    return best_index


def get_pin_position(positions, span_start, span_end, anchor="average", up_axis="y"):
    """Gets the position a foot is pinned to over a span.

    Args:
        positions (list): Per-frame positions.
        span_start (int): First index.
        span_end (int): Last index.
        anchor (str): "average" (mean over the span), "start", "end", or "still" (the frame
            where the foot moves least).
        up_axis (str): "y" or "z".

    Returns:
        tuple: Pin position.

    Raises:
        ValueError: When the anchor is unknown.
    """
    if anchor == "start":
        return tuple(positions[span_start])
    if anchor == "end":
        return tuple(positions[span_end])
    if anchor == "still":
        return tuple(positions[find_still_index(positions, span_start, span_end, up_axis)])
    if anchor != "average":
        raise ValueError(f'pin_at must be one of {", ".join(PIN_ANCHORS)}, not "{anchor}".')
    span = positions[span_start:span_end + 1]
    count = float(len(span)) or 1.0
    return tuple(sum(position[axis] for position in span) / count for axis in range(3))


def build_pin_targets(positions, span_start, span_end, up_axis="y", pin_height=False, min_height=None,
                      anchor="average"):
    """Builds the pinned foot positions for a contact span.

    The ground-plane position comes from ``anchor``; the height follows the original motion
    unless ``pin_height`` is on (then the anchor's height is used).

    Args:
        positions (list): Per-frame foot positions.
        span_start (int): First pinned index.
        span_end (int): Last pinned index.
        up_axis (str): "y" or "z".
        pin_height (bool): Also pin the height.
        min_height (float, optional): Lowest allowed height for every frame of the window.
        anchor (str): See get_pin_position.

    Returns:
        list: Target positions for every frame (outside the span the original position).
    """
    axis_index = get_axis_index(up_axis)
    pin = get_pin_position(positions, span_start, span_end, anchor, up_axis)
    targets = []
    for index, position in enumerate(positions):
        target = list(position)
        if span_start <= index <= span_end:
            for axis in range(3):
                if axis != axis_index or pin_height:
                    target[axis] = pin[axis]
        if min_height is not None:
            target[axis_index] = max(float(min_height), target[axis_index])
        targets.append(tuple(target))
    return targets


def extend_contact_span(heights, span_start, span_end, max_height, max_extend, positions=None, max_drift=None,
                        up_axis="y"):
    """Grows a span to the whole contact around it: neighbor frames whose height stays low.

    With ``positions`` and ``max_drift``, a neighbor frame only joins while the point stays within
    ``max_drift`` (along the ground) of the reported span's average position, so the span never
    grows into a step or a long shuffle.

    Args:
        heights (list): Per-frame heights above the floor.
        span_start (int): First index of the reported span.
        span_end (int): Last index of the reported span.
        max_height (float): Highest height that still counts as contact.
        max_extend (int): Most frames added on each side.
        positions (list, optional): Per-frame positions (same indexes as heights).
        max_drift (float, optional): Largest ground-plane distance from the span's average position.
        up_axis (str): "y" or "z".

    Returns:
        tuple: (start, end) indexes of the grown span.
    """
    center = None
    if positions is not None and max_drift is not None:
        center = get_pin_position(positions, span_start, span_end, "average", up_axis)
    axis_index = get_axis_index(up_axis)

    def is_contact(index):
        """Checks whether a frame still belongs to the contact.

        Args:
            index (int): Frame index.

        Returns:
            bool: True when low enough (and close enough to the contact).
        """
        if heights[index] > max_height:
            return False
        if center is None:
            return True
        drift = math.sqrt(sum((positions[index][axis] - center[axis]) ** 2 for axis in range(3) if axis != axis_index))
        return drift <= max_drift

    start, end = span_start, span_end
    while start > 0 and span_start - start < max_extend and is_contact(start - 1):
        start -= 1
    while end < len(heights) - 1 and end - span_end < max_extend and is_contact(end + 1):
        end += 1
    return start, end


def build_ground_offsets(contact_heights, floor_height, mode="both", smooth_radius=2):
    """Computes per-frame vertical offsets that put the lowest contact point on the floor.

    Args:
        contact_heights (list): Lowest contact height per frame.
        floor_height (float): Floor height.
        mode (str): "both", "raise" (only fix sinking), or "lower" (only fix floating).
        smooth_radius (int): Gaussian smoothing half width (0 = none).

    Returns:
        list: Offsets along the up axis.
    """
    offsets = []
    for height in contact_heights:
        offset = float(floor_height) - float(height)
        if mode == "raise":
            offset = max(0.0, offset)
        elif mode == "lower":
            offset = min(0.0, offset)
        offsets.append(offset)
    if smooth_radius and len(offsets) > 2:
        offsets = [vector[0] for vector in smooth_vectors([(value, 0.0, 0.0) for value in offsets], smooth_radius)]
    return offsets


def clamp_step_vectors(vectors, span_start, span_end, max_step):
    """Limits frame-to-frame movement inside a span, meeting the original motion at both ends.

    A forward pass (from the frame before the span) and a backward pass (from the frame after)
    each cap every step at ``max_step``; they are cross-faded across the span.

    Args:
        vectors (list): Per-frame vectors.
        span_start (int): First index to change (>= 1).
        span_end (int): Last index to change (<= len - 2).
        max_step (float): Largest allowed step length.

    Returns:
        list: New vectors.
    """
    def step_towards(current, target):
        """Moves current toward target by at most max_step.

        Args:
            current (tuple): Current vector.
            target (tuple): Target vector.

        Returns:
            tuple: Moved vector.
        """
        offset = math_utils.subtract(target, current)
        distance = math_utils.length(offset)
        if distance <= max_step or distance < 1e-12:
            return tuple(target)
        return math_utils.add(current, math_utils.scale(offset, max_step / distance))

    result = [tuple(vector) for vector in vectors]
    forward, backward = {}, {}
    current = result[span_start - 1]
    for index in range(span_start, span_end + 1):
        current = step_towards(current, result[index])
        forward[index] = current
    current = result[span_end + 1]
    for index in range(span_end, span_start - 1, -1):
        current = step_towards(current, result[index])
        backward[index] = current
    length_count = float(span_end - span_start + 2)
    for index in range(span_start, span_end + 1):
        blend = (index - span_start + 1) / length_count
        result[index] = math_utils.lerp(forward[index], backward[index], blend)
    return result


def clamp_step_quaternions(quaternions, span_start, span_end, max_angle):
    """Limits frame-to-frame rotation inside a span (see clamp_step_vectors).

    Args:
        quaternions (list): Per-frame quaternions.
        span_start (int): First index to change (>= 1).
        span_end (int): Last index to change (<= len - 2).
        max_angle (float): Largest allowed step in radians.

    Returns:
        list: New quaternions.
    """
    def step_towards(current, target):
        """Rotates current toward target by at most max_angle.

        Args:
            current (tuple): Current quaternion.
            target (tuple): Target quaternion.

        Returns:
            tuple: Rotated quaternion.
        """
        angle = quaternion_angle(current, target)
        if angle <= max_angle or angle < 1e-12:
            return transform_math.align_quaternion(target, current)
        return transform_math.slerp(current, target, max_angle / angle)

    result = [tuple(quaternion) for quaternion in quaternions]
    forward, backward = {}, {}
    current = result[span_start - 1]
    for index in range(span_start, span_end + 1):
        current = step_towards(current, result[index])
        forward[index] = current
    current = result[span_end + 1]
    for index in range(span_end, span_start - 1, -1):
        current = step_towards(current, result[index])
        backward[index] = current
    length_count = float(span_end - span_start + 2)
    for index in range(span_start, span_end + 1):
        blend = (index - span_start + 1) / length_count
        result[index] = transform_math.slerp(forward[index], backward[index], blend)
    return result


def quaternion_angle(quaternion_a, quaternion_b):
    """Measures the rotation angle between two quaternions.

    Args:
        quaternion_a (tuple): Quaternion.
        quaternion_b (tuple): Quaternion.

    Returns:
        float: Angle in radians (0 to pi).
    """
    cosine = abs(transform_math.quaternion_dot(transform_math.normalize_quaternion(quaternion_a),
                                               transform_math.normalize_quaternion(quaternion_b)))
    return 2.0 * math.acos(min(1.0, cosine))


def median_step(values, exclude_start, exclude_end, measure):
    """Gets the median frame-to-frame step outside a span.

    Args:
        values (list): Per-frame values.
        exclude_start (int): First excluded index.
        exclude_end (int): Last excluded index.
        measure (callable): ``measure(value_a, value_b)`` returning a step size.

    Returns:
        float: Median step (0 when there is nothing to measure).
    """
    steps = [measure(values[index - 1], values[index]) for index in range(1, len(values))
             if not (exclude_start <= index <= exclude_end + 1)]
    return math_utils.median(steps) if steps else 0.0


def limit_hinge_direction(upper, lower, hinge, measure, limit_degrees):
    """Gets the lower-bone direction that brings a hinge back inside its limit.

    Args:
        upper (tuple): Upper bone unit direction (parent joint to hinge joint).
        lower (tuple): Lower bone unit direction (hinge joint to its child).
        hinge (tuple): Unit hinge axis in world space (normal bend is a positive turn around it).
        measure (str): "backward" (bending past straight) or "side" (bending out of the hinge plane).
        limit_degrees (float): Largest allowed angle.

    Returns:
        tuple or None: New lower direction, or None when the joint is already inside the limit.
    """
    hinge = math_utils.normalize(math_utils.subtract(hinge, math_utils.scale(upper, math_utils.dot(hinge, upper))))
    if hinge is None:
        return None
    if measure == "backward":
        backward = -math_utils.signed_angle(upper, lower, hinge)
        if backward <= limit_degrees:
            return None
        return math_utils.rotate_vector(lower, hinge, math.radians(backward - limit_degrees))
    side_amount = math_utils.dot(lower, hinge)
    side_angle = math.degrees(math.asin(max(-1.0, min(1.0, side_amount))))
    if abs(side_angle) <= limit_degrees:
        return None
    planar = math_utils.normalize(math_utils.subtract(lower, math_utils.scale(hinge, side_amount)))
    if planar is None:
        return None
    limit_radians = math.radians(limit_degrees) * (1.0 if side_angle > 0 else -1.0)
    return math_utils.normalize(math_utils.add(math_utils.scale(planar, math.cos(limit_radians)),
                                               math_utils.scale(hinge, math.sin(limit_radians))))
