# GT Tools Module - Init File
import maya.cmds as cmds
import importlib
import logging
import sys
import os

# Global Vars
PACKAGE_VERSION = "1.7.22"

# Initial Setup - Add path and initialize logger
if __name__ != '__main__':
    MODULE_PATH = os.path.dirname(__file__)  # GT Tools Module Path
    sys.path.append(MODULE_PATH)  # Append Module Path

logging.basicConfig()
logger = logging.getLogger("gt-tools")
logger.setLevel(logging.DEBUG)


def execute_script(import_name, entry_point_function, reload=True):
    """
    Attempts to import and execute the provided script using it entry point function
    Args:
        import_name: Name of the script or module to import. For example "gt_utilities"
        entry_point_function: Name of the entry point function, usually the one that opens the script's GUI (string)
        reload: Whether or not to reload the module before executing it (optional, bool)

    Returns:
        succeeded: True if there were no errors (bool)
    """
    try:
        module = importlib.import_module(import_name)
        if reload:
            importlib.reload(module)
    except ModuleNotFoundError as e:
        logger.debug('"' + import_name + '" was not found.')
        logger.debug('Error: ' + str(e))
        raise e

    entry_line = 'module.' + entry_point_function + '()'
    try:
        eval(entry_line)
        return True
    except AttributeError as e:
        logger.debug('"' + entry_line + '" failed to run.')
        logger.debug('Error: ' + str(e))
        cmds.warning("Failed to execute entry point. Make sure the correct functions is being called.")
        return False


if __name__ == '__main__':
    print('Logger Level: ', logger.level)
