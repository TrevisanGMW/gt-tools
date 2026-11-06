"""
Motion Evaluation Math Utilities - Pure vector, series, and frame-span helpers.

Every function works on plain Python lists and tuples so the module stays
importable outside Maya and does not depend on external libraries.
"""

import math

SMALL_NUMBER = 1e-9


# ------------------------------------------------ Vectors ------------------------------------------------
def subtract(vector_a, vector_b):
    """Subtracts two 3D vectors.

    Args:
        vector_a (tuple): First vector.
        vector_b (tuple): Vector to subtract.

    Returns:
        tuple: Component-wise difference.
    """
    return (vector_a[0] - vector_b[0], vector_a[1] - vector_b[1], vector_a[2] - vector_b[2])


def add(vector_a, vector_b):
    """Adds two 3D vectors.

    Args:
        vector_a (tuple): First vector.
        vector_b (tuple): Second vector.

    Returns:
        tuple: Component-wise sum.
    """
    return (vector_a[0] + vector_b[0], vector_a[1] + vector_b[1], vector_a[2] + vector_b[2])


def scale(vector, factor):
    """Scales a 3D vector.

    Args:
        vector (tuple): Vector to scale.
        factor (float): Scale factor.

    Returns:
        tuple: Scaled vector.
    """
    return (vector[0] * factor, vector[1] * factor, vector[2] * factor)


def dot(vector_a, vector_b):
    """Computes the dot product of two 3D vectors.

    Args:
        vector_a (tuple): First vector.
        vector_b (tuple): Second vector.

    Returns:
        float: Dot product.
    """
    return vector_a[0] * vector_b[0] + vector_a[1] * vector_b[1] + vector_a[2] * vector_b[2]


def length(vector):
    """Computes the length of a 3D vector.

    Args:
        vector (tuple): Vector to measure.

    Returns:
        float: Euclidean length.
    """
    return math.sqrt(dot(vector, vector))


def distance(point_a, point_b):
    """Computes the distance between two 3D points.

    Args:
        point_a (tuple): First point.
        point_b (tuple): Second point.

    Returns:
        float: Euclidean distance.
    """
    return length(subtract(point_a, point_b))


def planar_distance(point_a, point_b):
    """Computes the ground-plane (XZ) distance between two Y-up points.

    Args:
        point_a (tuple): First point.
        point_b (tuple): Second point.

    Returns:
        float: Distance ignoring the vertical axis.
    """
    return math.hypot(point_a[0] - point_b[0], point_a[2] - point_b[2])


def lerp(point_a, point_b, blend):
    """Linearly interpolates two 3D points.

    Args:
        point_a (tuple): Start point.
        point_b (tuple): End point.
        blend (float): Blend from 0 (start) to 1 (end).

    Returns:
        tuple: Interpolated point.
    """
    return add(point_a, scale(subtract(point_b, point_a), blend))


def point_segment_distance(point, segment_start, segment_end):
    """Computes the shortest distance from a point to a 3D segment.

    Args:
        point (tuple): Query point.
        segment_start (tuple): Segment start.
        segment_end (tuple): Segment end.

    Returns:
        float: Shortest distance.
    """
    segment = subtract(segment_end, segment_start)
    segment_length_squared = dot(segment, segment)
    if segment_length_squared <= SMALL_NUMBER:
        return distance(point, segment_start)
    projection = dot(subtract(point, segment_start), segment) / segment_length_squared
    projection = max(0.0, min(1.0, projection))
    return distance(point, lerp(segment_start, segment_end, projection))


def segment_segment_distance(start_a, end_a, start_b, end_b):
    """Computes the shortest distance between two 3D segments.

    Args:
        start_a (tuple): First segment start.
        end_a (tuple): First segment end.
        start_b (tuple): Second segment start.
        end_b (tuple): Second segment end.

    Returns:
        float: Shortest distance between the segments.
    """
    direction_a = subtract(end_a, start_a)
    direction_b = subtract(end_b, start_b)
    offset = subtract(start_a, start_b)
    length_a = dot(direction_a, direction_a)
    length_b = dot(direction_b, direction_b)
    projection_b = dot(direction_b, offset)
    if length_a <= SMALL_NUMBER and length_b <= SMALL_NUMBER:
        return distance(start_a, start_b)
    if length_a <= SMALL_NUMBER:
        return point_segment_distance(start_a, start_b, end_b)
    if length_b <= SMALL_NUMBER:
        return point_segment_distance(start_b, start_a, end_a)
    projection_a = dot(direction_a, offset)
    cross_term = dot(direction_a, direction_b)
    denominator = length_a * length_b - cross_term * cross_term
    if denominator > SMALL_NUMBER:
        blend_a = max(0.0, min(1.0, (cross_term * projection_b - projection_a * length_b) / denominator))
    else:
        blend_a = 0.0
    blend_b = (cross_term * blend_a + projection_b) / length_b
    if blend_b < 0.0:
        blend_b = 0.0
        blend_a = max(0.0, min(1.0, -projection_a / length_a))
    elif blend_b > 1.0:
        blend_b = 1.0
        blend_a = max(0.0, min(1.0, (cross_term - projection_a) / length_a))
    closest_a = lerp(start_a, end_a, blend_a)
    closest_b = lerp(start_b, end_b, blend_b)
    return distance(closest_a, closest_b)


# ------------------------------------------------ Matrices ------------------------------------------------
def matrix_position(matrix):
    """Gets the translation of a flat row-major 4x4 Maya matrix.

    Args:
        matrix (list): Sixteen matrix values.

    Returns:
        tuple: Translation (x, y, z).
    """
    return (float(matrix[12]), float(matrix[13]), float(matrix[14]))


def compose_matrix(position, quaternion=(0.0, 0.0, 0.0, 1.0), scale_values=(1.0, 1.0, 1.0)):
    """Builds a flat row-major 4x4 matrix (Maya layout) from a position, rotation, and scale.

    Args:
        position (tuple): Translation (x, y, z).
        quaternion (tuple): Rotation quaternion as (x, y, z, w). It is normalized first.
        scale_values (tuple): Scale along the local X, Y, and Z axes.

    Returns:
        list: Sixteen matrix values, translation at indices 12, 13, 14.
    """
    x_value, y_value, z_value, w_value = (float(value) for value in quaternion)
    norm = math.sqrt(x_value * x_value + y_value * y_value + z_value * z_value + w_value * w_value) or 1.0
    x_value, y_value, z_value, w_value = (value / norm for value in (x_value, y_value, z_value, w_value))
    rows = [
        (1.0 - 2.0 * (y_value * y_value + z_value * z_value), 2.0 * (x_value * y_value + z_value * w_value),
         2.0 * (x_value * z_value - y_value * w_value)),
        (2.0 * (x_value * y_value - z_value * w_value), 1.0 - 2.0 * (x_value * x_value + z_value * z_value),
         2.0 * (y_value * z_value + x_value * w_value)),
        (2.0 * (x_value * z_value + y_value * w_value), 2.0 * (y_value * z_value - x_value * w_value),
         1.0 - 2.0 * (x_value * x_value + y_value * y_value)),
    ]
    values = []
    for row, row_scale in zip(rows, scale_values):
        values.extend([row[0] * row_scale, row[1] * row_scale, row[2] * row_scale, 0.0])
    values.extend([float(position[0]), float(position[1]), float(position[2]), 1.0])
    return values


def matrix_axes(matrix):
    """Gets the three axis rows of a flat row-major 4x4 Maya matrix.

    Args:
        matrix (list): Sixteen matrix values.

    Returns:
        list: X, Y, and Z axis vectors (including scale).
    """
    return [
        (float(matrix[0]), float(matrix[1]), float(matrix[2])),
        (float(matrix[4]), float(matrix[5]), float(matrix[6])),
        (float(matrix[8]), float(matrix[9]), float(matrix[10])),
    ]


def matrix_scale(matrix):
    """Gets the per-axis scale of a matrix.

    Args:
        matrix (list): Sixteen matrix values.

    Returns:
        tuple: Length of each axis row.
    """
    axes = matrix_axes(matrix)
    return (length(axes[0]), length(axes[1]), length(axes[2]))


def matrix_rotation(matrix):
    """Gets the normalized 3x3 rotation rows of a matrix.

    Args:
        matrix (list): Sixteen matrix values.

    Returns:
        list: Three unit-length axis vectors.
    """
    rotation = []
    for axis in matrix_axes(matrix):
        axis_length = length(axis)
        rotation.append(scale(axis, 1.0 / axis_length) if axis_length > SMALL_NUMBER else (0.0, 0.0, 0.0))
    return rotation


def rotation_angle_between(matrix_a, matrix_b):
    """Measures the rotation angle between the orientations of two matrices.

    Args:
        matrix_a (list): First matrix values.
        matrix_b (list): Second matrix values.

    Returns:
        float: Angle in degrees from 0 to 180.
    """
    rotation_a = matrix_rotation(matrix_a)
    rotation_b = matrix_rotation(matrix_b)
    trace = sum(dot(rotation_a[axis_index], rotation_b[axis_index]) for axis_index in range(3))
    cosine = max(-1.0, min(1.0, (trace - 1.0) * 0.5))
    return math.degrees(math.acos(cosine))


def is_finite_sequence(values):
    """Checks whether every value in a sequence is a finite number.

    Args:
        values (list): Numeric values.

    Returns:
        bool: True when no value is NaN or infinite.
    """
    try:
        return all(math.isfinite(float(value)) for value in values)
    except (TypeError, ValueError):
        return False


# ------------------------------------------------ Series ------------------------------------------------
def moving_average(values, window_size):
    """Smooths a numeric series with a centered moving average.

    Args:
        values (list): Numeric values.
        window_size (int): Number of samples in the window.

    Returns:
        list: Smoothed values with the input length.
    """
    values = [float(value) for value in values]
    window_size = max(1, int(window_size))
    if window_size <= 1 or len(values) < 3:
        return values
    half_window = window_size // 2
    smoothed = []
    for index in range(len(values)):
        window_values = values[max(0, index - half_window):min(len(values), index + half_window + 1)]
        smoothed.append(sum(window_values) / len(window_values))
    return smoothed


def quadratic_smooth(values, half_window=2):
    """Smooths a series with a centered least-squares quadratic fit (Savitzky-Golay).

    Smooth motion, even when fast, is close to quadratic over a few frames,
    so the residual of this fit isolates high-frequency noise.

    Args:
        values (list): Numeric values.
        half_window (int): Samples on each side of the center sample.

    Returns:
        list: Smoothed values. Edge samples keep their original values.
    """
    values = [float(value) for value in values]
    half_window = max(1, int(half_window))
    window_size = 2 * half_window + 1
    if len(values) < window_size:
        return list(values)
    offsets = list(range(-half_window, half_window + 1))
    sum_offset_2 = sum(offset ** 2 for offset in offsets)
    sum_offset_4 = sum(offset ** 4 for offset in offsets)
    denominator = window_size * sum_offset_4 - sum_offset_2 ** 2
    weights = [(sum_offset_4 - sum_offset_2 * offset ** 2) / denominator for offset in offsets]
    smoothed = list(values)
    for index in range(half_window, len(values) - half_window):
        smoothed[index] = sum(
            weight * values[index + offset] for weight, offset in zip(weights, offsets)
        )
    return smoothed


def jitter_residuals(positions, half_window=2):
    """Measures per-frame deviation of a trajectory from its quadratic smoothing.

    Args:
        positions (list): (x, y, z) positions, one per frame.
        half_window (int): Samples on each side used by the quadratic fit.

    Returns:
        list: Residual distances, one per frame (zero at the edges).
    """
    if not positions:
        return []
    smoothed_axes = [quadratic_smooth([position[axis] for position in positions], half_window) for axis in range(3)]
    residuals = []
    for frame_index, position in enumerate(positions):
        smoothed = (smoothed_axes[0][frame_index], smoothed_axes[1][frame_index], smoothed_axes[2][frame_index])
        residuals.append(distance(position, smoothed))
    return residuals


def speeds(positions, fps, planar=False):
    """Computes per-frame speeds from consecutive positions.

    Args:
        positions (list): (x, y, z) positions, one per frame.
        fps (float): Frames per second.
        planar (bool): Ignore the vertical (Y) axis when True.

    Returns:
        list: Speeds in units per second; the first frame copies the second.
    """
    if len(positions) < 2:
        return [0.0] * len(positions)
    measure = planar_distance if planar else distance
    values = [measure(positions[index], positions[index - 1]) * fps for index in range(1, len(positions))]
    return [values[0]] + values


def percentile(values, fraction):
    """Gets an interpolated percentile of unsorted values.

    Args:
        values (list): Numeric values.
        fraction (float): Position from 0 to 1.

    Returns:
        float: Percentile value, or 0.0 for empty input.
    """
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    exact_index = max(0.0, min(1.0, float(fraction))) * (len(ordered) - 1)
    lower_index = int(math.floor(exact_index))
    upper_index = min(lower_index + 1, len(ordered) - 1)
    blend = exact_index - lower_index
    return ordered[lower_index] * (1.0 - blend) + ordered[upper_index] * blend


def median(values):
    """Gets the median of unsorted values.

    Args:
        values (list): Numeric values.

    Returns:
        float: Median, or 0.0 for empty input.
    """
    return percentile(values, 0.5)


def smoothstep(value):
    """Evaluates a clamped cubic smoothstep.

    Args:
        value (float): Unclamped normalized value.

    Returns:
        float: Smooth value between 0 and 1.
    """
    value = max(0.0, min(1.0, float(value)))
    return value * value * (3.0 - 2.0 * value)


def fit_parabola(values, time_step):
    """Fits value = a*t^2 + b*t + c with least squares.

    Args:
        values (list): Samples at uniform time steps.
        time_step (float): Seconds between samples.

    Returns:
        float or None: Second derivative (2a) in units per second squared, or None if under-determined.
    """
    sample_count = len(values)
    if sample_count < 3:
        return None
    times = [index * time_step for index in range(sample_count)]
    sums = [sum(time ** power for time in times) for power in range(5)]
    targets = [sum(value * time ** power for value, time in zip(values, times)) for power in (2, 1, 0)]
    matrix = [
        [sums[4], sums[3], sums[2]],
        [sums[3], sums[2], sums[1]],
        [sums[2], sums[1], sums[0]],
    ]
    solution = solve_3x3(matrix, targets)
    if solution is None:
        return None
    return 2.0 * solution[0]


def solve_3x3(matrix, targets):
    """Solves a 3x3 linear system with Cramer's rule.

    Args:
        matrix (list): Three rows of three coefficients.
        targets (list): Right-hand side values.

    Returns:
        list or None: Solution, or None when the system is singular.
    """
    def determinant(rows):
        """Computes a 3x3 determinant.

        Args:
            rows (list): Three rows of three values.

        Returns:
            float: Determinant.
        """
        return (
            rows[0][0] * (rows[1][1] * rows[2][2] - rows[1][2] * rows[2][1])
            - rows[0][1] * (rows[1][0] * rows[2][2] - rows[1][2] * rows[2][0])
            + rows[0][2] * (rows[1][0] * rows[2][1] - rows[1][1] * rows[2][0])
        )

    base_determinant = determinant(matrix)
    if abs(base_determinant) <= 1e-15:
        return None
    solution = []
    for column_index in range(3):
        replaced = [list(row) for row in matrix]
        for row_index in range(3):
            replaced[row_index][column_index] = targets[row_index]
        solution.append(determinant(replaced) / base_determinant)
    return solution


# ------------------------------------------------ Frame Spans ------------------------------------------------
def indexes_to_spans(indexes):
    """Compresses frame indexes into inclusive index spans.

    Args:
        indexes (iterable): Frame indexes.

    Returns:
        list: Inclusive [start, end] index spans in ascending order.
    """
    spans = []
    for index in sorted(set(int(value) for value in indexes)):
        if spans and index == spans[-1][1] + 1:
            spans[-1][1] = index
        else:
            spans.append([index, index])
    return spans


def spans_to_indexes(spans):
    """Expands inclusive spans into a set of indexes.

    Args:
        spans (list): Inclusive [start, end] spans.

    Returns:
        set: Every index covered by the spans.
    """
    indexes = set()
    for start, end in spans:
        indexes.update(range(int(start), int(end) + 1))
    return indexes


def filter_minimum_run(indexes, minimum_run_length):
    """Keeps only indexes that belong to sufficiently long consecutive runs.

    Args:
        indexes (iterable): Flagged frame indexes.
        minimum_run_length (int): Minimum run length to keep.

    Returns:
        set: Indexes from runs at least ``minimum_run_length`` long.
    """
    minimum_run_length = max(1, int(minimum_run_length))
    kept = set()
    for start, end in indexes_to_spans(indexes):
        if end - start + 1 >= minimum_run_length:
            kept.update(range(start, end + 1))
    return kept


def find_runs(flags):
    """Finds consecutive True runs in a boolean series.

    Args:
        flags (list): Boolean values, one per frame.

    Returns:
        list: Inclusive [start, end] index spans where the flag is True.
    """
    return indexes_to_spans(index for index, flag in enumerate(flags) if flag)
