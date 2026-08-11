"""Reload File Utility Options.

Provides a dockable option window for reloading the current Maya file and
opening neighboring supported files from the same folder.
"""

import logging

import gt.ui.option_window as ui_option_window
import gt.ui.qt_utils as qt_utils
import gt.ui.qt_import as ui_qt
import gt.ui.resource_library as ui_res_lib


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEFAULT_FILE_FORMATS = ".ma, .mb, or .fbx"


def open_reload_file_options():
    """Opens the "Reload File" option window.

    Returns:
        OptionWindow: Created reload-file option window.
    """
    window = ui_option_window.OptionWindow(
        title="Reload File",
        object_name="gtReloadFileOptions",
        icon=ui_res_lib.Icon.util_reload_file,
        workspace_restore_factory=(
            "gt.tools.utility_options.reload_file_options.open_reload_file_options"
        ),
    )
    force_checkbox = ui_qt.QtWidgets.QCheckBox("Force Operation")
    force_checkbox.setToolTip("Force the operation and discard unsaved changes.")
    loop_checkbox = ui_qt.QtWidgets.QCheckBox("Loop Directory")
    loop_checkbox.setChecked(False)
    loop_checkbox.setToolTip(
        "Wrap to the first file after the last, or to the last file before the first."
    )
    formats_field = window.add_line_edit(
        "File Formats",
        default=DEFAULT_FILE_FORMATS,
        placeholder=DEFAULT_FILE_FORMATS,
        tooltip="Comma-, space-, or semicolon-separated file extensions.",
        key="file_formats",
        label_width=80,
    )
    window.controls["force"] = force_checkbox
    window.controls["loop_directory"] = loop_checkbox

    def _reload_file():
        """Reloads the current file using the selected force setting."""
        from gt.core import scene as core_scene

        core_scene.reload_file(force=force_checkbox.isChecked())

    def _open_previous_file():
        """Opens the previous supported file in the current folder."""
        from gt.core import scene as core_scene

        core_scene.open_adjacent_file(
            direction=-1,
            file_extensions=formats_field.text(),
            force=force_checkbox.isChecked(),
            loop_directory=loop_checkbox.isChecked(),
        )

    def _open_next_file():
        """Opens the next supported file in the current folder."""
        from gt.core import scene as core_scene

        core_scene.open_adjacent_file(
            direction=1,
            file_extensions=formats_field.text(),
            force=force_checkbox.isChecked(),
            loop_directory=loop_checkbox.isChecked(),
        )

    window.add_control_row([force_checkbox, loop_checkbox])
    window.add_button_row(
        [
            {
                "label": "Previous",
                "command": _open_previous_file,
                "tooltip": "Open the previous matching file in the current folder.",
            },
            {
                "label": "Reload File",
                "command": _reload_file,
                "variant": "primary",
                "icon": ui_res_lib.Icon.util_reload_file,
                "tooltip": "Reload the current file.",
            },
            {
                "label": "Next",
                "command": _open_next_file,
                "tooltip": "Open the next matching file in the current folder.",
            },
        ]
    )
    window.show_window()
    return window


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        open_reload_file_options()
