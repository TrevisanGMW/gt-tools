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

 2.0.0 - 2023-08-08
 Renamed tool from "GT Check for Updates" to "Package Updater".
 Updated to the test-driven development pattern.
 Recreated the update system to automatically download, extract and install update.
 Updated preferences system to use package variables instead of maya option vars
"""
from gt.tools.package_updater import package_updater_controller
from gt.tools.package_updater import package_updater_model
from gt.tools.package_updater import package_updater_view
from PySide2.QtWidgets import QApplication
from gt.utils import session_utils
import logging
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Tool Version
__version_tuple__ = (2, 0, 0)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def build_curve_library_gui(standalone=True):
    """
    Creates Model, View and Controller
    Args:
        standalone (bool, optional): If true, it will run the tool without the Maya window dependency.
                                     If false, it will attempt to retrieve the name of the main maya window as parent.
    """
    # Determine Parent
    if session_utils.is_script_in_py_maya():
        app = QApplication(sys.argv)
        _view = package_updater_view.PackageUpdaterView(version=__version__)
    else:
        from gt.ui.qt_utils import get_maya_main_window
        maya_window = get_maya_main_window()
        _view = package_updater_view.PackageUpdaterView(parent=maya_window, version=__version__)

    # Create connections
    _model = package_updater_model.PackageUpdaterModel()
    _controller = package_updater_controller.PackageUpdaterController(model=_model, view=_view)

    # Show window
    if standalone:
        _view.show()
        sys.exit(app.exec_())
    else:
        _view.show()
    return _view


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using this tool.
    """
    if session_utils.is_script_in_py_maya():
        build_curve_library_gui(standalone=True)
    else:
        build_curve_library_gui(standalone=False)


if __name__ == "__main__":
    launch_tool()
