"""Pure model and naming helpers for Morphing Utilities."""

import copy


DEFAULT_SETTINGS = {
    "morphing_object": "",
    "blend_node": "",
    "blend_nodes": [],
    "search_string": "",
    "replace_string": "",
    "symmetry_axis": "x",
    "mirror_direction": "-",
    "target_value": 1.0,
}


class MorphingUtilitiesModel:
    """Stores the current Morphing Utilities session state.

    The model intentionally contains no Maya or Qt imports. This keeps the
    naming and validation behavior easy to test outside of Maya.
    """

    def __init__(self):
        """Initializes a fresh session state."""
        self.settings = copy.deepcopy(DEFAULT_SETTINGS)

    @property
    def morphing_object(self):
        """Gets the loaded source object.

        Returns:
            str: Loaded source object name, or an empty string.
        """
        return self.settings["morphing_object"]

    @property
    def blend_node(self):
        """Gets the selected blend shape node.

        Returns:
            str: Selected blend shape node, or an empty string.
        """
        return self.settings["blend_node"]

    @property
    def blend_nodes(self):
        """Gets the blend shape nodes found on the source object.

        Returns:
            list: Ordered blend shape node names.
        """
        return list(self.settings["blend_nodes"])

    @property
    def search_string(self):
        """Gets the current target-name search string.

        Returns:
            str: Search text.
        """
        return self.settings["search_string"]

    @property
    def replace_string(self):
        """Gets the current target-name replacement string.

        Returns:
            str: Replacement text.
        """
        return self.settings["replace_string"]

    @property
    def symmetry_axis(self):
        """Gets the selected symmetry axis.

        Returns:
            str: Axis name.
        """
        return self.settings["symmetry_axis"]

    @property
    def mirror_direction(self):
        """Gets the selected mirror direction.

        Returns:
            str: Direction sign.
        """
        return self.settings["mirror_direction"]

    @property
    def target_value(self):
        """Gets the value used by the set-target-values operation.

        Returns:
            float: Target weight value.
        """
        return self.settings["target_value"]

    def set_source_state(self, morphing_object, blend_nodes):
        """Stores the source object and its discovered blend shape nodes.

        Args:
            morphing_object (str): Loaded source object.
            blend_nodes (list): Blend shape nodes found on the object.

        Returns:
            list: Sanitized blend shape node names.
        """
        clean_nodes = []
        for node in blend_nodes or []:
            node = str(node or "").strip()
            if node and node not in clean_nodes:
                clean_nodes.append(node)

        self.settings["morphing_object"] = str(morphing_object or "").strip()
        self.settings["blend_nodes"] = clean_nodes
        self.settings["blend_node"] = ""
        return list(clean_nodes)

    def set_blend_node(self, blend_node):
        """Stores the selected blend shape node.

        Args:
            blend_node (str): Blend shape node name.

        Returns:
            str: Sanitized blend shape node name.
        """
        blend_node = str(blend_node or "").strip()
        self.settings["blend_node"] = blend_node
        return blend_node

    def set_search_replace(self, search_string, replace_string):
        """Stores target-name search and replacement text.

        Args:
            search_string (str): Text to find.
            replace_string (str): Text to insert.
        """
        self.settings["search_string"] = str(search_string or "").strip()
        self.settings["replace_string"] = str(replace_string or "").strip()

    def set_mirror_settings(self, symmetry_axis, mirror_direction):
        """Stores the selected mirror options.

        Args:
            symmetry_axis (str): Axis used by the Maya blendShape command.
            mirror_direction (str): Direction sign, either ``-`` or ``+``.
        """
        symmetry_axis = str(symmetry_axis or "x").lower()
        mirror_direction = str(mirror_direction or "-")
        self.settings["symmetry_axis"] = symmetry_axis if symmetry_axis in "xyz" else "x"
        self.settings["mirror_direction"] = (
            mirror_direction if mirror_direction in ("-", "+") else "-"
        )

    def set_target_value(self, target_value):
        """Stores the value used for all target weights.

        Args:
            target_value (float): New target weight value.
        """
        self.settings["target_value"] = float(target_value)

    def validate_operation(self, operation):
        """Validates the current search fields for an operation.

        Args:
            operation (str): One of ``rename``, ``flip``, or ``mirror``.

        Returns:
            tuple: Boolean validity and a user-facing message.
        """
        if operation not in ("rename", "flip", "mirror"):
            return False, f"Unsupported morphing operation: {operation}"
        if operation == "rename" and not self.search_string:
            return False, "Enter Search text before renaming target names."
        return True, ""

    def build_rename_pairs(self, target_names):
        """Builds old/new names for the search-and-replace operation.

        Args:
            target_names (list): Existing blend shape target aliases.

        Returns:
            list: Pairs containing ``(old_name, new_name)``.
        """
        if not self.search_string:
            return []
        return [
            (target_name, target_name.replace(self.search_string, self.replace_string))
            for target_name in target_names or []
            if self.search_string in target_name
        ]

    def build_duplicate_pairs(self, target_names, operation):
        """Builds source and derived names for a duplicate operation.

        Args:
            target_names (list): Existing blend shape target aliases.
            operation (str): Either ``flip`` or ``mirror``.

        Returns:
            list: Pairs containing ``(source_name, derived_name)``.
        """
        if operation not in ("flip", "mirror"):
            return []

        suffix = "_Flipped" if operation == "flip" else "_Mirrored"
        pairs = []
        for target_name in target_names or []:
            if self.search_string not in target_name:
                continue
            if self.replace_string:
                derived_name = target_name.replace(self.search_string, self.replace_string)
            else:
                derived_name = f"{target_name}{suffix}"
            pairs.append((target_name, derived_name))
        return pairs

    def clear_scene_state(self):
        """Clears loaded Maya scene references while retaining form settings."""
        self.settings["morphing_object"] = ""
        self.settings["blend_node"] = ""
        self.settings["blend_nodes"] = []
