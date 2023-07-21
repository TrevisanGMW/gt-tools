"""
Package Setup Model - Logic
Install, uninstall, Run-only calls
"""
from gt.ui import progress_bar, resource_library
from PySide2.QtWidgets import QApplication
from gt.utils import version_utils
from gt.utils import system_utils
from gt.utils import setup_utils
from PySide2 import QtCore
import logging
import sys
import os

logger = logging.getLogger(__name__)


class PackageSetupModel(QtCore.QObject):
    INSTALL_STATUS_FAIL = "Failed"
    INSTALL_STATUS_INSTALLED = "Installed"
    INSTALL_STATUS_MISSING = "Not installed"  # Updated? Not Updated?
    CloseView = QtCore.Signal()
    UpdatePath = QtCore.Signal(object)
    UpdateStatus = QtCore.Signal(object)
    UpdateVersion = QtCore.Signal(object, object)

    def __init__(self, *args, **kwargs):
        """
        Initializes package setup model object
        Args:
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

        result = None
        try:
            result = setup_utils.install_package(callbacks=[self.progress_win.add_text_to_output_box,
                                                            self.progress_win.increase_progress_bar_value])
        except Exception as e:
            self.progress_win.add_text_to_output_box(input_string=str(e), color=resource_library.Color.Hex.red_soft)

        # Installation Result
        if result:
            self.update_status(self.INSTALL_STATUS_INSTALLED)
            self.progress_win.set_progress_bar_done()
            self.progress_win.first_button.clicked.connect(self.close_view)  # Closes parent (Package Setup View)
            self.progress_win.change_last_line_color(resource_library.Color.Hex.green_soft)
        else:
            self.progress_win.change_last_line_color(resource_library.Color.Hex.red_soft)

        # Show window
        if QApplication.instance():
            try:
                sys.exit(app.exec_())
            except Exception as e:
                logger.debug(e)
        return self.progress_win

    def uninstall_package(self):
        if not QApplication.instance():
            app = QApplication(sys.argv)

        self.progress_win = progress_bar.ProgressBarWindow()
        self.progress_win.show()
        self.progress_win.set_progress_bar_name("Uninstalling Script Package...")
        # Create connections
        self.progress_win.first_button.clicked.connect(self.progress_win.close_window)
        self.progress_win.set_progress_bar_max_value(7)  # Number of print functions inside installer
        self.progress_win.increase_progress_bar_value()

        result = None
        try:
            result = setup_utils.uninstall_package(callbacks=[self.progress_win.add_text_to_output_box,
                                                              self.progress_win.increase_progress_bar_value])
        except Exception as e:
            self.progress_win.add_text_to_output_box(input_string=str(e), color=resource_library.Color.Hex.red_soft)

        # Uninstallation Result
        if result:
            self.update_status(self.INSTALL_STATUS_MISSING)
            self.progress_win.set_progress_bar_done()
            self.progress_win.change_last_line_color(resource_library.Color.Hex.green_soft)
        else:
            self.progress_win.change_last_line_color(resource_library.Color.Hex.red_soft)

        # Show window
        if QApplication.instance():
            try:
                sys.exit(app.exec_())
            except Exception as e:
                logger.debug(e)
        return self.progress_win

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
        setup_version = version_utils.get_package_version()
        installed_version = version_utils.get_package_version(package_path=self.get_install_target_dir())
        self.UpdateVersion.emit(setup_version, installed_version)  # 1: Current Package Version, 2: Installed Version

    def close_view(self):
        self.CloseView.emit()


if __name__ == "__main__":
    model = PackageSetupModel()
    model.install_package()
