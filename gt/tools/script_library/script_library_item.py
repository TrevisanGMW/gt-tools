"""Serializable item used by the Script Library model and archive service."""

from gt.tools.script_library.script_library_constants import ScriptLibraryConstants
import os
import uuid


class ScriptLibraryItem:
    """Represents one script and its persistent presentation metadata."""

    def __init__(
        self,
        script_id,
        file_name,
        nice_name,
        description="",
        visible=True,
        icon_mode=ScriptLibraryConstants.ICON_MODE_DEFAULT,
        icon_value="",
        order=0,
    ):
        """Initializes a script library item.

        Args:
            script_id (str): Stable identifier for the script.
            file_name (str): Python file stored in the script directory.
            nice_name (str): User-facing script name.
            description (str, optional): User-facing script description.
            visible (bool, optional): Whether the item appears in use mode.
            icon_mode (str, optional): One of the supported icon modes.
            icon_value (str, optional): Package icon name or managed asset name.
            order (int, optional): Explicit display order.
        """
        self.script_id = str(script_id or uuid.uuid4().hex)
        self.file_name = os.path.basename(str(file_name or "script.py"))
        self.nice_name = str(nice_name or "Script")
        self.description = str(description or "")
        self.visible = bool(visible)
        self.icon_mode = (
            icon_mode
            if icon_mode in ScriptLibraryConstants.ICON_MODES
            else ScriptLibraryConstants.ICON_MODE_DEFAULT
        )
        self.icon_value = str(icon_value or "")
        self.order = int(order or 0)

    def to_dict(self):
        """Serializes the item to JSON-compatible data.

        Returns:
            dict: Serialized item metadata.
        """
        return {
            "id": self.script_id,
            "file_name": self.file_name,
            "nice_name": self.nice_name,
            "description": self.description,
            "visible": self.visible,
            "icon_mode": self.icon_mode,
            "icon_value": self.icon_value,
            "order": self.order,
        }

    @classmethod
    def from_dict(cls, data):
        """Creates an item from serialized metadata.

        Args:
            data (dict): Serialized item metadata.

        Returns:
            ScriptLibraryItem or None: Parsed item, or None for invalid data.
        """
        if not isinstance(data, dict):
            return None
        file_name = os.path.basename(str(data.get("file_name") or ""))
        if not file_name.lower().endswith(ScriptLibraryConstants.SCRIPT_EXTENSION):
            return None
        nice_name = str(data.get("nice_name") or "").strip()
        if not nice_name:
            nice_name = os.path.splitext(file_name)[0].replace("_", " ").title()
        icon_mode = data.get("icon_mode", ScriptLibraryConstants.ICON_MODE_DEFAULT)
        icon_value = str(data.get("icon_value") or "")
        if icon_mode in (
            ScriptLibraryConstants.ICON_MODE_CUSTOM,
            ScriptLibraryConstants.ICON_MODE_SNAPSHOT,
        ):
            icon_value = os.path.basename(icon_value)
        return cls(
            script_id=data.get("id"),
            file_name=file_name,
            nice_name=nice_name,
            description=data.get("description", ""),
            visible=data.get("visible", True),
            icon_mode=icon_mode,
            icon_value=icon_value,
            order=data.get("order", 0),
        )

