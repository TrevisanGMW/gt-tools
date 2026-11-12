"""
Batch Processor Settings Override Task Widget
"""

from gt.tools.batch_processor import batch_processor_run_settings as run_settings
from gt.tools.batch_processor.widgets import attr_widget_base
from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
from gt.tools.batch_processor.widgets.settings_override_variables_dialog import SettingsOverrideVariablesDialog
import gt.ui.qt_import as ui_qt
import gt.ui.resource_library as ui_res_lib
from functools import partial


OVERRIDE_ROWS = (
    (
        run_settings.WORKER_COUNT,
        "Max Workers",
        "Maximum concurrent worker processes from this point on.\n"
        "Lowering it never stops running jobs; new jobs wait until enough workers finish.",
        1,
        run_settings.MAX_WORKER_COUNT,
    ),
    (
        run_settings.MAX_RETRIES,
        "Retries",
        "Times a failed job is retried before its segment finishes. 0 disables retries.",
        0,
        run_settings.MAX_RETRY_COUNT,
    ),
    (
        run_settings.TIMEOUT_MINUTES,
        "Timeout (min)",
        "Minutes a job may run before it is canceled. 0 disables the timeout.\n"
        "Jobs that are already running keep the timeout they started with.",
        0,
        run_settings.MAX_TIMEOUT_MINUTES,
    ),
)

APPLY_INFO_TEXT = (
    "Multi-instance only. Enabled overrides take effect when this task's segment starts and stay "
    "active for the rest of the run, until another Settings Override task changes them. Settings "
    "never change in the middle of a segment: place this task above the processing tasks of a segment "
    "(for example, right after a \"Start New Segment\" input)."
)

TABLE_COLUMN_LABEL = 0
TABLE_COLUMN_OVERRIDE = 1
TABLE_COLUMN_VALUE = 2
TABLE_COLUMN_FILLER = 3
TABLE_COLUMN_SPACING = 28
TABLE_OVERRIDE_COLUMN_WIDTH = 80
VALUE_FIELD_MINIMUM_WIDTH = 110


class AttrWidgetSettingsOverrideTask(AttrWidgetTask):
    """Attribute widget for the Settings Override task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the Settings Override widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskSettingsOverride, optional): Settings Override task model.
            project (BatchProcessorModel, optional): Project model.
            refresh_parent_func (callable, optional): Refresh callback.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(
            parent=parent,
            task=task,
            project=project,
            refresh_parent_func=refresh_parent_func,
            *args,
            **kwargs
        )
        self.value_widgets = {}
        self.override_grid = None
        self.add_common_task_settings(include_source=False, include_target=False, include_overwrite=False)
        self.add_widget_separator_line(label_text="Run Settings Overrides")
        self.add_override_table()
        for setting_key, label_text, tooltip, minimum, maximum in OVERRIDE_ROWS:
            self.add_override_spin_box_row(setting_key, label_text, tooltip, minimum, maximum)
        self.add_override_maya_version_row()
        self.add_override_custom_variables_row()
        self.add_widget_separator_line(label_text="How It Applies")
        self.add_apply_info_label()
        self.content_layout.addStretch()

    def add_override_table(self):
        """Adds the grid that aligns setting labels, override checkboxes, and values as columns."""
        self.override_grid = ui_qt.QtWidgets.QGridLayout()
        self.override_grid.setContentsMargins(0, 0, 0, 5)
        self.override_grid.setHorizontalSpacing(TABLE_COLUMN_SPACING)
        self.override_grid.setVerticalSpacing(6)
        self.override_grid.setColumnMinimumWidth(TABLE_COLUMN_OVERRIDE, TABLE_OVERRIDE_COLUMN_WIDTH)
        # Equal stretch on the value and filler columns gives the value widgets half of the free width.
        self.override_grid.setColumnStretch(TABLE_COLUMN_VALUE, 1)
        self.override_grid.setColumnStretch(TABLE_COLUMN_FILLER, 1)
        headers = (
            (TABLE_COLUMN_LABEL, "Setting", ui_qt.QtLib.AlignmentFlag.AlignLeft),
            (TABLE_COLUMN_OVERRIDE, "Override", ui_qt.QtLib.AlignmentFlag.AlignHCenter),
            (TABLE_COLUMN_VALUE, "Value", ui_qt.QtLib.AlignmentFlag.AlignLeft),
        )
        for column, header_text, alignment in headers:
            header_label = ui_qt.QtWidgets.QLabel(header_text)
            attr_widget_base.configure_label_for_scaled_displays(header_label)
            header_label.setStyleSheet("color: grey;")
            self.override_grid.addWidget(header_label, 0, column, alignment)
        self.content_layout.addLayout(self.override_grid)

    def add_override_row_widgets(self, setting_key, label_text, tooltip, value_widget):
        """Places one override row in the table.

        Args:
            setting_key (str): Run setting key controlled by the row.
            label_text (str): Setting label shown in the first column.
            tooltip (str): Tooltip text shared by the row widgets.
            value_widget (QWidget): Value editor shown in the last column.
        """
        row = self.override_grid.rowCount()
        label = ui_qt.QtWidgets.QLabel(f"{label_text}:")
        attr_widget_base.configure_label_for_scaled_displays(label, minimum_width=110)
        label.setMinimumHeight(35)
        label.setToolTip(tooltip)
        self.override_grid.addWidget(label, row, TABLE_COLUMN_LABEL)
        flag_key = run_settings.get_override_flag_key(setting_key)
        checkbox = ui_qt.QtWidgets.QCheckBox()
        checkbox.setChecked(bool(self.task.settings.get(flag_key)))
        checkbox.setToolTip(f"Enable to change this setting.\n{tooltip}")
        checkbox.toggled.connect(lambda checked: self.set_override_enabled(setting_key, checked))
        self.override_grid.addWidget(checkbox, row, TABLE_COLUMN_OVERRIDE, ui_qt.QtLib.AlignmentFlag.AlignCenter)
        value_widget.setMinimumHeight(35)
        value_widget.setToolTip(tooltip)
        value_widget.setMinimumWidth(VALUE_FIELD_MINIMUM_WIDTH)
        value_widget.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        self.override_grid.addWidget(value_widget, row, TABLE_COLUMN_VALUE)
        self.value_widgets[setting_key] = value_widget
        self.refresh_value_enabled_state(setting_key)

    def add_override_spin_box_row(self, setting_key, label_text, tooltip, minimum, maximum):
        """Adds an override row with an integer value.

        Args:
            setting_key (str): Run setting key.
            label_text (str): Row label.
            tooltip (str): Tooltip text.
            minimum (int): Minimum value.
            maximum (int): Maximum value.
        """
        spin_box = ui_qt.QtWidgets.QSpinBox()
        spin_box.setRange(int(minimum), int(maximum))
        spin_box.setValue(run_settings.normalize_setting_value(setting_key, self.task.settings.get(setting_key)))
        spin_box.valueChanged.connect(partial(self.set_task_setting, key=setting_key))
        self.add_override_row_widgets(setting_key, label_text, tooltip, spin_box)

    def add_override_maya_version_row(self):
        """Adds the preferred Maya version override row."""
        setting_key = run_settings.PREFERRED_MAYA_VERSION
        tooltip = (
            "Maya version used by workers launched from this point on, e.g. 2025.\n"
            "Leave empty to use the mayapy that launched the tracker.\n"
            "If the version is not found, the current mayapy is kept and a warning is logged."
        )
        text_field = self.create_text_field(
            text=str(self.task.settings.get(setting_key) or ""),
            placeholder="Optional version, e.g. 2025",
            tooltip=tooltip,
        )
        text_field.editingFinished.connect(lambda: self.set_task_setting(text_field.text().strip(), key=setting_key))
        self.add_override_row_widgets(setting_key, "Preferred Maya", tooltip, text_field)

    def add_override_custom_variables_row(self):
        """Adds the custom variables override row, its editor button, and its summary line."""
        tooltip = (
            "Set new or modify existing custom variables ({my-variable}) for this run, from this task's\n"
            "segment on. The project's saved variables are not changed."
        )
        button = ui_qt.QtWidgets.QPushButton("Edit Variables")
        button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_env_var))
        button.setAutoDefault(False)
        button.clicked.connect(self.edit_custom_variables)
        self.add_override_row_widgets(run_settings.CUSTOM_VARIABLES, "Custom Variables", tooltip, button)
        self.custom_variable_summary_label = ui_qt.QtWidgets.QLabel()
        attr_widget_base.configure_label_for_scaled_displays(self.custom_variable_summary_label, word_wrap=True)
        summary_layout = ui_qt.QtWidgets.QHBoxLayout()
        summary_layout.setContentsMargins(12, 0, 12, 6)
        summary_layout.addWidget(self.custom_variable_summary_label)
        self.content_layout.addLayout(summary_layout)
        self.refresh_custom_variable_summary()

    def get_existing_custom_variables(self):
        """Gets the variables defined where this task runs.

        Returns:
            dict: Project custom variables with the overrides of earlier Settings Override
                tasks applied, keyed by normalized name.
        """
        definitions = self.project.get_custom_environment_variables()
        for task in self.project.tasks:
            if task is self.task or getattr(task, "id", None) == self.task.id:
                break
            earlier = run_settings.get_task_overrides(task).get(run_settings.CUSTOM_VARIABLES)
            if earlier:
                definitions = run_settings.apply_custom_variable_overrides(definitions, earlier)
        return definitions

    def edit_custom_variables(self):
        """Opens the custom variable override editor and stores its rows."""
        dialog = SettingsOverrideVariablesDialog(
            override_rows=self.task.settings.get(run_settings.CUSTOM_VARIABLES),
            existing_variables=self.get_existing_custom_variables(),
            parent=self,
            project=self.project,
        )
        if self.exec_dialog(dialog) != ui_qt.QtWidgets.QDialog.Accepted:
            return
        rows = dialog.get_override_rows()
        if rows is None:
            return
        self.task.settings[run_settings.CUSTOM_VARIABLES] = rows
        self.refresh_custom_variable_summary()
        summary_text = self.get_custom_variable_summary_text()
        self.emit_status_message(f"Saved custom variable overrides: {summary_text}.")

    def get_custom_variable_summary_text(self):
        """Builds the override counts for the saved rows.

        Returns:
            str: Text such as "2 overridden, 1 new, 5 unchanged", or a hint when there are no rows.
        """
        overrides = run_settings.normalize_custom_variable_overrides(
            self.task.settings.get(run_settings.CUSTOM_VARIABLES)
        )
        if not overrides:
            return "no variable rows"
        summary = run_settings.summarize_custom_variable_overrides(self.get_existing_custom_variables(), overrides)
        return run_settings.format_custom_variable_summary(summary)

    def refresh_custom_variable_summary(self):
        """Refreshes the summary line under the custom variables row."""
        label = getattr(self, "custom_variable_summary_label", None)
        if label is None:
            return
        enabled = bool(self.task.settings.get(run_settings.get_override_flag_key(run_settings.CUSTOM_VARIABLES)))
        text = self.get_custom_variable_summary_text()
        has_rows = text != "no variable rows"
        label.setText(f"Custom variables: {text}." + ("" if enabled or not has_rows else " (override is off)"))
        color = ui_res_lib.Color.Hex.green_pale if has_rows and enabled else ui_res_lib.Color.Hex.gray_dim
        label.setStyleSheet(f"color: {color};")

    def add_apply_info_label(self):
        """Adds a padded explanation of when the overrides are applied."""
        info_label = ui_qt.QtWidgets.QLabel(APPLY_INFO_TEXT)
        attr_widget_base.configure_label_for_scaled_displays(info_label, word_wrap=True)
        info_label.setStyleSheet("color: grey;")
        info_layout = ui_qt.QtWidgets.QHBoxLayout()
        info_layout.setContentsMargins(12, 2, 12, 8)
        info_layout.addWidget(info_label)
        self.content_layout.addLayout(info_layout)

    def set_override_enabled(self, setting_key, enabled):
        """Stores an override flag and updates the value widget state.

        Args:
            setting_key (str): Run setting key.
            enabled (bool): Whether the override is enabled.
        """
        self.set_task_setting(bool(enabled), key=run_settings.get_override_flag_key(setting_key))
        self.refresh_value_enabled_state(setting_key)
        if setting_key == run_settings.CUSTOM_VARIABLES:
            self.refresh_custom_variable_summary()

    def refresh_value_enabled_state(self, setting_key):
        """Enables a value widget only while its override is on.

        Args:
            setting_key (str): Run setting key.
        """
        widget = self.value_widgets.get(setting_key)
        if widget is None:
            return
        widget.setEnabled(bool(self.task.settings.get(run_settings.get_override_flag_key(setting_key))))
