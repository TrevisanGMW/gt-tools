"""
 Curve to Python - Script to convert curve shapes to python code.
 github.com/TrevisanGMW/gt-tools -  2020-01-02

 1.0.0 to 1.6.3 - 2020-01-03 to 2022-07-26
 Added support for non-unique names
 Fixed way the curve is generated to account for closed and opened curves
 Made script compatible with Python 3 (Maya 2022+)
 Added save to shelf

 2.0.0 - 2023-08-29
 Updated to VMC model using QT for the view.
 Added code highlighter
 Added line numbers
 Made view dockable
 Merged curve shape extraction tool
"""
from gt.tools.curve_to_python import curve_to_python_controller
from gt.tools.curve_to_python import curve_to_python_view
from gt.ui import qt_utils

# Tool Version
__version_tuple__ = (2, 0, 0)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using this tool.
    Creates Model, View and Controller and uses QtApplicationContext to determine context (inside of Maya or not?)
    """
    with qt_utils.QtApplicationContext() as context:
        _view = curve_to_python_view.CurveToPythonView(parent=context.get_parent(), version=__version__)
        _controller = curve_to_python_controller.CurveToPythonController(view=_view)


if __name__ == "__main__":
    launch_tool()
