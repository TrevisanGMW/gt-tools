"""
 Auto Rigger
 github.com/TrevisanGMW - 2020-12-08
"""
from gt.tools.auto_rigger import rigger_controller
from gt.tools.auto_rigger import rigger_model
from gt.tools.auto_rigger import rigger_view
from gt.ui import qt_utils
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Tool Version
__version_tuple__ = (0, 0, 1)
__version_suffix__ = 'alpha'
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using this tool.
    Creates Model, View and Controller and uses QtApplicationContext to determine context (inside of Maya or not?)
    """
    with qt_utils.QtApplicationContext() as context:
        _view = rigger_view.RiggerView(parent=context.get_parent(), version=__version__)
        _model = rigger_model.RiggerModel()
        _controller = rigger_controller.RiggerController(model=_model, view=_view)


if __name__ == "__main__":
    launch_tool()
