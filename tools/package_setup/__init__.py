from PySide2.QtWidgets import QWidget, QApplication
import logging
import sys
import os

# Paths to Append
source_dir = os.path.dirname(__file__)
tools_root_dir = os.path.dirname(source_dir)
for to_append in [source_dir, tools_root_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)

from utils import session_utils
from utils import setup_utils
import setup_controller
import setup_view

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_maya_main_window():
    """
    Finds the instance of maya's main window
    Returns:
        QWidget: The main maya widget
    """
    from shiboken2 import wrapInstance
    from maya import OpenMayaUI as OpenMayaUI
    ptr = OpenMayaUI.MQtUtil.mainWindow()
    maya_window = wrapInstance(int(ptr), QWidget)
    return maya_window


def build_installer_gui(standalone=True):
    """
    Creates installer GUI
    Parameters:
        standalone (bool, optional): If true, it will run the tool without the Maya window dependency.
                                     If false, it will attempt to retrieve the name of the main maya window as parent.
    """
    # Determine Parent
    if standalone:
        app = QApplication(sys.argv)
        _view = setup_view.PackageSetupWindow()
    else:
        maya_window = get_maya_main_window()
        _view = setup_view.PackageSetupWindow(parent=maya_window)

    # Create connections
    _controller = setup_controller.PackageSetupController()
    _view.controller = _controller  # To avoid garbage collection

    # Buttons
    _view.ButtonInstallClicked.connect(_controller.install_package)
    _view.ButtonUninstallClicked.connect(_controller.uninstall_package)
    _view.ButtonRunOnlyClicked.connect(_controller.run_only_package)

    # Feedback
    _controller.UpdatePath.connect(_view.update_installation_path_text_field)
    _controller.UpdateVersion.connect(_view.update_version_texts)
    _controller.UpdateStatus.connect(_view.update_status_text)

    # Initial Update
    _controller.update_path()
    _controller.update_version()
    _controller.update_status()

    # Show window
    if standalone:
        _view.show()
        sys.exit(app.exec_())
    else:
        _view.show()
    return _view


def launcher_entry_point():
    """ Determines if it should open the installer GUI as a child of Maya or by itself """
    setup_utils.reload_package_loaded_modules()
    if session_utils.is_script_in_py_maya():
        # Unload scripts
        # Save changes
        build_installer_gui(standalone=True)
    else:
        build_installer_gui(standalone=False)


def open_about_window():
    """ Opens about window for the package """
    import about_window
    about_window.build_gui_about_gt_tools()


if __name__ == "__main__":
    # build_installer_gui()
    launcher_entry_point()
