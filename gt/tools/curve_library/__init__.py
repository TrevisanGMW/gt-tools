"""
 Curve Library
 github.com/TrevisanGMW/gt-tools - 2023-07-17
"""
from gt.tools.curve_library import curve_library_controller
from gt.tools.curve_library import curve_library_model
from gt.tools.curve_library import curve_library_view
from PySide2.QtWidgets import QApplication
from gt.utils import session_utils
import logging
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Tool Version
__version_tuple__ = (1, 0, 1)
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
        _view = curve_library_view.CurveLibraryWindow(version=__version__)
    else:
        from gt.ui.qt_utils import get_maya_main_window
        maya_window = get_maya_main_window()
        _view = curve_library_view.CurveLibraryWindow(parent=maya_window, version=__version__)

    # Create connections
    _model = curve_library_model.CurveLibraryModel()
    _controller = curve_library_controller.CurveLibraryController(model=_model, view=_view)

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
