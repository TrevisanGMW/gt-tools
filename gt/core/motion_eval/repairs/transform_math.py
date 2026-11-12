"""
Pure transform math for repairs: flat row-major 4x4 matrices (Maya layout), 3x3 rotation rows,
and (x, y, z, w) quaternions.

Conventions follow math_utils: matrices are 16 values with the translation at indices 12-14 and
row vectors, so ``world = local * parent_world``. A quaternion turned into rotation rows with
``quaternion_to_rows`` rotates a row vector ``v * rows`` the same way the quaternion rotates it.
"""

import math

from .. import math_utils

SMALL_NUMBER = 1e-9
IDENTITY_QUATERNION = (0.0, 0.0, 0.0, 1.0)


def multiply_matrices(matrix_a, matrix_b):
    """Multiplies two flat 4x4 matrices (``matrix_a * matrix_b``).

    Args:
        matrix_a (list): Sixteen values.
        matrix_b (list): Sixteen values.

    Returns:
        list: Sixteen values.
    """
    result = []
    for row in range(4):
        for column in range(4):
            result.append(sum(float(matrix_a[row * 4 + inner]) * float(matrix_b[inner * 4 + column])
                              for inner in range(4)))
    return result


def invert_matrix(matrix):
    """Inverts an affine flat 4x4 matrix.

    Args:
        matrix (list): Sixteen values (last column 0, 0, 0, 1).

    Returns:
        list: Sixteen values.

    Raises:
        ValueError: When the 3x3 part is singular.
    """
    values = [float(value) for value in matrix]
    a_value, b_value, c_value = values[0], values[1], values[2]
    d_value, e_value, f_value = values[4], values[5], values[6]
    g_value, h_value, i_value = values[8], values[9], values[10]
    cofactor_a = e_value * i_value - f_value * h_value
    cofactor_b = -(d_value * i_value - f_value * g_value)
    cofactor_c = d_value * h_value - e_value * g_value
    determinant = a_value * cofactor_a + b_value * cofactor_b + c_value * cofactor_c
    if abs(determinant) < SMALL_NUMBER:
        raise ValueError("Matrix cannot be inverted (zero scale).")
    inverse_rows = [
        (cofactor_a, -(b_value * i_value - c_value * h_value), b_value * f_value - c_value * e_value),
        (cofactor_b, a_value * i_value - c_value * g_value, -(a_value * f_value - c_value * d_value)),
        (cofactor_c, -(a_value * h_value - b_value * g_value), a_value * e_value - b_value * d_value),
    ]
    inverse_rows = [tuple(value / determinant for value in row) for row in inverse_rows]
    translation = (values[12], values[13], values[14])
    inverse_translation = tuple(
        -sum(translation[inner] * inverse_rows[inner][column] for inner in range(3)) for column in range(3)
    )
    result = []
    for row in inverse_rows:
        result.extend([row[0], row[1], row[2], 0.0])
    result.extend([inverse_translation[0], inverse_translation[1], inverse_translation[2], 1.0])
    return result


def local_from_world(world_matrix, parent_world_matrix):
    """Computes a local matrix from a world matrix and its parent's world matrix.

    Args:
        world_matrix (list): Node world matrix.
        parent_world_matrix (list): Parent world matrix, or None for a top node.

    Returns:
        list: Local matrix.
    """
    if parent_world_matrix is None:
        return [float(value) for value in world_matrix]
    return multiply_matrices(world_matrix, invert_matrix(parent_world_matrix))


def world_from_local(local_matrix, parent_world_matrix):
    """Computes a world matrix from a local matrix and the parent's world matrix.

    Args:
        local_matrix (list): Local matrix.
        parent_world_matrix (list): Parent world matrix, or None for a top node.

    Returns:
        list: World matrix.
    """
    if parent_world_matrix is None:
        return [float(value) for value in local_matrix]
    return multiply_matrices(local_matrix, parent_world_matrix)


def rows_to_quaternion(rows):
    """Converts three unit rotation rows into a quaternion.

    Args:
        rows (list): Three unit axis vectors (see math_utils.matrix_rotation).

    Returns:
        tuple: Normalized quaternion (x, y, z, w).
    """
    m00, m01, m02 = rows[0]
    m10, m11, m12 = rows[1]
    m20, m21, m22 = rows[2]
    trace = m00 + m11 + m22
    if trace > 0.0:
        factor = math.sqrt(trace + 1.0) * 2.0
        quaternion = ((m12 - m21) / factor, (m20 - m02) / factor, (m01 - m10) / factor, 0.25 * factor)
    elif m00 > m11 and m00 > m22:
        factor = math.sqrt(max(SMALL_NUMBER, 1.0 + m00 - m11 - m22)) * 2.0
        quaternion = (0.25 * factor, (m01 + m10) / factor, (m02 + m20) / factor, (m12 - m21) / factor)
    elif m11 > m22:
        factor = math.sqrt(max(SMALL_NUMBER, 1.0 + m11 - m00 - m22)) * 2.0
        quaternion = ((m01 + m10) / factor, 0.25 * factor, (m12 + m21) / factor, (m20 - m02) / factor)
    else:
        factor = math.sqrt(max(SMALL_NUMBER, 1.0 + m22 - m00 - m11)) * 2.0
        quaternion = ((m02 + m20) / factor, (m12 + m21) / factor, 0.25 * factor, (m01 - m10) / factor)
    return normalize_quaternion(quaternion)


def quaternion_to_rows(quaternion):
    """Converts a quaternion into three rotation rows.

    Args:
        quaternion (tuple): Quaternion (x, y, z, w).

    Returns:
        list: Three unit axis vectors.
    """
    matrix = math_utils.compose_matrix((0.0, 0.0, 0.0), quaternion)
    return math_utils.matrix_axes(matrix)


def normalize_quaternion(quaternion):
    """Normalizes a quaternion.

    Args:
        quaternion (tuple): Quaternion (x, y, z, w).

    Returns:
        tuple: Unit quaternion, identity when the input has no length.
    """
    norm = math.sqrt(sum(float(value) * float(value) for value in quaternion))
    if norm < SMALL_NUMBER:
        return IDENTITY_QUATERNION
    return tuple(float(value) / norm for value in quaternion)


def quaternion_dot(quaternion_a, quaternion_b):
    """Dot product of two quaternions.

    Args:
        quaternion_a (tuple): Quaternion.
        quaternion_b (tuple): Quaternion.

    Returns:
        float: Dot product.
    """
    return sum(float(value_a) * float(value_b) for value_a, value_b in zip(quaternion_a, quaternion_b))


def align_quaternion(quaternion, reference):
    """Flips a quaternion's sign so it lies on the same hemisphere as a reference.

    Args:
        quaternion (tuple): Quaternion to align.
        reference (tuple): Reference quaternion.

    Returns:
        tuple: Equivalent quaternion closest to the reference.
    """
    if quaternion_dot(quaternion, reference) < 0.0:
        return tuple(-float(value) for value in quaternion)
    return tuple(float(value) for value in quaternion)


def slerp(quaternion_a, quaternion_b, blend):
    """Spherical interpolation between two quaternions (shortest path).

    Args:
        quaternion_a (tuple): Start quaternion.
        quaternion_b (tuple): End quaternion.
        blend (float): 0 returns the start, 1 the end.

    Returns:
        tuple: Unit quaternion.
    """
    start = normalize_quaternion(quaternion_a)
    end = align_quaternion(normalize_quaternion(quaternion_b), start)
    cosine = max(-1.0, min(1.0, quaternion_dot(start, end)))
    if cosine > 0.9995:
        mixed = tuple(value_a + (value_b - value_a) * blend for value_a, value_b in zip(start, end))
        return normalize_quaternion(mixed)
    angle = math.acos(cosine)
    sine = math.sin(angle)
    weight_a = math.sin((1.0 - blend) * angle) / sine
    weight_b = math.sin(blend * angle) / sine
    return normalize_quaternion(tuple(weight_a * value_a + weight_b * value_b for value_a, value_b in zip(start, end)))


def quaternion_from_to(from_direction, to_direction):
    """Builds the smallest rotation that turns one direction into another.

    Args:
        from_direction (tuple): Start direction (any length).
        to_direction (tuple): End direction (any length).

    Returns:
        tuple: Quaternion (x, y, z, w). Identity when a direction is zero; a half turn around a
            perpendicular axis when they are opposite.
    """
    start = math_utils.normalize(from_direction)
    end = math_utils.normalize(to_direction)
    if start is None or end is None:
        return IDENTITY_QUATERNION
    cosine = max(-1.0, min(1.0, math_utils.dot(start, end)))
    if cosine < -0.999999:
        axis = math_utils.perpendicular_vector(start)
        return (axis[0], axis[1], axis[2], 0.0)
    axis = math_utils.cross(start, end)
    return normalize_quaternion((axis[0], axis[1], axis[2], 1.0 + cosine))


def multiply_rows(rows_a, rows_b):
    """Multiplies two 3x3 rotation row sets (``rows_a * rows_b``).

    Args:
        rows_a (list): Three axis vectors.
        rows_b (list): Three axis vectors.

    Returns:
        list: Three axis vectors.
    """
    return [
        tuple(sum(rows_a[row][inner] * rows_b[inner][column] for inner in range(3)) for column in range(3))
        for row in range(3)
    ]


def rotate_row_vector(vector, rows):
    """Rotates a row vector by rotation rows (``vector * rows``).

    Args:
        vector (tuple): Vector.
        rows (list): Three axis vectors.

    Returns:
        tuple: Rotated vector.
    """
    return math_utils.to_world(rows, vector)


def split_matrix(matrix):
    """Splits a matrix into rotation rows, per-axis scale, and position.

    Args:
        matrix (list): Sixteen values.

    Returns:
        tuple: (rows, scale, position).
    """
    return math_utils.matrix_rotation(matrix), math_utils.matrix_scale(matrix), math_utils.matrix_position(matrix)


def join_matrix(rows, scale_values, position):
    """Builds a matrix from rotation rows, per-axis scale, and position.

    Args:
        rows (list): Three unit axis vectors.
        scale_values (tuple): Scale per axis.
        position (tuple): Translation.

    Returns:
        list: Sixteen values.
    """
    values = []
    for row, row_scale in zip(rows, scale_values):
        values.extend([row[0] * row_scale, row[1] * row_scale, row[2] * row_scale, 0.0])
    values.extend([float(position[0]), float(position[1]), float(position[2]), 1.0])
    return values


def matrix_to_quaternion(matrix):
    """Gets the rotation of a matrix as a quaternion.

    Args:
        matrix (list): Sixteen values.

    Returns:
        tuple: Quaternion (x, y, z, w).
    """
    return rows_to_quaternion(math_utils.matrix_rotation(matrix))


def replace_rotation(matrix, quaternion):
    """Replaces the rotation of a matrix, keeping its scale and position.

    Args:
        matrix (list): Sixteen values.
        quaternion (tuple): New rotation.

    Returns:
        list: Sixteen values.
    """
    _rows, scale_values, position = split_matrix(matrix)
    return join_matrix(quaternion_to_rows(quaternion), scale_values, position)


def replace_position(matrix, position):
    """Replaces the translation of a matrix.

    Args:
        matrix (list): Sixteen values.
        position (tuple): New translation.

    Returns:
        list: Sixteen values.
    """
    values = [float(value) for value in matrix]
    values[12], values[13], values[14] = float(position[0]), float(position[1]), float(position[2])
    return values
