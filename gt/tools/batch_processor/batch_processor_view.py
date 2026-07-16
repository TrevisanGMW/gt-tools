"""
Batch Processor View
"""

import logging

from gt.tools.batch_processor import batch_processor_task_widget
import gt.ui.tree_widget_enhanced as ui_tree_enhanced
import gt.ui.resource_library as ui_res_lib
import gt.core.session as core_session
from gt.ui.qt_utils import MayaWindowMeta
import gt.ui.qt_utils as qt_utils
import gt.ui.qt_import as ui_qt


logger = logging.getLogger(__name__)


class BatchProcessorView(metaclass=MayaWindowMeta):
    """Main Qt view for the Batch Processor tool."""

    TOOL_NAME = "Batch Processor"
    DATA_ROLE = ui_qt.QtLib.ItemDataRole.UserRole

    def __init__(self, parent=None, controller=None, version=None):
        """Initializes the batch processor view.

        Args:
            parent (str): Parent for this window.
            controller (BatchProcessorController, optional): Controller reference.
            version (str, optional): Tool version for the window title.
        """
        super().__init__(parent=parent)
        self.controller = controller
        self._version = version
        self.menu_top = None
        self.menu_items = []
        self.splitter = None
        self.task_tree = None
        self.task_attr_area = None
        self.grp_box_buttons = None
        self.run_btn = None
        self.run_selected_btn = None
        self.validate_btn = None
        self.status_text = None
        self.project_item = None
        self.close_func = None

        self.set_window_title()
        self.setGeometry(100, 100, 850, 560)
        self.setWindowFlags(
            self.windowFlags()
            | ui_qt.QtLib.WindowFlag.WindowMaximizeButtonHint
            | ui_qt.QtLib.WindowFlag.WindowMinimizeButtonHint
        )
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_auto_rigger))
        self.create_widgets()
        self.create_layout()
        self.apply_stylesheet()
        qt_utils.resize_to_screen(self, percentage=45, width_percentage=65)
        qt_utils.center_window(self)
        self.resize_splitter_to_screen()

    def create_widgets(self):
        """Creates widgets used by this view."""
        self.menu_top = ui_qt.QtWidgets.QMenuBar(self)

        self.splitter = ui_qt.QtWidgets.QSplitter(self)
        self.splitter.setHandleWidth(5)
        self.splitter.setChildrenCollapsible(False)

        self.task_tree = ui_tree_enhanced.QTreeEnhanced()
        self.task_tree.set_one_root_mode(state=True)
        self.task_tree.setHeaderHidden(True)
        self.task_tree.setSelectionMode(ui_qt.QtLib.SelectionMode.SingleSelection)
        font = ui_qt.QtGui.QFont()
        font.setPointSize(14)
        self.task_tree.setFont(font)
        self.task_tree.setIconSize(ui_qt.QtCore.QSize(32, 32))

        self.run_btn = ui_qt.QtWidgets.QPushButton("Run")
        self.run_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_build))
        self.run_btn.setToolTip("Run the active batch project from the first enabled task.")
        self.run_selected_btn = ui_qt.QtWidgets.QPushButton("Run Selected")
        self.run_selected_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_progress))
        self.run_selected_btn.setToolTip("Run the active batch project from the selected task.")
        self.validate_btn = ui_qt.QtWidgets.QPushButton("Validate")
        self.validate_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.validator_pass))
        self.validate_btn.setToolTip("Validate the active batch project.")

        self.task_attr_area = ui_qt.QtWidgets.QScrollArea()
        self.task_attr_area.setWidgetResizable(True)
        self.task_attr_area.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)

        self.status_text = ui_qt.QtWidgets.QLineEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setToolTip("Last meaningful batch processor message.")

    def create_layout(self):
        """Creates the main view layout."""
        main_layout = ui_qt.QtWidgets.QVBoxLayout()
        main_layout.setMenuBar(self.menu_top)
        self.menu_top.setStyleSheet(
            "QMenuBar {" "padding-top: 10; " "padding-right: 0; " "padding-bottom: 0; " "padding-left: 15;}"
        )

        left_widget = ui_qt.QtWidgets.QWidget()
        left_layout = ui_qt.QtWidgets.QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.task_tree)

        self.grp_box_buttons = ui_qt.QtWidgets.QGroupBox()
        layout_buttons = ui_qt.QtWidgets.QVBoxLayout()
        self.grp_box_buttons.setLayout(layout_buttons)
        top_button_row = ui_qt.QtWidgets.QHBoxLayout()
        top_button_row.addWidget(self.run_btn)
        top_button_row.addWidget(self.validate_btn)
        layout_buttons.addLayout(top_button_row)
        left_layout.addWidget(self.grp_box_buttons)

        right_widget = ui_qt.QtWidgets.QWidget()
        right_layout = ui_qt.QtWidgets.QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.task_attr_area)
        right_layout.addWidget(self.status_text)

        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(right_widget)

        body_layout = ui_qt.QtWidgets.QHBoxLayout()
        body_layout.addWidget(self.splitter)
        main_layout.setContentsMargins(15, 0, 15, 15)
        main_layout.addLayout(body_layout)
        self.setLayout(main_layout)

    def apply_stylesheet(self):
        """Applies the repository UI stylesheet."""
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
        self.task_attr_area.setStyleSheet(ui_res_lib.Stylesheet.scroll_area_base)
        qt_utils.set_status_line_text(self.status_text, "")

    def resize_splitter_to_screen(self, percentage=20):
        """Resizes the splitter to match a percentage of the screen size.

        Args:
            percentage (int, optional): Percentage of screen size used to seed splitter sizes.
        """
        if not 0 <= percentage <= 100:
            raise ValueError("Percentage should be between 0 and 100")
        if ui_qt.IS_PYSIDE6:
            screen = ui_qt.QtGui.QGuiApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
        else:
            screen_geometry = ui_qt.QtWidgets.QDesktopWidget().availableGeometry(self)
        width = screen_geometry.width() * percentage / 100
        self.splitter.setSizes([width * 0.25, width * 0.75])

    def set_window_title(self, prefix=None, add_tool_name=True, add_version=True):
        """Sets the window title for this tool.

        Args:
            prefix (str, optional): Optional title prefix.
            add_tool_name (bool, optional): Whether to include the tool name.
            add_version (bool, optional): Whether to include the version string.
        """
        window_title = ""
        if prefix is not None:
            window_title = "{0} - ".format(str(prefix))
        if add_tool_name:
            window_title += self.TOOL_NAME
        if self._version and add_version:
            window_title += " - (v{0})".format(str(self._version))
        self.setWindowTitle(window_title)

    def set_close_event_function(self, func):
        """Sets a function to run when trying to close this window.

        Args:
            func (callable): Close-event callback.
        """
        if callable(func):
            self.close_func = func

    def closeEvent(self, event):
        """Runs a custom function when trying to close the view.

        Args:
            event (QCloseEvent): Close event.
        """
        self._run_close_callback(self, event)

    def dockCloseEventTriggered(self):
        """Runs a custom function when closing the dockable Maya window."""
        self._run_close_callback(window=self)

    def _run_close_callback(self, *args, **kwargs):
        """Runs the close callback while ignoring stale Maya Qt wrappers.

        Args:
            *args: Positional arguments forwarded to the close callback.
            **kwargs: Keyword arguments forwarded to the close callback.
        """
        if not qt_utils.is_qt_object_valid(self):
            logger.debug("Ignored close callback for a deleted Batch Processor view.")
            return
        try:
            close_callback = self.close_func
            if not close_callback or not callable(close_callback):
                return
            close_callback(*args, **kwargs)
        except RuntimeError as exception:
            if "Internal C++ object" not in str(exception) or "already deleted" not in str(exception):
                raise
            logger.debug(f"Ignored stale Batch Processor close callback. Issue: {exception}")

    def clear_task_widget(self):
        """Clears the task attribute area."""
        self.task_attr_area.setWidget(ui_qt.QtWidgets.QWidget())

    def set_task_widget(self, widget):
        """Sets the given widget into the task attribute area.

        Args:
            widget (QWidget): Widget to display.
        """
        try:
            widget.controller = self.controller
        except Exception:
            pass
        self.task_attr_area.setWidget(widget)

    def get_task_widget(self):
        """Gets the current task attribute widget.

        Returns:
            QWidget: Current attribute widget.
        """
        return self.task_attr_area.widget()

    def add_item_to_task_tree(self, item):
        """Adds a top-level item to the task tree.

        Args:
            item (QTreeWidgetItem): Item to add.
        """
        self.task_tree.addTopLevelItem(item)

    def expand_all_task_tree_items(self):
        """Expands all task tree items."""
        self.task_tree.expandAll()

    def clear_task_tree(self):
        """Clears the task tree."""
        self.task_tree.clear()

    def refresh_tree(self, project):
        """Refreshes the project/task tree.

        Args:
            project (BatchProcessorModel): Project to display.
        """
        selected_task_id = self.get_selected_task_id()
        signals_were_blocked = self.task_tree.blockSignals(True)
        try:
            self.clear_task_tree()

            self.project_item = ui_tree_enhanced.QTreeItemEnhanced([project.project_name])
            self.project_item.setIcon(0, ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_project))
            self.project_item.setData(0, self.DATA_ROLE, "project")
            self.project_item.setFlags(self.project_item.flags() & ~ui_qt.QtLib.ItemFlag.ItemIsDragEnabled)
            self.add_item_to_task_tree(self.project_item)

            selected_item = None
            for task in project.tasks:
                label = task.display_name
                tree_item = ui_tree_enhanced.QTreeItemEnhanced([label])
                tree_item.setIcon(0, ui_qt.QtGui.QIcon(batch_processor_task_widget.get_icon_path(task.icon)))
                tree_item.setData(0, self.DATA_ROLE, task.id)
                tree_item.set_allow_parenting(False)
                self.project_item.addChild(tree_item)
                is_selected_task = bool(selected_task_id and selected_task_id == task.id)
                if not task.enabled:
                    tree_item.setForeground(0, ui_qt.QtGui.QColor(ui_res_lib.Color.Hex.gray_dim))
                    tree_item.setToolTip(0, "Task is disabled.")
                if is_selected_task:
                    selected_item = tree_item

            self.expand_all_task_tree_items()
            self.task_tree.setCurrentItem(selected_item or self.project_item)
        finally:
            self.task_tree.blockSignals(signals_were_blocked)

    def update_task_tree_item(self, task):
        """Updates an existing task tree item in place.

        Args:
            task (BatchTask): Task providing the current label and enabled state.

        Returns:
            bool: True when a matching tree item was found and updated.
        """
        if not self.project_item or not task:
            return False
        for index in range(self.project_item.childCount()):
            tree_item = self.project_item.child(index)
            if tree_item.data(0, self.DATA_ROLE) != task.id:
                continue
            tree_item.setText(0, task.display_name)
            if task.enabled:
                tree_item.setForeground(0, ui_qt.QtGui.QBrush())
                tree_item.setToolTip(0, "")
            else:
                tree_item.setForeground(0, ui_qt.QtGui.QColor(ui_res_lib.Color.Hex.gray_dim))
                tree_item.setToolTip(0, "Task is disabled.")
            return True
        return False

    def get_selected_task_id(self):
        """Gets the selected task id from the tree.

        Returns:
            str or None: Selected task id.
        """
        item = self.task_tree.currentItem()
        if not item:
            return None
        item_data = item.data(0, self.DATA_ROLE)
        if item_data == "project":
            return None
        return item_data

    def is_project_selected(self):
        """Checks whether the project root is selected.

        Returns:
            bool: True when project root is selected.
        """
        item = self.task_tree.currentItem()
        return bool(item and item.data(0, self.DATA_ROLE) == "project")

    def select_task_by_id(self, task_id):
        """Selects a task tree item by task id.

        Args:
            task_id (str): Task id to select.

        Returns:
            bool: True when a matching item was selected.
        """
        if not self.project_item or not task_id:
            return False
        for index in range(self.project_item.childCount()):
            item = self.project_item.child(index)
            if item.data(0, self.DATA_ROLE) == task_id:
                self.task_tree.setCurrentItem(item)
                return True
        return False

    def add_menu_parent(self, item_name):
        """Adds a parent menu.

        Args:
            item_name (str): Menu name.

        Returns:
            QMenu: Added menu.
        """
        menu = ui_qt.QtWidgets.QMenu(item_name, self.menu_top)
        self.menu_top.addMenu(menu)
        self.menu_items.append(menu)
        return menu

    def add_menu_action(self, parent_menu, action):
        """Adds a QAction to a menu.

        Args:
            parent_menu (QMenu): Target menu.
            action (QAction): Action to add.
        """
        self.menu_items.append(action)
        parent_menu.addAction(action)

    def add_menu_submenu(self, parent_menu, submenu_name, icon=None):
        """Adds a submenu to a parent menu item.

        Args:
            parent_menu (QMenu): Parent menu.
            submenu_name (str): Submenu name.
            icon (QIcon, optional): Optional submenu icon.

        Returns:
            QMenu: Created submenu.
        """
        submenu = ui_qt.QtWidgets.QMenu(submenu_name, parent_menu)
        parent_menu.addMenu(submenu)
        if icon:
            submenu.setIcon(icon)
        self.menu_items.append(submenu)
        return submenu

    def set_status(self, message, status="info"):
        """Sets the status line.

        Args:
            message (str): Status message.
            status (str, optional): Status level used for color.
        """
        qt_utils.set_status_line_text(self.status_text, str(message), status=status)

    def set_progress(self, text):
        """Sets progress text.

        Args:
            text (str): Progress text.
        """
        self.set_status(text)


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = BatchProcessorView()
        window.show()
