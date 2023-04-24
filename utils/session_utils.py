"""
Session Utilities
This script should not import "maya.cmds" as it's also intended to be used outside of Maya.
"""
from system_utils import get_temp_folder, get_system, OS_WINDOWS
from data_utils import write_json, read_json_dict
import logging
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("session_utils")
logger.setLevel(logging.INFO)


def is_script_in_interactive_maya():
    """
    Check if the script is running in "maya###.exe" or not
    Returns:
        True if running in interactive Maya, false if not.
    """
    try:
        import maya.cmds as cmds
    except ImportError:
        return False  # Failed to import cmds, not in Maya
    try:
        if cmds.about(batch=True):
            return False  # Batch mode
        else:
            return True  # Maya interactive!
    except AttributeError:
        # cmds module isn't fully loaded/populated (which only happens in batch, maya.standalone, or maya GUI)
        return False


def is_script_in_py_maya():
    """
    Check if the script is running in batch mode - e.g. "mayapy.exe"
    Returns:
        True if running in standalone python Maya, false if not.
    """
    try:
        import maya.cmds as cmds
    except ImportError:
        return False  # Failed to import cmds, not in MayaPy
    try:
        if not cmds.about(batch=True):
            return False  # Maya interactive
        else:
            return True  # Batch mode!
    except AttributeError:
        return True


def get_loaded_modules(state=None):
    """
    Get modules that are currently loaded in "sys.modules"
    Args:
        state (optional, list):  If a state is provided, it will be returned as the loaded_modules result.
    Returns:
        List of modules
    """
    if state is not None:
        return state
    return list(sys.modules.keys())


def get_new_modules(modules_to_ignore):
    """
    Find modules that were not in modules_to_ignore (usually the initial state).
    Args:
        modules_to_ignore (list): List of nodes to be filtered out.
        This is usually a list of modules previously saved
    Returns:
        A list of new modules
    """
    return [x for x in get_loaded_modules() if x not in modules_to_ignore]


def remove_modules(modules_to_remove):
    """
    Remove (unload) modules by deleting them from sys modules
    Args:
        modules_to_remove (list): List of modules to remove
    Returns:
        A list of modules that were successfully removed
    """
    removed_modules = []
    for module in modules_to_remove:
        if module not in sys.modules.keys():
            logger.debug(f'skipping absent module: "{module}"')
            continue
        del (sys.modules[module])
        logger.debug(f'removed "{module}"')
        removed_modules.append(module)
    return removed_modules


def reset_state(modules_to_ignore):
    """
    Resets state by removing modules from sys modules
    Args:
        modules_to_ignore (list): A list of modules to ignore. Usually initial state
    Returns:
        removed modules (modules removed when reseting)
    """
    return remove_modules(get_new_modules(modules_to_ignore))


def get_initial_state_file_path():
    """
    Generates a path to a JSON file used to store the JSON initial state
    """
    temp_dir = get_temp_folder()
    state_filename = os.path.join(temp_dir, "initial_state_module_list.json")
    return state_filename


def save_module_state():
    """
    Saves current state (list of loaded modules) to the initial state file (JSON)
    """
    state = get_loaded_modules()
    write_json(path=get_initial_state_file_path(), data={"initial_state": state})


def reset_session():
    """
    If the initial state file is found, it's used to reset the session
    Returns:
        List of removed modules
    """
    file_path = get_initial_state_file_path()
    if os.path.exists(file_path):
        state_dict = read_json_dict(path=file_path)
        return reset_state(state_dict.get("initial_state"))
    else:
        logger.warning(f'Unable to reset session. Missing initial state: {file_path}')


def reset_session_with_feedback(*args):
    """
    Resets session with printing feedback
    Returns:
        removed modules
    """
    removed_modules = reset_session()
    if removed_modules is not None:
        print('\n' + '-' * 80)
        for module in removed_modules:
            print(module)
        sys.stdout.write(f'{len(removed_modules)} modules were removed. (Open script editor to see the list)')
        return removed_modules


if __name__ == "__main__":
    from pprint import pprint
    import maya.standalone as standalone
    standalone.initialize()
    out = None
    pprint(out)
