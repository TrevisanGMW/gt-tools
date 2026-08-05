"""
Auto Rigger
github.com/TrevisanGMW - 2020-12-08
"""

from gt.tools.auto_rigger import rigger_controller
from gt.tools.auto_rigger import rigger_model
from gt.tools.auto_rigger import rigger_view
from gt.ui import qt_utils
import logging
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Tool Version
__version_tuple__ = (1, 0, 1)
__version_suffix__ = ""
__version__ = ".".join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool(project_path=None):
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using this tool.
    Creates Model, View and Controller and uses QtApplicationContext to determine context (inside of Maya or not?)
    Args:
        project_path (str, optional): If provided, the path is used as initial project o load in the tool.
    """
    with qt_utils.QtApplicationContext() as context:
        _view = rigger_view.RiggerView(parent=context.get_parent(), version=__version__)
        _model = rigger_model.RiggerModel()
        _controller = rigger_controller.RiggerController(model=_model, view=_view)
        if project_path and os.path.exists(project_path):
            _controller.load_project_from_file(file_path=project_path)


if __name__ == "__main__":
    import gt.utils.system as utils_sys

    # Save a project with the modules you want to test as "dev.json" on your desktop. Only loaded if found.
    desktop_path = utils_sys.get_desktop_path()
    development_project = os.path.join(desktop_path, "dev.json")
    launch_tool(project_path=development_project)
