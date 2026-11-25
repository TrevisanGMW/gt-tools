"""Attribute picking and read-only operation preview dialogs."""

import gt.ui.qt_import as ui_qt
import gt.ui.resource_library as ui_res_lib


class AttributeBrowserDialog(ui_qt.QtWidgets.QDialog):
    """Picks existing attribute names for a source or target field."""

    attributes_requested = ui_qt.QtCore.Signal(str, bool)
    attributes_applied = ui_qt.QtCore.Signal(list)

    def __init__(self, nodes, role="source", keyable=False, parent=None):
        """Builds a browser with an explicit object and attribute filter.

        Args:
            nodes (list): Objects available for inspection.
            role (str, optional): Source, target or legacy copy-only mode.
            keyable (bool, optional): Whether to initially show keyable attributes.
            parent (QWidget, optional): Parent window.
        """
        super().__init__(parent)
        self.role = role
        self.setAttribute(ui_qt.QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Choose Source Attribute" if role == "source" else "Choose Target Attributes")
        self.resize(420, 500)
        layout = ui_qt.QtWidgets.QVBoxLayout(self)
        layout.setSpacing(8)
        self.node_combo = ui_qt.QtWidgets.QComboBox()
        self.node_combo.addItems(nodes)
        self.node_combo.setToolTip("Object whose existing attributes are listed below.")
        layout.addWidget(ui_qt.QtWidgets.QLabel("Inspect object"))
        layout.addWidget(self.node_combo)
        self.attribute_filter = ui_qt.QtWidgets.QComboBox()
        self.attribute_filter.addItems(["All attributes", "Keyable only"])
        self.attribute_filter.setCurrentIndex(1 if keyable else 0)
        layout.addWidget(self.attribute_filter)
        self.search_field = ui_qt.QtWidgets.QLineEdit()
        self.search_field.setPlaceholderText("Filter attribute names...")
        layout.addWidget(self.search_field)
        self.attribute_list = ui_qt.QtWidgets.QListWidget()
        selection_mode = (
            ui_qt.QtWidgets.QAbstractItemView.SingleSelection if role == "source"
            else ui_qt.QtWidgets.QAbstractItemView.ExtendedSelection
        )
        self.attribute_list.setSelectionMode(selection_mode)
        layout.addWidget(self.attribute_list, 1)
        self.status_label = ui_qt.QtWidgets.QLabel()
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        hint_text = "Choose a name for the source attribute field."
        if role == "target":
            hint_text = "Ctrl/Shift selects multiple names. Names apply to every target object."
        hint = ui_qt.QtWidgets.QLabel(f"{hint_text} Missing attributes are reported in Preview.")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        buttons = ui_qt.QtWidgets.QHBoxLayout()
        action_names = {
            "source": "Set Source Attribute", "target": "Add Target Attributes", "copy": "Copy Names",
        }
        self.apply_button = ui_qt.QtWidgets.QPushButton(action_names.get(role, "Copy Names"))
        self.apply_button.setEnabled(False)
        close_button = ui_qt.QtWidgets.QPushButton("Close")
        buttons.addWidget(self.apply_button, 1)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)
        self.node_combo.currentTextChanged.connect(self.request_attributes)
        self.attribute_filter.currentIndexChanged.connect(self.request_attributes)
        self.search_field.textChanged.connect(self.filter_attributes)
        self.attribute_list.itemSelectionChanged.connect(self._update_apply_button)
        self.attribute_list.itemDoubleClicked.connect(self.apply_selection)
        self.apply_button.clicked.connect(self.apply_selection)
        close_button.clicked.connect(self.close)

    def request_attributes(self, *args):
        """Asks the controller to read attributes for the selected object.

        Args:
            *args: Ignored Qt signal values.
        """
        self.attributes_requested.emit(
            self.node_combo.currentText(), self.attribute_filter.currentIndex() == 1,
        )

    def set_attributes(self, attributes, message=""):
        """Replaces the available names without changing the text filter.

        Args:
            attributes (list): Existing attribute names on the selected node.
            message (str, optional): Error or empty-list explanation.
        """
        self.attribute_list.clear()
        self.attribute_list.addItems(attributes)
        self.status_label.setText(message or f"{len(attributes)} attribute(s) available.")
        self.filter_attributes(self.search_field.text())

    def filter_attributes(self, text):
        """Filters names and clears selection for hidden items.

        Args:
            text (str): Case-insensitive name filter.
        """
        for index in range(self.attribute_list.count()):
            item = self.attribute_list.item(index)
            hidden = text.lower() not in item.text().lower()
            if hidden:
                item.setSelected(False)
            item.setHidden(hidden)
        self._update_apply_button()

    def _update_apply_button(self):
        """Enables the action only when visible attributes are selected."""
        self.apply_button.setEnabled(bool(self.attribute_list.selectedItems()))

    def apply_selection(self, *args):
        """Copies or applies selected names without modifying Maya objects.

        Args:
            *args: Ignored Qt signal values.
        """
        names = [item.text() for item in self.attribute_list.selectedItems() if not item.isHidden()]
        if not names:
            return
        if self.role == "copy":
            ui_qt.QtWidgets.QApplication.clipboard().setText(", ".join(names))
        else:
            self.attributes_applied.emit(names)
        self.status_label.setText(f"Selected: {', '.join(names)}")


class ConnectionPreviewDialog(ui_qt.QtWidgets.QDialog):
    """Shows inspected scene operations, warnings and blocking issues."""

    refresh_requested = ui_qt.QtCore.Signal()
    STATUS_LABELS = {
        "ready": "Ready", "warning": "Warning", "blocked": "Blocked", "skipped": "No change",
    }
    STATUS_COLORS = {
        "ready": "#8BCB88", "warning": "#E2BE72", "blocked": "#E58A8A", "skipped": "#B8B8B8",
    }

    def __init__(self, parent=None):
        """Builds a searchable table and manual refresh controls.

        Args:
            parent (QWidget, optional): Parent window.
        """
        super().__init__(parent)
        self.setAttribute(ui_qt.QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Connect Attributes Preview")
        self.resize(1000, 480)
        layout = ui_qt.QtWidgets.QVBoxLayout(self)
        self.summary_label = ui_qt.QtWidgets.QLabel()
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)
        self.context_label = ui_qt.QtWidgets.QLabel()
        self.context_label.setWordWrap(True)
        layout.addWidget(self.context_label)
        filters = ui_qt.QtWidgets.QHBoxLayout()
        self.search_field = ui_qt.QtWidgets.QLineEdit()
        self.search_field.setPlaceholderText("Filter source, target or details...")
        self.status_filter = ui_qt.QtWidgets.QComboBox()
        for label, status in (
            ("All operations", ""), ("Blocked", "blocked"), ("Warnings", "warning"),
            ("No change", "skipped"), ("Ready", "ready"),
        ):
            self.status_filter.addItem(label, status)
        filters.addWidget(self.search_field, 1)
        filters.addWidget(self.status_filter)
        layout.addLayout(filters)
        self.table = ui_qt.QtWidgets.QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Source", "Via", "Target", "Status", "Details"])
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(ui_qt.QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(ui_qt.QtWidgets.QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            ui_res_lib.Stylesheet.table_widget_base
            + "QTableWidget { alternate-background-color: #353535; }"
        )
        header = self.table.horizontalHeader()
        header.setSortIndicator(-1, ui_qt.QtCore.Qt.AscendingOrder)
        for column in (0, 1, 2):
            header.setSectionResizeMode(column, ui_qt.QtLib.QHeaderView.Interactive)
            self.table.setColumnWidth(column, 200)
        header.setSectionResizeMode(3, ui_qt.QtLib.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, ui_qt.QtLib.QHeaderView.Stretch)
        layout.addWidget(self.table, 1)
        note = ui_qt.QtWidgets.QLabel(
            "Read-only snapshot. Refresh reads the current fields and object mode again. "
            "Run rechecks the scene, runs available operations and reports blocked items."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons = ui_qt.QtWidgets.QHBoxLayout()
        self.refresh_button = ui_qt.QtWidgets.QPushButton("Refresh")
        close_button = ui_qt.QtWidgets.QPushButton("Close")
        buttons.addWidget(self.refresh_button)
        buttons.addStretch()
        buttons.addWidget(close_button)
        layout.addLayout(buttons)
        self.search_field.textChanged.connect(self.filter_rows)
        self.status_filter.currentIndexChanged.connect(self.filter_rows)
        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        close_button.clicked.connect(self.close)

    def set_preview(self, rows, request, issues=None):
        """Displays a new snapshot while preserving filters and column widths.

        Args:
            rows (list): Structured inspection rows.
            request (dict): Settings and objects used for this snapshot.
            issues (list, optional): Request-level issues preventing inspection.
        """
        counts = {status: 0 for status in self.STATUS_LABELS}
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            status = row["status"]
            counts[status] += 1
            status_label = self.STATUS_LABELS[status]
            if status == "warning" and row["details"].startswith("Will replace:"):
                status_label = "Will replace"
            values = [row["source"], row["via"], row["target"], status_label, row["details"]]
            for column, value in enumerate(values):
                item = ui_qt.QtWidgets.QTableWidgetItem(value)
                item.setToolTip(value)
                self.table.setItem(row_index, column, item)
            status_item = self.table.item(row_index, 3)
            status_item.setData(ui_qt.QtLib.ItemDataRole.UserRole, status)
            status_item.setForeground(ui_qt.QtGui.QColor(self.STATUS_COLORS[status]))
        self.table.setColumnHidden(1, not any(row["via"] for row in rows))
        self.table.setSortingEnabled(True)
        self.table.resizeRowsToContents()
        operation = "Connect" if request.get("operation") == "connect" else "Disconnect incoming"
        self.setWindowTitle(f"{operation} Preview")
        self.summary_label.setText(
            " ".join(issues) if issues else (
                f"{len(rows)} operation(s): {counts['ready']} ready, {counts['warning']} warning(s), "
                f"{counts['blocked']} blocked, {counts['skipped']} no change."
            )
        )
        mode = "Current Selection" if request.get("use_selection") else "Loaded Objects"
        context = f"{operation} | {mode} | {len(request.get('target_objects', []))} target object(s)"
        if request.get("use_utility_node") and request.get("use_shared_input") and operation == "Connect":
            context += f" | Shared secondary input: {request.get('shared_input_node_type')}"
        self.context_label.setText(context)
        self.filter_rows()

    def filter_rows(self, *args):
        """Applies the text and status filters to the displayed table.

        Args:
            *args: Ignored Qt signal values.
        """
        text = self.search_field.text().lower()
        status = self.status_filter.currentData()
        for row_index in range(self.table.rowCount()):
            row_status = self.table.item(row_index, 3).data(ui_qt.QtLib.ItemDataRole.UserRole)
            row_text = " ".join(self.table.item(row_index, column).text() for column in range(5))
            self.table.setRowHidden(
                row_index, (bool(status) and status != row_status) or text not in row_text.lower(),
            )
