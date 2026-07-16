"""State and pure validation logic for Connect Attributes."""

import logging


logger = logging.getLogger(__name__)


class ConnectAttributesModel:
    """Stores persistent options and transient scene selections."""

    PREFS_NAME = "connect_attributes"
    NODE_TYPES = ("plusMinusAverage", "multiplyDivide", "condition")
    OPERATIONS = ("connect", "disconnect")
    DEFAULT_SETTINGS = {
        "use_selection": True,
        "operation": "connect",
        "source_attribute": "translate",
        "target_attributes": "translate, rotate, scale",
        "add_reverse_node": False,
        "force_connection": False,
        "use_utility_node": False,
        "utility_node_type": "plusMinusAverage",
        "use_shared_input": False,
        "shared_input_node_type": "condition",
    }

    def __init__(self, preferences=None):
        """Initializes settings and loads preferences.

        Args:
            preferences (Prefs, optional): Injected preference object, primarily for tests.
        """
        self.settings = dict(self.DEFAULT_SETTINGS)
        self.source_object = None
        self.target_objects = []
        self._preferences = preferences
        self.load_preferences()

    @staticmethod
    def parse_attributes(value):
        """Parses comma-separated attribute names and removes duplicates.

        Args:
            value (str): Comma-separated attribute text.

        Returns:
            list: Clean, unique attribute names in input order.
        """
        attributes = []
        for item in str(value or "").split(","):
            attribute = item.strip()
            if attribute and attribute not in attributes:
                attributes.append(attribute)
        return attributes

    @staticmethod
    def normalize_nodes(nodes):
        """Removes empty and duplicate node names while preserving order.

        Args:
            nodes (list): Scene node names.

        Returns:
            list: Clean, unique node names.
        """
        normalized = []
        for node in nodes or []:
            node_name = str(node or "").strip()
            if node_name and node_name not in normalized:
                normalized.append(node_name)
        return normalized

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
            logger.debug("Unable to initialize Connect Attributes preferences: %s", exception)
        return self._preferences

    def load_preferences(self):
        """Loads supported values from Prefs without touching scene state."""
        preferences = self._get_preferences()
        if not preferences:
            return
        try:
            stored_settings = preferences.get_raw_preferences()
        except Exception as exception:
            logger.debug("Unable to load Connect Attributes preferences: %s", exception)
            return
        for key, default_value in self.DEFAULT_SETTINGS.items():
            value = stored_settings.get(key, default_value)
            self.settings[key] = self._sanitize_setting(key, value)

    def save_preferences(self):
        """Writes all persistent settings through Prefs.

        Returns:
            bool: True when preferences were saved.
        """
        preferences = self._get_preferences()
        if not preferences:
            return False
        try:
            preferences.set_raw_preferences(dict(self.settings))
            preferences.save()
            return True
        except Exception as exception:
            logger.warning("Unable to save Connect Attributes preferences: %s", exception)
            return False

    def set_setting(self, key, value, save=True):
        """Updates one supported setting.

        Args:
            key (str): Setting key.
            value (object): New setting value.
            save (bool, optional): Whether to immediately save preferences.

        Returns:
            bool: True when the setting exists and was updated.
        """
        if key not in self.DEFAULT_SETTINGS:
            return False
        self.settings[key] = self._sanitize_setting(key, value)
        if save:
            self.save_preferences()
        return True

    def reset_preferences(self):
        """Restores and saves default persistent settings."""
        self.settings = dict(self.DEFAULT_SETTINGS)
        self.save_preferences()

    def set_source_object(self, source_object):
        """Stores the loaded source for the current Maya session.

        Args:
            source_object (str or None): Loaded source node.
        """
        self.source_object = str(source_object) if source_object else None

    def set_target_objects(self, target_objects):
        """Stores loaded targets for the current Maya session.

        Args:
            target_objects (list): Loaded target nodes.
        """
        self.target_objects = self.normalize_nodes(target_objects)

    def clear_loaded_nodes(self):
        """Clears transient source and target nodes."""
        self.source_object = None
        self.target_objects = []

    def build_request(self, selection=None):
        """Builds a normalized operation request from settings and scene input.

        Args:
            selection (list, optional): Ordered Maya selection when selection mode is active.

        Returns:
            tuple: Request dictionary and a list of validation messages.
        """
        is_connect = self.settings.get("operation") == "connect"
        if self.settings.get("use_selection"):
            nodes = self.normalize_nodes(selection)
            source_object = nodes[0] if nodes and is_connect else None
            target_objects = nodes[1:] if is_connect else nodes
        else:
            source_object = self.source_object if is_connect else None
            target_objects = self.normalize_nodes(self.target_objects)

        target_objects = [node for node in target_objects if node != source_object]
        request = dict(self.settings)
        request["source_object"] = source_object
        request["target_objects"] = target_objects
        request["source_attribute"] = str(self.settings.get("source_attribute") or "").strip()
        request["target_attributes"] = self.parse_attributes(self.settings.get("target_attributes"))
        return request, self.validate_request(request)

    @staticmethod
    def validate_request(request):
        """Validates a normalized operation request.

        Args:
            request (dict): Request produced by :meth:`build_request`.

        Returns:
            list: Human-readable validation messages. An empty list means valid.
        """
        issues = []
        if request.get("operation") == "connect" and not request.get("source_object"):
            issues.append("Choose one source object.")
        if not request.get("target_objects"):
            issues.append("Choose at least one target object.")
        if request.get("operation") == "connect" and not request.get("source_attribute"):
            issues.append("Enter a source attribute.")
        if not request.get("target_attributes"):
            issues.append("Enter at least one target attribute.")
        return issues

    @staticmethod
    def build_preview_lines(request):
        """Builds readable lines describing every requested plug operation.

        Args:
            request (dict): Validated request produced by :meth:`build_request`.

        Returns:
            list: Planned connection or disconnection descriptions.
        """
        preview_lines = []
        is_connect = request.get("operation") == "connect"
        source_plug = (
            f"{request.get('source_object')}.{request.get('source_attribute')}"
            if is_connect
            else None
        )
        chain_nodes = []
        if is_connect and request.get("use_utility_node"):
            chain_nodes.append(request.get("utility_node_type"))
        if is_connect and request.get("add_reverse_node"):
            chain_nodes.append("reverse")

        for target_object in request.get("target_objects", []):
            for target_attribute in request.get("target_attributes", []):
                target_plug = f"{target_object}.{target_attribute}"
                if not is_connect:
                    preview_lines.append(f"Disconnect incoming -> {target_plug}")
                    continue
                chain_parts = [source_plug]
                chain_parts.extend(f"[{node_type}]" for node_type in chain_nodes)
                chain_parts.append(target_plug)
                preview_lines.append(" -> ".join(chain_parts))
        return preview_lines

    def _sanitize_setting(self, key, value):
        """Converts a preference value to the expected supported value.

        Args:
            key (str): Setting key.
            value (object): Candidate value.

        Returns:
            object: Sanitized setting value.
        """
        default_value = self.DEFAULT_SETTINGS[key]
        if isinstance(default_value, bool):
            return bool(value)
        if key == "operation":
            return value if value in self.OPERATIONS else default_value
        if key in ("utility_node_type", "shared_input_node_type"):
            return value if value in self.NODE_TYPES else default_value
        return str(value) if value is not None else default_value
