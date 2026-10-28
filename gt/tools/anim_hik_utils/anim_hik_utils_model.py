"""Import-safe state and validation for HumanIK Utilities."""

import json
import logging
import math
import re
import xml.etree.ElementTree as ElementTree

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS = {
    "affect_center": False,
    "world_space": False,
    "force_proxy": False,
    "prefix": "",
    "last_directory": "",
}


def validate_node_name(name):
    """Validates a Maya node name before passing it to native HumanIK commands.

    Args:
        name (str): Node name, optionally including namespaces.

    Returns:
        str: Trimmed name.

    Raises:
        ValueError: If the name contains invalid characters.
    """
    name = str(name).strip()
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(?::[A-Za-z_][A-Za-z0-9_]*)*", name):
        raise ValueError("Use letters, numbers, underscores, and optional namespaces for the name.")
    return name


def read_definition(file_path, prefix=""):
    """Reads native HumanIK XML and resolves its requested bone names.

    Args:
        file_path (str): Existing XML file.
        prefix (str): Namespace prefix (for example "hero:") added to every bone name.

    Returns:
        list: Ordered pairs of HumanIK slots and requested bone names.

    Raises:
        ValueError: If the XML schema or mapping options are invalid.
    """
    root = ElementTree.parse(file_path).getroot()
    if root.tag != "config_root" or root.find("match_list") is None:
        raise ValueError("Choose a native HumanIK XML match list (config_root / match_list).")
    mappings = []
    seen_slots = set()
    for item in root.findall("./match_list/item"):
        slot, bone = item.get("key", ""), item.get("value", "")
        if not slot or not bone:
            continue
        if slot in seen_slots:
            raise ValueError(f"Duplicate HumanIK slot in XML: {slot}")
        seen_slots.add(slot)
        mappings.append((slot, f"{prefix}{bone}"))
    if not mappings:
        raise ValueError("The XML file has no populated bone mappings.")
    return mappings


def next_prefix(matching_prefixes, current_prefix):
    """Picks the prefix that follows the current one, wrapping around.

    Args:
        matching_prefixes (list): Candidate prefixes in a stable order.
        current_prefix (str): Prefix currently entered by the user.

    Returns:
        str: Following prefix, the first one when the current is not a candidate, or "" when empty.
    """
    if not matching_prefixes:
        return ""
    if current_prefix not in matching_prefixes:
        return matching_prefixes[0]
    return matching_prefixes[(matching_prefixes.index(current_prefix) + 1) % len(matching_prefixes)]


def read_properties(file_path):
    """Reads the flat property dictionary shared with the batch retarget task.

    Args:
        file_path (str): Existing JSON file.

    Returns:
        dict: Valid scalar properties.

    Raises:
        ValueError: If the file is empty or contains unsupported values.
    """
    with open(file_path, "r", encoding="utf-8") as stream:
        properties = json.load(stream)
    if not isinstance(properties, dict) or not properties:
        raise ValueError("Choose a non-empty HumanIK properties dictionary.")
    for name, value in properties.items():
        if not name or type(value) not in (str, bool, int, float):
            raise ValueError(f"Invalid HumanIK property: {name}")
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"Non-finite HumanIK property: {name}")
    return properties


class AnimHikUtilsModel:
    """Owns persistent options and transient character selection."""

    def __init__(self, prefs=None):
        """Loads optional preferences without importing the Maya runtime.

        Args:
            prefs (Prefs or bool, optional): Injected store; False disables persistence.
        """
        self.character = ""
        self.copied_properties = {}
        self.settings = dict(DEFAULT_SETTINGS)
        self.prefs = prefs
        try:
            if prefs is None:
                from gt.core.prefs import Prefs

                self.prefs = Prefs("anim_hik_utils")
            if self.prefs:
                self.update_settings(self.prefs.get_raw_preferences().get("state", {}))
        except Exception:
            logger.debug("HumanIK preferences unavailable; using session settings.", exc_info=True)
            self.prefs = False

    def update_settings(self, settings):
        """Accepts only known settings with their expected types.

        Args:
            settings (dict): Serialized or view-provided settings.
        """
        if not isinstance(settings, dict):
            return
        for key, default in DEFAULT_SETTINGS.items():
            value = settings.get(key, self.settings[key])
            if type(value) is type(default):
                self.settings[key] = value

    def save_preferences(self):
        """Persists tool options, excluding scene-specific character names."""
        if self.prefs:
            self.prefs.set_raw_preferences({"state": dict(self.settings)})
            self.prefs.save()

    def reset_to_defaults(self):
        """Resets and persists the tool options."""
        self.settings = dict(DEFAULT_SETTINGS)
        self.save_preferences()
