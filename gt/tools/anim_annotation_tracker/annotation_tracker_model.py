"""Model and persistence helpers for Annotation Tracker."""

import copy
import os
import shutil
import uuid

from gt.core.prefs import Prefs


PREFS_FILENAME = "anim_annotation_tracker"
LAST_USED_DATA_KEY = "last_used_data"
AUTOMATION_CHECK_STATES_KEY = "automation_check_states"
AUTOMATION_CHECK_STATES_PATH_KEY = "automation_check_states_path"
TOOL_MODE_PREFERENCE_KEY = "tool_mode"
DEFAULT_TOOL_MODE = "edit"
VALID_TOOL_MODES = ("navigate", "select", "edit", "razor")
SCENE_DATA_NODE_NAME = "animAnnotationData"
SCENE_DATA_ATTRIBUTE = "annotationData"
SCENE_LAST_EDITED_ATTRIBUTE = "lastEdited"
RESERVED_RANGE_CUSTOM_DATA_KEYS = (
    "name",
    "start_frame",
    "end_frame",
)
# Base hues are ordered before their lighter variants to maximize variation.
DEFAULT_SCRIPTED_RANGE_COLORS = (
    (31, 119, 180),
    (255, 127, 14),
    (44, 160, 44),
    (214, 39, 40),
    (148, 103, 189),
    (140, 86, 75),
    (227, 119, 194),
    (127, 127, 127),
    (188, 189, 34),
    (23, 190, 207),
    (174, 199, 232),
    (255, 187, 120),
    (152, 223, 138),
    (255, 152, 150),
    (197, 176, 213),
    (196, 156, 148),
    (247, 182, 210),
    (199, 199, 199),
    (219, 219, 141),
    (158, 218, 229),
)
SCRIPTED_RANGE_BASE_KEYS = {
    "id",
    "name",
    "start",
    "end",
    "start_frame",
    "end_frame",
    "color",
    "locked",
    "custom_data",
}

DEFAULT_PREFERENCES = {
    "schema_path": "",
    "automation_path": "",
    AUTOMATION_CHECK_STATES_KEY: {},
    AUTOMATION_CHECK_STATES_PATH_KEY: "",
    "magnet_enabled": True,
    "snap_threshold": 10,
    "auto_crop": False,
    "crop_tolerance": 50,
    "auto_stretch": False,
    "stretch_tolerance": 50,
    "show_timeline": True,
    "show_frames": True,
    "show_names": False,
    "random_colors": True,
    "sync_time": True,
    "limit_bounds": True,
    "razor_random_colors": True,
    "run_all_automations": True,
    "hide_private_automations": True,
    "show_validation_status": True,
    "write_scene_node": True,
    TOOL_MODE_PREFERENCE_KEY: DEFAULT_TOOL_MODE,
    LAST_USED_DATA_KEY: {},
}


def get_sample_directory():
    """Gets the packaged sample directory.

    Returns:
        str: Absolute sample directory path.
    """
    return os.path.join(os.path.dirname(__file__), "samples")


def get_sample_schema_directory():
    """Gets the packaged sample schema directory.

    Returns:
        str: Absolute sample schema directory path.
    """
    return os.path.join(get_sample_directory(), "schema")


def get_sample_schema_path():
    """Gets the packaged sample schema path.

    Returns:
        str: Absolute JSON schema path.
    """
    return os.path.join(get_sample_schema_directory(), "schema.json")


def copy_sample_schema(destination_path):
    """Copies the packaged sample schema to a destination file.

    Args:
        destination_path (str): File path where the schema should be copied.

    Returns:
        str: Normalized destination file path.

    Raises:
        ValueError: If the destination path is empty.
        OSError: If the packaged schema cannot be copied.
    """
    destination_path = str(destination_path or "").strip(' "\'')
    if not destination_path:
        raise ValueError("A destination schema path is required.")

    source_path = os.path.abspath(get_sample_schema_path())
    destination_path = os.path.abspath(destination_path)
    if os.path.normcase(source_path) != os.path.normcase(destination_path):
        shutil.copyfile(source_path, destination_path)
    return destination_path


def get_sample_automation_directory():
    """Gets the packaged sample automation directory.

    Returns:
        str: Absolute sample automation directory path.
    """
    return os.path.join(get_sample_directory(), "automations")


def get_sample_automation_path():
    """Gets the packaged sample automation path.

    Returns:
        str: Absolute Python automation path.
    """
    return os.path.join(get_sample_automation_directory(), "automation.py")


def get_sample_automation_paths():
    """Gets the packaged sample automation scripts in display order.

    Returns:
        list: Absolute Python sample automation paths.
    """
    automation_directory = get_sample_automation_directory()
    return sorted(
        [
            os.path.join(automation_directory, file_name)
            for file_name in os.listdir(automation_directory)
            if file_name.endswith(".py")
        ]
    )


def copy_sample_automation_scripts(destination_directory):
    """Copies packaged sample automation scripts without overwriting files.

    Args:
        destination_directory (str): Existing or new destination folder.

    Returns:
        tuple: Lists of copied and skipped destination file paths.
    """
    destination_directory = str(destination_directory or "").strip(' "\'')
    if not destination_directory:
        return [], []
    os.makedirs(destination_directory, exist_ok=True)
    copied_paths = []
    skipped_paths = []
    for source_path in get_sample_automation_paths():
        destination_path = os.path.join(
            destination_directory,
            os.path.basename(source_path),
        )
        if os.path.exists(destination_path):
            skipped_paths.append(destination_path)
            continue
        shutil.copyfile(source_path, destination_path)
        copied_paths.append(destination_path)
    return copied_paths, skipped_paths


def is_private_automation_path(script_path):
    """Checks whether an automation script is private.

    Automation scripts whose file name starts with an underscore are
    treated as private and can be hidden from the Automations tab.

    Args:
        script_path (str): Automation file name or path.

    Returns:
        bool: True when the automation script is private.
    """
    return os.path.basename(str(script_path or "")).startswith("_")


def filter_private_automation_paths(script_paths):
    """Filters private automation scripts out of a path list.

    Args:
        script_paths (list): Automation file names or paths.

    Returns:
        list: Automation paths whose file names do not start with an
            underscore, preserving the incoming order.
    """
    return [
        script_path
        for script_path in (script_paths or [])
        if not is_private_automation_path(script_path)
    ]


def get_default_preferences():
    """Builds default preferences without a pre-selected schema.

    Returns:
        dict: Default Annotation Tracker preferences.
    """
    return copy.deepcopy(DEFAULT_PREFERENCES)


def normalize_tool_mode(tool_mode):
    """Normalizes a stored timeline interaction mode.

    Args:
        tool_mode (object): Stored mode preference value.

    Returns:
        str: Valid interaction mode, defaulting to edit.
    """
    normalized_mode = str(tool_mode or "").strip().lower()
    if normalized_mode not in VALID_TOOL_MODES:
        return DEFAULT_TOOL_MODE
    return normalized_mode


def normalize_automation_path(automation_path):
    """Normalizes an automation folder path for preference comparisons.

    Args:
        automation_path (str): Automation folder path supplied by the user.

    Returns:
        str: Normalized automation folder path, or an empty string.
    """
    if not automation_path:
        return ""
    return os.path.normcase(os.path.normpath(str(automation_path).strip(' "\'')))


def flatten_schema_items(schema_items):
    """Flattens schema rows into editable field definitions.

    Args:
        schema_items (list): Schema items, including rows and separators.

    Returns:
        list: Field definitions in display order.
    """
    flattened_items = []
    for item in schema_items or []:
        if item.get("type") == "row":
            flattened_items.extend(flatten_schema_items(item.get("items", [])))
        elif item.get("type") != "separator":
            flattened_items.append(item)
    return flattened_items


def get_schema_field_names(schema):
    """Gets the editable field names for each schema data section.

    Args:
        schema (dict): Schema definition to inspect.

    Returns:
        dict: File and range data field names stored as sets.
    """
    field_definitions = _get_schema_field_definitions(schema)
    return {
        "file_data": set(field_definitions["file_data"]),
        "range_data": set(field_definitions["range_data"]),
    }


def _get_schema_field_definitions(schema):
    """Gets schema field definitions grouped by data section.

    Args:
        schema (dict): Schema definition to inspect.

    Returns:
        dict: File and range field definitions keyed by field name.
    """
    schema = schema if isinstance(schema, dict) else {}
    field_definitions = {}
    for data_key, schema_key in (
        ("file_data", "file_level"),
        ("range_data", "frame_range"),
    ):
        field_definitions[data_key] = {
            item.get("name"): item
            for item in flatten_schema_items(schema.get(schema_key, []))
            if item.get("name")
        }
    return field_definitions


def get_ordered_schema_data(schema, data, data_key):
    """Orders data to match the visible schema field order.

    Recognized schema fields are emitted first in the order in which they
    appear in the UI. Unknown fields are retained afterwards in their original
    order so data from a newer or missing schema is not silently discarded.

    Args:
        schema (dict): Schema definition that defines UI field order.
        data (dict): File or frame-range metadata to order.
        data_key (str): Data section, either ``file_data`` or ``range_data``.

    Returns:
        dict: Deep-copied metadata in schema/UI order.
    """
    data = data if isinstance(data, dict) else {}
    field_definitions = _get_schema_field_definitions(schema).get(data_key, {})
    ordered_data = {
        field_name: copy.deepcopy(data[field_name])
        for field_name in field_definitions
        if field_name in data
    }
    ordered_data.update(
        {
            field_name: copy.deepcopy(value)
            for field_name, value in data.items()
            if field_name not in ordered_data
        }
    )
    return ordered_data


def get_reserved_range_field_names(schema):
    """Gets frame-range schema names that collide with exported base fields.

    Args:
        schema (dict): Schema definition to inspect.

    Returns:
        list: Reserved field names in their UI order.
    """
    schema = schema if isinstance(schema, dict) else {}
    return [
        item.get("name")
        for item in flatten_schema_items(
            schema.get("frame_range", [])
        )
        if item.get("name") in RESERVED_RANGE_CUSTOM_DATA_KEYS
    ]


def _is_schema_value_supported(field_definition, value):
    """Checks whether a value is representable by its schema field.

    Args:
        field_definition (dict or None): Schema definition for the value.
        value (object): Stored value to inspect.

    Returns:
        bool: True when the replacement schema can retain the value.
    """
    if not isinstance(field_definition, dict):
        return False
    if value in (None, "", "---"):
        return True
    if field_definition.get("type") != "enum":
        return True
    options = field_definition.get("options", [])
    return str(value) in [str(option) for option in options]


def filter_schema_data(schema, data, data_key):
    """Filters values that cannot be retained by a schema data section.

    Args:
        schema (dict): Replacement schema definition.
        data (dict): Current file or range data values.
        data_key (str): Data section, either ``file_data`` or ``range_data``.

    Returns:
        dict: Compatible values copied from the source data.
    """
    data = data if isinstance(data, dict) else {}
    field_definitions = _get_schema_field_definitions(schema).get(data_key, {})
    return {
        name: copy.deepcopy(value)
        for name, value in data.items()
        if _is_schema_value_supported(field_definitions.get(name), value)
    }


def get_schema_data_loss(schema, file_data, ranges):
    """Finds saved values that a replacement schema would discard.

    Args:
        schema (dict): Replacement schema definition.
        file_data (dict): Current file-level values.
        ranges (list): Current range objects or serialized range dictionaries.

    Returns:
        dict: Sorted removed field names for ``file_data`` and ``range_data``.
    """
    file_data = file_data if isinstance(file_data, dict) else {}
    compatible_file_data = filter_schema_data(schema, file_data, "file_data")
    file_data_loss = set(file_data.keys()) - set(compatible_file_data.keys())
    range_data_loss = set()

    for range_item in ranges or []:
        if isinstance(range_item, dict):
            custom_data = range_item.get("custom_data", {})
        else:
            custom_data = getattr(range_item, "custom_data", {})
        if isinstance(custom_data, dict):
            compatible_range_data = filter_schema_data(
                schema,
                custom_data,
                "range_data",
            )
            range_data_loss.update(
                set(custom_data.keys()) - set(compatible_range_data.keys())
            )

    return {
        "file_data": sorted(file_data_loss),
        "range_data": sorted(range_data_loss),
    }


def _get_scripted_range_value(range_item, field_name, default=None):
    """Gets a field from a scripted range dictionary or object.

    Args:
        range_item (dict or object): Range definition supplied by a script.
        field_name (str): Field name to retrieve.
        default (object, optional): Value returned when the field is absent.

    Returns:
        object: Stored field value or the provided default.
    """
    if isinstance(range_item, dict):
        return range_item.get(field_name, default)
    return getattr(range_item, field_name, default)


def _normalize_scripted_range_color(color, range_index):
    """Normalizes a scripted range display color.

    Args:
        color (list or tuple): Optional RGB display color.
        range_index (int): Range index used to select a default color.

    Returns:
        list: Three integer RGB channel values clamped from 0 to 255.

    Raises:
        ValueError: If an explicit color does not contain three channels.
    """
    if color is None:
        color = DEFAULT_SCRIPTED_RANGE_COLORS[
            range_index % len(DEFAULT_SCRIPTED_RANGE_COLORS)
        ]
    if not isinstance(color, (list, tuple)) or len(color) != 3:
        raise ValueError("Range color must contain exactly three RGB values.")
    return [max(0, min(255, int(channel))) for channel in color]


def build_scene_payload(file_data, ranges):
    """Builds the tracker payload used by scripted scene integrations.

    Ranges can use the tracker's internal ``start``, ``end``, and
    ``custom_data`` layout or the public flattened ``start_frame`` and
    ``end_frame`` layout returned by :func:`build_annotation_data`. Unknown
    top-level dictionary keys are treated as custom frame-range metadata.

    Args:
        file_data (dict): File-level annotation metadata.
        ranges (list): Ordered range dictionaries or range-like objects.

    Returns:
        dict: JSON-compatible tracker scene payload.

    Raises:
        TypeError: If file or custom range metadata is not a dictionary.
        ValueError: If a range is missing bounds or has inverted bounds.
    """
    if not isinstance(file_data, dict):
        raise TypeError("File annotation data must be a dictionary.")

    normalized_ranges = []
    for range_index, range_item in enumerate(ranges or []):
        start_frame = _get_scripted_range_value(range_item, "start")
        if start_frame is None:
            start_frame = _get_scripted_range_value(range_item, "start_frame")
        end_frame = _get_scripted_range_value(range_item, "end")
        if end_frame is None:
            end_frame = _get_scripted_range_value(range_item, "end_frame")
        if start_frame is None or end_frame is None:
            raise ValueError(
                f"Range at index {range_index} is missing start or end bounds."
            )

        start_frame = int(start_frame)
        end_frame = int(end_frame)
        if end_frame < start_frame:
            raise ValueError(
                f"Range at index {range_index} ends before it starts."
            )

        custom_data = _get_scripted_range_value(
            range_item,
            "custom_data",
            {},
        )
        if custom_data is None:
            custom_data = {}
        if not isinstance(custom_data, dict):
            raise TypeError(
                f"Range at index {range_index} custom data must be a dictionary."
            )
        if isinstance(range_item, dict):
            flattened_custom_data = {
                key: copy.deepcopy(value)
                for key, value in range_item.items()
                if key not in SCRIPTED_RANGE_BASE_KEYS
            }
            flattened_custom_data.update(copy.deepcopy(custom_data))
            custom_data = flattened_custom_data
        else:
            custom_data = copy.deepcopy(custom_data)

        range_id = _get_scripted_range_value(range_item, "id")
        color = _normalize_scripted_range_color(
            _get_scripted_range_value(range_item, "color"),
            range_index,
        )
        normalized_ranges.append(
            {
                "id": str(range_id or uuid.uuid4()),
                "name": str(
                    _get_scripted_range_value(range_item, "name", "") or ""
                ),
                "start": start_frame,
                "end": end_frame,
                "color": color,
                "locked": bool(
                    _get_scripted_range_value(range_item, "locked", False)
                ),
                "custom_data": custom_data,
            }
        )

    normalized_ranges.sort(
        key=lambda item: (item["start"], item["end"], item["name"])
    )
    return {
        "range_data": normalized_ranges,
        "file_data": copy.deepcopy(file_data),
    }


def build_annotation_data(payload, schema=None):
    """Builds USD customData-compatible metadata from tracker scene data.

    The result deliberately omits tracker implementation fields, such as range
    identifiers, display colors, and lock states. Range data is stored in a
    dictionary rather than a list so the result can be supplied directly to a
    USD prim's ``customData`` without requiring an array of dictionaries.
    Frame-range metadata is flattened alongside the base range fields. When a
    schema is provided, file and frame-range metadata follow its visible UI
    order.

    Args:
        payload (dict): Serialized Annotation Tracker scene payload.
        schema (dict, optional): Active schema used to order metadata fields.

    Returns:
        dict: File and per-range user annotation data.
    """
    payload = payload if isinstance(payload, dict) else {}
    file_data = payload.get("file_data", {})
    range_data = payload.get("range_data", [])
    custom_data = {
        "file_data": get_ordered_schema_data(schema, file_data, "file_data"),
        "range_data": {},
    }

    if not isinstance(range_data, list):
        return custom_data

    range_key_width = max(3, len(str(len(range_data))))
    for index, range_item in enumerate(range_data):
        if not isinstance(range_item, dict):
            continue
        range_metadata = range_item.get("custom_data", {})
        range_custom_data = {
            "name": str(range_item.get("name", "")),
            "start_frame": range_item.get("start", 0),
            "end_frame": range_item.get("end", 0),
        }
        ordered_metadata = get_ordered_schema_data(
            schema,
            range_metadata,
            "range_data",
        )
        range_custom_data.update(
            {
                field_name: value
                for field_name, value in ordered_metadata.items()
                if field_name not in RESERVED_RANGE_CUSTOM_DATA_KEYS
            }
        )
        custom_data["range_data"][
            f"range_{index:0{range_key_width}d}"
        ] = range_custom_data
    return custom_data


def build_usd_custom_data(payload, schema=None):
    """Builds annotation data with the previous USD helper name.

    This compatibility wrapper preserves existing scripts that used the former
    function name. New integrations should use ``build_annotation_data``.

    Args:
        payload (dict): Serialized Annotation Tracker scene payload.
        schema (dict, optional): Active schema used to order metadata fields.

    Returns:
        dict: File and per-range user annotation data.
    """
    return build_annotation_data(payload, schema=schema)


def _is_missing_value(value):
    """Checks whether a schema value should be treated as missing.

    Args:
        value (object): Value to inspect.

    Returns:
        bool: True when the value is empty.
    """
    return value is None or value == "" or value == "---"


def adjust_adjacent_ranges(
    active_range,
    ranges,
    auto_crop=False,
    crop_tolerance=0,
    auto_stretch=False,
    stretch_tolerance=0,
):
    """Adjusts unlocked ranges adjacent to an edited range.

    Cropping resolves overlaps by moving the adjacent boundary away from the
    active range. Stretching resolves gaps by extending an adjacent range to
    the active range boundary. Each operation is limited by its tolerance.

    Args:
        active_range (object): Range currently being edited.
        ranges (list): All timeline ranges.
        auto_crop (bool): Whether nearby overlaps should be cropped.
        crop_tolerance (int): Maximum overlap corrected by cropping.
        auto_stretch (bool): Whether nearby gaps should be stretched closed.
        stretch_tolerance (int): Maximum gap corrected by stretching.

    Returns:
        list: Ranges changed by the adjustment.
    """
    if not active_range:
        return []

    sorted_ranges = sorted(ranges or [], key=lambda item: item.start)
    try:
        active_index = sorted_ranges.index(active_range)
    except ValueError:
        return []

    previous_range = (
        sorted_ranges[active_index - 1] if active_index > 0 else None
    )
    next_range = (
        sorted_ranges[active_index + 1]
        if active_index < len(sorted_ranges) - 1
        else None
    )
    changed_ranges = []

    if auto_crop and previous_range and not previous_range.locked:
        overlap = previous_range.end - active_range.start + 1
        new_end = active_range.start - 1
        if 0 < overlap <= max(0, int(crop_tolerance)):
            if new_end >= previous_range.start and previous_range.end != new_end:
                previous_range.end = new_end
                changed_ranges.append(previous_range)

    if auto_crop and next_range and not next_range.locked:
        overlap = active_range.end - next_range.start + 1
        new_start = active_range.end + 1
        if 0 < overlap <= max(0, int(crop_tolerance)):
            if new_start <= next_range.end and next_range.start != new_start:
                next_range.start = new_start
                changed_ranges.append(next_range)

    if auto_stretch and previous_range and not previous_range.locked:
        gap = active_range.start - previous_range.end - 1
        new_end = active_range.start - 1
        if 0 < gap <= max(0, int(stretch_tolerance)):
            if new_end >= previous_range.start and previous_range.end != new_end:
                previous_range.end = new_end
                changed_ranges.append(previous_range)

    if auto_stretch and next_range and not next_range.locked:
        gap = next_range.start - active_range.end - 1
        new_start = active_range.end + 1
        if 0 < gap <= max(0, int(stretch_tolerance)):
            if new_start <= next_range.end and next_range.start != new_start:
                next_range.start = new_start
                changed_ranges.append(next_range)

    return changed_ranges


def get_uncovered_frame_ranges(ranges, start_frame, end_frame):
    """Gets contiguous timeline spans that are not covered by ranges.

    Range bounds are treated as inclusive. Overlapping, adjacent, inverted, and
    out-of-bounds ranges are normalized before the uncovered spans are found.

    Args:
        ranges (list): Range-like objects with ``start`` and ``end`` values.
        start_frame (int): First frame of the timeline bounds.
        end_frame (int): Last frame of the timeline bounds.

    Returns:
        list: Ordered ``(start_frame, end_frame)`` tuples for uncovered spans.
    """
    timeline_start = min(int(start_frame), int(end_frame))
    timeline_end = max(int(start_frame), int(end_frame))
    covered_ranges = []
    for range_item in ranges or []:
        if range_item is None:
            continue
        range_start = getattr(range_item, "start", None)
        range_end = getattr(range_item, "end", None)
        if range_start is None or range_end is None:
            continue
        range_start = int(range_start)
        range_end = int(range_end)
        range_start, range_end = min(range_start, range_end), max(
            range_start,
            range_end,
        )
        if range_end < timeline_start or range_start > timeline_end:
            continue
        covered_ranges.append(
            (
                max(timeline_start, range_start),
                min(timeline_end, range_end),
            )
        )

    covered_ranges.sort()
    merged_ranges = []
    for range_start, range_end in covered_ranges:
        if not merged_ranges or range_start > merged_ranges[-1][1] + 1:
            merged_ranges.append([range_start, range_end])
        else:
            merged_ranges[-1][1] = max(merged_ranges[-1][1], range_end)

    uncovered_ranges = []
    next_frame = timeline_start
    for range_start, range_end in merged_ranges:
        if next_frame < range_start:
            uncovered_ranges.append((next_frame, range_start - 1))
        next_frame = max(next_frame, range_end + 1)
    if next_frame <= timeline_end:
        uncovered_ranges.append((next_frame, timeline_end))
    return uncovered_ranges


def get_uncovered_frame_range_at_frame(ranges, start_frame, end_frame, frame):
    """Gets the uncovered span that contains a frame.

    Args:
        ranges (list): Range-like objects with ``start`` and ``end`` values.
        start_frame (int): First frame of the timeline bounds.
        end_frame (int): Last frame of the timeline bounds.
        frame (int): Frame to inspect.

    Returns:
        tuple or None: Inclusive uncovered ``(start_frame, end_frame)`` span.
    """
    current_frame = int(frame)
    for range_start, range_end in get_uncovered_frame_ranges(
        ranges,
        start_frame,
        end_frame,
    ):
        if range_start <= current_frame <= range_end:
            return range_start, range_end
    return None


def collect_validation_errors(schema, ranges, file_data, start_frame, end_frame):
    """Collects all schema validation errors without touching Maya.

    Args:
        schema (dict): Loaded Annotation Tracker schema.
        ranges (list): RangeItem objects to validate.
        file_data (dict): File-level values.
        start_frame (int): Timeline start frame.
        end_frame (int): Timeline end frame.

    Returns:
        list: Human-readable validation errors.
    """
    if not schema:
        return ["No schema loaded."]

    errors = []
    validation_rules = schema.get("validation", {})
    ranges = list(ranges or [])
    file_data = file_data or {}

    if not validation_rules.get("allow_overlap", True):
        sorted_ranges = sorted(ranges, key=lambda item: item.start)
        for index in range(len(sorted_ranges) - 1):
            current_range = sorted_ranges[index]
            next_range = sorted_ranges[index + 1]
            if current_range.end > next_range.start:
                errors.append(
                    "Overlap detected between "
                    f"'{current_range.display_name}' and "
                    f"'{next_range.display_name}'"
                )

    if validation_rules.get("full_coverage", False):
        covered_frames = set()
        for range_item in ranges:
            covered_frames.update(range(range_item.start, range_item.end + 1))
        expected_frames = set(range(start_frame, end_frame + 1))
        missing_frames = expected_frames - covered_frames
        if missing_frames:
            errors.append(
                f"Timeline has {len(missing_frames)} uncovered frame(s)."
            )

    file_items = flatten_schema_items(schema.get("file_level", []))
    for item in file_items:
        value = file_data.get(item.get("name"))
        if item.get("required") and _is_missing_value(value):
            errors.append(f"File '{item.get('label', item.get('name'))}' is required.")

    range_items = flatten_schema_items(schema.get("frame_range", []))
    for range_item in ranges:
        for item in range_items:
            value = range_item.custom_data.get(item.get("name"))
            if item.get("required") and _is_missing_value(value):
                errors.append(
                    f"Range '{range_item.display_name}': "
                    f"'{item.get('label', item.get('name'))}' is required."
                )

    return errors


class AnnotationTrackerModel:
    """Stores persistent Annotation Tracker state."""

    def __init__(self):
        """Initializes the model and loads persistent preferences."""
        self.prefs = Prefs(PREFS_FILENAME)
        self.preferences = {}
        self.load_preferences()

    def load_preferences(self):
        """Loads preferences and fills missing keys with current defaults."""
        preferences = get_default_preferences()
        stored_preferences = self.prefs.get_raw_preferences()
        preferences.update(stored_preferences)
        preferences[TOOL_MODE_PREFERENCE_KEY] = normalize_tool_mode(
            preferences.get(TOOL_MODE_PREFERENCE_KEY)
        )
        if normalize_automation_path(preferences.get("automation_path")) == normalize_automation_path(
            get_sample_directory()
        ):
            preferences["automation_path"] = ""
            preferences[AUTOMATION_CHECK_STATES_KEY] = {}
            preferences[AUTOMATION_CHECK_STATES_PATH_KEY] = ""
        self.preferences = preferences
        return copy.deepcopy(self.preferences)

    def save_preferences(self):
        """Writes all current preferences to the package preferences file."""
        preferences = copy.deepcopy(self.preferences)
        tool_mode = normalize_tool_mode(
            preferences.get(TOOL_MODE_PREFERENCE_KEY)
        )
        self.preferences[TOOL_MODE_PREFERENCE_KEY] = tool_mode
        preferences[TOOL_MODE_PREFERENCE_KEY] = tool_mode
        automation_path = str(preferences.get("automation_path") or "").strip()
        self.preferences["automation_path"] = automation_path
        if automation_path:
            preferences["automation_path"] = automation_path
        else:
            preferences.pop("automation_path", None)
            preferences.pop(AUTOMATION_CHECK_STATES_KEY, None)
            preferences.pop(AUTOMATION_CHECK_STATES_PATH_KEY, None)
        self.prefs.set_raw_preferences(preferences)
        self.prefs.save()

    def get_preference(self, key, default=None):
        """Gets a preference value.

        Args:
            key (str): Preference key.
            default (object, optional): Fallback value.

        Returns:
            object: Stored or fallback value.
        """
        return self.preferences.get(key, default)

    def get_last_used_data(self):
        """Gets a copy of the most recently saved tracker data.

        Returns:
            dict: Last-used range and file metadata, or an empty dictionary.
        """
        return copy.deepcopy(self.preferences.get(LAST_USED_DATA_KEY, {}))

    def get_automation_check_states(self, automation_path):
        """Gets stored check states when they belong to the given folder.

        Script names that no longer exist are deliberately preserved here. The
        view ignores them while building the current list, allowing a script to
        regain its selection state if it returns to the same folder.

        Args:
            automation_path (str): Current automation folder path.

        Returns:
            dict: Mapping of automation file names to checked states.
        """
        normalized_path = normalize_automation_path(automation_path)
        stored_path = self.preferences.get(AUTOMATION_CHECK_STATES_PATH_KEY, "")
        if normalized_path != stored_path:
            return {}
        stored_states = self.preferences.get(AUTOMATION_CHECK_STATES_KEY, {})
        return copy.deepcopy(stored_states) if isinstance(stored_states, dict) else {}

    def reset_automation_check_states(self, automation_path, save=True):
        """Clears stored check states when the automation folder changes.

        Args:
            automation_path (str): New automation folder path.
            save (bool, optional): Whether to immediately persist the change.

        Returns:
            bool: True if a new folder caused stored states to be reset.
        """
        normalized_path = normalize_automation_path(automation_path)
        stored_path = self.preferences.get(AUTOMATION_CHECK_STATES_PATH_KEY, "")
        if normalized_path == stored_path:
            return False
        self.preferences[AUTOMATION_CHECK_STATES_PATH_KEY] = normalized_path
        self.preferences[AUTOMATION_CHECK_STATES_KEY] = {}
        if save:
            self.save_preferences()
        return True

    def set_automation_check_state(
        self,
        automation_path,
        script_name,
        is_checked,
        save=True,
    ):
        """Stores a selected state for an automation in the current folder.

        Args:
            automation_path (str): Automation folder that owns the script.
            script_name (str): Automation file name.
            is_checked (bool): Whether the automation is selected for batch runs.
            save (bool, optional): Whether to immediately persist the change.
        """
        normalized_path = normalize_automation_path(automation_path)
        stored_path = self.preferences.get(AUTOMATION_CHECK_STATES_PATH_KEY, "")
        if normalized_path != stored_path:
            self.preferences[AUTOMATION_CHECK_STATES_PATH_KEY] = normalized_path
            self.preferences[AUTOMATION_CHECK_STATES_KEY] = {}
        check_states = self.preferences.get(AUTOMATION_CHECK_STATES_KEY, {})
        if not isinstance(check_states, dict):
            check_states = {}
        check_states[str(script_name)] = bool(is_checked)
        self.preferences[AUTOMATION_CHECK_STATES_KEY] = check_states
        if save:
            self.save_preferences()

    def set_last_used_data(self, data, save=True):
        """Stores a copy of tracker data for reuse by later files.

        Args:
            data (dict): JSON-compatible range and file metadata.
            save (bool, optional): Whether to immediately persist preferences.
        """
        self.preferences[LAST_USED_DATA_KEY] = copy.deepcopy(data or {})
        if save:
            self.save_preferences()

    def set_preference(self, key, value, save=True):
        """Sets one preference value.

        Args:
            key (str): Preference key.
            value (object): New preference value.
            save (bool, optional): Whether to immediately persist the value.
        """
        self.preferences[key] = value
        if save:
            self.save_preferences()

    def update_preferences(self, values, save=True):
        """Updates several preferences together.

        Args:
            values (dict): Preference values to update.
            save (bool, optional): Whether to immediately persist the values.
        """
        self.preferences.update(values)
        if save:
            self.save_preferences()
