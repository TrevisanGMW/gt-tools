"""
QT Controller for setup
"""
from PySide2 import QtCore
from utils import setup_utils
from utils import system_utils
import logging
import os

logger = logging.getLogger(__name__)


class PackageSetupController(QtCore.QObject):
    INSTALL_STATUS_FAIL = "Failed"
    INSTALL_STATUS_SUCCESS = "Success"
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

    def install_package(self):
        result = None
        try:
            result = setup_utils.install_package()
        except Exception as e:
            logger.debug(str(e))
        # Update Status
        if result:
            self.update_status(self.INSTALL_STATUS_SUCCESS)
        else:
            self.update_status(self.INSTALL_STATUS_FAIL)

    @staticmethod
    def uninstall_package():
        setup_utils.uninstall_package()

    @staticmethod
    def run_only_package():
        system_utils.process_launch_options(["", "-launch"])

    @staticmethod
    def get_install_target_dir():
        maya_settings_dir = system_utils.get_maya_settings_dir(system_utils.get_system())
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


if __name__ == "__main__":
    PackageSetupController.install_package()
