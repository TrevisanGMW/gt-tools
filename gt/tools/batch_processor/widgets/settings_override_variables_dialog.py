"""Batch Processor Settings Override Custom Variables Dialog."""

from functools import partial

from gt.tools.batch_processor import batch_processor_model
from gt.tools.batch_processor import batch_processor_run_settings as run_settings
from gt.tools.batch_processor.widgets.custom_environment_variables_dialog import CustomEnvironmentVariablesDialog
import gt.ui.qt_import as ui_qt

COLUMN_VARIABLE = 0
COLUMN_VALUE = 1
COLUMN_QUERY = 2
COLUMN_UNSET = 5
COLUMN_STATE = 6

STATE_COLORS = {
    "new": "#7fbf7f",
    "overrides": "#e0b050",
    "same": "grey",
    "removes": "#d77a7a",
    "ignored": "grey",
    "invalid": "#d77a7a",
}


class SettingsOverrideVariablesDialog(CustomEnvironmentVariablesDialog):
    """Edits the custom variables a "Settings Override" task sets or unsets.

    It extends the project's Custom Variables editor with an Unset column, a state
    flag that shows whether each row is new or overrides an existing variable, and a
    menu to add existing variables as starting points.
    """

    def __init__(self, override_rows=None, existing_variables=None, parent=None, project=None):
        """Initializes the override editor.

        Args:
            override_rows (list, optional): Saved rows with "name", "value", "query" and "action" keys.
            existing_variables (dict, optional): Variables already defined where this task runs
                (project definitions plus earlier overrides), keyed by normalized name.
            parent (QWidget, optional): Parent widget.
            project (BatchProcessorModel, optional): Project context for testing queries.
        """
        super().__init__(custom_environment_variables=None, parent=parent, project=project)
        self.existing_variables = {name: dict(definition) for name, definition in (existing_variables or {}).items()}
        self._suspend_refresh = False
        self.setWindowTitle("Settings Override Custom Variables")
        self.variable_table.setColumnCount(7)
        self.variable_table.setHorizontalHeaderLabels(
            ["Variable", "Value / Python Expression", "Query", "Run", "", "Unset", "State"]
        )
        self.variable_table.setColumnWidth(COLUMN_UNSET, 55)
        self.variable_table.setColumnWidth(COLUMN_STATE, 150)
        self.variable_table.itemChanged.connect(self.refresh_row_states)
        self._add_override_note()
        self._add_existing_variables_button()
        for name, entry in run_settings.normalize_custom_variable_overrides(override_rows).items():
            self.add_variable_row(
                name=batch_processor_model.format_environment_key(name),
                value=entry.get("value", ""),
                is_query=entry.get("query", False),
                unset=entry.get("action") == run_settings.CUSTOM_VARIABLE_UNSET,
            )
        self.refresh_row_states()

    def _add_override_note(self):
        """Adds a note explaining how the rows are applied."""
        note = ui_qt.QtWidgets.QLabel(
            "Rows apply when this task's segment starts and stay active for the rest of the run. "
            "A row with an existing name overrides it, a new name adds a variable, and Unset removes one. "
            "The project's saved variables are never changed."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: grey;")
        self.layout().insertWidget(1, note)

    def _add_existing_variables_button(self):
        """Adds the menu button that copies existing variables into the table."""
        self.existing_menu = ui_qt.QtWidgets.QMenu(self)
        self.existing_button = ui_qt.QtWidgets.QPushButton("Add Existing  ▼")
        self.existing_button.setMinimumHeight(30)
        self.existing_button.setStyleSheet("padding: 4px 8px;")
        self.existing_button.setToolTip(
            "Add an existing variable as a row, pre-filled with its current value.\n"
            "Edit the value to override it, or tick Unset to remove it."
        )
        self.existing_button.clicked.connect(self.show_existing_menu)
        self.existing_menu.aboutToShow.connect(self.refresh_existing_menu)
        for index in range(self.layout().count()):
            item_layout = self.layout().itemAt(index).layout()
            if item_layout is not None and item_layout.indexOf(self.examples_button) >= 0:
                item_layout.insertWidget(item_layout.indexOf(self.examples_button) + 1, self.existing_button)
                return

    def show_existing_menu(self, checked=False):
        """Displays the menu of existing variables.

        Args:
            checked (bool, optional): Ignored button signal value.
        """
        self.refresh_existing_menu()
        menu_position = self.existing_button.mapToGlobal(self.existing_button.rect().bottomLeft())
        if hasattr(self.existing_menu, "exec"):
            self.existing_menu.exec(menu_position)
        else:
            self.existing_menu.exec_(menu_position)

    def refresh_existing_menu(self):
        """Rebuilds the menu from the existing variables, disabling names already in the table."""
        self.existing_menu.clear()
        if not self.existing_variables:
            self.existing_menu.addAction("No existing variables").setEnabled(False)
            return
        used_names = set(self._get_table_names())
        add_all_action = self.existing_menu.addAction("Add All Existing")
        add_all_action.setEnabled(any(name not in used_names for name in self.existing_variables))
        add_all_action.triggered.connect(self.add_all_existing_variables)
        self.existing_menu.addSeparator()
        for name, definition in self.existing_variables.items():
            action = self.existing_menu.addAction(batch_processor_model.format_environment_key(name))
            action.setEnabled(name not in used_names)
            action.setToolTip(f"{'Query' if definition.get('query') else 'Value'}: {definition.get('value', '')}")
            action.triggered.connect(partial(self.add_existing_variable, name=name))

    def add_existing_variable(self, checked=False, name=""):
        """Adds one existing variable as a row.

        Args:
            checked (bool, optional): Ignored action signal value.
            name (str, optional): Normalized name of the existing variable.
        """
        definition = self.existing_variables.get(name)
        if definition is None or name in self._get_table_names():
            return
        self.add_variable_row(
            name=batch_processor_model.format_environment_key(name),
            value=definition.get("value", ""),
            is_query=definition.get("query", False),
        )
        self.variable_table.scrollToBottom()

    def add_all_existing_variables(self, checked=False):
        """Adds every existing variable that is not already in the table.

        Args:
            checked (bool, optional): Ignored action signal value.
        """
        for name in self.existing_variables:
            self.add_existing_variable(name=name)

    def add_variable_row(self, checked=False, name="", value="", is_query=False, unset=False):
        """Adds one editable override row with Unset and State columns.

        Args:
            checked (bool, optional): Ignored signal value from the Add button.
            name (str, optional): Initial braced variable name.
            value (str, optional): Initial literal value or query expression.
            is_query (bool, optional): Whether the row evaluates its value.
            unset (bool, optional): Whether the row removes the variable.
        """
        self._suspend_refresh = True
        try:
            super().add_variable_row(name=name, value=value, is_query=is_query)
            row = self.variable_table.rowCount() - 1
            unset_checkbox = ui_qt.QtWidgets.QCheckBox()
            unset_checkbox.setChecked(bool(unset))
            unset_checkbox.setToolTip("Remove this variable instead of setting it.")
            unset_container = ui_qt.QtWidgets.QWidget()
            unset_layout = ui_qt.QtWidgets.QHBoxLayout(unset_container)
            unset_layout.setContentsMargins(0, 0, 0, 0)
            unset_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
            unset_layout.addWidget(unset_checkbox)
            self.variable_table.setCellWidget(row, COLUMN_UNSET, unset_container)
            state_label = ui_qt.QtWidgets.QLabel()
            state_label.setContentsMargins(6, 0, 6, 0)
            self.variable_table.setCellWidget(row, COLUMN_STATE, state_label)
            unset_checkbox.toggled.connect(self.refresh_row_states)
            self._get_row_checkbox(row, COLUMN_QUERY).toggled.connect(self.refresh_row_states)
        finally:
            self._suspend_refresh = False
        self.refresh_row_states()

    def remove_variable_row(self, checked=False, row=None):
        """Removes a row and refreshes the state flags.

        Args:
            checked (bool, optional): Ignored QPushButton signal value.
            row (int, optional): Row requested by the context menu.
        """
        super().remove_variable_row(checked=checked, row=row)
        self.refresh_row_states()

    def _get_row_checkbox(self, row, column):
        """Gets the checkbox stored in a centered cell container.

        Args:
            row (int): Table row.
            column (int): Table column.

        Returns:
            QCheckBox or None: Checkbox in the cell.
        """
        container = self.variable_table.cellWidget(row, column)
        return container.findChild(ui_qt.QtWidgets.QCheckBox) if container else None

    def _read_row(self, row):
        """Reads one table row without validating it.

        Args:
            row (int): Table row.

        Returns:
            dict: "name" (raw text), "value", "query" and "unset".
        """
        name_item = self.variable_table.item(row, COLUMN_VARIABLE)
        value_item = self.variable_table.item(row, COLUMN_VALUE)
        query_checkbox = self._get_row_checkbox(row, COLUMN_QUERY)
        unset_checkbox = self._get_row_checkbox(row, COLUMN_UNSET)
        return {
            "name": name_item.text().strip() if name_item else "",
            "value": value_item.text() if value_item else "",
            "query": bool(query_checkbox and query_checkbox.isChecked()),
            "unset": bool(unset_checkbox and unset_checkbox.isChecked()),
        }

    def _get_table_names(self):
        """Gets the normalized names of the valid rows.

        Returns:
            list: Normalized names in table order.
        """
        names = []
        for row in range(self.variable_table.rowCount()):
            raw_name = self._read_row(row)["name"]
            if batch_processor_model.is_valid_custom_environment_name(raw_name):
                names.append(batch_processor_model.normalize_environment_key(raw_name))
        return names

    def get_row_state(self, row_data):
        """Classifies a row against the existing variables.

        Args:
            row_data (dict): Row data from ``_read_row``.

        Returns:
            tuple: (state key, readable text, tooltip).
        """
        raw_name = row_data["name"]
        if not raw_name and not row_data["value"] and not row_data["query"] and not row_data["unset"]:
            return "", "", ""
        braced_name = raw_name
        if not batch_processor_model.is_valid_custom_environment_name(braced_name) or not (
            batch_processor_model.BatchProcessorModel.is_custom_environment_name_available(braced_name)
        ):
            return "invalid", "Invalid or reserved name", "Names must use the {name} format and not be built in."
        name = batch_processor_model.normalize_environment_key(raw_name)
        existing = self.existing_variables.get(name)
        if row_data["unset"]:
            if existing is None:
                return "ignored", "Not defined, no effect", "This variable does not exist, so unsetting it does nothing."
            return "removes", "Removes existing", f"Existing value: {existing.get('value', '')}"
        if existing is None:
            return "new", "New variable", "This variable does not exist yet."
        tooltip = f"Existing {'query' if existing.get('query') else 'value'}: {existing.get('value', '')}"
        if (existing.get("value", ""), bool(existing.get("query"))) == (row_data["value"], row_data["query"]):
            return "same", "Same as existing", tooltip
        return "overrides", "Overrides existing", tooltip

    def refresh_row_states(self, *args):
        """Updates every row's State column, editability, and the summary line.

        Args:
            *args: Ignored signal values.
        """
        if self._suspend_refresh:
            return
        for row in range(self.variable_table.rowCount()):
            row_data = self._read_row(row)
            state_label = self.variable_table.cellWidget(row, COLUMN_STATE)
            if state_label is None:
                continue
            state_key, text, tooltip = self.get_row_state(row_data)
            state_label.setText(text)
            state_label.setToolTip(tooltip)
            state_label.setStyleSheet(f"color: {STATE_COLORS.get(state_key, 'grey')};")
            self._set_row_editable(row, not row_data["unset"])
        rows = self._collect_rows()
        summary = run_settings.summarize_custom_variable_overrides(
            self.existing_variables, run_settings.normalize_custom_variable_overrides(rows)
        )
        self.set_status(run_settings.format_custom_variable_summary(summary), error=False)

    def _set_row_editable(self, row, editable):
        """Enables or disables the value editing of a row.

        Args:
            row (int): Table row.
            editable (bool): Whether the value and query can be edited.
        """
        value_item = self.variable_table.item(row, COLUMN_VALUE)
        if value_item is not None:
            flags = value_item.flags()
            if editable:
                flags = flags | ui_qt.QtCore.Qt.ItemIsEditable
            else:
                flags = flags & ~ui_qt.QtCore.Qt.ItemIsEditable
            if flags != value_item.flags():
                self._suspend_refresh = True
                value_item.setFlags(flags)
                self._suspend_refresh = False
        query_container = self.variable_table.cellWidget(row, COLUMN_QUERY)
        if query_container is not None:
            query_container.setEnabled(editable)

    def _collect_rows(self):
        """Builds override rows from the table without validating them.

        Returns:
            list: Rows with "name", "value", "query" and "action" keys, skipping empty rows.
        """
        rows = []
        for row in range(self.variable_table.rowCount()):
            row_data = self._read_row(row)
            if not (row_data["name"] or row_data["value"] or row_data["query"] or row_data["unset"]):
                continue
            rows.append(
                {
                    "name": row_data["name"],
                    "value": row_data["value"],
                    "query": row_data["query"],
                    "action": run_settings.CUSTOM_VARIABLE_UNSET if row_data["unset"]
                    else run_settings.CUSTOM_VARIABLE_SET,
                }
            )
        return rows

    def get_override_rows(self):
        """Builds validated override rows from the table.

        Returns:
            list or None: Rows with "name" (braced), "value", "query" and "action" keys in
                table order, or None when a row is invalid.
        """
        if self.get_custom_environment_variables() is None:
            return None
        rows = []
        for row in self._collect_rows():
            row["name"] = batch_processor_model.format_environment_key(row["name"])
            rows.append(row)
        return rows
