"""
Animation Evaluator Widgets - Reusable Qt widgets for editing evaluation presets.

PresetEditorWidget is shared by the Animation Evaluator tool and the Batch
Processor "Validate Animation" task, so both expose the same checks and thresholds.
"""

from gt.core.motion_eval import checks_base
from gt.core.motion_eval import presets
import gt.ui.qt_import as ui_qt
from functools import partial
import os

MAX_SPIN_VALUE = 1000000
PRESET_FILE_FILTER = "Evaluation Preset (*.json);;All Files (*)"
CHECK_TABLE_COLUMNS = ["On", "Check", "Weight", "Warn <", "Fail <", "Allow Fail"]
CHECK_TABLE_TOOLTIPS = [
    "Run this check.",
    "Check name. Select a row to edit its detection settings below.\n* marks a check changed from its defaults.",
    presets.SCORING_PARAMETERS_BY_KEY["weight"].tooltip,
    presets.SCORING_PARAMETERS_BY_KEY["warn_below"].tooltip,
    presets.SCORING_PARAMETERS_BY_KEY["fail_below"].tooltip,
    presets.SCORING_PARAMETERS_BY_KEY["allow_failure"].tooltip,
]
CHECK_COLUMN_KEYS = {0: "enabled", 2: "weight", 3: "warn_below", 4: "fail_below", 5: "allow_failure"}
SECTION_LABELS = {
    checks_base.MODE_GENERAL: "General Checks - any animated nodes",
    checks_base.MODE_BIPED: "Biped Checks - need a skeleton",
}
DISABLED_STYLESHEET = (
    "QLineEdit:disabled, QComboBox:disabled, QAbstractSpinBox:disabled, QTextEdit:disabled "
    "{ background-color: #353535; color: #6E6E6E; border-color: #3C3C3C; }"
    "QPushButton:disabled { background-color: #3A3A3A; color: #6E6E6E; }"
    "QCheckBox:disabled, QLabel:disabled { color: #6E6E6E; }"
)
HEADER_STYLESHEET = (
    "QHeaderView::section { background-color: #3A3A3A; color: #CCCCCC; border: none; "
    "border-right: 1px solid #2B2B2B; padding: 3px 4px; }"
)


class EmptyClickDeselector(ui_qt.QtCore.QObject):
    """Clears a view's selection when the user clicks an empty area of it."""

    def __init__(self, view):
        """Installs the filter on the view's viewport.

        Args:
            view (QAbstractItemView): Table, tree, or list view.
        """
        super().__init__(view)
        self.view = view
        view.viewport().installEventFilter(self)

    def eventFilter(self, watched, event):
        """Clears the selection on a press that hits no item.

        Args:
            watched (QObject): Viewport.
            event (QEvent): Event.

        Returns:
            bool: Always False, so the view still handles the event.
        """
        if event.type() == ui_qt.QtCore.QEvent.Type.MouseButtonPress:
            position = event.position().toPoint() if hasattr(event, "position") else event.pos()
            if not self.view.indexAt(position).isValid():
                self.view.clearSelection()
                self.view.setCurrentIndex(ui_qt.QtCore.QModelIndex())
        return False


def install_empty_click_deselect(view):
    """Makes a view deselect its items when an empty area is clicked.

    Args:
        view (QAbstractItemView): Table, tree, or list view.

    Returns:
        EmptyClickDeselector: Installed filter (parented to the view).
    """
    return EmptyClickDeselector(view)


def create_parameter_widget(spec, value, callback):
    """Creates an input widget for a parameter specification.

    Args:
        spec (ParameterSpec): Parameter description.
        value (object): Current value.
        callback (callable): Called with the new value when the user edits it.

    Returns:
        QWidget: Checkbox, spin box, combo box, or line edit.
    """
    if spec.value_type is bool:
        widget = ui_qt.QtWidgets.QCheckBox()
        widget.setChecked(bool(value))
        widget.toggled.connect(callback)
    elif spec.value_type is int:
        widget = ui_qt.QtWidgets.QSpinBox()
        widget.setRange(int(spec.minimum if spec.minimum is not None else -MAX_SPIN_VALUE),
                        int(spec.maximum if spec.maximum is not None else MAX_SPIN_VALUE))
        widget.setValue(int(value))
        widget.valueChanged.connect(callback)
    elif spec.value_type is float:
        widget = ui_qt.QtWidgets.QDoubleSpinBox()
        widget.setDecimals(int(spec.decimals))
        widget.setRange(float(spec.minimum if spec.minimum is not None else -MAX_SPIN_VALUE),
                        float(spec.maximum if spec.maximum is not None else MAX_SPIN_VALUE))
        widget.setSingleStep(10 ** -max(1, int(spec.decimals) - 1))
        widget.setValue(float(value))
        widget.valueChanged.connect(callback)
    elif spec.choices:
        widget = ui_qt.QtWidgets.QComboBox()
        widget.addItems(spec.choices)
        widget.setCurrentText(str(value))
        widget.currentTextChanged.connect(callback)
    else:
        widget = ui_qt.QtWidgets.QLineEdit(str(value))
        widget.setPlaceholderText("e.g. 10-24, 80")
        widget.editingFinished.connect(lambda: callback(widget.text()))
    widget.setToolTip(spec.tooltip or spec.label)
    return widget


def set_parameter_widget_value(widget, value):
    """Sets a parameter widget value without emitting change signals.

    Args:
        widget (QWidget): Widget created by create_parameter_widget.
        value (object): New value.
    """
    widget.blockSignals(True)
    try:
        if isinstance(widget, ui_qt.QtWidgets.QCheckBox):
            widget.setChecked(bool(value))
        elif isinstance(widget, (ui_qt.QtWidgets.QSpinBox, ui_qt.QtWidgets.QDoubleSpinBox)):
            widget.setValue(value)
        elif isinstance(widget, ui_qt.QtWidgets.QComboBox):
            widget.setCurrentText(str(value))
        elif isinstance(widget, ui_qt.QtWidgets.QLineEdit):
            widget.setText(str(value))
    finally:
        widget.blockSignals(False)


def get_text_width(widget, text):
    """Measures text with a widget's font.

    Args:
        widget (QWidget): Widget whose font is used.
        text (str): Text to measure.

    Returns:
        int: Width in pixels.
    """
    metrics = widget.fontMetrics()
    if hasattr(metrics, "horizontalAdvance"):
        return metrics.horizontalAdvance(text)
    return metrics.width(text)


def fit_combo_to_items(combo):
    """Makes a combo box wide enough to show its longest item.

    Args:
        combo (QComboBox): Combo box.
    """
    widest = max([get_text_width(combo, combo.itemText(index)) for index in range(combo.count())] or [0])
    combo.setMinimumWidth(widest + 42)


class PresetEditorWidget(ui_qt.QtWidgets.QWidget):
    """Edits an evaluation preset: global settings, check table, and per-check detection settings."""

    def __init__(self, parent=None, preset=None, changed_callback=None, show_mode=True, last_directory_getter=None):
        """Initializes the preset editor.

        Args:
            parent (QWidget, optional): Parent widget.
            preset (dict, optional): Stored (compact) preset.
            changed_callback (callable, optional): Called with the compact preset after every edit.
            show_mode (bool): Show the mode selector inside the editor.
            last_directory_getter (callable, optional): Returns the folder used by load/save dialogs.
        """
        super().__init__(parent)
        self.preset = presets.compact_preset(preset or presets.DEFAULT_PRESET)
        self.changed_callback = changed_callback
        self.last_directory_getter = last_directory_getter
        self.show_mode = show_mode
        self.mode_combo = None
        self.global_widgets = {}
        self.check_keys = []
        self.row_keys = []
        self.check_row_widgets = {}
        self.advanced_pages = {}
        self.advanced_widgets = {}
        self.selected_check_key = None
        self.checks_label = None
        self.check_table = None
        self.advanced_group = None
        self.advanced_stack = None
        self.summary_label = None
        self.build_ui()
        self.refresh()

    # ------------------------------------------------ Build ------------------------------------------------
    def build_ui(self):
        """Builds the editor layout."""
        layout = ui_qt.QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self.build_global_group())
        self.checks_label = ui_qt.QtWidgets.QLabel()
        self.checks_label.setStyleSheet("font-weight: bold;")
        self.checks_label.setToolTip(
            "General checks work on any animated nodes.\n"
            "Biped checks need a skeleton so feet, knees, and hips can be found."
        )
        layout.addWidget(self.checks_label)
        self.check_table = ui_qt.QtWidgets.QTableWidget(0, len(CHECK_TABLE_COLUMNS))
        self.check_table.setHorizontalHeaderLabels(CHECK_TABLE_COLUMNS)
        for column, tooltip in enumerate(CHECK_TABLE_TOOLTIPS):
            self.check_table.horizontalHeaderItem(column).setToolTip(tooltip)
        self.check_table.verticalHeader().setVisible(False)
        self.check_table.setSelectionBehavior(ui_qt.QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.check_table.setSelectionMode(ui_qt.QtLib.SelectionMode.SingleSelection)
        self.check_table.setEditTriggers(ui_qt.QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.check_table.setAutoScroll(False)
        self.check_table.setMinimumHeight(240)
        header = self.check_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(1, ui_qt.QtLib.QHeaderView.Stretch)
        for column in CHECK_COLUMN_KEYS:
            header.setSectionResizeMode(column, ui_qt.QtLib.QHeaderView.Interactive)
        self.check_table.itemSelectionChanged.connect(self.on_check_selection_changed)
        install_empty_click_deselect(self.check_table)
        layout.addWidget(self.check_table, 1)
        self.advanced_group = ui_qt.QtWidgets.QGroupBox("Detection Settings")
        self.advanced_group.setToolTip("Settings of the selected check. Hover each field for details.")
        advanced_layout = ui_qt.QtWidgets.QVBoxLayout(self.advanced_group)
        advanced_layout.setContentsMargins(8, 8, 8, 8)
        self.advanced_stack = ui_qt.QtWidgets.QStackedWidget()
        self.advanced_placeholder = ui_qt.QtWidgets.QLabel("Select a check above to edit its detection settings.")
        self.advanced_placeholder.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        self.advanced_placeholder.setStyleSheet("color: #8A8A8A; padding: 12px;")
        self.advanced_stack.addWidget(self.advanced_placeholder)
        advanced_layout.addWidget(self.advanced_stack)
        layout.addWidget(self.advanced_group)
        layout.addLayout(self.build_button_row())

    def build_global_group(self):
        """Builds the global settings grid.

        Returns:
            QGroupBox: Global settings group.
        """
        group = ui_qt.QtWidgets.QGroupBox("Global")
        group.setToolTip("Settings shared by every check.")
        grid = ui_qt.QtWidgets.QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)
        cells = []
        if self.show_mode:
            self.mode_combo = ui_qt.QtWidgets.QComboBox()
            for mode in checks_base.MODE_VALUES:
                self.mode_combo.addItem(presets.get_mode_display_label(mode), mode)
            self.mode_combo.setToolTip(
                "General: checks that work on any animated nodes.\n"
                "Biped: the General checks plus contact, ground, and body checks (needs a skeleton)."
            )
            self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
            fit_combo_to_items(self.mode_combo)
            cells.append(("Mode", self.mode_combo))
        resolved = presets.resolve_preset(self.preset)
        for spec in presets.GLOBAL_PARAMETERS:
            widget = create_parameter_widget(
                spec, resolved["settings"][spec.key], partial(self.on_global_changed, spec.key)
            )
            self.global_widgets[spec.key] = widget
            cells.append((spec.label, widget))
        for cell_index, (label_text, widget) in enumerate(cells):
            row, column = divmod(cell_index, 2)
            label = ui_qt.QtWidgets.QLabel(label_text)
            label.setToolTip(widget.toolTip())
            grid.addWidget(label, row, column * 2)
            grid.addWidget(widget, row, column * 2 + 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        return group

    def build_button_row(self):
        """Builds the summary label and preset buttons.

        Returns:
            QHBoxLayout: Button row.
        """
        row = ui_qt.QtWidgets.QHBoxLayout()
        self.summary_label = ui_qt.QtWidgets.QLabel()
        self.summary_label.setToolTip("Only values that differ from the defaults are stored in the preset.")
        row.addWidget(self.summary_label, 1)
        for label_text, tooltip, callback in (
            ("Reset All", "Restore every check and global setting to its default value.", self.reset_all),
            ("Load", "Load a preset JSON file (for example one shared by your team).", self.load_from_file),
            ("Save As...", "Save the current preset as JSON.\nOnly values changed from the defaults are written.",
             self.save_to_file),
        ):
            button = ui_qt.QtWidgets.QPushButton(label_text)
            button.setToolTip(tooltip)
            button.clicked.connect(callback)
            row.addWidget(button)
        return row

    # ------------------------------------------------ Refresh ------------------------------------------------
    def get_mode(self):
        """Gets the preset mode.

        Returns:
            str: Evaluation mode.
        """
        return presets.resolve_preset(self.preset)["mode"]

    def set_preset(self, preset, notify=False):
        """Replaces the edited preset.

        Args:
            preset (dict): Stored or resolved preset.
            notify (bool): Call the changed callback.
        """
        self.preset = presets.compact_preset(preset)
        self.refresh()
        if notify:
            self.notify_changed()

    def set_mode(self, mode, notify=True):
        """Sets the evaluation mode.

        Args:
            mode (str): Evaluation mode.
            notify (bool): Call the changed callback.
        """
        preset = presets.resolve_preset(self.preset)
        if preset["mode"] == mode:
            return
        preset["mode"] = mode
        self.set_preset(preset, notify=notify)

    def refresh(self):
        """Refreshes every control from the preset."""
        resolved = presets.resolve_preset(self.preset)
        if self.mode_combo is not None:
            self.mode_combo.blockSignals(True)
            self.mode_combo.setCurrentIndex(max(0, self.mode_combo.findData(resolved["mode"])))
            self.mode_combo.blockSignals(False)
        for key, widget in self.global_widgets.items():
            set_parameter_widget_value(widget, resolved["settings"][key])
        self.refresh_check_table(resolved)
        self.refresh_advanced_values(resolved)
        self.refresh_summary()

    def refresh_check_table(self, resolved):
        """Rebuilds the check table when the mode changes, otherwise updates its values.

        Args:
            resolved (dict): Resolved preset.
        """
        checks = presets.get_checks_for_mode(resolved["mode"])
        keys = [check.key for check in checks]
        if keys != self.check_keys:
            self.rebuild_check_table(checks, resolved)
            self.rebuild_advanced_pages(checks, resolved)
            if self.selected_check_key not in keys:
                self.selected_check_key = None
            self.select_check(self.selected_check_key)
        else:
            for check in checks:
                values = resolved["checks"][check.key]
                for key, widget in self.check_row_widgets[check.key].items():
                    set_parameter_widget_value(widget, values[key])
                self.update_row_style(check.key, values)
        enabled_count = sum(1 for check in checks if resolved["checks"][check.key]["enabled"])
        mode_label = checks_base.MODE_LABELS.get(resolved["mode"], resolved["mode"])
        self.checks_label.setText(
            f"{mode_label} mode: {presets.get_mode_check_summary(resolved['mode'])} ({enabled_count} enabled)"
        )

    def rebuild_check_table(self, checks, resolved):
        """Fills the table with section header rows and one row per check.

        Args:
            checks (list): CheckDefinition objects for the mode.
            resolved (dict): Resolved preset.
        """
        self.check_keys = [check.key for check in checks]
        self.check_row_widgets = {}
        self.row_keys = []
        rows = []
        current_section = None
        for check in checks:
            if check.mode != current_section:
                current_section = check.mode
                rows.append(("section", check.mode))
            rows.append(("check", check))
        self.check_table.blockSignals(True)
        self.check_table.clearSpans()
        self.check_table.clearContents()
        self.check_table.setRowCount(0)
        self.check_table.setRowCount(len(rows))
        for row, (row_type, value) in enumerate(rows):
            if row_type == "section":
                self.add_section_row(row, value)
                self.row_keys.append(None)
            else:
                self.populate_check_row(row, value, resolved["checks"][value.key])
                self.row_keys.append(value.key)
        self.check_table.blockSignals(False)
        self.update_column_widths()

    def add_section_row(self, row, mode):
        """Adds a non-selectable section header row.

        Args:
            row (int): Table row.
            mode (str): Check group mode.
        """
        item = ui_qt.QtWidgets.QTableWidgetItem(SECTION_LABELS.get(mode, mode))
        item.setFlags(ui_qt.QtLib.ItemFlag.ItemIsEnabled)
        item.setForeground(ui_qt.QtGui.QBrush(ui_qt.QtGui.QColor("#9FC9FF")))
        item.setBackground(ui_qt.QtGui.QBrush(ui_qt.QtGui.QColor("#262626")))
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        self.check_table.setItem(row, 0, item)
        self.check_table.setSpan(row, 0, 1, len(CHECK_TABLE_COLUMNS))

    def populate_check_row(self, row, check, values):
        """Fills one check table row.

        Args:
            row (int): Table row.
            check (CheckDefinition): Check definition.
            values (dict): Resolved check values.
        """
        widgets = {}
        for column, key in CHECK_COLUMN_KEYS.items():
            spec = presets.SCORING_PARAMETERS_BY_KEY[key]
            widget = create_parameter_widget(spec, values[key], partial(self.on_check_value_changed, check.key, key))
            if isinstance(widget, ui_qt.QtWidgets.QCheckBox):
                container = ui_qt.QtWidgets.QWidget()
                container_layout = ui_qt.QtWidgets.QHBoxLayout(container)
                container_layout.setContentsMargins(0, 0, 0, 0)
                container_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
                container_layout.addWidget(widget)
                self.check_table.setCellWidget(row, column, container)
            else:
                widget.setFrame(False)
                widget.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
                self.check_table.setCellWidget(row, column, widget)
            widgets[key] = widget
        label_item = ui_qt.QtWidgets.QTableWidgetItem(check.label)
        group_text = "Biped check (needs a skeleton)." if check.mode == checks_base.MODE_BIPED else "General check."
        label_item.setToolTip(f"{check.description}\n{group_text}")
        self.check_table.setItem(row, 1, label_item)
        self.check_row_widgets[check.key] = widgets
        self.update_row_style(check.key, values)

    def update_column_widths(self):
        """Sizes the value columns so numbers such as 100 or 10.00 are never cropped."""
        sample_texts = {0: "On", 2: "10.00", 3: "100", 4: "100", 5: "Allow Fail"}
        for column, sample in sample_texts.items():
            header_width = get_text_width(self.check_table, CHECK_TABLE_COLUMNS[column]) + 24
            value_width = get_text_width(self.check_table, sample) + 46
            self.check_table.setColumnWidth(column, max(header_width, value_width))

    def update_row_style(self, check_key, values):
        """Greys out disabled checks and marks changed ones.

        Args:
            check_key (str): Check key.
            values (dict): Resolved check values.
        """
        if check_key not in self.row_keys:
            return
        row = self.row_keys.index(check_key)
        item = self.check_table.item(row, 1)
        if item is None:
            return
        check = presets.get_check(check_key)
        is_changed = check_key in presets.compact_preset(self.preset)["checks"]
        item.setText(f"{check.label} *" if is_changed else check.label)
        item.setForeground(ui_qt.QtGui.QBrush(ui_qt.QtGui.QColor("#DDDDDD" if values["enabled"] else "#777777")))
        for key, widget in self.check_row_widgets.get(check_key, {}).items():
            if key != "enabled":
                widget.setEnabled(bool(values["enabled"]))

    # ------------------------------------------------ Detection Settings ------------------------------------------
    def rebuild_advanced_pages(self, checks, resolved):
        """Builds one detection-settings page per check. Selecting a check only switches pages.

        Args:
            checks (list): CheckDefinition objects for the mode.
            resolved (dict): Resolved preset.
        """
        for page in list(self.advanced_pages.values()):
            self.advanced_stack.removeWidget(page)
            page.deleteLater()
        self.advanced_pages = {}
        self.advanced_widgets = {}
        for check in checks:
            page = self.build_advanced_page(check, resolved["checks"][check.key])
            self.advanced_pages[check.key] = page
            self.advanced_stack.addWidget(page)

    def build_advanced_page(self, check, values):
        """Builds the detection settings of one check.

        Args:
            check (CheckDefinition): Check definition.
            values (dict): Resolved check values.

        Returns:
            QWidget: Page widget.
        """
        page = ui_qt.QtWidgets.QWidget()
        layout = ui_qt.QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        description = ui_qt.QtWidgets.QLabel(check.description)
        description.setWordWrap(True)
        layout.addWidget(description)
        grid = ui_qt.QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)
        specs = list(check.parameters) + [
            presets.SCORING_PARAMETERS_BY_KEY["event_penalty"],
            presets.SCORING_PARAMETERS_BY_KEY["frame_penalty"],
        ]
        widgets = {}
        for spec_index, spec in enumerate(specs):
            value = values["parameters"][spec.key] if spec.key in values["parameters"] else values[spec.key]
            widget = create_parameter_widget(spec, value, partial(self.on_check_value_changed, check.key, spec.key))
            widgets[spec.key] = widget
            row, column = divmod(spec_index, 2)
            label = ui_qt.QtWidgets.QLabel(spec.label)
            label.setToolTip(widget.toolTip())
            grid.addWidget(label, row, column * 2)
            grid.addWidget(widget, row, column * 2 + 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        layout.addLayout(grid)
        reset_row = ui_qt.QtWidgets.QHBoxLayout()
        reset_row.addStretch()
        reset_button = ui_qt.QtWidgets.QPushButton("Reset Check")
        reset_button.setToolTip(f"Restore {check.label} to its default values.")
        reset_button.clicked.connect(partial(self.reset_check, check.key))
        reset_row.addWidget(reset_button)
        layout.addLayout(reset_row)
        layout.addStretch()
        self.advanced_widgets[check.key] = widgets
        return page

    def refresh_advanced_values(self, resolved):
        """Updates every detection-settings page from the preset.

        Args:
            resolved (dict): Resolved preset.
        """
        for check_key, widgets in self.advanced_widgets.items():
            values = resolved["checks"][check_key]
            for key, widget in widgets.items():
                value = values["parameters"][key] if key in values["parameters"] else values[key]
                set_parameter_widget_value(widget, value)

    def show_advanced_page(self, check_key):
        """Shows the detection settings page of a check.

        Args:
            check_key (str): Check key.
        """
        page = self.advanced_pages.get(check_key)
        if page is None:
            self.advanced_stack.setCurrentWidget(self.advanced_placeholder)
            self.advanced_group.setTitle("Detection Settings")
            return
        self.advanced_stack.setCurrentWidget(page)
        self.advanced_group.setTitle(f"Detection Settings - {presets.get_check(check_key).label}")

    def select_check(self, check_key):
        """Selects a check row without scrolling any parent view.

        Args:
            check_key (str): Check key.
        """
        if not check_key or check_key not in self.row_keys:
            self.check_table.blockSignals(True)
            self.check_table.clearSelection()
            self.check_table.blockSignals(False)
            self.show_advanced_page(None)
            return
        self.check_table.blockSignals(True)
        self.check_table.selectRow(self.row_keys.index(check_key))
        self.check_table.blockSignals(False)
        self.show_advanced_page(check_key)

    def refresh_summary(self):
        """Updates the changed-values summary."""
        count = presets.count_overrides(self.preset)
        name = presets.resolve_preset(self.preset)["name"]
        self.summary_label.setText(f"Preset: {name} | {count} value(s) changed from defaults")

    # ------------------------------------------------ Events ------------------------------------------------
    def notify_changed(self):
        """Calls the changed callback with the compact preset."""
        if callable(self.changed_callback):
            self.changed_callback(presets.copy_preset(self.preset))

    def on_mode_changed(self, index):
        """Handles mode selection changes.

        Args:
            index (int): Combo index.
        """
        self.set_mode(self.mode_combo.itemData(index), notify=True)

    def on_global_changed(self, key, value):
        """Stores a global setting.

        Args:
            key (str): Global setting key.
            value (object): New value.
        """
        self.preset = presets.set_global_value(self.preset, key, value)
        self.refresh_summary()
        self.notify_changed()

    def on_check_value_changed(self, check_key, key, value):
        """Stores a check value without rebuilding the active widget.

        Args:
            check_key (str): Check key.
            key (str): Scoring or parameter key.
            value (object): New value.
        """
        self.preset = presets.set_check_value(self.preset, check_key, key, value)
        resolved = presets.resolve_preset(self.preset)
        self.update_row_style(check_key, resolved["checks"][check_key])
        if key == "enabled":
            self.refresh_check_table(resolved)
        self.refresh_summary()
        self.notify_changed()

    def on_check_selection_changed(self):
        """Shows the detection settings of the selected check."""
        rows = sorted(set(index.row() for index in self.check_table.selectedIndexes()))
        if not rows or rows[0] >= len(self.row_keys):
            self.selected_check_key = None
            self.show_advanced_page(None)
            return
        check_key = self.row_keys[rows[0]]
        if not check_key:
            self.selected_check_key = None
            self.select_check(None)
            return
        self.selected_check_key = check_key
        self.show_advanced_page(check_key)

    def reset_check(self, check_key):
        """Restores one check to its defaults.

        Args:
            check_key (str): Check key.
        """
        self.preset = presets.reset_check(self.preset, check_key)
        self.refresh()
        self.notify_changed()

    def reset_all(self):
        """Restores every value to its default while keeping the mode and name."""
        resolved = presets.resolve_preset(self.preset)
        self.set_preset(presets.create_preset(name=resolved["name"], mode=resolved["mode"]), notify=True)

    def get_dialog_directory(self):
        """Gets the starting folder for file dialogs.

        Returns:
            str: Existing folder or the user's home folder.
        """
        directory = self.last_directory_getter() if callable(self.last_directory_getter) else ""
        return directory if directory and os.path.isdir(directory) else os.path.expanduser("~")

    def load_from_file(self):
        """Loads a preset JSON file chosen by the user."""
        file_path, _ = ui_qt.QtWidgets.QFileDialog.getOpenFileName(
            self, "Load Evaluation Preset", self.get_dialog_directory(), PRESET_FILE_FILTER
        )
        if not file_path:
            return
        try:
            loaded = presets.load_preset(file_path)
        except (IOError, OSError, ValueError) as exception:
            ui_qt.QtWidgets.QMessageBox.warning(self, "Load Evaluation Preset", str(exception))
            return
        if not self.show_mode:
            loaded["mode"] = self.get_mode()
        self.set_preset(loaded, notify=True)

    def save_to_file(self):
        """Saves the preset to a JSON file chosen by the user."""
        file_path, _ = ui_qt.QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Evaluation Preset", self.get_dialog_directory(), PRESET_FILE_FILTER
        )
        if not file_path:
            return
        resolved = presets.resolve_preset(self.preset)
        resolved["name"] = os.path.splitext(os.path.basename(file_path))[0]
        self.set_preset(resolved, notify=True)
        try:
            presets.save_preset(self.preset, file_path)
        except (IOError, OSError) as exception:
            ui_qt.QtWidgets.QMessageBox.warning(self, "Save Evaluation Preset", str(exception))
            return
        self.summary_label.setText(f"Saved preset to {file_path}")
