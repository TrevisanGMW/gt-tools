"""
QT Controller for setup
"""
import sys

from PySide2.QtWidgets import QApplication
from PySide2 import QtCore
from utils import setup_utils
from utils import system_utils
from ui import progress_bar
import logging
import os

logger = logging.getLogger(__name__)


class PackageSetupController(QtCore.QObject):
    INSTALL_STATUS_FAIL = "Failed"
    INSTALL_STATUS_SUCCESS = "Success"
    CloseView = QtCore.Signal()
    UpdatePath = QtCore.Signal(object)
    UpdateStatus = QtCore.Signal(object)
    UpdateVersion = QtCore.Signal(object, object)

    def __init__(self, *args, **kwargs):
        """
        Initializes package setup controller object
        Parameters:
            args (any): Variable length argument list.
            kwargs (any): Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.progress_win = None

    def install_package(self):
        if not QApplication.instance():
            app = QApplication(sys.argv)

        self.progress_win = progress_bar.ProgressBarWindow()
        self.progress_win.show()
        self.progress_win.set_progress_bar_name("Installing Script Package...")
        # Create connections
        self.progress_win.first_button.clicked.connect(self.progress_win.close_window)
        self.progress_win.set_progress_bar_max_value(7)  # Number of print functions inside installer
        self.progress_win.increase_progress_bar_value()
        result = setup_utils.install_package(passthrough_functions=[self.progress_win.append_text_to_output_box,
                                                                    self.progress_win.increase_progress_bar_value])

        # Update Status
        if result:
            self.update_status(self.INSTALL_STATUS_SUCCESS)
            self.progress_win.set_progress_bar_done()
            self.progress_win.first_button.clicked.connect(self.close_view)
        else:
            self.update_status(self.INSTALL_STATUS_FAIL)

        # Show window
        if QApplication.instance():
            try:
                sys.exit(app.exec_())
            except Exception as e:
                logger.debug(e)
        return self.progress_win

    @staticmethod
    def uninstall_package():
        setup_utils.uninstall_package()

    @staticmethod
    def run_only_package():
        system_utils.process_launch_options(["", "-launch"])

    @staticmethod
    def get_install_target_dir():
        maya_settings_dir = system_utils.get_maya_preferences_dir(system_utils.get_system())
        return os.path.normpath(os.path.join(maya_settings_dir, setup_utils.PACKAGE_NAME))

    def update_path(self):
        try:
            package_target_folder = self.get_install_target_dir()
            self.UpdatePath.emit(package_target_folder)
        except Exception as e:
            logger.debug(str(e))
            self.UpdatePath.emit(f"Unable to get path. Issue: {str(e)}")

    def update_status(self, new_status=None):
        if new_status:
            self.UpdateStatus.emit(new_status)
        else:
            self.UpdateStatus.emit("Updated!")

    def update_version(self):
        setup_version = system_utils.get_package_version()
        installed_version = system_utils.get_package_version(package_path=self.get_install_target_dir())
        self.UpdateVersion.emit(setup_version, installed_version)  # 1: Current Package Version, 2: Installed Version

    def close_view(self):
        self.CloseView.emit()


if __name__ == "__main__":
    controller = PackageSetupController()
    controller.install_package()
