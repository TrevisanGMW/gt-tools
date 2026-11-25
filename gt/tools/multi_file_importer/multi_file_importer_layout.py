"""
Multi-File Importer Layout

Pure math that spreads imported files apart: in a line along a step vector, or in a grid of
rows and columns. Indexes are zero-based. Nothing here imports Maya.

Every layout is expressed as: offset = coefficient_a * vector_a + coefficient_b * vector_b
- Line: vector_a is the step, coefficient_b is always 0.
- Grid: vector_a points along the columns (X), vector_b along the rows (Z on the floor, Y on the wall).
Because the offset is linear in the vectors, the layout controls can drive it live from spacing attributes.
"""

from gt.tools.multi_file_importer import multi_file_importer_constants as constants
import math


def resolve_column_count(item_count, requested_columns=0):
    """Gets the number of grid columns.

    Args:
        item_count (int): Number of items in the grid.
        requested_columns (int, optional): Fixed column count. Zero or less picks a square-ish grid.

    Returns:
        int: Column count, at least 1.
    """
    item_count = max(1, int(item_count or 1))
    requested_columns = int(requested_columns or 0)
    if requested_columns > 0:
        return requested_columns
    return max(1, int(math.ceil(math.sqrt(item_count))))


def get_grid_cell(item_index, column_count):
    """Gets the row and column of an item in a grid filled row by row.

    Args:
        item_index (int): Zero-based item index.
        column_count (int): Number of columns.

    Returns:
        tuple: (row, column).
    """
    column_count = max(1, int(column_count))
    return int(item_index) // column_count, int(item_index) % column_count


def build_layout_coefficients(item_count, settings):
    """Builds the (coefficient_a, coefficient_b) pair of every item.

    Args:
        item_count (int): Number of items to place.
        settings (dict): Tool settings (offset_mode, grid_columns, center_layout).

    Returns:
        list: One (coefficient_a, coefficient_b) tuple per item. All zeros when the offset mode is None.
    """
    item_count = int(item_count or 0)
    offset_mode = settings.get("offset_mode", constants.OFFSET_NONE)
    center = bool(settings.get("center_layout"))
    if offset_mode == constants.OFFSET_LINE:
        center_a = (item_count - 1) / 2.0 if center else 0.0
        return [(float(index) - center_a, 0.0) for index in range(item_count)]
    if offset_mode == constants.OFFSET_GRID:
        column_count = resolve_column_count(item_count, settings.get("grid_columns", 0))
        used_columns = min(column_count, max(1, item_count))
        row_count = int(math.ceil(item_count / float(column_count))) if item_count else 1
        center_a = (used_columns - 1) / 2.0 if center else 0.0
        center_b = (row_count - 1) / 2.0 if center else 0.0
        coefficients = []
        for index in range(item_count):
            row, column = get_grid_cell(index, column_count)
            coefficients.append((column - center_a, row - center_b))
        return coefficients
    return [(0.0, 0.0) for _ in range(item_count)]


def build_layout_vectors(settings, max_size=None):
    """Builds vector_a and vector_b of the layout.

    Args:
        settings (dict): Tool settings (offset_mode, line_step_*, grid_*, auto_spacing*).
        max_size (list, optional): Largest item bounding box size [x, y, z]. Required for auto spacing.

    Returns:
        tuple: (vector_a, vector_b) as [x, y, z] lists.
    """
    offset_mode = settings.get("offset_mode", constants.OFFSET_NONE)
    use_auto = bool(settings.get("auto_spacing")) and max_size is not None
    padding = float(settings.get("auto_spacing_padding") or 0.0)
    if offset_mode == constants.OFFSET_LINE:
        step = [settings.get("line_step_x", 0.0), settings.get("line_step_y", 0.0), settings.get("line_step_z", 0.0)]
        if use_auto:
            step = get_auto_line_step(step, max_size, padding)
        return _as_vector(step), [0.0, 0.0, 0.0]
    if offset_mode == constants.OFFSET_GRID:
        plane = settings.get("grid_plane", constants.GRID_PLANE_XZ)
        spacing_a = float(settings.get("grid_spacing_a") or 0.0)
        spacing_b = float(settings.get("grid_spacing_b") or 0.0)
        if use_auto:
            spacing_a, spacing_b = get_auto_grid_spacing(max_size, padding, plane)
        vector_b = [0.0, spacing_b, 0.0] if plane == constants.GRID_PLANE_XY else [0.0, 0.0, spacing_b]
        return [spacing_a, 0.0, 0.0], vector_b
    return [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]


def combine_offset(coefficients, vector_a, vector_b):
    """Computes coefficient_a * vector_a + coefficient_b * vector_b.

    Args:
        coefficients (tuple): (coefficient_a, coefficient_b).
        vector_a (list): Vector A [x, y, z].
        vector_b (list): Vector B [x, y, z].

    Returns:
        list: Offset [x, y, z].
    """
    coefficient_a, coefficient_b = coefficients
    return [coefficient_a * value_a + coefficient_b * value_b for value_a, value_b in zip(vector_a, vector_b)]


def build_layout_offsets(item_count, settings, max_size=None):
    """Builds the offset of every item for the layout described by the tool settings.

    Args:
        item_count (int): Number of items to place.
        settings (dict): Tool settings.
        max_size (list, optional): Largest item bounding box size [x, y, z]. Required for auto spacing.

    Returns:
        list: One offset [x, y, z] per item. All zeros when the offset mode is None.
    """
    vector_a, vector_b = build_layout_vectors(settings, max_size=max_size)
    return [combine_offset(coefficients, vector_a, vector_b)
            for coefficients in build_layout_coefficients(item_count, settings)]


def get_auto_grid_spacing(max_size, padding, plane=constants.GRID_PLANE_XZ):
    """Gets grid spacing that fits the largest item plus padding.

    Args:
        max_size (list): Largest bounding box size [x, y, z].
        padding (float): Extra distance between items.
        plane (str, optional): Grid plane.

    Returns:
        tuple: (column_spacing, row_spacing).
    """
    size = _as_vector(max_size)
    row_size = size[1] if plane == constants.GRID_PLANE_XY else size[2]
    return size[0] + float(padding), row_size + float(padding)


def get_auto_line_step(direction, max_size, padding):
    """Scales a line direction so items never overlap.

    The step length is the largest item extent along the direction, plus padding.

    Args:
        direction (list): Line direction [x, y, z]. Falls back to +X when zero.
        max_size (list): Largest bounding box size [x, y, z].
        padding (float): Extra distance between items.

    Returns:
        list: Step [x, y, z].
    """
    direction = _as_vector(direction)
    length = math.sqrt(sum(value * value for value in direction))
    if length <= 0:
        direction, length = [1.0, 0.0, 0.0], 1.0
    unit = [value / length for value in direction]
    size = _as_vector(max_size)
    extent = sum(abs(unit_value) * size_value for unit_value, size_value in zip(unit, size))
    step_length = extent + float(padding)
    return [value * step_length for value in unit]


def get_max_size(bounding_boxes):
    """Gets the largest size per axis from bounding boxes.

    Args:
        bounding_boxes (list): Boxes as [min_x, min_y, min_z, max_x, max_y, max_z]. Invalid entries are ignored.

    Returns:
        list: Largest size [x, y, z], or None when no box is valid.
    """
    sizes = []
    for box in bounding_boxes or []:
        if not is_valid_bounding_box(box):
            continue
        sizes.append([float(box[index + 3]) - float(box[index]) for index in range(3)])
    if not sizes:
        return None
    return [max(size[axis] for size in sizes) for axis in range(3)]


def is_valid_bounding_box(box, max_extent=1e18):
    """Checks whether a bounding box is usable.

    Maya returns an inverted box of +/-1e20 for nodes without geometry (for example joints).

    Args:
        box (list): Box as [min_x, min_y, min_z, max_x, max_y, max_z].
        max_extent (float, optional): Absolute values above this are treated as invalid.

    Returns:
        bool: True when the box has six values, min <= max on every axis, and finite extents.
    """
    if not box or len(box) != 6:
        return False
    try:
        values = [float(value) for value in box]
    except (TypeError, ValueError):
        return False
    if any(abs(value) >= max_extent for value in values):
        return False
    return all(values[index] <= values[index + 3] for index in range(3))


def build_control_attribute_name(file_index, suffix=""):
    """Builds the layout-control attribute name of one file.

    Args:
        file_index (int): One-based file index.
        suffix (str, optional): Attribute suffix such as "OffsetX". Empty for the file separator.

    Returns:
        str: Attribute name such as "file01" or "file01OffsetX".
    """
    return f"file{str(int(file_index)).zfill(2)}{suffix}"


def _as_vector(values):
    """Converts a value list to a 3-item float list.

    Args:
        values (list): Up to three numbers.

    Returns:
        list: [x, y, z] floats; missing items are zero.
    """
    vector = [float(value or 0.0) for value in list(values or [])[:3]]
    while len(vector) < 3:
        vector.append(0.0)
    return vector
