"""Mode-based inputs for the Batch Processor Input Strings task."""

import os
from functools import partial
from gt.ui import qt_import as qt
from gt.ui import resource_library as ui_res_lib
from gt.ui import file_dialog as ui_file_dialog
from gt.ui.qt_utils import TablePlaceholderDelegate
from gt.tools.batch_processor.tasks import task_input_strings
from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask

ACTIVE_COLUMN = 0
VALUE_COLUMN = 1
DELETE_COLUMN = 2
NUMBER_LIMIT = 1000000
FILE_PREVIEW_LIMIT = 500
LINE_FILE_FILTER = "Text Files (*.txt);;All Files (*);;"
TOKEN_HELP = (
    "Use {input-string} and {input-string-index} in task settings and paths, or "
    "env['input-string'] and env['input-string-index'] in Python scripts with \"Pass Env\" enabled."
)
TABLE_TOOLTIP = (
    "One string per row; each active row starts in a new empty Maya scene.\n"
    f"{TOKEN_HELP}\n"
    "Unchecked and blank rows are skipped and excluded from the index; duplicates are kept.\n"
    "Double-click to edit. Right-click for more actions. Delete removes selected rows."
)
MODE_TOOLTIPS = {
    task_input_strings.INPUT_MODE_TABLE: "Run one job per active, nonblank row of the table below.",
    task_input_strings.INPUT_MODE_NUMBERS: ("Run one job per whole number from Start to End (inclusive). "
                                            "Counts down when End is lower than Start."),
    task_input_strings.INPUT_MODE_FILE: ("Run one job per nonblank line of a UTF-8 text file, read when the "
                                         "batch runs. The table is not used or modified."),
}


class AttrWidgetInputStringsTask(AttrWidgetTask):
    """Edits the input mode and its source without rebuilding the active control."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, **kwargs):
        """Builds the mode selector, one page per mode, and the segmentation section.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskInputStrings, optional): Edited task.
            project (BatchProcessorModel, optional): Owning project.
            refresh_parent_func (callable, optional): Parent refresh callback.
            **kwargs: Additional widget arguments.
        """
        super().__init__(parent=parent, task=task, project=project,
                         refresh_parent_func=refresh_parent_func, **kwargs)
        self.add_widget_separator_line(label_text="Input Strings")
        self.build_mode_selector()
        self.mode_pages = {}
        for mode, build_page in ((task_input_strings.INPUT_MODE_TABLE, self.build_table_page),
                                 (task_input_strings.INPUT_MODE_NUMBERS, self.build_number_page),
                                 (task_input_strings.INPUT_MODE_FILE, self.build_file_page)):
            page = qt.QtWidgets.QWidget()
            page_layout = qt.QtWidgets.QVBoxLayout(page)
            page_layout.setContentsMargins(0, 0, 0, 0)
            build_page(page_layout)
            page.setVisible(False)
            self.content_layout.addWidget(page)
            self.mode_pages[mode] = page
        states = task_input_strings.get_row_enabled_states(task.settings)
        self.insert_rows(task.settings.get("strings") or [], states=states)
        self.table.itemChanged.connect(self.commit)
        self.table.itemSelectionChanged.connect(self.update_status)
        self.add_segmentation_section(
            main_label="Start New Segment", main_key="start_new_input_list",
            main_tooltip="Replace earlier inputs with these strings for the following tasks.")
        self.content_layout.addStretch()
        self.update_row_indexes()
        self.show_mode(task_input_strings.get_input_mode(task.settings))

    def build_mode_selector(self):
        """Adds the exclusive mode buttons and the status line that names the running mode."""
        layout = self.add_labeled_layout("Mode", tooltip="Choose where this task gets its inputs.")
        self.mode_button_group = qt.QtWidgets.QButtonGroup(self)
        self.mode_button_group.setExclusive(True)
        self.mode_buttons = {}
        highlight = ui_res_lib.Color.Hex.blue_pastel
        checked_style = (f"QPushButton:checked {{ background-color: {highlight}; border: 1px solid {highlight}; "
                         "border-radius: 3px; color: #FFFFFF; font-weight: bold; }")
        for mode in task_input_strings.INPUT_MODES:
            button = qt.QtWidgets.QPushButton(task_input_strings.INPUT_MODE_LABELS[mode])
            button.setCheckable(True)
            button.setMinimumHeight(30)
            button.setStyleSheet(checked_style)
            button.setToolTip(MODE_TOOLTIPS[mode])
            button.clicked.connect(partial(self.set_input_mode, mode=mode))
            self.mode_button_group.addButton(button)
            layout.addWidget(button)
            self.mode_buttons[mode] = button
        self.status_label = qt.QtWidgets.QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setToolTip(TOKEN_HELP)
        self.content_layout.addWidget(self.status_label)

    def build_table_page(self, page_layout):
        """Adds the active/value/delete table, its context menu, and its buttons.

        Args:
            page_layout (QVBoxLayout): String Table page layout.
        """
        self.table = qt.QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Active", "String Value", ""])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(ACTIVE_COLUMN, qt.QtLib.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(VALUE_COLUMN, qt.QtLib.QHeaderView.Stretch)
        header.setSectionResizeMode(DELETE_COLUMN, qt.QtLib.QHeaderView.ResizeToContents)
        self.table.horizontalHeaderItem(ACTIVE_COLUMN).setToolTip("Use this string when running.")
        self.table.setSelectionBehavior(qt.QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(qt.QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setMinimumHeight(180)
        self.table.setToolTip(TABLE_TOOLTIP)
        self.placeholder_delegate = TablePlaceholderDelegate("Enter a string or motion description",
                                                             [VALUE_COLUMN], parent=self.table)
        self.table.setItemDelegateForColumn(VALUE_COLUMN, self.placeholder_delegate)
        self.table.setContextMenuPolicy(qt.QtCore.Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.context_menu = qt.QtWidgets.QMenu(self)
        shortcut_class = getattr(qt.QtGui, "QShortcut", None) or getattr(qt.QtWidgets, "QShortcut")
        self.delete_shortcut = shortcut_class(qt.QtGui.QKeySequence("Delete"), self.table)
        self.delete_shortcut.setContext(qt.QtCore.Qt.WidgetShortcut)
        self.delete_shortcut.activated.connect(self.remove_rows)
        page_layout.addWidget(self.table)
        actions = qt.QtWidgets.QHBoxLayout()
        self.buttons = {}
        for key, label, icon, tooltip, callback in (
                ("add", "Add", ui_res_lib.Icon.ui_add, "Append an empty row.", self.add_row),
                ("paste", "Paste Lines", ui_res_lib.Icon.rigger_action_paste_grayscale,
                 "Append one row per clipboard line.", self.paste_lines),
                ("import", "Import", ui_res_lib.Icon.library_import,
                 "Append one row per line of a text file.", self.import_lines),
                ("export", "Export", ui_res_lib.Icon.library_export,
                 "Save every row, active or not, as one line of a text file.", self.export_lines)):
            button = qt.QtWidgets.QPushButton(label)
            button.setIcon(qt.QtGui.QIcon(icon))
            button.setToolTip(tooltip)
            button.clicked.connect(callback)
            actions.addWidget(button)
            self.buttons[key] = button
        actions.addStretch()
        page_layout.addLayout(actions)

    def build_number_page(self, page_layout):
        """Adds the number range bounds, step, odd/even filter, skip list, and a value preview.

        Args:
            page_layout (QVBoxLayout): Number Range page layout.
        """
        tooltip = MODE_TOOLTIPS[task_input_strings.INPUT_MODE_NUMBERS]
        row = self.add_labeled_layout("Range", tooltip=tooltip, parent_layout=page_layout)
        self.number_spin_boxes = {}
        for key, label, minimum, field_tooltip in (
                ("number_start", "Start", -NUMBER_LIMIT, tooltip),
                ("number_end", "End", -NUMBER_LIMIT, tooltip),
                ("number_step", "Step", 1, "Use every Nth number, counted from Start. 1 uses every number.")):
            label_widget = qt.QtWidgets.QLabel(f"{label}:")
            label_widget.setToolTip(field_tooltip)
            spin_box = qt.QtWidgets.QSpinBox()
            spin_box.setRange(minimum, NUMBER_LIMIT)
            spin_box.setValue(int(self.task.settings.get(key) or 0))
            spin_box.setMinimumHeight(28)
            spin_box.setToolTip(field_tooltip)
            spin_box.valueChanged.connect(partial(self.set_number_bound, key=key))
            row.addWidget(label_widget)
            row.addWidget(spin_box)
            self.number_spin_boxes[key] = spin_box
        row.addStretch()
        filter_tooltip = "Keep every number in the range, or only the odd or only the even ones."
        filter_row = self.add_labeled_layout("Filter", tooltip=filter_tooltip, parent_layout=page_layout)
        self.number_filter_combo = qt.QtWidgets.QComboBox()
        self.number_filter_combo.setMinimumHeight(28)
        self.number_filter_combo.setToolTip(filter_tooltip)
        for number_filter in task_input_strings.NUMBER_FILTERS:
            self.number_filter_combo.addItem(task_input_strings.NUMBER_FILTER_LABELS[number_filter], number_filter)
        current_filter = self.task.settings.get("number_filter", task_input_strings.NUMBER_FILTER_ALL)
        self.number_filter_combo.setCurrentIndex(max(0, self.number_filter_combo.findData(current_filter)))
        self.number_filter_combo.currentIndexChanged.connect(self.set_number_filter)
        filter_row.addWidget(self.number_filter_combo)
        filter_row.addStretch()
        skip_tooltip = ("Numbers to leave out, separated by commas or spaces. Use 10-12 for an inclusive range. "
                        "Skipped numbers are not counted in {input-string-index}.")
        skip_row = self.add_labeled_layout("Skip", tooltip=skip_tooltip, parent_layout=page_layout)
        self.number_skip_field = self.create_text_field(text=self.task.settings.get("number_skip") or "",
                                                        placeholder="Numbers to skip, e.g. 4, 8, 10-12",
                                                        tooltip=skip_tooltip)
        self.number_skip_field.textChanged.connect(self.set_number_skip)
        skip_row.addWidget(self.number_skip_field)
        self.number_preview_label = qt.QtWidgets.QLabel()
        self.number_preview_label.setWordWrap(True)
        page_layout.addWidget(self.number_preview_label)

    def build_file_page(self, page_layout):
        """Adds the input file path field and a read-only preview of the lines that will run.

        Args:
            page_layout (QVBoxLayout): Input File page layout.
        """
        tooltip = (f"{MODE_TOOLTIPS[task_input_strings.INPUT_MODE_FILE]} Blank lines are skipped. "
                   "Paths inside the project are stored relative to {project-dir}.")
        file_widgets = self.add_path_template_field(
            "Input File", self.task.settings.get("input_file_path") or "",
            partial(self.set_task_setting, key="input_file_path"), placeholder="Text file with one input per line",
            tooltip=tooltip, file_filter=LINE_FILE_FILTER, return_widgets=True, parent_layout=page_layout)
        self.file_path_field = file_widgets["field"]
        self.file_path_field.textChanged.connect(self.update_status)
        reload_button = qt.QtWidgets.QPushButton()
        reload_button.setIcon(qt.QtGui.QIcon(ui_res_lib.Icon.util_reload_file))
        reload_button.setToolTip("Read the file again and refresh the preview.")
        reload_button.clicked.connect(self.update_status)
        file_widgets["layout"].addWidget(reload_button)
        self.file_preview = qt.QtWidgets.QPlainTextEdit()
        self.file_preview.setReadOnly(True)
        self.file_preview.setMinimumHeight(140)
        self.file_preview.setToolTip(f"Lines that will run, in order.\n{TOKEN_HELP}")
        page_layout.addWidget(self.file_preview)

    def create_delete_button(self):
        """Creates a trash button that removes the row that owns it.

        Returns:
            QPushButton: Row delete button.
        """
        return self.create_table_action_button(
            self.remove_button_row, "Remove this string.",
            icon_path=ui_res_lib.Icon.ui_trash, accessible_name="Delete String")

    def create_active_checkbox(self, enabled):
        """Creates a checkbox centered in its cell that marks a row for use.

        Args:
            enabled (bool): Initial active state.

        Returns:
            QWidget: Cell container exposing the checkbox as its "checkbox" attribute.
        """
        checkbox = qt.QtWidgets.QCheckBox()
        checkbox.setStyleSheet("QCheckBox { spacing: 0px; padding: 0px; margin: 0px; }")
        checkbox.setChecked(bool(enabled))
        checkbox.setToolTip("Use this string when running.")
        checkbox.toggled.connect(self.commit)
        container = qt.QtWidgets.QWidget()
        layout = qt.QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(qt.QtLib.AlignmentFlag.AlignCenter)
        layout.addWidget(checkbox)
        container.checkbox = checkbox
        return container

    def get_active_checkbox(self, row):
        """Gets the active checkbox of a row.

        Args:
            row (int): Table row.

        Returns:
            QCheckBox: Row checkbox.
        """
        return self.table.cellWidget(row, ACTIVE_COLUMN).checkbox

    def set_active_states(self, states):
        """Sets row checkboxes without committing each change, then commits once.

        Args:
            states (dict): Active flag keyed by row.
        """
        for row, active in states.items():
            checkbox = self.get_active_checkbox(row)
            blocked = checkbox.blockSignals(True)
            try:
                checkbox.setChecked(bool(active))
            finally:
                checkbox.blockSignals(blocked)
        self.commit()

    def insert_rows(self, values, states=None, row=None):
        """Inserts values without committing partial row changes.

        Args:
            values (list): Literal row values.
            states (list, optional): Active flags aligned with values; defaults to active.
            row (int, optional): Insertion row; appends when omitted.

        Returns:
            int: First inserted row.
        """
        first_row = self.table.rowCount() if row is None else max(0, min(row, self.table.rowCount()))
        blocked = self.table.blockSignals(True)
        try:
            for offset, value in enumerate(values):
                enabled = states[offset] if states and offset < len(states) else True
                current_row = first_row + offset
                self.table.insertRow(current_row)
                self.table.setCellWidget(current_row, ACTIVE_COLUMN, self.create_active_checkbox(enabled))
                self.table.setItem(current_row, VALUE_COLUMN, qt.QtWidgets.QTableWidgetItem(value))
                self.table.setCellWidget(current_row, DELETE_COLUMN, self.create_delete_button())
        finally:
            self.table.blockSignals(blocked)
        return first_row

    def append_value(self, value):
        """Appends a value without committing partial row changes.

        Args:
            value (str): Literal row value.
        """
        self.insert_rows([value])

    def get_selected_rows(self):
        """Gets the selected row numbers in table order.

        Returns:
            list: Sorted row numbers.
        """
        return sorted({index.row() for index in self.table.selectedIndexes()})

    def get_row_values(self, rows=None):
        """Gets row text in table order.

        Args:
            rows (list, optional): Rows to read; reads every row when omitted.

        Returns:
            list: Row values.
        """
        rows = range(self.table.rowCount()) if rows is None else rows
        return [self.table.item(row, VALUE_COLUMN).text() for row in rows]

    def is_row_active(self, row):
        """Checks whether a row is marked for use.

        Args:
            row (int): Table row.

        Returns:
            bool: True when the row checkbox is checked.
        """
        return self.get_active_checkbox(row).isChecked()

    def add_row(self, checked=False, row=None):
        """Adds an editable blank row and starts editing it.

        Args:
            checked (bool, optional): Ignored QPushButton signal value.
            row (int, optional): Insertion row; appends when omitted.
        """
        new_row = self.insert_rows([""], row=row)
        self.table.setCurrentCell(new_row, VALUE_COLUMN)
        self.commit()
        self.table.editItem(self.table.item(new_row, VALUE_COLUMN))

    def remove_rows(self, checked=False, rows=None):
        """Removes rows and retains the relative order of remaining values.

        Args:
            checked (bool, optional): Ignored action signal value.
            rows (list, optional): Rows to remove; removes the selection when omitted.
        """
        rows = self.get_selected_rows() if rows is None else rows
        if not rows:
            return
        for row in sorted(rows, reverse=True):
            self.table.removeRow(row)
        self.commit()
        self.emit_status_message(f"Removed {len(rows)} input string(s).")

    def remove_button_row(self, checked=False):
        """Removes the row that owns the clicked trash button.

        Args:
            checked (bool, optional): Ignored QPushButton signal value.
        """
        button = self.sender()
        row = next((index for index in range(self.table.rowCount())
                    if self.table.cellWidget(index, DELETE_COLUMN) == button), -1)
        if row >= 0:
            self.remove_rows(rows=[row])

    def add_lines(self, lines, row=None, source="clipboard"):
        """Inserts text lines as separate literal values.

        Args:
            lines (list): Values to add.
            row (int, optional): Insertion row; appends when omitted.
            source (str, optional): Source name used by the status message.
        """
        self.insert_rows(lines, row=row)
        self.commit()
        self.emit_status_message(f"Added {len(lines)} input string row(s) from {source}.")

    def paste_lines(self, checked=False, row=None):
        """Adds clipboard lines as separate literal values.

        Args:
            checked (bool, optional): Ignored signal value.
            row (int, optional): Insertion row; appends when omitted.
        """
        self.add_lines(qt.QtWidgets.QApplication.clipboard().text().splitlines(), row=row)

    def copy_rows(self, checked=False):
        """Copies the selected rows, or every row when nothing is selected, one line per row.

        Args:
            checked (bool, optional): Ignored action signal value.
        """
        rows = self.get_selected_rows() or list(range(self.table.rowCount()))
        qt.QtWidgets.QApplication.clipboard().setText("\n".join(self.get_row_values(rows)))
        self.emit_status_message(f"Copied {len(rows)} input string(s) to the clipboard.")

    def duplicate_rows(self, checked=False):
        """Inserts copies of the selected rows directly below the last selected row.

        Args:
            checked (bool, optional): Ignored action signal value.
        """
        rows = self.get_selected_rows()
        if not rows:
            return
        states = [self.is_row_active(row) for row in rows]
        self.insert_rows(self.get_row_values(rows), states=states, row=rows[-1] + 1)
        self.commit()
        self.emit_status_message(f"Duplicated {len(rows)} input string(s).")

    def set_rows_active(self, checked=False, active=True, rows=None):
        """Checks or unchecks rows with a single commit.

        Args:
            checked (bool, optional): Ignored action signal value.
            active (bool, optional): Requested active state.
            rows (list, optional): Rows to change; changes every row when omitted.
        """
        rows = range(self.table.rowCount()) if rows is None else rows
        self.set_active_states({row: active for row in rows})

    def set_selected_rows_active(self, checked=False, active=True):
        """Checks or unchecks the selected rows.

        Args:
            checked (bool, optional): Ignored action signal value.
            active (bool, optional): Requested active state.
        """
        self.set_rows_active(active=active, rows=self.get_selected_rows())

    def invert_active_rows(self, checked=False):
        """Toggles the active state of every row with a single commit.

        Args:
            checked (bool, optional): Ignored action signal value.
        """
        self.set_active_states({row: not self.is_row_active(row) for row in range(self.table.rowCount())})

    def remove_blank_rows(self, checked=False):
        """Removes rows whose text is empty or whitespace only.

        Args:
            checked (bool, optional): Ignored action signal value.
        """
        rows = [row for row, value in enumerate(self.get_row_values()) if not value.strip()]
        self.remove_rows(rows=rows)

    def show_context_menu(self, position):
        """Shows row editing, clipboard, and activation actions.

        Args:
            position (QPoint): Requested position within the table viewport.
        """
        row = self.table.rowAt(position.y())
        if row >= 0 and row not in self.get_selected_rows():
            self.table.selectRow(row)
        has_selection = bool(self.get_selected_rows())
        has_rows = self.table.rowCount() > 0
        insert_row = row + 1 if row >= 0 else None
        menu = self.context_menu
        menu.clear()
        for label, icon, enabled, callback in (
                ("Add Line", ui_res_lib.Icon.ui_add, True, partial(self.add_row, row=insert_row)),
                ("Duplicate Selected", ui_res_lib.Icon.rigger_action_duplicate_grayscale, has_selection,
                 self.duplicate_rows),
                (None, None, None, None),
                ("Copy Selected" if has_selection else "Copy All", ui_res_lib.Icon.rigger_action_copy_grayscale,
                 has_rows, self.copy_rows),
                ("Paste Lines", ui_res_lib.Icon.rigger_action_paste_grayscale, True,
                 partial(self.paste_lines, row=insert_row)),
                (None, None, None, None),
                ("Activate All", ui_res_lib.Icon.ui_checkbox_checked, has_rows,
                 partial(self.set_rows_active, active=True)),
                ("Deactivate All", ui_res_lib.Icon.ui_checkbox_unchecked, has_rows,
                 partial(self.set_rows_active, active=False)),
                ("Invert Active", ui_res_lib.Icon.ui_checkbox_invert, has_rows, self.invert_active_rows),
                ("Activate Selected", ui_res_lib.Icon.ui_rows_selected_checked, has_selection,
                 partial(self.set_selected_rows_active, active=True)),
                ("Deactivate Selected", ui_res_lib.Icon.ui_rows_selected_unchecked, has_selection,
                 partial(self.set_selected_rows_active, active=False)),
                (None, None, None, None),
                ("Remove Blank Lines", ui_res_lib.Icon.ui_remove_blank_lines, has_rows, self.remove_blank_rows),
                ("Delete Selected", ui_res_lib.Icon.ui_trash, has_selection, self.remove_rows)):
            if label is None:
                menu.addSeparator()
                continue
            action = menu.addAction(label)
            action.setIcon(qt.QtGui.QIcon(icon))
            action.setEnabled(enabled)
            action.triggered.connect(callback)
        menu.popup(self.table.viewport().mapToGlobal(position))

    def get_line_file_directory(self):
        """Gets the starting folder for line import and export dialogs.

        Returns:
            str: Project folder when available, otherwise the user home folder.
        """
        project_dir = self.project.get_project_dir() if self.project else ""
        return project_dir if project_dir and os.path.isdir(project_dir) else os.path.expanduser("~")

    def import_lines(self, checked=False):
        """Appends one row per line of a user-selected UTF-8 text file.

        Args:
            checked (bool, optional): Ignored QPushButton signal value.
        """
        file_path = ui_file_dialog.file_dialog(
            parent=self, caption="Import Input Strings", starting_directory=self.get_line_file_directory(),
            file_filter=LINE_FILE_FILTER, ok_caption="Import")
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8-sig") as line_file:
                lines = line_file.read().splitlines()
        except (OSError, UnicodeDecodeError) as exception:
            self.emit_status_message(f"Unable to import input strings: {exception}", status="warning")
            return
        self.add_lines(lines, source=os.path.basename(file_path))

    def export_lines(self, checked=False):
        """Writes every row as one line of a user-selected UTF-8 text file.

        Args:
            checked (bool, optional): Ignored QPushButton signal value.
        """
        values = self.get_row_values()
        if not values:
            self.emit_status_message("No input strings to export.", status="warning")
            return
        file_path = ui_file_dialog.file_dialog(
            parent=self, caption="Export Input Strings", write_mode=True,
            starting_directory=self.get_line_file_directory(), file_filter=LINE_FILE_FILTER, ok_caption="Export")
        if not file_path:
            return
        try:
            with open(file_path, "w", encoding="utf-8", newline="\n") as line_file:
                line_file.write("\n".join(values) + "\n")
        except OSError as exception:
            self.emit_status_message(f"Unable to export input strings: {exception}", status="warning")
            return
        self.emit_status_message(f"Exported {len(values)} input string(s) to {file_path}.")

    def set_input_mode(self, checked=False, mode=task_input_strings.INPUT_MODE_TABLE):
        """Stores the requested input mode and shows its page.

        Args:
            checked (bool, optional): Ignored QPushButton signal value.
            mode (str, optional): One of task_input_strings.INPUT_MODES.
        """
        if task_input_strings.get_input_mode(self.task.settings) == mode:
            self.show_mode(mode)
            return
        self.set_task_setting(mode, key="input_mode")
        self.show_mode(mode)
        label = task_input_strings.INPUT_MODE_LABELS[mode]
        self.emit_status_message(f'Task "{self.task.display_name}" now uses {label} mode.')

    def show_mode(self, mode):
        """Checks the mode button, shows the matching page, and refreshes the status line.

        Args:
            mode (str): One of task_input_strings.INPUT_MODES.
        """
        self.mode_buttons[mode].setChecked(True)
        for page_mode, page in self.mode_pages.items():
            page.setVisible(page_mode == mode)
        self.update_status()

    def set_number_bound(self, value, key):
        """Stores a number range bound.

        Args:
            value (int): New bound.
            key (str): "number_start", "number_end", or "number_step".
        """
        self.set_task_setting(int(value), key=key)
        self.update_status()

    def set_number_filter(self, index):
        """Stores the odd/even filter chosen in the combo box.

        Args:
            index (int): Selected combo box index.
        """
        self.set_task_setting(self.number_filter_combo.itemData(index), key="number_filter")
        self.update_status()

    def set_number_skip(self, text):
        """Stores the skip list text exactly as typed.

        Args:
            text (str): Skip list text.
        """
        self.set_task_setting(text, key="number_skip")
        self.update_status()

    def update_row_indexes(self):
        """Shows run indexes in the row header, leaving skipped rows unnumbered."""
        indexes = task_input_strings.get_row_indexes(self.task.settings)
        self.table.setVerticalHeaderLabels(["" if index is None else str(index) for index in indexes])

    def commit(self, unused_item=None):
        """Stores table edits without refreshing the parent panel.

        Args:
            unused_item (QTableWidgetItem, optional): Changed cell.
        """
        self.set_task_setting(self.get_row_values(), key="strings")
        self.set_task_setting([self.is_row_active(row) for row in range(self.table.rowCount())],
                              key="string_enabled")
        self.update_row_indexes()
        self.update_status()

    def get_mode_values(self):
        """Gets the values the active mode would run, or the first validation error.

        Returns:
            tuple: (list of values, str error message or empty string).
        """
        errors = self.task.validate(self.project).errors
        if errors:
            return [], errors[0]
        try:
            return self.task.get_input_values(self.project), ""
        except (OSError, UnicodeDecodeError) as exception:
            return [], str(exception)

    def update_status(self, *args):
        """Updates the running-mode status line, mode previews, and data-dependent actions.

        Args:
            *args: Ignored signal values.
        """
        mode = task_input_strings.get_input_mode(self.task.settings)
        label = task_input_strings.INPUT_MODE_LABELS[mode]
        values, error = self.get_mode_values()
        if error:
            self.status_label.setText(f"Running: {label} — {error}")
            self.status_label.setStyleSheet(f"color: {ui_res_lib.Color.Hex.orange};")
        else:
            self.status_label.setText(f"Running: {label} — {len(values)} input(s)")
            self.status_label.setStyleSheet("")
        self.buttons["export"].setEnabled(self.table.rowCount() > 0)
        if mode == task_input_strings.INPUT_MODE_NUMBERS:
            self.update_number_preview(values)
        elif mode == task_input_strings.INPUT_MODE_FILE:
            self.update_file_preview(values, error)

    def update_number_preview(self, values):
        """Shows the first and last numbers of the range.

        Args:
            values (list): Number values as strings.
        """
        if len(values) > 6:
            values = values[:3] + ["…"] + values[-2:]
        self.number_preview_label.setText(f"Values: {', '.join(values)}" if values else "")

    def update_file_preview(self, values, error):
        """Lists the numbered file lines that will run, or the reason nothing will run.

        Args:
            values (list): Nonblank file lines.
            error (str): Validation or read error, if any.
        """
        if error:
            self.file_preview.setPlainText(error)
            return
        lines = [f"{index}. {value}" for index, value in enumerate(values[:FILE_PREVIEW_LIMIT], 1)]
        if len(values) > FILE_PREVIEW_LIMIT:
            lines.append(f"… {len(values) - FILE_PREVIEW_LIMIT} more line(s)")
        self.file_preview.setPlainText("\n".join(lines))
