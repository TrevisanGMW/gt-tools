"""
Path Manager - A script for quickly re-pathing many elements in Maya.
 github.com/TrevisanGMW/gt-tools - 2020-08-26
"""

# Tool Version
__version_tuple__ = (1, 2, 3)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """Creates, connects, and launches the Path Manager MVC tool.

    Returns:
        PathManagerController: Active Path Manager controller.
    """
    from gt.tools.path_manager import path_manager_controller
    from gt.tools.path_manager import path_manager_model
    from gt.tools.path_manager import path_manager_view
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        view = path_manager_view.PathManagerView(parent=context.get_parent(), version=__version__)
        model = path_manager_model.PathManagerModel()
        controller = path_manager_controller.PathManagerController(model=model, view=view)
        controller.start()
        return controller


if __name__ == "__main__":
    launch_tool()
