"""Two-column pair editor matching the Batch Processor Input Strings table."""

import json
import os
from functools import partial
from gt.ui import qt_import as qt
from gt.ui import resource_library as resources
from gt.ui import file_dialog
from gt.ui.qt_utils import TablePlaceholderDelegate
from gt.tools.batch_processor.tasks import task_input_pairs as pairs
from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
from gt.tools.batch_processor.widgets.input_source_feedback import InputSourceFeedbackWidget


ACTIVE_COLUMN = 0
FILE_COLUMN = 1
STRING_COLUMN = 2
DELETE_COLUMN = 3
JSON_FILTER = "JSON Files (*.json);;All Files (*);;"
TOKEN_HELP = (
    "Use {input-file} for the original filename without its extension, or the manual name. "
    "Use {input-string} for the associated text and {input-string-index} for the running index. "
    "Python tasks with Pass Env enabled can read env['input-file'] and env['input-string']."
)


class AttrWidgetInputPairsTask(AttrWidgetTask):
    """Edits folder assignments and independent manual pairs without rebuilding the panel."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, **kwargs):
        """Builds the mode controls, folder settings, pair table, and segment settings.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskInputPairs, optional): Task being edited.
            project (BatchProcessorModel, optional): Owning project.
            refresh_parent_func (callable, optional): Parent refresh function.
            **kwargs: Additional base widget arguments.
        """
        super().__init__(parent=parent, task=task, project=project,
                         refresh_parent_func=refresh_parent_func, **kwargs)
        self._loading_table = False
        self._available_files = set()
        self._confirmed_source_root = ""
        self._column_widths_initialized = False
        self._resizing_pair_columns = False
        self._file_column_ratio = 0.5
        self.add_widget_separator_line(label_text="Input Pairs")
        self.build_mode_selector()
        self.build_folder_settings()
        self.build_pair_table()
        self.build_input_feedback()
        self.add_segmentation_section(
            main_label="Start New Segment", main_key="start_new_input_list",
            main_tooltip="Replace earlier inputs with these pairs for the following tasks.")
        self.content_layout.addStretch()
        self.show_mode()

    def build_mode_selector(self):
        """Adds exclusive mode buttons and a status line with placeholder help."""
        layout = self.add_labeled_layout("Mode", tooltip="Choose files with descriptions or manually named jobs.")
        self.mode_group = qt.QtWidgets.QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.mode_buttons = {}
        highlight = resources.Color.Hex.blue_pastel
        style = (f"QPushButton:checked {{ background-color: {highlight}; border: 1px solid {highlight}; "
                 "border-radius: 3px; color: #FFFFFF; font-weight: bold; }")
        for mode, label in pairs.INPUT_MODE_LABELS.items():
            button = qt.QtWidgets.QPushButton(label)
            button.setCheckable(True)
            button.setMinimumHeight(30)
            button.setStyleSheet(style)
            button.setToolTip("Assign text to discovered files." if mode == pairs.INPUT_MODE_FOLDER
                              else "Create a new empty Maya scene per custom name and description.")
            button.clicked.connect(partial(self.set_input_mode, mode=mode))
            self.mode_group.addButton(button)
            layout.addWidget(button)
            self.mode_buttons[mode] = button
        self.status_label = qt.QtWidgets.QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setToolTip(TOKEN_HELP)
        self.content_layout.addWidget(self.status_label)
        help_label = qt.QtWidgets.QLabel("Use {input-file} for names and {input-string} for descriptions.")
        help_label.setWordWrap(True)
        help_label.setToolTip(TOKEN_HELP)
        self.content_layout.addWidget(help_label)

    def build_folder_settings(self):
        """Adds the folder template and existing Input Files discovery filters."""
        self.folder_page = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QVBoxLayout(self.folder_page)
        layout.setContentsMargins(0, 0, 0, 0)
        self.folder_path_widgets = self.add_path_template_field(
            "Source Path", self.task.settings.get("source_path", ""),
            partial(self.set_folder_setting, key="source_path"),
            placeholder="{project-dir}/{input-dir}", dir_only=True, parent_layout=layout, return_widgets=True,
            tooltip="Folder containing the files to pair with descriptions. Refresh after changing its contents.")
        self.source_path_field = self.folder_path_widgets["field"]
        self.source_path_field.editingFinished.connect(self.refresh_source_path)
        self.folder_path_widgets["browse_button"].clicked.connect(lambda *args: self.refresh_source_path())
        options = self.add_labeled_layout("Discovery", parent_layout=layout)
        self.add_checkbox(
            "Include Subdirectories", self.task.settings.get("include_subdirectories", True),
            partial(self.set_folder_setting, key="include_subdirectories"), layout=options,
            tooltip="Use relative paths to distinguish files in nested folders.")
        self.add_row_label(layout=options, label_text="Extensions:", tooltip="Accepted file extensions.")
        self.extensions_field = self.create_text_field(
            text=", ".join(self.task.settings.get("extensions") or []), placeholder=".ma, .mb, .fbx")
        self.extensions_field.textChanged.connect(partial(self.set_folder_list, key="extensions"))
        self.extensions_field.editingFinished.connect(self.refresh_files)
        options.addWidget(self.extensions_field)
        self.add_task_index_checkbox(options)
        self.exclude_field = self.add_text_field(
            "Exclude Patterns", ", ".join(self.task.settings.get("exclude_patterns") or []),
            partial(self.set_folder_list, key="exclude_patterns"), parent_layout=layout,
            placeholder="*_tmp.ma, */cache/*", tooltip="Filename or path patterns to exclude.")
        self.exclude_field.editingFinished.connect(self.refresh_files)
        self.content_layout.addWidget(self.folder_page)

    def build_pair_table(self):
        """Adds active, filename, description, and row action columns with familiar table actions."""
        self.table = qt.QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Active", "Input File", "Input String", ""])
        header = self.table.horizontalHeader()
        for column in (ACTIVE_COLUMN, DELETE_COLUMN):
            header.setSectionResizeMode(column, qt.QtLib.QHeaderView.ResizeToContents)
        for column in (FILE_COLUMN, STRING_COLUMN):
            header.setSectionResizeMode(column, qt.QtLib.QHeaderView.Interactive)
        header.sectionResized.connect(self.on_pair_column_resized)
        self._pair_table_viewport = self.table.viewport()
        self._pair_table_viewport.installEventFilter(self)
        self.table.horizontalHeaderItem(STRING_COLUMN).setToolTip("Drag the header divider to resize this column.")
        self.table.setSelectionBehavior(qt.QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(qt.QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setMinimumHeight(180)
        self.table.setToolTip("Double-click to edit. Right-click for row actions. Missing files appear red.")
        self.file_delegate = TablePlaceholderDelegate("Custom file name (without extension)",
                                                     [FILE_COLUMN], parent=self.table)
        self.string_delegate = TablePlaceholderDelegate("Enter a string or motion description",
                                                       [STRING_COLUMN], parent=self.table)
        self.table.setItemDelegateForColumn(FILE_COLUMN, self.file_delegate)
        self.table.setItemDelegateForColumn(STRING_COLUMN, self.string_delegate)
        self.table.itemChanged.connect(self.commit)
        self.table.setContextMenuPolicy(qt.QtCore.Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.context_menu = qt.QtWidgets.QMenu(self)
        shortcut_class = getattr(qt.QtGui, "QShortcut", None) or getattr(qt.QtWidgets, "QShortcut")
        self.delete_shortcut = shortcut_class(qt.QtGui.QKeySequence("Delete"), self.table)
        self.delete_shortcut.setContext(qt.QtCore.Qt.WidgetShortcut)
        self.delete_shortcut.activated.connect(self.remove_rows)
        self.content_layout.addWidget(self.table)
        actions = qt.QtWidgets.QHBoxLayout()
        self.buttons = {}
        for key, label, icon, callback in (
                ("add", "Add", resources.Icon.ui_add, self.add_row),
                ("paste", "Paste Pairs", resources.Icon.rigger_action_paste_grayscale, self.paste_pairs),
                ("show_hidden", "Show Hidden", resources.Icon.ui_reset, self.restore_folder_files),
                ("import", "Import", resources.Icon.library_import, self.import_pairs),
                ("export", "Export", resources.Icon.library_export, self.export_pairs)):
            button = qt.QtWidgets.QPushButton(label)
            button.setIcon(qt.QtGui.QIcon(icon))
            button.setToolTip({"add": "Append an empty manual pair.",
                               "paste": "Paste JSON pairs or two tab-separated spreadsheet columns.",
                               "show_hidden": "Show hidden folder pairs again, including their saved descriptions.",
                               "import": "Merge pairs from a JSON file without deleting other rows.",
                               "export": "Save all visible pairs, including inactive and missing rows, as JSON."}[key])
            button.clicked.connect(callback)
            actions.addWidget(button)
            self.buttons[key] = button
        actions.addStretch()
        self.content_layout.addLayout(actions)

    def showEvent(self, event):
        """Fills the table width with the text columns using their current proportions.

        Args:
            event (QShowEvent): Widget show event.
        """
        super().showEvent(event)
        self._column_widths_initialized = True
        self.resize_pair_columns()

    def eventFilter(self, watched, event):
        """Fits the text columns when the table viewport changes size.

        Args:
            watched (QObject): Object receiving the event.
            event (QEvent): Event to inspect.

        Returns:
            bool: Whether normal event processing should stop.
        """
        if watched is self._pair_table_viewport and event.type() == qt.QtCore.QEvent.Resize:
            self.resize_pair_columns()
        return super().eventFilter(watched, event)

    def on_pair_column_resized(self, column, old_size, new_size):
        """Stores manually adjusted proportions and keeps the action column at the right edge.

        Args:
            column (int): Resized column index.
            old_size (int): Previous column width.
            new_size (int): Requested column width.
        """
        if not self._column_widths_initialized or self._resizing_pair_columns:
            return
        if column in (FILE_COLUMN, STRING_COLUMN):
            available_width = self.get_pair_text_columns_width()
            file_width = new_size if column == FILE_COLUMN else available_width - new_size
            self._file_column_ratio = max(0.0, min(1.0, file_width / available_width))
        self.resize_pair_columns()

    def get_pair_text_columns_width(self):
        """Gets the available width after reserving space for active and action columns.

        Returns:
            int: Combined width for the two text columns, respecting their minimum sizes.
        """
        header = self.table.horizontalHeader()
        available_width = self.table.viewport().width() - sum(
            header.sectionSize(column) for column in (ACTIVE_COLUMN, DELETE_COLUMN))
        return max(2 * header.minimumSectionSize(), available_width)

    def resize_pair_columns(self):
        """Expands or contracts the text columns while retaining the user's width proportions."""
        if not self._column_widths_initialized or self._resizing_pair_columns:
            return
        header = self.table.horizontalHeader()
        available_width = self.get_pair_text_columns_width()
        minimum_width = header.minimumSectionSize()
        file_width = max(minimum_width, min(available_width - minimum_width,
                                            round(available_width * self._file_column_ratio)))
        self._resizing_pair_columns = True
        try:
            header.resizeSection(FILE_COLUMN, file_width)
            header.resizeSection(STRING_COLUMN, available_width - file_width)
        finally:
            self._resizing_pair_columns = False

    def build_input_feedback(self):
        """Adds shared file statistics and refresh/preview controls for both pair modes."""
        self.input_feedback = InputSourceFeedbackWidget(
            self.refresh_files, lambda *args: self.show_resolved_input_files(), parent=self)
        self.input_count_label = self.input_feedback.label
        self.buttons["refresh"] = self.input_feedback.refresh_button
        self.buttons["resolved"] = self.input_feedback.preview_button
        self.content_layout.addWidget(self.input_feedback)

    def refresh_source_path(self):
        """Refreshes changed, confirmed source paths when they resolve to an existing directory."""
        try:
            root = self.task.get_input_dir(self.project)
        except (ValueError, TypeError, OSError):
            return
        if root and os.path.isdir(root) and os.path.normcase(root) != self._confirmed_source_root:
            self.refresh_files()

    def show_resolved_input_files(self):
        """Shows real file paths or virtual scene identities for the active pairs."""
        file_paths = self.task.discover_files(self.project) if self.project else []
        self.show_path_list(title="Resolved Input Pairs", file_paths=file_paths)
        self.emit_status_message(f"Resolved input preview found {len(file_paths)} pair(s).")

    def set_folder_setting(self, value, key):
        """Stores a discovery setting and refreshes after a checkbox change.

        Args:
            value (object): New setting value.
            key (str): Setting key.
        """
        self.set_task_setting(value, key=key)
        if key == "include_subdirectories":
            self.refresh_files()

    def set_folder_list(self, text, key):
        """Stores comma-separated extension or exclusion values.

        Args:
            text (str): Field contents.
            key (str): Setting key.
        """
        self.set_task_setting([value.strip() for value in text.split(",") if value.strip()], key=key)

    def set_input_mode(self, checked=False, mode=pairs.INPUT_MODE_FOLDER):
        """Switches modes while retaining the inactive table.

        Args:
            checked (bool, optional): Ignored button state.
            mode (str, optional): Requested pair mode.
        """
        self.set_task_setting(mode, key="input_mode")
        self.show_mode()

    def show_mode(self):
        """Updates visible controls and loads the active table."""
        mode = self.task.get_input_mode()
        if mode not in self.mode_buttons:
            self.emit_status_message(f"Unknown input pairs mode: {mode}", status="warning")
            return
        manual = mode == pairs.INPUT_MODE_MANUAL
        self.mode_buttons[mode].setChecked(True)
        self.folder_page.setVisible(not manual)
        self.buttons["add"].setVisible(manual)
        self.buttons["show_hidden"].setVisible(not manual)
        self.table.horizontalHeaderItem(DELETE_COLUMN).setToolTip("Delete a manual pair." if manual
                                                               else "Hide a pair; recover it with Show Hidden.")
        self.table.horizontalHeaderItem(FILE_COLUMN).setText("Input File" if not manual else "Custom File Name")
        filename_tooltip = (
            "Path relative to the source folder; {input-file} supplies its filename stem." if not manual
            else "Filename stem used literally by {input-file} and default output naming.")
        self.table.horizontalHeaderItem(FILE_COLUMN).setToolTip(
            f"{filename_tooltip}\nDrag the header divider to resize this column.")
        self.refresh_files(report=False)

    def refresh_files(self, checked=False, report=True):
        """Reconciles rows with disk and reloads the table without replacing its controls.

        Args:
            checked (bool, optional): Ignored signal state.
            report (bool, optional): Whether to report a completed refresh.
        """
        try:
            rows = self.task.get_pair_rows(self.project, synchronize=True)
            self._available_files = (set(self.task.get_folder_file_map(self.project))
                                     if self.task.get_input_mode() == pairs.INPUT_MODE_FOLDER else set())
        except (ValueError, TypeError, OSError) as exception:
            self.emit_status_message(f"Unable to refresh input pairs: {exception}", status="warning")
            return
        self._loading_table = True
        blocked = self.table.blockSignals(True)
        try:
            self.table.setRowCount(0)
            for row in rows:
                self.insert_pair(row)
        finally:
            self.table.blockSignals(blocked)
            self._loading_table = False
        self._confirmed_source_root = (os.path.normcase(self.task.get_input_dir(self.project))
                                       if self.task.get_input_mode() == pairs.INPUT_MODE_FOLDER else "")
        self.update_status()
        if report:
            self.emit_status_message(f"Refreshed {len(rows)} input pair(s).")

    def insert_pair(self, pair, row=None):
        """Inserts one complete row while suppressing partial table changes.

        Args:
            pair (dict): Pair values, ID, and active flag.
            row (int, optional): Insertion position; appends by default.

        Returns:
            int: Inserted row number.
        """
        row = self.table.rowCount() if row is None else row
        blocked = self.table.blockSignals(True)
        try:
            self.table.insertRow(row)
            checkbox = qt.QtWidgets.QCheckBox()
            checkbox.setChecked(pair.get("enabled", True))
            checkbox.setToolTip("Use this pair when its input is available.")
            checkbox.toggled.connect(self.commit)
            container = qt.QtWidgets.QWidget()
            layout = qt.QtWidgets.QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setAlignment(qt.QtLib.AlignmentFlag.AlignCenter)
            layout.addWidget(checkbox)
            container.checkbox = checkbox
            self.table.setCellWidget(row, ACTIVE_COLUMN, container)
            filename = qt.QtWidgets.QTableWidgetItem(pair["input_file"])
            filename.setData(qt.QtCore.Qt.UserRole, pair.get("id") or pairs.create_pair()["id"])
            if self.task.get_input_mode() == pairs.INPUT_MODE_FOLDER:
                filename.setFlags(filename.flags() & ~qt.QtCore.Qt.ItemIsEditable)
            self.table.setItem(row, FILE_COLUMN, filename)
            self.table.setItem(row, STRING_COLUMN, qt.QtWidgets.QTableWidgetItem(pair["input_string"]))
            manual = self.task.get_input_mode() == pairs.INPUT_MODE_MANUAL
            button = self.create_table_action_button(
                self.remove_button_row,
                "Delete this manual pair." if manual else "Hide this pair. Use Show Hidden to recover it.",
                icon_path=resources.Icon.ui_trash if manual else None,
                text="" if manual else "Hide", accessible_name="Delete Pair" if manual else "Hide Pair")
            self.table.setCellWidget(row, DELETE_COLUMN, button)
        finally:
            self.table.blockSignals(blocked)
        return row

    def get_selected_rows(self):
        """Gets the selected row numbers in table order.

        Returns:
            list: Selected rows.
        """
        return sorted({index.row() for index in self.table.selectedIndexes()})

    def get_row_pairs(self, rows=None):
        """Reads literal pair values, active flags, and IDs from the table.

        Args:
            rows (list, optional): Rows to read; reads all rows by default.

        Returns:
            list: Serialized pair dictionaries.
        """
        rows = range(self.table.rowCount()) if rows is None else rows
        return [{"id": self.table.item(row, FILE_COLUMN).data(qt.QtCore.Qt.UserRole),
                 "input_file": self.table.item(row, FILE_COLUMN).text(),
                 "input_string": self.table.item(row, STRING_COLUMN).text(),
                 "enabled": self.table.cellWidget(row, ACTIVE_COLUMN).checkbox.isChecked()} for row in rows]

    def commit(self, unused_value=None):
        """Saves table edits without rebuilding the active editor.

        Args:
            unused_value (object, optional): Ignored item or checkbox signal argument.
        """
        if self._loading_table:
            return
        self.task.set_pair_rows(self.get_row_pairs())
        self.update_status()

    def update_status(self):
        """Updates run indexes and missing-file colors using the latest folder snapshot."""
        manual = self.task.get_input_mode() == pairs.INPUT_MODE_MANUAL
        index = 0
        missing_count = 0
        name_error = ""
        blocked = self.table.blockSignals(True)
        try:
            for row, pair in enumerate(self.get_row_pairs()):
                missing = not manual and pairs.get_pair_key(pair["input_file"]) not in self._available_files
                missing_count += int(missing)
                active = pair["enabled"] and bool(pair["input_file"].strip()) and not missing
                if manual and active:
                    error = pairs.validate_manual_filename(pair["input_file"])
                    if error and not name_error:
                        name_error = f"Row {row + 1}: {error}"
                index += int(active)
                self.table.setVerticalHeaderItem(row, qt.QtWidgets.QTableWidgetItem(str(index) if active else ""))
                for column in (FILE_COLUMN, STRING_COLUMN):
                    item = self.table.item(row, column)
                    item.setForeground(qt.QtGui.QBrush(qt.QtGui.QColor(resources.Color.Hex.red)) if missing
                                       else qt.QtGui.QBrush())
                    item.setToolTip("File unavailable: assignment retained; this row will be skipped." if missing
                                    else TOKEN_HELP)
        finally:
            self.table.blockSignals(blocked)
        label = pairs.INPUT_MODE_LABELS.get(self.task.get_input_mode(), "Unknown Mode")
        suffix = f"; {missing_count} unavailable pair(s) retained" if missing_count else ""
        status = name_error or f"{index} input(s){suffix}"
        self.status_label.setText(f"Running: {label} - {status}")
        self.status_label.setStyleSheet(f"color: {resources.Color.Hex.orange};" if name_error else "")
        self.buttons["export"].setEnabled(self.table.rowCount() > 0)
        self.buttons["show_hidden"].setEnabled(bool(self.task.settings.get("excluded_files")))
        self.update_input_feedback()

    def update_input_feedback(self):
        """Updates file and pair counts without replacing an active table editor."""
        try:
            statistics = self.task.get_file_statistics(self.project)
        except (ValueError, TypeError, OSError) as exception:
            self.input_count_label.setText(f"Unable to resolve input statistics: {exception}")
            return
        extra_rows = [
            [("Pairs", statistics["pair_count"]), ("Assigned Pairs", statistics["assigned_count"]),
             ("Unassigned Pairs", statistics["unassigned_count"])],
            [("Inactive Pairs", statistics["inactive_count"])],
        ]
        if self.task.get_input_mode() == pairs.INPUT_MODE_FOLDER:
            extra_rows[-1].append(("Hidden Pairs", statistics["hidden_count"]))
            extra_rows.append([("Unavailable Files", statistics["unavailable_count"]),
                               ("Missing Files with Strings", statistics["missing_assigned_count"])])
        else:
            extra_rows[-1].extend([("Unnamed Pairs", statistics["unnamed_count"]),
                                   ("Invalid Names", statistics["invalid_name_count"])])
        self.input_feedback.set_statistics(statistics, extra_rows=extra_rows)

    def add_row(self, checked=False):
        """Appends a manual pair and starts editing its custom name.

        Args:
            checked (bool, optional): Ignored action state.
        """
        if self.task.get_input_mode() != pairs.INPUT_MODE_MANUAL:
            return
        row = self.insert_pair(pairs.create_pair())
        self.commit()
        self.table.setCurrentCell(row, FILE_COLUMN)
        self.table.editItem(self.table.item(row, FILE_COLUMN))

    def remove_rows(self, checked=False, rows=None):
        """Deletes manual pairs or hides folder pairs while preserving their stored values.

        Args:
            checked (bool, optional): Ignored action state.
            rows (list, optional): Rows to remove; uses selected rows by default.
        """
        rows = self.get_selected_rows() if rows is None else rows
        if not rows:
            return
        manual = self.task.get_input_mode() == pairs.INPUT_MODE_MANUAL
        if not manual:
            excluded = list(self.task.settings.get("excluded_files") or [])
            excluded.extend(pair["input_file"] for pair in self.get_row_pairs(rows))
            self.set_task_setting(sorted(set(excluded)), key="excluded_files")
        blocked = self.table.blockSignals(True)
        try:
            for row in sorted(rows, reverse=True):
                self.table.removeRow(row)
        finally:
            self.table.blockSignals(blocked)
        self.commit()
        action = "Deleted" if manual else "Hidden"
        self.emit_status_message(f"{action} {len(rows)} input pair(s).")

    def remove_button_row(self, checked=False):
        """Deletes or hides the row belonging to the clicked action button.

        Args:
            checked (bool, optional): Ignored button state.
        """
        button = self.sender()
        for row in range(self.table.rowCount()):
            if self.table.cellWidget(row, DELETE_COLUMN) == button:
                self.remove_rows(rows=[row])
                return

    def duplicate_rows(self, checked=False):
        """Duplicates selected manual pairs with fresh IDs.

        Args:
            checked (bool, optional): Ignored action state.
        """
        if self.task.get_input_mode() != pairs.INPUT_MODE_MANUAL:
            return
        rows = self.get_selected_rows()
        for offset, pair in enumerate(self.get_row_pairs(rows)):
            self.insert_pair(pairs.create_pair(pair["input_file"], pair["input_string"], pair["enabled"]),
                             row=rows[-1] + offset + 1)
        self.commit()

    def set_rows_active(self, checked=False, active=True, selected=False, invert=False):
        """Changes multiple active states with one final commit.

        Args:
            checked (bool, optional): Ignored action state.
            active (bool, optional): Requested active state.
            selected (bool, optional): Whether to limit changes to selected rows.
            invert (bool, optional): Whether to toggle each current state.
        """
        rows = self.get_selected_rows() if selected else range(self.table.rowCount())
        for row in rows:
            checkbox = self.table.cellWidget(row, ACTIVE_COLUMN).checkbox
            blocked = checkbox.blockSignals(True)
            checkbox.setChecked(not checkbox.isChecked() if invert else active)
            checkbox.blockSignals(blocked)
        self.commit()

    def remove_empty_rows(self, checked=False):
        """Removes empty manual rows or hides folder rows with no descriptions.

        Args:
            checked (bool, optional): Ignored action state.
        """
        manual = self.task.get_input_mode() == pairs.INPUT_MODE_MANUAL
        rows = [row for row, pair in enumerate(self.get_row_pairs()) if not pair["input_string"].strip()
                and (not manual or not pair["input_file"].strip())]
        self.remove_rows(rows=rows)

    def restore_folder_files(self, checked=False):
        """Shows hidden folder rows again with their original descriptions and active states.

        Args:
            checked (bool, optional): Ignored action state.
        """
        self.set_task_setting([], key="excluded_files")
        self.refresh_files()

    def get_export_data(self, rows=None):
        """Builds a versioned JSON payload retaining missing and inactive rows.

        Args:
            rows (list, optional): Rows to include; exports all by default.

        Returns:
            dict: Portable JSON pair document.
        """
        return {"version": pairs.PAIR_FILE_VERSION, "mode": self.task.get_input_mode(),
                "pairs": self.get_row_pairs(rows)}

    def copy_rows(self, checked=False):
        """Copies selected pairs or all pairs as JSON.

        Args:
            checked (bool, optional): Ignored action state.
        """
        data = self.get_export_data(self.get_selected_rows() or None)
        qt.QtWidgets.QApplication.clipboard().setText(json.dumps(data, ensure_ascii=False, indent=4))
        self.emit_status_message(f"Copied {len(data['pairs'])} input pair(s).")

    def apply_pair_data(self, data):
        """Validates and merges imported rows, preserving unrelated pairs and inactive mode data.

        Args:
            data (dict): Decoded JSON pair document.

        Raises:
            ValueError: For malformed data, without changing the existing task.
        """
        mode, incoming = pairs.read_pair_data(data)
        key = "manual_pairs" if mode == pairs.INPUT_MODE_MANUAL else "folder_pairs"
        existing = [dict(row) for row in self.task.settings[key]]
        pairs.validate_pair_rows(existing, mode)
        if mode == pairs.INPUT_MODE_MANUAL:
            existing.extend(pairs.create_pair(row["input_file"], row["input_string"], row.get("enabled", True))
                            for row in incoming)
        else:
            lookup = {pairs.get_pair_key(row["input_file"]): row for row in existing}
            for row in incoming:
                file_key = pairs.get_pair_key(row["input_file"])
                if file_key in lookup:
                    lookup[file_key].update(input_string=row["input_string"], enabled=row.get("enabled", True))
                else:
                    new_row = pairs.create_pair(row["input_file"], row["input_string"], row.get("enabled", True))
                    existing.append(new_row)
                    lookup[file_key] = new_row
            excluded = [filename for filename in self.task.settings.get("excluded_files", [])
                        if pairs.get_pair_key(filename) not in {pairs.get_pair_key(row["input_file"])
                                                               for row in incoming}]
            self.set_task_setting(excluded, key="excluded_files")
        self.set_task_setting(existing, key=key)
        self.set_input_mode(mode=mode)
        self.emit_status_message(f"Imported {len(incoming)} input pair(s).")

    def paste_pairs(self, checked=False):
        """Pastes JSON pairs or two tab-separated columns from a spreadsheet.

        Args:
            checked (bool, optional): Ignored action state.
        """
        text = qt.QtWidgets.QApplication.clipboard().text()
        try:
            if text.lstrip().startswith("{"):
                data = json.loads(text)
            else:
                rows = []
                for line in text.splitlines():
                    if not line.strip():
                        continue
                    if "\t" not in line:
                        raise ValueError("Paste two tab-separated columns: input file and input string.")
                    filename, description = line.split("\t", 1)
                    rows.append(pairs.create_pair(filename, description))
                data = {"version": pairs.PAIR_FILE_VERSION, "mode": self.task.get_input_mode(), "pairs": rows}
            self.apply_pair_data(data)
        except (ValueError, TypeError) as exception:
            self.emit_status_message(f"Unable to paste input pairs: {exception}", status="warning")

    def get_json_directory(self):
        """Gets the initial directory for import and export dialogs.

        Returns:
            str: Existing project folder or user home folder.
        """
        root = self.project.get_project_dir() if self.project else ""
        return root if root and os.path.isdir(root) else os.path.expanduser("~")

    def import_pairs(self, checked=False):
        """Imports a versioned JSON file into its corresponding pair mode.

        Args:
            checked (bool, optional): Ignored action state.
        """
        path = file_dialog.file_dialog(parent=self, caption="Import Input Pairs", file_filter=JSON_FILTER,
                                       starting_directory=self.get_json_directory(), ok_caption="Import")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8-sig") as pair_file:
                self.apply_pair_data(json.load(pair_file))
        except (OSError, ValueError, TypeError) as exception:
            self.emit_status_message(f"Unable to import input pairs: {exception}", status="warning")

    def export_pairs(self, checked=False):
        """Exports every visible pair, including missing files and inactive rows.

        Args:
            checked (bool, optional): Ignored action state.
        """
        path = file_dialog.file_dialog(parent=self, caption="Export Input Pairs", write_mode=True,
                                       file_filter=JSON_FILTER, starting_directory=self.get_json_directory(),
                                       ok_caption="Export")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8", newline="\n") as pair_file:
                json.dump(self.get_export_data(), pair_file, ensure_ascii=False, indent=4)
                pair_file.write("\n")
        except OSError as exception:
            self.emit_status_message(f"Unable to export input pairs: {exception}", status="warning")
            return
        self.emit_status_message(f"Exported {self.table.rowCount()} input pair(s) to {path}.")

    def show_context_menu(self, position):
        """Shows row editing, activation, JSON import/export, and folder refresh actions.

        Args:
            position (QPoint): Requested table viewport position.
        """
        row = self.table.rowAt(position.y())
        if row >= 0 and row not in self.get_selected_rows():
            self.table.selectRow(row)
        selected = bool(self.get_selected_rows())
        has_rows = self.table.rowCount() > 0
        manual = self.task.get_input_mode() == pairs.INPUT_MODE_MANUAL
        menu = self.context_menu
        menu.clear()
        actions = []
        if manual:
            actions.extend([("Add Pair", resources.Icon.ui_add, True, self.add_row),
                            ("Duplicate Selected", resources.Icon.rigger_action_duplicate_grayscale,
                             selected, self.duplicate_rows)])
        else:
            actions.extend([("Refresh Files", resources.Icon.ui_reset, True, self.refresh_files),
                            ("Show Hidden", resources.Icon.ui_reset,
                             bool(self.task.settings.get("excluded_files")), self.restore_folder_files)])
        actions.extend([
            ("Copy Selected" if selected else "Copy All", resources.Icon.rigger_action_copy_grayscale,
             has_rows, self.copy_rows),
            ("Paste Pairs", resources.Icon.rigger_action_paste_grayscale, True, self.paste_pairs),
            ("Import JSON", resources.Icon.library_import, True, self.import_pairs),
            ("Export JSON", resources.Icon.library_export, has_rows, self.export_pairs),
            (None, None, None, None),
            ("Activate All", resources.Icon.ui_checkbox_checked, has_rows, self.set_rows_active),
            ("Deactivate All", resources.Icon.ui_checkbox_unchecked, has_rows,
             partial(self.set_rows_active, active=False)),
            ("Invert Active", resources.Icon.ui_checkbox_invert, has_rows, partial(self.set_rows_active, invert=True)),
            ("Activate Selected", resources.Icon.ui_rows_selected_checked, selected,
             partial(self.set_rows_active, selected=True)),
            ("Deactivate Selected", resources.Icon.ui_rows_selected_unchecked, selected,
             partial(self.set_rows_active, selected=True, active=False)),
            (None, None, None, None),
            ("Remove Empty Pairs" if manual else "Hide Unassigned Pairs", resources.Icon.ui_remove_blank_lines,
             has_rows, self.remove_empty_rows),
            ("Delete Selected" if manual else "Hide Selected", resources.Icon.ui_trash if manual else None,
             selected, self.remove_rows)])
        for label, icon, enabled, callback in actions:
            if label is None:
                menu.addSeparator()
                continue
            action = menu.addAction(label)
            if icon:
                action.setIcon(qt.QtGui.QIcon(icon))
            action.setEnabled(enabled)
            action.triggered.connect(callback)
        menu.popup(self.table.viewport().mapToGlobal(position))
