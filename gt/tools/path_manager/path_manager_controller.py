"""Controller that connects the Path Manager model and view."""

from gt.tools.path_manager import path_manager_constants as constants
import gt.ui.qt_import as ui_qt


class PathManagerController:
    """Coordinates Path Manager view interaction and Maya path operations."""

    def __init__(self, model, view):
        """Initializes and connects the Path Manager MVC objects.

        Args:
            model (PathManagerModel): Tool model.
            view (PathManagerView): Tool view.
        """
        self.model = model
        self.view = view
        self.view.controller = self
        self._connect_view()

    def start(self):
        """Shows the view and populates its current path data."""
        self.refresh_paths()
        self.view.show()

    def refresh_paths(self):
        """Reads current Maya paths and updates the table."""
        self.view.populate_path_items(self.model.get_path_items())

    def browse_search_directory(self):
        """Opens Maya's directory selector and updates the search field."""
        try:
            cmds = self._get_maya_cmds()
            selected_paths = cmds.fileDialog2(
                fileFilter="Directories Only (.donotshowfiles)",
                dialogStyle=2,
                fm=3,
                caption="Select Search Directory",
                okc="Select Directory",
            )
        except RuntimeError as exception:
            self._show_warning(f"Unable to choose a search directory: {exception}")
            return
        if selected_paths:
            self.view.search_path_field.setText(selected_paths[0])

    def repair_paths(self):
        """Runs automatic repair with a temporary busy cursor."""
        self._set_busy_cursor(True)
        try:
            repaired_count, skipped_count, message = self.model.repair_paths(
                self.view.search_path_field.text()
            )
        finally:
            self._set_busy_cursor(False)
        self.refresh_paths()
        if message:
            self._show_warning(message)
        elif repaired_count or skipped_count:
            print(f"Path Manager repaired {repaired_count} path(s); {skipped_count} item(s) were skipped.")

    def open_search_replace_dialog(self):
        """Shows search-and-replace controls and applies accepted values."""
        values = self.view.show_search_replace_dialog()
        if not values:
            return
        search_text, replace_text = values
        updated_count, skipped_count, message = self.model.replace_paths(search_text, replace_text)
        if message:
            self._show_warning(message)
            return
        self.refresh_paths()
        print(f"Path Manager updated {updated_count} path(s); {skipped_count} item(s) were skipped.")

    def select_row_node(self, row, column):
        """Selects the Maya node represented by a clicked table row.

        Args:
            row (int): Clicked table row.
            column (int): Clicked table column.
        """
        del column
        path_item = self.view.get_path_item_from_row(row)
        if path_item:
            self.model.select_node(path_item.get("node_name"))

    def process_cell_change(self, row, column):
        """Applies a user edit from a node-name or path table cell.

        Args:
            row (int): Edited table row.
            column (int): Edited table column.
        """
        if column not in (constants.TABLE_COLUMN_NODE, constants.TABLE_COLUMN_PATH):
            return
        path_item = self.view.get_path_item_from_row(row)
        table_item = self.view.path_table.item(row, column)
        if not path_item or not table_item:
            return
        if column == constants.TABLE_COLUMN_NODE:
            self._rename_node(path_item, table_item.text())
        elif column == constants.TABLE_COLUMN_PATH:
            self._update_path(path_item, table_item.text())

    def _connect_view(self):
        """Connects all view signals to controller actions."""
        self.view.refresh_button.clicked.connect(self.refresh_paths)
        self.view.browse_button.clicked.connect(self.browse_search_directory)
        self.view.repair_button.clicked.connect(self.repair_paths)
        self.view.search_replace_button.clicked.connect(self.open_search_replace_dialog)
        self.view.path_table.cellClicked.connect(self.select_row_node)
        self.view.path_table.cellChanged.connect(self.process_cell_change)

    def _rename_node(self, path_item, new_name):
        """Renames a node then refreshes table data.

        Args:
            path_item (dict): Current item data.
            new_name (str): Requested node name.
        """
        original_name = path_item.get("node_name")
        if new_name == original_name:
            return
        success, _, message = self.model.rename_node(original_name, new_name)
        self.refresh_paths()
        if not success:
            self._show_warning(message)

    def _update_path(self, path_item, new_path):
        """Updates a path then refreshes table data.

        Args:
            path_item (dict): Current item data.
            new_path (str): Requested path.
        """
        if new_path == path_item.get("path"):
            return
        success, message = self.model.set_path(path_item, new_path)
        self.refresh_paths()
        if not success:
            self._show_warning(message)

    @staticmethod
    def _get_maya_cmds():
        """Gets maya.cmds only for controller-owned Maya dialogs.

        Returns:
            module: maya.cmds module.
        """
        import maya.cmds as cmds

        return cmds

    @staticmethod
    def _set_busy_cursor(is_busy):
        """Shows or clears a temporary Qt wait cursor.

        Args:
            is_busy (bool): Whether to enable the wait cursor.
        """
        application = ui_qt.QtWidgets.QApplication.instance()
        if not application:
            return
        if is_busy:
            cursor_shape = (
                ui_qt.QtCore.Qt.CursorShape.WaitCursor
                if ui_qt.IS_PYSIDE6
                else ui_qt.QtCore.Qt.WaitCursor
            )
            application.setOverrideCursor(ui_qt.QtGui.QCursor(cursor_shape))
            application.processEvents()
        else:
            application.restoreOverrideCursor()

    @staticmethod
    def _show_warning(message):
        """Sends a concise warning through Maya's standard warning channel.

        Args:
            message (str): Warning message to show.
        """
        if not message:
            return
        try:
            PathManagerController._get_maya_cmds().warning(message)
        except RuntimeError:
            print(f"Path Manager warning: {message}")
