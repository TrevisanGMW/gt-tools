"""
Timeline Utilities - Frame ranges, key ranges and playback ranges.

Pure range helpers can be used outside Maya. Functions that touch the scene import Maya
only when they are called, so this module stays importable in plain Python.

Import Line:
    import gt.core.timeline as core_timeline
"""

import logging
import math
import os
import re

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

TIME_INPUT_ANIM_CURVE_TYPES = ["animCurveTA", "animCurveTL", "animCurveTT", "animCurveTU"]

ROUNDING_NONE = "none"
ROUNDING_OUTWARD = "outward"
ROUNDING_NEAREST = "nearest"

PLAYBACK_OPTIONS_PATTERN = re.compile(rb"playbackOptions\s+(?P<flags>(?:-[A-Za-z]+\s+[-+0-9.eE]+\s*)+)")
PLAYBACK_FLAG_PATTERN = re.compile(rb"-(?P<flag>[A-Za-z]+)\s+(?P<value>[-+0-9.eE]+)")
PLAYBACK_MIN_FLAGS = (b"min", b"minTime")
PLAYBACK_MAX_FLAGS = (b"max", b"maxTime")
PLAYBACK_SCAN_CHUNK_SIZE = 8 * 1024 * 1024
PLAYBACK_SCAN_OVERLAP = 512
MAYA_SCENE_EXTENSIONS = (".ma", ".mb")


# ------------------------------------------------------------------ pure helpers
def is_valid_time_range(time_range):
    """Checks whether a value is a usable (start, end) frame range.

    Args:
        time_range (object): Value to inspect.

    Returns:
        bool: True when the value has two numeric items with start <= end.
    """
    try:
        start_frame, end_frame = time_range
        return float(start_frame) <= float(end_frame)
    except (TypeError, ValueError):
        return False


def combine_time_ranges(time_ranges):
    """Combines several frame ranges into one covering range.

    Args:
        time_ranges (list): Iterable of (start, end) tuples. None entries are ignored.

    Returns:
        tuple: (start, end) covering every range, or None when no valid range exists.
    """
    valid_ranges = [time_range for time_range in (time_ranges or []) if is_valid_time_range(time_range)]
    if not valid_ranges:
        return None
    return (
        min(float(time_range[0]) for time_range in valid_ranges),
        max(float(time_range[1]) for time_range in valid_ranges),
    )


def round_time_range(time_range, rounding=ROUNDING_OUTWARD):
    """Rounds a frame range to whole frames.

    Args:
        time_range (tuple): (start, end) range.
        rounding (str, optional): ROUNDING_OUTWARD floors the start and ceils the end, so the
            range never loses frames. ROUNDING_NEAREST rounds both ends. ROUNDING_NONE keeps values.

    Returns:
        tuple: Rounded (start, end) range, or None when the input range is invalid.
    """
    if not is_valid_time_range(time_range):
        return None
    start_frame, end_frame = float(time_range[0]), float(time_range[1])
    if rounding == ROUNDING_OUTWARD:
        return float(math.floor(start_frame)), float(math.ceil(end_frame))
    if rounding == ROUNDING_NEAREST:
        return float(round(start_frame)), float(round(end_frame))
    return start_frame, end_frame


def get_sequential_offset(time_range, next_start, gap_frames=0):
    """Gets the offset for one clip placed after the previous clips.

    Args:
        time_range (tuple): Clip (start, end) range, or None when the clip has no keys.
        next_start (float): Frame where this clip should start, or None to keep the clip start.
        gap_frames (float, optional): Frames inserted after this clip.

    Returns:
        tuple: (offset, next_start) where next_start is the start frame for the following clip.
    """
    if not is_valid_time_range(time_range):
        return 0.0, next_start
    clip_start, clip_end = float(time_range[0]), float(time_range[1])
    if next_start is None:
        next_start = clip_start
    offset = float(next_start) - clip_start
    return offset, clip_end + offset + max(0.0, float(gap_frames or 0))


def build_sequential_offsets(time_ranges, gap_frames=0, start_frame=None):
    """Builds time offsets that place clips one after another.

    Clips without a valid range keep a zero offset and do not advance the timeline.

    Args:
        time_ranges (list): Per-clip (start, end) ranges, or None for clips without keys.
        gap_frames (float, optional): Frames inserted between consecutive clips.
        start_frame (float, optional): Frame where the first clip starts. Defaults to the first valid range start.

    Returns:
        list: Offset, in frames, for each clip in the same order as time_ranges.
    """
    offsets = []
    next_start = None if start_frame is None else float(start_frame)
    for time_range in time_ranges or []:
        offset, next_start = get_sequential_offset(time_range, next_start, gap_frames=gap_frames)
        offsets.append(offset)
    return offsets


def parse_playback_range_from_bytes(data):
    """Finds the last playbackOptions min/max values in Maya scene data.

    Args:
        data (bytes): Raw scene bytes from a .ma or .mb file.

    Returns:
        tuple: (start, end) range, or None when no playbackOptions command is present.
    """
    found_range = None
    for match in PLAYBACK_OPTIONS_PATTERN.finditer(data or b""):
        flag_values = {}
        for flag_match in PLAYBACK_FLAG_PATTERN.finditer(match.group("flags")):
            flag_values[flag_match.group("flag")] = flag_match.group("value")
        start_value = next((flag_values[flag] for flag in PLAYBACK_MIN_FLAGS if flag in flag_values), None)
        end_value = next((flag_values[flag] for flag in PLAYBACK_MAX_FLAGS if flag in flag_values), None)
        try:
            candidate_range = (float(start_value), float(end_value))
        except (TypeError, ValueError):
            continue
        if is_valid_time_range(candidate_range):
            found_range = candidate_range
    return found_range


def read_stored_playback_range(file_path):
    """Reads the playback range saved in a Maya scene without opening it in Maya.

    The scene configuration script node stores a playbackOptions command, usually near the end
    of the file. The tail is checked first; the whole file is scanned in chunks only when needed.

    Args:
        file_path (str): Path to a .ma or .mb file.

    Returns:
        tuple: (start, end) range, or None when the file is not a Maya scene or has no stored range.
    """
    if os.path.splitext(str(file_path or ""))[1].lower() not in MAYA_SCENE_EXTENSIONS:
        return None
    if not os.path.isfile(file_path):
        return None
    try:
        file_size = os.path.getsize(file_path)
        with open(file_path, "rb") as scene_file:
            tail_start = max(0, file_size - PLAYBACK_SCAN_CHUNK_SIZE)
            scene_file.seek(tail_start)
            found_range = parse_playback_range_from_bytes(scene_file.read())
            if found_range or tail_start == 0:
                return found_range
            scene_file.seek(0)
            previous_tail = b""
            while True:
                chunk = scene_file.read(PLAYBACK_SCAN_CHUNK_SIZE)
                if not chunk:
                    break
                chunk_range = parse_playback_range_from_bytes(previous_tail + chunk)
                if chunk_range:
                    found_range = chunk_range
                previous_tail = chunk[-PLAYBACK_SCAN_OVERLAP:]
            return found_range
    except (IOError, OSError):
        return None


# ------------------------------------------------------------------ Maya runtime helpers
def _get_maya_cmds():
    """Imports maya.cmds on demand.

    Returns:
        module: maya.cmds.
    """
    import maya.cmds as cmds

    return cmds


def get_time_anim_curves(nodes=None):
    """Gets time-driven animation curves, ignoring driven-key curves.

    Args:
        nodes (list, optional): Nodes to filter. When omitted, every curve in the scene is returned.

    Returns:
        list: Animation curve node names.
    """
    cmds = _get_maya_cmds()
    if nodes is None:
        return cmds.ls(type=TIME_INPUT_ANIM_CURVE_TYPES) or []
    existing_nodes = [node for node in nodes if cmds.objExists(node)]
    if not existing_nodes:
        return []
    return cmds.ls(existing_nodes, type=TIME_INPUT_ANIM_CURVE_TYPES) or []


def get_key_range(anim_curves=None):
    """Gets the frame range covered by time-driven animation curves.

    Uses OpenMaya to read only the first and last key of each curve, so the cost stays low
    even for scenes with many curves. Falls back to maya.cmds when OpenMaya is unavailable.

    Args:
        anim_curves (list, optional): Curves to inspect. When omitted, every time-driven curve is used.

    Returns:
        tuple: (start, end) frame range, or None when no keys exist.
    """
    if anim_curves is None:
        anim_curves = get_time_anim_curves()
    anim_curves = list(anim_curves or [])
    if not anim_curves:
        return None
    try:
        return _get_key_range_open_maya(anim_curves)
    except Exception as exception:
        logger.debug(f"OpenMaya key range failed, using maya.cmds: {exception}")
    return _get_key_range_cmds(anim_curves)


def _get_key_range_open_maya(anim_curves):
    """Gets the key range with OpenMaya.

    Args:
        anim_curves (list): Animation curve node names.

    Returns:
        tuple: (start, end) frame range, or None when no keys exist.
    """
    import maya.api.OpenMaya as open_maya
    import maya.api.OpenMayaAnim as open_maya_anim

    ui_unit = open_maya.MTime.uiUnit()
    selection_list = open_maya.MSelectionList()
    for curve_name in anim_curves:
        selection_list.add(curve_name)
    time_ranges = []
    for selection_index in range(selection_list.length()):
        curve_function = open_maya_anim.MFnAnimCurve(selection_list.getDependNode(selection_index))
        key_count = curve_function.numKeys
        if not key_count:
            continue
        time_ranges.append(
            (
                curve_function.input(0).asUnits(ui_unit),
                curve_function.input(key_count - 1).asUnits(ui_unit),
            )
        )
    return combine_time_ranges(time_ranges)


def _get_key_range_cmds(anim_curves):
    """Gets the key range with maya.cmds.

    Args:
        anim_curves (list): Animation curve node names.

    Returns:
        tuple: (start, end) frame range, or None when no keys exist.
    """
    cmds = _get_maya_cmds()
    first_key = cmds.findKeyframe(anim_curves, which="first")
    last_key = cmds.findKeyframe(anim_curves, which="last")
    return combine_time_ranges([(first_key, last_key)])


def get_playback_range():
    """Gets the current scene playback range.

    Returns:
        tuple: (start, end) frame range.
    """
    cmds = _get_maya_cmds()
    return (
        cmds.playbackOptions(query=True, minTime=True),
        cmds.playbackOptions(query=True, maxTime=True),
    )


def set_playback_range(time_range, set_current_time=True):
    """Sets the playback and animation range.

    Args:
        time_range (tuple): (start, end) frame range.
        set_current_time (bool, optional): Move the current time to the range start.
    """
    cmds = _get_maya_cmds()
    start_frame, end_frame = float(time_range[0]), float(time_range[1])
    cmds.playbackOptions(
        animationStartTime=start_frame,
        animationEndTime=end_frame,
        minTime=start_frame,
        maxTime=end_frame,
    )
    if set_current_time:
        cmds.currentTime(start_frame, edit=True)


def offset_animation(anim_curves, offset):
    """Shifts every key on the requested curves.

    Args:
        anim_curves (list): Animation curves to shift.
        offset (float): Frame offset.
    """
    if not anim_curves or not offset:
        return
    cmds = _get_maya_cmds()
    cmds.keyframe(anim_curves, edit=True, relative=True, timeChange=float(offset), option="over")
