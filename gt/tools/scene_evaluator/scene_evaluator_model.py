"""Persistent settings and portable presets for Scene Evaluator."""

import logging

from gt.core import io as core_io


logger = logging.getLogger(__name__)
PRESET_FORMAT = "gt-tools.scene_evaluator"
PRESET_VERSION = 3
ACTION_SCRIPT_FILENAME = "<Scene Evaluator Action>"
ACTION_REQUIRE_PASS = "require_pass"
ACTION_CONFIRM_BYPASS = "confirm_bypass"
ACTION_ALWAYS_ALLOW = "always_allow"
DEFAULT_SETTINGS = {
    "format": PRESET_FORMAT,
    "version": PRESET_VERSION,
    "validators": [],
    "action": {"enabled": False, "label": "", "script": "", "mode": ACTION_REQUIRE_PASS},
}


class SceneEvaluatorModel:
    """Stores validator choices and the optional Python action."""

    def __init__(self, prefs):
        """Loads settings from the tool's preferences.

        Args:
            prefs (Prefs): Preferences backend.
        """
        self.prefs = prefs
        try:
            self.settings = normalize_settings(self.prefs.get_raw_preferences() or DEFAULT_SETTINGS)
        except ValueError as error:
            logger.warning("Could not load Scene Evaluator preferences. %s", error)
            self.settings = normalize_settings(DEFAULT_SETTINGS)

    def save_settings(self, settings):
        """Validates settings and commits them to Prefs.

        Args:
            settings (dict): Validator choices and action settings.

        Raises:
            ValueError: The settings are invalid.
            OSError: The preferences could not be saved.
        """
        settings = normalize_settings(settings)
        previous_preferences = self.prefs.get_raw_preferences()
        self.prefs.set_raw_preferences(settings)
        try:
            if not self.prefs.save():
                raise OSError("Could not save Scene Evaluator preferences.")
        except OSError:
            self.prefs.set_raw_preferences(previous_preferences)
            raise
        self.settings = settings

    @staticmethod
    def read_preset(path):
        """Reads and validates a JSON preset.

        Args:
            path (str): Path to a Scene Evaluator preset.

        Returns:
            dict: Validated settings. Action-only presets omit validator choices.
        """
        return normalize_settings(core_io.read_json_dict(path, raise_errors=True), allow_partial_preset=True)

    @staticmethod
    def write_preset(path, settings, include_validators=True):
        """Writes validator choices and action settings to a JSON preset.

        Args:
            path (str): Destination path.
            settings (dict): Settings to export.
            include_validators (bool, optional): Includes the selected validator IDs by default.

        Raises:
            ValueError: The settings are invalid.
            OSError: The preset could not be written.
        """
        preset = normalize_settings(settings)
        if not include_validators:
            preset.pop("validators")
        if core_io.write_json(path, preset) is None:
            raise OSError("Could not write the Scene Evaluator preset.")


def normalize_settings(settings, allow_partial_preset=False):
    """Validates and copies a versioned Scene Evaluator settings dictionary.

    Args:
        settings (dict): Raw preferences or preset data.
        allow_partial_preset (bool, optional): Allows current presets to omit validator choices.

    Returns:
        dict: Settings with unique validator IDs and a cleaned button label.

    Raises:
        ValueError: The settings have an unsupported format or invalid fields.
    """
    if not isinstance(settings, dict) or settings.get("format") != PRESET_FORMAT:
        raise ValueError("Expected a Scene Evaluator preset.")
    version = settings.get("version")
    if type(version) is not int or version not in (1, 2, PRESET_VERSION):
        raise ValueError("This Scene Evaluator preset version is unsupported.")

    action = settings.get("action")
    if not isinstance(action, dict):
        raise ValueError("Expected action button settings.")
    enabled = action.get("enabled")
    label = action.get("label")
    script = action.get("script")
    if not isinstance(enabled, bool):
        raise ValueError("Expected a boolean setting for the action button.")
    if not isinstance(label, str) or not isinstance(script, str):
        raise ValueError("Expected text for the button label and Python script.")
    if version == 1:
        require_pass = action.get("require_pass")
        if not isinstance(require_pass, bool):
            raise ValueError("Expected a boolean validation requirement in the preset.")
        mode = ACTION_REQUIRE_PASS if require_pass else ACTION_ALWAYS_ALLOW
    else:
        mode = action.get("mode")
        if mode not in (ACTION_REQUIRE_PASS, ACTION_CONFIRM_BYPASS, ACTION_ALWAYS_ALLOW):
            raise ValueError("Invalid action button mode.")
    label = label.strip()
    if enabled:
        if not label or not script.strip():
            raise ValueError("Enter a button label and Python script to enable the action.")
        try:
            compile(script, ACTION_SCRIPT_FILENAME, "exec")
        except SyntaxError as error:
            raise ValueError(f"Python action line {error.lineno}: {error.msg}") from error

    normalized = {
        "format": PRESET_FORMAT,
        "version": PRESET_VERSION,
        "action": {"enabled": enabled, "label": label, "script": script, "mode": mode},
    }
    if allow_partial_preset and version == PRESET_VERSION and "validators" not in settings:
        return normalized

    validators = settings.get("validators")
    if not isinstance(validators, list) or any(
        not isinstance(validator_id, str) or not validator_id.strip() for validator_id in validators
    ):
        raise ValueError("Expected a list of validator IDs.")
    normalized["validators"] = list(dict.fromkeys(validators))
    return normalized
