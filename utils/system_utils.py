"""
System Utilities - Utilities related to system activities, such as paths, open explorer, etc...
This script should not import "maya.cmds" as it's also intended to be used outside of Maya.
github.com/TrevisanGMW/gt-tools
"""
import subprocess
import tempfile
import logging
import pathlib
import base64
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


def get_temp_folder():
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
        OS_MAC: f"/Applications/Autodesk/",
        OS_WINDOWS: f"C:\\Program Files\\Autodesk\\",
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
        OS_WINDOWS: f"{install_dir}\\Maya{version}\\bin\\{executable_name}.exe",
    }
    if system not in maya_paths.keys():
        raise KeyError(f'Unable to find the given system in listed paths. System: "{system}"')

    return os.path.normpath(maya_paths.get(system))


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
        path = os.path.normpath(path)

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


def get_maya_settings_dir(system):
    """
    Get maya settings folder (folder contains scripts, prefs, etc..)
    Args:
        system (str): System string
    Returns:
        str: Path to settings folder (folder where you find scripts, prefs, etc..)
    """
    win_maya_settings_dir = ""
    mac_maya_settings_dir = ""
    if system == OS_WINDOWS:
        win_maya_settings_dir = os.path.expanduser('~')
        win_maya_settings_dir = os.path.join(win_maya_settings_dir, "Documents")
        win_maya_settings_dir = os.path.join(win_maya_settings_dir, "maya")
    elif system == OS_MAC:
        mac_maya_settings_dir = os.path.expanduser('~')
        mac_maya_settings_dir = os.path.join(mac_maya_settings_dir, "Library")
        mac_maya_settings_dir = os.path.join(mac_maya_settings_dir, "Preferences")
        mac_maya_settings_dir = os.path.join(mac_maya_settings_dir, "Autodesk")
        mac_maya_settings_dir = os.path.join(mac_maya_settings_dir, "maya")

    maya_settings_paths = {
        OS_LINUX: "/usr/bin/",
        OS_MAC: mac_maya_settings_dir,
        OS_WINDOWS: win_maya_settings_dir,
    }
    if system not in maya_settings_paths.keys():
        raise KeyError(f'Unable to find the given system in listed paths. System: "{system}"')

    return maya_settings_paths.get(system)


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
            maya_settings_dir = os.path.dirname(cmds.about(preferences=True))
        except Exception as e:
            logger.debug(f"Unable to retrieve settings using Maya commands. Issue: {e}. \n"
                         f"Attempting operation using system functions...")
            maya_settings_dir = get_maya_settings_dir(get_system())
    else:
        maya_settings_dir = get_maya_settings_dir(get_system())

    if os.path.exists(maya_settings_dir):
        maya_folders = os.listdir(maya_settings_dir)
        existing_folders = {}
        for folder in maya_folders:
            if re.match("^[0-9]{4}$", folder):
                existing_folders[folder] = os.path.join(maya_settings_dir, folder)
        return existing_folders
    else:
        logger.warning(f'Missing provided path: "{maya_settings_dir}"')
        return {}


def get_available_maya_install_dirs():
    """
    Gets all folders matching the pattern "Maya####" inside the autodesk directory.
    Returns:
        dict: Dictionary with maya versions as keys and path as value
        e.g. { "2024": "C:\\Users\\UserName\\Documents\\maya\\2024"}
        If nothing is found, it returns an empty dictionary
    """
    maya_settings_dir = get_maya_install_dir(get_system())

    if os.path.exists(maya_settings_dir):
        maya_folders = os.listdir(maya_settings_dir)
        existing_folders = {}
        for folder in maya_folders:
            if re.match("^maya[0-9]{4}$", folder.lower()):
                folder_digits = re.sub("[^0-9]", "", folder)
                existing_folders[folder_digits] = os.path.join(maya_settings_dir, folder)
        return existing_folders
    else:
        logger.warning(f'Missing provided path: "{maya_settings_dir}"')
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
        bool: True if a launch option was found an executed, otherwise None.
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
            import setup_utils
            setup_utils.install_package(clean_install=True)
        elif "-gui" in sys_args:
            import tools.package_setup as package_setup
            package_setup.launcher_entry_point()
        else:
            import setup_utils
            setup_utils.install_package(clean_install=False)
        return True
    elif sys_args[1] == "-uninstall":
        import setup_utils
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
    return initialize_from_package(import_path="tools." + import_path,
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
    return initialize_from_package(import_path="utils." + import_path,
                                   entry_point_function=entry_point_function)


def get_package_version(package_path=None):
    """
    Gets the package version, independently of the package folder name.
    Args:
        package_path (str, optional): If provided, the path will be used to determine the package path.
                                      It assumes that the package is using the same variable name "PACKAGE_VERSION"
    Returns:
        str: Package version as a string. "major.minor.patch"
        e.g. "3.0.0"
    """
    package_dir = package_path
    if package_path and os.path.exists(str(package_path)) is False:
        return "0.0.0"
    if package_path is None:
        utils_dir = os.path.dirname(__file__)
        package_dir = os.path.dirname(utils_dir)
    package_basename = os.path.basename(package_dir)
    package_parent_dir = os.path.dirname(package_dir)
    # Ensure package parent path is available
    if package_parent_dir not in sys.path:
        sys.path.append(package_parent_dir)
    try:
        imported_package = __import__(package_basename)
        return imported_package.PACKAGE_VERSION
    except Exception as e:
        logger.debug(f"Unable to retrieve current version. Issue: {str(e)}")
        return "0.0.0"


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
    utils_dir = os.path.dirname(__file__)
    package_loader_script = os.path.join(utils_dir, "data", "package_loader.py")  # utils/data/package_loader.py
    package_dir = os.path.dirname(utils_dir)
    file_content = ""
    if os.path.exists(package_loader_script):
        with open(package_loader_script, "r") as file:
            file_content = file.read()
    search_string = 'utils.executeDeferred(load_package_menu)'
    replace_string = f'utils.executeDeferred(load_package_menu, """{str(package_dir)}""")'
    injection_script = file_content.replace(search_string, replace_string)
    if launch_latest_maya:
        launch_maya(python_script=injection_script)
    else:
        if package_dir not in sys.path:
            sys.path.append(package_dir)
        try:
            from tools.package_setup import gt_tools_maya_menu
            gt_tools_maya_menu.load_menu()
        except Exception as e:
            logger.warning(f"Unable to load GT Tools. Issue: {str(e)}")


if __name__ == "__main__":
    from pprint import pprint
    out = None
    out = get_package_version()
    out = os.environ.keys()
    pprint(out)
