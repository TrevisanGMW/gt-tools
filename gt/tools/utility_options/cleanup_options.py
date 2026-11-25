"""Option windows for deleting display layers and merging namespaces."""

from gt.tools.utility_options import cleanup_options_model as model
from gt.ui import option_window as ui_option_window
from gt.ui import resource_library as ui_res_lib
from gt.ui import qt_utils


def _open_cleanup_options(namespaces=False):
    """Builds a filtered cleanup window using click-time scene candidates.

    Args:
        namespaces (bool, optional): Build namespace cleanup instead of layer cleanup.

    Returns:
        OptionWindow: Created cleanup window.
    """
    utility_name = "Namespaces" if namespaces else "Display Layers"
    factory_name = "open_delete_namespaces_options" if namespaces else "open_delete_display_layers_options"
    icon = ui_res_lib.Icon.util_delete_ns if namespaces else ui_res_lib.Icon.util_delete_display_layers
    description = "An empty filter deletes all eligible items. Matching is case-sensitive."
    if namespaces:
        description += " Match full namespace paths. Ignored parents and children are also kept."
    window = ui_option_window.OptionWindow(
        title=f"Delete {utility_name}",
        object_name=f"gtDelete{utility_name.replace(' ', '')}Options",
        icon=icon,
        description=description,
        workspace_restore_factory=f"gt.tools.utility_options.cleanup_options.{factory_name}",
    )
    match_combo = window.add_combobox(
        "Ignore When", list(model.MATCH_MODES), default=model.MATCH_MODES[0],
        tooltip="Choose how names are matched against the ignore text.",
    )
    ignore_field = window.add_line_edit(
        "Ignore Text", placeholder="Leave empty to delete all",
        tooltip="Literal, case-sensitive text. Wildcards are not used.",
    )
    status_label = window.add_label("Ready.")

    def _get_targets():
        """Resolves filtered candidates from the current scene.

        Returns:
            list: Layer names or namespace paths eligible for deletion.
        """
        import maya.cmds as cmds

        if namespaces:
            names = cmds.namespaceInfo(":", listOnlyNamespaces=True, recurse=True) or []
            names = [name.lstrip(":") for name in names if name.lstrip(":") not in ("UI", "shared")]
        else:
            names = [name for name in (cmds.ls(type="displayLayer") or []) if name != "defaultLayer"]
        return model.get_names_to_delete(
            names, ignore_field.text(), match_combo.currentText(), namespaces=namespaces,
        )

    def _preview():
        """Shows the deletion candidates without changing the scene."""
        targets = _get_targets()
        status_label.setText(f"Preview: {len(targets)} {utility_name.lower()} to delete. See Script Editor.")
        print(f"Delete {utility_name} preview ({len(targets)}): " + (", ".join(targets) or "None"))

    def _delete():
        """Deletes the current candidates and reports the affected count."""
        targets = _get_targets()
        if not targets:
            status_label.setText("No matching items to delete.")
            return
        if namespaces:
            from gt.core import namespace as core_namespace

            count = core_namespace.delete_namespaces(namespace_list=targets)
        else:
            from gt.core import display as core_display

            count = core_display.delete_display_layers(layer_list=targets)
        status_label.setText(f"Deleted {count} of {len(targets)} {utility_name.lower()}.")

    window.add_button_row([
        {"label": "Preview", "command": _preview, "tooltip": "List current deletion candidates."},
        {"label": f"Delete {utility_name}", "command": _delete, "variant": "primary", "icon": icon},
    ])
    window.show_window()
    return window


def open_delete_display_layers_options():
    """Opens the filtered display-layer deletion window.

    Returns:
        OptionWindow: Created display-layer option window.
    """
    return _open_cleanup_options()


def open_delete_namespaces_options():
    """Opens the filtered namespace deletion window.

    Returns:
        OptionWindow: Created namespace option window.
    """
    return _open_cleanup_options(namespaces=True)


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        open_delete_display_layers_options()
