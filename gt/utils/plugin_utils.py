"""
Plugin Utilities
github.com/TrevisanGMW/gt-tools
"""
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def load_plugin(plugin_name):
    """
    Check if a Maya plugin is available and load it if not already loaded.

    Args:
        plugin_name (str): The name of the plugin to check and load.

    Returns:
        bool: True if the plugin was loaded successfully or was already loaded, False otherwise.
    """
    if cmds.pluginInfo(plugin_name, query=True, loaded=True):
        return True

    try:
        cmds.loadPlugin(plugin_name)
        return True
    except Exception as e:
        logger.debug(str(e))
        return False


def load_plugins(plugin_names):
    """
    Load a list of Maya plugins using the load_plugin function.

    Args:
        plugin_names (List[str], str): A list of plugin names to load. (Strings are converted to list with one item)

    Returns:
        list: A list of tuples containing the plugin name and a boolean indicating whether it was loaded successfully.
    """
    results = []
    if isinstance(plugin_names, str):
        plugin_names = [plugin_names]
    for plugin_name in plugin_names:
        loaded = load_plugin(plugin_name)
        results.append((plugin_name, loaded))

    return results


def unload_plugin(plugin_name):
    """
    Unload a Maya plugin if it is currently loaded.

    Args:
        plugin_name (str): The name of the plugin to unload.

    Returns:
        bool: True if the plugin was unloaded successfully or was not loaded, False otherwise.
    """
    if cmds.pluginInfo(plugin_name, query=True, loaded=True):
        try:
            cmds.unloadPlugin(plugin_name)
            return True
        except Exception as e:
            logger.debug(str(e))
            return False
    else:
        return True  # Plugin was not loaded, so consider it unloaded


def unload_plugins(plugin_names):
    """
    Unload a list of Maya plugins using the unload_plugin function.

    Args:
        plugin_names (List[str], str): A list of plugin names to unload.

    Returns:
        list: A list of tuples containing the plugin name and a boolean indicating whether it was unloaded successfully.
              True means that it was unloaded.
    """
    results = []
    if isinstance(plugin_names, str):
        plugin_names = [plugin_names]
    for plugin_name in plugin_names:
        unloaded = unload_plugin(plugin_name)
        results.append((plugin_name, unloaded))
    return results


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    print(load_plugin('objExport'))
