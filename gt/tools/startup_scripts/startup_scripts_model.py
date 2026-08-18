"""Data model for the GT Tools Startup Scripts tool.

This module purposely contains no Maya imports so preference data and source
collection can be tested outside Maya.
"""

import copy
import os
import uuid


PREFS_FILENAME = "startup_scripts"
PREFS_KEY_CONFIGURATION = "configuration"
PREFS_SCHEMA_VERSION = 1

RUN_MODE_MAYA_STARTUP = "Maya Startup"
RUN_MODE_FILE_OPEN = "File Open"
RUN_MODE_BOTH = "Both"
RUN_MODE_VALUES = [RUN_MODE_MAYA_STARTUP, RUN_MODE_FILE_OPEN, RUN_MODE_BOTH]


def create_default_script(name="Startup Script"):
    """Creates a default startup-script configuration.

    Args:
        name (str, optional): Display name for the new configuration.

    Returns:
        dict: JSON-compatible startup-script configuration.
    """
    return {
        "id": str(uuid.uuid4()),
        "name": str(name or "Startup Script"),
        "enabled": True,
        "run_mode": RUN_MODE_MAYA_STARTUP,
        "print_execution_message": True,
        "script_text": "",
        "external_files": [],
        "script_directories": [],
        "font_size": 14,
    }


def normalize_source_entries(entries):
    """Normalizes script-source rows into JSON-compatible dictionaries.

    Args:
        entries (list): Raw source rows.

    Returns:
        list: Normalized source rows.
    """
    normalized_entries = []
    for entry in entries if isinstance(entries, list) else []:
        if isinstance(entry, dict):
            path = entry.get("path", "")
            enabled = entry.get("enabled", True)
        else:
            path = entry
            enabled = True
        path = str(path or "").strip()
        if not path:
            continue
        normalized_entries.append({"path": path, "enabled": bool(enabled)})
    return normalized_entries


def normalize_script_configuration(configuration):
    """Normalizes one startup-script configuration for tool editing.

    Args:
        configuration (dict): Raw configuration data.

    Returns:
        dict: Normalized JSON-compatible startup-script configuration.
    """
    default = create_default_script()
    source = configuration if isinstance(configuration, dict) else {}
    normalized = {
        "id": str(source.get("id") or default["id"]),
        "name": str(source.get("name") or default["name"]),
        "enabled": bool(source.get("enabled", default["enabled"])),
        "run_mode": source.get("run_mode", default["run_mode"]),
        "print_execution_message": bool(
            source.get("print_execution_message", default["print_execution_message"])
        ),
        "script_text": str(source.get("script_text") or ""),
        "external_files": normalize_source_entries(source.get("external_files")),
        "script_directories": normalize_source_entries(source.get("script_directories")),
        "font_size": int(source.get("font_size", default["font_size"]) or 14),
    }
    if normalized["run_mode"] not in RUN_MODE_VALUES:
        normalized["run_mode"] = RUN_MODE_MAYA_STARTUP
    normalized["font_size"] = max(8, min(24, normalized["font_size"]))
    return normalized


def is_source_entries_valid(entries):
    """Checks whether a stored source-entry list has the expected schema.

    Args:
        entries (list): Source entries read from preferences.

    Returns:
        bool: True when every entry is a valid source dictionary.
    """
    if not isinstance(entries, list):
        return False
    for entry in entries:
        if not isinstance(entry, dict):
            return False
        if not isinstance(entry.get("path"), str):
            return False
        if not isinstance(entry.get("enabled", True), bool):
            return False
    return True


def is_script_configuration_valid(configuration):
    """Checks whether a stored startup-script configuration is runnable safely.

    Args:
        configuration (dict): Configuration read from preferences.

    Returns:
        bool: True when the configuration has the expected schema.
    """
    if not isinstance(configuration, dict):
        return False
    required_types = {
        "id": str,
        "name": str,
        "enabled": bool,
        "run_mode": str,
        "print_execution_message": bool,
        "script_text": str,
        "font_size": int,
    }
    for key, expected_type in required_types.items():
        if not isinstance(configuration.get(key), expected_type):
            return False
    if not configuration.get("id") or configuration.get("run_mode") not in RUN_MODE_VALUES:
        return False
    return is_source_entries_valid(configuration.get("external_files")) and is_source_entries_valid(
        configuration.get("script_directories")
    )


def is_preferences_data_valid(data):
    """Checks the complete stored preference payload before startup execution.

    Args:
        data (dict): Preference configuration payload.

    Returns:
        bool: True when the payload matches the expected schema.
    """
    if not isinstance(data, dict):
        return False
    if data.get("schema_version") != PREFS_SCHEMA_VERSION:
        return False
    scripts = data.get("scripts")
    if not isinstance(scripts, list):
        return False
    script_ids = set()
    for script in scripts:
        if not is_script_configuration_valid(script):
            return False
        script_id = script.get("id")
        if script_id in script_ids:
            return False
        script_ids.add(script_id)
    return True


def get_sample_scripts_directory():
    """Gets the package directory that contains Startup Scripts examples.

    Returns:
        str: Absolute sample-script directory.
    """
    return os.path.join(os.path.dirname(__file__), "samples")


def get_sample_scripts():
    """Gets the packaged Python sample scripts in stable display order.

    Returns:
        list: Dictionaries containing absolute and display-relative paths.
    """
    samples_directory = get_sample_scripts_directory()
    if not os.path.isdir(samples_directory):
        return []
    scripts = []
    for current_directory, directory_names, file_names in os.walk(samples_directory):
        directory_names.sort(key=str.lower)
        for file_name in sorted(file_names, key=str.lower):
            if not file_name.lower().endswith(".py"):
                continue
            file_path = os.path.join(current_directory, file_name)
            scripts.append(
                {
                    "path": os.path.normpath(file_path),
                    "relative_path": os.path.normpath(
                        os.path.relpath(file_path, samples_directory)
                    ),
                }
            )
    return scripts


def load_script_file(script_path):
    """Loads Python source text from an external script file.

    Args:
        script_path (str): Existing Python file path.

    Returns:
        str: File source text.

    Raises:
        IOError: If the file cannot be read.
    """
    with open(script_path, "r", encoding="utf-8") as script_file:
        return script_file.read()


def collect_directory_script_paths(directory_path):
    """Collects Python files from a directory in deterministic recursive order.

    Args:
        directory_path (str): Root directory to scan.

    Returns:
        list: Existing Python file paths ordered by directory and file name.
    """
    if not directory_path or not os.path.isdir(directory_path):
        return []
    script_paths = []
    for current_directory, directory_names, file_names in os.walk(directory_path):
        directory_names.sort(key=str.lower)
        for file_name in sorted(file_names, key=str.lower):
            if file_name.lower().endswith(".py"):
                script_paths.append(os.path.normpath(os.path.join(current_directory, file_name)))
    return script_paths


def get_script_paths(configuration):
    """Gets all valid external script sources in the configuration's run order.

    Explicit files run first in their configured order. Directory files run next,
    with every directory scanned recursively in alphabetical order. Duplicate paths
    are omitted while retaining the first occurrence.

    Args:
        configuration (dict): Startup-script configuration.

    Returns:
        list: Existing Python script paths.
    """
    if not isinstance(configuration, dict):
        return []
    script_paths = []
    known_paths = set()

    def append_script_path(script_path):
        """Adds one existing script path when it was not already added.

        Args:
            script_path (str): Candidate Python script path.
        """
        if not script_path or not os.path.isfile(script_path):
            return
        if not script_path.lower().endswith(".py"):
            return
        normalized_path = os.path.normpath(script_path)
        comparison_path = os.path.normcase(normalized_path)
        if comparison_path in known_paths:
            return
        known_paths.add(comparison_path)
        script_paths.append(normalized_path)

    for entry in configuration.get("external_files", []):
        if isinstance(entry, dict) and entry.get("enabled", True):
            append_script_path(entry.get("path"))
    for entry in configuration.get("script_directories", []):
        if not isinstance(entry, dict) or not entry.get("enabled", True):
            continue
        for script_path in collect_directory_script_paths(entry.get("path")):
            append_script_path(script_path)
    return script_paths


def has_runnable_source(configuration):
    """Checks whether a configuration currently resolves to executable code.

    Args:
        configuration (dict): Startup-script configuration.

    Returns:
        bool: True when inline code or an external Python file is available.
    """
    if not isinstance(configuration, dict):
        return False
    if str(configuration.get("script_text") or "").strip():
        return True
    return bool(get_script_paths(configuration))


class StartupScriptsModel:
    """Stores Startup Scripts configurations using ``gt.core.prefs.Prefs``."""

    def __init__(self, prefs=None):
        """Initializes the model and loads valid saved configurations.

        Args:
            prefs (Prefs, optional): Preference object injected for testing.
        """
        if prefs is None:
            from gt.core.prefs import Prefs

            prefs = Prefs(PREFS_FILENAME)
        self.prefs = prefs
        self.scripts = [create_default_script()]
        self.loaded_preferences = self.load_preferences()

    def has_valid_preferences_file(self):
        """Checks whether a valid tool preference file is available on disk.

        Returns:
            bool: True when the file exists and its payload has a valid schema.
        """
        file_path = getattr(self.prefs, "file_name", "")
        if not file_path or not os.path.isfile(file_path):
            return False
        raw_preferences = self.prefs.get_raw_preferences()
        return is_preferences_data_valid(raw_preferences.get(PREFS_KEY_CONFIGURATION))

    def load_preferences(self):
        """Loads saved configurations when the stored preference data is valid.

        Returns:
            bool: True when configurations were loaded from preferences.
        """
        if not self.has_valid_preferences_file():
            self.scripts = [create_default_script()]
            return False
        raw_preferences = self.prefs.get_raw_preferences()
        configuration = raw_preferences.get(PREFS_KEY_CONFIGURATION)
        self.scripts = copy.deepcopy(configuration.get("scripts", []))
        return True

    def save_preferences(self):
        """Saves the current configuration list through ``Prefs``.

        Returns:
            dict: Saved preference configuration payload.
        """
        configuration = {
            "schema_version": PREFS_SCHEMA_VERSION,
            "scripts": copy.deepcopy(self.scripts),
        }
        self.prefs.get_raw_preferences()[PREFS_KEY_CONFIGURATION] = configuration
        self.prefs.save()
        self.loaded_preferences = True
        return configuration

    def get_scripts(self):
        """Gets a safe copy of all configured startup scripts.

        Returns:
            list: Startup-script configuration dictionaries.
        """
        return copy.deepcopy(self.scripts)

    def get_script(self, script_id):
        """Gets one startup script by its stable identifier.

        Args:
            script_id (str): Startup-script identifier.

        Returns:
            dict or None: Configuration copy when found.
        """
        for script in self.scripts:
            if script.get("id") == script_id:
                return copy.deepcopy(script)
        return None

    def add_script(self, name="Startup Script", save=True):
        """Adds a new default startup script.

        Args:
            name (str, optional): Display name for the script.
            save (bool, optional): Whether the preference file should update immediately.

        Returns:
            dict: Added script configuration.
        """
        script = create_default_script(name=name)
        self.scripts.append(script)
        if save:
            self.save_preferences()
        return copy.deepcopy(script)

    def duplicate_script(self, script_id, save=True):
        """Duplicates one script configuration with a new stable identifier.

        Args:
            script_id (str): Source script identifier.
            save (bool, optional): Whether the preference file should update immediately.

        Returns:
            dict or None: Duplicated configuration when the source exists.
        """
        script = self.get_script(script_id)
        if not script:
            return None
        script["id"] = str(uuid.uuid4())
        script["name"] = f"{script.get('name') or 'Startup Script'} Copy"
        self.scripts.append(script)
        if save:
            self.save_preferences()
        return copy.deepcopy(script)

    def update_script(self, script_id, updates, save=True):
        """Updates one script configuration using normalized editable values.

        Args:
            script_id (str): Script identifier to update.
            updates (dict): Values to merge into the existing configuration.
            save (bool, optional): Whether the preference file should update immediately.

        Returns:
            dict or None: Updated configuration when the script exists.
        """
        if not isinstance(updates, dict):
            return None
        for index, script in enumerate(self.scripts):
            if script.get("id") != script_id:
                continue
            updated_script = dict(script)
            updated_script.update(updates)
            updated_script["id"] = script_id
            self.scripts[index] = normalize_script_configuration(updated_script)
            if save:
                self.save_preferences()
            return copy.deepcopy(self.scripts[index])
        return None

    def remove_script(self, script_id, save=True):
        """Removes one script configuration.

        Args:
            script_id (str): Script identifier to remove.
            save (bool, optional): Whether the preference file should update immediately.

        Returns:
            bool: True when a script was removed.
        """
        for index, script in enumerate(self.scripts):
            if script.get("id") == script_id:
                self.scripts.pop(index)
                if save:
                    self.save_preferences()
                return True
        return False

    def move_script(self, script_id, offset, save=True):
        """Moves a script one or more positions in the execution order.

        Args:
            script_id (str): Script identifier to move.
            offset (int): Signed positional offset.
            save (bool, optional): Whether the preference file should update immediately.

        Returns:
            bool: True when the script order changed.
        """
        for index, script in enumerate(self.scripts):
            if script.get("id") != script_id:
                continue
            target_index = index + int(offset)
            if target_index < 0 or target_index >= len(self.scripts):
                return False
            self.scripts[index], self.scripts[target_index] = (
                self.scripts[target_index],
                self.scripts[index],
            )
            if save:
                self.save_preferences()
            return True
        return False
