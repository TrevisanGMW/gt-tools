"""Compact launch settings and preview for the Run Batch Project task."""

from functools import partial

from gt.tools.batch_processor import batch_processor_projects as projects
from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
import gt.ui.qt_import as ui_qt


class AttrWidgetRunBatchProject(AttrWidgetTask):
    """Edits child overrides and binds queue-dependent scheduling controls."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Builds launch controls without changing saved child projects.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskRunBatchProject, optional): Launch task model.
            project (BatchProcessorModel, optional): Parent project model.
            refresh_parent_func (callable, optional): Parent refresh callback.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(parent=parent, task=task, project=project,
                         refresh_parent_func=refresh_parent_func, *args, **kwargs)
        self.preview_dialog = None
        note = ui_qt.QtWidgets.QLabel(
            "Use Input Files with .batch extensions. Parent workers limit simultaneous projects. "
            "Place this task first in its input segment.")
        note.setWordWrap(True)
        self.content_layout.addWidget(note)
        self.add_schedule_controls()
        self.add_override_controls()
        self.add_window_and_log_controls()
        preview = ui_qt.QtWidgets.QPushButton("Preview Child Projects")
        preview.setToolTip("Validate child projects and inspect effective settings without running them.")
        preview.clicked.connect(self.preview_children)
        self.content_layout.addWidget(preview)
        self.content_layout.addStretch()

    def compact_row(self, label, layout=None):
        """Creates a row with adjacent labels and fields, and no internal stretch.

        Args:
            label (str): Field label.
            layout (QLayout, optional): Destination layout.

        Returns:
            tuple: Row layout and label widget.
        """
        destination = layout if layout is not None else self.content_layout
        row = ui_qt.QtWidgets.QHBoxLayout()
        row.setContentsMargins(0, 3, 0, 3)
        row.setSpacing(6)
        label_widget = ui_qt.QtWidgets.QLabel(label)
        row.addWidget(label_widget)
        destination.addLayout(row)
        return row, label_widget

    def setting_combo(self, label, key, values, tooltip, layout=None):
        """Adds a compact serialized choice field.

        Args:
            label (str): Display label.
            key (str): Task setting key.
            values (list): Supported values.
            tooltip (str): Multiline help text.
            layout (QLayout, optional): Destination layout.

        Returns:
            tuple: Choice widget and label widget.
        """
        row, label_widget = self.compact_row(label, layout)
        combo = ui_qt.QtWidgets.QComboBox()
        combo.addItems(values)
        combo.setCurrentText(self.task.settings[key])
        combo.setToolTip(tooltip)
        label_widget.setToolTip(tooltip)
        combo.currentTextChanged.connect(partial(self.set_task_setting, key=key))
        row.addWidget(combo, 1)
        return combo, label_widget

    def setting_spin(self, label, key, minimum, maximum, tooltip, layout=None, suffix=""):
        """Adds a compact integer field with a visible unit.

        Args:
            label (str): Display label.
            key (str): Task setting key.
            minimum (int): Minimum value.
            maximum (int): Maximum value.
            tooltip (str): Field help.
            layout (QLayout, optional): Destination layout.
            suffix (str, optional): Display unit.

        Returns:
            QSpinBox: Bound field.
        """
        row, label_widget = self.compact_row(label, layout)
        spin = ui_qt.QtWidgets.QSpinBox()
        spin.setRange(minimum, maximum)
        spin.setValue(self.task.settings[key])
        spin.setSuffix(suffix)
        spin.setMinimumWidth(75)
        spin.setToolTip(tooltip)
        label_widget.setToolTip(tooltip)
        spin.valueChanged.connect(partial(self.set_task_setting, key=key))
        row.addWidget(spin, 1)
        return spin

    def add_schedule_controls(self):
        """Adds queue eligibility, paired local schedule fields, and self exclusion."""
        self.add_widget_separator_line("Start Conditions")
        self.queue_combo, queue_label = self.setting_combo(
            "Queue Mode", "queue_mode", projects.QUEUE_MODES,
            "Independent: start projects as parent worker slots become available.\n"
            "Projects do not depend on the result of another project.\n\n"
            "Ordered Chain: each project waits for the previous project in input order.\n"
            "After Dependency selects the required outcome; the chain runs one at a time.\n\n"
            "Groups: projects in one input segment may run concurrently.\n"
            "The next segment waits for the entire previous group and its required outcome.\n"
            "Groups come from separate input segments, not from the worker count.\n\n"
            "Worker limits, scheduled times, delays, and deadlines also apply.")
        dependency_row = ui_qt.QtWidgets.QHBoxLayout()
        dependency_row.setSpacing(18)
        self.content_layout.addLayout(dependency_row)
        self.dependency_combo, self.dependency_label = self.setting_combo(
            "After Dependency", "dependency_outcome", projects.DEPENDENCY_OUTCOMES,
            "Used by Ordered Chain and Groups; ignored in Independent mode.\n"
            "Completion: continue after the previous project or group finishes.\n"
            "Success: continue only if the previous project, or every project in the group, succeeds.\n"
            "Failure: continue only if the previous project, or any project in the group, fails.\n"
            "Retries must finish first. The first project or group has no dependency.", layout=dependency_row)
        self.delay_spin = self.setting_spin(
            "Delay", "delay_seconds", 0, 86400,
            "Wait this many seconds after the dependency finishes.\n"
            "Without a dependency, count from parent startup. Waiting uses no worker slot.",
            layout=dependency_row, suffix=" s")
        dependency_row.setStretch(0, 2)
        dependency_row.setStretch(1, 1)
        self.queue_combo.currentTextChanged.connect(self.update_dependency_controls)
        self.update_dependency_controls(self.queue_combo.currentText())
        self.add_time_controls()
        failure_row = ui_qt.QtWidgets.QHBoxLayout()
        failure_row.setSpacing(18)
        self.content_layout.addLayout(failure_row)
        self.setting_combo(
            "On Failure", "failure_policy", projects.FAILURE_POLICIES,
            "Continue: allow other eligible projects to start.\n"
            "Stop Launching: block queued projects after a permanent failure.\n"
            "Already running projects finish; parent retry settings still apply.", layout=failure_row)
        ignore_checkbox = ui_qt.QtWidgets.QCheckBox("Auto Ignore This Project")
        ignore_checkbox.setChecked(self.task.settings["ignore_self"])
        ignore_checkbox.setToolTip(
            "Exclude this saved project if Input Files discovers it among the child projects.\n"
            "Enabled by default. Other recursive project loops are still rejected.")
        ignore_checkbox.toggled.connect(partial(self.set_task_setting, key="ignore_self"))
        failure_row.addWidget(ignore_checkbox)
        failure_row.setStretch(0, 1)

    def update_dependency_controls(self, mode):
        """Enables dependency settings only in modes that evaluate dependencies.

        Args:
            mode (str): Selected queue mode.
        """
        enabled = mode in ("Ordered Chain", "Groups")
        self.dependency_combo.setEnabled(enabled)
        self.dependency_label.setEnabled(enabled)

    def add_time_controls(self):
        """Adds adjacent start and deadline fields using short local timestamps."""
        row = ui_qt.QtWidgets.QHBoxLayout()
        row.setContentsMargins(0, 3, 0, 3)
        row.setSpacing(6)
        self.time_fields = {}
        for label, key, behavior in (
                ("Not Before", "not_before", "Earliest time a project may start. A past time allows immediate start."),
                ("Launch Deadline", "launch_deadline",
                 "Latest time a queued project may start. A past deadline blocks that project.")):
            label_widget = ui_qt.QtWidgets.QLabel(label)
            field = ui_qt.QtWidgets.QLineEdit(self.task.settings[key])
            field.setPlaceholderText("10-21 22:00")
            field.setMinimumWidth(90)
            tooltip = (f"{behavior}\n"
                       "Use HH:MM for the parent's start day, for example 22:00.\n"
                       "Use MM-DD HH:MM for a specific day, for example 10-21 22:00.\n"
                       "Times use your local timezone, 24-hour clock, and current year.\n"
                       "For an overnight deadline, include the following day's date.\n"
                       "Leave empty to disable. It does not stop a project that has already started.")
            label_widget.setToolTip(tooltip)
            field.setToolTip(tooltip)
            field.editingFinished.connect(partial(self.save_time_setting, key))
            row.addWidget(label_widget)
            row.addWidget(field, 1)
            self.time_fields[key] = field
        self.content_layout.addLayout(row)

    def save_time_setting(self, key):
        """Stores an edited schedule field.

        Args:
            key (str): Schedule setting key.
        """
        self.set_task_setting(self.time_fields[key].text().strip(), key)

    def add_override_controls(self):
        """Adds only opt-in overrides of the incoming child project's settings."""
        section = self.add_collapsible_section("Child Overrides", collapsed=False)
        grid = ui_qt.QtWidgets.QGridLayout()
        grid.setContentsMargins(0, 3, 0, 3)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)
        grid.setColumnStretch(2, 1)
        section["content_layout"].addLayout(grid)
        self.override_controls = {}
        for row_index, (label, key, minimum, unit, description) in enumerate((
                ("Workers", "worker_count", 1, "", "Worker limit inside each multi-instance child project.\n"
                 "Single-instance children still use one processing worker."),
                ("Job Timeout", "timeout_minutes", 0, " min", "Timeout for each processing job inside the child.\n"
                 "Zero disables the child's job timeout."),
                ("Job Retries", "max_retries", 0, "", "Retries for failed processing jobs inside the child.\n"
                 "Zero means one attempt with no retries."))):
            label_widget = ui_qt.QtWidgets.QLabel(label)
            checkbox = ui_qt.QtWidgets.QCheckBox("Override")
            checkbox.setChecked(self.task.settings[f"override_{key}"])
            spin = ui_qt.QtWidgets.QSpinBox()
            spin.setRange(minimum, 99999)
            spin.setValue(self.task.settings[key])
            spin.setSuffix(unit)
            spin.setMinimumWidth(75)
            spin.setEnabled(checkbox.isChecked())
            tooltip = f"{description}\nUnchecked uses the child's saved value. The parent is unchanged."
            for widget in (label_widget, checkbox, spin):
                widget.setToolTip(tooltip)
            checkbox.toggled.connect(partial(self.set_task_setting, key=f"override_{key}"))
            checkbox.toggled.connect(spin.setEnabled)
            spin.valueChanged.connect(partial(self.set_task_setting, key=key))
            grid.addWidget(label_widget, row_index, 0)
            grid.addWidget(checkbox, row_index, 1)
            grid.addWidget(spin, row_index, 2)
            self.override_controls[key] = (checkbox, spin)

    def add_window_and_log_controls(self):
        """Groups tracker behavior, empty-run policy, nesting, and retained logs."""
        self.add_widget_separator_line("Child Run Options")
        tracker_row = ui_qt.QtWidgets.QHBoxLayout()
        tracker_row.setContentsMargins(0, 3, 0, 3)
        tracker_row.setSpacing(18)
        self.content_layout.addLayout(tracker_row)
        show_checkbox = ui_qt.QtWidgets.QCheckBox("Show Child Tracker")
        show_checkbox.setChecked(self.task.settings["show_tracker"])
        show_checkbox.setToolTip("Unchecked runs without a Qt window; results and logs are still retained.")
        show_checkbox.toggled.connect(partial(self.set_task_setting, key="show_tracker"))
        tracker_row.addWidget(show_checkbox)
        policy_combo, policy_label = self.setting_combo(
            "After Processing", "window_policy", projects.WINDOW_POLICIES,
            "Only applies when Show Child Tracker is enabled.\n"
            "Applied after the final result is saved.\nWarnings count as success for Close On Success.",
            layout=tracker_row)
        for widget in (policy_combo, policy_label):
            widget.setEnabled(show_checkbox.isChecked())
            show_checkbox.toggled.connect(widget.setEnabled)
        tracker_row.setStretch(1, 1)
        self.add_run_controls()
        self.add_path_template_field("Log Folder", self.task.settings["logs_path"],
                                     partial(self.set_task_setting, key="logs_path"), dir_only=True,
                                     tooltip="Unique child run and attempt folders are retained under this root.")

    def add_run_controls(self):
        """Places empty-child handling and nesting in one expanding options row."""
        row = ui_qt.QtWidgets.QHBoxLayout()
        row.setSpacing(18)
        self.content_layout.addLayout(row)
        self.setting_combo("Empty Child", "empty_policy", ["Warning", "Failure"],
                           "Outcome when a child discovers no processing jobs.", layout=row)
        self.setting_spin("Maximum Nesting", "maximum_depth", 1, 32,
                          "Maximum number of nested child projects.\nRecursive loops are always rejected.",
                          layout=row)
        row.setStretch(0, 1)
        row.setStretch(1, 1)

    def preview_children(self):
        """Shows effective child settings, ignored inputs, and validation results."""
        from gt.tools.batch_processor.batch_processor_project_service import preview_projects

        try:
            rows = preview_projects(self.task, self.project)
            active_rows = [row for row in rows if not row.get("ignored")]
            workers = sorted((row.get("workers", 0) for row in active_rows), reverse=True)
            slots = int(self.project.run_settings["worker_count"])
            dialog = ui_qt.QtWidgets.QDialog(self)
            dialog.setWindowTitle("Child Project Preview")
            dialog.resize(780, 520)
            layout = ui_qt.QtWidgets.QVBoxLayout(dialog)
            text = ui_qt.QtWidgets.QPlainTextEdit()
            text.setReadOnly(True)
            lines = [f"Projects: {len(active_rows)} | Ignored: {len(rows) - len(active_rows)} | Parent slots: {slots}",
                     f"Maximum processing workers: {sum(workers[:slots])}",
                     "Counts exclude tracker and supervisor processes.", ""]
            for index, row in enumerate(rows, 1):
                lines.append(f"{index}. {row['path']}")
                if row.get("ignored"):
                    lines.extend([f"   Ignored: {row['reason']}", ""])
                    continue
                lines.extend([f"   Workers: {row.get('workers', '-')} | Job timeout (min): "
                              f"{row.get('timeout_minutes', '-')} | Retries: {row.get('max_retries', '-')}",
                              f"   Project folder: {row.get('project_dir', '-')}"])
                for folder in row.get("output_folders", []):
                    lines.append(f"   Output folder: {folder}")
                for error in row["errors"]:
                    lines.append(f"   ERROR: {error}")
                for warning in row["warnings"]:
                    lines.append(f"   Warning: {warning}")
                lines.append("")
            text.setPlainText("\n".join(lines))
            layout.addWidget(text)
            self.preview_dialog = dialog
            dialog.show()
            self.emit_status_message(f"Previewed {len(active_rows)} child project(s).")
        except Exception as error:
            self.emit_status_message(f"Unable to preview child projects: {error}", status="warning")
