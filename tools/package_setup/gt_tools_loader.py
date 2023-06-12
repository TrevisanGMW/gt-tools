"""
Loader for the GT Tools package. It assumes that the installation is present inside the maya preferences folder.
e.g. Windows: "Documents/maya/gt-tools"
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


def import_package():
    maya_preferences = os.path.dirname(cmds.about(preferences=True))
    package_path = os.path.join(maya_preferences, "gt-tools")
    if package_path not in sys.path:
        sys.path.append(package_path)
    try:
        from ui import maya_menu
        maya_menu.load_menu()
    except Exception as e:
        logger.warning(f"Expected path: {str(package_path)}")
        logger.warning(f"Unable to load GT Tools. Issue: {str(e)}")


utils.executeDeferred(import_package)
