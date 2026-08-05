"""Persistent state and pure data helpers for Transfer Transforms."""

import copy
import json
import logging


logger = logging.getLogger(__name__)


class TransferTransformsModel:
    """Stores persistent transfer settings and transform clipboard values."""

    PREFS_NAME = "transfer_transforms"
    ATTRIBUTES = ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz")
    DEFAULT_SETTINGS = {
        "left_tag": "L_",
        "right_tag": "R_",
        "tx_enabled": True,
        "tx_inverted": False,
        "ty_enabled": True,
        "ty_inverted": False,
        "tz_enabled": True,
        "tz_inverted": False,
        "rx_enabled": True,
        "rx_inverted": False,
        "ry_enabled": True,
        "ry_inverted": False,
        "rz_enabled": True,
        "rz_inverted": False,
        "sx_enabled": True,
        "sx_inverted": False,
        "sy_enabled": True,
        "sy_inverted": False,
        "sz_enabled": True,
        "sz_inverted": False,
    }
    DEFAULT_CLIPBOARD = {
        "tx": 0.0,
        "ty": 0.0,
        "tz": 0.0,
        "rx": 0.0,
        "ry": 0.0,
        "rz": 0.0,
        "sx": 1.0,
        "sy": 1.0,
        "sz": 1.0,
    }

    def __init__(self, preferences=None):
        """Initializes model state and loads persistent settings.

        Args:
            preferences (Prefs, optional): Injected preference object for tests.
        """
        self.settings = copy.deepcopy(self.DEFAULT_SETTINGS)
        self.clipboard = copy.deepcopy(self.DEFAULT_CLIPBOARD)
        self._preferences = preferences
        self.load_preferences()

    def _get_preferences(self):
        """Gets or lazily creates the preference object.

        Returns:
            Prefs or None: Preference object when available.
        """
        if self._preferences is not None:
            return self._preferences
        try:
            from gt.core.prefs import Prefs

            self._preferences = Prefs(self.PREFS_NAME)
        except Exception as exception:
            logger.debug("Unable to initialize Transfer Transforms preferences: %s", exception)
        return self._preferences

    def load_preferences(self):
        """Loads and sanitizes supported settings from Prefs."""
        preferences = self._get_preferences()
        if not preferences:
            return
        try:
            stored_settings = preferences.get_raw_preferences()
        except Exception as exception:
            logger.debug("Unable to load Transfer Transforms preferences: %s", exception)
            return
        for key, default_value in self.DEFAULT_SETTINGS.items():
            value = stored_settings.get(key, default_value)
            self.settings[key] = self._sanitize_setting(key, value)
        stored_clipboard = stored_settings.get("clipboard", {})
        if not isinstance(stored_clipboard, dict):
            stored_clipboard = {}
        for attribute, default_value in self.DEFAULT_CLIPBOARD.items():
            try:
                self.clipboard[attribute] = float(stored_clipboard.get(attribute, default_value))
            except (TypeError, ValueError):
                self.clipboard[attribute] = default_value

    def save_preferences(self):
        """Writes all persistent settings through Prefs.

        Returns:
            bool: True when preferences were saved.
        """
        preferences = self._get_preferences()
        if not preferences:
            return False
        try:
            payload = copy.deepcopy(self.settings)
            payload["clipboard"] = copy.deepcopy(self.clipboard)
            preferences.set_raw_preferences(payload)
            preferences.save()
            return True
        except Exception as exception:
            logger.warning("Unable to save Transfer Transforms preferences: %s", exception)
            return False

    def set_setting(self, key, value, save=True):
        """Updates one supported persistent setting.

        Args:
            key (str): Setting key.
            value (object): New setting value.
            save (bool, optional): Whether to save immediately.

        Returns:
            bool: True when the setting was accepted.
        """
        if key not in self.DEFAULT_SETTINGS:
            return False
        self.settings[key] = self._sanitize_setting(key, value)
        if save:
            self.save_preferences()
        return True

    def reset_preferences(self):
        """Restores and saves default settings and clipboard values."""
        self.settings = copy.deepcopy(self.DEFAULT_SETTINGS)
        self.clipboard = copy.deepcopy(self.DEFAULT_CLIPBOARD)
        self.save_preferences()

    def get_transform_options(self):
        """Builds enabled and inversion data for every transform channel.

        Returns:
            list: Dictionaries containing attribute, enabled, and inverted values.
        """
        options = []
        for attribute in self.ATTRIBUTES:
            options.append(
                {
                    "attribute": attribute,
                    "enabled": self.settings.get(f"{attribute}_enabled", True),
                    "inverted": self.settings.get(f"{attribute}_inverted", False),
                }
            )
        return options

    def set_clipboard_value(self, attribute, value, save=True):
        """Updates one persistent clipboard value.

        Args:
            attribute (str): Transform channel name.
            value (float): Transform value.
            save (bool, optional): Whether to save preferences immediately.

        Returns:
            bool: True when the value was accepted.
        """
        if attribute not in self.DEFAULT_CLIPBOARD:
            return False
        try:
            self.clipboard[attribute] = float(value)
        except (TypeError, ValueError):
            return False
        if save:
            self.save_preferences()
        return True

    def set_clipboard(self, values, save=True):
        """Updates known persistent clipboard values.

        Args:
            values (dict): Attribute-to-value mapping.
            save (bool, optional): Whether to save preferences after updating.
        """
        for attribute, value in (values or {}).items():
            self.set_clipboard_value(attribute, value, save=False)
        if save:
            self.save_preferences()

    @staticmethod
    def build_side_pairs(nodes, left_tag, right_tag):
        """Pairs selected nodes whose names differ only by their side tag.

        Args:
            nodes (list): Ordered node names.
            left_tag (str): Left-side name token.
            right_tag (str): Right-side name token.

        Returns:
            list: Unique ``(left_node, right_node)`` tuples.
        """
        if not left_tag or not right_tag or left_tag == right_tag:
            return []
        left_nodes = [node for node in nodes or [] if left_tag in node]
        right_lookup = {}
        for node in nodes or []:
            if right_tag in node:
                right_lookup.setdefault(node.replace(right_tag, "", 1), node)
        pairs = []
        for left_node in left_nodes:
            match_key = left_node.replace(left_tag, "", 1)
            right_node = right_lookup.get(match_key)
            if right_node:
                pairs.append((left_node, right_node))
        return pairs

    @staticmethod
    def write_transform_file(file_path, records, version):
        """Writes transform records to a readable JSON file.

        Args:
            file_path (str): Destination JSON path.
            records (list): Serializable transform records.
            version (str): Tool version.
        """
        payload = {"tool": "transfer_transforms", "version": str(version), "objects": records}
        with open(file_path, "w", encoding="utf-8") as output_file:
            json.dump(payload, output_file, indent=4)

    @staticmethod
    def read_transform_file(file_path):
        """Reads and validates transform records from JSON.

        Args:
            file_path (str): Source JSON path.

        Returns:
            list: Validated transform record dictionaries.

        Raises:
            ValueError: When the file does not use the current schema.
        """
        with open(file_path, "r", encoding="utf-8") as input_file:
            payload = json.load(input_file)
        if payload.get("tool") != "transfer_transforms" or not isinstance(payload.get("objects"), list):
            raise ValueError("The selected file is not a Transfer Transforms file.")
        return payload.get("objects")

    @staticmethod
    def _sanitize_setting(key, value):
        """Sanitizes a supported preference value.

        Args:
            key (str): Setting key.
            value (object): Stored value.

        Returns:
            object: Sanitized value.
        """
        if key.endswith("_enabled") or key.endswith("_inverted"):
            return bool(value)
        return str(value or "")
