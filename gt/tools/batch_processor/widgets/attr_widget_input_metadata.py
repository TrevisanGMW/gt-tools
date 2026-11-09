"""Slot naming and per-input value table for the Batch Processor Input Metadata task."""

import json
import os
from functools import partial
from gt.ui import qt_import as qt
from gt.ui import resource_library as resources
from gt.ui import file_dialog
from gt.tools.batch_processor import batch_processor_input_metadata as input_metadata
from gt.tools.batch_processor import batch_processor_task_base as task_base
from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
from gt.tools.batch_processor.widgets.table_height_handle import TableHeightHandle


ACTIVE_COLUMN = 0
INPUT_COLUMN = 1
FIRST_VALUE_COLUMN = 2
DELETE_COLUMN = FIRST_VALUE_COLUMN + input_metadata.MAX_SLOTS
JSON_FILTER = "JSON Files (*.json);;All Files (*);;"
METADATA_FILE_VERSION = 1
MATCH_HELP = (
    "Input matches an incoming item by relative path, relative path without extension,\n"
    "file name, or file stem (e.g. \"walk/walk_090.ma\", \"walk_090\").\n"
    "Wildcards * ? [ ] are allowed (e.g. \"*_090\" or \"*\" for a default row).\n"
    "Rows apply top to bottom; a non-empty cell overrides earlier rows, empty cells set nothing.\n"
    "Rows that match nothing are reported as warnings when the task runs."
)
ACCESS_HELP = (
    "Each slot is always available by number and, when named, by its name:\n"
    "  Variables: {input-meta-1}, {input-meta-seed}\n"
    "  Python (Pass Env): env['input-meta-seed']\n"
    "  Python (any): work_item.metadata['input_metadata']['seed']\n"
    "Names are cleaned automatically: \"Shot Code\" becomes \"shot-code\"."
)


class AttrWidgetInputMetadataTask(AttrWidgetTask):
    """Edits slot names and the per-input value table without rebuilding the panel."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, **kwargs):
        """Builds the slot controls, value table, and actions.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskInputMetadata, optional): Task being edited.
            project (BatchProcessorModel, optional): Owning project.
            refresh_parent_func (callable, optional): Parent refresh function.
            **kwargs: Additional base widget arguments.
        """
        super().__init__(parent=parent, task=task, project=project,
                         refresh_parent_func=refresh_parent_func, **kwargs)
        self._loading_table = False
        self.slot_rows = []
        self.add_widget_separator_line(label_text="Value Slots")
        self.build_slot_controls()
        self.add_widget_separator_line(label_text="Input Values")
        self.build_value_table()
        self.status_label = qt.QtWidgets.QLabel()
        self.status_label.setWordWrap(True)
        self.content_layout.addWidget(self.status_label)
        self.content_layout.addStretch()
        self.load_rows()
        self.refresh_slots()

    def build_slot_controls(self):
        """Adds the active slot count and one name field per slot."""
        count_layout = self.add_labeled_layout("Active Slots", tooltip="Number of values each input carries (1-5).")
        self.slot_count_spin = qt.QtWidgets.QSpinBox()
        self.slot_count_spin.setRange(1, input_metadata.MAX_SLOTS)
        self.slot_count_spin.setValue(self.task.get_slot_count())
        self.slot_count_spin.setMinimumHeight(30)
        self.slot_count_spin.setToolTip("Values in hidden slots are kept but not applied.")
        self.slot_count_spin.valueChanged.connect(self.set_slot_count)
        count_layout.addWidget(self.slot_count_spin)
        self.add_task_index_checkbox(count_layout)
        count_layout.addStretch()
        names = input_metadata.pad_values(self.task.settings.get("slot_names"))
        for slot_index in range(input_metadata.MAX_SLOTS):
            container = qt.QtWidgets.QWidget()
            layout = qt.QtWidgets.QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            self.add_row_label(layout, f"Slot {slot_index + 1} Name:", tooltip=ACCESS_HELP)
            field = self.create_text_field(text=names[slot_index], placeholder="Optional name, e.g. seed",
                                           tooltip=ACCESS_HELP)
            field.editingFinished.connect(partial(self.set_slot_name, slot_index=slot_index))
            layout.addWidget(field)
            preview = qt.QtWidgets.QLabel()
            preview.setStyleSheet("color: grey;")
            preview.setMinimumWidth(1)
            preview.setTextInteractionFlags(qt.QtCore.Qt.TextSelectableByMouse)
            layout.addWidget(preview)
            self.content_layout.addWidget(container)
            self.slot_rows.append({"container": container, "field": field, "preview": preview})

    def build_value_table(self):
        """Adds the per-input table, its height handle, and action buttons."""
        self.table = qt.QtWidgets.QTableWidget(0, DELETE_COLUMN + 1)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(ACTIVE_COLUMN, qt.QtLib.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(DELETE_COLUMN, qt.QtLib.QHeaderView.ResizeToContents)
        for column in range(INPUT_COLUMN, DELETE_COLUMN):
            header.setSectionResizeMode(column, qt.QtLib.QHeaderView.Stretch)
        self.table.setSelectionBehavior(qt.QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(qt.QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setMinimumHeight(180)
        self.table.setToolTip(f"Double-click to edit. Right-click for row actions.\n\n{MATCH_HELP}")
        self.table.itemChanged.connect(self.commit)
        self.table.setContextMenuPolicy(qt.QtCore.Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.context_menu = qt.QtWidgets.QMenu(self)
        shortcut_class = getattr(qt.QtGui, "QShortcut", None) or getattr(qt.QtWidgets, "QShortcut")
        self.delete_shortcut = shortcut_class(qt.QtGui.QKeySequence("Delete"), self.table)
        self.delete_shortcut.setContext(qt.QtCore.Qt.WidgetShortcut)
        self.delete_shortcut.activated.connect(self.remove_rows)
        self.content_layout.addWidget(self.table)
        self.table_height_handle = TableHeightHandle(
            table=self.table, task=self.task, state_key="input_metadata_table_height", parent=self)
        self.content_layout.addWidget(self.table_height_handle)
        actions = qt.QtWidgets.QHBoxLayout()
        for label, icon, tooltip, callback in (
                ("Add", resources.Icon.ui_add, "Append an empty row.", self.add_row),
                ("Add Inputs", resources.Icon.ui_reset,
                 "Add a row for every input this task currently receives that has no row yet.",
                 self.add_incoming_rows),
                ("Paste", resources.Icon.rigger_action_paste_grayscale,
                 "Paste tab-separated spreadsheet rows: input, then one column per slot.", self.paste_rows),
                ("Import", resources.Icon.library_import, "Append rows from a JSON file.", self.import_rows),
                ("Export", resources.Icon.library_export, "Save slot names and rows as JSON.", self.export_rows)):
            button = qt.QtWidgets.QPushButton(label)
            button.setIcon(qt.QtGui.QIcon(icon))
            button.setToolTip(tooltip)
            button.clicked.connect(callback)
            actions.addWidget(button)
        actions.addStretch()
        self.content_layout.addLayout(actions)
        help_label = qt.QtWidgets.QLabel("Hover the table for matching rules and the slot names for variable names.")
        help_label.setStyleSheet("color: grey;")
        help_label.setWordWrap(True)
        self.content_layout.addWidget(help_label)

    def set_slot_count(self, value):
        """Stores the active slot count and updates visible columns.

        Args:
            value (int): Active slot count.
        """
        self.set_task_setting(int(value), key="slot_count")
        self.refresh_slots()

    def set_slot_name(self, slot_index):
        """Cleans and stores one slot name, showing the cleaned value in its field.

        Args:
            slot_index (int): Zero-based slot index.
        """
        field = self.slot_rows[slot_index]["field"]
        cleaned = input_metadata.clean_slot_name(field.text())
        if field.text() != cleaned:
            field.setText(cleaned)
        names = input_metadata.pad_values(self.task.settings.get("slot_names"))
        if names[slot_index] == cleaned:
            self.refresh_slots()
            return
        names[slot_index] = cleaned
        self.set_task_setting(names, key="slot_names")
        self.refresh_slots()

    def refresh_slots(self):
        """Updates slot field visibility, variable previews, column headers, and status."""
        slot_count = self.task.get_slot_count()
        names = self.task.get_slot_names()
        variable_names = self.task.get_variable_names()
        for slot_index, slot_row in enumerate(self.slot_rows):
            slot_row["container"].setVisible(slot_index < slot_count)
            if slot_index < slot_count:
                error = input_metadata.get_slot_name_error(names[slot_index])
                slot_row["preview"].setText(error or "  ".join(variable_names[slot_index]))
                slot_row["preview"].setStyleSheet("color: #E57373;" if error else "color: grey;")
        labels = ["Active", "Input"]
        labels.extend(names[index] or f"Value {index + 1}" for index in range(input_metadata.MAX_SLOTS))
        labels.append("")
        self.table.setHorizontalHeaderLabels(labels)
        for slot_index in range(input_metadata.MAX_SLOTS):
            self.table.setColumnHidden(FIRST_VALUE_COLUMN + slot_index, slot_index >= slot_count)
        self.update_status()

    def load_rows(self):
        """Fills the table from stored rows, reporting malformed data in the status line."""
        self._loading_table = True
        try:
            self.table.setRowCount(0)
            try:
                rows = self.task.get_rows()
            except ValueError as exception:
                self.emit_status_message(f"Input Metadata rows are malformed: {exception}", status="warning")
                rows = []
            for row in rows:
                self.insert_row(row)
        finally:
            self._loading_table = False

    def insert_row(self, row, position=None):
        """Inserts one complete row without emitting partial edits.

        Args:
            row (dict): Row data.
            position (int, optional): Insertion index; appends by default.

        Returns:
            int: Inserted row index.
        """
        row = input_metadata.normalize_row(row)
        position = self.table.rowCount() if position is None else position
        blocked = self.table.blockSignals(True)
        try:
            self.table.insertRow(position)
            checkbox = qt.QtWidgets.QCheckBox()
            checkbox.setChecked(row["enabled"])
            checkbox.setToolTip("Apply this row.")
            checkbox.toggled.connect(self.commit)
            container = qt.QtWidgets.QWidget()
            layout = qt.QtWidgets.QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setAlignment(qt.QtLib.AlignmentFlag.AlignCenter)
            layout.addWidget(checkbox)
            container.checkbox = checkbox
            self.table.setCellWidget(position, ACTIVE_COLUMN, container)
            input_item = qt.QtWidgets.QTableWidgetItem(row["input"])
            input_item.setData(qt.QtCore.Qt.UserRole, row["id"])
            self.table.setItem(position, INPUT_COLUMN, input_item)
            for slot_index, value in enumerate(row["values"]):
                self.table.setItem(position, FIRST_VALUE_COLUMN + slot_index, qt.QtWidgets.QTableWidgetItem(value))
            button = self.create_table_action_button(self.remove_button_row, "Delete this row.",
                                                     icon_path=resources.Icon.ui_trash, accessible_name="Delete Row")
            self.table.setCellWidget(position, DELETE_COLUMN, button)
        finally:
            self.table.blockSignals(blocked)
        return position

    def get_table_rows(self, rows=None):
        """Reads rows from the table, including values in hidden slots.

        Args:
            rows (list, optional): Table row indices; reads all rows by default.

        Returns:
            list: Row dictionaries.
        """
        rows = range(self.table.rowCount()) if rows is None else rows
        result = []
        for row in rows:
            values = [self.table.item(row, FIRST_VALUE_COLUMN + index).text()
                      for index in range(input_metadata.MAX_SLOTS)]
            result.append({"id": self.table.item(row, INPUT_COLUMN).data(qt.QtCore.Qt.UserRole),
                           "enabled": self.table.cellWidget(row, ACTIVE_COLUMN).checkbox.isChecked(),
                           "input": self.table.item(row, INPUT_COLUMN).text().strip(), "values": values})
        return result

    def commit(self, unused_value=None):
        """Stores table edits in the task.

        Args:
            unused_value (object, optional): Ignored signal argument.
        """
        if self._loading_table:
            return
        self.task.set_rows(self.get_table_rows())
        self.update_status()

    def update_status(self):
        """Shows row counts and settings errors."""
        errors = input_metadata.get_settings_errors(self.task.settings)
        if errors:
            self.status_label.setText(errors[0])
            self.status_label.setStyleSheet("color: #E57373;")
            return
        rows = self.task.get_rows()
        active = sum(row["enabled"] and bool(row["input"].strip()) for row in rows)
        self.status_label.setText(f"{len(rows)} row(s), {active} active. Inputs without a row pass through "
                                  "with empty values.")
        self.status_label.setStyleSheet("color: grey;")

    def get_selected_rows(self):
        """Gets selected table row indices.

        Returns:
            list: Sorted row indices.
        """
        return sorted({index.row() for index in self.table.selectedIndexes()})

    def add_row(self, checked=False):
        """Appends an empty row and starts editing its input.

        Args:
            checked (bool, optional): Ignored button state.
        """
        position = self.insert_row(input_metadata.create_row())
        self.commit()
        self.table.setCurrentCell(position, INPUT_COLUMN)
        self.table.editItem(self.table.item(position, INPUT_COLUMN))

    def get_incoming_input_names(self):
        """Gets relative input paths from the enabled input tasks above this task in its segment.

        Returns:
            list: Relative input paths without extension, in discovery order.
        """
        if not self.project:
            return []
        names = []
        for work_item in self.task.get_upstream_input_items(self.project):
            relative_path = task_base.get_work_item_relative_path(work_item)
            name = os.path.splitext(relative_path or os.path.basename(work_item.source_path))[0]
            if name and name not in names:
                names.append(name)
        return names

    def add_incoming_rows(self, checked=False):
        """Adds one row per incoming input that no existing row names exactly.

        Args:
            checked (bool, optional): Ignored button state.
        """
        try:
            names = self.get_incoming_input_names()
        except Exception as exception:
            self.emit_status_message(f"Unable to list incoming inputs: {exception}", status="warning")
            return
        existing = {input_metadata.normalize_match_text(row["input"]) for row in self.get_table_rows()}
        added = [name for name in names if input_metadata.normalize_match_text(name) not in existing]
        for name in added:
            self.insert_row(input_metadata.create_row(name))
        self.commit()
        if not names:
            self.emit_status_message("No enabled input task above this task in its segment produced inputs.",
                                     status="warning")
            return
        self.emit_status_message(f"Added {len(added)} row(s); {len(names) - len(added)} input(s) already had one.")

    def remove_rows(self, checked=False, rows=None):
        """Deletes rows.

        Args:
            checked (bool, optional): Ignored action state.
            rows (list, optional): Rows to delete; uses the selection by default.
        """
        rows = self.get_selected_rows() if rows is None else rows
        if not rows:
            return
        blocked = self.table.blockSignals(True)
        try:
            for row in sorted(rows, reverse=True):
                self.table.removeRow(row)
        finally:
            self.table.blockSignals(blocked)
        self.commit()
        self.emit_status_message(f"Deleted {len(rows)} metadata row(s).")

    def remove_button_row(self, checked=False):
        """Deletes the row that owns the clicked delete button.

        Args:
            checked (bool, optional): Ignored button state.
        """
        button = self.sender()
        for row in range(self.table.rowCount()):
            if self.table.cellWidget(row, DELETE_COLUMN) == button:
                self.remove_rows(rows=[row])
                return

    def duplicate_rows(self, checked=False):
        """Duplicates selected rows below the selection with fresh IDs.

        Args:
            checked (bool, optional): Ignored action state.
        """
        rows = self.get_selected_rows()
        for offset, row in enumerate(self.get_table_rows(rows)):
            self.insert_row(input_metadata.create_row(row["input"], row["values"], row["enabled"]),
                            position=rows[-1] + offset + 1)
        self.commit()

    def set_rows_active(self, checked=False, active=True, selected=False):
        """Activates or deactivates all or selected rows.

        Args:
            checked (bool, optional): Ignored action state.
            active (bool, optional): Target state.
            selected (bool, optional): Whether to affect only selected rows.
        """
        rows = self.get_selected_rows() if selected else range(self.table.rowCount())
        self._loading_table = True
        try:
            for row in rows:
                self.table.cellWidget(row, ACTIVE_COLUMN).checkbox.setChecked(active)
        finally:
            self._loading_table = False
        self.commit()

    def append_rows(self, rows):
        """Validates and appends rows with fresh IDs.

        Args:
            rows (list): Row dictionaries.
        """
        input_metadata.validate_rows(rows)
        for row in rows:
            row = input_metadata.normalize_row(row)
            self.insert_row(input_metadata.create_row(row["input"], row["values"], row["enabled"]))
        self.commit()
        self.emit_status_message(f"Added {len(rows)} metadata row(s).")

    def paste_rows(self, checked=False):
        """Appends tab-separated rows from the clipboard.

        Args:
            checked (bool, optional): Ignored button state.
        """
        text = qt.QtWidgets.QApplication.clipboard().text()
        rows = []
        for line in text.splitlines():
            if not line.strip():
                continue
            cells = line.split("\t")
            rows.append({"input": cells[0].strip(), "values": input_metadata.pad_values(cells[1:]), "enabled": True})
        if not rows:
            self.emit_status_message("Clipboard has no rows. Copy spreadsheet cells: input, then values.",
                                     status="warning")
            return
        self.append_rows(rows)

    def get_json_directory(self):
        """Gets the initial folder for JSON dialogs.

        Returns:
            str: Project folder when it exists, otherwise the user home folder.
        """
        root = self.project.get_project_dir() if self.project else ""
        return root if root and os.path.isdir(root) else os.path.expanduser("~")

    def import_rows(self, checked=False):
        """Appends rows from an exported JSON file; slot names are not changed.

        Args:
            checked (bool, optional): Ignored button state.
        """
        path = file_dialog.file_dialog(parent=self, caption="Import Input Metadata", file_filter=JSON_FILTER,
                                       starting_directory=self.get_json_directory(), ok_caption="Import")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8-sig") as metadata_file:
                data = json.load(metadata_file)
            if not isinstance(data, dict) or data.get("version") != METADATA_FILE_VERSION:
                raise ValueError("Expected an Input Metadata JSON document with version 1.")
            self.append_rows(data.get("rows"))
        except (OSError, ValueError, TypeError) as exception:
            self.emit_status_message(f"Unable to import input metadata: {exception}", status="warning")

    def export_rows(self, checked=False):
        """Saves slot names and all rows as JSON.

        Args:
            checked (bool, optional): Ignored button state.
        """
        path = file_dialog.file_dialog(parent=self, caption="Export Input Metadata", write_mode=True,
                                       file_filter=JSON_FILTER, starting_directory=self.get_json_directory(),
                                       ok_caption="Export")
        if not path:
            return
        data = {"version": METADATA_FILE_VERSION, "slot_names": self.task.get_slot_names(),
                "rows": self.get_table_rows()}
        try:
            with open(path, "w", encoding="utf-8", newline="\n") as metadata_file:
                json.dump(data, metadata_file, ensure_ascii=False, indent=4)
                metadata_file.write("\n")
        except OSError as exception:
            self.emit_status_message(f"Unable to export input metadata: {exception}", status="warning")
            return
        self.emit_status_message(f"Exported {len(data['rows'])} metadata row(s) to {path}.")

    def show_context_menu(self, position):
        """Shows row actions.

        Args:
            position (QPoint): Requested table viewport position.
        """
        row = self.table.rowAt(position.y())
        if row >= 0 and row not in self.get_selected_rows():
            self.table.selectRow(row)
        selected = bool(self.get_selected_rows())
        has_rows = self.table.rowCount() > 0
        menu = self.context_menu
        menu.clear()
        for label, icon, enabled, callback in (
                ("Add Row", resources.Icon.ui_add, True, self.add_row),
                ("Add Inputs", resources.Icon.ui_reset, True, self.add_incoming_rows),
                ("Duplicate Selected", resources.Icon.rigger_action_duplicate_grayscale, selected,
                 self.duplicate_rows),
                (None, None, None, None),
                ("Activate All", resources.Icon.ui_checkbox_checked, has_rows, self.set_rows_active),
                ("Deactivate All", resources.Icon.ui_checkbox_unchecked, has_rows,
                 partial(self.set_rows_active, active=False)),
                ("Activate Selected", resources.Icon.ui_rows_selected_checked, selected,
                 partial(self.set_rows_active, selected=True)),
                ("Deactivate Selected", resources.Icon.ui_rows_selected_unchecked, selected,
                 partial(self.set_rows_active, active=False, selected=True)),
                (None, None, None, None),
                ("Delete Selected", resources.Icon.ui_trash, selected, self.remove_rows)):
            if label is None:
                menu.addSeparator()
                continue
            action = menu.addAction(label)
            action.setIcon(qt.QtGui.QIcon(icon))
            action.setEnabled(enabled)
            action.triggered.connect(callback)
        menu.popup(self.table.viewport().mapToGlobal(position))
