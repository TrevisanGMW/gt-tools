"""
 Package Updater - Checks for new releases and automatically download and install them
 github.com/TrevisanGMW/gt-tools - 2020-11-10
"""
from gt.tools.package_updater import package_updater_controller
from gt.tools.package_updater import package_updater_model
from gt.tools.package_updater import package_updater_view
from gt.ui import qt_utils
import threading
import logging

# Logging Setup

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Tool Version
__version_tuple__ = (2, 0, 5)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def build_package_updater_gui(model=None):
    """
    Creates Model, View and Controller
    Args:
        model (PackageUpdaterModel, optional): If provided, the function will use the existing model
                                               instead of creating a new one, thus using the existing request data.
    """
    # Determine Parent
    # _standalone = session_utils.is_script_in_py_maya()
    with qt_utils.QtApplicationContext() as context:
        _view = package_updater_view.PackageUpdaterView(parent=context.get_parent(), version=__version__)
        if model:
            _model = model
        else:
            _model = package_updater_model.PackageUpdaterModel()
        _controller = package_updater_controller.PackageUpdaterController(model=_model, view=_view)


def silently_check_for_updates():
    """Checks for package updates without displaying an interactive dialog."""
    _model = package_updater_model.PackageUpdaterModel()
    if not _model.get_auto_check():
        return
    if not _model.is_time_to_update():
        return

    def _initialize_tool_if_updating():
        """
        Internal function to check if an update is available, if it is, open package updater
        This function takes a little longer because it makes a request. It should always run as a thread.
        """
        _model.check_for_updates()
        _model.save_last_check_date_as_now()
        if _model.is_update_needed():
            build_package_updater_gui(model=_model)

    def _maya_retrieve_update_data():
        """ Internal function used to check for updates using threads in Maya """
        from gt.utils.system import execute_deferred
        execute_deferred(_initialize_tool_if_updating)
    try:
        thread = threading.Thread(None, target=_maya_retrieve_update_data)
        thread.start()
    except Exception as e:
        logger.debug(f'Unable to silently check for updates. Issue: {e}')


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using this tool.
    """
    build_package_updater_gui()


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    launch_tool()
