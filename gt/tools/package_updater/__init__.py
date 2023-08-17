"""
 Package Updater - Checks for new releases and automatically download and install them
 github.com/TrevisanGMW/gt-tools - 2020-11-10

 1.1.0 to 1.7.1 - 2020-11-11 to 2022-10-27
 Updated link to show only latest release.
 The "Update" button now is disabled after refreshing.
 Changed it, so it retrieves three latest releases
 Added dates to changelog
 Added a label for when the version is higher than expected (Unreleased Version)
 Added an auto check for updates so user does not need to manually check
 Added threading support so the http request doesn't slow things down
 Made script compatible with Python 3 (Maya 2022+)
 Updated parsing mechanism to be fully compatible with semantic versioning
 PEP8 Cleanup
 Added patch to version
 Added output message for when changing auto check or interval values
 Fixed an issue where it wouldn't be able to make an HTTP request on Maya 2023+

 2.0.0 to 2.0.2 - 2023-08-08 to 2023-08-16
 Renamed tool from "GT Check for Updates" to "Package Updater".
 Updated to the test-driven development pattern.
 Recreated the update system to automatically download, extract and install update.
 Updated preferences system to use package variables instead of maya option vars
 Made tool dockable
"""
from gt.tools.package_updater import package_updater_controller
from gt.tools.package_updater import package_updater_model
from gt.tools.package_updater import package_updater_view
from PySide2.QtWidgets import QApplication
from gt.utils import session_utils
from gt.ui import qt_utils
import threading
import logging
import sys

# Logging Setup

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Tool Version
__version_tuple__ = (2, 0, 3)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def build_package_updater_gui(model=None):
    """
    Creates Model, View and Controller
    Args:
        model (PackageUpdaterModel, optional): If provided, the function will use the existing model
                                               instead of creating a new one, thus using the existing request data.
    """
    # Determine Parent
    # _standalone = session_utils.is_script_in_py_maya()
    with qt_utils.QtApplicationContext() as context:
        _view = package_updater_view.PackageUpdaterView(parent=context.get_parent(), version=__version__)
        if model:
            _model = model
        else:
            _model = package_updater_model.PackageUpdaterModel()
        _controller = package_updater_controller.PackageUpdaterController(model=_model, view=_view)


def silently_check_for_updates():
    _model = package_updater_model.PackageUpdaterModel()
    if not _model.get_auto_check():
        return
    if not _model.is_time_to_update():
        return

    def _initialize_tool_if_updating():
        """
        Internal function to check if an update is available, if it is, open package updater
        This function takes a little longer because it makes a request. It should always run as a thread.
        """
        _model.check_for_updates()
        _model.save_last_check_date_as_now()
        if _model.is_update_needed():
            build_package_updater_gui(model=_model)

    def _maya_retrieve_update_data():
        """ Internal function used to run a thread in Maya """
        """ Internal function used to check for updates using threads in Maya """
        from gt.utils.system_utils import execute_deferred
        execute_deferred(_initialize_tool_if_updating)
    try:
        thread = threading.Thread(None, target=_maya_retrieve_update_data)
        thread.start()
    except Exception as e:
        logger.debug(f'Unable to silently check for updates. Issue: {e}')


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using this tool.
    """
    build_package_updater_gui()


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    launch_tool()
