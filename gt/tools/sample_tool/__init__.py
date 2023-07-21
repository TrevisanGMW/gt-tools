"""
 Sample Tool - A tool to be used as starting point or example for when creating new tools.
 github.com/TrevisanGMW/gt-tools - 2023-07-17
"""
from gt.tools.sample_tool import sample_controller
from gt.tools.sample_tool import sample_model
from gt.tools.sample_tool import sample_view
from PySide2.QtWidgets import QApplication
from gt.utils import session_utils
import logging
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def build_tool_example_gui(standalone=True):
    """
    Creates tool GUI and its connections.
    Parameters:
        standalone (bool, optional): If true, it will run the tool without the Maya window dependency.
                                     If false, it will attempt to retrieve the name of the main maya window as parent.
    """
    # Determine Parent
    if session_utils.is_script_in_py_maya():
        app = QApplication(sys.argv)
        _view = sample_view.SampleToolWindow()
    else:
        from gt.ui.qt_utils import get_maya_main_window
        maya_window = get_maya_main_window()
        _view = sample_view.SampleToolWindow(parent=maya_window)

    # Create connections
    _model = sample_model.SampleToolModel()
    _controller = sample_controller.SampleToolController(model=_model, view=_view)
    _controller.update_view()

    # Show window
    if standalone:
        _view.show()
        sys.exit(app.exec_())
    else:
        _view.show()
    return _view


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using this tool.
    """
    if session_utils.is_script_in_py_maya():
        build_tool_example_gui(standalone=True)
    else:
        build_tool_example_gui(standalone=False)


if __name__ == "__main__":
    launch_tool()
