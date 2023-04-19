"""
Setup Utilities
Used to install/uninstall package from system
"""

# from system_utils import get_maya_settings_dir
import maya.cmds as cmds
import traceback
import logging
import shutil
import glob
import stat
import time
import sys
import os
import re
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("setup_utils")
logger.setLevel(logging.INFO)

PACKAGE_NAME = "gt-tools"
PACKAGE_REQUIREMENTS = ['tools', 'utils', 'ui']


def get_maya_settings_dir():
    """
    Get maya settings dir using cmds
    Usually Documents/maya
    Returns:
        Path to maya settings directory. Usually "C:/Users/<user-name>/Documents/maya"
    """
    return os.path.dirname(cmds.about(preferences=True))


def get_package_requirements():
    """
    Gets all folders matching the pattern "Maya####" inside the autodesk directory.
    Returns:
        Dictionary with maya versions as keys and path as value
        e.g. { "2024": "C:\\Users\\UserName\\Documents\\maya\\2024"}
        If nothing is found, it returns an empty dictionary
    """
    source_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(source_dir)
    existing_folders = {}
    if os.path.exists(parent_dir):
        maya_folders = os.listdir(parent_dir)
        for folder in maya_folders:
            if folder in PACKAGE_REQUIREMENTS:
                existing_folders[folder] = os.path.join(parent_dir, folder)
    else:
        logger.warning(f'Missing package root: "{parent_dir}"')
        return {}
    if sorted(list(existing_folders)) != sorted(PACKAGE_REQUIREMENTS):
        logger.warning(f'Missing package requirement: Expected directories: "{PACKAGE_REQUIREMENTS}"')
        return {}
    return existing_folders


def install_package():
    """
    Todo:
        Return response, installed? overwrite? uninstall?
    """
    # Find Install Target Directory
    maya_settings_dir = get_maya_settings_dir()
    if not os.path.exists(maya_settings_dir):
        logger.warning(f'Unable to install package. Missing required path: "{maya_settings_dir}"')
        return
    # Find Source Install Directories
    package_requirements = get_package_requirements()
    if not package_requirements:
        logger.warning(f'Unable to install package. Missing required directories: "{PACKAGE_REQUIREMENTS}"')
        return
    # Create Package Folder
    package_target_folder = os.path.normpath(os.path.join(maya_settings_dir, PACKAGE_NAME))
    if not os.path.exists(package_target_folder):
        os.makedirs(package_target_folder)
    for requirement, requirement_path in package_requirements.items():
        shutil.copytree(src=requirement_path,
                        dst=os.path.join(package_target_folder, requirement),
                        dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('*.pyc', '__pycache__'))
    return


if __name__ == "__main__":
    from pprint import pprint
    import maya.standalone as standalone
    standalone.initialize()
    out = None
    out = install_package()
    pprint(out)

