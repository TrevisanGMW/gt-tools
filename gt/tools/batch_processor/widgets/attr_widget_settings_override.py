"""
Batch Processor Settings Override Task Widget
"""

from gt.tools.batch_processor import batch_processor_run_settings as run_settings
from gt.tools.batch_processor.widgets import attr_widget_base
from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
import gt.ui.qt_import as ui_qt
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

    def refresh_value_enabled_state(self, setting_key):
        """Enables a value widget only while its override is on.

        Args:
            setting_key (str): Run setting key.
        """
        widget = self.value_widgets.get(setting_key)
        if widget is None:
            return
        widget.setEnabled(bool(self.task.settings.get(run_settings.get_override_flag_key(setting_key))))
