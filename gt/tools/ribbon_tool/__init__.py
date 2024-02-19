"""
 Ribbon Tool
 github.com/TrevisanGMW/gt-tools -  2024-02-17
"""
from gt.tools.ribbon_tool import ribbon_tool_controller
from gt.tools.ribbon_tool import ribbon_tool_view
from gt.ui import qt_utils

# Tool Version
__version_tuple__ = (0, 0, 1)
__version_suffix__ = 'a'
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using this tool.
    Creates Model, View and Controller and uses QtApplicationContext to determine context (inside of Maya or not?)
    """
    with qt_utils.QtApplicationContext() as context:
        _view = ribbon_tool_view.RibbonToolView(parent=context.get_parent(), version=__version__)
        _controller = ribbon_tool_controller.RibbonToolController(view=_view)


if __name__ == "__main__":
    launch_tool()
