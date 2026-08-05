"""
 Extract Influence Joints
 github.com/TrevisanGMW/gt-tools - 2022-06-22
"""
from gt.tools.influences_to_python import influences_python_controller
from gt.tools.influences_to_python import influences_python_view
from gt.ui import qt_utils


# Tool Version
__version_tuple__ = (2, 0, 2)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using this tool.
    Creates Model, View and Controller and uses QtApplicationContext to determine context (inside of Maya or not?)
    """
    with qt_utils.QtApplicationContext() as context:
        _view = influences_python_view.InfluencesPythonView(parent=context.get_parent(), version=__version__)
        _controller = influences_python_controller.InfluencesPythonController(view=_view)


if __name__ == "__main__":
    launch_tool()
