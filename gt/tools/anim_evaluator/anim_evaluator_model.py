"""
Animation Evaluator Model - Import-safe state, template/preset handling, and preferences.
"""

from gt.core.motion_eval import checks_base
from gt.core.motion_eval import presets
from gt.core.motion_eval import templates
from gt.core.motion_eval import scene_io
from gt.core.motion_eval import sampling
import logging
import json
import os

logger = logging.getLogger(__name__)

TEMPLATE_SOURCE_BUILTIN = "builtin"
TEMPLATE_SOURCE_FILE = "file"
TEMPLATE_SOURCE_CUSTOM = "custom"

DEFAULT_SETTINGS = {
    "template_source": TEMPLATE_SOURCE_BUILTIN,
    "template_key": templates.DEFAULT_TEMPLATE_KEY,
    "template_path": "",
    "custom_template": {},
    "preset": presets.create_preset(mode=checks_base.MODE_BIPED),
    "range_mode": sampling.RANGE_PLAYBACK,
    "custom_start": 1,
    "custom_end": 120,
    "general_scope": sampling.SCOPE_ALL_JOINTS,
    "node_list": "",
    "score_target_mode": scene_io.TARGET_DEDICATED_NODE,
    "score_node_name": scene_io.DEFAULT_NODE_NAME,
    "score_attribute": scene_io.DEFAULT_SCORE_ATTRIBUTE,
    "report_attribute": scene_io.DEFAULT_REPORT_ATTRIBUTE,
    "write_report_attribute": True,
    "last_directory": "",
}


class AnimEvaluatorModel:
    """Owns persistent tool settings, the active template, the preset, and the last report."""

    def __init__(self, prefs=None):
        """Loads preferences lazily without importing Maya.

        Args:
            prefs (Prefs or bool, optional): Injected store; False disables persistence.
        """
        self.settings = json.loads(json.dumps(DEFAULT_SETTINGS))
        self.template = templates.get_builtin_template(templates.DEFAULT_TEMPLATE_KEY)
        self.last_report = None
        self.prefs = prefs
        try:
            if prefs is None:
                from gt.core.prefs import Prefs

                self.prefs = Prefs("anim_evaluator")
            if self.prefs:
                self.update_settings(self.prefs.get_raw_preferences().get("state", {}))
        except Exception:
            logger.debug("Animation Evaluator preferences unavailable; using session settings.", exc_info=True)
            self.prefs = False
        self.load_active_template(quiet=True)

    # ------------------------------------------------ Settings ------------------------------------------------
    def update_settings(self, settings):
        """Accepts known settings with their expected types.

        Args:
            settings (dict): Serialized or view-provided settings.
        """
        if not isinstance(settings, dict):
            return
        for key, default in DEFAULT_SETTINGS.items():
            if key not in settings:
                continue
            value = settings[key]
            if isinstance(default, bool) and isinstance(value, bool):
                self.settings[key] = value
            elif isinstance(default, int) and not isinstance(default, bool) and isinstance(value, (int, float)):
                self.settings[key] = int(value)
            elif isinstance(default, str) and isinstance(value, str):
                self.settings[key] = value
            elif isinstance(default, dict) and isinstance(value, dict):
                self.settings[key] = value
        self.settings["preset"] = presets.compact_preset(self.settings["preset"])

    def get_setting(self, key):
        """Gets a setting value.

        Args:
            key (str): Setting key.

        Returns:
            object: Setting value.
        """
        return self.settings.get(key, DEFAULT_SETTINGS.get(key))

    def set_setting(self, key, value):
        """Sets a setting and saves preferences.

        Args:
            key (str): Setting key.
            value (object): New value.
        """
        self.update_settings({key: value})
        self.save_preferences()

    def save_preferences(self):
        """Persists settings."""
        if self.prefs:
            self.prefs.set_raw_preferences({"state": self.settings})
            self.prefs.save()

    def reset_to_defaults(self):
        """Resets settings, template, and preset, then saves."""
        self.settings = json.loads(json.dumps(DEFAULT_SETTINGS))
        self.template = templates.get_builtin_template(templates.DEFAULT_TEMPLATE_KEY)
        self.last_report = None
        self.save_preferences()

    # ------------------------------------------------ Preset ------------------------------------------------
    def get_preset(self):
        """Gets the compact preset.

        Returns:
            dict: Stored preset.
        """
        return presets.copy_preset(self.settings["preset"])

    def set_preset(self, preset):
        """Stores a preset.

        Args:
            preset (dict): Stored or resolved preset.
        """
        self.settings["preset"] = presets.compact_preset(preset)
        self.save_preferences()

    def get_mode(self):
        """Gets the evaluation mode from the preset.

        Returns:
            str: Evaluation mode.
        """
        return presets.resolve_preset(self.settings["preset"])["mode"]

    def set_mode(self, mode):
        """Sets the evaluation mode.

        Args:
            mode (str): Evaluation mode.
        """
        resolved = presets.resolve_preset(self.settings["preset"])
        resolved["mode"] = mode
        self.set_preset(resolved)

    # ------------------------------------------------ Template ------------------------------------------------
    def load_active_template(self, quiet=False):
        """Loads the template described by the settings.

        Args:
            quiet (bool): Log failures at debug level instead of raising.

        Returns:
            dict: Active template.

        Raises:
            IOError, ValueError: If a file template cannot be loaded and quiet is False.
        """
        source = self.settings["template_source"]
        try:
            if source == TEMPLATE_SOURCE_FILE and self.settings["template_path"]:
                self.template = templates.load_template(self.settings["template_path"])
            elif source == TEMPLATE_SOURCE_CUSTOM and self.settings["custom_template"]:
                self.template = templates.normalize_template(self.settings["custom_template"])
            else:
                key = self.settings["template_key"]
                if key not in templates.BUILTIN_TEMPLATES:
                    key = templates.DEFAULT_TEMPLATE_KEY
                self.settings["template_source"] = TEMPLATE_SOURCE_BUILTIN
                self.settings["template_key"] = key
                self.template = templates.get_builtin_template(key)
        except (IOError, OSError, ValueError):
            if not quiet:
                raise
            logger.debug("Unable to load the saved skeleton template; using the default.", exc_info=True)
            self.settings["template_source"] = TEMPLATE_SOURCE_BUILTIN
            self.settings["template_key"] = templates.DEFAULT_TEMPLATE_KEY
            self.template = templates.get_builtin_template(templates.DEFAULT_TEMPLATE_KEY)
        return self.template

    def select_builtin_template(self, template_key):
        """Activates a built-in template.

        Args:
            template_key (str): Built-in key.

        Returns:
            dict: Active template.
        """
        self.settings["template_source"] = TEMPLATE_SOURCE_BUILTIN
        self.settings["template_key"] = template_key
        self.save_preferences()
        return self.load_active_template()

    def load_template_file(self, file_path):
        """Loads and activates a template file.

        Args:
            file_path (str): Template JSON path.

        Returns:
            dict: Active template.
        """
        template = templates.load_template(file_path)
        self.settings["template_source"] = TEMPLATE_SOURCE_FILE
        self.settings["template_path"] = file_path
        self.settings["last_directory"] = os.path.dirname(file_path)
        self.template = template
        self.save_preferences()
        return template

    def update_template(self, template):
        """Stores an edited template as the custom (unsaved) template.

        Args:
            template (dict): Edited template.

        Returns:
            dict: Active template.
        """
        self.template = templates.normalize_template(template)
        self.settings["template_source"] = TEMPLATE_SOURCE_CUSTOM
        self.settings["custom_template"] = self.template
        self.save_preferences()
        return self.template

    def save_template_file(self, file_path):
        """Saves the active template and activates the saved file.

        Args:
            file_path (str): Destination path.

        Returns:
            str: Written path.
        """
        self.template["name"] = self.template.get("name") or os.path.splitext(os.path.basename(file_path))[0]
        templates.save_template(self.template, file_path)
        self.settings["template_source"] = TEMPLATE_SOURCE_FILE
        self.settings["template_path"] = file_path
        self.settings["last_directory"] = os.path.dirname(file_path)
        self.save_preferences()
        return file_path

    def get_template_source_label(self):
        """Gets a readable description of the template source.

        Returns:
            str: Source label.
        """
        source = self.settings["template_source"]
        if source == TEMPLATE_SOURCE_FILE:
            return f"Custom Skeleton file: {self.settings['template_path']}"
        if source == TEMPLATE_SOURCE_CUSTOM:
            return "Custom Skeleton (edited, unsaved) - use Save As to keep it"
        return "Built-in"

    def uses_skeleton(self):
        """Checks whether the current mode and node scope need the skeleton.

        Returns:
            bool: True in Biped mode or with the Template Joints scope.
        """
        return (self.get_mode() == checks_base.MODE_BIPED
                or self.settings["general_scope"] == sampling.SCOPE_TEMPLATE_JOINTS)

    # ------------------------------------------------ Helpers ------------------------------------------------
    def get_node_names(self):
        """Gets the node list setting as names.

        Returns:
            list: Node names.
        """
        return [name.strip() for name in self.settings["node_list"].replace(";", ",").split(",") if name.strip()]

    def get_score_options(self):
        """Gets the score attribute options.

        Returns:
            dict: Keyword arguments for scene_io.write_score.
        """
        return {
            "target_mode": self.settings["score_target_mode"],
            "node_name": self.settings["score_node_name"],
            "score_attribute": self.settings["score_attribute"],
            "report_attribute": self.settings["report_attribute"],
            "write_report": self.settings["write_report_attribute"],
        }

    def get_last_directory(self):
        """Gets the folder used by file dialogs.

        Returns:
            str: Folder path or empty string.
        """
        return self.settings.get("last_directory") or ""
