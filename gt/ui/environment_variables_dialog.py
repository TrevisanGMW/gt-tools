"""Reusable browser for resolved environment-variable tokens and values."""

import gt.core.environment_references as core_env_refs
import gt.ui.qt_import as ui_qt
import gt.ui.resource_library as ui_res_lib

DEFAULT_REFERENCE_KIND_LABELS = {
    "task": ("task", "tasks"),
    "module": ("module", "modules"),
    "variable": ("variable", "variables"),
    "project": ("project setting", "project settings"),
}


class EnvironmentVariablesDialog(ui_qt.QtWidgets.QDialog):
    """Displays environment-variable tokens, values, descriptions, and optional references."""

    TOKEN_COLUMN = 0
    VALUE_COLUMN = 1
    DESCRIPTION_COLUMN = 2
    USED_BY_COLUMN = 3

    def __init__(
        self,
        refresh_callback,
        parent=None,
        title="Environment Variables",
        descriptions=None,
        custom_description="Custom environment variable defined by the user.",
        references_callback=None,
        references_tooltip="",
        reference_activated_callback=None,
        reference_kind_labels=None,
    ):
        """Initializes the environment-variable browser.

        Args:
            refresh_callback (callable): Function that returns the latest
                environment variables as a dictionary.
            parent (QWidget, optional): Parent widget.
            title (str, optional): Window title.
            descriptions (dict, optional): Built-in token descriptions.
            custom_description (str, optional): Description for unrecognized tokens.
            references_callback (callable, optional): Function returning a dictionary of
                unbraced token keys mapped to reference lists, as produced by
                ``gt.core.environment_references.find_references``. When omitted, the
                reference controls are not shown.
            references_tooltip (str, optional): Tooltip for the "Show references" checkbox,
                normally describing what the scan can and cannot detect.
            reference_activated_callback (callable, optional): Function receiving a
                reference dictionary when the user double-clicks a reference.
            reference_kind_labels (dict, optional): Source kind mapped to
                (singular, plural) labels used by the "Used by" summary.
        """
        super().__init__(parent)
        self.refresh_callback = refresh_callback
        self.descriptions = descriptions or {}
        self.custom_description = custom_description
        self.references_callback = references_callback
        self.reference_activated_callback = reference_activated_callback
        self.reference_kind_labels = dict(DEFAULT_REFERENCE_KIND_LABELS)
        self.reference_kind_labels.update(reference_kind_labels or {})
        self._all_values = {}
        self._references_by_token = {}
        self._displayed_references = []
        self._section_width_weights = [230, 300, 400, 200]
        self._adjusting_columns = False
        self.show_references_checkbox = None
        self.used_only_checkbox = None

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

        filter_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.filter_line_edit = ui_qt.QtWidgets.QLineEdit()
        self.filter_line_edit.setPlaceholderText("Filter variables...")
        self.filter_line_edit.textChanged.connect(self.filter_rows)
        filter_layout.addWidget(self.filter_line_edit, 1)
        if self.references_callback is not None:
            self._create_reference_toggles(filter_layout, references_tooltip)
        layout.addLayout(filter_layout)

        self.variable_table = ui_qt.QtWidgets.QTableWidget(0, 4)
        self.variable_table.setHorizontalHeaderLabels(
            ["Token", "Current value", "Description", "Used by"]
        )
        self._configure_read_only_table(self.variable_table)
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
        self.variable_table.itemSelectionChanged.connect(self.update_reference_panel)
        self.variable_table.setColumnHidden(self.USED_BY_COLUMN, True)

        header = self.variable_table.horizontalHeader()
        for column in range(self.variable_table.columnCount()):
            header.setSectionResizeMode(column, ui_qt.QtLib.QHeaderView.Interactive)
        for column, width in enumerate(self._section_width_weights):
            self.variable_table.setColumnWidth(column, width)
        header.sectionResized.connect(self.on_column_resized)

        self.reference_panel = self._create_reference_panel()
        self.content_splitter = ui_qt.QtWidgets.QSplitter(
            self._get_qt_enum(ui_qt.QtCore.Qt, "Orientation", "Vertical")
        )
        self.content_splitter.setChildrenCollapsible(False)
        self.content_splitter.addWidget(self.variable_table)
        self.content_splitter.addWidget(self.reference_panel)
        self.content_splitter.setStretchFactor(0, 3)
        self.content_splitter.setStretchFactor(1, 2)
        self.reference_panel.setVisible(False)
        layout.addWidget(self.content_splitter, 1)

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

    def _create_reference_toggles(self, filter_layout, references_tooltip):
        """Adds the reference checkboxes next to the filter field.

        Args:
            filter_layout (QHBoxLayout): Layout holding the filter field.
            references_tooltip (str): Tooltip describing the reference scan.
        """
        self.show_references_checkbox = ui_qt.QtWidgets.QCheckBox("Show references")
        self.show_references_checkbox.setToolTip(
            references_tooltip
            or "Shows where each variable is used in the current project."
        )
        self.show_references_checkbox.toggled.connect(self.set_references_visible)
        filter_layout.addWidget(self.show_references_checkbox)

        self.used_only_checkbox = ui_qt.QtWidgets.QCheckBox("Used only")
        self.used_only_checkbox.setToolTip(
            "Hides variables that are not referenced by the current project."
        )
        self.used_only_checkbox.setEnabled(False)
        self.used_only_checkbox.toggled.connect(
            lambda checked=False: self.filter_rows(self.filter_line_edit.text())
        )
        filter_layout.addWidget(self.used_only_checkbox)

    def _create_reference_panel(self):
        """Creates the panel listing where the selected variable is used.

        Returns:
            QWidget: Reference panel widget.
        """
        panel = ui_qt.QtWidgets.QWidget()
        panel_layout = ui_qt.QtWidgets.QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 4, 0, 0)
        panel_layout.setSpacing(4)

        self.reference_header_label = ui_qt.QtWidgets.QLabel()
        self.reference_header_label.setWordWrap(True)
        panel_layout.addWidget(self.reference_header_label)

        self.reference_table = ui_qt.QtWidgets.QTableWidget(0, 4)
        self.reference_table.setHorizontalHeaderLabels(["Used by", "Field", "Via", "Text"])
        self._configure_read_only_table(self.reference_table)
        self.reference_table.cellDoubleClicked.connect(self.on_reference_double_clicked)
        reference_header = self.reference_table.horizontalHeader()
        for column in range(self.reference_table.columnCount()):
            reference_header.setSectionResizeMode(column, ui_qt.QtLib.QHeaderView.Interactive)
        reference_header.setStretchLastSection(True)
        for column, width in enumerate((220, 220, 150)):
            self.reference_table.setColumnWidth(column, width)
        panel_layout.addWidget(self.reference_table, 1)
        return panel

    def _configure_read_only_table(self, table):
        """Applies shared read-only, row-selection table settings.

        Args:
            table (QTableWidget): Table to configure.
        """
        table.verticalHeader().hide()
        table.setAlternatingRowColors(True)
        table.setEditTriggers(
            self._get_qt_enum(
                ui_qt.QtWidgets.QAbstractItemView,
                "EditTrigger",
                "NoEditTriggers",
            )
        )
        table.setSelectionBehavior(
            self._get_qt_enum(
                ui_qt.QtWidgets.QAbstractItemView,
                "SelectionBehavior",
                "SelectRows",
            )
        )

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

    def is_showing_references(self):
        """Checks whether the reference column and panel are active.

        Returns:
            bool: True when references are enabled and shown.
        """
        return bool(
            self.show_references_checkbox is not None
            and self.show_references_checkbox.isChecked()
        )

    def get_visible_columns(self):
        """Gets the variable-table columns that are currently shown.

        Returns:
            list: Visible column indices in display order.
        """
        return [
            column
            for column in range(self.variable_table.columnCount())
            if not self.variable_table.isColumnHidden(column)
        ]

    def resizeEvent(self, event):
        """Resizes table columns proportionally when the window changes size.

        Args:
            event (QResizeEvent): Window resize event.
        """
        super().resizeEvent(event)
        if hasattr(self, "variable_table"):
            ui_qt.QtCore.QTimer.singleShot(0, self.resize_table_columns)

    def resize_table_columns(self):
        """Uses the table's full width while preserving visible column proportions."""
        if not hasattr(self, "variable_table"):
            return
        columns = self.get_visible_columns()
        table_width = self.variable_table.viewport().width()
        minimum_width = self.variable_table.horizontalHeader().minimumSectionSize()
        if not columns or table_width < minimum_width * len(columns):
            return

        weights = [self._section_width_weights[column] for column in columns]
        remaining_width = table_width
        remaining_weight = sum(weights)
        widths = {}
        for index, column in enumerate(columns[:-1]):
            sections_remaining = len(columns) - index - 1
            maximum_width = remaining_width - minimum_width * sections_remaining
            width = int(round(remaining_width * weights[index] / remaining_weight))
            width = min(max(minimum_width, width), maximum_width)
            widths[column] = width
            remaining_width -= width
            remaining_weight -= weights[index]
        widths[columns[-1]] = remaining_width
        self.set_column_widths(widths)

    def on_column_resized(self, resized_column, old_width, new_width):
        """Keeps visible columns fitted after a user adjusts a header section.

        Args:
            resized_column (int): Column whose width changed.
            old_width (int): Previous width of the resized column.
            new_width (int): Requested width of the resized column.
        """
        if self._adjusting_columns:
            return
        columns = self.get_visible_columns()
        if resized_column not in columns or len(columns) < 2:
            return
        table_width = self.variable_table.viewport().width()
        header = self.variable_table.horizontalHeader()
        minimum_width = header.minimumSectionSize()
        if table_width < minimum_width * len(columns):
            return

        resized_width = min(
            max(minimum_width, new_width),
            table_width - minimum_width * (len(columns) - 1),
        )
        other_columns = [column for column in columns if column != resized_column]
        other_weights = [header.sectionSize(column) for column in other_columns]
        remaining_width = table_width - resized_width
        remaining_weight = sum(other_weights) or len(other_weights)
        widths = {resized_column: resized_width}

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
        for column, width in widths.items():
            self._section_width_weights[column] = width

    def set_column_widths(self, widths):
        """Sets table column widths without treating them as user adjustments.

        Args:
            widths (dict, list): Widths keyed by column index, or a list in column order.
        """
        if isinstance(widths, (list, tuple)):
            widths = dict(enumerate(widths))
        self._adjusting_columns = True
        try:
            for column, width in widths.items():
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
        reference_error = self.refresh_references() if self.is_showing_references() else ""
        self.populate_table(selected_token=selected_token)
        self.update_result_count()
        if reference_error:
            self.status_label.setText(reference_error)

    def refresh_references(self):
        """Scans the project for variable references using the supplied callback.

        Returns:
            str: Error message when the scan failed, otherwise an empty string.
        """
        if self.references_callback is None:
            return ""
        try:
            references_by_token = self.references_callback()
            if not isinstance(references_by_token, dict):
                raise ValueError("The reference source did not return a dictionary.")
        except Exception as error:
            self._references_by_token = {}
            return f"Unable to find references: {error}"
        self._references_by_token = references_by_token
        return ""

    def set_references_visible(self, visible):
        """Shows or hides the "Used by" column and the reference panel.

        Args:
            visible (bool): Whether references should be displayed.
        """
        reference_error = ""
        if visible:
            reference_error = self.refresh_references()
            self.populate_table(selected_token=self.get_token_for_row())
        self.variable_table.setColumnHidden(self.USED_BY_COLUMN, not visible)
        self.reference_panel.setVisible(bool(visible))
        if self.used_only_checkbox is not None:
            self.used_only_checkbox.setEnabled(bool(visible))
        self.filter_rows(self.filter_line_edit.text())
        self.resize_table_columns()
        self.update_reference_panel()
        if reference_error:
            self.status_label.setText(reference_error)

    def get_references_for_token(self, token):
        """Gets the references found for a table token.

        Args:
            token (str): Braced or unbraced token shown in the table.

        Returns:
            list: Reference dictionaries, or an empty list when unused.
        """
        return list(self._references_by_token.get(core_env_refs.strip_token_braces(token), []))

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
            self.variable_table.setItem(row, self.TOKEN_COLUMN, token_item)
            self.variable_table.setItem(row, self.VALUE_COLUMN, value_item)
            self.variable_table.setItem(row, self.DESCRIPTION_COLUMN, description_item)
            self.variable_table.setItem(row, self.USED_BY_COLUMN, self.build_used_by_item(token))

        self.filter_rows(self.filter_line_edit.text())
        if selected_token:
            for row in range(self.variable_table.rowCount()):
                token_item = self.variable_table.item(row, self.TOKEN_COLUMN)
                if token_item and token_item.text() == selected_token:
                    if not self.variable_table.isRowHidden(row):
                        self.variable_table.selectRow(row)
                    break
        self.update_reference_panel()

    def build_used_by_item(self, token):
        """Builds the "Used by" summary cell for a token.

        Args:
            token (str): Token shown in the row.

        Returns:
            QTableWidgetItem: Summary item, greyed out when the token is unused.
        """
        references = self.get_references_for_token(token)
        summary = core_env_refs.summarize_references(references, self.reference_kind_labels)
        used_by_item = ui_qt.QtWidgets.QTableWidgetItem(summary or "Not used")
        if summary:
            labels = []
            for reference in references:
                if reference["source_label"] not in labels:
                    labels.append(reference["source_label"])
            used_by_item.setToolTip("\n".join(labels))
        else:
            used_by_item.setForeground(ui_qt.QtGui.QColor(145, 145, 145))
            used_by_item.setToolTip("No references were found in the current project.")
        return used_by_item

    def update_reference_panel(self):
        """Lists the references of the selected variable in the reference panel."""
        if not hasattr(self, "reference_table"):
            return
        self.reference_table.setRowCount(0)
        self._displayed_references = []
        if not self.is_showing_references():
            return
        token = self.get_token_for_row()
        if not token:
            self.reference_header_label.setText("Select a variable to see where it is used.")
            return

        references = self.get_references_for_token(token)
        direct_count = sum(1 for reference in references if not reference.get("via"))
        indirect_count = len(references) - direct_count
        if not references:
            self.reference_header_label.setText(
                f"{token} is not used by the current project. "
                "Hover over \"Show references\" for what the scan cannot detect."
            )
            return
        header_text = f"{token}: {direct_count} direct and {indirect_count} indirect use(s)."
        if self.reference_activated_callback is not None:
            header_text += " Double-click a row to select its source."
        self.reference_header_label.setText(header_text)

        disabled_color = ui_qt.QtGui.QColor(145, 145, 145)
        for reference in references:
            row = self.reference_table.rowCount()
            self.reference_table.insertRow(row)
            source_text = reference.get("source_label", "")
            if not reference.get("enabled", True):
                source_text += " (disabled)"
            via_text = " → ".join(f"{{{key}}}" for key in reference.get("via") or []) or "Direct"
            row_items = [
                ui_qt.QtWidgets.QTableWidgetItem(source_text),
                ui_qt.QtWidgets.QTableWidgetItem(self.format_reference_field(reference)),
                ui_qt.QtWidgets.QTableWidgetItem(via_text),
                ui_qt.QtWidgets.QTableWidgetItem(reference.get("snippet", "")),
            ]
            for column, item in enumerate(row_items):
                item.setToolTip(item.text())
                if not reference.get("enabled", True):
                    item.setForeground(disabled_color)
                self.reference_table.setItem(row, column, item)
            self._displayed_references.append(reference)

    @staticmethod
    def format_reference_field(reference):
        """Formats a reference location for display.

        Args:
            reference (dict): Reference dictionary.

        Returns:
            str: Field path with optional line number and use count.
        """
        field_text = reference.get("field") or "<value>"
        details = []
        if reference.get("line", 1) > 1:
            details.append(f"line {reference['line']}")
        if reference.get("count", 1) > 1:
            details.append(f"{reference['count']} uses")
        if details:
            field_text += f" ({', '.join(details)})"
        return field_text

    def on_reference_double_clicked(self, row, column):
        """Forwards a double-clicked reference to the tool.

        Args:
            row (int): Double-clicked reference row.
            column (int): Double-clicked column. Not used.
        """
        if self.reference_activated_callback is None:
            return
        if row < 0 or row >= len(self._displayed_references):
            return
        reference = self._displayed_references[row]
        try:
            self.reference_activated_callback(reference)
        except Exception as error:
            self.status_label.setText(f"Unable to select {reference.get('source_label')}: {error}")
            return
        self.status_label.setText(f"Selected {reference.get('source_label')}.")

    def filter_rows(self, text):
        """Hides rows that do not match the filter text or the "Used only" toggle.

        Args:
            text (str): Filter text.
        """
        needle = str(text or "").casefold()
        used_only = bool(
            self.used_only_checkbox is not None
            and self.used_only_checkbox.isEnabled()
            and self.used_only_checkbox.isChecked()
        )
        searched_columns = [self.TOKEN_COLUMN, self.VALUE_COLUMN, self.DESCRIPTION_COLUMN]
        if self.is_showing_references():
            searched_columns.append(self.USED_BY_COLUMN)
        for row in range(self.variable_table.rowCount()):
            cell_texts = []
            for column in searched_columns:
                item = self.variable_table.item(row, column)
                cell_texts.append(item.text().casefold() if item else "")
            is_hidden = not any(needle in cell_text for cell_text in cell_texts)
            if used_only and not is_hidden:
                is_hidden = not self.get_references_for_token(self.get_token_for_row(row=row))
            self.variable_table.setRowHidden(row, is_hidden)
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
        item = self.variable_table.item(row, self.TOKEN_COLUMN)
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
        if column == self.TOKEN_COLUMN:
            self.copy_token(row=row)
        elif column == self.VALUE_COLUMN:
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
