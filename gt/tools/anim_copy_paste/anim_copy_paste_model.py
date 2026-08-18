"""Session state and persistent settings for Copy/Paste Animation."""

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


PREFS_FILENAME = "anim_copy_paste"
PREFS_KEY_STATE = "state"


class AnimCopyPasteConstants:
    """Groups the supported Copy/Paste Animation mode identifiers."""

    class MappingMode:
        """Constants used to resolve copied objects to paste destinations."""

        SELECTION = "selection"
        NAME = "name"
        NAMESPACE = "namespace"

        @classmethod
        def get_available_modes(cls):
            """Gets supported object-to-destination mapping modes.

            Returns:
                list: Mapping-mode identifiers in UI display order.
            """
            return [cls.SELECTION, cls.NAME, cls.NAMESPACE]

    class CopyScope:
        """Constants used to choose which source animation keys are copied."""

        ALL = "all"
        SELECTED = "selected"
        BEFORE_CURRENT = "before_current"
        AFTER_CURRENT = "after_current"

        @classmethod
        def get_available_scopes(cls):
            """Gets supported animation-copy scopes.

            Returns:
                list: Copy-scope identifiers in UI display order.
            """
            return [cls.ALL, cls.SELECTED, cls.BEFORE_CURRENT, cls.AFTER_CURRENT]


class AnimCopyPasteModel:
    """Stores tool settings and portable copied-animation session data."""

    def __init__(self):
        """Initializes the model and loads preferences."""
        self.prefs = Prefs(PREFS_FILENAME)
        self.clip_data = {}
        self.reset_to_defaults()
        self.load_preferences()

    def reset_to_defaults(self):
        """Restores default paste behavior."""
        self.copy_scope = AnimCopyPasteConstants.CopyScope.ALL
        self.mapping_mode = AnimCopyPasteConstants.MappingMode.SELECTION
        self.source_namespace = ""
        self.target_namespace = ""
        self.source_attribute = ""
        self.destination_attribute = ""
        self.paste_at_current_frame = True
        self.paste_frame = 1.0
        self.apply_euler_filter = False

    def load_preferences(self):
        """Loads valid saved settings."""
        state = self.prefs.get_raw_preferences().get(PREFS_KEY_STATE) or {}
        if not isinstance(state, dict):
            return
        copy_scope = str(state.get("copy_scope") or self.copy_scope)
        if copy_scope in self.get_available_copy_scopes():
            self.copy_scope = copy_scope
        mapping_mode = str(state.get("mapping_mode") or self.mapping_mode)
        if mapping_mode in self.get_available_mapping_modes():
            self.mapping_mode = mapping_mode
        self.source_namespace = str(state.get("source_namespace") or "").strip().strip(":")
        self.target_namespace = str(state.get("target_namespace") or "").strip().strip(":")
        self.source_attribute = str(state.get("source_attribute") or "")
        self.destination_attribute = str(state.get("destination_attribute") or "")
        self.paste_at_current_frame = bool(state.get("paste_at_current_frame", self.paste_at_current_frame))
        self.paste_frame = self._get_float(state.get("paste_frame"), self.paste_frame)
        self.apply_euler_filter = bool(state.get("apply_euler_filter", self.apply_euler_filter))

    def save_preferences(self):
        """Saves current settings."""
        self.prefs.preferences[PREFS_KEY_STATE] = self.get_settings()
        self.prefs.save()

    def set_settings(self, settings):
        """Updates settings using view values.

        Args:
            settings (dict): Current view settings.
        """
        settings = settings if isinstance(settings, dict) else {}
        copy_scope = str(settings.get("copy_scope") or self.copy_scope)
        if copy_scope in self.get_available_copy_scopes():
            self.copy_scope = copy_scope
        mapping_mode = str(settings.get("mapping_mode") or self.mapping_mode)
        if mapping_mode in self.get_available_mapping_modes():
            self.mapping_mode = mapping_mode
        self.source_namespace = str(settings.get("source_namespace") or "").strip().strip(":")
        self.target_namespace = str(settings.get("target_namespace") or "").strip().strip(":")
        self.source_attribute = str(settings.get("source_attribute") or "").strip()
        self.destination_attribute = str(settings.get("destination_attribute") or "").strip()
        self.paste_at_current_frame = bool(settings.get("paste_at_current_frame", self.paste_at_current_frame))
        self.paste_frame = self._get_float(settings.get("paste_frame"), self.paste_frame)
        self.apply_euler_filter = bool(settings.get("apply_euler_filter", self.apply_euler_filter))

    def get_settings(self):
        """Gets serializable settings.

        Returns:
            dict: Current tool settings.
        """
        return {
            "copy_scope": self.copy_scope,
            "mapping_mode": self.mapping_mode,
            "source_namespace": self.source_namespace,
            "target_namespace": self.target_namespace,
            "source_attribute": self.source_attribute,
            "destination_attribute": self.destination_attribute,
            "paste_at_current_frame": bool(self.paste_at_current_frame),
            "paste_frame": float(self.paste_frame),
            "apply_euler_filter": bool(self.apply_euler_filter),
        }

    def set_clip_data(self, clip_data):
        """Stores copied animation data for the active tool session.

        Args:
            clip_data (dict): Portable animation clip payload.
        """
        self.clip_data = dict(clip_data or {})

    def has_clip_data(self):
        """Checks whether copy data contains at least one object.

        Returns:
            bool: True when a clip can be pasted.
        """
        return bool(self.clip_data.get("objects"))

    @staticmethod
    def get_available_mapping_modes():
        """Gets the supported source-to-destination mapping modes.

        Returns:
            list: Mapping-mode identifiers.
        """
        return AnimCopyPasteConstants.MappingMode.get_available_modes()

    @staticmethod
    def get_available_copy_scopes():
        """Gets the supported copy scopes.

        Returns:
            list: Copy-scope identifiers.
        """
        return AnimCopyPasteConstants.CopyScope.get_available_scopes()

    @staticmethod
    def _get_float(value, fallback):
        """Gets a numeric value with a safe fallback.

        Args:
            value (object): Candidate numeric value.
            fallback (float): Value returned when conversion fails.

        Returns:
            float: Converted candidate or fallback.
        """
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(fallback)
