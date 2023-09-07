"""
 Curve Library
 github.com/TrevisanGMW/gt-tools - 2023-07-17
"""
from gt.tools.curve_library import curve_library_controller
from gt.tools.curve_library import curve_library_model
from gt.tools.curve_library import curve_library_view
from gt.ui import qt_utils
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Tool Version
__version_tuple__ = (1, 1, 3)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using this tool.
    Creates Model, View and Controller and uses QtApplicationContext to determine context (inside of Maya or not?)
    """
    with qt_utils.QtApplicationContext() as context:
        _view = curve_library_view.CurveLibraryView(parent=context.get_parent(), version=__version__)
        _model = curve_library_model.CurveLibraryModel()
        _controller = curve_library_controller.CurveLibraryController(model=_model, view=_view)


if __name__ == "__main__":
    launch_tool()
