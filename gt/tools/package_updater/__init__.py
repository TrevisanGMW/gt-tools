"""
 GT Check for Updates - This script compares your current GT Tools version with the latest release.
 github.com/TrevisanGMW/gt-tools - 2020-11-10

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.

 1.1 - 2020-11-11
 Fixed a few issues with the color of the UI.
 Updated link to show only latest release.
 The "Update" button now is disabled after refreshing.

 1.2 - 2020-11-13
 Added code to try to retrieve the three latest releases

 1.3 - 2020-11-15
 Changed title background color to grey
 Added dates to changelog

 1.4 - 2020-12-04
 Added a text for when the version is higher than expected (Unreleased Version)
 Added an auto check for updates so user's don't forget to update
 Added threading support (so the http request doesn't slow things down)

 1.5 - 2021-05-11
 Made script compatible with Python 3 (Maya 2022+)

 1.6 - 2021-10-21
 Updated parsing mechanism to be fully compatible with semantic versioning
 Updated the silent update checker

 1.7.0 to 1.7.1 - 2022-07-07 to 2022-10-27
 PEP8 Cleanup
 Added patch to version
 Changed a few variable names
 Added output message for when changing auto check or interval values
 Fixed an issue where it wouldn't be able to make an HTTP request on Maya 2023+
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
__version_tuple__ = (1, 7, 1)
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
        _view = package_updater_view.PackageUpdaterView()
    else:
        from gt.ui.qt_utils import get_maya_main_window
        maya_window = get_maya_main_window()
        _view = package_updater_view.PackageUpdaterView(parent=maya_window)

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
