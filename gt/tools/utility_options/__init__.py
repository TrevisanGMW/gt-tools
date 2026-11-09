"""
Utility Options

Small option ("option box") windows the utilities menu. Each entry point builds a
generic OptionWindow (see "gt.ui.option_window") and wires it to the relevant core
functions, exposing extra options alongside the original utility action.

Entry points are re-exported here so they can be launched through the package loader, e.g.:
    initialize_tool("utility_options", "open_delete_keyframes_options")
"""

import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Tool Version
__version_tuple__ = (1, 3, 0)
__version_suffix__ = ""
__version__ = ".".join(str(n) for n in __version_tuple__) + __version_suffix__

def __getattr__(name):
    """Loads an exported option-window factory without importing Maya eagerly.

    Args:
        name (str): Requested package attribute.

    Returns:
        callable: Requested option-window entry point.

    Raises:
        AttributeError: If the requested name is not an exported entry point.
    """
    modules = {
        "open_delete_keyframes_options": "keyframe_options",
        "open_move_pivot_base_options": "pivot_options",
        "open_move_pivot_top_options": "pivot_options",
        "open_copy_paste_material_options": "material_options",
        "open_reload_file_options": "reload_file_options",
        "open_convert_to_locators_options": "convert_to_locators_options",
        "open_delete_display_layers_options": "cleanup_options",
        "open_delete_namespaces_options": "cleanup_options",
        "open_reset_joint_display_options": "joint_display_options",
    }
    if name not in modules:
        raise AttributeError(f"Module {__name__!r} has no attribute {name!r}")
    from importlib import import_module

    module = import_module(f"{__name__}.{modules[name]}")
    return getattr(module, name)


__all__ = [
    "open_delete_keyframes_options",
    "open_move_pivot_base_options",
    "open_move_pivot_top_options",
    "open_copy_paste_material_options",
    "open_reload_file_options",
    "open_convert_to_locators_options",
    "open_delete_display_layers_options",
    "open_delete_namespaces_options",
    "open_reset_joint_display_options",
]
