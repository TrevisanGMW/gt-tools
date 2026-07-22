"""
Pivot Utility Options

Option windows for pivot-related utilities. These assemble a generic OptionWindow with a
3x3 anchor grid and wire it to the pivot functions in "gt.core.transform".

The grid mirrors a top-down view of the bounding box. Rows map to the depth (Z) axis and
columns map to the horizontal (X) axis, while the vertical (Y) level is fixed per window
(base or top):

    Back-Left    Back     Back-Right
    Left         Center   Right
    Front-Left   Front    Front-Right
"""

import gt.ui.option_window as ui_option_window
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_utils as qt_utils
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Grid definition: rows top-to-bottom map to depth back -> center -> front.
# Columns left-to-right map to horizontal left -> center -> right.
_ANCHOR_GRID = [
    [("Back-Left", "left", "back"), ("Back", "center", "back"), ("Back-Right", "right", "back")],
    [("Left", "left", "center"), ("Center", "center", "center"), ("Right", "right", "center")],
    [("Front-Left", "left", "front"), ("Front", "center", "front"), ("Front-Right", "right", "front")],
]


def _build_anchor_grid(vertical):
    """
    Builds the OptionWindow button-grid specs for a given vertical level.

    Args:
        vertical (str): Y anchor level shared by every button ("base" or "top").

    Returns:
        list: Rows of button spec dictionaries for OptionWindow.add_button_grid.
    """
    from gt.core import transform as core_transform

    def _make_command(horizontal_anchor, depth_anchor):
        """Creates a pivot-move command bound to specific anchors."""
        def _command():
            core_transform.move_pivot_to_bounding_box_position(
                horizontal=horizontal_anchor,
                vertical=vertical,
                depth=depth_anchor,
            )
        return _command

    button_rows = []
    for row in _ANCHOR_GRID:
        spec_row = []
        for label, horizontal_anchor, depth_anchor in row:
            variant = "primary" if (horizontal_anchor == "center" and depth_anchor == "center") else "normal"
            spec_row.append(
                {
                    "label": label,
                    "command": _make_command(horizontal_anchor, depth_anchor),
                    "variant": variant,
                    "tooltip": f"Move pivot to the {vertical} {depth_anchor}-{horizontal_anchor} anchor "
                    f"of the bounding box.",
                }
            )
        button_rows.append(spec_row)
    return button_rows


def _open_move_pivot_options(vertical, title, object_name, icon):
    """
    Opens a "Move Pivot" option window for a given vertical level.

    Args:
        vertical (str): Y anchor level ("base" or "top").
        title (str): Window title.
        object_name (str): Stable Qt object name for the window.
        icon (str): Window icon resource path.

    Returns:
        OptionWindow: The created option window.
    """
    window = ui_option_window.OptionWindow(
        title=title,
        object_name=object_name,
        icon=icon,
        description=f"Move the pivot to a {vertical} anchor of each object's bounding box.",
    )
    window.add_button_grid(_build_anchor_grid(vertical), label="Bounding Box Anchor (top-down view)")
    window.show_window()
    return window


def open_move_pivot_base_options():
    """
    Opens the "Move Pivot to Base" option window.

    Returns:
        OptionWindow: The created option window.
    """
    return _open_move_pivot_options(
        vertical="base",
        title="Move Pivot to Base",
        object_name="gtMovePivotBaseOptions",
        icon=ui_res_lib.Icon.util_pivot_bottom,
    )


def open_move_pivot_top_options():
    """
    Opens the "Move Pivot to Top" option window.

    Returns:
        OptionWindow: The created option window.
    """
    return _open_move_pivot_options(
        vertical="top",
        title="Move Pivot to Top",
        object_name="gtMovePivotTopOptions",
        icon=ui_res_lib.Icon.util_pivot_top,
    )


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        open_move_pivot_base_options()
