"""
Sine Attributes Model

This module contains the SineAttributesModel class, which handles the data logic,
settings, and persistence for the Sine Attributes tool.
"""
import logging
import gt.core.prefs as core_prefs

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

PREFS_FILENAME = "sine_attributes"
PREFS_KEY_STATE = "state"


class SineAttributesModel:
    """Model used by the Sine Attributes tool to store and persist preferences."""

    def __init__(self):
        """Initializes the SineAttributesModel object."""
        self.prefs = core_prefs.Prefs(PREFS_FILENAME)
        self.sine_prefix = "sine"
        self.add_absolute_output = False
        self.nice_name_prefix = True
        self.load_preferences()

    def reset_to_defaults(self):
        """Resets all model settings to their default values."""
        self.sine_prefix = "sine"
        self.add_absolute_output = False
        self.nice_name_prefix = True

    def load_preferences(self):
        """Loads persisted preferences from the preferences file."""
        data = self.prefs.get_raw_preferences().get(PREFS_KEY_STATE) or {}
        if not isinstance(data, dict):
            return

        self.sine_prefix = data.get("sine_prefix", "sine")
        self.add_absolute_output = bool(data.get("add_absolute_output", False))
        self.nice_name_prefix = bool(data.get("nice_name_prefix", True))

    def save_preferences(self):
        """Saves current settings as persisted preferences."""
        state = {
            "sine_prefix": self.sine_prefix,
            "add_absolute_output": self.add_absolute_output,
            "nice_name_prefix": self.nice_name_prefix,
        }
        self.prefs.set_raw_preferences({PREFS_KEY_STATE: state})
        self.prefs.save()
