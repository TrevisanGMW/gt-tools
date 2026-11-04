"""
Batch Processor Merge Input Helpers

Pure Python helpers used by the Merge Input task. This module must stay importable
outside Maya, so it never imports maya.cmds or OpenMaya.
"""

import os
import re


LOAD_MODE_IMPORT = "Import"
LOAD_MODE_REFERENCE = "Reference"
LOAD_MODES = [LOAD_MODE_IMPORT, LOAD_MODE_REFERENCE]

TIME_RANGE_KEYFRAMES = "Keyframes (All Inputs)"
TIME_RANGE_FIRST_INPUT = "First Input"
TIME_RANGE_MANUAL = "Manual"
TIME_RANGE_KEEP = "Keep Scene Range"
TIME_RANGE_MODES = [TIME_RANGE_KEYFRAMES, TIME_RANGE_FIRST_INPUT, TIME_RANGE_MANUAL, TIME_RANGE_KEEP]

TIMING_ORIGINAL = "Original Time"
TIMING_SEQUENTIAL = "Sequential"
TIMING_MODES = [TIMING_ORIGINAL, TIMING_SEQUENTIAL]

FAILURE_SKIP = "Skip Input"
FAILURE_STOP = "Fail Merge"
FAILURE_POLICIES = [FAILURE_SKIP, FAILURE_STOP]

INPUT_NAME_TOKEN = "{input-name}"
INPUT_INDEX_TOKEN = "{input-index}"
INPUT_INDEX_PADDED_TOKEN = "{input-index-padded}"
INPUT_TOKENS = [INPUT_NAME_TOKEN, INPUT_INDEX_TOKEN, INPUT_INDEX_PADDED_TOKEN]

PLAYBACK_OPTIONS_PATTERN = re.compile(
    rb"playbackOptions\s+(?P<flags>(?:-[A-Za-z]+\s+[-+0-9.eE]+\s*)+)"
)
PLAYBACK_FLAG_PATTERN = re.compile(rb"-(?P<flag>[A-Za-z]+)\s+(?P<value>[-+0-9.eE]+)")
PLAYBACK_MIN_FLAGS = (b"min", b"minTime")
PLAYBACK_MAX_FLAGS = (b"max", b"maxTime")
PLAYBACK_SCAN_CHUNK_SIZE = 8 * 1024 * 1024
PLAYBACK_SCAN_OVERLAP = 512


def sanitize_maya_name(raw_name, fallback_name="input"):
    """Builds a Maya-safe node or namespace name.

    Args:
        raw_name (str): Requested name.
        fallback_name (str, optional): Name used when the cleaned name is empty.

    Returns:
        str: Name containing only letters, digits, and underscores, never starting with a digit.
    """
    cleaned_name = re.sub(r"[^A-Za-z0-9_]+", "_", str(raw_name or "")).strip("_")
    cleaned_name = re.sub(r"_+", "_", cleaned_name)
    if not cleaned_name:
        cleaned_name = re.sub(r"[^A-Za-z0-9_]+", "_", str(fallback_name or "input")).strip("_") or "input"
    if cleaned_name[0].isdigit():
        cleaned_name = f"_{cleaned_name}"
    return cleaned_name


def get_input_name(file_path):
    """Gets the display name of an input file without its extension.

    Args:
        file_path (str): Input file path.

    Returns:
        str: File base name without extension.
    """
    return os.path.splitext(os.path.basename(str(file_path or "")))[0]


def resolve_input_tokens(template, file_path, input_index, total_inputs):
    """Replaces Merge Input per-input tokens in a name template.

    Args:
        template (str): Template using {input-name}, {input-index}, or {input-index-padded}.
        file_path (str): Input file path.
        input_index (int): One-based input index.
        total_inputs (int): Number of inputs being merged.

    Returns:
        str: Template with input tokens replaced.
    """
    padding = max(2, len(str(max(1, int(total_inputs or 1)))))
    resolved_text = str(template or "")
    resolved_text = resolved_text.replace(INPUT_NAME_TOKEN, get_input_name(file_path))
    resolved_text = resolved_text.replace(INPUT_INDEX_PADDED_TOKEN, str(int(input_index)).zfill(padding))
    resolved_text = resolved_text.replace(INPUT_INDEX_TOKEN, str(int(input_index)))
    return resolved_text


def build_unique_name(base_name, used_names):
    """Builds a name that is not present in a set of used names.

    Args:
        base_name (str): Preferred name.
        used_names (set): Names already taken. The returned name is added to this set.

    Returns:
        str: Unique name, numbered when the preferred name is taken.
    """
    candidate_name = base_name
    suffix_number = 1
    lowered_names = set(name.lower() for name in used_names)
    while candidate_name.lower() in lowered_names:
        candidate_name = f"{base_name}_{suffix_number}"
        suffix_number += 1
    used_names.add(candidate_name)
    return candidate_name


def sort_input_paths(file_paths, sort_by_name=True):
    """Orders input paths deterministically.

    Args:
        file_paths (list): Input file paths.
        sort_by_name (bool, optional): Sort by case-insensitive path when True, keep incoming order otherwise.

    Returns:
        list: Ordered paths.
    """
    file_paths = list(file_paths or [])
    if not sort_by_name:
        return file_paths
    return sorted(file_paths, key=lambda path: os.path.normcase(os.path.normpath(str(path))))


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


def build_sequential_offsets(time_ranges, gap_frames=0, start_frame=None):
    """Builds time offsets that place clips one after another.

    Inputs without a valid range keep a zero offset and do not advance the timeline.

    Args:
        time_ranges (list): Per-input (start, end) ranges, or None for inputs without keys.
        gap_frames (float, optional): Frames inserted between consecutive clips.
        start_frame (float, optional): Frame where the first clip starts. Defaults to the first valid range start.

    Returns:
        list: Offset, in frames, for each input in the same order as time_ranges.
    """
    offsets = []
    next_start = None if start_frame is None else float(start_frame)
    for time_range in time_ranges or []:
        offset, next_start = get_sequential_offset(time_range, next_start, gap_frames=gap_frames)
        offsets.append(offset)
    return offsets


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


def build_spatial_offset(input_index, spacing):
    """Builds the translation applied to one input when spreading inputs apart.

    Args:
        input_index (int): One-based input index.
        spacing (list): Per-input translation step as [x, y, z].

    Returns:
        list: Translation [x, y, z] for this input. The first input stays at the origin.
    """
    step_values = list(spacing or [0, 0, 0])[:3]
    while len(step_values) < 3:
        step_values.append(0.0)
    multiplier = max(0, int(input_index) - 1)
    return [float(value) * multiplier for value in step_values]


def resolve_time_range(mode, keyframe_range=None, first_input_range=None, manual_range=None):
    """Resolves the final playback range for a merged scene.

    Args:
        mode (str): One of TIME_RANGE_MODES.
        keyframe_range (tuple, optional): Range covering all time-based keys in the merged scene.
        first_input_range (tuple, optional): Range stored in, or keyed by, the first input.
        manual_range (tuple, optional): User-defined range.

    Returns:
        tuple: (start, end) range, or None when the scene range should not change.
    """
    candidates = {
        TIME_RANGE_KEYFRAMES: keyframe_range,
        TIME_RANGE_FIRST_INPUT: first_input_range,
        TIME_RANGE_MANUAL: manual_range,
    }
    time_range = candidates.get(mode)
    if not is_valid_time_range(time_range):
        return None
    return float(time_range[0]), float(time_range[1])


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
    if os.path.splitext(str(file_path or ""))[1].lower() not in [".ma", ".mb"]:
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


def build_input_record(file_path, input_index, load_mode):
    """Builds the per-input result dictionary shared with scripts and logs.

    Args:
        file_path (str): Input file path.
        input_index (int): One-based input index.
        load_mode (str): Import or Reference.

    Returns:
        dict: Record with default values filled in by the merge runtime.
    """
    return {
        "path": file_path,
        "name": get_input_name(file_path),
        "index": int(input_index),
        "load_mode": load_mode,
        "status": "pending",
        "namespace": "",
        "nodes": [],
        "root_nodes": [],
        "reference_node": "",
        "group": "",
        "display_layer": "",
        "time_range": None,
        "time_offset": 0.0,
        "message": "",
    }
