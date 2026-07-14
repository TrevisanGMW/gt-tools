"""Utilities for checking and installing optional Python dependencies.

Dependencies are installed into the interpreter running this module. Inside Maya,
this means the active mayapy environment. No installation is attempted until
``ensure_dependencies`` is called.
"""

import importlib
import logging
import sys


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# When the stored preference does not exist, missing dependencies install after
# showing the progress window. Set this to False to require user confirmation.
DEFAULT_AUTO_INSTALL = True


def normalize_dependencies(dependencies):
    """Normalizes dependency declarations into import and package names.

    Args:
        dependencies (str, list, tuple, set, or dict): Import names, or a mapping
            of import names to pip package names. For example,
            ``{"PIL": "Pillow", "numpy": "numpy"}``.

    Returns:
        dict: Mapping of import names to pip package names.

    Raises:
        TypeError: If dependencies uses an unsupported type.
        ValueError: If an import or package name is empty.
    """
    if isinstance(dependencies, str):
        dependencies = [dependencies]
    if isinstance(dependencies, (list, tuple, set)):
        dependencies = {dependency: dependency for dependency in dependencies}
    if not isinstance(dependencies, dict):
        raise TypeError("Dependencies must be a string, sequence, or dictionary.")

    normalized = {}
    for import_name, package_name in dependencies.items():
        import_name = str(import_name).strip()
        package_name = str(package_name).strip()
        if not import_name or not package_name:
            raise ValueError("Dependency import and package names cannot be empty.")
        normalized[import_name] = package_name
    return normalized


def get_missing_dependencies(dependencies):
    """Gets dependencies that cannot be imported by the current interpreter.

    Args:
        dependencies (str, list, tuple, set, or dict): Dependency declarations.

    Returns:
        dict: Missing import names mapped to their pip package names.
    """
    normalized = normalize_dependencies(dependencies)
    missing = {}
    for import_name, package_name in normalized.items():
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing[import_name] = package_name
    return missing


def is_auto_install_enabled():
    """Gets the automatic dependency installation preference.

    Returns:
        bool: True when missing packages should install without confirmation.
    """
    try:
        from gt.core.prefs import PackagePrefs

        return PackagePrefs().is_dependency_auto_install_enabled(default=DEFAULT_AUTO_INSTALL)
    except Exception as exception:
        logger.debug("Unable to read dependency preference: %s", exception)
        return DEFAULT_AUTO_INSTALL


def build_pip_command(package_name):
    """Builds the pip command for the active Python interpreter.

    Args:
        package_name (str): Distribution name or pip requirement specifier.

    Returns:
        list: Command arguments suitable for subprocess or QProcess.
    """
    return [sys.executable, "-m", "pip", "install", str(package_name)]


def _show_dependency_installer(missing_dependencies, auto_start, parent=None):
    """Shows a modal dependency installer and waits for its result.

    Args:
        missing_dependencies (dict): Missing imports mapped to pip packages.
        auto_start (bool): Whether installation starts without confirmation.
        parent (QWidget, optional): Parent for the installer dialog.

    Returns:
        bool: True when every requested import is available after installation.
    """
    import gt.ui.qt_import as ui_qt
    import gt.ui.qt_utils as ui_qt_utils
    import gt.ui.resource_library as ui_res_lib

    application = ui_qt.QtWidgets.QApplication.instance()
    if not application:
        application = ui_qt.QtWidgets.QApplication(sys.argv)

    class DependencyInstallerDialog(ui_qt.QtWidgets.QDialog):
        """Modal window that installs pip packages and streams their output."""

        def __init__(self, dependency_map, start_automatically, dialog_parent=None):
            """Initializes the dependency installer dialog.

            Args:
                dependency_map (dict): Missing imports mapped to pip packages.
                start_automatically (bool): Whether to immediately begin.
                dialog_parent (QWidget, optional): Parent widget.
            """
            super().__init__(dialog_parent)
            self.dependency_map = dependency_map
            self.package_queue = list(dict.fromkeys(dependency_map.values()))
            self.package_index = 0
            self.install_succeeded = False
            self.process = None
            self.setWindowTitle("GT Tools Dependency Installer")
            self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_progress))
            self.setMinimumSize(680, 440)
            self.setModal(True)

            title = ui_qt.QtWidgets.QLabel("Additional Python Packages Required")
            title.setStyleSheet("font-size: 16px; font-weight: bold;")
            package_text = ", ".join(self.package_queue)
            self.description = ui_qt.QtWidgets.QLabel(
                "GT Tools needs the following packages in this Maya Python environment:\n" + package_text
            )
            self.description.setWordWrap(True)
            self.status_label = ui_qt.QtWidgets.QLabel("Ready to install.")
            self.progress_bar = ui_qt.QtWidgets.QProgressBar()
            self.progress_bar.setRange(0, len(self.package_queue))
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("%v of %m packages complete")
            self.output_box = ui_qt.QtWidgets.QPlainTextEdit()
            self.output_box.setReadOnly(True)
            if ui_qt.IS_PYSIDE6:
                no_wrap = ui_qt.QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap
            else:
                no_wrap = ui_qt.QtWidgets.QPlainTextEdit.NoWrap
            self.output_box.setLineWrapMode(no_wrap)
            self.install_button = ui_qt.QtWidgets.QPushButton("Install")
            self.close_button = ui_qt.QtWidgets.QPushButton("Quit")

            button_layout = ui_qt.QtWidgets.QHBoxLayout()
            button_layout.addStretch()
            button_layout.addWidget(self.install_button)
            button_layout.addWidget(self.close_button)
            layout = ui_qt.QtWidgets.QVBoxLayout(self)
            layout.addWidget(title)
            layout.addWidget(self.description)
            layout.addWidget(self.status_label)
            layout.addWidget(self.progress_bar)
            layout.addWidget(self.output_box, 1)
            layout.addLayout(button_layout)

            stylesheet = ui_res_lib.Stylesheet.maya_dialog_base
            stylesheet += ui_res_lib.Stylesheet.progress_bar_base
            stylesheet += ui_res_lib.Stylesheet.scroll_bar_base
            self.setStyleSheet(stylesheet)
            ui_qt_utils.center_window(self)

            self.install_button.clicked.connect(self.start_installation)
            self.close_button.clicked.connect(self.reject)
            if start_automatically:
                ui_qt.QtCore.QTimer.singleShot(0, self.start_installation)

        def append_output(self, text):
            """Appends process output and keeps the newest line visible.

            Args:
                text (str): Output text to append.
            """
            if not text:
                return
            self.output_box.moveCursor(ui_qt.QtLib.TextCursor.End)
            self.output_box.insertPlainText(text)
            self.output_box.moveCursor(ui_qt.QtLib.TextCursor.End)

        def start_installation(self):
            """Starts installing the queued packages."""
            self.install_button.setEnabled(False)
            self.close_button.setEnabled(False)
            self.package_index = 0
            self.progress_bar.setValue(0)
            self.output_box.clear()
            self._install_next_package()

        def _install_next_package(self):
            """Starts the next pip process or completes the installation."""
            if self.package_index >= len(self.package_queue):
                importlib.invalidate_caches()
                missing_after_install = get_missing_dependencies(self.dependency_map)
                self.install_succeeded = not missing_after_install
                if self.install_succeeded:
                    self.status_label.setText("Installation complete. Continuing...")
                    self.progress_bar.setValue(len(self.package_queue))
                    ui_qt.QtCore.QTimer.singleShot(350, self.accept)
                else:
                    names = ", ".join(missing_after_install)
                    self._show_failure("Packages installed, but imports still failed: " + names)
                return

            package_name = self.package_queue[self.package_index]
            self.status_label.setText(
                "Installing {} ({}/{})...".format(
                    package_name, self.package_index + 1, len(self.package_queue)
                )
            )
            command = build_pip_command(package_name)
            self.append_output("\n> {}\n".format(" ".join(command)))
            self.process = ui_qt.QtCore.QProcess(self)
            self.process.setProcessChannelMode(ui_qt.QtCore.QProcess.MergedChannels)
            self.process.readyReadStandardOutput.connect(self._read_process_output)
            self.process.finished.connect(self._process_finished)
            self.process.errorOccurred.connect(self._process_error)
            self.process.start(command[0], command[1:])

        def _read_process_output(self):
            """Reads and displays newly available pip output."""
            raw_output = self.process.readAllStandardOutput()
            self.append_output(bytes(raw_output).decode("utf-8", errors="replace"))

        def _process_finished(self, exit_code, exit_status):
            """Handles completion of the active pip process.

            Args:
                exit_code (int): Process exit code.
                exit_status (QProcess.ExitStatus): Qt process exit status.
            """
            self._read_process_output()
            if ui_qt.IS_PYSIDE6:
                expected_exit = ui_qt.QtCore.QProcess.ExitStatus.NormalExit
            else:
                expected_exit = ui_qt.QtCore.QProcess.NormalExit
            normal_exit = exit_status == expected_exit
            if exit_code != 0 or not normal_exit:
                package_name = self.package_queue[self.package_index]
                self._show_failure("Installation failed for {}.".format(package_name))
                return
            self.package_index += 1
            self.progress_bar.setValue(self.package_index)
            self._install_next_package()

        def _process_error(self, process_error):
            """Handles a pip process error such as failure to start.

            Args:
                process_error (QProcess.ProcessError): Reported process error.
            """
            if ui_qt.IS_PYSIDE6:
                failed_to_start = ui_qt.QtCore.QProcess.ProcessError.FailedToStart
            else:
                failed_to_start = ui_qt.QtCore.QProcess.FailedToStart
            if process_error == failed_to_start:
                self._show_failure("Unable to start pip with the current interpreter.")

        def _show_failure(self, message):
            """Updates controls after an installation failure.

            Args:
                message (str): Failure summary shown above the log.
            """
            self.install_succeeded = False
            self.status_label.setText(message + " Review the log below.")
            self.install_button.setText("Retry")
            self.install_button.setEnabled(True)
            self.close_button.setText("Close")
            self.close_button.setEnabled(True)

        def reject(self):
            """Closes the dialog after stopping an active installer process."""
            if ui_qt.IS_PYSIDE6:
                not_running = ui_qt.QtCore.QProcess.ProcessState.NotRunning
            else:
                not_running = ui_qt.QtCore.QProcess.NotRunning
            if self.process and self.process.state() != not_running:
                self.process.kill()
                self.process.waitForFinished(1000)
            super().reject()

    dialog = DependencyInstallerDialog(missing_dependencies, auto_start, parent)
    dialog.exec()
    return dialog.install_succeeded


def ensure_dependencies(dependencies, auto_install=None, parent=None):
    """Ensures imports are available, offering to install missing packages.

    This function blocks until the user quits or installation finishes, which
    allows a tool entry point to continue only after its dependencies are ready.

    Args:
        dependencies (str, list, tuple, set, or dict): Import names, or import
            names mapped to pip package names.
        auto_install (bool, optional): Overrides the stored automatic-install
            preference. When None, the package preference is used.
        parent (QWidget, optional): Parent for the installer dialog.

    Returns:
        bool: True when all dependencies are importable, otherwise False.
    """
    missing_dependencies = get_missing_dependencies(dependencies)
    if not missing_dependencies:
        return True
    if auto_install is None:
        auto_install = is_auto_install_enabled()
    try:
        return _show_dependency_installer(missing_dependencies, bool(auto_install), parent)
    except ImportError as exception:
        logger.error("Qt is unavailable, so dependencies cannot be installed interactively: %s", exception)
        return False


if __name__ == "__main__":
    # Manual test using common optional scientific packages. The prompt appears
    # only when one of them is missing from the active interpreter.
    TEST_DEPENDENCIES = {"numpy": "numpy", "scipy": "scipy"}
    ensure_dependencies(TEST_DEPENDENCIES, auto_install=False)
