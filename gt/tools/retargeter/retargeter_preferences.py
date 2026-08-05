"""Persistent preferences for the Animation Retargeter."""

import copy

PREFS_FILENAME = "retargeter"
PREFERENCE_DEFAULTS = {
    "active_tab": 0,
    "batch_status": False,
    "batch_source_folder": None,
    "batch_target_folder": None,
    "source_animation_path": None,
    "target_rig_path": None,
    "definition_filename": None,
    "override_delete_source": False,
    "override_target_namespace_status": False,
    "override_target_namespace": None,
    "delete_static_channels": True,
    "disable_post_processing": False,
    "definition_setup_filename": None,
    "source_path": None,
    "target_path": None,
    "source_namespace": None,
    "target_namespace": None,
    "linked_status": False,
    "select_scene_targets": True,
    "select_scene_sources": True,
    "definition_folder": None,
    "skip_existing_files": True,
    "multi_process_batch": False,
    "multi_process_max_instances": 6,
    "multi_write_log_file": True,
}


class RetargeterPreferences:
    """Stores and serializes the explicit Retargeter preference schema."""

    def __init__(self, prefs_object=None):
        """Initializes preferences with defaults and loads stored values.

        Args:
            prefs_object (Prefs, optional): Preferences backend used for persistence.
        """
        if prefs_object is None:
            import gt.core.prefs as core_prefs

            prefs_object = core_prefs.Prefs(PREFS_FILENAME)
        self._prefs = prefs_object
        self._values = copy.deepcopy(PREFERENCE_DEFAULTS)
        self.load()

    def get(self, key, default=None):
        """Gets a preference value.

        Args:
            key (str): Preference key.
            default (object, optional): Value returned for an unknown key.

        Returns:
            object: Stored preference value.
        """
        return self._values.get(key, default)

    def set(self, key, value):
        """Sets a preference value when the key belongs to the schema.

        Args:
            key (str): Preference key.
            value (object): Preference value.

        Returns:
            bool: True when the preference was updated.
        """
        if key not in PREFERENCE_DEFAULTS:
            return False
        self._values[key] = self._sanitize_value(key, value)
        return True

    def as_dict(self):
        """Gets a copy of the serializable preference values.

        Returns:
            dict: Current preference data.
        """
        return copy.deepcopy(self._values)

    def load(self):
        """Loads recognized preference keys from the persistence backend."""
        self._prefs.load()
        stored_values = self._prefs.get_raw_preferences()
        if not isinstance(stored_values, dict):
            return
        for key, value in stored_values.items():
            self.set(key, value)

    def save(self):
        """Writes the current explicit preference schema to disk."""
        self._prefs.set_raw_preferences(self.as_dict())
        self._prefs.save()

    @staticmethod
    def _sanitize_value(key, value):
        """Sanitizes values that have constrained UI ranges.

        Args:
            key (str): Preference key.
            value (object): Incoming value.

        Returns:
            object: Sanitized value.
        """
        if key == "active_tab":
            try:
                return max(0, min(2, int(value)))
            except (TypeError, ValueError):
                return PREFERENCE_DEFAULTS[key]
        if key == "multi_process_max_instances":
            try:
                return max(1, min(20, int(value)))
            except (TypeError, ValueError):
                return PREFERENCE_DEFAULTS[key]
        default_value = PREFERENCE_DEFAULTS[key]
        if isinstance(default_value, bool):
            return value if isinstance(value, bool) else default_value
        if value is None or isinstance(value, str):
            return value
        return default_value
