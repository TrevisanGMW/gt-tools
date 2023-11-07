"""
Auto Rigger View
"""
from PySide2.QtWidgets import QAction, QMenuBar, QTreeWidget, QTreeWidgetItem, QVBoxLayout
from PySide2.QtWidgets import QWidget, QSplitter, QDesktopWidget, QHBoxLayout
import gt.ui.resource_library as resource_library
from gt.ui.qt_utils import MayaWindowMeta
import gt.ui.qt_utils as qt_utils
from PySide2.QtGui import QIcon
from PySide2 import QtCore


class RiggerView(metaclass=MayaWindowMeta):
    def __init__(self, parent=None, controller=None, version=None):
        """
        Initialize the RiggerView (Auto Rigger View)
        This window represents the main GUI window of the tool.

        Args:
            parent (str): Parent for this window
            controller (ResourceLibraryController): RiggerController, not to be used.
                                                    Here to avoid the garbage collector.  Defaults to None.
            version (str, optional): If provided, it will be used to determine the window title. e.g. Title - (v1.2.3)
        """
        # super(ResourceLibraryView, self).__init__(parent=parent)
        super().__init__(parent=parent)
        self.controller = controller  # Only here so it doesn't get deleted by the garbage collectors
        self.menubar = None
        self.module_tree = None
        self.splitter = None

        window_title = "GT Auto Rigger"
        if version:
            window_title += f' - (v{str(version)})'
        self.setWindowTitle(window_title)
        self.setGeometry(100, 100, 400, 300)
        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.WindowMaximizeButtonHint |
                            QtCore.Qt.WindowMinimizeButtonHint)
        self.setWindowIcon(QIcon(resource_library.Icon.dev_brain))  # TODO TEMP @@@

        # Create Widgets and Layout
        self.create_widgets()
        self.create_layout()

        # Style Window
        stylesheet = resource_library.Stylesheet.scroll_bar_dark
        stylesheet += resource_library.Stylesheet.maya_basic_dialog
        stylesheet += resource_library.Stylesheet.list_widget_dark
        stylesheet += resource_library.Stylesheet.combobox_dark
        self.setStyleSheet(stylesheet)

        # Final Adjustments
        qt_utils.resize_to_screen(self, percentage=35)
        qt_utils.center_window(self)
        qt_utils.expand_all_tree_items_recursively(self.module_tree)
        self.resize_splitter_to_screen()

    def create_widgets(self):
        """Create the widgets for the window."""
        # Create a menu bar
        self.menubar = QMenuBar(self)
        file_menu = self.menubar.addMenu("File")

        # Add an "Exit" action to the menu
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Create a QTreeWidget and add items to it
        self.module_tree = QTreeWidget()

        item1 = QTreeWidgetItem(["Item 1"])
        item2 = QTreeWidgetItem(["Item 2"])

        item1.setIcon(0, QIcon(resource_library.Icon.dev_code))  # Set the icon for the first column (0)
        item2.setIcon(0, QIcon(resource_library.Icon.dev_ruler))  # Set the icon for the first column (0)

        item1.addChild(item2)

        self.module_tree.addTopLevelItem(item1)
        self.module_tree.setHeaderHidden(True)  # Hide the header

    def create_layout(self):
        """Create the layout for the window."""

        main_layout = QVBoxLayout()
        main_layout.setMenuBar(self.menubar)  # Set the menu bar at the top

        temp_layout = QWidget()

        self.splitter = QSplitter(self)
        self.splitter.setHandleWidth(5)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.module_tree)
        self.splitter.addWidget(temp_layout)

        body_layout = QHBoxLayout()  # Below the menu bar

        body_layout.addWidget(self.splitter)  # Add the QTreeWidget below the menu bar
        main_layout.addLayout(body_layout)

        self.setLayout(main_layout)

    def resize_splitter_to_screen(self, percentage=20):
        """
        Resizes the splitter to match a percentage of the screen size.

        Args:
            percentage (int, optional): The percentage of the screen size that the window should inherit.
                                        Must be a value between 0 and 100. Default is 20.

        Raises:
            ValueError: If the percentage is not within the range [0, 100].
        """
        if not 0 <= percentage <= 100:
            raise ValueError("Percentage should be between 0 and 100")
        screen_geometry = QDesktopWidget().availableGeometry(self)
        width = screen_geometry.width() * percentage / 100
        self.splitter.setSizes([width*.55, width*.60])


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = RiggerView()
        window.show()
