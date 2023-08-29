"""
 Resource Library
 github.com/TrevisanGMW/gt-tools - 2023-08-29
"""
from gt.tools.resource_library import resource_library_controller
from gt.tools.resource_library import resource_library_model
from gt.tools.resource_library import resource_library_view
from gt.ui import qt_utils
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Tool Version
__version_tuple__ = (1, 0, 0)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using this tool.
    Creates Model, View and Controller and uses QtApplicationContext to determine context (inside of Maya or not?)
    """
    with qt_utils.QtApplicationContext() as context:
        _view = resource_library_view.ResourceLibraryView(parent=context.get_parent(), version=__version__)
        _model = resource_library_model.ResourceLibraryModel()
        _controller = resource_library_controller.ResourceLibraryController(model=_model, view=_view)


if __name__ == "__main__":
    launch_tool()
