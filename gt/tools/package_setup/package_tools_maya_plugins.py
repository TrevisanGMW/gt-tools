"""
Maya Plugin Helpers for Package Setup
"""

import logging


logger = logging.getLogger(__name__)

STARTUP_PLUGINS = [
    "matrixNodes",
    "quatNodes",
    "lookdevKit",
]


def load_startup_plugins(plugin_names=None):
    """Loads startup plugins used by Auto Rigger tests and rig modules.

    Args:
        plugin_names (list, optional): Plugin names to load. Uses default startup plugins when omitted.

    Returns:
        list: Tuples with plugin names and loaded states.
    """
    plugin_names = plugin_names or STARTUP_PLUGINS
    try:
        from gt.core import plugin as core_plugin

        return core_plugin.load_plugins(plugin_names)
    except Exception as exception:
        logger.debug("Unable to load startup plugins: %s", exception)
        return [(plugin_name, False) for plugin_name in plugin_names]

