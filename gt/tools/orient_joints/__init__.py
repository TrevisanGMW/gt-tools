"""
 GT Orient Joints - Script for orienting multiple joints
 github.com/TrevisanGMW/gt-tools - 2023-01-19

"""
from gt.tools.orient_joints import orient_joints_controller
from gt.tools.orient_joints import orient_joints_view
from gt.ui import qt_utils

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
        _view = orient_joints_view.OrientJointsView(parent=context.get_parent(), version=__version__)
        _controller = orient_joints_controller.OrientJointsController(view=_view)


if __name__ == "__main__":
    launch_tool()
