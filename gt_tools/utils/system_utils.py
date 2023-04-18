"""
System Utilities - Utilities related to system activities, such as paths, open explorer, etc...
This script should not import "maya.cmds" as it's also intended to be used outside of Maya.
Writing and reading data should be handled in "data_utils"
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


def get_home_path():
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
    maya_settings_dir = get_maya_settings_dir(get_system())
    if os.path.exists(maya_settings_dir):
        maya_folders = os.listdir(maya_settings_dir)
        existing_folders = []
        for folder in maya_folders:
            if re.match("[0-9][0-9][0-9][0-9]", folder):
                existing_folders.append(os.path.join(maya_settings_dir, folder))
        return existing_folders
    else:
        logger.warning(f'Unable to process required path: "{maya_settings_dir}"')


def get_desktop_path():
    """
    Get path to the Desktop folder of the current user
    Returns:
        String (path) to the desktop folder
    """
    return os.path.join(get_home_path(), 'Desktop')


def get_temp_folder():
    return tempfile.gettempdir()


if __name__ == "__main__":
    from pprint import pprint
    out = None
    # out = get_maya_settings_dir(get_system())

    # out = get_available_maya_setting_dirs()
    # for t in out:
    #     open_file_dir(t)
    open_file_dir(get_temp_folder())
    pprint(out)
