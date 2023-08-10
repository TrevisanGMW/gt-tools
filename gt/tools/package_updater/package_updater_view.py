"""
Curve Library Window - The main GUI window class for the Curve Library tool.
"""
from PySide2.QtWidgets import QPushButton, QDialog, QLineEdit, QLabel
import gt.ui.resource_library as resource_library
from PySide2 import QtWidgets, QtCore
import gt.ui.qt_utils as qt_utils
from PySide2.QtGui import QIcon
import sys


class PackageUpdaterView(QDialog):
    def __init__(self, parent=None, controller=None, version=None):
        """
        Initialize the PackageUpdater.
        This window represents the main GUI window of the tool.

        Args:
            parent (str): Parent for this window
            controller (PackageUpdaterController): PackageUpdaterController, not to be used, here so it's not deleted
                                                   by the garbage collector.  Defaults to None.
            version (str, optional): If provided, it will be used to determine the window title. e.g. Title - (v1.2.3)
        """
        super().__init__(parent=parent)
        self.controller = controller  # Only here so it doesn't get deleted by the garbage collectors
        # Labels
        self.title_label = None
        self.status_label = None
        self.status_label = None
        self.web_response_label = None
        self.installed_version_label = None
        self.latest_release_label = None
        self.changelog_label = None
        # Content
        self.status_content = None
        self.web_response_content = None
        self.installed_version_content = None
        self.latest_release_content = None
        # Buttons
        self.update_button = None
        self.refresh_button = None
        self.interval_button = None
        self.auto_check_button = None
        # Misc
        self.changelog_box = None

        window_title = "Package Updater"
        if version:
            window_title += f' - (v{str(version)})'
        self.setWindowTitle(window_title)

        self.create_widgets()
        self.create_layout()

        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.WindowMaximizeButtonHint |
                            QtCore.Qt.WindowMinimizeButtonHint)
        self.setWindowIcon(QIcon(resource_library.Icon.tool_package_updater))

        stylesheet = resource_library.Stylesheet.dark_scroll_bar
        stylesheet += resource_library.Stylesheet.maya_basic_dialog
        stylesheet += resource_library.Stylesheet.dark_list_widget
        self.setStyleSheet(stylesheet)
        self.update_button.setStyleSheet(resource_library.Stylesheet.bright_push_button)
        qt_utils.resize_to_screen(self, percentage=35, width_percentage=30)
        qt_utils.center_window(self)
        # self.setWindowFlag(QtCore.Qt.Tool, True)  # Stay On Top Modality - Fixes Mac order issue

    def create_widgets(self):
        """Create the widgets for the window."""
        self.title_label = QtWidgets.QLabel("GT-Tools - Package Updater")
        self.title_label.setStyleSheet('background-color: rgb(93, 93, 93); border: 0px solid rgb(93, 93, 93); \
                                        color: rgb(255, 255, 255); padding: 5px; margin-bottom: 10px')
        self.status_label = QLabel("Status:")
        self.status_content = QLabel("<status>")

        self.web_response_label = QLabel("Web Response:")
        self.web_response_content = QLabel("<web-response>")

        self.installed_version_label = QLabel("Installed Version:")
        self.installed_version_content = QLabel("<installed-version>")

        self.latest_release_label = QLabel("Latest Release:")
        self.latest_release_content = QLabel("<latest-version>")

        self.changelog_label = QLabel("Latest Release Changelog:")
        self.changelog_label.setStyleSheet(f"font-weight: bold; font-size: 8pt; margin-top: 15; "
                                           f"color: {resource_library.Color.RGB.grey_lighter};")

        self.changelog_box = QLineEdit()
        self.changelog_box.setMinimumHeight(150)

        # Set Alignment Center
        for label in [self.title_label,
                      self.status_label,
                      self.status_content,
                      self.web_response_label,
                      self.web_response_content,
                      self.installed_version_label,
                      self.installed_version_content,
                      self.latest_release_label,
                      self.latest_release_content,
                      self.changelog_label,
                      ]:
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setFixedHeight(label.sizeHint().height())
            label.setFont(qt_utils.get_font(resource_library.Font.roboto))

        self.changelog_box.setSizePolicy(self.changelog_box.sizePolicy().Expanding,
                                         self.changelog_box.sizePolicy().Expanding)

        self.interval_button = QPushButton("Auto Check: Activated")
        self.interval_button.setStyleSheet("padding: 10;")
        self.interval_button.setToolTip("Change Check for Updates State (Activated/Deactivated)")
        self.auto_check_button = QPushButton("Interval: 15 Days")
        self.auto_check_button.setStyleSheet("padding: 10;")
        self.auto_check_button.setToolTip("Change Check for Updates Interval (5, 10, 15 days)")
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setStyleSheet("padding: 10; margin-bottom: 2;")
        self.refresh_button.setToolTip("Check Github Again for New Updates")
        self.update_button = QPushButton("Update")
        self.update_button.setToolTip("Download and Install Latest Update")

    def create_layout(self):
        """Create the layout for the window."""
        top_layout = QtWidgets.QHBoxLayout()
        top_left_widget = QtWidgets.QVBoxLayout()
        top_right_widget = QtWidgets.QVBoxLayout()
        top_layout.addLayout(top_left_widget)
        top_layout.addLayout(top_right_widget)

        top_left_widget.addWidget(self.status_label)
        top_left_widget.addWidget(self.web_response_label)
        top_left_widget.addWidget(self.installed_version_label)
        top_left_widget.addWidget(self.latest_release_label)

        top_right_widget.addWidget(self.status_content)
        top_right_widget.addWidget(self.web_response_content)
        top_right_widget.addWidget(self.installed_version_content)
        top_right_widget.addWidget(self.latest_release_content)

        bottom_layout = QtWidgets.QVBoxLayout()
        bottom_layout.addWidget(self.changelog_label)
        bottom_layout.addWidget(self.changelog_box)

        settings_buttons_layout = QtWidgets.QHBoxLayout()
        settings_buttons_layout.addWidget(self.interval_button)
        settings_buttons_layout.addWidget(self.auto_check_button)
        settings_buttons_layout.setContentsMargins(0, 5, 0, 2)  # @@@
        bottom_layout.addLayout(settings_buttons_layout)
        bottom_layout.addWidget(self.refresh_button)
        bottom_layout.addWidget(self.update_button)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.title_label)
        main_layout.setContentsMargins(15, 15, 15, 15)  # Make Margins Uniform LTRB
        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)

    def change_update_button_state(self, state):
        """
        Change the state of the "Update" button
        Args:
                state (bool): New state of the button: Disable/Enable the button True = Active, False = Inactive.
        """
        if isinstance(state, bool):
            self.update_button.setEnabled(state)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)  # Application - To launch without Maya
    window = PackageUpdaterView(version="1.2.3")  # View
    window.show()  # Open Windows
    # window.change_update_button_state(state=False)
    sys.exit(app.exec_())
