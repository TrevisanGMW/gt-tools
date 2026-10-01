"""Batch Processor Custom Environment Variables Dialog."""

from functools import partial
import os

from gt.tools.batch_processor import batch_processor_model
from gt.tools.batch_processor import batch_processor_environment_variables as environment_variables
import gt.ui.file_dialog as ui_file_dialog
import gt.ui.qt_import as ui_qt
import gt.ui.resource_library as ui_res_lib


CUSTOM_ENVIRONMENT_VARIABLE_EXAMPLES = [
    {
        "label": "Literal String",
        "name": "{custom-path}",
        "value": "example/custom/path",
        "query": False,
        "tooltip": "A custom environment variable with a fixed path value.",
    },
    {
        "label": "Maya Selection",
        "name": "{maya-selection}",
        "value": "cmds.ls(selection=True)",
        "query": True,
        "tooltip": "Returns the current Maya selection.",
    },
    {
        "label": "Custom Attribute",
        "name": "{custom-attr}",
        "value": "cmds.getAttr('object.attr')",
        "query": True,
        "tooltip": "Returns the object.attr value without processing it.",
    },
    {
        "label": "JSON Attribute",
        "name": "{custom-json-attr}",
        "value": (
            "', '.join(import_module('json').loads("
            "cmds.getAttr('object.attr')))"
        ),
        "query": True,
        "tooltip": "Converts JSON object.attr text into a comma-separated USD attribute list.",
    },
]


class CustomEnvironmentVariablesDialog(ui_qt.QtWidgets.QDialog):
    """Edits project-specific Batch Processor environment variables."""

    def __init__(self, custom_environment_variables=None, parent=None, project=None):
        """Initializes the custom environment-variable editor.

        Args:
            custom_environment_variables (dict, optional): Existing custom
                variable definitions keyed by normalized names.
            parent (QWidget, optional): Parent widget.
            project (BatchProcessorModel, optional): Project context for testing queries.
        """
        super().__init__(parent)
        self.project = project
        self.setWindowTitle("Batch Processor Custom Environment Variables")
        self.setMinimumSize(720, 380)
        self.resize(820, 460)

        layout = ui_qt.QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        description = ui_qt.QtWidgets.QLabel(
            "Add project-specific variables for task templates. Names must use "
            "the {name} format. Query values are evaluated in Maya with cmds, "
            "json, import_module, project, task, and env available."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        self.variable_table = ui_qt.QtWidgets.QTableWidget()
        self.variable_table.setColumnCount(5)
        self.variable_table.setHorizontalHeaderLabels(
            ["Variable", "Value / Python Expression", "Query", "Run", ""]
        )
        self.variable_table.setToolTip(
            "Query expressions run when a task asks for environment values. "
            "Failures are logged and resolve as an empty value."
        )
        self.variable_table.setAlternatingRowColors(True)
        self.variable_table.setContextMenuPolicy(ui_qt.QtCore.Qt.CustomContextMenu)
        self.variable_table.customContextMenuRequested.connect(self.show_variable_context_menu)
        self.variable_context_menu = ui_qt.QtWidgets.QMenu(self)
        self.variable_table.setColumnWidth(0, 170)
        self.variable_table.setColumnWidth(2, 65)
        self.variable_table.setColumnWidth(3, 42)
        self.variable_table.setColumnWidth(4, 42)
        self._configure_table_header()
        layout.addWidget(self.variable_table, 1)

        add_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.examples_menu = ui_qt.QtWidgets.QMenu(self)
        self.examples_button = ui_qt.QtWidgets.QPushButton("Examples  ▼")
        self.examples_button.setMinimumHeight(30)
        self.examples_button.setStyleSheet("padding: 4px 8px;")
        self.examples_button.setToolTip(
            "Add a pre-filled custom environment-variable example."
        )
        self.examples_button.clicked.connect(self.show_examples_menu)
        self.examples_menu.aboutToShow.connect(self.refresh_examples_menu)
        self.add_variable_button = ui_qt.QtWidgets.QPushButton("Add Variable")
        self.add_variable_button.setMinimumHeight(30)
        self.add_variable_button.setStyleSheet("padding: 4px 8px;")
        self.add_variable_button.setToolTip("Add an empty custom environment-variable row.")
        self.add_variable_button.clicked.connect(self.add_variable_row)
        add_layout.addWidget(self.add_variable_button)
        add_layout.addWidget(self.examples_button)
        add_layout.addStretch()
        self.import_variables_button = ui_qt.QtWidgets.QPushButton("Import Variables")
        self.export_variables_button = ui_qt.QtWidgets.QPushButton("Export Variables")
        self.import_variables_button.setToolTip(
            "Import variables from JSON. Existing variable names are skipped."
        )
        self.export_variables_button.setToolTip(
            "Export all current rows, including Query flags, to a JSON file."
        )
        self.import_variables_button.clicked.connect(self.import_variables)
        self.export_variables_button.clicked.connect(self.export_variables)
        for button in (self.import_variables_button, self.export_variables_button):
            button.setMinimumHeight(30)
            button.setStyleSheet("padding: 4px 8px;")
            add_layout.addWidget(button)
        layout.addLayout(add_layout)

        self.status_label = ui_qt.QtWidgets.QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #d77a7a;")
        layout.addWidget(self.status_label)

        buttons_layout = ui_qt.QtWidgets.QHBoxLayout()
        buttons_layout.addStretch()
        cancel_button = ui_qt.QtWidgets.QPushButton("Cancel")
        save_button = ui_qt.QtWidgets.QPushButton("Save")
        cancel_button.setMinimumHeight(32)
        save_button.setMinimumHeight(32)
        cancel_button.clicked.connect(self.reject)
        save_button.clicked.connect(self.save_variables)
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(save_button)
        layout.addLayout(buttons_layout)

        for name, definition in (custom_environment_variables or {}).items():
            definition = definition or {}
            self.add_variable_row(
                name=batch_processor_model.format_environment_key(name),
                value=definition.get("value", ""),
                is_query=definition.get("query", False),
            )

    def _configure_table_header(self):
        """Configures the variable-table header across supported Qt bindings."""
        header = self.variable_table.horizontalHeader()
        row_header = self.variable_table.verticalHeader()
        try:
            header.setSectionResizeMode(1, ui_qt.QtWidgets.QHeaderView.Stretch)
            row_header.setSectionResizeMode(ui_qt.QtWidgets.QHeaderView.ResizeToContents)
        except AttributeError:
            header.setResizeMode(1, ui_qt.QtWidgets.QHeaderView.Stretch)
            row_header.setResizeMode(ui_qt.QtWidgets.QHeaderView.ResizeToContents)

    def show_examples_menu(self, checked=False):
        """Displays the local custom environment-variable examples menu.

        Args:
            checked (bool, optional): Ignored button signal value.
        """
        self.refresh_examples_menu()
        menu_position = self.examples_button.mapToGlobal(
            self.examples_button.rect().bottomLeft()
        )
        if hasattr(self.examples_menu, "exec"):
            self.examples_menu.exec(menu_position)
        else:
            self.examples_menu.exec_(menu_position)

    def refresh_examples_menu(self):
        """Rebuilds the menu from the local custom-variable examples."""
        self.examples_menu.clear()
        for example in CUSTOM_ENVIRONMENT_VARIABLE_EXAMPLES:
            action = self.examples_menu.addAction(example["label"])
            action.setToolTip(example["tooltip"])
            action.triggered.connect(
                partial(self.add_example_variable, example=example)
            )

    def add_example_variable(self, checked=False, example=None):
        """Adds one selected example as a new custom-variable row.

        Args:
            checked (bool, optional): Ignored action signal value.
            example (dict, optional): Definition selected from the examples menu.
        """
        if not example:
            return
        self.add_variable_row(
            name=example.get("name", ""),
            value=example.get("value", ""),
            is_query=example.get("query", False),
        )
        self.variable_table.scrollToBottom()

    def add_variable_row(self, checked=False, name="", value="", is_query=False):
        """Adds one editable custom environment-variable row.

        Args:
            checked (bool, optional): Ignored signal value from the Add button.
            name (str, optional): Initial braced variable name.
            value (str, optional): Initial literal value or query expression.
            is_query (bool, optional): Whether the row evaluates its value.
        """
        row = self.variable_table.rowCount()
        self.variable_table.insertRow(row)
        name_item = ui_qt.QtWidgets.QTableWidgetItem(str(name or ""))
        name_item.setToolTip("Required format: {variable-name}")
        self.variable_table.setItem(row, 0, name_item)
        value_item = ui_qt.QtWidgets.QTableWidgetItem(str(value or ""))
        value_item.setToolTip(
            "Literal text when Query is disabled. A Python expression when Query is enabled. "
            "Use json.loads(cmds.getAttr('node.attribute')) to read JSON text attributes."
        )
        self.variable_table.setItem(row, 1, value_item)

        query_checkbox = ui_qt.QtWidgets.QCheckBox()
        query_checkbox.setStyleSheet(
            "QCheckBox { spacing: 0px; padding: 0px; margin: 0px; } "
            "QCheckBox::indicator { subcontrol-position: center; }"
        )
        query_checkbox.setSizePolicy(ui_qt.QtLib.SizePolicy.Fixed, ui_qt.QtLib.SizePolicy.Fixed)
        query_checkbox.setChecked(bool(is_query))
        query_checkbox.setToolTip(
            "Evaluate the value as a Python expression. Available values include cmds, json, "
            "env, project, and task. Use import_module('module_name') to load a module "
            "inside the expression."
        )
        query_container = ui_qt.QtWidgets.QWidget()
        query_layout = ui_qt.QtWidgets.QHBoxLayout(query_container)
        query_layout.setContentsMargins(0, 0, 0, 0)
        query_layout.setSpacing(0)
        query_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        query_layout.addWidget(query_checkbox)
        self.variable_table.setCellWidget(row, 2, query_container)

        run_button = ui_qt.QtWidgets.QPushButton()
        run_button.setAutoDefault(False)
        run_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.setup_run_only))
        run_button.setIconSize(ui_qt.QtCore.QSize(18, 18))
        run_button.setMinimumWidth(28)
        run_button.setAccessibleName("Run Query")
        run_button.setEnabled(bool(is_query))
        run_button.setToolTip(
            "Run this query in the current Maya scene and print its result. "
            "Uses current editor values and preceding rows; task is None at project level."
        )
        run_button.clicked.connect(partial(self.test_variable_query, name_item=name_item))
        query_checkbox.toggled.connect(run_button.setEnabled)
        self.variable_table.setCellWidget(row, 3, run_button)

        remove_button = ui_qt.QtWidgets.QPushButton()
        remove_button.setAutoDefault(False)
        remove_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_trash))
        remove_button.setIconSize(ui_qt.QtCore.QSize(18, 18))
        remove_button.setMinimumWidth(28)
        remove_button.setAccessibleName("Delete Variable")
        remove_button.setToolTip("Remove this custom environment variable.")
        remove_button.clicked.connect(self.remove_variable_row)
        self.variable_table.setCellWidget(row, 4, remove_button)

    def remove_variable_row(self, checked=False, row=None):
        """Removes the requested row or the row owning the clicked trash button.

        Args:
            checked (bool, optional): Ignored QPushButton signal value.
            row (int, optional): Row requested by the context menu.
        """
        if row is None:
            button = self.sender()
            row = next(
                (index for index in range(self.variable_table.rowCount())
                 if self.variable_table.cellWidget(index, 4) == button),
                -1,
            )
        if 0 <= row < self.variable_table.rowCount():
            self.variable_table.removeRow(row)
            self.set_status("Deleted variable. Click Save to apply.", error=False)

    def test_variable_query(self, checked=False, name_item=None):
        """Evaluates the clicked query and prints its result or error.

        Args:
            checked (bool, optional): Ignored QPushButton signal value.
            name_item (QTableWidgetItem, optional): Stable identity of the tested row.
        """
        row = self.variable_table.row(name_item) if name_item is not None else self.variable_table.currentRow()
        if row < 0 or not self.variable_table.cellWidget(row, 3).isEnabled():
            return
        variables = self.get_custom_environment_variables(rows=range(row + 1))
        if variables is None:
            return
        name = batch_processor_model.normalize_environment_key(self.variable_table.item(row, 0).text())
        try:
            result = environment_variables.evaluate_variable(name, variables, project=self.project)
            message = f"{{{name}}} = {result!r}"
        except Exception as exception:
            message = f"Unable to run {{{name}}}: {exception}"
            self.set_status(message)
            print(f"[Batch Processor] {message}")
            return
        print(f"[Batch Processor] {message}")
        self.set_status(message, error=False)

    def show_variable_context_menu(self, position):
        """Shows row transfer actions, including Paste on an empty table.

        Args:
            position (QPoint): Requested position within the table viewport.
        """
        row = self.variable_table.rowAt(position.y())
        if row >= 0:
            self.variable_table.setCurrentCell(row, 0)
        self.variable_context_menu.clear()
        copy_action = self.variable_context_menu.addAction("Copy Variable")
        copy_action.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_copy_grayscale))
        copy_action.setEnabled(row >= 0)
        copy_action.triggered.connect(partial(self.copy_variable, row=row))
        paste_action = self.variable_context_menu.addAction("Paste Variable")
        paste_action.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_paste_grayscale))
        paste_action.triggered.connect(self.paste_variable)
        duplicate_action = self.variable_context_menu.addAction("Duplicate Variable")
        duplicate_action.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_duplicate_grayscale))
        duplicate_action.setEnabled(row >= 0)
        duplicate_action.triggered.connect(partial(self.duplicate_variable, row=row))
        self.variable_context_menu.addSeparator()
        delete_action = self.variable_context_menu.addAction("Delete Variable")
        delete_action.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_trash))
        delete_action.setEnabled(row >= 0)
        delete_action.triggered.connect(partial(self.remove_variable_row, row=row))
        self.variable_context_menu.popup(self.variable_table.viewport().mapToGlobal(position))

    def copy_variable(self, checked=False, row=None):
        """Copies one complete variable definition to the system clipboard.

        Args:
            checked (bool, optional): Ignored action signal value.
            row (int, optional): Row to copy, or the current row when omitted.
        """
        row = self.variable_table.currentRow() if row is None else row
        if row < 0 or row >= self.variable_table.rowCount():
            self.set_status("Select a variable to copy.")
            return
        variables = self.get_custom_environment_variables(rows=[row])
        if not variables:
            if variables is not None:
                self.set_status("The selected row is empty.")
            return
        ui_qt.QtWidgets.QApplication.clipboard().setText(
            environment_variables.serialize_variables(variables)
        )
        self.set_status("Copied variable to clipboard.", error=False)

    def paste_variable(self, checked=False):
        """Appends a copied row, assigning a fresh name if it already exists.

        Args:
            checked (bool, optional): Ignored action signal value.
        """
        try:
            variables = environment_variables.deserialize_variables(
                ui_qt.QtWidgets.QApplication.clipboard().text()
            )
            if len(variables) != 1:
                raise ValueError("Copy a single variable row before pasting.")
        except ValueError as exception:
            self.set_status(f"Unable to paste variable: {exception}")
            return
        self._append_variable_copy(variables, action="Pasted")

    def duplicate_variable(self, checked=False, row=None):
        """Duplicates a validated row without changing the system clipboard.

        Args:
            checked (bool, optional): Ignored action signal value.
            row (int, optional): Row to duplicate, or the current row when omitted.
        """
        row = self.variable_table.currentRow() if row is None else row
        if row < 0 or row >= self.variable_table.rowCount():
            self.set_status("Select a variable to duplicate.")
            return
        variables = self.get_custom_environment_variables(rows=[row])
        if variables:
            self._append_variable_copy(variables, action="Duplicated")
        elif variables is not None:
            self.set_status("The selected row is empty.")

    def _append_variable_copy(self, variables, action):
        """Appends one transferred definition with a unique name.

        Args:
            variables (dict): One validated variable definition.
            action (str): Completed action to report in the status field.
        """
        name, definition = next(iter(variables.items()))
        existing_names = {
            batch_processor_model.normalize_environment_key(self.variable_table.item(row, 0).text())
            for row in range(self.variable_table.rowCount())
            if self.variable_table.item(row, 0)
        }
        pasted_name = name
        suffix = 1
        while pasted_name in existing_names:
            pasted_name = f"{name}-copy" if suffix == 1 else f"{name}-copy-{suffix}"
            suffix += 1
        self.add_variable_row(
            name=batch_processor_model.format_environment_key(pasted_name),
            value=definition["value"],
            is_query=definition["query"],
        )
        self.variable_table.setCurrentCell(self.variable_table.rowCount() - 1, 0)
        self.variable_table.scrollToBottom()
        self.set_status(f"{action} {{{pasted_name}}}. Click Save to apply.", error=False)

    def import_variables(self, checked=False):
        """Imports missing definitions, leaving existing rows intact.

        Args:
            checked (bool, optional): Ignored button signal value.
        """
        existing_variables = self.get_custom_environment_variables()
        if existing_variables is None:
            return
        file_path = ui_file_dialog.file_dialog(
            parent=self,
            caption="Import Custom Variables",
            file_filter="Custom Variables (*.json);;",
            ok_caption="Import",
        )
        if not file_path:
            return
        try:
            variables = environment_variables.read_variables(file_path)
        except (OSError, ValueError) as exception:
            self.set_status(f"Unable to import variables: {exception}")
            return
        added_count = 0
        for name, definition in variables.items():
            if name in existing_variables:
                continue
            self.add_variable_row(
                name=batch_processor_model.format_environment_key(name),
                value=definition["value"],
                is_query=definition["query"],
            )
            added_count += 1
        skipped_count = len(variables) - added_count
        self.set_status(
            f"Imported {added_count} variable(s); skipped {skipped_count} existing name(s). "
            "Click Save to apply.",
            error=False,
        )

    def export_variables(self, checked=False):
        """Exports validated editor contents through the standard file dialog.

        Args:
            checked (bool, optional): Ignored button signal value.
        """
        variables = self.get_custom_environment_variables()
        if variables is None:
            return
        file_path = ui_file_dialog.file_dialog(
            parent=self,
            caption="Export Custom Variables",
            write_mode=True,
            starting_directory="custom_variables.json",
            file_filter="Custom Variables (*.json);;",
            ok_caption="Export",
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".json"):
            file_path += ".json"
            if os.path.exists(file_path):
                response = ui_qt.QtWidgets.QMessageBox.question(
                    self, "Replace Variables File?", f'Replace the existing file?\n{file_path}',
                    ui_qt.QtWidgets.QMessageBox.Yes | ui_qt.QtWidgets.QMessageBox.No,
                    ui_qt.QtWidgets.QMessageBox.No,
                )
                if response != ui_qt.QtWidgets.QMessageBox.Yes:
                    return
        try:
            environment_variables.write_variables(file_path, variables)
        except (OSError, ValueError) as exception:
            self.set_status(f"Unable to export variables: {exception}")
            return
        self.set_status(f"Exported {len(variables)} variable(s) to: {file_path}", error=False)

    def get_custom_environment_variables(self, rows=None):
        """Builds validated custom environment-variable definitions from the table.

        Args:
            rows (iterable, optional): Specific row indices, or all rows when omitted.

        Returns:
            dict or None: Normalized variable definitions, or None when a row
            has invalid data.
        """
        variables = {}
        for row in range(self.variable_table.rowCount()) if rows is None else rows:
            name_item = self.variable_table.item(row, 0)
            value_item = self.variable_table.item(row, 1)
            name = name_item.text().strip() if name_item else ""
            value = value_item.text() if value_item else ""
            query_container = self.variable_table.cellWidget(row, 2)
            query_checkbox = query_container.findChild(ui_qt.QtWidgets.QCheckBox)
            is_query = query_checkbox.isChecked() if query_checkbox else False
            if not name and not value and not is_query:
                continue
            if not batch_processor_model.is_valid_custom_environment_name(name):
                self.set_status(
                    f'Row {row + 1}: Variable names must use the pattern {{name}}.'
                )
                return None
            if not batch_processor_model.BatchProcessorModel.is_custom_environment_name_available(name):
                self.set_status(f'Row {row + 1}: "{name}" is reserved by Batch Processor.')
                return None
            normalized_name = batch_processor_model.normalize_environment_key(name)
            if normalized_name in variables:
                self.set_status(f'Row {row + 1}: "{name}" is defined more than once.')
                return None
            variables[normalized_name] = {"value": value, "query": is_query}
        return variables

    def save_variables(self):
        """Validates editor rows and accepts the dialog when they are valid."""
        if self.get_custom_environment_variables() is not None:
            self.accept()

    def set_status(self, message, error=True):
        """Shows an in-dialog validation message.

        Args:
            message (str): Message to display.
            error (bool, optional): Whether to use validation error styling.
        """
        self.status_label.setStyleSheet("color: #d77a7a;" if error else "")
        self.status_label.setText(str(message or ""))
