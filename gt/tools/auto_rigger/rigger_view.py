"""
Auto Rigger View
"""
from PySide2.QtWidgets import QMenuBar, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QLabel, QScrollArea, QAction, QMenu
from PySide2.QtWidgets import QWidget, QSplitter, QDesktopWidget, QHBoxLayout, QPushButton, QGroupBox
from gt.utils.session_utils import is_script_in_interactive_maya
from gt.ui.tree_widget_enhanced import QTreeEnhanced
import gt.ui.resource_library as resource_library
from gt.ui.qt_utils import MayaWindowMeta
from PySide2.QtGui import QIcon, QFont
import gt.ui.qt_utils as qt_utils
from PySide2.QtCore import Qt
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
        self.menu_top = None
        self.menu_items = []  # To avoid garbage collection
        self.splitter = None
        self.module_tree = None
        self.module_attr_area = None
        self.buttons_grp_box = None
        self.build_proxy_btn = None
        self.build_rig_btn = None

        window_title = "GT Auto Rigger"
        if version:
            window_title += f' - (v{str(version)})'
        self.setWindowTitle(window_title)
        self.setGeometry(100, 100, 400, 300)
        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.WindowMaximizeButtonHint |
                            QtCore.Qt.WindowMinimizeButtonHint)
        self.setWindowIcon(QIcon(resource_library.Icon.tool_auto_rigger))

        # Create Widgets and Layout
        self.create_widgets()
        self.create_layout()

        # Style Window
        stylesheet = resource_library.Stylesheet.scroll_bar_base
        stylesheet += resource_library.Stylesheet.maya_dialog_base
        stylesheet += resource_library.Stylesheet.combobox_base
        stylesheet += resource_library.Stylesheet.tree_widget_base
        stylesheet += resource_library.Stylesheet.table_widget_base
        stylesheet += resource_library.Stylesheet.checkbox_base
        stylesheet += resource_library.Stylesheet.line_edit_base
        if not is_script_in_interactive_maya():
            stylesheet += resource_library.Stylesheet.menu_base
        self.setStyleSheet(stylesheet)
        self.splitter.setStyleSheet("QSplitter::handle {margin: 5;}")
        self.buttons_grp_box.setStyleSheet(resource_library.Stylesheet.group_box_base)

        # Final Adjustments
        qt_utils.resize_to_screen(self, percentage=30)
        qt_utils.center_window(self)

        self.resize_splitter_to_screen()

    def create_widgets(self):
        """Create the widgets for the window."""
        self.menu_top = QMenuBar(self)

        self.splitter = QSplitter(self)
        self.splitter.setHandleWidth(5)
        self.splitter.setChildrenCollapsible(False)

        self.module_tree = QTreeEnhanced()
        self.module_tree.set_one_root_mode(state=True)
        self.module_tree.setHeaderHidden(True)  # Hide the header
        self.module_tree.setDragDropMode(QTreeWidget.InternalMove)
        self.module_tree.setSelectionMode(QTreeWidget.SingleSelection)

        font = QFont()
        font.setPointSize(14)
        self.module_tree.setFont(font)
        icon_size = 32
        self.module_tree.setIconSize(QtCore.QSize(icon_size, icon_size))

        self.build_proxy_btn = QPushButton("Build Proxy")
        self.build_rig_btn = QPushButton("Build Rig")

        self.module_attr_area = QScrollArea()
        self.module_attr_area.setWidgetResizable(True)
        self.module_attr_area.setAlignment(Qt.AlignTop)

    def create_layout(self):
        """Create the layout for the window."""
        # Main Layout
        main_layout = QVBoxLayout()
        main_layout.setMenuBar(self.menu_top)  # Set the menu bar at the top
        self.menu_top.setStyleSheet("QMenuBar {"
                                    "padding-top: 10; "
                                    "padding-right: 0; "
                                    "padding-bottom: 0; "
                                    "padding-left: 15;}")

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.module_tree)

        self.buttons_grp_box = QGroupBox()
        buttons_grp_layout = QHBoxLayout()
        self.buttons_grp_box.setLayout(buttons_grp_layout)
        buttons_grp_layout.addWidget(self.build_rig_btn)
        buttons_grp_layout.addWidget(self.build_proxy_btn)
        left_layout.addLayout(buttons_grp_layout)
        left_layout.addWidget(self.buttons_grp_box)

        # Splitter
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(self.module_attr_area)

        # Body (Below Menu Bar)
        body_layout = QHBoxLayout()
        body_layout.addWidget(self.splitter)
        main_layout.setContentsMargins(15, 0, 15, 15)  # Adjust the values as needed
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
        self.splitter.setSizes([width * .2, width * .60])

    def clear_module_widget(self):
        self.module_attr_area.setWidget(QWidget())

    def set_module_widget(self, widget):
        self.module_attr_area.setWidget(widget)

    def add_item_to_module_tree(self, item):
        self.module_tree.addTopLevelItem(item)

    def expand_all_module_tree_items(self):
        self.module_tree.expandAll()

    def clear_module_tree(self):
        self.module_tree.clear()

    def add_menu_parent(self, item_name):
        """
        Adds a parent menu (child of the main menu)
        Args:
            item_name (str): Name of the item menu to be added
        Returns:
            QMenu: Added menu item.
        """
        return self.menu_top.addMenu(item_name)

    def add_menu_action(self, parent_menu, action):
        """
        Adds a QAction to a menu or target_menu
        Args:
            parent_menu (QMenu): The target menu item
            action (QAction): Action to be added to the menu.
        """
        self.menu_items.append(action)  # Avoid garbage collector
        parent_menu.addAction(action)

    @staticmethod
    def add_menu_submenu(parent_menu, submenu_name, icon=None):
        """
        Adds a submenu to a parent menu item.
        Args:
            parent_menu (QMenu): Parent menu item (where the submenu will exist)
            submenu_name (str): Name of the submenu to be added.
            icon (QIcon, optional): If provided, this will be the icon of the submenu
        Returns:
            QMenu: Created submenu.
        """
        params = {}
        if icon:
            params["icon"] = icon
        submenu = QMenu(submenu_name, **params)
        parent_menu.addMenu(submenu)
        return submenu


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = RiggerView()

        from gt.tools.auto_rigger.rig_framework import ModuleGeneric
        a_generic_module = ModuleGeneric(name="my module")

        # Test Adding Menubar Item
        file_menu = window.add_menu_parent("Project")

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

        # Test Widget Side
        a_widget = QWidget()
        a_layout = QHBoxLayout()
        a_widget.setLayout(a_layout)
        a_layout.addWidget(QLabel("A long name.............................................."))
        a_layout.addWidget(QPushButton("Button"))
        a_layout.setAlignment(Qt.AlignTop)

        window.set_module_widget(a_widget)

        window.show()
