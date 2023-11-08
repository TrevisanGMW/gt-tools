"""
Auto Rigger View
"""
from PySide2.QtWidgets import QMenuBar, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QLabel, QScrollArea, QAction, \
    QLineEdit
from PySide2.QtWidgets import QWidget, QSplitter, QDesktopWidget, QHBoxLayout
import gt.ui.resource_library as resource_library
from gt.ui.qt_utils import MayaWindowMeta
import gt.ui.qt_utils as qt_utils
from PySide2.QtGui import QIcon, QPixmap
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
        self.splitter = None
        self.module_tree = None
        self.module_attr_area = None

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

        # # Style Window
        # stylesheet = resource_library.Stylesheet.scroll_bar_dark
        # stylesheet += resource_library.Stylesheet.maya_basic_dialog
        # stylesheet += resource_library.Stylesheet.list_widget_dark
        # stylesheet += resource_library.Stylesheet.combobox_dark
        # self.setStyleSheet(stylesheet)

        # Final Adjustments
        qt_utils.resize_to_screen(self, percentage=35)
        qt_utils.center_window(self)

        self.resize_splitter_to_screen()

    def create_widgets(self):
        """Create the widgets for the window."""
        # Create a menu bar
        self.menubar = QMenuBar(self)

        self.splitter = QSplitter(self)
        self.splitter.setHandleWidth(5)
        self.splitter.setChildrenCollapsible(False)

        self.module_tree = QTreeWidget()
        self.module_tree.setHeaderHidden(True)  # Hide the header

        self.module_attr_area = QScrollArea()

    def create_layout(self):
        """Create the layout for the window."""
        # Main Layout
        main_layout = QVBoxLayout()
        main_layout.setMenuBar(self.menubar)  # Set the menu bar at the top

        # Splitter
        self.splitter.addWidget(self.module_tree)
        self.splitter.addWidget(self.module_attr_area)

        # Body (Below Menu Bar)
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
        self.splitter.setSizes([width * .55, width * .60])

    def set_module_widget(self, widget):
        self.module_attr_area.setWidget(widget)

    def get_menu_bar(self):
        return self.menubar

    def add_item_to_module_tree(self, item):
        self.module_tree.addTopLevelItem(item)

    def expand_all_module_tree_items(self):
        qt_utils.expand_all_tree_items_recursively(self.module_tree)

    def clear_module_tree(self):
        self.module_tree.clear()


def create_module_attr_widget(module):

    scroll_content = QWidget()
    scroll_content_layout = QVBoxLayout(scroll_content)

    icon_path = module.icon
    module_type = module.get_module_class_name(remove_module_prefix=True)
    name = module.get_name()

    name_layout = QHBoxLayout(scroll_content)
    icon = QIcon(icon_path)
    icon_label = QLabel()
    icon_label.setPixmap(icon.pixmap(32, 32))
    name_layout.addWidget(icon_label)
    name_layout.addWidget(QLabel(f"{module_type}"))
    name_text_field = QLineEdit()
    if name:
        name_text_field.setText(name)
    name_layout.addWidget(name_text_field)

    scroll_content_layout.addLayout(name_layout)

    return scroll_content


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = RiggerView()

        from gt.tools.auto_rigger.rigger_framework import ModuleGeneric
        a_generic_module = ModuleGeneric(name="my module")

        # Test Adding Module Parameter Widget
        content = create_module_attr_widget(a_generic_module)
        window.set_module_widget(content)

        # Test Adding Menubar Item
        file_menu = window.get_menu_bar().addMenu("Project")

        # Add an "Exit" action to the menu
        exit_action = QAction("Exit", icon=QIcon(resource_library.Icon.dev_chainsaw))
        exit_action.triggered.connect(window.close)
        file_menu.addAction(exit_action)

        # Test Adding Modules to Tree
        item1 = QTreeWidgetItem(["Item 1"])
        item2 = QTreeWidgetItem(["Item 2"])

        item1.setIcon(0, QIcon(resource_library.Icon.dev_code))  # Set the icon for the first column (0)
        item2.setIcon(0, QIcon(resource_library.Icon.dev_ruler))  # Set the icon for the first column (0)

        item1.addChild(item2)
        window.add_item_to_module_tree(item1)
        window.expand_all_module_tree_items()

        window.show()
