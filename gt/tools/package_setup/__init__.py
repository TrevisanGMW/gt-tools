"""
 Package Setup - Entry point tool used to install, uninstall or run tools directly from location.
 github.com/TrevisanGMW/gt-tools - 2023-06-01
"""
from gt.tools.package_setup import setup_controller
from gt.tools.package_setup import setup_view
from PySide2.QtWidgets import QApplication
from gt.utils import session_utils
from gt.utils import setup_utils
import logging
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
        from gt.ui.qt_utils import get_maya_main_window
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
    _controller.CloseView.connect(_view.close_window)

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
        build_installer_gui(standalone=True)
    else:
        build_installer_gui(standalone=False)


def open_about_window():
    """ Opens about window for the package """
    import about_window
    about_window.build_gui_about_gt_tools()


if __name__ == "__main__":
    launcher_entry_point()
