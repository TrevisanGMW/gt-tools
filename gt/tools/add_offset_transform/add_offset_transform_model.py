"""Add Offset Transform model and Maya runtime operations."""

import logging


logger = logging.getLogger(__name__)


class AddOffsetTransformModel:
    """Stores offset settings and creates transforms through core hierarchy."""

    DEFAULT_SETTINGS = {
        "transform_type": "Group",
        "pivot_source": "Selection",
        "transform_suffix": "offset",
        "outliner_color": [0.5, 1.0, 0.4],
    }

    def __init__(self):
        """Initializes settings and loads preferences."""
        self.settings = dict(self.DEFAULT_SETTINGS)
        self.settings["outliner_color"] = list(self.DEFAULT_SETTINGS["outliner_color"])
        self.load_preferences()

    def load_preferences(self):
        """Loads settings from the repository preference system."""
        try:
            from gt.core.prefs import Prefs

            preferences = Prefs("add_offset_transform")
            raw_preferences = preferences.get_raw_preferences()
            self.settings["transform_type"] = str(
                raw_preferences.get("transform_type", self.DEFAULT_SETTINGS["transform_type"])
            )
            self.settings["pivot_source"] = str(
                raw_preferences.get("pivot_source", self.DEFAULT_SETTINGS["pivot_source"])
            )
            self.settings["transform_suffix"] = str(
                raw_preferences.get("transform_suffix", self.DEFAULT_SETTINGS["transform_suffix"])
            )
            color = raw_preferences.get("outliner_color", self.DEFAULT_SETTINGS["outliner_color"])
            if isinstance(color, (list, tuple)) and len(color) == 3:
                self.settings["outliner_color"] = [float(component) for component in color]
        except Exception as exception:
            logger.debug("Unable to load Add Offset Transform preferences: %s", exception)

    def save_preferences(self):
        """Writes settings to the repository preference system."""
        from gt.core.prefs import Prefs

        preferences = Prefs("add_offset_transform")
        preferences.set_raw_preferences(dict(self.settings))
        preferences.save()

    def set_setting(self, key, value, save=True):
        """Updates one known setting.

        Args:
            key (str): Setting name.
            value (object): New value.
            save (bool, optional): Whether to save immediately.
        """
        if key not in self.DEFAULT_SETTINGS:
            return
        self.settings[key] = value
        if save:
            self.save_preferences()

    def reset_preferences(self):
        """Restores and saves default settings."""
        self.settings = dict(self.DEFAULT_SETTINGS)
        self.settings["outliner_color"] = list(self.DEFAULT_SETTINGS["outliner_color"])
        self.save_preferences()

    def create_offsets(self, targets=None):
        """Creates configured offset transforms for Maya objects.

        Args:
            targets (list, optional): Target objects. Current selection is used when omitted.

        Returns:
            list: Created offset node objects.

        Raises:
            RuntimeError: If no targets are provided or the suffix is empty.
        """
        import maya.cmds as cmds
        import gt.core.hierarchy as core_hierarchy

        targets = targets or cmds.ls(selection=True, long=True) or []
        if not targets:
            raise RuntimeError("Select at least one transform before adding an offset.")
        suffix = str(self.settings.get("transform_suffix") or "").strip().strip("_")
        if not suffix:
            raise RuntimeError("New Transform Suffix cannot be empty.")
        transform_type = str(self.settings.get("transform_type") or "Group").lower()
        pivot_source = "target" if self.settings.get("pivot_source") == "Selection" else "parent"
        cmds.undoInfo(openChunk=True, chunkName="Add Offset Transform")
        try:
            offsets = core_hierarchy.add_offset_transform(
                target_list=targets,
                transform_type=transform_type,
                pivot_source=pivot_source,
                transform_suffix=suffix,
            )
            color = self.settings.get("outliner_color") or self.DEFAULT_SETTINGS["outliner_color"]
            for offset in offsets:
                offset_name = str(offset)
                cmds.setAttr(offset_name + ".useOutlinerColor", True)
                cmds.setAttr(offset_name + ".outlinerColor", color[0], color[1], color[2])
            cmds.select([str(offset) for offset in offsets], replace=True)
            return offsets
        finally:
            cmds.undoInfo(closeChunk=True, chunkName="Add Offset Transform")
