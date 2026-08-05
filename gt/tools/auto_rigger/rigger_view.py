"""
Auto Rigger View
"""

import gt.ui.tree_widget_enhanced as ui_tree_enhanced
import gt.ui.resource_library as ui_res_lib
import gt.core.session as core_session
import gt.ui.qt_utils as ui_qt_utils
import gt.ui.qt_utils as qt_utils
import gt.ui.qt_import as ui_qt


class RiggerView(metaclass=ui_qt_utils.MayaWindowMeta):
    TOOL_NAME = "Auto Rigger"

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
        super().__init__(parent=parent)
        self.close_func = None
        self.controller = controller  # Only here so it doesn't get deleted by the garbage collectors
        self.menu_top = None
        self.menu_items = []  # To avoid garbage collection
        self.splitter = None
        self.module_tree = None
        self.module_attr_area = None

        self.grp_box_buttons = None
        self.build_proxy_btn = None
        self.build_rig_btn = None

        self.grp_box_logger = None
        self.logger_txt_field = None

        self._version = version
        self.set_window_title()
        self.setGeometry(100, 100, 400, 300)
        self.setWindowFlags(
            self.windowFlags()
            | ui_qt.QtLib.WindowFlag.WindowMaximizeButtonHint
            | ui_qt.QtLib.WindowFlag.WindowMinimizeButtonHint
        )
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_auto_rigger))

        # Create Widgets and Layout
        self.create_widgets()
        self.create_layout()

        # Style Window
        stylesheet = ui_res_lib.Stylesheet.scroll_bar_base
        stylesheet += ui_res_lib.Stylesheet.maya_dialog_base
        stylesheet += ui_res_lib.Stylesheet.combobox_base
        stylesheet += ui_res_lib.Stylesheet.tree_widget_base
        stylesheet += ui_res_lib.Stylesheet.table_widget_base
        stylesheet += ui_res_lib.Stylesheet.checkbox_base
        stylesheet += ui_res_lib.Stylesheet.line_edit_base
        stylesheet += ui_res_lib.Stylesheet.spin_box_base
        stylesheet += ui_res_lib.Stylesheet.slider_base
        if not core_session.is_script_in_interactive_maya():
            stylesheet += ui_res_lib.Stylesheet.menu_base
        self.setStyleSheet(stylesheet)
        self.splitter.setStyleSheet("QSplitter::handle {margin: 5;}")
        self.grp_box_buttons.setStyleSheet(ui_res_lib.Stylesheet.group_box_base)
        self.grp_box_logger.setStyleSheet(ui_res_lib.Stylesheet.group_box_base)
        self.module_attr_area.setStyleSheet(ui_res_lib.Stylesheet.scroll_area_base)

        # Final Adjustments
        qt_utils.resize_to_screen(self, percentage=45)
        qt_utils.center_window(self)

        self.resize_splitter_to_screen()

    def create_widgets(self):
        """Create the widgets for the window."""
        self.menu_top = ui_qt.QtWidgets.QMenuBar(self)

        self.splitter = ui_qt.QtWidgets.QSplitter(self)
        self.splitter.setHandleWidth(5)
        self.splitter.setChildrenCollapsible(False)

        self.module_tree = ui_tree_enhanced.QTreeEnhanced()
        self.module_tree.set_one_root_mode(state=True)
        self.module_tree.setHeaderHidden(True)  # Hide the header
        self.module_tree.setDragDropMode(ui_qt.QtLib.DragDropMode.InternalMove)
        self.module_tree.setSelectionMode(ui_qt.QtLib.SelectionMode.SingleSelection)

        font = ui_qt.QtGui.QFont()
        font.setPointSize(14)
        self.module_tree.setFont(font)
        icon_size = 32
        self.module_tree.setIconSize(ui_qt.QtCore.QSize(icon_size, icon_size))

        self.build_proxy_btn = ui_qt.QtWidgets.QPushButton("Build Proxy")
        self.build_rig_btn = ui_qt.QtWidgets.QPushButton("Build Rig")

        self.module_attr_area = ui_qt.QtWidgets.QScrollArea()
        self.module_attr_area.setWidgetResizable(True)
        self.module_attr_area.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)

        self.logger_txt_field = ui_qt.QtWidgets.QLineEdit()
        self.logger_txt_field.setReadOnly(True)

    def create_layout(self):
        """Create the layout for the window."""
        # Main Layout
        main_layout = ui_qt.QtWidgets.QVBoxLayout()
        main_layout.setMenuBar(self.menu_top)  # Set the menu bar at the top
        self.menu_top.setStyleSheet(
            "QMenuBar {" "padding-top: 10; " "padding-right: 0; " "padding-bottom: 0; " "padding-left: 15;}"
        )
        # Left Widget
        left_widget = ui_qt.QtWidgets.QWidget()
        left_layout = ui_qt.QtWidgets.QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.module_tree)

        self.grp_box_buttons = ui_qt.QtWidgets.QGroupBox()
        layout_buttons = ui_qt.QtWidgets.QHBoxLayout()
        self.grp_box_buttons.setLayout(layout_buttons)
        layout_buttons.addWidget(self.build_rig_btn)
        layout_buttons.addWidget(self.build_proxy_btn)
        left_layout.addLayout(layout_buttons)
        left_layout.addWidget(self.grp_box_buttons)

        # Right Widget
        right_widget = ui_qt.QtWidgets.QWidget()
        right_layout = ui_qt.QtWidgets.QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.module_attr_area)
        self.grp_box_logger = ui_qt.QtWidgets.QGroupBox()
        layout_logger = ui_qt.QtWidgets.QHBoxLayout()
        self.grp_box_logger.setLayout(layout_logger)
        layout_logger.addWidget(self.logger_txt_field)

        # Splitter
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(right_widget)

        # Body (Below Menu Bar)
        body_layout = ui_qt.QtWidgets.QHBoxLayout()
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
        if ui_qt.IS_PYSIDE6:
            screen = ui_qt.QtGui.QGuiApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
        else:
            screen_geometry = ui_qt.QtWidgets.QDesktopWidget().availableGeometry(self)
        width = screen_geometry.width() * percentage / 100
        self.splitter.setSizes([width * 0.2, width * 0.60])

    def set_window_title(self, prefix=None, add_tool_name=True, add_version=True):
        """
        Sets the window title for this tool.
        Args:
            prefix (str, optional): A new prefix for the tool title.
            add_tool_name (bool, optional): If True, the name of the tool is added to the title (after prefix)
            add_version (bool, optional): If True, the tool version is added to the end of the title.
        """
        _window_title = ""
        if prefix is not None:
            _window_title = f"{str(prefix)} - "
        if add_tool_name:
            _window_title += RiggerView.TOOL_NAME
        if self._version and add_version:
            _window_title += f" - (v{str(self._version)})"
        self.setWindowTitle(_window_title)

    def clear_module_widget(self):
        """Clears the module attribute area by setting an empty widget."""
        self.module_attr_area.setWidget(ui_qt.QtWidgets.QWidget())

    def set_module_widget(self, widget):
        """Sets the given widget into the module attribute area.
        Args:
            widget (QWidget): The widget to set in the module attribute area.
        """
        self.module_attr_area.setWidget(widget)

    def get_module_widget(self):
        """Sets the given widget into the module attribute area.
        Returns:
            widget (QWidget): The widget assigned to the "module_attr_area" variable.
        """
        return self.module_attr_area.widget()

    def add_item_to_module_tree(self, item):
        """
        Adds a top-level item to the module tree.
        Args:
            item (QTreeWidgetItem): The item to add to the module tree.
        """
        self.module_tree.addTopLevelItem(item)

    def expand_all_module_tree_items(self):
        """Expands all items in the module tree."""
        self.module_tree.expandAll()

    def clear_module_tree(self):
        """Clears all items from the module tree."""
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
        submenu = ui_qt.QtWidgets.QMenu(submenu_name, **params)
        parent_menu.addMenu(submenu)
        return submenu

    def set_close_event_function(self, func):
        """
        Sets function to run when trying to close the view window.
        This function will receive two keyword arguments. Window, which is self (this window) and the close QEvent.
        Args:
            func (callable): A function to be called when a user try to close the window.
        """
        if callable(func):
            self.close_func = func
            return

    def closeEvent(self, event):
        """
        This is an override, name of the function cannot be changed.
        Runs a custom function (if available) when trying to close the rigger view (UI)
        The event is ignored. It also passes a keyword arguments with the window (self).

        Args:
            event (QEvent): Closing event that comes with the click of the "X" (close) button.
        """
        # event.ignore()
        if self.close_func and callable(self.close_func):
            self.close_func(self, event)

    def dockCloseEventTriggered(self):
        """
        This is an override, name of the function cannot be changed.
        Function called when in Maya using the dockable version of the window.
        """
        if self.close_func and callable(self.close_func):
            self.close_func(window=self)


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = RiggerView()

        from gt.tools.auto_rigger.rig_framework import ModuleGeneric

        a_generic_module = ModuleGeneric(name="my module")

        # Test Adding Menubar Item
        file_menu = window.add_menu_parent("Project")

        # Add an "Exit" action to the menu

        exit_action = ui_qt.QtLib.QtGui.QAction("Exit", icon=ui_qt.QtGui.QIcon(ui_res_lib.Icon.dev_chainsaw))
        exit_action.triggered.connect(window.close)
        file_menu.addAction(exit_action)

        # Test Adding Modules to Tree
        item1 = ui_qt.QtWidgets.QTreeWidgetItem(["Item 1"])
        item2 = ui_qt.QtWidgets.QTreeWidgetItem(["Item 2"])

        item1.setIcon(0, ui_qt.QtGui.QIcon(ui_res_lib.Icon.dev_code))  # Set the icon for the first column (0)
        item2.setIcon(0, ui_qt.QtGui.QIcon(ui_res_lib.Icon.dev_ruler))  # Set the icon for the first column (0)

        item1.addChild(item2)
        window.add_item_to_module_tree(item1)
        window.expand_all_module_tree_items()

        # Test Widget Side
        a_widget = ui_qt.QtWidgets.QWidget()
        a_layout = ui_qt.QtWidgets.QHBoxLayout()
        a_widget.setLayout(a_layout)
        a_layout.addWidget(ui_qt.QtWidgets.QLabel("A long name.............................................."))
        a_layout.addWidget(ui_qt.QtWidgets.QPushButton("Button"))
        a_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)

        window.set_module_widget(a_widget)

        window.show()
