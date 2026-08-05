"""
Animation Clip Tracker Constants

Shared values used by the model, the view and the timeline widget.
This module is pure Python so it can be imported outside Maya and without Qt.
"""

MODE_NAVIGATE = "navigate"
MODE_SELECT = "select"
MODE_EDIT = "edit"
TIMELINE_MODES = [MODE_NAVIGATE, MODE_SELECT, MODE_EDIT]
DEFAULT_TIMELINE_MODE = MODE_EDIT
MODE_LABELS = {
    MODE_NAVIGATE: "Navigate",
    MODE_SELECT: "Select",
    MODE_EDIT: "Edit",
}


def get_mode_label(mode):
    """Gets the user-facing label of a timeline mode.

    Args:
        mode (str): Timeline mode key.

    Returns:
        str: Mode label, or an empty string when the mode is unknown.
    """
    return MODE_LABELS.get(mode, "")


def get_valid_mode(mode):
    """Gets a valid timeline mode key.

    Args:
        mode (str): Requested timeline mode key.

    Returns:
        str: Requested mode when valid, otherwise the default mode.
    """
    return mode if mode in TIMELINE_MODES else DEFAULT_TIMELINE_MODE


def get_mode_index(mode):
    """Gets the one-based index of a timeline mode.

    Args:
        mode (str): Timeline mode key.

    Returns:
        int: One-based mode index.
    """
    return TIMELINE_MODES.index(get_valid_mode(mode)) + 1


def get_mode_from_index(index):
    """Gets a timeline mode key from a one-based index.

    Args:
        index (int): One-based mode index.

    Returns:
        str: Timeline mode key. Defaults to the default mode when out of range.
    """
    position = int(index) - 1
    if 0 <= position < len(TIMELINE_MODES):
        return TIMELINE_MODES[position]
    return DEFAULT_TIMELINE_MODE
