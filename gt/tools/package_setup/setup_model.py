"""
Package Setup Model
Install, uninstall, Run-only calls
"""

import gt.ui.progress_bar as ui_progress_bar
import gt.ui.resource_library as ui_res_lib
import gt.core.version as core_version
import gt.core.setup as core_setup
import gt.core.feedback as core_feedback
import gt.utils.system as utils_system
import gt.ui.qt_import as ui_qt
import logging
import sys
import os

logger = logging.getLogger(__name__)


class PackageSetupModel(ui_qt.QtCore.QObject):
    CloseView = ui_qt.QtCore.Signal()
    UpdatePath = ui_qt.QtCore.Signal(object)
    UpdateStatus = ui_qt.QtCore.Signal(object)
    UpdateVersionSetup = ui_qt.QtCore.Signal(object)  # 1: Current Package Version
    UpdateVersionInstalled = ui_qt.QtCore.Signal(object)  # 2: Installed Version

    def __init__(self, *args, **kwargs):
        """
        Initializes package setup model object
        Args:
            args (any): Variable length argument list.
            kwargs (any): Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.progress_win = None
        self.package_name_color = ui_res_lib.Color.Hex.turquoise_dark

    def install_package(self):
        """Installs package"""
        if not ui_qt.QtWidgets.QApplication.instance():
            app = ui_qt.QtWidgets.QApplication(sys.argv)

        self.progress_win = ui_progress_bar.ProgressBarWindow()
        self.progress_win.show()
        self.progress_win.set_progress_bar_name("Installing Script Package...")
        # Create connections
        self.progress_win.first_button.clicked.connect(self.progress_win.close_window)
        self.progress_win.set_progress_bar_max_value(7)  # Number of print functions inside installer
        self.progress_win.increase_progress_bar_value()

        result = None
        try:
            result = core_setup.install_package(
                callbacks=[self.progress_win.add_text_to_output_box, self.progress_win.increase_progress_bar_value]
            )
        except Exception as e:
            self.progress_win.add_text_to_output_box(input_string=str(e), color=ui_res_lib.Color.Hex.red_melon)

        # Installation Result
        if result:
            self.update_version()
            self.update_status()
            self.progress_win.set_progress_bar_done()
            self.progress_win.first_button.clicked.connect(self.close_view)  # Closes parent (Package Setup View)
            self.progress_win.change_last_line_color(ui_res_lib.Color.Hex.green_oxley)
            feedback = core_feedback.FeedbackMessage(
                intro="GT-Tools",
                style_intro=f"color:{self.package_name_color};" f"text-decoration:underline;",
                conclusion="has been installed and is now active.",
            )
            feedback.print_inview_message(stay_time=4000)
        else:
            self.progress_win.change_last_line_color(ui_res_lib.Color.Hex.red_melon)

        # Show window
        if ui_qt.QtWidgets.QApplication.instance():
            try:
                sys.exit(app.exec_())
            except Exception as e:
                logger.debug(e)
        return self.progress_win

    def uninstall_package(self):
        """Uninstalls package"""
        if not ui_qt.QtWidgets.QApplication.instance():
            app = ui_qt.QtWidgets.QApplication(sys.argv)

        self.progress_win = ui_progress_bar.ProgressBarWindow()
        self.progress_win.show()
        self.progress_win.set_progress_bar_name("Uninstalling Script Package...")
        # Create connections
        self.progress_win.first_button.clicked.connect(self.progress_win.close_window)
        self.progress_win.set_progress_bar_max_value(7)  # Number of print functions inside installer
        self.progress_win.increase_progress_bar_value()

        result = None
        try:
            result = core_setup.uninstall_package(
                callbacks=[self.progress_win.add_text_to_output_box, self.progress_win.increase_progress_bar_value]
            )
        except Exception as e:
            self.progress_win.add_text_to_output_box(input_string=str(e), color=ui_res_lib.Color.Hex.red_melon)

        # Uninstallation Result
        if result:
            self.update_version()
            self.update_status()
            self.progress_win.set_progress_bar_done()
            self.progress_win.change_last_line_color(ui_res_lib.Color.Hex.green_oxley)
            feedback = core_feedback.FeedbackMessage(
                intro="GT-Tools",
                style_intro=f"color:{self.package_name_color};" f"text-decoration:underline;",
                conclusion="has been uninstalled and unloaded.",
            )
            feedback.print_inview_message(stay_time=4000)
        else:
            self.progress_win.change_last_line_color(ui_res_lib.Color.Hex.red_melon)

        # Show window
        if ui_qt.QtWidgets.QApplication.instance():
            try:
                sys.exit(app.exec_())
            except Exception as e:
                logger.debug(e)
        return self.progress_win

    def run_only_package(self):
        """
        Injects the necessary code to import the package from location and create its maya menu. (Do not copy any files)
        """
        utils_system.process_launch_args(["", "-launch"])
        feedback = core_feedback.FeedbackMessage(
            intro="GT-Tools",
            style_intro=f"color:{self.package_name_color};" f"text-decoration:underline;",
            conclusion="menu was initialized in run-only (one time use) mode.",
        )
        feedback.print_inview_message(stay_time=4000)

    @staticmethod
    def get_install_target_dir():
        """
        Gets the installation directory
        Returns:
            str: Path to the installation folder. e.g. ".../Documents/maya/gt-tools"
        """
        maya_settings_dir = utils_system.get_maya_preferences_dir(utils_system.get_system())
        return os.path.normpath(os.path.join(maya_settings_dir, core_setup.PACKAGE_NAME))

    def update_path(self):
        """
        Sends a signal so the view updates the target path for the package installation
        """
        try:
            package_target_folder = self.get_install_target_dir()
            self.UpdatePath.emit(package_target_folder)
        except Exception as e:
            logger.debug(str(e))
            self.UpdatePath.emit(f"Unable to get path. Issue: {str(e)}")

    def update_status(self):
        """Updates the status label to reflect current state"""
        setup_version = core_version.get_package_version()
        installed_module = os.path.join(self.get_install_target_dir(), core_setup.PACKAGE_MAIN_MODULE)
        installed_version = core_version.get_package_version(package_path=installed_module)
        if not installed_version:
            self.set_status("Not Installed")
            return
        status = core_version.compare_versions(installed_version, setup_version)

        if status == core_version.VERSION_EQUAL:
            self.set_status("Installed")
        elif status == core_version.VERSION_SMALLER:
            self.set_status("Needs Update")

    def set_status(self, new_status=None):
        """
        Sends a signal to the view, so it updates the status with a new string
        Args:
            new_status (str): String to be used as the new status
        """
        if new_status:
            self.UpdateStatus.emit(new_status)
        else:
            self.UpdateStatus.emit("Unknown")

    def update_version(self):
        """Sends signals to update view with the setup and installed versions"""
        setup_version = core_version.get_package_version()
        installed_module = os.path.join(self.get_install_target_dir(), core_setup.PACKAGE_MAIN_MODULE)
        installed_version = core_version.get_package_version(package_path=installed_module)
        # Attempt to find older version
        try:
            if not installed_version:
                installed_version = "0.0.0"
                if core_version.get_legacy_package_version() and core_setup.is_legacy_version_install_present():
                    installed_version = str(core_version.get_legacy_package_version())
        except Exception as e:
            logger.debug(f"Unable to retrieve legacy version. Issue: {str(e)}")
        self.UpdateVersionSetup.emit(setup_version)
        self.UpdateVersionInstalled.emit(installed_version)

    def close_view(self):
        """Sends a signal to close view"""
        self.CloseView.emit()


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    model = PackageSetupModel()
    # model.install_package()
    model.update_version()
