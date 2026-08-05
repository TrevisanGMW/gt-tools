"""
 Animation Retargeter
"""

import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Tool Version
__version_tuple__ = (1, 1, 0)
__version_suffix__ = ""
__version__ = ".".join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using this tool.
    Creates Model, View and Controller and uses QtApplicationContext to determine context (inside of Maya or not?)
    """
    from gt.tools.retargeter import retargeter_controller
    from gt.tools.retargeter import retargeter_model
    from gt.tools.retargeter import retargeter_view
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        _model = retargeter_model.RetargeterModel()
        _view = retargeter_view.RetargeterView(parent=context.get_parent(), model=_model, version=__version__)
        _controller = retargeter_controller.RetargeterController(model=_model, view=_view)


if __name__ == "__main__":
    launch_tool()
