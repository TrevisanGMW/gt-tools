"""Batch Processor Custom Environment Variables Dialog."""

from functools import partial

from gt.tools.batch_processor import batch_processor_model
import gt.ui.qt_import as ui_qt


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

    def __init__(self, custom_environment_variables=None, parent=None):
        """Initializes the custom environment-variable editor.

        Args:
            custom_environment_variables (dict, optional): Existing custom
                variable definitions keyed by normalized names.
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)
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
        self.variable_table.setColumnCount(4)
        self.variable_table.setHorizontalHeaderLabels(
            ["Variable", "Value / Python Expression", "Query", ""]
        )
        self.variable_table.setToolTip(
            "Query expressions run when a task asks for environment values. "
            "Failures are logged and resolve as an empty value."
        )
        self.variable_table.setAlternatingRowColors(True)
        self.variable_table.setColumnWidth(0, 170)
        self.variable_table.setColumnWidth(2, 65)
        self.variable_table.setColumnWidth(3, 42)
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
        try:
            header.setSectionResizeMode(1, ui_qt.QtWidgets.QHeaderView.Stretch)
        except AttributeError:
            header.setResizeMode(1, ui_qt.QtWidgets.QHeaderView.Stretch)

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
        query_checkbox.setChecked(bool(is_query))
        query_checkbox.setToolTip(
            "Evaluate the value as a Python expression. Available values include cmds, json, "
            "env, project, and task. Use import_module('module_name') to load a module "
            "inside the expression."
        )
        query_container = ui_qt.QtWidgets.QWidget()
        query_layout = ui_qt.QtWidgets.QHBoxLayout(query_container)
        query_layout.setContentsMargins(0, 0, 0, 0)
        query_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        query_layout.addWidget(query_checkbox)
        self.variable_table.setCellWidget(row, 2, query_container)

        remove_button = ui_qt.QtWidgets.QPushButton("X")
        remove_button.setMinimumWidth(28)
        remove_button.setToolTip("Remove this custom environment variable.")
        remove_button.clicked.connect(self.remove_variable_row)
        self.variable_table.setCellWidget(row, 3, remove_button)

    def remove_variable_row(self, checked=False):
        """Removes the table row that owns the clicked remove button.

        Args:
            checked (bool, optional): Ignored QPushButton signal value.
        """
        button = self.sender()
        for row in range(self.variable_table.rowCount()):
            if self.variable_table.cellWidget(row, 3) == button:
                self.variable_table.removeRow(row)
                return

    def get_custom_environment_variables(self):
        """Builds validated custom environment-variable definitions from the table.

        Returns:
            dict or None: Normalized variable definitions, or None when a row
            has invalid data.
        """
        variables = {}
        for row in range(self.variable_table.rowCount()):
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

    def set_status(self, message):
        """Shows an in-dialog validation message.

        Args:
            message (str): Message to display.
        """
        self.status_label.setText(str(message or ""))
