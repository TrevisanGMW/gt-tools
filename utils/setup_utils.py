"""
Setup Utilities - install/uninstall package from system
"""
import sys

from session_utils import is_script_in_py_maya
import maya.cmds as cmds
import logging
import shutil
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("setup_utils")
logger.setLevel(logging.INFO)

PACKAGE_NAME = "gt-tools"
PACKAGE_REQUIREMENTS = ['tools', 'utils', 'ui', '__init__.py']
PACKAGE_ENTRY_LINE = "source \"gt_tools_menu.mel\";"


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
    Gets required folders elements from the package root
    Returns:
        Dictionary with required files as keys and paths as values
        e.g. { "tools": "C:\\tools"}
        If nothing is found, it returns an empty dictionary
    """
    source_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(source_dir)
    found_requirements = {}
    if os.path.exists(parent_dir):
        package_root = os.listdir(parent_dir)
        for item in package_root:
            if item in PACKAGE_REQUIREMENTS:
                found_requirements[item] = os.path.join(parent_dir, item)
    else:
        logger.warning(f'Missing package root: "{parent_dir}"')
        return {}
    if sorted(list(found_requirements)) != sorted(PACKAGE_REQUIREMENTS):
        logger.warning(f'Missing package requirement: Expected items: "{PACKAGE_REQUIREMENTS}"')
        return {}
    return found_requirements


def copy_package_requirements(target_folder, package_requirements):
    """
    Copies files and directories from provided package_requirements to target folder
    Args:
        target_folder (str): Target folder. That's where the files will be copied to.
        package_requirements (dict): Dictionary containing key:"element name" and value:"element path"
                                     Essentially: file_name: file_path
                                     e.g {"tools": "C:/tools"}
                                     This can be generated using the function "get_package_requirements()"
    """
    # Is target a directory
    if not os.path.isdir(target_folder):
        raise NotADirectoryError(f'Unable to copy package requirements. "{target_folder}" is not a directory')
    # Copy
    for requirement, requirement_path in package_requirements.items():
        if os.path.isdir(requirement_path):  # Directories
            shutil.copytree(src=requirement_path,
                            dst=os.path.join(target_folder, requirement),
                            dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns('*.pyc', '__pycache__'))
        elif os.path.isfile(requirement_path):  # Files
            shutil.copy(requirement_path, target_folder)


def remove_previous_install(target_path):
    """
    Remove target path in case it exists and matches the name of the package.
    Function used to perform a clean installation.
    If package is not found or doesn't match the name, the operation is ignored.
    Args:
        target_path (str): Path to a directory that is a previous installation of the package
    """
    if os.path.exists(target_path):
        if os.path.basename(target_path) == PACKAGE_NAME:
            logger.debug(f'Removing previous install: "{target_path}"')
            shutil.rmtree(target_path)


def install_package(clean_install=True, verbose=True):
    """
    Installs package in the Maya Settings directory
    Args:
        clean_install (optional, bool): Will first delete the package folder before copying files. (No overwrite)
                                        Only deletes if the folder matches the name of the package. Default: True
        verbose (optional, bool): If active, script will print steps as it's going through it - Default: True
    Returns:
        bool: True if function reached the end successfully
    TODO:
        Add userSetup string
    """
    # If running in MayaPy - Initialize session
    if is_script_in_py_maya():
        print_when_true("Initializing Maya Standalone...", do_print=verbose)
        import maya.standalone
        maya.standalone.initialize()
    # Find Install Target Directory - Maya Settings Dir
    print_when_true("Fetching requirements...", do_print=verbose)
    maya_settings_dir = get_maya_settings_dir()
    if not os.path.exists(maya_settings_dir):
        logger.warning(f'Unable to install package. Missing required path: "{maya_settings_dir}"')
        return
    # Find Source Install Directories
    package_requirements = get_package_requirements()
    if not package_requirements:
        logger.warning(f'Unable to install package. Missing required directories: "{PACKAGE_REQUIREMENTS}"')
        return
    # Clean install
    package_target_folder = os.path.normpath(os.path.join(maya_settings_dir, PACKAGE_NAME))
    if clean_install:
        print_when_true("Removing previous install...", do_print=verbose)
        remove_previous_install(package_target_folder)
    # Create Package Folder
    if not os.path.exists(package_target_folder):
        os.makedirs(package_target_folder)
    # Copy files and directories
    print_when_true("Copying required files...", do_print=verbose)
    copy_package_requirements(package_target_folder, package_requirements)
    # Check installation integrity
    print_when_true("Checking installation integrity...", do_print=verbose)
    if check_installation_integrity(package_target_folder):
        print_when_true("\nInstallation completed successfully!", do_print=verbose)
        return True
    else:
        logger.warning(f'Installation failed integrity check. Package might not work as expected.')


def check_installation_integrity(package_target_folder):
    """
    Checks if all requirements were copied to the installation folder

    Parameters:
        package_target_folder (str): Path to the installation folder

    Returns:
        bool: True if all requirements were found. False otherwise.
    """
    if not package_target_folder or not os.path.isdir(package_target_folder):
        return False
    file_list = os.listdir(package_target_folder)
    missing_list = []
    for requirement in PACKAGE_REQUIREMENTS:
        if requirement not in file_list:
            missing_list.append(requirement)
    missing_string = ', '.join(missing_list)
    if len(missing_list) > 0:
        print(f"Missing required files: {missing_string}")
        return False
    return True


def uninstall_package():
    """
    Uninstalls package from the Maya Settings directory
    Returns:
        bool: True if function reached the end successfully
    TODO:
        Remove userSetup string
    """
    # If running in MayaPy - Initialize session
    if is_script_in_py_maya():
        logger.debug("Initializing Maya Standalone...")
        import maya.standalone
        maya.standalone.initialize()
    # Find Install Target Directory - Maya Settings Dir
    maya_settings_dir = get_maya_settings_dir()
    if not os.path.exists(maya_settings_dir):
        logger.warning(f'Unable to uninstall package. Unable to find install location: "{maya_settings_dir}"')
        return
    # Find Source Install Directories
    package_target_folder = os.path.normpath(os.path.join(maya_settings_dir, PACKAGE_NAME))
    if not os.path.exists(package_target_folder):
        logger.warning(f'Unable to uninstall package. No previous installation detected.')
        return
    # Clean install
    remove_previous_install(package_target_folder)
    return True


def print_when_true(input_string, do_print=True, use_system_write=False):
    """
    Print input string only when the parameter "do_print" is true
    Args:
        input_string (str): String to print
        do_print (optional, bool): If it should print or not (if active, it prints) - Default is active/True
        use_system_write (optional, bool): If active, it will uses "sys.stdout.write()" to print instead of
                                           the standard "print()" function. Default is inactive/False
    """
    if do_print:
        sys.stdout.write(f"{input_string}\n") if use_system_write else print(input_string)


def add_entry_line(file_path, create_missing_file=True):
    """
    Add entry line to provided path. The entry line is a line of code used to initialize package.

    Parameters:
        file_path (str): File path, usually a "userSetup" file
        create_missing_file (bool, optional): If provided file doesn't exist, a file is created.
    """
    # Determine if file is available and create missing ones
    if not file_path or not os.path.exists(file_path):
        if os.path.isdir(os.path.dirname(file_path)) and create_missing_file:
            open(file_path, 'a').close()  # Create empty file
            with open(file_path, 'w') as file:
                file.write(PACKAGE_ENTRY_LINE + "\n")
            return
        else:
            logger.warning(f'Unable to add entry line. Missing file: "{str(file_path)}".')
            return
    # Find if line exists before adding
    file_lines = []
    is_present = False
    with open(file_path, "r+") as file:
        file_lines = file.readlines()
        for line in file_lines:
            if line.startswith(PACKAGE_ENTRY_LINE):
                is_present = True

    if not is_present:
        with open(file_path, "w") as file:
            prefix = ""
            if len(file_lines) > 0:
                if not file_lines[-1].endswith("\n"):  # Is new line necessary?
                    prefix = "\n"
            file_lines.append(prefix + PACKAGE_ENTRY_LINE + "\n")
            file.writelines(file_lines)


if __name__ == "__main__":
    from pprint import pprint
    import maya.standalone as standalone

    # standalone.initialize()
    # logger.setLevel(logging.DEBUG)
    out = None
    # out = install_package()
    add_entry_line("C:\\Users\\guilherme.trevisan\\Desktop\\userSetup.mel")

    pprint(out)
