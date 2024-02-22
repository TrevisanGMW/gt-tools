"""
System Utilities - Utilities related to system activities, such as paths, open explorer, etc...
This script should not import "maya.cmds" as it's also intended to be used outside of Maya.
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.data_utils import DataDirConstants
from datetime import datetime
from functools import wraps
import subprocess
import traceback
import importlib
import tempfile
import logging
import pathlib
import base64
import time
import sys
import os
import re

OS_MAC = 'darwin'
OS_LINUX = 'linux'
OS_WINDOWS = 'win32'
known_systems = [OS_WINDOWS, OS_MAC, OS_LINUX]

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_system():
    """
    Get system in which this script is running
    Returns:
        str: System name.
        e.g. "win32" for Windows, or "darwin" for MacOS
    """
    system = sys.platform
    if system not in known_systems:
        logger.debug(f'Unexpected system returned: {system}]')
    return system


def is_system_macos():
    """
    Checks if the current operating system is macOS.
    Returns:
        bool: True if the operating system is macOS, False otherwise.
    """
    if get_system() == OS_MAC:
        return True
    return False


def is_system_windows():
    """
    Checks if the current operating system is Windows.
    Returns:
        bool: True if the operating system is Windows, False otherwise.
    """
    if get_system() == OS_WINDOWS:
        return True
    return False


def is_system_linux():
    """
    Checks if the current operating system is Linux.
    Returns:
        bool: True if the operating system is Linux, False otherwise.
    """
    if get_system() == OS_LINUX:
        return True
    return False


def get_temp_dir():
    """
    Get path to the tempo folder. It will be different depending on the system
    e.g. "C:\\Users\\<User-Name>>\\AppData\\Local\\Temp"
    Returns:
        str: String path to temp folder
    """
    return tempfile.gettempdir()


def get_home_dir():
    """
    Returns home path

    Returns:
        str: Home path
        Windows example: "C:/Users/<UserName>"
        MacOS example: TBD
    """
    # Maya uses the HOME environment variable on Windows causing it to add "Documents" to the path
    if get_system() == OS_WINDOWS:
        return os.path.expanduser(os.getenv('USERPROFILE'))
    else:
        return pathlib.Path.home()


def get_desktop_path():
    """
    Get path to the Desktop folder of the current user
    Returns:
        str: String (path) to the desktop folder
    """
    return os.path.join(get_home_dir(), 'Desktop')


def get_maya_install_dir(system):
    """
    Get Maya installation folder (Autodesk folder where you find all Maya versions)
    Return:
        str: Path to autodesk folder (where you find maya#### folders
        e.g. "C:/Program Files/Autodesk/"
    """
    autodesk_default_paths = {
        OS_LINUX: "/usr/bin/",
        OS_MAC: "/Applications/Autodesk",
        OS_WINDOWS: r"C:\Program Files\Autodesk",
    }
    if system not in autodesk_default_paths.keys():
        raise KeyError(f'Unable to find the given system in listed paths. System: "{system}"')

    return autodesk_default_paths.get(system)


def get_maya_path(system, version, get_maya_python=False):
    """
    Get a path to Maya executable or maya headless
    Args:
        system (str): System name
        version (str): Software version - #### e.g. "2023" or "2024"
        get_maya_python (optional, bool): If active, it will return maya python executable instead of maya interactive
    Returns:
        str: Path to Maya interactive or headless
    """
    install_dir = get_maya_install_dir(system)
    executable_name = "maya"
    if get_maya_python:
        executable_name = "mayapy"
    maya_paths = {
        OS_LINUX: "/usr/bin/",
        OS_MAC: f"{install_dir}/maya{version}/Maya.app/Contents/bin/{executable_name}",
        OS_WINDOWS: fr"{install_dir}\Maya{version}\bin\{executable_name}.exe",
    }
    if system not in maya_paths.keys():
        raise KeyError(f'Unable to find the given system in listed paths. System: "{system}"')

    return maya_paths.get(system)


def open_file_dir(path):
    """
    Opens the directory where the provided path points to
    Args:
        path (str): A path to a file or directory
    """
    system = get_system()
    if system == OS_WINDOWS:  # Windows
        # explorer needs forward slashes
        filebrowser_path = os.path.join(os.getenv('WINDIR'), 'explorer.exe')
        if os.path.isdir(path):
            subprocess.run([filebrowser_path, path])
        elif os.path.isfile(path):
            subprocess.run([filebrowser_path, '/select,', path])
    elif system == OS_MAC:  # Mac-OS
        try:
            subprocess.call(["open", "-R", path])
        except Exception as exception:
            logger.warning(f'Unable to open directory. Issue: {exception}')
    else:  # Linux/Other
        logger.warning(f'Unable to open directory. Unsupported system: "{system}".')


def get_maya_preferences_dir(system):
    """
    Get maya preferences folder (folder contains scripts, prefs, etc...)
    Args:
        system (str): System string
    Returns:
        str: Path to preferences folder (folder where you find scripts, prefs, etc...)
    """
    win_maya_preferences_dir = ""
    mac_maya_preferences_dir = ""
    if system == OS_WINDOWS:
        win_maya_preferences_dir = os.path.expanduser('~')
        try:
            import maya.cmds as cmds
            if cmds.about(batch=True):
                raise
            else:
                win_maya_preferences_dir = cmds.internalVar(userAppDir=True)
        except Exception as e:
            win_maya_preferences_dir = os.path.join(win_maya_preferences_dir, "Documents")
            logger.debug(f'Got Maya preferences path from outside Maya. Reason: {str(e)}')
            win_maya_preferences_dir = os.path.join(win_maya_preferences_dir, "maya")
    elif system == OS_MAC:
        mac_maya_preferences_dir = os.path.join(os.path.expanduser('~'), "Library", "Preferences", "Autodesk", "maya")

    maya_preferences_paths = {
        OS_LINUX: "/usr/bin/",
        OS_MAC: mac_maya_preferences_dir,
        OS_WINDOWS: win_maya_preferences_dir,
    }
    if system not in maya_preferences_paths.keys():
        raise KeyError(f'Unable to find the given system in listed paths. System: "{system}"')

    return maya_preferences_paths.get(system)


def get_available_maya_preferences_dirs(use_maya_commands=False):
    """
    Gets all folders matching the pattern "####" inside the parent maya preferences directory.
    Args:
        use_maya_commands (bool, optional): If true, it will attempt to import Maya cmds and use it for the operation.
                                            This different method provides a more robust way of generating the path
                                            but requires access to Maya commands. It can only be used when in Maya.
    Returns:
        dict: Dictionary with maya versions as keys and path as value
        e.g. { "2024": "C:\\Users\\UserName\\Documents\\maya\\2024"}
    """
    # Get Maya Preference folders
    if use_maya_commands:
        try:
            import maya.cmds as cmds
            maya_preferences_dir = os.path.dirname(cmds.about(preferences=True))
        except Exception as e:
            logger.debug(f"Unable to retrieve preferences using Maya commands. Issue: {e}. \n"
                         f"Attempting operation using system functions...")
            maya_preferences_dir = get_maya_preferences_dir(get_system())
    else:
        maya_preferences_dir = get_maya_preferences_dir(get_system())

    if os.path.exists(maya_preferences_dir):
        maya_folders = os.listdir(maya_preferences_dir)
        existing_folders = {}
        for folder in maya_folders:
            if re.match("^[0-9]{4}$", folder):
                existing_folders[folder] = os.path.join(maya_preferences_dir, folder)
        return existing_folders
    else:
        logger.warning(f'Missing provided path: "{maya_preferences_dir}"')
        return {}


def get_available_maya_install_dirs():
    """
    Gets all folders matching the pattern "Maya####" inside the autodesk directory.
    Returns:
        dict: Dictionary with maya versions as keys and path as value
        e.g. { "2024": "C:\\Users\\UserName\\Documents\\maya\\2024"}
        If nothing is found, it returns an empty dictionary
    """
    maya_preferences_dir = get_maya_install_dir(get_system())

    if os.path.exists(maya_preferences_dir):
        maya_folders = os.listdir(maya_preferences_dir)
        existing_folders = {}
        for folder in maya_folders:
            if re.match("^maya[0-9]{4}$", folder.lower()):
                folder_digits = re.sub("[^0-9]", "", folder)
                existing_folders[folder_digits] = os.path.join(maya_preferences_dir, folder)
        return existing_folders
    else:
        logger.warning(f'Missing provided path: "{maya_preferences_dir}"')
        return {}


def get_maya_executable(get_maya_python=False, preferred_version=None):
    """
    Gets a path to the executable of the latest available version of Maya detected on the system.
    If a preferred version si provided and is available, that is used instead
    Args:
        get_maya_python (optional, bool): If active, it will attempt to retrieve "mayapy" instead of "maya"
        preferred_version (optional, str): The preferred version. A string with four digits e.g. "2024"
                                              If found, that will be used, otherwise the latest detected version
                                              is returned instead.
    Returns:
        str: Path to Maya executable
        e.g. "C:\\Program Files\\Autodesk\\Maya2024\\bin\\maya.exe"
    """
    maya_installs = get_available_maya_install_dirs()
    if len(maya_installs) == 0:
        logger.warning("Unable to find latest Maya path. No Maya installation detected on this system.")
        return
    maya_install_dir = get_maya_path(get_system(), max(maya_installs), get_maya_python=get_maya_python)
    if preferred_version is not None and preferred_version in maya_installs:
        maya_install_dir = get_maya_path(get_system(), preferred_version, get_maya_python=get_maya_python)
    if not os.path.exists(maya_install_dir):
        logger.warning(f"Unable to find latest Maya path. Missing: {maya_install_dir}")
        return
    return maya_install_dir


def launch_maya_from_path(maya_path, python_script=None, additional_args=None):
    """
    Launches Maya using provided path
    Args:
        maya_path (str): Path to the maya executable e.g. "maya.exe" (Complete path)
        python_script (str): A python script in string format. If provided, it runs after opening Maya
        additional_args (optional, list): Additional arguments. e.g. ["-pythonver", "3"]
    Example:
        launch_maya(maya_path="C:\\Program Files\\Autodesk\\Maya2024\\bin\\maya.exe"
                    python_script='import sys; print("The arg number is: " + sys.argv[-1])',
                    preferred_version='2024',
                    additional_args=[7])  # Maya 2024 opens and prints "The arg number is: 7"
    """
    if not os.path.exists(maya_path):
        logger.warning(f"Unable to launch Maya. Provided path does not exist: {maya_path}")
        return
    args = [maya_path]
    if python_script is not None:
        encoded_python = base64.b64encode(python_script.encode('utf-8'))
        script_text = '''python("import base64; exec (base64.urlsafe_b64decode({}))")'''
        args += ['-c', script_text.format(encoded_python)]
    # Additional Arguments
    if additional_args is not None:
        if isinstance(additional_args, list):
            for arg in additional_args:
                args.append(str(arg))
        else:
            logger.warning(f"Unable to use additional arguments. Please use a list.")
    subprocess.check_call(args)


def launch_maya(preferred_version=None, python_script=None, additional_args=None):
    """
    Launches Maya latest automatically detected Maya executable
    Args:
        python_script (str): A python script in string format. If provided, it runs after opening Maya
        preferred_version (optional, str): The preferred version. A string with four digits e.g. "2024"
                                              If found, that will be used, otherwise the latest detected version
                                              is returned instead.
        additional_args (optional, list): A list of additional arguments (elements are converted to string)
                                          e.g. ["-pythonver", "3"]
    Example:
        launch_maya(python_script='import sys; print("The arg number is: " + sys.argv[-1])',
                    preferred_version='2024',
                    additional_args=[7])  # Maya 2024 opens and prints "The arg number is: 7"
    """
    maya_path = get_maya_executable(preferred_version=preferred_version)
    if maya_path:
        launch_maya_from_path(maya_path=maya_path,
                              python_script=python_script,
                              additional_args=additional_args)


def run_script_using_maya_python(script_path, preferred_version=None):
    """
    Runs provided script using the latest detected Maya Python ("mayapy")
    Args:
        script_path (str): Path to python script
        preferred_version (optional, str): The preferred version. A string with four digits e.g. "2024"
                                              If found, that will be used, otherwise the latest detected version
                                              is returned instead.
    """
    headless_maya = get_maya_executable(get_maya_python=True, preferred_version=preferred_version)
    if os.path.exists(headless_maya):
        output = subprocess.call([str(headless_maya), script_path])
        return output
    else:
        logger.warning(f"Unable to find maya python. Missing file: {headless_maya}")


def process_launch_options(sys_args):
    """
    Processes the package arguments to determine launch action.
    Available arguments:
        -install : Installs package, so it starts automatically when Maya runs. (Overwrite files if existing)
        -install -clean: Installs package, but if previous installation is detected, it deletes it first
        -install -gui: Opens installation GUI instead of running command-line installation

        -uninstall : Uninstall package (If detected on the system)

        -launch : Runs Maya with package from current location
        -launch -dev: Run Maya from current location with developer options
        -test: Run all unittests
    Args:
        sys_args (list): A "sys.argv" list. First object ("argv[0]") is expected to the script name.
                         (Full path is not guaranteed as it's system dependent)
    Returns:
        bool: True if a launch option was found an executed, otherwise False.
    """
    if not isinstance(sys_args, list):  # Initial type check
        raise TypeError(f'Provided argument is not a list. Please use "sys.argv" as input and try again.')
    if len(sys_args) == 0:  # Missing script name argument
        raise ValueError(f'Missing script name. Make sure to use "sys.argv" as input. Current input: {sys_args}')
    elif len(sys_args) == 1:  # No extra arguments
        logger.debug("No additional launch arguments.")
        return
    # Launch Options
    if sys_args[1] == "-install":
        if "-clean" in sys_args:
            import gt.utils.setup_utils as setup_utils
            setup_utils.install_package(clean_install=True)
        elif "-gui" in sys_args:
            import gt.tools.package_setup as package_setup
            package_setup.launcher_entry_point()
        else:
            import gt.utils.setup_utils as setup_utils
            setup_utils.install_package(clean_install=False)
        return True
    elif sys_args[1] == "-uninstall":
        import gt.utils.setup_utils as setup_utils
        setup_utils.uninstall_package()
        return True
    elif sys_args[1] == "-launch":
        if "-dev" in sys_args:
            print("launch in dev mode...")  # WIP
        try:
            import maya.cmds as cmds
            is_batch_mode = cmds.about(batch=True)
            load_package_menu(launch_latest_maya=is_batch_mode)
        except Exception as e:
            logger.debug(str(e))
            load_package_menu(launch_latest_maya=True)  # Failed to import cmds, not in Maya
        return True
    elif sys_args[1] == "-test":
        utils_dir = os.path.dirname(__file__)
        package_dir = os.path.dirname(utils_dir)
        if package_dir not in sys.path:
            sys.path.append(package_dir)  # Ensure package is available
        import tests
        if "-all" in sys_args:
            tests.run_all_tests_with_summary()
        else:
            print('Unrecognized or missing launching option:\n1. "-all" to run all unittests.\n')
            logger.warning("Unable to run test. Unrecognized or missing launching option.")
            return False
        return True
    else:
        unrecognized_args = ', '.join(f'"{str(arg)}"' for arg in sys_args[1:])
        sys.stdout.write(f"Unrecognized launch options: {unrecognized_args}\n")
        return False


def initialize_from_package(import_path, entry_point_function):
    """
    Attempts to import and execute the provided script using its entry point function
    Args:
        import_path (str): Name of the script or module to import. For example "tools.renamer"
        entry_point_function (str): Name of the entry point function, usually the one that opens the script's UI
                                    Parenthesis "()" are not necessary as it's automatically added when running it.

    Returns:
        bool: True if there were no errors, false if it failed
    """
    import importlib
    module = importlib.import_module(import_path)

    # Call Entry Function
    entry_line = 'module.' + entry_point_function + '()'
    try:
        eval(entry_line)
        return True
    except Exception as exception:
        logger.warning('"' + entry_line + '" failed to run.')
        logger.warning('Error: ' + str(exception))
        return False


def initialize_tool(import_path, entry_point_function="launch_tool"):
    """
    Attempts to import and execute the provided script using its entry point function
    Similar to "initialize_package", but with some default initial values.
    Args:
        import_path (str): Name of the script or module to import. For example "renamer"
                          IMPORTANT: The prefix "tools." will automatically be added to it.
        entry_point_function (str, optional): Name of the entry point function. Default "build_ui"
                                              Parenthesis "()" are automatically added when running it.

    Returns:
        bool: True if there were no errors, false if it failed
    """
    return initialize_from_package(import_path="gt.tools." + import_path,
                                   entry_point_function=entry_point_function)


def initialize_utility(import_path, entry_point_function="launch_tool"):
    """
    Attempts to import and execute the provided script using its entry point function
    Similar to "initialize_package", but with some default initial values.
    Args:
        import_path (str): Name of the script or module to import. For example "renamer"
                          IMPORTANT: The prefix "tools." will automatically be added to it.
        entry_point_function (str, optional): Name of the entry point function. Default "build_ui"
                                              Parenthesis "()" are automatically added when running it.

    Returns:
        bool: True if there were no errors, false if it failed
    """
    return initialize_from_package(import_path="gt.utils." + import_path,
                                   entry_point_function=entry_point_function)


def load_package_menu(launch_latest_maya=False):
    """
    Loads the script from the current location, so it can be used without installing it.
    It can also open the latest Maya version detected on the machine and injects the package loader script onto it
    causing the package main maya menu to be loaded from start.
    Essentially a "Run Only" option for the package and maya menu.
    Args:
        launch_latest_maya (bool, optional): If true, it will launch the latest detected version of Maya and inject
                                            the necessary code to import the package and create its maya menu.
    """
    # utils/data/scripts/package_loader.py
    package_loader_script = os.path.join(DataDirConstants.DIR_SCRIPTS, "package_loader.py")
    file_content = ""
    if os.path.exists(package_loader_script):
        with open(package_loader_script, "r") as file:
            file_content = file.read()
    search_string = 'utils.executeDeferred(load_package_menu)'
    replace_string = f'utils.executeDeferred(load_package_menu, """{str(DataDirConstants.DIR_PACKAGE)}""")'
    injection_script = file_content.replace(search_string, replace_string)
    if launch_latest_maya:
        launch_maya(python_script=injection_script)
    else:
        if DataDirConstants.DIR_PACKAGE not in sys.path:
            sys.path.append(DataDirConstants.DIR_PACKAGE)
        try:
            from gt.tools.package_setup import gt_tools_maya_menu
            gt_tools_maya_menu.load_menu()
        except Exception as e:
            logger.warning(f"Unable to load GT Tools. Issue: {str(e)}")


def time_profiler(func):
    """
    A decorator that measures the execution time of a function.

    Args:
        func (callable): The function to be profiled.

    Returns:
        callable: The decorated function.

    Example:
        @time_profiler
        def my_function(arg1, arg2):
            # Function code here

        my_function(10, arg2='test')

    Output:
        Function "my_function(10,) {'arg2': 'test'}" took 0.1234 seconds to run.
    """
    @wraps(func)
    def time_profiler_wrapper(*args, **kwargs):
        """
        Wrapper function that measures the execution time of the decorated function.

        Args:
            *args: Variable-length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The result of the decorated function.

        Prints:
            The execution time of the decorated function.

        Example:
            result = time_profiler_wrapper(10, arg2='test')
        """
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        print(f'Execution Time: {total_time:.4f} - Function: {func.__name__}{args} {kwargs}')
        return result
    return time_profiler_wrapper


def callback(callbacks, *args, **kwargs):
    """Execute a list of callback functions with the given arguments and keyword arguments.

    This function takes a list of callback functions, and for each function in the list,
    it attempts to call the function with the provided arguments and keyword arguments.

    Args:
        callbacks (list or callable): A list of callable functions or a single callable function.
            If a single function is provided, it will be converted into a list with one element.

        *args: Variable-length argument list to be passed to the callback functions.

        **kwargs: Arbitrary keyword arguments to be passed to the callback functions.

    Note:
        - If a callback function raises an exception during execution, the exception will be
          caught and logged as a debug message using the logger.

        - If an element in the 'callbacks' list is not a callable function, it will be ignored,
          and an error message will be logged using the logger.
    """
    if callbacks:
        if not isinstance(callbacks, list):
            callbacks = [callbacks]  # Convert to list in case arg was provided as a function
        for func in callbacks:
            if callable(func):
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    logger.debug(f"Unable to execute callback function. Issue: {e}")
            else:
                logger.debug(f"Error: {func} is not a callable function.")


def execute_deferred(func, *args, **kwargs):
    """
    Execute a function or code either immediately or deferred based on the Maya application state.

    This function checks if Maya is in interactive mode and either executes the provided function
    immediately or defers its execution. If Maya is not in interactive mode, it can execute the
    provided function as a string of code or a regular callable.


    Args:
        func: The function to be executed. It can be a callable function, a string containing code,
              or any other executable entity. If providing a function as a string, args and kwargs will be ignored.
        *args: Arguments to be passed to the function.
        **kwargs: Keyword arguments to be passed to the function.

    Example:
        # Defining a simple function
        def my_function(arg1, arg2):
            print(arg1 + arg2)

        # Calling execute_deferred with a regular function
        execute_deferred(my_function, 10, 20)  # This will be executed immediately

        # Calling execute_deferred with a code string
        code_str = "print('Code execution within Maya')"
        execute_deferred(code_str)  # This will be executed immediately if not in interactive mode

        # Using execute_deferred in interactive mode
        def print_message(msg):
            print(msg)

        execute_deferred(print_message, "Deferred execution in interactive mode")
        # This will be deferred if Maya is in interactive mode
    """
    try:
        import maya.utils
        import maya.OpenMaya
        if maya.OpenMaya.MGlobal.mayaState() == maya.OpenMaya.MGlobal.kInteractive:
            maya.utils.executeDeferred(func, *args, **kwargs)
            return
    except Exception as e:
        logger.debug(f'Unable to use "maya.utils.executeDeferred" to call function. Calling it normally. Issue: {e}')
    if isinstance(func, str):
        exec(func)
    else:
        func(*args, **kwargs)


def import_from_path(path):
    """
    Dynamically imports modules or objects using their full path.

    Args:
        path (str): The full path to the module or object (e.g., "module.submodule" or "module.submodule.ClassName").

    Returns:
        type: The imported module or object if successful, otherwise None.
    """
    try:
        module_path, object_name = path.rsplit('.', 1)
        module = importlib.import_module(module_path)

        if object_name:
            imported_object = getattr(module, object_name, None)
            if imported_object is not None:
                return imported_object
        else:
            return module

        return None
    except (ImportError, AttributeError, ValueError, ModuleNotFoundError) as e:
        return None


def get_function_arguments(func, kwargs_as_dict=False):
    """
    Get the arguments and keyword arguments of a given function.

    Args:
        func (callable): The function to inspect.
        kwargs_as_dict (bool, optional): If active, it will return the kwargs as a dictionary with
                                          the keyword names and their default values.

    Returns:
        tuple: A tuple containing two lists:
            - List of argument names
            - List of keyword argument names (or a dictionary in case "kwargs_as_dict" is True)
    """
    import inspect

    signature = inspect.signature(func)
    args = []
    kwargs = []
    kwargs_dict = {}

    for param_name, param in signature.parameters.items():
        if param.default == inspect.Parameter.empty:
            args.append(param_name)
        else:
            kwargs.append(param_name)
            kwargs_dict[param_name] = param.default
    if kwargs_as_dict:
        return args, kwargs_dict
    return args, kwargs


def get_docstring(func, strip=False, strip_new_lines=False):
    """
    Get the docstring of a target function.

    Args:
        func (callable): The function whose docstring needs to be retrieved.
        strip (bool, optional): If True, leading empty space will be removed from each line of the docstring.
        strip_new_lines (bool, optional): If True, it will remove new lines from the beginning of the docstring and end.

    Returns:
        str: The docstring of the target function.
    """
    if not callable(func):
        raise ValueError("Input 'func' must be a callable function.")

    docstring = func.__doc__
    if docstring is None:
        return ""

    if strip:
        # Remove leading empty spaces from each line of the docstring
        docstring = '\n'.join(line.lstrip() for line in docstring.split('\n'))
    if strip_new_lines:
        docstring = docstring.lstrip('\n')
        if docstring.endswith(docstring):
            docstring = docstring[:-len('\n')]

    return docstring


def get_formatted_time(format_str="%Y-%m-%d %H:%M:%S"):
    """
    Get the current time and return it as a formatted string.

    Args:
        format_str (str, optional): Format string for formatting the time. Defaults to "%Y-%m-%d %H:%M:%S".

    Returns:
        str: Formatted string representing the current time.
    """
    current_time = datetime.now()
    formatted_time = current_time.strftime(format_str)
    return formatted_time


def execute_python_code(code, import_cmds=False, use_maya_warning=False, verbose=True, exec_globals=None,
                        custom_logger=None, log_level=logging.WARNING, raise_errors=False):
    """
    Executes the given Python code string in the Maya environment.

    Args:
        code (str): The Python code to be executed.
        import_cmds (bool, optional): If active, it will automatically import maya.cmds and add it to "exec_globals"
        use_maya_warning (bool, optional): If active it will log using a "cmds.warning()"
        verbose (bool, optional): If active, it will return messages
        exec_globals (dict, optional): If provided, this dictionary is passed to the exec function as globals (2nd arg)
        custom_logger (Logger, optional): If provided, it will use this logger instead of the "system_utils" logger.
        log_level (int, optional): Logging level (only used if verbose is active)
        raise_errors (bool, optional): If active, it will raise errors instead of just giving messages.
    """
    _exec_globals = {}
    if exec_globals and isinstance(exec_globals, dict):
        _exec_globals = exec_globals
    try:
        if import_cmds:
            import maya.cmds as cmds
            _exec_globals['cmds'] = cmds
        exec(code, _exec_globals)
    except Exception as e:
        from gt.utils.feedback_utils import log_when_true
        traceback_str = traceback.format_exc()
        if raise_errors:
            raise e
        if use_maya_warning:
            import maya.cmds as cmds
            cmds.warning(traceback_str)
            cmds.warning(e)
            return
        _logger = logger
        if custom_logger:
            _logger = custom_logger
        log_when_true(input_logger=_logger, input_string=str(e), do_log=verbose, level=log_level)


def create_object(class_name, raise_errors=True, class_path=None, *args, **kwargs):
    """
    Creates an instance of a class based on the provided class name.

    Args:
        class_name (str): The name of the class to be instantiated.
        raise_errors (bool, optional): Whether to raise errors or log warnings for exceptions. Default is True.
        class_path (str, dict, optional): The module path where the class is located. Default is None.
                                          A dictionary can also be provided, for example "locals()"
        *args: Positional arguments to pass when creating the object.
        **kwargs: Keyword arguments to pass when creating the object.

    Returns:
        object: An instance of the specified class.

    Raises:
        TypeError: If the specified class_name does not correspond to a valid class.
        ImportError: If the specified module or class cannot be imported.
        AttributeError: If the specified class_name is not found in the module.
        NameError: If the specified class_name is not found in the global namespace.
    """
    if class_path and isinstance(class_path, str):
        # Attempt to import the module dynamically
        try:
            module = importlib.import_module(class_path)
        except ImportError as e:
            message = f"Error importing module '{class_path}': {str(e)}"
            if raise_errors:
                raise ImportError(message)
            else:
                logger.warning(message)
                return None

        # Check if the class name exists in the imported module
        if hasattr(module, class_name):
            class_obj = getattr(module, class_name)
        else:
            message = f"{class_name} not found in module '{class_path}'."
            if raise_errors:
                raise AttributeError(message)
            else:
                logger.warning(message)
                return None
    elif class_name in globals():
        # Get the class object using globals()
        class_obj = globals()[class_name]
    elif class_path and isinstance(class_path, dict) and class_name in class_path:
        class_obj = class_path[class_name]
    else:
        message = (f'Unable to create object. A path  for "{class_name}" was not provided and it was not found in the '
                   f'global namespace.')
        if raise_errors:
            raise NameError(message)
        else:
            logger.warning(message)
            return None

    # Check if the object is a class
    if isinstance(class_obj, type):
        try:
            # Create an instance of the class with args and kwargs
            obj = class_obj(*args, **kwargs)
            return obj
        except Exception as e:
            message = f"Error creating an instance of '{class_name}': {str(e)}"
            if raise_errors:
                raise TypeError(message)
            else:
                logger.warning(message)
                return None
    else:
        message = f"{class_name} is not a class."
        if raise_errors:
            raise TypeError(message)
        else:
            logger.warning(message)
            return None


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    # out = os.environ.keys()
    out = get_maya_preferences_dir(get_system())
    # out = initialize_from_package()
    print(out)
