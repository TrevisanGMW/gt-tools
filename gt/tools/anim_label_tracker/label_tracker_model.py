"""Model and persistence helpers for Animation Label Tracker."""

import copy
import os

from gt.core.prefs import Prefs


PREFS_FILENAME = "anim_label_tracker"
LAST_USED_DATA_KEY = "last_used_data"
AUTOMATION_CHECK_STATES_KEY = "automation_check_states"
AUTOMATION_CHECK_STATES_PATH_KEY = "automation_check_states_path"

DEFAULT_PREFERENCES = {
    "schema_path": "",
    "automation_path": "",
    AUTOMATION_CHECK_STATES_KEY: {},
    AUTOMATION_CHECK_STATES_PATH_KEY: "",
    "magnet_enabled": True,
    "snap_threshold": 10,
    "auto_crop": False,
    "crop_tolerance": 10,
    "auto_stretch": False,
    "stretch_tolerance": 10,
    "show_frames": True,
    "show_names": False,
    "random_colors": True,
    "sync_time": True,
    "limit_bounds": True,
    "razor_random_colors": True,
    "run_all_automations": True,
    "show_validation_status": True,
    "write_scene_node": True,
    LAST_USED_DATA_KEY: {},
}


def get_sample_directory():
    """Gets the packaged sample directory.

    Returns:
        str: Absolute sample directory path.
    """
    return os.path.join(os.path.dirname(__file__), "samples")


def get_sample_schema_path():
    """Gets the packaged sample schema path.

    Returns:
        str: Absolute JSON schema path.
    """
    return os.path.join(get_sample_directory(), "schema.json")


def get_sample_automation_path():
    """Gets the packaged sample automation path.

    Returns:
        str: Absolute Python automation path.
    """
    return os.path.join(get_sample_directory(), "automation.py")


def get_default_preferences():
    """Builds default preferences with packaged sample locations.

    Returns:
        dict: Default Animation Label Tracker preferences.
    """
    preferences = copy.deepcopy(DEFAULT_PREFERENCES)
    preferences["schema_path"] = get_sample_schema_path()
    preferences["automation_path"] = get_sample_directory()
    return preferences


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


def collect_validation_errors(schema, ranges, file_data, start_frame, end_frame):
    """Collects all schema validation errors without touching Maya.

    Args:
        schema (dict): Loaded Animation Label Tracker schema.
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


class AnimationLabelTrackerModel:
    """Stores persistent Animation Label Tracker state."""

    def __init__(self):
        """Initializes the model and loads persistent preferences."""
        self.prefs = Prefs(PREFS_FILENAME)
        self.preferences = {}
        self.load_preferences()

    def load_preferences(self):
        """Loads preferences and fills missing keys with current defaults."""
        preferences = get_default_preferences()
        preferences.update(self.prefs.get_raw_preferences())
        self.preferences = preferences
        return copy.deepcopy(self.preferences)

    def save_preferences(self):
        """Writes all current preferences to the package preferences file."""
        self.prefs.set_raw_preferences(copy.deepcopy(self.preferences))
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
