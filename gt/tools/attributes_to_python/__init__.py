"""
 GT Attributes to Python - Tools for extracting attributes as python code.
 github.com/TrevisanGMW/gt-tools - 2021-12-01

 0.0.2 to 1.0.1- 2022-03-31 to 2022-10-06
 Added "Extract User-Defined Attributes" function
 Added save to shelf
 Added triple quote to string attributes

 2.0.0 to 2.0.1 - 2023-08-27
 Updated to VMC model using QT for the view.
 Added code highlighter
 Added line numbers
 Made view dockable
"""
from gt.tools.attributes_to_python import attributes_to_python_controller
from gt.tools.attributes_to_python import attributes_to_python_view
from gt.ui import qt_utils

__version_tuple__ = (2, 0, 1)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using this tool.
    Creates Model, View and Controller and uses QtApplicationContext to determine context (inside of Maya or not?)
    """
    with qt_utils.QtApplicationContext() as context:
        _view = attributes_to_python_view.AttributesToPythonView(parent=context.get_parent(), version=__version__)
        _controller = attributes_to_python_controller.AttributesToPythonController(view=_view)


if __name__ == "__main__":
    launch_tool()
