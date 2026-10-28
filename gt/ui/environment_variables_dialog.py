"""Reusable browser for resolved environment-variable tokens and values."""

import gt.ui.qt_import as ui_qt
import gt.ui.resource_library as ui_res_lib


class EnvironmentVariablesDialog(ui_qt.QtWidgets.QDialog):
    """Displays environment-variable tokens, values, and descriptions."""

    def __init__(
        self,
        refresh_callback,
        parent=None,
        title="Environment Variables",
        descriptions=None,
        custom_description="Custom environment variable defined by the user.",
    ):
        """Initializes the environment-variable browser.

        Args:
            refresh_callback (callable): Function that returns the latest
                environment variables as a dictionary.
            parent (QWidget, optional): Parent widget.
            title (str, optional): Window title.
            descriptions (dict, optional): Built-in token descriptions.
            custom_description (str, optional): Description for unrecognized tokens.
        """
        super().__init__(parent)
        self.refresh_callback = refresh_callback
        self.descriptions = descriptions or {}
        self.custom_description = custom_description
        self._all_values = {}
        self._section_width_weights = [230, 300, 400]
        self._adjusting_columns = False

        self.setWindowTitle(title)
        self.setMinimumSize(600, 360)
        self.resize(1000, 560)

        layout = ui_qt.QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        description = ui_qt.QtWidgets.QLabel(
            "Filter by token, current value, or description. "
            "Right-click a row to copy its token or value."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        self.filter_line_edit = ui_qt.QtWidgets.QLineEdit()
        self.filter_line_edit.setPlaceholderText("Filter variables...")
        self.filter_line_edit.textChanged.connect(self.filter_rows)
        layout.addWidget(self.filter_line_edit)

        self.variable_table = ui_qt.QtWidgets.QTableWidget(0, 3)
        self.variable_table.setHorizontalHeaderLabels(
            ["Token", "Current value", "Description"]
        )
        self.variable_table.verticalHeader().hide()
        self.variable_table.setAlternatingRowColors(True)
        self.variable_table.setEditTriggers(
            self._get_qt_enum(
                ui_qt.QtWidgets.QAbstractItemView,
                "EditTrigger",
                "NoEditTriggers",
            )
        )
        self.variable_table.setSelectionBehavior(
            self._get_qt_enum(
                ui_qt.QtWidgets.QAbstractItemView,
                "SelectionBehavior",
                "SelectRows",
            )
        )
        self.variable_table.setSelectionMode(
            ui_qt.QtLib.SelectionMode.SingleSelection
        )
        self.variable_table.setContextMenuPolicy(
            self._get_qt_enum(
                ui_qt.QtCore.Qt,
                "ContextMenuPolicy",
                "CustomContextMenu",
            )
        )
        self.variable_table.customContextMenuRequested.connect(self.show_context_menu)
        self.variable_table.cellDoubleClicked.connect(self.copy_from_cell)

        header = self.variable_table.horizontalHeader()
        for column in range(self.variable_table.columnCount()):
            header.setSectionResizeMode(column, ui_qt.QtLib.QHeaderView.Interactive)
        for column, width in enumerate(self._section_width_weights):
            self.variable_table.setColumnWidth(column, width)
        header.sectionResized.connect(self.on_column_resized)
        layout.addWidget(self.variable_table, 1)

        self.status_label = ui_qt.QtWidgets.QLabel()
        self.status_label.setStyleSheet("color: #999999;")
        layout.addWidget(self.status_label)

        buttons_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.refresh_button = ui_qt.QtWidgets.QPushButton("Refresh")
        self.refresh_button.setToolTip("Re-read the current environment variables.")
        self.refresh_button.clicked.connect(self.refresh)
        buttons_layout.addWidget(self.refresh_button)
        buttons_layout.addStretch()

        close_button = ui_qt.QtWidgets.QPushButton("Close")
        close_button.clicked.connect(self.close)
        buttons_layout.addWidget(close_button)
        for button in (self.refresh_button, close_button):
            button.setMinimumHeight(32)
            button.setStyleSheet("padding: 5px 12px;")
        layout.addLayout(buttons_layout)

        self.variable_context_menu = ui_qt.QtWidgets.QMenu(self)
        copy_token_action = self.variable_context_menu.addAction("Copy Token")
        copy_token_action.setIcon(
            ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_copy_text)
        )
        copy_token_action.triggered.connect(self.copy_token)
        copy_value_action = self.variable_context_menu.addAction("Copy Value")
        copy_value_action.setIcon(
            ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_copy_text)
        )
        copy_value_action.triggered.connect(self.copy_value)

    @staticmethod
    def _get_qt_enum(owner, group_name, value_name):
        """Gets a Qt enum value across PySide2 and PySide6.

        Args:
            owner (type): Qt class or namespace containing the enum.
            group_name (str): Nested enum class name used by PySide6.
            value_name (str): Enum member name.

        Returns:
            object: The requested Qt enum member.
        """
        enum_group = getattr(owner, group_name, None)
        if enum_group is not None and hasattr(enum_group, value_name):
            return getattr(enum_group, value_name)
        return getattr(owner, value_name)

    def resizeEvent(self, event):
        """Resizes table columns proportionally when the window changes size.

        Args:
            event (QResizeEvent): Window resize event.
        """
        super().resizeEvent(event)
        if hasattr(self, "variable_table"):
            ui_qt.QtCore.QTimer.singleShot(0, self.resize_table_columns)

    def resize_table_columns(self):
        """Uses the table's full width while preserving column proportions."""
        if not hasattr(self, "variable_table"):
            return
        table_width = self.variable_table.viewport().width()
        header = self.variable_table.horizontalHeader()
        column_count = self.variable_table.columnCount()
        minimum_width = header.minimumSectionSize()
        if table_width < minimum_width * column_count:
            return

        weights = self._section_width_weights
        remaining_width = table_width
        remaining_weight = sum(weights)
        widths = []
        for column_weight in weights[:-1]:
            sections_remaining = column_count - len(widths) - 1
            maximum_width = remaining_width - minimum_width * sections_remaining
            width = int(round(remaining_width * column_weight / remaining_weight))
            width = min(max(minimum_width, width), maximum_width)
            widths.append(width)
            remaining_width -= width
            remaining_weight -= column_weight
        widths.append(remaining_width)
        self.set_column_widths(widths)

    def on_column_resized(self, resized_column, old_width, new_width):
        """Keeps columns fitted after a user adjusts a header section.

        Args:
            resized_column (int): Column whose width changed.
            old_width (int): Previous width of the resized column.
            new_width (int): Requested width of the resized column.
        """
        if self._adjusting_columns:
            return
        table_width = self.variable_table.viewport().width()
        header = self.variable_table.horizontalHeader()
        column_count = self.variable_table.columnCount()
        minimum_width = header.minimumSectionSize()
        if table_width < minimum_width * column_count:
            return

        resized_width = min(
            max(minimum_width, new_width),
            table_width - minimum_width * (column_count - 1),
        )
        other_columns = [
            column for column in range(column_count) if column != resized_column
        ]
        other_weights = [header.sectionSize(column) for column in other_columns]
        remaining_width = table_width - resized_width
        remaining_weight = sum(other_weights) or len(other_weights)
        widths = [0] * column_count
        widths[resized_column] = resized_width

        for index, column in enumerate(other_columns[:-1]):
            sections_remaining = len(other_columns) - index - 1
            maximum_width = remaining_width - minimum_width * sections_remaining
            width = int(round(remaining_width * other_weights[index] / remaining_weight))
            width = min(max(minimum_width, width), maximum_width)
            widths[column] = width
            remaining_width -= width
            remaining_weight -= other_weights[index]
        widths[other_columns[-1]] = remaining_width

        self.set_column_widths(widths)
        self._section_width_weights = list(widths)

    def set_column_widths(self, widths):
        """Sets table column widths without treating them as user adjustments.

        Args:
            widths (list): Widths to apply by column index.
        """
        self._adjusting_columns = True
        try:
            for column, width in enumerate(widths):
                self.variable_table.setColumnWidth(column, width)
        finally:
            self._adjusting_columns = False

    def showEvent(self, event):
        """Fits table columns once the dialog's initial layout is available.

        Args:
            event (QShowEvent): Window show event.
        """
        super().showEvent(event)
        self.resize_table_columns()

    def refresh(self, checked=False):
        """Reloads environment-variable values using the supplied callback.

        Args:
            checked (bool, optional): Ignored button signal value.
        """
        selected_token = self.get_token_for_row()
        try:
            values = self.refresh_callback()
            if not isinstance(values, dict):
                raise ValueError("The environment-variable source did not return a dictionary.")
        except Exception as error:
            self.status_label.setText(f"Unable to refresh variables: {error}")
            return

        self._all_values = {
            str(token): "" if value is None else str(value)
            for token, value in values.items()
        }
        self.populate_table(selected_token=selected_token)
        self.update_result_count()

    def populate_table(self, selected_token=None):
        """Rebuilds the table from the latest values.

        Args:
            selected_token (str, optional): Token to reselect after rebuilding.
        """
        self.variable_table.setRowCount(0)
        sorted_values = sorted(
            self._all_values.items(),
            key=lambda item: item[0].casefold(),
        )
        for token, value in sorted_values:
            row = self.variable_table.rowCount()
            self.variable_table.insertRow(row)
            token_item = ui_qt.QtWidgets.QTableWidgetItem(token)
            displayed_value = value if value else "<no-value>"
            value_item = ui_qt.QtWidgets.QTableWidgetItem(displayed_value)
            if value:
                value_item.setToolTip(value)
            else:
                value_item.setForeground(ui_qt.QtGui.QColor(145, 145, 145))
                value_item.setToolTip("This environment variable currently has no value.")
            description_item = ui_qt.QtWidgets.QTableWidgetItem(
                self.get_variable_description(token)
            )
            self.variable_table.setItem(row, 0, token_item)
            self.variable_table.setItem(row, 1, value_item)
            self.variable_table.setItem(row, 2, description_item)

        self.filter_rows(self.filter_line_edit.text())
        if selected_token:
            for row in range(self.variable_table.rowCount()):
                token_item = self.variable_table.item(row, 0)
                if token_item and token_item.text() == selected_token:
                    if not self.variable_table.isRowHidden(row):
                        self.variable_table.selectRow(row)
                    break

    def filter_rows(self, text):
        """Hides rows that do not match the token or value filter.

        Args:
            text (str): Filter text.
        """
        needle = str(text or "").casefold()
        for row in range(self.variable_table.rowCount()):
            token_item = self.variable_table.item(row, 0)
            value_item = self.variable_table.item(row, 1)
            description_item = self.variable_table.item(row, 2)
            token = token_item.text() if token_item else ""
            value = value_item.text() if value_item else ""
            description = description_item.text() if description_item else ""
            self.variable_table.setRowHidden(
                row,
                needle not in token.casefold()
                and needle not in value.casefold()
                and needle not in description.casefold(),
            )
        self.update_result_count()

    def get_variable_description(self, token):
        """Gets a built-in description or identifies a user-defined variable.

        Args:
            token (str): Braced or unbraced environment-variable name.

        Returns:
            str: Description for the token.
        """
        normalized_token = (
            str(token or "").strip().strip("{}").replace("_", "-").casefold()
        )
        description = self.descriptions.get(normalized_token)
        if description:
            return description
        return self.custom_description

    def get_token_for_row(self, row=None):
        """Gets a token from a specified or currently selected row.

        Args:
            row (int, optional): Row to read. Uses the current selection if omitted.

        Returns:
            str: Token from the row, or an empty string when no row is available.
        """
        if row is None:
            selected_items = self.variable_table.selectedItems()
            row = selected_items[0].row() if selected_items else self.variable_table.currentRow()
        if row < 0 or row >= self.variable_table.rowCount():
            return ""
        item = self.variable_table.item(row, 0)
        return item.text() if item else ""

    def update_result_count(self):
        """Displays how many variables match the current filter."""
        visible_count = sum(
            not self.variable_table.isRowHidden(row)
            for row in range(self.variable_table.rowCount())
        )
        total_count = len(self._all_values)
        self.status_label.setText(f"Showing {visible_count} of {total_count} variable(s).")

    def copy_token(self, checked=False, row=None):
        """Copies a row's token to the system clipboard.

        Args:
            checked (bool, optional): Ignored action signal value.
            row (int, optional): Row to copy. Uses the current selection if omitted.
        """
        token = self.get_token_for_row(row=row)
        if not token:
            return
        ui_qt.QtWidgets.QApplication.clipboard().setText(token)
        self.status_label.setText(f"Copied {token}.")

    def copy_value(self, checked=False, row=None):
        """Copies a row's current value to the system clipboard.

        Args:
            checked (bool, optional): Ignored action signal value.
            row (int, optional): Row to copy. Uses the current selection if omitted.
        """
        token = self.get_token_for_row(row=row)
        if not token:
            return
        value = self._all_values.get(token, "")
        ui_qt.QtWidgets.QApplication.clipboard().setText(value)
        if value:
            self.status_label.setText(f"Copied value for {token}.")
        else:
            self.status_label.setText(f"Copied the empty value for {token}.")

    def copy_from_cell(self, row, column):
        """Copies a token or value when its table cell is double-clicked.

        Args:
            row (int): Double-clicked row index.
            column (int): Double-clicked column index.
        """
        self.variable_table.setCurrentCell(row, column)
        self.variable_table.selectRow(row)
        if column == 0:
            self.copy_token(row=row)
        elif column == 1:
            self.copy_value(row=row)

    def show_context_menu(self, position):
        """Shows token and value copy actions for the row under the pointer.

        Args:
            position (QPoint): Position in the table viewport.
        """
        row = self.variable_table.rowAt(position.y())
        if row < 0:
            return
        self.variable_table.setCurrentCell(row, 0)
        self.variable_table.selectRow(row)
        self.variable_context_menu.popup(
            self.variable_table.viewport().mapToGlobal(position)
        )
