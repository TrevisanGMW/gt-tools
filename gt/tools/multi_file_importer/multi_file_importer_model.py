"""
Multi-File Importer Model

Holds the file list, tool settings, per-format settings, their persistence and their export/import.
Pure Python: importable and testable outside Maya.
"""

from gt.tools.multi_file_importer import multi_file_importer_constants as constants
from gt.tools.multi_file_importer import multi_file_importer_formats as formats
import gt.core.str as core_str
import logging
import json
import os
import uuid

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class FileEntry:
    """One file in the import list."""

    def __init__(self, path, enabled=True):
        """Initializes a file entry.

        Args:
            path (str): Absolute file path.
            enabled (bool, optional): Whether the file is imported when the tool runs.
        """
        self.entry_id = uuid.uuid4().hex
        self.path = os.path.normpath(path)
        self.enabled = bool(enabled)
        self.status = constants.STATUS_PENDING
        self.message = ""

    @property
    def name(self):
        """Gets the file name without its folder.

        Returns:
            str: File name with extension.
        """
        return os.path.basename(self.path)

    @property
    def folder(self):
        """Gets the folder containing the file.

        Returns:
            str: Folder path.
        """
        return os.path.dirname(self.path)

    def get_format(self):
        """Gets the format that handles this file.

        Returns:
            FormatBase: Format, or None when unsupported.
        """
        return formats.get_format_for_path(self.path)

    def get_format_label(self):
        """Gets the display label of the file format.

        Returns:
            str: Format label, or the bare extension when unsupported.
        """
        file_format = self.get_format()
        if file_format:
            return file_format.label
        return os.path.splitext(self.path)[1].lstrip(".").upper()

    def set_status(self, status, message=""):
        """Sets the import status.

        Args:
            status (str): One of the constants.STATUS_* values.
            message (str, optional): Detail shown in the tooltip.
        """
        self.status = status
        self.message = message or ""

    def to_dict(self):
        """Serializes the entry for preferences and exported settings.

        Returns:
            dict: {"path": str, "enabled": bool}.
        """
        return {"path": self.path, "enabled": self.enabled}


class MultiFileImporterModel:
    """Stores the Multi-File Importer state."""

    def __init__(self, prefs=None):
        """Initializes the model and loads saved preferences.

        Args:
            prefs (Prefs, optional): Preferences object. Created lazily when omitted.
        """
        self.prefs = prefs if prefs is not None else create_preferences()
        self.entries = []
        self.settings = dict(constants.DEFAULT_SETTINGS)
        self.format_settings = {}
        self.section_states = dict(constants.DEFAULT_SECTION_STATES)
        self.last_directory = ""
        self.selected_format = ""
        self.load_preferences()

    # ------------------------------------------------------------------ file list
    def get_allowed_extensions(self):
        """Gets the extensions accepted by the current format filter.

        Returns:
            list: Lowercase extensions including the dot.
        """
        filter_key = self.settings.get("extension_filter", constants.FILTER_ALL)
        file_format = formats.get_format(filter_key) if filter_key != constants.FILTER_ALL else None
        if file_format:
            return file_format.get_extensions()
        return formats.get_supported_extensions()

    def expand_paths(self, paths, recursive=None):
        """Expands dropped, pasted or picked paths into supported files.

        Args:
            paths (list): File and folder paths.
            recursive (bool, optional): Search sub-folders. Uses the "recursive" setting when omitted.

        Returns:
            tuple: (file_paths, unsupported_count). Folder contents are sorted by name.
        """
        if recursive is None:
            recursive = self.settings.get("recursive", False)
        allowed_extensions = set(self.get_allowed_extensions())
        file_paths = []
        unsupported_count = 0
        for path in paths or []:
            path = str(path or "").strip().strip('"')
            if not path:
                continue
            if os.path.isdir(path):
                candidates = list_folder_files(path, recursive=recursive)
            elif os.path.isfile(path):
                candidates = [path]
            else:
                continue
            for candidate in candidates:
                if os.path.splitext(candidate)[1].lower() in allowed_extensions:
                    file_paths.append(os.path.normpath(candidate))
                elif os.path.isfile(path):
                    unsupported_count += 1
        return file_paths, unsupported_count

    def add_paths(self, paths, recursive=None):
        """Adds files and folders to the list, skipping duplicates and unsupported formats.

        Args:
            paths (list): File and folder paths.
            recursive (bool, optional): Search sub-folders. Uses the "recursive" setting when omitted.

        Returns:
            dict: {"added": int, "duplicates": int, "unsupported": int}.
        """
        file_paths, unsupported_count = self.expand_paths(paths, recursive=recursive)
        added_count, duplicate_count = self._append_entries([(file_path, True) for file_path in file_paths])
        return {"added": added_count, "duplicates": duplicate_count, "unsupported": unsupported_count}

    def _append_entries(self, items):
        """Appends entries, skipping paths already listed.

        Args:
            items (list): (path, enabled) tuples.

        Returns:
            tuple: (added_count, duplicate_count).
        """
        existing_keys = set(os.path.normcase(entry.path) for entry in self.entries)
        added_count = 0
        duplicate_count = 0
        for path, enabled in items:
            path_key = os.path.normcase(os.path.normpath(path))
            if path_key in existing_keys:
                duplicate_count += 1
                continue
            existing_keys.add(path_key)
            self.entries.append(FileEntry(path, enabled=enabled))
            added_count += 1
        return added_count, duplicate_count

    def remove_entries(self, entry_ids):
        """Removes entries from the list.

        Args:
            entry_ids (list): Entry IDs to remove.

        Returns:
            int: Number of removed entries.
        """
        entry_ids = set(entry_ids or [])
        count_before = len(self.entries)
        self.entries = [entry for entry in self.entries if entry.entry_id not in entry_ids]
        return count_before - len(self.entries)

    def remove_unchecked(self):
        """Removes every unchecked entry.

        Returns:
            int: Number of removed entries.
        """
        return self.remove_entries([entry.entry_id for entry in self.entries if not entry.enabled])

    def remove_missing(self):
        """Removes entries whose file no longer exists.

        Returns:
            int: Number of removed entries.
        """
        return self.remove_entries([entry.entry_id for entry in self.entries if not os.path.isfile(entry.path)])

    def clear_entries(self):
        """Removes every entry."""
        self.entries = []

    def get_entry(self, entry_id):
        """Gets an entry by ID.

        Args:
            entry_id (str): Entry ID.

        Returns:
            FileEntry: Matching entry, or None.
        """
        return next((entry for entry in self.entries if entry.entry_id == entry_id), None)

    def get_entries(self, entry_ids):
        """Gets entries by ID, in list order.

        Args:
            entry_ids (list): Entry IDs.

        Returns:
            list: Matching FileEntry objects.
        """
        entry_ids = set(entry_ids or [])
        return [entry for entry in self.entries if entry.entry_id in entry_ids]

    def set_entry_enabled(self, entry_id, enabled):
        """Checks or unchecks one entry.

        Args:
            entry_id (str): Entry ID.
            enabled (bool): New state.
        """
        entry = self.get_entry(entry_id)
        if entry:
            entry.enabled = bool(enabled)

    def set_entries_enabled(self, entry_ids, enabled):
        """Checks or unchecks several entries (all entries when entry_ids is None).

        Args:
            entry_ids (list): Entry IDs, or None for every entry.
            enabled (bool): New state.
        """
        targets = self.entries if entry_ids is None else self.get_entries(entry_ids)
        for entry in targets:
            entry.enabled = bool(enabled)

    def solo_entries(self, entry_ids):
        """Checks only the given entries and unchecks every other entry.

        Args:
            entry_ids (list): Entry IDs to keep checked.
        """
        entry_ids = set(entry_ids or [])
        for entry in self.entries:
            entry.enabled = entry.entry_id in entry_ids

    def invert_checks(self):
        """Inverts the checked state of every entry."""
        for entry in self.entries:
            entry.enabled = not entry.enabled

    def get_enabled_entries(self):
        """Gets the entries that will be imported, in list order.

        Returns:
            list: Enabled FileEntry objects.
        """
        return [entry for entry in self.entries if entry.enabled]

    def sort_entries(self, sort_mode):
        """Sorts the list.

        Args:
            sort_mode (str): One of constants.SORT_MODES.
        """
        if sort_mode == constants.SORT_REVERSE:
            self.entries.reverse()
        elif sort_mode == constants.SORT_FOLDER:
            self.entries.sort(key=lambda entry: (os.path.normcase(entry.folder), entry.name.lower()))
        else:
            self.entries.sort(key=lambda entry: (entry.name.lower(), os.path.normcase(entry.folder)))

    def reset_statuses(self):
        """Marks every entry as pending again."""
        for entry in self.entries:
            entry.set_status(constants.STATUS_PENDING)

    # ------------------------------------------------------------------ settings
    def update_settings(self, settings):
        """Updates tool settings, ignoring unknown keys and invalid values.

        Args:
            settings (dict): New values.

        Returns:
            list: Keys whose value changed.
        """
        merged_settings = dict(self.settings)
        merged_settings.update(settings or {})
        previous_settings = self.settings
        if parse_frame_rate(merged_settings["frame_rate_custom"]) <= 0:
            merged_settings["frame_rate_custom"] = previous_settings["frame_rate_custom"]
        self.settings = normalize_settings(merged_settings)
        return [key for key, value in self.settings.items() if previous_settings.get(key) != value]

    def get_format_settings(self, format_key):
        """Gets the complete, valid settings of one format.

        Args:
            format_key (str): Format key.

        Returns:
            dict: Format settings.
        """
        file_format = formats.get_format(format_key)
        if not file_format:
            return {}
        return file_format.normalize_settings(self.format_settings.get(format_key))

    def set_format_settings(self, format_key, settings):
        """Stores the settings of one format.

        Args:
            format_key (str): Format key.
            settings (dict): Format settings.
        """
        file_format = formats.get_format(format_key)
        if file_format:
            self.format_settings[format_key] = file_format.normalize_settings(settings)

    def get_all_format_settings(self):
        """Gets the settings of every format.

        Returns:
            dict: Format key to settings.
        """
        return {file_format.key: self.get_format_settings(file_format.key) for file_format in formats.get_formats()}

    def set_section_state(self, section_key, expanded):
        """Stores whether a collapsible section is expanded.

        Args:
            section_key (str): Section key.
            expanded (bool): Expanded state.
        """
        self.section_states[section_key] = bool(expanded)

    def get_startup_section_states(self):
        """Gets the section states to show when the tool opens.

        Returns:
            dict: Collapsed states for every section.
        """
        return dict(constants.DEFAULT_SECTION_STATES)

    # ------------------------------------------------------------------ validation and names
    def validate(self):
        """Checks the list and settings before importing.

        Returns:
            tuple: (errors, warnings) as lists of user-facing messages.
        """
        errors = []
        warnings = []
        enabled_entries = self.get_enabled_entries()
        if not enabled_entries:
            errors.append("No files to import. Add files or check at least one file in the list.")
        missing_entries = [entry for entry in enabled_entries if not os.path.isfile(entry.path)]
        if missing_entries:
            warnings.append(f"{len(missing_entries)} file(s) no longer exist and will be skipped.")
        unsupported_entries = [entry for entry in enabled_entries if not entry.get_format()]
        if unsupported_entries:
            warnings.append(f"{len(unsupported_entries)} file(s) have no matching format and will be skipped.")
        if self.settings["namespace_mode"] == constants.NAMESPACE_CUSTOM:
            if not str(self.settings["namespace_template"]).strip():
                errors.append("Custom namespace is empty. Enter a template such as {name}.")
        if self.settings["timeline_mode"] == constants.TIMELINE_MANUAL:
            if float(self.settings["timeline_start"]) > float(self.settings["timeline_end"]):
                errors.append("Manual timeline start must be lower than or equal to the end.")
        if self.settings["frame_rate_source"] == constants.SOURCE_CUSTOM:
            if parse_frame_rate(self.settings["frame_rate_custom"]) <= 0:
                errors.append("Custom frame rate must be a positive number.")
        return errors, warnings

    def build_namespace(self, file_path, index):
        """Builds the preferred namespace for a file (not yet made unique).

        Args:
            file_path (str): File path.
            index (int): One-based position of the file in the import.

        Returns:
            str: Maya-safe namespace, or an empty string when no namespace should be used.
        """
        mode = self.settings["namespace_mode"]
        reference = self.settings["load_mode"] == constants.LOAD_MODE_REFERENCE
        if mode == constants.NAMESPACE_NONE and not reference:
            return ""
        template = self.settings["namespace_template"] if mode == constants.NAMESPACE_CUSTOM else constants.NAME_TOKEN
        return core_str.sanitize_maya_name(resolve_name_template(template, file_path, index), "file")

    def build_group_name(self, file_path, index):
        """Builds the per-file group name.

        Args:
            file_path (str): File path.
            index (int): One-based position of the file in the import.

        Returns:
            str: Maya-safe group name.
        """
        template = self.settings["group_template"] or f"{constants.NAME_TOKEN}_grp"
        return core_str.sanitize_maya_name(resolve_name_template(template, file_path, index), "file_grp")

    # ------------------------------------------------------------------ export and import
    def build_export_data(self):
        """Builds the data written by "Export Settings".

        Returns:
            dict: Settings, format settings, section states and (optionally) the file list.
        """
        data = {
            "tool": constants.EXPORT_TOOL_KEY,
            "version": constants.EXPORT_VERSION,
            constants.PREFS_KEY_SETTINGS: dict(self.settings),
            constants.PREFS_KEY_FORMAT_SETTINGS: self.get_all_format_settings(),
            constants.PREFS_KEY_SECTIONS: dict(self.section_states),
        }
        if self.settings.get("include_files_in_export"):
            data[constants.PREFS_KEY_FILES] = [entry.to_dict() for entry in self.entries]
        return data

    def apply_import_data(self, data):
        """Applies data produced by build_export_data.

        Args:
            data (dict): Imported data.

        Returns:
            int: Number of files added from the data (files already listed are skipped).

        Raises:
            ValueError: When the data is not Multi-File Importer settings.
        """
        if not isinstance(data, dict) or data.get("tool") != constants.EXPORT_TOOL_KEY:
            raise ValueError("The file does not contain Multi-File Importer settings.")
        self.settings = normalize_settings(data.get(constants.PREFS_KEY_SETTINGS))
        self.format_settings = self._read_format_settings(data.get(constants.PREFS_KEY_FORMAT_SETTINGS))
        self.section_states = self._read_section_states(data.get(constants.PREFS_KEY_SECTIONS))
        added_count, _ = self._append_entries(read_file_items(data.get(constants.PREFS_KEY_FILES)))
        return added_count

    def export_settings(self, file_path):
        """Writes the settings to a JSON file.

        Args:
            file_path (str): Destination path.
        """
        with open(file_path, "w", encoding="utf-8") as settings_file:
            json.dump(self.build_export_data(), settings_file, indent=4)

    def import_settings(self, file_path):
        """Reads settings from a JSON file and applies them.

        Args:
            file_path (str): Source path.

        Returns:
            int: Number of files added from the settings file.
        """
        with open(file_path, "r", encoding="utf-8") as settings_file:
            return self.apply_import_data(json.load(settings_file))

    # ------------------------------------------------------------------ persistence
    def load_preferences(self):
        """Loads saved settings. Missing or invalid values keep their defaults."""
        data = self._get_raw_preferences()
        stored_settings = data.get(constants.PREFS_KEY_SETTINGS)
        stored_settings = stored_settings if isinstance(stored_settings, dict) else {}
        stored_files = data.get(constants.PREFS_KEY_FILES)
        self.settings = normalize_settings(stored_settings)
        if "keep_file_list" not in stored_settings and isinstance(stored_files, list):
            # Preserve lists saved during the version where file list persistence was automatic.
            self.settings["keep_file_list"] = True
        self.format_settings = self._read_format_settings(data.get(constants.PREFS_KEY_FORMAT_SETTINGS))
        self.section_states = self.get_startup_section_states()
        self.last_directory = str(data.get(constants.PREFS_KEY_LAST_DIRECTORY) or "")
        self.selected_format = str(data.get(constants.PREFS_KEY_SELECTED_FORMAT) or "")
        self.entries = []
        if self.settings["keep_file_list"]:
            self._append_entries(read_file_items(stored_files))

    def save_preferences(self):
        """Saves all tool settings, format options, the last folder and the optional file list.

        Returns:
            bool: True when the preferences were written.
        """
        if self.prefs is None:
            return False
        try:
            raw_preferences = self.prefs.get_raw_preferences()
            raw_preferences[constants.PREFS_KEY_SETTINGS] = dict(self.settings)
            raw_preferences[constants.PREFS_KEY_FORMAT_SETTINGS] = dict(self.format_settings)
            raw_preferences.pop(constants.PREFS_KEY_SECTIONS, None)
            raw_preferences[constants.PREFS_KEY_LAST_DIRECTORY] = self.last_directory
            raw_preferences[constants.PREFS_KEY_SELECTED_FORMAT] = self.selected_format
            self._store_file_list(raw_preferences)
            return self.prefs.save() is not False
        except Exception as exception:
            logger.warning(f"Unable to save {constants.TOOL_NAME} preferences: {exception}")
            return False

    def write_changes(self, setting_keys=None, format_keys=None, last_directory=False, selected_format=False,
                      files=False):
        """Writes only the given values to the preferences file, right away.

        Reloads Prefs before applying the listed changes to preserve other saved values.

        Args:
            setting_keys (list, optional): Tool setting keys to write.
            format_keys (list, optional): Format keys whose settings should be written.
            last_directory (bool, optional): Write the last used folder.
            selected_format (bool, optional): Write the format shown in Format Options.
            files (bool, optional): Update the stored file list according to the file list preference.

        Returns:
            bool: True when the preferences were written.
        """
        if self.prefs is None:
            return False
        try:
            load_from_disk = getattr(self.prefs, "load", None)
            if callable(load_from_disk):
                load_from_disk()
            raw_preferences = self.prefs.get_raw_preferences()
            stored_settings = _get_stored_dict(raw_preferences, constants.PREFS_KEY_SETTINGS)
            for key in setting_keys or []:
                stored_settings[key] = self.settings[key]
            stored_formats = _get_stored_dict(raw_preferences, constants.PREFS_KEY_FORMAT_SETTINGS)
            for format_key in format_keys or []:
                stored_formats[format_key] = self.get_format_settings(format_key)
            raw_preferences.pop(constants.PREFS_KEY_SECTIONS, None)
            if last_directory:
                raw_preferences[constants.PREFS_KEY_LAST_DIRECTORY] = self.last_directory
            if selected_format:
                raw_preferences[constants.PREFS_KEY_SELECTED_FORMAT] = self.selected_format
            if files:
                self._store_file_list(raw_preferences)
            return self.prefs.save() is not False
        except Exception as exception:
            logger.warning(f"Unable to save {constants.TOOL_NAME} preferences: {exception}")
            return False

    def reset_preferences(self):
        """Resets the settings and keeps the current file list in the open tool.

        Returns:
            bool: True when preferences were written.
        """
        self.settings = dict(constants.DEFAULT_SETTINGS)
        self.format_settings = {}
        self.section_states = dict(constants.DEFAULT_SECTION_STATES)
        return self.save_preferences()

    def _store_file_list(self, raw_preferences):
        """Updates the stored file list according to the current persistence preference.

        Args:
            raw_preferences (dict): Stored preferences to update.
        """
        if self.settings["keep_file_list"]:
            raw_preferences[constants.PREFS_KEY_FILES] = [entry.to_dict() for entry in self.entries]
        else:
            raw_preferences.pop(constants.PREFS_KEY_FILES, None)

    @staticmethod
    def _read_format_settings(data):
        """Reads stored format settings, ignoring unknown formats.

        Args:
            data (dict): Stored format settings.

        Returns:
            dict: Format key to normalized settings.
        """
        format_settings = {}
        for format_key, settings in (data if isinstance(data, dict) else {}).items():
            file_format = formats.get_format(format_key)
            if file_format:
                format_settings[format_key] = file_format.normalize_settings(settings)
        return format_settings

    @staticmethod
    def _read_section_states(data):
        """Reads stored section states.

        Args:
            data (dict): Stored section states.

        Returns:
            dict: Section key to expanded state.
        """
        section_states = dict(constants.DEFAULT_SECTION_STATES)
        for section_key in section_states:
            if isinstance(data, dict) and section_key in data:
                section_states[section_key] = bool(data[section_key])
        return section_states

    def _get_raw_preferences(self):
        """Gets the raw preference dictionary.

        Returns:
            dict: Stored preference data, or an empty dictionary.
        """
        if self.prefs is None:
            return {}
        try:
            data = self.prefs.get_raw_preferences()
        except Exception as exception:
            logger.debug(f"Unable to read {constants.TOOL_NAME} preferences: {exception}")
            return {}
        return data if isinstance(data, dict) else {}


# ------------------------------------------------------------------ pure helpers
def normalize_settings(settings):
    """Builds a complete settings dictionary with valid values.

    Args:
        settings (dict): Stored or edited settings, possibly partial or outdated.

    Returns:
        dict: Settings for every key in constants.DEFAULT_SETTINGS.
    """
    settings = settings if isinstance(settings, dict) else {}
    normalized_settings = {}
    for key, default_value in constants.DEFAULT_SETTINGS.items():
        normalized_settings[key] = _coerce_value(settings.get(key), default_value)
    for key, choices in constants.CHOICE_SETTINGS.items():
        if normalized_settings[key] not in choices:
            normalized_settings[key] = constants.DEFAULT_SETTINGS[key]
    extension_filter = normalized_settings["extension_filter"]
    if extension_filter != constants.FILTER_ALL and not formats.get_format(extension_filter):
        normalized_settings["extension_filter"] = constants.FILTER_ALL
    if parse_frame_rate(normalized_settings["frame_rate_custom"]) <= 0:
        normalized_settings["frame_rate_custom"] = constants.DEFAULT_SETTINGS["frame_rate_custom"]
    normalized_settings["grid_columns"] = max(0, normalized_settings["grid_columns"])
    return normalized_settings


def _get_stored_dict(raw_preferences, key):
    """Gets (or creates) a dictionary stored under a key of the raw preferences.

    Args:
        raw_preferences (dict): Raw preference data, updated in place.
        key (str): Key holding a dictionary.

    Returns:
        dict: The stored dictionary.
    """
    stored_value = raw_preferences.get(key)
    if not isinstance(stored_value, dict):
        stored_value = {}
        raw_preferences[key] = stored_value
    return stored_value


def _coerce_value(value, default_value):
    """Coerces a value to the type of its default.

    Args:
        value (object): Value to coerce.
        default_value (object): Default value; its type is used.

    Returns:
        object: Coerced value, or the default when coercion fails.
    """
    if value is None:
        return default_value
    try:
        if isinstance(default_value, bool):
            return bool(value)
        if isinstance(default_value, int):
            return int(value)
        if isinstance(default_value, float):
            return float(value)
        return str(value)
    except (TypeError, ValueError):
        return default_value


def read_file_items(data):
    """Reads a stored file list.

    Args:
        data (list): Items such as {"path": str, "enabled": bool}.

    Returns:
        list: (path, enabled) tuples for valid items.
    """
    items = []
    for item in data if isinstance(data, list) else []:
        if isinstance(item, dict) and item.get("path"):
            items.append((str(item["path"]), bool(item.get("enabled", True))))
    return items


def parse_frame_rate(value):
    """Parses a frame rate value.

    Args:
        value (object): Frame rate such as "30" or 29.97.

    Returns:
        float: Frames per second, or 0.0 when invalid.
    """
    try:
        frame_rate = float(value)
    except (TypeError, ValueError):
        return 0.0
    return frame_rate if frame_rate > 0 else 0.0


def parse_pasted_paths(text):
    """Splits pasted text into paths (one per line, surrounding quotes removed).

    Args:
        text (str): Clipboard text.

    Returns:
        list: Non-empty paths.
    """
    paths = []
    for line in str(text or "").splitlines():
        line = line.strip().strip('"').strip("'").strip()
        if line.lower().startswith("file:///"):
            line = line[8:]
        if line:
            paths.append(line)
    return paths


def resolve_name_template(template, file_path, index):
    """Replaces {name} and {index} in a name template.

    Args:
        template (str): Template text.
        file_path (str): File path; {name} becomes the file name without extension.
        index (int): One-based file index; {index} becomes a two-digit (or wider) number.

    Returns:
        str: Resolved text.
    """
    file_name = os.path.splitext(os.path.basename(str(file_path or "")))[0]
    resolved_text = str(template or "")
    resolved_text = resolved_text.replace(constants.NAME_TOKEN, file_name)
    resolved_text = resolved_text.replace(constants.INDEX_TOKEN, str(int(index)).zfill(2))
    return resolved_text


def list_folder_files(folder_path, recursive=False):
    """Lists the files in a folder.

    Args:
        folder_path (str): Folder to list.
        recursive (bool, optional): Include sub-folders.

    Returns:
        list: File paths sorted by name within each folder.
    """
    file_paths = []
    if recursive:
        for root_path, folder_names, file_names in os.walk(folder_path):
            folder_names.sort(key=str.lower)
            for file_name in sorted(file_names, key=str.lower):
                file_paths.append(os.path.join(root_path, file_name))
        return file_paths
    try:
        names = sorted(os.listdir(folder_path), key=str.lower)
    except OSError as exception:
        logger.debug(f'Unable to list "{folder_path}": {exception}')
        return []
    for file_name in names:
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            file_paths.append(file_path)
    return file_paths


def create_preferences():
    """Creates the tool's persistent preferences object.

    Returns:
        Prefs or None: Preferences object, or None if unavailable.
    """
    try:
        import gt.core.prefs as core_prefs

        return core_prefs.Prefs(constants.PREFS_FILENAME)
    except Exception as exception:
        logger.warning(f"Unable to load {constants.TOOL_NAME} preferences: {exception}")
        return None


class MemoryPrefs:
    """Preferences backend for callers that need in-memory storage."""

    def __init__(self):
        """Initializes the in-memory preferences."""
        self.preferences = {}

    def get_raw_preferences(self):
        """Gets the raw preferences.

        Returns:
            dict: Preference data.
        """
        return self.preferences

    def save(self):
        """Keeps preferences in memory only."""
        return None
