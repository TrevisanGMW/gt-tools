"""
Session Utilities
This script should not import "maya.cmds" as it's also intended to be used outside of Maya.
"""
from gt.utils.data_utils import write_json, read_json_dict
from gt.utils.feedback_utils import print_when_true
from gt.utils.system_utils import get_temp_folder
import importlib
import inspect
import logging
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
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
        removed modules (modules removed when resetting)
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


def filter_loaded_modules_path_containing(filter_strings, return_module=True):
    """
    Looks through loaded modules and returns the ones containing the provided string under their path
    Args:
        filter_strings (list): A list of strings used to filter modules. If any are found under the module path,
                               then they will be included in the return list.
        return_module (bool, optional): If active, it will return the module.
                                        If inactive, it will return the module name.
    Returns:
        list: List of module names (the ones that contained the provided string under their path)
    """
    if isinstance(filter_strings, str):
        filter_strings = [filter_strings]
    if not isinstance(filter_strings, list):
        logger.error(f'Unable to filter modules. Expected "list" as argument, but received "{type(filter_strings)}')
        return []
    filtered_module_names = set()
    filtered_modules = set()
    for module_name in sys.modules.keys():
        module = sys.modules[module_name]
        if hasattr(module, "__file__") and isinstance(module.__file__, str):
            for contains_string in filter_strings:
                if contains_string in module.__file__:
                    filtered_module_names.add(module_name)
                    filtered_modules.add(module)
    if return_module:
        return list(filtered_modules)
    else:
        return list(filtered_module_names)


def remove_modules_startswith(prefix):
    """
    Removes modules from "sys.modules" dictionary that start with the specified prefix.
    Args:
        prefix (str): The prefix that the module names should start with.

    Returns:
        list: A list of module names that were removed.
    """
    modules_to_remove = set()
    # Iterate through all loaded modules
    for module_name in list(sys.modules.keys()):
        if module_name.startswith(prefix):
            modules_to_remove.add(module_name)
    # Remove the modules from the sys.modules dictionary
    for module_name in list(modules_to_remove):
        del sys.modules[module_name]
    return list(modules_to_remove)


def prepend_sys_path(new_path):
    """Prepends a path to the "sys.path" list.
    Args:
        new_path (str): The path to be prepended.
    Raises:
        TypeError: If new_path is not a string.
        ValueError: If new_path is an empty string.
    """
    if not isinstance(new_path, str):
        raise TypeError("new_path must be a string.")
    if not new_path:
        raise ValueError("new_path cannot be an empty string.")
    sys.path.insert(0, new_path)


def get_maya_version():
    """
    Get the version of Autodesk Maya.

    Returns:
        str: The version of Maya if successful, otherwise returns None.
    """
    try:
        import maya.cmds as cmds
        return cmds.about(version=True)
    except Exception as e:
        logger.debug(str(e))
        logger.debug(f'Unable to retrieve version using "cmds". Trying with "mel"...')
        try:
            import maya.mel as mel
            return mel.eval("about -v;")
        except ImportError:
            logger.warning(f'Unable to retrieve Maya version')
            return None


def is_maya_standalone_initialized():
    """
    Check if Maya standalone mode has been initialized.

    This function attempts to access a Maya function that is only available in standalone mode,
    without making any changes to the scene.

    Returns:
        bool: True if Maya standalone mode has been initialized, False otherwise.
    """
    try:
        import maya.cmds as cmds
        cmds.about(version=True) # Attempt to access a Maya function that is only available when initialized
        return True
    except Exception as e:
        logger.debug(str(e))
        return False    # If an exception is raised, it means maya.standalone has not been initialized


def get_module_path(module_name, verbose=False):
    """
    Retrieves the file path of a Python module.

    This function attempts to import the specified module and then retrieves its file path.
    If the module is successfully imported, its file path is returned.
    If the module cannot be imported, None is returned.

    Args:
        module_name (str): The name of the Python module.
        verbose (bool, optional): If True, enables verbose mode and prints additional information.
            Defaults to False.

    Returns:
        str or None: The file path of the imported module, or None if import fails.
    """
    try:
        module = importlib.import_module(module_name)
        module_file = inspect.getfile(module)
        print_when_true(module_file, use_system_write=True, do_print=verbose)
        return module_file
    except ImportError:
        return None


if __name__ == "__main__":
    from pprint import pprint
    import maya.standalone as standalone
    standalone.initialize()
    out = None
    # out = filter_loaded_modules_path_containing(["gt-tools", "sys"])
    # out = is_maya_standalone_initialized()
    out = get_module_path("gt")
    pprint(out)
