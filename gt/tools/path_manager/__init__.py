"""
 Path Manager - A script for quickly re-pathing many elements in Maya.
 github.com/TrevisanGMW/gt-tools - 2020-08-26

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.
"""
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Tool Version
__version_tuple__ = (1, 2, 3)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool Path Manager.
    """
    from gt.tools.path_manager import path_manager
    path_manager.script_version = __version__
    try:
        path_manager_dialog.close()
        path_manager_dialog.deleteLater()
    except Exception as e:
        logger.debug(f'Initializing tool variable for the first time. Debug description: "{str(e)}".')
    path_manager.try_to_close_gt_path_manager()
    path_manager_dialog = path_manager.GTPathManagerDialog()
    path_manager_dialog.show()


if __name__ == "__main__":
    launch_tool()
