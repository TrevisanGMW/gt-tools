"""
NumPy Utilities - Helpers for NumPy data, such as building animated locators from position arrays.

Useful to review generated or captured point data (for example joint positions) next to other files.
NumPy and Maya are imported only inside the functions that need them.

Import Line:
    import gt.utils.numpy as utils_numpy
"""

import gt.utils.bvh as utils_bvh
import logging
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

CENTIMETERS_PER_SOURCE_UNIT = {"m": 100.0, "cm": 1.0, "mm": 0.1}


def is_numpy_available():
    """Checks whether NumPy can be imported.

    Returns:
        bool: True when NumPy is available.
    """
    try:
        import numpy  # noqa: F401
    except ImportError:
        return False
    return True


def normalize_point_samples(array):
    """Converts an array of positions to shape (frames, points, 3).

    Accepted shapes: (frames, points, 3), (frames, 3) for a single point, and (frames, points * 3).

    Args:
        array (numpy.ndarray): Position data.

    Returns:
        numpy.ndarray: Array of shape (frames, points, 3).

    Raises:
        ValueError: When the shape cannot be interpreted as positions.
    """
    shape = tuple(array.shape)
    if len(shape) == 3 and shape[2] == 3:
        return array
    if len(shape) == 2 and shape[1] == 3:
        return array.reshape(shape[0], 1, 3)
    if len(shape) == 2 and shape[1] % 3 == 0 and shape[1] > 0:
        return array.reshape(shape[0], shape[1] // 3, 3)
    raise ValueError(f"Expected positions shaped (frames, points, 3), (frames, 3) or (frames, points*3); got {shape}.")


def build_point_names(point_count, prefix="point"):
    """Builds zero-padded point names.

    Args:
        point_count (int): Number of points.
        prefix (str, optional): Name prefix.

    Returns:
        list: Names such as "point_00", "point_01".
    """
    padding = max(2, len(str(max(0, int(point_count) - 1))))
    return [f"{prefix}_{str(index).zfill(padding)}" for index in range(int(point_count))]


def read_point_array(file_path, array_key="posed_joints"):
    """Loads position data from a .npy or .npz file.

    Args:
        file_path (str): Array path.
        array_key (str, optional): Array name inside .npz archives.

    Returns:
        numpy.ndarray: Positions shaped (frames, points, 3).

    Raises:
        KeyError: When the .npz archive has no array with that name.
    """
    import numpy

    if file_path.lower().endswith(".npz"):
        with numpy.load(file_path, allow_pickle=False) as archive:
            if array_key not in archive.files:
                raise KeyError(f'Array "{array_key}" not found. Available arrays: {", ".join(archive.files)}')
            array = archive[array_key]
    else:
        array = numpy.load(file_path, allow_pickle=False)
    return normalize_point_samples(numpy.asarray(array, dtype=float))


def import_point_array_file(
    file_path,
    namespace="",
    array_key="posed_joints",
    fps=30.0,
    source_unit="m",
    source_up_axis="y",
    start_frame=1.0,
    time_mode=utils_bvh.TIME_MODE_REAL_TIME,
    locator_scale=2.0,
):
    """Creates one animated locator per point stored in a NumPy file.

    Args:
        file_path (str): .npy or .npz path.
        namespace (str, optional): Namespace for the new nodes.
        array_key (str, optional): Array name inside .npz archives.
        fps (float, optional): Samples per second stored in the array.
        source_unit (str, optional): Unit of the stored positions ("m", "cm" or "mm").
        source_up_axis (str, optional): Up axis of the stored positions ("y" or "z").
        start_frame (float, optional): Timeline frame of the first sample.
        time_mode (str, optional): utils_bvh.TIME_MODE_REAL_TIME or TIME_MODE_FRAME_PER_FRAME.
        locator_scale (float, optional): Locator display size.

    Returns:
        dict: {"root": str, "time_range": tuple or None}.
    """
    import maya.cmds as cmds
    import maya.api.OpenMaya as open_maya
    import gt.core.anim as core_anim
    import gt.core.namespace as core_nspace
    import gt.core.str as core_str

    positions = read_point_array(file_path, array_key)
    centimeters = CENTIMETERS_PER_SOURCE_UNIT.get(source_unit, 100.0)
    scale = open_maya.MDistance(centimeters, open_maya.MDistance.kCentimeters).asUnits(open_maya.MDistance.uiUnit())
    scene_fps = open_maya.MTime(1.0, open_maya.MTime.kSeconds).asUnits(open_maya.MTime.uiUnit())
    frames = utils_bvh.build_frame_times(positions.shape[0], 1.0 / float(fps), scene_fps, start_frame, time_mode)
    base_name = core_str.sanitize_maya_name(os.path.splitext(os.path.basename(file_path))[0], "points")
    with core_nspace.NamespaceContext(namespace):
        points_group = cmds.createNode("transform", name=f"{base_name}_points", skipSelect=True)
        for point_index, point_name in enumerate(build_point_names(positions.shape[1])):
            locator = cmds.parent(cmds.spaceLocator(name=point_name)[0], points_group)[0]
            cmds.setAttr(f"{locator}.localScale", locator_scale, locator_scale, locator_scale)
            for axis_index, axis in enumerate("XYZ"):
                values = (positions[:, point_index, axis_index] * scale).tolist()
                core_anim.create_keyed_curve(f"{locator}.translate{axis}", frames, values)
    scene_up_axis = cmds.upAxis(query=True, axis=True)
    if str(source_up_axis).lower() == "y" and scene_up_axis == "z":
        cmds.setAttr(f"{points_group}.rotateX", 90)
    elif str(source_up_axis).lower() == "z" and scene_up_axis == "y":
        cmds.setAttr(f"{points_group}.rotateX", -90)
    return {
        "root": (cmds.ls(points_group, long=True) or [points_group])[0],
        "time_range": (frames[0], frames[-1]) if frames else None,
    }
