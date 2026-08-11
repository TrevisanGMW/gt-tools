"""
Material Utility Options

Option window for the Copy/Paste Material utility. It exposes both the copy and paste
actions in a single window, wired to the material functions in "gt.core.misc".
"""

import gt.ui.option_window as ui_option_window
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_utils as qt_utils
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def open_copy_paste_material_options():
    """
    Opens the "Copy/Paste Material" option window.

    Returns:
        OptionWindow: The created option window.
    """
    from gt.core import misc as core_misc

    window = ui_option_window.OptionWindow(
        title="Copy/Paste Material",
        object_name="gtCopyPasteMaterialOptions",
        icon=ui_res_lib.Icon.util_mod_copy_material,
        description="Copy a material from the selection, then paste it onto another selection.",
        workspace_restore_factory=(
            "gt.tools.utility_options.material_options.open_copy_paste_material_options"
        ),
    )
    window.add_button(
        "Copy Material",
        command=core_misc.material_copy,
        icon=ui_res_lib.Icon.util_mod_copy_material,
        tooltip="Copies material to clipboard.",
    )
    window.add_button(
        "Paste Material",
        command=core_misc.material_paste,
        icon=ui_res_lib.Icon.util_mod_paste_material,
        tooltip="Pastes material from clipboard.",
    )
    window.show_window()
    return window


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        open_copy_paste_material_options()
