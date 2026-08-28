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
__version_tuple__ = (1, 2, 0)
__version_suffix__ = ""
__version__ = ".".join(str(n) for n in __version_tuple__) + __version_suffix__

from gt.tools.utility_options.keyframe_options import open_delete_keyframes_options
from gt.tools.utility_options.pivot_options import (
    open_move_pivot_base_options,
    open_move_pivot_top_options,
)
from gt.tools.utility_options.material_options import open_copy_paste_material_options
from gt.tools.utility_options.reload_file_options import open_reload_file_options

__all__ = [
    "open_delete_keyframes_options",
    "open_move_pivot_base_options",
    "open_move_pivot_top_options",
    "open_copy_paste_material_options",
    "open_reload_file_options",
]
