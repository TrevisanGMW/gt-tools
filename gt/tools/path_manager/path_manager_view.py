"""Dockable Qt view for Path Manager."""

from gt.tools.path_manager import path_manager_constants as constants
from gt.ui.qt_utils import MayaWindowMeta
import gt.ui.qt_import as ui_qt
import gt.ui.qt_utils as qt_utils
import gt.ui.resource_library as ui_res_lib


class PathManagerView(metaclass=MayaWindowMeta):
    """Presents Path Manager controls and path-table data."""

    ATTRIBUTE_ROLE = ui_qt.QtLib.ItemDataRole.UserRole
    VALUE_ROLE = ui_qt.QtLib.ItemDataRole.UserRole + 1
    ITEM_ROLE = ui_qt.QtLib.ItemDataRole.UserRole + 2

    def __init__(self, parent=None, controller=None, version=None):
        """Initializes the Path Manager view.

        Args:
            parent (QWidget, optional): Parent widget.
            controller (PathManagerController, optional): Connected controller.
            version (str, optional): Tool version shown in the window title.
        """
        super().__init__(parent=parent)
        self.controller = controller
        self.version = version
        self.search_path_field = None
        self.browse_button = None
        self.path_table = None
        self.repair_button = None
        self.search_replace_button = None
        self.refresh_button = None
        self._set_window_properties()
        self.create_widgets()
        self.create_layout()
        qt_utils.center_window(self)

    def _set_window_properties(self):
        """Configures the dockable window's title, icon, and size limits."""
        title = constants.TOOL_NAME
        if self.version:
            title += f" - (v{self.version})"
        self.setWindowTitle(title)
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_path_manager))
        self.setMinimumSize(constants.WINDOW_MINIMUM_WIDTH, constants.WINDOW_MINIMUM_HEIGHT)
        self.resize(constants.WINDOW_DEFAULT_WIDTH, constants.WINDOW_DEFAULT_HEIGHT)
        self.setWindowFlags(
            self.windowFlags()
            | ui_qt.QtLib.WindowFlag.WindowMaximizeButtonHint
            | ui_qt.QtLib.WindowFlag.WindowMinimizeButtonHint
        )

    def create_widgets(self):
        """Creates controls owned by the Path Manager view."""
        self.search_path_field = ui_qt.QtWidgets.QLineEdit()
        self.search_path_field.setPlaceholderText("Path to a directory used by Auto Path Repair")
        self.search_path_field.setToolTip("Directory to scan recursively when repairing missing paths.")
        self.search_path_field.setSizePolicy(
            ui_qt.QtLib.SizePolicy.Expanding,
            ui_qt.QtLib.SizePolicy.Fixed,
        )

        self.browse_button = ui_qt.QtWidgets.QPushButton()
        self.browse_button.setIcon(ui_qt.QtGui.QIcon(":fileOpen.png"))
        self.browse_button.setToolTip("Select the directory searched by Auto Path Repair.")
        self.browse_button.setFixedSize(32, 28)

        self.path_table = ui_qt.QtWidgets.QTableWidget()
        self.path_table.setColumnCount(len(constants.TABLE_HEADERS))
        self.path_table.setHorizontalHeaderLabels(constants.TABLE_HEADERS)
        self.path_table.setAlternatingRowColors(True)
        self.path_table.setSelectionBehavior(ui_qt.QtWidgets.QAbstractItemView.SelectRows)
        self.path_table.setSelectionMode(ui_qt.QtWidgets.QAbstractItemView.SingleSelection)
        self.path_table.setEditTriggers(
            ui_qt.QtWidgets.QAbstractItemView.DoubleClicked
            | ui_qt.QtWidgets.QAbstractItemView.EditKeyPressed
        )
        self.path_table.setSizePolicy(
            ui_qt.QtLib.SizePolicy.Expanding,
            ui_qt.QtLib.SizePolicy.Expanding,
        )
        self.path_table.verticalHeader().setVisible(False)
        self.path_table.verticalHeader().setDefaultSectionSize(28)
        self.path_table.setStyleSheet(
            "QTableWidget::item { padding-left: 8px; padding-right: 8px; border: 0px; }"
        )
        header = self.path_table.horizontalHeader()
        header.setMinimumSectionSize(32)
        header.setSectionResizeMode(constants.TABLE_COLUMN_STATUS, ui_qt.QtLib.QHeaderView.Interactive)
        header.setSectionResizeMode(constants.TABLE_COLUMN_NODE, ui_qt.QtLib.QHeaderView.Interactive)
        header.setSectionResizeMode(constants.TABLE_COLUMN_TYPE, ui_qt.QtLib.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(constants.TABLE_COLUMN_PATH, ui_qt.QtLib.QHeaderView.Stretch)
        self.path_table.setColumnWidth(constants.TABLE_COLUMN_STATUS, 36)
        self.path_table.setColumnWidth(constants.TABLE_COLUMN_NODE, 170)
        self.path_table.setColumnWidth(constants.TABLE_COLUMN_TYPE, 135)

        self.repair_button = self._create_action_button("Auto Path Repair")
        self.repair_button.setToolTip("Search the selected directory and repair invalid paths by filename.")
        self.search_replace_button = self._create_action_button("Search and Replace")
        self.search_replace_button.setToolTip("Replace text in every path managed by this tool.")
        self.refresh_button = self._create_action_button("Refresh")
        self.refresh_button.setToolTip("Rebuild the table and check every path again.")

    def create_layout(self):
        """Creates an edge-padded, responsive Path Manager layout."""
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        main_layout.addWidget(self.path_table, 1)

        footer_layout = ui_qt.QtWidgets.QGridLayout()
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setHorizontalSpacing(6)
        footer_layout.setVerticalSpacing(6)

        search_label = ui_qt.QtWidgets.QLabel("Search Path:")
        search_label.setToolTip("Directory used by Auto Path Repair.")
        footer_layout.addWidget(search_label, 0, 0)
        footer_layout.addWidget(self.search_path_field, 0, 1)
        footer_layout.addWidget(self.browse_button, 0, 2)
        footer_layout.addWidget(self.repair_button, 0, 3)
        footer_layout.addWidget(self.search_replace_button, 0, 4)
        footer_layout.addWidget(self.refresh_button, 0, 5)
        footer_layout.setColumnStretch(1, 1)
        footer_layout.setColumnStretch(3, 0)
        footer_layout.setColumnStretch(4, 0)
        footer_layout.setColumnStretch(5, 0)
        main_layout.addLayout(footer_layout)

    def populate_path_items(self, path_items):
        """Displays fresh Path Manager data without emitting edit signals.

        Args:
            path_items (list): Path-item dictionaries provided by the model.
        """
        previous_state = self.path_table.blockSignals(True)
        try:
            self.path_table.setRowCount(0)
            for row, path_item in enumerate(path_items):
                self.path_table.insertRow(row)
                self._set_status_item(row, bool(path_item.get("is_valid")))
                self._set_data_item(
                    row,
                    constants.TABLE_COLUMN_NODE,
                    path_item.get("node_name"),
                    path_item.get("node_name"),
                    path_item=path_item,
                )
                self._set_data_item(
                    row,
                    constants.TABLE_COLUMN_TYPE,
                    path_item.get("display_type"),
                    path_item.get("node_type"),
                    icon_path=path_item.get("icon"),
                    editable=False,
                    path_item=path_item,
                )
                self._set_data_item(
                    row,
                    constants.TABLE_COLUMN_PATH,
                    path_item.get("path"),
                    path_item.get("path"),
                    attribute=path_item.get("attribute"),
                    alignment=ui_qt.QtLib.AlignmentFlag.AlignVCenter,
                    path_item=path_item,
                )
        finally:
            self.path_table.blockSignals(previous_state)

    def get_path_item_from_row(self, row):
        """Gets model data stored on a table row.

        Args:
            row (int): Table row index.

        Returns:
            dict or None: Stored path item data.
        """
        table_item = self.path_table.item(row, constants.TABLE_COLUMN_NODE)
        if not table_item:
            return None
        return table_item.data(self.ITEM_ROLE)

    def show_search_replace_dialog(self):
        """Shows the search-and-replace dialog and returns submitted values.

        Returns:
            tuple or None: Search and replacement strings, or None when cancelled.
        """
        dialog = ui_qt.QtWidgets.QDialog(self)
        dialog.setWindowTitle("Search and Replace")
        dialog.setWindowIcon(ui_qt.QtGui.QIcon(":search.png"))
        dialog.setMinimumWidth(360)
        layout = ui_qt.QtWidgets.QVBoxLayout(dialog)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        description = ui_qt.QtWidgets.QLabel("Search and replace text in all Path Manager paths.")
        description.setWordWrap(True)
        layout.addWidget(description)

        search_label = self._create_dialog_label("Search for:")
        search_field = ui_qt.QtWidgets.QLineEdit()
        search_field.setPlaceholderText("Text to find")
        replace_label = self._create_dialog_label("Replace with:")
        replace_field = ui_qt.QtWidgets.QLineEdit()
        replace_field.setPlaceholderText("Replacement text")
        layout.addWidget(search_label)
        layout.addWidget(search_field)
        layout.addWidget(replace_label)
        layout.addWidget(replace_field)

        buttons = ui_qt.QtWidgets.QDialogButtonBox()
        apply_button = buttons.addButton("Search and Replace", ui_qt.QtWidgets.QDialogButtonBox.AcceptRole)
        cancel_button = buttons.addButton(ui_qt.QtWidgets.QDialogButtonBox.Cancel)
        apply_button.setStyleSheet(ui_res_lib.Stylesheet.btn_push_base)
        cancel_button.setStyleSheet(ui_res_lib.Stylesheet.btn_push_base)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog_exec = getattr(dialog, "exec", None) or dialog.exec_
        if dialog_exec() != ui_qt.QtWidgets.QDialog.Accepted:
            return None
        return search_field.text(), replace_field.text()

    def _set_status_item(self, row, is_valid):
        """Creates a non-editable validity icon table item.

        Args:
            row (int): Target table row.
            is_valid (bool): Whether the represented path exists.
        """
        item = ui_qt.QtWidgets.QTableWidgetItem()
        item.setFlags(ui_qt.QtLib.ItemFlag.ItemIsEnabled | ui_qt.QtLib.ItemFlag.ItemIsSelectable)
        icon_path = constants.STATUS_ICON_VALID if is_valid else constants.STATUS_ICON_INVALID
        item.setIcon(ui_qt.QtGui.QIcon(icon_path))
        item.setToolTip("Path found" if is_valid else "Path not found")
        item.setTextAlignment(
            ui_qt.QtLib.AlignmentFlag.AlignHCenter | ui_qt.QtLib.AlignmentFlag.AlignVCenter
        )
        self.path_table.setItem(row, constants.TABLE_COLUMN_STATUS, item)

    def _set_data_item(
        self,
        row,
        column,
        text,
        value,
        attribute=None,
        icon_path=None,
        editable=True,
        alignment=None,
        path_item=None,
    ):
        """Creates a path-table item with its model data stored in roles.

        Args:
            row (int): Target table row.
            column (int): Target table column.
            text (str): Visible cell text.
            value (object): Original cell value.
            attribute (str, optional): Maya attribute used by editable path rows.
            icon_path (str, optional): Optional Maya icon resource path.
            editable (bool, optional): Whether the item can be edited.
            alignment (Qt.AlignmentFlag, optional): Text alignment.
            path_item (dict, optional): Full model item represented by the cell.
        """
        item = ui_qt.QtWidgets.QTableWidgetItem(str(text or ""))
        item.setData(self.VALUE_ROLE, value)
        item.setData(self.ATTRIBUTE_ROLE, attribute)
        item.setData(self.ITEM_ROLE, path_item)
        if icon_path:
            item.setIcon(ui_qt.QtGui.QIcon(icon_path))
        if not editable:
            item.setFlags(ui_qt.QtLib.ItemFlag.ItemIsEnabled | ui_qt.QtLib.ItemFlag.ItemIsSelectable)
        if alignment is None:
            alignment = ui_qt.QtLib.AlignmentFlag.AlignHCenter | ui_qt.QtLib.AlignmentFlag.AlignVCenter
        item.setTextAlignment(alignment)
        self.path_table.setItem(row, column, item)

    @staticmethod
    def _create_dialog_label(text):
        """Creates a visual section label used by the search dialog.

        Args:
            text (str): Label text.

        Returns:
            QLabel: Styled dialog label.
        """
        label = ui_qt.QtWidgets.QLabel(text)
        label.setStyleSheet("background-color: #5d5d5d; font-weight: bold; padding: 4px 6px;")
        return label

    @staticmethod
    def _create_action_button(text):
        """Creates a neutral Maya-gray action button.

        Args:
            text (str): Button label.

        Returns:
            QPushButton: Configured action button.
        """
        button = ui_qt.QtWidgets.QPushButton(text)
        button.setMinimumHeight(28)
        button.setStyleSheet(ui_res_lib.Stylesheet.btn_push_base)
        button.setSizePolicy(ui_qt.QtLib.SizePolicy.Minimum, ui_qt.QtLib.SizePolicy.Fixed)
        return button
