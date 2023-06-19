"""
Loader for the GT Tools package. It assumes that the installation is present inside the maya preferences folder.
e.g. Windows: "Documents/maya/gt-tools"
     MacOS: "Library/Preferences/Autodesk/Maya/gt-tools"
"""
import maya.utils as utils
import maya.cmds as cmds
import logging
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_tools_loader")
logger.setLevel(logging.INFO)


def load_package_menu(package_path=None):
    if not package_path:  # Find default install location
        maya_preferences = os.path.dirname(cmds.about(preferences=True))
        package_path = os.path.join(maya_preferences, "gt-tools")
    if not os.path.isdir(package_path):
        logger.warning(f"Missing package files. Expected location: {str(package_path)}")
        return
    if package_path not in sys.path:
        sys.path.append(package_path)
    try:
        from tools.package_setup import gt_tools_maya_menu
        gt_tools_maya_menu.load_menu()
    except Exception as e:
        logger.warning(f"Unable to load GT Tools. Issue: {str(e)}")


utils.executeDeferred(load_package_menu)

