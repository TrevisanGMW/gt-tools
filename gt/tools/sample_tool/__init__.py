"""
 Sample Tool - To be used as starting point or example for when creating new tools.
 2026-07-08
"""
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
    Creates Model, View and Controller
    """
    from gt.tools.sample_tool import sample_controller
    from gt.tools.sample_tool import sample_model
    from gt.tools.sample_tool import sample_view
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        _view = sample_view.SampleToolWindow(parent=context.get_parent(), version=__version__)
        _model = sample_model.SampleToolModel()
        _controller = sample_controller.SampleToolController(model=_model, view=_view)


if __name__ == "__main__":
    launch_tool()
