"""
System Utilities - Utilities related to system activities, such as paths, open explorer, etc...
This script should not import "maya.cmds" as it's also intended to be used outside of Maya.
github.com/TrevisanGMW/gt-tools
"""
import subprocess
import tempfile
import logging
import pathlib
import sys
import os
import re

OS_MAC = 'darwin'
OS_LINUX = 'linux'
OS_WINDOWS = 'win32'
known_systems = [OS_WINDOWS, OS_MAC, OS_LINUX]

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("system_utils")
logger.setLevel(logging.INFO)


def get_system():
    """
    Get system in which this script is running
    Returns:
        System name.
        e.g. "win32" for Windows, or "darwin" for MacOS
    """
    system = sys.platform
    if system not in known_systems:
        logger.debug(f'Unexpected system returned: {system}]')
    return system


def get_temp_folder():
    return tempfile.gettempdir()


def get_home_dir():
    """
    Returns home path

    Returns:
        Home path
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
        String (path) to the desktop folder
    """
    return os.path.join(get_home_dir(), 'Desktop')


def get_maya_install_dir(system):
    """
    Get Maya installation folder (Autodesk folder where you find all Maya versions)
    Return:
        Path to autodesk folder (where you find maya#### folders
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


def get_maya_path(system, version):
    """
    Get a path to Maya executable
    """
    install_dir = get_maya_install_dir(system)
    maya_paths = {
        OS_LINUX: "/usr/bin/",
        OS_MAC: f"{install_dir}/maya{version}/Maya.app/Contents/bin/maya",
        OS_WINDOWS: f"{install_dir}\\Maya{version}\\bin\\maya.exe",
    }
    if system not in maya_paths.keys():
        raise KeyError(f'Unable to find the given system in listed paths. System: "{system}"')

    return maya_paths.get(system)


def open_file_dir(path):
    """
    Opens the directory where the provided path points to
    Args:
        path (string): A path to a file or directory
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
    TODO:
        MacOS path
    """
    win_maya_settings_dir = ""
    if system == OS_WINDOWS:
        win_maya_settings_dir = os.path.expanduser('~')
        win_maya_settings_dir = os.path.join(win_maya_settings_dir, "Documents")
        win_maya_settings_dir = os.path.join(win_maya_settings_dir, "maya")

    maya_settings_paths = {
        OS_LINUX: "/usr/bin/",
        OS_MAC: f"~/Library/Preferences/Autodesk/maya",
        OS_WINDOWS: win_maya_settings_dir,
    }
    if system not in maya_settings_paths.keys():
        raise KeyError(f'Unable to find the given system in listed paths. System: "{system}"')

    return maya_settings_paths.get(system)


def get_available_maya_setting_dirs():
    """
    Gets all folders matching the pattern "####" inside the maya settings directory.
    Returns:
        Dictionary with maya versions as keys and path as value
        e.g. { "2024": "C:\\Users\\UserName\\Documents\\maya\\2024"}
    """
    maya_settings_dir = get_maya_settings_dir(get_system())
    if os.path.exists(maya_settings_dir):
        maya_folders = os.listdir(maya_settings_dir)
        existing_folders = {}
        for folder in maya_folders:
            if re.match("[0-9][0-9][0-9][0-9]", folder):
                existing_folders[folder] = os.path.join(maya_settings_dir, folder)
        return existing_folders
    else:
        logger.warning(f'Missing provided path: "{maya_settings_dir}"')


def get_available_maya_install_dirs():
    """
    Gets all folders matching the pattern "Maya####" inside the autodesk directory.
    Returns:
        Dictionary with maya versions as keys and path as value
        e.g. { "2024": "C:\\Users\\UserName\\Documents\\maya\\2024"}
        If nothing is found, it returns an empty dictionary
    """
    maya_settings_dir = get_maya_install_dir(get_system())
    if os.path.exists(maya_settings_dir):
        maya_folders = os.listdir(maya_settings_dir)
        existing_folders = {}
        for folder in maya_folders:
            if re.match("Maya[0-9][0-9][0-9][0-9]", folder):
                folder_digits = re.sub("[^0-9]", "", folder)
                existing_folders[folder_digits] = os.path.join(maya_settings_dir, folder)
        return existing_folders
    else:
        logger.warning(f'Missing provided path: "{maya_settings_dir}"')
        return {}


def get_latest_maya_path():
    maya_installs = get_available_maya_install_dirs()
    if len(maya_installs) == 0:
        logger.warning("Unable to find latest Maya path. No Maya installation detected on this system.")
        return
    latest_maya_install_dir = get_maya_path(get_system(), max(maya_installs))
    if not os.path.exists(latest_maya_install_dir):
        logger.warning(f"Unable to find latest Maya path. Missing: {latest_maya_install_dir}")
        return
    return latest_maya_install_dir


def launch_maya_from_path(maya_path, add_python_three_args=False):
    """
    Launches Maya
    Args:
        maya_path (string): Path to the maya executable e.g. "maya.exe"
        add_python_three_args (optional, bool): If active, it will try to add arguments to tell maya to run python 3
    """

    if add_python_three_args:
        subprocess.Popen([maya_path, "-pythonver", "3"])
    else:
        subprocess.Popen([maya_path])


def launch_latest_maya(add_python_three_args=False):
    maya_path = get_latest_maya_path()
    if maya_path:
        launch_maya_from_path(maya_path=maya_path,
                              add_python_three_args=add_python_three_args)


if __name__ == "__main__":
    from pprint import pprint
    out = None
    pprint(out)
