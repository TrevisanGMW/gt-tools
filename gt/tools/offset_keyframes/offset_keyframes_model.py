"""Session settings and persistence for Offset Keyframes."""

try:
    from gt.core.prefs import Prefs
except ImportError:
    class Prefs:
        """Minimal in-memory preference fallback used outside Maya."""

        def __init__(self, prefs_name):
            """Initializes empty fallback preferences.

            Args:
                prefs_name (str): Preference identifier retained for parity.
            """
            self.prefs_name = prefs_name
            self.preferences = {}

        def get_raw_preferences(self):
            """Gets fallback preference data.

            Returns:
                dict: In-memory preference data.
            """
            return self.preferences

        def save(self):
            """Matches the persistent preference API without writing data."""


PREFS_FILENAME = "offset_keyframes"
PREFS_KEY_STATE = "state"
SCOPE_ALL = "all"
SCOPE_SELECTED = "selected"
SCOPE_CURRENT = "current"
SCOPE_PLAYBACK = "playback"


class OffsetKeyframesModel:
    """Stores Offset Keyframes settings independently of Maya and Qt."""

    def __init__(self):
        """Initializes settings and loads saved preferences."""
        self.prefs = Prefs(PREFS_FILENAME)
        self.reset_to_defaults()
        self.load_preferences()

    def reset_to_defaults(self):
        """Restores the default tool settings."""
        self.offset_amount = 1.0
        self.scope = SCOPE_ALL
        self.stagger_step = 1.0
        self.apply_euler_filter = False

    def load_preferences(self):
        """Loads persisted settings when they are valid."""
        state = self.prefs.get_raw_preferences().get(PREFS_KEY_STATE) or {}
        if not isinstance(state, dict):
            return
        self.offset_amount = self._get_float(state.get("offset_amount"), self.offset_amount)
        self.stagger_step = self._get_float(state.get("stagger_step"), self.stagger_step)
        saved_scope = str(state.get("scope") or self.scope)
        if saved_scope in self.get_available_scopes():
            self.scope = saved_scope
        self.apply_euler_filter = bool(state.get("apply_euler_filter", self.apply_euler_filter))

    def save_preferences(self):
        """Saves the current settings to the package preference store."""
        self.prefs.preferences[PREFS_KEY_STATE] = self.get_settings()
        self.prefs.save()

    def get_settings(self):
        """Gets the current serializable settings.

        Returns:
            dict: Tool settings keyed by their preference names.
        """
        return {
            "offset_amount": float(self.offset_amount),
            "scope": self.scope,
            "stagger_step": float(self.stagger_step),
            "apply_euler_filter": bool(self.apply_euler_filter),
        }

    def set_settings(self, settings):
        """Updates settings from view data.

        Args:
            settings (dict): Tool settings supplied by the view.
        """
        settings = settings if isinstance(settings, dict) else {}
        self.offset_amount = self._get_float(settings.get("offset_amount"), self.offset_amount)
        self.stagger_step = self._get_float(settings.get("stagger_step"), self.stagger_step)
        scope = str(settings.get("scope") or self.scope)
        if scope in self.get_available_scopes():
            self.scope = scope
        self.apply_euler_filter = bool(settings.get("apply_euler_filter", self.apply_euler_filter))

    @staticmethod
    def get_available_scopes():
        """Gets the supported key-offset scopes.

        Returns:
            list: Scope identifiers.
        """
        return [SCOPE_ALL, SCOPE_SELECTED, SCOPE_CURRENT, SCOPE_PLAYBACK]

    @staticmethod
    def _get_float(value, fallback):
        """Gets a float with a fallback for invalid values.

        Args:
            value (object): Candidate value.
            fallback (float): Value returned when conversion fails.

        Returns:
            float: Converted candidate or fallback.
        """
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(fallback)
